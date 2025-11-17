# CDK Configuration Guide

## Overview

The CDK infrastructure has been refactored to use a YAML-based configuration system that enables:
- Zero-code deployments to any AWS environment
- Environment-specific resource sizing and feature flags
- Dynamic resource naming with consistent conventions
- Conditional resource creation based on configuration

## Configuration System

### Configuration Files

Located in `../config/`:
- `dev.yaml` - Development environment
- `staging.yaml` - Staging environment  
- `prod.yaml` - Production environment
- `schema.json` - JSON Schema for validation

### Configuration Structure

```yaml
environment:
  name: dev|staging|prod
  account_id: "123456789012" or "auto"
  region: us-east-1

project:
  name: supply-chain-agent
  prefix: sc-agent-dev  # Used for all resource names
  owner: team-name
  cost_center: cost-center-name

features:
  vpc_enabled: true|false
  waf_enabled: true|false
  multi_az: true|false
  xray_tracing: true|false
  backup_enabled: true|false

resources:
  lambda:
    memory_mb: 512-10240
    timeout_seconds: 1-900
    reserved_concurrency: 0-1000
    architecture: arm64|x86_64
  
  dynamodb:
    billing_mode: PAY_PER_REQUEST|PROVISIONED
    point_in_time_recovery: true|false
  
  logs:
    retention_days: 1|3|5|7|14|30|60|90|120|150|180|365|...
  
  backup:
    retention_days: 1-365

networking:
  vpc_cidr: 10.0.0.0/16
  nat_gateways: 1-3

api:
  throttle_rate_limit: 1-10000
  throttle_burst_limit: 1-10000
  cors_origins:
    - http://localhost:8501

monitoring:
  alarm_email: email@example.com
  dashboard_enabled: true|false

agents:
  default_model: anthropic.claude-3-5-sonnet-20241022-v2:0
  context_window_size: 1-100
  conversation_retention_days: 1-365

data:
  athena_database: database_name
  glue_catalog: AwsDataCatalog

tags:
  custom:
    Key: Value
```

## Resource Naming Conventions

All resources follow consistent naming patterns:

| Resource Type | Pattern | Example |
|--------------|---------|---------|
| S3 Bucket | `{prefix}-{purpose}-{account-id}-{region}` | `sc-agent-dev-data-123456789012-us-east-1` |
| DynamoDB Table | `{prefix}-{name}` | `sc-agent-dev-sessions` |
| Lambda Function | `{prefix}-{name}` | `sc-agent-dev-inventory-optimizer` |
| IAM Role | `{prefix}-{purpose}` | `sc-agent-dev-lambda-exec` |
| API Gateway | `{prefix}-{name}` | `sc-agent-dev-api` |
| Log Group | `/aws/{service}/{prefix}-{name}` | `/aws/lambda/sc-agent-dev-sql-executor` |

## Feature Flags

### VPC Deployment (`vpc_enabled`)

**When enabled:**
- Creates NetworkStack with VPC, subnets, NAT gateways
- Lambda functions deployed in private subnets
- VPC endpoints for AWS services
- Security groups and network ACLs

**When disabled:**
- No NetworkStack created
- Lambda functions run without VPC
- Faster cold starts
- Lower costs (no NAT gateway charges)

**Recommendation:**
- Dev: `false` (faster, cheaper)
- Staging: `true` (production-like)
- Prod: `true` (security, isolation)

### WAF Protection (`waf_enabled`)

**When enabled:**
- WAF Web ACL attached to API Gateway
- Managed rule sets for common threats
- Rate limiting
- SQL injection protection

**When disabled:**
- No WAF costs
- API Gateway throttling only

**Recommendation:**
- Dev: `false`
- Staging: `true` (testing)
- Prod: `true` (security)

### Multi-AZ Deployment (`multi_az`)

**When enabled:**
- VPC spans 3 availability zones
- Multiple NAT gateways (one per AZ)
- Higher availability

**When disabled:**
- VPC spans 2 availability zones
- Single NAT gateway
- Lower costs

**Recommendation:**
- Dev: `false`
- Staging: `true`
- Prod: `true`

### X-Ray Tracing (`xray_tracing`)

**When enabled:**
- Lambda functions have X-Ray tracing enabled
- API Gateway tracing enabled
- Detailed performance insights

**When disabled:**
- No tracing overhead
- No X-Ray costs

**Recommendation:**
- Dev: `false`
- Staging: `true` (debugging)
- Prod: `true` (monitoring)

### Automated Backups (`backup_enabled`)

**When enabled:**
- Creates BackupStack
- Daily and weekly backup plans
- Automated retention management

**When disabled:**
- No BackupStack created
- No backup costs
- Manual backups only

**Recommendation:**
- Dev: `false`
- Staging: `true`
- Prod: `true`

## Environment-Specific Configurations

### Development Environment

**Optimized for:** Cost, speed, iteration
**Features:**
- No VPC (faster cold starts)
- No WAF
- Single AZ
- No X-Ray tracing
- No automated backups
- Minimal Lambda memory (512 MB)
- Short log retention (3 days)
- Low concurrency limits (5)

