# Complete Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the production-ready Supply Chain Agentic AI application with full authentication, authorization, and role-based access control.

## What's Included

### Infrastructure (AWS Well-Architected)
- ✅ Multi-stack CDK deployment
- ✅ VPC with 3 AZs (high availability)
- ✅ KMS encryption for all data
- ✅ DynamoDB with PITR and backups
- ✅ Lambda with VPC, X-Ray tracing
- ✅ API Gateway with WAF protection
- ✅ Cognito with MFA support
- ✅ CloudWatch monitoring and alarms
- ✅ AWS Backup for disaster recovery

### Authentication & Authorization
- ✅ Cognito User Pool authentication
- ✅ JWT token validation
- ✅ Role-based access control (RBAC)
- ✅ Table-level permissions
- ✅ Agent-level permissions
- ✅ Lambda authorizer for API
- ✅ Streamlit login UI

### Application Features
- ✅ 3 personas (Warehouse Manager, Field Engineer, Procurement Specialist)
- ✅ 6 agents (SQL + 3 specialized agents)
- ✅ Natural language queries
- ✅ Real-time data analysis
- ✅ Predictive analytics

## Prerequisites

### Required Software
```bash
# AWS CLI
aws --version  # >= 2.0

# Python
python --version  # >= 3.11

# Node.js (for CDK)
node --version  # >= 18.0

# AWS CDK
npm install -g aws-cdk
cdk --version  # >= 2.100
```

### AWS Account Setup
1. AWS Account with admin access
2. Bedrock model access (Claude 3.5 Sonnet)
3. Service quotas verified:
   - Lambda concurrent executions: 1000+
   - DynamoDB tables: 10+
   - VPC: 1+

### AWS Credentials
```bash
aws configure
# Enter Access Key ID
# Enter Secret Access Key
# Enter Region (e.g., us-east-1)
```

## Step-by-Step Deployment

### Step 1: Clone and Setup

```bash
# Navigate to project
cd supply_chain_agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

Edit `cdk/config.py`:

```python
PROD_CONFIG = EnvironmentConfig(
    name="prod",
    account="YOUR_AWS_ACCOUNT_ID",  # Replace
    region="us-east-1",              # Your region
    alarm_email="ops@yourcompany.com",  # Your email
    enable_waf=True,
    enable_multi_az=True,
    # ... other settings
)
```

Edit `cdk/cdk.context.json`:

```json
{
  "environment": "prod",
  "alarm_email": "ops@yourcompany.com",
  "enable_waf": true,
  "enable_cicd": false
}
```

### Step 3: Create Lambda Layer

```bash
# Create layer directory
mkdir -p lambda_layers/common/python

# Install dependencies
pip install boto3 anthropic jwt requests -t lambda_layers/common/python/
```

### Step 4: Deploy Infrastructure

```bash
cd cdk

# Install CDK dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap

# Synthesize templates (verify)
cdk synth

# Deploy all stacks
cdk deploy --all --require-approval never
```

**Deployment Order**:
1. SupplyChainNetwork-prod (VPC, subnets, security groups)
2. SupplyChainSecurity-prod (KMS, Secrets Manager)
3. SupplyChainData-prod (S3, Glue, Athena)
4. SupplyChainApp-prod (Lambda, DynamoDB, API Gateway, Cognito)
5. SupplyChainMonitoring-prod (CloudWatch, SNS)
6. SupplyChainBackup-prod (AWS Backup)

**Expected Duration**: 15-20 minutes

### Step 5: Capture Outputs

```bash
# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name SupplyChainApp-prod \
  --query "Stacks[0].Outputs" \
  --output table

# Save important values:
# - USER_POOL_ID
# - USER_POOL_CLIENT_ID
# - API_ENDPOINT
# - ATHENA_RESULTS_BUCKET
```

Create `.env` file:

```bash
cat > ../.env << EOF
AWS_REGION=us-east-1
USER_POOL_ID=us-east-1_xxxxx
USER_POOL_CLIENT_ID=xxxxx
API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/
ATHENA_OUTPUT_LOCATION=s3://supply-chain-athena-ACCOUNT-REGION/
ATHENA_DATABASE=aws-gpl-cog-sc-db
EOF
```

### Step 6: Enable Bedrock Model Access

```bash
# Via AWS Console:
# 1. Go to Amazon Bedrock console
# 2. Navigate to "Model access"
# 3. Click "Manage model access"
# 4. Enable "Anthropic Claude 3.5 Sonnet"
# 5. Submit request (usually instant approval)

# Verify access
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'claude-3-5-sonnet')]"
```

### Step 7: Setup Data Catalog

```bash
# Create Glue database (if not exists)
aws glue create-database \
  --database-input '{"Name":"aws-gpl-cog-sc-db","Description":"Supply chain database"}'

