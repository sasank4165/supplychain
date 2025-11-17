# Environment Variables Reference

This document provides a comprehensive reference for all environment variables used by the Supply Chain Agentic AI Application.

## Overview

The application uses environment variables for all configuration to enable deployment across different AWS accounts, regions, and environments without code changes. Configuration can be provided through:

1. **Environment variables** - Set directly in your shell or deployment system
2. **.env files** - For local development (automatically loaded)
3. **Configuration files** - YAML files in `config/` directory (optional, provides additional structure)
4. **AWS Secrets Manager / Parameter Store** - For sensitive values in production

## Required Environment Variables

These variables **must** be set for the application to function:

### AWS Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for all services | `us-east-1` |

### Authentication (for Streamlit UI)

| Variable | Description | Example |
|----------|-------------|---------|
| `USER_POOL_ID` | Cognito User Pool ID | `us-east-1_XXXXXXXXX` |
| `USER_POOL_CLIENT_ID` | Cognito User Pool Client ID | `XXXXXXXXXXXXXXXXXXXXXXXXXX` |

## Optional Environment Variables

These variables have defaults but should be set for production deployments:

### General Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENVIRONMENT` | Environment name | `dev` | `dev`, `staging`, `prod` |
| `SC_AGENT_PREFIX` | Prefix for resource naming | `sc-agent` | `mycompany-sc-agent` |

### Amazon Bedrock

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `BEDROCK_MODEL_ID` | Bedrock model ID | `anthropic.claude-3-5-sonnet-20241022-v2:0` | `anthropic.claude-3-haiku-20240307-v1:0` |

### Amazon Athena

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ATHENA_DATABASE` | Athena database name | *(empty)* | `supply_chain_db` |
| `ATHENA_CATALOG` | Athena data catalog | `AwsDataCatalog` | `AwsDataCatalog` |
| `ATHENA_OUTPUT_LOCATION` | S3 location for query results | *(empty)* | `s3://my-bucket/athena-results/` |

### DynamoDB Tables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DYNAMODB_SESSION_TABLE` | Session storage table | *(empty)* | `sc-agent-sessions` |
| `DYNAMODB_MEMORY_TABLE` | Memory storage table | *(empty)* | `sc-agent-memory` |
| `DYNAMODB_CONVERSATION_TABLE` | Conversation history table | *(empty)* | `sc-agent-conversation` |

### Lambda Functions

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LAMBDA_SQL_EXECUTOR` | SQL executor function | *(empty)* | `sc-agent-sql-executor` |
| `LAMBDA_INVENTORY_OPTIMIZER` | Inventory optimizer function | *(empty)* | `sc-agent-inventory-optimizer` |
| `LAMBDA_LOGISTICS_OPTIMIZER` | Logistics optimizer function | *(empty)* | `sc-agent-logistics-optimizer` |
| `LAMBDA_SUPPLIER_ANALYZER` | Supplier analyzer function | *(empty)* | `sc-agent-supplier-analyzer` |

## Configuration Overrides

You can override any configuration value from YAML files using environment variables with the prefix `SC_AGENT_`. The format is:

```
SC_AGENT_<SECTION>_<SUBSECTION>_<KEY>=value
```

### Examples

Override Lambda memory size:
```bash
export SC_AGENT_RESOURCES_LAMBDA_MEMORY_MB=1024
```

Override log retention:
```bash
export SC_AGENT_RESOURCES_LOGS_RETENTION_DAYS=30
```

Enable VPC:
```bash
export SC_AGENT_FEATURES_VPC_ENABLED=true
```

## Local Development Setup

### 1. Copy the example file

```bash
cp .env.example .env
```

### 2. Edit .env with your values

```bash
# Minimal local development setup
AWS_REGION=us-east-1
ENVIRONMENT=dev
SC_AGENT_PREFIX=sc-agent-dev

# Set these after deploying infrastructure
ATHENA_DATABASE=supply_chain_db
ATHENA_OUTPUT_LOCATION=s3://your-bucket/athena-results/
DYNAMODB_SESSION_TABLE=sc-agent-dev-sessions
DYNAMODB_MEMORY_TABLE=sc-agent-dev-memory
DYNAMODB_CONVERSATION_TABLE=sc-agent-dev-conversation

