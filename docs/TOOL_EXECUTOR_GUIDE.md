# Tool Executor Framework Guide

## Overview

The Tool Executor framework provides asynchronous, parallel tool execution with automatic retry logic, timeout handling, and comprehensive status tracking for Lambda-based agent tools.

**Requirements Implemented:**
- 17.1: Parallel tool execution
- 17.2: Timeout handling for long-running tools
- 17.3: Retry logic with exponential backoff
- 17.4: Tool execution status tracking
- 17.5: Fallback responses on failure

## Architecture

### Core Components

1. **ToolExecutor** (`tool_executor.py`)
   - Main class for executing tools asynchronously
   - Manages parallel execution using asyncio
   - Tracks execution history and statistics
   - Implements retry logic with exponential backoff

2. **ToolExecutionRequest**
   - Data class representing a tool execution request
   - Contains tool name, Lambda function name, input data, timeout, and retry settings

3. **ToolExecutionResult**
   - Data class representing the result of a tool execution
   - Includes status, result data, error information, execution time, and attempt count

4. **ToolExecutionStatus**
   - Enum for tool execution states: PENDING, RUNNING, SUCCESS, FAILED, TIMEOUT, RETRYING

### Integration Points

- **BaseAgent**: Extended with async tool execution methods
- **Specialist Agents**: Updated to use ToolExecutor when available
- **Lambda Functions**: Updated to return structured responses
- **Orchestrator**: Initializes and distributes ToolExecutor to agents

## Usage

### Basic Tool Execution

```python
from tool_executor import ToolExecutor, ToolExecutionRequest

# Initialize executor
executor = ToolExecutor(region="us-east-1", max_workers=10)

# Create execution request
request = ToolExecutionRequest(
    tool_name="calculate_reorder_points",
    function_name="inventory-optimizer-lambda",
    input_data={"warehouse_code": "WH001"},
    timeout_seconds=30,
    max_retries=3
)

# Execute synchronously
result = executor.execute_tool_sync(request)

if result.is_success():
    print(f"Result: {result.result}")
    print(f"Execution time: {result.execution_time_ms}ms")
else:
    print(f"Error: {result.error}")
```

### Parallel Tool Execution

```python
# Create multiple requests
requests = [
    ToolExecutionRequest(
        tool_name="calculate_reorder_points",
        function_name="inventory-optimizer-lambda",
        input_data={"warehouse_code": "WH001"}
    ),
    ToolExecutionRequest(
        tool_name="identify_stockout_risks",
        function_name="inventory-optimizer-lambda",
        input_data={"warehouse_code": "WH001", "days_ahead": 7}
    ),
    ToolExecutionRequest(
        tool_name="forecast_demand",
        function_name="inventory-optimizer-lambda",
        input_data={"product_code": "P001", "warehouse_code": "WH001"}
    )
]

# Execute all in parallel
results = executor.execute_tools_sync(requests, timeout=60)

for result in results:
    print(f"{result.tool_name}: {result.status.value}")
```

### Using in Agents

Agents automatically use ToolExecutor when available:

```python
from agents import InventoryOptimizerAgent

# Agent automatically uses ToolExecutor if initialized
agent = InventoryOptimizerAgent(region="us-east-1")

# Tool execution now uses async framework with retry logic
result = agent.execute_tool(
    "calculate_reorder_points",
    {"warehouse_code": "WH001"}
)
```

### Accessing Execution Statistics

```python
# Get overall statistics
stats = executor.get_execution_stats()
print(f"Total executions: {stats['total_executions']}")
print(f"Success rate: {stats['success_rate']}%")
print(f"Average execution time: {stats['avg_execution_time_ms']}ms")

# Get tool-specific statistics
tool_stats = executor.get_tool_stats("calculate_reorder_points")
print(f"Tool executions: {tool_stats['total_executions']}")
print(f"Success rate: {tool_stats['success_rate']}%")

# Get recent executions
recent = executor.get_recent_executions(limit=10)
for execution in recent:
    print(f"{execution['tool_name']}: {execution['status']}")
```

## Configuration

### ToolExecutor Configuration

```python
executor = ToolExecutor(
    region="us-east-1",
    config=config_manager,  # Optional ConfigurationManager
    max_workers=10          # Maximum parallel workers
)
```

Configuration options from ConfigurationManager:
- `agents.tool_timeout_seconds`: Default timeout (default: 30)
- `agents.tool_max_retries`: Default max retries (default: 3)

### Per-Request Configuration

```python
request = ToolExecutionRequest(
    tool_name="my_tool",
    function_name="my-lambda",
    input_data={...},
    timeout_seconds=60,     # Override default timeout
    max_retries=5,          # Override default retries
    metadata={...}          # Optional metadata
)
```

## Retry Logic

The framework implements exponential backoff for retries:

- **Base backoff**: 1 second
- **Backoff formula**: `base_backoff * (2 ^ (attempt - 1))`
- **Example**: 1s, 2s, 4s, 8s...

