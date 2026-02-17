"""
Example Usage of Query Orchestrator

Demonstrates how to initialize and use the query orchestrator with all components.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.intent_classifier import IntentClassifier, Intent
from orchestrator.agent_router import AgentRouter
from orchestrator.query_orchestrator import QueryOrchestrator
from aws.bedrock_client import BedrockClient
from aws.redshift_client import RedshiftClient
from aws.lambda_client import LambdaClient
from aws.glue_client import GlueClient
from agents.warehouse_sql_agent import WarehouseSQLAgent
from agents.field_sql_agent import FieldEngineerSQLAgent
from agents.procurement_sql_agent import ProcurementSQLAgent
from agents.inventory_agent import InventoryAgent
from agents.logistics_agent import LogisticsAgent
from agents.supplier_agent import SupplierAgent
from semantic_layer.semantic_layer import SemanticLayer
from semantic_layer.business_metrics import Persona
from utils.config_manager import ConfigManager
from utils.logger import setup_logger


def create_orchestrator():
    """
    Create and initialize a complete query orchestrator.
    
    Returns:
        QueryOrchestrator instance
    """
    # Load configuration
    config = ConfigManager()
    
    # Setup logger
    logger = setup_logger(
        name="orchestrator_example",
        log_file=config.get("logging.file", "logs/orchestrator_example.log"),
        level=config.get("logging.level", "INFO")
    )
    
    logger.info("Initializing query orchestrator...")
    
    # Initialize AWS clients
    bedrock_client = BedrockClient(
        region=config.get("aws.region"),
        model_id=config.get("aws.bedrock.model_id"),
        logger=logger
    )
    
    redshift_client = RedshiftClient(
        workgroup_name=config.get("aws.redshift.workgroup_name"),
        database=config.get("aws.redshift.database"),
        region=config.get("aws.region"),
        logger=logger
    )
    
    lambda_client = LambdaClient(
        region=config.get("aws.region"),
        logger=logger
    )
    
    glue_client = GlueClient(
        region=config.get("aws.region"),
        catalog_id=config.get("aws.glue.catalog_id"),
        database=config.get("aws.glue.database"),
        logger=logger
    )
    
    # Initialize semantic layers for each persona
    warehouse_semantic_layer = SemanticLayer(
        glue_client=glue_client,
        persona=Persona.WAREHOUSE_MANAGER,
        logger=logger
    )
    
    field_semantic_layer = SemanticLayer(
        glue_client=glue_client,
        persona=Persona.FIELD_ENGINEER,
        logger=logger
    )
    
    procurement_semantic_layer = SemanticLayer(
        glue_client=glue_client,
        persona=Persona.PROCUREMENT_SPECIALIST,
        logger=logger
    )
    
    # Initialize SQL agents
    warehouse_sql_agent = WarehouseSQLAgent(
        bedrock_client=bedrock_client,
        redshift_client=redshift_client,
        semantic_layer=warehouse_semantic_layer,
        logger=logger
    )
    
    field_sql_agent = FieldEngineerSQLAgent(
        bedrock_client=bedrock_client,
        redshift_client=redshift_client,
        semantic_layer=field_semantic_layer,
        logger=logger
    )
    
    procurement_sql_agent = ProcurementSQLAgent(
        bedrock_client=bedrock_client,
        redshift_client=redshift_client,
        semantic_layer=procurement_semantic_layer,
        logger=logger
    )
    
    # Initialize specialized agents
    inventory_agent = InventoryAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name=config.get("aws.lambda.inventory_function"),
        logger=logger
    )
    
    logistics_agent = LogisticsAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name=config.get("aws.lambda.logistics_function"),
        logger=logger
    )
    
    supplier_agent = SupplierAgent(
        bedrock_client=bedrock_client,
        lambda_client=lambda_client,
        lambda_function_name=config.get("aws.lambda.supplier_function"),
        logger=logger
    )
    
    # Create agent mappings
    sql_agents = {
        "Warehouse Manager": warehouse_sql_agent,
        "Field Engineer": field_sql_agent,
        "Procurement Specialist": procurement_sql_agent
    }
    
    specialized_agents = {
        "Warehouse Manager": inventory_agent,
        "Field Engineer": logistics_agent,
        "Procurement Specialist": supplier_agent
    }
    
    # Initialize orchestrator components
    intent_classifier = IntentClassifier(
        bedrock_client=bedrock_client,
        logger=logger
    )
    
    agent_router = AgentRouter(
        sql_agents=sql_agents,
        specialized_agents=specialized_agents,
        logger=logger
    )
    
    orchestrator = QueryOrchestrator(
        intent_classifier=intent_classifier,
        agent_router=agent_router,
        logger=logger
    )
    
    logger.info("Query orchestrator initialized successfully")
    
    return orchestrator


def example_queries():
    """
    Run example queries through the orchestrator.
    """
    # Create orchestrator
    orchestrator = create_orchestrator()
    
    # Example session ID
    session_id = "example_session_001"
    
    print("\n" + "="*80)
    print("QUERY ORCHESTRATOR EXAMPLE")
    print("="*80 + "\n")
    
    # Example 1: SQL Query for Warehouse Manager
    print("\n--- Example 1: SQL Query (Warehouse Manager) ---")
    query1 = "Show me all products with low stock at warehouse WH001"
    persona1 = "Warehouse Manager"
    
    print(f"Query: {query1}")
    print(f"Persona: {persona1}")
    
    response1 = orchestrator.process_query(query1, persona1, session_id)
    
    print(f"Intent: {response1.intent.value}")
    print(f"Success: {response1.agent_response.success}")
    print(f"Execution Time: {response1.total_execution_time:.2f}s")
    print(f"Response: {response1.agent_response.content[:200]}...")
    
    # Example 2: Optimization Query for Warehouse Manager
    print("\n--- Example 2: Optimization Query (Warehouse Manager) ---")
    query2 = "Calculate reorder points for all products at warehouse WH001"
    persona2 = "Warehouse Manager"
    
    print(f"Query: {query2}")
    print(f"Persona: {persona2}")
    
    response2 = orchestrator.process_query(query2, persona2, session_id)
    
    print(f"Intent: {response2.intent.value}")
    print(f"Success: {response2.agent_response.success}")
    print(f"Execution Time: {response2.total_execution_time:.2f}s")
    print(f"Response: {response2.agent_response.content[:200]}...")
    
    # Example 3: Hybrid Query for Field Engineer
    print("\n--- Example 3: Hybrid Query (Field Engineer) ---")
    query3 = "Show me delayed orders and optimize delivery routes for them"
    persona3 = "Field Engineer"
    
    print(f"Query: {query3}")
    print(f"Persona: {persona3}")
    
    response3 = orchestrator.process_query(query3, persona3, session_id)
    
    print(f"Intent: {response3.intent.value}")
    print(f"Success: {response3.agent_response.success}")
    print(f"Execution Time: {response3.total_execution_time:.2f}s")
    print(f"Response: {response3.agent_response.content[:200]}...")
    
    # Example 4: SQL Query for Procurement Specialist
    print("\n--- Example 4: SQL Query (Procurement Specialist) ---")
    query4 = "List all suppliers and their total purchase order values"
    persona4 = "Procurement Specialist"
    
    print(f"Query: {query4}")
    print(f"Persona: {persona4}")
    
    response4 = orchestrator.process_query(query4, persona4, session_id)
    
    print(f"Intent: {response4.intent.value}")
    print(f"Success: {response4.agent_response.success}")
    print(f"Execution Time: {response4.total_execution_time:.2f}s")
    print(f"Response: {response4.agent_response.content[:200]}...")
    
    # Show conversation history
    print("\n--- Conversation History ---")
    history = orchestrator.get_session_history(session_id)
    print(f"Total interactions: {len(history)}")
    for i, interaction in enumerate(history, 1):
        print(f"{i}. Query: {interaction['query'][:50]}...")
    
    # Clear session
    orchestrator.clear_session(session_id)
    print(f"\nSession {session_id} cleared")
    
    print("\n" + "="*80)
    print("EXAMPLE COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        example_queries()
    except Exception as e:
        print(f"Error running example: {e}")
        import traceback
        traceback.print_exc()
