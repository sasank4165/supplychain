# SageMaker Deployment Guide

This guide provides step-by-step instructions for deploying the Supply Chain AI Assistant on Amazon SageMaker Notebook Instances.

## Overview

Amazon SageMaker provides a managed Jupyter notebook environment that's ideal for deploying the MVP application. Benefits include:

- **Integrated AWS Authentication**: Uses IAM roles for AWS service access
- **Team Collaboration**: Multiple users can access the same notebook instance
- **Managed Infrastructure**: No need to manage EC2 instances directly
- **Cost-Effective**: Pay only for compute time used
- **Easy Scaling**: Can upgrade instance type as needed

## Prerequisites

1. **AWS Account** with permissions to:
   - Create SageMaker Notebook Instances
   - Create IAM roles and policies
   - Access Bedrock, Redshift, Lambda, and Glue services

2. **AWS Resources** already deployed:
   - Redshift Serverless workgroup
   - AWS Glue Data Catalog database
   - Lambda functions (Inventory, Logistics, Supplier)
   - Sample data loaded

3. **Application Code** available either:
   - Uploaded to the notebook instance
   - In a Git repository
   - In an S3 bucket

## Deployment Options

### Option 1: SageMaker Notebook Instance (Recommended for MVP)

**Use Case**: Development, testing, team collaboration

**Instance Type**: ml.t3.medium (2 vCPU, 4 GB RAM)

**Cost**: ~$0.05/hour (~$36/month for 24/7, or ~$8/month for 8 hours/day, 5 days/week)

### Option 2: SageMaker Studio

**Use Case**: Integrated development environment with Jupyter

**Cost**: Similar to Notebook Instance, but with additional Studio features

## Step-by-Step Deployment

### Step 1: Create IAM Role for SageMaker

1. Go to **IAM Console** → **Roles** → **Create role**

2. Select **SageMaker** as the trusted entity

3. Attach the following AWS managed policies:
   - `AmazonSageMakerFullAccess`

4. Create and attach a custom inline policy for application access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*:*:model/anthropic.claude-3-5-sonnet-*"
    },
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
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:*:*:function:supply-chain-inventory-optimizer",
        "arn:aws:lambda:*:*:function:supply-chain-logistics-optimizer",
        "arn:aws:lambda:*:*:function:supply-chain-supplier-analyzer"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetTables",
        "glue:GetPartitions"
      ],
      "Resource": "*"
    }
  ]
}
```

5. Name the role: `SageMaker-SupplyChainMVP-Role`

### Step 2: Create SageMaker Notebook Instance

1. Go to **SageMaker Console** → **Notebook instances** → **Create notebook instance**

2. Configure the instance:
   - **Name**: `supply-chain-mvp`
   - **Instance type**: `ml.t3.medium`
   - **Platform identifier**: `Amazon Linux 2, Jupyter Lab 3`
   - **IAM role**: Select the role created in Step 1
   - **Root access**: Enabled (needed for installing packages)

3. **Network** (Optional):
   - VPC: Select if Redshift is in a VPC
   - Subnet: Select appropriate subnet
   - Security group: Ensure outbound access to AWS services

4. **Git repositories** (Optional):
   - Add your application repository if using Git

5. Click **Create notebook instance**

6. Wait for the instance status to change to **InService** (~5 minutes)

### Step 3: Upload Application Code

**Option A: Upload Files Directly**

1. Click **Open JupyterLab** on the notebook instance

2. In JupyterLab, create a new folder: `supply-chain-mvp`

3. Upload all application files to this folder:
   - Use the upload button in JupyterLab
   - Or use SCP: `scp -r mvp/ ec2-user@<notebook-instance>:/home/ec2-user/SageMaker/supply-chain-mvp/`

**Option B: Clone from Git**

1. Open a terminal in JupyterLab

2. Clone your repository:
```bash
cd /home/ec2-user/SageMaker
git clone <your-repo-url> supply-chain-mvp
cd supply-chain-mvp
```

### Step 4: Run Setup Script

1. Open a terminal in JupyterLab

2. Navigate to the application directory:
```bash
cd /home/ec2-user/SageMaker/supply-chain-mvp
```

3. Make the setup script executable:
```bash
chmod +x infrastructure/sagemaker/setup_notebook.sh
```

4. Run the setup script:
```bash
./infrastructure/sagemaker/setup_notebook.sh
```

5. The script will:
   - Create a Python virtual environment
   - Install all dependencies
   - Create configuration files from templates
   - Set up directory structure
   - Create startup scripts

### Step 5: Configure the Application

1. Edit `config.yaml` with your AWS resource details:
```bash
nano config.yaml
```

Update the following sections:
```yaml
aws:
  region: us-east-1  # Your AWS region
  bedrock:
    model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
  redshift:
    workgroup_name: supply-chain-mvp  # Your Redshift workgroup name
    database: supply_chain_db
  glue:
    catalog_id: "123456789012"  # Your AWS account ID
    database: supply_chain_catalog
  lambda:
    inventory_function: supply-chain-inventory-optimizer
    logistics_function: supply-chain-logistics-optimizer
    supplier_function: supply-chain-supplier-analyzer
