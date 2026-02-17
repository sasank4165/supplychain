# SageMaker Quick Start Guide (No CDK Required)

This guide helps you get the MVP running on SageMaker without CDK complexity.

## Key Features

- **Auto-detection**: AWS Account ID is automatically detected - no hardcoding needed!
- **Quick Setup Script**: Automated configuration and verification
- **Manual Setup**: Step-by-step instructions if you prefer manual setup

## Prerequisites

- SageMaker Notebook Instance running
- AWS Console access with permissions to create resources

## Step 1: Create Redshift Serverless (AWS Console)

1. Go to **AWS Console** → **Amazon Redshift** → **Serverless dashboard**
2. Click **Create workgroup**
3. Configure:
   - **Workgroup name**: `supply-chain-mvp`
   - **Namespace**: Create new → `supply-chain-mvp-namespace`
   - **Database name**: `supply_chain_db`
   - **Admin user**: `admin`
   - **Admin password**: (set a secure password - save it!)
   - **Base capacity**: 8 RPUs (cost-optimized)
   - **Publicly accessible**: Yes (for MVP)
4. Click **Create workgroup**
5. Wait 5-10 minutes for creation

## Step 2: Create Glue Database (AWS Console)

1. Go to **AWS Console** → **AWS Glue** → **Databases**
2. Click **Add database**
3. Configure:
   - **Database name**: `supply_chain_catalog`
   - **Description**: Schema metadata for Supply Chain MVP
4. Click **Create**

## Step 3: Quick Setup (Automated)

Run the quick setup script to automate configuration:

```bash
cd /home/ec2-user/SageMaker/supplychain/mvp
python scripts/quick_setup.py
```

This script will:
- Create `config.yaml` from the example
- Auto-detect your AWS account ID
- Verify AWS connectivity
- Create necessary directories

**OR** do it manually (Step 3a below):

## Step 3a: Configure the Application (Manual)

If you prefer to configure manually:

1. Copy the example config:
```bash
cp config.example.yaml config.yaml
```

2. Edit `config.yaml`:
```bash
nano config.yaml
```

3. Update these values (if needed):
```yaml
aws:
  region: us-east-1  # Your AWS region
  bedrock:
    model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
  redshift:
    workgroup_name: supply-chain-mvp
    database: supply_chain_db
  glue:
    catalog_id: ${AWS_ACCOUNT_ID}  # Auto-detected from AWS credentials
    database: supply_chain_catalog
```

**Note**: The `${AWS_ACCOUNT_ID}` will be automatically detected from your AWS credentials. You don't need to hardcode it!

4. Save and exit (Ctrl+X, Y, Enter)

## Step 4: Setup Glue Catalog Tables (Optional)

```bash
python scripts/setup_glue_catalog.py
```

## Step 5: Generate and Load Sample Data

```bash
python scripts/generate_sample_data.py --load-redshift --workgroup supply-chain-mvp --database supply_chain_db
```

This will:
- Connect to your Redshift workgroup
- Create tables (inventory, shipments, suppliers, etc.)
- Load sample data

## Step 6: Create Users

```bash
python scripts/create_user.py
```

Follow the prompts to create users with different personas:
- Procurement Manager
- Warehouse Manager
- Field Operations Manager

## Step 7: Start the Application

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## Step 8: Access the Application

Access via SageMaker proxy URL:
```
https://<your-notebook-instance-name>.notebook.us-east-1.sagemaker.aws/proxy/8501/
```

Replace `<your-notebook-instance-name>` with your actual notebook instance name.

## Troubleshooting

### Can't connect to Redshift

Check that your SageMaker IAM role has these permissions:
- `redshift-data:ExecuteStatement`
- `redshift-data:GetStatementResult`
- `redshift-data:DescribeStatement`
- `redshift-serverless:GetWorkgroup`

### Can't access Bedrock

Ensure Bedrock model access is enabled:
1. Go to **AWS Console** → **Amazon Bedrock** → **Model access**
2. Click **Manage model access**
3. Enable **Anthropic Claude 3.5 Sonnet**
4. Click **Save changes**

### Application won't start

Check logs:
```bash
# In the terminal where you ran streamlit
# Look for error messages
```

Common issues:
- Missing dependencies: `pip install -r requirements.txt`
- Wrong config values in `config.yaml`
- IAM permissions missing

## Cost Monitoring

The MVP costs approximately:
- **Redshift Serverless (8 RPUs)**: ~$0.36/hour when active (~$260/month if 24/7)
- **Bedrock API calls**: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
- **SageMaker Notebook (ml.t3.medium)**: ~$0.05/hour (~$36/month if 24/7)

**Cost Optimization Tips**:
1. Stop Redshift when not in use (can pause/resume)
2. Stop SageMaker notebook instance when not in use
3. Use the cost dashboard in the app to monitor Bedrock usage

## Next Steps

Once running:
1. Test all three personas
2. Try sample queries
3. Monitor costs in the dashboard
4. Review the main README.md for advanced features

## Lambda Functions (Optional)

The specialized agents (Inventory, Logistics, Supplier) can run without Lambda functions for the MVP. They'll execute directly in the Streamlit app. If you want to deploy Lambda functions later, you can do so manually through the AWS Console.

## Support

For issues:
- Check application logs in the terminal
- Review AWS service status
- Verify IAM permissions
- Check Redshift and Glue are properly configured
