"""Multi-agent orchestrator for supply chain application"""
import boto3
import json
from typing import Dict, Any, Optional, List
from agents import SQLAgent, InventoryOptimizerAgent, LogisticsAgent, SupplierAnalyzerAgent
from config import Persona

class SupplyChainOrchestrator:
    """Orchestrates multiple agents based on user persona and query intent"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        
        # Initialize agents for each persona
        self.agents = {
            Persona.WAREHOUSE_MANAGER: {
                "sql": SQLAgent("warehouse_manager", region),
                "specialist": InventoryOptimizerAgent(region)
            },
            Persona.FIELD_ENGINEER: {
                "sql": SQLAgent("field_engineer", region),
                "specialist": LogisticsAgent(region)
            },
            Persona.PROCUREMENT_SPECIALIST: {
                "sql": SQLAgent("procurement_specialist", region),
                "specialist": SupplierAnalyzerAgent(region)
            }
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
        """Process user query by routing to appropriate agent(s) with RBAC"""
        
        # Validate persona
        try:
            persona_enum = Persona(persona)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid persona: {persona}. Must be one of: warehouse_manager, field_engineer, procurement_specialist"
            }
        
        # Role-based access control check
        if context and 'groups' in context:
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
        
        # Get agents for this persona
        persona_agents = self.agents[persona_enum]
        
        # Classify intent
        intent = self.classify_intent(query, persona_enum)
        
        results = {
            "persona": persona,
            "intent": intent,
            "query": query,
            "session_id": session_id
        }
        
        # Route to appropriate agent(s)
        if intent == "sql_query":
            sql_result = persona_agents["sql"].process_query(query, session_id, context)
            results["sql_response"] = sql_result
            results["success"] = sql_result.get("success", False)
            
        elif intent == "optimization":
            specialist_result = persona_agents["specialist"].process_query(query, session_id, context)
            results["specialist_response"] = specialist_result
            results["success"] = specialist_result.get("success", False)
            
        else:  # both
            # First get data via SQL
            sql_result = persona_agents["sql"].process_query(query, session_id, context)
            
            # Then analyze with specialist agent
            enhanced_context = context or {}
            enhanced_context["sql_results"] = sql_result
            
            specialist_result = persona_agents["specialist"].process_query(
                query, session_id, enhanced_context
            )
            
            results["sql_response"] = sql_result
            results["specialist_response"] = specialist_result
            results["success"] = sql_result.get("success", False) and specialist_result.get("success", False)
        
        return results
    
    def get_agent_capabilities(self, persona: str) -> Dict[str, Any]:
        """Get capabilities of agents for a given persona"""
        try:
            persona_enum = Persona(persona)
        except ValueError:
            return {"error": f"Invalid persona: {persona}"}
        
        persona_agents = self.agents[persona_enum]
        
        return {
            "persona": persona,
            "sql_agent": {
                "name": persona_agents["sql"].agent_name,
                "capabilities": "Natural language to SQL query conversion and execution"
            },
            "specialist_agent": {
                "name": persona_agents["specialist"].agent_name,
                "tools": [tool["toolSpec"]["name"] for tool in persona_agents["specialist"].get_tools()]
            }
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
