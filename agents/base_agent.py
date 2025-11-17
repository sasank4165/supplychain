"""Base Agent class for all supply chain agents"""
import boto3
import json
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

# Import ToolExecutor for async tool execution
try:
    from tool_executor import ToolExecutor, ToolExecutionRequest, ToolExecutionStatus
    TOOL_EXECUTOR_AVAILABLE = True
except ImportError:
    logger.warning("ToolExecutor not available, falling back to synchronous execution")
    TOOL_EXECUTOR_AVAILABLE = False

class BaseAgent(ABC):
    """Base class for all agents in the supply chain system
    
    Supports configuration-driven initialization for plugin architecture.
    Agents can be instantiated with configuration dictionaries that specify
    model selection, timeouts, and other agent-specific parameters.
    
    Integrates with ModelManager for centralized model selection, fallback,
    and usage metrics collection.
    """
    
    def __init__(self, agent_name: str, persona: str, region: str = None, config: Optional[Dict[str, Any]] = None, model_manager=None, tool_executor=None):
        """Initialize base agent
        
        Args:
            agent_name: Name of the agent
            persona: Persona this agent serves (e.g., 'warehouse_manager')
            region: AWS region (if None, reads from environment)
            config: Optional configuration dictionary with agent-specific settings
            model_manager: Optional ModelManager instance for model invocations
            tool_executor: Optional ToolExecutor instance for async tool execution
        """
        self.agent_name = agent_name
        self.persona = persona
        
        # Get region from parameter or environment
        if region is None:
            import os
            region = os.getenv('AWS_REGION', 'us-east-1')
        self.region = region
        
        self.agent_config = config or {}
        self.model_manager = model_manager
        
        # Initialize AWS clients
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # Tool executor for async execution
        if tool_executor:
            self.tool_executor = tool_executor
        elif TOOL_EXECUTOR_AVAILABLE:
            self.tool_executor = ToolExecutor(region=region, config=config)
        else:
            self.tool_executor = None
        
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return the tools available to this agent"""
        pass
    
    @abstractmethod
    def process_query(self, query: str, session_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a user query and return response"""
        pass
    
    def save_session_state(self, session_id: str, state: Dict[str, Any]):
        """Save session state to DynamoDB"""
        from config import DYNAMODB_SESSION_TABLE
        table = self.dynamodb.Table(DYNAMODB_SESSION_TABLE)
        table.put_item(
            Item={
                'session_id': session_id,
                'persona': self.persona,
                'agent_name': self.agent_name,
                'state': json.dumps(state),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session state from DynamoDB"""
        from config import DYNAMODB_SESSION_TABLE
        table = self.dynamodb.Table(DYNAMODB_SESSION_TABLE)
        response = table.get_item(Key={'session_id': session_id})
        if 'Item' in response:
            return json.loads(response['Item']['state'])
        return None
    
    def get_model_id(self) -> str:
        """Get model ID for this agent from configuration or default
        
        Returns:
            Bedrock model ID
        """
        # Try to get from agent config first
        if self.agent_config and 'model' in self.agent_config:
            return self.agent_config['model']
        
        # Fall back to config.py default
        try:
            from config import BEDROCK_MODEL_ID
            return BEDROCK_MODEL_ID
        except ImportError:
            # Ultimate fallback
            return "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def get_timeout_seconds(self) -> int:
        """Get timeout in seconds for this agent from configuration
        
        Returns:
            Timeout in seconds (default: 60)
        """
        return self.agent_config.get('timeout_seconds', 60)
    
    def invoke_bedrock_model(self, prompt: str, system_prompt: str = "", tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """Invoke Bedrock Claude model with configuration-driven model selection
        
        Uses ModelManager if available for automatic fallback and metrics collection.
        Falls back to direct Bedrock invocation if ModelManager not available.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            tools: Optional list of tool definitions
            
        Returns:
            Model response text
        """
        # Format messages for Converse API
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        
        # Use ModelManager if available
        if self.model_manager:
            try:
                result = self.model_manager.invoke_model(
                    agent_name=self.agent_name,
                    messages=messages,
                    system_prompt=system_prompt,
                    tools=tools,
                    use_fallback=True
                )
                
                if result.get("success"):
                    response = result["response"]
                    # Extract text from response
                    if "output" in response and "message" in response["output"]:
                        content = response["output"]["message"]["content"]
                        if content and len(content) > 0:
                            return content[0].get("text", "")
                    return ""
                else:
                    # Fall through to direct invocation
                    print(f"Warning: ModelManager invocation failed, using direct invocation")
            except Exception as e:
                print(f"Warning: ModelManager error: {str(e)}, using direct invocation")
        
        # Fallback to direct Bedrock invocation
        model_id = self.get_model_id()
        
        response = self.bedrock_runtime.converse(
            modelId=model_id,
            messages=messages,
            system=[{"text": system_prompt}] if system_prompt else [],
            inferenceConfig={
                "maxTokens": 4096,
                "temperature": 0.0
            }
        )
        
        # Extract text from response
        if "output" in response and "message" in response["output"]:
            content = response["output"]["message"]["content"]
            if content and len(content) > 0:
                return content[0].get("text", "")
        
        return ""

    def execute_tool_async(
        self,
        tool_name: str,
        function_name: str,
        input_data: Dict[str, Any],
        timeout_seconds: Optional[int] = None,
        max_retries: Optional[int] = None,
        user_context: Optional[Dict[str, Any]] = None,
        access_controller = None
    ) -> Dict[str, Any]:
        """Execute a single tool asynchronously using ToolExecutor with access control
        
        Args:
            tool_name: Name of the tool
            function_name: Lambda function name
            input_data: Tool input parameters
            timeout_seconds: Optional timeout override
            max_retries: Optional max retries override
            user_context: Optional user context for access control
            access_controller: Optional AccessController instance
            
        Returns:
            Tool execution result
        """
        # Validate tool access if access controller and context provided
        if access_controller and user_context:
            if not access_controller.authorize_tool_access(user_context, tool_name):
                logger.warning(f"Tool access denied: {tool_name} for user {user_context.get('user_id', 'unknown')}")
                return {
                    "success": False,
                    "error": f"Access denied to tool: {tool_name}",
                    "status": 403
                }
        
        if not self.tool_executor:
            logger.warning("ToolExecutor not available, cannot execute tool asynchronously")
            return {
                "success": False,
                "error": "ToolExecutor not available"
            }
        
        # Create execution request
        request = ToolExecutionRequest(
            tool_name=tool_name,
            function_name=function_name,
            input_data=input_data,
            timeout_seconds=timeout_seconds or self.get_timeout_seconds(),
            max_retries=max_retries or 3,
            metadata={"agent": self.agent_name, "persona": self.persona}
        )
        
        # Execute synchronously (wraps async execution)
        result = self.tool_executor.execute_tool_sync(request)
        
        # Convert to standard response format
        if result.is_success():
            return {
                "success": True,
                "result": result.result,
                "execution_time_ms": result.execution_time_ms,
                "attempts": result.attempts
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "status": result.status.value,
                "execution_time_ms": result.execution_time_ms,
                "attempts": result.attempts
            }
    
    def execute_tools_parallel(
        self,
        tool_requests: List[Dict[str, Any]],
        timeout: Optional[int] = None,
        user_context: Optional[Dict[str, Any]] = None,
        access_controller = None
    ) -> List[Dict[str, Any]]:
        """Execute multiple tools in parallel using ToolExecutor with access control
        
        Args:
            tool_requests: List of tool request dictionaries with keys:
                - tool_name: Name of the tool
                - function_name: Lambda function name
                - input_data: Tool input parameters
                - timeout_seconds (optional): Timeout override
                - max_retries (optional): Max retries override
            timeout: Optional overall timeout for all tools
            user_context: Optional user context for access control
            access_controller: Optional AccessController instance
            
        Returns:
            List of tool execution results
        """
        # Validate tool access for all tools if access controller and context provided
        if access_controller and user_context:
            denied_tools = []
            for req in tool_requests:
                tool_name = req.get("tool_name")
                if not access_controller.authorize_tool_access(user_context, tool_name):
                    denied_tools.append(tool_name)
            
            if denied_tools:
                logger.warning(f"Tool access denied for user {user_context.get('user_id', 'unknown')}: {denied_tools}")
                return [
                    {
                        "success": False,
                        "tool_name": req.get("tool_name"),
                        "error": f"Access denied to tool: {req.get('tool_name')}",
                        "status": 403
                    }
                    if req.get("tool_name") in denied_tools
                    else {"success": True, "tool_name": req.get("tool_name"), "pending": True}
                    for req in tool_requests
                ]
        
        if not self.tool_executor:
            logger.warning("ToolExecutor not available, cannot execute tools in parallel")
            return [
                {"success": False, "error": "ToolExecutor not available"}
                for _ in tool_requests
            ]
        
        # Create execution requests
        requests = []
        for req in tool_requests:
            requests.append(ToolExecutionRequest(
                tool_name=req["tool_name"],
                function_name=req["function_name"],
                input_data=req["input_data"],
                timeout_seconds=req.get("timeout_seconds", self.get_timeout_seconds()),
                max_retries=req.get("max_retries", 3),
                metadata={"agent": self.agent_name, "persona": self.persona}
            ))
        
        # Execute in parallel
        results = self.tool_executor.execute_tools_sync(requests, timeout)
        
        # Convert to standard response format
        converted_results = []
        for result in results:
            if result.is_success():
                converted_results.append({
                    "success": True,
                    "tool_name": result.tool_name,
                    "result": result.result,
                    "execution_time_ms": result.execution_time_ms,
                    "attempts": result.attempts
                })
            else:
                converted_results.append({
                    "success": False,
                    "tool_name": result.tool_name,
                    "error": result.error,
                    "status": result.status.value,
                    "execution_time_ms": result.execution_time_ms,
                    "attempts": result.attempts
                })
        
        return converted_results
    
    def get_tool_execution_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics from ToolExecutor
        
        Returns:
            Dictionary with execution statistics
        """
        if not self.tool_executor:
            return {"error": "ToolExecutor not available"}
        
        return self.tool_executor.get_execution_stats()
