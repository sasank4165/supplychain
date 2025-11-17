"""Multi-agent orchestrator for supply chain application"""
import boto3
import json
from typing import Dict, Any, Optional, List
from config import Persona
from config_manager import ConfigurationManager
from agent_registry import AgentRegistry
from model_manager import ModelManager
from conversation_context_manager import ConversationContextManager
from access_controller import AccessController
from agents import SQLAgent, InventoryOptimizerAgent, LogisticsAgent, SupplierAnalyzerAgent

class SupplyChainOrchestrator:
    """Orchestrates multiple agents based on user persona and query intent
    
    Uses AgentRegistry for dynamic agent discovery and management instead of
    hardcoded agent instances. Supports configuration-driven agent initialization.
    Integrates ModelManager for centralized model selection and metrics.
    Integrates ConversationContextManager for conversation history management.
    Integrates MetricsCollector for comprehensive monitoring and analytics.
    """
    
    def __init__(self, region: str = None, config: Optional[ConfigurationManager] = None):
        """Initialize orchestrator with agent registry, model manager, context manager, and metrics collector
        
        Args:
            region: AWS region (if None, reads from environment or config)
            config: Optional ConfigurationManager instance. If not provided, will create one.
        """
        # Initialize configuration manager if not provided
        if config is None:
            try:
                import os
                environment = os.getenv("ENVIRONMENT", "dev")
                self.config = ConfigurationManager(environment=environment)
            except Exception as e:
                print(f"Warning: Failed to load configuration, using defaults: {e}")
                self.config = None
        else:
            self.config = config
        
        # Get region from config or parameter or environment
        if region is None:
            if self.config:
                region = self.config.get('environment.region', 'us-east-1')
            else:
                import os
                region = os.getenv('AWS_REGION', 'us-east-1')
        
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        
        # Initialize model manager
        if self.config:
            try:
                self.model_manager = ModelManager(self.config, region=region)
            except Exception as e:
                print(f"Warning: Failed to initialize ModelManager: {e}")
                self.model_manager = None
        else:
            self.model_manager = None
        
        # Initialize tool executor for async tool execution
        try:
            from tool_executor import ToolExecutor
            self.tool_executor = ToolExecutor(region=region, config=self.config)
        except Exception as e:
            print(f"Warning: Failed to initialize ToolExecutor: {e}")
            self.tool_executor = None
        
        # Initialize conversation context manager
        if self.config:
            try:
                self.context_manager = ConversationContextManager(
                    self.config,
                    region=region,
                    model_manager=self.model_manager
                )
            except Exception as e:
                print(f"Warning: Failed to initialize ConversationContextManager: {e}")
                self.context_manager = None
        else:
            self.context_manager = None
        
        # Initialize metrics collector
        try:
            from metrics_collector import MetricsCollector
            self.metrics_collector = MetricsCollector(region=region, config=self.config)
        except Exception as e:
            print(f"Warning: Failed to initialize MetricsCollector: {e}")
            self.metrics_collector = None
        
        # Initialize access controller
        try:
            self.access_controller = AccessController(region=region, config=self.config)
        except Exception as e:
            print(f"Warning: Failed to initialize AccessController: {e}")
            self.access_controller = None
        
        # Initialize agent registry with model manager
        if self.config:
            self.agent_registry = AgentRegistry(
                self.config, 
                auto_discover=True,
                model_manager=self.model_manager
            )
        else:
            # Fallback to hardcoded agents if config not available
            self.agent_registry = None
            self._init_hardcoded_agents(region)
    
    def _init_hardcoded_agents(self, region: str):
        """Fallback: Initialize agents with hardcoded configuration
        
        This method provides backward compatibility when configuration
        system is not available. Agents will use environment variables
        for configuration.
        """
        # Initialize specialist agents with tool executor
        # Region will be read from environment by agents if not provided
        warehouse_specialist = InventoryOptimizerAgent()
        field_specialist = LogisticsAgent()
        procurement_specialist = SupplierAnalyzerAgent()
        
        # Inject tool executor if available
        if hasattr(self, 'tool_executor') and self.tool_executor:
            warehouse_specialist.tool_executor = self.tool_executor
            field_specialist.tool_executor = self.tool_executor
            procurement_specialist.tool_executor = self.tool_executor
        
        self.agents = {
            Persona.WAREHOUSE_MANAGER: {
                "sql": SQLAgent("warehouse_manager"),
                "specialist": warehouse_specialist
            },
            Persona.FIELD_ENGINEER: {
                "sql": SQLAgent("field_engineer"),
                "specialist": field_specialist
            },
            Persona.PROCUREMENT_SPECIALIST: {
                "sql": SQLAgent("procurement_specialist"),
                "specialist": procurement_specialist
            }
        }
    
    def _get_agents_from_registry(self, persona: str) -> Dict[str, Any]:
        """Get agents for a persona from the registry
        
        Args:
            persona: Persona name
            
        Returns:
            Dictionary with 'sql' and 'specialist' agents
        """
        # Map persona to specialist agent
        persona_to_specialist = {
            "warehouse_manager": "inventory_optimizer",
            "field_engineer": "logistics_agent",
            "procurement_specialist": "supplier_analyzer"
        }
        
        # Get SQL agent for this persona
        # For SQL agent, we need to create persona-specific instances
        # Region will be read from environment by agent
        sql_agent = SQLAgent(persona)
        
        # Get specialist agent from registry
        specialist_name = persona_to_specialist.get(persona)
        specialist_agent = None
        
        if specialist_name:
            specialist_agent = self.agent_registry.get_agent(specialist_name)
            
            # If not found, try alternative names
            if not specialist_agent:
                # Try with _agent suffix
                specialist_agent = self.agent_registry.get_agent(f"{specialist_name}_agent")
        
        # Fallback to creating instances if not in registry
        if not specialist_agent:
            # Region will be read from environment by agents
            if persona == "warehouse_manager":
                specialist_agent = InventoryOptimizerAgent()
                # Inject tool executor if available
                if self.tool_executor:
                    specialist_agent.tool_executor = self.tool_executor
            elif persona == "field_engineer":
                specialist_agent = LogisticsAgent()
                # Inject tool executor if available
                if self.tool_executor:
                    specialist_agent.tool_executor = self.tool_executor
            elif persona == "procurement_specialist":
                specialist_agent = SupplierAnalyzerAgent()
                # Inject tool executor if available
                if self.tool_executor:
                    specialist_agent.tool_executor = self.tool_executor
        
        return {
            "sql": sql_agent,
            "specialist": specialist_agent
        }
    
    def classify_intent(self, query: str, persona: Persona) -> str:
        """Classify user intent to route to appropriate agent"""
        from config import BEDROCK_MODEL_ID
        
        system_prompt = """You are an intent classifier for a supply chain system.
        
Classify the user query into one of these categories:
- "sql_query": User wants to retrieve or analyze data (e.g., "show me", "what is", "list", "how many")
- "optimization": User wants recommendations or optimization (e.g., "optimize", "suggest", "recommend", "forecast")
- "both": Query requires both data retrieval and analysis

Return only one word: sql_query, optimization, or both"""
        
        messages = [{"role": "user", "content": [{"text": f"Query: {query}"}]}]
        
        response = self.bedrock_runtime.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=messages,
            system=[{"text": system_prompt}]
        )
        
        intent = response['output']['message']['content'][0]['text'].strip().lower()
        return intent
    
    def process_query(
        self, 
        query: str, 
        persona: str, 
        session_id: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Process user query by routing to appropriate agent(s) with RBAC, conversation context, and metrics tracking"""
        
        # Start timing for metrics
        import time
        start_time = time.time()
        
        # Extract user_id for metrics
        user_id = None
        if context:
            user_id = context.get('user_id') or context.get('username')
        
        # Validate persona
        try:
            persona_enum = Persona(persona)
        except ValueError:
            error_msg = f"Invalid persona: {persona}. Must be one of: warehouse_manager, field_engineer, procurement_specialist"
            
            # Record error metrics
            if self.metrics_collector:
                latency_ms = (time.time() - start_time) * 1000
                self.metrics_collector.record_error(
                    persona=persona,
                    agent="orchestrator",
                    error_type="invalid_persona",
                    error_message=error_msg,
                    context={'query': query, 'session_id': session_id}
                )
            
            return {
                "success": False,
                "error": error_msg
            }
        
        # Enhanced access control check using AccessController
        if context and self.access_controller:
            # Ensure persona is in context for access controller
            if 'persona' not in context:
                context['persona'] = persona
            
            # Authorize persona access
            if not self.access_controller.authorize(context, persona):
                error_msg = f"Access denied. You don't have permission to access {persona} features."
                
                # Record access denied metrics
                if self.metrics_collector:
                    latency_ms = (time.time() - start_time) * 1000
                    self.metrics_collector.record_error(
                        persona=persona,
                        agent="orchestrator",
                        error_type="access_denied",
                        error_message=error_msg,
                        context={'query': query, 'session_id': session_id, 'user_id': user_id}
                    )
                
                return {
                    "success": False,
                    "error": error_msg,
                    "status": 403
                }
        elif context and 'groups' in context:
            # Fallback to legacy RBAC if AccessController not available
            user_groups = context['groups']
            user_persona = context.get('persona')
            
            # Verify user's persona matches requested persona
            if user_persona != persona:
                return {
                    "success": False,
                    "error": f"Access denied. Your role is {user_persona}, but you're trying to access {persona} features.",
                    "status": 403
                }
            
            # Verify user has appropriate group membership
            expected_group = self._get_group_for_persona(persona)
            if expected_group not in user_groups:
                return {
                    "success": False,
                    "error": f"Access denied. You don't have the required group membership: {expected_group}",
                    "status": 403
                }
        
        # Store user message in conversation history
        if self.context_manager:
            self.context_manager.add_message(
                session_id=session_id,
                role='user',
                content=query,
                persona=persona,
                metadata={'timestamp': str(context.get('timestamp')) if context else None}
            )
        
        # Get conversation context for agents
        conversation_history = []
        if self.context_manager:
            conversation_history = self.context_manager.get_context(session_id)
        
        # Enhance context with conversation history
        enhanced_context = context or {}
        enhanced_context['conversation_history'] = conversation_history
        
        # Get agents for this persona
        if self.agent_registry:
            persona_agents = self._get_agents_from_registry(persona)
        else:
            persona_agents = self.agents[persona_enum]
        
        # Classify intent
        intent = self.classify_intent(query, persona_enum)
        
        results = {
            "persona": persona,
            "intent": intent,
            "query": query,
            "session_id": session_id
        }
        
        # Track token usage and tool executions for metrics
        total_token_count = 0
        tool_executions = []
        
        # Route to appropriate agent(s)
        try:
            if intent == "sql_query":
                sql_result = persona_agents["sql"].process_query(
                    query, session_id, enhanced_context, self.access_controller
                )
                results["sql_response"] = sql_result
                results["success"] = sql_result.get("success", False)
                
                # Track tokens and tools
                total_token_count += sql_result.get("token_count", 0)
                if sql_result.get("tools_used"):
                    tool_executions.extend(sql_result.get("tools_used", []))
                
                # Store assistant response
                if self.context_manager and sql_result.get("success"):
                    response_content = f"Retrieved {sql_result.get('row_count', 0)} rows"
                    self.context_manager.add_message(
                        session_id=session_id,
                        role='assistant',
                        content=response_content,
                        persona=persona,
                        metadata={'agent': 'sql_agent', 'intent': intent}
                    )
                
            elif intent == "optimization":
                specialist_result = persona_agents["specialist"].process_query(query, session_id, enhanced_context)
                results["specialist_response"] = specialist_result
                results["success"] = specialist_result.get("success", False)
                
                # Track tokens and tools
                total_token_count += specialist_result.get("token_count", 0)
                if specialist_result.get("tools_used"):
                    tool_executions.extend(specialist_result.get("tools_used", []))
                
                # Store assistant response
                if self.context_manager and specialist_result.get("success"):
                    response_content = specialist_result.get("response", "Optimization completed")
                    self.context_manager.add_message(
                        session_id=session_id,
                        role='assistant',
                        content=response_content,
                        persona=persona,
                        metadata={'agent': 'specialist_agent', 'intent': intent}
                    )
                
            else:  # both
                # First get data via SQL
                sql_result = persona_agents["sql"].process_query(
                    query, session_id, enhanced_context, self.access_controller
                )
                
                # Then analyze with specialist agent
                enhanced_context["sql_results"] = sql_result
                
                specialist_result = persona_agents["specialist"].process_query(
                    query, session_id, enhanced_context
                )
                
                results["sql_response"] = sql_result
                results["specialist_response"] = specialist_result
                results["success"] = sql_result.get("success", False) and specialist_result.get("success", False)
                
                # Track tokens and tools
                total_token_count += sql_result.get("token_count", 0)
                total_token_count += specialist_result.get("token_count", 0)
                if sql_result.get("tools_used"):
                    tool_executions.extend(sql_result.get("tools_used", []))
                if specialist_result.get("tools_used"):
                    tool_executions.extend(specialist_result.get("tools_used", []))
                
                # Store assistant response
                if self.context_manager and results.get("success"):
                    response_content = specialist_result.get("response", "Analysis completed")
                    self.context_manager.add_message(
                        session_id=session_id,
                        role='assistant',
                        content=response_content,
                        persona=persona,
                        metadata={'agent': 'both', 'intent': intent}
                    )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record successful query metrics
            if self.metrics_collector:
                agent_name = "sql_agent" if intent == "sql_query" else ("specialist_agent" if intent == "optimization" else "both")
                self.metrics_collector.record_query(
                    persona=persona,
                    agent=agent_name,
                    query=query,
                    latency_ms=latency_ms,
                    success=results.get("success", False),
                    token_count=total_token_count,
                    tool_executions=tool_executions,
                    user_id=user_id,
                    session_id=session_id,
                    intent=intent
                )
            
        except Exception as e:
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            # Record error metrics
            if self.metrics_collector:
                agent_name = "sql_agent" if intent == "sql_query" else ("specialist_agent" if intent == "optimization" else "both")
                self.metrics_collector.record_query(
                    persona=persona,
                    agent=agent_name,
                    query=query,
                    latency_ms=latency_ms,
                    success=False,
                    error_message=error_msg,
                    user_id=user_id,
                    session_id=session_id,
                    intent=intent
                )
                
                self.metrics_collector.record_error(
                    persona=persona,
                    agent=agent_name,
                    error_type="query_processing_error",
                    error_message=error_msg,
                    context={'query': query, 'session_id': session_id, 'intent': intent}
                )
            
            # Re-raise the exception
            raise
        
        return results
    
    def get_agent_capabilities(self, persona: str) -> Dict[str, Any]:
        """Get capabilities of agents for a given persona"""
        try:
            persona_enum = Persona(persona)
        except ValueError:
            return {"error": f"Invalid persona: {persona}"}
        
        # Get agents for this persona
        if self.agent_registry:
            persona_agents = self._get_agents_from_registry(persona)
        else:
            persona_agents = self.agents[persona_enum]
        
        result = {
            "persona": persona,
            "sql_agent": {
                "name": persona_agents["sql"].agent_name,
                "capabilities": "Natural language to SQL query conversion and execution"
            }
        }
        
        # Add specialist agent info if available
        if persona_agents.get("specialist"):
            specialist = persona_agents["specialist"]
            result["specialist_agent"] = {
                "name": specialist.agent_name,
                "tools": [tool["toolSpec"]["name"] for tool in specialist.get_tools()]
            }
        
        return result
    
    def get_all_registered_agents(self) -> Dict[str, Any]:
        """Get information about all registered agents in the registry
        
        Returns:
            Dictionary with agent registry information
        """
        if not self.agent_registry:
            return {"error": "Agent registry not initialized"}
        
        return {
            "registered_agents": self.agent_registry.list_agents(),
            "agent_count": len(self.agent_registry),
            "available_classes": self.agent_registry.list_available_agent_classes(),
            "capabilities": self.agent_registry.get_all_capabilities()
        }

    
    def _get_group_for_persona(self, persona: str) -> str:
        """Get Cognito group name for persona"""
        persona_to_group = {
            "warehouse_manager": "warehouse_managers",
            "field_engineer": "field_engineers",
            "procurement_specialist": "procurement_specialists"
        }
        return persona_to_group.get(persona, "")
    
    def validate_table_access(self, persona: str, table_name: str) -> bool:
        """Validate if persona has access to table"""
        from config import PERSONA_TABLE_ACCESS, Persona
        
        try:
            persona_enum = Persona(persona)
            allowed_tables = PERSONA_TABLE_ACCESS.get(persona_enum, [])
            return table_name in allowed_tables
        except:
            return False
    
    def get_conversation_history(self, session_id: str, max_messages: int = None) -> List[Dict[str, Any]]:
        """Get conversation history for a session
        
        Args:
            session_id: Session identifier
            max_messages: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        if not self.context_manager:
            return []
        
        return self.context_manager.get_context(session_id, max_messages)
    
    def clear_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """Clear conversation history for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with operation result
        """
        if not self.context_manager:
            return {"success": False, "error": "Context manager not initialized"}
        
        return self.context_manager.clear_context(session_id)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session statistics
        """
        if not self.context_manager:
            return {"error": "Context manager not initialized"}
        
        return self.context_manager.get_session_summary(session_id)

    def get_tool_execution_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics from ToolExecutor
        
        Returns:
            Dictionary with tool execution statistics
        """
        if not self.tool_executor:
            return {"error": "ToolExecutor not initialized"}
        
        return self.tool_executor.get_execution_stats()
    
    def get_tool_stats_by_name(self, tool_name: str) -> Dict[str, Any]:
        """Get statistics for a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with tool-specific statistics
        """
        if not self.tool_executor:
            return {"error": "ToolExecutor not initialized"}
        
        return self.tool_executor.get_tool_stats(tool_name)
    
    def get_metrics_stats(self) -> Dict[str, Any]:
        """Get metrics statistics from MetricsCollector
        
        Returns:
            Dictionary with metrics statistics
        """
        if not self.metrics_collector:
            return {"error": "MetricsCollector not initialized"}
        
        return self.metrics_collector.get_stats()
    
    def get_metrics_summary(
        self,
        start_time,
        end_time,
        persona: Optional[str] = None,
        agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get metrics summary from CloudWatch for a time period
        
        Args:
            start_time: Start of time period (datetime)
            end_time: End of time period (datetime)
            persona: Optional persona filter
            agent: Optional agent filter
            
        Returns:
            Dictionary with metrics summary from CloudWatch
        """
        if not self.metrics_collector:
            return {"error": "MetricsCollector not initialized"}
        
        return self.metrics_collector.get_metrics_summary(
            start_time=start_time,
            end_time=end_time,
            persona=persona,
            agent=agent
        )
    
    def flush_metrics(self):
        """Flush any buffered metrics to CloudWatch
        
        Call this before application shutdown to ensure all metrics are published.
        """
        if self.metrics_collector:
            self.metrics_collector.flush()
        
        if self.model_manager:
            self.model_manager.flush_metrics()
    
    def __del__(self):
        """Cleanup: flush metrics on orchestrator destruction"""
        try:
            self.flush_metrics()
        except:
            pass
