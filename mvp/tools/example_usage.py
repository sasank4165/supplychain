"""
Example Usage of Calculation Tools and Tool Registry

This file demonstrates how to use the calculation tools both directly
and through the Bedrock tool calling integration.
"""

from tools.calculation_tools import CalculationTools, Order, Location
from tools.tool_registry import (
    get_tool_registry,
    get_bedrock_tool_config,
    invoke_tool_from_bedrock,
    format_tool_result_for_bedrock
)


def example_direct_usage():
    """Example: Using calculation tools directly"""
    print("=" * 70)
    print("EXAMPLE 1: Direct Tool Usage")
    print("=" * 70)
    
    # Inventory Management
    print("\n1. Calculate Reorder Point:")
    reorder_point = CalculationTools.calculate_reorder_point(
        avg_daily_demand=15.0,
        lead_time_days=5,
        safety_stock=30.0
    )
    print(f"   Product with 15 units/day demand, 5 days lead time, 30 units safety stock")
    print(f"   → Reorder Point: {reorder_point} units")
    
    # Safety Stock
    print("\n2. Calculate Safety Stock:")
    safety_stock = CalculationTools.calculate_safety_stock(
        max_daily_demand=20.0,
        avg_daily_demand=15.0,
        max_lead_time=7,
        avg_lead_time=5
    )
    print(f"   Max demand: 20 units/day, Avg demand: 15 units/day")
    print(f"   Max lead time: 7 days, Avg lead time: 5 days")
    print(f"   → Safety Stock: {safety_stock} units")
    
    # Demand Forecasting
    print("\n3. Forecast Demand:")
    historical = [100, 105, 98, 110, 108, 115, 112, 120, 118, 125]
    forecast = CalculationTools.forecast_demand(
        historical_demand=historical,
        periods=5,
        method="weighted_moving_average",
        window_size=7
    )
    print(f"   Historical demand (last 10 periods): {historical}")
    print(f"   → Forecast (next 5 periods): {forecast}")
    
    # Supplier Score
    print("\n4. Calculate Supplier Score:")
    score = CalculationTools.calculate_supplier_score(
        fill_rate=0.98,
        on_time_rate=0.95,
        quality_rate=0.99,
        cost_competitiveness=0.88
    )
    print(f"   Fill Rate: 98%, On-Time: 95%, Quality: 99%, Cost: 88%")
    print(f"   → Supplier Score: {score:.3f} (out of 1.0)")
    
    # Route Optimization
    print("\n5. Optimize Delivery Route:")
    warehouse = Location(40.7128, -74.0060, "Main Warehouse")
    orders = [
        Order("SO-101", "123 Main St", "Downtown", 40.7589, -73.9851, priority=1),
        Order("SO-102", "456 Oak Ave", "Downtown", 40.7614, -73.9776, priority=3),
        Order("SO-103", "789 Pine Rd", "Uptown", 40.7829, -73.9654, priority=1),
        Order("SO-104", "321 Elm St", "Midtown", 40.7549, -73.9840, priority=2),
    ]
    route = CalculationTools.optimize_route(orders, warehouse)
    print(f"   Orders to deliver: {len(orders)}")
    print(f"   → Optimized sequence: {route.optimized_order}")
    print(f"   → Total distance: {route.total_distance_km} km")
    print(f"   → Estimated time: {route.estimated_time_hours} hours")
    print(f"   → Delivery groups: {route.delivery_groups}")


def example_tool_registry():
    """Example: Using the tool registry"""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 2: Tool Registry Usage")
    print("=" * 70)
    
    # Get registry
    registry = get_tool_registry()
    
    # List available tools
    print("\n1. Available Tools:")
    tools = registry.get_tool_names()
    for i, tool in enumerate(tools, 1):
        print(f"   {i}. {tool}")
    
    # Get tool description
    print("\n2. Tool Description:")
    description = registry.get_tool_description("calculate_reorder_point")
    print(f"   {description}")
    
    # Invoke tool through registry
    print("\n3. Invoke Tool via Registry:")
    result = registry.invoke_tool(
        "calculate_economic_order_quantity",
        {
            "annual_demand": 5000,
            "ordering_cost": 100,
            "holding_cost_per_unit": 5
        }
    )
    print(f"   Tool: calculate_economic_order_quantity")
    print(f"   Parameters: annual_demand=5000, ordering_cost=100, holding_cost=5")
    print(f"   → Result: {result} units")
    
    # Format result
    print("\n4. Format Tool Result:")
    formatted = registry.format_tool_result("calculate_economic_order_quantity", result)
    print(f"   Formatted for LLM: {formatted}")


