# Design Document

## Overview

This design document outlines the architecture and implementation approach for making the Supply Chain Agentic AI Application fully portable, configurable, and deployable to any AWS environment. The design focuses on externalized configuration, dynamic resource naming, enhanced AI agent capabilities, and comprehensive deployment automation.

### Design Goals

1. **Zero Code Changes**: Deploy to any AWS account/region without modifying source code
2. **Environment Isolation**: Support multiple environments (dev/staging/prod) with independent configurations
3. **Security First**: All sensitive data in Secrets Manager, least privilege IAM, audit logging
4. **Cost Optimization**: Environment-specific resource sizing and retention policies
5. **Extensibility**: Plugin-based agent architecture for easy capability expansion
6. **Observability**: Comprehensive monitoring, logging, and performance analytics

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Configuration Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ config.yaml  │  │ Parameter    │  │ Secrets      │             │
│  │ (per env)    │  │ Store        │  │ Manager      │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     Application Layer                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Multi-Agent Orchestrator                         │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │  │
│  │  │ Agent      │  │ Model      │  │ Context    │             │  │
│  │  │ Registry   │  │ Manager    │  │ Manager    │             │  │
│  │  └────────────┘  └────────────┘  └────────────┘             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ SQL Agent    │  │ Inventory    │  │ Logistics    │  ...        │
│  │ (Pluggable)  │  │ Agent        │  │ Agent        │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     Infrastructure Layer (CDK)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Network      │  │ Security     │  │ Data         │             │
│  │ Stack        │  │ Stack        │  │ Stack        │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Application  │  │ Monitoring   │  │ Backup       │             │
│  │ Stack        │  │ Stack        │  │ Stack        │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Configuration Management System

#### 1.1 Configuration File Structure

**File**: `config/{environment}.yaml`

```yaml
# Base configuration structure
environment:
  name: "dev"  # dev, staging, prod
  account_id: "auto"  # Auto-detect or specify
  region: "us-east-1"
  
project:
  name: "supply-chain-agent"
  prefix: "sc-agent"  # Used for resource naming
  owner: "platform-team"
  cost_center: "supply-chain"

features:
  vpc_enabled: true
  waf_enabled: false
  multi_az: false
  xray_tracing: false
  backup_enabled: true

resources:
  lambda:
    memory_mb: 512
    timeout_seconds: 180
    reserved_concurrency: 10
    architecture: "arm64"  # arm64 or x86_64
  
  dynamodb:
    billing_mode: "PAY_PER_REQUEST"  # PAY_PER_REQUEST or PROVISIONED
    point_in_time_recovery: true
  
  logs:
    retention_days: 7
  
  backup:
    retention_days: 7

networking:
  vpc_cidr: "10.0.0.0/16"
  nat_gateways: 1
  
api:
  throttle_rate_limit: 50
  throttle_burst_limit: 100
  cors_origins:
    - "http://localhost:8501"

monitoring:
  alarm_email: "dev-team@example.com"
  dashboard_enabled: true

agents:
  default_model: "anthropic.claude-3-5-sonnet-20241022-v2:0"
  context_window_size: 10
  conversation_retention_days: 30
  
  sql_agent:
    enabled: true
    model: "anthropic.claude-3-5-sonnet-20241022-v2:0"
    timeout_seconds: 60
  
  inventory_optimizer:
    enabled: true
    model: "anthropic.claude-3-5-sonnet-20241022-v2:0"
    tools:
      - calculate_reorder_points
      - forecast_demand
      - identify_stockout_risks
      - optimize_stock_levels
  
  logistics_agent:
    enabled: true
    model: "anthropic.claude-3-5-sonnet-20241022-v2:0"
  
  supplier_analyzer:
    enabled: true
    model: "anthropic.claude-3-5-sonnet-20241022-v2:0"

data:
  athena_database: "supply_chain_db"
  glue_catalog: "AwsDataCatalog"

tags:
  custom:
    Department: "Operations"
    Compliance: "SOC2"
```

#### 1.2 Configuration Loader

**Class**: `ConfigurationManager`

```python
class ConfigurationManager:
    """Centralized configuration management"""
    
    def __init__(self, environment: str, config_path: str = "config"):
        self.environment = environment
        self.config = self._load_config(config_path)
        self._validate_config()
    
    def _load_config(self, path: str) -> Dict:
        """Load and merge base + environment configs"""
        
    def _validate_config(self):
        """Validate against JSON schema"""
        
    def get(self, key_path: str, default=None):
        """Get config value by dot notation path"""
        
    def get_resource_name(self, resource_type: str, name: str) -> str:
        """Generate standardized resource name"""
        
    def get_tags(self) -> Dict[str, str]:
        """Get all tags for resources"""
```

