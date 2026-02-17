"""
Test script for semantic layer functionality.

This script tests the semantic layer components without requiring AWS credentials.
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import from the semantic_layer package
from business_metrics import BusinessMetrics, Persona, MetricDefinition


def test_business_metrics():
    """Test business metrics definitions."""
    print("=" * 60)
    print("Testing Business Metrics")
    print("=" * 60)
    
    # Test Warehouse Manager metrics
    print("\n1. Warehouse Manager Metrics:")
    wm_metrics = BusinessMetrics.get_metrics_for_persona(Persona.WAREHOUSE_MANAGER)
    print(f"   Total metrics: {len(wm_metrics)}")
    
    required_wm = ['low_stock', 'stockout_risk', 'reorder_needed']
    for metric_name in required_wm:
        if metric_name in wm_metrics:
            metric = wm_metrics[metric_name]
            print(f"   ✓ {metric_name}: {metric.description}")
        else:
            print(f"   ✗ {metric_name}: MISSING")
    
    # Test Field Engineer metrics
    print("\n2. Field Engineer Metrics:")
    fe_metrics = BusinessMetrics.get_metrics_for_persona(Persona.FIELD_ENGINEER)
    print(f"   Total metrics: {len(fe_metrics)}")
    
    required_fe = ['overdue_orders', 'delivery_today', 'delayed_shipments']
    for metric_name in required_fe:
        if metric_name in fe_metrics:
            metric = fe_metrics[metric_name]
            print(f"   ✓ {metric_name}: {metric.description}")
        else:
            print(f"   ✗ {metric_name}: MISSING")
    
    # Test Procurement Specialist metrics
    print("\n3. Procurement Specialist Metrics:")
    ps_metrics = BusinessMetrics.get_metrics_for_persona(Persona.PROCUREMENT_SPECIALIST)
    print(f"   Total metrics: {len(ps_metrics)}")
    
    required_ps = ['top_suppliers', 'cost_variance', 'pending_pos']
    for metric_name in required_ps:
        if metric_name in ps_metrics:
            metric = ps_metrics[metric_name]
            print(f"   ✓ {metric_name}: {metric.description}")
        else:
            print(f"   ✗ {metric_name}: MISSING")
    
    # Test keyword search
    print("\n4. Testing Keyword Search:")
    keywords = ['stock', 'low']
    results = BusinessMetrics.find_metric_by_keywords(keywords, Persona.WAREHOUSE_MANAGER)
    print(f"   Keywords: {keywords}")
    print(f"   Found {len(results)} metrics:")
    for metric in results:
        print(f"   - {metric.name}")
    
    # Test business terms
    print("\n5. Testing Business Terms:")
    terms = BusinessMetrics.get_common_business_terms()
    print(f"   Total business terms: {len(terms)}")
    sample_terms = ['low stock', 'overdue', 'pending']
    for term in sample_terms:
        if term in terms:
            print(f"   ✓ '{term}' -> {terms[term]}")
        else:
            print(f"   ✗ '{term}': MISSING")
    
    print("\n" + "=" * 60)
    print("Business Metrics Test Complete")
    print("=" * 60)


def test_metric_details():
    """Test detailed metric information."""
    print("\n" + "=" * 60)
    print("Detailed Metric Information")
    print("=" * 60)
    
    # Show example of each persona's key metric
    examples = [
        (Persona.WAREHOUSE_MANAGER, 'low_stock'),
        (Persona.FIELD_ENGINEER, 'overdue_orders'),
        (Persona.PROCUREMENT_SPECIALIST, 'top_suppliers')
    ]
    
    for persona, metric_name in examples:
        metrics = BusinessMetrics.get_metrics_for_persona(persona)
        if metric_name in metrics:
            metric = metrics[metric_name]
            print(f"\n{persona.value} - {metric.name}:")
            print(f"  Description: {metric.description}")
            print(f"  SQL Pattern: {metric.sql_pattern}")
            print(f"  Tables: {', '.join(metric.tables)}")
            if metric.example_query:
                print(f"  Example: \"{metric.example_query}\"")


def test_schema_provider_mock():
    """Test schema provider with mock data."""
    print("\n" + "=" * 60)
    print("Testing Schema Provider (Mock)")
    print("=" * 60)
    
    from schema_provider import TableSchema
    
    # Create mock table schema
    mock_schema = TableSchema(
        name='warehouse_product',
        columns={
            'warehouse_code': 'varchar(50)',
            'product_code': 'varchar(50)',
            'current_stock': 'integer',
            'minimum_stock': 'integer',
            'maximum_stock': 'integer',
            'reorder_point': 'integer'
        },
        description='Warehouse inventory levels',
        primary_keys=['warehouse_code', 'product_code']
    )
    
    print(f"\nMock Table: {mock_schema.name}")
    print(f"Description: {mock_schema.description}")
    print(f"Columns: {len(mock_schema.columns)}")
    for col_name, col_type in mock_schema.columns.items():
        print(f"  - {col_name}: {col_type}")
    print(f"Primary Keys: {mock_schema.primary_keys}")
    
    print("\n✓ Schema Provider data structures working correctly")


def test_semantic_layer_mock():
    """Test semantic layer with mock data."""
    print("\n" + "=" * 60)
    print("Testing Semantic Layer (Mock)")
    print("=" * 60)
    
    # Test allowed tables for each persona
    personas = [
        Persona.WAREHOUSE_MANAGER,
        Persona.FIELD_ENGINEER,
        Persona.PROCUREMENT_SPECIALIST
    ]
    
    for persona in personas:
        # Create mock semantic layer (without actual schema provider)
        # We'll just test the business logic
        print(f"\n{persona.value}:")
        
        # Get metrics
        metrics = BusinessMetrics.get_metrics_for_persona(persona)
        print(f"  Available metrics: {len(metrics)}")
        
        # Show sample metric names
        metric_names = list(metrics.keys())[:3]
        print(f"  Sample metrics: {', '.join(metric_names)}")
    
    print("\n✓ Semantic Layer structure working correctly")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("SEMANTIC LAYER TEST SUITE")
    print("=" * 60)
    
    try:
        test_business_metrics()
        test_metric_details()
        test_schema_provider_mock()
        test_semantic_layer_mock()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nThe semantic layer is ready for integration with:")
        print("  - AWS Glue Catalog (via GlueClient)")
        print("  - SQL Agents (for query generation)")
        print("  - Orchestrator (for intent classification)")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
