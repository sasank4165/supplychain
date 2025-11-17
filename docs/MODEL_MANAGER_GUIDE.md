# ModelManager Implementation Guide

## Overview

The ModelManager provides centralized model selection, configuration, and management for Amazon Bedrock models in the Supply Chain Agentic AI Application. It enables per-agent model configuration, automatic fallback logic, compatibility validation, and comprehensive usage metrics collection.

## Features

### 1. Per-Agent Model Configuration

Configure different models for different agents based on their requirements:

```yaml
# config/dev.yaml
agents:
  default_model: anthropic.claude-3-5-sonnet-20241022-v2:0
  
  sql_agent:
    enabled: true
    model: anthropic.claude-3-5-sonnet-20241022-v2:0  # Use Sonnet for complex SQL
    timeout_seconds: 60
  
  inventory_optimizer:
    enabled: true
    model: anthropic.claude-3-5-haiku-20241022-v1:0  # Use Haiku for cost savings
    timeout_seconds: 90
```

### 2. Automatic Model Fallback

If a primary model fails or is unavailable, ModelManager automatically falls back to an alternative model:

**Fallback Strategy:**
- Claude Sonnet → Claude Haiku (cheaper, faster)
- Claude Opus → Claude Sonnet (cheaper)
- Claude Haiku → Claude Sonnet (more capable)
- Titan/Llama → Claude Sonnet (most balanced)

### 3. Model Compatibility Validation

Validates that models support required features (e.g., tools, streaming) before invocation:

```python
is_compatible, error = model_manager.validate_model_compatibility(
    'amazon.titan-text-premier-v1:0',
    requires_tools=True
)
# Returns: (False, "Model does not support tools")
```

### 4. Usage Metrics Collection

Automatically collects and publishes metrics to CloudWatch:

**Metrics Collected:**
- Model latency (milliseconds)
- Input/output token counts
- Success/failure rates
- Cost per invocation
- Model usage by agent

**CloudWatch Namespace:** `{project-prefix}/Models`

## Usage

### Basic Usage

```python
from config_manager import ConfigurationManager
from model_manager import ModelManager

# Initialize
config = ConfigurationManager('dev')
model_manager = ModelManager(config)

# Invoke model for an agent
response = model_manager.invoke_model(
    agent_name='sql_agent',
    messages=[{"role": "user", "content": [{"text": "Hello"}]}],
    system_prompt="You are a SQL expert",
    use_fallback=True
)

if response['success']:
    print(f"Model used: {response['model_id']}")
    print(f"Latency: {response['latency_ms']}ms")
    print(f"Cost: ${response['cost']:.4f}")
    print(f"Tokens: {response['usage']['total_tokens']}")
```

### Integration with Agents

Agents automatically use ModelManager when available:

```python
from agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def process_query(self, query: str, session_id: str, context=None):
        # ModelManager is automatically used if available
        response = self.invoke_bedrock_model(
            prompt=query,
            system_prompt="You are a helpful assistant"
        )
        return {"response": response}
```

### Integration with Orchestrator

The orchestrator automatically initializes ModelManager and passes it to agents:

```python
from orchestrator import SupplyChainOrchestrator

# ModelManager is automatically initialized
orchestrator = SupplyChainOrchestrator()

# All agents will use ModelManager for model invocations
result = orchestrator.process_query(
    query="Show me inventory levels",
    persona="warehouse_manager",
    session_id="session-123"
)
```

## Model Catalog

### Supported Models

