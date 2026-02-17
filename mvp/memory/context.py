"""
Conversation Context Data Models

Defines data structures for conversation memory and context.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class Persona(Enum):
    """User persona types."""
    WAREHOUSE_MANAGER = "Warehouse Manager"
    FIELD_ENGINEER = "Field Engineer"
    PROCUREMENT_SPECIALIST = "Procurement Specialist"


@dataclass
class Interaction:
    """Represents a single query-response interaction."""
    query: str
    response: str
    timestamp: float
    intent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "response": self.response,
            "timestamp": self.timestamp,
            "intent": self.intent,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Interaction':
        """Create from dictionary."""
        return cls(
            query=data["query"],
            response=data["response"],
            timestamp=data["timestamp"],
            intent=data.get("intent"),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConversationContext:
    """
    Context for conversation memory.
    
    Stores conversation history and referenced entities for a session.
    """
    session_id: str
    persona: Persona
    history: List[Interaction] = field(default_factory=list)
    referenced_entities: Dict[str, Any] = field(default_factory=dict)
    last_query_time: Optional[float] = None
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    
    def add_interaction(self, query: str, response: str, intent: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Add an interaction to the conversation history.
        
        Args:
            query: User query
            response: System response
            intent: Optional intent classification
            metadata: Optional metadata
        """
        interaction = Interaction(
            query=query,
            response=response,
            timestamp=datetime.now().timestamp(),
            intent=intent,
            metadata=metadata or {}
        )
        self.history.append(interaction)
        self.last_query_time = interaction.timestamp
    
    def get_recent_history(self, n: int = 10) -> List[Interaction]:
        """
        Get the n most recent interactions.
        
        Args:
            n: Number of recent interactions to return
            
        Returns:
            List of recent Interaction objects
        """
        return self.history[-n:] if len(self.history) > n else self.history
    
    def get_history_summary(self, n: int = 5) -> str:
        """
        Get a text summary of recent conversation history.
        
        Args:
            n: Number of recent interactions to include
            
        Returns:
            Formatted string summary
        """
        recent = self.get_recent_history(n)
        
        if not recent:
            return "No conversation history"
        
        summary_lines = ["Recent Conversation History:"]
        for i, interaction in enumerate(recent, 1):
            summary_lines.append(f"{i}. Q: {interaction.query[:100]}...")
            summary_lines.append(f"   A: {interaction.response[:100]}...")
        
        return "\n".join(summary_lines)
    
    def add_referenced_entity(self, entity_type: str, entity_id: str, entity_data: Any):
        """
        Add a referenced entity to the context.
        
        Args:
            entity_type: Type of entity (e.g., 'product', 'order', 'warehouse')
            entity_id: Unique identifier for the entity
            entity_data: Entity data
        """
        if entity_type not in self.referenced_entities:
            self.referenced_entities[entity_type] = {}
        
        self.referenced_entities[entity_type][entity_id] = entity_data
    
    def get_referenced_entity(self, entity_type: str, entity_id: str) -> Optional[Any]:
        """
        Get a referenced entity from the context.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            
        Returns:
            Entity data if found, None otherwise
        """
        if entity_type in self.referenced_entities:
            return self.referenced_entities[entity_type].get(entity_id)
        return None
    
    def clear_history(self):
        """Clear conversation history."""
        self.history.clear()
        self.referenced_entities.clear()
        self.last_query_time = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "persona": self.persona.value if isinstance(self.persona, Persona) else str(self.persona),
            "history": [interaction.to_dict() for interaction in self.history],
            "referenced_entities": self.referenced_entities,
            "last_query_time": self.last_query_time,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Create from dictionary."""
        # Parse persona
        persona_str = data["persona"]
        persona = None
        for p in Persona:
            if p.value == persona_str:
                persona = p
                break
        if persona is None:
            persona = Persona.WAREHOUSE_MANAGER  # Default
        
        # Parse history
        history = [Interaction.from_dict(i) for i in data.get("history", [])]
        
        return cls(
            session_id=data["session_id"],
            persona=persona,
            history=history,
            referenced_entities=data.get("referenced_entities", {}),
            last_query_time=data.get("last_query_time"),
            created_at=data.get("created_at", datetime.now().timestamp())
        )


@dataclass
class SessionMetadata:
    """Metadata about a conversation session."""
    session_id: str
    persona: Persona
    created_at: float
    last_active: float
    interaction_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "persona": self.persona.value if isinstance(self.persona, Persona) else str(self.persona),
            "created_at": self.created_at,
            "last_active": self.last_active,
            "interaction_count": self.interaction_count
        }
