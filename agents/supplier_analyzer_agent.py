"""Supplier Analysis Agent for Procurement Specialist"""
import boto3
import json
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

class SupplierAnalyzerAgent(BaseAgent):
    """Agent for supplier performance analysis and cost optimization"""
    
    def __init__(self, region: str = None):
        super().__init__("supplier_analyzer_agent", "procurement_specialist", region)
        # Region is set by BaseAgent from environment if not provided
        self.lambda_client = boto3.client('lambda', region_name=self.region)
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return supplier analysis tools"""
        return [
            {
                "toolSpec": {
                    "name": "analyze_supplier_performance",
                    "description": "Analyze supplier performance metrics including on-time delivery, quality, and cost",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "supplier_code": {
                                    "type": "string",
                                    "description": "Supplier code to analyze (optional, analyzes all if not provided)"
                                },
                                "time_period_days": {
                                    "type": "integer",
                                    "description": "Number of days to analyze (default 90)"
                                }
                            }
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "compare_supplier_costs",
                    "description": "Compare costs across suppliers for similar products",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "product_group": {
                                    "type": "string",
                                    "description": "Product group to compare"
                                },
                                "supplier_codes": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of supplier codes to compare"
                                }
                            },
                            "required": ["product_group"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "identify_cost_savings_opportunities",
                    "description": "Identify opportunities for cost savings through supplier consolidation or negotiation",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "product_group": {
                                    "type": "string",
                                    "description": "Product group to analyze (optional)"
                                },
                                "min_savings_percentage": {
                                    "type": "number",
                                    "description": "Minimum savings percentage to report (default 5)"
                                }
                            }
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "analyze_purchase_order_trends",
                    "description": "Analyze purchase order trends and patterns",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "supplier_code": {
                                    "type": "string",
                                    "description": "Supplier code (optional)"
                                },
                                "months": {
                                    "type": "integer",
                                    "description": "Number of months to analyze (default 6)"
                                }
                            }
                        }
                    }
                }
            }
        ]
    
    def process_query(self, query: str, session_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process supplier analysis query"""
        from config import BEDROCK_MODEL_ID
        
        system_prompt = """You are a procurement and supplier analysis expert.

You have access to tools for:
- Analyzing supplier performance metrics
- Comparing costs across suppliers
- Identifying cost savings opportunities
- Analyzing purchase order trends

Use these tools to help procurement specialists make strategic sourcing decisions.
Provide data-driven insights and actionable recommendations."""
        
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
        """Execute supplier analysis tool via Lambda
        
        Uses ToolExecutor for async execution with retry logic if available,
        falls back to direct Lambda invocation otherwise.
        """
        from config import LAMBDA_SUPPLIER_ANALYZER
        
        # Try to use ToolExecutor if available
        if self.tool_executor:
            result = self.execute_tool_async(
                tool_name=tool_name,
                function_name=LAMBDA_SUPPLIER_ANALYZER,
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
                FunctionName=LAMBDA_SUPPLIER_ANALYZER,
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
