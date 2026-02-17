"""
Unit Tests for SQL Agents

Tests the SQL agent functionality including SQL generation,
validation, and persona-specific behavior.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, AgentResponse
from agents.sql_agent import SQLAgent, ConversationContext
from agents.warehouse_sql_agent import WarehouseSQLAgent
from agents.field_sql_agent import FieldEngineerSQLAgent
from agents.procurement_sql_agent import ProcurementSQLAgent
from semantic_layer.business_metrics import Persona


def test_base_agent():
    """Test BaseAgent functionality."""
    print("Testing BaseAgent...")
    
    agent = BaseAgent("TestAgent")
    
    # Test success response
    response = agent.create_success_response(
        content="Test successful",
        data={"key": "value"},
        execution_time=1.5
    )
    
    assert response.success == True
    assert response.content == "Test successful"
    assert response.data == {"key": "value"}
    assert response.error is None
    assert response.execution_time == 1.5
    
    # Test error response
    error_response = agent.create_error_response(
        error_message="Test error",
        execution_time=0.5
    )
    
    assert error_response.success == False
    assert error_response.error == "Test error"
    assert error_response.content == ""
    
    print("✓ BaseAgent tests passed")


def test_sql_validation():
    """Test SQL validation logic."""
    print("\nTesting SQL validation...")
    
    # Mock objects for testing
    class MockBedrockClient:
        pass
    
    class MockRedshiftClient:
        pass
    
    class MockSemanticLayer:
        def get_allowed_tables(self):
            return ['product', 'warehouse_product']
    
    agent = SQLAgent(
        agent_name="TestSQLAgent",
        persona=Persona.WAREHOUSE_MANAGER,
        bedrock_client=MockBedrockClient(),
        redshift_client=MockRedshiftClient(),
        semantic_layer=MockSemanticLayer()
    )
    
    # Test valid SELECT query
    valid_sql = "SELECT * FROM product WHERE product_code = 'ABC123'"
    assert agent._validate_sql(valid_sql) == True
    
    # Test destructive operations
    invalid_sqls = [
        "DELETE FROM product WHERE product_code = 'ABC123'",
        "DROP TABLE product",
        "UPDATE product SET unit_cost = 100",
        "INSERT INTO product VALUES ('X', 'Y')",
        "TRUNCATE TABLE product",
        "ALTER TABLE product ADD COLUMN test VARCHAR(50)"
    ]
    
    for sql in invalid_sqls:
        assert agent._validate_sql(sql) == False, f"Should reject: {sql}"
    
    # Test non-SELECT query
    assert agent._validate_sql("SHOW TABLES") == False
    
    # Test query with allowed table
    assert agent._validate_sql("SELECT * FROM product") == True
    assert agent._validate_sql("SELECT * FROM warehouse_product") == True
    
    print("✓ SQL validation tests passed")


def test_sql_extraction():
    """Test SQL extraction from Bedrock responses."""
    print("\nTesting SQL extraction...")
    
    class MockBedrockClient:
        pass
    
    class MockRedshiftClient:
        pass
    
    class MockSemanticLayer:
        def get_allowed_tables(self):
            return ['product']
    
    agent = SQLAgent(
        agent_name="TestSQLAgent",
        persona=Persona.WAREHOUSE_MANAGER,
        bedrock_client=MockBedrockClient(),
        redshift_client=MockRedshiftClient(),
        semantic_layer=MockSemanticLayer()
    )
    
    # Test extraction from code block with sql tag
    response1 = """Here's the SQL query:
