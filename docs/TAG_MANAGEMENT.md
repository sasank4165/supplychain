# Tag Management Guide

## Overview

The Supply Chain Agentic AI Application uses a comprehensive tag management system to ensure consistent tagging across all AWS resources. This system provides:

- **Standard Tags**: Automatically applied to all resources
- **Custom Tags**: Environment-specific tags from configuration
- **Tag Validation**: Pre-deployment validation of tag compliance
- **Tag Inheritance**: Nested stack tag propagation
- **Cost Allocation**: Automatic cost tracking tags

## Tag Manager

The `TagManager` class in `config_manager.py` provides centralized tag management functionality.

### Features

1. **Automatic Standard Tags**: Generates required tags for all resources
2. **Custom Tag Support**: Loads custom tags from YAML configuration
3. **Tag Validation**: Validates tags against AWS requirements
4. **Multiple Formats**: Supports CDK, CloudFormation, and dictionary formats
5. **Cost Allocation**: Identifies and manages cost tracking tags

## Standard Tags

All resources automatically receive these standard tags:

| Tag Key | Description | Example |
|---------|-------------|---------|
| `Project` | Project name | `supply-chain-agent` |
| `Environment` | Environment name | `dev`, `staging`, `prod` |
| `ManagedBy` | Management tool | `CDK` |
| `Owner` | Team or person responsible | `platform-team` |
| `CostCenter` | Cost center for billing | `supply-chain` |
| `Region` | AWS region | `us-east-1` |
| `AccountId` | AWS account ID | `123456789012` |

## Custom Tags

Custom tags are defined in environment configuration files (`config/{environment}.yaml`):

```yaml
tags:
  required:
    - Project
    - Environment
    - ManagedBy
    - Owner
    - CostCenter
  validation:
    enforce_required: true
    max_tags: 50
  custom:
    Department: Engineering
    Application: SupplyChainAgent
    Compliance: Internal
```

### Environment-Specific Tags

#### Development
- `Department: Engineering`
- `Application: SupplyChainAgent`
- `Compliance: Internal`

#### Staging
- `Department: Operations`
- `Application: SupplyChainAgent`
- `Purpose: PreProduction`
- `Compliance: Internal`

#### Production
- `Department: Operations`
- `Application: SupplyChainAgent`
- `Compliance: SOC2`
- `DataClassification: Confidential`
- `BackupPolicy: Daily`
- `SecurityZone: Restricted`

## Tag Validation

### Pre-Deployment Validation

Run tag validation before deployment:

```bash
# Windows
py scripts\validate-tags.py --environment dev

# Linux/Mac
python scripts/validate-tags.py --environment dev
```

### Validation Checks

The validation script checks:

1. **Required Tags**: All required tags are present
2. **Tag Count**: Total tags don't exceed AWS limits (50)
3. **Tag Format**: Keys and values meet AWS requirements
4. **Cost Allocation**: Cost tracking tags are present
5. **Reserved Prefixes**: No `aws:` or `AWS:` prefixes

### Strict Mode

Enable strict mode to treat warnings as errors:

```bash
py scripts\validate-tags.py --environment prod --strict
```

## Tag Requirements

### AWS Tag Constraints

- **Key Length**: 1-128 characters
- **Value Length**: 0-256 characters
- **Allowed Characters**: Letters, numbers, spaces, and `+-=._:/@`
- **Reserved Prefixes**: Cannot start with `aws:` or `AWS:`
- **Maximum Tags**: 50 tags per resource

### Required Tags

The following tags are required on all resources:

- `Project`
- `Environment`
- `ManagedBy`
- `Owner`
- `CostCenter`

Additional required tags can be configured per environment.

## Using TagManager in Code

### Python Application Code

```python
from config_manager import ConfigurationManager, TagManager

# Initialize
config = ConfigurationManager(environment='dev')
tag_manager = TagManager(config)

# Get all tags
tags = tag_manager.get_tags()

# Get tags with additional tags
tags = tag_manager.get_tags({'Component': 'Lambda'})

# Get only standard tags
standard_tags = tag_manager.get_standard_tags()

# Get only custom tags
custom_tags = tag_manager.get_custom_tags()

# Validate tags
is_valid, missing = tag_manager.validate_required_tags(tags)

# Get cost allocation tags
cost_tags = tag_manager.get_cost_allocation_tags()
```

### CDK Stack Code

```python
from config import load_cdk_config

# Load configuration
config = load_cdk_config('dev')

# Get tags for a stack
tags = config.get_tags({'Component': 'Network'})

# Apply tags to a stack
for key, value in tags.items():
    cdk.Tags.of(stack).add(key, value)
```

### CDK App (app.py)

The CDK app automatically applies tags to all stacks:

```python
# Helper function applies tags with inheritance
def apply_tags_to_stack(stack, additional_tags=None):
    stack_tags = config.get_tags(additional_tags)
    for key, value in stack_tags.items():
        cdk.Tags.of(stack).add(key, value)

# Apply to stack with component tag
apply_tags_to_stack(network_stack, {'Component': 'Network'})
```

## Tag Inheritance

Tags are inherited by nested resources within CDK stacks:

1. **Stack-Level Tags**: Applied to the stack construct
2. **Resource-Level Tags**: Inherited by all resources in the stack
3. **Additional Tags**: Can be added to specific resources

