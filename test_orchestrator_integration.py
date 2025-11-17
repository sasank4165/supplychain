"""Test orchestrator integration with all architecture components

This test verifies that the orchestrator properly integrates:
- AgentRegistry for agent management
- ModelManager for model selection
- ConversationContextManager for conversation history
- ToolExecutor for parallel tool execution
- MetricsCollector for monitoring and analytics
- AccessController for access control
"""
import os
import sys
from datetime import datetime, timedelta

# Set test environment
os.environ['ENVIRONMENT'] = 'dev'
os.environ['AWS_REGION'] = 'us-east-1'

def test_orchestrator_initialization():
    """Test that orchestrator initializes all components"""
    print("Testing orchestrator initialization...")
    
    try:
        from orchestrator import SupplyChainOrchestrator
        
        # Initialize orchestrator (will use environment variables)
        orchestrator = SupplyChainOrchestrator()
        
        # Check that all components are initialized
        components = {
            'config': orchestrator.config,
            'model_manager': orchestrator.model_manager,
            'tool_executor': orchestrator.tool_executor,
            'context_manager': orchestrator.context_manager,
            'metrics_collector': orchestrator.metrics_collector,
            'access_controller': orchestrator.access_controller,
            'agent_registry': orchestrator.agent_registry
        }
        
        print("\nComponent initialization status:")
        for name, component in components.items():
            status = "✓ Initialized" if component is not None else "✗ Not initialized"
            print(f"  {name}: {status}")
        
        # Verify critical components are initialized
        assert orchestrator.metrics_collector is not None, "MetricsCollector should be initialized"
        assert orchestrator.access_controller is not None, "AccessController should be initialized"
        
        print("\n✓ All critical components initialized successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_registry_integration():
    """Test AgentRegistry integration"""
    print("\n" + "="*60)
    print("Testing AgentRegistry integration...")
    
    try:
        from orchestrator import SupplyChainOrchestrator
        
        orchestrator = SupplyChainOrchestrator()
        
        if orchestrator.agent_registry:
            # Get all registered agents
            agents = orchestrator.get_all_registered_agents()
            print(f"\nRegistered agents: {agents.get('registered_agents', [])}")
            print(f"Agent count: {agents.get('agent_count', 0)}")
            
            # Get capabilities for a persona
            capabilities = orchestrator.get_agent_capabilities('warehouse_manager')
            print(f"\nWarehouse manager capabilities:")
            print(f"  SQL Agent: {capabilities.get('sql_agent', {}).get('name')}")
            if 'specialist_agent' in capabilities:
                print(f"  Specialist Agent: {capabilities['specialist_agent'].get('name')}")
                print(f"  Tools: {capabilities['specialist_agent'].get('tools', [])}")
            
            print("\n✓ AgentRegistry integration working")
        else:
            print("\n⚠ AgentRegistry not initialized (using fallback)")
        
        return True
        
    except Exception as e:
        print(f"\n✗ AgentRegistry integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics_collector_integration():
    """Test MetricsCollector integration"""
    print("\n" + "="*60)
    print("Testing MetricsCollector integration...")
    
    try:
        from orchestrator import SupplyChainOrchestrator
        
        orchestrator = SupplyChainOrchestrator()
        
        if orchestrator.metrics_collector:
            # Get current stats
            stats = orchestrator.get_metrics_stats()
            print(f"\nMetrics statistics:")
            print(f"  Total queries: {stats.get('total_queries', 0)}")
            print(f"  Successful queries: {stats.get('successful_queries', 0)}")
            print(f"  Failed queries: {stats.get('failed_queries', 0)}")
            print(f"  Success rate: {stats.get('success_rate_percent', 0)}%")
            
            # Test recording a metric
            orchestrator.metrics_collector.record_query(
                persona='warehouse_manager',
                agent='test_agent',
                query='test query',
                latency_ms=100.0,
                success=True,
                token_count=50,
                session_id='test-session'
            )
            
            # Get updated stats
            updated_stats = orchestrator.get_metrics_stats()
            print(f"\nAfter recording test metric:")
            print(f"  Total queries: {updated_stats.get('total_queries', 0)}")
            
            # Flush metrics
            orchestrator.flush_metrics()
            print("\n✓ MetricsCollector integration working")
        else:
            print("\n✗ MetricsCollector not initialized")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n✗ MetricsCollector integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_access_controller_integration():
    """Test AccessController integration"""
    print("\n" + "="*60)
    print("Testing AccessController integration...")
    
    try:
        from orchestrator import SupplyChainOrchestrator
        
        orchestrator = SupplyChainOrchestrator()
        
        if orchestrator.access_controller:
            # Test persona authorization
            test_context = {
                'user_id': 'test-user',
                'username': 'test-user',
                'groups': ['warehouse_managers'],
                'persona': 'warehouse_manager'
            }
            
            authorized = orchestrator.access_controller.authorize(
                test_context,
                'warehouse_manager'
            )
            print(f"\nAuthorization test (warehouse_manager with correct group): {authorized}")
            
            # Test unauthorized access
            unauthorized_context = {
                'user_id': 'test-user',
                'username': 'test-user',
                'groups': ['field_engineers'],
                'persona': 'field_engineer'
            }
            
            not_authorized = orchestrator.access_controller.authorize(
                unauthorized_context,
                'warehouse_manager'
            )
            print(f"Authorization test (warehouse_manager with wrong group): {not_authorized}")
            
            # Get accessible tables
            tables = orchestrator.access_controller.get_accessible_tables('warehouse_manager')
            print(f"\nAccessible tables for warehouse_manager: {len(tables)} tables")
            
            # Get accessible tools
            tools = orchestrator.access_controller.get_accessible_tools('warehouse_manager')
            print(f"Accessible tools for warehouse_manager: {tools}")
            
            print("\n✓ AccessController integration working")
        else:
            print("\n✗ AccessController not initialized")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n✗ AccessController integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_executor_integration():
    """Test ToolExecutor integration"""
    print("\n" + "="*60)
    print("Testing ToolExecutor integration...")
    
    try:
        from orchestrator import SupplyChainOrchestrator
        
        orchestrator = SupplyChainOrchestrator()
        
        if orchestrator.tool_executor:
            # Get execution stats
            stats = orchestrator.get_tool_execution_stats()
            print(f"\nTool execution statistics:")
            print(f"  Total executions: {stats.get('total_executions', 0)}")
            print(f"  Success count: {stats.get('success_count', 0)}")
            print(f"  Success rate: {stats.get('success_rate', 0)}%")
            
            print("\n✓ ToolExecutor integration working")
        else:
            print("\n⚠ ToolExecutor not initialized")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ToolExecutor integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("="*60)
    print("ORCHESTRATOR INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        ("Initialization", test_orchestrator_initialization),
        ("AgentRegistry", test_agent_registry_integration),
        ("MetricsCollector", test_metrics_collector_integration),
        ("AccessController", test_access_controller_integration),
        ("ToolExecutor", test_tool_executor_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All integration tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
