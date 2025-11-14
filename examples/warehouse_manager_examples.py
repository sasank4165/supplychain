"""Example queries for Warehouse Manager persona"""
from orchestrator import SupplyChainOrchestrator
import json

def run_examples():
    """Run example queries for warehouse manager"""
    orchestrator = SupplyChainOrchestrator()
    persona = "warehouse_manager"
    session_id = "example_session_wm"
    
    examples = [
        # SQL Queries
        "Show me all products with stock below minimum levels in warehouse WH01",
        "What are the top 10 products by sales volume in the last 30 days?",
        "List all products from supplier SUP001 with their current stock levels",
        
        # Optimization Queries
        "Calculate optimal reorder points for warehouse WH01",
        "Forecast demand for product P12345 for the next 30 days",
        "Identify products at risk of stockout in the next 7 days",
        "Suggest optimal stock levels for warehouse WH01 with 95% service level",
        
        # Combined Queries
        "Show me current inventory and suggest reorder points for fast-moving products"
    ]
    
    print("=" * 80)
    print("WAREHOUSE MANAGER EXAMPLES")
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
                if sql_resp.get('results'):
                    print(f"Sample data: {json.dumps(sql_resp['results'][:2], indent=2)}")
        
        if result.get('specialist_response'):
            spec_resp = result['specialist_response']
            print(f"\nSpecialist Response: {spec_resp.get('response', 'N/A')}")
        
        print("\n")

if __name__ == "__main__":
    run_examples()
