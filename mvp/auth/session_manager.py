"""
Session Manager for Supply Chain AI Assistant

Handles user session management with secure session tokens and timeout.
"""

import uuid
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Session:
    """Session data model"""
    session_id: str
    username: str
    persona: Optional[str]
    created_at: datetime
    last_activity: datetime
    
    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """
        Check if session has expired.
        
        Args:
            timeout_seconds: Session timeout in seconds (default 1 hour)
            
        Returns:
            True if session expired, False otherwise
        """
        return (datetime.now() - self.last_activity).total_seconds() > timeout_seconds
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()


class SessionManager:
    """
    Manages user sessions with secure tokens and timeout.
    
    Features:
    - UUID4 session tokens
    - Session timeout (default 1 hour)
    - Session invalidation on logout
    - Persona tracking per session
    """
    
    def __init__(self, session_timeout: int = 3600):
        """
        Initialize session manager.
        
        Args:
            session_timeout: Session timeout in seconds (default 3600 = 1 hour)
        """
        self.session_timeout = session_timeout
        self._sessions: Dict[str, Session] = {}
    
    def create_session(self, username: str, persona: Optional[str] = None) -> str:
        """
        Create a new session for a user.
        
        Args:
            username: Username
            persona: Initial persona (optional)
            
        Returns:
            Session ID (UUID4)
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = Session(
            session_id=session_id,
            username=username,
            persona=persona,
            created_at=now,
            last_activity=now
        )
        
        self._sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session object if valid and not expired, None otherwise
        """
        session = self._sessions.get(session_id)
        
        if session is None:
            return None
        
        # Check if session expired
        if session.is_expired(self.session_timeout):
            self.invalidate_session(session_id)
            return None
        
        # Update last activity
        session.update_activity()
        return session
    
    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate (delete) a session.
        
        Args:
            session_id: Session ID to invalidate
            
        Returns:
            True if session was invalidated, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def update_persona(self, session_id: str, persona: str) -> bool:
        """
        Update the persona for a session.
        
        Args:
            session_id: Session ID
            persona: New persona
            
        Returns:
            True if updated successfully, False if session not found
        """
        session = self.get_session(session_id)
        if session:
            session.persona = persona
            return True
        return False
    
    def get_username(self, session_id: str) -> Optional[str]:
        """
        Get username for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Username if session valid, None otherwise
        """
        session = self.get_session(session_id)
        return session.username if session else None
    
    def get_persona(self, session_id: str) -> Optional[str]:
        """
        Get current persona for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Persona if session valid, None otherwise
        """
        session = self.get_session(session_id)
        return session.persona if session else None
    
    def cleanup_expired_sessions(self):
        """Remove all expired sessions"""
        expired_ids = [
            sid for sid, session in self._sessions.items()
            if session.is_expired(self.session_timeout)
        ]
        
        for sid in expired_ids:
            del self._sessions[sid]
    
    def get_active_session_count(self) -> int:
        """
        Get count of active (non-expired) sessions.
        
        Returns:
            Number of active sessions
        """
        self.cleanup_expired_sessions()
        return len(self._sessions)
    
    def get_user_sessions(self, username: str) -> list[str]:
        """
        Get all active session IDs for a user.
        
        Args:
            username: Username
            
        Returns:
            List of session IDs
        """
        self.cleanup_expired_sessions()
        return [
            sid for sid, session in self._sessions.items()
            if session.username == username
        ]
