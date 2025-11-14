#!/bin/bash
# Deployment script for Supply Chain Agentic AI Application

set -e

echo "🚀 Deploying Supply Chain Agentic AI Application"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure'"
    exit 1
fi

# Get AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo "📍 Deploying to Account: $AWS_ACCOUNT, Region: $AWS_REGION"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create Lambda layer
echo "🔧 Creating Lambda layer..."
mkdir -p lambda_layers/common/python
pip install boto3 -t lambda_layers/common/python/

# Bootstrap CDK (if not already done)
echo "🏗️  Bootstrapping CDK..."
cd cdk
cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION

# Deploy CDK stack
echo "☁️  Deploying CDK stack..."
cdk deploy --require-approval never

# Get outputs
echo "📋 Getting stack outputs..."
ATHENA_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name SupplyChainAgentStack \
    --query "Stacks[0].Outputs[?OutputKey=='AthenaResultsBucketName'].OutputValue" \
    --output text)

USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name SupplyChainAgentStack \
    --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
    --output text)

API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name SupplyChainAgentStack \
    --query "Stacks[0].Outputs[?OutputKey=='APIEndpoint'].OutputValue" \
    --output text)

cd ..

# Update config with deployed resources
echo "⚙️  Updating configuration..."
cat > .env << EOF
AWS_REGION=$AWS_REGION
ATHENA_OUTPUT_LOCATION=s3://$ATHENA_BUCKET/
USER_POOL_ID=$USER_POOL_ID
API_ENDPOINT=$API_ENDPOINT
EOF

echo "✅ Deployment complete!"
echo ""
echo "📝 Configuration saved to .env"
echo "🌐 API Endpoint: $API_ENDPOINT"
echo "👤 User Pool ID: $USER_POOL_ID"
echo ""
echo "Next steps:"
echo "1. Create users in Cognito User Pool"
echo "2. Update ATHENA_DATABASE in config.py with your database name"
echo "3. Run the Streamlit app: streamlit run app.py"
