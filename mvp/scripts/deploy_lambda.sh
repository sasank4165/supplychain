#!/bin/bash

# Deploy Lambda Functions for Supply Chain MVP
# This script packages and deploys all three Lambda functions:
# - Inventory Optimizer
# - Logistics Optimizer  
# - Supplier Analyzer

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
REDSHIFT_WORKGROUP="${REDSHIFT_WORKGROUP:-supply-chain-mvp}"
REDSHIFT_DATABASE="${REDSHIFT_DATABASE:-supply_chain_db}"
LAMBDA_ROLE_NAME="${LAMBDA_ROLE_NAME:-SupplyChainLambdaRole}"

# Lambda function names
INVENTORY_FUNCTION="supply-chain-inventory-optimizer"
LOGISTICS_FUNCTION="supply-chain-logistics-optimizer"
SUPPLIER_FUNCTION="supply-chain-supplier-analyzer"

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="$PROJECT_ROOT/lambda_functions"

echo -e "${GREEN}=== Supply Chain Lambda Deployment ===${NC}"
echo "Region: $AWS_REGION"
echo "Redshift Workgroup: $REDSHIFT_WORKGROUP"
echo "Redshift Database: $REDSHIFT_DATABASE"
echo ""

# Function to check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}Error: AWS CLI is not installed${NC}"
        echo "Please install AWS CLI: https://aws.amazon.com/cli/"
        exit 1
    fi
    echo -e "${GREEN}✓ AWS CLI found${NC}"
}

# Function to check AWS credentials
check_aws_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}Error: AWS credentials not configured${NC}"
        echo "Please configure AWS credentials using 'aws configure'"
        exit 1
    fi
    echo -e "${GREEN}✓ AWS credentials configured${NC}"
    aws sts get-caller-identity
    echo ""
}

# Function to get or create IAM role for Lambda
get_or_create_lambda_role() {
    echo -e "${YELLOW}Checking Lambda IAM role...${NC}"
    
    # Check if role exists
    if aws iam get-role --role-name "$LAMBDA_ROLE_NAME" &> /dev/null; then
        echo -e "${GREEN}✓ IAM role $LAMBDA_ROLE_NAME already exists${NC}"
        ROLE_ARN=$(aws iam get-role --role-name "$LAMBDA_ROLE_NAME" --query 'Role.Arn' --output text)
    else
        echo "Creating IAM role $LAMBDA_ROLE_NAME..."
        
        # Create trust policy
        TRUST_POLICY='{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }'
        
        # Create role
        ROLE_ARN=$(aws iam create-role \
            --role-name "$LAMBDA_ROLE_NAME" \
            --assume-role-policy-document "$TRUST_POLICY" \
            --query 'Role.Arn' \
            --output text)
        
        echo -e "${GREEN}✓ Created IAM role: $ROLE_ARN${NC}"
        
        # Attach policies
        echo "Attaching policies to role..."
        
        # Basic Lambda execution
        aws iam attach-role-policy \
            --role-name "$LAMBDA_ROLE_NAME" \
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        
        # Redshift Data API access
        REDSHIFT_POLICY='{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "redshift-data:ExecuteStatement",
                        "redshift-data:DescribeStatement",
                        "redshift-data:GetStatementResult",
                        "redshift-data:ListStatements"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "redshift-serverless:GetWorkgroup",
                        "redshift-serverless:GetNamespace"
                    ],
                    "Resource": "*"
                }
            ]
        }'
        
        aws iam put-role-policy \
            --role-name "$LAMBDA_ROLE_NAME" \
            --policy-name "RedshiftDataAPIAccess" \
            --policy-document "$REDSHIFT_POLICY"
        
        echo -e "${GREEN}✓ Attached policies to role${NC}"
        
        # Wait for role to be available
        echo "Waiting for role to propagate..."
        sleep 10
    fi
    
    echo "Role ARN: $ROLE_ARN"
    echo ""
}

