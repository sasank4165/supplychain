# Lambda Functions for Supply Chain MVP

This directory contains the Lambda function implementations for the three specialized agents in the Supply Chain AI system.

## Overview

The Lambda functions provide domain-specific optimization and analysis tools that are invoked by the specialized agents through the Bedrock orchestration layer.

### Functions

1. **Inventory Optimizer** (`inventory_optimizer/`)
   - Function Name: `supply-chain-inventory-optimizer`
   - Purpose: Inventory optimization tools for Warehouse Managers
   - Tools:
     - `calculate_reorder_point`: Calculate optimal reorder point for a product
     - `identify_low_stock`: Find products below stock threshold
     - `forecast_demand`: Forecast future demand using historical data
     - `identify_stockout_risk`: Identify products at risk of stockout

2. **Logistics Optimizer** (`logistics_optimizer/`)
   - Function Name: `supply-chain-logistics-optimizer`
   - Purpose: Logistics optimization tools for Field Engineers
   - Tools:
     - `optimize_delivery_route`: Optimize delivery routes by area and priority
     - `check_fulfillment_status`: Get detailed order fulfillment status
     - `identify_delayed_orders`: Find orders past their delivery date
     - `calculate_warehouse_capacity`: Calculate warehouse capacity utilization

3. **Supplier Analyzer** (`supplier_analyzer/`)
   - Function Name: `supply-chain-supplier-analyzer`
   - Purpose: Supplier analysis tools for Procurement Specialists
   - Tools:
     - `analyze_supplier_performance`: Analyze supplier performance metrics
     - `compare_supplier_costs`: Compare costs across suppliers
     - `identify_cost_savings`: Identify cost savings opportunities
     - `analyze_purchase_trends`: Analyze purchase order trends over time

## Architecture

Each Lambda function:
- Uses the Redshift Data API to query the supply chain database
- Accepts an `action` parameter to route to the appropriate tool
- Returns structured JSON responses with success/error status
- Has a 30-second timeout and 256MB memory allocation
- Uses Python 3.11 runtime

## Deployment

### Prerequisites

- AWS CLI installed and configured
- Python 3.11+ installed
- AWS credentials with permissions to:
  - Create/update Lambda functions
  - Create/manage IAM roles
  - Access Redshift Data API

### Deployment Scripts

Two deployment scripts are provided:

**Linux/Mac:**
```bash
cd mvp/scripts
chmod +x deploy_lambda.sh
./deploy_lambda.sh
```

**Windows (PowerShell):**
```powershell
cd mvp\scripts
.\deploy_lambda.ps1
```

### Environment Variables

The deployment script configures these environment variables for each function:
- `REDSHIFT_WORKGROUP_NAME`: Redshift Serverless workgroup name (default: `supply-chain-mvp`)
- `REDSHIFT_DATABASE`: Database name (default: `supply_chain_db`)

### Custom Deployment

You can customize the deployment by setting environment variables:

```bash
# Linux/Mac
export AWS_REGION=us-west-2
export REDSHIFT_WORKGROUP=my-workgroup
export REDSHIFT_DATABASE=my_database
./deploy_lambda.sh

# Windows PowerShell
.\deploy_lambda.ps1 -AwsRegion "us-west-2" -RedshiftWorkgroup "my-workgroup" -RedshiftDatabase "my_database"
```

## IAM Permissions

The Lambda functions require an IAM role with the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
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
}
```

The deployment script automatically creates this role if it doesn't exist.

## Testing

### Manual Testing via AWS Console

1. Go to AWS Lambda Console
2. Select the function to test
3. Create a test event with the appropriate payload
4. Click "Test" to invoke the function

### Example Test Payloads

**Inventory Optimizer - Identify Low Stock:**
```json
{
  "action": "identify_low_stock",
  "warehouse_code": "WH-001",
  "threshold": 1.0
}
```

**Inventory Optimizer - Calculate Reorder Point:**
```json
{
  "action": "calculate_reorder_point",
  "product_code": "PROD-001",
  "warehouse_code": "WH-001"
}
```

**Logistics Optimizer - Identify Delayed Orders:**
```json
{
  "action": "identify_delayed_orders",
  "warehouse_code": "WH-001",
  "days": 7
}
```

**Logistics Optimizer - Optimize Delivery Route:**
```json
{
  "action": "optimize_delivery_route",
  "order_ids": ["SO-001", "SO-002", "SO-003"],
  "warehouse_code": "WH-001"
}
```

**Supplier Analyzer - Analyze Performance:**
```json
{
  "action": "analyze_supplier_performance",
  "supplier_code": "SUP-001",
  "days": 90
}
```

**Supplier Analyzer - Compare Costs:**
```json
{
  "action": "compare_supplier_costs",
  "product_group": "Electronics",
  "suppliers": ["SUP-001", "SUP-002"]
}
```

### Testing via AWS CLI

```bash
# Test Inventory Optimizer
aws lambda invoke \
  --function-name supply-chain-inventory-optimizer \
  --payload '{"action":"identify_low_stock","warehouse_code":"WH-001","threshold":1.0}' \
  response.json

