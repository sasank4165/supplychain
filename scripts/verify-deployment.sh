#!/bin/bash
# Deployment verification script
# Verifies that all resources are deployed and functional

set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default values
ENVIRONMENT="dev"
STACK_NAME=""
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --stack-name|-s)
            STACK_NAME="$2"
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
            echo "  --stack-name, -s NAME    CloudFormation stack name"
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

# Set stack name if not specified
if [ -z "$STACK_NAME" ]; then
    CONFIG_FILE="config/${ENVIRONMENT}.yaml"
    if [ -f "$CONFIG_FILE" ]; then
        PREFIX=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['project']['prefix'])" 2>/dev/null || echo "sc-agent-${ENVIRONMENT}")
    else
        PREFIX="sc-agent-${ENVIRONMENT}"
    fi
    STACK_NAME="${PREFIX}-stack"
fi

echo "🔍 Deployment Verification"
echo "Environment: $ENVIRONMENT"
echo "Stack Name: $STACK_NAME"
echo ""

VERIFICATION_FAILED=false

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
    VERIFICATION_FAILED=true
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}


# Get AWS region
AWS_REGION=${AWS_REGION:-$(aws configure get region)}
AWS_REGION=${AWS_REGION:-us-east-1}

# 1. Verify CloudFormation stack
echo "Checking CloudFormation stack..."
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].StackStatus" \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$STACK_STATUS" = "UPDATE_COMPLETE" ]; then
    print_success "CloudFormation stack is deployed: $STACK_STATUS"
else
    print_error "CloudFormation stack status: $STACK_STATUS"
fi

# Function to get stack output
get_output() {
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" \
        --output text 2>/dev/null || echo ""
}

# 2. Verify S3 buckets
echo ""
echo "Checking S3 buckets..."
ATHENA_BUCKET=$(get_output "AthenaResultsBucketName")

if [ -n "$ATHENA_BUCKET" ]; then
    if aws s3 ls "s3://$ATHENA_BUCKET" --region "$AWS_REGION" &> /dev/null; then
        print_success "Athena results bucket exists: $ATHENA_BUCKET"
    else
        print_error "Athena results bucket not accessible: $ATHENA_BUCKET"
    fi
else
    print_warning "Athena bucket name not found in stack outputs"
fi

# 3. Verify DynamoDB tables
echo ""
echo "Checking DynamoDB tables..."
CONVERSATION_TABLE=$(get_output "ConversationTableName")

