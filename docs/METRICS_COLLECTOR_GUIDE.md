# Metrics Collector Guide

## Overview

The Metrics Collector provides comprehensive monitoring and analytics capabilities for the Supply Chain Agentic AI Application. It collects performance metrics, tracks errors, publishes to CloudWatch, and provides structured logging for all agent interactions.

## Features

- **Performance Metrics**: Track query latency, success rates, and throughput
- **Token Usage Tracking**: Monitor AI model token consumption for cost optimization
- **Error Tracking**: Capture errors with full context for debugging
- **Custom Business Metrics**: Record domain-specific metrics
- **Structured Logging**: JSON-formatted logs for easy parsing and analysis
- **CloudWatch Integration**: Automatic metric publishing and dashboard visualization
- **Batch Processing**: Efficient metric buffering and batch publishing

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Orchestrator │  │ Agents       │  │ Tool         │      │
│  │              │  │              │  │ Executor     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  MetricsCollector                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  • Record Query Metrics                              │   │
│  │  • Record Business Metrics                           │   │
│  │  • Record Errors with Context                        │   │
│  │  • Structured JSON Logging                           │   │
│  │  • Metrics Buffering                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS CloudWatch                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Metrics      │  │ Dashboards   │  │ Alarms       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Installation

The MetricsCollector is included in the main application. No additional installation required.

```python
from metrics_collector import MetricsCollector, create_metrics_collector
from config_manager import ConfigurationManager
```

## Usage

### Basic Initialization

```python
from metrics_collector import MetricsCollector

# Simple initialization
metrics = MetricsCollector(region="us-east-1")

# With configuration
from config_manager import ConfigurationManager
config = ConfigurationManager(environment="prod")
metrics = MetricsCollector(region="us-east-1", config=config)

# With custom namespace
metrics = MetricsCollector(
    region="us-east-1",
    namespace="MyApp/CustomMetrics"
)
```

### Recording Query Metrics

```python
import time

# Start timing
start_time = time.time()

# Process query
try:
    result = agent.process_query(query, session_id, context)
    success = True
    error_message = None
except Exception as e:
    success = False
    error_message = str(e)

# Calculate latency
latency_ms = (time.time() - start_time) * 1000

# Record metrics
metrics.record_query(
    persona="warehouse_manager",
    agent="inventory_optimizer",
    query="What items need reordering?",
    latency_ms=latency_ms,
    success=success,
    token_count=1250,
    error_message=error_message,
    tool_executions=[
        {
            "tool_name": "calculate_reorder_points",
            "duration_ms": 450,
            "success": True
        }
    ],
    user_id="user123",
    session_id="session456",
    intent="optimization"
)
```

### Recording Business Metrics

```python
# Record inventory optimization metric
metrics.record_business_metric(
    metric_name="ItemsOptimized",
    value=45,
    unit="Count",
    dimensions={
        "Warehouse": "WH-001",
        "Category": "Electronics"
    }
)

# Record cost savings
metrics.record_business_metric(
    metric_name="EstimatedCostSavings",
    value=12500.50,
    unit="None",  # Dollar amount
    dimensions={
        "Persona": "procurement_specialist",
        "OptimizationType": "supplier_consolidation"
    }
)

# Record forecast accuracy
metrics.record_business_metric(
    metric_name="ForecastAccuracy",
    value=94.5,
    unit="Percent",
    dimensions={
        "Agent": "inventory_optimizer",
        "TimeHorizon": "30_days"
    }
)
```

### Recording Errors

```python
# Record error with context
metrics.record_error(
    persona="field_engineer",
    agent="logistics_agent",
    error_type="database_timeout",
    error_message="Query execution exceeded 30 second timeout",
    context={
        "query": "Complex route optimization query",
        "session_id": "session789",
        "user_id": "user456",
        "table": "shipments",
        "timeout_seconds": 30
    }
)

# Record validation error
metrics.record_error(
    persona="warehouse_manager",
    agent="sql_agent",
    error_type="validation_error",
    error_message="Invalid warehouse code format",
    context={
        "warehouse_code": "INVALID",
        "expected_format": "WH-XXX"
    }
)
```

### Getting Statistics

```python
# Get current statistics
stats = metrics.get_stats()
print(f"Total queries: {stats['total_queries']}")
print(f"Success rate: {stats['success_rate_percent']}%")
print(f"Average latency: {stats['average_latency_ms']}ms")
print(f"Average tokens per query: {stats['average_tokens_per_query']}")

# Get metrics summary from CloudWatch
from datetime import datetime, timedelta

end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=24)

summary = metrics.get_metrics_summary(
    start_time=start_time,
    end_time=end_time,
    persona="warehouse_manager",
    agent="inventory_optimizer"
)

print(f"Latency data points: {len(summary['latency'])}")
print(f"Success count: {summary['success_count']}")
print(f"Error count: {summary['error_count']}")
```

