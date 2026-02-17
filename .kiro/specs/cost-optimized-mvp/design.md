# Design Document - Cost-Optimized Supply Chain MVP

## Overview

This design document describes the architecture and implementation approach for a cost-optimized MVP of the supply chain agentic AI system. The MVP supports all three personas (Warehouse Manager, Field Engineer, Procurement Specialist) with comprehensive functionality while minimizing AWS infrastructure costs.

### Key Design Principles

1. **Cost Optimization**: Use Redshift Serverless instead of Athena, minimal Lambda functions, no API Gateway or DynamoDB
2. **Modularity**: Design for easy migration to full production architecture
3. **Simplicity**: Streamlined orchestration without complex routing
4. **Performance**: Query caching and conversation memory for fast responses
5. **Observability**: Cost tracking and comprehensive logging

### Technology Stack

- **AI/ML**: Amazon Bedrock (Claude 3.5 Sonnet)
- **Database**: Amazon Redshift Serverless with AWS Glue Data Catalog
- **Compute**: AWS Lambda (3 functions for specialized agents)
- **Application**: Python 3.11+ with Streamlit
- **Deployment**: Local, EC2 instance, or Amazon SageMaker Studio/Notebook

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                          │
│  - Login/Auth  - Persona Selector  - Query Input            │
│  - Results Display  - Cost Tracker  - Conversation History  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator                               │
│  - Intent Classification  - Agent Routing                    │
│  - Session Management  - Cost Tracking                       │
└─────────┬───────────────────────────────┬───────────────────┘
          │                               │
          ▼                               ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│   SQL Agents (3)     │      │  Specialized Agents (3)      │
│  - Warehouse Mgr     │      │  - Inventory (Lambda)        │
│  - Field Engineer    │      │  - Logistics (Lambda)        │
│  - Procurement       │      │  - Supplier (Lambda)         │
└──────┬───────────────┘      └──────┬───────────────────────┘
       │                             │
       ▼                             ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│  Amazon Bedrock      │      │  Python Calculation Tools    │
│  (Claude 3.5)        │      │  - reorder_point             │
│  - Tool Calling      │      │  - safety_stock              │
│  - SQL Generation    │      │  - supplier_score            │
└──────┬───────────────┘      └──────┬───────────────────────┘
       │                             │
       ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Redshift Serverless + Glue Catalog             │
│  - 6 Tables  - Schema Metadata  - Query Execution           │
└─────────────────────────────────────────────────────────────┘
```


## Components and Interfaces

### 1. Authentication Module

**Purpose**: Handle user login and persona authorization

**Components**:
- `AuthManager`: Manages authentication and authorization
- `UserStore`: Stores user credentials and persona assignments (JSON file)
- `SessionManager`: Manages active user sessions

**Interface**:
```python
class AuthManager:
    def authenticate(username: str, password: str) -> Optional[User]
    def authorize_persona(user: User, persona: str) -> bool
    def get_authorized_personas(user: User) -> List[str]
    def logout(session_id: str) -> None
```

**Data Model**:
```json
{
  "users": [
    {
      "username": "john_doe",
      "password_hash": "bcrypt_hash",
      "personas": ["Warehouse Manager", "Field Engineer"],
      "active": true
    }
  ]
}
```

### 2. Orchestrator

**Purpose**: Route queries to appropriate agents based on persona and intent

**Components**:
- `QueryOrchestrator`: Main orchestration logic
- `IntentClassifier`: Determines if query needs SQL, specialized agent, or both
- `AgentRouter`: Routes to appropriate agent based on persona

**Interface**:
```python
class QueryOrchestrator:
    def process_query(
        query: str, 
        persona: str, 
        session_id: str
    ) -> QueryResponse
    
    def classify_intent(query: str, persona: str) -> Intent
    def route_to_agents(query: str, intent: Intent, persona: str) -> AgentResponse
```

**Intent Types**:
- `SQL_QUERY`: Data retrieval query
- `OPTIMIZATION`: Specialized agent task
- `HYBRID`: Requires both SQL and specialized agent


### 3. SQL Agents

**Purpose**: Convert natural language to SQL and execute queries

**Components**:
- `BaseSQLAgent`: Base class with common SQL functionality
- `WarehouseSQLAgent`: Warehouse Manager specific SQL agent
- `FieldEngineerSQLAgent`: Field Engineer specific SQL agent
- `ProcurementSQLAgent`: Procurement Specialist specific SQL agent

**Interface**:
```python
class BaseSQLAgent:
    def __init__(self, bedrock_client, redshift_client, semantic_layer):
        pass
    
    def process_query(query: str, context: ConversationContext) -> SQLResponse
    def generate_sql(query: str, context: ConversationContext) -> str
    def execute_sql(sql: str) -> QueryResult
    def format_results(result: QueryResult) -> FormattedResponse
