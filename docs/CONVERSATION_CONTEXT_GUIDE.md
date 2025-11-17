# Conversation Context Management Guide

## Overview

The Conversation Context Management System provides persistent conversation history storage and retrieval for multi-turn agent interactions. It enables agents to maintain context across multiple queries within a session, improving response quality and user experience.

## Features

- **Persistent Storage**: Conversation history stored in DynamoDB with automatic TTL
- **Configurable Context Windows**: Control how many messages are included in context
- **Automatic Summarization**: Summarizes older messages when token limits are exceeded
- **Session-based Retrieval**: Retrieve conversation history by session ID
- **Persona Tracking**: Track conversations by user persona for analytics
- **Flexible Configuration**: Environment-specific retention policies and window sizes

## Architecture

### Components

1. **ConversationContextManager**: Core class managing conversation storage and retrieval
2. **DynamoDB Table**: `conversations` table with TTL and GSI for efficient queries
3. **Orchestrator Integration**: Automatic context injection into agent queries
4. **Configuration System**: Environment-specific settings for context management

### Data Model

#### DynamoDB Schema

**Table Name**: `{prefix}-conversations`

**Primary Key**:
- Partition Key: `message_id` (STRING) - Format: `{session_id}#{timestamp}`
- Sort Key: `timestamp` (STRING) - ISO 8601 format

**Attributes**:
- `session_id` (STRING) - Unique session identifier
- `role` (STRING) - Message role: 'user', 'assistant', 'system'
- `content` (STRING) - Message content
- `token_count` (NUMBER) - Estimated token count
- `ttl` (NUMBER) - Unix timestamp for automatic deletion
- `persona` (STRING) - User persona (optional)
- `metadata` (MAP) - Additional metadata (optional)

**Global Secondary Indexes**:
1. `session-timestamp-index`: Query by session_id and timestamp
2. `persona-timestamp-index`: Query by persona and timestamp (for analytics)

## Configuration

### Environment Variables

```bash
# DynamoDB table name
CONVERSATION_TABLE=sc-agent-dev-conversations
DYNAMODB_CONVERSATION_TABLE=sc-agent-dev-conversations  # Alternative name
```

### YAML Configuration

```yaml
# config/dev.yaml
resources:
  dynamodb:
    conversation_table: sc-agent-dev-conversations

agents:
  context_window_size: 5              # Number of messages in context
  conversation_retention_days: 7      # TTL for conversation history
  max_tokens_per_context: 3000        # Token limit before summarization
```

### Environment-Specific Settings

| Setting | Dev | Staging | Prod |
|---------|-----|---------|------|
| context_window_size | 5 | 10 | 10 |
| conversation_retention_days | 7 | 30 | 90 |
| max_tokens_per_context | 3000 | 4000 | 5000 |

## Usage

### Basic Usage

```python
from config_manager import ConfigurationManager
from conversation_context_manager import ConversationContextManager

# Initialize
config = ConfigurationManager(environment='dev')
context_manager = ConversationContextManager(config, region='us-east-1')

# Add a message
context_manager.add_message(
    session_id='session-123',
    role='user',
    content='Show me inventory levels for warehouse WH01',
    persona='warehouse_manager'
)

# Get conversation context
messages = context_manager.get_context('session-123', max_messages=10)

# Clear conversation history
context_manager.clear_context('session-123')
```

### Orchestrator Integration

The orchestrator automatically manages conversation context:

```python
from orchestrator import SupplyChainOrchestrator

orchestrator = SupplyChainOrchestrator()

# Process query - context is automatically managed
result = orchestrator.process_query(
    query='What are the current stock levels?',
    persona='warehouse_manager',
    session_id='session-123',
    context={'username': 'john.doe', 'groups': ['warehouse_managers']}
)

# Get conversation history
history = orchestrator.get_conversation_history('session-123')

# Get session summary
summary = orchestrator.get_session_summary('session-123')

# Clear conversation
orchestrator.clear_conversation_history('session-123')
```

### Agent-Specific Context

Retrieve context filtered for a specific agent:

```python
# Get context relevant to inventory optimizer agent
inventory_context = context_manager.get_context_for_agent(
    session_id='session-123',
    agent_name='inventory_optimizer',
    max_messages=5
)
```

## Conversation Summarization

When the total token count exceeds `max_tokens_per_context`, the system automatically:

1. Keeps the most recent messages (50% of context window)
2. Summarizes older messages using the configured LLM
3. Stores the summary as a system message
4. Returns summary + recent messages as context

### Summarization Example

**Before Summarization** (15 messages, 4500 tokens):
```
User: Show inventory for WH01
Assistant: Here are the inventory levels...
User: What about WH02?
Assistant: WH02 inventory levels are...
[... 11 more messages ...]
```

**After Summarization** (1 summary + 5 recent messages, 2800 tokens):
```
System: [Summary] User inquired about inventory levels for warehouses WH01 and WH02...
User: What's the reorder point for product P123?
Assistant: The reorder point for P123 is...
[... 3 more recent messages ...]
```

## API Reference

### ConversationContextManager

#### `__init__(config, region, model_manager=None)`

Initialize the context manager.

**Parameters**:
- `config` (ConfigurationManager): Configuration instance
- `region` (str): AWS region
- `model_manager` (ModelManager, optional): Model manager for summarization

#### `add_message(session_id, role, content, metadata=None, persona=None)`

Add a message to conversation history.