# Lambda functions (set after deployment)
LAMBDA_INVENTORY_OPTIMIZER=sc-agent-dev-inventory-optimizer
LAMBDA_LOGISTICS_OPTIMIZER=sc-agent-dev-logistics-optimizer
LAMBDA_SUPPLIER_ANALYZER=sc-agent-dev-supplier-analyzer

# Cognito (set after deployment)
USER_POOL_ID=us-east-1_XXXXXXXXX
USER_POOL_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 3. Verify configuration

```bash
python startup_validator.py
```

## Production Deployment

For production deployments, environment variables should be:

1. **Set by deployment system** - CDK, CloudFormation, or deployment scripts
2. **Loaded from Parameter Store** - For non-sensitive configuration
3. **Loaded from Secrets Manager** - For sensitive values

### Example: Setting via CDK

```python
lambda_function = aws_lambda.Function(
    self, "MyFunction",
    environment={
        "AWS_REGION": self.region,
        "ENVIRONMENT": "prod",
        "ATHENA_DATABASE": athena_database.database_name,
        "DYNAMODB_SESSION_TABLE": session_table.table_name,
        # ... other variables
    }
)
```

### Example: Loading from Parameter Store

```python
import boto3

ssm = boto3.client('ssm')
response = ssm.get_parameter(Name='/sc-agent-prod/athena-database')
os.environ['ATHENA_DATABASE'] = response['Parameter']['Value']
```

## Validation

The application validates environment variables at startup. You can run validation manually:

```bash
# Basic validation
python startup_validator.py

# Skip AWS credential check
python startup_validator.py --no-aws

# Check that AWS resources exist
python startup_validator.py --check-resources

# Quiet mode (only show errors)
python startup_validator.py --quiet
```

## Troubleshooting

### Missing Required Variables

**Error**: `Required environment variable not set: AWS_REGION`

**Solution**: Set the missing variable in your .env file or environment:
```bash
export AWS_REGION=us-east-1
```

### AWS Credentials Not Configured

**Error**: `AWS credentials not configured or invalid`

**Solution**: Configure AWS credentials using one of these methods:
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Option 3: IAM role (recommended for EC2/ECS/Lambda)
# Credentials are automatically provided
```

### Configuration File Not Found

**Warning**: `Configuration file not found: config/dev.yaml`

**Solution**: This is optional. The application will use environment variables only. To use configuration files:
```bash
# Copy example configuration
cp config/dev.yaml.example config/dev.yaml

# Edit with your values
vim config/dev.yaml
```

### Resource Not Found

**Warning**: `DynamoDB tables not found: sc-agent-sessions`

**Solution**: Deploy the infrastructure first:
```bash
cd cdk
cdk deploy
```

## Security Best Practices

### 1. Never Commit Secrets

Add to `.gitignore`:
```
.env
.env.*
!.env.example
```

### 2. Use Secrets Manager in Production

```python
from secrets_manager import SecretsManager

secrets = SecretsManager(region='us-east-1', prefix='sc-agent-prod')
api_key = secrets.get_secret('external-api-key')
```

### 3. Rotate Credentials Regularly

```bash
# Update secret in Secrets Manager
aws secretsmanager update-secret \
  --secret-id sc-agent-prod/api-key \
  --secret-string "new-secret-value"
```

### 4. Use IAM Roles

Prefer IAM roles over access keys for AWS credentials:
- EC2 instances: Instance profile
- ECS tasks: Task role
- Lambda functions: Execution role

## Environment-Specific Examples

### Development

```bash
# .env.dev
ENVIRONMENT=dev
SC_AGENT_PREFIX=sc-agent-dev
ATHENA_DATABASE=supply_chain_dev
# ... minimal resources
```

### Staging

```bash
# .env.staging
ENVIRONMENT=staging
SC_AGENT_PREFIX=sc-agent-staging
ATHENA_DATABASE=supply_chain_staging
# ... production-like resources
```

### Production

```bash
# .env.prod
ENVIRONMENT=prod
SC_AGENT_PREFIX=sc-agent-prod
ATHENA_DATABASE=supply_chain_prod
# ... full production resources
```

## Additional Resources

- [Configuration Management Guide](docs/CONFIGURATION_QUICKSTART.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Secrets Management](SECRETS_MANAGEMENT.md)
- [AWS Best Practices](https://docs.aws.amazon.com/wellarchitected/)
