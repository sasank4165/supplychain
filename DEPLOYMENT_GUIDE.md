# Supply Chain Agentic AI Application - Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Pre-Deployment Setup](#pre-deployment-setup)
4. [Configuration](#configuration)
5. [Deployment Steps](#deployment-steps)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedures](#rollback-procedures)

## Overview

This guide provides step-by-step instructions for deploying the Supply Chain Agentic AI Application to any AWS environment. The application is fully portable and can be deployed to multiple AWS accounts and regions without code modifications.

### Deployment Architecture

The application uses AWS CDK for infrastructure as code and supports three environment types:
- **Development (dev)**: Minimal resources, short retention periods, cost-optimized
- **Staging**: Production-like configuration for testing
- **Production (prod)**: Full resources, extended retention, high availability

### Estimated Deployment Time

- First-time deployment: 30-45 minutes
- Subsequent deployments: 15-20 minutes

## Prerequisites

### Required Tools

1. **AWS CLI** (version 2.x or later)
   ```bash
   aws --version
   # Should output: aws-cli/2.x.x or later
   ```

2. **Python** (version 3.9 or later)
   ```bash
   python --version
   # Should output: Python 3.9.x or later
   ```

3. **Node.js** (version 18.x or later) - Required for AWS CDK
   ```bash
   node --version
   # Should output: v18.x.x or later
   ```

4. **AWS CDK** (version 2.x)
   ```bash
   npm install -g aws-cdk
   cdk --version
   # Should output: 2.x.x or later
   ```

### AWS Account Requirements

1. **AWS Account Access**
   - Administrative access or sufficient permissions to create:
     - IAM roles and policies
     - Lambda functions
     - DynamoDB tables
     - S3 buckets
     - API Gateway
     - CloudWatch resources
     - Secrets Manager secrets
     - Systems Manager parameters

2. **Amazon Bedrock Access**
   - Bedrock service must be available in your target region
   - Model access must be enabled for:
     - Anthropic Claude 3.5 Sonnet
     - (Optional) Other models you plan to use

   To enable model access:
   ```bash
   # Navigate to Amazon Bedrock console
   # Go to Model access
   # Request access for required models
   ```

3. **Service Quotas**
   - Lambda concurrent executions: At least 100
   - DynamoDB tables: At least 10
   - S3 buckets: At least 5
   - API Gateway APIs: At least 5

   Check quotas:
   ```bash
   aws service-quotas list-service-quotas \
     --service-code lambda \
     --query 'Quotas[?QuotaName==`Concurrent executions`]'
   ```

### Network Requirements

- Outbound internet access for:
  - AWS service endpoints
  - CDK asset uploads
  - Package downloads (pip, npm)

## Pre-Deployment Setup

### Step 1: Clone and Prepare Repository

```bash
# Clone the repository
git clone <repository-url>
cd supply-chain-agent

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install CDK dependencies
cd cdk
pip install -r requirements.txt
cd ..
```

### Step 2: Configure AWS Credentials

```bash
# Configure AWS CLI with your credentials
aws configure

# Verify credentials
aws sts get-caller-identity

# Output should show your account ID and user/role
```

### Step 3: Verify Bedrock Access

```bash
# Check Bedrock model access
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `claude`)].modelId'

# Verify you can access Claude models
```

## Configuration

### Step 1: Choose Your Environment

Decide which environment you're deploying:
- `dev` - Development environment
- `staging` - Staging environment
- `prod` - Production environment

```bash
export ENVIRONMENT=dev  # or staging, or prod
```

### Step 2: Create Configuration File

Copy the appropriate example configuration:

```bash
# Use existing configuration or create from template
cp config/dev.yaml config/my-dev.yaml

# Edit the configuration file
# See CONFIGURATION_REFERENCE.md for all parameters
```

### Step 3: Customize Configuration

Edit `config/my-dev.yaml` with your specific settings:

```yaml
environment:
  name: "dev"
  region: "us-east-1"  # Your target region
  
project:
  name: "supply-chain-agent"
  prefix: "my-sc-agent"  # Unique prefix for your deployment
  owner: "your-team@example.com"
  cost_center: "supply-chain"

# Customize other settings as needed
# See CONFIGURATION_REFERENCE.md for details
```

### Step 4: Validate Configuration

```bash
# Validate configuration file
python scripts/validate-config.py --config config/my-dev.yaml

# Should output: "Configuration is valid"
```

## Deployment Steps

### Step 1: Run Pre-Deployment Validation

```bash
# Run comprehensive pre-deployment checks
./scripts/validate-deployment.sh --environment $ENVIRONMENT --config config/my-dev.yaml

# This checks:
# - AWS credentials
# - Service quotas
# - Bedrock access
# - Configuration validity
# - Required permissions
```

If validation fails, address the issues before proceeding.

### Step 2: Load Configuration

```bash
# Load configuration into environment
source ./scripts/load-config.sh --environment $ENVIRONMENT --config config/my-dev.yaml

# This sets environment variables needed for deployment
```

### Step 3: Bootstrap CDK (First Time Only)

If this is your first CDK deployment in this account/region:

```bash
# Bootstrap CDK
./scripts/bootstrap-cdk.sh --environment $ENVIRONMENT

# This creates the CDK toolkit stack for asset storage
```

### Step 4: Deploy Infrastructure

```bash
# Deploy all stacks
./deploy.sh --environment $ENVIRONMENT

# Or deploy with specific configuration file
./deploy.sh --environment $ENVIRONMENT --config config/my-dev.yaml

# Deployment will:
# 1. Synthesize CDK stacks
# 2. Create/update CloudFormation stacks
# 3. Deploy Lambda functions
# 4. Create DynamoDB tables
# 5. Set up API Gateway
# 6. Configure monitoring
```

**Note**: You'll be prompted to approve IAM changes and security group modifications. Review carefully and approve.

### Step 5: Monitor Deployment

```bash
# Watch deployment progress
# CDK will show real-time status of resource creation

# Typical deployment order:
# 1. Network stack (if VPC enabled)
# 2. Security stack
# 3. Data stack (DynamoDB, S3)
# 4. Application stack (Lambda, API Gateway)
# 5. Monitoring stack (CloudWatch)
```

### Step 6: Save Deployment Outputs

```bash
# CDK will output important values at the end:
# - API Gateway endpoint URL
# - S3 bucket names
# - DynamoDB table names
# - Cognito User Pool ID

# Save these outputs for reference
```

## Post-Deployment Configuration

### Step 1: Initialize Secrets

```bash
# Initialize secrets in Secrets Manager
python scripts/init-secrets.py --environment $ENVIRONMENT

# This creates placeholder secrets that you should update
```

### Step 2: Update Secrets with Real Values

```bash
# Update database credentials (if using external DB)
aws secretsmanager update-secret \
  --secret-id /my-sc-agent/dev/database/credentials \
  --secret-string '{"username":"admin","password":"your-secure-password"}'

# Update API keys (if needed)
aws secretsmanager update-secret \
  --secret-id /my-sc-agent/dev/api/keys \
  --secret-string '{"api_key":"your-api-key"}'
```

### Step 3: Run Post-Deployment Script

```bash
# Configure additional settings
./scripts/post-deploy.sh --environment $ENVIRONMENT

# This script:
# - Stores outputs in Parameter Store
# - Creates initial DynamoDB items
# - Sets up CloudWatch alarms
# - Configures log groups
```

### Step 4: Create Cognito Users

```bash
# Create test users
./scripts/setup-users.sh --environment $ENVIRONMENT

# Or manually create users in Cognito console
```

### Step 5: Upload Sample Data (Optional)

```bash
# Generate and upload sample data for testing
python scripts/generate_sample_data.py --environment $ENVIRONMENT

# This creates sample inventory, shipments, and supplier data
```

## Verification

### Step 1: Run Deployment Verification

```bash
# Verify all resources are working
./scripts/verify-deployment.sh --environment $ENVIRONMENT

# This checks:
# - Lambda functions are active
# - DynamoDB tables are accessible
# - API Gateway is responding
# - Secrets are configured
# - CloudWatch logs are being created
```

### Step 2: Test API Endpoint

```bash
# Get API endpoint from outputs
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name my-sc-agent-app-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Test health endpoint
curl $API_ENDPOINT/health

# Should return: {"status": "healthy"}
```

### Step 3: Test Agent Query

```bash
# Test a simple query through the API
curl -X POST $API_ENDPOINT/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "query": "Show me current inventory levels",
    "persona": "warehouse_manager"
  }'

# Should return agent response with inventory data
```

### Step 4: Verify Monitoring

```bash
# Check CloudWatch dashboard
aws cloudwatch get-dashboard \
  --dashboard-name my-sc-agent-agents-dev

# View recent logs
aws logs tail /aws/lambda/my-sc-agent-orchestrator-dev --follow
```

### Step 5: Run Smoke Tests

```bash
# Run automated smoke tests
./scripts/test-deployment.sh --environment $ENVIRONMENT

# This runs a suite of tests to verify functionality
```

## Troubleshooting

### Common Issues

#### 1. CDK Bootstrap Fails

**Error**: "Unable to resolve AWS account to use"

**Solution**:
```bash
# Ensure AWS credentials are configured
aws sts get-caller-identity

# Explicitly specify account and region
cdk bootstrap aws://ACCOUNT-ID/REGION
```

#### 2. Bedrock Access Denied

**Error**: "AccessDeniedException: Could not access model"

**Solution**:
```bash
# Enable model access in Bedrock console
# Or use CLI:
aws bedrock put-model-invocation-logging-configuration \
  --region us-east-1
```

#### 3. Lambda Deployment Fails

**Error**: "Code size exceeds maximum"

**Solution**:
```bash
# Use Lambda layers for large dependencies
# Or enable Docker-based deployment in CDK
```

#### 4. DynamoDB Table Already Exists

**Error**: "Table already exists"

**Solution**:
```bash
# Use a different prefix in configuration
# Or delete existing table if safe to do so
aws dynamodb delete-table --table-name existing-table-name
```

#### 5. API Gateway 403 Errors

**Error**: "Missing Authentication Token"

**Solution**:
```bash
# Verify Cognito user pool is configured
# Check API Gateway authorizer settings
# Ensure valid JWT token is provided
```

### Getting Help

For additional troubleshooting, see:
- [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)
- [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)
- Check CloudWatch Logs for detailed error messages

## Rollback Procedures

### Rollback to Previous Version

```bash
# Rollback to previous deployment
./scripts/rollback.sh --environment $ENVIRONMENT --version previous

# This reverts CloudFormation stacks to previous state
```

### Complete Environment Cleanup

```bash
# Remove all resources (with confirmation)
./scripts/cleanup.sh --environment $ENVIRONMENT

# Force cleanup without confirmation (use with caution)
./scripts/cleanup.sh --environment $ENVIRONMENT --force

# Preserve data during cleanup
./scripts/cleanup.sh --environment $ENVIRONMENT --preserve-data
```

### Manual Rollback

If automated rollback fails:

```bash
# 1. Identify the stack
aws cloudformation list-stacks --stack-status-filter UPDATE_ROLLBACK_FAILED

# 2. Continue rollback
aws cloudformation continue-update-rollback --stack-name <stack-name>

# 3. Or delete and redeploy
aws cloudformation delete-stack --stack-name <stack-name>
```

## Next Steps

After successful deployment:

1. **Configure Monitoring**: Set up CloudWatch alarms and dashboards
2. **Set Up CI/CD**: Integrate with your CI/CD pipeline
3. **Load Production Data**: Import real inventory and supplier data
4. **User Training**: Train users on the application
5. **Performance Tuning**: Monitor and optimize based on usage patterns

## Additional Resources

- [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) - Complete configuration documentation
- [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) - Detailed troubleshooting steps
- [AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md) - Guide for adding new agents
- [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) - Day-to-day operations guide
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)

## Support

For issues or questions:
- Check the troubleshooting guide
- Review CloudWatch logs
- Contact your DevOps team
- Open an issue in the repository