```sql
SELECT * FROM product
```
"""
    sql1 = agent._extract_sql_from_response(response1)
    assert sql1 == "SELECT * FROM product"
    
    # Test extraction from code block without sql tag
    response2 = """```
SELECT * FROM product
```"""
    sql2 = agent._extract_sql_from_response(response2)
    assert sql2 == "SELECT * FROM product"
    
    # Test extraction without code blocks
    response3 = "SELECT * FROM product;"
    sql3 = agent._extract_sql_from_response(response3)
    assert sql3 == "SELECT * FROM product"
    
    # Test semicolon removal
    response4 = "```sql\nSELECT * FROM product;\n```"
    sql4 = agent._extract_sql_from_response(response4)
    assert sql4 == "SELECT * FROM product"
    
    print("✓ SQL extraction tests passed")


def test_persona_agents():
    """Test persona-specific agent initialization."""
    print("\nTesting persona-specific agents...")
    
    class MockBedrockClient:
        pass
    
    class MockRedshiftClient:
        pass
    
    class MockSemanticLayer:
        def __init__(self, persona):
            self.persona = persona
        
        def get_allowed_tables(self):
            if self.persona == Persona.WAREHOUSE_MANAGER:
                return ['product', 'warehouse_product', 'sales_order_header', 'sales_order_line']
            elif self.persona == Persona.FIELD_ENGINEER:
                return ['product', 'warehouse_product', 'sales_order_header', 'sales_order_line']
            elif self.persona == Persona.PROCUREMENT_SPECIALIST:
                return ['product', 'warehouse_product', 'purchase_order_header', 'purchase_order_line']
            return []
    
    # Test Warehouse Manager agent
    warehouse_agent = WarehouseSQLAgent(
        bedrock_client=MockBedrockClient(),
        redshift_client=MockRedshiftClient(),
        semantic_layer=MockSemanticLayer(Persona.WAREHOUSE_MANAGER)
    )
    assert warehouse_agent.get_persona() == Persona.WAREHOUSE_MANAGER
    assert warehouse_agent.agent_name == "WarehouseManagerSQLAgent"
    
    # Test Field Engineer agent
    field_agent = FieldEngineerSQLAgent(
        bedrock_client=MockBedrockClient(),
        redshift_client=MockRedshiftClient(),
        semantic_layer=MockSemanticLayer(Persona.FIELD_ENGINEER)
    )
    assert field_agent.get_persona() == Persona.FIELD_ENGINEER
    assert field_agent.agent_name == "FieldEngineerSQLAgent"
    
    # Test Procurement Specialist agent
    procurement_agent = ProcurementSQLAgent(
        bedrock_client=MockBedrockClient(),
        redshift_client=MockRedshiftClient(),
        semantic_layer=MockSemanticLayer(Persona.PROCUREMENT_SPECIALIST)
    )
    assert procurement_agent.get_persona() == Persona.PROCUREMENT_SPECIALIST
    assert procurement_agent.agent_name == "ProcurementSpecialistSQLAgent"
    
    print("✓ Persona agent tests passed")


def test_conversation_context():
    """Test ConversationContext data model."""
    print("\nTesting ConversationContext...")
    
    context = ConversationContext(
        session_id="test123",
        persona=Persona.WAREHOUSE_MANAGER,
        history=[
            {"query": "Show inventory", "response": "..."},
            {"query": "Filter by warehouse A", "response": "..."}
        ],
        referenced_entities={"warehouse": "A", "product": "ABC123"}
    )
    
    assert context.session_id == "test123"
    assert context.persona == Persona.WAREHOUSE_MANAGER
    assert len(context.history) == 2
    assert context.referenced_entities["warehouse"] == "A"
    assert context.last_query_time is None
    
    print("✓ ConversationContext tests passed")


def test_result_formatting():
    """Test result formatting for different personas."""
    print("\nTesting result formatting...")
    
    class MockQueryResult:
        def __init__(self, columns, rows):
            self.columns = columns
            self.rows = rows
            self.row_count = len(rows)
            self.execution_time = 1.0
        
        def to_dict_list(self):
            return [dict(zip(self.columns, row)) for row in self.rows]
    
    class MockBedrockClient:
        pass
    
    class MockRedshiftClient:
        pass
    
    class MockSemanticLayer:
        def get_allowed_tables(self):
            return ['product', 'warehouse_product']
    
    # Test Warehouse Manager formatting
    warehouse_agent = WarehouseSQLAgent(
        bedrock_client=MockBedrockClient(),
        redshift_client=MockRedshiftClient(),
        semantic_layer=MockSemanticLayer()
    )
    
    result = MockQueryResult(
        columns=['product_code', 'current_stock', 'minimum_stock'],
        rows=[
            ['ABC123', 5, 10],
            ['XYZ789', 15, 10]
        ]
    )
    
    formatted = warehouse_agent.format_results(result, "Show low stock items")
    assert "2 results" in formatted
    assert "ABC123" in formatted
    assert "⚠️" in formatted  # Low stock indicator
    
    print("✓ Result formatting tests passed")


if __name__ == "__main__":
    print("Running SQL Agent Tests\n" + "=" * 50)
    
    try:
        test_base_agent()
        test_sql_validation()
        test_sql_extraction()
        test_persona_agents()
        test_conversation_context()
        test_result_formatting()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