#### 1.3 Secrets and Parameters Integration

**Class**: `SecretsManager`

```python
class SecretsManager:
    """Manage secrets and parameters"""
    
    def __init__(self, region: str, prefix: str):
        self.ssm = boto3.client('ssm', region_name=region)
        self.secrets = boto3.client('secretsmanager', region_name=region)
        self.prefix = prefix
    
    def get_secret(self, name: str) -> str:
        """Retrieve secret from Secrets Manager"""
        
    def get_parameter(self, name: str) -> str:
        """Retrieve parameter from Parameter Store"""
        
    def put_secret(self, name: str, value: str):
        """Store secret in Secrets Manager"""
        
    def put_parameter(self, name: str, value: str, secure: bool = False):
        """Store parameter in Parameter Store"""
```

### 2. Dynamic Resource Naming

#### 2.1 Naming Convention

**Pattern**: `{prefix}-{resource-type}-{environment}-{suffix}`

**Examples**:
- S3 Bucket: `sc-agent-data-prod-123456789012-us-east-1`
- DynamoDB Table: `sc-agent-sessions-prod`
- Lambda Function: `sc-agent-inventory-optimizer-prod`
- IAM Role: `sc-agent-lambda-exec-prod`

#### 2.2 Resource Name Generator

```python
class ResourceNamer:
    """Generate consistent resource names"""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
        self.prefix = config.get("project.prefix")
        self.environment = config.get("environment.name")
        self.account_id = self._get_account_id()
        self.region = config.get("environment.region")
    
    def s3_bucket(self, purpose: str) -> str:
        """Generate S3 bucket name (globally unique)"""
        return f"{self.prefix}-{purpose}-{self.account_id}-{self.region}"
    
    def dynamodb_table(self, name: str) -> str:
        """Generate DynamoDB table name"""
        return f"{self.prefix}-{name}-{self.environment}"
    
    def lambda_function(self, name: str) -> str:
        """Generate Lambda function name"""
        return f"{self.prefix}-{name}-{self.environment}"
    
    def iam_role(self, purpose: str) -> str:
        """Generate IAM role name"""
        return f"{self.prefix}-{purpose}-{self.environment}"
```

### 3. Enhanced Agent Framework

#### 3.1 Agent Registry (Plugin Architecture)

**Class**: `AgentRegistry`

```python
class AgentRegistry:
    """Registry for pluggable agents"""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        self._discover_agents()
    
    def _discover_agents(self):
        """Auto-discover and register agents from config"""
        agent_configs = self.config.get("agents")
        for agent_name, agent_config in agent_configs.items():
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
    
    def list_agents(self) -> List[str]:
        """List all registered agents"""
        return list(self.agents.keys())
```

#### 3.2 Model Manager

**Class**: `ModelManager`

```python
class ModelManager:
    """Manage AI model selection and fallback"""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_cache: Dict[str, ModelConfig] = {}
    
    def get_model_for_agent(self, agent_name: str) -> str:
        """Get configured model ID for agent"""
        agent_config = self.config.get(f"agents.{agent_name}")
        return agent_config.get("model", self.config.get("agents.default_model"))
    
    def invoke_model(
        self, 
        model_id: str, 
        messages: List[Dict],
        system_prompt: str = "",
        **kwargs
    ) -> Dict:
        """Invoke model with fallback support"""
        try:
            return self._invoke_primary(model_id, messages, system_prompt, **kwargs)
        except Exception as e:
            fallback_model = self._get_fallback_model(model_id)
            if fallback_model:
                return self._invoke_primary(fallback_model, messages, system_prompt, **kwargs)
            raise
    
    def _get_fallback_model(self, model_id: str) -> Optional[str]:
        """Get fallback model if primary fails"""
        # Implement fallback logic
```

#### 3.3 Context Manager

**Class**: `ConversationContextManager`

```python
class ConversationContextManager:
    """Manage conversation history and context"""
    
    def __init__(self, config: ConfigurationManager, dynamodb_table: str):
        self.config = config
        self.table = boto3.resource('dynamodb').Table(dynamodb_table)
        self.context_window = config.get("agents.context_window_size", 10)
    
    def get_context(self, session_id: str, max_messages: int = None) -> List[Dict]:
        """Retrieve conversation context"""
        max_messages = max_messages or self.context_window
        # Retrieve from DynamoDB
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None):
        """Add message to conversation history"""
        # Store in DynamoDB with TTL
    
    def summarize_context(self, session_id: str) -> str:
        """Summarize conversation when context exceeds limits"""
        # Use LLM to summarize
    
    def clear_context(self, session_id: str):
        """Clear conversation history"""
```

