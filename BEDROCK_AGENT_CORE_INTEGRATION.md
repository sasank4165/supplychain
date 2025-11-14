## Amazon Bedrock Agent Core Integration

This document describes how the Supply Chain Agentic AI application integrates patterns from [Amazon Bedrock Agent Core samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples).

## Key Patterns Implemented

### 1. Enhanced Base Agent Architecture

**File**: `agents/enhanced_base_agent.py`

**Patterns from Agent Core**:
- ✅ **Tool Registry Pattern**: Centralized tool registration and management
- ✅ **Structured Tool Results**: Consistent result format with status, data, error
- ✅ **Conversation Memory**: Context window management with message history
- ✅ **Agentic Loop (ReAct)**: Reason → Act → Observe pattern
- ✅ **Error Handling**: Graceful error handling with retries
- ✅ **Observability**: Structured logging throughout

```python
from agents.enhanced_base_agent import EnhancedBaseAgent, ToolRegistry

class MyAgent(EnhancedBaseAgent):
    def _register_tools(self):
        self.tool_registry.register_tool(
            name="my_tool",
            description="Tool description",
            input_schema={...},
            handler=self._handle_my_tool
        )
```

### 2. Tool Registry with Validation

**Pattern**: Centralized tool management with type-safe registration

```python
class ToolRegistry:
    def register_tool(self, name, description, input_schema, handler):
        # Validates and registers tool
        # Stores handler for execution
        
    def execute_tool(self, name, input_data):
        # Executes tool with error handling
        # Returns structured ToolResult
```

**Benefits**:
- Type-safe tool definitions
- Centralized validation
- Consistent error handling
- Easy to test and mock

### 3. Structured Tool Results

**Pattern**: Consistent result format across all tools

```python
@dataclass
class ToolResult:
    status: ToolStatus  # SUCCESS, ERROR, PARTIAL
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict] = None
```

**Benefits**:
- Predictable response format
- Easy error detection
- Metadata for debugging
- Serializable for logging

### 4. Conversation Memory Management

**Pattern**: Manages conversation history with context window limits

```python
class ConversationMemory:
    def add_message(self, role, content, metadata=None):
        # Adds message to history
        # Automatically trims to max_messages
        
    def get_messages(self):
        # Returns messages in Bedrock format
```

**Benefits**:
- Automatic context window management
- Preserves conversation flow
- Metadata tracking
- Easy to persist/restore

### 5. Agentic Loop (ReAct Pattern)

**Pattern**: Iterative reasoning and action loop

```python
def process_query(self, query, session_id, context):
    iteration = 0
    while iteration < max_iterations:
        # 1. Reason: Invoke model with tools
        response = self._invoke_with_tools(context)
        
        # 2. Act: Execute tools if requested
        if stop_reason == 'tool_use':
            tool_results = self._execute_tools(response, context)
            
        # 3. Observe: Add results to conversation
        self.memory.add_message("user", tool_results)
        
        # 4. Repeat or return final answer
        if stop_reason == 'end_turn':
            return final_answer
```

**Benefits**:
- Multi-step reasoning
- Tool chaining
- Iterative refinement
- Prevents infinite loops

### 6. Enhanced Error Handling

**Pattern**: Graceful error handling with structured exceptions

```python
class ToolExecutionError(Exception):
    """Custom exception for tool execution errors"""
    pass

class AgentError(Exception):
    """Custom exception for agent errors"""
    pass

# Usage
try:
    result = self.tool_registry.execute_tool(name, input)
except ToolExecutionError as e:
    logger.error(f"Tool error: {e}")
    return ToolResult(status=ToolStatus.ERROR, error=str(e))
```

**Benefits**:
- Specific error types
- Better debugging
- Graceful degradation
- User-friendly error messages

### 7. Observability with Structured Logging

**Pattern**: Comprehensive logging at all levels

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Throughout code
logger.info(f"Executing tool: {tool_name}")
logger.error(f"Tool execution error: {str(e)}")
logger.warning(f"Max iterations reached")
```

**Benefits**:
- Easy debugging
- Performance monitoring
- Audit trail
- CloudWatch integration

## Comparison: Original vs Enhanced

### Original Base Agent

```python
class BaseAgent(ABC):
    def process_query(self, query, session_id, context):
        # Direct Bedrock invocation
        response = self.bedrock_runtime.converse(...)
        
        # Manual tool handling
        if 'toolUse' in response:
            # Execute tools manually
            pass
        
        return response
