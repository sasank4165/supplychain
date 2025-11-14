# Deployment Guide

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Python 3.11+** installed
4. **Node.js 18+** (for CDK)
5. **AWS CDK** installed: `npm install -g aws-cdk`

## Architecture Components

### AWS Services Used

- **Amazon Bedrock**: Claude 3.5 Sonnet for agent orchestration
- **AWS Athena**: SQL query execution
- **AWS Lambda**: Tool execution (3 functions)
- **Amazon S3**: Athena results storage
- **AWS Glue Data Catalog**: Metadata management
- **Amazon DynamoDB**: Session state and memory (2 tables)
- **Amazon API Gateway**: REST API
- **AWS Cognito**: User authentication
- **Amazon CloudWatch**: Logging and monitoring

### Lambda Functions

1. **inventory-optimizer**: Inventory forecasting and optimization
2. **logistics-optimizer**: Route optimization and order tracking
3. **supplier-analyzer**: Supplier performance and cost analysis

## Step-by-Step Deployment

### 1. Clone and Setup

```bash
cd supply_chain_agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure AWS

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and Region
```

### 3. Update Configuration

Edit `config.py`:
- Set `ATHENA_DATABASE` to your Glue database name
- Set `ATHENA_CATALOG` if different from "AwsDataCatalog"
- Verify table names match your schema

### 4. Deploy Infrastructure

```bash
chmod +x deploy.sh
./deploy.sh
```

This script will:
- Install dependencies
- Create Lambda layers
- Bootstrap CDK
- Deploy all infrastructure
- Create `.env` file with outputs

### 5. Setup Cognito Users

Create users for each persona:

```bash
# Warehouse Manager
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username warehouse_manager1 \
  --user-attributes Name=email,Value=wm@example.com \
  --temporary-password TempPass123!

# Field Engineer
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username field_engineer1 \
  --user-attributes Name=email,Value=fe@example.com \
  --temporary-password TempPass123!

# Procurement Specialist
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username procurement1 \
  --user-attributes Name=email,Value=ps@example.com \
  --temporary-password TempPass123!
```

### 6. Test Lambda Functions

```bash
# Test inventory optimizer
aws lambda invoke \
  --function-name supply-chain-inventory-optimizer \
  --payload '{"tool_name":"identify_stockout_risks","input":{"warehouse_code":"WH01"}}' \
  response.json

cat response.json
```

### 7. Run Streamlit Application

```bash
streamlit run app.py
```

Access at: http://localhost:8501

## Configuration Files

### Environment Variables

Create `.env` file:
```
AWS_REGION=us-east-1
ATHENA_OUTPUT_LOCATION=s3://your-bucket/
ATHENA_DATABASE=aws-gpl-cog-sc-db
USER_POOL_ID=us-east-1_xxxxx
API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/
```

### Bedrock Model Access

Enable Claude 3.5 Sonnet in Bedrock console:
1. Go to AWS Bedrock Console
2. Navigate to Model Access
3. Request access to Anthropic Claude 3.5 Sonnet
4. Wait for approval (usually instant)

## Data Setup

### 1. Create Glue Database

```bash
aws glue create-database \
  --database-input '{"Name":"aws-gpl-cog-sc-db","Description":"Supply chain database"}'
```

### 2. Create Tables

Use AWS Glue Crawler or create tables manually:

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS `aws-gpl-cog-sc-db`.`product` (
  `product_code` string,
  `short_name` string,
  `product_description` string,
  `product_group` string,
  `supplier_code1` string,
  `standard_cost` double,
  `standard_rrp` double,
  `stock_item` string,
  `manufactured` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES ('field.delim'=',')
LOCATION 's3://your-data-bucket/product/'
TBLPROPERTIES ('has_encrypted_data'='false');
```

Repeat for all tables: `warehouse_product`, `purchase_order_header`, `purchase_order_line`, `sales_order_header`, `sales_order_line`

### 3. Load Sample Data

Upload CSV files to S3:
```bash
aws s3 cp product.csv s3://your-data-bucket/product/
aws s3 cp warehouse_product.csv s3://your-data-bucket/warehouse_product/
# ... etc
```

## Monitoring

### CloudWatch Logs

View Lambda logs:
```bash
aws logs tail /aws/lambda/supply-chain-inventory-optimizer --follow
```

### Athena Query History

Check Athena console for query execution history and performance.

### DynamoDB Tables

Monitor session and memory tables in DynamoDB console.

## Cost Optimization

- **Athena**: Pay per query, optimize with partitioning
- **Lambda**: 512MB memory, 300s timeout (adjust as needed)
- **DynamoDB**: On-demand billing (consider provisioned for high traffic)
- **Bedrock**: Pay per token (Claude 3.5 Sonnet pricing)
- **S3**: Lifecycle policy deletes Athena results after 30 days

## Troubleshooting

### Lambda Timeout
Increase timeout in `supply_chain_stack.py`:
```python
timeout=Duration.seconds(600)
```

### Athena Query Errors
- Check table schemas match data
- Verify S3 permissions
- Check Glue Data Catalog

### Bedrock Access Denied
- Enable model access in Bedrock console
- Verify IAM permissions

### Cognito Authentication Issues
- Check user pool configuration
- Verify user exists and is confirmed

## Security Best Practices

1. **IAM Roles**: Use least privilege principle
2. **Encryption**: Enable at rest and in transit
3. **VPC**: Deploy Lambda in VPC for production
4. **Secrets**: Use AWS Secrets Manager for sensitive data
5. **API Gateway**: Enable throttling and WAF
6. **Cognito**: Enforce strong password policies
7. **CloudTrail**: Enable for audit logging

## Scaling Considerations

- **Lambda Concurrency**: Set reserved concurrency if needed
- **DynamoDB**: Monitor capacity and enable auto-scaling
- **Athena**: Use partitioning for large datasets
- **API Gateway**: Configure caching for frequent queries
- **Bedrock**: Monitor token usage and costs

## Cleanup

To remove all resources:

```bash
cd cdk
cdk destroy
```

Note: DynamoDB tables and S3 buckets with `RETAIN` policy must be deleted manually.
