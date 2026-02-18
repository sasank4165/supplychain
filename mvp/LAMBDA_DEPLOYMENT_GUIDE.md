# Lambda Functions Deployment Guide

## Overview
This guide will help you deploy the three specialized Lambda functions required for the Supply Chain AI Assistant:
1. **Inventory Optimizer** - For Warehouse Manager persona
2. **Logistics Optimizer** - For Field Engineer persona
3. **Supplier Analyzer** - For Procurement Specialist persona

## Prerequisites

### 1. AWS CLI Installed
Check if AWS CLI is installed:
```bash
aws --version
```

If not installed, install it:
- **Windows**: Download from https://aws.amazon.com/cli/
- **Linux/Mac**: 
  ```bash
  pip install awscli
  ```

### 2. AWS Credentials Configured
Since you're using Microsoft SSO, you need to configure AWS CLI with your SSO credentials.

**Option A: Use SageMaker IAM Role (Recommended)**
If you're deploying from SageMaker, the instance already has IAM credentials. Just verify:
```bash
aws sts get-caller-identity
```

**Option B: Configure SSO**
```bash
aws configure sso
# Follow the prompts to set up SSO
```

### 3. Required IAM Permissions
Your IAM role/user needs these permissions:
- `lambda:CreateFunction`
- `lambda:UpdateFunctionCode`
- `lambda:UpdateFunctionConfiguration`
- `lambda:GetFunction`
- `iam:CreateRole`
- `iam:AttachRolePolicy`
- `iam:PutRolePolicy`
- `iam:GetRole`
- `redshift-data:*` (for Lambda functions to access Redshift)

### 4. Python 3.11+ Installed
Check Python version:
```bash
python --version
```

### 5. Redshift Serverless Running
Ensure your Redshift Serverless workgroup is running and accessible.

## Deployment Steps

### Step 1: Navigate to Scripts Directory
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp/scripts
```

### Step 2: Review Configuration
The deployment script will use these default values:
- **AWS Region**: `us-east-1`
- **Redshift Workgroup**: `supply-chain-mvp`
- **Redshift Database**: `supply_chain_db`
- **IAM Role Name**: `SupplyChainLambdaRole`

To customize, set environment variables:
```bash
export AWS_REGION=us-west-2
export REDSHIFT_WORKGROUP=my-workgroup
export REDSHIFT_DATABASE=my_database
```

### Step 3: Make Script Executable (Linux/Mac)
```bash
chmod +x deploy_lambda.sh
```

### Step 4: Run Deployment Script

**On Linux/Mac/SageMaker:**
```bash
./deploy_lambda.sh
```

**On Windows (PowerShell):**
```powershell
.\deploy_lambda.ps1
```

### Step 5: Monitor Deployment
The script will:
1. ✓ Check AWS CLI installation
2. ✓ Verify AWS credentials
3. ✓ Create/verify IAM role for Lambda functions
4. ✓ Package each Lambda function
5. ✓ Deploy/update functions in AWS Lambda
6. ✓ Configure environment variables
7. ✓ Optionally test each function

Expected output:
```
=== Supply Chain Lambda Deployment ===
Region: us-east-1
Redshift Workgroup: supply-chain-mvp
Redshift Database: supply_chain_db

✓ AWS CLI found
✓ AWS credentials configured
✓ IAM role SupplyChainLambdaRole already exists

Deploying supply-chain-inventory-optimizer...
✓ Created function supply-chain-inventory-optimizer

Deploying supply-chain-logistics-optimizer...
✓ Created function supply-chain-logistics-optimizer

Deploying supply-chain-supplier-analyzer...
✓ Created function supply-chain-supplier-analyzer

=== Deployment Complete ===
```

### Step 6: Verify Deployment
Check that functions are deployed:
```bash
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `supply-chain`)].FunctionName'
```

Expected output:
```json
[
    "supply-chain-inventory-optimizer",
    "supply-chain-logistics-optimizer",
    "supply-chain-supplier-analyzer"
]
```

## Testing Lambda Functions

### Test via AWS CLI

**Test Inventory Optimizer:**
```bash
aws lambda invoke \
  --function-name supply-chain-inventory-optimizer \
  --payload '{"action":"identify_low_stock","warehouse_code":"WH-001","threshold":1.0}' \
  response.json

cat response.json
```

**Test Logistics Optimizer:**
```bash
aws lambda invoke \
  --function-name supply-chain-logistics-optimizer \
  --payload '{"action":"identify_delayed_orders","warehouse_code":"WH-001","days":7}' \
  response.json

cat response.json
```

**Test Supplier Analyzer:**
```bash
aws lambda invoke \
  --function-name supply-chain-supplier-analyzer \
  --payload '{"action":"analyze_purchase_trends","days":90,"group_by":"month"}' \
  response.json