```

**Limitations**:
- No tool registry
- Manual tool execution
- No conversation memory
- Limited error handling
- No iteration control

### Enhanced Base Agent

```python
class EnhancedBaseAgent(ABC):
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.memory = ConversationMemory()
        self._register_tools()
    
    def process_query(self, query, session_id, context):
        # Agentic loop with tool registry
        while iteration < max_iterations:
            response = self._invoke_with_tools(context)
            
            if stop_reason == 'tool_use':
                # Automatic tool execution via registry
                tool_results = self._execute_tools(response, context)
            
            if stop_reason == 'end_turn':
                return final_answer
```

**Improvements**:
- ✅ Tool registry pattern
- ✅ Automatic tool execution
- ✅ Conversation memory
- ✅ Structured error handling
- ✅ Iteration control
- ✅ Better observability

## Migration Guide

### Step 1: Update Imports

```python
# Old
from agents.base_agent import BaseAgent

# New
from agents.enhanced_base_agent import EnhancedBaseAgent
```

### Step 2: Update Agent Class

```python
# Old
class MyAgent(BaseAgent):
    def get_tools(self):
        return [{"toolSpec": {...}}]
    
    def process_query(self, query, session_id, context):
        # Manual implementation
        pass

# New
class MyAgent(EnhancedBaseAgent):
    def _register_tools(self):
        self.tool_registry.register_tool(
            name="my_tool",
            description="...",
            input_schema={...},
            handler=self._handle_my_tool
        )
    
    def get_system_prompt(self):
        return "You are an expert..."
    
    def _handle_my_tool(self, input_data):
        # Tool implementation
        return result
```

### Step 3: Update Tool Handlers

```python
# Old
def execute_tool(self, tool_name, tool_input):
    if tool_name == "my_tool":
        # Execute
        return result

# New
def _handle_my_tool(self, input_data):
    try:
        # Extract context
        context = input_data.pop('_context', None)
        
        # Execute tool
        result = do_something(input_data)
        
        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
```

### Step 4: Update Orchestrator

```python
# Old
result = agent.process_query(query, session_id)

# New
result = agent.process_query(query, session_id, context={
    "username": user['username'],
    "groups": user['groups'],
    "persona": user['persona']
})
```

## Usage Examples

### Example 1: Enhanced Inventory Optimizer

```python
from agents.enhanced_inventory_optimizer import EnhancedInventoryOptimizerAgent

# Initialize agent
agent = EnhancedInventoryOptimizerAgent(region="us-east-1")

# Process query with context
result = agent.process_query(
    query="What products are at risk of stockout in warehouse WH01?",
    session_id="session123",
    context={
        "username": "warehouse_manager1",
        "groups": ["warehouse_managers"],
        "persona": "warehouse_manager"
    }
)

# Result structure
{
    "success": True,
    "response": "Based on current inventory levels...",
    "iterations": 2,
    "session_id": "session123"
}
```

### Example 2: Tool Registry Usage

```python
# Register custom tool
agent.tool_registry.register_tool(
    name="custom_analysis",
    description="Perform custom inventory analysis",
    input_schema={
        "type": "object",
        "properties": {
            "warehouse_code": {"type": "string"},
            "analysis_type": {"type": "string"}
        },
        "required": ["warehouse_code"]
    },
    handler=lambda input: {"result": "analysis complete"}
)

# Tool is automatically available to agent
```

### Example 3: Conversation Memory

```python
# Add messages manually
agent.memory.add_message("user", "Show me inventory levels")
agent.memory.add_message("assistant", "Here are the levels...")

# Get conversation history
messages = agent.memory.get_messages()

# Clear history
agent.reset_conversation()
```

## Best Practices

### 1. Tool Design

```python
# ✅ Good: Specific, focused tool
self.tool_registry.register_tool(
    name="calculate_reorder_points",
    description="Calculate optimal reorder points for products",
    input_schema={
        "type": "object",
        "properties": {
            "warehouse_code": {"type": "string"},
            "product_codes": {"type": "array"}
        }
    },
    handler=self._handle_reorder_points
)

