# Deployment Guide - Quick Navigation

This guide helps you navigate the deployment documentation for the Supply Chain AI Assistant MVP.

## Documentation Overview

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **README.md** | Main documentation with setup instructions | Start here for overview and quick start |
| **CONFIGURATION.md** | Detailed configuration reference | When configuring the application |
| **ENVIRONMENT_VARIABLES.md** | Environment variables reference | When setting up credentials and secrets |
| **infrastructure/sagemaker/README.md** | SageMaker deployment guide | When deploying to SageMaker |
| **DEPLOYMENT_GUIDE.md** | This file - navigation guide | When you need to find specific documentation |

## Getting Started Paths

### Path 1: Local Development (Fastest)

**Goal**: Get the application running on your local machine for development and testing.

**Time**: 30-45 minutes

**Steps**:
1. Read: **README.md** → Prerequisites section
2. Read: **README.md** → Quick Start section
3. Follow: Steps 1-9 in Quick Start
4. Reference: **ENVIRONMENT_VARIABLES.md** for credential setup
5. Reference: **CONFIGURATION.md** if you need to customize settings

**Key Documents**:
- README.md (Quick Start)
- ENVIRONMENT_VARIABLES.md (AWS credentials)
- CONFIGURATION.md (Optional customization)

---

### Path 2: SageMaker Deployment (Team Collaboration)

**Goal**: Deploy the application on Amazon SageMaker for team access.

**Time**: 1-2 hours

**Steps**:
1. Read: **README.md** → Prerequisites section
2. Read: **README.md** → Deployment Options → Option 2: Amazon SageMaker
3. Read: **infrastructure/sagemaker/README.md** → Complete guide
4. Follow: Step-by-step deployment in SageMaker README
5. Reference: **CONFIGURATION.md** for SageMaker-specific settings
6. Reference: **ENVIRONMENT_VARIABLES.md** for environment setup

**Key Documents**:
- infrastructure/sagemaker/README.md (Primary guide)
- README.md (Prerequisites and overview)
- CONFIGURATION.md (SageMaker configuration)
- ENVIRONMENT_VARIABLES.md (Minimal - uses IAM role)

---

### Path 3: EC2 Production Deployment (Full Control)

**Goal**: Deploy the application on EC2 for production use with custom domain.

**Time**: 2-3 hours

**Steps**:
1. Read: **README.md** → Prerequisites section
2. Read: **README.md** → Deployment Options → Option 3: EC2 Instance
3. Follow: Detailed EC2 setup steps in README.md
4. Reference: **CONFIGURATION.md** for production settings
5. Reference: **ENVIRONMENT_VARIABLES.md** for IAM role setup

**Key Documents**:
- README.md (EC2 deployment section)
- CONFIGURATION.md (Production configuration)
- ENVIRONMENT_VARIABLES.md (IAM roles)

---

## Common Tasks

### Task: Configure AWS Credentials

**Documents**:
1. **ENVIRONMENT_VARIABLES.md** → Required Environment Variables
2. **ENVIRONMENT_VARIABLES.md** → Setting Environment Variables → Method 1: .env File

**Quick Steps**:
```bash
cp .env.example .env
nano .env  # Add your AWS credentials
```

---

### Task: Update Application Configuration

**Documents**:
1. **CONFIGURATION.md** → AWS Configuration
2. **CONFIGURATION.md** → Application Configuration

**Quick Steps**:
```bash
cp config.example.yaml config.yaml
nano config.yaml  # Update with your settings
```

---

### Task: Create User Accounts

**Documents**:
1. **README.md** → Quick Start → Step 7: Create User Accounts
2. **CONFIGURATION.md** → Authentication Configuration

**Quick Steps**:
```bash
python scripts/create_user.py
# Follow prompts to create users
```

---

### Task: Deploy Infrastructure (CDK)

**Documents**:
1. **README.md** → Quick Start → Step 4: Deploy Infrastructure
2. **infrastructure/cdk/README.md** (if exists)

**Quick Steps**:
```bash
cd infrastructure/cdk
./deploy.sh  # Linux/Mac
# or
deploy.bat  # Windows
```

---

### Task: Set Up Database and Sample Data

**Documents**:
1. **README.md** → Quick Start → Step 6: Set Up Database Schema and Sample Data

**Quick Steps**:
```bash
python scripts/setup_glue_catalog.py
python scripts/generate_sample_data.py
```

---

### Task: Troubleshoot Issues

