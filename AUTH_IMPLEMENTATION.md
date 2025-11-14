# Authentication & Authorization Implementation Guide

## Complete RBAC Implementation

This document describes the complete authentication and role-based access control (RBAC) implementation for the Supply Chain Agentic AI application.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Login                               │
│                    (Streamlit UI / API)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Cognito User Pool                         │
│              (Authentication & Group Management)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      JWT Token Issuance                          │
│            (Access Token, ID Token, Refresh Token)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Lambda Authorizer (API)                        │
│                   or AuthManager (Streamlit)                     │
│                    (Token Validation)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator                                │
│              (Persona & Group Validation)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SQL Agent                                   │
│              (Table-Level Access Control)                        │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Components

### 1. Cognito User Pool (CDK)

**File**: `cdk/supply_chain_stack.py`

```python
user_pool = cognito.UserPool(
    self, "UserPool",
    user_pool_name="supply-chain-agent-users",
    password_policy=cognito.PasswordPolicy(
        min_length=12,
        require_lowercase=True,
        require_uppercase=True,
        require_digits=True,
        require_symbols=True
    ),
    mfa=cognito.Mfa.OPTIONAL,
    advanced_security_mode=cognito.AdvancedSecurityMode.ENFORCED
)

# User groups for each persona
cognito.CfnUserPoolGroup(
    self, "WarehouseManagerGroup",
    user_pool_id=user_pool.user_pool_id,
    group_name="warehouse_managers"
)
```

**Features**:
- Strong password policies
- MFA support
- Advanced security mode
- Group-based access control

### 2. AuthManager (Python)

**File**: `auth/auth_manager.py`

**Key Methods**:
- `sign_in(username, password)` - Authenticate user
- `sign_out(access_token)` - Sign out user
- `verify_token(token)` - Validate JWT token
- `check_table_access(groups, table)` - Verify table access
- `check_agent_access(groups, agent)` - Verify agent access

**Access Control Matrices**:

```python
role_table_access = {
    "warehouse_managers": [
        "product", "warehouse_product",
        "sales_order_header", "sales_order_line"
    ],
    "field_engineers": [
        "product", "warehouse_product",
        "sales_order_header", "sales_order_line"
    ],
    "procurement_specialists": [
        "product", "warehouse_product",
        "purchase_order_header", "purchase_order_line"
    ]
}

role_agent_access = {
    "warehouse_managers": ["sql_agent", "inventory_optimizer"],
    "field_engineers": ["sql_agent", "logistics_optimizer"],
    "procurement_specialists": ["sql_agent", "supplier_analyzer"]
}
```

### 3. Login UI (Streamlit)

**File**: `auth/login_ui.py`

**Components**:
- `render_login_page()` - Login form
- `render_user_profile()` - User profile sidebar
- `render_change_password_dialog()` - Password change
- `check_authentication()` - Check if authenticated
- `get_current_user()` - Get current user info

**Session State**:
```python
st.session_state.authenticated = True
st.session_state.access_token = "..."
st.session_state.username = "user1"
st.session_state.groups = ["warehouse_managers"]
st.session_state.persona = "warehouse_manager"
```

### 4. Lambda Authorizer (API Gateway)

**File**: `lambda_functions/authorizer.py`

**Flow**:
1. Extract JWT token from Authorization header
2. Verify token signature using Cognito public keys
3. Validate expiration, audience, issuer
4. Extract user info (username, groups, persona)
5. Generate IAM policy (Allow/Deny)
6. Inject context into request

**Response**:
```python
{
    "principalId": "username",
    "policyDocument": {
        "Statement": [{
            "Action": "execute-api:Invoke",
            "Effect": "Allow",
            "Resource": "arn:aws:execute-api:..."
        }]
    },
    "context": {
        "username": "user1",
        "groups": '["warehouse_managers"]',
        "persona": "warehouse_manager"
    }
}
```

### 5. Orchestrator RBAC

**File**: `orchestrator.py`

**Validation**:
```python
def process_query(self, query, persona, session_id, context=None):
    # Verify user's persona matches requested persona
    if user_persona != persona:
        return {"success": False, "error": "Access denied", "status": 403}
    
    # Verify group membership
    expected_group = self._get_group_for_persona(persona)
    if expected_group not in user_groups:
        return {"success": False, "error": "Access denied", "status": 403}
```

### 6. SQL Agent Table Access Control

**File**: `agents/sql_agent.py`

**Validation**:
```python
def execute_athena_query(self, sql_query, context=None):
    # Extract tables from SQL
    tables_in_query = self._extract_tables_from_sql(sql_query)
    
    # Get allowed tables for persona
    allowed_tables = PERSONA_TABLE_ACCESS.get(persona_enum, [])
    
    # Check each table
    for table in tables_in_query:
        if table not in allowed_tables:
            return {
                "error": f"Access denied to table: {table}",
                "status": 403
            }
```

## User Management

### Creating Users

**Script**: `scripts/setup-users.sh`

```bash
#!/bin/bash
# Create user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username warehouse_manager1 \
  --user-attributes Name=email,Value=wm1@example.com \
  --temporary-password "TempPass123!"

# Add to group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username warehouse_manager1 \
  --group-name warehouse_managers
```

### User Groups

