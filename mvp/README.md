# Supply Chain AI Assistant - MVP

Cost-optimized Minimum Viable Product (MVP) for the Supply Chain Agentic AI System.

## Overview

This MVP provides comprehensive supply chain AI capabilities for three personas:
- **Warehouse Manager**: Inventory management and optimization
- **Field Engineer**: Logistics and delivery optimization
- **Procurement Specialist**: Supplier analysis and cost optimization

### Key Features

- Natural language SQL queries with Bedrock Claude 3.5 Sonnet
- Specialized optimization agents (Inventory, Logistics, Supplier)
- Semantic data layer with AWS Glue Catalog integration
- Query result caching for fast responses
- Conversation memory for context-aware interactions
- Real-time cost tracking and monitoring
- Authentication and role-based access control

### Technology Stack

- **AI/ML**: Amazon Bedrock (Claude 3.5 Sonnet)
- **Database**: Amazon Redshift Serverless (8 RPUs)
- **Schema Metadata**: AWS Glue Data Catalog
- **Compute**: AWS Lambda (3 functions)
- **Application**: Python 3.11+ with Streamlit
- **Deployment**: Local, EC2, or SageMaker

## Project Structure

```
mvp/
├── agents/              # SQL and specialized agents
├── auth/                # Authentication and authorization
├── aws/                 # AWS service client wrappers
├── cache/               # Query result caching
├── cost/                # Cost tracking and monitoring
├── database/            # Database connection and queries
├── infrastructure/      # CDK infrastructure code
│   └── cdk/            # CDK stack definitions
├── lambda_functions/    # Lambda function handlers
│   ├── inventory_optimizer/
│   ├── logistics_optimizer/
│   ├── supplier_analyzer/
│   └── layer/          # Shared Lambda layer
├── memory/              # Conversation memory
├── orchestrator/        # Query orchestration and routing
├── scripts/             # Setup and utility scripts
├── semantic_layer/      # Business term mapping
├── tests/               # Test suite
├── tools/               # Python calculation tools
├── ui/                  # Streamlit UI components
├── utils/               # Utility functions
├── logs/                # Application logs
├── config.example.yaml  # Configuration template
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Prerequisites

### Software Requirements

- **Python**: 3.11 or higher
- **AWS CLI**: Version 2.x ([Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- **AWS CDK CLI**: `npm install -g aws-cdk` ([CDK Documentation](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html))
- **Git**: For cloning the repository (optional)

### AWS Account Requirements

Your AWS account must have:

1. **Bedrock Model Access**: Enable Claude 3.5 Sonnet in the Bedrock console
   - Go to AWS Console → Bedrock → Model access
   - Request access to Anthropic Claude 3.5 Sonnet
   - Wait for approval (usually instant)

2. **IAM Permissions** for:
   - Redshift Serverless (create workgroups, namespaces)
   - AWS Glue (create databases, tables)
   - AWS Lambda (create functions, layers)
   - Amazon Bedrock (invoke models)
   - IAM (create roles, policies)
   - CloudFormation (for CDK deployments)

3. **Service Quotas**:
   - Redshift Serverless: At least 8 RPUs available
   - Lambda: Concurrent executions quota
   - Bedrock: Token limits for Claude 3.5 Sonnet

### AWS Credentials

Configure AWS credentials using one of these methods:

**Option 1: AWS CLI Configuration**
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region (e.g., us-east-1), Output format (json)
```

**Option 2: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

**Option 3: IAM Role** (for EC2/SageMaker deployments)
- Attach an IAM role with required permissions to your instance

## Quick Start

Follow these steps to get the application running locally:

### 1. Clone or Download the Repository

```bash
# If using git
git clone <repository-url>
cd supply-chain-mvp/mvp

# Or download and extract the ZIP file
cd mvp
```

### 2. Set Up Python Environment

**Windows:**
```cmd
# Run the setup script
scripts\setup_venv.bat

# Activate the virtual environment
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
# Make the script executable
chmod +x scripts/setup_venv.sh

# Run the setup script
./scripts/setup_venv.sh

# Activate the virtual environment
source venv/bin/activate
```

The setup script will:
- Create a Python virtual environment
- Install all required dependencies from requirements.txt
- Verify the installation

### 3. Configure AWS Credentials

**Option A: Using .env file (Recommended for local development)**

```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your AWS credentials
nano .env  # or use your preferred editor
```

Update these values in `.env`:
```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
```

**Option B: Using AWS CLI**

If you've already configured AWS CLI, the application will use those credentials automatically.

### 4. Deploy AWS Infrastructure

Deploy the required AWS resources using CDK:

```bash
cd infrastructure/cdk

# Windows
deploy.bat

# Linux/Mac
chmod +x deploy.sh
./deploy.sh
```

**What gets deployed:**
- Redshift Serverless workgroup (8 RPUs minimum)
- Redshift Serverless namespace
- AWS Glue Data Catalog database
- 3 Lambda functions:
  - Inventory Optimizer
  - Logistics Optimizer
  - Supplier Analyzer
