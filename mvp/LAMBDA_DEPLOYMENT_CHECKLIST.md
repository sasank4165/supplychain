# Lambda Deployment Checklist

## Pre-Deployment Checklist

- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS credentials configured (`aws sts get-caller-identity`)
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Redshift Serverless workgroup is running
- [ ] IAM permissions verified (Lambda, IAM, Redshift Data API)

## Deployment Steps

### 1. Navigate to Scripts Directory
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp/scripts
```

### 2. Make Script Executable (if needed)
```bash
chmod +x deploy_lambda.sh
```

### 3. Run Deployment
```bash
./deploy_lambda.sh
```

### 4. Verify Deployment
```bash
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `supply-chain`)].FunctionName'
```

Expected output:
```
[
    "supply-chain-inventory-optimizer",
    "supply-chain-logistics-optimizer", 
    "supply-chain-supplier-analyzer"
]
```

## Post-Deployment Checklist

- [ ] All 3 Lambda functions deployed successfully
- [ ] Test Inventory Optimizer function
- [ ] Test Logistics Optimizer function
- [ ] Test Supplier Analyzer function
- [ ] Update `mvp/config.yaml` with function names
- [ ] Restart Streamlit app
- [ ] Test specialized agent queries in UI

## Testing Commands

### Test Inventory Optimizer
```bash
aws lambda invoke \
  --function-name supply-chain-inventory-optimizer \
  --payload '{"action":"identify_low_stock","warehouse_code":"WH-001","threshold":1.0}' \
  response.json && cat response.json
```

### Test Logistics Optimizer
```bash
aws lambda invoke \
  --function-name supply-chain-logistics-optimizer \
  --payload '{"action":"identify_delayed_orders","warehouse_code":"WH-001","days":7}' \
  response.json && cat response.json
```

### Test Supplier Analyzer
```bash
aws lambda invoke \
  --function-name supply-chain-supplier-analyzer \
  --payload '{"action":"analyze_purchase_trends","days":90,"group_by":"month"}' \
  response.json && cat response.json
```

## Update config.yaml

Add these lines to `mvp/config.yaml`:

```yaml
aws:
  region: us-east-1
  lambda:
    inventory_function: supply-chain-inventory-optimizer
    logistics_function: supply-chain-logistics-optimizer
    supplier_function: supply-chain-supplier-analyzer
```

## Verify in Application

1. Start Streamlit app:
   ```bash
   cd mvp
   streamlit run app.py
   ```

2. Login with `demo_warehouse` / `demo123`

3. Try an optimization query:
   - "Calculate reorder points for warehouse WH001"
   - This should invoke the Inventory Optimizer Lambda function

4. Check CloudWatch Logs for Lambda invocations:
   ```bash
   aws logs tail /aws/lambda/supply-chain-inventory-optimizer --follow
   ```

## Troubleshooting Quick Fixes

### If deployment fails:
1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify IAM permissions
3. Check script output for specific errors

### If functions don't work:
1. Check CloudWatch Logs
2. Verify Redshift workgroup name in config
3. Test with AWS CLI first before testing in app

### If "Access Denied" errors:
1. Verify Lambda IAM role has Redshift Data API permissions
2. Check Redshift security group settings
3. Ensure workgroup is running

## Success Criteria

✅ All 3 Lambda functions deployed
✅ All 3 functions tested successfully via AWS CLI
✅ config.yaml updated with function names
✅ Streamlit app can invoke Lambda functions
✅ No errors in CloudWatch Logs

## Next Steps After Deployment

1. Test each persona's specialized queries
2. Monitor CloudWatch metrics for performance
3. Review CloudWatch Logs for any errors
4. Adjust Lambda timeout/memory if needed
5. Set up CloudWatch alarms for errors (optional)

## Quick Reference

**Deploy:** `./deploy_lambda.sh`
**List:** `aws lambda list-functions`
**Test:** `aws lambda invoke --function-name <name> --payload '<json>' response.json`
**Logs:** `aws logs tail /aws/lambda/<function-name> --follow`
**Delete:** `aws lambda delete-function --function-name <name>`

## Documentation

- Full Guide: `mvp/LAMBDA_DEPLOYMENT_GUIDE.md`
- Lambda README: `mvp/lambda_functions/README.md`
- Deployment Scripts: `mvp/scripts/deploy_lambda.sh` or `deploy_lambda.ps1`
