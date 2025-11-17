# Secrets and Parameter Management Guide

This guide explains how to manage secrets and configuration parameters for the Supply Chain Agentic AI Application.

## Overview

The application uses a multi-layered approach to configuration management:

1. **YAML Configuration Files** - Non-sensitive configuration (in `config/` directory)
2. **AWS Parameter Store** - Non-sensitive runtime configuration
3. **AWS Secrets Manager** - Sensitive data (credentials, API keys)
4. **Environment Variables** - Local development and overrides

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Code                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         ConfigurationManager                            │ │
│  │  - Loads YAML config                                   │ │
│  │  - Validates against schema                            │ │
│  │  - Provides unified access                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         SecretsManager                                  │ │
│  │  - Retrieves from Secrets Manager                      │ │
│  │  - Retrieves from Parameter Store                      │ │
│  │  - Falls back to environment variables                 │ │
│  │  - Caches values for performance                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓
    ┌──────────────────────┬──────────────────────┐
    ↓                      ↓                      ↓
┌─────────┐         ┌─────────────┐      ┌──────────────┐
│ Secrets │         │  Parameter  │      │ Environment  │
│ Manager │         │    Store    │      │  Variables   │
└─────────┘         └─────────────┘      └──────────────┘
```

## Components

### 1. SecretsManager Class

Located in `secrets_manager.py`, this class provides:

- **get_secret(name)** - Retrieve secret from Secrets Manager
- **get_parameter(name)** - Retrieve parameter from Parameter Store
- **put_secret(name, value)** - Store secret in Secrets Manager
- **put_parameter(name, value)** - Store parameter in Parameter Store

### 2. ConfigurationManager Integration

The `ConfigurationManager` class integrates with `SecretsManager`:

```python
from config_manager import ConfigurationManager

config = ConfigurationManager(environment='dev')

# Get configuration value
database = config.get('data.athena_database')

# Get secret
api_key = config.get_secret('api-key')

# Get parameter
db_name = config.get_parameter('database-name')
```

### 3. Environment Variable Support

For local development, you can use environment variables instead of AWS services:

```bash
# Secrets (prefix: SECRET_)
export SECRET_API_KEY="my-secret-key"

# Parameters (prefix: PARAM_)
export PARAM_DATABASE_NAME="my-database"
```

## Setup Instructions

### For New Environments

#### 1. Initialize Secrets and Parameters

Use the initialization script to create all required secrets and parameters:

```bash
# Dry run to see what would be created
python scripts/init-secrets.py --environment dev --dry-run

# Create secrets and parameters
python scripts/init-secrets.py --environment dev

# Force overwrite existing values
python scripts/init-secrets.py --environment dev --force
```

This creates:

**Parameters in Parameter Store:**
- `/sc-agent-dev/athena/database`
- `/sc-agent-dev/athena/output-location`
- `/sc-agent-dev/dynamodb/session-table`
- `/sc-agent-dev/lambda/sql-executor`
- And more...

**Secrets in Secrets Manager:**
- `sc-agent-dev/database/connection-string`
- `sc-agent-dev/api/external-api-key`
- `sc-agent-dev/cognito/user-pool-id`
- And more...

#### 2. Update Placeholder Secrets

The initialization script creates placeholder secrets. Update them with actual values:

```bash
# List secrets
aws secretsmanager list-secrets --filters Key=name,Values=sc-agent-dev

# Update a secret
aws secretsmanager update-secret \
  --secret-id sc-agent-dev/api/external-api-key \
  --secret-string "actual-api-key-value"
```

### For Local Development

#### Option 1: Use .env Files

Generate a .env file from your configuration:

```bash
# Generate .env file
python scripts/setup-local-env.py --environment dev

# Review and update the file
cat .env

# Update placeholder values
nano .env
```

Load the .env file in your application:

```python
from env_loader import load_env_auto

# Automatically loads .env or .env.{environment}
load_env_auto()

# Or load specific file
from env_loader import load_env_file
load_env_file('.env.dev')
```

#### Option 2: Set Environment Variables Manually

```bash
# Linux/Mac
export AWS_REGION=us-east-1
export ATHENA_DATABASE=supply_chain_db
export ATHENA_OUTPUT_LOCATION=s3://my-bucket/

# Windows (PowerShell)
$env:AWS_REGION="us-east-1"
$env:ATHENA_DATABASE="supply_chain_db"
```

## Usage in Application Code

### Lambda Functions

Lambda functions automatically receive environment variables from the CDK deployment:

```python
import os

# Load from environment variables
ATHENA_DATABASE = os.environ.get('ATHENA_DATABASE')
ATHENA_OUTPUT = os.environ.get('ATHENA_OUTPUT_LOCATION')

# Validate required variables
if not ATHENA_DATABASE or not ATHENA_OUTPUT:
    raise ValueError("Required environment variables not set")
```

### Application Code

Use ConfigurationManager for centralized access:

```python
from config_manager import ConfigurationManager, ResourceNamer

# Initialize
config = ConfigurationManager(environment='dev')
namer = ResourceNamer(config)

# Get configuration values
database = config.get('data.athena_database')
model_id = config.get('agents.default_model')

