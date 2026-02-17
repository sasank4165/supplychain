"""
Simple verification script for calculation tools and tool registry.
Run with: python -m mvp.tools.verify_tools
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mvp.tools.calculation_tools import CalculationTools, Order, Location
from mvp.tools.tool_registry import get_tool_registry, get_bedrock_tool_config


def test_calculation_tools():
    """Test all calculation tools"""
    print("Testing Calculation Tools...")
    print("-" * 60)
    
    # Test 1: Reorder Point
    print("\n1. Testing calculate_reorder_point:")
    result = CalculationTools.calculate_reorder_point(10.0, 7, 20.0)
    print(f"   Input: avg_daily_demand=10.0, lead_time_days=7, safety_stock=20.0")
    print(f"   Result: {result}")
    assert result == 90.0, f"Expected 90.0, got {result}"
    print("   ✓ PASSED")
    
    # Test 2: Safety Stock
    print("\n2. Testing calculate_safety_stock:")
    result = CalculationTools.calculate_safety_stock(15.0, 10.0, 10, 7)
    print(f"   Input: max_daily_demand=15.0, avg_daily_demand=10.0, max_lead_time=10, avg_lead_time=7")
    print(f"   Result: {result}")
    assert result == 80.0, f"Expected 80.0, got {result}"
    print("   ✓ PASSED")
    
    # Test 3: Supplier Score
    print("\n3. Testing calculate_supplier_score:")
    result = CalculationTools.calculate_supplier_score(0.95, 0.90, 0.98, 0.85)
    print(f"   Input: fill_rate=0.95, on_time_rate=0.90, quality_rate=0.98, cost_competitiveness=0.85")
    print(f"   Result: {result}")
    assert result == 0.916, f"Expected 0.916, got {result}"
    print("   ✓ PASSED")
    
    # Test 4: Demand Forecast
    print("\n4. Testing forecast_demand:")
    historical = [10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 13.0]
    result = CalculationTools.forecast_demand(historical, 3, "moving_average", 7)
    print(f"   Input: historical={historical}, periods=3, method='moving_average'")
    print(f"   Result: {result}")
    assert len(result) == 3, f"Expected 3 periods, got {len(result)}"
    print("   ✓ PASSED")
    
    # Test 5: Route Optimization
    print("\n5. Testing optimize_route:")
    warehouse = Location(40.7128, -74.0060, "Warehouse A")
    orders = [
        Order("SO-001", "123 Main St", "Downtown", 40.7589, -73.9851, 1),
        Order("SO-002", "456 Oak Ave", "Downtown", 40.7614, -73.9776, 3),
        Order("SO-003", "789 Pine Rd", "Uptown", 40.7829, -73.9654, 1)
    ]
    result = CalculationTools.optimize_route(orders, warehouse)
    print(f"   Input: 3 orders (2 Downtown, 1 Uptown)")
    print(f"   Optimized Order: {result.optimized_order}")
    print(f"   Total Distance: {result.total_distance_km} km")
    print(f"   Estimated Time: {result.estimated_time_hours} hours")
    print(f"   Delivery Groups: {result.delivery_groups}")
    assert len(result.optimized_order) == 3, f"Expected 3 orders, got {len(result.optimized_order)}"
    print("   ✓ PASSED")
    
    # Test 6: Economic Order Quantity
    print("\n6. Testing calculate_economic_order_quantity:")
    result = CalculationTools.calculate_economic_order_quantity(1000, 50, 2)
    print(f"   Input: annual_demand=1000, ordering_cost=50, holding_cost_per_unit=2")
    print(f"   Result: {result}")
    assert result == 223.61, f"Expected 223.61, got {result}"
    print("   ✓ PASSED")
    
    # Test 7: Inventory Turnover
    print("\n7. Testing calculate_inventory_turnover:")
    result = CalculationTools.calculate_inventory_turnover(500000, 50000)
    print(f"   Input: cost_of_goods_sold=500000, average_inventory=50000")
    print(f"   Result: {result}")
    assert result == 10.0, f"Expected 10.0, got {result}"
    print("   ✓ PASSED")
    
    # Test 8: Days of Supply
    print("\n8. Testing calculate_days_of_supply:")
    result = CalculationTools.calculate_days_of_supply(100, 10)
    print(f"   Input: current_inventory=100, avg_daily_demand=10")
    print(f"   Result: {result}")
    assert result == 10.0, f"Expected 10.0, got {result}"
    print("   ✓ PASSED")
    
    print("\n" + "=" * 60)
    print("All Calculation Tools Tests PASSED! ✓")
    print("=" * 60)


def test_tool_registry():
    """Test tool registry"""
    print("\n\nTesting Tool Registry...")
    print("-" * 60)
    
    # Test 1: Get Registry
    print("\n1. Testing get_tool_registry:")
    registry = get_tool_registry()
    print(f"   Registry instance: {type(registry).__name__}")
    print("   ✓ PASSED")
    
    # Test 2: Get Tool Names
    print("\n2. Testing get_tool_names:")
    names = registry.get_tool_names()
    print(f"   Number of tools: {len(names)}")
    print(f"   Tool names: {', '.join(names[:3])}...")
    assert len(names) >= 8, f"Expected at least 8 tools, got {len(names)}"
    print("   ✓ PASSED")
    
    # Test 3: Get Tool Definitions
    print("\n3. Testing get_tool_definitions:")
    definitions = registry.get_tool_definitions()
    print(f"   Number of definitions: {len(definitions)}")
    first_def = definitions[0]
    print(f"   First tool: {first_def['toolSpec']['name']}")
    assert "toolSpec" in first_def, "Missing toolSpec"
    assert "name" in first_def["toolSpec"], "Missing name"
    assert "description" in first_def["toolSpec"], "Missing description"
    assert "inputSchema" in first_def["toolSpec"], "Missing inputSchema"
    print("   ✓ PASSED")
    
    # Test 4: Invoke Tool
    print("\n4. Testing invoke_tool:")
    result = registry.invoke_tool(
        "calculate_reorder_point",
        {"avg_daily_demand": 10.0, "lead_time_days": 7, "safety_stock": 20.0}
    )
    print(f"   Tool: calculate_reorder_point")
    print(f"   Result: {result}")
    assert result == 90.0, f"Expected 90.0, got {result}"
    print("   ✓ PASSED")
    
    # Test 5: Format Tool Result
    print("\n5. Testing format_tool_result:")
    formatted = registry.format_tool_result("calculate_reorder_point", 90.0)
    print(f"   Formatted result: {formatted}")
    assert "90.0" in formatted, f"Expected '90.0' in result"
    print("   ✓ PASSED")
    
    # Test 6: Get Bedrock Tool Config
    print("\n6. Testing get_bedrock_tool_config:")
    config = get_bedrock_tool_config()
    print(f"   Config keys: {list(config.keys())}")
    print(f"   Number of tools in config: {len(config['tools'])}")
    assert "tools" in config, "Missing 'tools' key"
    assert len(config["tools"]) >= 8, f"Expected at least 8 tools"
    print("   ✓ PASSED")
    
    # Test 7: Get Tool Description
    print("\n7. Testing get_tool_description:")
    description = registry.get_tool_description("calculate_reorder_point")
    print(f"   Description: {description[:80]}...")
    assert description is not None, "Description should not be None"
    assert "reorder point" in description.lower(), "Description should mention reorder point"
    print("   ✓ PASSED")
    
    print("\n" + "=" * 60)
    print("All Tool Registry Tests PASSED! ✓")
    print("=" * 60)


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("VERIFICATION SCRIPT FOR CALCULATION TOOLS")
    print("=" * 60)
    
    try:
        test_calculation_tools()
        test_tool_registry()
        
        print("\n\n" + "=" * 60)
        print("ALL TESTS PASSED SUCCESSFULLY! ✓✓✓")
        print("=" * 60)
        print("\nThe calculation tools and tool registry are working correctly.")
        print("They are ready to be integrated with Bedrock agents.")
        
    except AssertionError as e:
        print(f"\n\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
