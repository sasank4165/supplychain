"""
Conversation Memory

Manages session-level conversation memory with history storage.
"""

from typing import Dict, List, Optional, Any
import time
import threading
from datetime import datetime

from memory.context import ConversationContext, Interaction, Persona, SessionMetadata


class ConversationMemory:
    """
    Session-level conversation memory manager.
    
    Features:
    - Store last N interactions per session
    - Thread-safe operations
    - Session management (create, get, clear)
    - Automatic history trimming
    - Session timeout handling
    """
    
    def __init__(self, max_history: int = 10, session_timeout: int = 3600):
        """
        Initialize conversation memory.
        
        Args:
            max_history: Maximum number of interactions to store per session
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.max_history = max_history
        self.session_timeout = session_timeout
        
        # Session storage
        self._sessions: Dict[str, ConversationContext] = {}
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
    
    def create_session(self, session_id: str, persona: Persona) -> ConversationContext:
        """
        Create a new conversation session.
        
        Args:
            session_id: Unique session identifier
            persona: User persona
            
        Returns:
            New ConversationContext
        """
        with self._lock:
            context = ConversationContext(
                session_id=session_id,
                persona=persona,
                history=[],
                referenced_entities={},
                last_query_time=time.time(),
                created_at=time.time()
            )
            
            self._sessions[session_id] = context
            return context
    
    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        """
        Get conversation context for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationContext if found, None otherwise
        """
        with self._lock:
            return self._sessions.get(session_id)
    
    def get_or_create_session(self, session_id: str, persona: Persona) -> ConversationContext:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Session identifier
            persona: User persona
            
        Returns:
            ConversationContext
        """
        context = self.get_session(session_id)
        if context is None:
            context = self.create_session(session_id, persona)
        return context
    
    def add_interaction(
        self,
        session_id: str,
        query: str,
        response: str,
        intent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an interaction to session history.
        
        Args:
            session_id: Session identifier
            query: User query
            response: System response
            intent: Optional intent classification
            metadata: Optional metadata
        """
        with self._lock:
            if session_id not in self._sessions:
                # Session doesn't exist, can't add interaction
                return
            
            context = self._sessions[session_id]
            context.add_interaction(query, response, intent, metadata)
            
            # Trim history if exceeds max
            if len(context.history) > self.max_history:
                context.history = context.history[-self.max_history:]
    
    def get_history(self, session_id: str, n: Optional[int] = None) -> List[Interaction]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            n: Number of recent interactions (None = all)
            
        Returns:
            List of Interaction objects
        """
        with self._lock:
            if session_id not in self._sessions:
                return []
            
            context = self._sessions[session_id]
            if n is None:
                return context.history.copy()
            else:
                return context.get_recent_history(n)
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Get full conversation context for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationContext if found, None otherwise
        """
        return self.get_session(session_id)
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was cleared, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].clear_history()
                return True
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session completely.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def switch_persona(self, session_id: str, new_persona: Persona, clear_history: bool = True) -> bool:
        """
        Switch persona for a session.
        
        Args:
            session_id: Session identifier
            new_persona: New persona to switch to
            clear_history: Whether to clear conversation history (default: True)
            
        Returns:
            True if persona was switched, False if session not found
        """
        with self._lock:
            if session_id not in self._sessions:
                return False
            
            context = self._sessions[session_id]
            context.persona = new_persona
            
            if clear_history:
                context.clear_history()
            
            return True
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove sessions that have exceeded timeout.
        
        Returns:
            Number of sessions removed
        """
        with self._lock:
            current_time = time.time()
            expired_sessions = []
            
            for session_id, context in self._sessions.items():
                if context.last_query_time:
                    time_since_last_query = current_time - context.last_query_time
                    if time_since_last_query > self.session_timeout:
                        expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self._sessions[session_id]
            
            return len(expired_sessions)
    
    def get_all_sessions(self) -> List[SessionMetadata]:
        """
        Get metadata for all active sessions.
        
        Returns:
            List of SessionMetadata objects
        """
        with self._lock:
            metadata_list = []
            
            for session_id, context in self._sessions.items():
                metadata = SessionMetadata(
                    session_id=session_id,
                    persona=context.persona,
                    created_at=context.created_at,
                    last_active=context.last_query_time or context.created_at,
                    interaction_count=len(context.history)
                )
                metadata_list.append(metadata)
            
            return metadata_list
    
    def get_session_count(self) -> int:
        """
        Get number of active sessions.
        
        Returns:
            Number of sessions
        """
        with self._lock:
            return len(self._sessions)
    
    def get_total_interactions(self) -> int:
        """
        Get total number of interactions across all sessions.
        
        Returns:
            Total interaction count
        """
        with self._lock:
            return sum(len(context.history) for context in self._sessions.values())
    
    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Export session data to dictionary.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session data or None if not found
        """
        with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id].to_dict()
            return None
    
    def import_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Import session data from dictionary.
        
        Args:
            session_data: Dictionary with session data
            
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            with self._lock:
                context = ConversationContext.from_dict(session_data)
                self._sessions[context.session_id] = context
                return True
        except Exception:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get conversation memory statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            total_interactions = sum(len(context.history) for context in self._sessions.values())
            
            # Calculate average interactions per session
            avg_interactions = total_interactions / len(self._sessions) if self._sessions else 0
            
            return {
                "active_sessions": len(self._sessions),
                "total_interactions": total_interactions,
                "avg_interactions_per_session": avg_interactions,
                "max_history": self.max_history,
                "session_timeout": self.session_timeout
            }


def create_conversation_memory_from_config(config: Dict[str, Any]) -> ConversationMemory:
    """
    Create ConversationMemory instance from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured ConversationMemory instance
    """
    conversation_config = config.get("conversation", {})
    app_config = config.get("app", {})
    
    max_history = conversation_config.get("max_history", 10)
    session_timeout = app_config.get("session_timeout", 3600)
    
    return ConversationMemory(max_history=max_history, session_timeout=session_timeout)