```

**Persona-Specific Table Access**:
- **Warehouse Manager**: product, warehouse_product, sales_order_header, sales_order_line
- **Field Engineer**: product, warehouse_product, sales_order_header, sales_order_line
- **Procurement Specialist**: product, warehouse_product, purchase_order_header, purchase_order_line

**SQL Generation Flow**:
1. Load conversation context
2. Retrieve schema metadata from Glue Catalog
3. Apply semantic layer business terms
4. Generate SQL using Bedrock with tool calling
5. Validate SQL syntax
6. Execute against Redshift Serverless
7. Format and return results

### 4. Specialized Agents

**Purpose**: Provide domain-specific optimization and analysis

**Components**:
- `InventoryAgent`: Inventory optimization for Warehouse Managers
- `LogisticsAgent`: Delivery optimization for Field Engineers
- `SupplierAgent`: Supplier analysis for Procurement Specialists

**Interface**:
```python
class BaseSpecializedAgent:
    def __init__(self, bedrock_client, lambda_client, redshift_client):
        pass
    
    def process_request(request: str, context: ConversationContext) -> AgentResponse
    def invoke_tool(tool_name: str, parameters: dict) -> ToolResult
```

**Tools by Agent**:

**InventoryAgent Tools**:
- `calculate_reorder_point(product_code, warehouse_code)`: Calculate optimal reorder point
- `identify_low_stock(warehouse_code, threshold)`: Find products below threshold
- `forecast_demand(product_code, days)`: Forecast demand using historical data
- `identify_stockout_risk(warehouse_code, days)`: Identify products at risk

**LogisticsAgent Tools**:
- `optimize_delivery_route(order_ids, warehouse_code)`: Optimize delivery routes
- `check_fulfillment_status(order_id)`: Get detailed order status
- `identify_delayed_orders(warehouse_code, days)`: Find delayed orders
- `calculate_warehouse_capacity(warehouse_code)`: Calculate capacity utilization

**SupplierAgent Tools**:
- `analyze_supplier_performance(supplier_code, days)`: Analyze supplier metrics
- `compare_supplier_costs(product_group, suppliers)`: Compare costs
- `identify_cost_savings(threshold_percent)`: Find savings opportunities
- `analyze_purchase_trends(days, group_by)`: Analyze PO trends


### 5. Semantic Layer

**Purpose**: Map business terms to SQL patterns and provide schema context

**Components**:
- `SemanticLayer`: Main semantic layer implementation
- `BusinessMetrics`: Business metric definitions
- `SchemaProvider`: Glue Catalog schema access

**Interface**:
```python
class SemanticLayer:
    def __init__(self, glue_client, persona: str):
        pass
    
    def get_business_metrics() -> Dict[str, MetricDefinition]
    def get_table_schema(table_name: str) -> TableSchema
    def resolve_business_term(term: str) -> SQLPattern
    def enrich_query_context(query: str) -> EnrichedContext
```

**Business Metrics Example**:
```python
{
    "low_stock": {
        "description": "Products below minimum stock level",
        "sql_pattern": "current_stock < minimum_stock",
        "tables": ["warehouse_product"],
        "personas": ["Warehouse Manager"]
    },
    "overdue_orders": {
        "description": "Orders past delivery date",
        "sql_pattern": "delivery_date < CURRENT_DATE AND status != 'Delivered'",
        "tables": ["sales_order_header"],
        "personas": ["Field Engineer"]
    },
    "top_suppliers": {
        "description": "Suppliers with highest order volume",
        "sql_pattern": "GROUP BY supplier_code ORDER BY SUM(order_quantity) DESC",
        "tables": ["purchase_order_header", "purchase_order_line"],
        "personas": ["Procurement Specialist"]
    }
}
```

### 6. Query Cache

**Purpose**: Cache query results for fast repeated access

**Components**:
- `QueryCache`: In-memory cache with TTL
- `CacheKey`: Query fingerprinting
- `CacheStats`: Cache hit/miss statistics

**Interface**:
```python
class QueryCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        pass
    
    def get(cache_key: str) -> Optional[CachedResult]
    def set(cache_key: str, result: QueryResult, ttl: int) -> None
    def invalidate(pattern: str) -> int
    def get_stats() -> CacheStats
```

**Cache Strategy**:
- Cache key: Hash of (query_text, persona, parameters)
- Default TTL: 5 minutes
- Dashboard queries TTL: 15 minutes
- Max cache size: 1000 entries (LRU eviction)
- Cache warming: Pre-cache common queries on startup


### 7. Conversation Memory

**Purpose**: Maintain session context for follow-up queries

**Components**:
- `ConversationMemory`: Session-level conversation storage
- `ConversationContext`: Context object passed to agents

**Interface**:
```python
class ConversationMemory:
    def __init__(self, max_history: int = 10):
        pass
    
    def add_interaction(session_id: str, query: str, response: str) -> None
    def get_context(session_id: str) -> ConversationContext
    def clear_session(session_id: str) -> None
    def get_history(session_id: str) -> List[Interaction]
