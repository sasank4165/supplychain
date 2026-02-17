"""
Quick User Creation Script

Usage:
    python mvp/scripts/add_user.py <username> <password> <personas>

Example:
    python mvp/scripts/add_user.py john_doe mypassword "Warehouse Manager,Field Engineer"
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.auth_manager import AuthManager


def main():
    if len(sys.argv) < 4:
        print("Usage: python add_user.py <username> <password> <personas>")
        print('Example: python add_user.py john_doe mypassword "Warehouse Manager,Field Engineer"')
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    personas_str = sys.argv[3]
    
    # Parse personas
    personas = [p.strip() for p in personas_str.split(",")]
    
    # Validate personas
    valid_personas = ["Warehouse Manager", "Field Engineer", "Procurement Specialist"]
    for persona in personas:
        if persona not in valid_personas:
            print(f"Error: Invalid persona '{persona}'")
            print(f"Valid personas: {', '.join(valid_personas)}")
            sys.exit(1)
    
    # Validate password length
    if len(password) < 8:
        print("Error: Password must be at least 8 characters")
        sys.exit(1)
    
    # Create user
    auth_manager = AuthManager("mvp/auth/users.json")
    success = auth_manager.create_user(
        username=username,
        password=password,
        personas=personas,
        active=True
    )
    
    if success:
        print(f"✓ User '{username}' created successfully!")
        print(f"  Personas: {', '.join(personas)}")
    else:
        print(f"✗ Failed to create user '{username}' (user may already exist)")
        sys.exit(1)


if __name__ == "__main__":
    main()