```

2. Create user accounts in `auth/users.json`:
```bash
python scripts/create_user.py
```

Follow the prompts to create users with appropriate personas.

### Step 6: Start the Application

**Manual Start:**
```bash
cd /home/ec2-user/SageMaker/supply-chain-mvp
./start_app.sh
```

**Or as a Service (Auto-start on boot):**
```bash
sudo systemctl enable supply-chain-mvp
sudo systemctl start supply-chain-mvp
```

**Check Status:**
```bash
sudo systemctl status supply-chain-mvp
```

### Step 7: Access the Application

The application runs on port 8501. Access it using the SageMaker proxy URL:

**URL Format:**
```
https://<notebook-instance-name>.notebook.<region>.sagemaker.aws/proxy/8501/
```

**Example:**
```
https://supply-chain-mvp.notebook.us-east-1.sagemaker.aws/proxy/8501/
```

**Alternative: Port Forwarding**

If the proxy doesn't work, use SSH port forwarding:

1. Get the notebook instance endpoint from SageMaker Console

2. Set up port forwarding:
```bash
ssh -i <your-key.pem> -L 8501:localhost:8501 ec2-user@<notebook-instance-endpoint>
```

3. Access the application at: `http://localhost:8501`

## Lifecycle Configuration (Auto-Start)

To automatically start the application when the notebook instance starts:

### Step 1: Create Lifecycle Configuration

1. Go to **SageMaker Console** → **Lifecycle configurations** → **Create configuration**

2. **Name**: `supply-chain-mvp-startup`

3. **Scripts**:
   - **Start notebook**: Copy the contents of `infrastructure/sagemaker/lifecycle_config.sh`

4. Click **Create configuration**

### Step 2: Attach to Notebook Instance

1. Stop the notebook instance

2. Click **Update settings**

3. Under **Lifecycle configuration**, select `supply-chain-mvp-startup`

4. Click **Update notebook instance**

5. Start the notebook instance

The application will now start automatically when the instance starts!

## Monitoring and Troubleshooting

### View Application Logs

```bash
# Streamlit logs
tail -f /home/ec2-user/SageMaker/supply-chain-mvp/logs/streamlit.log

# Application logs
tail -f /home/ec2-user/SageMaker/supply-chain-mvp/logs/app.log

# Service logs (if using systemd)
sudo journalctl -u supply-chain-mvp -f
```

### Check if Application is Running

```bash
# Check process
ps aux | grep streamlit

# Check port
netstat -tuln | grep 8501
```

### Restart Application

```bash
# If running manually
pkill -f "streamlit run app.py"
./start_app.sh

# If running as service
sudo systemctl restart supply-chain-mvp
```

