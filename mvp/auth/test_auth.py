"""
Tests for authentication and session management
"""

import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta

from auth_manager import AuthManager, User
from session_manager import SessionManager, Session


class TestAuthManager:
    """Test cases for AuthManager"""
    
    @pytest.fixture
    def temp_users_file(self):
        """Create temporary users file"""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def auth_manager(self, temp_users_file):
        """Create AuthManager with temporary file"""
        return AuthManager(temp_users_file)
    
    def test_create_user(self, auth_manager):
        """Test user creation"""
        success = auth_manager.create_user(
            username="test_user",
            password="password123",
            personas=["Warehouse Manager"],
            active=True
        )
        
        assert success is True
        
        # Verify user was created
        user = auth_manager.get_user("test_user")
        assert user is not None
        assert user.username == "test_user"
        assert user.personas == ["Warehouse Manager"]
        assert user.active is True
    
    def test_create_duplicate_user(self, auth_manager):
        """Test creating duplicate user fails"""
        auth_manager.create_user("test_user", "password123", ["Warehouse Manager"])
        
        # Try to create again
        success = auth_manager.create_user("test_user", "password456", ["Field Engineer"])
        assert success is False
    
    def test_authenticate_valid_user(self, auth_manager):
        """Test authentication with valid credentials"""
        auth_manager.create_user("test_user", "password123", ["Warehouse Manager"])
        
        user = auth_manager.authenticate("test_user", "password123")
        assert user is not None
        assert user.username == "test_user"
    
    def test_authenticate_invalid_password(self, auth_manager):
        """Test authentication with invalid password"""
        auth_manager.create_user("test_user", "password123", ["Warehouse Manager"])
        
        user = auth_manager.authenticate("test_user", "wrong_password")
        assert user is None
    
    def test_authenticate_nonexistent_user(self, auth_manager):
        """Test authentication with nonexistent user"""
        user = auth_manager.authenticate("nonexistent", "password123")
        assert user is None
    
    def test_authenticate_inactive_user(self, auth_manager):
        """Test authentication with inactive user"""
        auth_manager.create_user("test_user", "password123", ["Warehouse Manager"], active=False)
        
        user = auth_manager.authenticate("test_user", "password123")
        assert user is None
    
    def test_authorize_persona(self, auth_manager):
        """Test persona authorization"""
        auth_manager.create_user(
            "test_user", 
            "password123", 
            ["Warehouse Manager", "Field Engineer"]
        )
        
        user = auth_manager.get_user("test_user")
        
        assert auth_manager.authorize_persona(user, "Warehouse Manager") is True
        assert auth_manager.authorize_persona(user, "Field Engineer") is True
        assert auth_manager.authorize_persona(user, "Procurement Specialist") is False
    
    def test_get_authorized_personas(self, auth_manager):
        """Test getting authorized personas"""
        auth_manager.create_user(
            "test_user",
            "password123",
            ["Warehouse Manager", "Field Engineer"]
        )
        
        user = auth_manager.get_user("test_user")
        personas = auth_manager.get_authorized_personas(user)
        
        assert len(personas) == 2
        assert "Warehouse Manager" in personas
        assert "Field Engineer" in personas
    
    def test_update_user_password(self, auth_manager):
        """Test updating user password"""
        auth_manager.create_user("test_user", "password123", ["Warehouse Manager"])
        
        # Update password
        success = auth_manager.update_user("test_user", password="new_password")
        assert success is True
        
        # Old password should not work
        user = auth_manager.authenticate("test_user", "password123")
        assert user is None
        
        # New password should work
        user = auth_manager.authenticate("test_user", "new_password")
        assert user is not None
    
    def test_update_user_personas(self, auth_manager):
        """Test updating user personas"""
        auth_manager.create_user("test_user", "password123", ["Warehouse Manager"])
        
        # Update personas
        success = auth_manager.update_user(
            "test_user",
            personas=["Field Engineer", "Procurement Specialist"]
        )
        assert success is True
        
        # Verify personas updated
        user = auth_manager.get_user("test_user")
        assert len(user.personas) == 2
        assert "Field Engineer" in user.personas
        assert "Procurement Specialist" in user.personas
    
    def test_update_user_active_status(self, auth_manager):
        """Test updating user active status"""
        auth_manager.create_user("test_user", "password123", ["Warehouse Manager"])
        
        # Deactivate user
        success = auth_manager.update_user("test_user", active=False)
        assert success is True
        
        # User should not be able to authenticate
        user = auth_manager.authenticate("test_user", "password123")
        assert user is None
    
    def test_delete_user(self, auth_manager):
        """Test deleting user"""
        auth_manager.create_user("test_user", "password123", ["Warehouse Manager"])
        
        # Delete user
        success = auth_manager.delete_user("test_user")
        assert success is True
        
        # User should not exist
        user = auth_manager.get_user("test_user")
        assert user is None
    
    def test_delete_nonexistent_user(self, auth_manager):
        """Test deleting nonexistent user"""
        success = auth_manager.delete_user("nonexistent")
        assert success is False
    
    def test_list_users(self, auth_manager):
        """Test listing all users"""
        auth_manager.create_user("user1", "password123", ["Warehouse Manager"])
        auth_manager.create_user("user2", "password456", ["Field Engineer"])
        
        users = auth_manager.list_users()
        assert len(users) == 2
        
        usernames = [u.username for u in users]
        assert "user1" in usernames
        assert "user2" in usernames