```

**Context Structure**:
```python
@dataclass
class ConversationContext:
    session_id: str
    persona: str
    history: List[Interaction]  # Last 10 interactions
    referenced_entities: Dict[str, Any]  # Products, orders, etc.
    last_query_time: datetime
```

**Context Usage**:
- SQL Agent uses context to resolve ambiguous references ("that product", "those orders")
- Specialized agents use context to maintain state across multi-turn interactions
- Context cleared on persona switch or explicit user request

### 8. Cost Tracker

**Purpose**: Track and display AWS costs per query and daily totals

**Components**:
- `CostTracker`: Cost calculation and tracking
- `CostLogger`: Log costs to file for analysis

**Interface**:
```python
class CostTracker:
    def __init__(self):
        pass
    
    def calculate_query_cost(
        bedrock_tokens: TokenUsage,
        redshift_bytes_scanned: int,
        lambda_duration_ms: int
    ) -> Cost
    
    def add_query_cost(session_id: str, cost: Cost) -> None
    def get_daily_cost() -> Cost
    def get_monthly_estimate() -> Cost
    def get_cost_breakdown() -> Dict[str, Cost]
```

**Cost Calculation**:
- **Bedrock**: $0.003 per 1K input tokens, $0.015 per 1K output tokens
- **Redshift Serverless**: $0.36 per RPU-hour (8 RPUs minimum)
- **Lambda**: $0.0000166667 per GB-second
- **Glue Catalog**: $1 per 100K requests (negligible)

**Cost Display**:
- Per-query cost shown after each response
- Daily running total in UI sidebar
- Estimated monthly cost based on daily average
- Cost breakdown by service


### 9. Python Calculation Tools

**Purpose**: Provide precise business calculations invoked by LLM

**Components**:
- `CalculationTools`: Collection of calculation functions
- `ToolRegistry`: Register and invoke tools

**Interface**:
```python
class CalculationTools:
    @staticmethod
    def calculate_reorder_point(
        avg_daily_demand: float,
        lead_time_days: int,
        safety_stock: float
    ) -> float:
        """Reorder Point = (Avg Daily Demand × Lead Time) + Safety Stock"""
        return (avg_daily_demand * lead_time_days) + safety_stock
    
    @staticmethod
    def calculate_safety_stock(
        max_daily_demand: float,
        avg_daily_demand: float,
        max_lead_time: int,
        avg_lead_time: int
    ) -> float:
        """Safety Stock = (Max Daily Demand × Max Lead Time) - (Avg Daily Demand × Avg Lead Time)"""
        return (max_daily_demand * max_lead_time) - (avg_daily_demand * avg_lead_time)
    
    @staticmethod
    def calculate_supplier_score(
        fill_rate: float,
        on_time_rate: float,
        quality_rate: float,
        cost_competitiveness: float
    ) -> float:
        """Weighted supplier score: 30% fill, 30% on-time, 20% quality, 20% cost"""
        return (fill_rate * 0.3 + on_time_rate * 0.3 + 
                quality_rate * 0.2 + cost_competitiveness * 0.2)
    
    @staticmethod
    def forecast_demand(
        historical_demand: List[float],
        periods: int,
        method: str = "moving_average"
    ) -> List[float]:
        """Forecast future demand using specified method"""
        # Implementation details
        pass
    
    @staticmethod
    def optimize_route(
        orders: List[Order],
        warehouse_location: Location
    ) -> RouteOptimization:
        """Optimize delivery route by grouping orders by delivery area"""
        # Implementation details
        pass
