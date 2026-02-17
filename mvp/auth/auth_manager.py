"""
Authentication Manager for Supply Chain AI Assistant

Handles user authentication with bcrypt password hashing and persona-based authorization.
"""

import json
import os
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime
import bcrypt


@dataclass
class User:
    """User data model"""
    username: str
    password_hash: str
    personas: List[str]
    active: bool
    created_date: str
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary for JSON storage"""
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "personas": self.personas,
            "active": self.active,
            "created_date": self.created_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create user from dictionary"""
        return cls(
            username=data["username"],
            password_hash=data["password_hash"],
            personas=data["personas"],
            active=data.get("active", True),
            created_date=data.get("created_date", datetime.now().isoformat())
        )


class AuthManager:
    """
    Manages user authentication and authorization.
    
    Features:
    - Bcrypt password hashing (cost factor 12)
    - Persona-based authorization
    - User storage in JSON file
    - Active/inactive user management
    """
    
    def __init__(self, users_file: str = "mvp/auth/users.json"):
        """
        Initialize authentication manager.
        
        Args:
            users_file: Path to users JSON file
        """
        self.users_file = users_file
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Create users file if it doesn't exist"""
        if not os.path.exists(self.users_file):
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            self._save_users({"users": []})
    
    def _load_users(self) -> Dict:
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": []}
    
    def _save_users(self, data: Dict):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt with cost factor 12.
        
        Args:
            password: Plain text password
            
        Returns:
            Bcrypt hash as string
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            password_hash: Bcrypt hash
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        data = self._load_users()
        
        for user_data in data.get("users", []):
            if user_data["username"] == username:
                user = User.from_dict(user_data)
                
                # Check if user is active
                if not user.active:
                    return None
                
                # Verify password
                if self._verify_password(password, user.password_hash):
                    return user
                else:
                    return None
        
        return None
    
    def authorize_persona(self, user: User, persona: str) -> bool:
        """
        Check if user is authorized for a specific persona.
        
        Args:
            user: User object
            persona: Persona name (e.g., "Warehouse Manager")
            
        Returns:
            True if authorized, False otherwise
        """
        return persona in user.personas
    
    def get_authorized_personas(self, user: User) -> List[str]:
        """
        Get list of personas user is authorized for.
        
        Args:
            user: User object
            
        Returns:
            List of persona names
        """
        return user.personas.copy()
    
    def create_user(
        self, 
        username: str, 
        password: str, 
        personas: List[str],
        active: bool = True
    ) -> bool:
        """
        Create a new user.
        
        Args:
            username: Username (must be unique)
            password: Plain text password (will be hashed)
            personas: List of authorized personas
            active: Whether user is active
            
        Returns:
            True if user created successfully, False if username exists
        """
        data = self._load_users()
        
        # Check if username already exists
        for user_data in data.get("users", []):
            if user_data["username"] == username:
                return False
        
        # Create new user
        user = User(
            username=username,
            password_hash=self._hash_password(password),
            personas=personas,
            active=active,
            created_date=datetime.now().isoformat()
        )
        
        data["users"].append(user.to_dict())
        self._save_users(data)
        return True
    
    def update_user(
        self,
        username: str,
        password: Optional[str] = None,
        personas: Optional[List[str]] = None,
        active: Optional[bool] = None
    ) -> bool:
        """
        Update an existing user.
        
        Args:
            username: Username to update
            password: New password (optional)
            personas: New personas list (optional)
            active: New active status (optional)
            
        Returns:
            True if user updated successfully, False if user not found
        """
        data = self._load_users()
        
        for i, user_data in enumerate(data.get("users", [])):
            if user_data["username"] == username:
                # Update fields if provided
                if password is not None:
                    user_data["password_hash"] = self._hash_password(password)
                if personas is not None:
                    user_data["personas"] = personas
                if active is not None:
                    user_data["active"] = active
                
                data["users"][i] = user_data
                self._save_users(data)
                return True
        
        return False
    
    def delete_user(self, username: str) -> bool:
        """
        Delete a user.
        
        Args:
            username: Username to delete
            
        Returns:
            True if user deleted successfully, False if user not found
        """
        data = self._load_users()
        
        original_count = len(data.get("users", []))
        data["users"] = [u for u in data.get("users", []) if u["username"] != username]
        
        if len(data["users"]) < original_count:
            self._save_users(data)
            return True
        
        return False
    
    def get_user(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to retrieve
            
        Returns:
            User object if found, None otherwise
        """
        data = self._load_users()
        
        for user_data in data.get("users", []):
            if user_data["username"] == username:
                return User.from_dict(user_data)
        
        return None
    
    def list_users(self) -> List[User]:
        """
        List all users.
        
        Returns:
            List of User objects
        """
        data = self._load_users()
        return [User.from_dict(u) for u in data.get("users", [])]
