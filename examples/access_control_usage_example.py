"""Example usage of AccessController for fine-grained access control

This example demonstrates:
1. Persona-level authorization
2. Table-level access validation
3. Tool-level access validation
4. Row-level security injection
5. Bulk access validation
6. Audit log retrieval
7. Integration with orchestrator and agents
"""
import os
from datetime import datetime, timedelta
from access_controller import AccessController
from orchestrator import SupplyChainOrchestrator
from agents import SQLAgent, InventoryOptimizerAgent


def example_1_basic_access_control():
    """Example 1: Basic access control checks"""
    print("\n=== Example 1: Basic Access Control ===\n")
    
    # Initialize access controller
    access_controller = AccessController(region="us-east-1")
    
    # User context from authentication
    warehouse_manager_context = {
        "user_id": "user123",
        "username": "john.doe",
        "persona": "warehouse_manager",
        "groups": ["warehouse_managers"],
        "session_id": "session_abc"
    }
    
    # Check persona access
    print("1. Checking persona access...")
    if access_controller.authorize(warehouse_manager_context, "warehouse_manager"):
        print("   ✓ User authorized for warehouse_manager persona")
    else:
        print("   ✗ User NOT authorized for warehouse_manager persona")
    
    # Check table access
    print("\n2. Checking table access...")
    tables_to_check = ["warehouse_product", "purchase_order_header", "product"]
    
    for table in tables_to_check:
        can_access = access_controller.authorize_table_access(
            warehouse_manager_context,
            table,
            "read"
        )
        status = "✓ Allowed" if can_access else "✗ Denied"
        print(f"   {status}: {table}")
    
    # Check tool access
    print("\n3. Checking tool access...")
    tools_to_check = [
        "execute_sql_query",
        "calculate_reorder_points",
        "analyze_supplier_performance"
    ]
    
    for tool in tools_to_check:
        can_execute = access_controller.authorize_tool_access(
            warehouse_manager_context,
            tool
        )
        status = "✓ Allowed" if can_execute else "✗ Denied"
        print(f"   {status}: {tool}")


def example_2_row_level_security():
    """Example 2: Row-level security injection"""
    print("\n=== Example 2: Row-Level Security ===\n")
    
    access_controller = AccessController(region="us-east-1")
    
    warehouse_manager_context = {
        "user_id": "user123",
        "username": "john.doe",
        "persona": "warehouse_manager",
        "groups": ["warehouse_managers"],
        "session_id": "session_abc"
    }
    
    # Original SQL query
    original_sql = "SELECT * FROM warehouse_product WHERE product_code = 'ABC123'"
    print(f"Original SQL:\n{original_sql}\n")
    
    # Apply row-level security
    secured_sql = access_controller.inject_row_level_security(
        warehouse_manager_context,
        original_sql
    )
    print(f"Secured SQL:\n{secured_sql}\n")
    
    # Example with JOIN
    original_sql_join = """
    SELECT p.product_code, p.short_name, w.physical_stock_su
    FROM product p
    JOIN warehouse_product w ON p.product_code = w.product_code
    WHERE p.product_group = 'Electronics'
    """
    print(f"Original SQL with JOIN:\n{original_sql_join}\n")
    
    secured_sql_join = access_controller.inject_row_level_security(
        warehouse_manager_context,
        original_sql_join
    )
    print(f"Secured SQL with JOIN:\n{secured_sql_join}\n")


def example_3_bulk_validation():
    """Example 3: Bulk access validation"""
    print("\n=== Example 3: Bulk Access Validation ===\n")
    
    access_controller = AccessController(region="us-east-1")
    
    field_engineer_context = {
        "user_id": "user456",
        "username": "jane.smith",
        "persona": "field_engineer",
        "groups": ["field_engineers"],
        "session_id": "session_def"
    }
    
    # Validate multiple tables at once
    print("1. Bulk table access validation:")
    tables = [
        "product",
        "warehouse_product",
        "sales_order_header",
        "purchase_order_header"
    ]
    
    table_access = access_controller.validate_bulk_table_access(
        field_engineer_context,
        tables,
        "read"
    )
    
    for table, allowed in table_access.items():
        status = "✓ Allowed" if allowed else "✗ Denied"
        print(f"   {status}: {table}")
    
    # Validate multiple tools at once
    print("\n2. Bulk tool access validation:")
    tools = [
        "execute_sql_query",
        "optimize_delivery_routes",
        "calculate_reorder_points",
        "track_shipments"
    ]
    
    tool_access = access_controller.validate_bulk_tool_access(
        field_engineer_context,
        tools
    )
    
    for tool, allowed in tool_access.items():
        status = "✓ Allowed" if allowed else "✗ Denied"
        print(f"   {status}: {tool}")


