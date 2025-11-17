# Cleanup and Rollback Quick Reference

Quick reference for cleanup and rollback operations.

## Rollback Commands

### Preview Rollback
```bash
bash scripts/rollback.sh --environment ENV --dry-run
```

### Rollback to Previous Version
```bash
bash scripts/rollback.sh --environment ENV
```

### Rollback with Auto-Approve (CI/CD)
```bash
bash scripts/rollback.sh --environment ENV --auto-approve
```

## Cleanup Commands

### Preview Cleanup
```bash
bash scripts/cleanup.sh --environment ENV --dry-run
```

### Standard Cleanup (Preserve Data)
```bash
bash scripts/cleanup.sh --environment ENV
```

### Cleanup with Data Deletion
```bash
bash scripts/cleanup.sh --environment ENV --no-preserve-data
```

### Complete Removal
```bash
bash scripts/cleanup.sh --environment ENV --force-delete --delete-logs
```

## Common Scenarios

### Rollback Failed Deployment
```bash
# 1. Preview rollback
bash scripts/rollback.sh --environment prod --dry-run

# 2. Execute rollback
bash scripts/rollback.sh --environment prod

# 3. Verify
bash scripts/verify-deployment.sh --environment prod
```

### Remove Development Environment
```bash
# Complete removal (no data preservation needed)
bash scripts/cleanup.sh --environment dev --force-delete --delete-logs
```

### Cleanup Staging (Keep Data)
```bash
# Remove infrastructure but preserve data
bash scripts/cleanup.sh --environment staging
```

### Emergency Cleanup
```bash
# Force delete everything
bash scripts/cleanup.sh --environment ENV --force-delete --delete-logs
```

## Confirmation Prompts

### Rollback Confirmation
Type: `ROLLBACK`

### Standard Cleanup Confirmation
Type: `DELETE`

### Force Delete Confirmation
Type: `DELETE-EVERYTHING`

## What Gets Deleted/Preserved

### Standard Cleanup (Default)

**Deleted:**
- Lambda functions
- API Gateway
- Cognito User Pools
- VPC and networking
- IAM roles
- CloudWatch alarms

**Preserved:**
- S3 buckets and data
- DynamoDB tables and data
- CloudWatch logs
- KMS keys

### Cleanup with --no-preserve-data

**Additionally Deleted:**
- S3 buckets (emptied first)
- DynamoDB tables
- All data

**Still Preserved:**
- CloudWatch logs

### Force Delete

**Everything Deleted:**
- All infrastructure
- All data
- All logs (if --delete-logs used)

## Rollback Behavior

### What Gets Rolled Back
- CloudFormation stack configuration
- Lambda function code and configuration
- API Gateway configuration
- IAM roles and policies
- VPC and networking configuration

### What Doesn't Get Rolled Back
- S3 bucket contents
- DynamoDB table data
- CloudWatch logs
- Secrets Manager secrets

## Troubleshooting

### Stack Not Found
```bash
# Check if stack exists
aws cloudformation describe-stacks --stack-name STACK-NAME
```

### Bucket Not Empty
```bash
# Manually empty bucket
aws s3 rm s3://BUCKET-NAME --recursive
aws s3 rb s3://BUCKET-NAME
```

### Table Deletion Protection
```bash
# Disable protection
aws dynamodb update-table --table-name TABLE-NAME --no-deletion-protection-enabled
aws dynamodb delete-table --table-name TABLE-NAME
```

### Permission Denied
- Check IAM permissions
- Verify CloudFormation delete permissions
- Check for SCPs blocking deletion

## Safety Tips

1. **Always use --dry-run first**
2. **Verify environment name**
3. **Backup critical data**
4. **Test in dev/staging first**
5. **Monitor CloudFormation console**

## Manual Resource Deletion

### List Resources
```bash
# CloudFormation stacks
aws cloudformation list-stacks --query 'StackSummaries[?contains(StackName, `sc-agent`)]'

# S3 buckets
aws s3 ls | grep sc-agent

# DynamoDB tables
aws dynamodb list-tables --query 'TableNames[?contains(@, `sc-agent`)]'

# Log groups
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/sc-agent
```

### Delete Resources
```bash
# Delete S3 bucket
aws s3 rm s3://BUCKET-NAME --recursive
aws s3 rb s3://BUCKET-NAME

# Delete DynamoDB table
aws dynamodb delete-table --table-name TABLE-NAME

# Delete log group
aws logs delete-log-group --log-group-name LOG-GROUP-NAME
```

## Environment-Specific Defaults

| Environment | Data Preservation | Log Preservation | Versioning | Backups |
|-------------|------------------|------------------|------------|---------|
| Production  | Yes              | Yes              | Yes        | Yes     |
| Staging     | Yes              | No               | Yes        | Yes     |
| Development | No               | No               | No         | No      |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | Error or user cancelled |

## Related Documentation

- [Complete Cleanup and Rollback Guide](CLEANUP_ROLLBACK_GUIDE.md)
- [Deployment Guide](COMPLETE_DEPLOYMENT_GUIDE.md)
- [Configuration Reference](../config/README.md)