| Model ID | Family | Max Tokens | Tools | Streaming | Cost (Input/Output per 1K) |
|----------|--------|------------|-------|-----------|---------------------------|
| anthropic.claude-3-5-sonnet-20241022-v2:0 | Claude | 8192 | ✓ | ✓ | $0.003 / $0.015 |
| anthropic.claude-3-5-haiku-20241022-v1:0 | Claude | 8192 | ✓ | ✓ | $0.001 / $0.005 |
| anthropic.claude-3-opus-20240229-v1:0 | Claude | 4096 | ✓ | ✓ | $0.015 / $0.075 |
| amazon.titan-text-premier-v1:0 | Titan | 3072 | ✗ | ✓ | $0.0005 / $0.0015 |
| meta.llama3-70b-instruct-v1:0 | Llama | 2048 | ✗ | ✓ | $0.00265 / $0.0035 |

### Model Selection Guidelines

**For SQL Generation (sql_agent):**
- Recommended: Claude Sonnet (best SQL accuracy)
- Alternative: Claude Haiku (faster, lower cost)

**For Inventory Optimization:**
- Recommended: Claude Haiku (cost-effective for calculations)
- Alternative: Claude Sonnet (more complex analysis)

**For Logistics Planning:**
- Recommended: Claude Sonnet (complex routing logic)
- Alternative: Claude Opus (highest capability)

**For Supplier Analysis:**
- Recommended: Claude Sonnet (balanced performance)
- Alternative: Claude Haiku (cost savings)

## Configuration

### Environment-Specific Configuration

**Development:**
```yaml
agents:
  default_model: anthropic.claude-3-5-sonnet-20241022-v2:0
  context_window_size: 5
  
  sql_agent:
    model: anthropic.claude-3-5-haiku-20241022-v1:0  # Use cheaper model
```

**Production:**
```yaml
agents:
  default_model: anthropic.claude-3-5-sonnet-20241022-v2:0
  context_window_size: 10
  
  sql_agent:
    model: anthropic.claude-3-5-sonnet-20241022-v2:0  # Use best model
```

## Metrics and Monitoring

### CloudWatch Metrics

ModelManager publishes the following metrics to CloudWatch:

**Metric: ModelLatency**
- Unit: Milliseconds
- Dimensions: Agent, Model
- Description: Time taken for model invocation

**Metric: InputTokens**
- Unit: Count
- Dimensions: Agent, Model
- Description: Number of input tokens processed

**Metric: OutputTokens**
- Unit: Count
- Dimensions: Agent, Model
- Description: Number of output tokens generated

**Metric: ModelInvocations**
- Unit: Count
- Dimensions: Agent, Model, Success
- Description: Total number of model invocations

**Metric: ModelCost**
- Unit: None (USD)
- Dimensions: Agent, Model
- Description: Cost of model invocation

### Usage Summary

Get a summary of buffered metrics:

```python
summary = model_manager.get_usage_summary()
print(f"Total invocations: {summary['total_invocations']}")
print(f"Total cost: ${summary['total_cost_usd']:.4f}")
print(f"Average latency: {summary['average_latency_ms']:.2f}ms")
```

### Flushing Metrics

Ensure all metrics are published before shutdown:

```python
# Flush buffered metrics to CloudWatch
model_manager.flush_metrics()
```

## Error Handling

### Model Unavailable

If a model is unavailable, ModelManager automatically tries the fallback:

```python
# Primary model fails -> automatically tries fallback
response = model_manager.invoke_model(
    agent_name='sql_agent',
    messages=messages,
    use_fallback=True  # Enable automatic fallback
)

if response.get('fallback_used'):
    print(f"Fallback model used: {response['model_id']}")
```

### No Fallback Available

If both primary and fallback fail, an exception is raised:

```python
try:
    response = model_manager.invoke_model(...)
except ModelManagerError as e:
    print(f"Model invocation failed: {e}")
    # Handle error appropriately
```

### Compatibility Issues

Validate compatibility before invocation:

```python
is_compatible, error = model_manager.validate_model_compatibility(
    model_id='amazon.titan-text-premier-v1:0',
    requires_tools=True
)

if not is_compatible:
    print(f"Model not compatible: {error}")
    # Use a different model
```

## Best Practices

### 1. Use Appropriate Models for Tasks

