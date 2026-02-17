"""
Example usage of authentication module
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import AuthManager, SessionManager


def example_authentication_flow():
    """Example: Complete authentication flow"""
    print("=" * 60)
    print("Example 1: Authentication Flow")
    print("=" * 60)
    
    # Initialize managers
    auth_manager = AuthManager("auth/users.json")
    session_manager = SessionManager(session_timeout=3600)
    
    # Step 1: User login
    print("\n1. User Login")
    username = "demo_warehouse"
    password = "password"
    
    user = auth_manager.authenticate(username, password)
    if user:
        print(f"   ✓ Login successful: {user.username}")
        print(f"   ✓ Available personas: {', '.join(user.personas)}")
    else:
        print("   ✗ Login failed")
        return
    
    # Step 2: Create session
    print("\n2. Create Session")
    session_id = session_manager.create_session(user.username, user.personas[0])
    print(f"   ✓ Session created: {session_id}")
    print(f"   ✓ Active persona: {user.personas[0]}")
    
    # Step 3: Check authorization
    print("\n3. Check Authorization")
    if auth_manager.authorize_persona(user, "Warehouse Manager"):
        print("   ✓ User authorized for Warehouse Manager")
    else:
        print("   ✗ User not authorized")
    
    # Step 4: Process query (simulated)
    print("\n4. Process Query")
    session = session_manager.get_session(session_id)
    if session:
        print(f"   ✓ Session valid")
        print(f"   ✓ User: {session.username}")
        print(f"   ✓ Persona: {session.persona}")
        print("   ✓ Query would be processed here...")
    
    # Step 5: Logout
    print("\n5. Logout")
    session_manager.invalidate_session(session_id)
    print("   ✓ Session invalidated")


def example_user_management():
    """Example: User management operations"""
    print("\n\n" + "=" * 60)
    print("Example 2: User Management")
    print("=" * 60)
    
    auth_manager = AuthManager("auth/users.json")
    
    # List all users
    print("\n1. List All Users")
    users = auth_manager.list_users()
    for user in users:
        print(f"   - {user.username}: {', '.join(user.personas)}")
    
    # Get specific user
    print("\n2. Get Specific User")
    user = auth_manager.get_user("demo_admin")
    if user:
        print(f"   ✓ Username: {user.username}")
        print(f"   ✓ Personas: {', '.join(user.personas)}")
        print(f"   ✓ Active: {user.active}")


def example_multi_persona_user():
    """Example: User with multiple personas"""
    print("\n\n" + "=" * 60)
    print("Example 3: Multi-Persona User")
    print("=" * 60)
    
    auth_manager = AuthManager("auth/users.json")
    session_manager = SessionManager()
    
    # Login as admin (has all personas)
    print("\n1. Login as Admin")
    user = auth_manager.authenticate("demo_admin", "password")
    if user:
        print(f"   ✓ Login successful: {user.username}")
        print(f"   ✓ Available personas: {', '.join(user.personas)}")
    
    # Create session with first persona
    print("\n2. Create Session with Warehouse Manager")
    session_id = session_manager.create_session(user.username, "Warehouse Manager")
    session = session_manager.get_session(session_id)
    print(f"   ✓ Current persona: {session.persona}")
    
    # Switch persona
    print("\n3. Switch to Field Engineer")
    session_manager.update_persona(session_id, "Field Engineer")
    session = session_manager.get_session(session_id)
    print(f"   ✓ Current persona: {session.persona}")
    
    # Verify authorization for all personas
    print("\n4. Verify Authorization")
    for persona in ["Warehouse Manager", "Field Engineer", "Procurement Specialist"]:
        authorized = auth_manager.authorize_persona(user, persona)
        status = "✓" if authorized else "✗"
        print(f"   {status} {persona}: {'Authorized' if authorized else 'Not authorized'}")


def example_session_expiration():
    """Example: Session expiration"""
    print("\n\n" + "=" * 60)
    print("Example 4: Session Expiration")
    print("=" * 60)
    
    # Create session manager with short timeout
    session_manager = SessionManager(session_timeout=2)
    
    print("\n1. Create Session (2 second timeout)")
    session_id = session_manager.create_session("test_user", "Warehouse Manager")
    print(f"   ✓ Session created: {session_id}")
    
    print("\n2. Get Session Immediately")
    session = session_manager.get_session(session_id)
    if session:
        print(f"   ✓ Session valid: {session.username}")
    
    print("\n3. Wait 3 seconds...")
    import time
    time.sleep(3)
    
    print("\n4. Get Session After Timeout")
    session = session_manager.get_session(session_id)
    if session:
        print(f"   ✓ Session still valid: {session.username}")
    else:
        print("   ✗ Session expired (as expected)")


def main():
    """Run all examples"""
    example_authentication_flow()
    example_user_management()
    example_multi_persona_user()
    example_session_expiration()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
