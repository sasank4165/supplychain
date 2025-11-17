#!/bin/bash
# Cleanup script for Supply Chain Agentic AI Application
# Safely removes infrastructure with data preservation options

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
ENVIRONMENT="dev"
CONFIG_FILE=""
PRESERVE_DATA=true
FORCE_DELETE=false
DRY_RUN=false
DELETE_LOGS=false

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
        --no-preserve-data)
            PRESERVE_DATA=false
            shift
            ;;
        --force-delete)
            FORCE_DELETE=true
            PRESERVE_DATA=false
            shift
            ;;
        --delete-logs)
            DELETE_LOGS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Cleanup CDK deployment and associated resources"
            echo ""
            echo "Options:"
            echo "  --environment, -e ENV    Environment name (dev, staging, prod)"
            echo "  --config, -c FILE        Path to config file (default: config/ENV.yaml)"
            echo "  --no-preserve-data       Delete S3 and DynamoDB data (default: preserve)"
            echo "  --force-delete           Force delete all resources including data"
            echo "  --delete-logs            Delete CloudWatch log groups"
            echo "  --dry-run                Show what would be deleted without executing"
            echo "  --help, -h               Show this help message"
            echo ""
            echo "Data Preservation:"
            echo "  By default, S3 buckets and DynamoDB tables with RETAIN policy are preserved."
            echo "  Use --no-preserve-data to delete data resources."
            echo "  Use --force-delete for complete removal of all resources."
            echo ""
            echo "Examples:"
            echo "  $0 --environment dev                      # Cleanup dev, preserve data"
            echo "  $0 --environment dev --dry-run            # Preview cleanup"
            echo "  $0 --environment prod --no-preserve-data  # Cleanup prod, delete data"
            echo "  $0 --environment dev --force-delete       # Complete removal"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Set config file if not specified
if [ -z "$CONFIG_FILE" ]; then
    CONFIG_FILE="config/${ENVIRONMENT}.yaml"
fi

echo -e "${YELLOW}⚠️  Infrastructure Cleanup${NC}"
echo "========================"
echo "Environment: $ENVIRONMENT"
echo "Config File: $CONFIG_FILE"
echo "Preserve Data: $PRESERVE_DATA"
echo "Force Delete: $FORCE_DELETE"
echo "Delete Logs: $DELETE_LOGS"
echo ""

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}✗${NC} Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Load configuration
echo "Loading configuration..."
if bash scripts/load-config.sh --environment "$ENVIRONMENT" --config "$CONFIG_FILE" --export; then
    source .env
    echo -e "${GREEN}✓${NC} Configuration loaded"
else
    echo -e "${RED}✗${NC} Failed to load configuration"
    exit 1
fi
echo ""

# Get resource names from configuration
PROJECT_PREFIX="${PROJECT_PREFIX:-sc-agent}"
STACK_PREFIX="${PROJECT_PREFIX}-${ENVIRONMENT}"

# List of stacks in reverse deployment order
STACKS=(
    "${STACK_PREFIX}-backup"
    "${STACK_PREFIX}-monitoring"
    "${STACK_PREFIX}-app"
    "${STACK_PREFIX}-data"
    "${STACK_PREFIX}-security"
    "${STACK_PREFIX}-network"
)

# Function to check if stack exists
stack_exists() {
    local stack_name=$1
    aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].StackName' \
        --output text 2>/dev/null
}

# Function to list S3 buckets for environment
list_s3_buckets() {
    echo -e "${BLUE}S3 Buckets:${NC}"
    aws s3api list-buckets \
        --query "Buckets[?contains(Name, '${PROJECT_PREFIX}')].Name" \
        --output text \
        --region "$AWS_REGION" 2>/dev/null | tr '\t' '\n' | grep "${ENVIRONMENT}" || echo "  None found"
}

# Function to list DynamoDB tables for environment
list_dynamodb_tables() {
    echo -e "${BLUE}DynamoDB Tables:${NC}"
    aws dynamodb list-tables \
        --region "$AWS_REGION" \
        --query "TableNames[?contains(@, '${PROJECT_PREFIX}')]" \
        --output text 2>/dev/null | tr '\t' '\n' | grep "${ENVIRONMENT}" || echo "  None found"
}

# Function to list CloudWatch log groups
list_log_groups() {
    echo -e "${BLUE}CloudWatch Log Groups:${NC}"
    aws logs describe-log-groups \
        --log-group-name-prefix "/aws/lambda/${PROJECT_PREFIX}" \
        --region "$AWS_REGION" \
        --query 'logGroups[*].logGroupName' \
        --output text 2>/dev/null | tr '\t' '\n' | grep "${ENVIRONMENT}" || echo "  None found"
}

