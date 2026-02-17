"""
Example Usage of SQL Agents

Demonstrates how to use the SQL agents with real AWS services.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import WarehouseSQLAgent, FieldEngineerSQLAgent, ProcurementSQLAgent
from agents import ConversationContext
from aws.bedrock_client import BedrockClient
from aws.redshift_client import RedshiftClient
from aws.glue_client import GlueClient
from semantic_layer.semantic_layer import SemanticLayer
from semantic_layer.schema_provider import SchemaProvider
from semantic_layer.business_metrics import Persona
from utils.config_manager import ConfigManager
import logging


def setup_logging():
    """Set up logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def initialize_clients(config: ConfigManager):
    """
    Initialize AWS clients from configuration.
    
    Args:
        config: ConfigManager instance
        
    Returns:
        Tuple of (bedrock_client, redshift_client, glue_client)
    """
    # Initialize Bedrock client
    bedrock_config = config.get_bedrock_config()
    bedrock_client = BedrockClient(
        region=config.get_aws_region(),
        model_id=bedrock_config['model_id'],
        max_tokens=bedrock_config.get('max_tokens', 4096),
        temperature=bedrock_config.get('temperature', 0.0)
    )
    
    # Initialize Redshift client
    redshift_config = config.get_redshift_config()
    redshift_client = RedshiftClient(
        region=config.get_aws_region(),
        workgroup_name=redshift_config['workgroup_name'],
        database=redshift_config['database'],
        timeout=redshift_config.get('data_api_timeout', 30)
    )
    
    # Initialize Glue client
    glue_config = config.get_glue_config()
    glue_client = GlueClient(
        region=config.get_aws_region(),
        database=glue_config['database'],
        catalog_id=glue_config.get('catalog_id')
    )
    
    return bedrock_client, redshift_client, glue_client


def create_agent(persona: Persona, bedrock_client, redshift_client, glue_client):
    """
    Create a SQL agent for the specified persona.
    
    Args:
        persona: User persona
        bedrock_client: Bedrock client
        redshift_client: Redshift client
        glue_client: Glue client
        
    Returns:
        SQL agent instance
    """
    # Create schema provider and semantic layer
    schema_provider = SchemaProvider(glue_client)
    semantic_layer = SemanticLayer(schema_provider, persona)
    
    # Create appropriate agent based on persona
    if persona == Persona.WAREHOUSE_MANAGER:
        return WarehouseSQLAgent(
            bedrock_client=bedrock_client,
            redshift_client=redshift_client,
            semantic_layer=semantic_layer
        )
    elif persona == Persona.FIELD_ENGINEER:
        return FieldEngineerSQLAgent(
            bedrock_client=bedrock_client,
            redshift_client=redshift_client,
            semantic_layer=semantic_layer
        )
    elif persona == Persona.PROCUREMENT_SPECIALIST:
        return ProcurementSQLAgent(
            bedrock_client=bedrock_client,
            redshift_client=redshift_client,
            semantic_layer=semantic_layer
        )
    else:
        raise ValueError(f"Unknown persona: {persona}")


