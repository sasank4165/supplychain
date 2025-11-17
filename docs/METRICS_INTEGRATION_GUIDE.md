# Metrics Integration Guide

## Quick Start: Adding Metrics to Orchestrator

This guide shows how to integrate the MetricsCollector with the existing orchestrator.

## Step 1: Initialize MetricsCollector in Orchestrator

Add the MetricsCollector to the orchestrator's `__init__` method:

```python
# In orchestrator.py, add import
from metrics_collector import MetricsCollector

# In __init__ method, after initializing context_manager:
# Initialize metrics collector
if self.config:
    try:
        self.metrics_collector = MetricsCollector(
            region=region,
            config=self.config
        )
    except Exception as e:
        print(f"Warning: Failed to initialize MetricsCollector: {e}")
        self.metrics_collector = None
else:
    self.metrics_collector = None
```

## Step 2: Add Metrics to process_query Method

Wrap the query processing with metrics collection:

```python
def process_query(
    self, 
    query: str, 
    persona: str, 
    session_id: str,
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """Process user query with metrics collection"""
    
    import time
    start_time = time.time()
    
    # ... existing validation code ...
    
    try:
        # ... existing query processing code ...
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Extract token count from results
        token_count = 0
        if "sql_response" in results:
            token_count += results["sql_response"].get("token_count", 0)
        if "specialist_response" in results:
            token_count += results["specialist_response"].get("token_count", 0)
        
        # Record metrics
        if self.metrics_collector:
            self.metrics_collector.record_query(
                persona=persona,
                agent=results.get("intent", "unknown"),
                query=query,
                latency_ms=latency_ms,
                success=results.get("success", False),
                token_count=token_count,
                error_message=results.get("error"),
                session_id=session_id,
                user_id=context.get("user_id") if context else None,
                intent=results.get("intent")
            )
        
        return results
        
    except Exception as e:
        # Record error metrics
        latency_ms = (time.time() - start_time) * 1000
        
        if self.metrics_collector:
            self.metrics_collector.record_query(
                persona=persona,
                agent="orchestrator",
                query=query,
                latency_ms=latency_ms,
                success=False,
                error_message=str(e),
                session_id=session_id,
                user_id=context.get("user_id") if context else None
            )
            
            self.metrics_collector.record_error(
                persona=persona,
                agent="orchestrator",
                error_type="processing_error",
                error_message=str(e),
                context={
                    "query": query,
                    "session_id": session_id,
                    "user_id": context.get("user_id") if context else None
                }
            )
        
        raise
```

## Step 3: Add Metrics Getter Methods

Add convenience methods to access metrics:

```python
def get_metrics_stats(self) -> Dict[str, Any]:
    """Get current metrics statistics
    
    Returns:
        Dictionary with metrics statistics
    """
    if not self.metrics_collector:
        return {"error": "MetricsCollector not initialized"}
    
    return self.metrics_collector.get_stats()

def flush_metrics(self):
    """Manually flush metrics buffer"""
    if self.metrics_collector:
        self.metrics_collector.flush()
```

## Step 4: Update app.py to Use Metrics

In your Streamlit app, display metrics:

```python
# In app.py
import streamlit as st

# After processing query
result = orchestrator.process_query(query, persona, session_id, context)

# Display metrics in sidebar
with st.sidebar:
    st.subheader("📊 Metrics")
    
    stats = orchestrator.get_metrics_stats()
    if "error" not in stats:
        st.metric("Total Queries", stats['total_queries'])
        st.metric("Success Rate", f"{stats['success_rate_percent']:.1f}%")
        st.metric("Avg Latency", f"{stats['average_latency_ms']:.0f}ms")
        st.metric("Avg Tokens", f"{stats['average_tokens_per_query']:.0f}")
```

## Step 5: Deploy Monitoring Stack

Deploy the CloudWatch monitoring stack:

```bash
# Navigate to CDK directory
cd cdk

# Add monitoring stack to app.py
# In cdk/app.py:
from monitoring_stack import MonitoringStack

# After creating supply_chain_stack:
monitoring_stack = MonitoringStack(
    app,
    f"{config['project']['prefix']}-monitoring",
    config=config,
    env=env
)

# Deploy
cdk deploy --all
```

## Step 6: Configure Alarm Notifications

Update your environment config to enable alarms:

```yaml
# In config/prod.yaml
monitoring:
  alarm_email: ops-team@example.com
  dashboard_enabled: true
```

## Complete Example

Here's a complete example of the updated orchestrator initialization:

