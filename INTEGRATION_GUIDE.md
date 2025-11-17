# Configuration System Integration Guide

This guide explains how to integrate the new configuration management system with the existing Supply Chain Agentic AI Application codebase.

## Overview

The new configuration system replaces hardcoded values in `config.py` with a flexible, environment-aware configuration management system.

## Migration Steps

### Step 1: Update Imports

**Old Code (config.py):**
```python
from config import (
    AWS_REGION,
    BEDROCK_MODEL_ID,
    ATHENA_DATABASE,
    DYNAMODB_SESSION_TABLE,
    LAMBDA_SQL_EXECUTOR
)
```

**New Code:**
```python
from config_manager import ConfigurationManager, ResourceNamer

# Initialize once at application startup
config = ConfigurationManager()
namer = ResourceNamer(config)

# Access values
AWS_REGION = config.get('environment.region')
BEDROCK_MODEL_ID = config.get('agents.default_model')
ATHENA_DATABASE = config.get('data.athena_database')
DYNAMODB_SESSION_TABLE = namer.dynamodb_table('sessions')
LAMBDA_SQL_EXECUTOR = namer.lambda_function('sql-executor')
```

### Step 2: Update Application Code

#### app.py
```python
# OLD
from config import AWS_REGION, BEDROCK_MODEL_ID

# NEW
from config_manager import ConfigurationManager

config = ConfigurationManager()
AWS_REGION = config.get('environment.region')
BEDROCK_MODEL_ID = config.get('agents.default_model')
```

#### orchestrator.py
```python
# OLD
from config import (
    BEDROCK_MODEL_ID,
    DYNAMODB_SESSION_TABLE,
    LAMBDA_SQL_EXECUTOR
)

# NEW
from config_manager import ConfigurationManager, ResourceNamer

config = ConfigurationManager()
namer = ResourceNamer(config)

BEDROCK_MODEL_ID = config.get('agents.default_model')
DYNAMODB_SESSION_TABLE = namer.dynamodb_table('sessions')
LAMBDA_SQL_EXECUTOR = namer.lambda_function('sql-executor')
```

#### Agent Classes
```python
# OLD
from config import BEDROCK_MODEL_ID, AWS_REGION

class BaseAgent:
    def __init__(self):
        self.model_id = BEDROCK_MODEL_ID
        self.region = AWS_REGION

# NEW
from config_manager import ConfigurationManager

class BaseAgent:
    def __init__(self, config: ConfigurationManager = None):
        self.config = config or ConfigurationManager()
        self.model_id = self.config.get('agents.default_model')
        self.region = self.config.get('environment.region')
```

### Step 3: Update CDK Code

#### cdk/config.py
```python
# OLD
AWS_REGION = "us-east-1"
PROJECT_NAME = "supply-chain-agent"

# NEW
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigurationManager, ResourceNamer
import os

# Load environment from environment variable
environment = os.getenv('ENVIRONMENT', 'dev')
config = ConfigurationManager(environment=environment)
namer = ResourceNamer(config)

# Export values for CDK stacks
AWS_REGION = config.get('environment.region')
AWS_ACCOUNT = config.get('environment.account_id')
PROJECT_NAME = config.get('project.name')
PROJECT_PREFIX = config.get('project.prefix')

# Feature flags
VPC_ENABLED = config.get('features.vpc_enabled')
WAF_ENABLED = config.get('features.waf_enabled')
MULTI_AZ = config.get('features.multi_az')
XRAY_TRACING = config.get('features.xray_tracing')

# Resource configuration
LAMBDA_MEMORY = config.get('resources.lambda.memory_mb')
LAMBDA_TIMEOUT = config.get('resources.lambda.timeout_seconds')
LAMBDA_ARCHITECTURE = config.get('resources.lambda.architecture')
LOG_RETENTION_DAYS = config.get('resources.logs.retention_days')

# Tags
RESOURCE_TAGS = config.get_tags()
```

#### cdk/supply_chain_stack.py
```python
# OLD
bucket = s3.Bucket(self, "DataBucket",
    bucket_name="supply-chain-data-bucket"
)

# NEW
from config_manager import ResourceNamer

bucket = s3.Bucket(self, "DataBucket",
    bucket_name=namer.s3_bucket('data'),
    removal_policy=RemovalPolicy.RETAIN if config.get('environment.name') == 'prod' else RemovalPolicy.DESTROY
)

# Apply tags
for key, value in config.get_tags().items():
    Tags.of(bucket).add(key, value)
```

### Step 4: Update Lambda Functions

#### lambda_functions/inventory_optimizer.py
```python
# OLD
import os
DYNAMODB_TABLE = "supply-chain-agent-sessions"
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"

# NEW
import os
import sys
from pathlib import Path

# Add parent directory for imports (if needed)
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigurationManager, ResourceNamer

# Initialize configuration
config = ConfigurationManager()
namer = ResourceNamer(config)

# Get values
DYNAMODB_TABLE = namer.dynamodb_table('sessions')
MODEL_ID = config.get('agents.inventory_optimizer.model')
TIMEOUT = config.get('agents.inventory_optimizer.timeout_seconds', 60)
```

### Step 5: Update Environment Variables

Set the environment before running:

```bash
# Windows
set ENVIRONMENT=dev

# Linux/Mac
export ENVIRONMENT=dev
```

Or use environment-specific overrides:

