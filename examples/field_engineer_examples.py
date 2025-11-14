"""Example queries for Field Engineer persona"""
from orchestrator import SupplyChainOrchestrator
import json

def run_examples():
    """Run example queries for field engineer"""
    orchestrator = SupplyChainOrchestrator()
    persona = "field_engineer"
    session_id = "example_session_fe"
    
    examples = [
        # SQL Queries
        "Show me all orders scheduled for delivery today",
        "List orders with status 'PICKING' or 'PACKED' from warehouse WH01",
        "What is the fulfillment status of order SO12345?",
        
        # Logistics Queries
        "Optimize delivery route for orders SO001, SO002, SO003 from warehouse WH01",
        "Check fulfillment status of order SO12345",
        "Identify all delayed orders in warehouse WH01",
        "Calculate warehouse capacity utilization for WH01",
        
        # Combined Queries
        "Show me delayed orders and suggest optimized delivery routes"
    ]
    
    print("=" * 80)
    print("FIELD ENGINEER EXAMPLES")
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