**Parameters**:
- `session_id` (str): Session identifier
- `role` (str): Message role ('user', 'assistant', 'system')
- `content` (str): Message content
- `metadata` (dict, optional): Additional metadata
- `persona` (str, optional): User persona

**Returns**: Dict with success status and message details

#### `get_context(session_id, max_messages=None, include_system=True)`

Retrieve conversation context for a session.

**Parameters**:
- `session_id` (str): Session identifier
- `max_messages` (int, optional): Maximum messages to retrieve
- `include_system` (bool): Include system messages

**Returns**: List of message dictionaries

#### `clear_context(session_id)`

Clear all conversation history for a session.

**Parameters**:
- `session_id` (str): Session identifier

**Returns**: Dict with success status and deleted count

#### `get_session_summary(session_id)`

Get summary statistics for a session.

**Parameters**:
- `session_id` (str): Session identifier

**Returns**: Dict with session statistics

## Best Practices

### 1. Session Management

- Use unique session IDs per user conversation
- Consider using UUIDs for session IDs
- Clear sessions when users explicitly start new conversations

### 2. Context Window Sizing

- **Development**: Small windows (5 messages) for faster testing
- **Production**: Larger windows (10-15 messages) for better context
- Balance between context quality and token costs

### 3. Retention Policies

- **Development**: Short retention (7 days) to reduce storage costs
- **Production**: Longer retention (90 days) for audit and analytics
- Consider compliance requirements for data retention

### 4. Token Management

- Monitor token usage to optimize costs
- Adjust `max_tokens_per_context` based on model limits
- Use summarization to maintain context without exceeding limits

### 5. Metadata Usage

Store useful metadata for debugging and analytics:

```python
context_manager.add_message(
    session_id='session-123',
    role='assistant',
    content='Analysis complete',
    metadata={
        'agent_name': 'inventory_optimizer',
        'tools_used': ['calculate_reorder_points', 'forecast_demand'],
        'execution_time_ms': 1250,
        'model_id': 'anthropic.claude-3-5-sonnet-20241022-v2:0'
    }
)
```

## Monitoring and Analytics

### CloudWatch Metrics

Monitor conversation context usage:

```python
# Publish custom metrics
cloudwatch.put_metric_data(
    Namespace='SupplyChainAgent/Conversations',
    MetricData=[
        {
            'MetricName': 'MessageCount',
            'Value': len(messages),
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'SessionId', 'Value': session_id},
                {'Name': 'Persona', 'Value': persona}
            ]
        }
    ]
)
```

### Analytics Queries

Query conversation patterns using the persona-timestamp index:

```python
# Get all conversations for a persona in a time range
response = table.query(
    IndexName='persona-timestamp-index',
    KeyConditionExpression='persona = :p AND timestamp BETWEEN :start AND :end',
    ExpressionAttributeValues={
        ':p': 'warehouse_manager',
        ':start': '2024-01-01T00:00:00',
        ':end': '2024-01-31T23:59:59'
    }
)
```

## Troubleshooting

### Issue: Context not being retrieved

**Symptoms**: Agents don't have access to previous conversation

**Solutions**:
1. Verify DynamoDB table exists and has correct GSI
2. Check IAM permissions for DynamoDB access
3. Verify session_id is consistent across queries
4. Check CloudWatch logs for errors

### Issue: High token usage

**Symptoms**: Increased costs, slow responses

**Solutions**:
1. Reduce `context_window_size` in configuration
2. Lower `max_tokens_per_context` to trigger summarization earlier
3. Implement more aggressive message filtering
4. Clear old sessions regularly

### Issue: Summarization failures

**Symptoms**: Context exceeds limits without summarization

**Solutions**:
1. Verify Bedrock model access
2. Check model_manager initialization
3. Review CloudWatch logs for summarization errors
4. Ensure sufficient IAM permissions for Bedrock

## CDK Deployment

The conversation table is automatically created by CDK:

```python
# cdk/supply_chain_stack.py
conversation_table = dynamodb.Table(
    self, "ConversationTable",
    table_name=config.resource_namer.dynamodb_table('conversations'),
    partition_key=dynamodb.Attribute(
        name="message_id",
        type=dynamodb.AttributeType.STRING
    ),
    sort_key=dynamodb.Attribute(
        name="timestamp",
        type=dynamodb.AttributeType.STRING
    ),
    time_to_live_attribute="ttl",
    # ... additional configuration
)
```

## Security Considerations

1. **Encryption**: All data encrypted at rest using KMS
2. **Access Control**: IAM policies restrict table access
3. **TTL**: Automatic deletion prevents indefinite data retention
4. **Audit Logging**: CloudTrail logs all DynamoDB operations
5. **Data Classification**: Consider PII in conversation content

## Performance Optimization

1. **Query Optimization**: Use GSI for efficient session queries
2. **Batch Operations**: Use batch_writer for bulk operations
3. **Caching**: Consider caching recent context in memory
4. **Pagination**: Implement pagination for large conversation histories
5. **Compression**: Consider compressing large message content

## Future Enhancements

- [ ] Conversation branching for multi-path interactions
- [ ] Semantic search across conversation history
- [ ] Real-time conversation analytics dashboard
- [ ] Conversation export and import functionality
- [ ] Multi-language conversation support
- [ ] Conversation templates and patterns

## References

- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Configuration Management Guide](./CONFIGURATION_GUIDE.md)
