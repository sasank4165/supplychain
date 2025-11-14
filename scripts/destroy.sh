#!/bin/bash
# Destroy all infrastructure

set -e

echo "⚠️  DANGER: Infrastructure Destruction Script"
echo "=============================================="

ENVIRONMENT="${1:-prod}"

echo "Environment: $ENVIRONMENT"
echo ""
echo "This will DELETE all resources including:"
echo "- Lambda functions"
echo "- DynamoDB tables (with data)"
echo "- S3 buckets (with data)"
echo "- VPC and networking"
echo "- Cognito user pools"
echo "- All monitoring and alarms"
echo ""
read -p "Type 'DELETE' to confirm destruction: " CONFIRM

if [ "$CONFIRM" != "DELETE" ]; then
    echo "❌ Destruction cancelled"
    exit 1
fi

cd "$(dirname "$0")/../cdk"

echo "🗑️  Destroying stacks..."

# Destroy in reverse order
cdk destroy SupplyChainBackup-$ENVIRONMENT --force
cdk destroy SupplyChainMonitoring-$ENVIRONMENT --force
cdk destroy SupplyChainApp-$ENVIRONMENT --force
cdk destroy SupplyChainData-$ENVIRONMENT --force
cdk destroy SupplyChainSecurity-$ENVIRONMENT --force
cdk destroy SupplyChainNetwork-$ENVIRONMENT --force

echo ""
echo "⚠️  Note: Some resources with RETAIN policy must be deleted manually:"
echo "- S3 buckets"
echo "- DynamoDB tables"
echo "- KMS keys"
echo "- CloudWatch log groups"
echo ""
echo "To delete S3 buckets:"
echo "aws s3 rb s3://supply-chain-data-ACCOUNT-REGION --force"
echo "aws s3 rb s3://supply-chain-athena-ACCOUNT-REGION --force"