def example_bedrock_integration():
    """Example: Bedrock tool calling integration"""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 3: Bedrock Integration")
    print("=" * 70)
    
    # Get Bedrock tool configuration
    print("\n1. Get Bedrock Tool Config:")
    config = get_bedrock_tool_config()
    print(f"   Number of tools: {len(config['tools'])}")
    print(f"   First tool: {config['tools'][0]['toolSpec']['name']}")
    
    # Simulate Bedrock tool use block
    print("\n2. Simulate Bedrock Tool Use:")
    simulated_tool_use = {
        "toolUseId": "tooluse_abc123",
        "name": "calculate_days_of_supply",
        "input": {
            "current_inventory": 500,
            "avg_daily_demand": 25
        }
    }
    print(f"   Tool Use Block: {simulated_tool_use}")
    
    # Invoke tool from Bedrock block
    result = invoke_tool_from_bedrock(simulated_tool_use)
    print(f"   → Result: {result} days")
    
    # Format result for Bedrock
    print("\n3. Format Result for Bedrock:")
    tool_result = format_tool_result_for_bedrock(
        tool_use_id="tooluse_abc123",
        tool_name="calculate_days_of_supply",
        result=result
    )
    print(f"   Tool Result Block:")
    print(f"   {tool_result}")


def example_error_handling():
    """Example: Error handling"""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 4: Error Handling")
    print("=" * 70)
    
    # Invalid parameter
    print("\n1. Invalid Parameter (negative value):")
    try:
        CalculationTools.calculate_reorder_point(-10, 7, 20)
    except ValueError as e:
        print(f"   ✓ Caught error: {e}")
    
    # Out of range
    print("\n2. Out of Range (rate > 1.0):")
    try:
        CalculationTools.calculate_supplier_score(1.5, 0.9, 0.98, 0.85)
    except ValueError as e:
        print(f"   ✓ Caught error: {e}")
    
    # Invalid tool name
    print("\n3. Invalid Tool Name:")
    registry = get_tool_registry()
    try:
        registry.invoke_tool("nonexistent_tool", {})
    except ValueError as e:
        print(f"   ✓ Caught error: {e}")
    
    # Missing parameters
    print("\n4. Missing Required Parameters:")
    try:
        registry.invoke_tool("calculate_reorder_point", {"avg_daily_demand": 10})
    except ValueError as e:
        print(f"   ✓ Caught error: {e}")


def example_bedrock_workflow():
    """Example: Complete Bedrock workflow simulation"""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 5: Complete Bedrock Workflow Simulation")
    print("=" * 70)
    
    print("\nScenario: User asks 'What's the reorder point for product X?'")
    print("The agent needs to:")
    print("1. Query database for product data")
    print("2. Use calculation tool to compute reorder point")
    print("3. Return result to user")
    
    # Step 1: Simulated database query results
    print("\n[Step 1] Database Query Results:")
    product_data = {
        "product_code": "PROD-001",
        "product_name": "Widget A",
        "avg_daily_demand": 12.5,
        "lead_time_days": 6,
        "safety_stock": 25.0
    }
    print(f"   Product: {product_data['product_name']}")
    print(f"   Avg Daily Demand: {product_data['avg_daily_demand']}")
    print(f"   Lead Time: {product_data['lead_time_days']} days")
    print(f"   Safety Stock: {product_data['safety_stock']}")
    
    # Step 2: Bedrock decides to use tool
    print("\n[Step 2] Bedrock Tool Use Decision:")
    tool_use = {
        "toolUseId": "tooluse_xyz789",
        "name": "calculate_reorder_point",
        "input": {
            "avg_daily_demand": product_data["avg_daily_demand"],
            "lead_time_days": product_data["lead_time_days"],
            "safety_stock": product_data["safety_stock"]
        }
    }
    print(f"   Tool: {tool_use['name']}")
    print(f"   Parameters: {tool_use['input']}")
    
    # Step 3: Execute tool
    print("\n[Step 3] Execute Tool:")
    result = invoke_tool_from_bedrock(tool_use)
    print(f"   → Reorder Point: {result} units")
    
    # Step 4: Format for Bedrock
    print("\n[Step 4] Format Result for Bedrock:")
    tool_result = format_tool_result_for_bedrock(
        tool_use_id=tool_use["toolUseId"],
        tool_name=tool_use["name"],
        result=result
    )
    print(f"   Tool Result: {tool_result['toolResult']['content'][0]['json']}")
    
    # Step 5: Final response to user
    print("\n[Step 5] Final Response to User:")
    print(f"   'The reorder point for {product_data['product_name']} is {result} units.'")
    print(f"   'This means you should place a new order when inventory reaches {result} units.'")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("CALCULATION TOOLS - EXAMPLE USAGE")
    print("=" * 70)
    
    example_direct_usage()
    example_tool_registry()
    example_bedrock_integration()
    example_error_handling()
    example_bedrock_workflow()
    
    print("\n\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)
    print("\nThese examples demonstrate:")
    print("  ✓ Direct tool usage for calculations")
    print("  ✓ Tool registry for managing tools")
    print("  ✓ Bedrock integration for LLM tool calling")
    print("  ✓ Error handling and validation")
    print("  ✓ Complete workflow simulation")
    print("\nThe tools are ready for integration with agents and orchestrator!")


if __name__ == "__main__":
    import sys
    import os
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    main()
