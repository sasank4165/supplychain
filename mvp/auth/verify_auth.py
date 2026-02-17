"""
Verification script for authentication module
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.auth_manager import AuthManager
from auth.session_manager import SessionManager


def test_auth_manager():
    """Test AuthManager functionality"""
    print("Testing AuthManager...")
    
    # Initialize with test file
    auth_manager = AuthManager("auth/users.json")
    
    # Test 1: Authenticate demo user
    print("\n1. Testing authentication with demo_warehouse user...")
    user = auth_manager.authenticate("demo_warehouse", "password")
    if user:
        print(f"   ✓ Authentication successful: {user.username}")
        print(f"   ✓ Personas: {user.personas}")
    else:
        print("   ✗ Authentication failed")
        return False
    
    # Test 2: Check persona authorization
    print("\n2. Testing persona authorization...")
    if auth_manager.authorize_persona(user, "Warehouse Manager"):
        print("   ✓ User authorized for Warehouse Manager")
    else:
        print("   ✗ Authorization failed")
        return False
    
    if not auth_manager.authorize_persona(user, "Procurement Specialist"):
        print("   ✓ User correctly not authorized for Procurement Specialist")
    else:
        print("   ✗ Authorization check failed")
        return False
    
    # Test 3: Get authorized personas
    print("\n3. Testing get_authorized_personas...")
    personas = auth_manager.get_authorized_personas(user)
    print(f"   ✓ Authorized personas: {personas}")
    
    # Test 4: List all users
    print("\n4. Testing list_users...")
    users = auth_manager.list_users()
    print(f"   ✓ Found {len(users)} users")
    for u in users:
        print(f"     - {u.username}: {', '.join(u.personas)}")
    
    # Test 5: Invalid authentication
    print("\n5. Testing invalid authentication...")
    invalid_user = auth_manager.authenticate("demo_warehouse", "wrong_password")
    if invalid_user is None:
        print("   ✓ Invalid password correctly rejected")
    else:
        print("   ✗ Invalid password accepted (should fail)")
        return False
    
    print("\n✓ All AuthManager tests passed!")
    return True


def test_session_manager():
    """Test SessionManager functionality"""
    print("\n\nTesting SessionManager...")
    
    # Initialize
    session_manager = SessionManager(session_timeout=3600)
    
    # Test 1: Create session
    print("\n1. Testing session creation...")
    session_id = session_manager.create_session("test_user", "Warehouse Manager")
    print(f"   ✓ Session created: {session_id}")
    
    # Test 2: Get session
    print("\n2. Testing get_session...")
    session = session_manager.get_session(session_id)
    if session:
        print(f"   ✓ Session retrieved: {session.username}, {session.persona}")
    else:
        print("   ✗ Failed to retrieve session")
        return False
    
    # Test 3: Update persona
    print("\n3. Testing update_persona...")
    success = session_manager.update_persona(session_id, "Field Engineer")
    if success:
        session = session_manager.get_session(session_id)
        print(f"   ✓ Persona updated to: {session.persona}")
    else:
        print("   ✗ Failed to update persona")
        return False
    
    # Test 4: Get username and persona
    print("\n4. Testing get_username and get_persona...")
    username = session_manager.get_username(session_id)
    persona = session_manager.get_persona(session_id)
    print(f"   ✓ Username: {username}, Persona: {persona}")
    
    # Test 5: Invalidate session
    print("\n5. Testing invalidate_session...")
    success = session_manager.invalidate_session(session_id)
    if success:
        session = session_manager.get_session(session_id)
        if session is None:
            print("   ✓ Session invalidated successfully")
        else:
            print("   ✗ Session still exists after invalidation")
            return False
    else:
        print("   ✗ Failed to invalidate session")
        return False
    
    # Test 6: Active session count
    print("\n6. Testing active session count...")
    session_id1 = session_manager.create_session("user1")
    session_id2 = session_manager.create_session("user2")
    count = session_manager.get_active_session_count()
    print(f"   ✓ Active sessions: {count}")
    
    print("\n✓ All SessionManager tests passed!")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("  Authentication Module Verification")
    print("=" * 60)
    
    auth_success = test_auth_manager()
    session_success = test_session_manager()
    
    print("\n" + "=" * 60)
    if auth_success and session_success:
        print("  ✓ ALL TESTS PASSED")
    else:
        print("  ✗ SOME TESTS FAILED")
    print("=" * 60)
    
    return auth_success and session_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
