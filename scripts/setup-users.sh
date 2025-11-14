#!/bin/bash
# Setup Cognito users for each persona

set -e

echo "👥 Cognito User Setup Script"
echo "============================"

USER_POOL_ID="${1}"
REGION="${AWS_REGION:-us-east-1}"

if [ -z "$USER_POOL_ID" ]; then
    echo "Usage: $0 <USER_POOL_ID>"
    echo "Example: $0 us-east-1_xxxxx"
    exit 1
fi

echo "User Pool ID: $USER_POOL_ID"
echo "Region: $REGION"
echo ""

# Function to create user
create_user() {
    local username=$1
    local email=$2
    local group=$3
    
    echo "Creating user: $username ($email)"
    
    # Create user
    aws cognito-idp admin-create-user \
        --user-pool-id $USER_POOL_ID \
        --username $username \
        --user-attributes Name=email,Value=$email Name=email_verified,Value=true \
        --temporary-password "TempPass123!" \
        --region $REGION \
        --message-action SUPPRESS
    
    # Add to group
    aws cognito-idp admin-add-user-to-group \
        --user-pool-id $USER_POOL_ID \
        --username $username \
        --group-name $group \
        --region $REGION
    
    echo "✅ Created $username"
}

# Create Warehouse Manager users
echo "Creating Warehouse Manager users..."
create_user "warehouse_manager1" "wm1@example.com" "warehouse_managers"
create_user "warehouse_manager2" "wm2@example.com" "warehouse_managers"

# Create Field Engineer users
echo "Creating Field Engineer users..."
create_user "field_engineer1" "fe1@example.com" "field_engineers"
create_user "field_engineer2" "fe2@example.com" "field_engineers"

# Create Procurement Specialist users
echo "Creating Procurement Specialist users..."
create_user "procurement1" "ps1@example.com" "procurement_specialists"
create_user "procurement2" "ps2@example.com" "procurement_specialists"

echo ""
echo "✅ All users created successfully!"
echo ""
echo "User credentials:"
echo "- Username: <username>"
echo "- Temporary Password: TempPass123!"
echo ""
echo "Users must change password on first login."
echo ""
echo "To reset a user's password:"
echo "aws cognito-idp admin-set-user-password \\"
echo "  --user-pool-id $USER_POOL_ID \\"
echo "  --username <username> \\"
echo "  --password <new-password> \\"
echo "  --permanent"
