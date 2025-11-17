#!/bin/bash
# Deployment script for Supply Chain Agentic AI Application
# Uses configuration system for environment-specific deployments

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default values
ENVIRONMENT="dev"
CONFIG_FILE=""
SKIP_VALIDATION=false
SKIP_BOOTSTRAP=false
AUTO_APPROVE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --config|-c)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --skip-bootstrap)
            SKIP_BOOTSTRAP=true
            shift
            ;;
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --environment, -e ENV    Environment name (dev, staging, prod)"
            echo "  --config, -c FILE        Path to config file (default: config/ENV.yaml)"
            echo "  --skip-validation        Skip pre-deployment validation"
            echo "  --skip-bootstrap         Skip CDK bootstrap check"
            echo "  --auto-approve           Auto-approve CDK deployment"
            echo "  --help, -h               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set config file if not specified
if [ -z "$CONFIG_FILE" ]; then
    CONFIG_FILE="config/${ENVIRONMENT}.yaml"
fi

echo "🚀 Deploying Supply Chain Agentic AI Application"
echo "Environment: $ENVIRONMENT"
echo "Config File: $CONFIG_FILE"
echo ""

# Step 1: Pre-deployment validation
if [ "$SKIP_VALIDATION" = false ]; then
    echo "Step 1: Running pre-deployment validation..."
    if bash scripts/validate-deployment.sh --environment "$ENVIRONMENT" --config "$CONFIG_FILE"; then
        echo -e "${GREEN}✓${NC} Validation passed"
    else
        echo -e "${RED}✗${NC} Validation failed"
        exit 1
    fi
    echo ""
fi

# Step 2: Load configuration
echo "Step 2: Loading configuration..."
if bash scripts/load-config.sh --environment "$ENVIRONMENT" --config "$CONFIG_FILE" --export; then
    source .env
    echo -e "${GREEN}✓${NC} Configuration loaded"
else
    echo -e "${RED}✗${NC} Failed to load configuration"
    exit 1
fi
echo ""

# Step 3: Bootstrap CDK
if [ "$SKIP_BOOTSTRAP" = false ]; then
    echo "Step 3: Checking CDK bootstrap..."
    bash scripts/bootstrap-cdk.sh --environment "$ENVIRONMENT" --config "$CONFIG_FILE"
    echo ""
fi

# Step 4: Install dependencies
echo "Step 4: Installing dependencies..."
pip install -q -r requirements.txt
echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# Step 5: Deploy CDK stack
echo "Step 5: Deploying CDK infrastructure..."
cd cdk

# Set CDK context from configuration
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT_ID
export CDK_DEFAULT_REGION=$AWS_REGION

# Build CDK deploy command
CDK_DEPLOY_CMD="cdk deploy"
if [ "$AUTO_APPROVE" = true ]; then
    CDK_DEPLOY_CMD="$CDK_DEPLOY_CMD --require-approval never"
fi

# Add context parameters
CDK_DEPLOY_CMD="$CDK_DEPLOY_CMD -c environment=$ENVIRONMENT"
CDK_DEPLOY_CMD="$CDK_DEPLOY_CMD -c config_file=../$CONFIG_FILE"

echo "Running: $CDK_DEPLOY_CMD"
eval $CDK_DEPLOY_CMD

if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} CDK deployment failed"
    cd ..
    exit 1
fi

cd ..
echo -e "${GREEN}✓${NC} CDK deployment completed"
echo ""

# Step 6: Post-deployment configuration
echo "Step 6: Running post-deployment configuration..."
bash scripts/post-deploy.sh --environment "$ENVIRONMENT"
echo ""

# Step 7: Verify deployment
echo "Step 7: Verifying deployment..."
bash scripts/verify-deployment.sh --environment "$ENVIRONMENT"
echo ""

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review deployment outputs in .env file"
echo "2. Create users: bash scripts/setup-users.sh"
echo "3. Run the application: streamlit run app.py"