class TestSessionManager:
    """Test cases for SessionManager"""
    
    @pytest.fixture
    def session_manager(self):
        """Create SessionManager"""
        return SessionManager(session_timeout=3600)
    
    def test_create_session(self, session_manager):
        """Test session creation"""
        session_id = session_manager.create_session("test_user", "Warehouse Manager")
        
        assert session_id is not None
        assert len(session_id) == 36  # UUID4 length
    
    def test_get_session(self, session_manager):
        """Test getting session"""
        session_id = session_manager.create_session("test_user", "Warehouse Manager")
        
        session = session_manager.get_session(session_id)
        assert session is not None
        assert session.username == "test_user"
        assert session.persona == "Warehouse Manager"
    
    def test_get_nonexistent_session(self, session_manager):
        """Test getting nonexistent session"""
        session = session_manager.get_session("nonexistent-id")
        assert session is None
    
    def test_session_expiration(self):
        """Test session expiration"""
        # Create session manager with 1 second timeout
        session_manager = SessionManager(session_timeout=1)
        session_id = session_manager.create_session("test_user")
        
        # Session should be valid immediately
        session = session_manager.get_session(session_id)
        assert session is not None
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Session should be expired
        session = session_manager.get_session(session_id)
        assert session is None
    
    def test_invalidate_session(self, session_manager):
        """Test session invalidation"""
        session_id = session_manager.create_session("test_user")
        
        # Invalidate session
        success = session_manager.invalidate_session(session_id)
        assert success is True
        
        # Session should not exist
        session = session_manager.get_session(session_id)
        assert session is None
    
    def test_update_persona(self, session_manager):
        """Test updating session persona"""
        session_id = session_manager.create_session("test_user", "Warehouse Manager")
        
        # Update persona
        success = session_manager.update_persona(session_id, "Field Engineer")
        assert success is True
        
        # Verify persona updated
        session = session_manager.get_session(session_id)
        assert session.persona == "Field Engineer"
    
    def test_get_username(self, session_manager):
        """Test getting username from session"""
        session_id = session_manager.create_session("test_user")
        
        username = session_manager.get_username(session_id)
        assert username == "test_user"
    
    def test_get_persona(self, session_manager):
        """Test getting persona from session"""
        session_id = session_manager.create_session("test_user", "Warehouse Manager")
        
        persona = session_manager.get_persona(session_id)
        assert persona == "Warehouse Manager"
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions"""
        # Create session manager with 1 second timeout
        session_manager = SessionManager(session_timeout=1)
        
        # Create multiple sessions
        session_id1 = session_manager.create_session("user1")
        session_id2 = session_manager.create_session("user2")
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Cleanup expired sessions
        session_manager.cleanup_expired_sessions()
        
        # Both sessions should be removed
        assert session_manager.get_active_session_count() == 0
    
    def test_get_active_session_count(self, session_manager):
        """Test getting active session count"""
        session_manager.create_session("user1")
        session_manager.create_session("user2")
        
        count = session_manager.get_active_session_count()
        assert count == 2
    
    def test_get_user_sessions(self, session_manager):
        """Test getting all sessions for a user"""
        session_id1 = session_manager.create_session("test_user")
        session_id2 = session_manager.create_session("test_user")
        session_id3 = session_manager.create_session("other_user")
        
        user_sessions = session_manager.get_user_sessions("test_user")
        assert len(user_sessions) == 2
        assert session_id1 in user_sessions
        assert session_id2 in user_sessions
        assert session_id3 not in user_sessions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
