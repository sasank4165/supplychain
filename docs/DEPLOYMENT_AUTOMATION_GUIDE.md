# Deployment Automation Guide

This guide explains the automated deployment scripts for the Supply Chain Agentic AI Application.

## Overview

The deployment automation system provides a complete, configuration-driven deployment workflow with validation, bootstrapping, deployment, and verification steps.

## Scripts

### 1. validate-deployment.sh

Pre-deployment validation script that checks all prerequisites before deployment.

**Usage:**
```bash
bash scripts/validate-deployment.sh --environment dev [OPTIONS]
```

**Options:**
- `--environment, -e ENV`: Environment name (dev, staging, prod)
- `--config, -c FILE`: Path to config file (default: config/ENV.yaml)
- `--verbose, -v`: Enable verbose output
- `--help, -h`: Show help message

**Checks Performed:**
- AWS CLI installation and version
- Python 3 installation
- AWS CDK installation
- AWS credentials configuration
- Configuration file existence and validity
- Bedrock API access and model availability
- Service quotas (Lambda concurrency, etc.)
- Python dependencies
- CDK bootstrap status

**Example:**
```bash
# Validate dev environment
bash scripts/validate-deployment.sh --environment dev

# Validate with verbose output
bash scripts/validate-deployment.sh --environment prod --verbose
```

### 2. load-config.sh

Configuration loader that parses YAML configuration and exports environment variables.

**Usage:**
```bash
bash scripts/load-config.sh --environment dev [OPTIONS]
```

**Options:**
- `--environment, -e ENV`: Environment name
- `--config, -c FILE`: Path to config file
- `--output, -o FILE`: Output file for environment variables (default: .env)
- `--export`: Export variables to current shell
- `--help, -h`: Show help message

**Generated Variables:**
- `ENVIRONMENT`: Environment name
- `AWS_REGION`: AWS region
- `AWS_ACCOUNT_ID`: AWS account ID
- `PROJECT_NAME`, `PROJECT_PREFIX`: Project identifiers
- `LAMBDA_MEMORY_MB`, `LAMBDA_TIMEOUT_SECONDS`: Resource configurations
- `DEFAULT_MODEL`: Bedrock model ID
- And many more...

**Example:**
```bash
# Load configuration and save to .env
bash scripts/load-config.sh --environment dev

# Load and export to current shell
bash scripts/load-config.sh --environment prod --export
source .env
```



### 3. bootstrap-cdk.sh

CDK bootstrap script that prepares AWS account for CDK deployments.

**Usage:**
```bash
bash scripts/bootstrap-cdk.sh --environment dev [OPTIONS]
```

**Options:**
- `--environment, -e ENV`: Environment name
- `--config, -c FILE`: Path to config file
- `--force, -f`: Force bootstrap even if already bootstrapped
- `--help, -h`: Show help message

**What it does:**
- Checks if CDK is already bootstrapped
- Installs CDK dependencies if needed
- Runs `cdk bootstrap` with appropriate parameters
- Applies environment tags to bootstrap resources

**Example:**
```bash
# Bootstrap for dev environment
bash scripts/bootstrap-cdk.sh --environment dev

# Force re-bootstrap
bash scripts/bootstrap-cdk.sh --environment prod --force
```

### 4. deploy.sh (Updated)

Main deployment script that orchestrates the entire deployment process.

**Usage:**
```bash
bash deploy.sh --environment dev [OPTIONS]
```

**Options:**
- `--environment, -e ENV`: Environment name (required)
- `--config, -c FILE`: Path to config file
- `--skip-validation`: Skip pre-deployment validation
- `--skip-bootstrap`: Skip CDK bootstrap check
- `--auto-approve`: Auto-approve CDK deployment (no prompts)
- `--help, -h`: Show help message

**Deployment Steps:**
1. Pre-deployment validation
2. Configuration loading
3. CDK bootstrap check
4. Dependency installation
5. CDK infrastructure deployment
6. Post-deployment configuration
7. Deployment verification