- Lambda Layer with shared dependencies
- IAM roles and policies for all services

**Deployment time**: ~10-15 minutes

**Important**: Note the CDK outputs - you'll need these values for configuration:
- RedshiftWorkgroupName
- GlueDatabaseName
- InventoryLambdaArn
- LogisticsLambdaArn
- SupplierLambdaArn

### 5. Configure the Application

```bash
# Return to mvp directory
cd ../..

# Copy configuration template
cp config.example.yaml config.yaml

# Edit config.yaml
nano config.yaml  # or use your preferred editor
```

Update these sections in `config.yaml`:

```yaml
aws:
  region: us-east-1  # Your AWS region
  bedrock:
    model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
  redshift:
    workgroup_name: supply-chain-mvp-workgroup  # From CDK output
    database: supply_chain_db
  glue:
    catalog_id: "123456789012"  # Your AWS account ID
    database: supply_chain_catalog  # From CDK output
  lambda:
    inventory_function: supply-chain-inventory-optimizer  # From CDK output
    logistics_function: supply-chain-logistics-optimizer  # From CDK output
    supplier_function: supply-chain-supplier-analyzer  # From CDK output
```

### 6. Set Up Database Schema and Sample Data

```bash
# Create Glue Catalog tables
python scripts/setup_glue_catalog.py

# Generate and load sample data into Redshift
python scripts/generate_sample_data.py
```

**What gets created:**
- 6 tables in Glue Catalog (product, warehouse_product, sales_order_header, sales_order_line, purchase_order_header, purchase_order_line)
- Sample data:
  - 100+ products
  - 3 warehouses
  - 90 days of sales orders
  - 90 days of purchase orders

**Data generation time**: ~5 minutes

### 7. Create User Accounts

```bash
# Create your first user
python scripts/create_user.py
```

Follow the prompts:
- Enter username
- Enter password (minimum 8 characters)
- Select personas (Warehouse Manager, Field Engineer, Procurement Specialist)

You can create multiple users with different persona assignments.

### 8. Run the Application

```bash
# Make sure you're in the mvp directory with venv activated
streamlit run app.py
```

The application will start and display:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.x:8501
```

### 9. Access and Login

1. Open your browser and go to `http://localhost:8501`
2. You'll see the login page
3. Enter the username and password you created in step 7
4. Select your persona
5. Start querying!

## First Steps After Login

### Test the System

Try these example queries to verify everything is working:

**Warehouse Manager:**
```
Show me all products with low stock levels
Calculate reorder point for product P001 in warehouse WH001
```

**Field Engineer:**
```
Show me orders scheduled for delivery today
Which orders are delayed?
```

**Procurement Specialist:**
```
Show me all suppliers
Analyze supplier performance for the last 30 days
```

### Explore the Features

- **Query Input**: Type natural language questions in the main text area
- **Results Display**: View results in tables and charts
- **Conversation History**: See past queries in the left sidebar
- **Cost Tracking**: Monitor costs in the left sidebar
- **Cache Statistics**: View cache hit rate and performance

## Deployment Options

### Option 1: Local Development (Recommended for Getting Started)

**Use Case**: Development, testing, demos, single-user access

**Requirements**:
- Local machine with Python 3.11+
- AWS credentials configured
- Internet connection for AWS API calls

**Pros**:
- No deployment costs (only AWS service costs)
- Fast iteration and debugging
- Easy to set up and tear down
- Full control over environment

**Cons**:
- Single user only
- Not accessible remotely
- No high availability
- Must keep computer running

**Setup**: Follow the Quick Start guide above

**Cost**: $0 for compute (only AWS service costs ~$150-200/month)

---

### Option 2: Amazon SageMaker Notebook Instance (Recommended for Teams)

**Use Case**: Team collaboration, shared development environment, production MVP

**Requirements**:
- AWS account with SageMaker permissions
- Application code uploaded or in Git repository

**Instance Types**:
- **ml.t3.medium**: 2 vCPU, 4 GB RAM - $0.05/hour (~$36/month 24/7)
- **ml.t3.large**: 2 vCPU, 8 GB RAM - $0.10/hour (~$72/month 24/7)
- **ml.t3.xlarge**: 4 vCPU, 16 GB RAM - $0.20/hour (~$144/month 24/7)

**Pros**:
- Integrated AWS authentication (IAM roles)
- Team collaboration support
- Managed infrastructure
- Easy scaling
- Built-in Jupyter for data exploration
- Can schedule start/stop to save costs

**Cons**:
- Additional compute cost
- Requires SageMaker knowledge
- More complex setup than local

**Setup**: See detailed guide in `infrastructure/sagemaker/README.md`

**Quick Setup**:
1. Create SageMaker Notebook Instance (ml.t3.medium)
2. Upload application code or clone from Git
3. Run `infrastructure/sagemaker/setup_notebook.sh`
4. Configure `config.yaml` and `auth/users.json`
5. Start application: `./start_app.sh`
6. Access via SageMaker proxy URL

