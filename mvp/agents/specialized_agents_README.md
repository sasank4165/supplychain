# Specialized Agents

This document describes the specialized agents for the Supply Chain MVP system.

## Overview

The specialized agents provide domain-specific optimization and analysis capabilities by invoking AWS Lambda functions and integrating with Amazon Bedrock for AI orchestration. Each agent is designed for a specific persona and provides tools tailored to their needs.

## Agents

### 1. Inventory Agent

**Purpose**: Inventory optimization for Warehouse Managers

**Lambda Function**: `supply-chain-inventory-optimizer`

**Available Tools**:
- `calculate_reorder_point`: Calculate optimal reorder point for a product
- `identify_low_stock`: Find products below minimum stock levels
- `forecast_demand`: Forecast future demand based on historical data
- `identify_stockout_risk`: Identify products at risk of stockout

**Example Usage**:
```python
from agents.inventory_agent import InventoryAgent
from aws.bedrock_client import BedrockClient
from aws.lambda_client import LambdaClient

# Initialize clients
bedrock_client = BedrockClient(
    region='us-east-1',
    model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'
)
lambda_client = LambdaClient(region='us-east-1')

# Create agent
inventory_agent = InventoryAgent(
    bedrock_client=bedrock_client,
    lambda_client=lambda_client,
    lambda_function_name='supply-chain-inventory-optimizer'
)

# Process request with AI orchestration
response = inventory_agent.process_request(
    request="Show me products with low stock at warehouse WH-001"
)

print(response.content)
print(f"Execution time: {response.execution_time:.2f}s")

# Or invoke tool directly
result = inventory_agent.invoke_tool_directly(
    tool_name='identify_low_stock',
    parameters={
        'warehouse_code': 'WH-001',
        'threshold': 1.0
    }
)
```

### 2. Logistics Agent

**Purpose**: Logistics optimization for Field Engineers

**Lambda Function**: `supply-chain-logistics-optimizer`

**Available Tools**:
- `optimize_delivery_route`: Optimize delivery routes by grouping orders
- `check_fulfillment_status`: Get detailed order fulfillment status
- `identify_delayed_orders`: Find orders past their delivery date
- `calculate_warehouse_capacity`: Calculate warehouse capacity utilization

**Example Usage**:
```python
from agents.logistics_agent import LogisticsAgent
from aws.bedrock_client import BedrockClient
from aws.lambda_client import LambdaClient

# Initialize clients
bedrock_client = BedrockClient(
    region='us-east-1',
    model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'
)
lambda_client = LambdaClient(region='us-east-1')

# Create agent
logistics_agent = LogisticsAgent(
    bedrock_client=bedrock_client,
    lambda_client=lambda_client,
    lambda_function_name='supply-chain-logistics-optimizer'
)

# Process request with AI orchestration
response = logistics_agent.process_request(
    request="Optimize delivery route for orders SO-001, SO-002, SO-003 from WH-001"
)

print(response.content)

# Or invoke tool directly
result = logistics_agent.invoke_tool_directly(
    tool_name='identify_delayed_orders',
    parameters={
        'warehouse_code': 'WH-001',
        'days': 7
    }
)
```

### 3. Supplier Agent

**Purpose**: Supplier analysis for Procurement Specialists

**Lambda Function**: `supply-chain-supplier-analyzer`

**Available Tools**:
- `analyze_supplier_performance`: Analyze supplier performance metrics
- `compare_supplier_costs`: Compare costs across suppliers
- `identify_cost_savings`: Find cost savings opportunities
- `analyze_purchase_trends`: Analyze purchase order trends

**Example Usage**:
```python
from agents.supplier_agent import SupplierAgent
from aws.bedrock_client import BedrockClient
from aws.lambda_client import LambdaClient

# Initialize clients
bedrock_client = BedrockClient(
    region='us-east-1',
    model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'
)
lambda_client = LambdaClient(region='us-east-1')

# Create agent
supplier_agent = SupplierAgent(
    bedrock_client=bedrock_client,
    lambda_client=lambda_client,
    lambda_function_name='supply-chain-supplier-analyzer'
)

# Process request with AI orchestration
response = supplier_agent.process_request(
    request="Analyze performance of supplier SUP-001 over the last 90 days"
)

print(response.content)

# Or invoke tool directly
result = supplier_agent.invoke_tool_directly(
    tool_name='compare_supplier_costs',
    parameters={
        'product_group': 'Electronics',
        'suppliers': ['SUP-001', 'SUP-002']
    }
)
```

## Architecture

### Agent Flow

1. **User Request**: Natural language request from user
2. **Message Building**: Build conversation messages with context
3. **Bedrock Orchestration**: Send to Bedrock with tool definitions
4. **Tool Selection**: Bedrock selects appropriate tools
5. **Lambda Invocation**: Agent invokes Lambda functions
6. **Result Processing**: Process Lambda results
7. **Final Response**: Bedrock generates final response with analysis

### Tool Calling Flow

```
User Request
    ↓
Bedrock (with tools)
    ↓
Tool Use Decision
    ↓
Lambda Invocation
    ↓
Tool Results
    ↓
Bedrock (with results)
    ↓
Final Response
```

## Key Features

### 1. AI Orchestration

All agents integrate with Amazon Bedrock for intelligent tool selection and response generation. The AI determines which tools to use based on the user's request.

### 2. Conversation Context

Agents support conversation context to maintain state across multiple interactions:

