"""
Agent Router

Routes queries to appropriate agents based on persona and intent.
Manages SQL agents and specialized agents for each persona.
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.intent_classifier import Intent
from agents.base_agent import AgentResponse
from agents.sql_agent import SQLAgent
from agents.inventory_agent import InventoryAgent
from agents.logistics_agent import LogisticsAgent
from agents.supplier_agent import SupplierAgent
from semantic_layer.business_metrics import Persona


class AgentRouter:
    """
    Routes queries to appropriate agents based on persona and intent.
    
    Manages:
    - 3 SQL agents (one per persona)
    - 3 specialized agents (Inventory, Logistics, Supplier)
    """
    
    def __init__(
        self,
        sql_agents: Dict[str, SQLAgent],
        specialized_agents: Dict[str, Any],
        logger=None
    ):
        """
        Initialize agent router.
        
        Args:
            sql_agents: Dictionary mapping persona names to SQL agents
                       e.g., {"Warehouse Manager": warehouse_sql_agent, ...}
            specialized_agents: Dictionary mapping persona names to specialized agents
                               e.g., {"Warehouse Manager": inventory_agent, ...}
            logger: Optional logger instance
        """
        self.sql_agents = sql_agents
        self.specialized_agents = specialized_agents
        self.logger = logger
        
        self._log_info(f"Initialized with {len(sql_agents)} SQL agents and {len(specialized_agents)} specialized agents")
    
    def route(
        self,
        query: str,
        intent: Intent,
        persona: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Route query to appropriate agent(s) based on intent and persona.
        
        Args:
            query: User's natural language query
            intent: Classified intent (SQL_QUERY, OPTIMIZATION, or HYBRID)
            persona: User's persona
            context: Optional conversation context
            
        Returns:
            AgentResponse with results
        """
        self._log_info(f"Routing query for persona '{persona}' with intent '{intent.value}'")
        
        try:
            if intent == Intent.SQL_QUERY:
                return self._route_to_sql_agent(query, persona, context)
            
            elif intent == Intent.OPTIMIZATION:
                return self._route_to_specialized_agent(query, persona, context)
            
            elif intent == Intent.HYBRID:
                return self._route_to_hybrid(query, persona, context)
            
            else:
                # Unknown intent, default to SQL
                self._log_warning(f"Unknown intent: {intent}. Defaulting to SQL agent")
                return self._route_to_sql_agent(query, persona, context)
                
        except Exception as e:
            self._log_error(f"Routing failed: {e}")
            # Return error response
            return AgentResponse(
                success=False,
                content=f"Failed to process query: {str(e)}",
                data=None,
                execution_time=0.0,
                metadata={"error": str(e)}
            )
    
    def _route_to_sql_agent(
        self,
        query: str,
        persona: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Route query to SQL agent for data retrieval.
        
        Args:
            query: User's query
            persona: User's persona
            context: Optional conversation context
            
        Returns:
            AgentResponse from SQL agent
        """
        self._log_info(f"Routing to SQL agent for persona: {persona}")
        
        # Get SQL agent for persona
        sql_agent = self.sql_agents.get(persona)
        
        if not sql_agent:
            self._log_error(f"No SQL agent found for persona: {persona}")
            return AgentResponse(
                success=False,
                content=f"No SQL agent configured for persona: {persona}",
                data=None,
                execution_time=0.0,
                metadata={"error": "agent_not_found"}
            )
        
        # Process query with SQL agent
        return sql_agent.process_query(query, context)
    
    def _route_to_specialized_agent(
        self,
        query: str,
        persona: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Route query to specialized agent for optimization/analysis.
        
        Args:
            query: User's query
            persona: User's persona
            context: Optional conversation context
            
        Returns:
            AgentResponse from specialized agent
        """
        self._log_info(f"Routing to specialized agent for persona: {persona}")
        
        # Get specialized agent for persona
        specialized_agent = self.specialized_agents.get(persona)
        
        if not specialized_agent:
            self._log_error(f"No specialized agent found for persona: {persona}")
            return AgentResponse(
                success=False,
                content=f"No specialized agent configured for persona: {persona}",
                data=None,
                execution_time=0.0,
                metadata={"error": "agent_not_found"}
            )
        
        # Process request with specialized agent
        return specialized_agent.process_request(query, context)
    
    def _route_to_hybrid(
        self,
        query: str,
        persona: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Route query to both SQL and specialized agents for hybrid processing.
        
        For hybrid queries, we:
        1. First execute SQL agent to get data
        2. Then pass results to specialized agent for analysis
        
        Args:
            query: User's query
            persona: User's persona
            context: Optional conversation context
            
        Returns:
            Combined AgentResponse
        """
        self._log_info(f"Routing to hybrid processing for persona: {persona}")
        
        # Get both agents
        sql_agent = self.sql_agents.get(persona)
        specialized_agent = self.specialized_agents.get(persona)
        
        if not sql_agent or not specialized_agent:
            self._log_error(f"Missing agents for hybrid processing. SQL: {sql_agent is not None}, Specialized: {specialized_agent is not None}")
            return AgentResponse(
                success=False,
                content="Cannot process hybrid query: missing required agents",
                data=None,
                execution_time=0.0,
                metadata={"error": "agents_not_found"}
            )
        
        # Step 1: Execute SQL query to get data
        self._log_info("Step 1: Executing SQL agent")
        sql_response = sql_agent.process_query(query, context)
        
        if not sql_response.success:
            self._log_error("SQL agent failed in hybrid processing")
            return sql_response
        
        # Step 2: Pass SQL results to specialized agent for analysis
        self._log_info("Step 2: Executing specialized agent with SQL results")
        
        # Build enhanced query with SQL results context
        enhanced_query = self._build_enhanced_query(query, sql_response)
        
        # Update context with SQL results
        enhanced_context = context.copy() if context else {}
        enhanced_context["sql_results"] = sql_response.data
        
        specialized_response = specialized_agent.process_request(enhanced_query, enhanced_context)
        
        if not specialized_response.success:
            self._log_error("Specialized agent failed in hybrid processing")
            return specialized_response
        
        # Combine responses
        combined_response = self._combine_responses(sql_response, specialized_response)
        
        self._log_info("Hybrid processing completed successfully")
        
        return combined_response
    
    def _build_enhanced_query(self, original_query: str, sql_response: AgentResponse) -> str:
        """
        Build enhanced query with SQL results for specialized agent.
        
        Args:
            original_query: Original user query
            sql_response: Response from SQL agent
            
        Returns:
            Enhanced query string
        """
        # Extract SQL results summary
        sql_data = sql_response.data
        
        if hasattr(sql_data, 'results') and sql_data.results:
            row_count = sql_data.results.row_count
            summary = f"Based on the SQL query results ({row_count} rows), {original_query}"
        else:
            summary = f"Based on the data retrieved, {original_query}"
        
        return summary
    
    def _combine_responses(
        self,
        sql_response: AgentResponse,
        specialized_response: AgentResponse
    ) -> AgentResponse:
        """
        Combine SQL and specialized agent responses.
        
        Args:
            sql_response: Response from SQL agent
            specialized_response: Response from specialized agent
            
        Returns:
            Combined AgentResponse
        """
        # Combine content
        combined_content = f"{sql_response.content}\n\n{specialized_response.content}"
        
        # Combine data
        combined_data = {
            "sql_results": sql_response.data,
            "optimization_results": specialized_response.data
        }
        
        # Combine execution times
        total_execution_time = sql_response.execution_time + specialized_response.execution_time
        
        # Combine metadata
        combined_metadata = {
            "intent": "HYBRID",
            "sql_metadata": sql_response.metadata,
            "optimization_metadata": specialized_response.metadata
        }
        
        return AgentResponse(
            success=True,
            content=combined_content,
            data=combined_data,
            execution_time=total_execution_time,
            metadata=combined_metadata
        )
    
    def get_available_personas(self) -> list:
        """
        Get list of available personas.
        
        Returns:
            List of persona names
        """
        return list(self.sql_agents.keys())
    
    def validate_persona(self, persona: str) -> bool:
        """
        Validate that a persona is supported.
        
        Args:
            persona: Persona name to validate
            
        Returns:
            True if persona is valid, False otherwise
        """
        return persona in self.sql_agents
    
    def _log_info(self, message: str):
        """Log info message."""
        if self.logger:
            self.logger.info(f"[AgentRouter] {message}")
    
    def _log_warning(self, message: str):
        """Log warning message."""
        if self.logger:
            self.logger.warning(f"[AgentRouter] {message}")
    
    def _log_error(self, message: str):
        """Log error message."""
        if self.logger:
            self.logger.error(f"[AgentRouter] {message}")
