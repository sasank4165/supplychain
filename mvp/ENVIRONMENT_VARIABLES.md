# Environment Variables Reference

Quick reference guide for environment variables used in the Supply Chain AI Assistant MVP.

## Overview

Environment variables provide configuration values that:
- Should not be committed to version control (secrets, credentials)
- Vary between deployment environments (dev, staging, production)
- Are specific to the deployment instance

## Required Environment Variables

### AWS_REGION

**Description**: AWS region where resources are deployed

**Required**: Yes

**Example**: `us-east-1`

**Valid Values**:
- `us-east-1` (US East - N. Virginia) - Recommended
- `us-west-2` (US West - Oregon)
- `eu-west-1` (Europe - Ireland)
- `ap-southeast-1` (Asia Pacific - Singapore)

**How to Set**:
```bash
# In .env file
AWS_REGION=us-east-1

# Or export in shell
export AWS_REGION=us-east-1
```

---

### AWS_ACCOUNT_ID

**Description**: Your AWS account ID (12-digit number)

**Required**: Yes

**Example**: `123456789012`

**How to Find**:
```bash
aws sts get-caller-identity --query Account --output text
```

**How to Set**:
```bash
# In .env file
AWS_ACCOUNT_ID=123456789012

# Or export in shell
export AWS_ACCOUNT_ID=123456789012
```

---

### SESSION_SECRET

**Description**: Secret key for encrypting session tokens

**Required**: Yes

**Example**: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6`

**Security Requirements**:
- At least 32 characters long
- Cryptographically random
- Never commit to version control
- Unique per deployment

**How to Generate**:
```bash
# Linux/Mac
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"

# Windows PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

**How to Set**:
```bash
# In .env file
SESSION_SECRET=your_generated_secret_here

# Or export in shell
export SESSION_SECRET=your_generated_secret_here
```

---

## Optional Environment Variables

### AWS_ACCESS_KEY_ID

**Description**: AWS access key for authentication

**Required**: Only for local development (not needed on EC2/SageMaker with IAM roles)

**Example**: `AKIAIOSFODNN7EXAMPLE`

**Security Warning**: Never commit to version control!

**How to Get**:
1. Go to AWS Console → IAM → Users → Your User → Security Credentials
2. Create access key
3. Copy the access key ID

**How to Set**:
```bash
# In .env file
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE

# Or use AWS CLI
aws configure
```

**Best Practice**: Use IAM roles instead of access keys when possible (EC2, SageMaker, Lambda).

---

### AWS_SECRET_ACCESS_KEY

**Description**: AWS secret key for authentication

**Required**: Only for local development (not needed on EC2/SageMaker with IAM roles)

**Example**: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

**Security Warning**: Never commit to version control! Never share!

**How to Get**:
- Shown only once when creating access key
- If lost, must create new access key

**How to Set**:
```bash
# In .env file
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Or use AWS CLI
aws configure
```

**Best Practice**: Use IAM roles instead of access keys when possible.

---

### AWS_DEFAULT_REGION

**Description**: Alternative to AWS_REGION (used by AWS CLI)

**Required**: No (use AWS_REGION instead)

**Example**: `us-east-1`

**Note**: If both are set, AWS_REGION takes precedence in the application.

---

### STREAMLIT_SERVER_PORT

**Description**: Port for Streamlit application

**Required**: No

**Default**: `8501`

**Example**: `8502`

**How to Set**:
```bash
# In .env file
STREAMLIT_SERVER_PORT=8502

# Or pass as command line argument
streamlit run app.py --server.port 8502
```

---

### STREAMLIT_SERVER_ADDRESS

**Description**: Address for Streamlit to bind to

**Required**: No

**Default**: `localhost`

**Example**: `0.0.0.0` (listen on all interfaces)

**How to Set**:
```bash
# In .env file
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Or pass as command line argument
streamlit run app.py --server.address 0.0.0.0
```

**Use Cases**:
- `localhost`: Local development only
- `0.0.0.0`: Remote access (EC2, SageMaker)

---

## Setting Environment Variables

### Method 1: .env File (Recommended)

Create a `.env` file in the `mvp/` directory:

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env
```

Example `.env` file:
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Application Configuration
SESSION_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6

# Optional: Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

**Pros**:
- Easy to manage
- Automatically loaded by application
- Can be different per environment

**Cons**:
- Must not be committed to version control
- Must be created on each deployment

---

### Method 2: Shell Export

Export variables in your shell:

```bash
# Bash/Zsh
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
export SESSION_SECRET=your_secret_here

# Windows CMD
set AWS_REGION=us-east-1
set AWS_ACCOUNT_ID=123456789012
set SESSION_SECRET=your_secret_here

# Windows PowerShell
$env:AWS_REGION="us-east-1"
$env:AWS_ACCOUNT_ID="123456789012"
$env:SESSION_SECRET="your_secret_here"
```

**Pros**:
- No files to manage
- Temporary (cleared when shell closes)

**Cons**:
- Must be set every time
- Not persistent across sessions

---

### Method 3: System Environment Variables

Set system-wide environment variables:

**Linux/Mac**:
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export AWS_REGION=us-east-1' >> ~/.bashrc
echo 'export AWS_ACCOUNT_ID=123456789012' >> ~/.bashrc
echo 'export SESSION_SECRET=your_secret_here' >> ~/.bashrc

# Reload
source ~/.bashrc
```

**Windows**:
1. Search for "Environment Variables" in Start Menu
2. Click "Edit the system environment variables"
3. Click "Environment Variables" button
4. Add new variables under "User variables"