**Documents**:
1. **README.md** → Troubleshooting section (comprehensive)
2. **CONFIGURATION.md** → Troubleshooting Configuration Issues
3. **infrastructure/sagemaker/README.md** → Monitoring and Troubleshooting (for SageMaker)

**Common Issues**:
- Redshift connection: README.md → Troubleshooting → Issue 2
- Bedrock access denied: README.md → Troubleshooting → Issue 3
- Lambda errors: README.md → Troubleshooting → Issue 4
- Authentication issues: README.md → Troubleshooting → Issue 5

---

### Task: Optimize Costs

**Documents**:
1. **README.md** → Cost Estimate section
2. **CONFIGURATION.md** → Configuration Examples → Example 1: Cost-Optimized Configuration

**Quick Tips**:
- Use Claude 3 Haiku for development (83% cheaper)
- Enable query caching (30-40% savings on Redshift)
- Schedule SageMaker instance (78% savings)
- See: README.md → Cost Estimate → Cost Optimization Tips

---

### Task: Improve Performance

**Documents**:
1. **CONFIGURATION.md** → Configuration Examples → Example 2: Performance-Optimized Configuration
2. **README.md** → Troubleshooting → Issue 8: Performance Issues

**Quick Tips**:
- Increase cache size and TTL
- Use larger cache for production
- Optimize Redshift queries
- See: CONFIGURATION.md → Cache Configuration

---

### Task: Enhance Security

**Documents**:
1. **CONFIGURATION.md** → Configuration Examples → Example 3: Security-Focused Configuration
2. **ENVIRONMENT_VARIABLES.md** → Security Best Practices

**Quick Tips**:
- Use IAM roles instead of access keys
- Rotate session secrets regularly
- Shorter session timeouts
- See: ENVIRONMENT_VARIABLES.md → Security Best Practices

---

## Document Structure Reference

### README.md Structure

```
├── Overview
├── Project Structure
├── Prerequisites
│   ├── Software Requirements
│   ├── AWS Account Requirements
│   └── AWS Credentials
├── Quick Start (Steps 1-9)
├── First Steps After Login
├── Deployment Options
│   ├── Option 1: Local Development
│   ├── Option 2: Amazon SageMaker
│   └── Option 3: EC2 Instance
├── Cost Estimate
│   ├── AWS Services
│   ├── Compute Options
│   ├── Total Monthly Cost Scenarios
│   ├── Cost Breakdown by Service
│   └── Cost Optimization Tips
├── Usage Examples
│   ├── Warehouse Manager Queries
│   ├── Field Engineer Queries
│   ├── Procurement Specialist Queries
│   └── Tips for Effective Queries
├── Configuration
├── Authentication
├── Monitoring
├── Troubleshooting (10 common issues)
├── Development
└── Migration to Production
```

---

### CONFIGURATION.md Structure

```
├── Configuration Files
├── AWS Configuration
│   ├── Bedrock Configuration
│   ├── Redshift Configuration
│   ├── Glue Configuration
│   └── Lambda Configuration
├── Application Configuration
├── Cache Configuration
├── Conversation Memory Configuration
├── Cost Tracking Configuration
├── Logging Configuration
├── Authentication Configuration
├── Environment Variables
├── Deployment-Specific Configurations
│   ├── Local Development
│   ├── SageMaker
│   └── EC2 Production
├── Configuration Examples
│   ├── Cost-Optimized
│   ├── Performance-Optimized
│   └── Security-Focused
├── Configuration Validation
├── Troubleshooting Configuration Issues
└── Best Practices
```

---

### ENVIRONMENT_VARIABLES.md Structure

```
├── Overview
├── Required Environment Variables
│   ├── AWS_REGION
│   ├── AWS_ACCOUNT_ID
│   └── SESSION_SECRET
├── Optional Environment Variables
│   ├── AWS_ACCESS_KEY_ID
│   ├── AWS_SECRET_ACCESS_KEY
│   └── Streamlit Variables
├── Setting Environment Variables
│   ├── Method 1: .env File
│   ├── Method 2: Shell Export
│   ├── Method 3: System Variables
│   └── Method 4: IAM Roles
├── Environment-Specific Configurations
│   ├── Local Development
│   ├── SageMaker Deployment
│   └── EC2 Production
├── Verifying Environment Variables
├── Security Best Practices
├── Troubleshooting
└── Quick Reference Table
```

---

### infrastructure/sagemaker/README.md Structure