def example_4_orchestrator_integration():
    """Example 4: Integration with orchestrator"""
    print("\n=== Example 4: Orchestrator Integration ===\n")
    
    # Initialize orchestrator (automatically creates AccessController)
    orchestrator = SupplyChainOrchestrator(region="us-east-1")
    
    warehouse_manager_context = {
        "user_id": "user123",
        "username": "john.doe",
        "persona": "warehouse_manager",
        "groups": ["warehouse_managers"],
        "session_id": "session_abc"
    }
    
    print("Processing query with automatic access control...")
    
    # This will automatically:
    # 1. Validate persona access
    # 2. Validate table access (in SQL agent)
    # 3. Apply row-level security
    # 4. Validate tool access (if tools used)
    # 5. Log all access decisions
    
    result = orchestrator.process_query(
        query="Show me products with low stock levels",
        persona="warehouse_manager",
        session_id="session_abc",
        context=warehouse_manager_context
    )
    
    if result.get("success"):
        print("   ✓ Query processed successfully")
        print(f"   Intent: {result.get('intent')}")
    else:
        print(f"   ✗ Query failed: {result.get('error')}")
        if result.get("status") == 403:
            print("   (Access denied)")


def example_5_sql_agent_integration():
    """Example 5: Integration with SQL agent"""
    print("\n=== Example 5: SQL Agent Integration ===\n")
    
    access_controller = AccessController(region="us-east-1")
    sql_agent = SQLAgent(persona="warehouse_manager", region="us-east-1")
    
    warehouse_manager_context = {
        "user_id": "user123",
        "username": "john.doe",
        "persona": "warehouse_manager",
        "groups": ["warehouse_managers"],
        "session_id": "session_abc"
    }
    
    print("Processing SQL query with access control...")
    
    # SQL agent will:
    # 1. Validate table access
    # 2. Apply row-level security
    # 3. Execute query
    
    result = sql_agent.process_query(
        query="Show me all products in warehouse WH01",
        session_id="session_abc",
        context=warehouse_manager_context,
        access_controller=access_controller
    )
    
    if result.get("success"):
        print("   ✓ Query executed successfully")
        print(f"   SQL: {result.get('sql')}")
        print(f"   Rows: {result.get('row_count')}")
    else:
        print(f"   ✗ Query failed: {result.get('error')}")


def example_6_tool_execution_with_access_control():
    """Example 6: Tool execution with access control"""
    print("\n=== Example 6: Tool Execution with Access Control ===\n")
    
    access_controller = AccessController(region="us-east-1")
    agent = InventoryOptimizerAgent(region="us-east-1")
    
    warehouse_manager_context = {
        "user_id": "user123",
        "username": "john.doe",
        "persona": "warehouse_manager",
        "groups": ["warehouse_managers"],
        "session_id": "session_abc"
    }
    
    print("Executing tool with access control...")
    
    # This will validate tool access before execution
    result = agent.execute_tool_async(
        tool_name="calculate_reorder_points",
        function_name="inventory-optimizer-lambda",
        input_data={"warehouse_code": "WH01"},
        user_context=warehouse_manager_context,
        access_controller=access_controller
    )
    
    if result.get("success"):
        print("   ✓ Tool executed successfully")
        print(f"   Execution time: {result.get('execution_time_ms')}ms")
    else:
        print(f"   ✗ Tool execution failed: {result.get('error')}")
        if result.get("status") == 403:
            print("   (Access denied)")


