"""Unit tests for ModelManager"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from model_manager import ModelManager, ModelConfig, ModelUsageMetrics, ModelManagerError
from config_manager import ConfigurationManager


class TestModelManager(unittest.TestCase):
    """Test ModelManager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock configuration
        self.mock_config = Mock(spec=ConfigurationManager)
        self.mock_config.get.side_effect = lambda key, default=None: {
            'environment.region': 'us-east-1',
            'project.prefix': 'test-agent',
            'agents.default_model': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'agents.sql_agent': {
                'enabled': True,
                'model': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
                'timeout_seconds': 60
            },
            'agents.inventory_optimizer': {
                'enabled': True,
                'model': 'anthropic.claude-3-5-haiku-20241022-v1:0',
                'timeout_seconds': 90
            }
        }.get(key, default)
    
    @patch('model_manager.boto3.client')
    def test_model_manager_initialization(self, mock_boto_client):
        """Test ModelManager initialization"""
        model_manager = ModelManager(self.mock_config)
        
        self.assertEqual(model_manager.region, 'us-east-1')
        self.assertEqual(model_manager.metrics_namespace, 'test-agent/Models')
        self.assertIsNotNone(model_manager.bedrock_runtime)
        self.assertIsNotNone(model_manager.cloudwatch)
    
    def test_get_model_for_agent(self):
        """Test getting model ID for specific agent"""
        with patch('model_manager.boto3.client'):
            model_manager = ModelManager(self.mock_config)
            
            # Test agent-specific model
            model_id = model_manager.get_model_for_agent('sql_agent')
            self.assertEqual(model_id, 'anthropic.claude-3-5-sonnet-20241022-v2:0')
            
            # Test agent with different model
            model_id = model_manager.get_model_for_agent('inventory_optimizer')
            self.assertEqual(model_id, 'anthropic.claude-3-5-haiku-20241022-v1:0')
            
            # Test fallback to default for unknown agent
            model_id = model_manager.get_model_for_agent('unknown_agent')
            self.assertEqual(model_id, 'anthropic.claude-3-5-sonnet-20241022-v2:0')
    
    def test_get_fallback_model(self):
        """Test fallback model selection"""
        with patch('model_manager.boto3.client'):
            model_manager = ModelManager(self.mock_config)
            
            # Mock model availability
            model_manager._check_model_availability = Mock(return_value=True)
            
            # Test Sonnet -> Haiku fallback
            fallback = model_manager.get_fallback_model('anthropic.claude-3-5-sonnet-20241022-v2:0')
            self.assertEqual(fallback, 'anthropic.claude-3-5-haiku-20241022-v1:0')
            
            # Test Opus -> Sonnet fallback
            fallback = model_manager.get_fallback_model('anthropic.claude-3-opus-20240229-v1:0')
            self.assertEqual(fallback, 'anthropic.claude-3-5-sonnet-20241022-v2:0')
            
            # Test Haiku -> Sonnet fallback
            fallback = model_manager.get_fallback_model('anthropic.claude-3-5-haiku-20241022-v1:0')
            self.assertEqual(fallback, 'anthropic.claude-3-5-sonnet-20241022-v2:0')
    
    def test_get_model_config(self):
        """Test getting model configuration"""
        with patch('model_manager.boto3.client'):
            model_manager = ModelManager(self.mock_config)
            
            # Test valid model
            config = model_manager.get_model_config('anthropic.claude-3-5-sonnet-20241022-v2:0')
            self.assertIsNotNone(config)
            self.assertEqual(config.model_family, 'claude')
            self.assertTrue(config.supports_tools)
            
            # Test invalid model
            config = model_manager.get_model_config('invalid-model')
            self.assertIsNone(config)
    
    def test_validate_model_compatibility(self):
        """Test model compatibility validation"""
        with patch('model_manager.boto3.client'):
            model_manager = ModelManager(self.mock_config)
            
            # Test Claude model with tools (should pass)
            is_compatible, error = model_manager.validate_model_compatibility(
                'anthropic.claude-3-5-sonnet-20241022-v2:0',
                requires_tools=True
            )
            self.assertTrue(is_compatible)
            self.assertIsNone(error)
            
            # Test Titan model with tools (should fail)
            is_compatible, error = model_manager.validate_model_compatibility(
                'amazon.titan-text-premier-v1:0',
                requires_tools=True
            )
            self.assertFalse(is_compatible)
            self.assertIn('does not support tools', error)
            
            # Test invalid model
            is_compatible, error = model_manager.validate_model_compatibility(
                'invalid-model',
                requires_tools=False
            )
            self.assertFalse(is_compatible)
            self.assertIn('not found', error)
    
    def test_model_usage_metrics(self):
        """Test ModelUsageMetrics dataclass"""
        metrics = ModelUsageMetrics(
            agent_name='test_agent',
            model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
            timestamp=datetime.utcnow(),
            input_tokens=100,
            output_tokens=200,
            latency_ms=500.0,
            success=True
        )
        
        # Test to_dict conversion
        metrics_dict = metrics.to_dict()
        self.assertEqual(metrics_dict['agent_name'], 'test_agent')
        self.assertEqual(metrics_dict['input_tokens'], 100)
        self.assertEqual(metrics_dict['output_tokens'], 200)
        
        # Test cost calculation
        model_config = ModelConfig(
            model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
            model_family='claude',
            max_tokens=8192,
            temperature=1.0,
            supports_tools=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.003,
            cost_per_1k_output_tokens=0.015
        )
        
        cost = metrics.get_cost(model_config)
        expected_cost = (100 / 1000) * 0.003 + (200 / 1000) * 0.015
        self.assertAlmostEqual(cost, expected_cost, places=6)
    
    @patch('model_manager.boto3.client')
    def test_list_available_models(self, mock_boto_client):
        """Test listing available models"""
        model_manager = ModelManager(self.mock_config)
        model_manager._check_model_availability = Mock(return_value=True)
        
        models = model_manager.list_available_models()
        
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        
        # Check first model has required fields
        first_model = models[0]
        self.assertIn('model_id', first_model)
        self.assertIn('model_family', first_model)
        self.assertIn('supports_tools', first_model)
        self.assertIn('available', first_model)
    
    @patch('model_manager.boto3.client')
    def test_usage_summary(self, mock_boto_client):
        """Test usage summary generation"""
        model_manager = ModelManager(self.mock_config)
        
        # Add some metrics to buffer
        model_manager._metrics_buffer = [
            ModelUsageMetrics(
                agent_name='agent1',
                model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
                timestamp=datetime.utcnow(),
                input_tokens=100,
                output_tokens=200,
                latency_ms=500.0,
                success=True
            ),
            ModelUsageMetrics(
                agent_name='agent2',
                model_id='anthropic.claude-3-5-haiku-20241022-v1:0',
                timestamp=datetime.utcnow(),
                input_tokens=50,
                output_tokens=100,
                latency_ms=300.0,
                success=True
            )
        ]
        
        summary = model_manager.get_usage_summary()
        
        self.assertEqual(summary['total_invocations'], 2)
        self.assertEqual(summary['successful_invocations'], 2)
        self.assertEqual(summary['total_input_tokens'], 150)
        self.assertEqual(summary['total_output_tokens'], 300)
        self.assertIn('total_cost_usd', summary)
        self.assertIn('models_used', summary)


if __name__ == '__main__':
    unittest.main()
