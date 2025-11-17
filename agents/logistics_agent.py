"""Logistics and Maintenance Agent for Field Engineer"""
import boto3
import json
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

class LogisticsAgent(BaseAgent):
    """Agent for logistics optimization and field operations"""
    
    def __init__(self, region: str = None):
        super().__init__("logistics_agent", "field_engineer", region)
        # Region is set by BaseAgent from environment if not provided
        self.lambda_client = boto3.client('lambda', region_name=self.region)
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return logistics optimization tools"""
        return [
            {
                "toolSpec": {
                    "name": "optimize_delivery_route",
                    "description": "Optimize delivery routes for multiple orders to minimize time and cost",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "warehouse_code": {
                                    "type": "string",
                                    "description": "Starting warehouse code"
                                },
                                "sales_order_numbers": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of sales order numbers to deliver"
                                },
                                "delivery_date": {
                                    "type": "string",
                                    "description": "Target delivery date (YYYYMMDD format)"
                                }
                            },
                            "required": ["warehouse_code"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "check_order_fulfillment_status",
                    "description": "Check detailed fulfillment status of orders including picking, packing, and shipping",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "sales_order_number": {
                                    "type": "string",
                                    "description": "Sales order number to check"
                                }
                            },
                            "required": ["sales_order_number"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "identify_delayed_orders",
                    "description": "Identify orders that are delayed or at risk of delay",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "warehouse_code": {
                                    "type": "string",
                                    "description": "Warehouse code (optional)"
                                },
                                "days_overdue": {
                                    "type": "integer",
                                    "description": "Minimum days overdue (default 0 for at-risk orders)"
                                }
                            }
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "calculate_warehouse_capacity",
                    "description": "Calculate current warehouse capacity utilization and available space",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "warehouse_code": {
                                    "type": "string",
                                    "description": "Warehouse code to analyze"
                                }
                            },
                            "required": ["warehouse_code"]
                        }
                    }
                }
            }
        ]
    
    def process_query(self, query: str, session_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process logistics query"""
        from config import BEDROCK_MODEL_ID
        
        system_prompt = """You are a logistics and field operations expert.

You have access to tools for:
- Optimizing delivery routes
- Checking order fulfillment status
- Identifying delayed orders
- Calculating warehouse capacity

Use these tools to help field engineers manage deliveries, track orders, and optimize operations.
Provide practical, actionable recommendations."""
        
        messages = [{"role": "user", "content": [{"text": query}]}]
        
        response = self.bedrock_runtime.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=messages,
            system=[{"text": system_prompt}],
            toolConfig={"tools": self.get_tools()}
        )
        
        if response['stopReason'] == 'tool_use':
            tool_results = []
            for content in response['output']['message']['content']:
                if 'toolUse' in content:
                    tool_use = content['toolUse']
                    result = self.execute_tool(tool_use['name'], tool_use['input'])
                    tool_results.append({
                        "toolUseId": tool_use['toolUseId'],
                        "content": [{"json": result}]
                    })
            
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
        """Execute logistics tool via Lambda
        
        Uses ToolExecutor for async execution with retry logic if available,
        falls back to direct Lambda invocation otherwise.
        """
        from config import LAMBDA_LOGISTICS_OPTIMIZER
        
        # Try to use ToolExecutor if available
        if self.tool_executor:
            result = self.execute_tool_async(
                tool_name=tool_name,
                function_name=LAMBDA_LOGISTICS_OPTIMIZER,
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
        payload = {"tool_name": tool_name, "input": tool_input}
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=LAMBDA_LOGISTICS_OPTIMIZER,
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