def example_7_audit_logs():
    """Example 7: Retrieving and analyzing audit logs"""
    print("\n=== Example 7: Audit Log Retrieval ===\n")
    
    access_controller = AccessController(region="us-east-1")
    
    # Get audit logs from last hour
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow()
    
    print("Retrieving audit logs...")
    
    # Get all denied access attempts
    denied_logs = access_controller.get_audit_logs(
        start_time=start_time,
        end_time=end_time,
        decision="deny",
        limit=50
    )
    
    if denied_logs:
        print(f"\nFound {len(denied_logs)} denied access attempts:\n")
        for log in denied_logs[:5]:  # Show first 5
            print(f"   User: {log['user_id']}")
            print(f"   Resource: {log['resource_type']}/{log['resource_name']}")
            print(f"   Action: {log['action']}")
            print(f"   Reason: {log['reason']}")
            print(f"   Time: {log['timestamp']}")
            print()
    else:
        print("   No denied access attempts found")
    
    # Get logs for specific user
    user_logs = access_controller.get_audit_logs(
        start_time=start_time,
        end_time=end_time,
        user_id="user123",
        limit=50
    )
    
    if user_logs:
        print(f"\nFound {len(user_logs)} access decisions for user123")
        
        # Analyze access patterns
        allowed = sum(1 for log in user_logs if log['decision'] == 'allow')
        denied = sum(1 for log in user_logs if log['decision'] == 'deny')
        
        print(f"   Allowed: {allowed}")
        print(f"   Denied: {denied}")


def example_8_access_denied_handling():
    """Example 8: Handling access denied scenarios"""
    print("\n=== Example 8: Access Denied Handling ===\n")
    
    access_controller = AccessController(region="us-east-1")
    
    # User trying to access wrong persona
    warehouse_user_context = {
        "user_id": "user123",
        "username": "john.doe",
        "persona": "warehouse_manager",
        "groups": ["warehouse_managers"],
        "session_id": "session_abc"
    }
    
    print("1. Attempting to access procurement specialist features...")
    if not access_controller.authorize(warehouse_user_context, "procurement_specialist"):
        print("   ✗ Access denied: User is not in procurement_specialists group")
        print("   Action: Redirect to appropriate persona or show error")
    
    print("\n2. Attempting to access restricted table...")
    if not access_controller.authorize_table_access(
        warehouse_user_context,
        "purchase_order_header",
        "read"
    ):
        print("   ✗ Access denied: Table not in allowed list for warehouse_manager")
        print("   Action: Show error message, log security event")
    
    print("\n3. Attempting to execute unauthorized tool...")
    if not access_controller.authorize_tool_access(
        warehouse_user_context,
        "analyze_supplier_performance"
    ):
        print("   ✗ Access denied: Tool not available for warehouse_manager")
        print("   Action: Return 403 error, suggest alternative tools")


def example_9_get_accessible_resources():
    """Example 9: Getting accessible resources for a persona"""
    print("\n=== Example 9: Get Accessible Resources ===\n")
    
    access_controller = AccessController(region="us-east-1")
    
    personas = ["warehouse_manager", "field_engineer", "procurement_specialist"]
    
    for persona in personas:
        print(f"\n{persona.replace('_', ' ').title()}:")
        
        # Get accessible tables
        tables = access_controller.get_accessible_tables(persona)
        print(f"   Tables ({len(tables)}):")
        for table in tables:
            print(f"      - {table}")
        
        # Get accessible tools
        tools = access_controller.get_accessible_tools(persona)
        print(f"   Tools ({len(tools)}):")
        for tool in tools:
            print(f"      - {tool}")


def main():
    """Run all examples"""
    print("=" * 70)
    print("Access Control Usage Examples")
    print("=" * 70)
    
    try:
        example_1_basic_access_control()
        example_2_row_level_security()
        example_3_bulk_validation()
        example_9_get_accessible_resources()
        
        # Note: Examples 4-8 require AWS credentials and resources
        print("\n" + "=" * 70)
        print("Note: Examples 4-8 require AWS credentials and deployed resources")
        print("=" * 70)
        
        # Uncomment to run with AWS resources:
        # example_4_orchestrator_integration()
        # example_5_sql_agent_integration()
        # example_6_tool_execution_with_access_control()
        # example_7_audit_logs()
        # example_8_access_denied_handling()
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
