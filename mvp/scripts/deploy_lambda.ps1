# Deploy Lambda Functions for Supply Chain MVP
# PowerShell script for Windows users

param(
    [string]$AwsRegion = "us-east-1",
    [string]$RedshiftWorkgroup = "supply-chain-mvp",
    [string]$RedshiftDatabase = "supply_chain_db",
    [string]$LambdaRoleName = "SupplyChainLambdaRole"
)

# Lambda function names
$InventoryFunction = "supply-chain-inventory-optimizer"
$LogisticsFunction = "supply-chain-logistics-optimizer"
$SupplierFunction = "supply-chain-supplier-analyzer"

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$LambdaDir = Join-Path $ProjectRoot "lambda_functions"

Write-Host "=== Supply Chain Lambda Deployment ===" -ForegroundColor Green
Write-Host "Region: $AwsRegion"
Write-Host "Redshift Workgroup: $RedshiftWorkgroup"
Write-Host "Redshift Database: $RedshiftDatabase"
Write-Host ""

# Function to check if AWS CLI is installed
function Test-AwsCli {
    try {
        $null = aws --version
        Write-Host "✓ AWS CLI found" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Error: AWS CLI is not installed" -ForegroundColor Red
        Write-Host "Please install AWS CLI: https://aws.amazon.com/cli/"
        return $false
    }
}

# Function to check AWS credentials
function Test-AwsCredentials {
    try {
        $identity = aws sts get-caller-identity 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ AWS credentials configured" -ForegroundColor Green
            Write-Host $identity
            Write-Host ""
            return $true
        }
        else {
            throw "Credentials not configured"
        }
    }
    catch {
        Write-Host "Error: AWS credentials not configured" -ForegroundColor Red
        Write-Host "Please configure AWS credentials using 'aws configure'"
        return $false
    }
}

# Function to get or create IAM role for Lambda
function Get-OrCreateLambdaRole {
    Write-Host "Checking Lambda IAM role..." -ForegroundColor Yellow
    
    # Check if role exists
    $roleExists = aws iam get-role --role-name $LambdaRoleName 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ IAM role $LambdaRoleName already exists" -ForegroundColor Green
        $roleArn = (aws iam get-role --role-name $LambdaRoleName --query 'Role.Arn' --output text)
    }
    else {
        Write-Host "Creating IAM role $LambdaRoleName..."
        
        # Create trust policy
        $trustPolicy = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
"@
        
        # Create role
        $roleArn = aws iam create-role `
            --role-name $LambdaRoleName `
            --assume-role-policy-document $trustPolicy `
            --query 'Role.Arn' `
            --output text
        
        Write-Host "✓ Created IAM role: $roleArn" -ForegroundColor Green
        
        # Attach policies
        Write-Host "Attaching policies to role..."
        
        # Basic Lambda execution
        aws iam attach-role-policy `
            --role-name $LambdaRoleName `
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        
        # Redshift Data API access
        $redshiftPolicy = @"
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
"@
        
        aws iam put-role-policy `
            --role-name $LambdaRoleName `
            --policy-name "RedshiftDataAPIAccess" `
            --policy-document $redshiftPolicy
        
        Write-Host "✓ Attached policies to role" -ForegroundColor Green
        
        # Wait for role to propagate
        Write-Host "Waiting for role to propagate..."
        Start-Sleep -Seconds 10
    }
    
    Write-Host "Role ARN: $roleArn"
    Write-Host ""
    return $roleArn
}

# Function to package and deploy a Lambda function
function Deploy-Lambda {
    param(
        [string]$FunctionName,
        [string]$FunctionDir,
        [string]$Description,
        [string]$RoleArn
    )
    
    Write-Host "Deploying $FunctionName..." -ForegroundColor Yellow
    
    # Create deployment package directory
    $deployDir = Join-Path $LambdaDir ".deploy\$FunctionName"
    if (Test-Path $deployDir) {
        Remove-Item -Recurse -Force $deployDir
    }
    New-Item -ItemType Directory -Path $deployDir | Out-Null
    
    # Copy handler code
    Copy-Item (Join-Path $FunctionDir "handler.py") $deployDir
    
    # Install dependencies if requirements.txt exists
    $requirementsFile = Join-Path $FunctionDir "requirements.txt"
    if (Test-Path $requirementsFile) {
        Write-Host "Installing dependencies..."
        pip install -r $requirementsFile -t $deployDir --quiet
    }
    
    # Create ZIP package
    Write-Host "Creating deployment package..."
    $zipFile = Join-Path $LambdaDir ".deploy\$FunctionName.zip"
    if (Test-Path $zipFile) {
        Remove-Item $zipFile
    }
    
    # Use PowerShell's Compress-Archive
    $currentDir = Get-Location
    Set-Location $deployDir
    Compress-Archive -Path * -DestinationPath $zipFile
    Set-Location $currentDir
    
    # Check if function exists
    $functionExists = aws lambda get-function --function-name $FunctionName --region $AwsRegion 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Updating existing function..."
        aws lambda update-function-code `
            --function-name $FunctionName `
            --zip-file "fileb://$zipFile" `
            --region $AwsRegion `
            --output text | Out-Null
        
        # Update environment variables
        aws lambda update-function-configuration `
            --function-name $FunctionName `
            --environment "Variables={REDSHIFT_WORKGROUP_NAME=$RedshiftWorkgroup,REDSHIFT_DATABASE=$RedshiftDatabase}" `
            --region $AwsRegion `
            --output text | Out-Null
        
        Write-Host "✓ Updated function $FunctionName" -ForegroundColor Green
    }
    else {
        Write-Host "Creating new function..."
        aws lambda create-function `
            --function-name $FunctionName `
            --runtime python3.11 `
            --role $RoleArn `
            --handler handler.lambda_handler `
            --zip-file "fileb://$zipFile" `
            --timeout 30 `
            --memory-size 256 `
            --environment "Variables={REDSHIFT_WORKGROUP_NAME=$RedshiftWorkgroup,REDSHIFT_DATABASE=$RedshiftDatabase}" `
            --description $Description `
            --region $AwsRegion `
            --output text | Out-Null
        
        Write-Host "✓ Created function $FunctionName" -ForegroundColor Green
    }
    
    # Clean up
    Remove-Item -Recurse -Force $deployDir
    Remove-Item $zipFile
    
    Write-Host ""
}