### Manual Flushing

```python
# Metrics are automatically flushed when buffer is full
# But you can manually flush if needed

metrics.flush()  # Force flush all buffered metrics
```

## Integration with Orchestrator

The MetricsCollector integrates seamlessly with the orchestrator:

```python
from orchestrator import SupplyChainOrchestrator
from metrics_collector import MetricsCollector
from config_manager import ConfigurationManager
import time

# Initialize
config = ConfigurationManager(environment="prod")
orchestrator = SupplyChainOrchestrator(region="us-east-1", config=config)
metrics = MetricsCollector(region="us-east-1", config=config)

# Process query with metrics
def process_with_metrics(query, persona, session_id, context):
    start_time = time.time()
    
    try:
        result = orchestrator.process_query(query, persona, session_id, context)
        success = result.get("success", False)
        error_message = result.get("error")
        
        # Extract token count if available
        token_count = 0
        if "sql_response" in result:
            token_count += result["sql_response"].get("token_count", 0)
        if "specialist_response" in result:
            token_count += result["specialist_response"].get("token_count", 0)
        
        # Record metrics
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_query(
            persona=persona,
            agent=result.get("intent", "unknown"),
            query=query,
            latency_ms=latency_ms,
            success=success,
            token_count=token_count,
            error_message=error_message,
            session_id=session_id,
            intent=result.get("intent")
        )
        
        return result
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_query(
            persona=persona,
            agent="orchestrator",
            query=query,
            latency_ms=latency_ms,
            success=False,
            error_message=str(e),
            session_id=session_id
        )
        raise

# Use it
result = process_with_metrics(
    query="Show me items with low stock",
    persona="warehouse_manager",
    session_id="session123",
    context={"user_id": "user456"}
)
```

## CloudWatch Metrics

### Standard Metrics

The MetricsCollector publishes the following metrics to CloudWatch:

| Metric Name | Unit | Dimensions | Description |
|-------------|------|------------|-------------|
| `QueryLatency` | Milliseconds | Persona, Agent | Query processing time |
| `QueryCount` | Count | Persona, Agent, Success | Number of queries |
| `TokenUsage` | Count | Agent, Persona | AI model tokens consumed |
| `ErrorCount` | Count | Agent, Persona | Number of errors |
| `ErrorByType` | Count | ErrorType, Agent, Persona | Errors by category |
| `ToolExecutionTime` | Milliseconds | ToolName, Agent, Success | Tool execution duration |
| `IntentClassification` | Count | Intent, Persona | Intent distribution |

### Custom Business Metrics

You can publish any custom metrics relevant to your business:

```python
# Inventory metrics
metrics.record_business_metric(
    metric_name="StockoutRiskItems",
    value=12,
    unit="Count",
    dimensions={"Warehouse": "WH-001", "Severity": "High"}
)

# Logistics metrics
metrics.record_business_metric(
    metric_name="RouteOptimizationSavings",
    value=2500.00,
    unit="None",
    dimensions={"Region": "Northeast", "OptimizationType": "distance"}
)

# Supplier metrics
metrics.record_business_metric(
    metric_name="SupplierPerformanceScore",
    value=87.5,
    unit="Percent",
    dimensions={"Supplier": "SUP-123", "Category": "Electronics"}
)
```

## CloudWatch Dashboards

The monitoring stack creates two dashboards:

### Agent Performance Dashboard

Visualizes:
- Query latency by persona (average, p50, p95, p99)
- Query count by success status
- Token usage by agent
- Error count by agent
- Tool execution time
- Intent classification distribution
- Overall success rate
- Total queries

### Cost Tracking Dashboard

Visualizes:
- Token usage by agent (cost proxy)
- Daily token usage trends
- Query count by persona (usage patterns)
- Average tokens per query

Access dashboards in AWS Console:
```
CloudWatch → Dashboards → {prefix}-agents
CloudWatch → Dashboards → {prefix}-costs
```

## CloudWatch Alarms

The monitoring stack creates the following alarms:

### High Error Rate Alarm
- **Threshold**: Error rate > 10%
- **Evaluation**: 2 consecutive periods of 5 minutes
- **Action**: SNS notification

### High Latency Alarm
- **Threshold**: p95 latency > 5000ms
- **Evaluation**: 2 consecutive periods of 5 minutes
- **Action**: SNS notification

### High Token Usage Alarm
- **Threshold**: Hourly token usage > 100,000
- **Evaluation**: 1 period of 1 hour
- **Action**: SNS notification

