# Configuration Reference

## Table of Contents

1. [Overview](#overview)
2. [Configuration File Structure](#configuration-file-structure)
3. [Environment Section](#environment-section)
4. [Project Section](#project-section)
5. [Features Section](#features-section)
6. [Resources Section](#resources-section)
7. [Networking Section](#networking-section)
8. [API Section](#api-section)
9. [Monitoring Section](#monitoring-section)
10. [Agents Section](#agents-section)
11. [Data Section](#data-section)
12. [Tags Section](#tags-section)
13. [Configuration Examples](#configuration-examples)
14. [Environment Variables](#environment-variables)
15. [Best Practices](#best-practices)

## Overview

The Supply Chain Agentic AI Application uses YAML configuration files to manage environment-specific settings. Each environment (dev, staging, prod) has its own configuration file that defines all deployment parameters.

### Configuration File Location

Configuration files are stored in the `config/` directory:
```
config/
├── dev.yaml       # Development environment
├── staging.yaml   # Staging environment
├── prod.yaml      # Production environment
└── schema.json    # JSON Schema for validation
```

### Configuration Validation

All configuration files are validated against `config/schema.json` before deployment:

```bash
python scripts/validate-config.py --config config/dev.yaml
```

## Configuration File Structure

```yaml
environment:      # Environment identification
project:          # Project metadata
features:         # Feature flags
resources:        # Resource sizing and configuration
networking:       # Network configuration
api:              # API Gateway settings
monitoring:       # Monitoring and alerting
agents:           # AI agent configuration
data:             # Data source configuration
tags:             # Resource tagging
```

## Environment Section

Defines the target AWS environment for deployment.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | Yes | - | Environment name: `dev`, `staging`, or `prod` |
| `account_id` | string | No | auto-detect | AWS account ID (use "auto" for auto-detection) |
| `region` | string | Yes | - | AWS region (e.g., `us-east-1`) |

### Example

```yaml
environment:
  name: "dev"
  account_id: "auto"  # Auto-detect from AWS credentials
  region: "us-east-1"
```

### Valid Regions

- `us-east-1` (N. Virginia)
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)
- `ap-southeast-1` (Singapore)
- Any region where Amazon Bedrock is available

## Project Section

Defines project metadata used for resource naming and tagging.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | Yes | - | Project name (alphanumeric and hyphens) |
| `prefix` | string | Yes | - | Resource name prefix (lowercase, max 20 chars) |
| `owner` | string | Yes | - | Team or individual owner email |
| `cost_center` | string | No | - | Cost center for billing allocation |

### Example

```yaml
project:
  name: "supply-chain-agent"
  prefix: "sc-agent"
  owner: "platform-team@example.com"
  cost_center: "supply-chain-ops"
```

### Naming Conventions

The `prefix` is used to generate all resource names:
- S3 Buckets: `{prefix}-{purpose}-{account-id}-{region}`
- DynamoDB Tables: `{prefix}-{name}-{environment}`
- Lambda Functions: `{prefix}-{function}-{environment}`
- IAM Roles: `{prefix}-{role}-{environment}`

## Features Section

Feature flags to enable/disable optional components.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `vpc_enabled` | boolean | No | `false` | Deploy Lambda functions in VPC |
| `waf_enabled` | boolean | No | `false` | Enable AWS WAF for API Gateway |
| `multi_az` | boolean | No | `false` | Deploy across multiple availability zones |
| `xray_tracing` | boolean | No | `false` | Enable AWS X-Ray tracing |
| `backup_enabled` | boolean | No | `true` | Enable automated backups |

### Example

```yaml
features:
  vpc_enabled: true      # Use VPC for Lambda
  waf_enabled: false     # No WAF in dev
  multi_az: false        # Single AZ for dev
  xray_tracing: true     # Enable tracing
  backup_enabled: true   # Enable backups
```

### Feature Impact

- **vpc_enabled**: Adds VPC, subnets, NAT gateways (increases cost)
- **waf_enabled**: Adds WAF rules for API protection (recommended for prod)
- **multi_az**: Deploys resources across 3 AZs (increases availability and cost)
- **xray_tracing**: Enables detailed request tracing (slight performance impact)
- **backup_enabled**: Enables DynamoDB point-in-time recovery and S3 versioning

## Resources Section

Configures resource sizing and capacity settings.

### Lambda Configuration

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `memory_mb` | integer | No | `512` | Lambda memory in MB (128-10240) |
| `timeout_seconds` | integer | No | `180` | Lambda timeout in seconds (1-900) |
| `reserved_concurrency` | integer | No | `10` | Reserved concurrent executions |
| `architecture` | string | No | `arm64` | CPU architecture: `arm64` or `x86_64` |

### DynamoDB Configuration

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `billing_mode` | string | No | `PAY_PER_REQUEST` | `PAY_PER_REQUEST` or `PROVISIONED` |
| `point_in_time_recovery` | boolean | No | `true` | Enable point-in-time recovery |
| `read_capacity` | integer | No | `5` | Read capacity units (if PROVISIONED) |
| `write_capacity` | integer | No | `5` | Write capacity units (if PROVISIONED) |

### Logs Configuration

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `retention_days` | integer | No | `7` | CloudWatch Logs retention (1-3653 days) |

### Backup Configuration

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `retention_days` | integer | No | `7` | Backup retention period (1-35 days) |

### Example

```yaml
resources:
  lambda:
    memory_mb: 1024
    timeout_seconds: 300
    reserved_concurrency: 50
    architecture: "arm64"
  
  dynamodb:
    billing_mode: "PAY_PER_REQUEST"
    point_in_time_recovery: true
  
  logs:
    retention_days: 14
  
  backup:
    retention_days: 14
```

### Sizing Recommendations

| Environment | Lambda Memory | Concurrency | Log Retention | Backup Retention |
|-------------|---------------|-------------|---------------|------------------|
| Development | 512 MB | 10 | 7 days | 7 days |
| Staging | 1024 MB | 50 | 14 days | 14 days |
| Production | 1024-2048 MB | 100+ | 30 days | 30 days |

## Networking Section

Configures VPC and network settings (only used if `vpc_enabled: true`).

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `vpc_cidr` | string | No | `10.0.0.0/16` | VPC CIDR block |
| `nat_gateways` | integer | No | `1` | Number of NAT gateways (1-3) |
| `vpc_endpoints` | array | No | `[]` | List of VPC endpoints to create |

### Example

```yaml
networking:
  vpc_cidr: "10.0.0.0/16"
  nat_gateways: 2
  vpc_endpoints:
    - "s3"
    - "dynamodb"
    - "secretsmanager"
    - "ssm"
```

### VPC Endpoint Options

- `s3` - S3 Gateway endpoint (no cost)
- `dynamodb` - DynamoDB Gateway endpoint (no cost)
- `secretsmanager` - Secrets Manager Interface endpoint
- `ssm` - Systems Manager Interface endpoint
- `bedrock-runtime` - Bedrock Runtime Interface endpoint

## API Section

Configures API Gateway settings.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `throttle_rate_limit` | integer | No | `50` | Steady-state requests per second |
| `throttle_burst_limit` | integer | No | `100` | Maximum burst requests |
| `cors_origins` | array | No | `["*"]` | Allowed CORS origins |
| `api_key_required` | boolean | No | `false` | Require API key for requests |

### Example

```yaml
api:
  throttle_rate_limit: 100
  throttle_burst_limit: 200
  cors_origins:
    - "https://app.example.com"
    - "http://localhost:8501"
  api_key_required: false
```

### Throttling Guidelines

| Environment | Rate Limit | Burst Limit |
|-------------|------------|-------------|
| Development | 10-50 | 50-100 |
| Staging | 50-100 | 100-200 |
| Production | 100-1000 | 200-2000 |

## Monitoring Section

Configures CloudWatch monitoring and alerting.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `alarm_email` | string | No | - | Email for alarm notifications |
| `dashboard_enabled` | boolean | No | `true` | Create CloudWatch dashboard |
| `detailed_monitoring` | boolean | No | `false` | Enable detailed CloudWatch metrics |

### Example

```yaml
monitoring:
  alarm_email: "ops-team@example.com"
  dashboard_enabled: true
  detailed_monitoring: true
```

## Agents Section

Configures AI agents and their behavior.

### Global Agent Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `default_model` | string | No | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Default Bedrock model ID |
| `context_window_size` | integer | No | `10` | Number of conversation messages to retain |
| `conversation_retention_days` | integer | No | `30` | Days to retain conversation history |

### Per-Agent Configuration

Each agent can have its own configuration:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Enable/disable the agent |
| `model` | string | No | (uses default) | Bedrock model ID for this agent |
| `timeout_seconds` | integer | No | `60` | Agent execution timeout |
| `tools` | array | No | `[]` | List of tool names available to agent |

### Example

```yaml
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
    tools:
      - optimize_routes
      - calculate_shipping_costs
      - track_shipments
  
  supplier_analyzer:
    enabled: true
    model: "anthropic.claude-3-5-sonnet-20241022-v2:0"
    tools:
      - analyze_supplier_performance
      - identify_risks
      - recommend_alternatives
```

### Available Models

- `anthropic.claude-3-5-sonnet-20241022-v2:0` - Claude 3.5 Sonnet (recommended)
- `anthropic.claude-3-sonnet-20240229-v1:0` - Claude 3 Sonnet
- `anthropic.claude-3-haiku-20240307-v1:0` - Claude 3 Haiku (faster, lower cost)
- `amazon.titan-text-premier-v1:0` - Amazon Titan Text Premier
- `meta.llama3-70b-instruct-v1:0` - Meta Llama 3 70B

## Data Section

Configures data sources and databases.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `athena_database` | string | No | `supply_chain_db` | Athena database name |
| `glue_catalog` | string | No | `AwsDataCatalog` | Glue Data Catalog name |
| `s3_data_prefix` | string | No | `data/` | S3 prefix for data files |

### Example

```yaml
data:
  athena_database: "supply_chain_db"
  glue_catalog: "AwsDataCatalog"
  s3_data_prefix: "data/"
```

## Tags Section

Defines resource tags for cost allocation and governance.

### Standard Tags

These tags are automatically applied:
- `Project` - From `project.name`
- `Environment` - From `environment.name`
- `ManagedBy` - Set to "CDK"
- `Owner` - From `project.owner`
- `CostCenter` - From `project.cost_center`

### Custom Tags

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `custom` | object | No | `{}` | Additional custom tags |

### Example

```yaml
tags:
  custom:
    Department: "Operations"
    Compliance: "SOC2"
    DataClassification: "Internal"
    BackupPolicy: "Daily"
```

## Configuration Examples

### Development Environment

```yaml
environment:
  name: "dev"
  region: "us-east-1"

project:
  name: "supply-chain-agent"
  prefix: "sc-agent"
  owner: "dev-team@example.com"

features:
  vpc_enabled: false
  waf_enabled: false
  multi_az: false
  xray_tracing: true

resources:
  lambda:
    memory_mb: 512
    timeout_seconds: 180
    reserved_concurrency: 10
    architecture: "arm64"
  logs:
    retention_days: 7
  backup:
    retention_days: 7

api:
  throttle_rate_limit: 50
  throttle_burst_limit: 100

agents:
  default_model: "anthropic.claude-3-haiku-20240307-v1:0"  # Lower cost
  context_window_size: 5
```

### Production Environment

```yaml
environment:
  name: "prod"
  region: "us-east-1"

project:
  name: "supply-chain-agent"
  prefix: "sc-agent"
  owner: "platform-team@example.com"
  cost_center: "supply-chain-ops"

features:
  vpc_enabled: true
  waf_enabled: true
  multi_az: true
  xray_tracing: true
  backup_enabled: true

resources:
  lambda:
    memory_mb: 2048
    timeout_seconds: 300
    reserved_concurrency: 100
    architecture: "arm64"
  dynamodb:
    billing_mode: "PAY_PER_REQUEST"
    point_in_time_recovery: true
  logs:
    retention_days: 30
  backup:
    retention_days: 30

networking:
  vpc_cidr: "10.0.0.0/16"
  nat_gateways: 3
  vpc_endpoints:
    - "s3"
    - "dynamodb"
    - "secretsmanager"
    - "bedrock-runtime"

api:
  throttle_rate_limit: 500
  throttle_burst_limit: 1000
  cors_origins:
    - "https://app.example.com"

monitoring:
  alarm_email: "ops-team@example.com"
  dashboard_enabled: true
  detailed_monitoring: true

agents:
  default_model: "anthropic.claude-3-5-sonnet-20241022-v2:0"
  context_window_size: 20
  conversation_retention_days: 90

tags:
  custom:
    Department: "Operations"
    Compliance: "SOC2"
    DataClassification: "Confidential"
```

## Environment Variables

Configuration values are loaded into environment variables during deployment:

| Environment Variable | Configuration Path | Description |
|---------------------|-------------------|-------------|
| `ENVIRONMENT` | `environment.name` | Environment name |
| `AWS_REGION` | `environment.region` | AWS region |
| `PROJECT_PREFIX` | `project.prefix` | Resource name prefix |
| `DEFAULT_MODEL_ID` | `agents.default_model` | Default Bedrock model |
| `CONTEXT_WINDOW_SIZE` | `agents.context_window_size` | Conversation context size |

See [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) for complete list.

## Best Practices

### 1. Use Environment-Specific Files

Create separate configuration files for each environment:
```
config/dev.yaml
config/staging.yaml
config/prod.yaml
```

### 2. Never Commit Secrets

Never put sensitive values in configuration files. Use AWS Secrets Manager:
```yaml
# ❌ Bad
database:
  password: "my-secret-password"

# ✅ Good
database:
  password_secret: "/sc-agent/prod/database/password"
```

### 3. Use Consistent Prefixes

Use the same prefix across all environments for easy identification:
```yaml
# Development
prefix: "sc-agent"

# Production
prefix: "sc-agent"  # Same prefix, different environment
```

### 4. Validate Before Deployment

Always validate configuration before deploying:
```bash
python scripts/validate-config.py --config config/prod.yaml
```

### 5. Document Custom Settings

Add comments to explain non-obvious settings:
```yaml
resources:
  lambda:
    memory_mb: 2048  # Increased for large dataset processing
    reserved_concurrency: 100  # Peak load: 80 req/sec
```

### 6. Use Feature Flags Wisely

Enable expensive features only where needed:
```yaml
# Development: minimal features
features:
  vpc_enabled: false
  waf_enabled: false
  multi_az: false

# Production: full features
features:
  vpc_enabled: true
  waf_enabled: true
  multi_az: true
```

### 7. Monitor Costs

Use appropriate resource sizing for each environment:
```yaml
# Development: cost-optimized
resources:
  lambda:
    memory_mb: 512
    reserved_concurrency: 10

# Production: performance-optimized
resources:
  lambda:
    memory_mb: 2048
    reserved_concurrency: 100
```

### 8. Version Control

Keep configuration files in version control:
```bash
git add config/dev.yaml
git commit -m "Update dev configuration"
```

### 9. Use Schema Validation

Leverage the JSON schema for validation:
```bash
# Validate against schema
python scripts/validate-config.py --config config/prod.yaml --schema config/schema.json
```

### 10. Test Configuration Changes

Test configuration changes in dev before applying to production:
```bash
# Deploy to dev first
./deploy.sh --environment dev --config config/dev.yaml

# Verify functionality
./scripts/verify-deployment.sh --environment dev

# Then deploy to prod
./deploy.sh --environment prod --config config/prod.yaml
```

## Related Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment instructions
- [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) - Environment variable reference
- [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) - Troubleshooting help
- [config/schema.json](config/schema.json) - JSON Schema definition