**Cost Optimization**:
- **24/7 operation**: ~$36/month
- **8 hours/day, 5 days/week**: ~$8/month (use Lambda to auto-start/stop)
- **Savings**: Up to 78% with scheduled operation

**Access URL Format**:
```
https://<notebook-instance-name>.notebook.<region>.sagemaker.aws/proxy/8501/
```

---

### Option 3: EC2 Instance (For Production with Full Control)

**Use Case**: Production deployment, custom domain, full infrastructure control

**Requirements**:
- AWS account with EC2 permissions
- Domain name (optional, for HTTPS)
- SSL certificate (optional, for HTTPS)

**Instance Types**:
- **t3.small**: 2 vCPU, 2 GB RAM - $0.021/hour (~$15/month)
- **t3.medium**: 2 vCPU, 4 GB RAM - $0.042/hour (~$30/month)
- **t3.large**: 2 vCPU, 8 GB RAM - $0.083/hour (~$60/month)

**Pros**:
- Full control over environment
- Can use custom domain
- Lower cost than SageMaker for 24/7 operation
- Easy to backup and restore
- Can configure HTTPS with Let's Encrypt

**Cons**:
- Manual infrastructure management
- Need to handle security updates
- No built-in authentication (must implement)
- Requires more DevOps knowledge

**Setup Steps**:

1. **Launch EC2 Instance**:
   - AMI: Amazon Linux 2 or Ubuntu 22.04
   - Instance type: t3.small (minimum)
   - Security group: Allow inbound on port 80 (HTTP) and 443 (HTTPS)
   - Attach IAM role with required permissions

2. **Install Dependencies**:
```bash
# Connect to instance
ssh -i your-key.pem ec2-user@<instance-ip>

# Update system
sudo yum update -y  # Amazon Linux
# or
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python 3.11
sudo yum install python3.11 -y  # Amazon Linux
# or
sudo apt install python3.11 python3.11-venv -y  # Ubuntu

# Install git
sudo yum install git -y  # Amazon Linux
# or
sudo apt install git -y  # Ubuntu
```

3. **Deploy Application**:
```bash
# Clone repository
cd /home/ec2-user
git clone <your-repo-url> supply-chain-mvp
cd supply-chain-mvp/mvp

# Set up virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure application
cp config.example.yaml config.yaml
nano config.yaml  # Update with your settings

# Create users
python scripts/create_user.py
```

4. **Set Up as System Service**:
```bash
# Create systemd service file
sudo nano /etc/systemd/system/supply-chain-mvp.service
```

Add this content:
```ini
[Unit]
Description=Supply Chain AI Assistant
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/supply-chain-mvp/mvp
ExecStart=/home/ec2-user/supply-chain-mvp/mvp/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable supply-chain-mvp
sudo systemctl start supply-chain-mvp
sudo systemctl status supply-chain-mvp
```

5. **Configure Nginx as Reverse Proxy** (Optional, for HTTPS):
```bash
# Install nginx
sudo yum install nginx -y  # Amazon Linux
# or
sudo apt install nginx -y  # Ubuntu

# Configure nginx
sudo nano /etc/nginx/conf.d/supply-chain.conf
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Start nginx:
```bash
sudo systemctl enable nginx
sudo systemctl start nginx
```

6. **Set Up SSL with Let's Encrypt** (Optional):
```bash
# Install certbot
sudo yum install certbot python3-certbot-nginx -y  # Amazon Linux
# or
sudo apt install certbot python3-certbot-nginx -y  # Ubuntu