| Group | Persona | Tables | Agents |
|-------|---------|--------|--------|
| warehouse_managers | warehouse_manager | product, warehouse_product, sales_order_* | sql_agent, inventory_optimizer |
| field_engineers | field_engineer | product, warehouse_product, sales_order_* | sql_agent, logistics_optimizer |
| procurement_specialists | procurement_specialist | product, warehouse_product, purchase_order_* | sql_agent, supplier_analyzer |

## Access Control Flow

### Streamlit Application

```
1. User enters credentials
   ↓
2. AuthManager.sign_in() → Cognito
   ↓
3. Cognito returns JWT tokens
   ↓
4. Store tokens in session_state
   ↓
5. Extract groups from token
   ↓
6. Determine persona from groups
   ↓
7. User query → Orchestrator
   ↓
8. Orchestrator validates persona & groups
   ↓
9. SQL Agent validates table access
   ↓
10. Execute query or return 403
```

### API Gateway

```
1. Client sends request with Authorization header
   ↓
2. API Gateway invokes Lambda Authorizer
   ↓
3. Authorizer validates JWT token
   ↓
4. Authorizer returns IAM policy + context
   ↓
5. API Gateway allows/denies request
   ↓
6. Lambda function receives context
   ↓
7. Lambda validates access
   ↓
8. Execute or return 403
```

## Testing

### Test Authentication

```bash
python auth/test_auth.py
```

**Tests**:
1. Sign in with credentials
2. Verify token
3. Check table access
4. Check agent access
5. Get accessible resources
6. Sign out

### Test RBAC Scenarios

```bash
python auth/test_auth.py --scenarios
```

**Scenarios**:
1. Warehouse Manager access patterns
2. Field Engineer access patterns
3. Procurement Specialist access patterns

### Manual Testing

```python
from auth.auth_manager import AuthManager

auth = AuthManager(user_pool_id, client_id)

# Test sign in
result = auth.sign_in("warehouse_manager1", "password")
assert result['success'] == True
assert result['persona'] == "warehouse_manager"

# Test table access
groups = result['groups']
assert auth.check_table_access(groups, "warehouse_product") == True
assert auth.check_table_access(groups, "purchase_order_header") == False

# Test agent access
assert auth.check_agent_access(groups, "inventory_optimizer") == True
assert auth.check_agent_access(groups, "supplier_analyzer") == False
```

## Security Features

### Authentication
- ✅ Cognito-based authentication
- ✅ JWT token validation
- ✅ Token expiration (1 hour)
- ✅ Refresh token rotation (30 days)
- ✅ MFA support (optional)
- ✅ Password policies (12+ chars, complexity)

### Authorization
- ✅ Role-based access control (RBAC)
- ✅ Group-based permissions
- ✅ Table-level access control
- ✅ Agent-level access control
- ✅ Dynamic SQL validation
- ✅ Persona validation

### Session Management
- ✅ Secure session storage
- ✅ Session timeout
- ✅ Logout functionality
- ✅ Token refresh
- ✅ Cross-tab synchronization

### Audit & Compliance
- ✅ CloudWatch logging
- ✅ CloudTrail audit logs
- ✅ DynamoDB session tracking
- ✅ Access attempt logging
- ✅ Failed login monitoring

## Deployment

### 1. Deploy Infrastructure

```bash
cd cdk
cdk deploy SupplyChainApp-prod
```

### 2. Create User Groups

```bash
# Groups are created automatically by CDK
# Verify:
aws cognito-idp list-groups --user-pool-id $USER_POOL_ID
```

### 3. Create Users

```bash
./scripts/setup-users.sh $USER_POOL_ID
```

### 4. Test Authentication

```bash
export USER_POOL_ID="us-east-1_xxxxx"
export USER_POOL_CLIENT_ID="xxxxx"
python auth/test_auth.py
```

### 5. Run Application

```bash
streamlit run app.py
```

## Troubleshooting

### Issue: "Access denied" errors

**Solution**:
1. Verify user is in correct Cognito group
2. Check persona matches group membership
3. Verify table is in allowed list for persona

```bash
# Check user groups
aws cognito-idp admin-list-groups-for-user \
  --user-pool-id $USER_POOL_ID \
  --username warehouse_manager1
```

### Issue: "Token expired" errors

**Solution**:
1. Use refresh token to get new access token
2. Re-authenticate if refresh token expired

```python
result = auth.refresh_token(refresh_token)
new_access_token = result['access_token']
```

### Issue: "Invalid token" errors

**Solution**:
1. Verify token format (Bearer <token>)
2. Check token hasn't been tampered with
3. Verify Cognito User Pool configuration

## Best Practices

1. **Principle of Least Privilege**
   - Grant minimum necessary permissions
   - Review access regularly
   - Remove unused permissions

2. **Token Management**
   - Store tokens securely
   - Never log tokens
   - Rotate tokens regularly
   - Use HTTPS only

3. **Password Security**
   - Enforce strong passwords
   - Enable MFA for sensitive roles
   - Regular password rotation
   - Monitor failed login attempts

4. **Audit & Monitoring**
   - Log all access attempts
   - Monitor for suspicious activity
   - Regular security reviews
   - Compliance reporting

## References

- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [auth/RBAC_GUIDE.md](auth/RBAC_GUIDE.md) - Detailed RBAC guide
- [auth/README.md](auth/README.md) - Auth module documentation
