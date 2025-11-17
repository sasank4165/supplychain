#!/bin/bash
# Pre-deployment validation script
# Validates prerequisites and configuration before deployment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
CONFIG_FILE=""
VERBOSE=false

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
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --environment, -e ENV    Environment name (dev, staging, prod)"
            echo "  --config, -c FILE        Path to config file (default: config/ENV.yaml)"
            echo "  --verbose, -v            Enable verbose output"
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

echo "🔍 Pre-Deployment Validation"
echo "Environment: $ENVIRONMENT"
echo "Config File: $CONFIG_FILE"
echo ""

VALIDATION_FAILED=false

# Function to print success message
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error message
print_error() {
    echo -e "${RED}✗${NC} $1"
    VALIDATION_FAILED=true
}


# Function to print warning message
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Check AWS CLI is installed
echo "Checking prerequisites..."
if command -v aws &> /dev/null; then
    print_success "AWS CLI is installed ($(aws --version))"
else
    print_error "AWS CLI is not installed. Please install it from https://aws.amazon.com/cli/"
fi

# 2. Check Python is installed
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python is installed ($PYTHON_VERSION)"
else
    print_error "Python 3 is not installed"
fi

# 3. Check CDK is installed
if command -v cdk &> /dev/null; then
    CDK_VERSION=$(cdk --version)
    print_success "AWS CDK is installed ($CDK_VERSION)"
else
    print_error "AWS CDK is not installed. Install with: npm install -g aws-cdk"
fi

# 4. Check AWS credentials are configured
echo ""
echo "Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
    print_success "AWS credentials are configured"
    echo "  Account: $AWS_ACCOUNT"
    echo "  Identity: $AWS_USER"
else
    print_error "AWS credentials are not configured. Run 'aws configure'"
fi

# 5. Check configuration file exists
echo ""
echo "Checking configuration..."
if [ -f "$CONFIG_FILE" ]; then
    print_success "Configuration file exists: $CONFIG_FILE"
else
    print_error "Configuration file not found: $CONFIG_FILE"
fi


# 6. Validate configuration file with Python script
if [ -f "$CONFIG_FILE" ] && [ -f "scripts/validate-config.py" ]; then
    if python3 scripts/validate-config.py --config "$CONFIG_FILE" &> /dev/null; then
        print_success "Configuration file is valid"
    else
        print_error "Configuration file validation failed"
        if [ "$VERBOSE" = true ]; then
            python3 scripts/validate-config.py --config "$CONFIG_FILE"
        fi
    fi
fi

# 7. Check Bedrock model access
echo ""
echo "Checking Bedrock access..."
if aws bedrock list-foundation-models --region us-east-1 &> /dev/null; then
    print_success "Bedrock API is accessible"
    
    # Check for Claude model access
    if aws bedrock list-foundation-models --region us-east-1 --query "modelSummaries[?contains(modelId, 'claude')].modelId" --output text | grep -q "claude"; then
        print_success "Claude models are available"
    else
        print_warning "Claude models may not be available. Request access in AWS Console."
    fi
else
    print_warning "Cannot verify Bedrock access. Ensure you have enabled Bedrock in your region."
fi

# 8. Check service quotas
echo ""
echo "Checking service quotas..."

# Check Lambda concurrent executions quota
LAMBDA_QUOTA=$(aws service-quotas get-service-quota \
    --service-code lambda \
    --quota-code L-B99A9384 \
    --query 'Quota.Value' \
    --output text 2>/dev/null || echo "1000")

if [ "$LAMBDA_QUOTA" -ge 100 ]; then
    print_success "Lambda concurrent executions quota: $LAMBDA_QUOTA"
else
    print_warning "Lambda concurrent executions quota is low: $LAMBDA_QUOTA"
fi


# 9. Check required Python packages
echo ""
echo "Checking Python dependencies..."
if [ -f "requirements.txt" ]; then
    MISSING_PACKAGES=()
    while IFS= read -r package; do
        # Skip empty lines and comments
        [[ -z "$package" || "$package" =~ ^# ]] && continue
        
        # Extract package name (before ==, >=, etc.)
        pkg_name=$(echo "$package" | sed 's/[>=<].*//' | tr -d '[:space:]')
        
        if python3 -c "import $pkg_name" 2>/dev/null; then
            [ "$VERBOSE" = true ] && echo "  ✓ $pkg_name"
        else
            MISSING_PACKAGES+=("$pkg_name")
        fi
    done < requirements.txt
    
    if [ ${#MISSING_PACKAGES[@]} -eq 0 ]; then
        print_success "All required Python packages are installed"
    else
        print_warning "Missing Python packages: ${MISSING_PACKAGES[*]}"
        echo "  Run: pip install -r requirements.txt"
    fi
fi

# 10. Check CDK bootstrap status
echo ""
echo "Checking CDK bootstrap status..."
AWS_REGION=${AWS_REGION:-us-east-1}
BOOTSTRAP_STACK="CDKToolkit"

if aws cloudformation describe-stacks --stack-name "$BOOTSTRAP_STACK" --region "$AWS_REGION" &> /dev/null; then
    print_success "CDK is bootstrapped in $AWS_REGION"
else
    print_warning "CDK is not bootstrapped in $AWS_REGION"
    echo "  Run: cd cdk && cdk bootstrap"
fi

# Summary
echo ""
echo "========================================="
if [ "$VALIDATION_FAILED" = true ]; then
    echo -e "${RED}❌ Validation FAILED${NC}"
    echo "Please fix the errors above before deploying."
    exit 1
else
    echo -e "${GREEN}✅ Validation PASSED${NC}"
    echo "Ready to deploy to $ENVIRONMENT environment."
    exit 0
fi