# Get certificate
sudo certbot --nginx -d your-domain.com
```

**Cost**: ~$15-60/month depending on instance type

---

### Deployment Comparison

| Feature | Local | SageMaker | EC2 |
|---------|-------|-----------|-----|
| **Setup Complexity** | Easy | Medium | Hard |
| **Cost (Compute)** | $0 | $8-36/month | $15-60/month |
| **Multi-User** | No | Yes | Yes |
| **Remote Access** | No | Yes | Yes |
| **Auto-Scaling** | No | Manual | Manual |
| **Managed** | No | Yes | No |
| **Custom Domain** | No | No | Yes |
| **HTTPS** | No | Yes | Yes (with setup) |
| **Best For** | Development | Team MVP | Production |

### Recommended Path

1. **Start**: Local development for initial testing
2. **MVP**: SageMaker Notebook for team collaboration
3. **Production**: EC2 with nginx or migrate to full production architecture (ECS Fargate + ALB)

## Cost Estimate

### AWS Services (Monthly Costs)

#### Core Services (Required)

| Service | Configuration | Usage Pattern | Monthly Cost |
|---------|--------------|---------------|--------------|
| **Redshift Serverless** | 8 RPUs (minimum) | 24/7 operation | ~$130 |
| **AWS Lambda** | 3 functions, 512MB each | 1000 invocations/day | ~$5 |
| **AWS Glue Catalog** | 6 tables | Metadata storage | ~$1 |
| **Amazon Bedrock** | Claude 3.5 Sonnet | 100-200 queries/day | ~$10-50 |

**Total Core AWS Services**: ~$146-186/month

#### Compute Options (Choose One)

| Option | Configuration | Usage Pattern | Monthly Cost |
|--------|--------------|---------------|--------------|
| **Local** | Your computer | Development only | $0 |
| **SageMaker** | ml.t3.medium | 24/7 | ~$36 |
| **SageMaker** | ml.t3.medium | 8 hrs/day, 5 days/week | ~$8 |
| **EC2** | t3.small | 24/7 | ~$15 |
| **EC2** | t3.medium | 24/7 | ~$30 |

### Total Monthly Cost Scenarios

| Scenario | Configuration | Monthly Cost |
|----------|--------------|--------------|
| **Development** | Local + AWS services | ~$146-186 |
| **Team MVP (Part-time)** | SageMaker (scheduled) + AWS | ~$154-194 |
| **Team MVP (24/7)** | SageMaker (24/7) + AWS | ~$182-222 |
| **Production (Small)** | EC2 t3.small + AWS | ~$161-201 |
| **Production (Medium)** | EC2 t3.medium + AWS | ~$176-216 |

### Cost Breakdown by Service

#### Redshift Serverless: ~$130/month

- **Pricing**: $0.36 per RPU-hour
- **Configuration**: 8 RPUs (minimum)
- **Calculation**: 8 RPUs × $0.36 × 24 hours × 30 days = ~$2,073.60/month

**Wait, that seems high!** 

Actually, Redshift Serverless charges only when actively processing queries. For moderate usage (100-200 queries/day, ~1-2 hours of active processing):
- **Active time**: ~2 hours/day
- **Monthly cost**: 8 RPUs × $0.36 × 2 hours × 30 days = ~$173/month

For light usage (50 queries/day, ~30 minutes active):
- **Active time**: 0.5 hours/day  
- **Monthly cost**: 8 RPUs × $0.36 × 0.5 hours × 30 days = ~$43/month

**Estimated for MVP**: ~$100-150/month depending on query volume

#### Amazon Bedrock: ~$10-50/month

- **Input tokens**: $0.003 per 1,000 tokens
- **Output tokens**: $0.015 per 1,000 tokens

**Example calculation** (100 queries/day):
- Average input: 2,000 tokens/query
- Average output: 500 tokens/query
- Daily cost: (100 × 2,000 × $0.003/1000) + (100 × 500 × $0.015/1000) = $0.60 + $0.75 = $1.35/day
- **Monthly cost**: $1.35 × 30 = ~$40/month

**Range**: $10-50/month depending on query complexity and volume

#### AWS Lambda: ~$5/month

- **Pricing**: $0.0000166667 per GB-second
- **Configuration**: 512MB memory, ~1 second execution

**Example calculation** (1000 invocations/day):
- Per invocation: 0.5 GB × 1 second × $0.0000166667 = $0.0000083
- Daily cost: 1000 × $0.0000083 = $0.0083
- **Monthly cost**: $0.0083 × 30 = ~$0.25/month

Plus free tier: 1M requests/month, 400,000 GB-seconds/month

**Estimated**: ~$5/month (well within free tier for MVP usage)

#### AWS Glue Catalog: ~$1/month

- **Pricing**: $1 per 100,000 requests
- **Usage**: Metadata lookups for schema information

**Estimated**: <$1/month (minimal usage)

### Cost Optimization Tips

#### 1. Redshift Serverless Optimization

- **Use query caching**: Reduces redundant queries (cache hit rate target: 40-50%)
- **Optimize queries**: Use WHERE clauses, avoid SELECT *
- **Schedule data loads**: Load data during off-peak hours
- **Monitor usage**: Use CloudWatch to track RPU consumption

**Potential savings**: 30-40% reduction in Redshift costs

#### 2. Bedrock Token Optimization

- **Optimize prompts**: Remove unnecessary context
- **Use conversation memory**: Avoid repeating information
- **Cache tool definitions**: Don't send tool schemas every time
- **Limit output tokens**: Set max_tokens appropriately

**Potential savings**: 20-30% reduction in Bedrock costs

#### 3. Compute Cost Optimization

**SageMaker Scheduling**:
- Use Lambda to start/stop notebook instance on schedule
- Example: 8 AM - 6 PM, Monday-Friday
- **Savings**: 78% ($36/month → $8/month)

**EC2 Reserved Instances**:
- Commit to 1-year term for 40% discount
- t3.small: $15/month → $9/month
- **Savings**: 40%

#### 4. Overall Cost Reduction Strategies

1. **Start small**: Begin with local development ($0 compute)
2. **Use scheduled SageMaker**: Only run during business hours
3. **Monitor and optimize**: Use cost dashboard to track spending
4. **Set up billing alerts**: Get notified when costs exceed thresholds
5. **Clean up unused resources**: Delete test data, old Lambda versions

### Cost Monitoring

The application includes built-in cost tracking:

- **Per-query cost**: Displayed after each query
- **Daily running total**: Shown in sidebar
- **Estimated monthly cost**: Based on daily average
- **Cost breakdown**: By service (Bedrock, Redshift, Lambda)
- **Cost logs**: Written to `logs/cost_tracking.log`

### Setting Up Billing Alerts

1. Go to **AWS Billing Console** → **Budgets**
2. Create a new budget:
   - **Budget type**: Cost budget
   - **Amount**: $200/month (adjust as needed)
   - **Alerts**: 
     - 80% threshold ($160)
     - 100% threshold ($200)
     - 120% threshold ($240)
3. Add email notifications

### Comparing to Production Architecture

| Component | MVP | Production | Savings |
|-----------|-----|------------|---------|
| **Database** | Redshift Serverless | Athena | Similar |
| **Compute** | Single instance | ECS Fargate + ALB | -$100/month |
| **Caching** | In-memory | ElastiCache | -$50/month |
| **Session State** | Local file | DynamoDB | -$25/month |
| **API Layer** | Direct | API Gateway | -$30/month |
| **Auth** | Local file | Cognito | -$0-50/month |
| **Total** | ~$150-220/month | ~$350-500/month | **~$200/month savings** |

The MVP architecture provides **40-60% cost savings** compared to full production architecture while maintaining all core functionality.

## Usage Examples

### Warehouse Manager Queries

The Warehouse Manager persona focuses on inventory management and optimization.

#### Basic Inventory Queries

```
"Show me products with low stock levels"
"List all products in warehouse WH001"
"Which products have stock below minimum levels?"
"Show me inventory levels for product group Electronics"
```

#### Reorder Point Calculations

```
"Calculate reorder points for warehouse WH001"
"What's the reorder point for product P12345?"
"Calculate safety stock for all products in warehouse WH002"
```

#### Demand Forecasting

```
"Forecast demand for product P12345 for next 30 days"
"Show me demand trends for Electronics products"
"Which products have increasing demand?"
```

#### Stockout Risk Analysis

```
"Which products are at risk of stockout?"
"Identify products that will run out in the next 7 days"
"Show me stockout risk for warehouse WH001"
```

#### Inventory Optimization

```
"Optimize inventory levels for warehouse WH001"
"Which products should I reorder today?"
"Calculate optimal order quantities for low stock items"
```

---

### Field Engineer Queries

The Field Engineer persona focuses on logistics, delivery, and order fulfillment.

#### Order Status Queries

```
"Show orders for delivery today"
"List all pending orders"
"Which orders are in transit?"
"Show me orders for customer C12345"
```

#### Delivery Optimization

```
"Optimize delivery route for orders in downtown area"
"Group orders by delivery area"
"Which orders can be delivered together?"
```

#### Delayed Orders

```
"Which orders are delayed?"
"Show me overdue deliveries"
"List orders past their delivery date"
"Identify orders at risk of delay"
```

#### Fulfillment Tracking

```
"Check fulfillment status for order SO-2024-001"
"Show me partially fulfilled orders"
"Which orders are fully fulfilled?"
"List unfulfilled orders from last week"
```

#### Warehouse Capacity

```
"Calculate warehouse capacity for WH001"
"Show me warehouse utilization"
"Which warehouse has the most available space?"
```

---

### Procurement Specialist Queries

The Procurement Specialist persona focuses on supplier management and cost optimization.

#### Supplier Analysis

```
"Analyze supplier performance for last 90 days"
"Show me all suppliers"
"Which suppliers have the best on-time delivery rate?"
"List suppliers for product group Electronics"
```

#### Cost Comparison

```
"Compare costs between suppliers for product group Electronics"
"Which supplier offers the best price for product P12345?"
"Show me cost variance by supplier"
```

#### Cost Savings

```
"Identify cost savings opportunities"
"Which suppliers have the highest cost variance?"
"Show me potential savings from supplier consolidation"
```

#### Purchase Order Trends

```
"Show purchase order trends by month"
"Analyze purchase patterns for last quarter"
"Which products have the highest purchase volume?"
"Show me purchase orders by supplier"
```

#### Supplier Performance Metrics

```
"Calculate supplier score for SUP001"
"Show me supplier fill rates"
"Which suppliers have quality issues?"
"Analyze supplier lead times"
```

---

### Advanced Queries (Hybrid)

These queries combine SQL data retrieval with specialized agent calculations:

#### Warehouse Manager Advanced

```
"Show me low stock products and calculate their reorder points"
"Identify stockout risks and forecast demand for next 30 days"
"List products below minimum stock and optimize reorder quantities"
```

#### Field Engineer Advanced

```
"Show me today's orders and optimize the delivery route"
"List delayed orders and calculate warehouse capacity impact"
"Identify orders for delivery and group by area"
```

#### Procurement Specialist Advanced

```
"Show me all suppliers and analyze their performance"
"List purchase orders from last month and identify cost savings"
"Compare supplier costs and calculate potential savings"
```

---

### Follow-Up Questions

The system maintains conversation context, so you can ask follow-up questions:

**Initial Query:**
```
"Show me products with low stock in warehouse WH001"
```

**Follow-Up Questions:**
```
"Calculate reorder points for these products"
"Which of these have the highest demand?"
"Show me suppliers for these products"
"What's the total cost to restock these items?"
```

---

### Tips for Effective Queries

1. **Be specific**: Include warehouse codes, product codes, or date ranges
   - Good: "Show me low stock products in warehouse WH001"
   - Better: "Show me products below 50 units in warehouse WH001"

2. **Use business terms**: The semantic layer understands common terms
   - "low stock", "overdue orders", "top suppliers"
   - "stockout risk", "delayed shipments", "cost variance"

3. **Combine queries**: Ask for multiple things in one query
   - "Show me low stock products and their suppliers"
   - "List delayed orders and calculate delivery route"

4. **Use follow-ups**: Build on previous queries
   - First: "Show me all suppliers"
   - Then: "Analyze performance for the top 3"

5. **Specify time ranges**: Include date ranges for trends
   - "last 30 days", "this month", "last quarter"
   - "between January 1 and March 31"

6. **Request calculations**: Ask for specific metrics
   - "calculate reorder point"
   - "forecast demand"
   - "optimize route"

---

### Query Response Time

Expected response times:

- **Simple SQL queries**: 1-3 seconds
- **Complex SQL queries**: 3-5 seconds
- **Specialized agent calls**: 5-10 seconds
- **Hybrid queries**: 8-15 seconds
- **Cached queries**: <1 second

The system caches identical queries for 5 minutes (dashboard queries for 15 minutes) to improve performance.

## Configuration

See `config.example.yaml` for all configuration options.

Key settings:
- **Bedrock model**: Claude 3.5 Sonnet (default)
- **Cache TTL**: 5 minutes (default), 15 minutes (dashboard)
- **Conversation history**: Last 10 interactions
- **Session timeout**: 1 hour

## Authentication

Default users are stored in `config/users.json`. To create users:

```bash
python scripts/create_user.py
```

Users can be assigned to one or more personas.

## Monitoring

### Cost Tracking

Real-time cost tracking is displayed in the UI:
- Per-query cost
- Daily running total
- Estimated monthly cost
- Cost breakdown by service

Costs are logged to `logs/cost_tracking.log`.

### Application Logs

Application logs are written to `logs/app.log` with rotation (10MB max, 5 backups).

## Troubleshooting

### Common Issues and Solutions

#### 1. Application Won't Start

**Symptom**: Error when running `streamlit run app.py`

**Possible Causes and Solutions**:

**A. Missing Dependencies**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Verify installation
pip list | grep streamlit
pip list | grep boto3
```

