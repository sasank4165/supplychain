# Access Control Quick Reference

## Quick Start

```python
from access_controller import AccessController

# Initialize
access_controller = AccessController(region="us-east-1")

# User context (from authentication)
user_context = {
    "user_id": "user123",
    "username": "john.doe",
    "persona": "warehouse_manager",
    "groups": ["warehouse_managers"],
    "session_id": "session_abc"
}
```

## Common Operations

### Check Persona Access
```python
if not access_controller.authorize(user_context, "warehouse_manager"):
    return {"error": "Access denied", "status": 403}
```

### Check Table Access
```python
if not access_controller.authorize_table_access(user_context, "warehouse_product", "read"):
    return {"error": "Access denied to table", "status": 403}
```

### Check Tool Access
```python
if not access_controller.authorize_tool_access(user_context, "calculate_reorder_points"):
    return {"error": "Access denied to tool", "status": 403}
```

### Apply Row-Level Security
```python
sql = "SELECT * FROM warehouse_product"
secured_sql = access_controller.inject_row_level_security(user_context, sql)
```

### Bulk Validation
```python
# Multiple tables
table_access = access_controller.validate_bulk_table_access(
    user_context, 
    ["product", "warehouse_product", "purchase_order_header"],
    "read"
)

# Multiple tools
tool_access = access_controller.validate_bulk_tool_access(
    user_context,
    ["execute_sql_query", "calculate_reorder_points"]
)
```

## Access Mappings

### Personas → Groups
| Persona | Group |
|---------|-------|
| warehouse_manager | warehouse_managers |
| field_engineer | field_engineers |
| procurement_specialist | procurement_specialists |

### Personas → Tables
| Persona | Tables |
|---------|--------|
| warehouse_manager | product, warehouse_product, sales_order_header, sales_order_line |
| field_engineer | product, warehouse_product, sales_order_header, sales_order_line |
| procurement_specialist | product, warehouse_product, purchase_order_header, purchase_order_line |

### Personas → Tools
| Persona | Tools |
|---------|-------|
| warehouse_manager | execute_sql_query, calculate_reorder_points, forecast_demand, identify_stockout_risks, optimize_stock_levels |
| field_engineer | execute_sql_query, optimize_delivery_routes, calculate_shipping_costs, track_shipments, analyze_logistics_performance |
| procurement_specialist | execute_sql_query, analyze_supplier_performance, identify_cost_savings, evaluate_supplier_risk, recommend_suppliers |

## Integration Examples

### With Orchestrator
```python
from orchestrator import SupplyChainOrchestrator

orchestrator = SupplyChainOrchestrator(region="us-east-1")

# Access control is automatic
result = orchestrator.process_query(
    query="Show me low stock items",
    persona="warehouse_manager",
    session_id="session_abc",
    context=user_context
)
```

### With SQL Agent
```python
from agents import SQLAgent

sql_agent = SQLAgent(persona="warehouse_manager", region="us-east-1")

result = sql_agent.process_query(
    query="Show all products",
    session_id="session_abc",
    context=user_context,
    access_controller=access_controller
)
```

### With Base Agent (Tools)
```python
from agents import InventoryOptimizerAgent

agent = InventoryOptimizerAgent(region="us-east-1")

result = agent.execute_tool_async(
    tool_name="calculate_reorder_points",
    function_name="inventory-optimizer-lambda",
    input_data={"warehouse_code": "WH01"},
    user_context=user_context,
    access_controller=access_controller
)
```

## Audit Logs

### Retrieve Logs
```python
from datetime import datetime, timedelta

logs = access_controller.get_audit_logs(
    start_time=datetime.utcnow() - timedelta(hours=1),
    end_time=datetime.utcnow(),
    user_id="user123",
    resource_type="table",
    decision="deny",
    limit=100
)
```

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
  "session_id": "session_abc"
}
```

## Error Handling

### Standard Error Response
```python
{
    "success": False,
    "error": "Access denied to table: purchase_order_header",
    "status": 403
}
```

### Check for Access Errors
```python
result = orchestrator.process_query(...)

if not result.get("success") and result.get("status") == 403:
    # Handle access denied
    log_security_event(result["error"])
    return user_friendly_error()
```

## Helper Methods

### Get Accessible Resources
```python
# Get tables user can access
tables = access_controller.get_accessible_tables("warehouse_manager")

# Get tools user can execute
tools = access_controller.get_accessible_tools("warehouse_manager")
```

## Testing

### Basic Test
```python
def test_access_control():
    access_controller = AccessController(region="us-east-1")
    
    context = {
        "user_id": "test_user",
        "persona": "warehouse_manager",
        "groups": ["warehouse_managers"]
    }
    
    # Should allow
    assert access_controller.authorize_table_access(context, "warehouse_product", "read")
    
    # Should deny
    assert not access_controller.authorize_table_access(context, "purchase_order_header", "read")
```

## Common Issues

### Issue: Access Denied
**Check:**
1. User in correct Cognito group?
2. Persona matches user's role?
3. Table/tool in allowed list?
4. Review audit logs for reason

### Issue: RLS Not Applied
**Check:**
1. User context contains persona?
2. RLS rules defined for persona?
3. Table name matches rule key?
4. Check CloudWatch logs

### Issue: Logs Not Appearing
**Check:**
1. CloudWatch log group exists?
2. IAM permissions for PutLogEvents?
3. Log stream created successfully?

## Best Practices

1. ✅ Always provide complete user context
2. ✅ Handle 403 errors gracefully
3. ✅ Review audit logs regularly
4. ✅ Test access control in unit tests
5. ✅ Use bulk operations for efficiency
6. ✅ Log security events
7. ✅ Follow least privilege principle

## Related Documentation

- [Complete Guide](ACCESS_CONTROLLER_GUIDE.md)
- [Implementation Summary](TASK_10_IMPLEMENTATION_SUMMARY.md)
- [RBAC Guide](../auth/RBAC_GUIDE.md)
