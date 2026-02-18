"""
Inventory Agent

Specialized agent for inventory optimization tasks for Warehouse Managers.
Invokes Inventory Optimizer Lambda function and integrates with Bedrock for tool calling.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import json

from agents.base_agent import BaseAgent, AgentResponse
from aws.bedrock_client import BedrockClient, BedrockResponse
from aws.lambda_client import LambdaClient, LambdaClientError


class InventoryAgent(BaseAgent):
    """
    Inventory Agent for Warehouse Managers.
    
    Provides inventory optimization capabilities including:
    - Calculate reorder points
    - Identify low stock products
    - Forecast demand
    - Identify stockout risks
    """
    
    # Tool definitions for Bedrock
    TOOL_DEFINITIONS = [
        {
            "toolSpec": {
                "name": "calculate_reorder_point",
                "description": "Calculate the optimal reorder point for a product at a specific warehouse. The reorder point is the inventory level at which a new order should be placed.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "product_code": {
                                "type": "string",
                                "description": "The product code to calculate reorder point for"
                            },
                            "warehouse_code": {
                                "type": "string",
                                "description": "The warehouse code where the product is stored"
                            }
                        },
                        "required": ["product_code", "warehouse_code"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "identify_low_stock",
                "description": "Identify products that are below their minimum stock level at a warehouse. Returns products that need immediate attention.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "warehouse_code": {
                                "type": "string",
                                "description": "The warehouse code to check for low stock"
                            },
                            "threshold": {
                                "type": "number",
                                "description": "Stock level threshold as a ratio (e.g., 1.0 means at or below minimum stock, 1.5 means 50% above minimum)"
                            }
                        },
                        "required": ["warehouse_code", "threshold"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "forecast_demand",
                "description": "Forecast future demand for a product based on historical sales data. Uses moving average method.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "product_code": {
                                "type": "string",
                                "description": "The product code to forecast demand for"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to forecast into the future"
                            }
                        },
                        "required": ["product_code", "days"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "identify_stockout_risk",
                "description": "Identify products at risk of stockout within a specified time period. Considers current stock, demand forecast, and lead time.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "warehouse_code": {
                                "type": "string",
                                "description": "The warehouse code to check for stockout risk"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look ahead for stockout risk"
                            }
                        },
                        "required": ["warehouse_code", "days"]
                    }
                }
            }
        }
    ]
    
    def __init__(
        self,
        bedrock_client: BedrockClient,
        lambda_client: LambdaClient,
        lambda_function_name: str,
        logger=None
    ):
        """
        Initialize Inventory Agent.
        
        Args:
            bedrock_client: BedrockClient instance for AI orchestration
            lambda_client: LambdaClient instance for Lambda invocations
            lambda_function_name: Name of the Inventory Optimizer Lambda function
            logger: Optional logger instance
        """
        super().__init__(agent_name="InventoryAgent", logger=logger)
        self.bedrock_client = bedrock_client
        self.lambda_client = lambda_client
        self.lambda_function_name = lambda_function_name
        
        self.log_info(f"Initialized with Lambda function: {lambda_function_name}")
    
    def process_request(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process an inventory optimization request.
        
        Args:
            request: Natural language request from user
            context: Optional conversation context
            
        Returns:
            AgentResponse with optimization results
        """
        start_time = time.time()
        
        try:
            self.log_info(f"Processing request: {request[:100]}...")
            
            # Build conversation messages
            messages = self._build_messages(request, context)
            
            # System prompt for inventory optimization
            system_prompt = self._get_system_prompt()
            
            # Converse with Bedrock using tools
            bedrock_response = self.bedrock_client.converse_with_tools(
                messages=messages,
                tools=self.TOOL_DEFINITIONS,
                system=[{"text": system_prompt}]
            )
            
            # Check if tools were used
            if bedrock_response.tool_use:
                # Execute tools and get results
                tool_results = self._execute_tools(bedrock_response.tool_use)
                
                # Continue conversation with tool results
                final_response = self._continue_with_tool_results(
                    messages=messages,
                    assistant_response=bedrock_response,
                    tool_results=tool_results,
                    system_prompt=system_prompt
                )
                
                execution_time = time.time() - start_time
                
                return self.create_success_response(
                    content=final_response.content,
                    data={
                        "tool_results": tool_results,
                        "token_usage": {
                            "input_tokens": final_response.token_usage.input_tokens,
                            "output_tokens": final_response.token_usage.output_tokens,
                            "total_tokens": final_response.token_usage.total_tokens
                        }
                    },
                    execution_time=execution_time,
                    metadata={"tools_used": [t["name"] for t in bedrock_response.tool_use]}
                )
            else:
                # No tools used, return direct response
                execution_time = time.time() - start_time
                
                return self.create_success_response(
                    content=bedrock_response.content,
                    data={
                        "token_usage": {
                            "input_tokens": bedrock_response.token_usage.input_tokens,
                            "output_tokens": bedrock_response.token_usage.output_tokens,
                            "total_tokens": bedrock_response.token_usage.total_tokens
                        }
                    },
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            return self.handle_exception(
                exception=e,
                context="processing inventory request",
                execution_time=execution_time
            )
    
    def _build_messages(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Build conversation messages for Bedrock."""
        messages = []
        
        # Add conversation history if available
        if context and hasattr(context, 'history'):
            for interaction in context.history:
                messages.append({
                    "role": "user",
                    "content": [{"text": interaction.query}]
                })
                # Truncate response to avoid overwhelming context
                response_preview = interaction.response[:300] + "..." if len(interaction.response) > 300 else interaction.response
                messages.append({
                    "role": "assistant",
                    "content": [{"text": response_preview}]
                })
        
        # Add current request
        messages.append({
            "role": "user",
            "content": [{"text": request}]
        })
        
        return messages
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for inventory optimization."""
        return """You are an Inventory Optimization Assistant for Warehouse Managers.

Your role is to help warehouse managers optimize inventory levels, prevent stockouts, and make data-driven reordering decisions.

You have access to the following tools:
- calculate_reorder_point: Calculate optimal reorder point for a product
- identify_low_stock: Find products below minimum stock levels
- forecast_demand: Forecast future demand based on historical data
- identify_stockout_risk: Identify products at risk of running out

When responding:
1. Use the appropriate tools to gather data
2. Provide clear, actionable recommendations
3. Explain the reasoning behind your recommendations
4. Include specific numbers and metrics
5. Prioritize urgent issues (stockouts, critical low stock)

Always be concise and focus on actionable insights."""
    
    def _execute_tools(self, tool_use_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute Lambda tools requested by Bedrock.
        
        Args:
            tool_use_blocks: List of tool use blocks from Bedrock response
            
        Returns:
            List of tool results
        """
        results = []
        
        for tool_use in tool_use_blocks:
            tool_name = tool_use.get("name")
            tool_use_id = tool_use.get("toolUseId")
            tool_input = tool_use.get("input", {})
            
            self.log_info(f"Executing tool: {tool_name} with input: {tool_input}")
            
            try:
                # Invoke Lambda function
                lambda_payload = {
                    "action": tool_name,
                    **tool_input
                }
                
                lambda_response = self.lambda_client.invoke(
                    function_name=self.lambda_function_name,
                    payload=lambda_payload
                )
                
                if lambda_response.is_success:
                    # Parse response body
                    body = lambda_response.payload.get("body", "{}")
                    if isinstance(body, str):
                        body = json.loads(body)
                    
                    result_data = body.get("data", {})
                    
                    results.append({
                        "tool_use_id": tool_use_id,
                        "tool_name": tool_name,
                        "result": result_data,
                        "success": True
                    })
                    
                    self.log_info(f"Tool {tool_name} executed successfully")
                else:
                    error_msg = lambda_response.payload.get("error", "Unknown error")
                    results.append({
                        "tool_use_id": tool_use_id,
                        "tool_name": tool_name,
                        "result": {"error": error_msg},
                        "success": False
                    })
                    
                    self.log_error(f"Tool {tool_name} failed: {error_msg}")
                    
            except LambdaClientError as e:
                results.append({
                    "tool_use_id": tool_use_id,
                    "tool_name": tool_name,
                    "result": {"error": str(e)},
                    "success": False
                })
                
                self.log_error(f"Lambda invocation failed for {tool_name}", e)
            except Exception as e:
                results.append({
                    "tool_use_id": tool_use_id,
                    "tool_name": tool_name,
                    "result": {"error": str(e)},
                    "success": False
                })
                
                self.log_error(f"Unexpected error executing {tool_name}", e)
        
        return results
    
    def _continue_with_tool_results(
        self,
        messages: List[Dict[str, Any]],
        assistant_response: BedrockResponse,
        tool_results: List[Dict[str, Any]],
        system_prompt: str
    ) -> BedrockResponse:
        """
        Continue conversation with tool results.
        
        Args:
            messages: Original conversation messages
            assistant_response: Assistant's response with tool use
            tool_results: Results from tool execution
            system_prompt: System prompt
            
        Returns:
            Final BedrockResponse with analysis
        """
        # Build assistant message with tool use
        assistant_content = []
        
        # Add text content if any
        if assistant_response.content:
            assistant_content.append({"text": assistant_response.content})
        
        # Add tool use blocks
        for tool_use in assistant_response.tool_use:
            assistant_content.append({"toolUse": tool_use})
        
        messages.append({
            "role": "assistant",
            "content": assistant_content
        })
        
        # Build user message with tool results
        tool_result_content = []
        for result in tool_results:
            tool_result_content.append({
                "toolResult": {
                    "toolUseId": result["tool_use_id"],
                    "content": [{"json": result["result"]}]
                }
            })
        
        messages.append({
            "role": "user",
            "content": tool_result_content
        })
        
        # Get final response from Bedrock with tool definitions
        final_response = self.bedrock_client.converse(
            messages=messages,
            system=[{"text": system_prompt}],
            tools=self.TOOL_DEFINITIONS
        )
        
        return final_response
    
    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return [tool["toolSpec"]["name"] for tool in self.TOOL_DEFINITIONS]
    
    def invoke_tool_directly(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke a tool directly without Bedrock orchestration.
        
        Args:
            tool_name: Name of the tool to invoke
            parameters: Tool parameters
            
        Returns:
            Tool result
            
        Raises:
            ValueError: If tool name is invalid
            LambdaClientError: If Lambda invocation fails
        """
        available_tools = self.get_available_tools()
        if tool_name not in available_tools:
            raise ValueError(
                f"Invalid tool name: {tool_name}. "
                f"Available tools: {', '.join(available_tools)}"
            )
        
        self.log_info(f"Direct invocation of tool: {tool_name}")
        
        lambda_payload = {
            "action": tool_name,
            **parameters
        }
        
        lambda_response = self.lambda_client.invoke(
            function_name=self.lambda_function_name,
            payload=lambda_payload
        )
        
        if lambda_response.is_success:
            body = lambda_response.payload.get("body", "{}")
            if isinstance(body, str):
                body = json.loads(body)
            return body.get("data", {})
        else:
            raise LambdaClientError(
                f"Tool invocation failed: {lambda_response.payload.get('error', 'Unknown error')}"
            )
