# Access Controller Guide

## Overview

The `AccessController` provides fine-grained access control for the Supply Chain Agentic AI Application. It enforces security policies at multiple levels:

- **Persona-level authorization**: Validates user access to specific personas
- **Table-level access control**: Restricts database table access based on user roles
- **Tool-level access control**: Controls which AI agent tools users can execute
- **Row-level security**: Injects SQL filters to restrict data visibility
- **Audit logging**: Comprehensive logging of all access decisions to CloudWatch

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Request                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Orchestrator                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Validate Persona Access                          │  │
│  │     AccessController.authorize()                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              SQL Agent                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  2. Validate Table Access                            │  │
│  │     AccessController.authorize_table_access()        │  │
│  │                                                       │  │
│  │  3. Inject Row-Level Security                        │  │
│  │     AccessController.inject_row_level_security()     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Specialist Agents                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  4. Validate Tool Access                             │  │
│  │     AccessController.authorize_tool_access()         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              CloudWatch Logs                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  5. Audit Log All Decisions                          │  │
│  │     AccessController._log_access_decision()          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Initialization

### Basic Initialization

```python
from access_controller import AccessController

# Initialize with default settings
access_controller = AccessController(region="us-east-1")
```

### With Configuration Manager

```python
from config_manager import ConfigurationManager
from access_controller import AccessController

# Initialize with configuration
config = ConfigurationManager(environment="prod")
access_controller = AccessController(region="us-east-1", config=config)
```

## Access Control Levels

### 1. Persona-Level Authorization

Validates that a user has permission to access a specific persona.

```python
user_context = {
    "user_id": "user123",
    "username": "john.doe",
    "persona": "warehouse_manager",
    "groups": ["warehouse_managers"],
    "session_id": "session_abc"
}

# Check if user can access warehouse_manager persona
authorized = access_controller.authorize(user_context, "warehouse_manager")

if not authorized:
    return {"error": "Access denied", "status": 403}
```

**Persona to Group Mapping:**
- `warehouse_manager` → `warehouse_managers`
- `field_engineer` → `field_engineers`
- `procurement_specialist` → `procurement_specialists`

### 2. Table-Level Access Control

Restricts access to database tables based on user persona.

```python
# Check if user can read from a table
can_access = access_controller.authorize_table_access(
    user_context=user_context,
    table_name="warehouse_product",
    action="read"
)

if not can_access:
    return {"error": "Access denied to table", "status": 403}
```

**Table Access by Persona:**

| Persona | Accessible Tables |
|---------|------------------|
| Warehouse Manager | product, warehouse_product, sales_order_header, sales_order_line |
| Field Engineer | product, warehouse_product, sales_order_header, sales_order_line |
| Procurement Specialist | product, warehouse_product, purchase_order_header, purchase_order_line |

### 3. Tool-Level Access Control

Controls which AI agent tools users can execute.

```python
# Check if user can execute a tool
can_execute = access_controller.authorize_tool_access(
    user_context=user_context,
    tool_name="calculate_reorder_points"
)

if not can_execute:
    return {"error": "Access denied to tool", "status": 403}
```

**Tool Access by Persona:**

**Warehouse Manager:**
- execute_sql_query
- calculate_reorder_points
- forecast_demand
- identify_stockout_risks
- optimize_stock_levels

**Field Engineer:**
- execute_sql_query
- optimize_delivery_routes
- calculate_shipping_costs
- track_shipments
- analyze_logistics_performance

**Procurement Specialist:**
- execute_sql_query
- analyze_supplier_performance
- identify_cost_savings
- evaluate_supplier_risk
- recommend_suppliers

### 4. Row-Level Security

Automatically injects SQL filters to restrict data visibility based on user context.

```python
# Original SQL query
sql_query = "SELECT * FROM warehouse_product WHERE product_code = 'ABC123'"

# Inject row-level security filters
secured_query = access_controller.inject_row_level_security(
    user_context=user_context,
    sql_query=sql_query
)

# Result might be:
# SELECT * FROM warehouse_product 
# WHERE (warehouse_code IN (SELECT warehouse_code FROM user_warehouses WHERE user_id = 'user123')) 
# AND product_code = 'ABC123'
```

