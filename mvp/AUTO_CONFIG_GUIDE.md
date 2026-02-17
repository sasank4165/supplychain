# Automatic Configuration Guide

## Overview

The Supply Chain MVP now supports **automatic AWS account ID detection**, eliminating the need to hardcode your account ID in configuration files.

## How It Works

### 1. Environment Variable Substitution

The configuration system supports environment variable substitution using the `${VAR_NAME}` syntax:

```yaml
aws:
  glue:
    catalog_id: ${AWS_ACCOUNT_ID}
```

### 2. Automatic Detection

When `${AWS_ACCOUNT_ID}` is encountered, the system:
1. First checks if the `AWS_ACCOUNT_ID` environment variable is set
2. If not set, automatically calls AWS STS `get_caller_identity()` to detect your account ID
3. Uses the detected value in your configuration

### 3. No Hardcoding Required

You can use the default `config.example.yaml` as-is:

```yaml
aws:
  glue:
    catalog_id: ${AWS_ACCOUNT_ID}  # Auto-detected!
```

## Usage

### Quick Setup (Recommended)

Run the automated setup script:

```bash
python scripts/quick_setup.py
```

This will:
- Create `config.yaml` from `config.example.yaml`
- Verify AWS connectivity
- Test account ID detection
- Create necessary directories

### Manual Setup

1. Copy the example config:
```bash
cp config.example.yaml config.yaml
```

2. Leave `${AWS_ACCOUNT_ID}` as-is - it will be auto-detected!

3. Test the configuration:
```bash
python scripts/test_config.py
```

## Environment Variable Options

You can also set the account ID explicitly if needed:

### Option 1: Environment Variable

```bash
export AWS_ACCOUNT_ID=193871648423
export SESSION_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
```

### Option 2: Hardcode (Not Recommended)

```yaml
aws:
  glue:
    catalog_id: "193871648423"
auth:
  session_secret: "your-secret-key-here"
```

## Supported Variables

The configuration system supports these special variables:

| Variable | Description | Auto-Detection |
|----------|-------------|----------------|
| `${AWS_ACCOUNT_ID}` | AWS Account ID | ✓ Yes (via STS) |
| `${SESSION_SECRET}` | Session secret key | ✓ Yes (auto-generated) |
| `${AWS_REGION}` | AWS Region | ✗ No (must be set) |

## Default Values

You can provide default values using the `:` syntax:

```yaml
aws:
  region: ${AWS_REGION:us-east-1}  # Defaults to us-east-1
  glue:
    catalog_id: ${AWS_ACCOUNT_ID}  # Auto-detected, no default needed
```

## Testing

### Test Configuration Loading

```bash
python scripts/test_config.py
```

Expected output:
```
✓ Configuration loaded successfully
✓ AWS Account ID detected: 193871648423
✓ Account ID format is valid
```

### Test AWS Connectivity

```bash
python scripts/quick_setup.py
```

This verifies:
- AWS credentials are configured
- STS access (for account ID detection)
- Bedrock access
- Redshift Data API access
- Glue access

## Troubleshooting

### Account ID Not Detected

**Problem**: Configuration fails with "AWS_ACCOUNT_ID not set"

**Solutions**:
1. Verify AWS credentials are configured:
   ```bash
   aws sts get-caller-identity
   ```

2. Check IAM permissions - need `sts:GetCallerIdentity`

3. Set explicitly as environment variable:
   ```bash
   export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
   ```

### Permission Denied

**Problem**: "AccessDenied" when detecting account ID

**Solution**: Ensure your IAM role has the `sts:GetCallerIdentity` permission (this is usually granted by default)

### Wrong Account ID

**Problem**: Detected account ID is incorrect

**Solution**: Check which AWS credentials are being used:
```bash
aws sts get-caller-identity
```

## Implementation Details

The auto-detection is implemented in `utils/config_manager.py`:

```python
def _get_aws_account_id(self) -> Optional[str]:
    """Auto-detect AWS account ID using boto3."""
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        return identity['Account']
    except Exception:
        return None

def _generate_session_secret(self) -> str:
    """Generate a secure random session secret."""
    import secrets
    return secrets.token_hex(32)
```

## Benefits

1. **No Hardcoding**: Account ID and session secrets are never hardcoded in config files
2. **Portable**: Same config works across different AWS accounts
3. **Secure**: No sensitive data in version control, session secrets are cryptographically random
4. **Automatic**: Works out of the box on SageMaker and EC2
5. **Flexible**: Can still override with environment variables if needed

## Best Practices

1. **Use Auto-Detection**: Leave `${AWS_ACCOUNT_ID}` in config.yaml
2. **Don't Commit Secrets**: Never commit actual account IDs to git
3. **Test Configuration**: Run `test_config.py` after setup
4. **Document Overrides**: If you set environment variables, document them

## Related Files

- `mvp/utils/config_manager.py` - Configuration manager with auto-detection
- `mvp/config.example.yaml` - Example configuration with `${AWS_ACCOUNT_ID}`
- `mvp/scripts/quick_setup.py` - Automated setup script
- `mvp/scripts/test_config.py` - Configuration testing script
- `mvp/SAGEMAKER_QUICKSTART.md` - Quick start guide

## Summary

The automatic configuration detection makes setup easier and more secure. You no longer need to:
- Look up your account ID
- Generate session secrets manually
- Hardcode sensitive values in configuration files
- Worry about committing sensitive data to git

Just use `${AWS_ACCOUNT_ID}` and `${SESSION_SECRET}` in your config, and they work automatically!