**Example:**
```bash
# Interactive deployment to dev
bash deploy.sh --environment dev

# Automated deployment to prod
bash deploy.sh --environment prod --auto-approve

# Quick deployment (skip validation)
bash deploy.sh --environment dev --skip-validation --skip-bootstrap
```

### 5. post-deploy.sh

Post-deployment configuration script that retrieves outputs and configures the application.

**Usage:**
```bash
bash scripts/post-deploy.sh --environment dev [OPTIONS]
```

**Options:**
- `--environment, -e ENV`: Environment name
- `--stack-name, -s NAME`: CloudFormation stack name
- `--output, -o FILE`: Output file (default: .env)
- `--help, -h`: Show help message

**What it does:**
- Retrieves CloudFormation stack outputs
- Updates .env file with deployment information
- Stores outputs in Parameter Store for easy retrieval
- Displays deployment summary

**Retrieved Outputs:**
- API Gateway endpoint
- Cognito User Pool ID and Client ID
- S3 bucket names
- DynamoDB table names
- Lambda function names

**Example:**
```bash
# Run post-deployment configuration
bash scripts/post-deploy.sh --environment dev

# Use custom stack name
bash scripts/post-deploy.sh --environment prod --stack-name my-custom-stack
```



### 6. verify-deployment.sh

Deployment verification script that validates all resources are properly deployed.

**Usage:**
```bash
bash scripts/verify-deployment.sh --environment dev [OPTIONS]
```

**Options:**
- `--environment, -e ENV`: Environment name
- `--stack-name, -s NAME`: CloudFormation stack name
- `--verbose, -v`: Enable verbose output
- `--help, -h`: Show help message

**Verification Checks:**
- CloudFormation stack status
- S3 buckets existence and accessibility
- DynamoDB tables status
- Lambda functions state
- Cognito User Pool status
- API Gateway endpoint
- IAM roles existence
- CloudWatch Log Groups
- Resource tagging

**Example:**
```bash
# Verify dev deployment
bash scripts/verify-deployment.sh --environment dev

# Verify with verbose output
bash scripts/verify-deployment.sh --environment prod --verbose
```

## Complete Deployment Workflow

### First-Time Deployment

```bash
# 1. Validate prerequisites
bash scripts/validate-deployment.sh --environment dev

# 2. Deploy
bash deploy.sh --environment dev

# The deploy script automatically runs:
# - Configuration loading
# - CDK bootstrap (if needed)
# - Infrastructure deployment
# - Post-deployment configuration
# - Verification
```

### Subsequent Deployments

```bash
# Quick deployment (skip validation and bootstrap)
bash deploy.sh --environment dev --skip-validation --skip-bootstrap --auto-approve
```

### Manual Step-by-Step Deployment

```bash
# 1. Validate
bash scripts/validate-deployment.sh --environment dev

# 2. Load configuration
bash scripts/load-config.sh --environment dev --export
source .env

# 3. Bootstrap CDK (first time only)
bash scripts/bootstrap-cdk.sh --environment dev

# 4. Deploy CDK
cd cdk
cdk deploy -c environment=dev -c config_file=../config/dev.yaml
cd ..

# 5. Post-deployment configuration
bash scripts/post-deploy.sh --environment dev

# 6. Verify deployment
bash scripts/verify-deployment.sh --environment dev
```

## Environment-Specific Deployments

### Development Environment

```bash
# Dev uses minimal resources for cost savings
bash deploy.sh --environment dev --auto-approve
```

### Staging Environment

```bash
# Staging uses production-like configuration
bash deploy.sh --environment staging
```

### Production Environment

```bash
# Production requires manual approval and full validation
bash deploy.sh --environment prod

# Or with all checks
bash scripts/validate-deployment.sh --environment prod --verbose
bash deploy.sh --environment prod
bash scripts/verify-deployment.sh --environment prod --verbose
```

## Configuration Files

Each environment has its own configuration file:

- `config/dev.yaml` - Development environment
- `config/staging.yaml` - Staging environment
- `config/prod.yaml` - Production environment

See [Configuration Reference](CONFIGURATION_REFERENCE.md) for details on all configuration parameters.