Example:
```python
# Stack gets base tags + Component tag
apply_tags_to_stack(app_stack, {'Component': 'Application'})

# All Lambda functions in app_stack inherit these tags
# Individual resources can have additional tags
```

## Cost Allocation Tags

The following tags are automatically identified as cost allocation tags:

- `CostCenter`
- `Environment`
- `Project`
- `Owner`
- Any custom tag containing "cost" or "billing"

### Enabling Cost Allocation Tags in AWS

1. Go to AWS Billing Console
2. Navigate to Cost Allocation Tags
3. Activate the following tags:
   - `CostCenter`
   - `Environment`
   - `Project`
   - `Owner`
   - `Component`

## Deployment Integration

### Automated Validation

The enhanced deployment script automatically validates tags:

```powershell
# Windows PowerShell
.\scripts\deploy-with-validation.ps1 -Environment dev

# Skip validation (not recommended)
.\scripts\deploy-with-validation.ps1 -Environment dev -SkipValidation

# Strict mode (warnings as errors)
.\scripts\deploy-with-validation.ps1 -Environment prod -StrictTags
```

### Manual Validation

Validate tags before deployment:

```bash
# Validate dev environment
py scripts\validate-tags.py --environment dev

# Validate prod with strict mode
py scripts\validate-tags.py --environment prod --strict
```

## Best Practices

### 1. Always Use Standard Tags

Ensure all resources have the standard tags by using `TagManager`:

```python
tags = tag_manager.get_tags()
```

### 2. Add Component Tags

Add component-specific tags for better organization:

```python
tags = tag_manager.get_tags({'Component': 'Lambda', 'Function': 'Optimizer'})
```

### 3. Validate Before Deployment

Always run tag validation before deploying:

```bash
py scripts\validate-tags.py --environment prod --strict
```

### 4. Use Descriptive Custom Tags

Add meaningful custom tags in configuration:

```yaml
tags:
  custom:
    Department: Engineering
    Application: SupplyChainAgent
    DataClassification: Confidential
    BackupPolicy: Daily
```

### 5. Keep Tags Consistent

Use the same tag keys across environments with different values:

```yaml
# dev.yaml
tags:
  custom:
    Compliance: Internal

# prod.yaml
tags:
  custom:
    Compliance: SOC2
```

## Troubleshooting

### Tag Validation Fails

**Problem**: Tag validation fails with missing required tags

**Solution**: Check configuration file has all required tags defined:

```yaml
tags:
  required:
    - Project
    - Environment
    - ManagedBy
    - Owner
    - CostCenter
```

### Tag Count Exceeds Limit

**Problem**: Tag count exceeds AWS limit of 50

**Solution**: Review and remove unnecessary custom tags:

```bash
py scripts\validate-tags.py --environment prod
```

### Invalid Tag Characters

**Problem**: Tag validation fails with invalid characters

**Solution**: Ensure tags only use allowed characters: `a-zA-Z0-9 +-=._:/@`

### Reserved Prefix Error

**Problem**: Tag key starts with `aws:` or `AWS:`

**Solution**: Remove reserved prefix from tag key

## Examples

### Example 1: Basic Tag Usage

```python
from config_manager import ConfigurationManager, TagManager

config = ConfigurationManager(environment='dev')
tag_manager = TagManager(config)

# Get all tags
tags = tag_manager.get_tags()
print(f"Total tags: {len(tags)}")

# Validate tags
is_valid, missing = tag_manager.validate_required_tags(tags)
if not is_valid:
    print(f"Missing tags: {missing}")
```

### Example 2: CDK Resource Tagging

```python
from aws_cdk import aws_lambda as lambda_
from config import load_cdk_config

config = load_cdk_config('prod')

# Create Lambda function
function = lambda_.Function(
    self, "MyFunction",
    # ... function config ...
)

# Apply tags
tags = config.get_tags({'Component': 'Lambda', 'Function': 'MyFunction'})
for key, value in tags.items():
    cdk.Tags.of(function).add(key, value)
```

### Example 3: Custom Validation

```python
from config_manager import TagManager

tag_manager = TagManager(config)

# Custom tags to validate
my_tags = {
    'Project': 'my-project',
    'Environment': 'dev',
    'CustomTag': 'value'
}

# Validate
is_valid, missing = tag_manager.validate_required_tags(my_tags)
if not is_valid:
    print(f"Validation failed. Missing: {missing}")
else:
    print("All required tags present")
```

## Reference

### TagManager Methods

| Method | Description |
|--------|-------------|
| `get_tags(additional_tags)` | Get all tags with optional additional tags |
| `get_standard_tags()` | Get only standard tags |
| `get_custom_tags()` | Get only custom tags |
| `validate_required_tags(tags)` | Validate required tags are present |
| `format_tags_for_cloudformation()` | Format tags for CloudFormation |
| `get_cost_allocation_tags()` | Get cost allocation tags |

### Configuration Schema

```yaml
tags:
  required:              # List of required tag keys
    - Project
    - Environment
  validation:            # Validation settings
    enforce_required: true
    max_tags: 50
  custom:                # Custom tags (key-value pairs)
    Department: Engineering
    Application: MyApp
```

## See Also

- [Configuration Guide](../cdk/CONFIGURATION_GUIDE.md)
- [Deployment Guide](../COMPLETE_DEPLOYMENT_GUIDE.md)
- [AWS Tagging Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