```bash
# Override specific values
export SC_AGENT_ENVIRONMENT_REGION=us-west-2
export SC_AGENT_RESOURCES_LAMBDA_MEMORY_MB=1024
```

### Step 6: Update Deployment Scripts

#### deploy.sh
```bash
#!/bin/bash

# OLD
cdk deploy --all

# NEW
# Set environment
export ENVIRONMENT=${1:-dev}

# Validate configuration
python scripts/validate-config.py --environment $ENVIRONMENT --check-aws

if [ $? -ne 0 ]; then
    echo "Configuration validation failed. Aborting deployment."
    exit 1
fi

# Deploy with environment
cdk deploy --all --context environment=$ENVIRONMENT
```

## Backward Compatibility

To maintain backward compatibility during migration, you can keep the old `config.py` and have it use the new system:

```python
# config.py (backward compatible wrapper)
from config_manager import ConfigurationManager, ResourceNamer
import os

# Initialize configuration
_config = ConfigurationManager(environment=os.getenv('ENVIRONMENT', 'dev'))
_namer = ResourceNamer(_config)

# Export old variable names
AWS_REGION = _config.get('environment.region')
BEDROCK_MODEL_ID = _config.get('agents.default_model')
ATHENA_DATABASE = _config.get('data.athena_database')
ATHENA_CATALOG = _config.get('data.glue_catalog')
ATHENA_OUTPUT_LOCATION = os.getenv("ATHENA_OUTPUT_LOCATION", 
    f"s3://{_namer.s3_bucket('athena-results')}/")

# DynamoDB Tables
DYNAMODB_SESSION_TABLE = _namer.dynamodb_table('sessions')
DYNAMODB_MEMORY_TABLE = _namer.dynamodb_table('memory')

# Lambda Functions
LAMBDA_SQL_EXECUTOR = _namer.lambda_function('sql-executor')
LAMBDA_INVENTORY_OPTIMIZER = _namer.lambda_function('inventory-optimizer')
LAMBDA_LOGISTICS_OPTIMIZER = _namer.lambda_function('logistics-optimizer')
LAMBDA_SUPPLIER_ANALYZER = _namer.lambda_function('supplier-analyzer')

# Keep existing schema and persona definitions
from enum import Enum

class Persona(Enum):
    WAREHOUSE_MANAGER = "warehouse_manager"
    FIELD_ENGINEER = "field_engineer"
    PROCUREMENT_SPECIALIST = "procurement_specialist"

SCHEMA_TABLES = {
    # ... keep existing schema definitions
}

PERSONA_TABLE_ACCESS = {
    # ... keep existing persona access definitions
}
```

This allows existing code to continue working while you gradually migrate to the new system.

## Testing the Integration

### 1. Unit Tests
```bash
python tests/test_config_manager.py
```

### 2. Configuration Validation
```bash
python scripts/validate-config.py --environment dev --check-aws
```

### 3. Integration Test
```python
# test_integration.py
from config_manager import ConfigurationManager, ResourceNamer

def test_integration():
    config = ConfigurationManager(environment='dev')
    namer = ResourceNamer(config)
    
    # Test that all required values are accessible
    assert config.get('environment.region') is not None
    assert config.get('agents.default_model') is not None
    
    # Test resource naming
    bucket = namer.s3_bucket('data')
    assert 'data' in bucket
    assert len(bucket) <= 63
    
    print("✅ Integration test passed")

if __name__ == '__main__':
    test_integration()
```

### 4. End-to-End Test
```bash
# Set environment
export ENVIRONMENT=dev

# Run application
python app.py
```

## Common Issues and Solutions

### Issue 1: Import Error
**Error:** `ModuleNotFoundError: No module named 'config_manager'`

**Solution:** Ensure `config_manager.py` is in the project root or add to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue 2: Configuration Not Found
**Error:** `ConfigurationError: Configuration file not found`

**Solution:** Ensure you're running from project root and config files exist:
```bash
ls config/*.yaml
```

### Issue 3: AWS Credentials
**Error:** `Failed to auto-detect AWS account ID`

**Solution:** Configure AWS credentials:
```bash
aws configure
```

Or set account_id explicitly in config file.

### Issue 4: Schema Validation
**Error:** `Configuration validation failed`

**Solution:** Install required dependencies:
```bash
pip install pyyaml jsonschema
```

## Rollback Plan

If you need to rollback to the old system:

1. Keep the old `config.py` file
2. Revert imports in application code
3. Remove `config_manager.py` from imports
4. Continue using hardcoded values

The old and new systems can coexist during migration.

## Best Practices

1. **Validate Before Deploy**: Always run validation script before deployment
2. **Use Environment Variables**: Override configs without modifying files
3. **Test in Dev First**: Validate changes in dev before prod
4. **Document Changes**: Update documentation when adding new config parameters
5. **Version Control**: Commit config files but never commit secrets
6. **Use Secrets Manager**: Store sensitive values in AWS Secrets Manager, not config files

## Next Steps

After integrating the configuration system:

1. ✅ Task 2: Implement secrets and parameter management
2. ✅ Task 3: Refactor CDK infrastructure for parameterization
3. ✅ Task 11: Create deployment automation scripts
4. ✅ Task 13: Update application code for environment variables

## Support

For questions or issues:
- Review [Configuration README](config/README.md)
- Check [Quick Start Guide](CONFIGURATION_QUICKSTART.md)
- Run validation script for detailed errors
- Review usage examples in `examples/config_usage_example.py`
