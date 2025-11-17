# Environment Variables - Quick Reference

Quick reference guide for environment variable configuration in the Supply Chain Agentic AI Application.

## Quick Start

### 1. Local Development Setup

```bash
# Copy example file
cp .env.example .env

# Edit with your values
vim .env

# Validate configuration
python startup_validator.py
```

### 2. Minimal Required Variables

```bash
# .env
AWS_REGION=us-east-1
USER_POOL_ID=us-east-1_XXXXXXXXX
USER_POOL_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 3. Run Application

```bash
# Streamlit UI
streamlit run app.py

# Or with explicit environment
ENVIRONMENT=dev streamlit run app.py
```

## Common Configurations

### Development Environment

```bash
ENVIRONMENT=dev
AWS_REGION=us-east-1
SC_AGENT_PREFIX=sc-agent-dev
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Production Environment

```bash
ENVIRONMENT=prod
AWS_REGION=us-east-1
SC_AGENT_PREFIX=sc-agent-prod
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

## Configuration Priority

The application loads configuration in this order (later overrides earlier):

1. **Configuration file** (`config/{environment}.yaml`)
2. **Environment variables** (direct)
3. **Environment variable overrides** (`SC_AGENT_*`)

## Override Examples

### Override Lambda Memory

```bash
export SC_AGENT_RESOURCES_LAMBDA_MEMORY_MB=1024
```

### Override Log Retention

```bash
export SC_AGENT_RESOURCES_LOGS_RETENTION_DAYS=30
```

### Enable Features

```bash
export SC_AGENT_FEATURES_VPC_ENABLED=true
export SC_AGENT_FEATURES_WAF_ENABLED=true
```

## Validation Commands

```bash
# Full validation
python startup_validator.py

# Skip AWS check (for local testing)
python startup_validator.py --no-aws

# Check resources exist
python startup_validator.py --check-resources

# Quiet mode
python startup_validator.py --quiet
```

## Troubleshooting

### Issue: Missing AWS_REGION

```bash
export AWS_REGION=us-east-1
```

### Issue: AWS Credentials Not Found

```bash
# Configure AWS CLI
aws configure

# Or set directly
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

### Issue: Configuration File Not Found

This is optional - the app works with environment variables only:

```bash
# Create config file (optional)
cp config/dev.yaml.example config/dev.yaml
```

### Issue: Resources Not Found

Deploy infrastructure first:

```bash
cd cdk
cdk deploy
```

## Environment Variable List

### Required
- `AWS_REGION` - AWS region

### Authentication
- `USER_POOL_ID` - Cognito User Pool ID
- `USER_POOL_CLIENT_ID` - Cognito Client ID

### Optional (with defaults)
- `ENVIRONMENT` - Environment name (default: `dev`)
- `SC_AGENT_PREFIX` - Resource prefix (default: `sc-agent`)
- `BEDROCK_MODEL_ID` - Model ID (default: Claude 3.5 Sonnet)
- `ATHENA_DATABASE` - Athena database name
- `ATHENA_OUTPUT_LOCATION` - S3 path for Athena results
- `DYNAMODB_SESSION_TABLE` - Session table name
- `DYNAMODB_MEMORY_TABLE` - Memory table name
- `DYNAMODB_CONVERSATION_TABLE` - Conversation table name
- `LAMBDA_INVENTORY_OPTIMIZER` - Inventory Lambda name
- `LAMBDA_LOGISTICS_OPTIMIZER` - Logistics Lambda name
- `LAMBDA_SUPPLIER_ANALYZER` - Supplier Lambda name

## Loading Mechanisms

### Automatic Loading (.env file)

The application automatically loads `.env` files:

```python
# Automatically loaded on import
from env_loader import load_env_auto
load_env_auto()  # Loads .env.{ENVIRONMENT} or .env
```

### Manual Loading

```python
from env_loader import load_env_file

# Load specific file
load_env_file('.env.dev')

# Override existing variables
load_env_file('.env.dev', override=True)
```

### Configuration Manager

```python
from config_manager import ConfigurationManager

# Load configuration
config = ConfigurationManager(environment='dev')

# Get values
region = config.get('environment.region')
prefix = config.get('project.prefix')
```

## Best Practices

### 1. Use .env for Local Development

```bash
# .env (not committed)
AWS_REGION=us-east-1
ENVIRONMENT=dev
# ... other variables
```

### 2. Use Configuration Files for Structure

```yaml
# config/dev.yaml
environment:
  name: dev
  region: us-east-1
resources:
  lambda:
    memory_mb: 512
```

### 3. Use Secrets Manager for Production

```python
from secrets_manager import SecretsManager

secrets = SecretsManager(region='us-east-1', prefix='sc-agent')
api_key = secrets.get_secret('api-key')
```

### 4. Validate Before Deployment

```bash
# Always validate before deploying
python startup_validator.py --check-resources
```

## See Also

- [Full Environment Variables Reference](../ENVIRONMENT_VARIABLES.md)
- [Configuration Management Guide](../CONFIGURATION_QUICKSTART.md)
- [Deployment Guide](../DEPLOYMENT.md)
- [Secrets Management](../SECRETS_MANAGEMENT.md)