**B. Python Version Mismatch**
```bash
# Check Python version (must be 3.11+)
python --version

# If wrong version, recreate virtual environment
deactivate
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows
pip install -r requirements.txt
```

**C. Port Already in Use**
```bash
# Check if port 8501 is in use
netstat -tuln | grep 8501  # Linux/Mac
netstat -ano | findstr 8501  # Windows

# Kill the process or use a different port
streamlit run app.py --server.port 8502
```

**D. Configuration File Missing**
```bash
# Verify config.yaml exists
ls -la config.yaml

# If missing, copy from template
cp config.example.yaml config.yaml
nano config.yaml  # Update with your settings
```

---

#### 2. Redshift Connection Issues

**Symptom**: "Unable to connect to Redshift" or "Redshift query failed"

**Possible Causes and Solutions**:

**A. Incorrect Workgroup Name**
```bash
# Verify workgroup name in config.yaml
cat config.yaml | grep workgroup_name

# List available workgroups
aws redshift-serverless list-workgroups --region us-east-1

# Update config.yaml with correct name
```

**B. IAM Permissions Missing**
```bash
# Test Redshift Data API access
aws redshift-data execute-statement \
    --workgroup-name supply-chain-mvp-workgroup \
    --database supply_chain_db \
    --sql "SELECT 1" \
    --region us-east-1

# If error, check IAM permissions:
# - redshift-data:ExecuteStatement
# - redshift-data:DescribeStatement
# - redshift-data:GetStatementResult
```