```

**Tool Registration for Bedrock**:
```python
TOOL_DEFINITIONS = [
    {
        "name": "calculate_reorder_point",
        "description": "Calculate optimal reorder point for a product",
        "parameters": {
            "avg_daily_demand": {"type": "number", "description": "Average daily demand"},
            "lead_time_days": {"type": "integer", "description": "Lead time in days"},
            "safety_stock": {"type": "number", "description": "Safety stock quantity"}
        }
    },
    # ... other tools
]
```


### 10. Streamlit UI

**Purpose**: Provide user interface for authentication, query input, and results display

**Components**:
- `LoginPage`: Authentication interface
- `MainApp`: Main application interface
- `ResultsDisplay`: Query results visualization
- `CostDashboard`: Cost tracking display
- `ConversationSidebar`: Conversation history

**UI Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  Supply Chain AI Assistant                    [Logout]      │
├─────────────────────────────────────────────────────────────┤
│  Persona: [Warehouse Manager ▼]                             │
├──────────────────────┬──────────────────────────────────────┤
│  Conversation        │  Main Query Area                     │
│  History             │                                      │
│  ─────────────       │  Enter your query:                   │
│  1. Show low stock   │  ┌────────────────────────────────┐ │
│  2. Calculate...     │  │                                │ │
│  3. Forecast...      │  └────────────────────────────────┘ │
│                      │  [Submit Query]                      │
│  Cost Tracker        │                                      │
│  ─────────────       │  Results:                            │
│  Query: $0.02        │  ┌────────────────────────────────┐ │
│  Daily: $1.45        │  │  [Table/Chart Display]         │ │
│  Monthly: ~$43.50    │  │                                │ │
│                      │  └────────────────────────────────┘ │
│  Cache Stats         │                                      │
│  ─────────────       │  Query Cost: $0.02                   │
│  Hit Rate: 45%       │  Execution Time: 2.3s                │
│  Cached: 23          │                                      │
└──────────────────────┴──────────────────────────────────────┘
```

**Key Features**:
- Session state management
- Real-time cost updates
- Conversation history with clickable past queries
- Cache statistics
- Error message display
- Loading indicators
- Export results to CSV


## Data Models

### Database Schema

**Table: product**
```sql
CREATE TABLE product (
    product_code VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    product_group VARCHAR(50),
    unit_cost DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    supplier_code VARCHAR(50),
    supplier_name VARCHAR(200),
    created_date DATE,
    updated_date DATE
);
```

**Table: warehouse_product**
```sql
CREATE TABLE warehouse_product (
    warehouse_code VARCHAR(50),
    product_code VARCHAR(50),
    current_stock INTEGER,
    minimum_stock INTEGER,
    maximum_stock INTEGER,
    reorder_point INTEGER,
    lead_time_days INTEGER,
    last_restock_date DATE,
    PRIMARY KEY (warehouse_code, product_code),
    FOREIGN KEY (product_code) REFERENCES product(product_code)
);
```

**Table: sales_order_header**
```sql
CREATE TABLE sales_order_header (
    sales_order_prefix VARCHAR(10),
    sales_order_number VARCHAR(50),
    order_date DATE,
    customer_code VARCHAR(50),
    customer_name VARCHAR(200),
    warehouse_code VARCHAR(50),
    delivery_address VARCHAR(500),
    delivery_area VARCHAR(100),
    delivery_date DATE,
    status VARCHAR(50),
    PRIMARY KEY (sales_order_prefix, sales_order_number)
);
```

**Table: sales_order_line**
```sql
CREATE TABLE sales_order_line (
    sales_order_prefix VARCHAR(10),
    sales_order_number VARCHAR(50),
    sales_order_line INTEGER,
    product_code VARCHAR(50),
    order_quantity INTEGER,
    fulfilled_quantity INTEGER,
    unit_price DECIMAL(10,2),
    line_total DECIMAL(10,2),
    fulfillment_status VARCHAR(50),
    PRIMARY KEY (sales_order_prefix, sales_order_number, sales_order_line),
    FOREIGN KEY (sales_order_prefix, sales_order_number) 
        REFERENCES sales_order_header(sales_order_prefix, sales_order_number),
    FOREIGN KEY (product_code) REFERENCES product(product_code)
);
```

**Table: purchase_order_header**
```sql
CREATE TABLE purchase_order_header (
    purchase_order_prefix VARCHAR(10),
    purchase_order_number VARCHAR(50),
    order_date DATE,
    supplier_code VARCHAR(50),
    supplier_name VARCHAR(200),
    warehouse_code VARCHAR(50),
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    status VARCHAR(50),
    PRIMARY KEY (purchase_order_prefix, purchase_order_number)
);
```

**Table: purchase_order_line**
```sql
CREATE TABLE purchase_order_line (
    purchase_order_prefix VARCHAR(10),
    purchase_order_number VARCHAR(50),
    purchase_order_line INTEGER,
    product_code VARCHAR(50),
    order_quantity INTEGER,
    received_quantity INTEGER,
    unit_cost DECIMAL(10,2),
    line_total DECIMAL(10,2),
    receipt_status VARCHAR(50),
    PRIMARY KEY (purchase_order_prefix, purchase_order_number, purchase_order_line),
    FOREIGN KEY (purchase_order_prefix, purchase_order_number) 
        REFERENCES purchase_order_header(purchase_order_prefix, purchase_order_number),
    FOREIGN KEY (product_code) REFERENCES product(product_code)
);
```


### Application Data Models

**User Model**:
```python
@dataclass
class User:
    username: str
    password_hash: str
    personas: List[str]
    active: bool
    created_date: datetime
```