# Get resource names
bucket_name = namer.s3_bucket('data')
table_name = namer.dynamodb_table('sessions')

# Get secrets (if needed)
api_key = config.get_secret('api-key')
```

### Agents and Orchestrator

```python
from config_manager import ConfigurationManager

config = ConfigurationManager()

# Use configuration in agents
bedrock_model = config.get('agents.default_model')
timeout = config.get('agents.sql_agent.timeout_seconds', 60)
```

## Security Best Practices

### 1. Never Hardcode Secrets

❌ **Bad:**
```python
API_KEY = "sk-1234567890abcdef"
DATABASE_URL = "postgresql://user:password@host/db"
```

✅ **Good:**
```python
from secrets_manager import get_secret

API_KEY = get_secret('api-key')
DATABASE_URL = get_secret('database/connection-string')
```

### 2. Use Appropriate Storage

| Type | Storage | Example |
|------|---------|---------|
| Sensitive | Secrets Manager | API keys, passwords, connection strings |
| Non-sensitive | Parameter Store | Database names, S3 bucket names |
| Configuration | YAML files | Feature flags, resource sizes |

### 3. Protect .env Files

Add to `.gitignore`:
```
.env
.env.*
!.env.example
```

### 4. Use IAM Permissions

Restrict access to secrets and parameters:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:sc-agent-dev/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/sc-agent-dev/*"
    }
  ]
}
```

### 5. Enable Secret Rotation

For production secrets, enable automatic rotation:

```bash
aws secretsmanager rotate-secret \
  --secret-id sc-agent-prod/database/connection-string \
  --rotation-lambda-arn arn:aws:lambda:region:account:function:rotation-function \
  --rotation-rules AutomaticallyAfterDays=30
```

## Troubleshooting

### Secret Not Found

```
SecretsError: Secret not found: sc-agent-dev/api-key
```

**Solution:**
1. Check the secret exists: `aws secretsmanager list-secrets`
2. Verify the prefix matches your configuration
3. Check IAM permissions

### Access Denied

```
SecretsError: Access denied to secret: sc-agent-dev/api-key
```

**Solution:**
1. Verify IAM role/user has `secretsmanager:GetSecretValue` permission
2. Check resource-based policies on the secret
3. Verify you're using the correct AWS credentials

### Environment Variable Not Set

```
ConfigurationError: Required environment variable not set: ATHENA_DATABASE
```

**Solution:**
1. For local development: Create .env file with `python scripts/setup-local-env.py`
2. For Lambda: Ensure CDK sets environment variables
3. For production: Verify deployment configuration

### SecretsManager Not Available

```
Warning: Failed to initialize SecretsManager: ...
```

**Solution:**
1. Install boto3: `pip install boto3`
2. Configure AWS credentials: `aws configure`
3. For local development: Use .env files as fallback

## Migration from Hardcoded Values

### Step 1: Identify Hardcoded Values

Search for hardcoded values in your codebase:

```bash
# Find potential hardcoded values
grep -r "aws-gpl-cog-sc-db" .
grep -r "s3://.*bucket" .
```

### Step 2: Move to Environment Variables

Replace hardcoded values with environment variable lookups:

```python
# Before
ATHENA_DATABASE = "aws-gpl-cog-sc-db"

# After
ATHENA_DATABASE = os.environ.get('ATHENA_DATABASE')
```

### Step 3: Update Configuration Files

Add values to your YAML configuration:

```yaml
data:
  athena_database: "supply_chain_db"
  glue_catalog: "AwsDataCatalog"
```

### Step 4: Initialize Secrets

Run the initialization script:

```bash
python scripts/init-secrets.py --environment dev
```

### Step 5: Update Deployment

Ensure CDK sets environment variables for Lambda functions:

```python
lambda_function = lambda_.Function(
    self, "MyFunction",
    environment={
        'ATHENA_DATABASE': config.get('data.athena_database'),
        'ATHENA_OUTPUT_LOCATION': f"s3://{bucket.bucket_name}/"
    }
)
```

## Reference

### Environment Variable Naming Conventions

| Prefix | Purpose | Example |
|--------|---------|---------|
| `AWS_` | AWS SDK configuration | `AWS_REGION` |
| `SC_AGENT_` | Application configuration | `SC_AGENT_PREFIX` |
| `SECRET_` | Local secret fallback | `SECRET_API_KEY` |
| `PARAM_` | Local parameter fallback | `PARAM_DATABASE_NAME` |

### Parameter Store Paths

All parameters use the pattern: `/{prefix}/{category}/{name}`

Examples:
- `/sc-agent-dev/athena/database`
- `/sc-agent-dev/lambda/sql-executor`
- `/sc-agent-prod/monitoring/alarm-email`

### Secrets Manager Names

All secrets use the pattern: `{prefix}/{category}/{name}`

Examples:
- `sc-agent-dev/database/connection-string`
- `sc-agent-dev/api/external-api-key`
- `sc-agent-prod/cognito/user-pool-id`

## Additional Resources

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [AWS Systems Manager Parameter Store Documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [python-dotenv Documentation](https://github.com/theskumar/python-dotenv)
