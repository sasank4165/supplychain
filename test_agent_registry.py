"""Test script for Agent Registry functionality

This script tests the agent registry and plugin architecture to ensure:
1. Agent classes are discovered correctly
2. Agents are registered from configuration
3. Agents can be retrieved and used
4. Agent capabilities are reported correctly
"""

import sys
from config_manager import ConfigurationManager
from agent_registry import AgentRegistry


def test_agent_registry():
    """Test agent registry functionality"""
    
    print("=" * 70)
    print("Testing Agent Registry and Plugin Architecture")
    print("=" * 70)
    print()
    
    # Test 1: Load configuration
    print("Test 1: Loading configuration...")
    try:
        config = ConfigurationManager(environment='dev')
        print(f"✓ Configuration loaded: {config.environment}")
        print(f"  Region: {config.get('environment.region')}")
        print(f"  Prefix: {config.get('project.prefix')}")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False
    print()
    
    # Test 2: Initialize agent registry
    print("Test 2: Initializing agent registry...")
    try:
        registry = AgentRegistry(config, auto_discover=True)
        print(f"✓ Agent registry initialized: {registry}")
    except Exception as e:
        print(f"✗ Failed to initialize registry: {e}")
        return False
    print()
    
    # Test 3: List available agent classes
    print("Test 3: Listing available agent classes...")
    try:
        available_classes = registry.list_available_agent_classes()
        print(f"✓ Found {len(available_classes)} agent classes:")
        for cls in available_classes:
            print(f"  - {cls}")
    except Exception as e:
        print(f"✗ Failed to list agent classes: {e}")
        return False
    print()
    
    # Test 4: List registered agents
    print("Test 4: Listing registered agents...")
    try:
        registered_agents = registry.list_agents()
        print(f"✓ Registered {len(registered_agents)} agents:")
        for agent_name in registered_agents:
            print(f"  - {agent_name}")
    except Exception as e:
        print(f"✗ Failed to list registered agents: {e}")
        return False
    print()
    
    # Test 5: Get agent capabilities
    print("Test 5: Getting agent capabilities...")
    try:
        for agent_name in registered_agents:
            capabilities = registry.get_agent_capabilities(agent_name)
            print(f"✓ Agent: {agent_name}")
            print(f"  Class: {capabilities.get('class')}")
            print(f"  Persona: {capabilities.get('persona')}")
            print(f"  Model: {capabilities.get('model')}")
            if 'tools' in capabilities:
                print(f"  Tools: {', '.join(capabilities['tools'])}")
            print()
    except Exception as e:
        print(f"✗ Failed to get agent capabilities: {e}")
        return False
    
    # Test 6: Retrieve specific agents
    print("Test 6: Retrieving specific agents...")
    test_agents = ['inventory_optimizer', 'logistics_agent', 'supplier_analyzer']
    for agent_name in test_agents:
        try:
            agent = registry.get_agent(agent_name)
            if agent:
                print(f"✓ Retrieved agent: {agent_name} ({agent.__class__.__name__})")
            else:
                print(f"✗ Agent not found: {agent_name}")
        except Exception as e:
            print(f"✗ Failed to retrieve agent '{agent_name}': {e}")
    print()
    
    # Test 7: Get all capabilities
    print("Test 7: Getting all capabilities...")
    try:
        all_capabilities = registry.get_all_capabilities()
        print(f"✓ Retrieved capabilities for {len(all_capabilities)} agents")
    except Exception as e:
        print(f"✗ Failed to get all capabilities: {e}")
        return False
    print()
    
    print("=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)
    
    return True


def test_orchestrator_integration():
    """Test orchestrator integration with agent registry"""
    
    print()
    print("=" * 70)
    print("Testing Orchestrator Integration with Agent Registry")
    print("=" * 70)
    print()
    
    try:
        from orchestrator import SupplyChainOrchestrator
        
        # Test 1: Initialize orchestrator with config
        print("Test 1: Initializing orchestrator with configuration...")
        config = ConfigurationManager(environment='dev')
        orchestrator = SupplyChainOrchestrator(config=config)
        print(f"✓ Orchestrator initialized")
        print(f"  Agent registry: {orchestrator.agent_registry}")
        print()
        
        # Test 2: Get registered agents info
        print("Test 2: Getting registered agents from orchestrator...")
        agents_info = orchestrator.get_all_registered_agents()
        if 'error' not in agents_info:
            print(f"✓ Found {agents_info['agent_count']} registered agents:")
            for agent_name in agents_info['registered_agents']:
                print(f"  - {agent_name}")
        else:
            print(f"✗ Error: {agents_info['error']}")
        print()
        
        # Test 3: Get capabilities for each persona
        print("Test 3: Getting agent capabilities for each persona...")
        personas = ['warehouse_manager', 'field_engineer', 'procurement_specialist']
        for persona in personas:
            try:
                capabilities = orchestrator.get_agent_capabilities(persona)
                print(f"✓ Persona: {persona}")
                print(f"  SQL Agent: {capabilities['sql_agent']['name']}")
                if 'specialist_agent' in capabilities:
                    print(f"  Specialist: {capabilities['specialist_agent']['name']}")
                    print(f"  Tools: {len(capabilities['specialist_agent']['tools'])}")
                print()
            except Exception as e:
                print(f"✗ Failed for persona '{persona}': {e}")
                print()
        
        print("=" * 70)
        print("Orchestrator integration tests completed!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"✗ Orchestrator integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run tests
    success = test_agent_registry()
    
    if success:
        success = test_orchestrator_integration()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
