# Operations Runbook

## Table of Contents

1. [Overview](#overview)
2. [Daily Operations](#daily-operations)
3. [Monitoring and Alerting](#monitoring-and-alerting)
4. [Common Tasks](#common-tasks)
5. [Incident Response](#incident-response)
6. [Maintenance Procedures](#maintenance-procedures)
7. [Backup and Recovery](#backup-and-recovery)
8. [Performance Tuning](#performance-tuning)
9. [Security Operations](#security-operations)
10. [Cost Management](#cost-management)
11. [Escalation Procedures](#escalation-procedures)
12. [Runbook Checklists](#runbook-checklists)

## Overview

This runbook provides step-by-step procedures for operating and maintaining the Supply Chain Agentic AI Application in production. It covers routine tasks, incident response, and troubleshooting procedures.

### Key Contacts

| Role | Contact | Escalation Level |
|------|---------|------------------|
| On-Call Engineer | oncall@example.com | Level 1 |
| Platform Team Lead | platform-lead@example.com | Level 2 |
| AWS Support | AWS Console | Level 3 |
| Security Team | security@example.com | Security Issues |

### Service Level Objectives (SLOs)

- **Availability**: 99.9% uptime
- **Latency**: P95 < 3 seconds
- **Error Rate**: < 0.1%
- **Recovery Time Objective (RTO)**: 1 hour
- **Recovery Point Objective (RPO)**: 24 hours

## Daily Operations

### Morning Health Check

Perform these checks at the start of each business day:

**1. Check System Status**
```bash
# Check all CloudFormation stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `sc-agent-prod`)].{Name:StackName,Status:StackStatus}'
```

**2. Review CloudWatch Alarms**
```bash
# Check for active alarms
aws cloudwatch describe-alarms \
  --state-value ALARM \
  --query 'MetricAlarms[*].{Name:AlarmName,State:StateValue,Reason:StateReason}'
```

**3. Check Lambda Function Health**
```bash
# Check Lambda errors in last 24 hours
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=sc-agent-orchestrator-prod \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

**4. Review Recent Logs**
```bash
# Check for errors in last hour
aws logs filter-log-events \
  --log-group-name /aws/lambda/sc-agent-orchestrator-prod \
  --start-time $(($(date +%s) - 3600))000 \
  --filter-pattern "ERROR"
```

**5. Verify API Gateway Health**
```bash
# Test health endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name sc-agent-app-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

curl -s $API_ENDPOINT/health | jq
```

**6. Check DynamoDB Metrics**
```bash
# Check DynamoDB throttling
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value=sc-agent-sessions-prod \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

**7. Review Cost Dashboard**
- Navigate to AWS Cost Explorer
- Check daily spend vs. budget
- Review cost allocation by service
- Identify any anomalies

**Daily Health Check Checklist:**
- [ ] All stacks in healthy state
- [ ] No active CloudWatch alarms
- [ ] Lambda error rate < 0.1%
- [ ] API Gateway responding
- [ ] No DynamoDB throttling
- [ ] Costs within expected range

### Evening Review

**1. Review Daily Metrics**
```bash
# Get daily query count
aws cloudwatch get-metric-statistics \
  --namespace sc-agent/Agents \
  --metric-name QueryCount \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum
```

**2. Check for Failed Deployments**
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name sc-agent-app-prod \
  --max-items 50 \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`]'
```

**3. Review Security Events**
```bash
# Check CloudTrail for security-related events
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin \
  --max-results 10
```

## Monitoring and Alerting

### CloudWatch Dashboard

Access the main dashboard:
```bash
# Open dashboard URL
echo "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=sc-agent-agents-prod"
```

**Key Metrics to Monitor:**

1. **Query Latency**
   - Metric: `sc-agent/Agents/QueryLatency`
   - Threshold: P95 < 3000ms
   - Action: Investigate if exceeded

2. **Error Rate**
   - Metric: `sc-agent/Agents/QueryCount` (Success=False)
   - Threshold: < 0.1%
   - Action: Check logs immediately

3. **Token Usage**
   - Metric: `sc-agent/Agents/TokenUsage`
   - Threshold: Monitor for cost anomalies
   - Action: Review if 50% increase

4. **Lambda Throttling**
   - Metric: `AWS/Lambda/Throttles`
   - Threshold: 0
   - Action: Increase concurrency

### Alarm Response Procedures

**High Error Rate Alarm**

When error rate exceeds 1%:

1. Check recent deployments:
```bash
aws cloudformation describe-stack-events \
  --stack-name sc-agent-app-prod \
  --max-items 20
```

2. Review error logs:
```bash
aws logs tail /aws/lambda/sc-agent-orchestrator-prod \
  --filter-pattern "ERROR" \
  --since 1h
```

3. Identify error pattern:
   - Authentication errors → Check Cognito
   - Bedrock errors → Check model access
   - Database errors → Check DynamoDB
   - Timeout errors → Check Lambda configuration

4. If critical, consider rollback:
```bash
./scripts/rollback.sh --environment prod --version previous
```

**High Latency Alarm**

When P95 latency exceeds 5 seconds:

1. Check X-Ray traces:
```bash
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --filter-expression 'duration > 5'
```

2. Identify bottleneck:
   - Lambda cold starts → Enable provisioned concurrency
   - Database queries → Optimize queries
   - External API calls → Check timeouts
   - Large context → Reduce context window

3. Apply immediate fix if possible
4. Schedule performance optimization

**Lambda Throttling Alarm**

When Lambda functions are throttled:

1. Check current concurrency:
```bash
aws lambda get-function-concurrency \
  --function-name sc-agent-orchestrator-prod
```

2. Increase reserved concurrency:
```bash
aws lambda put-function-concurrency \
  --function-name sc-agent-orchestrator-prod \
  --reserved-concurrent-executions 150
```

3. Update configuration for permanent fix:
```yaml
# In config/prod.yaml
resources:
  lambda:
    reserved_concurrency: 150
```

4. Redeploy with updated configuration

**DynamoDB Throttling Alarm**

When DynamoDB tables are throttled:

1. Check current capacity:
```bash
aws dynamodb describe-table \
  --table-name sc-agent-sessions-prod \
  --query 'Table.BillingModeSummary'
```

2. If using provisioned capacity, increase it:
```bash
aws dynamodb update-table \
  --table-name sc-agent-sessions-prod \
  --provisioned-throughput ReadCapacityUnits=100,WriteCapacityUnits=100
```

3. Consider switching to on-demand:
```yaml
# In config/prod.yaml
resources:
  dynamodb:
    billing_mode: PAY_PER_REQUEST
```

## Common Tasks

### Task 1: Deploy Configuration Update

**Scenario**: Update agent configuration without code changes

**Steps**:

1. Update configuration file:
```bash
vi config/prod.yaml
```

2. Validate configuration:
```bash
python scripts/validate-config.py --config config/prod.yaml
```

3. Deploy changes:
```bash
./deploy.sh --environment prod --config config/prod.yaml
```

4. Verify deployment:
```bash
./scripts/verify-deployment.sh --environment prod
```

5. Monitor for issues:
```bash
aws logs tail /aws/lambda/sc-agent-orchestrator-prod --follow
```

**Rollback if needed**:
```bash
./scripts/rollback.sh --environment prod --version previous
```

### Task 2: Add New Cognito User

**Scenario**: Create user account for new team member

**Steps**:

1. Get User Pool ID:
```bash
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name sc-agent-app-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)
```

2. Create user:
```bash
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username john.doe@example.com \
  --user-attributes Name=email,Value=john.doe@example.com \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS
```

3. Add user to group:
```bash
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username john.doe@example.com \
  --group-name warehouse_managers
```

4. Send credentials to user securely

### Task 3: Rotate Secrets

**Scenario**: Rotate database credentials or API keys

**Steps**:

1. Generate new credentials
2. Update secret in Secrets Manager:
```bash
aws secretsmanager update-secret \
  --secret-id /sc-agent/prod/database/credentials \
  --secret-string '{"username":"admin","password":"new-secure-password"}'
```

3. Restart Lambda functions to pick up new secret:
```bash
aws lambda update-function-configuration \
  --function-name sc-agent-orchestrator-prod \
  --environment Variables={FORCE_REFRESH=true}
```

4. Verify application still works:
```bash
curl -X POST $API_ENDPOINT/query \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"test","persona":"warehouse_manager"}'
```

5. Document rotation in change log

### Task 4: Scale Resources for High Traffic

**Scenario**: Prepare for expected high traffic event

**Steps**:

1. Increase Lambda concurrency:
```yaml
# In config/prod.yaml
resources:
  lambda:
    reserved_concurrency: 200  # Increase from 100
    provisioned_concurrency: 50  # Add warm instances
```

2. Enable DynamoDB auto-scaling (if using provisioned):
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/sc-agent-sessions-prod \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --min-capacity 50 \
  --max-capacity 500
```

3. Deploy changes:
```bash
./deploy.sh --environment prod
```

4. Monitor during event:
```bash
watch -n 30 'aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value=sc-agent-orchestrator-prod \
  --start-time $(date -u -d "5 minutes ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Maximum'
```

5. Scale back after event

### Task 5: Update Bedrock Model

**Scenario**: Switch to newer or different Bedrock model

**Steps**:

1. Verify model access:
```bash
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `claude`)].modelId'
```

2. Update configuration:
```yaml
# In config/prod.yaml
agents:
  default_model: anthropic.claude-3-5-sonnet-20241022-v2:0  # New model
```

3. Test in dev first:
```bash
./deploy.sh --environment dev
# Run tests
./scripts/test-deployment.sh --environment dev
```

4. Deploy to production:
```bash
./deploy.sh --environment prod
```

5. Monitor token usage and costs:
```bash
aws cloudwatch get-metric-statistics \
  --namespace sc-agent/Agents \
  --metric-name TokenUsage \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

### Task 6: Clear Old Conversation History

**Scenario**: Clean up old conversation data to reduce costs

**Steps**:

1. Check current item count:
```bash
aws dynamodb describe-table \
  --table-name sc-agent-conversations-prod \
  --query 'Table.ItemCount'
```

2. DynamoDB TTL should handle this automatically, but to manually clean:
```python
# Run cleanup script
python scripts/cleanup_old_conversations.py --days 90 --environment prod
```

3. Verify cleanup:
```bash
aws dynamodb describe-table \
  --table-name sc-agent-conversations-prod \
  --query 'Table.ItemCount'
```

## Incident Response

### Severity Levels

**P0 - Critical**
- Complete service outage
- Data loss or corruption
- Security breach
- Response time: Immediate
- Escalation: Immediate to Level 2

**P1 - High**
- Partial service degradation
- High error rate (>5%)
- Performance severely impacted
- Response time: 15 minutes
- Escalation: 30 minutes to Level 2

**P2 - Medium**
- Minor service degradation
- Elevated error rate (1-5%)
- Non-critical feature unavailable
- Response time: 1 hour
- Escalation: 2 hours to Level 2

**P3 - Low**
- Cosmetic issues
- Minor performance impact
- Response time: Next business day
- Escalation: As needed

### Incident Response Procedure

**1. Detection and Triage (0-5 minutes)**

- Acknowledge alarm/alert
- Assess severity level
- Create incident ticket
- Notify on-call team

**2. Investigation (5-15 minutes)**

```bash
# Quick diagnostic commands
# Check stack status
aws cloudformation describe-stacks --stack-name sc-agent-app-prod

# Check recent errors
aws logs tail /aws/lambda/sc-agent-orchestrator-prod --since 30m --filter-pattern "ERROR"

# Check CloudWatch alarms
aws cloudwatch describe-alarms --state-value ALARM

# Check X-Ray for traces
aws xray get-trace-summaries --start-time $(date -u -d '30 minutes ago' +%s) --end-time $(date -u +%s)
```

**3. Containment (15-30 minutes)**

- If security incident: Isolate affected resources
- If performance issue: Scale resources
- If bug: Rollback to previous version
- Document all actions taken

**4. Resolution (30 minutes - 2 hours)**

- Apply fix
- Verify resolution
- Monitor for recurrence
- Update incident ticket

**5. Post-Incident (Within 24 hours)**

- Write incident report
- Identify root cause
- Create action items
- Update runbook

### Common Incident Scenarios

**Scenario: Complete API Outage**

**Symptoms**: All API requests failing, health check down

**Investigation**:
```bash
# Check API Gateway
aws apigateway get-rest-apis

# Check Lambda function
aws lambda get-function --function-name sc-agent-orchestrator-prod

# Check recent deployments
aws cloudformation describe-stack-events --stack-name sc-agent-app-prod --max-items 20
```

**Resolution**:
1. If recent deployment: Rollback
```bash
./scripts/rollback.sh --environment prod --version previous
```

2. If AWS service issue: Check AWS Health Dashboard
3. If configuration issue: Fix and redeploy
4. If quota exceeded: Request limit increase

**Scenario: High Error Rate**

**Symptoms**: Error rate >5%, some requests succeeding

**Investigation**:
```bash
# Analyze error patterns
aws logs insights query \
  --log-group-name /aws/lambda/sc-agent-orchestrator-prod \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | stats count() by @message'
```

**Resolution**:
1. If specific error pattern: Apply targeted fix
2. If Bedrock errors: Check model access and quotas
3. If database errors: Check DynamoDB capacity
4. If timeout errors: Increase Lambda timeout or optimize code

**Scenario: Data Corruption**

**Symptoms**: Incorrect data returned, data integrity issues

**Investigation**:
```bash
# Check recent DynamoDB operations
aws dynamodb describe-table --table-name sc-agent-sessions-prod

# Check for recent data modifications
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::DynamoDB::Table \
  --max-results 50
```

**Resolution**:
1. Identify scope of corruption
2. Restore from point-in-time backup:
```bash
aws dynamodb restore-table-to-point-in-time \
  --source-table-name sc-agent-sessions-prod \
  --target-table-name sc-agent-sessions-prod-restored \
  --restore-date-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)
```
3. Verify restored data
4. Switch application to restored table
5. Investigate root cause

## Maintenance Procedures

### Planned Maintenance Window

**Preparation (1 week before)**:

1. Schedule maintenance window
2. Notify stakeholders
3. Prepare rollback plan
4. Test changes in staging

**Maintenance Day**:

1. Post maintenance notice
2. Create backup:
```bash
# Backup DynamoDB tables
aws dynamodb create-backup \
  --table-name sc-agent-sessions-prod \
  --backup-name pre-maintenance-$(date +%Y%m%d)
```

3. Perform maintenance
4. Run verification tests
5. Monitor for issues
6. Post completion notice

### Patching and Updates

**Monthly Security Patches**:

1. Review AWS security bulletins
2. Update Lambda runtimes if needed:
```yaml
# In CDK stack
runtime=lambda_.Runtime.PYTHON_3_11  # Update version
```

3. Update dependencies:
```bash
pip list --outdated
pip install --upgrade <package>
```

4. Test in dev environment
5. Deploy to staging
6. Deploy to production

### Database Maintenance

**Weekly Tasks**:

1. Review DynamoDB metrics
2. Check for hot partitions
3. Optimize queries if needed
4. Review backup status

**Monthly Tasks**:

1. Analyze table usage patterns
2. Adjust capacity if needed
3. Review and clean up old data
4. Test restore procedures

## Backup and Recovery

### Backup Strategy

**Automated Backups**:

- DynamoDB: Point-in-time recovery enabled (35-day retention)
- S3: Versioning enabled
- CloudFormation: Stack templates stored in S3
- Configuration: Version controlled in Git

**Manual Backups**:

Create on-demand backup before major changes:
```bash
# DynamoDB backup
aws dynamodb create-backup \
  --table-name sc-agent-sessions-prod \
  --backup-name manual-backup-$(date +%Y%m%d-%H%M%S)

# S3 backup (if needed)
aws s3 sync s3://sc-agent-data-prod s3://sc-agent-backup-prod/$(date +%Y%m%d)/
```

### Recovery Procedures

**Recover DynamoDB Table**:

1. List available backups:
```bash
aws dynamodb list-backups \
  --table-name sc-agent-sessions-prod
```

2. Restore from backup:
```bash
aws dynamodb restore-table-from-backup \
  --target-table-name sc-agent-sessions-prod-restored \
  --backup-arn <backup-arn>
```

3. Verify restored data
4. Update application configuration to use restored table

**Recover from Point-in-Time**:

```bash
aws dynamodb restore-table-to-point-in-time \
  --source-table-name sc-agent-sessions-prod \
  --target-table-name sc-agent-sessions-prod-restored \
  --restore-date-time 2024-01-15T10:00:00Z
```

**Recover S3 Data**:

```bash
# List versions
aws s3api list-object-versions \
  --bucket sc-agent-data-prod \
  --prefix data/

# Restore specific version
aws s3api copy-object \
  --bucket sc-agent-data-prod \
  --copy-source sc-agent-data-prod/data/file.json?versionId=<version-id> \
  --key data/file.json
```

### Disaster Recovery

**Full Environment Recovery**:

1. Ensure configuration files are available
2. Deploy infrastructure:
```bash
./deploy.sh --environment prod --config config/prod.yaml
```

3. Restore data from backups
4. Verify all services
5. Update DNS/endpoints if needed
6. Run full test suite

**Recovery Time Objective (RTO)**: 1 hour
**Recovery Point Objective (RPO)**: 24 hours

## Performance Tuning

### Lambda Optimization

**Memory Tuning**:

Test different memory configurations:
```bash
# Test with different memory sizes
for memory in 512 1024 1536 2048; do
  aws lambda update-function-configuration \
    --function-name sc-agent-orchestrator-prod \
    --memory-size $memory
  # Run load test
  # Measure latency and cost
done
```

**Provisioned Concurrency**:

Enable for consistent performance:
```yaml
# In config/prod.yaml
resources:
  lambda:
    provisioned_concurrency: 10  # Keep 10 instances warm
```

### DynamoDB Optimization

**Query Optimization**:

1. Use Query instead of Scan
2. Add secondary indexes for common access patterns
3. Use projection expressions to reduce data transfer
4. Implement pagination for large result sets

**Capacity Planning**:

Monitor and adjust:
```bash
# Check consumed capacity
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=sc-agent-sessions-prod \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average,Maximum
```

### Bedrock Optimization

**Model Selection**:

- Use Claude Haiku for simple queries (lower cost)
- Use Claude Sonnet for complex reasoning
- Monitor token usage per model

**Context Management**:

- Reduce context window size
- Implement conversation summarization
- Cache frequent queries

## Security Operations

### Security Monitoring

**Daily Security Checks**:

1. Review CloudTrail logs:
```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin \
  --max-results 50
```

2. Check for unauthorized access:
```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=UnauthorizedOperation \
  --max-results 50
```

3. Review IAM changes:
```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::IAM::Role \
  --max-results 50
```

4. Check security group changes:
```bash
aws ec2 describe-security-groups \
  --filters Name=group-name,Values=sc-agent-* \
  --query 'SecurityGroups[*].{Name:GroupName,Rules:IpPermissions}'
```

### Security Incident Response

**Suspected Breach**:

1. **Immediate Actions**:
   - Isolate affected resources
   - Revoke compromised credentials
   - Enable CloudTrail logging if not already enabled
   - Notify security team

2. **Investigation**:
```bash
# Review all API calls from suspicious IP
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=<username> \
  --max-results 1000

# Check for data exfiltration
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetObject \
  --max-results 1000
```

3. **Containment**:
```bash
# Rotate all secrets
aws secretsmanager rotate-secret --secret-id /sc-agent/prod/database/credentials

# Update security groups
aws ec2 revoke-security-group-ingress \
  --group-id <security-group-id> \
  --ip-permissions <suspicious-rules>

# Disable compromised users
aws cognito-idp admin-disable-user \
  --user-pool-id <pool-id> \
  --username <username>
```

4. **Recovery and Remediation**:
   - Patch vulnerabilities
   - Update access controls
   - Restore from clean backup if needed
   - Document incident

### Access Control Audit

**Monthly Access Review**:

1. Review IAM roles and policies:
```bash
aws iam list-roles --query 'Roles[?contains(RoleName, `sc-agent`)]'
```

2. Review Cognito users and groups:
```bash
aws cognito-idp list-users --user-pool-id <pool-id>
```

3. Remove inactive users
4. Verify least privilege access
5. Document findings

## Cost Management

### Cost Monitoring

**Daily Cost Check**:

```bash
# Get yesterday's cost
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '1 day ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --filter file://cost-filter.json
```

**Weekly Cost Analysis**:

1. Review Cost Explorer dashboard
2. Analyze cost by service
3. Identify cost anomalies
4. Review Bedrock token usage
5. Check for unused resources

### Cost Optimization

**Identify Savings Opportunities**:

1. **Lambda**:
   - Use ARM64 architecture (20% savings)
   - Right-size memory allocation
   - Reduce timeout for quick functions

2. **DynamoDB**:
   - Use on-demand for variable workloads
   - Enable auto-scaling for provisioned capacity
   - Implement TTL for temporary data

3. **S3**:
   - Use Intelligent-Tiering
   - Implement lifecycle policies
   - Delete old logs and backups

4. **CloudWatch**:
   - Reduce log retention
   - Use metric filters instead of storing all logs
   - Delete unused dashboards

**Cost Optimization Script**:

```bash
# Find unused resources
# Old Lambda versions
aws lambda list-versions-by-function \
  --function-name sc-agent-orchestrator-prod \
  --query 'Versions[?Version!=`$LATEST`]'

# Old CloudWatch log groups
aws logs describe-log-groups \
  --query 'logGroups[?storedBytes>`1000000000`]'

# Unused S3 buckets
aws s3api list-buckets --query 'Buckets[*].Name' | \
  xargs -I {} aws s3api get-bucket-tagging --bucket {}
```

### Budget Alerts

**Set Up Budget Alerts**:

```bash
aws budgets create-budget \
  --account-id <account-id> \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

**budget.json**:
```json
{
  "BudgetName": "sc-agent-prod-monthly",
  "BudgetLimit": {
    "Amount": "1000",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

## Escalation Procedures

### When to Escalate

**Escalate to Level 2 (Platform Team Lead) when**:
- P0 incident not resolved in 30 minutes
- P1 incident not resolved in 1 hour
- Multiple services affected
- Data loss suspected
- Security incident confirmed
- Need architectural decision

**Escalate to Level 3 (AWS Support) when**:
- AWS service issue suspected
- Need quota increase urgently
- Complex technical issue beyond team expertise
- Suspected AWS infrastructure problem

### Escalation Contacts

| Level | Contact | Response Time | Availability |
|-------|---------|---------------|--------------|
| L1 | oncall@example.com | 15 min | 24/7 |
| L2 | platform-lead@example.com | 30 min | Business hours |
| L3 | AWS Support (Enterprise) | 15 min | 24/7 |
| Security | security@example.com | Immediate | 24/7 |

### Escalation Template

```
Subject: [P0/P1/P2] Brief description

Incident ID: INC-YYYYMMDD-NNN
Severity: P0/P1/P2
Start Time: YYYY-MM-DD HH:MM UTC
Affected Service: API/Lambda/Database/etc
Impact: Number of users/requests affected

Symptoms:
- Bullet point list of symptoms

Actions Taken:
- Bullet point list of actions

Current Status:
- Current state of incident

Assistance Needed:
- Specific help required
```

## Runbook Checklists

### Pre-Deployment Checklist

- [ ] Configuration validated
- [ ] Changes tested in dev
- [ ] Changes tested in staging
- [ ] Rollback plan prepared
- [ ] Stakeholders notified
- [ ] Backup created
- [ ] Monitoring dashboard ready
- [ ] On-call engineer available

### Post-Deployment Checklist

- [ ] All stacks deployed successfully
- [ ] Health checks passing
- [ ] No CloudWatch alarms
- [ ] API responding correctly
- [ ] Sample queries tested
- [ ] Logs flowing correctly
- [ ] Metrics being published
- [ ] Documentation updated
- [ ] Stakeholders notified

### Incident Response Checklist

- [ ] Incident ticket created
- [ ] Severity assessed
- [ ] On-call team notified
- [ ] Initial investigation complete
- [ ] Containment actions taken
- [ ] Resolution applied
- [ ] Verification complete
- [ ] Stakeholders updated
- [ ] Post-incident review scheduled

### Monthly Maintenance Checklist

- [ ] Review CloudWatch dashboards
- [ ] Analyze cost trends
- [ ] Review security logs
- [ ] Check backup status
- [ ] Test restore procedures
- [ ] Review and update documentation
- [ ] Check for AWS service updates
- [ ] Review and optimize queries
- [ ] Clean up old resources
- [ ] Update dependencies

### Quarterly Review Checklist

- [ ] Review SLO compliance
- [ ] Analyze incident trends
- [ ] Review capacity planning
- [ ] Update disaster recovery plan
- [ ] Conduct DR drill
- [ ] Review access controls
- [ ] Update runbook
- [ ] Team training on new features
- [ ] Review and optimize costs
- [ ] Stakeholder feedback session

## Quick Reference Commands

### Status Checks

```bash
# Overall health
./scripts/verify-deployment.sh --environment prod

# Stack status
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Active alarms
aws cloudwatch describe-alarms --state-value ALARM

# Recent errors
aws logs tail /aws/lambda/sc-agent-orchestrator-prod --since 1h --filter-pattern "ERROR"
```

### Common Fixes

```bash
# Restart Lambda (force new deployment)
aws lambda update-function-configuration \
  --function-name sc-agent-orchestrator-prod \
  --environment Variables={FORCE_REFRESH=true}

# Increase Lambda concurrency
aws lambda put-function-concurrency \
  --function-name sc-agent-orchestrator-prod \
  --reserved-concurrent-executions 150

# Clear DynamoDB throttling (switch to on-demand)
aws dynamodb update-table \
  --table-name sc-agent-sessions-prod \
  --billing-mode PAY_PER_REQUEST

# Rollback deployment
./scripts/rollback.sh --environment prod --version previous
```

### Emergency Contacts

```bash
# On-call engineer
echo "oncall@example.com"

# Platform team lead
echo "platform-lead@example.com"

# AWS Support
echo "https://console.aws.amazon.com/support/"

# Security team
echo "security@example.com"
```

## Related Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment procedures
- [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) - Configuration options
- [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) - Troubleshooting help
- [AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md) - Agent development
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-01-15 | 1.0 | Initial runbook | Platform Team |

---

**Document Owner**: Platform Team  
**Last Updated**: 2024-01-15  
**Review Frequency**: Quarterly  
**Next Review**: 2024-04-15
