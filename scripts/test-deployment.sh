#!/bin/bash
# Test deployed infrastructure

set -e

echo "🧪 Testing Deployed Infrastructure"
echo "==================================="

ENVIRONMENT="${1:-prod}"
REGION="${AWS_REGION:-us-east-1}"

echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo ""

# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name SupplyChainApp-$ENVIRONMENT \
    --query "Stacks[0].Outputs[?OutputKey=='APIEndpoint'].OutputValue" \
    --output text \
    --region $REGION)

echo "API Endpoint: $API_ENDPOINT"

# Test health endpoint
echo ""
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "${API_ENDPOINT}health")
echo "Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# Test Lambda functions
echo ""
echo "Testing Lambda functions..."

# Test inventory optimizer
echo "Testing inventory optimizer..."
aws lambda invoke \
    --function-name supply-chain-inventory-optimizer \
    --payload '{"tool_name":"identify_stockout_risks","input":{"warehouse_code":"WH01","days_ahead":7}}' \
    --region $REGION \
    /tmp/inventory-response.json

if [ $? -eq 0 ]; then
    echo "✅ Inventory optimizer working"
    cat /tmp/inventory-response.json
else
    echo "❌ Inventory optimizer failed"
fi

# Test logistics optimizer
echo ""
echo "Testing logistics optimizer..."
aws lambda invoke \
    --function-name supply-chain-logistics-optimizer \
    --payload '{"tool_name":"calculate_warehouse_capacity","input":{"warehouse_code":"WH01"}}' \
    --region $REGION \
    /tmp/logistics-response.json

if [ $? -eq 0 ]; then
    echo "✅ Logistics optimizer working"
    cat /tmp/logistics-response.json
else
    echo "❌ Logistics optimizer failed"
fi

# Test supplier analyzer
echo ""
echo "Testing supplier analyzer..."
aws lambda invoke \
    --function-name supply-chain-supplier-analyzer \
    --payload '{"tool_name":"analyze_supplier_performance","input":{"time_period_days":90}}' \
    --region $REGION \
    /tmp/supplier-response.json

if [ $? -eq 0 ]; then
    echo "✅ Supplier analyzer working"
    cat /tmp/supplier-response.json
else
    echo "❌ Supplier analyzer failed"
fi

# Check DynamoDB tables
echo ""
echo "Checking DynamoDB tables..."
aws dynamodb describe-table \
    --table-name supply-chain-agent-sessions \
    --region $REGION \
    --query "Table.TableStatus" \
    --output text

if [ $? -eq 0 ]; then
    echo "✅ DynamoDB tables accessible"
else
    echo "❌ DynamoDB tables not accessible"
fi

# Check S3 buckets
echo ""
echo "Checking S3 buckets..."
aws s3 ls | grep supply-chain

if [ $? -eq 0 ]; then
    echo "✅ S3 buckets accessible"
else
    echo "❌ S3 buckets not accessible"
fi

echo ""
echo "✅ All tests completed!"
