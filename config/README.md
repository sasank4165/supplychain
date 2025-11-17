# Configuration Management

This directory contains environment-specific configuration files for the Supply Chain Agentic AI Application.

## Overview

The configuration system provides:
- **Environment-specific settings**: Separate configs for dev, staging, and prod
- **Schema validation**: JSON Schema ensures configuration correctness
- **Dynamic resource naming**: Consistent naming conventions across all AWS resources
- **Environment variable overrides**: Override any config value via environment variables
- **Auto-detection**: Automatically detect AWS account ID and region

## Configuration Files

- `schema.json` - JSON Schema defining valid configuration structure
- `dev.yaml` - Development environment configuration (cost-optimized)
- `staging.yaml` - Staging environment configuration (production-like)
- `prod.yaml` - Production environment configuration (high availability)

## Usage

### Loading Configuration

```python
from config_manager import ConfigurationManager, ResourceNamer

# Load configuration for specific environment
config = ConfigurationManager(environment='dev')

# Access configuration values
lambda_memory = config.get('resources.lambda.memory_mb')
region = config.get('environment.region')

# Get required values (raises error if missing)
prefix = config.get_required('project.prefix')

# Get all tags
tags = config.get_tags()
```

### Resource Naming

```python
from config_manager import ResourceNamer

# Initialize resource namer
namer = ResourceNamer(config)

# Generate resource names
bucket_name = namer.s3_bucket('data')
# Output: sc-agent-dev-data-123456789012-us-east-1

table_name = namer.dynamodb_table('sessions')
# Output: sc-agent-dev-sessions

function_name = namer.lambda_function('sql-executor')
# Output: sc-agent-dev-sql-executor

role_name = namer.iam_role('lambda-exec')
# Output: sc-agent-dev-lambda-exec
```

### Environment Variables

Set the environment to use:
```bash
export ENVIRONMENT=dev
```

Override specific configuration values:
```bash
# Override Lambda memory
export SC_AGENT_RESOURCES_LAMBDA_MEMORY_MB=1024

# Override region
export SC_AGENT_ENVIRONMENT_REGION=us-west-2

# Override feature flags
export SC_AGENT_FEATURES_VPC_ENABLED=true
```

## Configuration Structure

### Environment Section
```yaml
environment:
  name: dev              # Environment name (dev, staging, prod)
  account_id: auto       # AWS account ID or 'auto' for auto-detection
  region: us-east-1      # AWS region
```

### Project Section
```yaml
project:
  name: supply-chain-agent
  prefix: sc-agent-dev   # Resource name prefix
  owner: platform-team
  cost_center: supply-chain
```

### Features Section
```yaml
features:
  vpc_enabled: false     # Deploy Lambda in VPC
  waf_enabled: false     # Enable WAF for API Gateway
  multi_az: false        # Multi-AZ deployment
  xray_tracing: false    # Enable X-Ray tracing
  backup_enabled: true   # Enable automated backups
```

### Resources Section
```yaml
resources:
  lambda:
    memory_mb: 512
    timeout_seconds: 180
    reserved_concurrency: 10
    architecture: arm64
  
  dynamodb:
    billing_mode: PAY_PER_REQUEST
    point_in_time_recovery: true
  
  logs:
    retention_days: 7
  
  backup:
    retention_days: 7
```

### Agents Section
```yaml
agents:
  default_model: anthropic.claude-3-5-sonnet-20241022-v2:0
  context_window_size: 10
  conversation_retention_days: 30
  
  sql_agent:
    enabled: true
    model: anthropic.claude-3-5-sonnet-20241022-v2:0
    timeout_seconds: 60
```

## Validation

Validate configuration before deployment:

```bash
# Validate specific environment
python scripts/validate-config.py --environment dev

# Validate all environments
python scripts/validate-config.py --all

# Validate with AWS connectivity checks
python scripts/validate-config.py --environment prod --check-aws
```

The validation script checks:
- ✅ YAML syntax
- ✅ JSON schema compliance
- ✅ Resource naming conventions
- ✅ Feature flag combinations
- ✅ Resource sizing appropriateness
- ✅ Required tags
- ✅ AWS connectivity (optional)
- ✅ Bedrock model access (optional)

## Environment-Specific Recommendations

### Development (dev.yaml)
- **Purpose**: Local development and testing
- **Cost**: Optimized for minimal cost
- **Features**: Minimal features enabled
- **Resources**: Small instance sizes
- **Retention**: Short retention periods (3-7 days)

### Staging (staging.yaml)
- **Purpose**: Pre-production testing
- **Cost**: Balanced cost and features
- **Features**: Production-like setup
- **Resources**: Medium instance sizes
- **Retention**: Medium retention periods (14 days)

### Production (prod.yaml)
- **Purpose**: Live production workloads
- **Cost**: Optimized for reliability
- **Features**: All security and HA features enabled
- **Resources**: Production-grade sizing
- **Retention**: Extended retention periods (30+ days)

## Adding New Configuration Parameters

1. Update `schema.json` with new parameter definition
2. Add parameter to environment YAML files with appropriate values
3. Update this README with documentation
4. Add validation logic to `validate-config.py` if needed

## Troubleshooting

### Configuration file not found
```
ConfigurationError: Configuration file not found: config/dev.yaml
```
**Solution**: Ensure you're running from the project root directory and the config file exists.

### Schema validation failed
```
ConfigurationError: Configuration validation failed: 'name' is a required property
```
**Solution**: Check that all required fields are present in your configuration file.

### AWS account ID auto-detection failed
```
ConfigurationError: Failed to auto-detect AWS account ID
```
**Solution**: Configure AWS credentials or set `account_id` explicitly in the config file.

### Invalid resource name
```
ERROR: S3 bucket name too long: sc-agent-dev-data-123456789012-us-east-1 (65 chars)
```
**Solution**: Shorten the project prefix in the configuration.

## Best Practices

1. **Never commit secrets**: Use AWS Secrets Manager for sensitive values
2. **Use environment variables**: Override configs without modifying files
3. **Validate before deploy**: Always run validation script before deployment
4. **Document changes**: Update this README when adding new parameters
5. **Test in dev first**: Validate configuration changes in dev before prod
6. **Use consistent naming**: Follow the established naming conventions
7. **Tag everything**: Ensure all resources have proper tags for cost tracking

## Related Documentation

- [Deployment Guide](../DEPLOYMENT.md)
- [Architecture Overview](../ARCHITECTURE.md)
- [CDK Configuration](../cdk/README.md)