```python
class SupplyChainOrchestrator:
    def __init__(self, region: str = "us-east-1", config: Optional[ConfigurationManager] = None):
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        
        # Initialize configuration
        if config is None:
            try:
                self.config = ConfigurationManager()
            except Exception as e:
                print(f"Warning: Failed to load configuration: {e}")
                self.config = None
        else:
            self.config = config
        
        # Initialize model manager
        if self.config:
            try:
                self.model_manager = ModelManager(self.config, region=region)
            except Exception as e:
                print(f"Warning: Failed to initialize ModelManager: {e}")
                self.model_manager = None
        else:
            self.model_manager = None
        
        # Initialize tool executor
        try:
            from tool_executor import ToolExecutor
            self.tool_executor = ToolExecutor(region=region, config=self.config)
        except Exception as e:
            print(f"Warning: Failed to initialize ToolExecutor: {e}")
            self.tool_executor = None
        
        # Initialize context manager
        if self.config:
            try:
                self.context_manager = ConversationContextManager(
                    self.config,
                    region=region,
                    model_manager=self.model_manager
                )
            except Exception as e:
                print(f"Warning: Failed to initialize ConversationContextManager: {e}")
                self.context_manager = None
        else:
            self.context_manager = None
        
        # Initialize metrics collector
        if self.config:
            try:
                from metrics_collector import MetricsCollector
                self.metrics_collector = MetricsCollector(
                    region=region,
                    config=self.config
                )
            except Exception as e:
                print(f"Warning: Failed to initialize MetricsCollector: {e}")
                self.metrics_collector = None
        else:
            self.metrics_collector = None
        
        # Initialize agent registry
        if self.config:
            self.agent_registry = AgentRegistry(
                self.config, 
                auto_discover=True,
                model_manager=self.model_manager
            )
        else:
            self._init_hardcoded_agents(region)
```

## Testing Metrics

Test the metrics integration:

```python
# test_metrics_integration.py
from orchestrator import SupplyChainOrchestrator
from config_manager import ConfigurationManager

def test_metrics_integration():
    # Initialize
    config = ConfigurationManager(environment="dev")
    orchestrator = SupplyChainOrchestrator(region="us-east-1", config=config)
    
    # Process a query
    result = orchestrator.process_query(
        query="Show me items with low stock",
        persona="warehouse_manager",
        session_id="test-session-123",
        context={"user_id": "test-user"}
    )
    
    # Get metrics
    stats = orchestrator.get_metrics_stats()
    
    print("Metrics Statistics:")
    print(f"  Total Queries: {stats['total_queries']}")
    print(f"  Success Rate: {stats['success_rate_percent']}%")
    print(f"  Average Latency: {stats['average_latency_ms']:.2f}ms")
    
    # Flush metrics to CloudWatch
    orchestrator.flush_metrics()
    
    print("\nMetrics flushed to CloudWatch!")

if __name__ == "__main__":
    test_metrics_integration()
```

## Viewing Metrics in CloudWatch

1. **Access Dashboards:**
   - Go to AWS Console → CloudWatch → Dashboards
   - Open `{prefix}-agents` for agent performance
   - Open `{prefix}-costs` for cost tracking

2. **View Metrics:**
   - Go to AWS Console → CloudWatch → Metrics
   - Select namespace: `{prefix}/Agents`
   - Browse available metrics

3. **Check Alarms:**
   - Go to AWS Console → CloudWatch → Alarms
   - View alarm status and history

## Business Metrics Examples

Add custom business metrics for your domain:

```python
# In agent code, after processing
if orchestrator.metrics_collector:
    orchestrator.metrics_collector.record_business_metric(
        metric_name="ItemsOptimized",
        value=len(optimized_items),
        unit="Count",
        dimensions={
            "Warehouse": warehouse_code,
            "Category": category
        }
    )
```

## Troubleshooting

### Metrics Not Appearing

1. Check IAM permissions for `cloudwatch:PutMetricData`
2. Verify metrics collector is initialized
3. Check application logs for errors
4. Manually flush: `orchestrator.flush_metrics()`

### High Latency

1. Metrics are buffered and published in batches
2. Increase buffer size in config if needed
3. Check network connectivity to CloudWatch

## Best Practices

1. **Always Record Metrics**: Even for failures
2. **Include Context**: Add user_id, session_id for debugging
3. **Flush on Shutdown**: Ensure metrics are published
4. **Monitor Costs**: Track token usage regularly
5. **Set Appropriate Alarms**: Tune thresholds based on usage

## Next Steps

1. Deploy monitoring stack
2. Configure alarm notifications
3. Test metrics collection
4. View dashboards
5. Add custom business metrics
6. Set up log aggregation

## Related Documentation

- [Metrics Collector Guide](./METRICS_COLLECTOR_GUIDE.md)
- [Task 9 Implementation Summary](./TASK_9_IMPLEMENTATION_SUMMARY.md)
- [Configuration Guide](./CONFIGURATION_GUIDE.md)
