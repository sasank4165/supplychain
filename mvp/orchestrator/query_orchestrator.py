"""
Query Orchestrator

Main orchestrator that coordinates intent classification and agent routing.
Integrates SQL agents and specialized agents to process user queries.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import time
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.intent_classifier import IntentClassifier, Intent
from orchestrator.agent_router import AgentRouter
from agents.base_agent import AgentResponse
from agents.sql_agent import SQLAgent
from aws.bedrock_client import BedrockClient
from semantic_layer.business_metrics import Persona
from cache.query_cache import QueryCache
from memory.context import ConversationContext


@dataclass
class QueryResponse:
    """Response from query orchestrator."""
    query: str
    persona: str
    intent: Intent
    agent_response: AgentResponse
    total_execution_time: float
    cached: bool = False


class QueryOrchestrator:
    """
    Main orchestrator for query processing.
    
    Coordinates:
    1. Intent classification (SQL_QUERY, OPTIMIZATION, HYBRID)
    2. Agent routing based on persona and intent
    3. Session management
    4. Response formatting
    """
    
    def __init__(
        self,
        intent_classifier: IntentClassifier,
        agent_router: AgentRouter,
        query_cache: Optional[QueryCache] = None,
        logger=None
    ):
        """
        Initialize query orchestrator.
        
        Args:
            intent_classifier: IntentClassifier instance
            agent_router: AgentRouter instance
            query_cache: Optional QueryCache instance for caching results
            logger: Optional logger instance
        """
        self.intent_classifier = intent_classifier
        self.agent_router = agent_router
        self.query_cache = query_cache
        self.logger = logger
        
        # Session storage for conversation contexts
        self.sessions: Dict[str, ConversationContext] = {}
        
        self._log_info("Query orchestrator initialized")
        if self.query_cache:
            self._log_info("Query caching enabled")
    
    def process_query(
        self,
        query: str,
        persona: str,
        session_id: str
    ) -> QueryResponse:
        """
        Process a user query end-to-end.
        
        Args:
            query: User's natural language query
            persona: User's persona (Warehouse Manager, Field Engineer, Procurement Specialist)
            session_id: Session identifier for conversation memory
            
        Returns:
            QueryResponse with results
        """
        start_time = time.time()
        
        try:
            self._log_info(f"Processing query for persona '{persona}', session '{session_id}': {query[:100]}...")
            
            # Validate persona
            if not self.agent_router.validate_persona(persona):
                self._log_error(f"Invalid persona: {persona}")
                return self._create_error_response(
                    query=query,
                    persona=persona,
                    error_message=f"Invalid persona: {persona}. Available personas: {', '.join(self.agent_router.get_available_personas())}",
                    execution_time=time.time() - start_time
                )
            
            # Check cache if enabled
            if self.query_cache:
                cache_key = QueryCache.generate_cache_key(query, persona)
                cached_result = self.query_cache.get(cache_key)
                
                if cached_result is not None:
                    self._log_info(f"Cache hit for query: {query[:50]}...")
                    
                    # IMPORTANT: Still update context even for cached queries
                    context = self._get_or_create_context(session_id, persona)
                    self._update_context(session_id, query, cached_result.agent_response.content)
                    
                    # Return cached response
                    cached_response = cached_result
                    cached_response.cached = True
                    cached_response.total_execution_time = time.time() - start_time
                    return cached_response
                
                self._log_info("Cache miss, processing query")
            
            # Step 1: Get conversation context first
            context = self._get_or_create_context(session_id, persona)
            
            # Step 2: Classify intent (with context for follow-up questions)
            self._log_info("Step 1: Classifying intent")
            intent = self.classify_intent(query, persona, context)
            
            # Step 3: Route to appropriate agent(s)
            self._log_info(f"Step 2: Routing to agents (intent: {intent.value})")
            agent_response = self.route_to_agents(query, intent, persona, context)
            
            # Step 4: Update conversation context
            if agent_response.success:
                self._update_context(session_id, query, agent_response.content)
            
            # Calculate total execution time
            total_execution_time = time.time() - start_time
            
            self._log_info(f"Query processed successfully in {total_execution_time:.2f}s")
            
            # Create query response
            response = QueryResponse(
                query=query,
                persona=persona,
                intent=intent,
                agent_response=agent_response,
                total_execution_time=total_execution_time,
                cached=False
            )
            
            # Cache the response if caching is enabled and query was successful
            if self.query_cache and agent_response.success:
                cache_key = QueryCache.generate_cache_key(query, persona)
                self.query_cache.set(cache_key, response)
                self._log_info(f"Cached query result with key: {cache_key[:16]}...")
            
            return response
            
        except Exception as e:
            self._log_error(f"Query processing failed: {e}")
            return self._create_error_response(
                query=query,
                persona=persona,
                error_message=f"Query processing failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def classify_intent(self, query: str, persona: str, context=None) -> Intent:
        """
        Classify query intent.
        
        Args:
            query: User's query
            persona: User's persona
            context: Optional conversation context
            
        Returns:
            Intent enum value
        """
        return self.intent_classifier.classify(query, persona, context)
    
    def route_to_agents(
        self,
        query: str,
        intent: Intent,
        persona: str,
        context: Optional[ConversationContext] = None
    ) -> AgentResponse:
        """
        Route query to appropriate agent(s).
        
        Args:
            query: User's query
            intent: Classified intent
            persona: User's persona
            context: Optional conversation context
            
        Returns:
            AgentResponse from agent(s)
        """
        # Pass ConversationContext directly to agent router
        return self.agent_router.route(query, intent, persona, context)
    
    def _get_or_create_context(self, session_id: str, persona: str) -> ConversationContext:
        """
        Get existing conversation context or create new one.
        
        Args:
            session_id: Session identifier
            persona: User's persona
            
        Returns:
            ConversationContext for the session
        """
        if session_id not in self.sessions:
            # Create new context
            persona_enum = self._parse_persona(persona)
            self.sessions[session_id] = ConversationContext(
                session_id=session_id,
                persona=persona_enum,
                history=[],
                referenced_entities={},
                last_query_time=time.time()
            )
            self._log_info(f"Created new conversation context for session: {session_id}")
        else:
            # Update last query time
            self.sessions[session_id].last_query_time = time.time()
        
        return self.sessions[session_id]
    
    def _update_context(self, session_id: str, query: str, response: str):
        """
        Update conversation context with new interaction.
        
        Args:
            session_id: Session identifier
            query: User's query
            response: System response
        """
        if session_id in self.sessions:
            context = self.sessions[session_id]
            
            # Use the new add_interaction method from ConversationContext
            context.add_interaction(query, response)
            
            # Keep only last 10 interactions (trim if needed)
            if len(context.history) > 10:
                context.history = context.history[-10:]
            
            self._log_info(f"Updated context for session {session_id}. History size: {len(context.history)}")
    
    def clear_session(self, session_id: str):
        """
        Clear conversation context for a session.
        
        Args:
            session_id: Session identifier to clear
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._log_info(f"Cleared session: {session_id}")
    
    def get_session_history(self, session_id: str) -> list:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of interactions
        """
        if session_id in self.sessions:
            return self.sessions[session_id].history
        return []
    
    def switch_persona(self, session_id: str, new_persona: str):
        """
        Switch persona for a session (clears conversation history).
        
        Args:
            session_id: Session identifier
            new_persona: New persona to switch to
        """
        if session_id in self.sessions:
            persona_enum = self._parse_persona(new_persona)
            self.sessions[session_id].persona = persona_enum
            # Use the clear_history method from ConversationContext
            self.sessions[session_id].clear_history()
            self._log_info(f"Switched persona to {new_persona} for session {session_id}")
    
    def _parse_persona(self, persona_str: str) -> Persona:
        """
        Parse persona string to Persona enum.
        
        Args:
            persona_str: Persona string
            
        Returns:
            Persona enum value
        """
        persona_map = {
            "Warehouse Manager": Persona.WAREHOUSE_MANAGER,
            "Field Engineer": Persona.FIELD_ENGINEER,
            "Procurement Specialist": Persona.PROCUREMENT_SPECIALIST
        }
        
        return persona_map.get(persona_str, Persona.WAREHOUSE_MANAGER)
    
    def _create_error_response(
        self,
        query: str,
        persona: str,
        error_message: str,
        execution_time: float
    ) -> QueryResponse:
        """
        Create error query response.
        
        Args:
            query: Original query
            persona: User's persona
            error_message: Error message
            execution_time: Execution time
            
        Returns:
            QueryResponse with error
        """
        error_agent_response = AgentResponse(
            success=False,
            content=error_message,
            data=None,
            execution_time=execution_time,
            metadata={"error": True}
        )
        
        return QueryResponse(
            query=query,
            persona=persona,
            intent=Intent.SQL_QUERY,  # Default intent
            agent_response=error_agent_response,
            total_execution_time=execution_time,
            cached=False
        )
    
    def get_available_personas(self) -> list:
        """
        Get list of available personas.
        
        Returns:
            List of persona names
        """
        return self.agent_router.get_available_personas()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics or empty dict if caching disabled
        """
        if self.query_cache:
            return self.query_cache.get_stats()
        return {}
    
    def invalidate_cache(self, pattern: str = "") -> int:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Pattern to match (empty string = clear all)
            
        Returns:
            Number of entries invalidated
        """
        if self.query_cache:
            if pattern:
                return self.query_cache.invalidate(pattern)
            else:
                self.query_cache.clear()
                return -1  # Indicate all cleared
        return 0
    
    def _log_info(self, message: str):
        """Log info message."""
        if self.logger:
            self.logger.info(f"[QueryOrchestrator] {message}")
    
    def _log_warning(self, message: str):
        """Log warning message."""
        if self.logger:
            self.logger.warning(f"[QueryOrchestrator] {message}")
    
    def _log_error(self, message: str):
        """Log error message."""
        if self.logger:
            self.logger.error(f"[QueryOrchestrator] {message}")
