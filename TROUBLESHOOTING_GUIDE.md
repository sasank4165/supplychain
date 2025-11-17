# Troubleshooting Guide

## Table of Contents

1. [Overview](#overview)
2. [Deployment Issues](#deployment-issues)
3. [Runtime Issues](#runtime-issues)
4. [Agent Issues](#agent-issues)
5. [Infrastructure Issues](#infrastructure-issues)
6. [Performance Issues](#performance-issues)
7. [Security Issues](#security-issues)
8. [Data Issues](#data-issues)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Common Error Messages](#common-error-messages)

## Overview

This guide provides solutions to common issues encountered when deploying and operating the Supply Chain Agentic AI Application.

### General Troubleshooting Steps

1. **Check CloudWatch Logs**: Most issues are logged in CloudWatch
2. **Verify Configuration**: Ensure configuration files are valid
3. **Check AWS Service Health**: Verify AWS services are operational
4. **Review Recent Changes**: Identify what changed before the issue started
5. **Test in Isolation**: Isolate the problem component

### Getting Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/sc-agent-orchestrator-dev --follow

# View specific log group
aws logs tail <log-group-name> --since 1h

# Search logs for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/sc-agent-orchestrator-dev \
  --filter-pattern "ERROR"
```

## Deployment Issues

### Issue: CDK Bootstrap Fails

**Symptoms**:
```
Error: Unable to resolve AWS account to use
```

**Causes**:
- AWS credentials not configured
- Insufficient permissions
- Wrong region selected

**Solutions**:

1. Verify AWS credentials:
```bash
aws sts get-caller-identity
```

2. Check AWS CLI configuration:
```bash
aws configure list
```

3. Explicitly specify account and region:
```bash
cdk bootstrap aws://123456789012/us-east-1
```

4. Verify IAM permissions:
```bash
# Required permissions:
# - cloudformation:*
# - s3:*
# - iam:*
# - lambda:*
```

---

### Issue: Stack Deployment Fails

**Symptoms**:
```
CREATE_FAILED: Resource creation failed
ROLLBACK_IN_PROGRESS
```

**Causes**:
- Resource limits exceeded
- Invalid configuration
- Dependency issues
- Insufficient permissions

**Solutions**:

1. Check CloudFormation events:
```bash
aws cloudformation describe-stack-events \
  --stack-name sc-agent-app-dev \
  --max-items 20
```

2. Review specific resource failure:
```bash
aws cloudformation describe-stack-resources \
  --stack-name sc-agent-app-dev \
  --query 'StackResources[?ResourceStatus==`CREATE_FAILED`]'
```

3. Check service quotas:
```bash
aws service-quotas list-service-quotas \
  --service-code lambda \
  --query 'Quotas[?QuotaName==`Concurrent executions`]'
```

4. Validate configuration:
```bash
python scripts/validate-config.py --config config/dev.yaml
```

5. Clean up and retry:
```bash
./scripts/cleanup.sh --environment dev
./deploy.sh --environment dev
```

---

### Issue: Lambda Deployment Package Too Large

**Symptoms**:
```
Error: Unzipped size must be smaller than 262144000 bytes
```

**Causes**:
- Too many dependencies
- Large files included in package
- Inefficient packaging

**Solutions**:

1. Use Lambda Layers for dependencies:
```python
# In CDK stack
layer = lambda_.LayerVersion(
    self, "DependenciesLayer",
    code=lambda_.Code.from_asset("layers/dependencies"),
    compatible_runtimes=[lambda_.Runtime.PYTHON_3_9]
)
```

2. Exclude unnecessary files:
```python
# In CDK stack
lambda_.Function(
    self, "Function",
    code=lambda_.Code.from_asset(
        "lambda_functions",
        exclude=["*.pyc", "__pycache__", "tests"]
    )
)
```

3. Use Docker-based deployment:
```python
# In CDK stack
lambda_.DockerImageFunction(
    self, "Function",
    code=lambda_.DockerImageCode.from_image_asset("lambda_functions")
)
```

---

### Issue: Bedrock Access Denied

**Symptoms**:
```
AccessDeniedException: Could not access model
```

**Causes**:
- Model access not enabled
- Wrong region
- Insufficient IAM permissions

**Solutions**:

1. Enable model access in Bedrock console:
   - Navigate to Amazon Bedrock console
   - Go to "Model access"
   - Request access for required models

2. Verify model availability in region:
```bash
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `claude`)].modelId'
```

3. Check IAM permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": "arn:aws:bedrock:*::foundation-model/*"
}
```

4. Test model access:
```bash
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","messages":[{"role":"user","content":"Hello"}],"max_tokens":100}' \
  --region us-east-1 \
  output.json
```

---

### Issue: DynamoDB Table Already Exists

**Symptoms**:
```
ResourceAlreadyExistsException: Table already exists
```

**Causes**:
- Previous deployment not cleaned up
- Name collision with existing table
- Deployment interrupted

**Solutions**:

1. Use different prefix in configuration:
```yaml
project:
  prefix: "sc-agent-v2"  # Change prefix
```

2. Delete existing table (if safe):
```bash
aws dynamodb delete-table --table-name sc-agent-sessions-dev
```

3. Import existing table into CDK:
```python
# In CDK stack
table = dynamodb.Table.from_table_name(
    self, "ExistingTable",
    table_name="sc-agent-sessions-dev"
)
```

4. Complete cleanup and redeploy:
```bash
./scripts/cleanup.sh --environment dev --force
./deploy.sh --environment dev
```

## Runtime Issues

### Issue: API Gateway Returns 403 Forbidden

**Symptoms**:
```
{"message": "Missing Authentication Token"}
```

**Causes**:
- Invalid or missing JWT token
- Cognito authorizer misconfigured
- API key required but not provided
- CORS issues

**Solutions**:

1. Verify Cognito user pool:
```bash
aws cognito-idp list-user-pools --max-results 10
```

2. Get valid JWT token:
```bash
# Authenticate user
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <client-id> \
  --auth-parameters USERNAME=<username>,PASSWORD=<password>
```

3. Test with token:
```bash
curl -X POST https://api.example.com/query \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

4. Check API Gateway authorizer:
```bash
aws apigateway get-authorizers --rest-api-id <api-id>
```

5. Verify CORS configuration:
```bash
# Check if OPTIONS method exists
aws apigateway get-method \
  --rest-api-id <api-id> \
  --resource-id <resource-id> \
  --http-method OPTIONS
```

---

### Issue: Lambda Function Timeout

**Symptoms**:
```
Task timed out after 180.00 seconds
```

**Causes**:
- Long-running query
- Slow external API calls
- Database connection issues
- Insufficient resources

**Solutions**:

1. Increase timeout in configuration:
```yaml
resources:
  lambda:
    timeout_seconds: 300  # Increase to 5 minutes
```

2. Optimize query performance:
```python
# Add pagination
# Use connection pooling
# Cache frequent queries
```

3. Increase Lambda memory (also increases CPU):
```yaml
resources:
  lambda:
    memory_mb: 2048  # More memory = more CPU
```

4. Use asynchronous processing:
```python
# Invoke Lambda asynchronously
lambda_client.invoke(
    FunctionName='function-name',
    InvocationType='Event',  # Async
    Payload=json.dumps(payload)
)
```

5. Check CloudWatch logs for bottlenecks:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/sc-agent-orchestrator-dev \
  --filter-pattern "Duration"
```

---

### Issue: Lambda Cold Start Latency

**Symptoms**:
- First request takes 5-10 seconds
- Subsequent requests are fast
- Intermittent slow responses

**Causes**:
- Lambda cold starts
- Large deployment package
- Many dependencies to load

**Solutions**:

1. Enable provisioned concurrency (production):
```yaml
resources:
  lambda:
    provisioned_concurrency: 5  # Keep 5 instances warm
```

2. Use ARM64 architecture (faster cold starts):
```yaml
resources:
  lambda:
    architecture: "arm64"
```

3. Optimize imports:
```python
# Import only what you need
from boto3 import client  # Not: import boto3

# Lazy load heavy dependencies
def get_model():
    import heavy_library
    return heavy_library.Model()
```

4. Reduce package size:
```bash
# Remove unnecessary files
# Use Lambda Layers
# Minimize dependencies
```

5. Implement warming strategy:
```python
# Add warming handler
if event.get('source') == 'aws.events':
    return {'statusCode': 200, 'body': 'warmed'}
```

---

### Issue: DynamoDB Throttling

**Symptoms**:
```
ProvisionedThroughputExceededException
```

**Causes**:
- Exceeded read/write capacity
- Hot partition key
- Burst capacity exhausted

**Solutions**:

1. Switch to on-demand billing:
```yaml
resources:
  dynamodb:
    billing_mode: "PAY_PER_REQUEST"
```

2. Increase provisioned capacity:
```yaml
resources:
  dynamodb:
    billing_mode: "PROVISIONED"
    read_capacity: 50
    write_capacity: 50
```

3. Enable auto-scaling:
```python
# In CDK stack
table.auto_scale_read_capacity(
    min_capacity=5,
    max_capacity=100
).scale_on_utilization(target_utilization_percent=70)
```

4. Implement exponential backoff:
```python
import time
from botocore.exceptions import ClientError

def put_item_with_retry(table, item, max_retries=3):
    for attempt in range(max_retries):
        try:
            return table.put_item(Item=item)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                time.sleep(2 ** attempt)
            else:
                raise
```

5. Optimize partition key design:
```python
# Use composite key to distribute load
partition_key = f"{user_id}#{timestamp.date()}"
```

## Agent Issues

### Issue: Agent Returns Empty or Invalid Response

**Symptoms**:
- Agent returns empty string
- Response doesn't match expected format
- Missing required fields

**Causes**:
- Model prompt issues
- Tool execution failures
- Context too large
- Model limitations

**Solutions**:

1. Check agent logs:
```bash
aws logs tail /aws/lambda/sc-agent-orchestrator-dev --follow
```

2. Verify model configuration:
```yaml
agents:
  sql_agent:
    model: "anthropic.claude-3-5-sonnet-20241022-v2:0"  # Verify model ID
```

3. Test model directly:
```python
import boto3

bedrock = boto3.client('bedrock-runtime')
response = bedrock.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'messages': [{'role': 'user', 'content': 'Hello'}],
        'max_tokens': 1000
    })
)
```

4. Reduce context size:
```yaml
agents:
  context_window_size: 5  # Reduce from 10
```

5. Add error handling:
```python
try:
    response = agent.process_query(query)
    if not response:
        return {"error": "Empty response from agent"}
except Exception as e:
    logger.error(f"Agent error: {str(e)}")
    return {"error": "Agent processing failed"}
```

---

### Issue: Tool Execution Fails

**Symptoms**:
```
ToolExecutionError: Failed to execute tool
```

**Causes**:
- Lambda function errors
- Invalid tool parameters
- Timeout
- Permission issues

**Solutions**:

1. Check tool Lambda logs:
```bash
aws logs tail /aws/lambda/sc-agent-inventory-optimizer-dev --follow
```

2. Test tool directly:
```bash
aws lambda invoke \
  --function-name sc-agent-inventory-optimizer-dev \
  --payload '{"action":"calculate_reorder_points","parameters":{}}' \
  output.json
```

3. Verify tool permissions:
```bash
# Check Lambda execution role
aws iam get-role --role-name sc-agent-lambda-exec-dev
```

4. Increase tool timeout:
```yaml
agents:
  inventory_optimizer:
    timeout_seconds: 120  # Increase timeout
```

5. Add retry logic:
```python
# In tool_executor.py
async def _execute_tool(self, tool: Dict, timeout: int) -> Dict:
    for attempt in range(3):
        try:
            result = await self._invoke_lambda(tool, timeout)
            return {"success": True, "result": result}
        except Exception as e:
            if attempt == 2:
                return {"success": False, "error": str(e)}
            await asyncio.sleep(2 ** attempt)
```

---

### Issue: Context Window Exceeded

**Symptoms**:
```
ValidationException: Input is too long
```

**Causes**:
- Too many conversation messages
- Large message content
- Model token limit exceeded

**Solutions**:

1. Reduce context window:
```yaml
agents:
  context_window_size: 5  # Reduce from 10
```

2. Implement conversation summarization:
```python
# In conversation_context_manager.py
def summarize_context(self, session_id: str) -> str:
    messages = self.get_context(session_id)
    # Use LLM to summarize
    summary = self.model_manager.invoke_model(
        model_id=self.config.get("agents.default_model"),
        messages=[{
            "role": "user",
            "content": f"Summarize this conversation: {messages}"
        }]
    )
    return summary
```

3. Truncate old messages:
```python
def get_context(self, session_id: str, max_messages: int = None) -> List[Dict]:
    max_messages = max_messages or self.context_window
    messages = self._fetch_from_dynamodb(session_id)
    return messages[-max_messages:]  # Keep only recent messages
```

4. Use smaller model for context:
```yaml
agents:
  default_model: "anthropic.claude-3-haiku-20240307-v1:0"  # Smaller context
```

## Infrastructure Issues

### Issue: VPC Lambda Cannot Access Internet

**Symptoms**:
- Lambda timeout when calling external APIs
- Cannot reach AWS services
- DNS resolution fails

**Causes**:
- No NAT Gateway configured
- Route table misconfigured
- Security group blocking traffic

**Solutions**:

1. Verify NAT Gateway exists:
```bash
aws ec2 describe-nat-gateways \
  --filter "Name=state,Values=available"
```

2. Check route tables:
```bash
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=<vpc-id>"
```

3. Add VPC endpoints:
```yaml
networking:
  vpc_endpoints:
    - "s3"
    - "dynamodb"
    - "secretsmanager"
    - "bedrock-runtime"
```

4. Verify security group rules:
```bash
aws ec2 describe-security-groups \
  --group-ids <security-group-id>
```

5. Test connectivity from Lambda:
```python
import urllib.request

def lambda_handler(event, context):
    try:
        response = urllib.request.urlopen('https://www.google.com')
        return {'statusCode': 200, 'body': 'Connected'}
    except Exception as e:
        return {'statusCode': 500, 'body': str(e)}
```

---

### Issue: S3 Bucket Access Denied

**Symptoms**:
```
AccessDenied: Access Denied
```

**Causes**:
- Bucket policy blocking access
- IAM permissions missing
- Bucket in different account
- Encryption key access denied

**Solutions**:

1. Check bucket policy:
```bash
aws s3api get-bucket-policy --bucket sc-agent-data-dev
```

2. Verify IAM permissions:
```bash
aws iam get-role-policy \
  --role-name sc-agent-lambda-exec-dev \
  --policy-name S3Access
```

3. Test access:
```bash
aws s3 ls s3://sc-agent-data-dev/
```

4. Add required permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::sc-agent-data-dev",
    "arn:aws:s3:::sc-agent-data-dev/*"
  ]
}
```

5. Check KMS key permissions (if encrypted):
```bash
aws kms describe-key --key-id <key-id>
```

## Performance Issues

### Issue: High Query Latency

**Symptoms**:
- Queries take >5 seconds
- Inconsistent response times
- User complaints about slowness

**Causes**:
- Cold starts
- Inefficient queries
- Large datasets
- Network latency

**Solutions**:

1. Enable X-Ray tracing:
```yaml
features:
  xray_tracing: true
```

2. Analyze trace data:
```bash
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s)
```

3. Optimize database queries:
```python
# Add indexes
# Use pagination
# Cache frequent queries
# Use DynamoDB query instead of scan
```

4. Increase Lambda resources:
```yaml
resources:
  lambda:
    memory_mb: 2048  # More memory = more CPU
```

5. Use provisioned concurrency:
```yaml
resources:
  lambda:
    provisioned_concurrency: 10
```

6. Implement caching:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_inventory_data(warehouse_id):
    # Cache results
    return query_database(warehouse_id)
```

---

### Issue: High Token Usage Costs

**Symptoms**:
- Unexpectedly high AWS bills
- Bedrock costs increasing
- Token usage metrics high

**Causes**:
- Large context windows
- Inefficient prompts
- Too many model calls
- Using expensive models

**Solutions**:

1. Use cheaper models where appropriate:
```yaml
agents:
  sql_agent:
    model: "anthropic.claude-3-haiku-20240307-v1:0"  # Cheaper
```

2. Reduce context window:
```yaml
agents:
  context_window_size: 5  # Reduce from 10
```

3. Optimize prompts:
```python
# Be concise
# Remove unnecessary examples
# Use system prompts efficiently
```

4. Implement caching:
```python
# Cache model responses for identical queries
# Use conversation summarization
```

5. Monitor token usage:
```bash
aws cloudwatch get-metric-statistics \
  --namespace sc-agent/Agents \
  --metric-name TokenUsage \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

## Security Issues

### Issue: Secrets Not Found

**Symptoms**:
```
ResourceNotFoundException: Secrets Manager can't find the specified secret
```

**Causes**:
- Secret not created
- Wrong secret name
- Wrong region
- Insufficient permissions

**Solutions**:

1. List secrets:
```bash
aws secretsmanager list-secrets
```

2. Create missing secret:
```bash
aws secretsmanager create-secret \
  --name /sc-agent/dev/database/credentials \
  --secret-string '{"username":"admin","password":"password"}'
```

3. Verify secret name:
```python
# Check configuration
secret_name = config.get("database.password_secret")
print(f"Looking for secret: {secret_name}")
```

4. Check IAM permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": "arn:aws:secretsmanager:*:*:secret:/sc-agent/*"
}
```

---

### Issue: IAM Permission Denied

**Symptoms**:
```
AccessDeniedException: User is not authorized to perform action
```

**Causes**:
- Missing IAM permissions
- Wrong resource ARN
- Service control policies
- Permission boundaries

**Solutions**:

1. Check current permissions:
```bash
aws iam get-role-policy \
  --role-name sc-agent-lambda-exec-dev \
  --policy-name DefaultPolicy
```

2. Add required permissions:
```bash
aws iam put-role-policy \
  --role-name sc-agent-lambda-exec-dev \
  --policy-name AdditionalPermissions \
  --policy-document file://policy.json
```

3. Use IAM policy simulator:
```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/sc-agent-lambda-exec-dev \
  --action-names bedrock:InvokeModel \
  --resource-arns "*"
```

4. Check CloudTrail for denied actions:
```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AccessDenied \
  --max-results 10
```

## Data Issues

### Issue: Athena Query Fails

**Symptoms**:
```
SYNTAX_ERROR: line 1:1: Table does not exist
```

**Causes**:
- Table not created in Glue Catalog
- Wrong database name
- Data not in S3
- Partition issues

**Solutions**:

1. List Glue tables:
```bash
aws glue get-tables --database-name supply_chain_db
```

2. Create missing table:
```bash
aws glue create-table \
  --database-name supply_chain_db \
  --table-input file://table-definition.json
```

3. Verify S3 data:
```bash
aws s3 ls s3://sc-agent-data-dev/data/
```

4. Repair partitions:
```sql
MSCK REPAIR TABLE supply_chain_db.inventory;
```

5. Test query:
```bash
aws athena start-query-execution \
  --query-string "SELECT * FROM supply_chain_db.inventory LIMIT 10" \
  --result-configuration OutputLocation=s3://sc-agent-data-dev/query-results/
```

## Monitoring and Logging

### Issue: Logs Not Appearing in CloudWatch

**Symptoms**:
- No logs in CloudWatch
- Missing log groups
- Logs delayed

**Causes**:
- IAM permissions missing
- Log group not created
- Retention policy deleted logs
- Wrong log group name

**Solutions**:

1. List log groups:
```bash
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/sc-agent
```

2. Create log group:
```bash
aws logs create-log-group --log-group-name /aws/lambda/sc-agent-orchestrator-dev
```

3. Check IAM permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "arn:aws:logs:*:*:*"
}
```

4. Verify Lambda logging:
```python
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Lambda invoked")
    # Your code
```

---

### Issue: Metrics Not Showing in CloudWatch

**Symptoms**:
- Dashboard shows no data
- Metrics missing
- Alarms not triggering

**Causes**:
- Metrics not being published
- Wrong namespace
- IAM permissions missing
- Time range issue

**Solutions**:

1. List metrics:
```bash
aws cloudwatch list-metrics --namespace sc-agent/Agents
```

2. Verify metric publishing:
```python
# In metrics_collector.py
cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
    Namespace='sc-agent/Agents',
    MetricData=[{
        'MetricName': 'TestMetric',
        'Value': 1,
        'Unit': 'Count'
    }]
)
```

3. Check IAM permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "cloudwatch:PutMetricData"
  ],
  "Resource": "*"
}
```

4. Adjust time range in console:
```
# Change from "Last 1 hour" to "Last 24 hours"
```

## Common Error Messages

### "Rate exceeded"

**Cause**: API throttling
**Solution**: Implement exponential backoff, increase limits, or reduce request rate

### "Invalid parameter value"

**Cause**: Configuration error
**Solution**: Validate configuration file, check parameter types and ranges

### "Resource not found"

**Cause**: Resource doesn't exist or wrong name
**Solution**: Verify resource names, check region, ensure deployment completed

### "Timeout"

**Cause**: Operation took too long
**Solution**: Increase timeout, optimize code, check for blocking operations

### "Out of memory"

**Cause**: Lambda memory limit exceeded
**Solution**: Increase Lambda memory, optimize memory usage, reduce data size

### "Connection refused"

**Cause**: Network connectivity issue
**Solution**: Check security groups, NAT Gateway, VPC endpoints

### "Signature expired"

**Cause**: Clock skew or old credentials
**Solution**: Sync system clock, refresh AWS credentials

### "Throttling exception"

**Cause**: Too many requests
**Solution**: Implement backoff, increase capacity, use batching

## Getting Additional Help

### Resources

- [AWS Support](https://console.aws.amazon.com/support/)
- [AWS Documentation](https://docs.aws.amazon.com/)
- [CloudWatch Logs Insights](https://console.aws.amazon.com/cloudwatch/home#logsV2:logs-insights)
- [AWS X-Ray Console](https://console.aws.amazon.com/xray/)

### Diagnostic Commands

```bash
# Check all stack statuses
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Get recent CloudWatch alarms
aws cloudwatch describe-alarms --state-value ALARM

# Check Lambda function errors
aws lambda get-function --function-name sc-agent-orchestrator-dev

# View recent CloudTrail events
aws cloudtrail lookup-events --max-results 50

# Check service health
aws health describe-events --filter eventTypeCategories=issue
```

### Contact Support

If issues persist:
1. Gather logs and error messages
2. Document steps to reproduce
3. Check AWS Service Health Dashboard
4. Contact AWS Support or your DevOps team
5. Open an issue in the repository

## Related Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md)
- [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)
- [AWS Troubleshooting Documentation](https://docs.aws.amazon.com/troubleshooting/)