**Query Response Model**:
```python
@dataclass
class QueryResponse:
    query: str
    persona: str
    intent: Intent
    sql_query: Optional[str]
    results: Optional[pd.DataFrame]
    agent_response: Optional[str]
    cost: Cost
    execution_time: float
    cached: bool
    timestamp: datetime
```

**Cost Model**:
```python
@dataclass
class Cost:
    bedrock_cost: float
    redshift_cost: float
    lambda_cost: float
    total_cost: float
    tokens_used: TokenUsage
```

## Error Handling

### Error Categories

1. **Authentication Errors**
   - Invalid credentials
   - Unauthorized persona access
   - Session expired

2. **Query Errors**
   - Invalid SQL syntax
   - Query timeout
   - Database connection failure

3. **Agent Errors**
   - Bedrock API errors (throttling, quota)
   - Lambda invocation failures
   - Tool execution errors

4. **System Errors**
   - Configuration errors
   - Resource unavailable
   - Network errors

### Error Handling Strategy

```python
class ErrorHandler:
    def handle_error(error: Exception, context: ErrorContext) -> ErrorResponse:
        """
        1. Log full error details with stack trace
        2. Determine error category and severity
        3. Generate user-friendly message
        4. Suggest remediation steps if applicable
        5. Track error metrics
        """
        pass
```

**User-Friendly Error Messages**:
- Authentication: "Invalid username or password. Please try again."
- Query: "Unable to process your query. Please rephrase and try again."
- System: "Service temporarily unavailable. Please try again in a moment."

**Error Recovery**:
- Automatic retry for transient errors (3 attempts with exponential backoff)
- Fallback to cached results when available
- Graceful degradation (e.g., skip caching if cache unavailable)


## Deployment Options

### Option 1: Local Development

**Use Case**: Development, testing, demos

**Setup**:
- Python virtual environment
- AWS credentials configured locally
- Streamlit runs on localhost:8501

**Pros**:
- No deployment costs
- Fast iteration
- Easy debugging

**Cons**:
- Single user only
- Not accessible remotely
- No high availability

### Option 2: Amazon SageMaker

**Use Case**: Team collaboration, production MVP

**Deployment Approaches**:

**A. SageMaker Studio**:
- Deploy Streamlit app in SageMaker Studio
- Use Studio's built-in authentication
- Access via Studio interface
- Shared environment for team

**B. SageMaker Notebook Instance**:
- Deploy on ml.t3.medium instance ($0.05/hour)
- Run Streamlit as background process
- Access via proxy or port forwarding
- Persistent storage with EBS

**C. SageMaker Hosting (Real-time Endpoint)**:
- Package app as container
- Deploy as SageMaker endpoint
- Auto-scaling capabilities
- Production-grade hosting

**Setup Steps for SageMaker Notebook**:
```bash
# 1. Create notebook instance (ml.t3.medium)
# 2. Install dependencies
pip install -r requirements.txt

# 3. Run Streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# 4. Access via SageMaker proxy URL
```

**IAM Permissions Required**:
- Bedrock: `bedrock:InvokeModel`
- Redshift: `redshift-data:ExecuteStatement`, `redshift-data:GetStatementResult`
- Lambda: `lambda:InvokeFunction`
- Glue: `glue:GetTable`, `glue:GetDatabase`

**Cost Estimate (SageMaker Notebook)**:
- ml.t3.medium: ~$36/month (24/7)
- Or ~$8/month (8 hours/day, 5 days/week)
- Plus AWS service costs (~$150/month)
- **Total**: ~$44-186/month depending on usage

**Pros**:
- Integrated with AWS ecosystem
- Built-in authentication and security
- Team collaboration support
- Managed infrastructure
- Easy scaling

**Cons**:
- Additional compute cost
- Requires SageMaker knowledge
- More complex setup than local

### Option 3: EC2 Instance

**Use Case**: Production deployment with full control

**Setup**:
- Launch t3.small EC2 instance ($15/month)
- Install Python and dependencies
- Run Streamlit as systemd service
- Use nginx as reverse proxy
- SSL certificate with Let's Encrypt

**Pros**:
- Full control over environment
- Can use custom domain
- Lower cost than SageMaker for 24/7
- Easy to backup and restore

**Cons**:
- Manual infrastructure management
- Need to handle security updates
- No built-in authentication

### Recommended Approach

**For MVP**: **SageMaker Notebook Instance (ml.t3.medium)**

**Rationale**:
1. Integrated AWS authentication
2. Easy team access
3. Managed infrastructure
4. Cost-effective for part-time usage
5. Can easily migrate to SageMaker Hosting later
6. Built-in Jupyter for data exploration