def example_warehouse_manager_queries(agent):
    """
    Example queries for Warehouse Manager persona.
    
    Args:
        agent: WarehouseSQLAgent instance
    """
    print("\n" + "=" * 60)
    print("WAREHOUSE MANAGER QUERIES")
    print("=" * 60)
    
    queries = [
        "Show me all products with low stock",
        "What's the current stock level for product ABC123?",
        "Which products need reordering in warehouse WH001?",
        "Show me the top 10 products by stock value",
        "List all products with stock below minimum level"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        
        response = agent.process_query(query)
        
        if response.success:
            print(f"✓ Success (took {response.execution_time:.2f}s)")
            print(f"SQL: {response.metadata.get('sql', 'N/A')}")
            print(f"Rows: {response.metadata.get('row_count', 0)}")
            print(f"\nResponse:\n{response.content}")
        else:
            print(f"✗ Error: {response.error}")


def example_field_engineer_queries(agent):
    """
    Example queries for Field Engineer persona.
    
    Args:
        agent: FieldEngineerSQLAgent instance
    """
    print("\n" + "=" * 60)
    print("FIELD ENGINEER QUERIES")
    print("=" * 60)
    
    queries = [
        "Show me today's deliveries",
        "Which orders are overdue?",
        "Show me orders for delivery area Downtown",
        "What's the status of order SO-2024-001?",
        "List all pending orders"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        
        response = agent.process_query(query)
        
        if response.success:
            print(f"✓ Success (took {response.execution_time:.2f}s)")
            print(f"SQL: {response.metadata.get('sql', 'N/A')}")
            print(f"Rows: {response.metadata.get('row_count', 0)}")
            print(f"\nResponse:\n{response.content}")
        else:
            print(f"✗ Error: {response.error}")


def example_procurement_specialist_queries(agent):
    """
    Example queries for Procurement Specialist persona.
    
    Args:
        agent: ProcurementSQLAgent instance
    """
    print("\n" + "=" * 60)
    print("PROCUREMENT SPECIALIST QUERIES")
    print("=" * 60)
    
    queries = [
        "Show me pending purchase orders",
        "What's the total spend with supplier SUP001?",
        "Which suppliers have the best on-time delivery?",
        "Show me overdue purchase orders",
        "Compare costs for product group Electronics across suppliers"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        
        response = agent.process_query(query)
        
        if response.success:
            print(f"✓ Success (took {response.execution_time:.2f}s)")
            print(f"SQL: {response.metadata.get('sql', 'N/A')}")
            print(f"Rows: {response.metadata.get('row_count', 0)}")
            print(f"\nResponse:\n{response.content}")
        else:
            print(f"✗ Error: {response.error}")


def example_with_conversation_context(agent):
    """
    Example of using conversation context for follow-up queries.
    
    Args:
        agent: SQL agent instance
    """
    print("\n" + "=" * 60)
    print("CONVERSATION CONTEXT EXAMPLE")
    print("=" * 60)
    
    # Create conversation context
    context = ConversationContext(
        session_id="example_session",
        persona=agent.get_persona(),
        history=[],
        referenced_entities={}
    )
    
    # First query
    query1 = "Show me products in warehouse WH001"
    print(f"\nQuery 1: {query1}")
    print("-" * 60)
    
    response1 = agent.process_query(query1, context)
    
    if response1.success:
        print(f"✓ Success")
        print(f"SQL: {response1.metadata.get('sql', 'N/A')}")
        
        # Add to context
        context.history.append({
            "query": query1,
            "response": response1.content
        })
        context.referenced_entities["warehouse"] = "WH001"
    
    # Follow-up query (should use context)
    query2 = "Show me the low stock items there"
    print(f"\nQuery 2 (follow-up): {query2}")
    print("-" * 60)
    
    response2 = agent.process_query(query2, context)
    
    if response2.success:
        print(f"✓ Success")
        print(f"SQL: {response2.metadata.get('sql', 'N/A')}")
        print(f"\nResponse:\n{response2.content}")


def main():
    """Main example function."""
    setup_logging()
    
    print("SQL Agents Example Usage")
    print("=" * 60)
    
    try:
        # Load configuration
        print("\nLoading configuration...")
        config = ConfigManager("config.yaml")
        
        # Initialize clients
        print("Initializing AWS clients...")
        bedrock_client, redshift_client, glue_client = initialize_clients(config)
        
        # Test connection
        print("Testing Redshift connection...")
        if redshift_client.test_connection():
            print("✓ Redshift connection successful")
        
        # Example 1: Warehouse Manager
        print("\n\nExample 1: Warehouse Manager Agent")
        warehouse_agent = create_agent(
            Persona.WAREHOUSE_MANAGER,
            bedrock_client,
            redshift_client,
            glue_client
        )
        example_warehouse_manager_queries(warehouse_agent)
        
        # Example 2: Field Engineer
        print("\n\nExample 2: Field Engineer Agent")
        field_agent = create_agent(
            Persona.FIELD_ENGINEER,
            bedrock_client,
            redshift_client,
            glue_client
        )
        example_field_engineer_queries(field_agent)
        
        # Example 3: Procurement Specialist
        print("\n\nExample 3: Procurement Specialist Agent")
        procurement_agent = create_agent(
            Persona.PROCUREMENT_SPECIALIST,
            bedrock_client,
            redshift_client,
            glue_client
        )
        example_procurement_specialist_queries(procurement_agent)
        
        # Example 4: Conversation Context
        print("\n\nExample 4: Using Conversation Context")
        example_with_conversation_context(warehouse_agent)
        
        print("\n" + "=" * 60)
        print("Examples completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Note: This example requires:
    # 1. Valid AWS credentials configured
    # 2. config.yaml file with proper settings
    # 3. Redshift Serverless workgroup running
    # 4. Glue Catalog database with tables
    # 5. Sample data loaded
    
    print("Note: This example requires AWS resources to be set up.")
    print("Make sure you have:")
    print("  - AWS credentials configured")
    print("  - config.yaml with proper settings")
    print("  - Redshift Serverless running")
    print("  - Glue Catalog database created")
    print("  - Sample data loaded")
    print("\nProceed? (y/n): ", end="")
    
    response = input().strip().lower()
    if response == 'y':
        main()
    else:
        print("Skipping example execution.")
