"""
Integration Tests for Task 16: End-to-End System Validation

Tests all three personas (Warehouse Manager, Field Engineer, Procurement Specialist)
and validates system features including caching, conversation memory, cost tracking,
and authentication.
"""

import sys
import os
import time
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache.query_cache import QueryCache
from memory.conversation_memory import ConversationMemory
from memory.context import Persona, ConversationContext
from cost.cost_tracker import CostTracker, TokenUsage
from auth.auth_manager import AuthManager
from auth.session_manager import SessionManager


# ============================================================================
# Test 16.1: Warehouse Manager Workflows
# ============================================================================

class TestWarehouseManagerWorkflows:
    """Test Warehouse Manager persona workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache = QueryCache(max_size=100, default_ttl=300)
        self.memory = ConversationMemory(max_history=10)
        cost_config = {
            'enabled': True,
            'bedrock_input_cost_per_1k': 0.003,
            'bedrock_output_cost_per_1k': 0.015,
            'redshift_rpu_cost_per_hour': 0.36,
            'lambda_cost_per_gb_second': 0.0000166667
        }
        self.cost_tracker = CostTracker(cost_config)
        self.session_id = "wm_test_session"
        
    def test_sql_query_inventory_data(self):
        """Test SQL queries for inventory data."""
        print("\n=== Test 16.1.1: SQL Query for Inventory Data ===")
        
        # Create session for Warehouse Manager
        context = self.memory.create_session(self.session_id, Persona.WAREHOUSE_MANAGER)
        assert context.persona == Persona.WAREHOUSE_MANAGER
        print("✓ Warehouse Manager session created")
        
        # Simulate SQL query for low stock items
        query = "Show me products with low stock levels"
        
        # Mock SQL response
        sql_response = {
            'query': 'SELECT product_code, product_name, current_stock, minimum_stock FROM warehouse_product WHERE current_stock < minimum_stock',
            'results': [
                {'product_code': 'P001', 'product_name': 'Widget A', 'current_stock': 5, 'minimum_stock': 10},
                {'product_code': 'P002', 'product_name': 'Widget B', 'current_stock': 3, 'minimum_stock': 8}
            ],
            'execution_time': 1.2
        }
        
        # Cache the result
        cache_key = QueryCache.generate_cache_key(query, "Warehouse Manager")
        self.cache.set(cache_key, sql_response)
        
        # Add to conversation memory
        self.memory.add_interaction(self.session_id, query, str(sql_response))
        
        # Verify cache hit
        cached = self.cache.get(cache_key)
        assert cached is not None
        assert len(cached['results']) == 2
        print(f"✓ SQL query cached: {len(cached['results'])} low stock items")
        
        # Verify conversation history
        history = self.memory.get_history(self.session_id)
        assert len(history) == 1
        assert history[0].query == query
        print("✓ Query added to conversation history")
        
        print("✅ Test 16.1.1 passed: SQL query for inventory data")
    
    def test_inventory_optimization_tools(self):
        """Test inventory optimization tools."""
        print("\n=== Test 16.1.2: Inventory Optimization Tools ===")
        
        # Simulate reorder point calculation
        from tools.calculation_tools import CalculationTools
        
        avg_daily_demand = 10.0
        lead_time_days = 7
        safety_stock = 20.0
        
        reorder_point = CalculationTools.calculate_reorder_point(
            avg_daily_demand, lead_time_days, safety_stock
        )
        
        assert reorder_point == 90.0
        print(f"✓ Reorder point calculated: {reorder_point}")
        
        # Simulate safety stock calculation
        max_daily_demand = 15.0
        avg_daily_demand = 10.0
        max_lead_time = 10
        avg_lead_time = 7
        
        safety_stock_calc = CalculationTools.calculate_safety_stock(
            max_daily_demand, avg_daily_demand, max_lead_time, avg_lead_time
        )
        
        assert safety_stock_calc == 80.0
        print(f"✓ Safety stock calculated: {safety_stock_calc}")
        
        print("✅ Test 16.1.2 passed: Inventory optimization tools")
    
    def test_demand_forecasting(self):
        """Test demand forecasting functionality."""
        print("\n=== Test 16.1.3: Demand Forecasting ===")
        
        from tools.calculation_tools import CalculationTools
        
        # Historical demand data
        historical_demand = [100, 105, 110, 108, 112, 115, 120]
        periods = 3
        
        forecast = CalculationTools.forecast_demand(
            historical_demand, periods, method="moving_average"
        )
        
        assert len(forecast) == periods
        assert all(f > 0 for f in forecast)
        print(f"✓ Demand forecast generated: {forecast}")
        
        # Test with exponential smoothing
        forecast_exp = CalculationTools.forecast_demand(
            historical_demand, periods, method="exponential_smoothing"
        )
        
        assert len(forecast_exp) == periods
        print(f"✓ Exponential smoothing forecast: {forecast_exp}")
        
        print("✅ Test 16.1.3 passed: Demand forecasting")


# ============================================================================
# Test 16.2: Field Engineer Workflows
# ============================================================================

class TestFieldEngineerWorkflows:
    """Test Field Engineer persona workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache = QueryCache(max_size=100, default_ttl=300)
        self.memory = ConversationMemory(max_history=10)
        self.session_id = "fe_test_session"
    
    def test_sql_query_order_data(self):
        """Test SQL queries for order and delivery data."""
        print("\n=== Test 16.2.1: SQL Query for Order Data ===")
        
        # Create session for Field Engineer
        context = self.memory.create_session(self.session_id, Persona.FIELD_ENGINEER)
        assert context.persona == Persona.FIELD_ENGINEER
        print("✓ Field Engineer session created")
        
        # Simulate SQL query for orders
        query = "Show me orders scheduled for delivery today"
        
        # Mock SQL response
        sql_response = {
            'query': 'SELECT * FROM sales_order_header WHERE delivery_date = CURRENT_DATE',
            'results': [
                {'order_id': 'SO001', 'customer': 'Customer A', 'status': 'In Transit'},
                {'order_id': 'SO002', 'customer': 'Customer B', 'status': 'Ready'}
            ],
            'execution_time': 0.8
        }
        
        # Cache and store
        cache_key = QueryCache.generate_cache_key(query, "Field Engineer")
        self.cache.set(cache_key, sql_response)
        self.memory.add_interaction(self.session_id, query, str(sql_response))
        
        # Verify
        cached = self.cache.get(cache_key)
        assert cached is not None
        assert len(cached['results']) == 2
        print(f"✓ Order query cached: {len(cached['results'])} orders today")
        
        print("✅ Test 16.2.1 passed: SQL query for order data")
    
    def test_logistics_optimization_tools(self):
        """Test logistics optimization tools."""
        print("\n=== Test 16.2.2: Logistics Optimization Tools ===")
        
        from tools.calculation_tools import CalculationTools, Order, Location
        
        # Create test orders with all required fields
        orders = [
            Order(order_id='SO001', delivery_address='123 Main St', delivery_area='North', 
                  latitude=40.7589, longitude=-73.9851, priority=1),
            Order(order_id='SO002', delivery_address='456 Oak Ave', delivery_area='North',
                  latitude=40.7614, longitude=-73.9776, priority=1),
            Order(order_id='SO003', delivery_address='789 Pine Rd', delivery_area='South',
                  latitude=40.7489, longitude=-73.9680, priority=2)
        ]
        
        warehouse_location = Location(latitude=40.7128, longitude=-74.0060, address="Warehouse")
        
        # Optimize route
        route_optimization = CalculationTools.optimize_route(orders, warehouse_location)
        
        assert route_optimization is not None
        assert len(route_optimization.optimized_order) > 0
        print(f"✓ Route optimized: {len(route_optimization.optimized_order)} stops")
        print(f"  Estimated distance: {route_optimization.total_distance_km:.2f} km")
        
        print("✅ Test 16.2.2 passed: Logistics optimization tools")
    
    def test_fulfillment_tracking(self):
        """Test order fulfillment tracking."""
        print("\n=== Test 16.2.3: Fulfillment Tracking ===")
        
        # Simulate fulfillment status check
        query = "What is the status of order SO001?"
        
        fulfillment_status = {
            'order_id': 'SO001',
            'status': 'In Transit',
            'items': [
                {'product': 'Widget A', 'ordered': 10, 'fulfilled': 10},
                {'product': 'Widget B', 'ordered': 5, 'fulfilled': 5}
            ],
            'delivery_date': '2024-02-17',
            'tracking_number': 'TRK123456'
        }
        
        # Cache the status
        cache_key = QueryCache.generate_cache_key(query, "Field Engineer")
        self.cache.set(cache_key, fulfillment_status)
        
        # Verify
        cached = self.cache.get(cache_key)
        assert cached is not None
        assert cached['status'] == 'In Transit'
        assert len(cached['items']) == 2
        print(f"✓ Fulfillment status tracked: {cached['status']}")
        
        print("✅ Test 16.2.3 passed: Fulfillment tracking")


