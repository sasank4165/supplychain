# Configuration Management Quick Start Guide

This guide will help you get started with the new configuration management system for the Supply Chain Agentic AI Application.

## What's New?

The application now uses a centralized configuration system that:
- ✅ Eliminates hardcoded values
- ✅ Supports multiple environments (dev, staging, prod)
- ✅ Provides dynamic resource naming
- ✅ Validates configuration before deployment
- ✅ Supports environment variable overrides

## Quick Start

### 1. Install Dependencies

```bash
pip install pyyaml jsonschema
```

### 2. Choose Your Environment

Set the environment you want to use:

```bash
# Windows
set ENVIRONMENT=dev

# Linux/Mac
export ENVIRONMENT=dev
```

### 3. Validate Configuration

Before deploying, validate your configuration:

```bash
# Windows
scripts\validate-config.bat dev

# Linux/Mac
python scripts/validate-config.py --environment dev
```

### 4. Use in Your Code

```python
from config_manager import ConfigurationManager, ResourceNamer

# Load configuration
config = ConfigurationManager(environment='dev')

# Access values
region = config.get('environment.region')
lambda_memory = config.get('resources.lambda.memory_mb')

# Generate resource names
namer = ResourceNamer(config)
bucket_name = namer.s3_bucket('data')
table_name = namer.dynamodb_table('sessions')
```

## Configuration Files

Three environment configurations are provided:

### Development (`config/dev.yaml`)
- **Purpose**: Local development and testing
- **Cost**: Minimal (optimized for cost)
- **Features**: Basic features only
- **Resources**: Small instance sizes

### Staging (`config/staging.yaml`)
- **Purpose**: Pre-production testing
- **Cost**: Moderate
- **Features**: Production-like setup
- **Resources**: Medium instance sizes

### Production (`config/prod.yaml`)
- **Purpose**: Live production workloads
- **Cost**: Optimized for reliability
- **Features**: All security and HA features
- **Resources**: Production-grade sizing

## Common Tasks

### Override Configuration Values

Use environment variables to override any configuration value:

```bash
# Override Lambda memory
export SC_AGENT_RESOURCES_LAMBDA_MEMORY_MB=1024

# Override region
export SC_AGENT_ENVIRONMENT_REGION=us-west-2

# Enable VPC
export SC_AGENT_FEATURES_VPC_ENABLED=true
```

### Add Custom Tags

Edit your environment's YAML file:

```yaml
tags:
  custom:
    Department: Operations
    Compliance: SOC2
    YourCustomTag: YourValue
```

### Change Resource Sizing

Edit the `resources` section in your environment's YAML file:

```yaml
resources:
  lambda:
    memory_mb: 1024        # Increase memory
    timeout_seconds: 300   # Increase timeout
    reserved_concurrency: 50  # Increase concurrency
```

### Enable/Disable Features

Edit the `features` section:

```yaml
features:
  vpc_enabled: true      # Enable VPC deployment
  waf_enabled: true      # Enable WAF protection
  multi_az: true         # Enable multi-AZ
  xray_tracing: true     # Enable X-Ray tracing
```

## Resource Naming Convention

All resources follow consistent naming patterns:

| Resource Type | Pattern | Example |
|--------------|---------|---------|
| S3 Bucket | `{prefix}-{purpose}-{account}-{region}` | `sc-agent-dev-data-123456789012-us-east-1` |
| DynamoDB Table | `{prefix}-{name}` | `sc-agent-dev-sessions` |
| Lambda Function | `{prefix}-{name}` | `sc-agent-dev-sql-executor` |
| IAM Role | `{prefix}-{purpose}` | `sc-agent-dev-lambda-exec` |

## Validation Checks

The validation script checks:

- ✅ YAML syntax correctness
- ✅ JSON schema compliance
- ✅ Resource naming conventions
- ✅ Feature flag combinations
- ✅ Resource sizing appropriateness
- ✅ Required tags present
- ✅ AWS connectivity (optional)
- ✅ Bedrock model access (optional)

## Examples

See `examples/config_usage_example.py` for comprehensive usage examples:

```bash
python examples/config_usage_example.py
```

## Troubleshooting

### Configuration file not found
**Problem**: `ConfigurationError: Configuration file not found`

**Solution**: Ensure you're in the project root directory and the config file exists in `config/` directory.

### AWS credentials not configured
**Problem**: `Failed to auto-detect AWS account ID`

**Solution**: Configure AWS credentials:
```bash
aws configure
```

Or set `account_id` explicitly in your config file instead of using `auto`.

### Schema validation failed
**Problem**: `Configuration validation failed`

**Solution**: Check that all required fields are present in your YAML file. Compare with the example configs.

### Python not found
**Problem**: `Python was not found`

**Solution**: Install Python 3.7+ from python.org or use your system's package manager.

## Migration from Old Config

If you're migrating from the old `config.py`:

### Old Way:
```python
from config import AWS_REGION, BEDROCK_MODEL_ID, DYNAMODB_SESSION_TABLE

region = AWS_REGION
model = BEDROCK_MODEL_ID
table = DYNAMODB_SESSION_TABLE
```

### New Way:
```python
from config_manager import ConfigurationManager, ResourceNamer

config = ConfigurationManager()
namer = ResourceNamer(config)

region = config.get('environment.region')
model = config.get('agents.default_model')
table = namer.dynamodb_table('sessions')
```

## Next Steps

1. **Review Configuration**: Check `config/dev.yaml` and adjust values for your needs
2. **Validate**: Run `scripts/validate-config.py --environment dev`
3. **Test Locally**: Use the configuration in your local development
4. **Deploy**: Use the configuration system in your CDK deployment

## Additional Resources

- [Configuration README](config/README.md) - Detailed documentation
- [Usage Examples](examples/config_usage_example.py) - Code examples
- [Validation Script](scripts/validate-config.py) - Validation tool
- [Schema Definition](config/schema.json) - Configuration schema

## Support

For issues or questions:
1. Check the [Configuration README](config/README.md)
2. Run validation script for detailed error messages
3. Review example configurations in `config/` directory
4. Check usage examples in `examples/config_usage_example.py`
