# Semantic Layer

The semantic layer maps business terms to SQL patterns and provides schema metadata for SQL generation. It integrates with AWS Glue Data Catalog to provide comprehensive context to SQL agents.

## Components

### 1. Business Metrics (`business_metrics.py`)

Defines business metrics and their SQL patterns for each persona.

**Key Classes:**
- `Persona`: Enum for user personas (Warehouse Manager, Field Engineer, Procurement Specialist)
- `MetricDefinition`: Data class defining a business metric
- `BusinessMetrics`: Collection of all business metrics

**Warehouse Manager Metrics:**
- `low_stock`: Products below minimum stock level
- `stockout_risk`: Products at risk of stockout
- `reorder_needed`: Products that need reordering
- `out_of_stock`: Products with zero stock
- `overstock`: Products exceeding maximum stock
- `stock_turnover`: Stock turnover rates
- `inventory_value`: Total inventory value

**Field Engineer Metrics:**
- `overdue_orders`: Orders past delivery date
- `delivery_today`: Orders for delivery today
- `delayed_shipments`: Delayed shipments
- `pending_orders`: Orders with pending status
- `in_transit_orders`: Orders in transit
- `unfulfilled_lines`: Unfulfilled order lines
- `delivery_by_area`: Orders by delivery area
- `orders_by_warehouse`: Orders by warehouse

**Procurement Specialist Metrics:**
- `top_suppliers`: Top suppliers by volume
- `cost_variance`: Cost variance analysis
- `pending_pos`: Pending purchase orders
- `late_deliveries`: Late supplier deliveries
- `supplier_performance`: Supplier on-time rate
- `incomplete_receipts`: Incomplete PO receipts
- `purchase_by_product_group`: Purchases by product group
- `supplier_cost_comparison`: Supplier cost comparison

**Usage Example:**
```python
from semantic_layer.business_metrics import BusinessMetrics, Persona

# Get metrics for a persona
wm_metrics = BusinessMetrics.get_metrics_for_persona(Persona.WAREHOUSE_MANAGER)

# Find metrics by keywords
results = BusinessMetrics.find_metric_by_keywords(['stock', 'low'], Persona.WAREHOUSE_MANAGER)

# Get common business terms
terms = BusinessMetrics.get_common_business_terms()
# Returns: {'low stock': 'current_stock < minimum_stock', ...}
```

### 2. Schema Provider (`schema_provider.py`)

Fetches schema metadata from AWS Glue Data Catalog.

**Key Classes:**
- `TableSchema`: Simplified table schema
- `SchemaProvider`: Provides schema metadata from Glue Catalog

**Features:**
- Fetch table schemas from Glue Catalog
- Cache schemas for performance
- Generate human-readable table context
- Identify related tables through foreign keys
- Extract primary and foreign key information

**Usage Example:**
```python
from aws.glue_client import GlueClient
from semantic_layer.schema_provider import SchemaProvider

# Initialize
glue_client = GlueClient(region='us-east-1', database='supply_chain_catalog')
schema_provider = SchemaProvider(glue_client)

# Get table schema
schema = schema_provider.get_table_schema('warehouse_product')
print(schema.columns)  # {'warehouse_code': 'varchar(50)', ...}

# Get all tables
tables = schema_provider.list_tables()

# Generate context for LLM
context = schema_provider.generate_table_context('warehouse_product')
```

### 3. Semantic Layer (`semantic_layer.py`)

Main semantic layer that combines business metrics and schema metadata.

**Key Classes:**
- `EnrichedContext`: Enriched query context with business and schema info
- `SemanticLayer`: Main semantic layer implementation

**Features:**
- Enrich user queries with business context
- Identify relevant tables and metrics
- Suggest table joins
- Generate complete context for LLM prompts
- Persona-specific table access control

**Usage Example:**
```python
from semantic_layer import SemanticLayer, Persona
from semantic_layer.schema_provider import SchemaProvider
from aws.glue_client import GlueClient

# Initialize
glue_client = GlueClient(region='us-east-1', database='supply_chain_catalog')
schema_provider = SchemaProvider(glue_client)
semantic_layer = SemanticLayer(schema_provider, Persona.WAREHOUSE_MANAGER)

# Enrich a query
query = "Show me products with low stock"
enriched = semantic_layer.enrich_query_context(query)

print(enriched.relevant_tables)  # ['warehouse_product', 'product']
print(enriched.relevant_metrics)  # [MetricDefinition(name='low_stock', ...)]
print(enriched.business_terms)   # {'low stock': 'current_stock < minimum_stock'}

# Generate full context for LLM
context = semantic_layer.generate_full_context_for_llm(query)
# Returns formatted string with schema, metrics, and business terms
```

## Integration with SQL Agents

The semantic layer is designed to be used by SQL agents for query generation:

```python
# In SQL Agent
from semantic_layer import SemanticLayer, Persona

class WarehouseSQLAgent:
    def __init__(self, bedrock_client, redshift_client, semantic_layer):
        self.semantic_layer = semantic_layer
        # ...
    
    def generate_sql(self, query: str) -> str:
        # Get enriched context
        context = self.semantic_layer.generate_full_context_for_llm(query)
        
        # Build prompt with context
        prompt = f"""
        {context}
        
        User Query: {query}
        
        Generate a SQL query to answer this question.
        """
        
        # Call Bedrock with prompt
        sql = self.bedrock_client.generate_sql(prompt)
        return sql
```

## Persona-Specific Table Access

Each persona has access to specific tables:

**Warehouse Manager:**
- product
- warehouse_product
- sales_order_header
- sales_order_line

**Field Engineer:**
- product
- warehouse_product
- sales_order_header
- sales_order_line

**Procurement Specialist:**
- product
- warehouse_product
- purchase_order_header
- purchase_order_line

## Testing

Run the test suite to verify functionality:

```bash
cd mvp/semantic_layer
python test_semantic_layer.py
```

The test suite validates:
- All required metrics are defined for each persona
- Keyword search works correctly
- Business terms are properly mapped
- Schema provider data structures work
- Semantic layer structure is correct

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SQL Agent                            │
│  - Receives user query                                  │
│  - Needs schema and business context                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Semantic Layer                          │
│  - Enriches query with context                          │
│  - Maps business terms to SQL                           │
│  - Identifies relevant tables and metrics               │
└────────┬───────────────────────────┬────────────────────┘
         │                           │
         ▼                           ▼
┌──────────────────┐      ┌──────────────────────────────┐
│ Schema Provider  │      │   Business Metrics           │
│ - Glue Catalog   │      │   - Metric definitions       │
│ - Table schemas  │      │   - SQL patterns             │
│ - Relationships  │      │   - Business terms           │
└──────────────────┘      └──────────────────────────────┘
```

## Future Enhancements

1. **Dynamic Metric Learning**: Learn new metrics from user queries
2. **Query Pattern Recognition**: Identify common query patterns
3. **Automatic Join Optimization**: Suggest optimal join strategies
4. **Metric Validation**: Validate metric SQL patterns against schema
5. **Multi-language Support**: Support business terms in multiple languages
6. **Metric Dependencies**: Define dependencies between metrics
7. **Custom Metrics**: Allow users to define custom metrics

## Requirements

- Python 3.11+
- boto3 (for AWS Glue Catalog access)
- AWS credentials with Glue permissions

## Related Components

- `aws/glue_client.py`: AWS Glue Data Catalog client
- `agents/sql_agent.py`: SQL agent that uses semantic layer
- `orchestrator/query_orchestrator.py`: Orchestrator that routes queries