**Migration Path**:
- Start: Local development
- MVP: SageMaker Notebook (8 hours/day)
- Production: SageMaker Hosting or ECS Fargate with ALB


## Testing Strategy

### Unit Tests

**Components to Test**:
- Authentication logic
- SQL generation
- Calculation tools
- Cache operations
- Cost calculations
- Semantic layer resolution

**Framework**: pytest

**Example**:
```python
def test_calculate_reorder_point():
    result = CalculationTools.calculate_reorder_point(
        avg_daily_demand=10.0,
        lead_time_days=7,
        safety_stock=20.0
    )
    assert result == 90.0

def test_cache_hit():
    cache = QueryCache()
    cache.set("key1", {"data": "value"}, ttl=300)
    result = cache.get("key1")
    assert result is not None
    assert result["data"] == "value"
```

### Integration Tests

**Scenarios**:
- End-to-end query flow (user input → SQL → results)
- Bedrock API integration
- Redshift query execution
- Lambda function invocation
- Glue catalog metadata retrieval

**Approach**:
- Use test AWS account
- Mock external dependencies where appropriate
- Test with sample data

### User Acceptance Testing

**Test Cases by Persona**:

**Warehouse Manager**:
- Query low stock products
- Calculate reorder points
- Forecast demand
- Identify stockout risks

**Field Engineer**:
- Query orders for delivery
- Optimize delivery routes
- Check order fulfillment status
- Identify delayed orders

**Procurement Specialist**:
- Analyze supplier performance
- Compare supplier costs
- Identify cost savings
- Analyze purchase trends

**Success Criteria**:
- Query response time < 5 seconds (95th percentile)
- Query accuracy > 95%
- User satisfaction > 4/5
- Cost per query < $0.05


## Configuration Management

### Configuration File Structure

**config.yaml**:
```yaml
# AWS Configuration
aws:
  region: us-east-1
  bedrock:
    model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
    max_tokens: 4096
    temperature: 0.0
  redshift:
    workgroup_name: supply-chain-mvp
    database: supply_chain_db
    data_api_timeout: 30
  glue:
    catalog_id: "123456789012"
    database: supply_chain_catalog
  lambda:
    inventory_function: supply-chain-inventory-optimizer
    logistics_function: supply-chain-logistics-optimizer
    supplier_function: supply-chain-supplier-analyzer

# Application Configuration
app:
  name: Supply Chain AI Assistant
  version: 1.0.0
  session_timeout: 3600
  max_query_length: 1000

# Cache Configuration
cache:
  enabled: true
  max_size: 1000
  default_ttl: 300
  dashboard_ttl: 900

# Conversation Memory
conversation:
  max_history: 10
  clear_on_persona_switch: true

# Cost Tracking
cost:
  enabled: true
  log_file: logs/cost_tracking.log
  bedrock_input_cost_per_1k: 0.003
  bedrock_output_cost_per_1k: 0.015
  redshift_rpu_cost_per_hour: 0.36
  lambda_cost_per_gb_second: 0.0000166667

# Logging
logging:
  level: INFO
  file: logs/app.log
  max_bytes: 10485760  # 10MB
  backup_count: 5

# Authentication
auth:
  users_file: config/users.json
  session_secret: ${SESSION_SECRET}  # From environment variable
  password_min_length: 8
```

### Environment Variables

Required environment variables:
- `AWS_REGION`: AWS region
- `AWS_ACCESS_KEY_ID`: AWS access key (or use IAM role)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key (or use IAM role)
- `SESSION_SECRET`: Secret key for session management

### Configuration Loading

```python
class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self._validate_config()
    
    def _load_config(self, path: str) -> dict:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        # Substitute environment variables
        return self._substitute_env_vars(config)
    
    def _validate_config(self):
        # Validate required fields
        required = ['aws.region', 'aws.bedrock.model_id', 'aws.redshift.workgroup_name']
        for field in required:
            if not self._get_nested(field):
                raise ConfigError(f"Missing required config: {field}")
```


## Security Considerations

### Authentication & Authorization

1. **Password Security**:
   - Passwords hashed with bcrypt (cost factor 12)
   - Minimum 8 characters
   - No password stored in plain text

2. **Session Management**:
   - Secure session tokens (UUID4)
   - Session timeout after 1 hour of inactivity
   - Session invalidation on logout

3. **Persona Authorization**:
   - Users assigned to specific personas
   - Authorization check before every query
   - Audit log of persona access

### Data Security

1. **AWS Credentials**:
   - Use IAM roles when possible (SageMaker, EC2)
   - Never commit credentials to code
   - Rotate credentials regularly

2. **Database Access**:
   - Use Redshift Data API (no direct connection)
   - Least privilege IAM policies
   - Query logging enabled

