"""Unit tests for MetricsCollector

Tests cover:
- Metrics recording and publishing
- Business metrics
- Error tracking
- Statistics calculation
- CloudWatch integration
- Structured logging
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import json
from metrics_collector import (
    MetricsCollector,
    AgentMetrics,
    MetricType,
    create_metrics_collector
)


class TestAgentMetrics(unittest.TestCase):
    """Test AgentMetrics dataclass"""
    
    def test_agent_metrics_creation(self):
        """Test creating AgentMetrics instance"""
        metrics = AgentMetrics(
            persona="warehouse_manager",
            agent_name="inventory_optimizer",
            query="Test query",
            timestamp=datetime.utcnow(),
            latency_ms=1250.5,
            success=True,
            token_count=1500
        )
        
        self.assertEqual(metrics.persona, "warehouse_manager")
        self.assertEqual(metrics.agent_name, "inventory_optimizer")
        self.assertEqual(metrics.latency_ms, 1250.5)
        self.assertTrue(metrics.success)
        self.assertEqual(metrics.token_count, 1500)
        self.assertEqual(metrics.tool_executions, [])
    
    def test_agent_metrics_to_dict(self):
        """Test converting AgentMetrics to dictionary"""
        timestamp = datetime.utcnow()
        metrics = AgentMetrics(
            persona="field_engineer",
            agent_name="logistics_agent",
            query="Test query",
            timestamp=timestamp,
            latency_ms=500.0,
            success=True
        )
        
        data = metrics.to_dict()
        
        self.assertEqual(data['persona'], "field_engineer")
        self.assertEqual(data['agent_name'], "logistics_agent")
        self.assertEqual(data['latency_ms'], 500.0)
        self.assertEqual(data['timestamp'], timestamp.isoformat())


class TestMetricsCollector(unittest.TestCase):
    """Test MetricsCollector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_cloudwatch = Mock()
        self.patcher = patch('boto3.client')
        self.mock_boto_client = self.patcher.start()
        self.mock_boto_client.return_value = self.mock_cloudwatch
    
    def tearDown(self):
        """Clean up patches"""
        self.patcher.stop()
    
    def test_initialization(self):
        """Test MetricsCollector initialization"""
        collector = MetricsCollector(region="us-east-1")
        
        self.assertEqual(collector.region, "us-east-1")
        self.assertEqual(collector.namespace, "SupplyChainAgent/Agents")
        self.assertEqual(collector.buffer_size, 20)
        self.assertEqual(len(collector.metrics_buffer), 0)
    
    def test_initialization_with_config(self):
        """Test initialization with configuration"""
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default=None: {
            'project.prefix': 'test-app',
        }.get(key, default)
        
        collector = MetricsCollector(region="us-west-2", config=mock_config)
        
        self.assertEqual(collector.namespace, "test-app/Agents")
        self.assertEqual(collector.region, "us-west-2")
    
    def test_initialization_with_custom_namespace(self):
        """Test initialization with custom namespace"""
        collector = MetricsCollector(
            region="us-east-1",
            namespace="CustomApp/Metrics"
        )
        
        self.assertEqual(collector.namespace, "CustomApp/Metrics")
    
    def test_record_query_success(self):
        """Test recording successful query"""
        collector = MetricsCollector(region="us-east-1")
        
        collector.record_query(
            persona="warehouse_manager",
            agent="inventory_optimizer",
            query="Test query",
            latency_ms=1250.5,
            success=True,
            token_count=1500,
            session_id="session123",
            intent="optimization"
        )
        
        # Check statistics updated
        self.assertEqual(collector.stats['total_queries'], 1)
        self.assertEqual(collector.stats['successful_queries'], 1)
        self.assertEqual(collector.stats['failed_queries'], 0)
        self.assertEqual(collector.stats['total_latency_ms'], 1250.5)
        self.assertEqual(collector.stats['total_tokens'], 1500)
        
        # Check metrics buffered
        self.assertGreater(len(collector.metrics_buffer), 0)
    
    def test_record_query_failure(self):
        """Test recording failed query"""
        collector = MetricsCollector(region="us-east-1")
        
        collector.record_query(
            persona="field_engineer",
            agent="logistics_agent",
            query="Test query",
            latency_ms=500.0,
            success=False,
            error_message="Database timeout",
            session_id="session456"
        )
        
        # Check statistics updated
        self.assertEqual(collector.stats['total_queries'], 1)
        self.assertEqual(collector.stats['successful_queries'], 0)
        self.assertEqual(collector.stats['failed_queries'], 1)
    
    def test_record_query_with_tool_executions(self):
        """Test recording query with tool execution details"""
        collector = MetricsCollector(region="us-east-1")
        
        tool_executions = [
            {"tool_name": "calculate_reorder_points", "duration_ms": 450, "success": True},
            {"tool_name": "forecast_demand", "duration_ms": 320, "success": True}
        ]
        
        collector.record_query(
            persona="warehouse_manager",
            agent="inventory_optimizer",
            query="Test query",
            latency_ms=1000.0,
            success=True,
            tool_executions=tool_executions
        )
        
        # Check tool execution metrics in buffer
        tool_metrics = [m for m in collector.metrics_buffer if m['MetricName'] == 'ToolExecutionTime']
        self.assertEqual(len(tool_metrics), 2)
    
    def test_metrics_buffer_flush(self):
        """Test metrics buffer auto-flush"""
        collector = MetricsCollector(region="us-east-1")
        collector.buffer_size = 5  # Small buffer for testing
        
        # Record enough queries to trigger flush
        for i in range(3):
            collector.record_query(
                persona="warehouse_manager",
                agent="sql_agent",
                query=f"Query {i}",
                latency_ms=100.0,
                success=True
            )
        
        # Should have triggered flush
        self.mock_cloudwatch.put_metric_data.assert_called()
    
    def test_record_business_metric(self):
        """Test recording custom business metric"""
        collector = MetricsCollector(region="us-east-1")
        
        collector.record_business_metric(
            metric_name="ItemsOptimized",
            value=45,
            unit="Count",
            dimensions={"Warehouse": "WH-001", "Category": "Electronics"}
        )
        
        # Check metric in buffer
        self.assertEqual(len(collector.metrics_buffer), 1)
        metric = collector.metrics_buffer[0]
        self.assertEqual(metric['MetricName'], "ItemsOptimized")
        self.assertEqual(metric['Value'], 45)
        self.assertEqual(metric['Unit'], "Count")
    
    def test_record_error(self):
        """Test recording error with context"""
        collector = MetricsCollector(region="us-east-1")
        
        collector.record_error(
            persona="field_engineer",
            agent="logistics_agent",
            error_type="database_timeout",
            error_message="Query exceeded timeout",
            context={"query": "Complex query", "timeout": 30}
        )
        
        # Check error metric in buffer
        error_metrics = [m for m in collector.metrics_buffer if m['MetricName'] == 'ErrorByType']
        self.assertEqual(len(error_metrics), 1)
        self.assertEqual(error_metrics[0]['Dimensions'][0]['Value'], "database_timeout")
    
    def test_get_stats(self):
        """Test getting statistics"""
        collector = MetricsCollector(region="us-east-1")
        
        # Record some queries
        collector.record_query("warehouse_manager", "sql_agent", "Q1", 100.0, True, 500)
        collector.record_query("warehouse_manager", "sql_agent", "Q2", 200.0, True, 600)
        collector.record_query("warehouse_manager", "sql_agent", "Q3", 150.0, False, 0)
        
        stats = collector.get_stats()
        
        self.assertEqual(stats['total_queries'], 3)
        self.assertEqual(stats['successful_queries'], 2)
        self.assertEqual(stats['failed_queries'], 1)
        self.assertAlmostEqual(stats['success_rate_percent'], 66.67, places=1)
        self.assertAlmostEqual(stats['average_latency_ms'], 150.0, places=1)
        self.assertEqual(stats['total_tokens_used'], 1100)
    
    def test_get_stats_empty(self):
        """Test getting statistics with no data"""
        collector = MetricsCollector(region="us-east-1")
        
        stats = collector.get_stats()
        
        self.assertEqual(stats['total_queries'], 0)
        self.assertEqual(stats['success_rate_percent'], 0)
        self.assertEqual(stats['average_latency_ms'], 0)
    
    def test_manual_flush(self):
        """Test manual metrics flush"""
        collector = MetricsCollector(region="us-east-1")
        
        collector.record_query("warehouse_manager", "sql_agent", "Q1", 100.0, True)
        
        # Manually flush
        collector.flush()
        
        # Buffer should be empty
        self.assertEqual(len(collector.metrics_buffer), 0)
        self.mock_cloudwatch.put_metric_data.assert_called()
    
    def test_flush_empty_buffer(self):
        """Test flushing empty buffer"""
        collector = MetricsCollector(region="us-east-1")
        
        # Flush empty buffer
        collector.flush()
        
        # Should not call CloudWatch
        self.mock_cloudwatch.put_metric_data.assert_not_called()
    
    def test_cloudwatch_publish_format(self):
        """Test CloudWatch metric data format"""
        collector = MetricsCollector(region="us-east-1")
        collector.buffer_size = 5
        
        collector.record_query(
            persona="warehouse_manager",
            agent="inventory_optimizer",
            query="Test",
            latency_ms=1000.0,
            success=True,
            token_count=500
        )
        
        collector.flush()
        
        # Verify put_metric_data was called
        self.mock_cloudwatch.put_metric_data.assert_called()
        
        # Get the call arguments
        call_args = self.mock_cloudwatch.put_metric_data.call_args
        
        # Verify namespace
        self.assertEqual(call_args[1]['Namespace'], "SupplyChainAgent/Agents")
        
        # Verify metric data structure
        metric_data = call_args[1]['MetricData']
        self.assertIsInstance(metric_data, list)
        self.assertGreater(len(metric_data), 0)
        
        # Check first metric has required fields
        first_metric = metric_data[0]
        self.assertIn('MetricName', first_metric)
        self.assertIn('Value', first_metric)
        self.assertIn('Unit', first_metric)
        self.assertIn('Dimensions', first_metric)
    
    def test_structured_logging(self):
        """Test structured JSON logging"""
        collector = MetricsCollector(region="us-east-1")
        
        with patch.object(collector.logger, 'info') as mock_log:
            collector.record_query(
                persona="warehouse_manager",
                agent="sql_agent",
                query="Test query",
                latency_ms=100.0,
                success=True
            )
            
            # Verify logging was called
            mock_log.assert_called_once()
            
            # Verify log message is valid JSON
            log_message = mock_log.call_args[0][0]
            log_data = json.loads(log_message)
            
            self.assertEqual(log_data['persona'], "warehouse_manager")
            self.assertEqual(log_data['agent_name'], "sql_agent")
    
    def test_get_metrics_summary(self):
        """Test getting metrics summary from CloudWatch"""
        collector = MetricsCollector(region="us-east-1")
        
        # Mock CloudWatch responses
        self.mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Timestamp': datetime.utcnow(), 'Average': 1250.5}
            ]
        }
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        summary = collector.get_metrics_summary(
            start_time=start_time,
            end_time=end_time,
            persona="warehouse_manager",
            agent="inventory_optimizer"
        )
        
        # Verify summary structure
        self.assertIn('time_period', summary)
        self.assertIn('filters', summary)
        self.assertIn('latency', summary)
        self.assertEqual(summary['filters']['persona'], "warehouse_manager")
        self.assertEqual(summary['filters']['agent'], "inventory_optimizer")
    
    def test_create_metrics_collector_function(self):
        """Test convenience function"""
        collector = create_metrics_collector(region="us-west-2")
        
        self.assertIsInstance(collector, MetricsCollector)
        self.assertEqual(collector.region, "us-west-2")