# Upload sample data to S3
DATA_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name SupplyChainData-prod \
  --query "Stacks[0].Outputs[?OutputKey=='DataBucketName'].OutputValue" \
  --output text)

# Upload your CSV files
aws s3 cp data/product.csv s3://$DATA_BUCKET/product/
aws s3 cp data/warehouse_product.csv s3://$DATA_BUCKET/warehouse_product/
# ... upload other tables

# Create Glue tables (use Crawler or manual DDL)
# See DEPLOYMENT.md for table schemas
```

### Step 8: Create Users

```bash
cd ../scripts

# Make script executable
chmod +x setup-users.sh

# Run user setup
./setup-users.sh $USER_POOL_ID

# This creates:
# - warehouse_manager1, warehouse_manager2
# - field_engineer1, field_engineer2
# - procurement1, procurement2
```

**Default Password**: `TempPass123!` (must be changed on first login)

### Step 9: Test Deployment

```bash
# Make test script executable
chmod +x test-deployment.sh

# Run tests
./test-deployment.sh prod

# Expected output:
# ✅ Health check passed
# ✅ Inventory optimizer working
# ✅ Logistics optimizer working
# ✅ Supplier analyzer working
# ✅ DynamoDB tables accessible
# ✅ S3 buckets accessible
```

### Step 10: Test Authentication

```bash
cd ..

# Set environment variables
export USER_POOL_ID="us-east-1_xxxxx"
export USER_POOL_CLIENT_ID="xxxxx"
export AWS_REGION="us-east-1"

# Run auth tests
python auth/test_auth.py

# Follow prompts to test:
# - Sign in
# - Token verification
# - Table access control
# - Agent access control
# - Sign out
```

### Step 11: Launch Application

```bash
# Run Streamlit app
streamlit run app.py

# Access at: http://localhost:8501

# Login with:
# Username: warehouse_manager1
# Password: TempPass123!
# (You'll be prompted to change password)
```

## Post-Deployment Configuration

### 1. Configure Alarms

```bash
# Verify SNS subscription
# Check email for confirmation link
# Click to confirm alarm notifications
```

### 2. Setup Backup

```bash
# Verify backup plan
aws backup list-backup-plans

# Check backup vault
aws backup list-backup-vaults
```

### 3. Enable WAF (Optional)

```bash
# Deploy WAF stack
cd cdk
cdk deploy SupplyChainWAF-prod

# Associate with API Gateway
# (Done automatically by CDK)
```

### 4. Configure CI/CD (Optional)

```bash
# Deploy CI/CD stack
cdk deploy SupplyChainCICD-prod

# Push code to CodeCommit
git remote add aws <codecommit-url>
git push aws main
```

## Verification Checklist

### Infrastructure
- [ ] All CDK stacks deployed successfully
- [ ] VPC created with 3 AZs
- [ ] Lambda functions deployed
- [ ] DynamoDB tables created
- [ ] S3 buckets created
- [ ] API Gateway endpoint accessible
- [ ] Cognito User Pool created

### Security
- [ ] KMS keys created and rotating
- [ ] Secrets Manager configured
- [ ] VPC endpoints created
- [ ] Security groups configured
- [ ] IAM roles have least privilege
- [ ] CloudTrail enabled

### Authentication
- [ ] Cognito User Pool configured
- [ ] User groups created
- [ ] Test users created
- [ ] MFA enabled (optional)
- [ ] Password policies enforced

### Monitoring
- [ ] CloudWatch dashboards created
- [ ] Alarms configured
- [ ] SNS topic subscribed
- [ ] Log groups created
- [ ] X-Ray tracing enabled

### Backup
- [ ] Backup vault created
- [ ] Backup plans configured
- [ ] PITR enabled on DynamoDB
- [ ] S3 versioning enabled

### Application
- [ ] Bedrock model access enabled
- [ ] Glue database created
- [ ] Sample data uploaded
- [ ] Lambda functions tested
- [ ] API endpoints tested
- [ ] Streamlit app running

## Testing Scenarios

### Scenario 1: Warehouse Manager

```bash
# Login as warehouse_manager1
# Try queries:
"Show me products below minimum stock in warehouse WH01"
"Calculate optimal reorder points for warehouse WH01"
"Forecast demand for product P12345"

# Should work: ✅
# - Access to warehouse_product table
# - Access to inventory_optimizer agent

# Should fail: ❌
# - Access to purchase_order_header table
# - Access to supplier_analyzer agent
```

### Scenario 2: Field Engineer

```bash
# Login as field_engineer1
# Try queries:
"Show me all orders for delivery today"
"Optimize delivery route for orders SO001, SO002"
"Check fulfillment status of order SO12345"

# Should work: ✅
# - Access to sales_order_header table
# - Access to logistics_optimizer agent