**Pros**:
- Persistent across sessions
- Available to all applications

**Cons**:
- Harder to manage
- Affects all applications
- Security risk if shared system

---

### Method 4: IAM Roles (Recommended for AWS Deployments)

Use IAM roles instead of access keys:

**EC2**:
1. Create IAM role with required permissions
2. Attach role to EC2 instance
3. No need to set AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY

**SageMaker**:
1. Create IAM role with required permissions
2. Attach role to SageMaker Notebook Instance
3. No need to set AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY

**Lambda**:
1. Create IAM role with required permissions
2. Assign role to Lambda function
3. No need to set AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY

**Pros**:
- Most secure (no credentials in files)
- Automatic credential rotation
- Easier to manage permissions

**Cons**:
- Only works on AWS services
- Requires IAM role setup

---

## Environment-Specific Configurations

### Local Development

```bash
# .env for local development
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
SESSION_SECRET=dev_secret_key_here
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

---

### SageMaker Deployment

```bash
# .env for SageMaker (minimal - uses IAM role)
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
SESSION_SECRET=sagemaker_secret_key_here
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

**Note**: No AWS credentials needed - SageMaker uses IAM role.

---

### EC2 Production Deployment

```bash
# .env for EC2 (minimal - uses IAM role)
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
SESSION_SECRET=production_secret_key_here
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

**Note**: No AWS credentials needed - EC2 uses IAM role.

---

## Verifying Environment Variables

### Check if Variables are Set

```bash
# Linux/Mac/Windows PowerShell
echo $AWS_REGION
echo $AWS_ACCOUNT_ID
echo $SESSION_SECRET

# Windows CMD
echo %AWS_REGION%
echo %AWS_ACCOUNT_ID%
echo %SESSION_SECRET%
```

### List All Environment Variables

```bash
# Linux/Mac
env | grep AWS
env | grep SESSION

# Windows CMD
set | findstr AWS
set | findstr SESSION

# Windows PowerShell
Get-ChildItem Env: | Where-Object {$_.Name -like "*AWS*"}
Get-ChildItem Env: | Where-Object {$_.Name -like "*SESSION*"}
```

### Test in Python

```python
import os

# Check if variables are set
print(f"AWS_REGION: {os.getenv('AWS_REGION')}")
print(f"AWS_ACCOUNT_ID: {os.getenv('AWS_ACCOUNT_ID')}")
print(f"SESSION_SECRET: {'Set' if os.getenv('SESSION_SECRET') else 'Not set'}")

# Load from .env file
from dotenv import load_dotenv
load_dotenv()

print(f"After loading .env:")
print(f"AWS_REGION: {os.getenv('AWS_REGION')}")
print(f"AWS_ACCOUNT_ID: {os.getenv('AWS_ACCOUNT_ID')}")
```

---

## Security Best Practices

### 1. Never Commit Secrets

Add to `.gitignore`:
```
.env
.env.*
!.env.example
```

### 2. Use Different Secrets per Environment

- Development: `dev_secret_key`
- Staging: `staging_secret_key`
- Production: `production_secret_key`

### 3. Rotate Secrets Regularly

```bash
# Generate new session secret
openssl rand -hex 32

# Update .env file
nano .env

# Restart application
```

### 4. Use IAM Roles When Possible

Prefer IAM roles over access keys:
- EC2: Attach IAM role to instance
- SageMaker: Attach IAM role to notebook
- Lambda: Assign IAM role to function

### 5. Limit Access Key Permissions

If using access keys:
- Create dedicated IAM user for application
- Grant only required permissions
- Enable MFA for IAM user
- Rotate keys regularly

### 6. Monitor for Exposed Secrets

Use tools to scan for exposed secrets:
- git-secrets
- truffleHog
- GitHub secret scanning

### 7. Use AWS Secrets Manager (Advanced)

For production, consider AWS Secrets Manager:
```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

# Use in application
session_secret = get_secret('supply-chain-mvp/session-secret')
```

---

## Troubleshooting

### Issue: Environment variable not found

```bash
# Check if .env file exists
ls -la .env

# Check if variable is in .env
cat .env | grep AWS_REGION

# Verify python-dotenv is installed
pip show python-dotenv

# Test loading .env
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('AWS_REGION'))"
```

### Issue: AWS credentials not working

```bash
# Test AWS credentials
aws sts get-caller-identity

# If error, check credentials
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# Reconfigure if needed
aws configure
```

### Issue: Session secret not set

```bash
# Check if SESSION_SECRET is set
echo $SESSION_SECRET

# If empty, generate and set
openssl rand -hex 32
export SESSION_SECRET=generated_secret_here

# Or add to .env
echo "SESSION_SECRET=generated_secret_here" >> .env
```

---

## Quick Reference Table

| Variable | Required | Default | Used For |
|----------|----------|---------|----------|
| `AWS_REGION` | Yes | - | AWS service region |
| `AWS_ACCOUNT_ID` | Yes | - | Glue catalog ID |
| `SESSION_SECRET` | Yes | - | Session encryption |
| `AWS_ACCESS_KEY_ID` | No* | - | AWS authentication |
| `AWS_SECRET_ACCESS_KEY` | No* | - | AWS authentication |
| `STREAMLIT_SERVER_PORT` | No | 8501 | Application port |
| `STREAMLIT_SERVER_ADDRESS` | No | localhost | Bind address |

\* Required for local development, not needed with IAM roles

---

## Additional Resources

- [AWS Environment Variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)
- [Python dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [AWS IAM Roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)
- [Streamlit Configuration](https://docs.streamlit.io/library/advanced-features/configuration)