cat response.json
```

### Test via AWS Console

1. Go to AWS Lambda Console: https://console.aws.amazon.com/lambda/
2. Select one of the functions (e.g., `supply-chain-inventory-optimizer`)
3. Click "Test" tab
4. Create a new test event with this payload:
   ```json
   {
     "action": "identify_low_stock",
     "warehouse_code": "WH-001",
     "threshold": 1.0
   }
   ```
5. Click "Test" button
6. Review the execution results

## Update config.yaml

After successful deployment, update your `mvp/config.yaml` to reference the Lambda functions:

```yaml
aws:
  region: us-east-1
  lambda:
    inventory_function: supply-chain-inventory-optimizer
    logistics_function: supply-chain-logistics-optimizer
    supplier_function: supply-chain-supplier-analyzer
```

## Troubleshooting

### Issue 1: "AWS CLI not found"
**Solution**: Install AWS CLI
```bash
pip install awscli
```

### Issue 2: "AWS credentials not configured"
**Solution**: If on SageMaker, verify IAM role is attached to the instance. Otherwise, configure credentials:
```bash
aws configure
```

### Issue 3: "Access Denied" when creating IAM role
**Solution**: Your IAM user/role needs `iam:CreateRole` permission. Ask your AWS administrator to grant this permission or create the role manually.

### Issue 4: "Function already exists" error
**Solution**: The script should update existing functions. If it fails, delete the function and redeploy:
```bash
aws lambda delete-function --function-name supply-chain-inventory-optimizer
./deploy_lambda.sh
```

### Issue 5: Lambda function times out
**Solution**: 
1. Check CloudWatch Logs for errors
2. Verify Redshift workgroup is running
3. Verify IAM role has Redshift Data API permissions
4. Increase timeout in Lambda configuration (max 15 minutes)

### Issue 6: "No module named 'boto3'" error
**Solution**: The deployment script should include boto3. If not, add it to `requirements.txt`:
```bash
echo "boto3>=1.26.0" >> mvp/lambda_functions/inventory_optimizer/requirements.txt
```

### Issue 7: Redshift connection errors
**Solution**: 
1. Verify workgroup name and database name in config
2. Check that Lambda IAM role has Redshift Data API permissions
3. Ensure Redshift Serverless is running

## Monitoring

### CloudWatch Logs
View logs for each function:
```bash
# Inventory Optimizer logs
aws logs tail /aws/lambda/supply-chain-inventory-optimizer --follow

# Logistics Optimizer logs
aws logs tail /aws/lambda/supply-chain-logistics-optimizer --follow

# Supplier Analyzer logs
aws logs tail /aws/lambda/supply-chain-supplier-analyzer --follow
```

### CloudWatch Metrics
Monitor in AWS Console:
1. Go to CloudWatch Console
2. Select "Metrics" → "Lambda"
3. View metrics for your functions:
   - Invocations
   - Duration
   - Errors
   - Throttles

## Cost Estimation

Lambda costs are based on:
- **Requests**: $0.20 per 1M requests
- **Duration**: $0.0000166667 per GB-second

**Example for moderate usage (1000 invocations/day):**
- Requests: ~$0.006/day
- Duration (256MB, 5s avg): ~$0.02/day
- **Total: ~$0.78/month**

## Next Steps

After successful deployment:

1. ✅ Verify all 3 functions are deployed
2. ✅ Test each function with sample payloads
3. ✅ Update `mvp/config.yaml` with function names
4. ✅ Restart your Streamlit app
5. ✅ Test specialized agent queries in the UI

## Manual Deployment (Alternative)

If the script doesn't work, you can deploy manually:

### 1. Create IAM Role
Create a role with Lambda execution and Redshift Data API permissions.

### 2. Package Function
```bash
cd mvp/lambda_functions/inventory_optimizer
zip -r function.zip handler.py
```

### 3. Create Function
```bash
aws lambda create-function \
  --function-name supply-chain-inventory-optimizer \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/SupplyChainLambdaRole \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables={REDSHIFT_WORKGROUP_NAME=supply-chain-mvp,REDSHIFT_DATABASE=supply_chain_db}
```

### 4. Repeat for Other Functions
Repeat steps 2-3 for `logistics_optimizer` and `supplier_analyzer`.

## Support

For issues:
1. Check CloudWatch Logs for detailed error messages
2. Review deployment script output
3. Verify AWS credentials and permissions
4. Ensure Redshift Serverless is accessible
5. Check `mvp/lambda_functions/README.md` for more details

## Quick Reference

**Deploy all functions:**
```bash
cd mvp/scripts
./deploy_lambda.sh
```

**List deployed functions:**
```bash
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `supply-chain`)].FunctionName'
```

**Test a function:**
```bash
aws lambda invoke \
  --function-name supply-chain-inventory-optimizer \
  --payload '{"action":"identify_low_stock","warehouse_code":"WH-001","threshold":1.0}' \
  response.json
```

**View logs:**
```bash
aws logs tail /aws/lambda/supply-chain-inventory-optimizer --follow
```

**Update function code:**
```bash
./deploy_lambda.sh  # Script will update existing functions
```