3. **Data in Transit**:
   - HTTPS for Streamlit (in production)
   - TLS for all AWS API calls

4. **Data at Rest**:
   - Redshift encryption enabled
   - Encrypted EBS volumes (SageMaker/EC2)

### Input Validation

1. **Query Input**:
   - Max length validation (1000 chars)
   - SQL injection prevention (parameterized queries)
   - Sanitize user input before logging

2. **SQL Generation**:
   - Validate generated SQL before execution
   - Whitelist allowed tables per persona
   - Prevent destructive operations (DROP, DELETE, UPDATE)

### Audit Logging

Log the following events:
- User login/logout
- Persona selection/switch
- Query execution (query text, persona, timestamp)
- Cost information
- Errors and exceptions
- Configuration changes


## Performance Optimization

### Query Performance

1. **Caching Strategy**:
   - Cache identical queries for 5 minutes
   - Cache dashboard queries for 15 minutes
   - Pre-warm cache with common queries
   - LRU eviction policy

2. **Database Optimization**:
   - Use Redshift sort keys on date columns
   - Use distribution keys on join columns
   - Analyze query execution plans
   - Monitor Redshift query performance

3. **Parallel Processing**:
   - Execute independent tool calls in parallel
   - Async Lambda invocations where possible

### Cost Optimization

1. **Bedrock**:
   - Optimize prompts to reduce token usage
   - Cache tool definitions
   - Use streaming responses where applicable

2. **Redshift Serverless**:
   - Start with 8 RPUs (minimum)
   - Monitor and adjust based on usage
   - Use query result caching
   - Schedule data loads during off-peak

3. **Lambda**:
   - Right-size memory allocation
   - Use ARM architecture (Graviton2)
   - Minimize cold starts with provisioned concurrency (if needed)

### Monitoring Metrics

**Application Metrics**:
- Query response time (p50, p95, p99)
- Cache hit rate
- Error rate by type
- Active sessions

**AWS Metrics**:
- Bedrock token usage
- Redshift query execution time
- Lambda invocation count and duration
- Cost per query

**Alerting Thresholds**:
- Error rate > 5%
- Query response time p95 > 10 seconds
- Daily cost > $20
- Cache hit rate < 30%


## Migration Path to Production

### Current MVP Architecture

- Redshift Serverless (8 RPUs)
- 3 Lambda functions
- Glue Data Catalog
- Bedrock
- Single application instance (SageMaker/EC2)

### Production Architecture

- Amazon Athena (serverless, pay-per-query)
- API Gateway + Lambda (scalable API)
- DynamoDB (session state, caching)
- Cognito (enterprise authentication)
- ECS Fargate + ALB (scalable application)
- CloudWatch (comprehensive monitoring)
- Multi-region deployment

### Migration Steps

**Phase 1: Database Migration**
1. Export Redshift data to S3 (Parquet format)
2. Create Glue crawlers for S3 data
3. Update SQL agents to use Athena instead of Redshift
4. Test query compatibility
5. Switch traffic to Athena

**Phase 2: API Layer**
1. Create API Gateway REST API
2. Move orchestrator logic to Lambda
3. Implement API authentication
4. Add rate limiting and throttling
5. Update UI to call API

**Phase 3: Authentication**
1. Create Cognito user pool
2. Migrate users from local file
3. Implement Cognito authentication in UI
4. Add MFA support
5. Implement fine-grained permissions

**Phase 4: Scalability**
1. Containerize Streamlit app
2. Deploy to ECS Fargate
3. Add Application Load Balancer
4. Implement auto-scaling
5. Add CloudWatch dashboards

**Phase 5: High Availability**
1. Multi-AZ deployment
2. DynamoDB for session state
3. ElastiCache for query caching
4. Multi-region replication (optional)

### Code Modularity for Migration

**Database Abstraction**:
```python
class DatabaseClient(ABC):
    @abstractmethod
    def execute_query(self, sql: str) -> QueryResult:
        pass

class RedshiftClient(DatabaseClient):
    # Redshift implementation
    pass

class AthenaClient(DatabaseClient):
    # Athena implementation
    pass

# Easy to switch via configuration
db_client = RedshiftClient() if config.use_redshift else AthenaClient()
```

**Configuration-Driven**:
```yaml
database:
  type: redshift  # or athena
  redshift:
    workgroup_name: supply-chain-mvp
  athena:
    output_location: s3://bucket/athena-results/
```

This modular design ensures smooth migration from MVP to production with minimal code changes.


## Project Structure

