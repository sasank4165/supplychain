"""Example queries for Procurement Specialist persona"""
from orchestrator import SupplyChainOrchestrator
import json

def run_examples():
    """Run example queries for procurement specialist"""
    orchestrator = SupplyChainOrchestrator()
    persona = "procurement_specialist"
    session_id = "example_session_ps"
    
    examples = [
        # SQL Queries
        "Show me all purchase orders from supplier SUP001 in the last 90 days",
        "List all products from product group PG01 with their suppliers and costs",
        "What is the total value of open purchase orders?",
        
        # Supplier Analysis Queries
        "Analyze supplier performance for the last 90 days",
        "Compare costs across suppliers for product group PG01",
        "Identify cost savings opportunities with at least 5% savings potential",
        "Show purchase order trends for the last 6 months",
        
        # Combined Queries
        "Show me supplier performance and identify cost savings opportunities"
    ]
    
    print("=" * 80)
    print("PROCUREMENT SPECIALIST EXAMPLES")
    print("=" * 80)
    
    for i, query in enumerate(examples, 1):
        print(f"\n{'='*80}")
        print(f"Example {i}: {query}")
        print(f"{'='*80}\n")
        
        result = orchestrator.process_query(
            query=query,
            persona=persona,
            session_id=session_id
        )
        
        print(f"Intent: {result.get('intent')}")
        print(f"Success: {result.get('success')}")
        
        if result.get('sql_response'):
            sql_resp = result['sql_response']
            if sql_resp.get('success'):
                print(f"\nSQL Query: {sql_resp.get('sql')}")
                print(f"Rows returned: {sql_resp.get('row_count')}")
        
        if result.get('specialist_response'):
            spec_resp = result['specialist_response']
            print(f"\nSpecialist Response: {spec_resp.get('response', 'N/A')}")
        
        print("\n")

if __name__ == "__main__":
    run_examples()