# Function to package and deploy a Lambda function
deploy_lambda() {
    local FUNCTION_NAME=$1
    local FUNCTION_DIR=$2
    local DESCRIPTION=$3
    
    echo -e "${YELLOW}Deploying $FUNCTION_NAME...${NC}"
    
    # Create deployment package directory
    DEPLOY_DIR="$LAMBDA_DIR/.deploy/$FUNCTION_NAME"
    rm -rf "$DEPLOY_DIR"
    mkdir -p "$DEPLOY_DIR"
    
    # Copy handler code
    cp "$FUNCTION_DIR/handler.py" "$DEPLOY_DIR/"
    
    # Install dependencies if requirements.txt exists
    if [ -f "$FUNCTION_DIR/requirements.txt" ]; then
        echo "Installing dependencies..."
        pip install -r "$FUNCTION_DIR/requirements.txt" -t "$DEPLOY_DIR" --quiet
    fi
    
    # Create ZIP package
    echo "Creating deployment package..."
    cd "$DEPLOY_DIR"
    ZIP_FILE="$LAMBDA_DIR/.deploy/${FUNCTION_NAME}.zip"
    zip -r "$ZIP_FILE" . -q
    cd - > /dev/null
    
    # Check if function exists
    if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$AWS_REGION" &> /dev/null; then
        echo "Updating existing function..."
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file "fileb://$ZIP_FILE" \
            --region "$AWS_REGION" \
            --output text > /dev/null
        
        # Update environment variables
        aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --environment "Variables={REDSHIFT_WORKGROUP_NAME=$REDSHIFT_WORKGROUP,REDSHIFT_DATABASE=$REDSHIFT_DATABASE}" \
            --region "$AWS_REGION" \
            --output text > /dev/null
        
        echo -e "${GREEN}✓ Updated function $FUNCTION_NAME${NC}"
    else
        echo "Creating new function..."
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --runtime python3.11 \
            --role "$ROLE_ARN" \
            --handler handler.lambda_handler \
            --zip-file "fileb://$ZIP_FILE" \
            --timeout 30 \
            --memory-size 256 \
            --environment "Variables={REDSHIFT_WORKGROUP_NAME=$REDSHIFT_WORKGROUP,REDSHIFT_DATABASE=$REDSHIFT_DATABASE}" \
            --description "$DESCRIPTION" \
            --region "$AWS_REGION" \
            --output text > /dev/null
        
        echo -e "${GREEN}✓ Created function $FUNCTION_NAME${NC}"
    fi
    
    # Clean up
    rm -rf "$DEPLOY_DIR"
    rm -f "$ZIP_FILE"
    
    echo ""
}

# Function to test a Lambda function
test_lambda() {
    local FUNCTION_NAME=$1
    local TEST_PAYLOAD=$2
    
    echo -e "${YELLOW}Testing $FUNCTION_NAME...${NC}"
    
    # Invoke function
    RESPONSE=$(aws lambda invoke \
        --function-name "$FUNCTION_NAME" \
        --payload "$TEST_PAYLOAD" \
        --region "$AWS_REGION" \
        /tmp/lambda-response.json 2>&1)
    
    # Check for errors
    if echo "$RESPONSE" | grep -q "StatusCode.*200"; then
        echo -e "${GREEN}✓ Function invoked successfully${NC}"
        echo "Response:"
        cat /tmp/lambda-response.json | python -m json.tool 2>/dev/null || cat /tmp/lambda-response.json
    else
        echo -e "${RED}✗ Function invocation failed${NC}"
        echo "$RESPONSE"
    fi
    
    rm -f /tmp/lambda-response.json
    echo ""
}

# Main deployment flow
main() {
    echo "Starting deployment..."
    echo ""
    
    # Pre-flight checks
    check_aws_cli
    check_aws_credentials
    
    # Get or create IAM role
    get_or_create_lambda_role
    
    # Deploy Lambda functions
    deploy_lambda \
        "$INVENTORY_FUNCTION" \
        "$LAMBDA_DIR/inventory_optimizer" \
        "Inventory optimization tools for Warehouse Managers"
    
    deploy_lambda \
        "$LOGISTICS_FUNCTION" \
        "$LAMBDA_DIR/logistics_optimizer" \
        "Logistics optimization tools for Field Engineers"
    
    deploy_lambda \
        "$SUPPLIER_FUNCTION" \
        "$LAMBDA_DIR/supplier_analyzer" \
        "Supplier analysis tools for Procurement Specialists"
    
    echo -e "${GREEN}=== Deployment Complete ===${NC}"
    echo ""
    echo "Lambda Functions:"
    echo "  - $INVENTORY_FUNCTION"
    echo "  - $LOGISTICS_FUNCTION"
    echo "  - $SUPPLIER_FUNCTION"
    echo ""
    
    # Test functions (optional)
    read -p "Do you want to test the Lambda functions? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${YELLOW}Testing Lambda functions...${NC}"
        echo ""
        
        # Test Inventory Optimizer
        test_lambda "$INVENTORY_FUNCTION" '{"action":"identify_low_stock","warehouse_code":"WH-001","threshold":1.0}'
        
        # Test Logistics Optimizer
        test_lambda "$LOGISTICS_FUNCTION" '{"action":"identify_delayed_orders","warehouse_code":"WH-001","days":7}'
        
        # Test Supplier Analyzer
        test_lambda "$SUPPLIER_FUNCTION" '{"action":"analyze_purchase_trends","days":90,"group_by":"month"}'
    fi
    
    echo -e "${GREEN}Done!${NC}"
}

# Run main function
main