### 4. Enhanced Orchestrator

#### 4.1 Updated Orchestrator Design

```python
class SupplyChainOrchestrator:
    """Enhanced orchestrator with plugin support"""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
        self.agent_registry = AgentRegistry(config)
        self.model_manager = ModelManager(config)
        self.context_manager = ConversationContextManager(config, ...)
        self.metrics_collector = MetricsCollector(config)
        self.access_controller = AccessController(config)
    
    def process_query(
        self,
        query: str,
        persona: str,
        session_id: str,
        user_context: Dict
    ) -> Dict[str, Any]:
        """Process query with enhanced capabilities"""
        
        # Access control check
        if not self.access_controller.authorize(user_context, persona):
            return {"success": False, "error": "Access denied", "status": 403}
        
        # Get conversation context
        context = self.context_manager.get_context(session_id)
        
        # Classify intent
        intent = self.classify_intent(query, persona, context)
        
        # Route to agents
        agents = self._get_agents_for_intent(intent, persona)
        
        # Execute with metrics
        start_time = time.time()
        try:
            results = self._execute_agents(agents, query, session_id, user_context, context)
            self.metrics_collector.record_success(persona, time.time() - start_time)
            return results
        except Exception as e:
            self.metrics_collector.record_error(persona, str(e))
            raise
    
    def _execute_agents(
        self,
        agents: List[BaseAgent],
        query: str,
        session_id: str,
        user_context: Dict,
        context: List[Dict]
    ) -> Dict:
        """Execute agents with parallel tool support"""
        # Implement parallel execution
```

### 5. Asynchronous Tool Execution

#### 5.1 Tool Executor

```python
class ToolExecutor:
    """Execute agent tools asynchronously"""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
        self.lambda_client = boto3.client('lambda')
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def execute_tools_parallel(
        self,
        tools: List[Dict],
        timeout: int = 30
    ) -> List[Dict]:
        """Execute multiple tools in parallel"""
        tasks = [self._execute_tool(tool, timeout) for tool in tools]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._process_results(results)
    
    async def _execute_tool(self, tool: Dict, timeout: int) -> Dict:
        """Execute single tool with retry"""
        for attempt in range(3):
            try:
                result = await self._invoke_lambda(tool, timeout)
                return {"success": True, "result": result}
            except Exception as e:
                if attempt == 2:
                    return {"success": False, "error": str(e)}
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 6. Monitoring and Analytics

#### 6.1 Metrics Collector

```python
class MetricsCollector:
    """Collect and publish agent metrics"""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = f"{config.get('project.prefix')}/Agents"
    
    def record_query(
        self,
        persona: str,
        agent: str,
        latency_ms: float,
        success: bool,
        token_count: int = 0
    ):
        """Record query metrics"""
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    'MetricName': 'QueryLatency',
                    'Value': latency_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'Persona', 'Value': persona},
                        {'Name': 'Agent', 'Value': agent}
                    ]
                },
                {
                    'MetricName': 'QueryCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Persona', 'Value': persona},
                        {'Name': 'Success', 'Value': str(success)}
                    ]
                },
                {
                    'MetricName': 'TokenUsage',
                    'Value': token_count,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Agent', 'Value': agent}
                    ]
                }
            ]
        )
```

#### 6.2 CloudWatch Dashboard

```python
# CDK Dashboard Definition
dashboard = cloudwatch.Dashboard(
    self, "AgentDashboard",
    dashboard_name=f"{config.get_resource_name('dashboard', 'agents')}"
)