# Should fail: ❌
# - Access to purchase_order_header table
# - Access to inventory_optimizer agent
```

### Scenario 3: Procurement Specialist

```bash
# Login as procurement1
# Try queries:
"Show me all purchase orders from supplier SUP001"
"Analyze supplier performance for last 90 days"
"Identify cost savings opportunities"

# Should work: ✅
# - Access to purchase_order_header table
# - Access to supplier_analyzer agent

# Should fail: ❌
# - Access to sales_order_header table
# - Access to logistics_optimizer agent
```

## Monitoring & Maintenance

### Daily Tasks
- Check CloudWatch dashboard
- Review alarm notifications
- Monitor Lambda errors
- Check API Gateway metrics

### Weekly Tasks
- Review access logs
- Check backup status
- Review cost reports
- Update dependencies

### Monthly Tasks
- Security audit
- Access review
- Performance optimization
- Capacity planning

## Troubleshooting

### Issue: CDK deployment fails

```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name SupplyChainApp-prod \
  --max-items 20

# Common fixes:
# - Verify AWS credentials
# - Check service quotas
# - Review IAM permissions
# - Check for naming conflicts
```

### Issue: Lambda timeout

```bash
# Increase timeout in cdk/config.py
lambda_timeout=600

# Redeploy
cdk deploy SupplyChainApp-prod
```

### Issue: Authentication fails

```bash
# Verify Cognito configuration
aws cognito-idp describe-user-pool \
  --user-pool-id $USER_POOL_ID

# Check user exists
aws cognito-idp admin-get-user \
  --user-pool-id $USER_POOL_ID \
  --username warehouse_manager1

# Reset password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username warehouse_manager1 \
  --password NewPassword123! \
  --permanent
```

### Issue: Access denied errors

```bash
# Check user groups
aws cognito-idp admin-list-groups-for-user \
  --user-pool-id $USER_POOL_ID \
  --username warehouse_manager1

# Add to group if missing
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username warehouse_manager1 \
  --group-name warehouse_managers
```

## Cost Optimization

### Estimated Monthly Costs (1000 queries/day)

| Service | Cost |
|---------|------|
| Bedrock (Claude 3.5) | $150-300 |
| Lambda | $20-50 |
| Athena | $50-100 |
| DynamoDB | $10-30 |
| S3 | $5-10 |
| API Gateway | $5-10 |
| VPC (NAT Gateway) | $100-150 |
| **Total** | **$340-650/month** |

### Cost Reduction Tips
1. Use S3 Intelligent-Tiering
2. Enable DynamoDB auto-scaling
3. Optimize Athena queries (partitioning)
4. Use Lambda ARM64 architecture
5. Implement API Gateway caching
6. Review and remove unused resources

## Cleanup

### To Remove All Resources

```bash
cd scripts
chmod +x destroy.sh
./destroy.sh prod

# Type 'DELETE' to confirm

# Manually delete retained resources:
# - S3 buckets (with data)
# - DynamoDB tables (with data)
# - KMS keys (after 30-day waiting period)
# - CloudWatch log groups
```

## Support & Documentation

### Documentation Files
- `README.md` - Quick start guide
- `DEPLOYMENT.md` - Detailed deployment
- `ARCHITECTURE.md` - Technical architecture
- `AUTH_IMPLEMENTATION.md` - Authentication guide
- `auth/RBAC_GUIDE.md` - RBAC details
- `cdk/README.md` - Infrastructure guide

### Getting Help
1. Check CloudWatch Logs
2. Review CloudFormation events
3. Verify IAM permissions
4. Test with AWS CLI
5. Check AWS Service Health Dashboard

## Next Steps

1. **Production Hardening**
   - Enable WAF
   - Configure custom domain
   - Setup SSL certificates
   - Enable CloudFront

2. **Monitoring Enhancement**
   - Create custom dashboards
   - Configure detailed alarms
   - Setup log aggregation
   - Enable AWS X-Ray insights

3. **Disaster Recovery**
   - Setup cross-region replication
   - Test backup restoration
   - Document recovery procedures
   - Conduct DR drills

4. **Performance Optimization**
   - Analyze query patterns
   - Optimize Lambda memory
   - Implement caching
   - Partition Athena tables

5. **Security Hardening**
   - Enable GuardDuty
   - Setup Security Hub
   - Configure AWS Config
   - Implement AWS Inspector

## Success Criteria

✅ All infrastructure deployed
✅ Authentication working
✅ RBAC enforced
✅ All personas can login
✅ Queries execute successfully
✅ Access control validated
✅ Monitoring configured
✅ Backups enabled
✅ Documentation complete

**Congratulations! Your production-ready Supply Chain Agentic AI application is now deployed!** 🎉
