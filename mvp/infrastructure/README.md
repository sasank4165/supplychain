# Supply Chain MVP Infrastructure

This directory contains the AWS CDK infrastructure code for the Supply Chain MVP.

## Architecture

The CDK stack creates:

1. **Redshift Serverless Workgroup** (8 RPUs)
   - Cost-optimized data warehouse
   - Publicly accessible for MVP
   - Database: `supply_chain_db`

2. **AWS Glue Data Catalog**
   - Database: `supply_chain_catalog`
   - Stores table schemas and metadata

3. **Lambda Functions** (3 functions)
   - `supply-chain-inventory-optimizer`: Inventory optimization tools
   - `supply-chain-logistics-optimizer`: Logistics optimization tools
   - `supply-chain-supplier-analyzer`: Supplier analysis tools

4. **IAM Roles and Permissions**
   - Lambda execution role with Redshift Data API, Bedrock, and Glue access
   - Redshift role with S3 and Glue access

## Prerequisites

- AWS CLI configured with credentials
- AWS CDK CLI installed: `npm install -g aws-cdk`
- Python 3.11+
- AWS account with appropriate permissions

## Deployment

### Windows

```cmd
cd mvp\infrastructure\cdk
deploy.bat
```

### Linux/Mac

```bash
cd mvp/infrastructure/cdk
chmod +x deploy.sh
./deploy.sh
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy stack
cdk deploy
```

## Post-Deployment

After deployment, note the following outputs:

- `RedshiftWorkgroupName`: Use this in your config.yaml
- `RedshiftDatabase`: Database name
- `GlueDatabaseName`: Glue catalog database name
- `InventoryLambdaArn`: Inventory optimizer Lambda ARN
- `LogisticsLambdaArn`: Logistics optimizer Lambda ARN
- `SupplierLambdaArn`: Supplier analyzer Lambda ARN

### Update Redshift Password

The default password is `TempPassword123!`. Change it immediately:

```bash
aws redshift-serverless update-namespace \
  --namespace-name supply-chain-mvp-namespace \
  --admin-user-password "YourSecurePassword"
```

## Cost Estimate

- **Redshift Serverless**: ~$130/month (8 RPUs, 24/7)
- **Lambda**: ~$5/month (moderate usage)
- **Glue Catalog**: ~$1/month
- **VPC**: Free (no NAT gateways)

**Total**: ~$136/month

## Cleanup

To destroy all resources:

```bash
cdk destroy
```

## Troubleshooting

### CDK Bootstrap Error

If you get a bootstrap error, run:

```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### Lambda Deployment Error

Ensure the Lambda function directories exist:
- `mvp/lambda_functions/inventory_optimizer/`
- `mvp/lambda_functions/logistics_optimizer/`
- `mvp/lambda_functions/supplier_analyzer/`
- `mvp/lambda_functions/layer/`

### Redshift Connection Issues

Ensure your IP is whitelisted in the Redshift security group.