**C. Redshift Not Running**
```bash
# Check workgroup status
aws redshift-serverless get-workgroup \
    --workgroup-name supply-chain-mvp-workgroup \
    --region us-east-1

# Status should be "AVAILABLE"
# If not, wait a few minutes or restart workgroup
```

**D. Network/VPC Issues**
- If Redshift is in a VPC, ensure your application can reach it
- Check security group rules allow inbound traffic
- Verify VPC endpoints are configured correctly

---

#### 3. Bedrock Access Denied

**Symptom**: "Access denied" or "Model not found" when querying

**Possible Causes and Solutions**:

**A. Model Access Not Enabled**
1. Go to AWS Console → Bedrock → Model access
2. Click "Manage model access"
3. Enable "Anthropic Claude 3.5 Sonnet"
4. Wait for approval (usually instant)

**B. IAM Permissions Missing**
```bash
# Test Bedrock access
aws bedrock-runtime invoke-model \
    --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
    --body '{"anthropic_version":"bedrock-2023-05-31","messages":[{"role":"user","content":"Hello"}],"max_tokens":100}' \
    --region us-east-1 \
    output.json

# If error, add IAM permission:
# - bedrock:InvokeModel
# - bedrock:InvokeModelWithResponseStream
```

**C. Wrong Region**
```bash
# Bedrock is only available in certain regions
# Supported: us-east-1, us-west-2, eu-west-1, ap-southeast-1

# Update config.yaml with supported region
aws:
  region: us-east-1  # Change to supported region
```

