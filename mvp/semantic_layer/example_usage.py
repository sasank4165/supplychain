"""
Example usage of the Semantic Layer with AWS Glue Catalog.

This script demonstrates how to use the semantic layer in a real scenario.
Note: Requires AWS credentials and a configured Glue Catalog.
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from aws.glue_client import GlueClient
from semantic_layer.schema_provider import SchemaProvider
from semantic_layer.semantic_layer import SemanticLayer
from semantic_layer.business_metrics import Persona


def example_warehouse_manager():
    """Example: Warehouse Manager using semantic layer."""
    print("=" * 60)
    print("Example: Warehouse Manager")
    print("=" * 60)
    
    # Initialize components
    # Note: Update these values for your environment
    glue_client = GlueClient(
        region='us-east-1',
        database='supply_chain_catalog'
    )
    
    schema_provider = SchemaProvider(glue_client)
    semantic_layer = SemanticLayer(schema_provider, Persona.WAREHOUSE_MANAGER)
    
    # Example query
    query = "Show me products with low stock in warehouse WH001"
    
    print(f"\nUser Query: {query}")
    print("\n" + "-" * 60)
    
    # Enrich the query
    enriched = semantic_layer.enrich_query_context(query)
    
    print("\nEnriched Context:")
    print(f"  Relevant Tables: {enriched.relevant_tables}")
    print(f"  Relevant Metrics: {[m.name for m in enriched.relevant_metrics]}")
    print(f"  Business Terms: {enriched.business_terms}")
    
    # Generate full context for LLM
    print("\n" + "-" * 60)
    print("Full Context for LLM:")
    print("-" * 60)
    context = semantic_layer.generate_full_context_for_llm(query)
    print(context)


def example_field_engineer():
    """Example: Field Engineer using semantic layer."""
    print("\n" + "=" * 60)
    print("Example: Field Engineer")
    print("=" * 60)
    
    # Initialize components
    glue_client = GlueClient(
        region='us-east-1',
        database='supply_chain_catalog'
    )
    
    schema_provider = SchemaProvider(glue_client)
    semantic_layer = SemanticLayer(schema_provider, Persona.FIELD_ENGINEER)
    
    # Example query
    query = "What orders are overdue for delivery?"
    
    print(f"\nUser Query: {query}")
    print("\n" + "-" * 60)
    
    # Get allowed tables
    allowed_tables = semantic_layer.get_allowed_tables()
    print(f"\nAllowed Tables: {allowed_tables}")
    
    # Get business metrics
    metrics = semantic_layer.get_business_metrics()
    print(f"\nAvailable Metrics: {len(metrics)}")
    for name, metric in list(metrics.items())[:3]:
        print(f"  - {name}: {metric.description}")
    
    # Enrich the query
    enriched = semantic_layer.enrich_query_context(query)
    print(f"\nRelevant Metrics for Query: {[m.name for m in enriched.relevant_metrics]}")


def example_procurement_specialist():
    """Example: Procurement Specialist using semantic layer."""
    print("\n" + "=" * 60)
    print("Example: Procurement Specialist")
    print("=" * 60)
    
    # Initialize components
    glue_client = GlueClient(
        region='us-east-1',
        database='supply_chain_catalog'
    )
    
    schema_provider = SchemaProvider(glue_client)
    semantic_layer = SemanticLayer(schema_provider, Persona.PROCUREMENT_SPECIALIST)
    
    # Example query
    query = "Who are our top suppliers by order volume?"
    
    print(f"\nUser Query: {query}")
    print("\n" + "-" * 60)
    
    # Resolve business terms
    term = "top suppliers"
    resolved = semantic_layer.resolve_business_term(term)
    if resolved:
        print(f"\nBusiness Term '{term}' resolves to: {resolved}")
    
    # Get metric details
    metric = semantic_layer.business_metrics.get_metric('top_suppliers')
    if metric:
        print(f"\nMetric Details:")
        print(f"  Name: {metric.name}")
        print(f"  Description: {metric.description}")
        print(f"  SQL Pattern: {metric.sql_pattern}")
        print(f"  Tables: {', '.join(metric.tables)}")


def example_schema_exploration():
    """Example: Exploring schema metadata."""
    print("\n" + "=" * 60)
    print("Example: Schema Exploration")
    print("=" * 60)
    
    # Initialize components
    glue_client = GlueClient(
        region='us-east-1',
        database='supply_chain_catalog'
    )
    
    schema_provider = SchemaProvider(glue_client)
    
    # List all tables
    print("\nAvailable Tables:")
    tables = schema_provider.list_tables()
    for table in tables:
        print(f"  - {table}")
    
    # Get schema for a specific table
    print("\nWarehouse Product Schema:")
    schema = schema_provider.get_table_schema('warehouse_product')
    print(f"  Table: {schema.name}")
    print(f"  Columns: {len(schema.columns)}")
    for col_name, col_type in list(schema.columns.items())[:5]:
        print(f"    - {col_name}: {col_type}")
    
    # Find tables with a specific column
    print("\nTables with 'product_code' column:")
    tables_with_col = schema_provider.get_tables_with_column('product_code')
    for table in tables_with_col:
        print(f"  - {table}")
    
    # Get related tables
    print("\nTables related to 'sales_order_line':")
    related = schema_provider.get_related_tables('sales_order_line')
    for table in related:
        print(f"  - {table}")


def example_query_enrichment_workflow():
    """Example: Complete query enrichment workflow."""
    print("\n" + "=" * 60)
    print("Example: Complete Query Enrichment Workflow")
    print("=" * 60)
    
    # Initialize components
    glue_client = GlueClient(
        region='us-east-1',
        database='supply_chain_catalog'
    )
    
    schema_provider = SchemaProvider(glue_client)
    
    # Test queries for each persona
    test_cases = [
        (Persona.WAREHOUSE_MANAGER, "Show me products that need reordering"),
        (Persona.FIELD_ENGINEER, "What deliveries are scheduled for today?"),
        (Persona.PROCUREMENT_SPECIALIST, "Show me pending purchase orders")
    ]
    
    for persona, query in test_cases:
        print(f"\n{'-' * 60}")
        print(f"Persona: {persona.value}")
        print(f"Query: {query}")
        print(f"{'-' * 60}")
        
        semantic_layer = SemanticLayer(schema_provider, persona)
        enriched = semantic_layer.enrich_query_context(query)
        
        print(f"Relevant Tables: {enriched.relevant_tables}")
        print(f"Relevant Metrics: {[m.name for m in enriched.relevant_metrics]}")
        
        if enriched.business_terms:
            print(f"Business Terms Found:")
            for term, pattern in enriched.business_terms.items():
                print(f"  - '{term}' -> {pattern}")
        
        if enriched.suggested_joins:
            print(f"Suggested Joins:")
            for join in enriched.suggested_joins:
                print(f"  - {join}")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("SEMANTIC LAYER USAGE EXAMPLES")
    print("=" * 60)
    print("\nNote: These examples require:")
    print("  - AWS credentials configured")
    print("  - Glue Catalog database 'supply_chain_catalog'")
    print("  - Tables created in the catalog")
    print("\n")
    
    try:
        # Run examples
        # Uncomment the examples you want to run
        
        # example_warehouse_manager()
        # example_field_engineer()
        # example_procurement_specialist()
        # example_schema_exploration()
        # example_query_enrichment_workflow()
        
        print("\nTo run examples, uncomment the function calls in the main block.")
        print("Make sure you have AWS credentials and Glue Catalog configured.")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("  1. AWS credentials configured")
        print("  2. Glue Catalog database created")
        print("  3. Tables defined in the catalog")
        import traceback
        traceback.print_exc()