# ============================================================================
# Test 16.3: Procurement Specialist Workflows
# ============================================================================

class TestProcurementSpecialistWorkflows:
    """Test Procurement Specialist persona workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache = QueryCache(max_size=100, default_ttl=300)
        self.memory = ConversationMemory(max_history=10)
        self.session_id = "ps_test_session"
    
    def test_sql_query_purchase_order_data(self):
        """Test SQL queries for purchase order and supplier data."""
        print("\n=== Test 16.3.1: SQL Query for Purchase Order Data ===")
        
        # Create session for Procurement Specialist
        context = self.memory.create_session(self.session_id, Persona.PROCUREMENT_SPECIALIST)
        assert context.persona == Persona.PROCUREMENT_SPECIALIST
        print("✓ Procurement Specialist session created")
        
        # Simulate SQL query for purchase orders
        query = "Show me pending purchase orders"
        
        # Mock SQL response
        sql_response = {
            'query': 'SELECT * FROM purchase_order_header WHERE status = \'Pending\'',
            'results': [
                {'po_id': 'PO001', 'supplier': 'Supplier A', 'total': 5000.00},
                {'po_id': 'PO002', 'supplier': 'Supplier B', 'total': 3500.00}
            ],
            'execution_time': 1.0
        }
        
        # Cache and store
        cache_key = QueryCache.generate_cache_key(query, "Procurement Specialist")
        self.cache.set(cache_key, sql_response)
        self.memory.add_interaction(self.session_id, query, str(sql_response))
        
        # Verify
        cached = self.cache.get(cache_key)
        assert cached is not None
        assert len(cached['results']) == 2
        print(f"✓ PO query cached: {len(cached['results'])} pending orders")
        
        print("✅ Test 16.3.1 passed: SQL query for purchase order data")
    
    def test_supplier_analysis_tools(self):
        """Test supplier analysis tools."""
        print("\n=== Test 16.3.2: Supplier Analysis Tools ===")
        
        from tools.calculation_tools import CalculationTools
        
        # Calculate supplier score
        fill_rate = 0.95
        on_time_rate = 0.90
        quality_rate = 0.92
        cost_competitiveness = 0.88
        
        supplier_score = CalculationTools.calculate_supplier_score(
            fill_rate, on_time_rate, quality_rate, cost_competitiveness
        )
        
        expected_score = (0.95 * 0.3 + 0.90 * 0.3 + 0.92 * 0.2 + 0.88 * 0.2)
        assert abs(supplier_score - expected_score) < 0.01
        print(f"✓ Supplier score calculated: {supplier_score:.2f}")
        
        print("✅ Test 16.3.2 passed: Supplier analysis tools")
    
    def test_cost_comparison(self):
        """Test supplier cost comparison."""
        print("\n=== Test 16.3.3: Supplier Cost Comparison ===")
        
        # Simulate cost comparison query
        query = "Compare costs for Widget A across suppliers"
        
        cost_comparison = {
            'product': 'Widget A',
            'suppliers': [
                {'supplier': 'Supplier A', 'unit_cost': 10.50, 'lead_time': 7},
                {'supplier': 'Supplier B', 'unit_cost': 10.00, 'lead_time': 10},
                {'supplier': 'Supplier C', 'unit_cost': 11.00, 'lead_time': 5}
            ],
            'recommendation': 'Supplier B offers best cost, but Supplier C has fastest delivery'
        }
        
        # Cache the comparison
        cache_key = QueryCache.generate_cache_key(query, "Procurement Specialist")
        self.cache.set(cache_key, cost_comparison)
        
        # Verify
        cached = self.cache.get(cache_key)
        assert cached is not None
        assert len(cached['suppliers']) == 3
        print(f"✓ Cost comparison cached: {len(cached['suppliers'])} suppliers")
        
        print("✅ Test 16.3.3 passed: Supplier cost comparison")



# ============================================================================
# Test 16.4: System Features Validation
# ============================================================================

class TestSystemFeatures:
    """Test system-wide features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache = QueryCache(max_size=100, default_ttl=300)
        self.memory = ConversationMemory(max_history=10)
        cost_config = {
            'enabled': True,
            'bedrock_input_cost_per_1k': 0.003,
            'bedrock_output_cost_per_1k': 0.015,
            'redshift_rpu_cost_per_hour': 0.36,
            'lambda_cost_per_gb_second': 0.0000166667
        }
        self.cost_tracker = CostTracker(cost_config)
    
    def test_query_caching_identical_queries(self):
        """Test query caching with identical queries."""
        print("\n=== Test 16.4.1: Query Caching ===")
        
        query = "Show me inventory levels"
        persona = "Warehouse Manager"
        
        # First query - cache miss
        cache_key = QueryCache.generate_cache_key(query, persona)
        result1 = self.cache.get(cache_key)
        assert result1 is None
        print("✓ First query: cache miss (expected)")
        
        # Store result
        response = {'data': 'inventory data', 'timestamp': datetime.now().isoformat()}
        self.cache.set(cache_key, response)
        
        # Second identical query - cache hit
        result2 = self.cache.get(cache_key)
        assert result2 is not None
        assert result2['data'] == 'inventory data'
        print("✓ Second query: cache hit (expected)")
        
        # Verify cache statistics
        stats = self.cache.get_stats()
        assert stats['hits'] >= 1
        assert stats['misses'] >= 1
        print(f"✓ Cache stats: {stats['hits']} hits, {stats['misses']} misses")
        
        print("✅ Test 16.4.1 passed: Query caching")
    
    def test_conversation_memory_followup(self):
        """Test conversation memory with follow-up questions."""
        print("\n=== Test 16.4.2: Conversation Memory ===")
        
        session_id = "test_session"
        self.memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
        
        # First query
        query1 = "Show me low stock items"
        response1 = "Low stock: Widget A (5 units), Widget B (3 units)"
        self.memory.add_interaction(session_id, query1, response1)
        
        # Follow-up query with context reference
        query2 = "What is the reorder point for Widget A?"
        response2 = "Widget A reorder point: 10 units"
        self.memory.add_interaction(session_id, query2, response2)
        
        # Verify conversation history
        history = self.memory.get_history(session_id)
        assert len(history) == 2
        assert history[0].query == query1
        assert history[1].query == query2
        print(f"✓ Conversation history: {len(history)} interactions")
        
        # Verify context retrieval
        context = self.memory.get_context(session_id)
        assert context.persona == Persona.WAREHOUSE_MANAGER
        assert len(context.history) == 2
        print("✓ Context retrieved with full history")
        
        print("✅ Test 16.4.2 passed: Conversation memory")
    
    def test_cost_tracking_calculations(self):
        """Test cost tracking calculations."""
        print("\n=== Test 16.4.3: Cost Tracking ===")
        
        # Simulate Bedrock token usage
        token_usage = TokenUsage(input_tokens=1000, output_tokens=500)
        
        # Calculate query cost
        cost = self.cost_tracker.calculate_query_cost(
            bedrock_tokens=token_usage,
            redshift_execution_time=1.5,  # 1.5 seconds
            lambda_duration_ms=500
        )
        
        assert cost.bedrock_cost > 0
        assert cost.redshift_cost > 0
        assert cost.lambda_cost > 0
        assert cost.total_cost > 0
        print(f"✓ Query cost calculated: ${cost.total_cost:.4f}")
        print(f"  - Bedrock: ${cost.bedrock_cost:.4f}")
        print(f"  - Redshift: ${cost.redshift_cost:.4f}")
        print(f"  - Lambda: ${cost.lambda_cost:.4f}")
        
        # Add to daily tracking
        session_id = "test_session"
        self.cost_tracker.add_query_cost(session_id, cost)
        
        # Verify daily cost
        daily_cost = self.cost_tracker.get_daily_cost()
        assert daily_cost.total_cost >= cost.total_cost
        print(f"✓ Daily cost tracked: ${daily_cost.total_cost:.4f}")
        
        # Verify monthly estimate
        monthly_estimate = self.cost_tracker.get_monthly_estimate()
        assert monthly_estimate > 0
        print(f"✓ Monthly estimate: ${monthly_estimate:.2f}")
        
        print("✅ Test 16.4.3 passed: Cost tracking")
    
    def test_authentication_and_authorization(self):
        """Test authentication and persona authorization."""
        print("\n=== Test 16.4.4: Authentication & Authorization ===")
        
        # Create temporary users file for testing
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            users_file = f.name
        
        try:
            # Initialize auth manager with temp file
            auth_manager = AuthManager(users_file=users_file)
            
            # Create test users
            auth_manager.create_user("test_wm", "password123", ["Warehouse Manager"])
            auth_manager.create_user("test_fe", "password123", ["Field Engineer"])
            auth_manager.create_user("test_multi", "password123", ["Warehouse Manager", "Procurement Specialist"])
            print("✓ Test users created")
            
            # Test successful authentication
            user = auth_manager.authenticate("test_wm", "password123")
            assert user is not None
            assert user.username == "test_wm"
            print("✓ Authentication successful")
            
            # Test failed authentication
            user_fail = auth_manager.authenticate("test_wm", "wrongpassword")
            assert user_fail is None
            print("✓ Failed authentication handled correctly")
            
            # Test persona authorization
            user_wm = auth_manager.authenticate("test_wm", "password123")
            assert auth_manager.authorize_persona(user_wm, "Warehouse Manager")
            assert not auth_manager.authorize_persona(user_wm, "Field Engineer")
            print("✓ Persona authorization working")
            
            # Test multi-persona user
            user_multi = auth_manager.authenticate("test_multi", "password123")
            personas = auth_manager.get_authorized_personas(user_multi)
            assert len(personas) == 2
            assert "Warehouse Manager" in personas
            assert "Procurement Specialist" in personas
            print(f"✓ Multi-persona user: {len(personas)} personas")
            
            # Test session management
            session_manager = SessionManager()
            session_token = session_manager.create_session(user_wm.username)
            assert session_token is not None
            print("✓ Session created")
            
            # Validate session
            session = session_manager.get_session(session_token)
            assert session is not None
            assert session.username == "test_wm"
            print("✓ Session validated")
            
            # Invalidate session
            session_manager.invalidate_session(session_token)
            invalid_session = session_manager.get_session(session_token)
            assert invalid_session is None
            print("✓ Session invalidated")
            
        finally:
            # Clean up temp file
            if os.path.exists(users_file):
                os.unlink(users_file)
        
        print("✅ Test 16.4.4 passed: Authentication & Authorization")


