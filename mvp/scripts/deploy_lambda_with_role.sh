#!/bin/bash

# Deploy Lambda Functions with Existing IAM Role
# Use this script when you don't have permission to create IAM roles

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
REDSHIFT_WORKGROUP="${REDSHIFT_WORKGROUP:-supply-chain-mvp}"
REDSHIFT_DATABASE="${REDSHIFT_DATABASE:-supply_chain_db}"

# Lambda function names
INVENTORY_FUNCTION="supply-chain-inventory-optimizer"
LOGISTICS_FUNCTION="supply-chain-logistics-optimizer"
SUPPLIER_FUNCTION="supply-chain-supplier-analyzer"

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="$PROJECT_ROOT/lambda_functions"

echo -e "${GREEN}=== Supply Chain Lambda Deployment (With Existing Role) ===${NC}"
echo "Region: $AWS_REGION"
echo "Redshift Workgroup: $REDSHIFT_WORKGROUP"
echo "Redshift Database: $REDSHIFT_DATABASE"
echo ""

# Check for LAMBDA_ROLE_ARN environment variable
if [ -z "$LAMBDA_ROLE_ARN" ]; then
    echo -e "${YELLOW}No LAMBDA_ROLE_ARN environment variable found.${NC}"
    echo ""
    echo "Please provide an existing Lambda execution role ARN."
    echo ""
    echo "To find existing roles:"
    echo "  aws iam list-roles --query 'Roles[?contains(RoleName, \`Lambda\`)].RoleName'"
    echo ""
    echo "To get role ARN:"
    echo "  aws iam get-role --role-name YOUR_ROLE_NAME --query 'Role.Arn' --output text"
    echo ""
    read -p "Enter Lambda Role ARN: " LAMBDA_ROLE_ARN
    
    if [ -z "$LAMBDA_ROLE_ARN" ]; then
        echo -e "${RED}Error: Role ARN is required${NC}"
        exit 1
    fi
fi

echo "Using IAM Role: $LAMBDA_ROLE_ARN"
echo ""

# Verify role exists
echo -e "${YELLOW}Verifying IAM role...${NC}"
ROLE_NAME=$(echo "$LAMBDA_ROLE_ARN" | awk -F'/' '{print $NF}')
if aws iam get-role --role-name "$ROLE_NAME" &> /dev/null; then
    echo -e "${GREEN}✓ IAM role verified${NC}"
else
    echo -e "${RED}Error: Role $ROLE_NAME not found${NC}"
    exit 1
fi
echo ""

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
            --role "$LAMBDA_ROLE_ARN" \
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

# Main deployment
echo "Starting deployment..."
echo ""

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
echo ""
echo "Next steps:"
echo "1. Verify functions: aws lambda list-functions --query 'Functions[?starts_with(FunctionName, \`supply-chain\`)].FunctionName'"
echo "2. Update mvp/config.yaml with function names"
echo "3. Restart your Streamlit app"
