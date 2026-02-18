"""
Path Verification Script

Verifies that all file paths are correctly configured and accessible.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.config_manager import ConfigManager


def verify_paths():
    """Verify all critical file paths"""
    print("=" * 70)
    print("  Path Verification")
    print("=" * 70)
    
    # Get script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mvp_dir = os.path.abspath(os.path.join(script_dir, '..'))
    
    print(f"\nScript directory: {script_dir}")
    print(f"MVP directory: {mvp_dir}")
    
    # Check config file
    print("\n--- Configuration File ---")
    config_path = os.path.join(mvp_dir, 'config.yaml')
    if os.path.exists(config_path):
        print(f"✓ config.yaml found: {config_path}")
    else:
        config_path = os.path.join(mvp_dir, 'config.example.yaml')
        print(f"⚠ config.yaml not found, using: {config_path}")
    
    # Load config
    try:
        config_manager = ConfigManager(config_path)
        print("✓ Configuration loaded successfully")
        
        # Get users_file from config
        users_file_relative = config_manager.get('auth.users_file', 'auth/users.json')
        print(f"  users_file (from config): {users_file_relative}")
        
        # Resolve absolute path
        users_file_absolute = os.path.join(mvp_dir, users_file_relative)
        print(f"  users_file (absolute): {users_file_absolute}")
        
        # Check if file exists
        print("\n--- Users File ---")
        if os.path.exists(users_file_absolute):
            print(f"✓ users.json found: {users_file_absolute}")
            
            # Count users
            import json
            with open(users_file_absolute, 'r') as f:
                data = json.load(f)
                user_count = len(data.get('users', []))
                print(f"  Number of users: {user_count}")
                
                if user_count > 0:
                    print("  Users:")
                    for user in data['users']:
                        personas = ', '.join(user.get('personas', []))
                        print(f"    - {user['username']} ({personas})")
        else:
            print(f"✗ users.json NOT found: {users_file_absolute}")
        
        # Check other critical paths
        print("\n--- Other Critical Paths ---")
        
        paths_to_check = [
            ('logs directory', os.path.join(mvp_dir, 'logs')),
            ('auth directory', os.path.join(mvp_dir, 'auth')),
            ('aws directory', os.path.join(mvp_dir, 'aws')),
            ('ui directory', os.path.join(mvp_dir, 'ui')),
        ]
        
        for name, path in paths_to_check:
            if os.path.exists(path):
                print(f"✓ {name}: {path}")
            else:
                print(f"✗ {name} NOT found: {path}")
        
        print("\n" + "=" * 70)
        print("  Verification Complete")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error loading configuration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verify_paths()