dashboard.add_widgets(
    cloudwatch.GraphWidget(
        title="Query Latency by Persona",
        left=[
            cloudwatch.Metric(
                namespace=f"{prefix}/Agents",
                metric_name="QueryLatency",
                statistic="Average",
                dimensions_map={"Persona": persona}
            ) for persona in ["warehouse_manager", "field_engineer", "procurement_specialist"]
        ]
    ),
    cloudwatch.GraphWidget(
        title="Success Rate",
        left=[
            cloudwatch.Metric(
                namespace=f"{prefix}/Agents",
                metric_name="QueryCount",
                statistic="Sum",
                dimensions_map={"Success": "True"}
            )
        ]
    ),
    cloudwatch.GraphWidget(
        title="Token Usage by Agent",
        left=[
            cloudwatch.Metric(
                namespace=f"{prefix}/Agents",
                metric_name="TokenUsage",
                statistic="Sum"
            )
        ]
    )
)
```

### 7. Access Control Enhancement

#### 7.1 Access Controller

```python
class AccessController:
    """Fine-grained access control"""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
        self.table_permissions = self._load_table_permissions()
        self.tool_permissions = self._load_tool_permissions()
    
    def authorize(self, user_context: Dict, persona: str) -> bool:
        """Authorize user for persona"""
        user_groups = user_context.get('groups', [])
        required_group = self._get_group_for_persona(persona)
        return required_group in user_groups
    
    def authorize_table_access(
        self,
        user_context: Dict,
        table_name: str
    ) -> bool:
        """Authorize table access"""
        persona = user_context.get('persona')
        allowed_tables = self.table_permissions.get(persona, [])
        return table_name in allowed_tables
    
    def authorize_tool_access(
        self,
        user_context: Dict,
        tool_name: str
    ) -> bool:
        """Authorize tool execution"""
        persona = user_context.get('persona')
        allowed_tools = self.tool_permissions.get(persona, [])
        return tool_name in allowed_tools
    
    def inject_row_level_security(
        self,
        user_context: Dict,
        sql_query: str
    ) -> str:
        """Inject row-level security filters"""
        # Add WHERE clauses based on user context
        # Example: Add warehouse_code filter for warehouse managers
```

## Data Models

### Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["environment", "project", "resources"],
  "properties": {
    "environment": {
      "type": "object",
      "required": ["name", "region"],
      "properties": {
        "name": {"type": "string", "enum": ["dev", "staging", "prod"]},
        "account_id": {"type": "string"},
        "region": {"type": "string"}
      }
    },
    "project": {
      "type": "object",
      "required": ["name", "prefix"],
      "properties": {
        "name": {"type": "string"},
        "prefix": {"type": "string", "pattern": "^[a-z0-9-]+$"},
        "owner": {"type": "string"},
        "cost_center": {"type": "string"}
      }
    },
    "features": {
      "type": "object",
      "properties": {
        "vpc_enabled": {"type": "boolean"},
        "waf_enabled": {"type": "boolean"},
        "multi_az": {"type": "boolean"},
        "xray_tracing": {"type": "boolean"},
        "backup_enabled": {"type": "boolean"}
      }
    }
  }
}
```

### Agent Metrics Schema

```python
@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    persona: str
    agent_name: str
    query: str
    timestamp: datetime
    latency_ms: float
    success: bool
    error_message: Optional[str]
    token_count: int
    tool_executions: List[Dict]
    user_id: str
```

### Conversation Context Schema

```python
@dataclass
class ConversationMessage:
    """Conversation message"""
    session_id: str
    timestamp: datetime
    role: str  # user, assistant, system
    content: str
    metadata: Dict
    token_count: int
    ttl: int  # DynamoDB TTL
```

## Error Handling

### 1. Configuration Errors

- **Missing Required Config**: Fail fast at startup with clear error message
- **Invalid Config Values**: Validate against schema and provide specific error
- **Missing AWS Resources**: Check prerequisites before deployment

### 2. Runtime Errors

- **Model Unavailable**: Fallback to alternative model
- **Tool Execution Failure**: Return partial results with error context
- **Access Denied**: Return 403 with clear message (no system details)
- **Timeout**: Cancel operation and return timeout error

### 3. Deployment Errors

- **CDK Synthesis Failure**: Validate configuration before synthesis
- **Resource Creation Failure**: Rollback stack automatically
- **Quota Exceeded**: Check quotas in pre-deployment validation

## Testing Strategy

### 1. Unit Tests

- Configuration loading and validation
- Resource name generation
- Access control logic
- Agent registration and discovery
- Model selection and fallback

### 2. Integration Tests

- End-to-end agent query processing
- Tool execution with real Lambda functions
- DynamoDB context storage and retrieval
- CloudWatch metrics publishing
- Secrets Manager integration

### 3. Deployment Tests

- Deploy to test AWS account
- Verify all resources created correctly
- Test configuration overrides
- Validate resource naming
- Test cleanup script

### 4. Performance Tests

- Query latency under load
- Parallel tool execution
- Context retrieval performance
- Token usage optimization

## Deployment Process

### 1. Pre-Deployment Validation

```bash
# Validation script
./scripts/validate-deployment.sh --environment dev --config config/dev.yaml

# Checks:
# - AWS credentials configured
# - Target account/region accessible
# - Bedrock model access enabled
# - Service quotas sufficient
# - Configuration file valid
# - Required IAM permissions present
```

