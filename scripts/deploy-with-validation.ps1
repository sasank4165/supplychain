# Enhanced Deployment Script with Tag Validation
# PowerShell version for Windows

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment,
    
    [switch]$SkipValidation,
    [switch]$StrictTags
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying Supply Chain Agentic AI Application" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host ""

# Set environment variable
$env:ENVIRONMENT = $Environment

# Check AWS credentials
Write-Host "🔐 Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    $awsAccount = $identity.Account
    $awsRegion = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }
    Write-Host "✓ AWS Account: $awsAccount" -ForegroundColor Green
    Write-Host "✓ AWS Region: $awsRegion" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials not configured. Please run 'aws configure'" -ForegroundColor Red
    exit 1
}

# Validate configuration
Write-Host ""
Write-Host "📋 Validating configuration..." -ForegroundColor Yellow
try {
    python scripts/validate-config.py --environment $Environment
    Write-Host "✓ Configuration validation passed" -ForegroundColor Green
} catch {
    Write-Host "❌ Configuration validation failed" -ForegroundColor Red
    exit 1
}

# Validate tags
if (-not $SkipValidation) {
    Write-Host ""
    Write-Host "🏷️  Validating tags..." -ForegroundColor Yellow
    try {
        $strictArg = if ($StrictTags) { "--strict" } else { "" }
        python scripts/validate-tags.py --environment $Environment $strictArg
        Write-Host "✓ Tag validation passed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Tag validation failed" -ForegroundColor Red
        Write-Host "Use -SkipValidation to bypass tag validation (not recommended)" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "⚠️  Skipping tag validation (not recommended)" -ForegroundColor Yellow
}

# Install Python dependencies
Write-Host ""
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create Lambda layer
Write-Host ""
Write-Host "🔧 Creating Lambda layer..." -ForegroundColor Yellow
if (-not (Test-Path "lambda_layers/common/python")) {
    New-Item -ItemType Directory -Force -Path "lambda_layers/common/python" | Out-Null
}
pip install boto3 -t lambda_layers/common/python/

# Bootstrap CDK (if not already done)
Write-Host ""
Write-Host "🏗️  Bootstrapping CDK..." -ForegroundColor Yellow
Set-Location cdk
cdk bootstrap "aws://$awsAccount/$awsRegion" --context environment=$Environment

# Synthesize CDK stack
Write-Host ""
Write-Host "🔨 Synthesizing CDK stack..." -ForegroundColor Yellow
cdk synth --context environment=$Environment

# Deploy CDK stack
Write-Host ""
Write-Host "☁️  Deploying CDK stack..." -ForegroundColor Yellow
cdk deploy --all --require-approval never --context environment=$Environment

# Get stack outputs
Write-Host ""
Write-Host "📋 Getting stack outputs..." -ForegroundColor Yellow

$stackPrefix = "SupplyChainApp-$Environment"

try {
    $outputs = aws cloudformation describe-stacks `
        --stack-name $stackPrefix `
        --query "Stacks[0].Outputs" `
        --output json | ConvertFrom-Json
    
    $athenaBucket = ($outputs | Where-Object { $_.OutputKey -eq "AthenaResultsBucketName" }).OutputValue
    $userPoolId = ($outputs | Where-Object { $_.OutputKey -eq "UserPoolId" }).OutputValue
    $apiEndpoint = ($outputs | Where-Object { $_.OutputKey -eq "APIEndpoint" }).OutputValue
    
    Write-Host "✓ Retrieved stack outputs" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not retrieve all stack outputs" -ForegroundColor Yellow
}

Set-Location ..

# Update .env file
Write-Host ""
Write-Host "⚙️  Updating configuration..." -ForegroundColor Yellow

$envContent = @"
ENVIRONMENT=$Environment
AWS_REGION=$awsRegion
ATHENA_OUTPUT_LOCATION=s3://$athenaBucket/
USER_POOL_ID=$userPoolId
API_ENDPOINT=$apiEndpoint
"@

$envContent | Out-File -FilePath ".env" -Encoding utf8

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Configuration saved to .env" -ForegroundColor Cyan
Write-Host "🌐 API Endpoint: $apiEndpoint" -ForegroundColor Cyan
Write-Host "👤 User Pool ID: $userPoolId" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Create users in Cognito User Pool" -ForegroundColor White
Write-Host "2. Upload sample data to S3" -ForegroundColor White
Write-Host "3. Run the Streamlit app: streamlit run app.py" -ForegroundColor White