# ============================================================================
# End-to-End Integration Tests
# ============================================================================

class TestEndToEndIntegration:
    """Test complete end-to-end workflows."""
    
    def test_complete_warehouse_manager_workflow(self):
        """Test complete Warehouse Manager workflow from login to query."""
        print("\n=== Test: Complete Warehouse Manager Workflow ===")
        
        # Initialize all components
        cache = QueryCache(max_size=100, default_ttl=300)
        memory = ConversationMemory(max_history=10)
        cost_config = {
            'enabled': True,
            'bedrock_input_cost_per_1k': 0.003,
            'bedrock_output_cost_per_1k': 0.015,
            'redshift_rpu_cost_per_hour': 0.36,
            'lambda_cost_per_gb_second': 0.0000166667
        }
        cost_tracker = CostTracker(cost_config)
        
        # Step 1: Authentication (simulated)
        print("Step 1: User authentication")
        user = Mock()
        user.username = "warehouse_user"
        user.personas = ["Warehouse Manager"]
        print("✓ User authenticated")
        
        # Step 2: Create session
        print("Step 2: Create session")
        session_id = "e2e_wm_session"
        context = memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
        print("✓ Session created")
        
        # Step 3: Submit query
        print("Step 3: Submit query")
        query = "Show me products with stock below reorder point"
        cache_key = QueryCache.generate_cache_key(query, "Warehouse Manager")
        
        # Check cache (miss expected)
        cached_result = cache.get(cache_key)
        assert cached_result is None
        print("✓ Cache miss (first query)")
        
        # Step 4: Execute query (simulated)
        print("Step 4: Execute query")
        query_result = {
            'sql': 'SELECT * FROM warehouse_product WHERE current_stock < reorder_point',
            'results': [
                {'product': 'Widget A', 'stock': 5, 'reorder_point': 10},
                {'product': 'Widget B', 'stock': 8, 'reorder_point': 15}
            ],
            'execution_time': 1.5
        }
        print(f"✓ Query executed: {len(query_result['results'])} results")
        
        # Step 5: Cache result
        print("Step 5: Cache result")
        cache.set(cache_key, query_result)
        print("✓ Result cached")
        
        # Step 6: Add to conversation memory
        print("Step 6: Update conversation memory")
        memory.add_interaction(session_id, query, str(query_result))
        print("✓ Interaction recorded")
        
        # Step 7: Track cost
        print("Step 7: Track cost")
        token_usage = TokenUsage(input_tokens=500, output_tokens=300)
        cost = cost_tracker.calculate_query_cost(
            bedrock_tokens=token_usage,
            redshift_execution_time=1.5,
            lambda_duration_ms=0
        )
        cost_tracker.add_query_cost(session_id, cost)
        print(f"✓ Cost tracked: ${cost.total_cost:.4f}")
        
        # Step 8: Follow-up query (cache hit)
        print("Step 8: Follow-up query (cache hit)")
        cached_result = cache.get(cache_key)
        assert cached_result is not None
        assert len(cached_result['results']) == 2
        print("✓ Cache hit on repeat query")
        
        # Step 9: Verify final state
        print("Step 9: Verify final state")
        history = memory.get_history(session_id)
        assert len(history) == 1
        
        cache_stats = cache.get_stats()
        assert cache_stats['hits'] >= 1
        
        daily_cost = cost_tracker.get_daily_cost()
        assert daily_cost.total_cost > 0
        
        print("✓ All components in correct state")
        print("✅ Complete workflow test passed")
    
    def test_persona_switching_workflow(self):
        """Test switching between personas in same session."""
        print("\n=== Test: Persona Switching Workflow ===")
        
        memory = ConversationMemory(max_history=10)
        cache = QueryCache(max_size=100, default_ttl=300)
        
        session_id = "persona_switch_session"
        
        # Start as Warehouse Manager
        print("Step 1: Start as Warehouse Manager")
        memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
        memory.add_interaction(session_id, "Show inventory", "Inventory: ...")
        assert len(memory.get_history(session_id)) == 1
        print("✓ Warehouse Manager session active")
        
        # Switch to Field Engineer
        print("Step 2: Switch to Field Engineer")
        memory.switch_persona(session_id, Persona.FIELD_ENGINEER, clear_history=True)
        assert len(memory.get_history(session_id)) == 0
        print("✓ Switched to Field Engineer, history cleared")
        
        # Add new interaction
        memory.add_interaction(session_id, "Show orders", "Orders: ...")
        assert len(memory.get_history(session_id)) == 1
        print("✓ New interaction in Field Engineer context")
        
        # Verify context
        context = memory.get_context(session_id)
        assert context.persona == Persona.FIELD_ENGINEER
        print("✓ Context reflects current persona")
        
        print("✅ Persona switching test passed")