**Row-Level Security Rules:**

Currently configured for warehouse managers and field engineers to restrict access to specific warehouses based on user assignments.

## Bulk Operations

### Validate Multiple Tables

```python
tables = ["product", "warehouse_product", "purchase_order_header"]

results = access_controller.validate_bulk_table_access(
    user_context=user_context,
    table_names=tables,
    action="read"
)

# Results: {"product": True, "warehouse_product": True, "purchase_order_header": False}
```

### Validate Multiple Tools

```python
tools = ["execute_sql_query", "calculate_reorder_points", "analyze_supplier_performance"]

results = access_controller.validate_bulk_tool_access(
    user_context=user_context,
    tool_names=tools
)

# Results: {"execute_sql_query": True, "calculate_reorder_points": True, "analyze_supplier_performance": False}
```

## Audit Logging

All access control decisions are automatically logged to CloudWatch Logs for compliance and security monitoring.

### Log Structure

```json
{
  "timestamp": "2024-11-14T10:30:00.000Z",
  "user_id": "user123",
  "resource_type": "table",
  "resource_name": "warehouse_product",
  "action": "read",
  "decision": "allow",
  "reason": "Persona warehouse_manager table access",
  "persona": "warehouse_manager",
  "groups": ["warehouse_managers"],
  "session_id": "session_abc",
  "metadata": {}
}
```

### Retrieve Audit Logs

```python
from datetime import datetime, timedelta

# Get audit logs for the last hour
start_time = datetime.utcnow() - timedelta(hours=1)
end_time = datetime.utcnow()

logs = access_controller.get_audit_logs(
    start_time=start_time,
    end_time=end_time,
    user_id="user123",
    resource_type="table",
    decision="deny",
    limit=100
)

for log in logs:
    print(f"{log['timestamp']}: {log['decision']} - {log['reason']}")
```

## Integration with Orchestrator

The orchestrator automatically uses the AccessController for all requests:

```python
from orchestrator import SupplyChainOrchestrator

orchestrator = SupplyChainOrchestrator(region="us-east-1")

# User context from authentication
user_context = {
    "user_id": "user123",
    "username": "john.doe",
    "persona": "warehouse_manager",
    "groups": ["warehouse_managers"],
    "session_id": "session_abc"
}

# Process query with automatic access control
result = orchestrator.process_query(
    query="Show me low stock items",
    persona="warehouse_manager",
    session_id="session_abc",
    context=user_context
)
```

## Integration with SQL Agent

The SQL Agent uses AccessController for table access validation and row-level security:

```python
from agents import SQLAgent

sql_agent = SQLAgent(persona="warehouse_manager", region="us-east-1")

# Process query with access control
result = sql_agent.process_query(
    query="Show me all products",
    session_id="session_abc",
    context=user_context,
    access_controller=access_controller
)
```

## Integration with Base Agent

Specialist agents inherit tool access control from BaseAgent:

```python
from agents import InventoryOptimizerAgent

agent = InventoryOptimizerAgent(region="us-east-1")

# Execute tool with access control
result = agent.execute_tool_async(
    tool_name="calculate_reorder_points",
    function_name="inventory-optimizer-lambda",
    input_data={"warehouse_code": "WH01"},
    user_context=user_context,
    access_controller=access_controller
)
```

## Configuration

### Custom Table Access Rules

Modify `config.py` to customize table access:

```python
PERSONA_TABLE_ACCESS: Dict[Persona, List[str]] = {
    Persona.WAREHOUSE_MANAGER: [
        "product", 
        "warehouse_product", 
        "sales_order_header", 
        "sales_order_line",
        "custom_table"  # Add custom table
    ],
    # ... other personas
}
```

### Custom Tool Access Rules

Modify `access_controller.py` to customize tool access:

