# Agent Development Guide

## Table of Contents

1. [Overview](#overview)
2. [Agent Architecture](#agent-architecture)
3. [Creating a New Agent](#creating-a-new-agent)
4. [Agent Configuration](#agent-configuration)
5. [Tool Development](#tool-development)
6. [Testing Agents](#testing-agents)
7. [Deploying Agents](#deploying-agents)
8. [Best Practices](#best-practices)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)

## Overview

This guide explains how to develop new AI agents for the Supply Chain Agentic AI Application. The application uses a plugin-based architecture that allows you to add new agents without modifying core orchestration logic.

### What is an Agent?

An agent is a specialized AI component that:
- Handles specific types of queries (e.g., inventory, logistics, supplier analysis)
- Uses Amazon Bedrock foundation models for natural language understanding
- Can execute tools (Lambda functions) to perform actions
- Maintains conversation context
- Returns structured responses

### Agent Lifecycle

1. **Registration**: Agent is discovered and registered from configuration
2. **Initialization**: Agent loads its configuration and tools
3. **Query Processing**: Agent receives queries from orchestrator
4. **Tool Execution**: Agent invokes tools as needed
5. **Response Generation**: Agent formats and returns results

## Agent Architecture

### Base Agent Class

All agents inherit from `BaseAgent`:

```python
# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import boto3
import json

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize agent with configuration
        
        Args:
            config: Agent-specific configuration from YAML
        """
        self.config = config
        self.model_id = config.get('model')
        self.timeout = config.get('timeout_seconds', 60)
        self.tools = config.get('tools', [])
        self.bedrock = boto3.client('bedrock-runtime')
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass
    
    @abstractmethod
    def can_handle(self, query: str, persona: str) -> bool:
        """Determine if this agent can handle the query"""
        pass
    
    def process_query(
        self,
        query: str,
        persona: str,
        context: List[Dict] = None,
        user_context: Dict = None
    ) -> Dict[str, Any]:
        """
        Process a user query
        
        Args:
            query: User's question or request
            persona: User's role (warehouse_manager, field_engineer, etc.)
            context: Conversation history
            user_context: User metadata (permissions, preferences, etc.)
            
        Returns:
            Dict with response, metadata, and any tool results
        """
        # Build messages for Bedrock
        messages = self._build_messages(query, context)
        
        # Invoke Bedrock model
        response = self._invoke_model(messages)
        
        # Execute tools if needed
        if self._needs_tools(response):
            tool_results = self._execute_tools(response, user_context)
            response = self._incorporate_tool_results(response, tool_results)
        
        return {
            'response': response,
            'agent': self.__class__.__name__,
            'model': self.model_id,
            'tools_used': self.tools
        }
    
    def _invoke_model(self, messages: List[Dict]) -> str:
        """Invoke Bedrock model"""
        body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'messages': messages,
            'system': self.get_system_prompt(),
            'max_tokens': 4096,
            'temperature': 0.7
        }
        
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text']
    
    def _build_messages(self, query: str, context: List[Dict] = None) -> List[Dict]:
        """Build message list for Bedrock"""
        messages = []
        
        # Add conversation context
        if context:
            for msg in context[-5:]:  # Last 5 messages
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        # Add current query
        messages.append({
            'role': 'user',
            'content': query
        })
        
        return messages
    
    def _needs_tools(self, response: str) -> bool:
        """Check if response indicates tool usage needed"""
        # Implement tool detection logic
        return False
    
    def _execute_tools(self, response: str, user_context: Dict) -> List[Dict]:
        """Execute required tools"""
        # Implement tool execution
        return []
    
    def _incorporate_tool_results(self, response: str, tool_results: List[Dict]) -> str:
        """Incorporate tool results into response"""
        # Implement result incorporation
        return response
``
`

### Agent Registry

The `AgentRegistry` manages agent discovery and registration:

```python
# agent_registry.py
class AgentRegistry:
    """Registry for pluggable agents"""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        self._discover_agents()
    
    def _discover_agents(self):
        """Auto-discover and register agents from configuration"""
        agent_configs = self.config.get("agents")
        
        for agent_name, agent_config in agent_configs.items():
            if agent_name in ['default_model', 'context_window_size', 'conversation_retention_days']:
                continue  # Skip global settings
            
            if agent_config.get("enabled", True):
                self.register_agent(agent_name, agent_config)
    
    def register_agent(self, name: str, config: Dict):
        """Register an agent"""
        agent_class = self._load_agent_class(name)
        agent = agent_class(config)
        self.agents[name] = agent
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get registered agent by name"""
        return self.agents.get(name)
```

## Creating a New Agent

### Step 1: Define Agent Class

Create a new file in the `agents/` directory:

```python
# agents/my_new_agent.py
from agents.base_agent import BaseAgent
from typing import Dict, Any

class MyNewAgent(BaseAgent):
    """Agent for handling specific domain queries"""
    
    def get_system_prompt(self) -> str:
        """Define the agent's behavior and capabilities"""
        return """You are a specialized AI agent for [domain].
        
Your capabilities:
- Capability 1
- Capability 2
- Capability 3

When responding:
- Be concise and accurate
- Use data from tools when available
- Cite sources when appropriate
- Ask clarifying questions if needed

Available tools:
- tool_1: Description
- tool_2: Description
"""
    
    def can_handle(self, query: str, persona: str) -> bool:
        """Determine if this agent should handle the query"""
        # Check for keywords or patterns
        keywords = ['keyword1', 'keyword2', 'keyword3']
        query_lower = query.lower()
        
        # Check if query contains relevant keywords
        if any(keyword in query_lower for keyword in keywords):
            return True
        
        # Check if persona is relevant
        relevant_personas = ['persona1', 'persona2']
        if persona in relevant_personas:
            return True
        
        return False
```

### Step 2: Add Configuration

Add agent configuration to `config/dev.yaml`, `config/staging.yaml`, and `config/prod.yaml`:

```yaml
agents:
  # ... existing agents ...
  
  my_new_agent:
    enabled: true
    model: anthropic.claude-3-5-sonnet-20241022-v2:0
    timeout_seconds: 60
    tools:
      - tool_1
      - tool_2
```

### Step 3: Register Agent

The agent will be automatically discovered and registered by the `AgentRegistry` based on the configuration.

### Step 4: Test Agent

Create tests for your agent:

```python
# tests/test_my_new_agent.py
import pytest
from agents.my_new_agent import MyNewAgent

def test_agent_initialization():
    config = {
        'model': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
        'timeout_seconds': 60,
        'tools': ['tool_1', 'tool_2']
    }
    agent = MyNewAgent(config)
    assert agent.model_id == config['model']
    assert agent.timeout == 60

def test_can_handle():
    agent = MyNewAgent({})
    assert agent.can_handle("query with keyword1", "persona1") == True
    assert agent.can_handle("unrelated query", "other_persona") == False

def test_process_query():
    agent = MyNewAgent({
        'model': 'anthropic.claude-3-5-sonnet-20241022-v2:0'
    })
    result = agent.process_query(
        query="Test query",
        persona="persona1",
        context=[],
        user_context={}
    )
    assert 'response' in result
    assert 'agent' in result
```

## Agent Configuration

### Configuration Parameters

Each agent can have the following configuration parameters:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Enable/disable the agent |
| `model` | string | No | (uses default) | Bedrock model ID |
| `timeout_seconds` | integer | No | `60` | Maximum execution time |
| `tools` | array | No | `[]` | List of available tools |
| `max_retries` | integer | No | `3` | Tool execution retries |
| `temperature` | float | No | `0.7` | Model temperature (0-1) |

### Example Configuration

```yaml
agents:
  my_agent:
    enabled: true
    model: anthropic.claude-3-5-sonnet-20241022-v2:0
    timeout_seconds: 120
    temperature: 0.5
    tools:
      - analyze_data
      - generate_report
    max_retries: 3
    custom_settings:
      max_results: 100
      include_metadata: true
```

### Accessing Configuration

```python
class MyAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Access standard config
        self.model_id = config.get('model')
        self.timeout = config.get('timeout_seconds', 60)
        
        # Access custom settings
        custom = config.get('custom_settings', {})
        self.max_results = custom.get('max_results', 50)
        self.include_metadata = custom.get('include_metadata', False)
```

## Tool Development

### Creating a Tool (Lambda Function)

Tools are Lambda functions that agents can invoke to perform actions.

**Step 1: Create Lambda Function**

```python
# lambda_functions/my_tool.py
import json
import boto3

def lambda_handler(event, context):
    """
    Tool for performing specific action
    
    Event structure:
    {
        "action": "tool_name",
        "parameters": {
            "param1": "value1",
            "param2": "value2"
        },
        "user_context": {
            "user_id": "user123",
            "permissions": ["read", "write"]
        }
    }
    """
    try:
        action = event.get('action')
        parameters = event.get('parameters', {})
        user_context = event.get('user_context', {})
        
        # Validate permissions
        if not has_permission(user_context, action):
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Permission denied'})
            }
        
        # Perform action
        result = perform_action(action, parameters)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'result': result
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def has_permission(user_context: dict, action: str) -> bool:
    """Check if user has permission for action"""
    permissions = user_context.get('permissions', [])
    required_permission = get_required_permission(action)
    return required_permission in permissions

def perform_action(action: str, parameters: dict):
    """Perform the requested action"""
    if action == 'analyze_data':
        return analyze_data(parameters)
    elif action == 'generate_report':
        return generate_report(parameters)
    else:
        raise ValueError(f"Unknown action: {action}")
```

**Step 2: Add Lambda to CDK Stack**

```python
# cdk/supply_chain_stack.py
my_tool_function = lambda_.Function(
    self, "MyToolFunction",
    function_name=f"{prefix}-my-tool-{environment}",
    runtime=lambda_.Runtime.PYTHON_3_11,
    handler="my_tool.lambda_handler",
    code=lambda_.Code.from_asset("lambda_functions"),
    timeout=Duration.seconds(60),
    memory_size=512,
    environment={
        "ENVIRONMENT": environment,
        "LOG_LEVEL": "INFO"
    }
)
```

**Step 3: Grant Permissions**

```python
# Grant Lambda access to required resources
data_bucket.grant_read(my_tool_function)
dynamodb_table.grant_read_write_data(my_tool_function)
```

### Tool Invocation from Agent

```python
class MyAgent(BaseAgent):
    def _execute_tools(self, response: str, user_context: Dict) -> List[Dict]:
        """Execute required tools"""
        lambda_client = boto3.client('lambda')
        results = []
        
        for tool_name in self.tools:
            payload = {
                'action': tool_name,
                'parameters': self._extract_parameters(response, tool_name),
                'user_context': user_context
            }
            
            response = lambda_client.invoke(
                FunctionName=f"sc-agent-{tool_name}-{self.environment}",
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            results.append({
                'tool': tool_name,
                'result': result
            })
        
        return results
```

## Testing Agents

### Unit Tests

```python
# tests/test_my_agent.py
import pytest
from unittest.mock import Mock, patch
from agents.my_new_agent import MyNewAgent

@pytest.fixture
def agent():
    config = {
        'model': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
        'timeout_seconds': 60,
        'tools': ['tool_1']
    }
    return MyNewAgent(config)

def test_system_prompt(agent):
    prompt = agent.get_system_prompt()
    assert len(prompt) > 0
    assert 'capabilities' in prompt.lower()

def test_can_handle_relevant_query(agent):
    assert agent.can_handle("relevant query", "relevant_persona") == True

def test_can_handle_irrelevant_query(agent):
    assert agent.can_handle("irrelevant query", "other_persona") == False

@patch('boto3.client')
def test_process_query(mock_boto, agent):
    # Mock Bedrock response
    mock_bedrock = Mock()
    mock_boto.return_value = mock_bedrock
    mock_bedrock.invoke_model.return_value = {
        'body': Mock(read=lambda: json.dumps({
            'content': [{'text': 'Test response'}]
        }).encode())
    }
    
    result = agent.process_query(
        query="Test query",
        persona="test_persona",
        context=[],
        user_context={}
    )
    
    assert result['response'] == 'Test response'
    assert result['agent'] == 'MyNewAgent'
```

### Integration Tests

```python
# tests/integration/test_agent_integration.py
import pytest
import boto3
from agents.my_new_agent import MyNewAgent

@pytest.mark.integration
def test_agent_with_real_bedrock():
    """Test agent with real Bedrock API"""
    config = {
        'model': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
        'timeout_seconds': 60
    }
    agent = MyNewAgent(config)
    
    result = agent.process_query(
        query="What is 2+2?",
        persona="test_persona",
        context=[],
        user_context={}
    )
    
    assert 'response' in result
    assert '4' in result['response']

@pytest.mark.integration
def test_agent_with_tools():
    """Test agent with tool execution"""
    config = {
        'model': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
        'tools': ['my_tool']
    }
    agent = MyNewAgent(config)
    
    result = agent.process_query(
        query="Execute my_tool",
        persona="test_persona",
        context=[],
        user_context={'permissions': ['execute_tools']}
    )
    
    assert 'tools_used' in result
```

### Running Tests

```bash
# Run unit tests
pytest tests/test_my_agent.py -v

# Run integration tests
pytest tests/integration/ -v -m integration

# Run with coverage
pytest tests/ --cov=agents --cov-report=html

# Run specific test
pytest tests/test_my_agent.py::test_can_handle -v
```

## Deploying Agents

### Deployment Checklist

- [ ] Agent class implemented and tested
- [ ] Configuration added to all environment files
- [ ] Tools (Lambda functions) created and tested
- [ ] IAM permissions configured
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Code reviewed

### Deployment Steps

**1. Deploy to Development**

```bash
# Update configuration
vi config/dev.yaml

# Validate configuration
python scripts/validate-config.py --config config/dev.yaml

# Deploy
./deploy.sh --environment dev

# Verify
./scripts/verify-deployment.sh --environment dev
```

**2. Test in Development**

```bash
# Test agent endpoint
curl -X POST $API_ENDPOINT/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Test query for new agent",
    "persona": "test_persona"
  }'
```

**3. Deploy to Staging**

```bash
# Update staging config
vi config/staging.yaml

# Deploy to staging
./deploy.sh --environment staging

# Run integration tests
pytest tests/integration/ -v
```

**4. Deploy to Production**

```bash
# Update production config
vi config/prod.yaml

# Create backup
aws dynamodb create-backup \
  --table-name sc-agent-sessions-prod \
  --backup-name pre-agent-deployment-$(date +%Y%m%d)

# Deploy to production
./deploy.sh --environment prod

# Monitor deployment
aws logs tail /aws/lambda/sc-agent-orchestrator-prod --follow

# Verify
./scripts/verify-deployment.sh --environment prod
```

## Best Practices

### 1. Agent Design

**Single Responsibility**
- Each agent should handle one domain or capability
- Don't create "super agents" that do everything
- Split complex agents into multiple specialized agents

**Clear Intent Detection**
- Use specific keywords and patterns
- Implement confidence scoring
- Handle ambiguous queries gracefully

**Robust Error Handling**
- Catch and log all exceptions
- Provide helpful error messages
- Implement fallback responses

### 2. Prompt Engineering

**System Prompts**
- Be specific about agent capabilities
- Include examples of good responses
- Define output format clearly
- Set appropriate tone and style

**Example**:
```python
def get_system_prompt(self) -> str:
    return """You are an inventory optimization specialist.

Your role:
- Analyze inventory levels and trends
- Identify stockout risks
- Recommend reorder points
- Optimize stock levels

Response format:
1. Summary (2-3 sentences)
2. Key findings (bullet points)
3. Recommendations (numbered list)
4. Data sources used

Tone: Professional, data-driven, actionable
"""
```

### 3. Tool Usage

**Tool Design**
- Keep tools focused and single-purpose
- Make tools idempotent when possible
- Implement proper error handling
- Add comprehensive logging

**Tool Permissions**
- Always validate user permissions
- Use least privilege principle
- Log all tool executions
- Implement rate limiting

### 4. Performance

**Optimize Latency**
- Use appropriate model for task (Haiku for simple, Sonnet for complex)
- Minimize context size
- Cache frequent queries
- Use parallel tool execution

**Manage Costs**
- Monitor token usage
- Use cheaper models where appropriate
- Implement conversation summarization
- Set appropriate timeouts

### 5. Testing

**Test Coverage**
- Unit tests for all methods
- Integration tests for end-to-end flows
- Load tests for performance
- Security tests for permissions

**Test Data**
- Use realistic test data
- Test edge cases
- Test error conditions
- Test with different personas

### 6. Monitoring

**Key Metrics**
- Query latency
- Success rate
- Token usage
- Tool execution time
- Error rate by type

**Logging**
- Log all queries and responses
- Log tool executions
- Log errors with context
- Use structured logging

## Examples

### Example 1: Simple Query Agent

```python
# agents/faq_agent.py
from agents.base_agent import BaseAgent

class FAQAgent(BaseAgent):
    """Agent for handling frequently asked questions"""
    
    def get_system_prompt(self) -> str:
        return """You are a helpful FAQ assistant.
        
Answer common questions about:
- System usage
- Features and capabilities
- Troubleshooting
- Best practices

Keep answers concise and accurate.
"""
    
    def can_handle(self, query: str, persona: str) -> bool:
        faq_keywords = ['how to', 'what is', 'help', 'guide']
        return any(kw in query.lower() for kw in faq_keywords)
```

### Example 2: Data Analysis Agent

```python
# agents/analytics_agent.py
from agents.base_agent import BaseAgent
import json

class AnalyticsAgent(BaseAgent):
    """Agent for data analysis and reporting"""
    
    def get_system_prompt(self) -> str:
        return """You are a data analytics specialist.

Capabilities:
- Analyze trends and patterns
- Generate insights from data
- Create visualizations
- Provide recommendations

Always cite data sources and confidence levels.
"""
    
    def can_handle(self, query: str, persona: str) -> bool:
        analytics_keywords = ['analyze', 'trend', 'report', 'insight']
        return any(kw in query.lower() for kw in analytics_keywords)
    
    def process_query(self, query, persona, context=None, user_context=None):
        # Get data from tools
        data = self._fetch_data(query, user_context)
        
        # Analyze data
        analysis = self._analyze_data(data)
        
        # Generate response
        response = self._generate_response(query, analysis)
        
        return {
            'response': response,
            'data': data,
            'analysis': analysis,
            'agent': self.__class__.__name__
        }
    
    def _fetch_data(self, query, user_context):
        """Fetch relevant data using tools"""
        # Implementation
        pass
    
    def _analyze_data(self, data):
        """Analyze the data"""
        # Implementation
        pass
    
    def _generate_response(self, query, analysis):
        """Generate natural language response"""
        # Implementation
        pass
```

## Troubleshooting

### Common Issues

**Issue: Agent not being registered**

Solution:
1. Check configuration file syntax
2. Verify `enabled: true` in config
3. Check agent class name matches file name
4. Review CloudWatch logs for errors

**Issue: Agent not handling queries**

Solution:
1. Check `can_handle()` logic
2. Verify keywords and patterns
3. Test with different query variations
4. Add logging to `can_handle()`

**Issue: Tool execution fails**

Solution:
1. Check Lambda function logs
2. Verify IAM permissions
3. Check tool payload format
4. Test tool independently

**Issue: High latency**

Solution:
1. Reduce context window size
2. Use faster model (Haiku)
3. Optimize tool execution
4. Enable parallel processing

### Debugging Tips

**Enable Debug Logging**

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MyAgent(BaseAgent):
    def process_query(self, query, persona, context=None, user_context=None):
        logger.debug(f"Processing query: {query}")
        logger.debug(f"Persona: {persona}")
        logger.debug(f"Context: {context}")
        
        result = super().process_query(query, persona, context, user_context)
        
        logger.debug(f"Result: {result}")
        return result
```

**Test Locally**

```python
# test_agent_locally.py
from agents.my_agent import MyAgent

config = {
    'model': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
    'timeout_seconds': 60
}

agent = MyAgent(config)

result = agent.process_query(
    query="Test query",
    persona="test_persona",
    context=[],
    user_context={}
)

print(json.dumps(result, indent=2))
```

## Related Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment procedures
- [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) - Configuration options
- [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) - Troubleshooting help
- [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) - Operations procedures
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)

---

**Document Owner**: Platform Team  
**Last Updated**: 2024-01-15  
**Review Frequency**: Quarterly
