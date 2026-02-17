"""Simple direct test of the tools"""
import sys
import os

# Add the mvp directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import from tools
from tools.calculation_tools import CalculationTools, Order, Location
from tools.tool_registry import get_tool_registry

print("Testing Calculation Tools...")
print("-" * 60)

# Test 1: Reorder Point
print("\n1. Reorder Point:")
result = CalculationTools.calculate_reorder_point(10.0, 7, 20.0)
print(f"   Result: {result} (expected 90.0)")
assert result == 90.0

# Test 2: Safety Stock
print("\n2. Safety Stock:")
result = CalculationTools.calculate_safety_stock(15.0, 10.0, 10, 7)
print(f"   Result: {result} (expected 80.0)")
assert result == 80.0

# Test 3: Supplier Score
print("\n3. Supplier Score:")
result = CalculationTools.calculate_supplier_score(0.95, 0.90, 0.98, 0.85)
print(f"   Result: {result} (expected 0.921)")
assert result == 0.921

# Test 4: Tool Registry
print("\n4. Tool Registry:")
registry = get_tool_registry()
names = registry.get_tool_names()
print(f"   Number of tools: {len(names)}")
print(f"   Tools: {names}")
assert len(names) >= 8

# Test 5: Invoke via Registry
print("\n5. Invoke via Registry:")
result = registry.invoke_tool(
    "calculate_reorder_point",
    {"avg_daily_demand": 10.0, "lead_time_days": 7, "safety_stock": 20.0}
)
print(f"   Result: {result} (expected 90.0)")
assert result == 90.0

# Test 6: Get Bedrock Config
print("\n6. Bedrock Tool Config:")
from tools.tool_registry import get_bedrock_tool_config
config = get_bedrock_tool_config()
print(f"   Config has 'tools' key: {'tools' in config}")
print(f"   Number of tool definitions: {len(config['tools'])}")
assert "tools" in config
assert len(config["tools"]) >= 8

print("\n" + "=" * 60)
print("ALL TESTS PASSED! ✓")
print("=" * 60)