```python
self.tool_permissions = {
    "warehouse_manager": [
        "execute_sql_query",
        "calculate_reorder_points",
        "custom_tool"  # Add custom tool
    ],
    # ... other personas
}
```

### Custom Row-Level Security Rules

Modify `access_controller.py` to add RLS rules:

```python
self.row_level_security_rules = {
    "warehouse_manager": {
        "warehouse_product": "warehouse_code IN (SELECT warehouse_code FROM user_warehouses WHERE user_id = '{user_id}')",
        "custom_table": "region = '{user_region}'"  # Add custom RLS rule
    },
    # ... other personas
}
```

## Best Practices

### 1. Always Provide User Context

```python
# Good: Full context
user_context = {
    "user_id": "user123",
    "username": "john.doe",
    "persona": "warehouse_manager",
    "groups": ["warehouse_managers"],
    "session_id": "session_abc"
}

# Bad: Missing fields
user_context = {
    "user_id": "user123"
}
```

### 2. Handle Access Denied Gracefully

```python
result = orchestrator.process_query(query, persona, session_id, context)

if not result.get("success") and result.get("status") == 403:
    # Log security event
    logger.warning(f"Access denied for user {context['user_id']}")
    
    # Return user-friendly message
    return {
        "error": "You don't have permission to perform this action",
        "status": 403
    }
```

### 3. Review Audit Logs Regularly

```python
# Daily security review
logs = access_controller.get_audit_logs(
    start_time=datetime.utcnow() - timedelta(days=1),
    decision="deny",
    limit=1000
)

# Alert on suspicious patterns
denied_by_user = {}
for log in logs:
    user_id = log['user_id']
    denied_by_user[user_id] = denied_by_user.get(user_id, 0) + 1

for user_id, count in denied_by_user.items():
    if count > 10:
        alert_security_team(f"User {user_id} had {count} access denials")
```

### 4. Test Access Control

```python
# Unit test for access control
def test_warehouse_manager_cannot_access_purchase_orders():
    context = {
        "user_id": "test_user",
        "persona": "warehouse_manager",
        "groups": ["warehouse_managers"]
    }
    
    can_access = access_controller.authorize_table_access(
        context, 
        "purchase_order_header", 
        "read"
    )
    
    assert can_access is False
```

## Troubleshooting

### Access Denied Errors

**Problem:** User receives "Access denied" error

**Solutions:**
1. Verify user is in correct Cognito group
2. Check persona matches user's assigned role
3. Review audit logs for specific denial reason
4. Verify table/tool is in allowed list for persona

### Row-Level Security Not Applied

**Problem:** RLS filters not appearing in SQL queries

**Solutions:**
1. Verify user_context contains persona
2. Check RLS rules are defined for persona
3. Ensure table name matches RLS rule key exactly
4. Review CloudWatch logs for RLS application

### Audit Logs Not Appearing

**Problem:** Access decisions not logged to CloudWatch

**Solutions:**
1. Verify CloudWatch log group exists
2. Check IAM permissions for PutLogEvents
3. Review application logs for CloudWatch errors
4. Ensure log stream is created successfully

## Security Considerations

1. **Least Privilege**: Only grant minimum required access
2. **Defense in Depth**: Multiple layers of access control
3. **Audit Everything**: All decisions logged for compliance
4. **Fail Secure**: Deny access by default if validation fails
5. **Regular Reviews**: Periodically review access patterns and rules

## Performance Considerations

1. **Caching**: Consider caching access decisions for frequently accessed resources
2. **Bulk Operations**: Use bulk validation methods when checking multiple resources
3. **Async Logging**: CloudWatch logging is non-blocking
4. **Query Optimization**: RLS filters should use indexed columns

## Related Documentation

- [Authentication Guide](../auth/README.md)
- [RBAC Guide](../auth/RBAC_GUIDE.md)
- [Orchestrator Guide](ORCHESTRATOR_GUIDE.md)
- [Agent Development Guide](AGENT_DEVELOPMENT_GUIDE.md)
