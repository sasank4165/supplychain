# User Management Guide

## User Credentials Location

All user credentials are stored in: **`mvp/auth/users.json`**

This is the single source of truth for user authentication.

## Demo Users

The system comes with 4 pre-configured demo users:

| Username | Password | Persona(s) |
|----------|----------|------------|
| `demo_warehouse` | `demo123` | Warehouse Manager |
| `demo_field` | `demo123` | Field Engineer |
| `demo_procurement` | `demo123` | Procurement Specialist |
| `demo_admin` | `demo123` | All three personas |

## Managing Users

### Option 1: Using the Script (Recommended)

Run the user management script from the **workspace root**:

```bash
cd /home/ec2-user/SageMaker/supplychain
python mvp/scripts/create_user.py
```

This interactive script allows you to:
1. List all users
2. Create new user
3. Update existing user
4. Delete user

The script automatically reads the correct path from your configuration.

### Option 2: Manual Editing

You can manually edit `mvp/auth/users.json`, but you'll need to:
1. Generate bcrypt password hashes (cost factor 12)
2. Follow the JSON structure exactly
3. Ensure valid persona names

**Example user entry:**
```json
{
  "username": "john_doe",
  "password_hash": "$2b$12$...",
  "personas": ["Warehouse Manager"],
  "active": true,
  "created_date": "2024-01-01T00:00:00"
}
```

## Available Personas

- **Warehouse Manager**: Inventory management and stock optimization
- **Field Engineer**: Logistics, delivery, and order fulfillment
- **Procurement Specialist**: Supplier management and purchase orders

Users can be assigned to multiple personas.

## Password Requirements

- Minimum 8 characters
- Stored as bcrypt hashes (never plain text)
- Cost factor: 12

## Troubleshooting

### "Invalid username or password" Error

1. Verify the user exists in `mvp/auth/users.json`
2. Check that `active` is set to `true`
3. Ensure you're using the correct password
4. Check that the persona is assigned to the user

### Script Can't Find users.json

Make sure you're running the script from the workspace root:
```bash
cd /home/ec2-user/SageMaker/supplychain
python mvp/scripts/create_user.py
```

### Changes Not Reflected in App

1. Restart the Streamlit application
2. Clear your browser cache
3. Verify changes were saved to `mvp/auth/users.json`

## Security Notes

- Never commit `users.json` with real passwords to version control
- Use strong passwords for production deployments
- Consider using environment-based user management for production
- The demo passwords (`demo123`) should only be used for testing

## Configuration

The users file path is configured in `config.yaml`:

```yaml
auth:
  users_file: auth/users.json  # Relative to mvp directory
```

If no config exists, the system defaults to `mvp/auth/users.json`.