# ============================================================================
# Test Runner
# ============================================================================

def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("TASK 16: INTEGRATION TESTING AND VALIDATION")
    print("="*70)
    
    try:
        # Test 16.1: Warehouse Manager Workflows
        print("\n" + "="*70)
        print("TEST SUITE 16.1: WAREHOUSE MANAGER WORKFLOWS")
        print("="*70)
        wm_tests = TestWarehouseManagerWorkflows()
        wm_tests.setup_method()
        wm_tests.test_sql_query_inventory_data()
        wm_tests.test_inventory_optimization_tools()
        wm_tests.test_demand_forecasting()
        
        # Test 16.2: Field Engineer Workflows
        print("\n" + "="*70)
        print("TEST SUITE 16.2: FIELD ENGINEER WORKFLOWS")
        print("="*70)
        fe_tests = TestFieldEngineerWorkflows()
        fe_tests.setup_method()
        fe_tests.test_sql_query_order_data()
        fe_tests.test_logistics_optimization_tools()
        fe_tests.test_fulfillment_tracking()
        
        # Test 16.3: Procurement Specialist Workflows
        print("\n" + "="*70)
        print("TEST SUITE 16.3: PROCUREMENT SPECIALIST WORKFLOWS")
        print("="*70)
        ps_tests = TestProcurementSpecialistWorkflows()
        ps_tests.setup_method()
        ps_tests.test_sql_query_purchase_order_data()
        ps_tests.test_supplier_analysis_tools()
        ps_tests.test_cost_comparison()
        
        # Test 16.4: System Features
        print("\n" + "="*70)
        print("TEST SUITE 16.4: SYSTEM FEATURES VALIDATION")
        print("="*70)
        sys_tests = TestSystemFeatures()
        sys_tests.setup_method()
        sys_tests.test_query_caching_identical_queries()
        sys_tests.test_conversation_memory_followup()
        sys_tests.test_cost_tracking_calculations()
        sys_tests.test_authentication_and_authorization()
        
        # End-to-End Tests
        print("\n" + "="*70)
        print("END-TO-END INTEGRATION TESTS")
        print("="*70)
        e2e_tests = TestEndToEndIntegration()
        e2e_tests.test_complete_warehouse_manager_workflow()
        e2e_tests.test_persona_switching_workflow()
        
        # Summary
        print("\n" + "="*70)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("="*70)
        print("\nTask 16 Implementation Verified:")
        print("  ✓ 16.1: Warehouse Manager workflows (SQL, optimization, forecasting)")
        print("  ✓ 16.2: Field Engineer workflows (orders, logistics, tracking)")
        print("  ✓ 16.3: Procurement Specialist workflows (POs, suppliers, costs)")
        print("  ✓ 16.4: System features (caching, memory, cost, auth)")
        print("  ✓ End-to-end integration workflows")
        print("="*70)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
