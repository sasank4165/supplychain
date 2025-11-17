# Cleanup and Rollback Guide

This guide explains how to safely cleanup infrastructure and rollback deployments for the Supply Chain Agentic AI Application.

## Table of Contents

- [Overview](#overview)
- [Rollback Operations](#rollback-operations)
- [Cleanup Operations](#cleanup-operations)
- [Data Preservation](#data-preservation)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The application provides two main scripts for managing deployment lifecycle:

1. **Rollback Script** (`scripts/rollback.sh`) - Revert to previous stack versions
2. **Cleanup Script** (`scripts/cleanup.sh`) - Remove infrastructure with data preservation options

Both scripts support:
- Environment-specific operations
- Dry-run mode for preview
- Data preservation options
- Confirmation prompts for safety

## Rollback Operations

### When to Use Rollback

Use rollback when:
- A deployment introduces bugs or issues
- You need to revert to a known good state
- Testing a deployment and want to undo changes
- A deployment partially fails and needs reverting

### Rollback Script Usage

```bash
# Basic rollback to previous version
bash scripts/rollback.sh --environment dev

# Preview rollback without executing
bash scripts/rollback.sh --environment prod --dry-run

# Rollback with auto-approval (CI/CD)
bash scripts/rollback.sh --environment staging --auto-approve

# Rollback to specific version
bash scripts/rollback.sh --environment prod --version 20241116120000
```

### Rollback Options

| Option | Description | Default |
|--------|-------------|---------|
| `--environment, -e` | Environment name (dev, staging, prod) | dev |
| `--version, -v` | Version to rollback to | previous |
| `--config, -c` | Path to config file | config/ENV.yaml |
| `--dry-run` | Preview without executing | false |
| `--auto-approve` | Skip confirmation prompt | false |

### Rollback Process

The rollback script performs these steps:

1. **Load Configuration** - Reads environment configuration
2. **Check Stack History** - Retrieves previous stack versions
3. **Validate Rollback** - Ensures rollback is possible
4. **Execute Rollback** - Reverts stacks in reverse order
5. **Verify State** - Confirms successful rollback

### Rollback Limitations

- Cannot rollback if previous version doesn't exist
- Some resource changes may not be reversible
- Data in S3 and DynamoDB is preserved (not rolled back)
- Manual intervention may be needed for complex scenarios

## Cleanup Operations

### When to Use Cleanup

Use cleanup when:
- Decommissioning an environment
- Removing test/development deployments
- Cleaning up after failed deployments
- Reducing AWS costs by removing unused resources

### Cleanup Script Usage

```bash
# Basic cleanup (preserves data)
bash scripts/cleanup.sh --environment dev

# Preview cleanup without executing
bash scripts/cleanup.sh --environment dev --dry-run

# Cleanup and delete data
bash scripts/cleanup.sh --environment dev --no-preserve-data

# Complete removal including logs
bash scripts/cleanup.sh --environment dev --force-delete --delete-logs

# Cleanup specific environment
bash scripts/cleanup.sh --environment staging --config config/staging.yaml
```

### Cleanup Options

| Option | Description | Default |
|--------|-------------|---------|
| `--environment, -e` | Environment name | dev |
| `--config, -c` | Path to config file | config/ENV.yaml |
| `--no-preserve-data` | Delete S3 and DynamoDB data | false (preserve) |
| `--force-delete` | Force delete all resources | false |
| `--delete-logs` | Delete CloudWatch log groups | false |
| `--dry-run` | Preview without executing | false |

### Cleanup Process

The cleanup script performs these steps:

1. **Load Configuration** - Reads environment configuration
2. **List Resources** - Identifies all resources to delete
3. **Confirm Deletion** - Prompts for confirmation
4. **Delete Stacks** - Removes CloudFormation stacks in order
5. **Delete Data** - Removes S3/DynamoDB if not preserving
6. **Delete Logs** - Removes log groups if requested
7. **Verify Cleanup** - Confirms all resources removed

### Cleanup Modes

#### Standard Cleanup (Default)

Preserves data resources:
```bash
bash scripts/cleanup.sh --environment dev
```

**Deletes:**
- Lambda functions
- API Gateway
- Cognito User Pools
- VPC and networking
- IAM roles
- CloudWatch alarms

**Preserves:**
- S3 buckets and data
- DynamoDB tables and data
- CloudWatch log groups
- KMS keys

#### Cleanup with Data Deletion

Removes data resources:
```bash
bash scripts/cleanup.sh --environment dev --no-preserve-data
```

**Additionally Deletes:**
- S3 buckets (after emptying)
- DynamoDB tables
- All stored data

**Still Preserves:**
- CloudWatch log groups (unless --delete-logs)

#### Force Delete (Complete Removal)

Removes everything:
```bash
bash scripts/cleanup.sh --environment dev --force-delete --delete-logs
```

**Deletes Everything:**
- All infrastructure
- All data
- All logs
- Complete environment removal

## Data Preservation

### Why Preserve Data?

Data preservation is enabled by default to:
- Prevent accidental data loss
- Allow infrastructure recreation without data loss
- Support testing and development workflows
- Comply with data retention policies

### What Gets Preserved?

#### S3 Buckets
- Data bucket (supply chain data)
- Athena results bucket
- All object versions (if versioning enabled)

#### DynamoDB Tables
- Session table
- Memory table
- Conversation history table
- All data and indexes

#### CloudWatch Logs
- Lambda function logs
- API Gateway logs
- VPC Flow Logs

### Removal Policies

The application uses CDK removal policies:

| Resource Type | Production | Staging | Development |
|--------------|------------|---------|-------------|
| S3 Buckets | RETAIN | RETAIN | DESTROY |
| DynamoDB Tables | RETAIN | RETAIN | DESTROY |
| CloudWatch Logs | RETAIN | DESTROY | DESTROY |
| Lambda Functions | DESTROY | DESTROY | DESTROY |
| VPC | DESTROY | DESTROY | DESTROY |

### Manual Data Deletion

If you need to manually delete preserved resources:

#### Delete S3 Buckets
```bash
# List buckets
aws s3 ls | grep sc-agent

# Empty and delete bucket
aws s3 rm s3://BUCKET-NAME --recursive
aws s3 rb s3://BUCKET-NAME
```

#### Delete DynamoDB Tables
```bash
# List tables
aws dynamodb list-tables --query 'TableNames[?contains(@, `sc-agent`)]'

# Delete table
aws dynamodb delete-table --table-name TABLE-NAME
```

#### Delete CloudWatch Log Groups
```bash
# List log groups
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/sc-agent

# Delete log group
aws logs delete-log-group --log-group-name LOG-GROUP-NAME
```

## Best Practices

### Before Rollback

1. **Backup Current State** - Take snapshots if needed
2. **Review Changes** - Understand what will be reverted
3. **Test in Lower Environment** - Try rollback in dev/staging first
4. **Notify Team** - Inform stakeholders of rollback
5. **Check Dependencies** - Ensure no external dependencies on current version

### Before Cleanup

1. **Verify Environment** - Double-check you're cleaning the right environment
2. **Backup Data** - Export critical data if not preserving
3. **Check Dependencies** - Ensure no other systems depend on resources
4. **Review Costs** - Understand cost implications of preserved resources
5. **Document Reason** - Record why cleanup is being performed

### During Operations

1. **Use Dry-Run First** - Always preview changes before executing
2. **Monitor Progress** - Watch CloudFormation console for status
3. **Check for Errors** - Review any error messages carefully
4. **Keep Logs** - Save script output for troubleshooting
5. **Verify Completion** - Confirm all expected resources are affected

### After Operations

1. **Verify State** - Check AWS console to confirm changes
2. **Test Functionality** - Verify application works (rollback) or is gone (cleanup)
3. **Update Documentation** - Record what was done
4. **Review Costs** - Monitor AWS billing for expected changes
5. **Clean Up Artifacts** - Remove any temporary files or backups

## Troubleshooting

### Rollback Issues

#### Stack Not Found
```
Error: Stack does not exist
```

**Solution:** Stack may have been deleted. Check CloudFormation console.

#### No Previous Version
```
Error: No version history found
```

**Solution:** This is the first deployment. Cannot rollback.

#### Rollback Failed
```
Error: Stack rollback failed
```

**Solutions:**
1. Check CloudFormation events for specific error
2. Try manual rollback in CloudFormation console
3. Use cleanup script if rollback not possible
4. Contact AWS support for stuck stacks

### Cleanup Issues

#### Stack Deletion Failed
```
Error: Failed to delete stack
```

**Solutions:**
1. Check for resources with RETAIN policy
2. Manually delete retained resources first
3. Use force-delete option
4. Check IAM permissions

#### S3 Bucket Not Empty
```
Error: Bucket not empty
```

**Solution:** Script should empty bucket first. If it fails:
```bash
aws s3 rm s3://BUCKET-NAME --recursive
aws s3api delete-bucket --bucket BUCKET-NAME
```

#### DynamoDB Table Deletion Protection
```
Error: Table has deletion protection enabled
```

**Solution:** Script disables protection. If it fails:
```bash
aws dynamodb update-table \
  --table-name TABLE-NAME \
  --no-deletion-protection-enabled

aws dynamodb delete-table --table-name TABLE-NAME
```

#### Permission Denied
```
Error: Access Denied
```

**Solutions:**
1. Check IAM permissions for your user/role
2. Ensure you have CloudFormation delete permissions
3. Verify S3 and DynamoDB delete permissions
4. Check for SCPs (Service Control Policies) blocking deletion

### Recovery Procedures

#### Partial Cleanup
If cleanup fails partway through:

1. **Identify Remaining Resources**
   ```bash
   bash scripts/cleanup.sh --environment ENV --dry-run
   ```

2. **Manual Cleanup**
   - Delete remaining stacks in CloudFormation console
   - Delete S3 buckets manually
   - Delete DynamoDB tables manually

3. **Verify Complete**
   ```bash
   # Check for remaining resources
   aws cloudformation list-stacks --query 'StackSummaries[?contains(StackName, `sc-agent`)]'
   aws s3 ls | grep sc-agent
   aws dynamodb list-tables --query 'TableNames[?contains(@, `sc-agent`)]'
   ```

#### Failed Rollback Recovery

If rollback fails and stack is in bad state:

1. **Try Continuing Update**
   ```bash
   aws cloudformation continue-update-rollback --stack-name STACK-NAME
   ```

2. **Delete and Redeploy**
   ```bash
   bash scripts/cleanup.sh --environment ENV
   bash deploy.sh --environment ENV
   ```

3. **Contact AWS Support**
   - For stuck stacks
   - For resources that won't delete
   - For permission issues

## Safety Checklist

Before running cleanup or rollback:

- [ ] Verified correct environment
- [ ] Ran dry-run to preview changes
- [ ] Backed up critical data (if needed)
- [ ] Notified team members
- [ ] Checked for dependent systems
- [ ] Reviewed cost implications
- [ ] Have rollback plan (for cleanup)
- [ ] Have access to AWS console
- [ ] Have necessary IAM permissions
- [ ] Documented reason for operation

## Examples

### Development Environment Cleanup
```bash
# Quick cleanup of dev environment (no data preservation needed)
bash scripts/cleanup.sh \
  --environment dev \
  --force-delete \
  --delete-logs
```

### Production Rollback
```bash
# Safe rollback of production with preview
bash scripts/rollback.sh \
  --environment prod \
  --dry-run

# Execute after review
bash scripts/rollback.sh \
  --environment prod
```

### Staging Cleanup with Data Preservation
```bash
# Cleanup staging but keep data for analysis
bash scripts/cleanup.sh \
  --environment staging \
  --delete-logs
```

### Emergency Cleanup
```bash
# Complete removal in emergency
bash scripts/cleanup.sh \
  --environment dev \
  --force-delete \
  --delete-logs \
  --auto-approve  # Use with caution!
```

## Additional Resources

- [Deployment Guide](COMPLETE_DEPLOYMENT_GUIDE.md)
- [Configuration Reference](../config/README.md)
- [Troubleshooting Guide](DEPLOYMENT_QUICK_REFERENCE.md)
- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
