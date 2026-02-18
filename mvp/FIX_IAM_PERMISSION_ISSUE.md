# Fix IAM Permission Issue - Quick Guide

## Your Error
```
AccessDenied: User is not authorized to perform: iam:CreateRole
```

Your SageMaker role (`SageMaker-SupplyChain-Role`) doesn't have permission to create IAM roles.

## Quick Solution

### Option A: Find and Use Existing Lambda Role (Fastest)

**Step 1: List existing Lambda roles**
```bash
aws iam list-roles --query 'Roles[?contains(RoleName, `Lambda`) || contains(RoleName, `lambda`)].RoleName'
```

**Step 2: If you see any role, get its ARN**
```bash
# Replace ROLE_NAME with one from the list above
aws iam get-role --role-name ROLE_NAME --query 'Role.Arn' --output text
```

**Step 3: Deploy with that role**
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp/scripts
chmod +x deploy_lambda_with_role.sh

# Set the role ARN (replace with your actual ARN)
export LAMBDA_ROLE_ARN="arn:aws:iam::193871648423:role/YOUR_ROLE_NAME"

# Deploy
./deploy_lambda_with_role.sh
```

### Option B: Use SageMaker Role (If It Has Lambda Permissions)

Your SageMaker role might already have the necessary permissions for Lambda.

**Step 1: Get your SageMaker role ARN**
```bash
aws sts get-caller-identity --query 'Arn' --output text
```

This shows: `arn:aws:sts::193871648423:assumed-role/SageMaker-SupplyChain-Role/SageMaker`

The role ARN is: `arn:aws:iam::193871648423:role/SageMaker-SupplyChain-Role`

**Step 2: Check if it has Lambda permissions**
```bash
aws iam list-attached-role-policies --role-name SageMaker-SupplyChain-Role
aws iam list-role-policies --role-name SageMaker-SupplyChain-Role
```

**Step 3: If it has Lambda permissions, use it**
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp/scripts
chmod +x deploy_lambda_with_role.sh

export LAMBDA_ROLE_ARN="arn:aws:iam::193871648423:role/SageMaker-SupplyChain-Role"

./deploy_lambda_with_role.sh
```

### Option C: Ask AWS Admin to Create Role (Most Reliable)

**Send this email to your AWS administrator:**

---

**Subject**: Request Lambda Execution Role Creation

Hi,

I need an IAM role created for Lambda functions. My SageMaker role doesn't have permission to create IAM roles.

**Role Details:**
- **Role Name**: `SupplyChainLambdaRole`
- **Trust Policy**: Allow Lambda service to assume this role
- **Permissions Needed**:
  1. `AWSLambdaBasicExecutionRole` (AWS managed policy)
  2. Redshift Data API access (inline policy below)

**Inline Policy JSON** (name it `RedshiftDataAPIAccess`):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "redshift-data:ExecuteStatement",
        "redshift-data:DescribeStatement",
        "redshift-data:GetStatementResult",
        "redshift-data:ListStatements",
        "redshift-serverless:GetWorkgroup",
        "redshift-serverless:GetNamespace"
      ],
      "Resource": "*"
    }
  ]
}
```

Once created, please provide me with the Role ARN.

Thank you!

---

**After they give you the ARN, use Option A Step 3 above.**

### Option D: Create Role via AWS Console

If you have AWS Console access:

**Step 1: Go to IAM Console**
https://console.aws.amazon.com/iam/home?region=us-east-1#/roles

**Step 2: Click "Create role"**

**Step 3: Select trusted entity**
- Choose "AWS service"
- Select "Lambda"
- Click "Next"

**Step 4: Add permissions**
- Search for and select: `AWSLambdaBasicExecutionRole`
- Click "Next"

**Step 5: Name and create**
- Role name: `SupplyChainLambdaRole`
- Description: `Execution role for Supply Chain Lambda functions`
- Click "Create role"

**Step 6: Add Redshift permissions**
- Find your new role in the list and click on it
- Click "Add permissions" → "Create inline policy"
- Click "JSON" tab
- Paste:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "redshift-data:ExecuteStatement",
        "redshift-data:DescribeStatement",
        "redshift-data:GetStatementResult",
        "redshift-data:ListStatements",
        "redshift-serverless:GetWorkgroup",
        "redshift-serverless:GetNamespace"
      ],
      "Resource": "*"
    }
  ]
}
```
- Click "Review policy"
- Name: `RedshiftDataAPIAccess`
- Click "Create policy"

**Step 7: Copy the Role ARN**
- It's shown at the top of the role page
- Looks like: `arn:aws:iam::193871648423:role/SupplyChainLambdaRole`

**Step 8: Deploy Lambda functions**
Use Option A Step 3 above with this ARN.

## After Deployment

**Verify deployment:**
```bash
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `supply-chain`)].FunctionName'
```

**Test a function:**
```bash
aws lambda invoke \
  --function-name supply-chain-inventory-optimizer \
  --payload '{"action":"identify_low_stock","warehouse_code":"WH-001","threshold":1.0}' \
  response.json

cat response.json
```

**Update config.yaml:**
Make sure these lines are in `mvp/config.yaml`:
```yaml
aws:
  region: us-east-1
  lambda:
    inventory_function: supply-chain-inventory-optimizer
    logistics_function: supply-chain-logistics-optimizer
    supplier_function: supply-chain-supplier-analyzer
```

**Restart app:**
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp
streamlit run app.py --server.port 8501
```

## Summary

1. **Find or create** a Lambda execution role
2. **Get the role ARN**
3. **Deploy** using `deploy_lambda_with_role.sh` with the ARN
4. **Test** the functions
5. **Update** config.yaml
6. **Restart** the app

## Need Help?

Check these files:
- `mvp/LAMBDA_DEPLOY_WITHOUT_IAM.md` - Detailed alternatives
- `mvp/LAMBDA_DEPLOYMENT_GUIDE.md` - Full deployment guide
- `mvp/lambda_functions/README.md` - Lambda documentation
