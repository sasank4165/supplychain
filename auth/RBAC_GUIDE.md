# Role-Based Access Control (RBAC) Guide

## Overview

This application implements comprehensive role-based access control (RBAC) to ensure users can only access data and features appropriate for their role.

## Authentication Flow

```
User Login → Cognito Authentication → JWT Token → Token Validation → Access Control
```

### 1. User Login
- Users authenticate via Cognito User Pool
- Username/password authentication
- MFA support (optional)
- Password policies enforced

### 2. Token Issuance
- Cognito issues JWT tokens:
  - **ID Token**: Contains user identity and attributes
  - **Access Token**: Used for API authorization
  - **Refresh Token**: Used to obtain new tokens

### 3. Token Validation
- Tokens validated on each request
- Signature verification using Cognito public keys
- Expiration check
- Audience and issuer validation

## Role Hierarchy

### Personas (Roles)

1. **Warehouse Manager** (`warehouse_managers` group)
   - Focus: Inventory management and optimization
   - Access: Warehouse and sales data

2. **Field Engineer** (`field_engineers` group)
   - Focus: Logistics and order fulfillment
   - Access: Warehouse and sales data

3. **Procurement Specialist** (`procurement_specialists` group)
   - Focus: Supplier management and cost optimization
   - Access: Purchase order and supplier data

## Access Control Matrix

### Table-Level Access

| Table | Warehouse Manager | Field Engineer | Procurement Specialist |
|-------|------------------|----------------|----------------------|
| product | ✅ | ✅ | ✅ |
| warehouse_product | ✅ | ✅ | ✅ |
| sales_order_header | ✅ | ✅ | ❌ |
| sales_order_line | ✅ | ✅ | ❌ |
| purchase_order_header | ❌ | ❌ | ✅ |
| purchase_order_line | ❌ | ❌ | ✅ |

### Agent-Level Access

| Agent | Warehouse Manager | Field Engineer | Procurement Specialist |
|-------|------------------|----------------|----------------------|
| SQL Agent | ✅ | ✅ | ✅ |
| Inventory Optimizer | ✅ | ❌ | ❌ |
| Logistics Optimizer | ❌ | ✅ | ❌ |
| Supplier Analyzer | ❌ | ❌ | ✅ |

## Implementation Layers

### Layer 1: Cognito User Pool
- User authentication
- Group membership
- Password policies
- MFA enforcement

### Layer 2: API Gateway Authorizer
- JWT token validation
- Request authorization
- Context injection (username, groups, persona)

### Layer 3: Application Layer (Orchestrator)
- Persona validation
- Group membership verification
- Agent access control

### Layer 4: Data Layer (SQL Agent)
- Table access validation
- SQL query inspection
- Dynamic table filtering

## Security Features

### 1. Authentication
- ✅ Cognito-based authentication
- ✅ JWT token validation
- ✅ Token expiration (1 hour)
- ✅ Refresh token rotation
- ✅ MFA support

### 2. Authorization
- ✅ Role-based access control
- ✅ Group-based permissions
- ✅ Table-level access control
- ✅ Agent-level access control
- ✅ Dynamic SQL validation

### 3. Session Management
- ✅ Secure session storage
- ✅ Session timeout
- ✅ Logout functionality
- ✅ Token refresh

### 4. Audit & Compliance
- ✅ CloudWatch logging
- ✅ CloudTrail audit logs
- ✅ DynamoDB session tracking
- ✅ Access attempt logging

## User Management

### Creating Users

```bash
# Create user via AWS CLI
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username <username> \
  --user-attributes Name=email,Value=<email> \
  --temporary-password <temp-password>

# Add user to group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id <USER_POOL_ID> \
  --username <username> \
  --group-name warehouse_managers
```

### User Groups

Create groups in Cognito:
- `warehouse_managers`
- `field_engineers`
- `procurement_specialists`

### Password Policy

- Minimum length: 12 characters
- Requires: uppercase, lowercase, numbers, symbols
- Temporary password validity: 3 days
- Password history: 5 passwords

## API Authentication

### Request Headers

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### Example Request

```bash
curl -X POST https://api.example.com/query/inventory \
  -H "Authorization: Bearer eyJraWQ..." \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"identify_stockout_risks","input":{"warehouse_code":"WH01"}}'
```

### Response with Access Denied

```json
{
  "success": false,
  "error": "Access denied to table: purchase_order_header",
  "status": 403
}
```

## Streamlit Authentication

### Login Flow

1. User enters credentials
2. App calls Cognito authentication
3. Tokens stored in session state
4. User redirected to main app
5. Persona determined from groups

### Session State

```python
st.session_state.authenticated = True
st.session_state.access_token = "..."
st.session_state.username = "user1"
st.session_state.groups = ["warehouse_managers"]
st.session_state.persona = "warehouse_manager"
```

### Logout

```python
# Clear session state
for key in list(st.session_state.keys()):
    del st.session_state[key]
st.rerun()
```

## Testing RBAC

### Test Cases

1. **Valid Access**
   - Warehouse Manager queries warehouse_product ✅
   - Field Engineer uses logistics optimizer ✅
   - Procurement Specialist queries purchase orders ✅

2. **Invalid Access**
   - Warehouse Manager queries purchase orders ❌
   - Field Engineer uses inventory optimizer ❌
   - Procurement Specialist queries sales orders ❌

3. **Cross-Persona Access**
   - User with warehouse_manager persona tries to access field_engineer features ❌

### Testing Script

```python
# Test table access
from auth.auth_manager import AuthManager

auth = AuthManager(user_pool_id, client_id)

# Sign in
result = auth.sign_in("warehouse_manager1", "password")
groups = result['groups']

# Check table access
can_access = auth.check_table_access(groups, "warehouse_product")  # True
can_access = auth.check_table_access(groups, "purchase_order_header")  # False

# Check agent access
can_use = auth.check_agent_access(groups, "inventory_optimizer")  # True
can_use = auth.check_agent_access(groups, "supplier_analyzer")  # False
```

## Troubleshooting

### Common Issues

1. **"Access denied" errors**
   - Verify user is in correct Cognito group
   - Check persona matches group membership
   - Verify table is in allowed list for persona

2. **"Token expired" errors**
   - Use refresh token to get new access token
   - Re-authenticate if refresh token expired

3. **"Invalid token" errors**
   - Verify token format (Bearer <token>)
   - Check token hasn't been tampered with
   - Verify Cognito User Pool configuration

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

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

## Compliance

### GDPR
- User data encryption
- Right to deletion
- Access logging
- Data minimization

### SOC 2
- Access controls
- Audit logging
- Encryption
- Monitoring

### HIPAA (if applicable)
- PHI encryption
- Access controls
- Audit trails
- BAA agreements

## References

- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
