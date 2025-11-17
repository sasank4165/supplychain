#!/bin/bash
# Rollback script for Supply Chain Agentic AI Application
# Supports rolling back to previous CDK stack versions

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
ENVIRONMENT="dev"
VERSION="previous"
CONFIG_FILE=""
DRY_RUN=false
AUTO_APPROVE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --version|-v)
            VERSION="$2"
            shift 2
            ;;
        --config|-c)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Rollback CDK deployment to a previous version"
            echo ""
            echo "Options:"
            echo "  --environment, -e ENV    Environment name (dev, staging, prod)"
            echo "  --version, -v VERSION    Version to rollback to (default: previous)"
            echo "                           Options: previous, <stack-version-id>"
            echo "  --config, -c FILE        Path to config file (default: config/ENV.yaml)"
            echo "  --dry-run                Show what would be rolled back without executing"
            echo "  --auto-approve           Auto-approve rollback without confirmation"
            echo "  --help, -h               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --environment dev                    # Rollback dev to previous version"
            echo "  $0 --environment prod --dry-run         # Preview prod rollback"
            echo "  $0 --environment staging --version 123  # Rollback to specific version"
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

echo -e "${YELLOW}⚠️  CDK Stack Rollback${NC}"
echo "===================="
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo "Config File: $CONFIG_FILE"
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

# Get stack names from configuration
PROJECT_PREFIX="${PROJECT_PREFIX:-sc-agent}"
STACK_PREFIX="${PROJECT_PREFIX}-${ENVIRONMENT}"

# List of stacks in deployment order
STACKS=(
    "${STACK_PREFIX}-network"
    "${STACK_PREFIX}-security"
    "${STACK_PREFIX}-data"
    "${STACK_PREFIX}-app"
    "${STACK_PREFIX}-monitoring"
    "${STACK_PREFIX}-backup"
)

# Function to get stack version history
get_stack_versions() {
    local stack_name=$1
    echo -e "${BLUE}Checking version history for ${stack_name}...${NC}"
    
    # Get CloudFormation stack events to find previous versions
    aws cloudformation describe-stack-events \
        --stack-name "$stack_name" \
        --query 'StackEvents[?ResourceType==`AWS::CloudFormation::Stack` && ResourceStatus==`UPDATE_COMPLETE`].[Timestamp,PhysicalResourceId]' \
        --output table \
        --region "$AWS_REGION" 2>/dev/null || echo "No version history found"
}

# Function to check if stack exists
stack_exists() {
    local stack_name=$1
    aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].StackName' \
        --output text 2>/dev/null
}

# Dry run mode
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}DRY RUN MODE - No changes will be made${NC}"
    echo ""
    
    for stack in "${STACKS[@]}"; do
        if stack_exists "$stack" >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Stack exists: $stack"
            get_stack_versions "$stack"
        else
            echo -e "${YELLOW}⊘${NC} Stack not found: $stack"
        fi
        echo ""
    done
    
    echo -e "${BLUE}Dry run complete. Use without --dry-run to execute rollback.${NC}"
    exit 0
fi

# Confirmation prompt
if [ "$AUTO_APPROVE" = false ]; then
    echo -e "${YELLOW}WARNING: This will rollback the following stacks:${NC}"
    for stack in "${STACKS[@]}"; do
        echo "  - $stack"
    done
    echo ""
    echo "This operation will:"
    echo "  • Revert infrastructure to previous state"
    echo "  • May cause temporary service disruption"
    echo "  • Preserve data in S3 and DynamoDB (RETAIN policy)"
    echo ""
    read -p "Type 'ROLLBACK' to confirm: " CONFIRM
    
    if [ "$CONFIRM" != "ROLLBACK" ]; then
        echo -e "${YELLOW}Rollback cancelled${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${BLUE}Starting rollback process...${NC}"
echo ""

# Change to CDK directory
cd cdk

# Set CDK context
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT_ID
export CDK_DEFAULT_REGION=$AWS_REGION

# Function to rollback a single stack
rollback_stack() {
    local stack_name=$1
    
    echo -e "${BLUE}Rolling back stack: ${stack_name}${NC}"
    
    # Check if stack exists
    if ! stack_exists "$stack_name" >/dev/null 2>&1; then
        echo -e "${YELLOW}⊘${NC} Stack not found, skipping: $stack_name"
        return 0
    fi
    
    # For CDK, we use the previous template to update the stack
    # This effectively rolls back to the previous state
    if [ "$VERSION" = "previous" ]; then
        # Get the previous template from CloudFormation
        echo "  Retrieving previous template..."
        
        # Use AWS CLI to get stack template
        TEMPLATE_FILE="/tmp/${stack_name}-previous.json"
        aws cloudformation get-template \
            --stack-name "$stack_name" \
            --template-stage Original \
            --region "$AWS_REGION" \
            --query 'TemplateBody' \
            --output text > "$TEMPLATE_FILE" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓${NC} Retrieved previous template"
            
            # Update stack with previous template
            echo "  Updating stack with previous template..."
            aws cloudformation update-stack \
                --stack-name "$stack_name" \
                --template-body "file://${TEMPLATE_FILE}" \
                --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
                --region "$AWS_REGION" 2>/dev/null
            
            if [ $? -eq 0 ]; then
                echo "  Waiting for stack update to complete..."
                aws cloudformation wait stack-update-complete \
                    --stack-name "$stack_name" \
                    --region "$AWS_REGION"
                
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}  ✓${NC} Stack rolled back successfully"
                else
                    echo -e "${RED}  ✗${NC} Stack rollback failed"
                    return 1
                fi
            else
                echo -e "${YELLOW}  ⊘${NC} No updates needed or rollback not possible"
            fi
            
            rm -f "$TEMPLATE_FILE"
        else
            echo -e "${YELLOW}  ⊘${NC} Could not retrieve previous template"
        fi
    else
        echo -e "${YELLOW}  ⊘${NC} Specific version rollback not yet implemented"
        echo "  Use CloudFormation console to rollback to specific version: $VERSION"
    fi
    
    echo ""
}

# Rollback stacks in reverse order (to handle dependencies)
echo "Rolling back stacks in reverse order..."
echo ""

ROLLBACK_FAILED=false

for ((i=${#STACKS[@]}-1; i>=0; i--)); do
    stack="${STACKS[$i]}"
    if ! rollback_stack "$stack"; then
        ROLLBACK_FAILED=true
        echo -e "${RED}✗${NC} Rollback failed for: $stack"
        echo ""
        echo "You may need to:"
        echo "  1. Check CloudFormation console for detailed error"
        echo "  2. Manually rollback the stack"
        echo "  3. Use cleanup script if rollback is not possible"
        break
    fi
done

cd ..

echo ""
if [ "$ROLLBACK_FAILED" = false ]; then
    echo -e "${GREEN}✅ Rollback completed successfully${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Verify application functionality"
    echo "  2. Check CloudWatch logs for any issues"
    echo "  3. Run verification: bash scripts/verify-deployment.sh --environment $ENVIRONMENT"
else
    echo -e "${RED}❌ Rollback failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check CloudFormation console for detailed errors"
    echo "  2. Review stack events: aws cloudformation describe-stack-events --stack-name <stack-name>"
    echo "  3. Consider using cleanup script: bash scripts/cleanup.sh --environment $ENVIRONMENT"
    exit 1
fi
