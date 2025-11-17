# Supply Chain Agentic AI Application

Production-scale multi-agent AI system for supply chain management built on AWS.

## 🚀 Quick Start

```bash
# Clone and setup
cd supply_chain_agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure AWS
aws configure

# Deploy infrastructure (automated)
bash deploy.sh --environment dev

# Run application
streamlit run app.py
```

Access at: http://localhost:8501

**New!** Automated deployment with validation, configuration management, and verification. See [Deployment Automation Guide](docs/DEPLOYMENT_AUTOMATION_GUIDE.md) for details.

## 📋 Overview

This system provides AI-powered assistance for three supply chain personas:

### 1. 👷 Warehouse Manager
- **SQL Agent**: Inventory and stock queries
- **Inventory Optimizer**: Forecasting, reorder points, stockout prevention

### 2. 🚚 Field Engineer  
- **SQL Agent**: Order and delivery queries
- **Logistics Agent**: Route optimization, fulfillment tracking

### 3. 💼 Procurement Specialist
- **SQL Agent**: Purchase order and supplier queries
- **Supplier Analyzer**: Performance analysis, cost optimization

## 🏗️ Architecture

```
User → Streamlit UI → Orchestrator → [SQL Agent | Specialist Agent]
                                           ↓              ↓
                                        Athena       Lambda Tools
                                           ↓              ↓
                                    Glue Data Catalog
```

### AWS Services
- **Amazon Bedrock**: Claude 3.5 Sonnet (agent orchestration)
- **AWS Athena**: SQL execution
- **AWS Lambda**: Tool execution (3 functions)
- **Amazon S3**: Data storage
- **AWS Glue**: Data catalog
- **Amazon DynamoDB**: Session state (2 tables)
- **Amazon API Gateway**: REST API
- **AWS Cognito**: Authentication
- **Amazon CloudWatch**: Monitoring

### Database Tables
- `product`: Product master data
- `warehouse_product`: Warehouse inventory
- `purchase_order_header` & `purchase_order_line`: Purchase orders
- `sales_order_header` & `sales_order_line`: Sales orders

## 💡 Example Queries

### Warehouse Manager
```
"Show me products below minimum stock in warehouse WH01"
"Calculate optimal reorder points for warehouse WH01"
"Forecast demand for product P12345 for next 30 days"
"Identify products at risk of stockout in next 7 days"
```

### Field Engineer
```
"Show me all orders for delivery today"
"Optimize delivery route for orders SO001, SO002, SO003"
"Check fulfillment status of order SO12345"
"Identify delayed orders in warehouse WH01"
```

### Procurement Specialist
```
"Analyze supplier performance for last 90 days"
"Compare costs across suppliers for product group PG01"
"Identify cost savings opportunities with 5%+ savings"
"Show purchase order trends for last 6 months"
```

## 📁 Project Structure

```
supply_chain_agent/
├── agents/                 # Agent implementations
├── lambda_functions/       # Lambda tool functions
├── cdk/                   # Infrastructure as code
├── examples/              # Usage examples
├── tests/                 # Unit tests
├── orchestrator.py        # Multi-agent orchestrator
├── config.py             # Configuration
├── app.py                # Streamlit UI
└── deploy.sh             # Deployment script
```

## 📚 Documentation

- **README.md** (this file): Quick start
- **DEPLOYMENT.md**: Detailed deployment guide
- **ARCHITECTURE.md**: Technical architecture
- **PROJECT_SUMMARY.md**: Complete project overview
- **docs/TAG_MANAGEMENT.md**: Tag management and validation guide
- **cdk/CONFIGURATION_GUIDE.md**: Configuration reference

## 🔧 Configuration

Edit `config.py`:
```python
ATHENA_DATABASE = "aws-gpl-cog-sc-db"
ATHENA_OUTPUT_LOCATION = "s3://your-bucket/"
BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
```

## 🧪 Testing

```bash
# Unit tests
python -m pytest tests/

# Example queries
python examples/warehouse_manager_examples.py
python examples/field_engineer_examples.py
python examples/procurement_specialist_examples.py
```

## 💰 Cost Estimate

Monthly cost for 1000 queries/day: **$240-500**
- Bedrock: $150-300
- Lambda: $20-50
- Athena: $50-100
- DynamoDB: $10-30
- Other: $10-20

## 🔒 Security

- Cognito authentication with MFA
- Persona-based table access control
- IAM role-based permissions
- Encryption at rest and in transit
- CloudTrail audit logging

## 📊 Monitoring

- CloudWatch Logs for all services
- Lambda metrics (invocations, errors, duration)
- Athena query performance
- DynamoDB capacity utilization
- API Gateway request metrics

## 🚀 Deployment

### Prerequisites
- AWS Account with Bedrock access
- AWS CLI configured
- Python 3.11+
- Node.js 18+ (for CDK)

### Automated Deployment (Recommended)

```bash
# Deploy to development environment
bash deploy.sh --environment dev

# Deploy to production with validation
bash scripts/validate-deployment.sh --environment prod
bash deploy.sh --environment prod
```

The automated deployment includes:
- ✅ Pre-deployment validation
- ✅ Configuration loading from YAML
- ✅ CDK bootstrap check
- ✅ Infrastructure deployment
- ✅ Post-deployment configuration
- ✅ Deployment verification

### Manual Deployment

```bash
# Step-by-step deployment
bash scripts/validate-deployment.sh --environment dev
bash scripts/load-config.sh --environment dev
bash scripts/bootstrap-cdk.sh --environment dev
cd cdk && cdk deploy && cd ..
bash scripts/post-deploy.sh --environment dev
bash scripts/verify-deployment.sh --environment dev
```

### Cleanup and Rollback

```bash
# Rollback to previous version
bash scripts/rollback.sh --environment prod

# Cleanup environment (preserve data)
bash scripts/cleanup.sh --environment dev

# Complete removal
bash scripts/cleanup.sh --environment dev --force-delete
```

### Documentation
- [Deployment Automation Guide](docs/DEPLOYMENT_AUTOMATION_GUIDE.md) - Complete automation guide
- [Deployment Quick Reference](docs/DEPLOYMENT_QUICK_REFERENCE.md) - Common commands
- [Cleanup and Rollback Guide](docs/CLEANUP_ROLLBACK_GUIDE.md) - Cleanup and rollback operations
- [Cleanup Quick Reference](docs/CLEANUP_ROLLBACK_QUICK_REFERENCE.md) - Quick command reference
- [Configuration Reference](config/README.md) - Configuration parameters
- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment guide

## 🛠️ Troubleshooting

**Lambda timeout**: Increase timeout in `supply_chain_stack.py`
**Athena errors**: Check table schemas and S3 permissions
**Bedrock access denied**: Enable model access in Bedrock console
**Authentication issues**: Verify Cognito user pool configuration

## 📈 Performance

- Query latency: 2-5 seconds
- Tool execution: 3-10 seconds
- End-to-end: 5-15 seconds
- Throughput: 100 req/s (configurable)

## 🔄 Future Enhancements

- Real-time streaming with Kinesis
- Advanced ML forecasting models
- Mobile app for field engineers
- Voice interface with Amazon Lex
- Multi-region deployment
- ERP system integration

## 📝 License

See LICENSE file for details.

## 🤝 Contributing

See CONTRIBUTING.md for guidelines.

## 📧 Support

For issues and questions, please open a GitHub issue.