# Function to test a Lambda function
function Test-LambdaFunction {
    param(
        [string]$FunctionName,
        [string]$TestPayload
    )
    
    Write-Host "Testing $FunctionName..." -ForegroundColor Yellow
    
    # Invoke function
    $responseFile = "$env:TEMP\lambda-response.json"
    $response = aws lambda invoke `
        --function-name $FunctionName `
        --payload $TestPayload `
        --region $AwsRegion `
        $responseFile 2>&1
    
    # Check for errors
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Function invoked successfully" -ForegroundColor Green
        Write-Host "Response:"
        Get-Content $responseFile | ConvertFrom-Json | ConvertTo-Json -Depth 10
    }
    else {
        Write-Host "✗ Function invocation failed" -ForegroundColor Red
        Write-Host $response
    }
    
    if (Test-Path $responseFile) {
        Remove-Item $responseFile
    }
    Write-Host ""
}

# Main deployment flow
function Main {
    Write-Host "Starting deployment..."
    Write-Host ""
    
    # Pre-flight checks
    if (-not (Test-AwsCli)) {
        exit 1
    }
    
    if (-not (Test-AwsCredentials)) {
        exit 1
    }
    
    # Get or create IAM role
    $roleArn = Get-OrCreateLambdaRole
    
    # Deploy Lambda functions
    Deploy-Lambda `
        -FunctionName $InventoryFunction `
        -FunctionDir (Join-Path $LambdaDir "inventory_optimizer") `
        -Description "Inventory optimization tools for Warehouse Managers" `
        -RoleArn $roleArn
    
    Deploy-Lambda `
        -FunctionName $LogisticsFunction `
        -FunctionDir (Join-Path $LambdaDir "logistics_optimizer") `
        -Description "Logistics optimization tools for Field Engineers" `
        -RoleArn $roleArn
    
    Deploy-Lambda `
        -FunctionName $SupplierFunction `
        -FunctionDir (Join-Path $LambdaDir "supplier_analyzer") `
        -Description "Supplier analysis tools for Procurement Specialists" `
        -RoleArn $roleArn
    
    Write-Host "=== Deployment Complete ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "Lambda Functions:"
    Write-Host "  - $InventoryFunction"
    Write-Host "  - $LogisticsFunction"
    Write-Host "  - $SupplierFunction"
    Write-Host ""
    
    # Test functions (optional)
    $test = Read-Host "Do you want to test the Lambda functions? (y/n)"
    if ($test -eq 'y' -or $test -eq 'Y') {
        Write-Host ""
        Write-Host "Testing Lambda functions..." -ForegroundColor Yellow
        Write-Host ""
        
        # Test Inventory Optimizer
        Test-LambdaFunction -FunctionName $InventoryFunction -TestPayload '{"action":"identify_low_stock","warehouse_code":"WH-001","threshold":1.0}'
        
        # Test Logistics Optimizer
        Test-LambdaFunction -FunctionName $LogisticsFunction -TestPayload '{"action":"identify_delayed_orders","warehouse_code":"WH-001","days":7}'
        
        # Test Supplier Analyzer
        Test-LambdaFunction -FunctionName $SupplierFunction -TestPayload '{"action":"analyze_purchase_trends","days":90,"group_by":"month"}'
    }
    
    Write-Host "Done!" -ForegroundColor Green
}

# Run main function
Main
