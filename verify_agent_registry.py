"""Simple verification script for Agent Registry"""

print("Starting Agent Registry verification...")
print()

# Test 1: Import modules
print("1. Testing imports...")
try:
    from config_manager import ConfigurationManager
    print("   ✓ ConfigurationManager imported")
except Exception as e:
    print(f"   ✗ Failed to import ConfigurationManager: {e}")
    exit(1)

try:
    from agent_registry import AgentRegistry
    print("   ✓ AgentRegistry imported")
except Exception as e:
    print(f"   ✗ Failed to import AgentRegistry: {e}")
    exit(1)

try:
    from agents import BaseAgent, SQLAgent, InventoryOptimizerAgent
    print("   ✓ Agent classes imported")
except Exception as e:
    print(f"   ✗ Failed to import agent classes: {e}")
    exit(1)

print()

# Test 2: Load configuration
print("2. Loading configuration...")
try:
    config = ConfigurationManager(environment='dev')
    print(f"   ✓ Configuration loaded for environment: {config.environment}")
    print(f"   ✓ Region: {config.get('environment.region')}")
    print(f"   ✓ Project prefix: {config.get('project.prefix')}")
except Exception as e:
    print(f"   ✗ Failed to load configuration: {e}")
    exit(1)

print()

# Test 3: Initialize registry
print("3. Initializing Agent Registry...")
try:
    registry = AgentRegistry(config, auto_discover=True)
    print(f"   ✓ Registry initialized: {registry}")
    print(f"   ✓ Registered agents: {len(registry)}")
except Exception as e:
    print(f"   ✗ Failed to initialize registry: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()

# Test 4: List agents
print("4. Listing registered agents...")
try:
    agents = registry.list_agents()
    print(f"   ✓ Found {len(agents)} agents:")
    for agent_name in agents:
        print(f"      - {agent_name}")
except Exception as e:
    print(f"   ✗ Failed to list agents: {e}")
    exit(1)

print()

# Test 5: Get agent capabilities
print("5. Getting agent capabilities...")
try:
    for agent_name in agents[:3]:  # Test first 3 agents
        caps = registry.get_agent_capabilities(agent_name)
        print(f"   ✓ {agent_name}:")
        print(f"      Class: {caps.get('class')}")
        print(f"      Model: {caps.get('model')}")
except Exception as e:
    print(f"   ✗ Failed to get capabilities: {e}")
    exit(1)

print()

# Test 6: Test orchestrator
print("6. Testing orchestrator integration...")
try:
    from orchestrator import SupplyChainOrchestrator
    orch = SupplyChainOrchestrator(config=config)
    print(f"   ✓ Orchestrator initialized")
    print(f"   ✓ Agent registry available: {orch.agent_registry is not None}")
    
    # Get registered agents info
    info = orch.get_all_registered_agents()
    if 'error' not in info:
        print(f"   ✓ Orchestrator has {info['agent_count']} registered agents")
    else:
        print(f"   ✗ Error getting agents: {info['error']}")
except Exception as e:
    print(f"   ✗ Failed orchestrator test: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("=" * 60)
print("✓ All verification tests passed!")
print("=" * 60)
