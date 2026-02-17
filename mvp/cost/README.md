# Cost Tracking Module

This module provides comprehensive cost calculation, tracking, and logging functionality for AWS services used in the Supply Chain AI MVP system.

## Overview

The cost tracking module monitors and reports costs for:
- **Amazon Bedrock**: Token-based pricing for AI model usage
- **Amazon Redshift Serverless**: RPU-hour pricing for data warehouse queries
- **AWS Lambda**: GB-second pricing for specialized agent functions

## Components

### 1. CostTracker (`cost_tracker.py`)

Main class for calculating and tracking costs.

**Key Features:**
- Calculate costs for individual queries
- Track session-level and daily costs
- Generate cost breakdowns by service
- Estimate monthly costs based on usage
- Thread-safe cost accumulation

**Usage Example:**
```python
from cost.cost_tracker import CostTracker, TokenUsage

# Initialize tracker with configuration
config = {
    'enabled': True,
    'bedrock_input_cost_per_1k': 0.003,
    'bedrock_output_cost_per_1k': 0.015,
    'redshift_rpu_cost_per_hour': 0.36,
    'redshift_base_rpus': 8,
    'lambda_cost_per_gb_second': 0.0000166667
}
tracker = CostTracker(config)

# Calculate query cost
tokens = TokenUsage(input_tokens=1000, output_tokens=500)
cost = tracker.calculate_query_cost(
    bedrock_tokens=tokens,
    redshift_execution_time=2.5,
    lambda_duration_ms=300,
    lambda_memory_mb=512
)

# Add to session tracking
tracker.add_query_cost(session_id="user123", cost=cost)

# Get cost summary
print(tracker.get_cost_summary(session_id="user123"))
```

### 2. CostLogger (`cost_logger.py`)

Class for logging cost information to file and generating reports.

**Key Features:**
- Log individual query costs with metadata
- Generate daily cost summaries
- Create formatted cost reports
- Export cost data to JSON or CSV
- Read and filter log entries

**Usage Example:**
```python
from cost.cost_logger import CostLogger

# Initialize logger
logger = CostLogger(log_file_path="logs/cost_tracking.log", enabled=True)

# Log query cost
logger.log_query_cost(
    session_id="user123",
    persona="Warehouse Manager",
    query="Show me low stock products",
    cost=cost,
    execution_time=2.5,
    cached=False,
    query_type="SQL_QUERY"
)

# Log daily summary
logger.log_daily_summary(
    target_date=date.today(),
    total_cost=daily_cost,
    query_count=50
)

# Generate cost report
report = logger.generate_cost_report(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
    cost_data=tracker.get_all_daily_costs()
)
print(report)

# Export cost data
logger.export_cost_data(
    output_file="reports/costs.json",
    cost_data=tracker.get_all_daily_costs(),
    format='json'
)
```

## Data Models

### TokenUsage
```python
@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
```

### Cost
```python
@dataclass
class Cost:
    bedrock_cost: float = 0.0
    redshift_cost: float = 0.0
    lambda_cost: float = 0.0
    total_cost: float = 0.0
    tokens_used: TokenUsage = field(default_factory=TokenUsage)
```

## Configuration

Cost tracking is configured in `config.yaml`:

```yaml
cost:
  enabled: true
  log_file: logs/cost_tracking.log
  bedrock_input_cost_per_1k: 0.003
  bedrock_output_cost_per_1k: 0.015
  redshift_rpu_cost_per_hour: 0.36
  redshift_base_rpus: 8
  lambda_cost_per_gb_second: 0.0000166667
```

## Pricing Information

### Amazon Bedrock (Claude 3.5 Sonnet)
- Input tokens: $0.003 per 1,000 tokens
- Output tokens: $0.015 per 1,000 tokens

### Amazon Redshift Serverless
- $0.36 per RPU-hour
- Minimum 8 RPUs (base capacity)

### AWS Lambda
- $0.0000166667 per GB-second
- Default memory: 512 MB

## Cost Tracking Workflow

1. **Query Execution**: When a query is executed, collect metrics:
   - Bedrock token usage (input/output)
   - Redshift execution time
   - Lambda duration and memory

2. **Cost Calculation**: Use `CostTracker.calculate_query_cost()` to compute costs

3. **Cost Logging**: Use `CostLogger.log_query_cost()` to log the cost information

4. **Cost Accumulation**: Use `CostTracker.add_query_cost()` to add to session/daily totals

5. **Cost Reporting**: Generate reports and summaries as needed

## Integration Example

```python
from cost import CostTracker, CostLogger, TokenUsage

# Initialize
config = load_config()
tracker = CostTracker(config['cost'])
logger = CostLogger(config['cost']['log_file'], enabled=config['cost']['enabled'])

# During query execution
def process_query(session_id, persona, query):
    start_time = time.time()
    
    # Execute query and collect metrics
    result = execute_query(query)
    execution_time = time.time() - start_time
    
    # Get token usage from Bedrock response
    tokens = TokenUsage(
        input_tokens=result.bedrock_input_tokens,
        output_tokens=result.bedrock_output_tokens
    )
    
    # Calculate cost
    cost = tracker.calculate_query_cost(
        bedrock_tokens=tokens,
        redshift_execution_time=result.redshift_time,
        lambda_duration_ms=result.lambda_duration,
        lambda_memory_mb=512
    )
    
    # Track and log
    tracker.add_query_cost(session_id, cost)
    logger.log_query_cost(
        session_id=session_id,
        persona=persona,
        query=query,
        cost=cost,
        execution_time=execution_time,
        cached=result.cached,
        query_type=result.query_type
    )
    
    return result, cost
```

## Testing

Run the verification script to test the cost tracking module:

```bash
cd mvp/cost
python verify_cost_tracking.py
```

## Log Format

Cost logs are written in JSON format for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "session_id": "user123",
  "persona": "Warehouse Manager",
  "query": "Show me low stock products",
  "query_type": "SQL_QUERY",
  "cached": false,
  "execution_time": 2.5,
  "costs": {
    "bedrock": 0.0123,
    "redshift": 0.0045,
    "lambda": 0.0008,
    "total": 0.0176
  },
  "tokens": {
    "input": 1000,
    "output": 500,
    "total": 1500
  }
}
```

## Cost Optimization Tips

1. **Enable Caching**: Reduce costs by caching frequently accessed queries
2. **Optimize Prompts**: Minimize token usage by using concise prompts
3. **Monitor Daily Costs**: Set up alerts when daily costs exceed thresholds
4. **Right-size Lambda**: Adjust Lambda memory allocation based on actual usage
5. **Use Query Result Cache**: Avoid re-executing identical queries

## Monthly Cost Estimates

Based on typical usage patterns:

| Usage Level | Queries/Day | Est. Monthly Cost |
|-------------|-------------|-------------------|
| Light       | 50          | $50-75            |
| Moderate    | 150         | $150-200          |
| Heavy       | 300         | $300-400          |

Costs include Bedrock, Redshift Serverless (8 RPUs), and Lambda invocations.