# Function to empty S3 bucket
empty_s3_bucket() {
    local bucket_name=$1
    echo "  Emptying bucket: $bucket_name"
    
    # Delete all versions and delete markers
    aws s3api list-object-versions \
        --bucket "$bucket_name" \
        --region "$AWS_REGION" \
        --output json \
        --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' 2>/dev/null | \
    jq -r '.Objects[]? | "--key \"\(.Key)\" --version-id \"\(.VersionId)\""' | \
    xargs -I {} aws s3api delete-object --bucket "$bucket_name" --region "$AWS_REGION" {} 2>/dev/null || true
    
    # Delete delete markers
    aws s3api list-object-versions \
        --bucket "$bucket_name" \
        --region "$AWS_REGION" \
        --output json \
        --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' 2>/dev/null | \
    jq -r '.Objects[]? | "--key \"\(.Key)\" --version-id \"\(.VersionId)\""' | \
    xargs -I {} aws s3api delete-object --bucket "$bucket_name" --region "$AWS_REGION" {} 2>/dev/null || true
    
    # Delete remaining objects
    aws s3 rm "s3://${bucket_name}" --recursive --region "$AWS_REGION" 2>/dev/null || true
    
    echo -e "${GREEN}  ✓${NC} Bucket emptied"
}

# Function to delete S3 bucket
delete_s3_bucket() {
    local bucket_name=$1
    echo "  Deleting bucket: $bucket_name"
    
    # Empty bucket first
    empty_s3_bucket "$bucket_name"
    
    # Delete bucket
    aws s3api delete-bucket \
        --bucket "$bucket_name" \
        --region "$AWS_REGION" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓${NC} Bucket deleted"
    else
        echo -e "${YELLOW}  ⊘${NC} Could not delete bucket (may not exist)"
    fi
}

# Function to delete DynamoDB table
delete_dynamodb_table() {
    local table_name=$1
    echo "  Deleting table: $table_name"
    
    # Disable deletion protection if enabled
    aws dynamodb update-table \
        --table-name "$table_name" \
        --no-deletion-protection-enabled \
        --region "$AWS_REGION" 2>/dev/null || true
    
    # Delete table
    aws dynamodb delete-table \
        --table-name "$table_name" \
        --region "$AWS_REGION" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓${NC} Table deletion initiated"
    else
        echo -e "${YELLOW}  ⊘${NC} Could not delete table (may not exist)"
    fi
}

# Function to delete CloudWatch log group
delete_log_group() {
    local log_group=$1
    echo "  Deleting log group: $log_group"
    
    aws logs delete-log-group \
        --log-group-name "$log_group" \
        --region "$AWS_REGION" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓${NC} Log group deleted"
    else
        echo -e "${YELLOW}  ⊘${NC} Could not delete log group (may not exist)"
    fi
}

# Dry run mode
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}DRY RUN MODE - No changes will be made${NC}"
    echo ""
    
    echo "CloudFormation Stacks to be deleted:"
    for stack in "${STACKS[@]}"; do
        if stack_exists "$stack" >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $stack"
        else
            echo -e "  ${YELLOW}⊘${NC} $stack (not found)"
        fi
    done
    echo ""
    
    if [ "$PRESERVE_DATA" = false ]; then
        list_s3_buckets
        echo ""
        list_dynamodb_tables
        echo ""
    else
        echo -e "${BLUE}Data resources will be preserved (S3, DynamoDB)${NC}"
        echo ""
    fi
    
    if [ "$DELETE_LOGS" = true ]; then
        list_log_groups
        echo ""
    fi
    
    echo -e "${BLUE}Dry run complete. Use without --dry-run to execute cleanup.${NC}"
    exit 0
fi

# Confirmation prompt
if [ "$FORCE_DELETE" = true ]; then
    echo -e "${RED}⚠️  FORCE DELETE MODE - ALL DATA WILL BE PERMANENTLY DELETED${NC}"
fi

echo -e "${YELLOW}WARNING: This will delete the following resources:${NC}"
echo ""
echo "CloudFormation Stacks:"
for stack in "${STACKS[@]}"; do
    echo "  - $stack"
done
echo ""

if [ "$PRESERVE_DATA" = false ]; then
    echo "Data Resources (WILL BE DELETED):"
    echo "  - S3 buckets and all contents"
    echo "  - DynamoDB tables and all data"
    echo ""
fi

if [ "$DELETE_LOGS" = true ]; then
    echo "CloudWatch Logs (WILL BE DELETED):"
    echo "  - All log groups for this environment"
    echo ""
fi

echo "This operation:"
if [ "$PRESERVE_DATA" = true ]; then
    echo "  • Will preserve S3 buckets and DynamoDB tables"
    echo "  • Will delete Lambda functions, API Gateway, Cognito, etc."
    echo "  • Can be reversed by redeploying"
else
    echo "  • Will permanently delete ALL resources including data"
    echo "  • CANNOT be reversed - data will be lost"
    echo "  • Requires manual recreation and data restoration"
fi
echo ""

if [ "$FORCE_DELETE" = true ]; then
    read -p "Type 'DELETE-EVERYTHING' to confirm complete deletion: " CONFIRM
    REQUIRED_CONFIRM="DELETE-EVERYTHING"