**D. Model ID Incorrect**
```bash
# Verify model ID in config.yaml
cat config.yaml | grep model_id

# Should be: anthropic.claude-3-5-sonnet-20241022-v2:0
# Update if different
```

---

#### 4. Lambda Invocation Errors

**Symptom**: "Lambda function not found" or "Invocation failed"

**Possible Causes and Solutions**:

**A. Function Name Incorrect**
```bash
# List Lambda functions
aws lambda list-functions --region us-east-1 | grep supply-chain

# Update config.yaml with correct function names
aws:
  lambda:
    inventory_function: supply-chain-inventory-optimizer
    logistics_function: supply-chain-logistics-optimizer
    supplier_function: supply-chain-supplier-analyzer
```

**B. IAM Permissions Missing**
```bash
# Test Lambda invocation
aws lambda invoke \
    --function-name supply-chain-inventory-optimizer \
    --payload '{"action":"test"}' \
    --region us-east-1 \
    response.json

# If error, add IAM permission:
# - lambda:InvokeFunction
```

**C. Lambda Function Not Deployed**
```bash
# Check if Lambda functions exist
aws lambda get-function \
    --function-name supply-chain-inventory-optimizer \
    --region us-east-1

# If not found, deploy Lambda functions
cd infrastructure/cdk
./deploy.sh  # or deploy.bat on Windows
```

**D. Lambda Execution Errors**
```bash
# Check Lambda logs in CloudWatch
aws logs tail /aws/lambda/supply-chain-inventory-optimizer --follow

# Common issues:
# - Missing dependencies in Lambda layer
# - Timeout (increase timeout in CDK stack)
# - Memory limit (increase memory in CDK stack)
```

---

#### 5. Authentication Issues

**Symptom**: "Invalid credentials" or "User not found"

**Possible Causes and Solutions**:

**A. Users File Missing**
```bash
# Check if users.json exists
ls -la auth/users.json

# If missing, create from template
cp auth/users.json.example auth/users.json

# Create a user
python scripts/create_user.py
```

**B. Incorrect Password**
```bash
# Reset user password
python scripts/create_user.py

# Enter existing username to update password
```

**C. Users File Corrupted**
```bash
# Validate JSON syntax
python -m json.tool auth/users.json

# If invalid, restore from backup or recreate
cp auth/users.json.example auth/users.json
python scripts/create_user.py
```

**D. Session Expired**
- Sessions expire after 1 hour of inactivity
- Simply log in again
- To change timeout, update config.yaml:
```yaml
app:
  session_timeout: 3600  # seconds (1 hour)
```

---

#### 6. Glue Catalog Issues

**Symptom**: "Table not found" or "Database not found"

**Possible Causes and Solutions**:

**A. Catalog Not Set Up**
```bash
# Run Glue catalog setup
python scripts/setup_glue_catalog.py

# Verify tables created
aws glue get-tables \
    --database-name supply_chain_catalog \
    --region us-east-1
```

**B. Database Name Incorrect**
```bash
# List Glue databases
aws glue get-databases --region us-east-1

# Update config.yaml with correct database name
aws:
  glue:
    database: supply_chain_catalog  # Update if different
```

**C. IAM Permissions Missing**
```bash
# Test Glue access
aws glue get-table \
    --database-name supply_chain_catalog \
    --name product \
    --region us-east-1

# If error, add IAM permissions:
# - glue:GetDatabase
# - glue:GetTable
# - glue:GetTables
```

---

#### 7. Sample Data Issues

**Symptom**: "No data returned" or "Table is empty"

**Possible Causes and Solutions**:

**A. Data Not Loaded**
```bash
# Generate and load sample data
python scripts/generate_sample_data.py

# This will:
# - Create sample data
# - Load into Redshift
# - Verify data loaded correctly
```

**B. Data Load Failed**
```bash
# Check script output for errors
python scripts/generate_sample_data.py 2>&1 | tee data_load.log

# Common issues:
# - Redshift connection failed
# - IAM permissions missing
# - Table schema mismatch
```

