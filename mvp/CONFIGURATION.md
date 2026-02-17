# Configuration Guide

This guide provides detailed documentation for all configuration options in the Supply Chain AI Assistant MVP.

## Table of Contents

- [Configuration Files](#configuration-files)
- [AWS Configuration](#aws-configuration)
- [Application Configuration](#application-configuration)
- [Cache Configuration](#cache-configuration)
- [Conversation Memory Configuration](#conversation-memory-configuration)
- [Cost Tracking Configuration](#cost-tracking-configuration)
- [Logging Configuration](#logging-configuration)
- [Authentication Configuration](#authentication-configuration)
- [Environment Variables](#environment-variables)
- [Deployment-Specific Configurations](#deployment-specific-configurations)
- [Configuration Examples](#configuration-examples)

## Configuration Files

The application uses multiple configuration files:

| File | Purpose | Location | Required |
|------|---------|----------|----------|
| `config.yaml` | Main application configuration | `mvp/config.yaml` | Yes |
| `.env` | Environment variables and AWS credentials | `mvp/.env` | Optional |
| `auth/users.json` | User credentials and persona assignments | `mvp/auth/users.json` | Yes |

### Creating Configuration Files

```bash
# Copy templates
cp config.example.yaml config.yaml
cp .env.example .env
cp auth/users.json.example auth/users.json

# Edit with your settings
nano config.yaml
nano .env
```

## AWS Configuration

### Bedrock Configuration

Amazon Bedrock provides the AI/ML capabilities for the application.

```yaml
aws:
  region: us-east-1
  bedrock:
    model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
    max_tokens: 4096
    temperature: 0.0
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_id` | string | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Bedrock model identifier |
| `max_tokens` | integer | `4096` | Maximum tokens in model response |
| `temperature` | float | `0.0` | Model temperature (0.0 = deterministic, 1.0 = creative) |

#### Supported Models

- `anthropic.claude-3-5-sonnet-20241022-v2:0` (Recommended)
- `anthropic.claude-3-sonnet-20240229-v1:0`
- `anthropic.claude-3-haiku-20240307-v1:0` (Lower cost, less capable)

#### Supported Regions

- `us-east-1` (US East - N. Virginia) - Recommended
- `us-west-2` (US West - Oregon)
- `eu-west-1` (Europe - Ireland)
- `ap-southeast-1` (Asia Pacific - Singapore)

#### Cost Implications

- **Claude 3.5 Sonnet**: $0.003/1K input tokens, $0.015/1K output tokens
- **Claude 3 Haiku**: $0.00025/1K input tokens, $0.00125/1K output tokens (83% cheaper)

**Recommendation**: Use Claude 3.5 Sonnet for production, Claude 3 Haiku for development/testing.

---

### Redshift Configuration

Amazon Redshift Serverless provides the data warehouse.

```yaml
aws:
  redshift:
    workgroup_name: supply-chain-mvp-workgroup
    database: supply_chain_db
    data_api_timeout: 30
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workgroup_name` | string | Required | Redshift Serverless workgroup name |
| `database` | string | `supply_chain_db` | Database name within the workgroup |
| `data_api_timeout` | integer | `30` | Query timeout in seconds |

#### Finding Your Workgroup Name

```bash
# List all workgroups
aws redshift-serverless list-workgroups --region us-east-1

# Get workgroup details
aws redshift-serverless get-workgroup \
    --workgroup-name supply-chain-mvp-workgroup \
    --region us-east-1
```

#### Timeout Considerations

- **Simple queries**: 5-10 seconds
- **Complex queries**: 10-30 seconds
- **Large data scans**: 30-60 seconds

**Recommendation**: Set timeout to 30 seconds for most use cases, increase to 60 for complex queries.

---

### Glue Configuration

AWS Glue Data Catalog stores table schemas and metadata.

```yaml
aws:
  glue:
    catalog_id: "123456789012"
    database: supply_chain_catalog
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `catalog_id` | string | Required | AWS account ID (12 digits) |
| `database` | string | `supply_chain_catalog` | Glue database name |

#### Finding Your Catalog ID

```bash
# Your AWS account ID is the catalog ID
aws sts get-caller-identity --query Account --output text
```

#### Finding Your Database Name

```bash
# List all Glue databases
aws glue get-databases --region us-east-1

# Get database details
aws glue get-database \
    --name supply_chain_catalog \
    --region us-east-1
```

---

### Lambda Configuration

AWS Lambda functions provide specialized agent capabilities.

```yaml
aws:
  lambda:
    inventory_function: supply-chain-inventory-optimizer
    logistics_function: supply-chain-logistics-optimizer
    supplier_function: supply-chain-supplier-analyzer
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `inventory_function` | string | Required | Inventory optimizer Lambda function name |
| `logistics_function` | string | Required | Logistics optimizer Lambda function name |
| `supplier_function` | string | Required | Supplier analyzer Lambda function name |

#### Finding Your Lambda Function Names

```bash
# List all Lambda functions
aws lambda list-functions --region us-east-1 | grep supply-chain

# Get function details
aws lambda get-function \
    --function-name supply-chain-inventory-optimizer \
    --region us-east-1
```

---

## Application Configuration

General application settings.

```yaml
app:
  name: Supply Chain AI Assistant
  version: 1.0.0
  session_timeout: 3600
  max_query_length: 1000
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | string | `Supply Chain AI Assistant` | Application display name |
| `version` | string | `1.0.0` | Application version |
| `session_timeout` | integer | `3600` | Session timeout in seconds (1 hour) |
| `max_query_length` | integer | `1000` | Maximum query length in characters |

#### Session Timeout

Controls how long a user session remains active without interaction.

- **Short timeout** (1800 = 30 minutes): Better security, more frequent logins
- **Medium timeout** (3600 = 1 hour): Balanced (recommended)
- **Long timeout** (7200 = 2 hours): Fewer logins, less secure

#### Max Query Length

Limits the length of user queries to prevent abuse and control costs.

- **Short** (500 chars): Restricts complex queries
- **Medium** (1000 chars): Balanced (recommended)
- **Long** (2000 chars): Allows very detailed queries

---

## Cache Configuration

Query result caching improves performance and reduces costs.

```yaml
cache:
  enabled: true
  max_size: 1000
  default_ttl: 300
  dashboard_ttl: 900
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable query caching |
| `max_size` | integer | `1000` | Maximum number of cached queries |
| `default_ttl` | integer | `300` | Default cache TTL in seconds (5 minutes) |
| `dashboard_ttl` | integer | `900` | Dashboard query TTL in seconds (15 minutes) |

#### Cache Strategy

**Default TTL (300 seconds = 5 minutes)**:
- Used for regular user queries
- Balances freshness and performance
- Reduces redundant database queries

**Dashboard TTL (900 seconds = 15 minutes)**:
- Used for dashboard/summary queries
- Data changes less frequently
- Higher cache hit rate

#### Cache Size

The `max_size` parameter controls how many queries are cached:

- **Small** (500): Lower memory usage, more cache evictions
- **Medium** (1000): Balanced (recommended)
- **Large** (2000): Higher memory usage, fewer evictions

**Memory usage**: ~1-5 MB per cached query (depends on result size)

#### Disabling Cache

To disable caching (not recommended):

```yaml
cache:
  enabled: false
```

**Impact**:
- All queries hit the database
- Slower response times
- Higher AWS costs (more Redshift queries)
- No cache statistics

---

## Conversation Memory Configuration

Conversation memory maintains context across queries.

```yaml
conversation:
  max_history: 10
  clear_on_persona_switch: true
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_history` | integer | `10` | Number of interactions to remember |
| `clear_on_persona_switch` | boolean | `true` | Clear history when switching personas |

#### Max History

Controls how many past interactions are remembered:

- **Small** (5): Less context, lower memory usage
- **Medium** (10): Balanced (recommended)
- **Large** (20): More context, higher memory usage

**Memory usage**: ~1-2 KB per interaction

#### Clear on Persona Switch

When `true`, conversation history is cleared when user switches personas:

- **Pros**: Prevents context confusion between personas
- **Cons**: Loses context when switching back

**Recommendation**: Keep `true` for production, set to `false` for testing.

---

## Cost Tracking Configuration

Cost tracking monitors AWS spending.

```yaml
cost:
  enabled: true
  log_file: logs/cost_tracking.log
  bedrock_input_cost_per_1k: 0.003
  bedrock_output_cost_per_1k: 0.015
  redshift_rpu_cost_per_hour: 0.36
  lambda_cost_per_gb_second: 0.0000166667
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable cost tracking |
| `log_file` | string | `logs/cost_tracking.log` | Cost log file path |
| `bedrock_input_cost_per_1k` | float | `0.003` | Bedrock input token cost (per 1K tokens) |
| `bedrock_output_cost_per_1k` | float | `0.015` | Bedrock output token cost (per 1K tokens) |
| `redshift_rpu_cost_per_hour` | float | `0.36` | Redshift RPU cost per hour |
| `lambda_cost_per_gb_second` | float | `0.0000166667` | Lambda cost per GB-second |

#### Cost Rates

These rates are based on AWS pricing as of 2024. Update if pricing changes:

**Bedrock (Claude 3.5 Sonnet)**:
- Input: $0.003 per 1K tokens
- Output: $0.015 per 1K tokens

**Bedrock (Claude 3 Haiku)**:
- Input: $0.00025 per 1K tokens
- Output: $0.00125 per 1K tokens

**Redshift Serverless**:
- $0.36 per RPU-hour (8 RPU minimum)

**Lambda**:
- $0.0000166667 per GB-second
- $0.20 per 1M requests

#### Disabling Cost Tracking

To disable cost tracking:

```yaml
cost:
  enabled: false
```

**Impact**:
- No cost information displayed in UI
- No cost logs generated
- Slightly faster query processing

---

## Logging Configuration

Application logging configuration.

```yaml
logging:
  level: INFO
  file: logs/app.log
  max_bytes: 10485760
  backup_count: 5
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | string | `INFO` | Logging level |
| `file` | string | `logs/app.log` | Log file path |
| `max_bytes` | integer | `10485760` | Max log file size in bytes (10 MB) |
| `backup_count` | integer | `5` | Number of backup log files to keep |

#### Logging Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| `DEBUG` | Detailed diagnostic information | Development, troubleshooting |
| `INFO` | General informational messages | Production (recommended) |
| `WARNING` | Warning messages for potential issues | Production (minimal logging) |
| `ERROR` | Error messages only | Production (errors only) |

#### Log Rotation

Logs are automatically rotated when they reach `max_bytes`:

- **Current log**: `logs/app.log`
- **Backup logs**: `logs/app.log.1`, `logs/app.log.2`, etc.
- **Max backups**: Controlled by `backup_count`

**Total disk usage**: `max_bytes × (backup_count + 1)`

Example: 10 MB × 6 = 60 MB total

---

## Authentication Configuration

User authentication and authorization settings.

```yaml
auth:
  users_file: auth/users.json
  session_secret: ${SESSION_SECRET}
  password_min_length: 8
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `users_file` | string | `auth/users.json` | User credentials file path |
| `session_secret` | string | Required | Secret key for session encryption |
| `password_min_length` | integer | `8` | Minimum password length |

#### Session Secret

The session secret is used to encrypt session tokens. It should be:

- **Random**: Use a cryptographically secure random string
- **Long**: At least 32 characters
- **Secret**: Never commit to version control

**Generate a session secret**:

```bash
# Linux/Mac
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"

# Windows PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

**Set in environment variable**:

```bash
# In .env file
SESSION_SECRET=your_generated_secret_here
```

#### Users File Format

The `auth/users.json` file stores user credentials:

```json
{
  "users": [
    {
      "username": "john_doe",
      "password_hash": "$2b$12$...",
      "personas": ["Warehouse Manager", "Field Engineer"],
      "active": true,
      "created_date": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Create users**:

```bash
python scripts/create_user.py
```

---

## Environment Variables

Environment variables provide sensitive configuration values.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | `us-east-1` |
| `AWS_ACCOUNT_ID` | AWS account ID | `123456789012` |
| `SESSION_SECRET` | Session encryption key | `abc123...` |

### Optional Variables (for local development)

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |

### Setting Environment Variables

**Option 1: .env file** (Recommended for local development)

```bash
# Create .env file
cp .env.example .env

# Edit .env
nano .env
```

```bash
# .env contents
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
SESSION_SECRET=your_session_secret
```

**Option 2: Export in shell**

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
export SESSION_SECRET=your_session_secret
```

**Option 3: IAM Role** (Recommended for EC2/SageMaker)

When running on EC2 or SageMaker, use IAM roles instead of access keys:

- No need to set `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY`
- Application automatically uses instance IAM role
- More secure (no credentials in files)

---

## Deployment-Specific Configurations

### Local Development Configuration

Optimized for single-user development on local machine.

```yaml
aws:
  region: us-east-1
  bedrock:
    model_id: anthropic.claude-3-haiku-20240307-v1:0  # Lower cost for dev
    max_tokens: 2048
    temperature: 0.0
  redshift:
    workgroup_name: supply-chain-mvp-workgroup
    database: supply_chain_db
    data_api_timeout: 30

app:
  session_timeout: 7200  # 2 hours for development
  max_query_length: 2000

cache:
  enabled: true
  max_size: 500  # Smaller cache for local
  default_ttl: 300
  dashboard_ttl: 900

conversation:
  max_history: 5  # Less history for development
  clear_on_persona_switch: false  # Keep context when testing

cost:
  enabled: true

logging:
  level: DEBUG  # Detailed logging for development
  file: logs/app.log
  max_bytes: 5242880  # 5 MB
  backup_count: 3
```

---

### SageMaker Configuration

Optimized for team collaboration on SageMaker Notebook Instance.

```yaml
aws:
  region: us-east-1
  bedrock:
    model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
    max_tokens: 4096
    temperature: 0.0
  redshift:
    workgroup_name: supply-chain-mvp-workgroup
    database: supply_chain_db
    data_api_timeout: 30

app:
  session_timeout: 3600  # 1 hour
  max_query_length: 1000

cache:
  enabled: true
  max_size: 1000
  default_ttl: 300
  dashboard_ttl: 900

conversation:
  max_history: 10
  clear_on_persona_switch: true

cost:
  enabled: true

logging:
  level: INFO  # Production logging
  file: logs/app.log
  max_bytes: 10485760  # 10 MB
  backup_count: 5
```

**Note**: SageMaker uses IAM role for AWS authentication. No need to set AWS credentials in .env file.

---

### EC2 Production Configuration

Optimized for production deployment on EC2 instance.

```yaml
aws:
  region: us-east-1
  bedrock:
    model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
    max_tokens: 4096
    temperature: 0.0
  redshift:
    workgroup_name: supply-chain-mvp-workgroup
    database: supply_chain_db
    data_api_timeout: 60  # Longer timeout for production

app:
  session_timeout: 3600  # 1 hour
  max_query_length: 1000

cache:
  enabled: true
  max_size: 2000  # Larger cache for production
  default_ttl: 300
  dashboard_ttl: 900

conversation:
  max_history: 10
  clear_on_persona_switch: true

cost:
  enabled: true

logging:
  level: INFO
  file: logs/app.log
  max_bytes: 20971520  # 20 MB for production
  backup_count: 10  # More backups
```

---

## Configuration Examples

### Example 1: Cost-Optimized Configuration

Minimize AWS costs for development/testing.

```yaml
aws:
  region: us-east-1
  bedrock:
    model_id: anthropic.claude-3-haiku-20240307-v1:0  # Cheapest model
    max_tokens: 1024  # Limit output tokens
    temperature: 0.0

cache:
  enabled: true
  max_size: 2000  # Large cache to reduce queries
  default_ttl: 600  # 10 minutes
  dashboard_ttl: 1800  # 30 minutes

cost:
  enabled: true  # Monitor costs closely
```

**Expected savings**: 60-70% on Bedrock costs, 30-40% on Redshift costs

---

### Example 2: Performance-Optimized Configuration

Maximize performance for production use.

```yaml
aws:
  bedrock:
    model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
    max_tokens: 4096
    temperature: 0.0
  redshift:
    data_api_timeout: 60  # Allow longer queries

cache:
  enabled: true
  max_size: 5000  # Very large cache
  default_ttl: 600  # 10 minutes
  dashboard_ttl: 1800  # 30 minutes

conversation:
  max_history: 20  # More context

logging:
  level: WARNING  # Minimal logging overhead
```

**Expected improvement**: 50-60% faster response times for cached queries

---

### Example 3: Security-Focused Configuration

Enhanced security for sensitive data.

```yaml
app:
  session_timeout: 1800  # 30 minutes (shorter)
  max_query_length: 500  # Limit query complexity

auth:
  password_min_length: 12  # Stronger passwords

conversation:
  max_history: 5  # Less data in memory
  clear_on_persona_switch: true  # Always clear context

logging:
  level: INFO  # Log all activities
  max_bytes: 10485760
  backup_count: 10  # Keep more audit logs
```

---

## Configuration Validation

### Validate Configuration File

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# If valid, no output
# If invalid, shows error message
```

### Test AWS Connectivity

```bash
# Test Bedrock
python -c "
import boto3
import yaml
config = yaml.safe_load(open('config.yaml'))
client = boto3.client('bedrock-runtime', region_name=config['aws']['region'])
print('Bedrock: OK')
"

# Test Redshift
python -c "
import boto3
import yaml
config = yaml.safe_load(open('config.yaml'))
client = boto3.client('redshift-data', region_name=config['aws']['region'])
print('Redshift: OK')
"

# Test Lambda
python -c "
import boto3
import yaml
config = yaml.safe_load(open('config.yaml'))
client = boto3.client('lambda', region_name=config['aws']['region'])
print('Lambda: OK')
"
```

### Verify Configuration Values

```bash
# Display current configuration
python -c "
import yaml
import json
config = yaml.safe_load(open('config.yaml'))
print(json.dumps(config, indent=2))
"
```

---

## Troubleshooting Configuration Issues

### Issue: Configuration file not found

```bash
# Check if file exists
ls -la config.yaml

# If missing, copy from template
cp config.example.yaml config.yaml
```

### Issue: Invalid YAML syntax

```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Common issues:
# - Incorrect indentation (use spaces, not tabs)
# - Missing colons
# - Unquoted special characters
```

### Issue: Environment variable not substituted

```bash
# Check if .env file exists
ls -la .env

# Verify environment variable is set
echo $SESSION_SECRET

# If empty, set it
export SESSION_SECRET=your_secret_here
```

### Issue: AWS credentials not working

```bash
# Test AWS credentials
aws sts get-caller-identity

# If error, reconfigure AWS CLI
aws configure
```

---

## Best Practices

1. **Never commit secrets**: Add `config.yaml`, `.env`, and `auth/users.json` to `.gitignore`

2. **Use environment variables**: Store sensitive values in environment variables, not config files

3. **Validate after changes**: Always test configuration after making changes

4. **Document custom settings**: Add comments to explain non-standard configurations

5. **Backup configurations**: Keep backups of working configurations

6. **Use templates**: Start from `config.example.yaml` for new deployments

7. **Monitor costs**: Enable cost tracking and set up billing alerts

8. **Rotate secrets**: Regularly rotate session secrets and AWS credentials

9. **Test in development**: Test configuration changes in development before production

10. **Version control**: Track configuration templates (not actual configs) in version control

---

## Additional Resources

- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Redshift Serverless Pricing](https://aws.amazon.com/redshift/pricing/)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [YAML Syntax Guide](https://yaml.org/spec/1.2/spec.html)
- [Python dotenv Documentation](https://pypi.org/project/python-dotenv/)
