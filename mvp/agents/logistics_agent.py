"""
Logistics Agent

Specialized agent for logistics optimization tasks for Field Engineers.
Invokes Logistics Optimizer Lambda function and integrates with Bedrock for tool calling.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import json

from agents.base_agent import BaseAgent, AgentResponse
from aws.bedrock_client import BedrockClient, BedrockResponse
from aws.lambda_client import LambdaClient, LambdaClientError


class LogisticsAgent(BaseAgent):
    """
    Logistics Agent for Field Engineers.
    
    Provides logistics optimization capabilities including:
    - Optimize delivery routes
    - Check order fulfillment status
    - Identify delayed orders
    - Calculate warehouse capacity
    """
    
    # Tool definitions for Bedrock
    TOOL_DEFINITIONS = [
        {
            "toolSpec": {
                "name": "optimize_delivery_route",
                "description": "Optimize delivery routes for a set of orders by grouping them by delivery area and prioritizing by delivery date. Returns an optimized route plan.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "order_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of sales order IDs to optimize routes for"
                            },
                            "warehouse_code": {
                                "type": "string",
                                "description": "The warehouse code from which orders will be delivered"
                            }
                        },
                        "required": ["order_ids", "warehouse_code"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "check_fulfillment_status",
                "description": "Get detailed fulfillment status for a specific order including line items, quantities, and fulfillment progress.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The sales order ID to check status for"
                            }
                        },
                        "required": ["order_id"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "identify_delayed_orders",
                "description": "Identify orders that are past their delivery date or at risk of delay. Returns orders that need immediate attention.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "warehouse_code": {
                                "type": "string",
                                "description": "The warehouse code to check for delayed orders"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back for delayed orders"
                            }
                        },
                        "required": ["warehouse_code", "days"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "calculate_warehouse_capacity",
                "description": "Calculate warehouse capacity utilization based on current inventory levels and maximum capacity. Returns capacity metrics and recommendations.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "warehouse_code": {
                                "type": "string",
                                "description": "The warehouse code to calculate capacity for"
                            }
                        },
                        "required": ["warehouse_code"]
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
        Initialize Logistics Agent.
        
        Args:
            bedrock_client: BedrockClient instance for AI orchestration
            lambda_client: LambdaClient instance for Lambda invocations
            lambda_function_name: Name of the Logistics Optimizer Lambda function
            logger: Optional logger instance
        """
        super().__init__(agent_name="LogisticsAgent", logger=logger)
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
        Process a logistics optimization request.
        
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
            
            # System prompt for logistics optimization
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
                context="processing logistics request",
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
                messages.append({
                    "role": "assistant",
                    "content": [{"text": interaction.response}]
                })
        
        # Add current request
        messages.append({
            "role": "user",
            "content": [{"text": request}]
        })
        
        return messages
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for logistics optimization."""
        return """You are a Logistics Optimization Assistant for Field Engineers.

Your role is to help field engineers optimize delivery routes, track order fulfillment, and ensure timely deliveries.

You have access to the following tools:
- optimize_delivery_route: Optimize delivery routes by grouping orders by area
- check_fulfillment_status: Get detailed status of order fulfillment
- identify_delayed_orders: Find orders that are delayed or at risk
- calculate_warehouse_capacity: Calculate warehouse capacity utilization

When responding:
1. Use the appropriate tools to gather data
2. Provide clear, actionable recommendations
3. Prioritize urgent deliveries and delayed orders
4. Include specific order IDs and delivery areas
5. Suggest route optimizations to improve efficiency

Always be concise and focus on actionable insights for field operations."""
    
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
        
        # Get final response from Bedrock
        final_response = self.bedrock_client.converse(
            messages=messages,
            system=[{"text": system_prompt}]
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