**Estimated Cost:** $50-100/month

### Staging Environment

**Optimized for:** Production-like testing
**Features:**
- VPC enabled
- WAF enabled
- Multi-AZ
- X-Ray tracing
- Automated backups
- Medium Lambda memory (1024 MB)
- Medium log retention (14 days)
- Medium concurrency (50)

**Estimated Cost:** $200-400/month

### Production Environment

**Optimized for:** Reliability, security, performance
**Features:**
- VPC enabled
- WAF enabled
- Multi-AZ
- X-Ray tracing
- Automated backups
- High Lambda memory (1024 MB)
- Extended log retention (30 days)
- High concurrency (100)

**Estimated Cost:** $500-1000+/month

## Deployment Workflow

### 1. Select Environment

```bash
export ENVIRONMENT=dev  # or staging, prod
```

### 2. Review Configuration

```bash
cat ../config/$ENVIRONMENT.yaml
```

### 3. Validate Configuration

```bash
python ../scripts/validate-config.py --environment $ENVIRONMENT
```

### 4. Synthesize CloudFormation

```bash
cd cdk
cdk synth --context environment=$ENVIRONMENT
```

### 5. Review Changes

```bash
cdk diff --context environment=$ENVIRONMENT
```

### 6. Deploy

```bash
cdk deploy --all --context environment=$ENVIRONMENT
```

## Customization

### Override Configuration Values

**Via Environment Variables:**
```bash
export SC_AGENT_RESOURCES_LAMBDA_MEMORY_MB=2048
export SC_AGENT_FEATURES_XRAY_TRACING=true
cdk deploy --all --context environment=dev
```

**Via YAML File:**
Edit `config/dev.yaml` and redeploy.

### Add Custom Tags

```yaml
tags:
  custom:
    Department: Engineering
    Project: SupplyChain
    Compliance: SOC2
    Owner: platform-team
```

### Change Resource Sizing

```yaml
resources:
  lambda:
    memory_mb: 2048  # Increase for better performance
    timeout_seconds: 600  # Increase for long-running tasks
    reserved_concurrency: 200  # Increase for high traffic
```

## Conditional Stack Creation

Stacks are created based on configuration:

| Stack | Condition | Configuration |
|-------|-----------|---------------|
| NetworkStack | `vpc_enabled: true` | `features.vpc_enabled` |
| SecurityStack | Always | N/A |
| DataStack | Always | N/A |
| SupplyChainAgentStack | Always | N/A |
| MonitoringStack | `dashboard_enabled: true` | `monitoring.dashboard_enabled` |
| BackupStack | `backup_enabled: true` | `features.backup_enabled` |

## Troubleshooting

### Configuration Validation Errors

**Error:** "Required configuration key not found"
**Solution:** Ensure all required fields are present in YAML file

**Error:** "Invalid value for field"
**Solution:** Check schema.json for valid values

### Account ID Auto-Detection

**Error:** "Failed to auto-detect AWS account ID"
**Solution:** 
1. Ensure AWS credentials are configured: `aws sts get-caller-identity`
2. Or set `account_id` explicitly in YAML

### VPC Deployment Issues

**Error:** "Insufficient IP addresses"
**Solution:** Use larger CIDR block (e.g., /16 instead of /24)

**Error:** "NAT Gateway limit exceeded"
**Solution:** Request service quota increase or reduce `nat_gateways`

### Lambda Cold Starts

**Issue:** Slow Lambda cold starts
**Solution:**
1. Disable VPC for dev: `vpc_enabled: false`
2. Use ARM64 architecture: `architecture: arm64`
3. Reduce memory if possible
4. Consider provisioned concurrency (prod only)

## Best Practices

1. **Use separate AWS accounts** for dev, staging, prod
2. **Test in dev first** before deploying to higher environments
3. **Review diffs** before applying: `cdk diff`
4. **Enable backups** for production
5. **Monitor costs** using cost allocation tags
6. **Rotate secrets** regularly
7. **Review IAM policies** for least privilege
8. **Use ARM64** for cost savings (20% cheaper)
9. **Set appropriate retention** based on compliance needs
10. **Tag all resources** for cost tracking

## Security Considerations

- All data encrypted at rest (KMS)
- All data encrypted in transit (TLS 1.2+)
- Secrets stored in Secrets Manager
- IAM roles follow least privilege
- VPC isolation (when enabled)
- WAF protection (when enabled)
- MFA for Cognito users
- CloudWatch Logs for audit trail

## Cost Optimization

- Use `arm64` architecture (20% cheaper)
- Disable VPC for dev (no NAT costs)
- Use short retention for dev (lower storage costs)
- Use `PAY_PER_REQUEST` for variable workloads
- Set appropriate concurrency limits
- Use S3 lifecycle policies
- Monitor and optimize based on usage

## Support

For issues or questions:
1. Check configuration validation
2. Review CloudWatch logs
3. Check CDK synthesis output
4. Consult AWS documentation
5. Review this guide
