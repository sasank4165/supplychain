"""Enhanced Base Agent using Amazon Bedrock Agent Core patterns"""
import boto3
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Import ToolExecutor for async tool execution
try:
    from tool_executor import ToolExecutor, ToolExecutionRequest, ToolExecutionStatus
    TOOL_EXECUTOR_AVAILABLE = True
except ImportError:
    logger.warning("ToolExecutor not available, falling back to synchronous execution")
    TOOL_EXECUTOR_AVAILABLE = False


class ToolStatus(Enum):
    """Tool execution status"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass
class ToolResult:
    """Structured tool execution result"""
    status: ToolStatus
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata or {}
        }


@dataclass
class AgentMessage:
    """Structured agent message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Optional[Dict] = None


class ToolRegistry:
    """Registry for agent tools with validation"""
    
    def __init__(self):
        self._tools: Dict[str, Dict] = {}
        self._handlers: Dict[str, Callable] = {}
    
    def register_tool(
        self, 
        name: str, 
        description: str, 
        input_schema: Dict,
        handler: Callable
    ):
        """Register a tool with its handler"""
        self._tools[name] = {
            "toolSpec": {
                "name": name,
                "description": description,
                "inputSchema": {"json": input_schema}
            }
        }
        self._handlers[name] = handler
        logger.info(f"Registered tool: {name}")
    
    def get_tools(self) -> List[Dict]:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def execute_tool(self, name: str, input_data: Dict) -> ToolResult:
        """Execute a tool by name"""
        if name not in self._handlers:
            return ToolResult(
                status=ToolStatus.ERROR,
                data=None,
                error=f"Tool not found: {name}"
            )
        
        try:
            handler = self._handlers[name]
            result = handler(input_data)
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=result,
                metadata={"tool_name": name}
            )
        except Exception as e:
            logger.error(f"Tool execution error for {name}: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                data=None,
                error=str(e),
                metadata={"tool_name": name}
            )