if [ -n "$CONVERSATION_TABLE" ]; then
    TABLE_STATUS=$(aws dynamodb describe-table \
        --table-name "$CONVERSATION_TABLE" \
        --region "$AWS_REGION" \
        --query "Table.TableStatus" \
        --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$TABLE_STATUS" = "ACTIVE" ]; then
        print_success "Conversation table is active: $CONVERSATION_TABLE"
    else
        print_error "Conversation table status: $TABLE_STATUS"
    fi
else
    print_warning "Conversation table name not found in stack outputs"
fi


# 4. Verify Lambda functions
echo ""
echo "Checking Lambda functions..."

check_lambda() {
    local function_name=$1
    local display_name=$2
    
    if [ -n "$function_name" ]; then
        FUNCTION_STATE=$(aws lambda get-function \
            --function-name "$function_name" \
            --region "$AWS_REGION" \
            --query "Configuration.State" \
            --output text 2>/dev/null || echo "NOT_FOUND")
        
        if [ "$FUNCTION_STATE" = "Active" ]; then
            print_success "$display_name is active: $function_name"
        else
            print_error "$display_name state: $FUNCTION_STATE"
        fi
    else
        print_warning "$display_name not found in stack outputs"
    fi
}

SQL_EXECUTOR=$(get_output "SqlExecutorFunctionName")
INVENTORY_OPTIMIZER=$(get_output "InventoryOptimizerFunctionName")
LOGISTICS_AGENT=$(get_output "LogisticsAgentFunctionName")
SUPPLIER_ANALYZER=$(get_output "SupplierAnalyzerFunctionName")

check_lambda "$SQL_EXECUTOR" "SQL Executor function"
check_lambda "$INVENTORY_OPTIMIZER" "Inventory Optimizer function"
check_lambda "$LOGISTICS_AGENT" "Logistics Agent function"
check_lambda "$SUPPLIER_ANALYZER" "Supplier Analyzer function"

# 5. Verify Cognito User Pool
echo ""
echo "Checking Cognito User Pool..."
USER_POOL_ID=$(get_output "UserPoolId")

if [ -n "$USER_POOL_ID" ]; then
    POOL_STATUS=$(aws cognito-idp describe-user-pool \
        --user-pool-id "$USER_POOL_ID" \
        --region "$AWS_REGION" \
        --query "UserPool.Status" \
        --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$POOL_STATUS" = "Enabled" ] || [ -n "$POOL_STATUS" ]; then
        print_success "User Pool is active: $USER_POOL_ID"
    else
        print_error "User Pool status: $POOL_STATUS"
    fi
else
    print_warning "User Pool ID not found in stack outputs"
fi

# 6. Verify API Gateway
echo ""
echo "Checking API Gateway..."
API_ENDPOINT=$(get_output "APIEndpoint")

if [ -n "$API_ENDPOINT" ]; then
    print_success "API Gateway endpoint: $API_ENDPOINT"
    
    # Try to ping the API (health check)
    if [ "$VERBOSE" = true ]; then
        echo "  Testing API endpoint..."
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_ENDPOINT/health" 2>/dev/null || echo "000")
        
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
            echo "  API is responding (HTTP $HTTP_CODE)"
        else
            echo "  API may not be fully ready (HTTP $HTTP_CODE)"
        fi
    fi
else
    print_warning "API endpoint not found in stack outputs"
fi


# 7. Verify IAM roles
echo ""
echo "Checking IAM roles..."

# Check if Lambda execution role exists
LAMBDA_ROLE="${PREFIX}-lambda-exec"
if aws iam get-role --role-name "$LAMBDA_ROLE" --region "$AWS_REGION" &> /dev/null; then
    print_success "Lambda execution role exists: $LAMBDA_ROLE"
else
    print_warning "Lambda execution role not found: $LAMBDA_ROLE"
fi

# 8. Verify CloudWatch Log Groups
echo ""
echo "Checking CloudWatch Log Groups..."

check_log_group() {
    local function_name=$1
    local log_group="/aws/lambda/$function_name"
    
    if [ -n "$function_name" ]; then
        if aws logs describe-log-groups \
            --log-group-name-prefix "$log_group" \
            --region "$AWS_REGION" \
            --query "logGroups[?logGroupName=='$log_group']" \
            --output text | grep -q "$log_group"; then
            [ "$VERBOSE" = true ] && echo "  ✓ Log group exists: $log_group"
        else
            [ "$VERBOSE" = true ] && echo "  ⚠ Log group not found: $log_group"
        fi
    fi
}

check_log_group "$SQL_EXECUTOR"
check_log_group "$INVENTORY_OPTIMIZER"
check_log_group "$LOGISTICS_AGENT"
check_log_group "$SUPPLIER_ANALYZER"

print_success "CloudWatch Log Groups checked"

# 9. Verify resource tags
echo ""
echo "Checking resource tags..."

if [ -n "$CONVERSATION_TABLE" ]; then
    TAGS=$(aws dynamodb list-tags-of-resource \
        --resource-arn "arn:aws:dynamodb:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):table/$CONVERSATION_TABLE" \
        --region "$AWS_REGION" \
        --query "Tags[?Key=='Environment'].Value" \
        --output text 2>/dev/null || echo "")
    
    if [ "$TAGS" = "$ENVIRONMENT" ]; then
        print_success "Resources are properly tagged with Environment=$ENVIRONMENT"
    else
        print_warning "Resource tags may not be correctly applied"
    fi
fi

# Summary
echo ""
echo "========================================="
if [ "$VERIFICATION_FAILED" = true ]; then
    echo -e "${RED}❌ Verification FAILED${NC}"
    echo "Some resources are not properly deployed or accessible."
    echo "Review the errors above and check CloudFormation stack events."
    exit 1
else
    echo -e "${GREEN}✅ Verification PASSED${NC}"
    echo "All resources are deployed and accessible."
    echo ""
    echo "Deployment is ready for use!"
    exit 0
fi
