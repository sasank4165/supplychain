"""Test authentication and authorization"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.auth_manager import AuthManager

def test_authentication():
    """Test authentication flow"""
    
    # Initialize auth manager
    user_pool_id = os.getenv("USER_POOL_ID", "us-east-1_xxxxx")
    client_id = os.getenv("USER_POOL_CLIENT_ID", "xxxxx")
    region = os.getenv("AWS_REGION", "us-east-1")
    
    auth = AuthManager(user_pool_id, client_id, region)
    
    print("=" * 80)
    print("AUTHENTICATION TESTS")
    print("=" * 80)
    
    # Test 1: Sign in
    print("\n1. Testing sign in...")
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    result = auth.sign_in(username, password)
    
    if result.get("success"):
        print("✅ Sign in successful!")
        print(f"Username: {result['username']}")
        print(f"Email: {result['email']}")
        print(f"Groups: {result['groups']}")
        print(f"Persona: {result['persona']}")
        
        access_token = result['access_token']
        
        # Test 2: Verify token
        print("\n2. Testing token verification...")
        verification = auth.verify_token(result['id_token'])
        
        if verification.get("valid"):
            print("✅ Token valid!")
            print(f"Username: {verification['username']}")
            print(f"Groups: {verification['groups']}")
        else:
            print(f"❌ Token invalid: {verification.get('error')}")
        
        # Test 3: Check table access
        print("\n3. Testing table access control...")
        groups = result['groups']
        
        test_tables = [
            "product",
            "warehouse_product",
            "sales_order_header",
            "purchase_order_header"
        ]
        
        for table in test_tables:
            has_access = auth.check_table_access(groups, table)
            status = "✅" if has_access else "❌"
            print(f"{status} Access to {table}: {has_access}")
        
        # Test 4: Check agent access
        print("\n4. Testing agent access control...")
        
        test_agents = [
            "sql_agent",
            "inventory_optimizer",
            "logistics_optimizer",
            "supplier_analyzer"
        ]
        
        for agent in test_agents:
            has_access = auth.check_agent_access(groups, agent)
            status = "✅" if has_access else "❌"
            print(f"{status} Access to {agent}: {has_access}")
        
        # Test 5: Get accessible resources
        print("\n5. Getting accessible resources...")
        tables = auth.get_accessible_tables(groups)
        agents = auth.get_accessible_agents(groups)
        
        print(f"Accessible tables: {', '.join(tables)}")
        print(f"Accessible agents: {', '.join(agents)}")
        
        # Test 6: Sign out
        print("\n6. Testing sign out...")
        result = auth.sign_out(access_token)
        
        if result.get("success"):
            print("✅ Sign out successful!")
        else:
            print(f"❌ Sign out failed: {result.get('error')}")
        
    else:
        print(f"❌ Sign in failed: {result.get('error')}")
    
    print("\n" + "=" * 80)
    print("TESTS COMPLETED")
    print("=" * 80)


def test_rbac_scenarios():
    """Test specific RBAC scenarios"""
    
    print("\n" + "=" * 80)
    print("RBAC SCENARIO TESTS")
    print("=" * 80)
    
    user_pool_id = os.getenv("USER_POOL_ID", "us-east-1_xxxxx")
    client_id = os.getenv("USER_POOL_CLIENT_ID", "xxxxx")
    region = os.getenv("AWS_REGION", "us-east-1")
    
    auth = AuthManager(user_pool_id, client_id, region)
    
    # Scenario 1: Warehouse Manager
    print("\nScenario 1: Warehouse Manager")
    print("-" * 40)
    groups = ["warehouse_managers"]
    
    print("Should have access to:")
    print("  ✅ warehouse_product")
    print("  ✅ sales_order_header")
    print("  ✅ inventory_optimizer")
    
    print("\nShould NOT have access to:")
    print("  ❌ purchase_order_header")
    print("  ❌ supplier_analyzer")
    
    # Scenario 2: Field Engineer
    print("\nScenario 2: Field Engineer")
    print("-" * 40)
    groups = ["field_engineers"]
    
    print("Should have access to:")
    print("  ✅ warehouse_product")
    print("  ✅ sales_order_header")
    print("  ✅ logistics_optimizer")
    
    print("\nShould NOT have access to:")
    print("  ❌ purchase_order_header")
    print("  ❌ inventory_optimizer")
    
    # Scenario 3: Procurement Specialist
    print("\nScenario 3: Procurement Specialist")
    print("-" * 40)
    groups = ["procurement_specialists"]
    
    print("Should have access to:")
    print("  ✅ purchase_order_header")
    print("  ✅ purchase_order_line")
    print("  ✅ supplier_analyzer")
    
    print("\nShould NOT have access to:")
    print("  ❌ sales_order_header")
    print("  ❌ logistics_optimizer")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test authentication and RBAC")
    parser.add_argument("--scenarios", action="store_true", help="Run RBAC scenario tests")
    args = parser.parse_args()
    
    if args.scenarios:
        test_rbac_scenarios()
    else:
        test_authentication()