# ❌ Bad: Vague, multi-purpose tool
self.tool_registry.register_tool(
    name="do_inventory_stuff",
    description="Does various inventory things",
    ...
)
```

### 2. Error Handling

```python
# ✅ Good: Specific error handling
def _handle_tool(self, input_data):
    try:
        result = execute_operation(input_data)
        return result
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise ToolExecutionError(f"Invalid input: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

# ❌ Bad: Silent failures
def _handle_tool(self, input_data):
    try:
        return execute_operation(input_data)
    except:
        return {}
```

### 3. System Prompts

```python
# ✅ Good: Clear, specific instructions
def get_system_prompt(self):
    return """You are an inventory optimization expert.

Your role:
- Analyze inventory data
- Provide actionable recommendations
- Prevent stockouts
- Minimize costs

Use tools to get accurate data before making recommendations."""

# ❌ Bad: Vague instructions
def get_system_prompt(self):
    return "You help with inventory."
```

### 4. Logging

```python
# ✅ Good: Structured, informative logging
logger.info(f"Processing query for session {session_id}")
logger.info(f"Iteration {iteration}/{max_iterations}")
logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
logger.error(f"Tool execution failed: {error}", exc_info=True)

# ❌ Bad: Minimal or no logging
print("Processing...")
```

## Testing

### Unit Tests

```python
import unittest
from agents.enhanced_inventory_optimizer import EnhancedInventoryOptimizerAgent

class TestEnhancedAgent(unittest.TestCase):
    def setUp(self):
        self.agent = EnhancedInventoryOptimizerAgent()
    
    def test_tool_registration(self):
        tools = self.agent.tool_registry.get_tools()
        self.assertEqual(len(tools), 4)
        
        tool_names = [t['toolSpec']['name'] for t in tools]
        self.assertIn('calculate_reorder_points', tool_names)
    
    def test_tool_execution(self):
        result = self.agent.tool_registry.execute_tool(
            'calculate_reorder_points',
            {'warehouse_code': 'WH01'}
        )
        self.assertEqual(result.status, ToolStatus.SUCCESS)
```

### Integration Tests

```python
def test_full_query_flow():
    agent = EnhancedInventoryOptimizerAgent()
    
    result = agent.process_query(
        query="Show stockout risks in WH01",
        session_id="test123",
        context={"persona": "warehouse_manager"}
    )
    
    assert result['success'] == True
    assert 'response' in result
    assert result['iterations'] > 0
```

## Performance Considerations

### 1. Conversation Memory

- Default max_messages: 20
- Adjust based on context window size
- Clear memory for long-running sessions

### 2. Tool Execution

- Tools execute synchronously
- Consider async for long-running operations
- Implement timeouts for external calls

### 3. Iteration Limits

- Default max_iterations: 10
- Prevents infinite loops
- Adjust based on complexity

## Monitoring & Observability

### CloudWatch Logs

```python
# Logs are automatically sent to CloudWatch
# Filter patterns:
# - "ERROR" - All errors
# - "Executing tool" - Tool usage
# - "Iteration" - Agent loops
```

### Metrics

```python
# Custom metrics to track:
- Tool execution count
- Average iterations per query
- Error rate by tool
- Response time
```

### X-Ray Tracing

```python
# Lambda functions have X-Ray enabled
# Trace:
- Bedrock invocations
- Tool executions
- DynamoDB operations
```

## References

- [Amazon Bedrock Agent Core Samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples)
- [Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)
- [ReAct Pattern](https://arxiv.org/abs/2210.03629)
- [Tool Use with Claude](https://docs.anthropic.com/claude/docs/tool-use)

## Next Steps

1. **Migrate Remaining Agents**: Update SQL, Logistics, and Supplier agents
2. **Add Async Support**: For long-running tool operations
3. **Implement Caching**: Cache tool results for common queries
4. **Add Metrics**: Custom CloudWatch metrics for monitoring
5. **Enhance Testing**: More comprehensive test coverage
