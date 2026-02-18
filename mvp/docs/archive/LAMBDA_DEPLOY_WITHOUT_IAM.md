# Deploy Lambda Functions Without IAM Role Creation Permission

## Issue
Your SageMaker role doesn't have permission to create IAM roles:
```
AccessDenied: User is not authorized to perform: iam:CreateRole
```

## Solution Options

### Option 1: Use Existing IAM Role (Recommended)

If you already have a Lambda execution role, use it directly.

#### Step 1: Find Existing Lambda Role
```bash
aws iam list-roles --query 'Roles[?contains(RoleName, `Lambda`)].RoleName'
```

Look for roles like:
- `AWSLambdaBasicExecutionRole`
- `LambdaExecutionRole`
- Any role with "Lambda" in the name

#### Step 2: Get the Role ARN
```bash
aws iam get-role --role-name YOUR_ROLE_NAME --query 'Role.Arn' --output text
```

Example output:
```
arn:aws:iam::193871648423:role/LambdaExecutionRole
```

#### Step 3: Deploy with Existing Role
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp/scripts

# Set the role ARN
export LAMBDA_ROLE_ARN="arn:aws:iam::193871648423:role/YOUR_ROLE_NAME"

# Run modified deployment
./deploy_lambda_with_role.sh
```

### Option 2: Ask AWS Administrator to Create Role

Send this to your AWS administrator:

**Subject**: Request Lambda Execution Role for Supply Chain Project

**Message**:
```
Hi,

I need an IAM role created for Lambda functions in the Supply Chain project.

Role Name: SupplyChainLambdaRole
Trust Policy: Lambda service (lambda.amazonaws.com)

Required Permissions:
1. AWSLambdaBasicExecutionRole (managed policy)
2. Redshift Data API access (inline policy below)

Inline Policy (RedshiftDataAPIAccess):
{
  "Version": "2012-10-17",
  "Statement": [
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

Once created, please provide me with the Role ARN.

Thank you!
```

After they create it, they'll give you an ARN like:
```
arn:aws:iam::193871648423:role/SupplyChainLambdaRole
```

Then use Option 1 above to deploy.

### Option 3: Create Role via AWS Console

If you have console access:

#### Step 1: Go to IAM Console
https://console.aws.amazon.com/iam/

#### Step 2: Create Role
1. Click "Roles" → "Create role"
2. Select "AWS service" → "Lambda"
3. Click "Next"

#### Step 3: Attach Policies
1. Search and select: `AWSLambdaBasicExecutionRole`
2. Click "Next"

#### Step 4: Name the Role
- Role name: `SupplyChainLambdaRole`
- Description: `Execution role for Supply Chain Lambda functions`
- Click "Create role"

#### Step 5: Add Redshift Permissions
1. Find your new role in the list
2. Click on it
3. Click "Add permissions" → "Create inline policy"
4. Click "JSON" tab
5. Paste this policy:
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
6. Click "Review policy"
7. Name: `RedshiftDataAPIAccess`
8. Click "Create policy"

#### Step 6: Get Role ARN
1. Click on the role
2. Copy the ARN (looks like: `arn:aws:iam::193871648423:role/SupplyChainLambdaRole`)

#### Step 7: Deploy Lambda Functions
Use the ARN from Step 6 with Option 1 above.

### Option 4: Manual Lambda Deployment

If all else fails, deploy manually via AWS Console:

#### For Each Function (Inventory, Logistics, Supplier):

**1. Package the Function**
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp/lambda_functions/inventory_optimizer
zip -r function.zip handler.py
```

**2. Go to Lambda Console**
https://console.aws.amazon.com/lambda/

**3. Create Function**
- Click "Create function"
- Choose "Author from scratch"
- Function name: `supply-chain-inventory-optimizer`
- Runtime: Python 3.11
- Architecture: x86_64
- Execution role: Choose existing role (from Option 3)
- Click "Create function"

**4. Upload Code**
- In the "Code" tab
- Click "Upload from" → ".zip file"
- Select the `function.zip` you created
- Click "Save"

**5. Configure Environment Variables**
- Click "Configuration" tab
- Click "Environment variables"
- Click "Edit"
- Add:
  - Key: `REDSHIFT_WORKGROUP_NAME`, Value: `supply-chain-mvp`
  - Key: `REDSHIFT_DATABASE`, Value: `supply_chain_db`
- Click "Save"

**6. Adjust Settings**
- Click "Configuration" → "General configuration"
- Click "Edit"
- Timeout: 30 seconds
- Memory: 256 MB
- Click "Save"

**7. Repeat for Other Functions**
- `supply-chain-logistics-optimizer` (use `logistics_optimizer/handler.py`)
- `supply-chain-supplier-analyzer` (use `supplier_analyzer/handler.py`)