Retries are triggered on:
- Lambda invocation errors
- Timeout errors
- Application errors from Lambda

## Timeout Handling

Two levels of timeout:

1. **Per-tool timeout**: Individual tool execution timeout
2. **Overall timeout**: Total timeout for parallel execution

```python
# Per-tool timeout
request = ToolExecutionRequest(
    tool_name="my_tool",
    function_name="my-lambda",
    input_data={...},
    timeout_seconds=30  # This tool times out after 30s
)

# Overall timeout for parallel execution
results = executor.execute_tools_sync(
    requests,
    timeout=60  # All tools must complete within 60s
)
```

## Lambda Function Updates

Lambda functions now return structured responses:

```python
def lambda_handler(event, context):
    tool_name = event.get('tool_name')
    tool_input = event.get('input', {})
    start_time = datetime.now()
    
    try:
        # Execute tool logic
        result = execute_tool_logic(tool_name, tool_input)
        
        # Return structured response
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "success": True,
            "result": result,
            "tool_name": tool_name,
            "execution_time_ms": execution_time
        }
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
            "execution_time_ms": execution_time
        }
```

## Error Handling

The framework provides comprehensive error handling:

### Success Response
```python
{
    "success": True,
    "result": {...},
    "execution_time_ms": 150.5,
    "attempts": 1
}
```

### Failure Response
```python
{
    "success": False,
    "error": "Error message",
    "status": "failed",  # or "timeout"
    "execution_time_ms": 300.0,
    "attempts": 3
}
```

### Fallback Behavior

Agents automatically fall back to direct Lambda invocation if ToolExecutor is not available:

```python
# In agent execute_tool method
if self.tool_executor:
    # Use async execution with retry
    result = self.execute_tool_async(...)
else:
    # Fallback to direct Lambda invocation
    result = self.lambda_client.invoke(...)
```

## Monitoring and Observability

### Execution Tracking

All tool executions are tracked in memory:

```python
# Access execution history
for execution in executor.execution_history:
    print(f"Tool: {execution.tool_name}")
    print(f"Status: {execution.status.value}")
    print(f"Time: {execution.execution_time_ms}ms")
    print(f"Attempts: {execution.attempts}")
```

### Statistics

```python
stats = executor.get_execution_stats()
# Returns:
{
    "total_executions": 100,
    "success_count": 95,
    "failure_count": 3,
    "timeout_count": 2,
    "success_rate": 95.0,
    "avg_execution_time_ms": 250.5,
    "avg_attempts": 1.2
}
```

### Logging

The framework uses Python's logging module:

```python
import logging

# Enable debug logging
logging.getLogger('tool_executor').setLevel(logging.DEBUG)
```

Log messages include:
- Tool execution start/completion
- Retry attempts
- Timeout warnings
- Error details

## Best Practices

1. **Set appropriate timeouts**: Consider Lambda execution limits (15 minutes max)
2. **Use parallel execution**: For independent tools, execute in parallel
3. **Monitor statistics**: Track success rates and execution times
4. **Handle failures gracefully**: Check result status before using data
5. **Clear history periodically**: Prevent memory growth in long-running processes

```python
# Clear history after processing
executor.clear_history()
```

## Testing

Run the test suite:

```bash
python test_tool_executor.py
```

Tests cover:
- Basic initialization
- Request/result structures
- Parallel execution setup
- Statistics tracking
- Error handling

## Migration Guide

### For Existing Agents

1. Agents automatically use ToolExecutor when available
2. No code changes required in agent implementations
3. Fallback to direct Lambda invocation if ToolExecutor unavailable

### For New Agents

```python
class MyAgent(BaseAgent):
    def execute_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        # Use ToolExecutor if available
        if self.tool_executor:
            return self.execute_tool_async(
                tool_name=tool_name,
                function_name=LAMBDA_FUNCTION_NAME,
                input_data=tool_input
            )
        
        # Fallback to direct invocation
        return self.lambda_client.invoke(...)
```

## Performance Considerations

- **Parallel execution**: Up to `max_workers` tools execute simultaneously
- **Async overhead**: Minimal overhead for async/await operations
- **Memory usage**: Execution history stored in memory (clear periodically)
- **Network**: Uses ThreadPoolExecutor for Lambda invocations

## Troubleshooting

### Tool Execution Fails

1. Check Lambda function logs
2. Verify timeout settings
3. Review retry attempts in result
4. Check execution statistics

### Timeout Issues

1. Increase per-tool timeout
2. Increase overall timeout for parallel execution
3. Optimize Lambda function performance
4. Check network connectivity

### High Failure Rate

1. Review error messages in results
2. Check Lambda function permissions
3. Verify input data format
4. Monitor Lambda function metrics

## Future Enhancements

Potential improvements:
- Persistent execution history (DynamoDB)
- CloudWatch metrics integration
- Circuit breaker pattern
- Tool execution caching
- Distributed tracing support