```python
context = {
    "history": [
        {"query": "Show low stock", "response": "Found 5 products..."},
        {"query": "Calculate reorder for PROD-001", "response": "Reorder point is 50..."}
    ]
}

response = agent.process_request(
    request="What about PROD-002?",
    context=context
)
```

### 3. Direct Tool Invocation

For programmatic use, tools can be invoked directly without AI orchestration:

```python
result = agent.invoke_tool_directly(
    tool_name='calculate_reorder_point',
    parameters={
        'product_code': 'PROD-001',
        'warehouse_code': 'WH-001'
    }
)
```

### 4. Error Handling

Agents inherit comprehensive error handling from BaseAgent:
- User-friendly error messages
- Detailed logging
- Exception handling
- Graceful degradation

### 5. Token Usage Tracking

All responses include token usage information for cost tracking:

```python
response = agent.process_request(request="...")
print(f"Input tokens: {response.data['token_usage']['input_tokens']}")
print(f"Output tokens: {response.data['token_usage']['output_tokens']}")
```

## Configuration

Agents are configured through the main config.yaml file:

```yaml
aws:
  region: us-east-1
  bedrock:
    model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
    max_tokens: 4096
    temperature: 0.0
  lambda:
    inventory_function: supply-chain-inventory-optimizer
    logistics_function: supply-chain-logistics-optimizer
    supplier_function: supply-chain-supplier-analyzer
```

## Testing

### Unit Tests

Run unit tests to verify agent initialization and tool definitions:

```bash
python mvp/agents/test_specialized_agents.py
```

### Integration Tests

Integration tests require deployed Lambda functions and AWS credentials:

```python
# Set up AWS credentials
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Run integration tests
python mvp/agents/test_specialized_agents_integration.py
```

## Response Format

All agents return `AgentResponse` objects:

```python
@dataclass
class AgentResponse:
    success: bool              # Whether request succeeded
    content: str              # Response content/message
    data: Optional[Any]       # Optional data payload
    error: Optional[str]      # Error message if failed
    execution_time: float     # Execution time in seconds
    metadata: Optional[Dict]  # Optional metadata
```

**Success Response**:
```python
response = agent.process_request(request="...")
if response.success:
    print(response.content)
    print(f"Tools used: {response.metadata['tools_used']}")
    print(f"Time: {response.execution_time:.2f}s")
```

**Error Response**:
```python
if not response.success:
    print(f"Error: {response.error}")
```

## Best Practices

### 1. Use AI Orchestration for Natural Language

For natural language requests, use `process_request()` to leverage Bedrock's intelligence:

```python
response = agent.process_request(
    request="Find products that need reordering at WH-001"
)
```

### 2. Use Direct Invocation for Programmatic Access

For programmatic access with known parameters, use `invoke_tool_directly()`:

```python
result = agent.invoke_tool_directly(
    tool_name='identify_low_stock',
    parameters={'warehouse_code': 'WH-001', 'threshold': 1.0}
)
```

### 3. Provide Conversation Context

For follow-up questions, provide conversation context:

```python
context = {"history": previous_interactions}
response = agent.process_request(request="What about that product?", context=context)
```

### 4. Handle Errors Gracefully

Always check response success and handle errors:

```python
response = agent.process_request(request="...")
if response.success:
    # Process successful response
    print(response.content)
else:
    # Handle error
    print(f"Error: {response.error}")
```

### 5. Track Token Usage

Monitor token usage for cost optimization:

```python
response = agent.process_request(request="...")
tokens = response.data['token_usage']
print(f"Total tokens: {tokens['total_tokens']}")
```

## Troubleshooting

### Common Issues

**1. Lambda function not found**
- Verify Lambda function is deployed
- Check function name in config.yaml
- Verify AWS credentials have Lambda invoke permissions

**2. Bedrock API errors**
- Check AWS region supports Bedrock
- Verify model ID is correct
- Check Bedrock service quotas

**3. Tool invocation failures**
- Check Lambda function logs in CloudWatch
- Verify Redshift Serverless is running
- Check Lambda IAM role has Redshift Data API permissions

**4. Import errors**
- Ensure all dependencies are installed
- Check Python path includes mvp directory
- Verify AWS SDK (boto3) is installed

## Performance

### Typical Response Times

- **Direct tool invocation**: 2-5 seconds
- **AI orchestration (single tool)**: 3-7 seconds
- **AI orchestration (multiple tools)**: 5-15 seconds

### Optimization Tips

1. Use direct invocation when possible
2. Cache frequently requested data
3. Optimize Lambda function performance
4. Use conversation context to reduce token usage
5. Set appropriate Bedrock temperature (0.0 for deterministic)

## Security

### Authentication

- Agents use AWS credentials from environment or IAM roles
- No credentials stored in code
- Lambda functions use IAM roles for Redshift access

### Authorization

- Persona-based access control at orchestrator level
- Lambda functions validate input parameters
- Redshift Data API uses temporary credentials

### Data Protection

- All data in transit encrypted (TLS)
- CloudWatch logs may contain sensitive data
- Configure log retention policies appropriately

## Next Steps

After implementing specialized agents:

1. Test each agent with sample requests
2. Verify Lambda function integration
3. Implement orchestrator (Task 9)
4. Add caching and conversation memory (Task 10)
5. Integrate with Streamlit UI (Task 14)

## Support

For issues or questions:
- Check agent logs for detailed error messages
- Review Lambda function CloudWatch logs
- Verify AWS credentials and permissions
- Ensure all dependencies are installed
