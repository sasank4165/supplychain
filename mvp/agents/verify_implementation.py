"""
Verification Script for SQL Agents Implementation

Verifies that all components are properly implemented and can be imported.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def verify_imports():
    """Verify all modules can be imported."""
    print("Verifying imports...")
    
    try:
        from agents import BaseAgent, AgentResponse
        print("✓ BaseAgent imported")
        
        from agents import SQLAgent, SQLResponse, ConversationContext
        print("✓ SQLAgent imported")
        
        from agents import WarehouseSQLAgent
        print("✓ WarehouseSQLAgent imported")
        
        from agents import FieldEngineerSQLAgent
        print("✓ FieldEngineerSQLAgent imported")
        
        from agents import ProcurementSQLAgent
        print("✓ ProcurementSQLAgent imported")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def verify_data_models():
    """Verify data models are properly defined."""
    print("\nVerifying data models...")
    
    try:
        from agents import AgentResponse, SQLResponse, ConversationContext
        from semantic_layer.business_metrics import Persona
        
        # Test AgentResponse
        response = AgentResponse(
            success=True,
            content="Test",
            data=None,
            error=None,
            execution_time=1.0,
            metadata={}
        )
        assert response.success == True
        print("✓ AgentResponse model works")
        
        # Test SQLResponse
        sql_response = SQLResponse(
            query="test query",
            sql="SELECT * FROM test",
            results=None,
            formatted_response="test",
            execution_time=1.0,
            cached=False
        )
        assert sql_response.query == "test query"
        print("✓ SQLResponse model works")
        
        # Test ConversationContext
        context = ConversationContext(
            session_id="test",
            persona=Persona.WAREHOUSE_MANAGER,
            history=[],
            referenced_entities={}
        )
        assert context.session_id == "test"
        print("✓ ConversationContext model works")
        
        return True
        
    except Exception as e:
        print(f"✗ Data model error: {e}")
        return False


def verify_agent_creation():
    """Verify agents can be instantiated."""
    print("\nVerifying agent creation...")
    
    try:
        from agents import WarehouseSQLAgent, FieldEngineerSQLAgent, ProcurementSQLAgent
        from semantic_layer.business_metrics import Persona
        
        # Mock clients for testing
        class MockBedrockClient:
            pass
        
        class MockRedshiftClient:
            pass
        
        class MockSemanticLayer:
            def __init__(self, persona):
                self.persona = persona
            
            def get_allowed_tables(self):
                return ['product', 'warehouse_product']
        
        # Test Warehouse Manager agent
        warehouse_agent = WarehouseSQLAgent(
            bedrock_client=MockBedrockClient(),
            redshift_client=MockRedshiftClient(),
            semantic_layer=MockSemanticLayer(Persona.WAREHOUSE_MANAGER)
        )
        assert warehouse_agent.agent_name == "WarehouseManagerSQLAgent"
        assert warehouse_agent.get_persona() == Persona.WAREHOUSE_MANAGER
        print("✓ WarehouseSQLAgent can be created")
        
        # Test Field Engineer agent
        field_agent = FieldEngineerSQLAgent(
            bedrock_client=MockBedrockClient(),
            redshift_client=MockRedshiftClient(),
            semantic_layer=MockSemanticLayer(Persona.FIELD_ENGINEER)
        )
        assert field_agent.agent_name == "FieldEngineerSQLAgent"
        assert field_agent.get_persona() == Persona.FIELD_ENGINEER
        print("✓ FieldEngineerSQLAgent can be created")
        
        # Test Procurement Specialist agent
        procurement_agent = ProcurementSQLAgent(
            bedrock_client=MockBedrockClient(),
            redshift_client=MockRedshiftClient(),
            semantic_layer=MockSemanticLayer(Persona.PROCUREMENT_SPECIALIST)
        )
        assert procurement_agent.agent_name == "ProcurementSpecialistSQLAgent"
        assert procurement_agent.get_persona() == Persona.PROCUREMENT_SPECIALIST
        print("✓ ProcurementSQLAgent can be created")
        
        return True
        
    except Exception as e:
        print(f"✗ Agent creation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_file_structure():
    """Verify all required files exist."""
    print("\nVerifying file structure...")
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    required_files = [
        'base_agent.py',
        'sql_agent.py',
        'warehouse_sql_agent.py',
        'field_sql_agent.py',
        'procurement_sql_agent.py',
        '__init__.py',
        'README.md',
        'test_agents.py',
        'example_usage.py',
        'IMPLEMENTATION_SUMMARY.md'
    ]
    
    all_exist = True
    for filename in required_files:
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            print(f"✓ {filename} exists")
        else:
            print(f"✗ {filename} missing")
            all_exist = False
    
    return all_exist


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("SQL Agents Implementation Verification")
    print("=" * 60)
    
    results = []
    
    # Run verification checks
    results.append(("Imports", verify_imports()))
    results.append(("Data Models", verify_data_models()))
    results.append(("Agent Creation", verify_agent_creation()))
    results.append(("File Structure", verify_file_structure()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All verification checks passed!")
        print("\nImplementation is complete and ready for integration.")
        return 0
    else:
        print("\n✗ Some verification checks failed.")
        print("\nPlease review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
