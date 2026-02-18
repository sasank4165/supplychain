"""
User Management Utility for Supply Chain AI Assistant

Interactive script to create, update, and delete users.
"""

import sys
import os
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.auth_manager import AuthManager


AVAILABLE_PERSONAS = [
    "Warehouse Manager",
    "Field Engineer",
    "Procurement Specialist"
]


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_users(auth_manager: AuthManager):
    """Display all users"""
    users = auth_manager.list_users()
    
    if not users:
        print("No users found.")
        return
    
    print(f"\n{'Username':<20} {'Personas':<40} {'Active':<10}")
    print("-" * 70)
    
    for user in users:
        personas_str = ", ".join(user.personas)
        active_str = "Yes" if user.active else "No"
        print(f"{user.username:<20} {personas_str:<40} {active_str:<10}")
    
    print()


def create_user(auth_manager: AuthManager):
    """Create a new user"""
    print_header("Create New User")
    
    # Get username
    username = input("Username: ").strip()
    if not username:
        print("Error: Username cannot be empty.")
        return
    
    # Check if user exists
    if auth_manager.get_user(username):
        print(f"Error: User '{username}' already exists.")
        return
    
    # Get password
    password = getpass("Password: ")
    if len(password) < 8:
        print("Error: Password must be at least 8 characters.")
        return
    
    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        print("Error: Passwords do not match.")
        return
    
    # Select personas
    print("\nAvailable personas:")
    for i, persona in enumerate(AVAILABLE_PERSONAS, 1):
        print(f"  {i}. {persona}")
    
    print("\nEnter persona numbers separated by commas (e.g., 1,2):")
    persona_input = input("Personas: ").strip()
    
    try:
        persona_indices = [int(x.strip()) - 1 for x in persona_input.split(",")]
        personas = [AVAILABLE_PERSONAS[i] for i in persona_indices if 0 <= i < len(AVAILABLE_PERSONAS)]
        
        if not personas:
            print("Error: No valid personas selected.")
            return
    except (ValueError, IndexError):
        print("Error: Invalid persona selection.")
        return
    
    # Active status
    active_input = input("\nActive user? (Y/n): ").strip().lower()
    active = active_input != 'n'
    
    # Create user
    success = auth_manager.create_user(
        username=username,
        password=password,
        personas=personas,
        active=active
    )
    
    if success:
        print(f"\n✓ User '{username}' created successfully!")
        print(f"  Personas: {', '.join(personas)}")
        print(f"  Active: {'Yes' if active else 'No'}")
    else:
        print(f"\n✗ Failed to create user '{username}'.")


def update_user(auth_manager: AuthManager):
    """Update an existing user"""
    print_header("Update User")
    
    # Get username
    username = input("Username to update: ").strip()
    if not username:
        print("Error: Username cannot be empty.")
        return
    
    # Check if user exists
    user = auth_manager.get_user(username)
    if not user:
        print(f"Error: User '{username}' not found.")
        return
    
    print(f"\nCurrent settings for '{username}':")
    print(f"  Personas: {', '.join(user.personas)}")
    print(f"  Active: {'Yes' if user.active else 'No'}")
    
    # Update password
    print("\nUpdate password? (leave blank to skip)")
    password = getpass("New password: ")
    
    if password:
        if len(password) < 8:
            print("Error: Password must be at least 8 characters.")
            return
        
        password_confirm = getpass("Confirm password: ")
        if password != password_confirm:
            print("Error: Passwords do not match.")
            return
    else:
        password = None
    
    # Update personas
    print("\nUpdate personas? (leave blank to skip)")
    print("Available personas:")
    for i, persona in enumerate(AVAILABLE_PERSONAS, 1):
        print(f"  {i}. {persona}")
    
    persona_input = input("Personas (e.g., 1,2): ").strip()
    
    if persona_input:
        try:
            persona_indices = [int(x.strip()) - 1 for x in persona_input.split(",")]
            personas = [AVAILABLE_PERSONAS[i] for i in persona_indices if 0 <= i < len(AVAILABLE_PERSONAS)]
            
            if not personas:
                print("Error: No valid personas selected.")
                return
        except (ValueError, IndexError):
            print("Error: Invalid persona selection.")
            return
    else:
        personas = None
    
    # Update active status
    active_input = input("\nUpdate active status? (Y/n/skip): ").strip().lower()
    if active_input == 'skip' or active_input == '':
        active = None
    else:
        active = active_input != 'n'
    
    # Update user
    success = auth_manager.update_user(
        username=username,
        password=password,
        personas=personas,
        active=active
    )
    
    if success:
        print(f"\n✓ User '{username}' updated successfully!")
        
        # Show updated settings
        updated_user = auth_manager.get_user(username)
        print(f"  Personas: {', '.join(updated_user.personas)}")
        print(f"  Active: {'Yes' if updated_user.active else 'No'}")
    else:
        print(f"\n✗ Failed to update user '{username}'.")


def delete_user(auth_manager: AuthManager):
    """Delete a user"""
    print_header("Delete User")
    
    # Get username
    username = input("Username to delete: ").strip()
    if not username:
        print("Error: Username cannot be empty.")
        return
    
    # Check if user exists
    user = auth_manager.get_user(username)
    if not user:
        print(f"Error: User '{username}' not found.")
        return
    
    # Confirm deletion
    print(f"\nUser details:")
    print(f"  Username: {user.username}")
    print(f"  Personas: {', '.join(user.personas)}")
    print(f"  Active: {'Yes' if user.active else 'No'}")
    
    confirm = input(f"\nAre you sure you want to delete '{username}'? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Deletion cancelled.")
        return
    
    # Delete user
    success = auth_manager.delete_user(username)
    
    if success:
        print(f"\n✓ User '{username}' deleted successfully!")
    else:
        print(f"\n✗ Failed to delete user '{username}'.")


def main():
    """Main menu"""
    # Initialize auth manager with config-based path
    # Try to load from config, fallback to default
    try:
        from utils.config_manager import ConfigManager
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.example.yaml')
        config_manager = ConfigManager(config_path)
        users_file = config_manager.get('auth.users_file', 'auth/users.json')
        # Make path absolute from mvp directory
        users_file = os.path.join(os.path.dirname(__file__), '..', users_file)
    except Exception:
        # Fallback to default path
        users_file = os.path.join(os.path.dirname(__file__), '..', 'auth', 'users.json')
    
    auth_manager = AuthManager(users_file)
    
    while True:
        print_header("User Management Utility")
        print("1. List all users")
        print("2. Create new user")
        print("3. Update user")
        print("4. Delete user")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == '1':
            print_header("All Users")
            print_users(auth_manager)
        elif choice == '2':
            create_user(auth_manager)
        elif choice == '3':
            update_user(auth_manager)
        elif choice == '4':
            delete_user(auth_manager)
        elif choice == '5':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid option. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