else
    read -p "Type 'DELETE' to confirm cleanup: " CONFIRM
    REQUIRED_CONFIRM="DELETE"
fi

if [ "$CONFIRM" != "$REQUIRED_CONFIRM" ]; then
    echo -e "${YELLOW}Cleanup cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Starting cleanup process...${NC}"
echo ""

# Change to CDK directory
cd cdk

# Set CDK context
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT_ID
export CDK_DEFAULT_REGION=$AWS_REGION

# Delete CloudFormation stacks
echo "Deleting CloudFormation stacks..."
echo ""

CLEANUP_FAILED=false

for stack in "${STACKS[@]}"; do
    if stack_exists "$stack" >/dev/null 2>&1; then
        echo -e "${BLUE}Deleting stack: ${stack}${NC}"
        
        cdk destroy "$stack" \
            --force \
            -c environment="$ENVIRONMENT" \
            -c config_file="../$CONFIG_FILE" 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Stack deleted: $stack"
        else
            echo -e "${RED}✗${NC} Failed to delete stack: $stack"
            CLEANUP_FAILED=true
        fi
        echo ""
    else
        echo -e "${YELLOW}⊘${NC} Stack not found, skipping: $stack"
        echo ""
    fi
done

cd ..

# Delete data resources if not preserving
if [ "$PRESERVE_DATA" = false ]; then
    echo ""
    echo -e "${BLUE}Deleting data resources...${NC}"
    echo ""
    
    # Delete S3 buckets
    echo "Deleting S3 buckets..."
    BUCKETS=$(aws s3api list-buckets \
        --query "Buckets[?contains(Name, '${PROJECT_PREFIX}')].Name" \
        --output text \
        --region "$AWS_REGION" 2>/dev/null | tr '\t' '\n' | grep "${ENVIRONMENT}" || true)
    
    if [ -n "$BUCKETS" ]; then
        while IFS= read -r bucket; do
            if [ -n "$bucket" ]; then
                delete_s3_bucket "$bucket"
            fi
        done <<< "$BUCKETS"
    else
        echo "  No S3 buckets found"
    fi
    echo ""
    
    # Delete DynamoDB tables
    echo "Deleting DynamoDB tables..."
    TABLES=$(aws dynamodb list-tables \
        --region "$AWS_REGION" \
        --query "TableNames[?contains(@, '${PROJECT_PREFIX}')]" \
        --output text 2>/dev/null | tr '\t' '\n' | grep "${ENVIRONMENT}" || true)
    
    if [ -n "$TABLES" ]; then
        while IFS= read -r table; do
            if [ -n "$table" ]; then
                delete_dynamodb_table "$table"
            fi
        done <<< "$TABLES"
        
        echo "  Waiting for table deletions to complete..."
        sleep 10
    else
        echo "  No DynamoDB tables found"
    fi
    echo ""
fi

# Delete CloudWatch log groups if requested
if [ "$DELETE_LOGS" = true ]; then
    echo ""
    echo -e "${BLUE}Deleting CloudWatch log groups...${NC}"
    echo ""
    
    LOG_GROUPS=$(aws logs describe-log-groups \
        --log-group-name-prefix "/aws/lambda/${PROJECT_PREFIX}" \
        --region "$AWS_REGION" \
        --query 'logGroups[*].logGroupName' \
        --output text 2>/dev/null | tr '\t' '\n' | grep "${ENVIRONMENT}" || true)
    
    if [ -n "$LOG_GROUPS" ]; then
        while IFS= read -r log_group; do
            if [ -n "$log_group" ]; then
                delete_log_group "$log_group"
            fi
        done <<< "$LOG_GROUPS"
    else
        echo "  No log groups found"
    fi
    echo ""
fi

# Summary
echo ""
if [ "$CLEANUP_FAILED" = false ]; then
    echo -e "${GREEN}✅ Cleanup completed successfully${NC}"
    echo ""
    
    if [ "$PRESERVE_DATA" = true ]; then
        echo "Data resources preserved:"
        echo "  • S3 buckets (may incur storage costs)"
        echo "  • DynamoDB tables (may incur storage costs)"
        echo ""
        echo "To delete data resources later:"
        echo "  bash scripts/cleanup.sh --environment $ENVIRONMENT --no-preserve-data"
    else
        echo "All resources deleted including data"
    fi
    
    if [ "$DELETE_LOGS" = false ]; then
        echo ""
        echo "CloudWatch logs preserved. To delete:"
        echo "  bash scripts/cleanup.sh --environment $ENVIRONMENT --delete-logs"
    fi
else
    echo -e "${RED}❌ Cleanup completed with errors${NC}"
    echo ""
    echo "Some resources may not have been deleted. Check:"
    echo "  1. CloudFormation console for stack status"
    echo "  2. S3 console for remaining buckets"
    echo "  3. DynamoDB console for remaining tables"
    echo ""
    echo "You may need to manually delete remaining resources"
    exit 1
fi