- **Complex reasoning:** Claude Sonnet or Opus
- **Simple tasks:** Claude Haiku (cost-effective)
- **Tool usage required:** Claude models only
- **Cost-sensitive:** Haiku or Titan

### 2. Enable Fallback in Production

Always enable fallback for production workloads:

```python
response = model_manager.invoke_model(
    agent_name='agent',
    messages=messages,
    use_fallback=True  # Always enable in production
)
```

### 3. Monitor Costs

Regularly review usage metrics to optimize costs:

```python
summary = model_manager.get_usage_summary()
if summary['total_cost_usd'] > threshold:
    # Consider switching to cheaper models
    pass
```

### 4. Validate Model Access

Ensure Bedrock model access is enabled in your AWS account before deployment:

```bash
# Check model availability
aws bedrock list-foundation-models --region us-east-1
```

### 5. Configure Per-Environment

Use different models for different environments:

- **Dev:** Cheaper models (Haiku, Titan)
- **Staging:** Production-like models (Sonnet)
- **Production:** Best models for quality (Sonnet, Opus)

## Troubleshooting

### Issue: Model Access Denied

**Symptom:** `AccessDeniedException` when invoking models

**Solution:**
1. Enable model access in AWS Bedrock console
2. Verify IAM permissions include `bedrock:InvokeModel`
3. Check if model is available in your region

### Issue: High Costs

**Symptom:** Unexpected high costs from model usage

**Solution:**
1. Review usage summary: `model_manager.get_usage_summary()`
2. Switch to cheaper models (Haiku instead of Sonnet)
3. Reduce context window size in configuration
4. Implement caching for repeated queries

### Issue: Slow Response Times

**Symptom:** High latency for model invocations

**Solution:**
1. Use faster models (Haiku instead of Opus)
2. Reduce max_tokens in configuration
3. Optimize prompts to be more concise
4. Consider using streaming for long responses

### Issue: Fallback Not Working

**Symptom:** Errors even with fallback enabled

**Solution:**
1. Check if fallback model has access enabled
2. Verify fallback model supports required features
3. Review CloudWatch logs for detailed errors
4. Ensure AWS credentials are valid

## API Reference

### ModelManager

```python
class ModelManager:
    def __init__(self, config: ConfigurationManager, region: Optional[str] = None)
    
    def get_model_for_agent(self, agent_name: str) -> str
    def get_fallback_model(self, primary_model_id: str) -> Optional[str]
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]
    
    def validate_model_compatibility(
        self,
        model_id: str,
        requires_tools: bool = False,
        requires_streaming: bool = False
    ) -> Tuple[bool, Optional[str]]
    
    def invoke_model(
        self,
        agent_name: str,
        messages: List[Dict[str, Any]],
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_fallback: bool = True,
        **kwargs
    ) -> Dict[str, Any]
    
    def flush_metrics(self)
    def get_usage_summary(self) -> Dict[str, Any]
    def list_available_models(self) -> List[Dict[str, Any]]
```

### ModelConfig

```python
@dataclass
class ModelConfig:
    model_id: str
    model_family: str
    max_tokens: int
    temperature: float
    supports_tools: bool
    supports_streaming: bool
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
```

### ModelUsageMetrics

```python
@dataclass
class ModelUsageMetrics:
    agent_name: str
    model_id: str
    timestamp: datetime
    input_tokens: int
    output_tokens: int
    latency_ms: float
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]
    def get_cost(self, model_config: ModelConfig) -> float
```

## Testing

Run the verification script to test ModelManager:

```bash
python verify_model_manager.py
```

Run unit tests:

```bash
python -m unittest tests.test_model_manager -v
```

## Related Documentation

- [Configuration Management Guide](../cdk/CONFIGURATION_GUIDE.md)
- [Agent Registry Guide](AGENT_REGISTRY_GUIDE.md)
- [Deployment Guide](../DEPLOYMENT.md)
