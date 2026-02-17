# Authentication Module

This module provides authentication and authorization functionality for the Supply Chain AI Assistant MVP.

## Components

### AuthManager (`auth_manager.py`)

Handles user authentication with bcrypt password hashing and persona-based authorization.

**Features:**
- Bcrypt password hashing with cost factor 12
- User storage in JSON file
- Persona-based authorization
- Active/inactive user management
- CRUD operations for users

**Usage:**
```python
from mvp.auth import AuthManager

# Initialize
auth_manager = AuthManager("mvp/auth/users.json")

# Authenticate user
user = auth_manager.authenticate("username", "password")
if user:
    print(f"Authenticated: {user.username}")
    print(f"Personas: {user.personas}")

# Check persona authorization
if auth_manager.authorize_persona(user, "Warehouse Manager"):
    print("User authorized for Warehouse Manager persona")

# Get authorized personas
personas = auth_manager.get_authorized_personas(user)
```

### SessionManager (`session_manager.py`)

Manages user sessions with secure tokens and timeout.

**Features:**
- UUID4 session tokens
- Session timeout (default 1 hour)
- Session invalidation on logout
- Persona tracking per session
- Automatic cleanup of expired sessions

**Usage:**
```python
from mvp.auth import SessionManager

# Initialize
session_manager = SessionManager(session_timeout=3600)

# Create session after authentication
session_id = session_manager.create_session(username="john_doe", persona="Warehouse Manager")

# Get session
session = session_manager.get_session(session_id)
if session:
    print(f"User: {session.username}, Persona: {session.persona}")

# Update persona
session_manager.update_persona(session_id, "Field Engineer")

# Invalidate session (logout)
session_manager.invalidate_session(session_id)
```

## User Data Model

Users are stored in `users.json` with the following structure:

```json
{
  "users": [
    {
      "username": "john_doe",
      "password_hash": "$2b$12$...",
      "personas": ["Warehouse Manager", "Field Engineer"],
      "active": true,
      "created_date": "2024-01-01T00:00:00"
    }
  ]
}
```

## Demo Users

The system comes with pre-configured demo users (all with password "password"):

| Username | Password | Personas |
|----------|----------|----------|
| demo_warehouse | password | Warehouse Manager |
| demo_field | password | Field Engineer |
| demo_procurement | password | Procurement Specialist |
| demo_admin | password | All personas |

## Security Features

1. **Password Hashing**: Bcrypt with cost factor 12
2. **Session Tokens**: Secure UUID4 tokens
3. **Session Timeout**: Automatic expiration after 1 hour of inactivity
4. **Persona Authorization**: Users can only access authorized personas
5. **Active/Inactive Users**: Ability to disable users without deletion

## Creating Users

Use the `scripts/create_user.py` utility to create new users:

```bash
python mvp/scripts/create_user.py
```

Or programmatically:

```python
from mvp.auth import AuthManager

auth_manager = AuthManager()
success = auth_manager.create_user(
    username="new_user",
    password="secure_password",
    personas=["Warehouse Manager"],
    active=True
)
```

## Integration with Streamlit

The authentication module integrates with Streamlit's session state:

```python
import streamlit as st
from mvp.auth import AuthManager, SessionManager

# Initialize managers
auth_manager = AuthManager()
session_manager = SessionManager()

# Login flow
if 'session_id' not in st.session_state:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        user = auth_manager.authenticate(username, password)
        if user:
            session_id = session_manager.create_session(user.username)
            st.session_state.session_id = session_id
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid credentials")
else:
    # User is logged in
    session = session_manager.get_session(st.session_state.session_id)
    if session:
        st.write(f"Welcome, {session.username}!")
    else:
        # Session expired
        del st.session_state.session_id
        st.rerun()
```

## Requirements

- Python 3.11+
- bcrypt

Install dependencies:
```bash
pip install bcrypt
```
