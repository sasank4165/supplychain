"""
Example Usage of Specialized Agents

Demonstrates how to use Inventory, Logistics, and Supplier agents.
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
from utils.config_manager import ConfigManager


def example_inventory_agent():
    """Example: Using Inventory Agent."""
    print("=" * 60)
    print("Example: Inventory Agent")
    print("=" * 60)
    
    # Load configuration
    config = ConfigManager('config.yaml')
    
    # Initialize clients
    bedrock_client = BedrockClient(
        region=config.get('aws.region'),
        model_id=config.get('aws.bedrock.model_id'),
        max_tokens=config.get('aws.bedrock.max_tokens'),
        temperature=config.get('aws.bedrock.temperature')
    )
    
    lambda_client = LambdaClient(region=config.get('aws.region'))
    
    # Create Inventory Agent
    inventory_agent = InventoryAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name=config.get('aws.lambda.inventory_function')
    )
    
    print("\n1. AI Orchestration - Natural Language Request")
    print("-" * 60)
    
    # Example 1: Natural language request with AI orchestration
    request = "Show me all products with low stock at warehouse WH-001"
    print(f"Request: {request}")
    
    response = inventory_agent.process_request(request=request)
    
    if response.success:
        print(f"\nResponse: {response.content}")
        print(f"Execution time: {response.execution_time:.2f}s")
        if 'tools_used' in response.metadata:
            print(f"Tools used: {', '.join(response.metadata['tools_used'])}")
    else:
        print(f"Error: {response.error}")
    
    print("\n2. Direct Tool Invocation")
    print("-" * 60)
    
    # Example 2: Direct tool invocation
    print("Tool: identify_low_stock")
    print("Parameters: warehouse_code='WH-001', threshold=1.0")
    
    try:
        result = inventory_agent.invoke_tool_directly(
            tool_name='identify_low_stock',
            parameters={
                'warehouse_code': 'WH-001',
                'threshold': 1.0
            }
        )
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n3. Calculate Reorder Point")
    print("-" * 60)
    
    # Example 3: Calculate reorder point
    print("Tool: calculate_reorder_point")
    print("Parameters: product_code='PROD-001', warehouse_code='WH-001'")
    
    try:
        result = inventory_agent.invoke_tool_directly(
            tool_name='calculate_reorder_point',
            parameters={
                'product_code': 'PROD-001',
                'warehouse_code': 'WH-001'
            }
        )
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"Error: {e}")


def example_logistics_agent():
    """Example: Using Logistics Agent."""
    print("\n\n" + "=" * 60)
    print("Example: Logistics Agent")
    print("=" * 60)
    
    # Load configuration
    config = ConfigManager('config.yaml')
    
    # Initialize clients
    bedrock_client = BedrockClient(
        region=config.get('aws.region'),
        model_id=config.get('aws.bedrock.model_id'),
        max_tokens=config.get('aws.bedrock.max_tokens'),
        temperature=config.get('aws.bedrock.temperature')
    )
    
    lambda_client = LambdaClient(region=config.get('aws.region'))
    
    # Create Logistics Agent
    logistics_agent = LogisticsAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name=config.get('aws.lambda.logistics_function')
    )
    
    print("\n1. AI Orchestration - Natural Language Request")
    print("-" * 60)
    
    # Example 1: Natural language request
    request = "Show me delayed orders from warehouse WH-001 in the last 7 days"
    print(f"Request: {request}")
    
    response = logistics_agent.process_request(request=request)
    
    if response.success:
        print(f"\nResponse: {response.content}")
        print(f"Execution time: {response.execution_time:.2f}s")
    else:
        print(f"Error: {response.error}")
    
    print("\n2. Direct Tool Invocation - Identify Delayed Orders")
    print("-" * 60)
    
    # Example 2: Direct tool invocation
    print("Tool: identify_delayed_orders")
    print("Parameters: warehouse_code='WH-001', days=7")
    
    try:
        result = logistics_agent.invoke_tool_directly(
            tool_name='identify_delayed_orders',
            parameters={
                'warehouse_code': 'WH-001',
                'days': 7
            }
        )
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n3. Optimize Delivery Route")
    print("-" * 60)
    
    # Example 3: Optimize delivery route
    print("Tool: optimize_delivery_route")
    print("Parameters: order_ids=['SO-001', 'SO-002', 'SO-003'], warehouse_code='WH-001'")
    
    try:
        result = logistics_agent.invoke_tool_directly(
            tool_name='optimize_delivery_route',
            parameters={
                'order_ids': ['SO-001', 'SO-002', 'SO-003'],
                'warehouse_code': 'WH-001'
            }
        )
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"Error: {e}")


def example_supplier_agent():
    """Example: Using Supplier Agent."""
    print("\n\n" + "=" * 60)
    print("Example: Supplier Agent")
    print("=" * 60)
    
    # Load configuration
    config = ConfigManager('config.yaml')
    
    # Initialize clients
    bedrock_client = BedrockClient(
        region=config.get('aws.region'),
        model_id=config.get('aws.bedrock.model_id'),
        max_tokens=config.get('aws.bedrock.max_tokens'),
        temperature=config.get('aws.bedrock.temperature')
    )
    
    lambda_client = LambdaClient(region=config.get('aws.region'))
    
    # Create Supplier Agent
    supplier_agent = SupplierAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name=config.get('aws.lambda.supplier_function')
    )
    
    print("\n1. AI Orchestration - Natural Language Request")
    print("-" * 60)
    
    # Example 1: Natural language request
    request = "Analyze the performance of supplier SUP-001 over the last 90 days"
    print(f"Request: {request}")
    
    response = supplier_agent.process_request(request=request)
    
    if response.success:
        print(f"\nResponse: {response.content}")
        print(f"Execution time: {response.execution_time:.2f}s")
    else:
        print(f"Error: {response.error}")
    
    print("\n2. Direct Tool Invocation - Analyze Performance")
    print("-" * 60)
    
    # Example 2: Direct tool invocation
    print("Tool: analyze_supplier_performance")
    print("Parameters: supplier_code='SUP-001', days=90")
    
    try:
        result = supplier_agent.invoke_tool_directly(
            tool_name='analyze_supplier_performance',
            parameters={
                'supplier_code': 'SUP-001',
                'days': 90
            }
        )
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n3. Compare Supplier Costs")
    print("-" * 60)
    
    # Example 3: Compare costs
    print("Tool: compare_supplier_costs")
    print("Parameters: product_group='Electronics', suppliers=['SUP-001', 'SUP-002']")
    
    try:
        result = supplier_agent.invoke_tool_directly(
            tool_name='compare_supplier_costs',
            parameters={
                'product_group': 'Electronics',
                'suppliers': ['SUP-001', 'SUP-002']
            }
        )
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"Error: {e}")


def example_conversation_context():
    """Example: Using conversation context for follow-up questions."""
    print("\n\n" + "=" * 60)
    print("Example: Conversation Context")
    print("=" * 60)
    
    # Load configuration
    config = ConfigManager('config.yaml')
    
    # Initialize clients
    bedrock_client = BedrockClient(
        region=config.get('aws.region'),
        model_id=config.get('aws.bedrock.model_id'),
        max_tokens=config.get('aws.bedrock.max_tokens'),
        temperature=config.get('aws.bedrock.temperature')
    )
    
    lambda_client = LambdaClient(region=config.get('aws.region'))
    
    # Create Inventory Agent
    inventory_agent = InventoryAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name=config.get('aws.lambda.inventory_function')
    )
    
    # First request
    print("\n1. Initial Request")
    print("-" * 60)
    request1 = "Show me low stock products at WH-001"
    print(f"Request: {request1}")
    
    response1 = inventory_agent.process_request(request=request1)
    
    if response1.success:
        print(f"Response: {response1.content[:200]}...")
    
    # Build context
    context = {
        "history": [
            {
                "query": request1,
                "response": response1.content
            }
        ]
    }
    
    # Follow-up request with context
    print("\n2. Follow-up Request (with context)")
    print("-" * 60)
    request2 = "Calculate reorder points for those products"
    print(f"Request: {request2}")
    
    response2 = inventory_agent.process_request(
        request=request2,
        context=context
    )
    
    if response2.success:
        print(f"Response: {response2.content[:200]}...")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Specialized Agents - Example Usage")
    print("=" * 60)
    print("\nNote: These examples require:")
    print("- AWS credentials configured")
    print("- Lambda functions deployed")
    print("- Redshift Serverless running with sample data")
    print("- config.yaml properly configured")
    print("\n" + "=" * 60)
    
    try:
        # Run examples
        example_inventory_agent()
        example_logistics_agent()
        example_supplier_agent()
        example_conversation_context()
        
        print("\n\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