class TestMetricsIntegration(unittest.TestCase):
    """Integration tests for metrics collection"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_cloudwatch = Mock()
        self.patcher = patch('boto3.client')
        self.mock_boto_client = self.patcher.start()
        self.mock_boto_client.return_value = self.mock_cloudwatch
    
    def tearDown(self):
        """Clean up patches"""
        self.patcher.stop()
    
    def test_end_to_end_query_metrics(self):
        """Test complete query metrics flow"""
        collector = MetricsCollector(region="us-east-1")
        collector.buffer_size = 10
        
        # Simulate multiple queries
        queries = [
            ("warehouse_manager", "inventory_optimizer", True, 1200.0, 1500),
            ("field_engineer", "logistics_agent", True, 800.0, 1000),
            ("procurement_specialist", "supplier_analyzer", False, 500.0, 0),
        ]
        
        for persona, agent, success, latency, tokens in queries:
            collector.record_query(
                persona=persona,
                agent=agent,
                query="Test query",
                latency_ms=latency,
                success=success,
                token_count=tokens
            )
        
        # Get statistics
        stats = collector.get_stats()
        
        self.assertEqual(stats['total_queries'], 3)
        self.assertEqual(stats['successful_queries'], 2)
        self.assertEqual(stats['failed_queries'], 1)
        self.assertEqual(stats['total_tokens_used'], 2500)
    
    def test_business_metrics_workflow(self):
        """Test business metrics recording workflow"""
        collector = MetricsCollector(region="us-east-1")
        
        # Record various business metrics
        collector.record_business_metric(
            "ItemsOptimized", 45, "Count",
            {"Warehouse": "WH-001"}
        )
        
        collector.record_business_metric(
            "CostSavings", 12500.50, "None",
            {"Persona": "procurement_specialist"}
        )
        
        collector.record_business_metric(
            "ForecastAccuracy", 94.5, "Percent",
            {"Agent": "inventory_optimizer"}
        )
        
        # Verify metrics buffered
        self.assertEqual(len(collector.metrics_buffer), 3)
        
        # Flush and verify
        collector.flush()
        self.mock_cloudwatch.put_metric_data.assert_called()


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
