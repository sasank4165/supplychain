#!/bin/bash
# CDK Bootstrap script
# Bootstraps AWS CDK in the target account and region

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default values
ENVIRONMENT="dev"
CONFIG_FILE=""
FORCE=false

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
        --force|-f)
            FORCE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --environment, -e ENV    Environment name (dev, staging, prod)"
            echo "  --config, -c FILE        Path to config file (default: config/ENV.yaml)"
            echo "  --force, -f              Force bootstrap even if already bootstrapped"
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

echo "🏗️  CDK Bootstrap"
echo "Environment: $ENVIRONMENT"
echo ""

# Load configuration to get region and account
if [ -f "$CONFIG_FILE" ]; then
    AWS_REGION=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['environment']['region'])" 2>/dev/null || echo "us-east-1")
    ACCOUNT_ID=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['environment']['account_id'])" 2>/dev/null || echo "auto")
else
    AWS_REGION=${AWS_REGION:-us-east-1}
    ACCOUNT_ID="auto"
fi


# Get actual account ID if set to auto
if [ "$ACCOUNT_ID" = "auto" ]; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
fi

echo "Target Account: $ACCOUNT_ID"
echo "Target Region: $AWS_REGION"
echo ""

# Check if already bootstrapped
BOOTSTRAP_STACK="CDKToolkit"
if aws cloudformation describe-stacks --stack-name "$BOOTSTRAP_STACK" --region "$AWS_REGION" &> /dev/null; then
    if [ "$FORCE" = false ]; then
        echo -e "${GREEN}✓${NC} CDK is already bootstrapped in $AWS_REGION"
        echo "Use --force to re-bootstrap"
        exit 0
    else
        echo -e "${YELLOW}⚠${NC} Re-bootstrapping CDK in $AWS_REGION"
    fi
else
    echo "Bootstrapping CDK for the first time..."
fi

# Navigate to CDK directory
if [ -d "cdk" ]; then
    cd cdk
else
    echo "❌ CDK directory not found"
    exit 1
fi

# Install CDK dependencies if needed
if [ -f "requirements.txt" ] && [ ! -d ".venv" ]; then
    echo "Installing CDK dependencies..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi

# Bootstrap CDK
echo "Running CDK bootstrap..."
cdk bootstrap aws://$ACCOUNT_ID/$AWS_REGION \
    --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess \
    --tags "Environment=$ENVIRONMENT" \
    --tags "ManagedBy=CDK"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ CDK bootstrap completed successfully${NC}"
    echo "Account: $ACCOUNT_ID"
    echo "Region: $AWS_REGION"
else
    echo ""
    echo "❌ CDK bootstrap failed"
    exit 1
fi

cd ..