### Common Issues

**Issue: Application won't start**
- Check logs: `tail -f logs/streamlit.log`
- Verify config.yaml is correct
- Ensure virtual environment is activated
- Check IAM role permissions

**Issue: Can't access via proxy URL**
- Verify notebook instance is running
- Check security group allows outbound traffic
- Try port forwarding instead

**Issue: AWS service access denied**
- Verify IAM role has correct permissions
- Check resource ARNs in IAM policy
- Ensure Bedrock model access is enabled in AWS Console

**Issue: Database connection fails**
- Verify Redshift workgroup name in config.yaml
- Check Redshift is in the same VPC as notebook (if using VPC)
- Verify IAM role has redshift-data permissions

## Cost Optimization

### Instance Scheduling

Stop the notebook instance when not in use to save costs:

**Manual:**
- Stop: SageMaker Console → Notebook instances → Stop
- Start: SageMaker Console → Notebook instances → Start

**Automated with Lambda:**

Create a Lambda function to start/stop on a schedule:

```python
import boto3

def lambda_handler(event, context):
    sagemaker = boto3.client('sagemaker')
    
    action = event.get('action', 'stop')
    instance_name = 'supply-chain-mvp'
    
    if action == 'start':
        sagemaker.start_notebook_instance(NotebookInstanceName=instance_name)
    elif action == 'stop':
        sagemaker.stop_notebook_instance(NotebookInstanceName=instance_name)
    
    return {'statusCode': 200, 'body': f'{action} completed'}
```

Schedule with EventBridge:
- Start: Monday-Friday at 8 AM
- Stop: Monday-Friday at 6 PM

**Cost Savings:**
- 24/7: ~$36/month
- 8 hours/day, 5 days/week: ~$8/month
- **Savings: ~$28/month (78%)**

### Right-Sizing

Monitor resource usage and adjust instance type:

- **Light usage** (1-2 users): ml.t3.medium ($0.05/hour)
- **Moderate usage** (3-5 users): ml.t3.large ($0.10/hour)
- **Heavy usage** (5+ users): ml.t3.xlarge ($0.20/hour)

## Upgrading and Maintenance

### Update Application Code

```bash
cd /home/ec2-user/SageMaker/supply-chain-mvp

# If using git
git pull

# Restart application
sudo systemctl restart supply-chain-mvp
```

### Update Dependencies

```bash
cd /home/ec2-user/SageMaker/supply-chain-mvp
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart supply-chain-mvp
```

### Backup Configuration

```bash
# Backup important files
tar -czf backup-$(date +%Y%m%d).tar.gz \
    config.yaml \
    auth/users.json \
    logs/

# Copy to S3
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

## Security Best Practices

1. **Use IAM Roles**: Never store AWS credentials in code or config files

2. **Restrict Network Access**: Use VPC and security groups to limit access

3. **Enable Encryption**: Use encrypted EBS volumes for notebook storage

4. **Regular Updates**: Keep Python packages and system packages updated

5. **Audit Logging**: Enable CloudTrail logging for SageMaker API calls

6. **Strong Passwords**: Enforce strong passwords in auth/users.json

7. **HTTPS Only**: Always access via HTTPS (SageMaker proxy provides this)

## Next Steps

After successful deployment:

1. **Test All Personas**: Verify each persona can query and use specialized agents

2. **Load Production Data**: Replace sample data with real data

3. **Monitor Costs**: Track daily costs using the cost dashboard

4. **Train Users**: Provide training on how to use the system

5. **Plan Migration**: When ready, migrate to production architecture (see main README.md)

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review main README.md for general troubleshooting
- Check AWS service status: https://status.aws.amazon.com/

## Additional Resources

- [SageMaker Notebook Instances Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html)
- [SageMaker Lifecycle Configurations](https://docs.aws.amazon.com/sagemaker/latest/dg/notebook-lifecycle-config.html)
- [Streamlit Documentation](https://docs.streamlit.io/)
