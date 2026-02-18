# Deploy Lambda Functions - Quick Start

## For SageMaker Users

Follow these simple steps to deploy the Lambda functions right now.

## Step 1: Open Terminal in SageMaker

In your SageMaker Jupyter environment, open a terminal.

## Step 2: Navigate to Scripts Directory

```bash
cd /home/ec2-user/SageMaker/supplychain/mvp/scripts
```

## Step 3: Verify AWS Credentials

```bash
aws sts get-caller-identity
```

You should see your AWS account information. If you get an error, your SageMaker instance may not have the correct IAM role attached.

## Step 4: Make Script Executable

```bash
chmod +x deploy_lambda.sh
```

## Step 5: Run Deployment

```bash
./deploy_lambda.sh
```

The script will:
1. Check AWS CLI (should already be installed on SageMaker)
2. Verify credentials (using SageMaker IAM role)
3. Create IAM role for Lambda functions
4. Package and deploy all 3 Lambda functions
5. Ask if you want to test them

**When prompted "Do you want to test the Lambda functions? (y/n)"**
- Type `y` and press Enter to test
- Or type `n` to skip testing

## Step 6: Verify Deployment

```bash
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `supply-chain`)].FunctionName'
```

You should see:
```json
[
    "supply-chain-inventory-optimizer",
    "supply-chain-logistics-optimizer",
    "supply-chain-supplier-analyzer"
]
```

## Step 7: Update config.yaml

Open `mvp/config.yaml` and verify these lines exist under the `aws` section:

```yaml
aws:
  region: us-east-1
  lambda:
    inventory_function: supply-chain-inventory-optimizer
    logistics_function: supply-chain-logistics-optimizer
    supplier_function: supply-chain-supplier-analyzer
```

If they don't exist, add them.

## Step 8: Restart Your Streamlit App

If your app is running, stop it (Ctrl+C) and restart:

```bash
cd /home/ec2-user/SageMaker/supplychain/mvp
streamlit run app.py --server.port 8501
```

## Step 9: Test in the Application

1. Login with `demo_warehouse` / `demo123`
2. Select "Warehouse Manager" persona
3. Try this query: "Calculate reorder points for warehouse WH001"
4. The app should now invoke the Lambda function!

## That's It!

Your Lambda functions are now deployed and ready to use.

## If Something Goes Wrong

### Error: "AWS CLI not found"
SageMaker should have AWS CLI pre-installed. If not:
```bash
pip install awscli
```

### Error: "Access Denied"
Your SageMaker IAM role may not have sufficient permissions. You need:
- Lambda create/update permissions
- IAM role creation permissions
- Redshift Data API permissions

Contact your AWS administrator to add these permissions to your SageMaker execution role.

### Error: "Function already exists"
The script should update existing functions. If it fails:
```bash
# Delete the function and redeploy
aws lambda delete-function --function-name supply-chain-inventory-optimizer
aws lambda delete-function --function-name supply-chain-logistics-optimizer
aws lambda delete-function --function-name supply-chain-supplier-analyzer

# Run deployment again
./deploy_lambda.sh
```

### Error: Lambda function times out
1. Check CloudWatch Logs:
   ```bash
   aws logs tail /aws/lambda/supply-chain-inventory-optimizer --follow
   ```
2. Verify Redshift workgroup is running
3. Check that workgroup name in config.yaml matches your actual workgroup

## Quick Test Commands

Test each function individually:

```bash
# Test Inventory Optimizer
aws lambda invoke \
  --function-name supply-chain-inventory-optimizer \
  --payload '{"action":"identify_low_stock","warehouse_code":"WH-001","threshold":1.0}' \
  response.json
cat response.json

# Test Logistics Optimizer
aws lambda invoke \
  --function-name supply-chain-logistics-optimizer \
  --payload '{"action":"identify_delayed_orders","warehouse_code":"WH-001","days":7}' \
  response.json
cat response.json

# Test Supplier Analyzer
aws lambda invoke \
  --function-name supply-chain-supplier-analyzer \
  --payload '{"action":"analyze_purchase_trends","days":90,"group_by":"month"}' \
  response.json
cat response.json
```

## View Logs

```bash
# View Inventory Optimizer logs
aws logs tail /aws/lambda/supply-chain-inventory-optimizer --follow

# View Logistics Optimizer logs
aws logs tail /aws/lambda/supply-chain-logistics-optimizer --follow

# View Supplier Analyzer logs
aws logs tail /aws/lambda/supply-chain-supplier-analyzer --follow
```

## Need More Help?

Check these files:
- `mvp/LAMBDA_DEPLOYMENT_GUIDE.md` - Detailed deployment guide
- `mvp/LAMBDA_DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist
- `mvp/lambda_functions/README.md` - Lambda functions documentation

## Summary

```bash
# 1. Navigate to scripts
cd /home/ec2-user/SageMaker/supplychain/mvp/scripts

# 2. Make executable
chmod +x deploy_lambda.sh

# 3. Deploy
./deploy_lambda.sh

# 4. Verify
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `supply-chain`)].FunctionName'

# 5. Test
aws lambda invoke --function-name supply-chain-inventory-optimizer --payload '{"action":"identify_low_stock","warehouse_code":"WH-001","threshold":1.0}' response.json

# 6. Restart app
cd /home/ec2-user/SageMaker/supplychain/mvp
streamlit run app.py --server.port 8501
```

Done! 🎉
