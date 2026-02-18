# Lambda Deployment Solution - IAM Permission Issue

## Problem Summary
Your deployment failed with:
```
AccessDenied: User is not authorized to perform: iam:CreateRole
```

Your SageMaker role (`SageMaker-SupplyChain-Role`) cannot create IAM roles.

## ✅ Solution: Use Existing Role

I've created a new deployment script that uses an existing IAM role instead of creating one.

## Quick Steps

### Step 1: Find an Existing Lambda Role

Run this command on SageMaker:
```bash
aws iam list-roles --query 'Roles[?contains(RoleName, `Lambda`) || contains(RoleName, `lambda`)].RoleName'
```

**If you see any roles listed**, pick one and go to Step 2.

**If no roles are listed**, you have 3 options:
- **Option A**: Ask your AWS admin to create a role (see below)
- **Option B**: Create role via AWS Console (see `mvp/FIX_IAM_PERMISSION_ISSUE.md`)
- **Option C**: Try using your SageMaker role (see below)

### Step 2: Get the Role ARN

```bash
# Replace ROLE_NAME with the role from Step 1
aws iam get-role --role-name ROLE_NAME --query 'Role.Arn' --output text
```

Example output:
```
arn:aws:iam::193871648423:role/LambdaExecutionRole
```

### Step 3: Deploy Lambda Functions

```bash
cd /home/ec2-user/SageMaker/supplychain/mvp/scripts

# Make script executable
chmod +x deploy_lambda_with_role.sh

# Set the role ARN (use your actual ARN from Step 2)
export LAMBDA_ROLE_ARN="arn:aws:iam::193871648423:role/YOUR_ROLE_NAME"

# Deploy
./deploy_lambda_with_role.sh
```

The script will:
1. ✓ Verify the role exists
2. ✓ Package each Lambda function
3. ✓ Deploy all 3 functions
4. ✓ Configure environment variables
5. ✓ Optionally test each function

### Step 4: Verify Deployment

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

### Step 5: Test a Function

```bash
aws lambda invoke \
  --function-name supply-chain-inventory-optimizer \
  --payload '{"action":"identify_low_stock","warehouse_code":"WH-001","threshold":1.0}' \
  response.json

cat response.json
```

### Step 6: Restart Your App

```bash
cd /home/ec2-user/SageMaker/supplychain/mvp
streamlit run app.py --server.port 8501
```

## Alternative: Try Using SageMaker Role

Your SageMaker role might already have Lambda permissions.

```bash
cd /home/ec2-user/SageMaker/supplychain/mvp/scripts
chmod +x deploy_lambda_with_role.sh

# Use your SageMaker role
export LAMBDA_ROLE_ARN="arn:aws:iam::193871648423:role/SageMaker-SupplyChain-Role"

./deploy_lambda_with_role.sh
```

If this works, great! If not, the script will tell you the role doesn't have the right permissions.

## Request Role from AWS Admin

If you need your AWS admin to create a role, send them this:

---

**Subject**: Request Lambda Execution Role for Supply Chain Project

Hi,

I need an IAM role created for Lambda functions. My SageMaker role doesn't have `iam:CreateRole` permission.

**Role Configuration:**

**1. Create Role**
- Role name: `SupplyChainLambdaRole`
- Trusted entity: Lambda service (`lambda.amazonaws.com`)

**2. Attach Managed Policy**
- `AWSLambdaBasicExecutionRole`

**3. Add Inline Policy** (name: `RedshiftDataAPIAccess`)
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

**4. Provide Role ARN**
After creation, please send me the Role ARN (looks like: `arn:aws:iam::193871648423:role/SupplyChainLambdaRole`)

Thank you!

---

## Files Created

I've created these files to help you:

1. **`mvp/scripts/deploy_lambda_with_role.sh`** - New deployment script that uses existing role
2. **`mvp/FIX_IAM_PERMISSION_ISSUE.md`** - Quick fix guide
3. **`mvp/LAMBDA_DEPLOY_WITHOUT_IAM.md`** - Detailed alternatives including manual deployment
4. **`mvp/LAMBDA_DEPLOYMENT_SOLUTION.md`** - This file

## Summary

```bash
# 1. Find existing Lambda role
aws iam list-roles --query 'Roles[?contains(RoleName, `Lambda`)].RoleName'

# 2. Get role ARN
aws iam get-role --role-name ROLE_NAME --query 'Role.Arn' --output text

# 3. Deploy with that role
cd /home/ec2-user/SageMaker/supplychain/mvp/scripts
chmod +x deploy_lambda_with_role.sh
export LAMBDA_ROLE_ARN="arn:aws:iam::193871648423:role/YOUR_ROLE_NAME"
./deploy_lambda_with_role.sh

# 4. Verify
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `supply-chain`)].FunctionName'

# 5. Test
aws lambda invoke --function-name supply-chain-inventory-optimizer --payload '{"action":"identify_low_stock","warehouse_code":"WH-001","threshold":1.0}' response.json

# 6. Restart app
cd /home/ec2-user/SageMaker/supplychain/mvp
streamlit run app.py --server.port 8501
```

## Next Steps

1. **Try Step 1 above** to find an existing Lambda role
2. **If found**, use Steps 2-6 to deploy
3. **If not found**, request role from AWS admin or create via console
4. **After deployment**, test the functions and restart your app

The application will then have full functionality with all specialized agents working!