```
├── Overview
├── Prerequisites
├── Deployment Options
│   ├── Option 1: SageMaker Notebook Instance
│   └── Option 2: SageMaker Studio
├── Step-by-Step Deployment (7 steps)
├── Lifecycle Configuration (Auto-Start)
├── Monitoring and Troubleshooting
├── Cost Optimization
│   ├── Instance Scheduling
│   └── Right-Sizing
├── Upgrading and Maintenance
├── Security Best Practices
└── Next Steps
```

---

## Quick Reference: File Locations

### Configuration Files

```
mvp/
├── config.yaml                          # Main configuration (create from template)
├── config.example.yaml                  # Configuration template
├── .env                                 # Environment variables (create from template)
├── .env.example                         # Environment variables template
└── auth/
    ├── users.json                       # User credentials (create from template)
    └── users.json.example               # User credentials template
```

### Documentation Files

```
mvp/
├── README.md                            # Main documentation
├── CONFIGURATION.md                     # Configuration reference
├── ENVIRONMENT_VARIABLES.md             # Environment variables reference
├── DEPLOYMENT_GUIDE.md                  # This file
└── infrastructure/
    └── sagemaker/
        ├── README.md                    # SageMaker deployment guide
        ├── setup_notebook.sh            # SageMaker setup script
        └── lifecycle_config.sh          # SageMaker auto-start script
```

### Scripts

```
mvp/
└── scripts/
    ├── setup_venv.sh                    # Python environment setup (Linux/Mac)
    ├── setup_venv.bat                   # Python environment setup (Windows)
    ├── setup_glue_catalog.py            # Create Glue catalog tables
    ├── generate_sample_data.py          # Generate and load sample data
    ├── create_user.py                   # Create user accounts
    └── deploy_lambda.sh                 # Deploy Lambda functions
```

---

## Recommended Reading Order

### For First-Time Users

1. **README.md** → Overview and Prerequisites
2. **README.md** → Quick Start (complete all steps)
3. **README.md** → Usage Examples (try example queries)
4. **README.md** → Troubleshooting (if issues arise)

### For Administrators

1. **README.md** → Overview and Prerequisites
2. **ENVIRONMENT_VARIABLES.md** → Complete guide
3. **CONFIGURATION.md** → Complete guide
4. **README.md** → Deployment Options (choose one)
5. **infrastructure/sagemaker/README.md** (if using SageMaker)

### For Developers

1. **README.md** → Overview and Project Structure
2. **README.md** → Quick Start (local development)
3. **CONFIGURATION.md** → Development configuration
4. **README.md** → Development section
5. Component-specific READMEs in each directory

---

## Getting Help

### Step 1: Check Documentation

1. Search this guide for your task
2. Read the relevant documentation section
3. Follow the step-by-step instructions

### Step 2: Check Troubleshooting

1. **README.md** → Troubleshooting section
2. Find your issue in the list
3. Follow the solution steps

### Step 3: Check Logs

```bash
# Application logs
tail -f logs/app.log

# Cost tracking logs
tail -f logs/cost_tracking.log

# Streamlit logs (if running as service)
sudo journalctl -u supply-chain-mvp -f
```

### Step 4: Verify Configuration

```bash
# Check configuration file
python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"

# Check environment variables
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('AWS_REGION'))"

# Test AWS connectivity
aws sts get-caller-identity
```

### Step 5: Contact Support

If still having issues:
- Provide error messages from logs
- Describe what you were trying to do
- Include your deployment type (local, SageMaker, EC2)
- Share relevant configuration (redact secrets!)

---

## Additional Resources

### AWS Documentation

- [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/)
- [Redshift Serverless](https://docs.aws.amazon.com/redshift/latest/mgmt/serverless-whatis.html)
- [AWS Glue Data Catalog](https://docs.aws.amazon.com/glue/latest/dg/catalog-and-crawler.html)
- [AWS Lambda](https://docs.aws.amazon.com/lambda/)
- [Amazon SageMaker](https://docs.aws.amazon.com/sagemaker/)

### Python Documentation

- [Streamlit](https://docs.streamlit.io/)
- [Boto3 (AWS SDK)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Python dotenv](https://pypi.org/project/python-dotenv/)

### Tools

- [AWS CLI](https://docs.aws.amazon.com/cli/)
- [AWS CDK](https://docs.aws.amazon.com/cdk/)
- [YAML Syntax](https://yaml.org/)

---

## Document Maintenance

This deployment guide is maintained alongside the application. When updating:

1. Update relevant documentation files
2. Update this navigation guide if structure changes
3. Test all documented procedures
4. Update version numbers and dates

**Last Updated**: 2024-01-15

**Version**: 1.0.0
