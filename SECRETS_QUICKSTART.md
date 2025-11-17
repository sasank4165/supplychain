# Secrets Management Quick Start

Quick reference for using the new secrets and parameter management system.

## For Local Development

### 1. Generate .env File

```bash
python scripts/setup-local-env.py --environment dev
```

### 2. Update Placeholder Values

Edit `.env` and replace PLACEHOLDER values:

```bash
# Edit the file
nano .env

# Or use your preferred editor
code .env
```

### 3. Run Your Application

The `.env` file will be automatically loaded:

```bash
python app.py
```

## For AWS Deployment

### 1. Initialize Secrets and Parameters

```bash
# Preview what will be created
python scripts/init-secrets.py --environment dev --dry-run

# Create secrets and parameters
python scripts/init-secrets.py --environment dev
```

### 2. Update Placeholder Secrets

```bash
# List secrets
aws secretsmanager list-secrets --filters Key=name,Values=sc-agent-dev

# Update a secret
aws secretsmanager update-secret \
  --secret-id sc-agent-dev/api/external-api-key \
  --secret-string "your-actual-api-key"
```

### 3. Deploy with CDK

The CDK will automatically set environment variables for Lambda functions.

## Using in Code

### Get Configuration Values

```python
from config_manager import ConfigurationManager

config = ConfigurationManager(environment='dev')

# Get from YAML config
database = config.get('data.athena_database')
model = config.get('agents.default_model')

# Get from Parameter Store
param_value = config.get_parameter('database-name')

# Get from Secrets Manager
api_key = config.get_secret('api-key')
```

### Get Environment Variables

```python
import os

# Direct access
region = os.getenv('AWS_REGION')
database = os.getenv('ATHENA_DATABASE')

# With validation
from config import get_required_env

database = get_required_env('ATHENA_DATABASE', 'Athena database name')
```

### In Lambda Functions

```python
import os

# Load at module level
ATHENA_DATABASE = os.environ.get('ATHENA_DATABASE')
ATHENA_OUTPUT = os.environ.get('ATHENA_OUTPUT_LOCATION')

# Validate
if not ATHENA_DATABASE or not ATHENA_OUTPUT:
    raise ValueError("Required environment variables not set")
```

## Environment Variables Reference

### Required Variables

```bash
AWS_REGION=us-east-1
ATHENA_DATABASE=supply_chain_db
ATHENA_OUTPUT_LOCATION=s3://your-bucket/
```

### Optional Variables

```bash
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
USER_POOL_ID=us-east-1_XXXXXXXXX
USER_POOL_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
```

## Troubleshooting

### "Required environment variable not set"

**Solution:** Create a `.env` file or set the environment variable:

```bash
# Option 1: Generate .env file
python scripts/setup-local-env.py --environment dev

# Option 2: Set manually
export ATHENA_DATABASE=supply_chain_db
```

### "Secret not found"

**Solution:** Initialize secrets:

```bash
python scripts/init-secrets.py --environment dev
```

### "Access denied to secret"

**Solution:** Check IAM permissions:

```bash
# Verify your AWS identity
aws sts get-caller-identity

# Check secret permissions
aws secretsmanager describe-secret --secret-id sc-agent-dev/api-key
```

## Best Practices

1. **Never commit .env files** - They're in .gitignore
2. **Use Secrets Manager for sensitive data** - API keys, passwords, tokens
3. **Use Parameter Store for configuration** - Database names, bucket names
4. **Use YAML files for non-sensitive config** - Feature flags, resource sizes
5. **Validate environment variables at startup** - Fail fast with clear errors

## Quick Commands

```bash
# Generate .env for local dev
python scripts/setup-local-env.py --environment dev

# Initialize AWS secrets/parameters
python scripts/init-secrets.py --environment dev

# List all secrets
aws secretsmanager list-secrets

# List all parameters
aws ssm describe-parameters

# Update a secret
aws secretsmanager update-secret --secret-id <name> --secret-string <value>

# Update a parameter
aws ssm put-parameter --name <name> --value <value> --overwrite
```

## More Information

See [SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md) for comprehensive documentation.
