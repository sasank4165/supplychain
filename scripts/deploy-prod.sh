#!/bin/bash
# Production deployment script with safety checks

set -e

echo "🚀 Production Deployment Script"
echo "================================"

# Configuration
ENVIRONMENT="prod"
REGION="${AWS_REGION:-us-east-1}"
ALARM_EMAIL="${ALARM_EMAIL:-ops@example.com}"

# Safety checks
echo "⚠️  WARNING: You are about to deploy to PRODUCTION"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Alarm Email: $ALARM_EMAIL"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo "✅ Deploying to account: $AWS_ACCOUNT"

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK not installed. Run: npm install -g aws-cdk"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
cd "$(dirname "$0")/.."
pip install -r requirements.txt

# Create Lambda layer
echo "🔧 Creating Lambda layer..."
mkdir -p lambda_layers/common/python
pip install boto3 anthropic -t lambda_layers/common/python/

# CDK Bootstrap (if needed)
echo "🏗️  Checking CDK bootstrap..."
cd cdk
pip install -r requirements.txt

if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $REGION &> /dev/null; then
    echo "Bootstrapping CDK..."
    cdk bootstrap aws://$AWS_ACCOUNT/$REGION
fi

# Synthesize templates
echo "🔨 Synthesizing CloudFormation templates..."
cdk synth --context environment=$ENVIRONMENT \
          --context alarm_email=$ALARM_EMAIL \
          --context region=$REGION

# Show diff
echo "📊 Showing changes..."
cdk diff --all --context environment=$ENVIRONMENT

echo ""
read -p "Proceed with deployment? (yes/no): " PROCEED

if [ "$PROCEED" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Deploy stacks in order
echo "☁️  Deploying infrastructure..."

# Network stack
echo "Deploying Network Stack..."
cdk deploy SupplyChainNetwork-$ENVIRONMENT \
    --context environment=$ENVIRONMENT \
    --context alarm_email=$ALARM_EMAIL \
    --require-approval never

# Security stack
echo "Deploying Security Stack..."
cdk deploy SupplyChainSecurity-$ENVIRONMENT \
    --context environment=$ENVIRONMENT \
    --context alarm_email=$ALARM_EMAIL \
    --require-approval never

# Data stack
echo "Deploying Data Stack..."
cdk deploy SupplyChainData-$ENVIRONMENT \
    --context environment=$ENVIRONMENT \
    --context alarm_email=$ALARM_EMAIL \
    --require-approval never

# Application stack
echo "Deploying Application Stack..."
cdk deploy SupplyChainApp-$ENVIRONMENT \
    --context environment=$ENVIRONMENT \
    --context alarm_email=$ALARM_EMAIL \
    --require-approval never

# Monitoring stack
echo "Deploying Monitoring Stack..."
cdk deploy SupplyChainMonitoring-$ENVIRONMENT \
    --context environment=$ENVIRONMENT \
    --context alarm_email=$ALARM_EMAIL \
    --require-approval never

# Backup stack
echo "Deploying Backup Stack..."
cdk deploy SupplyChainBackup-$ENVIRONMENT \
    --context environment=$ENVIRONMENT \
    --context alarm_email=$ALARM_EMAIL \
    --require-approval never

# Get outputs
echo "📋 Retrieving stack outputs..."
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name SupplyChainApp-$ENVIRONMENT \
    --query "Stacks[0].Outputs[?OutputKey=='APIEndpoint'].OutputValue" \
    --output text \
    --region $REGION)

USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name SupplyChainApp-$ENVIRONMENT \
    --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
    --output text \
    --region $REGION)

echo ""
echo "✅ Deployment Complete!"
echo "======================="
echo "API Endpoint: $API_ENDPOINT"
echo "User Pool ID: $USER_POOL_ID"
echo "Region: $REGION"
echo ""
echo "Next steps:"
echo "1. Create Cognito users"
echo "2. Test API endpoints"
echo "3. Monitor CloudWatch dashboard"
echo "4. Verify alarms are configured"
