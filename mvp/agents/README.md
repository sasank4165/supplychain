# SQL Agents Module

This module provides SQL agents for converting natural language queries to SQL and executing them against the Redshift database.

## Overview

The agents module implements a hierarchical agent architecture:

1. **BaseAgent**: Common functionality for all agents (logging, error handling, response formatting)
2. **SQLAgent**: Base SQL agent with SQL generation and execution logic
3. **Persona-Specific SQL Agents**: Specialized agents for each user persona

## Architecture

```
BaseAgent (base_agent.py)
    ↓
SQLAgent (sql_agent.py)
    ↓
    ├── WarehouseSQLAgent (warehouse_sql_agent.py)
    ├── FieldEngineerSQLAgent (field_sql_agent.py)
    └── ProcurementSQLAgent (procurement_sql_agent.py)
```

## Components

### BaseAgent

Provides common functionality:
- Logging (info, error, debug)
- Response creation (success/error)
- Exception handling
- User-friendly error messages

### SQLAgent

Core SQL agent functionality:
- Natural language to SQL conversion using Bedrock
- SQL validation and safety checks
- Query execution against Redshift
- Result formatting
- Integration with semantic layer for business context

### Persona-Specific Agents

#### WarehouseSQLAgent
- **Persona**: Warehouse Manager
- **Tables**: product, warehouse_product, sales_order_header, sales_order_line
- **Focus**: Inventory management, stock levels, reorder points
- **Key Queries**: Low stock, reorder needs, stock availability

#### FieldEngineerSQLAgent
- **Persona**: Field Engineer
- **Tables**: product, warehouse_product, sales_order_header, sales_order_line
- **Focus**: Order delivery, logistics, fulfillment tracking
- **Key Queries**: Delivery schedules, overdue orders, fulfillment status

#### ProcurementSQLAgent
- **Persona**: Procurement Specialist
- **Tables**: product, warehouse_product, purchase_order_header, purchase_order_line
- **Focus**: Purchase orders, supplier management, cost analysis
- **Key Queries**: Supplier performance, cost comparison, pending POs

## Usage

### Basic Usage

```python
from agents import WarehouseSQLAgent
from aws.bedrock_client import BedrockClient
from aws.redshift_client import RedshiftClient
from semantic_layer.semantic_layer import SemanticLayer
from semantic_layer.business_metrics import Persona
from semantic_layer.schema_provider import SchemaProvider
from aws.glue_client import GlueClient

# Initialize clients
bedrock_client = BedrockClient(
    region='us-east-1',
    model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'
)

redshift_client = RedshiftClient(
    region='us-east-1',
    workgroup_name='supply-chain-mvp',
    database='supply_chain_db'
)

glue_client = GlueClient(
    region='us-east-1',
    database='supply_chain_catalog'
)

# Initialize semantic layer
schema_provider = SchemaProvider(glue_client)
semantic_layer = SemanticLayer(schema_provider, Persona.WAREHOUSE_MANAGER)

# Create agent
agent = WarehouseSQLAgent(
    bedrock_client=bedrock_client,
    redshift_client=redshift_client,
    semantic_layer=semantic_layer
)

# Process query
response = agent.process_query("Show me products with low stock")

if response.success:
    print(response.content)
    print(f"SQL: {response.metadata['sql']}")
    print(f"Rows: {response.metadata['row_count']}")
else:
    print(f"Error: {response.error}")
```

### With Conversation Context

```python
from agents import ConversationContext

# Create conversation context
context = ConversationContext(
    session_id="user123",
    persona=Persona.WAREHOUSE_MANAGER,
    history=[
        {"query": "Show warehouse inventory", "response": "..."},
        {"query": "Filter by warehouse A", "response": "..."}
    ],
    referenced_entities={"warehouse": "A"}
)

# Process query with context
response = agent.process_query(
    "Show me the low stock items",
    context=context
)
```

## Data Models

### AgentResponse

```python
@dataclass
class AgentResponse:
    success: bool
    content: str
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
```

### SQLResponse

```python
@dataclass
class SQLResponse:
    query: str
    sql: str
    results: Optional[QueryResult]
    formatted_response: str
    execution_time: float
    cached: bool = False
```

### ConversationContext

```python
@dataclass
class ConversationContext:
    session_id: str
    persona: Persona
    history: List[Dict[str, str]]
    referenced_entities: Dict[str, Any]
    last_query_time: Optional[float] = None
```

## SQL Generation Process

1. **Enrich Context**: Semantic layer enriches query with business terms and schema
2. **Build Prompts**: System and user prompts built with persona-specific guidance
3. **Generate SQL**: Bedrock generates SQL from natural language
4. **Validate SQL**: Safety checks (no destructive operations, allowed tables only)
5. **Execute Query**: Redshift executes validated SQL
6. **Format Results**: Results formatted with persona-specific context

## SQL Validation

All generated SQL is validated for safety:
- ✅ Must be SELECT queries only
- ✅ Must reference allowed tables for persona
- ❌ No DELETE, DROP, TRUNCATE, ALTER, CREATE, INSERT, UPDATE
- ❌ No access to tables outside persona scope

## Error Handling

Agents provide user-friendly error messages:
- Connection errors → "Unable to connect to the service"
- Timeout errors → "Request took too long to complete"
- Permission errors → "You don't have permission"
- Not found errors → "Resource was not found"
- Generic errors → "An error occurred, please try again"

## Logging

All agents log:
- Query processing start/end
- Generated SQL
- Query execution time
- Row counts
- Errors with stack traces

## Integration Points

### Bedrock Client
- SQL generation from natural language
- Tool calling support (future)
- Token usage tracking

### Redshift Client
- Query execution via Data API
- Result pagination
- Connection management

### Semantic Layer
- Business term resolution
- Schema metadata
- Table access control
- Query context enrichment

## Testing

See `test_agents.py` for unit tests and `example_usage.py` for usage examples.

## Future Enhancements

- [ ] Query result caching
- [ ] Conversation memory integration
- [ ] Multi-turn query refinement
- [ ] Query explanation generation
- [ ] SQL optimization suggestions
- [ ] Query performance monitoring