Configure alarm email in your environment config:
```yaml
monitoring:
  alarm_email: ops-team@example.com
  dashboard_enabled: true
```

## Structured Logging

All metrics are logged as structured JSON for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "agent_metrics",
  "message": {
    "persona": "warehouse_manager",
    "agent_name": "inventory_optimizer",
    "query": "What items need reordering?",
    "timestamp": "2024-01-15T10:30:45.123Z",
    "latency_ms": 1250.5,
    "success": true,
    "error_message": null,
    "token_count": 1250,
    "tool_executions": [
      {
        "tool_name": "calculate_reorder_points",
        "duration_ms": 450,
        "success": true
      }
    ],
    "user_id": "user123",
    "session_id": "session456",
    "intent": "optimization"
  }
}
```

Error logs include full context:

```json
{
  "timestamp": "2024-01-15T10:35:12.456Z",
  "level": "ERROR",
  "logger": "agent_metrics",
  "message": {
    "error_type": "agent_error",
    "persona": "field_engineer",
    "agent": "logistics_agent",
    "error_category": "database_timeout",
    "error_message": "Query execution exceeded 30 second timeout",
    "timestamp": "2024-01-15T10:35:12.456Z",
    "context": {
      "query": "Complex route optimization query",
      "session_id": "session789",
      "user_id": "user456",
      "table": "shipments",
      "timeout_seconds": 30
    }
  }
}
```

## Best Practices

### 1. Always Record Metrics

Record metrics for every query, even failures:

```python
try:
    result = agent.process_query(query, session_id, context)
    metrics.record_query(..., success=True)
except Exception as e:
    metrics.record_query(..., success=False, error_message=str(e))
    raise
```

### 2. Include Rich Context

Provide as much context as possible for debugging:

```python
metrics.record_error(
    persona=persona,
    agent=agent_name,
    error_type="validation_error",
    error_message=str(e),
    context={
        "query": query,
        "session_id": session_id,
        "user_id": user_id,
        "input_parameters": params,
        "validation_rules": rules
    }
)
```

### 3. Use Consistent Dimensions

Use consistent dimension values for better aggregation:

```python
# Good - consistent naming
dimensions = {"Warehouse": "WH-001", "Category": "Electronics"}

# Bad - inconsistent naming
dimensions = {"warehouse": "wh-001", "cat": "electronics"}
```

### 4. Flush on Shutdown

Ensure metrics are flushed before application shutdown:

```python
import atexit

metrics = MetricsCollector(region="us-east-1", config=config)
atexit.register(metrics.flush)
```

### 5. Monitor Cost Metrics

Track token usage to control costs:

```python
# Set up alerts for high token usage
if stats['total_tokens'] > threshold:
    notify_ops_team("High token usage detected")
```

## Configuration

Configure monitoring in your environment YAML:

```yaml
monitoring:
  alarm_email: ops-team@example.com
  dashboard_enabled: true
  metrics_namespace: custom-namespace  # Optional
  buffer_size: 20  # Metrics buffer size
  
agents:
  default_model: anthropic.claude-3-5-sonnet-20241022-v2:0
  context_window_size: 10
  
  # Per-agent configuration
  inventory_optimizer:
    enabled: true
    model: anthropic.claude-3-5-sonnet-20241022-v2:0
```

## Troubleshooting

### Metrics Not Appearing in CloudWatch

1. Check IAM permissions for `cloudwatch:PutMetricData`
2. Verify namespace is correct
3. Check for errors in application logs
4. Manually flush metrics: `metrics.flush()`

### High Latency in Metric Publishing

1. Increase buffer size to reduce API calls
2. Check network connectivity to CloudWatch
3. Consider async metric publishing

### Missing Dimensions

1. Ensure all dimension values are strings
2. Check for None values in dimensions
3. Validate dimension names (no special characters)

## API Reference

### MetricsCollector

#### `__init__(region, config, namespace)`
Initialize metrics collector.

#### `record_query(persona, agent, query, latency_ms, success, ...)`
Record query metrics.

#### `record_business_metric(metric_name, value, unit, dimensions, timestamp)`
Record custom business metric.

#### `record_error(persona, agent, error_type, error_message, context)`
Record error with context.

#### `get_stats()`
Get current statistics.

#### `get_metrics_summary(start_time, end_time, persona, agent)`
Get metrics summary from CloudWatch.

#### `flush()`
Manually flush metrics buffer.

## Examples

See `examples/metrics_usage_example.py` for complete examples.

## Related Documentation

- [Configuration Manager Guide](./CONFIGURATION_GUIDE.md)
- [Model Manager Guide](./MODEL_MANAGER_GUIDE.md)
- [Agent Registry Guide](./AGENT_REGISTRY_GUIDE.md)
- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