**C. Verify Data Loaded**
```bash
# Query Redshift to check data
aws redshift-data execute-statement \
    --workgroup-name supply-chain-mvp-workgroup \
    --database supply_chain_db \
    --sql "SELECT COUNT(*) FROM product" \
    --region us-east-1

# Get results
aws redshift-data get-statement-result \
    --id <statement-id-from-above> \
    --region us-east-1
```

---

#### 8. Performance Issues

**Symptom**: Slow query responses or timeouts

**Possible Causes and Solutions**:

**A. Redshift Query Optimization**
```bash
# Check query execution time in logs
tail -f logs/app.log | grep "Query execution time"

# Optimize queries:
# - Add WHERE clauses to filter data
# - Avoid SELECT * (specify columns)
# - Use LIMIT for large result sets
```

**B. Cache Not Working**
```bash
# Check cache statistics in UI sidebar
# Hit rate should be 30-50%

# If low hit rate:
# - Increase cache TTL in config.yaml
# - Increase cache size
# - Check if queries are identical (case-sensitive)
```

**C. Bedrock Token Limits**
```bash
# Check token usage in logs
tail -f logs/app.log | grep "tokens"

# Reduce token usage:
# - Shorten prompts
# - Limit conversation history
# - Reduce max_tokens in config.yaml
```

**D. Network Latency**
```bash
# Test network latency to AWS
ping bedrock.us-east-1.amazonaws.com

# If high latency:
# - Use AWS region closer to you
# - Check internet connection
# - Consider deploying on EC2/SageMaker in same region
```

---

#### 9. Cost Tracking Issues

**Symptom**: Costs not displayed or incorrect

**Possible Causes and Solutions**:

**A. Cost Tracking Disabled**
```bash
# Check config.yaml
cat config.yaml | grep -A 5 "cost:"

# Ensure enabled: true
cost:
  enabled: true
```

**B. Cost Log File Missing**
```bash
# Check if logs directory exists
mkdir -p logs

# Verify cost log file
ls -la logs/cost_tracking.log

# If missing, it will be created on first query
```

**C. Incorrect Cost Calculations**
- Cost calculations are estimates based on AWS pricing
- Actual costs may vary slightly
- Check AWS Billing Console for accurate costs

---

#### 10. UI Display Issues

**Symptom**: UI not rendering correctly or blank page

**Possible Causes and Solutions**:

**A. Browser Cache**
```bash
# Clear browser cache
# Chrome: Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
# Firefox: Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)

# Or use incognito/private mode
```

**B. Streamlit Version**
```bash
# Check Streamlit version
pip show streamlit

# Should be 1.28.0 or higher
# Upgrade if needed
pip install --upgrade streamlit
```

**C. Port Forwarding Issues** (SageMaker/EC2)
```bash
# Verify port forwarding is working
curl http://localhost:8501

# If using SageMaker proxy, check URL format:
# https://<instance-name>.notebook.<region>.sagemaker.aws/proxy/8501/
```

---

### Getting Help

If you're still experiencing issues:

1. **Check Logs**:
   ```bash
   # Application logs
   tail -f logs/app.log
   
   # Streamlit logs (if running as service)
   sudo journalctl -u supply-chain-mvp -f
   
   # Lambda logs
   aws logs tail /aws/lambda/supply-chain-inventory-optimizer --follow
   ```

2. **Enable Debug Logging**:
   ```yaml
   # In config.yaml
   logging:
     level: DEBUG  # Change from INFO to DEBUG
   ```

3. **Test AWS Services Individually**:
   ```bash
   # Test Bedrock
   python -c "import boto3; client = boto3.client('bedrock-runtime', region_name='us-east-1'); print('Bedrock OK')"
   
   # Test Redshift
   python -c "import boto3; client = boto3.client('redshift-data', region_name='us-east-1'); print('Redshift OK')"
   
   # Test Lambda
   python -c "import boto3; client = boto3.client('lambda', region_name='us-east-1'); print('Lambda OK')"
   ```

4. **Check AWS Service Status**:
   - Visit: https://status.aws.amazon.com/
   - Check status of Bedrock, Redshift, Lambda in your region

5. **Review Documentation**:
   - Main README.md (this file)
   - Component-specific READMEs in each directory
   - AWS service documentation

6. **Contact Support**:
   - Internal team support channel
   - AWS Support (for AWS service issues)

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
flake8 .
```

### Type Checking

```bash
mypy .
```

## Migration to Production

This MVP uses Redshift Serverless for cost optimization. To migrate to production:

1. Replace Redshift Serverless with AWS Athena
2. Update database client in `aws/redshift_client.py`
3. Modify SQL generation for Athena syntax
4. Deploy with API Gateway and DynamoDB for multi-user support

See migration documentation (to be created in task 17.1).

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review application logs in `logs/`
3. Check AWS CloudWatch logs for Lambda functions
4. Review CDK deployment outputs

## License

Internal use only.
