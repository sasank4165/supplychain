"""
Test Login Script

Tests authentication with the demo credentials to verify users.json is correctly configured.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.auth_manager import AuthManager


def test_login():
    """Test login with demo credentials"""
    print("=" * 70)
    print("  Testing Authentication")
    print("=" * 70)
    
    # Determine users file path (same logic as app.py)
    try:
        from utils.config_manager import ConfigManager
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.example.yaml')
        
        config_manager = ConfigManager(config_path)
        users_file = config_manager.get('auth.users_file', 'auth/users.json')
        
        # Make path absolute from mvp directory
        mvp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        users_file_absolute = os.path.join(mvp_dir, users_file)
        
        print(f"\nUsers file path: {users_file_absolute}")
        print(f"File exists: {os.path.exists(users_file_absolute)}")
        
    except Exception as e:
        print(f"\nError loading config: {e}")
        users_file_absolute = os.path.join(os.path.dirname(__file__), '..', 'auth', 'users.json')
        print(f"Using fallback path: {users_file_absolute}")
    
    # Initialize AuthManager
    try:
        auth_manager = AuthManager(users_file_absolute)
        print("\n✓ AuthManager initialized successfully")
    except Exception as e:
        print(f"\n✗ Failed to initialize AuthManager: {e}")
        return
    
    # Test credentials
    test_credentials = [
        ("demo_warehouse", "demo123"),
        ("demo_field", "demo123"),
        ("demo_procurement", "demo123"),
        ("demo_admin", "demo123"),
    ]
    
    print("\n" + "-" * 70)
    print("Testing Demo Credentials")
    print("-" * 70)
    
    for username, password in test_credentials:
        user = auth_manager.authenticate(username, password)
        if user:
            personas = ', '.join(user.personas)
            print(f"✓ {username:20} → SUCCESS ({personas})")
        else:
            print(f"✗ {username:20} → FAILED")
    
    # Test invalid credentials
    print("\n" + "-" * 70)
    print("Testing Invalid Credentials (should fail)")
    print("-" * 70)
    
    invalid_tests = [
        ("demo_warehouse", "wrong_password"),
        ("nonexistent_user", "demo123"),
        ("", ""),
    ]
    
    for username, password in invalid_tests:
        user = auth_manager.authenticate(username, password)
        if user:
            print(f"✗ {username or '(empty)':20} → UNEXPECTED SUCCESS")
        else:
            print(f"✓ {username or '(empty)':20} → Correctly rejected")
    
    print("\n" + "=" * 70)
    print("  Test Complete")
    print("=" * 70)


if __name__ == "__main__":
    test_login()
