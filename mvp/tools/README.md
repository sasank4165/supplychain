# Calculation Tools Module

This module provides Python calculation functions for supply chain business metrics and a registry for integrating these tools with Amazon Bedrock.

## Overview

The tools module consists of two main components:

1. **CalculationTools** (`calculation_tools.py`): Python functions for business calculations
2. **ToolRegistry** (`tool_registry.py`): Registry for Bedrock tool calling integration

## Available Tools

### Inventory Management Tools

#### 1. calculate_reorder_point
Calculate the optimal reorder point for a product.

```python
from mvp.tools import CalculationTools

result = CalculationTools.calculate_reorder_point(
    avg_daily_demand=10.0,
    lead_time_days=7,
    safety_stock=20.0
)
# Result: 90.0
```

#### 2. calculate_safety_stock
Calculate safety stock to buffer against variability.

```python
result = CalculationTools.calculate_safety_stock(
    max_daily_demand=15.0,
    avg_daily_demand=10.0,
    max_lead_time=10,
    avg_lead_time=7
)
# Result: 80.0
```

#### 3. calculate_economic_order_quantity
Calculate EOQ for optimal order sizing.

```python
result = CalculationTools.calculate_economic_order_quantity(
    annual_demand=1000,
    ordering_cost=50,
    holding_cost_per_unit=2
)
# Result: 223.61
```

#### 4. calculate_inventory_turnover
Calculate inventory turnover ratio.

```python
result = CalculationTools.calculate_inventory_turnover(
    cost_of_goods_sold=500000,
    average_inventory=50000
)
# Result: 10.0
```

#### 5. calculate_days_of_supply
Calculate how many days current inventory will last.

```python
result = CalculationTools.calculate_days_of_supply(
    current_inventory=100,
    avg_daily_demand=10
)
# Result: 10.0
```

### Forecasting Tools

#### 6. forecast_demand
Forecast future demand using historical data.

```python
historical = [10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 13.0]
result = CalculationTools.forecast_demand(
    historical_demand=historical,
    periods=3,
    method="moving_average",
    window_size=7
)
# Result: [12.14, 12.14, 12.14]
```

Supported methods:
- `moving_average`: Simple moving average
- `weighted_moving_average`: Recent data weighted more heavily
- `exponential_smoothing`: Exponential smoothing (alpha=0.3)

### Logistics Tools

#### 7. optimize_route
Optimize delivery route by grouping orders and prioritizing urgent deliveries.

```python
from mvp.tools import Order, Location

warehouse = Location(40.7128, -74.0060, "Warehouse A")
orders = [
    Order("SO-001", "123 Main St", "Downtown", 40.7589, -73.9851, priority=1),
    Order("SO-002", "456 Oak Ave", "Downtown", 40.7614, -73.9776, priority=3),
]

result = CalculationTools.optimize_route(orders, warehouse)
# Result: RouteOptimization with optimized_order, distance, time, groups
```

### Supplier Analysis Tools

#### 8. calculate_supplier_score
Calculate weighted supplier performance score.

```python
result = CalculationTools.calculate_supplier_score(
    fill_rate=0.95,
    on_time_rate=0.90,
    quality_rate=0.98,
    cost_competitiveness=0.85
)
# Result: 0.921
```

Weights:
- Fill Rate: 30%
- On-Time Rate: 30%
- Quality Rate: 20%
- Cost Competitiveness: 20%

## Bedrock Integration

### Using with Bedrock Converse API

```python
from mvp.tools import get_bedrock_tool_config, invoke_tool_from_bedrock, format_tool_result_for_bedrock
import boto3

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Get tool configuration
tool_config = get_bedrock_tool_config()

# Make request with tools
response = bedrock.converse(
    modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
    messages=[
        {
            "role": "user",
            "content": [{"text": "Calculate the reorder point for a product with 10 units daily demand, 7 days lead time, and 20 units safety stock"}]
        }
    ],
    toolConfig=tool_config
)

# Check if model wants to use a tool
if response['stopReason'] == 'tool_use':
    for content in response['output']['message']['content']:
        if 'toolUse' in content:
            tool_use = content['toolUse']
            
            # Invoke the tool
            result = invoke_tool_from_bedrock(tool_use)
            
            # Format result for Bedrock
            tool_result = format_tool_result_for_bedrock(
                tool_use['toolUseId'],
                tool_use['name'],
                result
            )
            
            # Send result back to Bedrock
            # ... continue conversation
```

### Tool Registry API

```python
from mvp.tools import get_tool_registry

# Get registry instance
registry = get_tool_registry()

# List available tools
tool_names = registry.get_tool_names()
print(tool_names)

# Get tool definitions for Bedrock
definitions = registry.get_tool_definitions()

# Invoke a tool directly
result = registry.invoke_tool(
    "calculate_reorder_point",
    {
        "avg_daily_demand": 10.0,
        "lead_time_days": 7,
        "safety_stock": 20.0
    }
)

# Format result for display
formatted = registry.format_tool_result("calculate_reorder_point", result)
```

## Testing

Run the simple test to verify all tools work:

```bash
cd mvp/tools
python simple_test.py
```

Run full test suite with pytest:

```bash
python -m pytest mvp/tools/test_tools.py -v
```

## Error Handling

All calculation tools validate inputs and raise `ValueError` for invalid parameters:

```python
try:
    result = CalculationTools.calculate_reorder_point(-10, 7, 20)
except ValueError as e:
    print(f"Error: {e}")
    # Output: Error: All parameters must be non-negative
```

## Integration with Agents

These tools are designed to be invoked by:

1. **SQL Agents**: For calculations that complement SQL queries
2. **Specialized Agents**: For domain-specific optimizations
3. **Orchestrator**: For hybrid queries requiring both data and calculations

Example agent integration:

```python
from mvp.tools import get_tool_registry
from mvp.aws import BedrockClient

class InventoryAgent:
    def __init__(self):
        self.bedrock = BedrockClient()
        self.tool_registry = get_tool_registry()
    
    def process_request(self, user_query):
        # Get tool config
        tool_config = get_bedrock_tool_config()
        
        # Send to Bedrock with tools
        response = self.bedrock.converse(
            messages=[{"role": "user", "content": [{"text": user_query}]}],
            toolConfig=tool_config
        )
        
        # Handle tool use
        # ... implementation
```

## Performance Considerations

- All calculations are performed in-memory with O(1) or O(n) complexity
- Route optimization uses a simplified heuristic (O(n log n))
- For production, consider caching frequently used calculations
- Forecast methods are lightweight and suitable for real-time use

## Future Enhancements

Potential additions:
- Advanced forecasting methods (ARIMA, Prophet)
- Integration with external routing APIs (Google Maps, HERE)
- Multi-objective optimization for route planning
- Machine learning-based demand forecasting
- Supplier risk scoring with external data

## References

- [Amazon Bedrock Tool Use Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html)
- [Inventory Management Formulas](https://en.wikipedia.org/wiki/Reorder_point)
- [Economic Order Quantity](https://en.wikipedia.org/wiki/Economic_order_quantity)