### 2. Deployment Steps

```bash
# 1. Set environment
export ENVIRONMENT=dev

# 2. Load configuration
./scripts/load-config.sh --environment $ENVIRONMENT

# 3. Bootstrap CDK (first time only)
./scripts/bootstrap-cdk.sh --environment $ENVIRONMENT

# 4. Deploy infrastructure
./scripts/deploy.sh --environment $ENVIRONMENT

# 5. Post-deployment configuration
./scripts/post-deploy.sh --environment $ENVIRONMENT

# 6. Verify deployment
./scripts/verify-deployment.sh --environment $ENVIRONMENT
```

### 3. Post-Deployment

- Store outputs in Parameter Store
- Create Cognito users
- Upload sample data (if needed)
- Run smoke tests
- Update documentation with endpoints

### 4. Rollback

```bash
# Rollback to previous version
./scripts/rollback.sh --environment $ENVIRONMENT --version previous

# Complete cleanup
./scripts/cleanup.sh --environment $ENVIRONMENT --confirm
```

## Security Considerations

### 1. Secrets Management

- All credentials in Secrets Manager with rotation
- No secrets in code or environment variables
- Secrets encrypted with KMS
- Audit logging for secret access

### 2. Network Security

- Lambda functions in private subnets (when VPC enabled)
- VPC endpoints for AWS services
- Security groups with least privilege
- WAF for API Gateway (production)

### 3. IAM Security

- Least privilege IAM roles
- Service-specific roles (no shared roles)
- Resource-based policies where applicable
- Regular IAM access analysis

### 4. Data Security

- Encryption at rest (S3, DynamoDB, EBS)
- Encryption in transit (TLS 1.2+)
- KMS customer-managed keys
- S3 bucket policies blocking public access

### 5. Application Security

- Input validation and sanitization
- SQL injection prevention
- Row-level security enforcement
- Rate limiting and throttling
- Audit logging for all operations

## Cost Optimization

### 1. Environment-Specific Sizing

| Resource | Dev | Staging | Prod |
|----------|-----|---------|------|
| Lambda Memory | 512 MB | 1024 MB | 1024 MB |
| Lambda Concurrency | 10 | 50 | 100 |
| Log Retention | 7 days | 14 days | 30 days |
| Backup Retention | 7 days | 14 days | 30 days |
| NAT Gateways | 1 | 2 | 3 |

### 2. Cost Reduction Strategies

- ARM64 Lambda architecture (20% cost reduction)
- DynamoDB on-demand for variable workloads
- S3 Intelligent-Tiering for data
- Athena partition pruning
- Lambda provisioned concurrency only for prod
- CloudWatch Logs retention policies

### 3. Cost Monitoring

- Cost allocation tags on all resources
- CloudWatch billing alarms
- Cost Explorer reports
- Budget alerts per environment

## Performance Optimization

### 1. Latency Optimization

- Parallel tool execution
- Lambda warm starts (provisioned concurrency)
- DynamoDB DAX for caching (optional)
- API Gateway caching
- Athena query result caching

### 2. Throughput Optimization

- Lambda reserved concurrency
- DynamoDB auto-scaling (if provisioned)
- API Gateway throttling limits
- Batch processing for bulk operations

### 3. Token Usage Optimization

- Context window management
- Conversation summarization
- Prompt caching (when available)
- Model selection per use case

## Monitoring and Observability

### 1. Metrics

- Query latency (p50, p95, p99)
- Success rate per agent
- Token usage per agent
- Tool execution time
- Error rate by type
- Cost per query

### 2. Logs

- Structured JSON logging
- Request/response logging
- Error stack traces
- Access control decisions
- Tool execution details

### 3. Alarms

- High error rate
- High latency
- Lambda throttling
- DynamoDB throttling
- Cost threshold exceeded

### 4. Dashboards

- Agent performance overview
- Cost tracking
- Error analysis
- User activity
- Resource utilization

## Documentation

### 1. Deployment Guide

- Prerequisites checklist
- Step-by-step deployment
- Configuration reference
- Troubleshooting guide
- Rollback procedures

### 2. Configuration Reference

- All configuration parameters
- Default values
- Valid ranges
- Examples per environment

### 3. Agent Development Guide

- Creating new agents
- Tool definition format
- Testing agents
- Registering agents

### 4. Operations Runbook

- Common issues and solutions
- Monitoring and alerting
- Backup and restore
- Scaling procedures
- Security incident response