## Troubleshooting

### Validation Failures

**Problem:** AWS credentials not configured
```bash
# Solution: Configure AWS CLI
aws configure
```

**Problem:** Bedrock models not available
```bash
# Solution: Enable Bedrock model access in AWS Console
# Go to: AWS Console > Bedrock > Model access > Request access
```

**Problem:** Configuration file validation failed
```bash
# Solution: Validate configuration manually
python3 scripts/validate-config.py --config config/dev.yaml

# Check for syntax errors in YAML
python3 -c "import yaml; yaml.safe_load(open('config/dev.yaml'))"
```

### Bootstrap Failures

**Problem:** CDK bootstrap fails with permissions error
```bash
# Solution: Ensure your AWS credentials have AdministratorAccess
# Or at minimum: CloudFormation, S3, IAM permissions
```

**Problem:** Bootstrap stack already exists but is corrupted
```bash
# Solution: Force re-bootstrap
bash scripts/bootstrap-cdk.sh --environment dev --force
```

### Deployment Failures

**Problem:** CDK deployment fails with resource conflicts
```bash
# Solution: Check CloudFormation events
aws cloudformation describe-stack-events --stack-name sc-agent-dev-stack

# Delete and redeploy if needed
cdk destroy
bash deploy.sh --environment dev
```

**Problem:** Lambda functions fail to deploy
```bash
# Solution: Check Lambda quotas
aws service-quotas get-service-quota \
  --service-code lambda \
  --quota-code L-B99A9384

# Request quota increase if needed
```

### Verification Failures

**Problem:** Resources exist but verification fails
```bash
# Solution: Check IAM permissions for describe/list operations
# Ensure your credentials can read CloudFormation, Lambda, DynamoDB, etc.
```

**Problem:** API Gateway not responding
```bash
# Solution: Check API Gateway deployment
aws apigateway get-deployments --rest-api-id <api-id>

# Check Lambda function logs
aws logs tail /aws/lambda/<function-name> --follow
```

## Best Practices

### 1. Always Validate Before Deploying

```bash
# Run validation before every deployment
bash scripts/validate-deployment.sh --environment prod --verbose
```

### 2. Use Configuration Files

Never hardcode values. Always use configuration files:

```yaml
# config/prod.yaml
resources:
  lambda:
    memory_mb: 1024  # Adjust per environment
    timeout_seconds: 300
```

### 3. Tag All Resources

Ensure all resources are properly tagged for cost tracking:

```yaml
tags:
  custom:
    CostCenter: "Engineering"
    Project: "SupplyChain"
    Owner: "platform-team"
```

### 4. Monitor Deployments

```bash
# Watch CloudFormation events during deployment
watch -n 5 'aws cloudformation describe-stack-events \
  --stack-name sc-agent-dev-stack \
  --max-items 10 \
  --query "StackEvents[*].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId]" \
  --output table'
```

### 5. Backup Before Updates

```bash
# Export current stack template before updates
aws cloudformation get-template \
  --stack-name sc-agent-prod-stack \
  --query TemplateBody \
  > backup-template-$(date +%Y%m%d).json
```

### 6. Use Parameter Store

Store sensitive configuration in Parameter Store, not in .env files:

```bash
# Store API keys
aws ssm put-parameter \
  --name /sc-agent-prod/api-key \
  --value "your-secret-key" \
  --type SecureString
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Validate Deployment
        run: bash scripts/validate-deployment.sh --environment prod
      
      - name: Deploy
        run: bash deploy.sh --environment prod --auto-approve
```

### GitLab CI Example

```yaml
deploy:
  stage: deploy
  image: amazon/aws-cli
  script:
    - bash scripts/validate-deployment.sh --environment prod
    - bash deploy.sh --environment prod --auto-approve
  only:
    - main
```

## Additional Resources

- [Configuration Reference](CONFIGURATION_REFERENCE.md)
- [CDK Documentation](../cdk/README.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [AWS CDK Best Practices](https://docs.aws.amazon.com/cdk/latest/guide/best-practices.html)
