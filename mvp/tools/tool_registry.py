"""
Tool Registry for Bedrock Tool Calling

This module registers Python calculation tools with Bedrock-compatible definitions,
enabling the LLM to invoke these tools through the Bedrock Converse API.
"""

from typing import Dict, List, Any, Callable, Optional
import json
from .calculation_tools import CalculationTools, Order, Location, RouteOptimization


class ToolRegistry:
    """
    Registry for managing calculation tools and their Bedrock-compatible definitions.
    
    This class provides:
    1. Tool definitions in Bedrock's expected format
    2. Tool invocation logic
    3. Result formatting for LLM consumption
    """
    
    def __init__(self):
        """Initialize the tool registry with all available tools."""
        self.tools = CalculationTools()
        self._tool_map = self._build_tool_map()
    
    def _build_tool_map(self) -> Dict[str, Callable]:
        """
        Build a mapping of tool names to their implementation functions.
        
        Returns:
            Dict mapping tool names to callable functions
        """
        return {
            "calculate_reorder_point": self.tools.calculate_reorder_point,
            "calculate_safety_stock": self.tools.calculate_safety_stock,
            "calculate_supplier_score": self.tools.calculate_supplier_score,
            "forecast_demand": self.tools.forecast_demand,
            "optimize_route": self._optimize_route_wrapper,
            "calculate_economic_order_quantity": self.tools.calculate_economic_order_quantity,
            "calculate_inventory_turnover": self.tools.calculate_inventory_turnover,
            "calculate_days_of_supply": self.tools.calculate_days_of_supply,
        }
    
    def _optimize_route_wrapper(self, orders_data: List[Dict], warehouse_data: Dict) -> Dict:
        """
        Wrapper for optimize_route to handle JSON serialization.
        
        Args:
            orders_data: List of order dictionaries
            warehouse_data: Warehouse location dictionary
        
        Returns:
            Dict representation of RouteOptimization
        """
        # Convert dictionaries to objects
        orders = [
            Order(
                order_id=o["order_id"],
                delivery_address=o["delivery_address"],
                delivery_area=o["delivery_area"],
                latitude=o["latitude"],
                longitude=o["longitude"],
                priority=o.get("priority", 1)
            )
            for o in orders_data
        ]
        
        warehouse = Location(
            latitude=warehouse_data["latitude"],
            longitude=warehouse_data["longitude"],
            address=warehouse_data["address"]
        )
        
        # Call the actual function
        result = self.tools.optimize_route(orders, warehouse)
        
        # Convert result to dictionary
        return {
            "optimized_order": result.optimized_order,
            "total_distance_km": result.total_distance_km,
            "estimated_time_hours": result.estimated_time_hours,
            "delivery_groups": result.delivery_groups
        }
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get Bedrock-compatible tool definitions for all registered tools.
        
        Returns:
            List of tool definition dictionaries in Bedrock format
        """
        return [
            {
                "toolSpec": {
                    "name": "calculate_reorder_point",
                    "description": "Calculate the optimal reorder point for a product based on average daily demand, lead time, and safety stock. Use this when determining when to reorder inventory.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "avg_daily_demand": {
                                    "type": "number",
                                    "description": "Average daily demand for the product in units per day"
                                },
                                "lead_time_days": {
                                    "type": "integer",
                                    "description": "Lead time from order placement to delivery in days"
                                },
                                "safety_stock": {
                                    "type": "number",
                                    "description": "Safety stock quantity in units to buffer against variability"
                                }
                            },
                            "required": ["avg_daily_demand", "lead_time_days", "safety_stock"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "calculate_safety_stock",
                    "description": "Calculate the safety stock quantity needed to buffer against demand and lead time variability. Use this to determine appropriate safety stock levels.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "max_daily_demand": {
                                    "type": "number",
                                    "description": "Maximum observed daily demand in units per day"
                                },
                                "avg_daily_demand": {
                                    "type": "number",
                                    "description": "Average daily demand in units per day"
                                },
                                "max_lead_time": {
                                    "type": "integer",
                                    "description": "Maximum observed lead time in days"
                                },
                                "avg_lead_time": {
                                    "type": "integer",
                                    "description": "Average lead time in days"
                                }
                            },
                            "required": ["max_daily_demand", "avg_daily_demand", "max_lead_time", "avg_lead_time"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "calculate_supplier_score",
                    "description": "Calculate a weighted supplier performance score based on fill rate, on-time delivery, quality, and cost competitiveness. Returns a score from 0.0 to 1.0.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "fill_rate": {
                                    "type": "number",
                                    "description": "Percentage of orders fulfilled completely, as a decimal from 0.0 to 1.0"
                                },
                                "on_time_rate": {
                                    "type": "number",
                                    "description": "Percentage of orders delivered on time, as a decimal from 0.0 to 1.0"
                                },
                                "quality_rate": {
                                    "type": "number",
                                    "description": "Percentage of products meeting quality standards, as a decimal from 0.0 to 1.0"
                                },
                                "cost_competitiveness": {
                                    "type": "number",
                                    "description": "Cost competitiveness score from 0.0 to 1.0, where 1.0 is most competitive"
                                }
                            },
                            "required": ["fill_rate", "on_time_rate", "quality_rate", "cost_competitiveness"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "forecast_demand",
                    "description": "Forecast future demand using historical data and specified forecasting method. Supports moving average, weighted moving average, and exponential smoothing.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "historical_demand": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "description": "List of historical demand values, with most recent values last"
                                },
                                "periods": {
                                    "type": "integer",
                                    "description": "Number of future periods to forecast"
                                },
                                "method": {
                                    "type": "string",
                                    "enum": ["moving_average", "weighted_moving_average", "exponential_smoothing"],
                                    "description": "Forecasting method to use",
                                    "default": "moving_average"
                                },
                                "window_size": {
                                    "type": "integer",
                                    "description": "Window size for moving average methods",
                                    "default": 7
                                }
                            },
                            "required": ["historical_demand", "periods"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "optimize_route",
                    "description": "Optimize delivery route by grouping orders by delivery area and prioritizing urgent orders. Returns optimized order sequence and estimates.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "orders_data": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "order_id": {"type": "string"},
                                            "delivery_address": {"type": "string"},
                                            "delivery_area": {"type": "string"},
                                            "latitude": {"type": "number"},
                                            "longitude": {"type": "number"},
                                            "priority": {"type": "integer", "default": 1}
                                        },
                                        "required": ["order_id", "delivery_address", "delivery_area", "latitude", "longitude"]
                                    },
                                    "description": "List of orders to deliver"
                                },
                                "warehouse_data": {
                                    "type": "object",
                                    "properties": {
                                        "latitude": {"type": "number"},
                                        "longitude": {"type": "number"},
                                        "address": {"type": "string"}
                                    },
                                    "required": ["latitude", "longitude", "address"],
                                    "description": "Warehouse location (starting point)"
                                }
                            },
                            "required": ["orders_data", "warehouse_data"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "calculate_economic_order_quantity",
                    "description": "Calculate the Economic Order Quantity (EOQ) for optimal order sizing that minimizes total ordering and holding costs.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "annual_demand": {
                                    "type": "number",
                                    "description": "Annual demand for the product in units per year"
                                },
                                "ordering_cost": {
                                    "type": "number",
                                    "description": "Fixed cost per order in currency units"
                                },
                                "holding_cost_per_unit": {
                                    "type": "number",
                                    "description": "Annual cost to hold one unit in inventory in currency units"
                                }
                            },
                            "required": ["annual_demand", "ordering_cost", "holding_cost_per_unit"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "calculate_inventory_turnover",
                    "description": "Calculate inventory turnover ratio, which measures how many times inventory is sold and replaced over a period. Higher values indicate efficient inventory management.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "cost_of_goods_sold": {
                                    "type": "number",
                                    "description": "Total cost of goods sold during the period"
                                },
                                "average_inventory": {
                                    "type": "number",
                                    "description": "Average inventory value during the period"
                                }
                            },
                            "required": ["cost_of_goods_sold", "average_inventory"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "calculate_days_of_supply",
                    "description": "Calculate how many days the current inventory will last at the current consumption rate. Useful for inventory planning.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "current_inventory": {
                                    "type": "number",
                                    "description": "Current inventory quantity in units"
                                },
                                "avg_daily_demand": {
                                    "type": "number",
                                    "description": "Average daily demand in units per day"
                                }
                            },
                            "required": ["current_inventory", "avg_daily_demand"]
                        }
                    }
                }
            }
        ]
    
    def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Invoke a tool by name with the provided parameters.
        
        Args:
            tool_name: Name of the tool to invoke
            parameters: Dictionary of parameters for the tool
        
        Returns:
            Result of the tool invocation
        
        Raises:
            ValueError: If tool name is not found or parameters are invalid
        """
        if tool_name not in self._tool_map:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool_func = self._tool_map[tool_name]
        
        try:
            result = tool_func(**parameters)
            return result
        except TypeError as e:
            raise ValueError(f"Invalid parameters for tool {tool_name}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error executing tool {tool_name}: {str(e)}")
    
    def format_tool_result(self, tool_name: str, result: Any) -> str:
        """
        Format tool result for LLM consumption.
        
        Args:
            tool_name: Name of the tool that was invoked
            result: Result from the tool invocation
        
        Returns:
            Formatted string representation of the result
        """
        if isinstance(result, (int, float)):
            return f"{result}"
        elif isinstance(result, list):
            return json.dumps(result, indent=2)
        elif isinstance(result, dict):
            return json.dumps(result, indent=2)
        else:
            return str(result)
    
    def get_tool_names(self) -> List[str]:
        """
        Get list of all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tool_map.keys())
    
    def get_tool_description(self, tool_name: str) -> Optional[str]:
        """
        Get description for a specific tool.
        
        Args:
            tool_name: Name of the tool
        
        Returns:
            Tool description or None if tool not found
        """
        for tool_def in self.get_tool_definitions():
            if tool_def["toolSpec"]["name"] == tool_name:
                return tool_def["toolSpec"]["description"]
        return None


# Singleton instance for easy access
_registry_instance = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the singleton ToolRegistry instance.
    
    Returns:
        ToolRegistry instance
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    return _registry_instance


# Convenience functions for common operations

def get_bedrock_tool_config() -> Dict[str, Any]:
    """
    Get the complete tool configuration for Bedrock Converse API.
    
    This returns the toolConfig parameter that should be passed to
    the Bedrock converse() or converse_stream() API calls.
    
    Returns:
        Dictionary with tools configuration for Bedrock
    
    Example:
        >>> config = get_bedrock_tool_config()
        >>> response = bedrock_client.converse(
        ...     modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
        ...     messages=[...],
        ...     toolConfig=config
        ... )
    """
    registry = get_tool_registry()
    return {
        "tools": registry.get_tool_definitions()
    }


def invoke_tool_from_bedrock(tool_use_block: Dict[str, Any]) -> Any:
    """
    Invoke a tool from a Bedrock tool use block.
    
    This is a convenience function for handling tool use blocks returned
    by Bedrock in the response.
    
    Args:
        tool_use_block: The toolUse block from Bedrock response
    
    Returns:
        Result of the tool invocation
    
    Example:
        >>> tool_use = {
        ...     "toolUseId": "tooluse_123",
        ...     "name": "calculate_reorder_point",
        ...     "input": {"avg_daily_demand": 10, "lead_time_days": 7, "safety_stock": 20}
        ... }
        >>> result = invoke_tool_from_bedrock(tool_use)
        >>> print(result)
        90.0
    """
    registry = get_tool_registry()
    tool_name = tool_use_block.get("name")
    parameters = tool_use_block.get("input", {})
    
    return registry.invoke_tool(tool_name, parameters)


def format_tool_result_for_bedrock(
    tool_use_id: str,
    tool_name: str,
    result: Any,
    is_error: bool = False
) -> Dict[str, Any]:
    """
    Format tool result for Bedrock tool result message.
    
    Args:
        tool_use_id: The toolUseId from the tool use block
        tool_name: Name of the tool that was invoked
        result: Result from the tool invocation (or error message if is_error=True)
        is_error: Whether this is an error result
    
    Returns:
        Dictionary formatted as a Bedrock tool result content block
    
    Example:
        >>> result_block = format_tool_result_for_bedrock(
        ...     "tooluse_123",
        ...     "calculate_reorder_point",
        ...     90.0
        ... )
        >>> # Use in message to Bedrock
        >>> message = {
        ...     "role": "user",
        ...     "content": [result_block]
        ... }
    """
    registry = get_tool_registry()
    
    if is_error:
        content = f"Error: {result}"
        status = "error"
    else:
        content = registry.format_tool_result(tool_name, result)
        status = "success"
    
    return {
        "toolResult": {
            "toolUseId": tool_use_id,
            "content": [
                {
                    "json": {
                        "result": content,
                        "status": status
                    }
                }
            ]
        }
    }
