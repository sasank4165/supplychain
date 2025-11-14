# Supply Chain Agentic AI - Architecture

## Overview

This is a production-scale multi-agent AI system for supply chain management, built on AWS services with Amazon Bedrock as the orchestration layer.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│                    (Streamlit Web App)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Multi-Agent Orchestrator                       │
│              (Intent Classification & Routing)                   │
└─────────────┬───────────────────────────────┬───────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────┐    ┌─────────────────────────────────┐
│      SQL Agent          │    │   Specialist Agents             │
│  (Natural Language      │    │  - Inventory Optimizer          │
│   to SQL Conversion)    │    │  - Logistics Optimizer          │
│                         │    │  - Supplier Analyzer            │
└──────────┬──────────────┘    └──────────┬──────────────────────┘
           │                              │
           ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────────────┐
│    AWS Athena           │    │    AWS Lambda Functions         │
│  (SQL Execution)        │    │  (Tool Execution)               │
└──────────┬──────────────┘    └──────────┬──────────────────────┘
           │                              │
           ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AWS Glue Data Catalog                          │
│              (Supply Chain Database Schema)                      │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Architecture

### 1. Multi-Agent Orchestrator

**Purpose**: Routes queries to appropriate agents based on user persona and intent

**Components**:
- Intent Classifier (using Bedrock Claude)
- Agent Router
- Session Manager

**Flow**:
1. Receives user query and persona
2. Classifies intent (sql_query, optimization, or both)
3. Routes to appropriate agent(s)
4. Aggregates responses
5. Returns unified result

### 2. SQL Agent (Per Persona)

**Purpose**: Convert natural language to SQL and execute queries

**Capabilities**:
- Natural language understanding
- SQL generation with schema awareness
- Query execution on Athena
- Result formatting

**Persona-Specific Access**:
- **Warehouse Manager**: product, warehouse_product, sales_order_*
- **Field Engineer**: product, warehouse_product, sales_order_*
- **Procurement Specialist**: product, purchase_order_*, warehouse_product

### 3. Specialist Agents

#### Inventory Optimizer Agent (Warehouse Manager)

**Tools**:
1. `calculate_reorder_points`: Optimal reorder point calculation
2. `forecast_demand`: Demand forecasting using historical data
3. `identify_stockout_risks`: Stockout risk identification
4. `optimize_stock_levels`: Stock level optimization

**Algorithms**:
- Moving average for demand forecasting
- Safety stock calculation (Z-score based)
- Economic Order Quantity (EOQ) principles

#### Logistics Agent (Field Engineer)

**Tools**:
1. `optimize_delivery_route`: Route optimization by delivery area
2. `check_order_fulfillment_status`: Detailed order status
3. `identify_delayed_orders`: Delayed order identification
4. `calculate_warehouse_capacity`: Capacity utilization

**Features**:
- Area-based route grouping
- Real-time fulfillment tracking
- Capacity monitoring

#### Supplier Analyzer Agent (Procurement Specialist)

**Tools**:
1. `analyze_supplier_performance`: Performance metrics (fill rate, on-time delivery)
2. `compare_supplier_costs`: Cost comparison across suppliers
3. `identify_cost_savings_opportunities`: Savings identification
4. `analyze_purchase_order_trends`: Trend analysis

**Metrics**:
- Fill rate
- Cost variance
- Order completion rate
- Trend analysis

## Data Model

### Tables

1. **product**: Product master data
   - Primary Key: product_code
   - Contains: descriptions, costs, supplier info

2. **warehouse_product**: Warehouse-specific inventory
   - Primary Key: (warehouse_code, product_code)
   - Contains: stock levels, min/max, lead times

3. **purchase_order_header**: PO headers
   - Primary Key: (purchase_order_prefix, purchase_order_number)
   - Contains: supplier, dates, status

4. **purchase_order_line**: PO line items
   - Primary Key: (purchase_order_prefix, purchase_order_number, purchase_order_line)
   - Contains: quantities, prices, receipt status

5. **sales_order_header**: Sales order headers
   - Primary Key: (sales_order_prefix, sales_order_number)
   - Contains: customer, delivery info, status

