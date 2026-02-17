"""
Test Specialized Agents

Tests for Inventory, Logistics, and Supplier agents.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.inventory_agent import InventoryAgent
from agents.logistics_agent import LogisticsAgent
from agents.supplier_agent import SupplierAgent
from aws.bedrock_client import BedrockClient
from aws.lambda_client import LambdaClient


def test_inventory_agent_initialization():
    """Test Inventory Agent initialization."""
    print("Testing Inventory Agent initialization...")
    
    # Mock clients (would use real clients in integration tests)
    bedrock_client = BedrockClient(
        region='us-east-1',
        model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'
    )
    lambda_client = LambdaClient(region='us-east-1')
    
    agent = InventoryAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name='supply-chain-inventory-optimizer'
    )
    
    assert agent.agent_name == "InventoryAgent"
    assert agent.lambda_function_name == 'supply-chain-inventory-optimizer'
    
    # Check available tools
    tools = agent.get_available_tools()
    assert 'calculate_reorder_point' in tools
    assert 'identify_low_stock' in tools
    assert 'forecast_demand' in tools
    assert 'identify_stockout_risk' in tools
    
    print("✓ Inventory Agent initialized successfully")
    print(f"  Available tools: {', '.join(tools)}")


def test_logistics_agent_initialization():
    """Test Logistics Agent initialization."""
    print("\nTesting Logistics Agent initialization...")
    
    bedrock_client = BedrockClient(
        region='us-east-1',
        model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'
    )
    lambda_client = LambdaClient(region='us-east-1')
    
    agent = LogisticsAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name='supply-chain-logistics-optimizer'
    )
    
    assert agent.agent_name == "LogisticsAgent"
    assert agent.lambda_function_name == 'supply-chain-logistics-optimizer'
    
    # Check available tools
    tools = agent.get_available_tools()
    assert 'optimize_delivery_route' in tools
    assert 'check_fulfillment_status' in tools
    assert 'identify_delayed_orders' in tools
    assert 'calculate_warehouse_capacity' in tools
    
    print("✓ Logistics Agent initialized successfully")
    print(f"  Available tools: {', '.join(tools)}")


def test_supplier_agent_initialization():
    """Test Supplier Agent initialization."""
    print("\nTesting Supplier Agent initialization...")
    
    bedrock_client = BedrockClient(
        region='us-east-1',
        model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'
    )
    lambda_client = LambdaClient(region='us-east-1')
    
    agent = SupplierAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name='supply-chain-supplier-analyzer'
    )
    
    assert agent.agent_name == "SupplierAgent"
    assert agent.lambda_function_name == 'supply-chain-supplier-analyzer'
    
    # Check available tools
    tools = agent.get_available_tools()
    assert 'analyze_supplier_performance' in tools
    assert 'compare_supplier_costs' in tools
    assert 'identify_cost_savings' in tools
    assert 'analyze_purchase_trends' in tools
    
    print("✓ Supplier Agent initialized successfully")
    print(f"  Available tools: {', '.join(tools)}")


def test_tool_definitions():
    """Test that tool definitions are properly formatted for Bedrock."""
    print("\nTesting tool definitions format...")
    
    bedrock_client = BedrockClient(
        region='us-east-1',
        model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'
    )
    lambda_client = LambdaClient(region='us-east-1')
    
    # Test Inventory Agent tools
    inventory_agent = InventoryAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name='supply-chain-inventory-optimizer'
    )
    
    for tool_def in inventory_agent.TOOL_DEFINITIONS:
        assert 'toolSpec' in tool_def
        assert 'name' in tool_def['toolSpec']
        assert 'description' in tool_def['toolSpec']
        assert 'inputSchema' in tool_def['toolSpec']
        assert 'json' in tool_def['toolSpec']['inputSchema']
    
    print("✓ Tool definitions are properly formatted")


def test_agent_inheritance():
    """Test that specialized agents inherit from BaseAgent."""
    print("\nTesting agent inheritance...")
    
    bedrock_client = BedrockClient(
        region='us-east-1',
        model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'
    )
    lambda_client = LambdaClient(region='us-east-1')
    
    inventory_agent = InventoryAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name='supply-chain-inventory-optimizer'
    )
    
    # Check that BaseAgent methods are available
    assert hasattr(inventory_agent, 'log_info')
    assert hasattr(inventory_agent, 'log_error')
    assert hasattr(inventory_agent, 'create_success_response')
    assert hasattr(inventory_agent, 'create_error_response')
    assert hasattr(inventory_agent, 'handle_exception')
    
    print("✓ Specialized agents properly inherit from BaseAgent")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Specialized Agents Implementation")
    print("=" * 60)
    
    try:
        test_inventory_agent_initialization()
        test_logistics_agent_initialization()
        test_supplier_agent_initialization()
        test_tool_definitions()
        test_agent_inheritance()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