```
mvp-cost-optimized/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── config.yaml                     # Application configuration
├── config.example.yaml             # Configuration template
├── README.md                       # Setup and usage documentation
│
├── auth/                           # Authentication module
│   ├── __init__.py
│   ├── auth_manager.py            # Authentication logic
│   ├── session_manager.py         # Session management
│   └── users.json                 # User credentials (gitignored)
│
├── agents/                         # Agent implementations
│   ├── __init__.py
│   ├── base_agent.py              # Base agent class
│   ├── sql_agent.py               # SQL agent base
│   ├── warehouse_sql_agent.py     # Warehouse Manager SQL agent
│   ├── field_sql_agent.py         # Field Engineer SQL agent
│   ├── procurement_sql_agent.py   # Procurement SQL agent
│   ├── inventory_agent.py         # Inventory specialized agent
│   ├── logistics_agent.py         # Logistics specialized agent
│   └── supplier_agent.py          # Supplier specialized agent
│
├── orchestrator/                   # Orchestration logic
│   ├── __init__.py
│   ├── query_orchestrator.py      # Main orchestrator
│   ├── intent_classifier.py       # Intent classification
│   └── agent_router.py            # Agent routing
│
├── semantic_layer/                 # Semantic layer
│   ├── __init__.py
│   ├── semantic_layer.py          # Semantic layer implementation
│   ├── business_metrics.py        # Business metric definitions
│   └── schema_provider.py         # Glue catalog schema access
│
├── tools/                          # Calculation tools
│   ├── __init__.py
│   ├── calculation_tools.py       # Python calculation functions
│   └── tool_registry.py           # Tool registration for Bedrock
│
├── cache/                          # Caching module
│   ├── __init__.py
│   ├── query_cache.py             # Query result cache
│   └── cache_stats.py             # Cache statistics
│
├── memory/                         # Conversation memory
│   ├── __init__.py
│   ├── conversation_memory.py     # Conversation storage
│   └── context.py                 # Context models
│
├── cost/                           # Cost tracking
│   ├── __init__.py
│   ├── cost_tracker.py            # Cost calculation and tracking
│   └── cost_logger.py             # Cost logging
│
├── database/                       # Database clients
│   ├── __init__.py
│   ├── database_client.py         # Abstract database client
│   ├── redshift_client.py         # Redshift Serverless client
│   └── athena_client.py           # Athena client (for migration)
│
├── aws/                            # AWS service clients
│   ├── __init__.py
│   ├── bedrock_client.py          # Bedrock client wrapper
│   ├── lambda_client.py           # Lambda client wrapper
│   └── glue_client.py             # Glue catalog client
│
├── ui/                             # UI components
│   ├── __init__.py
│   ├── login_page.py              # Login interface
│   ├── main_app.py                # Main application interface
│   ├── results_display.py         # Results visualization
│   ├── cost_dashboard.py          # Cost tracking display
│   └── conversation_sidebar.py    # Conversation history
│
├── utils/                          # Utility functions
│   ├── __init__.py
│   ├── config_manager.py          # Configuration management
│   ├── error_handler.py           # Error handling
│   └── logger.py                  # Logging setup
│
├── lambda_functions/               # Lambda function code
│   ├── inventory_optimizer/
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── logistics_optimizer/
│   │   ├── handler.py
│   │   └── requirements.txt
│   └── supplier_analyzer/
│       ├── handler.py
│       └── requirements.txt
│
├── infrastructure/                 # Infrastructure as code
│   ├── cdk/
│   │   ├── app.py
│   │   ├── mvp_stack.py
│   │   └── cdk.json
│   └── sagemaker/
│       ├── lifecycle_config.sh
│       └── setup_notebook.sh
│
├── scripts/                        # Utility scripts
│   ├── generate_sample_data.py    # Sample data generation
│   ├── setup_glue_catalog.py      # Glue catalog setup
│   ├── deploy_lambda.sh           # Lambda deployment
│   └── create_user.py             # User creation utility
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_agents.py
│   ├── test_orchestrator.py
│   ├── test_cache.py
│   ├── test_tools.py
│   └── test_integration.py
│
└── logs/                           # Log files (gitignored)
    ├── app.log
    └── cost_tracking.log
```

## Summary

This design provides a comprehensive, cost-optimized MVP architecture that:

1. **Supports all three personas** with specialized agents and tools
2. **Minimizes AWS costs** using Redshift Serverless, minimal Lambda, and no unnecessary services
3. **Includes advanced features** like semantic layer, caching, conversation memory, and cost tracking
4. **Provides flexible deployment** options including SageMaker, EC2, or local
5. **Enables easy migration** to full production architecture through modular design
6. **Ensures security** with authentication, authorization, and audit logging
7. **Optimizes performance** through caching and query optimization
8. **Maintains observability** with comprehensive logging and cost tracking

The estimated monthly cost is **~$150-200** for moderate usage (100-200 queries/day), which is significantly lower than the full production architecture (~$240-500/month) while maintaining all core functionality.

