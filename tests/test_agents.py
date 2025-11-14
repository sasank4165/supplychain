"""Unit tests for supply chain agents"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.sql_agent import SQLAgent
from agents.inventory_optimizer_agent import InventoryOptimizerAgent
from agents.logistics_agent import LogisticsAgent
from agents.supplier_analyzer_agent import SupplierAnalyzerAgent
from orchestrator import SupplyChainOrchestrator

class TestSQLAgent(unittest.TestCase):
    """Test SQL Agent functionality"""
    
    @patch('boto3.client')
    def setUp(self, mock_boto):
        """Setup test fixtures"""
        self.agent = SQLAgent("warehouse_manager")
    
    def test_get_schema_context(self):
        """Test schema context generation"""
        schema = self.agent.get_schema_context()
        self.assertIn("product", schema)
        self.assertIn("warehouse_product", schema)
    
    def test_get_tools(self):
        """Test tool definitions"""
        tools = self.agent.get_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["toolSpec"]["name"], "execute_sql_query")

class TestInventoryOptimizerAgent(unittest.TestCase):
    """Test Inventory Optimizer Agent"""
    
    @patch('boto3.client')
    def setUp(self, mock_boto):
        """Setup test fixtures"""
        self.agent = InventoryOptimizerAgent()
    
    def test_get_tools(self):
        """Test tool definitions"""
        tools = self.agent.get_tools()
        tool_names = [t["toolSpec"]["name"] for t in tools]
        
        self.assertIn("calculate_reorder_points", tool_names)
        self.assertIn("forecast_demand", tool_names)
        self.assertIn("identify_stockout_risks", tool_names)
        self.assertIn("optimize_stock_levels", tool_names)

class TestLogisticsAgent(unittest.TestCase):
    """Test Logistics Agent"""
    
    @patch('boto3.client')
    def setUp(self, mock_boto):
        """Setup test fixtures"""
        self.agent = LogisticsAgent()
    
    def test_get_tools(self):
        """Test tool definitions"""
        tools = self.agent.get_tools()
        tool_names = [t["toolSpec"]["name"] for t in tools]
        
        self.assertIn("optimize_delivery_route", tool_names)
        self.assertIn("check_order_fulfillment_status", tool_names)
        self.assertIn("identify_delayed_orders", tool_names)
        self.assertIn("calculate_warehouse_capacity", tool_names)

class TestSupplierAnalyzerAgent(unittest.TestCase):
    """Test Supplier Analyzer Agent"""
    
    @patch('boto3.client')
    def setUp(self, mock_boto):
        """Setup test fixtures"""
        self.agent = SupplierAnalyzerAgent()
    
    def test_get_tools(self):
        """Test tool definitions"""
        tools = self.agent.get_tools()
        tool_names = [t["toolSpec"]["name"] for t in tools]
        
        self.assertIn("analyze_supplier_performance", tool_names)
        self.assertIn("compare_supplier_costs", tool_names)
        self.assertIn("identify_cost_savings_opportunities", tool_names)
        self.assertIn("analyze_purchase_order_trends", tool_names)

class TestOrchestrator(unittest.TestCase):
    """Test Multi-Agent Orchestrator"""
    
    @patch('boto3.client')
    def setUp(self, mock_boto):
        """Setup test fixtures"""
        self.orchestrator = SupplyChainOrchestrator()
    
    def test_get_agent_capabilities(self):
        """Test agent capability retrieval"""
        capabilities = self.orchestrator.get_agent_capabilities("warehouse_manager")
        
        self.assertEqual(capabilities["persona"], "warehouse_manager")
        self.assertIn("sql_agent", capabilities)
        self.assertIn("specialist_agent", capabilities)
    
    def test_invalid_persona(self):
        """Test invalid persona handling"""
        capabilities = self.orchestrator.get_agent_capabilities("invalid_persona")
        self.assertIn("error", capabilities)

if __name__ == '__main__':
    unittest.main()