6. **sales_order_line**: Sales order line items
   - Primary Key: (sales_order_prefix, sales_order_number, sales_order_line)
   - Contains: quantities, fulfillment status

## AWS Services

### Core Services

1. **Amazon Bedrock**
   - Model: Claude 3.5 Sonnet
   - Purpose: Agent orchestration, NL understanding, tool calling
   - API: Converse API with tool use

2. **AWS Athena**
   - Purpose: SQL query execution
   - Database: Glue Data Catalog
   - Output: S3 bucket

3. **AWS Lambda**
   - 3 functions for tool execution
   - Runtime: Python 3.11
   - Timeout: 300s
   - Memory: 512MB

4. **Amazon S3**
   - Athena query results
   - Data storage
   - Lifecycle: 30-day retention

5. **AWS Glue Data Catalog**
   - Metadata management
   - Table schemas
   - Partitioning

6. **Amazon DynamoDB**
   - Session state storage
   - Agent memory
   - Billing: On-demand

### Supporting Services

7. **Amazon API Gateway**
   - REST API endpoints
   - Throttling: 100 req/s
   - CORS enabled

8. **AWS Cognito**
   - User authentication
   - User pools per persona
   - MFA support

9. **Amazon CloudWatch**
   - Logging
   - Monitoring
   - Alarms

10. **AWS IAM**
    - Role-based access control
    - Least privilege principle

## Security Architecture

### Authentication & Authorization

- **Cognito User Pools**: User authentication
- **IAM Roles**: Service-to-service authentication
- **API Gateway Authorizer**: API access control

### Data Protection

- **Encryption at Rest**: S3, DynamoDB, Athena results
- **Encryption in Transit**: TLS 1.2+
- **VPC**: Lambda functions in VPC (optional)

### Access Control

- **Persona-based access**: Table-level restrictions
- **IAM policies**: Least privilege
- **Resource policies**: S3, Lambda

## Scalability

### Horizontal Scaling

- **Lambda**: Auto-scales to 1000 concurrent executions
- **DynamoDB**: On-demand capacity
- **Athena**: Serverless, auto-scaling

### Performance Optimization

- **Athena**: Partitioning by date
- **Lambda**: Provisioned concurrency (optional)
- **API Gateway**: Caching
- **DynamoDB**: DAX for caching (optional)

## Monitoring & Observability

### Metrics

- Lambda invocations, duration, errors
- Athena query execution time
- DynamoDB read/write capacity
- API Gateway requests, latency

### Logging

- CloudWatch Logs for all services
- Structured logging in Lambda
- Query history in Athena

### Alarms

- Lambda errors > threshold
- API Gateway 5xx errors
- DynamoDB throttling
- Athena query failures

## Cost Optimization

### Strategies

1. **Athena**: Partition pruning, columnar formats (Parquet)
2. **Lambda**: Right-size memory, use ARM architecture
3. **DynamoDB**: On-demand for variable traffic
4. **S3**: Lifecycle policies, Intelligent-Tiering
5. **Bedrock**: Prompt optimization, caching

### Estimated Monthly Costs (1000 queries/day)

- Bedrock: $150-300 (token-based)
- Lambda: $20-50
- Athena: $50-100 (data scanned)
- DynamoDB: $10-30
- S3: $5-10
- API Gateway: $5-10
- **Total**: ~$240-500/month

## Disaster Recovery

### Backup Strategy

- **DynamoDB**: Point-in-time recovery enabled
- **S3**: Versioning enabled
- **Glue Catalog**: Backup via CloudFormation

### Recovery Objectives

- **RTO**: < 1 hour (redeploy via CDK)
- **RPO**: < 5 minutes (DynamoDB PITR)

## Future Enhancements

1. **Multi-region deployment** for high availability
2. **Real-time streaming** with Kinesis
3. **Advanced ML models** for forecasting
4. **Mobile app** for field engineers
5. **Integration** with ERP systems
6. **Voice interface** with Amazon Lex
7. **Automated alerts** via SNS/SES
8. **Advanced analytics** with QuickSight
