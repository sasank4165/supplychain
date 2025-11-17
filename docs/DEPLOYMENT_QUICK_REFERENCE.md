# Deployment Quick Reference

Quick reference for common deployment tasks.

## Quick Start

```bash
# First-time deployment
bash deploy.sh --environment dev

# Update existing deployment
bash deploy.sh --environment dev --skip-bootstrap --auto-approve
```

## Common Commands

### Validate Environment

```bash
# Check all prerequisites
bash scripts/validate-deployment.sh --environment dev

# Verbose validation
bash scripts/validate-deployment.sh --environment prod --verbose
```

### Deploy

```bash
# Interactive deployment
bash deploy.sh --environment dev

# Automated deployment
bash deploy.sh --environment prod --auto-approve

# Quick deployment (skip checks)
bash deploy.sh --environment dev --skip-validation --skip-bootstrap
```

### Verify Deployment

```bash
# Basic verification
bash scripts/verify-deployment.sh --environment dev

# Detailed verification
bash scripts/verify-deployment.sh --environment prod --verbose
```

### Load Configuration

```bash
# Load config to .env file
bash scripts/load-config.sh --environment dev

# Load and export to shell
bash scripts/load-config.sh --environment dev --export
source .env
```

## Environment Variables

After deployment, key variables are available in `.env`:

```bash
# Source environment variables
source .env

# View API endpoint
echo $API_ENDPOINT

# View User Pool ID
echo $USER_POOL_ID
```

## Stack Management

### View Stack Status

```bash
aws cloudformation describe-stacks \
  --stack-name sc-agent-dev-stack \
  --query "Stacks[0].StackStatus"
```

### View Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name sc-agent-dev-stack \
  --query "Stacks[0].Outputs"
```

### Delete Stack

```bash
cd cdk
cdk destroy
```

## Resource Access

### View Lambda Functions

```bash
aws lambda list-functions \
  --query "Functions[?starts_with(FunctionName, 'sc-agent-dev')].[FunctionName,Runtime,LastModified]" \
  --output table
```

### View DynamoDB Tables

```bash
aws dynamodb list-tables \
  --query "TableNames[?starts_with(@, 'sc-agent-dev')]"
```

### View S3 Buckets

```bash
aws s3 ls | grep sc-agent-dev
```

## Logs and Monitoring

### View Lambda Logs

```bash
# Tail logs
aws logs tail /aws/lambda/sc-agent-dev-sql-executor --follow

# View recent logs
aws logs tail /aws/lambda/sc-agent-dev-sql-executor --since 1h
```

### View CloudWatch Metrics

```bash
# Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=sc-agent-dev-sql-executor \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## Troubleshooting

### Check Stack Events

```bash
aws cloudformation describe-stack-events \
  --stack-name sc-agent-dev-stack \
  --max-items 20 \
  --query "StackEvents[*].[Timestamp,ResourceStatus,ResourceType,ResourceStatusReason]" \
  --output table
```

### Test Lambda Function

```bash
aws lambda invoke \
  --function-name sc-agent-dev-sql-executor \
  --payload '{"test": "data"}' \
  response.json
```

### Check Bedrock Access

```bash
aws bedrock list-foundation-models \
  --query "modelSummaries[?contains(modelId, 'claude')].[modelId,modelName]" \
  --output table
```

## Configuration Management

### Validate Configuration

```bash
python3 scripts/validate-config.py --config config/dev.yaml
```

### View Configuration

```bash
# View YAML config
cat config/dev.yaml

# Parse specific value
python3 -c "import yaml; print(yaml.safe_load(open('config/dev.yaml'))['resources']['lambda']['memory_mb'])"
```

### Update Configuration

```bash
# Edit configuration file
nano config/dev.yaml

# Validate changes
python3 scripts/validate-config.py --config config/dev.yaml

# Redeploy with new config
bash deploy.sh --environment dev --auto-approve
```

## Parameter Store

### View Parameters

```bash
aws ssm get-parameters-by-path \
  --path /sc-agent-dev \
  --recursive \
  --query "Parameters[*].[Name,Value]" \
  --output table
```

### Get Specific Parameter

```bash
aws ssm get-parameter \
  --name /sc-agent-dev/api-endpoint \
  --query "Parameter.Value" \
  --output text
```

## Cost Management

### View Resource Tags

```bash
# DynamoDB table tags
aws dynamodb list-tags-of-resource \
  --resource-arn arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/sc-agent-dev-conversations
```

### Estimate Costs

```bash
# View Lambda costs (last 7 days)
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '7 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --filter file://filter.json
```

## Cleanup

### Remove All Resources

```bash
# Destroy CDK stack
cd cdk
cdk destroy

# Verify deletion
aws cloudformation list-stacks \
  --stack-status-filter DELETE_COMPLETE \
  --query "StackSummaries[?contains(StackName, 'sc-agent-dev')]"
```

### Clean Local Files

```bash
# Remove generated files
rm -f .env .env.backup
rm -rf cdk.out
rm -rf lambda_layers
```

## Cheat Sheet

| Task | Command |
|------|---------|
| Deploy dev | `bash deploy.sh -e dev` |
| Deploy prod | `bash deploy.sh -e prod` |
| Validate | `bash scripts/validate-deployment.sh -e dev` |
| Verify | `bash scripts/verify-deployment.sh -e dev` |
| Load config | `bash scripts/load-config.sh -e dev` |
| View logs | `aws logs tail /aws/lambda/FUNCTION_NAME --follow` |
| Stack status | `aws cloudformation describe-stacks --stack-name STACK_NAME` |
| Destroy | `cd cdk && cdk destroy` |

## Support

For detailed documentation, see:
- [Deployment Automation Guide](DEPLOYMENT_AUTOMATION_GUIDE.md)
- [Configuration Reference](../config/README.md)
- [CDK Documentation](../cdk/README.md)
