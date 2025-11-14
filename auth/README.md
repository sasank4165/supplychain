# Authentication & Authorization Module

## Overview

This module provides comprehensive authentication and role-based access control (RBAC) for the Supply Chain Agentic AI application.

## Components

### 1. AuthManager (`auth_manager.py`)
Core authentication and authorization manager that handles:
- User sign in/sign out
- Token management (access, ID, refresh tokens)
- Password management (change, forgot, reset)
- Token verification
- Role-based access control
- Table-level permissions
- Agent-level permissions

### 2. Login UI (`login_ui.py`)
Streamlit UI components for:
- Login page
- Password reset flow
- User profile display
- Change password dialog
- Session management

### 3. Lambda Authorizer (`../lambda_functions/authorizer.py`)
API Gateway Lambda authorizer for:
- JWT token validation
- Cognito public key verification
- IAM policy generation
- Request context injection

## Quick Start

### Initialize AuthManager

```python
from auth.auth_manager import AuthManager

auth = AuthManager(
    user_pool_id="us-east-1_xxxxx",
    client_id="xxxxx",
    region="us-east-1"
)
```

### Sign In

```python
result = auth.sign_in("username", "password")

if result['success']:
    access_token = result['access_token']
    persona = result['persona']
    groups = result['groups']
```

### Verify Token

```python
verification = auth.verify_token(access_token)

if verification['valid']:
    username = verification['username']
    groups = verification['groups']
```

### Check Access

```python
# Check table access
can_access = auth.check_table_access(groups, "warehouse_product")

# Check agent access
can_use = auth.check_agent_access(groups, "inventory_optimizer")

# Get all accessible resources
tables = auth.get_accessible_tables(groups)
agents = auth.get_accessible_agents(groups)
```

## Decorators

### @require_auth

Require authentication for a function:

```python
from auth import require_auth

@require_auth
def protected_function(token=None, auth_manager=None, user_info=None):
    username = user_info['username']
    # Function logic
```

### @require_persona

Require specific persona:

```python
from auth import require_persona

@require_persona(["warehouse_manager"])
def warehouse_only_function(user_info=None):
    # Only warehouse managers can call this
```

### @require_table_access

Require access to specific table:

```python
from auth import require_table_access

@require_table_access("purchase_order_header")
def query_purchase_orders(user_info=None, auth_manager=None):
    # Only users with PO access can call this
```

## Streamlit Integration

### Login Page

```python
from auth.login_ui import render_login_page, check_authentication

if not check_authentication():
    render_login_page(auth_manager)
    st.stop()
```

### User Profile

```python
from auth.login_ui import render_user_profile

render_user_profile(auth_manager)
```

### Get Current User

```python
from auth.login_ui import get_current_user

user = get_current_user()
if user:
    username = user['username']
    persona = user['persona']
```

## Testing

### Run Authentication Tests

```bash
# Interactive test
python auth/test_auth.py

# Scenario tests
python auth/test_auth.py --scenarios
```

### Manual Testing

```python
# Test sign in
result = auth.sign_in("warehouse_manager1", "password")

# Test table access
groups = ["warehouse_managers"]
assert auth.check_table_access(groups, "warehouse_product") == True
assert auth.check_table_access(groups, "purchase_order_header") == False

# Test agent access
assert auth.check_agent_access(groups, "inventory_optimizer") == True
assert auth.check_agent_access(groups, "supplier_analyzer") == False
```

## Configuration

### Environment Variables

```bash
export USER_POOL_ID="us-east-1_xxxxx"
export USER_POOL_CLIENT_ID="xxxxx"
export AWS_REGION="us-east-1"
```

### Role Mappings

Edit `auth_manager.py` to customize:

```python
self.persona_groups = {
    "warehouse_manager": "warehouse_managers",
    "field_engineer": "field_engineers",
    "procurement_specialist": "procurement_specialists"
}

self.role_table_access = {
    "warehouse_managers": ["product", "warehouse_product", ...],
    # ...
}

self.role_agent_access = {
    "warehouse_managers": ["sql_agent", "inventory_optimizer"],
    # ...
}
```

## Security Best Practices

1. **Token Storage**
   - Store tokens in secure session state
   - Never log tokens
   - Clear tokens on logout

2. **Token Validation**
   - Verify signature using Cognito public keys
   - Check expiration
   - Validate audience and issuer

3. **Password Management**
   - Enforce strong password policies
   - Use temporary passwords for new users
   - Implement password rotation

4. **Access Control**
   - Principle of least privilege
   - Regular access reviews
   - Audit all access attempts

5. **Session Management**
   - Implement session timeout
   - Secure session storage
   - Logout on inactivity

## Troubleshooting

### "Invalid token" Error
- Check token format (should be JWT)
- Verify token hasn't expired
- Ensure Cognito configuration is correct

### "Access denied" Error
- Verify user is in correct Cognito group
- Check persona matches group membership
- Verify resource is in allowed list

### "User not found" Error
- Verify user exists in Cognito User Pool
- Check username spelling
- Ensure user is confirmed

## API Reference

See [RBAC_GUIDE.md](RBAC_GUIDE.md) for complete API reference and access control matrix.

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review Cognito User Pool configuration
3. Verify IAM permissions
4. Test with AWS CLI
