# Orchestrator Integration Quick Reference

## Overview

The orchestrator now integrates six major architecture components for a production-ready system.

## Component Status

| Component | Status | Purpose |
|-----------|--------|---------|
| AgentRegistry | ✓ Integrated | Dynamic agent discovery and management |
| ModelManager | ✓ Integrated | Centralized model selection and metrics |
| ConversationContextManager | ✓ Integrated | Conversation history management |
| ToolExecutor | ✓ Integrated | Parallel tool execution with retry |
| MetricsCollector | ✓ Integrated | Monitoring and analytics |
| AccessController | ✓ Integrated | Fine-grained access control |

## Quick Start

### Initialize Orchestrator
```python
from orchestrator import SupplyChainOrchestrator

# Auto-initializes all components
orchestrator = SupplyChainOrchestrator()
```

### Process Query with Full Integration
```python
result = orchestrator.process_query(
    query="Show me inventory levels",
    persona="warehouse_manager",
    session_id="session-123",
    context={
        'user_id': 'user-456',
        'groups': ['warehouse_managers'],
        'persona': 'warehouse_manager'
    }
)
# Automatically:
# - Checks access control
# - Retrieves conversation history
# - Routes to appropriate agents
# - Records metrics
# - Stores response in history
```

## Metrics & Monitoring

### Get Current Statistics
```python
stats = orchestrator.get_metrics_stats()
# Returns: total_queries, successful_queries, failed_queries,
#          success_rate_percent, average_latency_ms, total_tokens_used
```

### Get CloudWatch Metrics
```python
from datetime import datetime, timedelta

summary = orchestrator.get_metrics_summary(
    start_time=datetime.utcnow() - timedelta(hours=1),
    end_time=datetime.utcnow(),
    persona="warehouse_manager"
)
```

### Flush Metrics Before Shutdown
```python
orchestrator.flush_metrics()
```

## Conversation Management

### Get Conversation History
```python
history = orchestrator.get_conversation_history(
    session_id="session-123",
    max_messages=10
)
```

### Clear Conversation
```python
result = orchestrator.clear_conversation_history("session-123")
```

### Get Session Summary
```python
summary = orchestrator.get_session_summary("session-123")
# Returns: total_messages, total_tokens, role_counts, timestamps
```

## Agent Management

### Get All Registered Agents
```python
agents = orchestrator.get_all_registered_agents()
# Returns: registered_agents, agent_count, available_classes, capabilities
```

### Get Agent Capabilities
```python
capabilities = orchestrator.get_agent_capabilities("warehouse_manager")
# Returns: sql_agent info, specialist_agent info, tools list
```

## Tool Execution

### Get Tool Statistics
```python
stats = orchestrator.get_tool_execution_stats()
# Returns: total_executions, success_count, failure_count,
#          timeout_count, success_rate, avg_execution_time_ms
```

### Get Tool-Specific Stats
```python
tool_stats = orchestrator.get_tool_stats_by_name("calculate_reorder_points")
```

## Metrics Published to CloudWatch

| Metric Name | Dimensions | Description |
|-------------|------------|-------------|
| QueryLatency | Persona, Agent | Query processing time (ms) |
| QueryCount | Persona, Agent, Success | Number of queries |
| TokenUsage | Agent, Persona | Token consumption |
| ErrorCount | Agent, Persona | Error count |
| ToolExecutionTime | ToolName, Agent, Success | Tool execution duration |
| IntentClassification | Intent, Persona | Intent distribution |

## Error Handling

All components gracefully degrade if initialization fails:
- Warning messages logged
- Component set to None
- Orchestrator continues with available components

## Environment Variables

```bash
ENVIRONMENT=dev|staging|prod
AWS_REGION=us-east-1
CONVERSATION_TABLE=table-name
DYNAMODB_CONVERSATION_TABLE=table-name
```

## Configuration

Components configured via `config/{environment}.yaml`:
```yaml
agents:
  default_model: "anthropic.claude-3-5-sonnet-20241022-v2:0"
  context_window_size: 10
  conversation_retention_days: 30
  tool_timeout_seconds: 30
  tool_max_retries: 3
```

## Testing

Run integration tests:
```bash
python test_orchestrator_integration.py
```

Expected output:
```
✓ PASS: Initialization
✓ PASS: AgentRegistry
✓ PASS: MetricsCollector
✓ PASS: AccessController
✓ PASS: ToolExecutor

Total: 5/5 tests passed
```

## Common Patterns

### Query with Metrics Tracking
```python
import time

start = time.time()
result = orchestrator.process_query(...)
latency = (time.time() - start) * 1000

# Metrics automatically recorded in process_query
stats = orchestrator.get_metrics_stats()
```

### Multi-turn Conversation
```python
session_id = "user-session-123"

# First query
result1 = orchestrator.process_query(
    query="Show inventory levels",
    persona="warehouse_manager",
    session_id=session_id,
    context=user_context
)

# Second query (with history)
result2 = orchestrator.process_query(
    query="Which items are low?",
    persona="warehouse_manager",
    session_id=session_id,
    context=user_context
)
# Automatically includes conversation history
```

### Access Control Check
```python
# Automatic in process_query, but can check manually:
if orchestrator.access_controller:
    authorized = orchestrator.access_controller.authorize(
        user_context,
        "warehouse_manager"
    )
```

## Troubleshooting

### Component Not Initialized
Check logs for warning messages:
```
Warning: Failed to initialize MetricsCollector: <error>
```

### Metrics Not Publishing
- Check AWS credentials
- Verify CloudWatch permissions
- Call `flush_metrics()` before shutdown

### Access Denied Errors
- Verify user has correct groups in context
- Check PERSONA_TABLE_ACCESS configuration
- Review audit logs in CloudWatch

## Performance Tips

1. **Batch Metrics**: Metrics auto-batch (20 items) before publishing
2. **Context Window**: Adjust `context_window_size` based on needs
3. **Tool Timeout**: Configure per-agent timeout values
4. **Parallel Tools**: ToolExecutor uses 10 workers by default

## Related Documentation

- [Task 16 Implementation Summary](TASK_16_IMPLEMENTATION_SUMMARY.md)
- [Metrics Collector Guide](METRICS_COLLECTOR_GUIDE.md)
- [Access Controller Guide](ACCESS_CONTROLLER_GUIDE.md)
- [Tool Executor Guide](TOOL_EXECUTOR_GUIDE.md)
- [Conversation Context Guide](CONVERSATION_CONTEXT_GUIDE.md)
