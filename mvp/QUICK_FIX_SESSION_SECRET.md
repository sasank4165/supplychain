# Quick Fix: SESSION_SECRET Error

## Problem

You're seeing this error:
```
Failed to initialize application: Error loading configuration: 
Environment variable 'SESSION_SECRET' is not set and no default provided
```

## Solution

The latest version of the config manager now **auto-generates** the session secret! You just need to update your config manager.

### Option 1: Use Updated Config Manager (Recommended)

The `utils/config_manager.py` has been updated to auto-generate session secrets. Just restart your Streamlit app:

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

The session secret will be automatically generated on startup.

### Option 2: Set Environment Variable

If you prefer to set it explicitly:

```bash
export SESSION_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Option 3: Hardcode in config.yaml (Not Recommended)

Edit `config.yaml` and replace:
```yaml
session_secret: ${SESSION_SECRET}
```

With:
```yaml
session_secret: "your-generated-secret-here"
```

Generate a secret with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## What Changed

The config manager now automatically:
1. **Auto-detects AWS Account ID** - No need to hardcode it
2. **Auto-generates SESSION_SECRET** - Cryptographically secure random key

Both `${AWS_ACCOUNT_ID}` and `${SESSION_SECRET}` in config.yaml will work automatically!

## Verify It Works

Test your configuration:
```bash
python scripts/test_config.py
```

Expected output:
```
✓ AWS Account ID detected: 193871648423
✓ Session secret generated: a1b2c3d4e5f6... (truncated)
✓ All tests passed!
```

## Why This Matters

- **Security**: Session secrets are cryptographically random (64 hex characters)
- **Convenience**: No manual generation needed
- **Portability**: Same config works everywhere
- **No Hardcoding**: Sensitive values never committed to git

## Still Having Issues?

1. Make sure you have the latest `utils/config_manager.py`
2. Verify `config.yaml` exists (copy from `config.example.yaml`)
3. Check that `config.yaml` has `session_secret: ${SESSION_SECRET}`
4. Run the test script: `python scripts/test_config.py`

The session secret is generated fresh each time the app starts, which is perfect for development. For production, you'd want to set it explicitly so sessions persist across restarts.