# View response
cat response.json | python -m json.tool
```

### Automated Testing

The deployment script includes an optional testing phase that invokes each function with sample payloads.

## Response Format

All Lambda functions return responses in this format:

**Success Response:**
```json
{
  "statusCode": 200,
  "body": "{\"success\": true, \"data\": {...}}"
}
```

**Error Response:**
```json
{
  "statusCode": 400,
  "body": "{\"success\": false, \"error\": \"Error message\"}"
}
```

## Monitoring

### CloudWatch Logs

Each Lambda function logs to CloudWatch Logs:
- Log Group: `/aws/lambda/<function-name>`
- Logs include:
  - Function invocations
  - SQL queries executed
  - Errors and exceptions
  - Execution duration

### CloudWatch Metrics

Monitor these metrics in CloudWatch:
- Invocations: Number of times function is invoked
- Duration: Execution time
- Errors: Number of failed invocations
- Throttles: Number of throttled invocations

## Cost Optimization

Lambda costs are based on:
- Number of requests: $0.20 per 1M requests
- Duration: $0.0000166667 per GB-second

**Estimated costs for moderate usage (1000 invocations/day):**
- Requests: ~$0.006/day
- Duration (256MB, 5s avg): ~$0.02/day
- **Total: ~$0.78/month**

## Troubleshooting

### Common Issues

**1. Function timeout**
- Increase timeout in Lambda configuration (max 15 minutes)
- Optimize SQL queries for better performance

**2. Permission denied errors**
- Verify IAM role has Redshift Data API permissions
- Check Redshift workgroup security settings

**3. Query execution errors**
- Verify Redshift workgroup and database names
- Check that sample data has been loaded
- Review CloudWatch logs for SQL errors

**4. Import errors**
- Ensure all dependencies are included in deployment package
- Verify Python version compatibility (3.11)

### Debug Mode

To enable detailed logging, add this to the handler code:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Local Testing

You can test Lambda functions locally using the AWS SAM CLI:

```bash
# Install SAM CLI
pip install aws-sam-cli

# Test function locally
sam local invoke supply-chain-inventory-optimizer \
  --event test-event.json
```

### Adding New Tools

To add a new tool to a Lambda function:

1. Add the tool function to `handler.py`
2. Update the `lambda_handler` routing logic
3. Update the function documentation
4. Add test cases
5. Redeploy using the deployment script

## Integration

The Lambda functions are invoked by the specialized agents through the `LambdaClient` wrapper:

```python
from mvp.aws.lambda_client import LambdaClient, InventoryOptimizerClient

# Initialize clients
lambda_client = LambdaClient(region='us-east-1')
inventory_client = InventoryOptimizerClient(
    lambda_client=lambda_client,
    function_name='supply-chain-inventory-optimizer'
)

# Invoke tool
result = inventory_client.identify_low_stock(
    warehouse_code='WH-001',
    threshold=1.0
)
```

## Security

- Lambda functions use IAM roles for authentication
- No hardcoded credentials in code
- Redshift Data API uses temporary credentials
- All data in transit is encrypted (TLS)
- CloudWatch logs may contain sensitive data - configure retention policies

## Next Steps

After deploying Lambda functions:

1. Verify functions are deployed: `aws lambda list-functions`
2. Test each function with sample payloads
3. Review CloudWatch logs for any errors
4. Update `config.yaml` with function names
5. Proceed to implement specialized agents (Task 8)

## Support

For issues or questions:
- Check CloudWatch logs for detailed error messages
- Review the deployment script output
- Verify AWS credentials and permissions
- Ensure Redshift Serverless is running and accessible
