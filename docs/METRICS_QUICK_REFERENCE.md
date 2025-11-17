# Metrics System Quick Reference

## Initialization

```python
from metrics_collector import MetricsCollector
from config_manager import ConfigurationManager

# With config
config = ConfigurationManager(environment="prod")
metrics = MetricsCollector(region="us-east-1", config=config)

# Simple
metrics = MetricsCollector(region="us-east-1")
```

## Record Query Metrics

```python
metrics.record_query(
    persona="warehouse_manager",
    agent="inventory_optimizer",
    query="What items need reordering?",
    latency_ms=1250.5,
    success=True,
    token_count=1500,
    session_id="session123",
    user_id="user456",
    intent="optimization"
)
```

## Record Business Metrics

```python
metrics.record_business_metric(
    metric_name="ItemsOptimized",
    value=45,
    unit="Count",
    dimensions={"Warehouse": "WH-001", "Category": "Electronics"}
)
```

## Record Errors

```python
metrics.record_error(
    persona="field_engineer",
    agent="logistics_agent",
    error_type="database_timeout",
    error_message="Query exceeded timeout",
    context={"query": "Complex query", "timeout": 30}
)
```

## Get Statistics

```python
stats = metrics.get_stats()
# Returns:
# {
#   'total_queries': 100,
#   'successful_queries': 95,
#   'failed_queries': 5,
#   'success_rate_percent': 95.0,
#   'average_latency_ms': 1250.5,
#   'total_tokens_used': 150000,
#   'average_tokens_per_query': 1500.0
# }
```

## Flush Metrics

```python
metrics.flush()  # Manually publish to CloudWatch
```

## CloudWatch Metrics Published

| Metric | Unit | Dimensions |
|--------|------|------------|
| QueryLatency | Milliseconds | Persona, Agent |
| QueryCount | Count | Persona, Agent, Success |
| TokenUsage | Count | Agent, Persona |
| ErrorCount | Count | Agent, Persona |
| ErrorByType | Count | ErrorType, Agent, Persona |
| ToolExecutionTime | Milliseconds | ToolName, Agent, Success |
| IntentClassification | Count | Intent, Persona |

## CloudWatch Dashboards

- **{prefix}-agents**: Agent performance metrics
- **{prefix}-costs**: Cost tracking metrics

## CloudWatch Alarms

- **{prefix}-high-error-rate**: Error rate > 10%
- **{prefix}-high-latency**: p95 latency > 5000ms
- **{prefix}-high-token-usage**: Hourly tokens > 100,000

## Configuration

```yaml
# config/prod.yaml
monitoring:
  alarm_email: ops-team@example.com
  dashboard_enabled: true
```

## Common Patterns

### Wrap Query Processing

```python
import time

start_time = time.time()
try:
    result = agent.process_query(query, session_id, context)
    success = True
    error_message = None
except Exception as e:
    success = False
    error_message = str(e)
    raise
finally:
    latency_ms = (time.time() - start_time) * 1000
    metrics.record_query(
        persona=persona,
        agent=agent_name,
        query=query,
        latency_ms=latency_ms,
        success=success,
        error_message=error_message,
        session_id=session_id
    )
```

### Track Tool Executions

```python
tool_executions = [
    {"tool_name": "calculate_reorder_points", "duration_ms": 450, "success": True},
    {"tool_name": "forecast_demand", "duration_ms": 320, "success": True}
]

metrics.record_query(
    ...,
    tool_executions=tool_executions
)
```

### Custom Business Metrics

```python
# Inventory optimization
metrics.record_business_metric("ItemsOptimized", 45, "Count", 
    {"Warehouse": "WH-001"})

# Cost savings
metrics.record_business_metric("CostSavings", 12500.50, "None",
    {"Persona": "procurement_specialist"})

# Forecast accuracy
metrics.record_business_metric("ForecastAccuracy", 94.5, "Percent",
    {"Agent": "inventory_optimizer"})
```

## IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    }
  ]
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Metrics not appearing | Check IAM permissions, verify namespace |
| High latency | Increase buffer size, check network |
| Missing dimensions | Ensure all values are strings |
| Buffer not flushing | Call `metrics.flush()` manually |

## Files

- `metrics_collector.py` - Core implementation
- `cdk/monitoring_stack.py` - CloudWatch dashboards/alarms
- `test_metrics_collector.py` - Unit tests
- `examples/metrics_usage_example.py` - Examples
- `docs/METRICS_COLLECTOR_GUIDE.md` - Full guide
- `docs/METRICS_INTEGRATION_GUIDE.md` - Integration guide

## Links

- [Full Documentation](./METRICS_COLLECTOR_GUIDE.md)
- [Integration Guide](./METRICS_INTEGRATION_GUIDE.md)
- [Implementation Summary](./TASK_9_IMPLEMENTATION_SUMMARY.md)
- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
