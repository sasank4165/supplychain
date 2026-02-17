# Query Orchestrator

The Query Orchestrator is the central coordination component of the Cost-Optimized Supply Chain MVP. It manages intent classification, agent routing, and session management to process user queries efficiently.

## Overview

The orchestrator consists of three main components:

1. **Intent Classifier** - Determines query intent (SQL_QUERY, OPTIMIZATION, or HYBRID)
2. **Agent Router** - Routes queries to appropriate agents based on persona and intent
3. **Query Orchestrator** - Coordinates the entire query processing pipeline

## Architecture

```
User Query
    ↓
Query Orchestrator
    ↓
Intent Classifier → Determines intent type
    ↓
Agent Router → Routes to appropriate agent(s)
    ↓
    ├─→ SQL Agent (for data retrieval)
    ├─→ Specialized Agent (for optimization)
    └─→ Both (for hybrid queries)
    ↓
Response
```

## Components

### 1. Intent Classifier

Classifies user queries into three intent types:

- **SQL_QUERY**: Data retrieval from database
  - Example: "Show me all products with low stock"
  
- **OPTIMIZATION**: Specialized agent tasks (calculations, analysis)
  - Example: "Calculate reorder points for product ABC123"
  
- **HYBRID**: Requires both SQL and optimization
  - Example: "Show me low stock products and calculate their reorder points"

**Usage:**
```python
from orchestrator import IntentClassifier
from aws.bedrock_client import BedrockClient

bedrock_client = BedrockClient(region="us-east-1", model_id="...")
classifier = IntentClassifier(bedrock_client, logger)

intent = classifier.classify(
    query="Show me all products with low stock",
    persona="Warehouse Manager"
)
# Returns: Intent.SQL_QUERY
```

### 2. Agent Router

Routes queries to appropriate agents based on persona and intent.

**Supported Personas:**
- Warehouse Manager → SQL Agent + Inventory Agent
- Field Engineer → SQL Agent + Logistics Agent
- Procurement Specialist → SQL Agent + Supplier Agent

**Routing Logic:**
- `SQL_QUERY` → Routes to SQL agent only
- `OPTIMIZATION` → Routes to specialized agent only
- `HYBRID` → Routes to both agents sequentially

**Usage:**
```python
from orchestrator import AgentRouter

router = AgentRouter(
    sql_agents={
        "Warehouse Manager": warehouse_sql_agent,
        "Field Engineer": field_sql_agent,
        "Procurement Specialist": procurement_sql_agent
    },
    specialized_agents={
        "Warehouse Manager": inventory_agent,
        "Field Engineer": logistics_agent,
        "Procurement Specialist": supplier_agent
    },
    logger=logger
)

response = router.route(
    query="Show me low stock products",
    intent=Intent.SQL_QUERY,
    persona="Warehouse Manager",
    context=None
)
```

### 3. Query Orchestrator

Main orchestrator that coordinates the entire query processing pipeline.

**Features:**
- Intent classification
- Agent routing
- Session management
- Conversation memory (last 10 interactions)
- Persona switching

**Usage:**
```python
from orchestrator import QueryOrchestrator

orchestrator = QueryOrchestrator(
    intent_classifier=classifier,
    agent_router=router,
    logger=logger
)

response = orchestrator.process_query(
    query="Show me all products with low stock",
    persona="Warehouse Manager",
    session_id="user_session_123"
)

print(f"Intent: {response.intent.value}")
print(f"Success: {response.agent_response.success}")
print(f"Response: {response.agent_response.content}")
```

## Query Processing Flow

1. **Validate Persona**: Ensure persona is supported
2. **Classify Intent**: Determine query intent using Bedrock
3. **Get Context**: Retrieve or create conversation context for session
4. **Route to Agents**: Route query to appropriate agent(s)
5. **Update Context**: Store interaction in conversation memory
6. **Return Response**: Return formatted response to user

## Session Management

The orchestrator maintains session-level conversation contexts:

```python
# Get conversation history
history = orchestrator.get_session_history("session_123")

# Clear session
orchestrator.clear_session("session_123")

# Switch persona (clears history)
orchestrator.switch_persona("session_123", "Field Engineer")
```

## Hybrid Query Processing

For hybrid queries that require both SQL and optimization:

1. Execute SQL agent to retrieve data
2. Pass SQL results to specialized agent
3. Specialized agent analyzes data and provides recommendations
4. Combine both responses into single output

Example:
```
Query: "Show me low stock products and calculate their reorder points"

Step 1: SQL Agent retrieves low stock products
Step 2: Inventory Agent calculates reorder points for those products
Step 3: Combined response with data + recommendations
```

## Error Handling

The orchestrator handles errors gracefully:

- Invalid persona → Returns error with available personas
- Intent classification failure → Defaults to SQL_QUERY
- Agent routing failure → Returns error response
- Agent execution failure → Returns agent error response

## Integration Example

See `example_usage.py` for a complete integration example:

```bash
cd mvp/orchestrator
python example_usage.py
```

## Configuration

The orchestrator requires the following configuration:

```yaml
aws:
  region: us-east-1
  bedrock:
    model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
  redshift:
    workgroup_name: supply-chain-mvp
    database: supply_chain_db
  lambda:
    inventory_function: supply-chain-inventory-optimizer
    logistics_function: supply-chain-logistics-optimizer
    supplier_function: supply-chain-supplier-analyzer
  glue:
    catalog_id: "123456789012"
    database: supply_chain_catalog
```

## Testing

Run tests for the orchestrator:

```bash
cd mvp
python -m pytest tests/test_orchestrator.py -v
```

## Dependencies

- `aws.bedrock_client` - For intent classification and SQL generation
- `agents.sql_agent` - For SQL query processing
- `agents.inventory_agent` - For inventory optimization
- `agents.logistics_agent` - For logistics optimization
- `agents.supplier_agent` - For supplier analysis
- `semantic_layer` - For business context and schema metadata

## Performance

- Intent classification: ~0.5-1s (Bedrock API call)
- SQL query routing: ~2-5s (SQL generation + execution)
- Optimization routing: ~3-8s (Lambda invocation + analysis)
- Hybrid routing: ~5-13s (SQL + optimization combined)

## Future Enhancements

- Query result caching integration
- Cost tracking per query
- Parallel execution for hybrid queries
- Advanced conversation memory with entity extraction
- Query rewriting based on conversation context

## Related Documentation

- [Agents README](../agents/README.md)
- [Semantic Layer README](../semantic_layer/README.md)
- [Design Document](../../.kiro/specs/cost-optimized-mvp/design.md)