class ConversationMemory:
    """Manages conversation history with context window management"""
    
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.messages: List[AgentMessage] = []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation history"""
        message = AgentMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata
        )
        self.messages.append(message)
        
        # Trim to max messages (keep system messages)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages(self) -> List[Dict]:
        """Get messages in Bedrock format"""
        return [
            {"role": msg.role, "content": [{"text": msg.content}]}
            for msg in self.messages
        ]
    
    def clear(self):
        """Clear conversation history"""
        self.messages = []


class EnhancedBaseAgent(ABC):
    """
    Enhanced base agent using Amazon Bedrock Agent Core patterns
    
    Features:
    - Tool registry with validation
    - Conversation memory management
    - Structured tool results
    - Error handling and retry logic
    - Observability with logging
    - Session state management
    """
    
    def __init__(
        self, 
        agent_name: str, 
        persona: str, 
        region: str = "us-east-1",
        max_iterations: int = 10,
        tool_executor: Optional[Any] = None
    ):
        self.agent_name = agent_name
        self.persona = persona
        self.region = region
        self.max_iterations = max_iterations
        
        # AWS clients
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # Tool registry
        self.tool_registry = ToolRegistry()
        
        # Conversation memory
        self.memory = ConversationMemory()
        
        # Tool executor for async execution
        if tool_executor:
            self.tool_executor = tool_executor
        elif TOOL_EXECUTOR_AVAILABLE:
            self.tool_executor = ToolExecutor(region=region)
        else:
            self.tool_executor = None
        
        # Register tools
        self._register_tools()
        
        logger.info(f"Initialized {agent_name} for persona {persona}")
    
    @abstractmethod
    def _register_tools(self):
        """Register agent-specific tools"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get agent-specific system prompt"""
        pass
    
    def process_query(
        self, 
        query: str, 
        session_id: str, 
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process user query with agentic loop
        
        Implements the ReAct pattern:
        1. Reason about the query
        2. Act by calling tools
        3. Observe results
        4. Repeat until answer is found
        """
        try:
            # Add user message to memory
            self.memory.add_message("user", query)
            
            # Load session state
            session_state = self.load_session_state(session_id)
            
            # Agentic loop
            iteration = 0
            while iteration < self.max_iterations:
                iteration += 1
                logger.info(f"Iteration {iteration}/{self.max_iterations}")
                
                # Invoke model with tools
                response = self._invoke_with_tools(context)
                
                # Check stop reason
                stop_reason = response.get('stopReason')
                
                if stop_reason == 'end_turn':
                    # Model has final answer
                    final_text = self._extract_text_from_response(response)
                    self.memory.add_message("assistant", final_text)
                    
                    # Save session state
                    self.save_session_state(session_id, {
                        "last_query": query,
                        "iterations": iteration,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    return {
                        "success": True,
                        "response": final_text,
                        "iterations": iteration,
                        "session_id": session_id
                    }
                
                elif stop_reason == 'tool_use':
                    # Model wants to use tools
                    tool_results = self._execute_tools(response, context)
                    
                    # Add tool results to conversation
                    self.memory.add_message(
                        "user",
                        json.dumps(tool_results),
                        metadata={"type": "tool_results"}
                    )
                
                elif stop_reason == 'max_tokens':
                    logger.warning("Max tokens reached")
                    return {
                        "success": False,
                        "error": "Response too long, please simplify your query"
                    }
                
                else:
                    logger.warning(f"Unexpected stop reason: {stop_reason}")
                    break
            
            # Max iterations reached
            return {
                "success": False,
                "error": f"Max iterations ({self.max_iterations}) reached without answer"
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _invoke_with_tools(self, context: Optional[Dict] = None) -> Dict:
        """Invoke Bedrock model with tool configuration"""
        from config import BEDROCK_MODEL_ID
        
        messages = self.memory.get_messages()
        system_prompt = self.get_system_prompt()
        
        # Add context to system prompt if provided
        if context:
            system_prompt += f"\n\nContext: {json.dumps(context)}"
        
        try:
            response = self.bedrock_runtime.converse(
                modelId=BEDROCK_MODEL_ID,
                messages=messages,
                system=[{"text": system_prompt}],
                toolConfig={"tools": self.tool_registry.get_tools()},
                inferenceConfig={
                    "temperature": 0.0,
                    "maxTokens": 4096
                }
            )
            return response
        except Exception as e:
            logger.error(f"Bedrock invocation error: {str(e)}")
            raise
    
    def _execute_tools(
        self, 
        response: Dict, 
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Execute tools requested by the model"""
        tool_results = []
        
        output = response.get('output', {})
        message = output.get('message', {})
        content = message.get('content', [])
        
        for content_block in content:
            if 'toolUse' in content_block:
                tool_use = content_block['toolUse']
                tool_name = tool_use['name']
                tool_input = tool_use['input']
                tool_use_id = tool_use['toolUseId']
                
                logger.info(f"Executing tool: {tool_name}")
                
                # Execute tool with context
                if context:
                    tool_input['_context'] = context
                
                result = self.tool_registry.execute_tool(tool_name, tool_input)
                
                # Format result for Bedrock
                tool_results.append({
                    "toolUseId": tool_use_id,
                    "content": [{"json": result.to_dict()}]
                })
        
        return tool_results
    
    def _extract_text_from_response(self, response: Dict) -> str:
        """Extract text content from Bedrock response"""
        output = response.get('output', {})
        message = output.get('message', {})
        content = message.get('content', [])
        
        text_parts = []
        for content_block in content:
            if 'text' in content_block:
                text_parts.append(content_block['text'])
        
        return ' '.join(text_parts)
    
    def save_session_state(self, session_id: str, state: Dict[str, Any]):
        """Save session state to DynamoDB"""
        from config import DYNAMODB_SESSION_TABLE
        
        try:
            table = self.dynamodb.Table(DYNAMODB_SESSION_TABLE)
            table.put_item(
                Item={
                    'session_id': session_id,
                    'persona': self.persona,
                    'agent_name': self.agent_name,
                    'state': json.dumps(state),
                    'timestamp': datetime.utcnow().isoformat(),
                    'ttl': int(datetime.utcnow().timestamp()) + 86400  # 24 hours
                }
            )
            logger.info(f"Saved session state for {session_id}")
        except Exception as e:
            logger.error(f"Error saving session state: {str(e)}")
    
    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session state from DynamoDB"""
        from config import DYNAMODB_SESSION_TABLE
        
        try:
            table = self.dynamodb.Table(DYNAMODB_SESSION_TABLE)
            response = table.get_item(Key={'session_id': session_id})
            if 'Item' in response:
                return json.loads(response['Item']['state'])
        except Exception as e:
            logger.error(f"Error loading session state: {str(e)}")
        
        return None
    
    def reset_conversation(self):
        """Reset conversation memory"""
        self.memory.clear()
        logger.info(f"Reset conversation for {self.agent_name}")


class ToolExecutionError(Exception):
    """Custom exception for tool execution errors"""
    pass


class AgentError(Exception):
    """Custom exception for agent errors"""
    pass
