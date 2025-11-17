"""Inventory Optimization Agent for Warehouse Manager"""
import boto3
import json
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

class InventoryOptimizerAgent(BaseAgent):
    """Agent for inventory forecasting and optimization"""
    
    def __init__(self, region: str = None):
        super().__init__("inventory_optimizer_agent", "warehouse_manager", region)
        # Region is set by BaseAgent from environment if not provided
        self.lambda_client = boto3.client('lambda', region_name=self.region)
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return inventory optimization tools"""
        return [
            {
                "toolSpec": {
                    "name": "calculate_reorder_points",
                    "description": "Calculate optimal reorder points for products based on historical data, lead times, and demand patterns",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "warehouse_code": {
                                    "type": "string",
                                    "description": "Warehouse code to analyze"
                                },
                                "product_codes": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of product codes (optional, analyzes all if not provided)"
                                }
                            },
                            "required": ["warehouse_code"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "forecast_demand",
                    "description": "Forecast product demand for the next period based on historical sales data",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "product_code": {
                                    "type": "string",
                                    "description": "Product code to forecast"
                                },
                                "warehouse_code": {
                                    "type": "string",
                                    "description": "Warehouse code"
                                },
                                "forecast_days": {
                                    "type": "integer",
                                    "description": "Number of days to forecast (default 30)"
                                }
                            },
                            "required": ["product_code", "warehouse_code"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "identify_stockout_risks",
                    "description": "Identify products at risk of stockout based on current inventory and demand",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "warehouse_code": {
                                    "type": "string",
                                    "description": "Warehouse code to analyze"
                                },
                                "days_ahead": {
                                    "type": "integer",
                                    "description": "Number of days to look ahead (default 7)"
                                }
                            },
                            "required": ["warehouse_code"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "optimize_stock_levels",
                    "description": "Suggest optimal stock levels to minimize costs while maintaining service levels",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "warehouse_code": {
                                    "type": "string",
                                    "description": "Warehouse code"
                                },
                                "target_service_level": {
                                    "type": "number",
                                    "description": "Target service level percentage (default 95)"
                                }
                            },
                            "required": ["warehouse_code"]
                        }
                    }
                }
            }
        ]
    
    def process_query(self, query: str, session_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process inventory optimization query using Bedrock agent orchestration"""
        from config import BEDROCK_MODEL_ID
        
        system_prompt = """You are an inventory optimization expert for warehouse management.
        
You have access to tools for:
- Calculating optimal reorder points
- Forecasting product demand
- Identifying stockout risks
- Optimizing stock levels

Use these tools to help warehouse managers make data-driven inventory decisions.
Provide actionable insights and recommendations."""
        
        # Use Bedrock Converse API with tools
        messages = [{"role": "user", "content": [{"text": query}]}]
        
        response = self.bedrock_runtime.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=messages,
            system=[{"text": system_prompt}],
            toolConfig={"tools": self.get_tools()}
        )
        
        # Process tool calls if any
        if response['stopReason'] == 'tool_use':
            tool_results = []
            for content in response['output']['message']['content']:
                if 'toolUse' in content:
                    tool_use = content['toolUse']
                    tool_name = tool_use['name']
                    tool_input = tool_use['input']
                    
                    # Execute tool
                    result = self.execute_tool(tool_name, tool_input)
                    tool_results.append({
                        "toolUseId": tool_use['toolUseId'],
                        "content": [{"json": result}]
                    })
            
            # Continue conversation with tool results
            messages.append(response['output']['message'])
            messages.append({"role": "user", "content": tool_results})
            
            final_response = self.bedrock_runtime.converse(
                modelId=BEDROCK_MODEL_ID,
                messages=messages,
                system=[{"text": system_prompt}]
            )
            
            return {
                "success": True,
                "response": final_response['output']['message']['content'][0]['text'],
                "tool_calls": len(tool_results)
            }
        
        return {
            "success": True,
            "response": response['output']['message']['content'][0]['text']
        }
    
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute inventory optimization tool via Lambda
        
        Uses ToolExecutor for async execution with retry logic if available,
        falls back to direct Lambda invocation otherwise.
        """
        from config import LAMBDA_INVENTORY_OPTIMIZER
        
        # Try to use ToolExecutor if available
        if self.tool_executor:
            result = self.execute_tool_async(
                tool_name=tool_name,
                function_name=LAMBDA_INVENTORY_OPTIMIZER,
                input_data=tool_input
            )
            
            if result.get("success"):
                # Extract the actual result from Lambda response
                lambda_result = result.get("result", {})
                if isinstance(lambda_result, dict) and lambda_result.get("success"):
                    return lambda_result.get("result", lambda_result)
                return lambda_result
            else:
                # Return error in expected format
                return {"error": result.get("error", "Tool execution failed")}
        
        # Fallback to direct Lambda invocation
        payload = {
            "tool_name": tool_name,
            "input": tool_input
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=LAMBDA_INVENTORY_OPTIMIZER,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            # Handle new structured response format
            if isinstance(result, dict) and result.get("success"):
                return result.get("result", result)
            
            return result
        except Exception as e:
            return {"error": str(e)}
