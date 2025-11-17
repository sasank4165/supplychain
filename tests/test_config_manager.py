"""Unit tests for Configuration Management System"""

import unittest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigurationManager, ResourceNamer, ConfigurationError


class TestConfigurationManager(unittest.TestCase):
    """Test ConfigurationManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ConfigurationManager(environment='dev')
    
    def test_load_config(self):
        """Test configuration loading"""
        self.assertIsNotNone(self.config.config)
        self.assertEqual(self.config.environment, 'dev')
    
    def test_get_value(self):
        """Test getting configuration values"""
        env_name = self.config.get('environment.name')
        self.assertEqual(env_name, 'dev')
        
        region = self.config.get('environment.region')
        self.assertIsNotNone(region)
    
    def test_get_default(self):
        """Test getting value with default"""
        value = self.config.get('nonexistent.key', 'default_value')
        self.assertEqual(value, 'default_value')
    
    def test_get_required(self):
        """Test getting required value"""
        prefix = self.config.get_required('project.prefix')
        self.assertIsNotNone(prefix)
    
    def test_get_required_missing(self):
        """Test getting missing required value raises error"""
        with self.assertRaises(ConfigurationError):
            self.config.get_required('nonexistent.key')
    
    def test_get_tags(self):
        """Test getting resource tags"""
        tags = self.config.get_tags()
        self.assertIsInstance(tags, dict)
        self.assertIn('Project', tags)
        self.assertIn('Environment', tags)
        self.assertIn('ManagedBy', tags)
    
    def test_nested_config_access(self):
        """Test accessing nested configuration"""
        lambda_memory = self.config.get('resources.lambda.memory_mb')
        self.assertIsInstance(lambda_memory, int)
        self.assertGreater(lambda_memory, 0)
    
    def test_feature_flags(self):
        """Test feature flag access"""
        vpc_enabled = self.config.get('features.vpc_enabled')
        self.assertIsInstance(vpc_enabled, bool)
    
    def test_agent_config(self):
        """Test agent configuration access"""
        default_model = self.config.get('agents.default_model')
        self.assertIsNotNone(default_model)
        self.assertIn('claude', default_model.lower())


class TestResourceNamer(unittest.TestCase):
    """Test ResourceNamer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ConfigurationManager(environment='dev')
        self.namer = ResourceNamer(self.config)
    
    def test_s3_bucket_name(self):
        """Test S3 bucket name generation"""
        bucket_name = self.namer.s3_bucket('data')
        
        # Check format
        self.assertIn('data', bucket_name)
        self.assertIn(self.namer.prefix, bucket_name)
        
        # Check length constraint
        self.assertLessEqual(len(bucket_name), 63)
        
        # Check valid characters (lowercase, numbers, hyphens)
        self.assertTrue(all(c.islower() or c.isdigit() or c == '-' for c in bucket_name))
    
    def test_dynamodb_table_name(self):
        """Test DynamoDB table name generation"""
        table_name = self.namer.dynamodb_table('sessions')
        
        self.assertIn('sessions', table_name)
        self.assertIn(self.namer.prefix, table_name)
    
    def test_lambda_function_name(self):
        """Test Lambda function name generation"""
        function_name = self.namer.lambda_function('sql-executor')
        
        self.assertIn('sql-executor', function_name)
        self.assertIn(self.namer.prefix, function_name)
    
    def test_iam_role_name(self):
        """Test IAM role name generation"""
        role_name = self.namer.iam_role('lambda-exec')
        
        self.assertIn('lambda-exec', role_name)
        self.assertIn(self.namer.prefix, role_name)
    
    def test_log_group_name(self):
        """Test CloudWatch log group name generation"""
        log_group = self.namer.cloudwatch_log_group('lambda/sql-executor')
        
        self.assertTrue(log_group.startswith('/aws/lambda/'))
        self.assertIn('sql-executor', log_group)
    
    def test_parameter_store_path(self):
        """Test Parameter Store path generation"""
        param_path = self.namer.parameter_store_path('database-url')
        
        self.assertTrue(param_path.startswith('/'))
        self.assertIn('database-url', param_path)
        self.assertIn(self.namer.prefix, param_path)
    
    def test_secrets_manager_name(self):
        """Test Secrets Manager name generation"""
        secret_name = self.namer.secrets_manager_name('api-key')
        
        self.assertIn('api-key', secret_name)
        self.assertIn(self.namer.prefix, secret_name)
    
    def test_name_consistency(self):
        """Test that same input produces same output"""
        bucket1 = self.namer.s3_bucket('data')
        bucket2 = self.namer.s3_bucket('data')
        
        self.assertEqual(bucket1, bucket2)


class TestEnvironmentConfigs(unittest.TestCase):
    """Test different environment configurations"""
    
    def test_dev_config(self):
        """Test dev environment configuration"""
        config = ConfigurationManager(environment='dev')
        
        self.assertEqual(config.get('environment.name'), 'dev')
        self.assertFalse(config.get('features.vpc_enabled'))
        self.assertFalse(config.get('features.waf_enabled'))
    
    def test_staging_config(self):
        """Test staging environment configuration"""
        config = ConfigurationManager(environment='staging')
        
        self.assertEqual(config.get('environment.name'), 'staging')
        # Staging typically has more features enabled
        self.assertTrue(config.get('features.vpc_enabled'))
    
    def test_prod_config(self):
        """Test prod environment configuration"""
        config = ConfigurationManager(environment='prod')
        
        self.assertEqual(config.get('environment.name'), 'prod')
        # Production should have all features enabled
        self.assertTrue(config.get('features.vpc_enabled'))
        self.assertTrue(config.get('features.waf_enabled'))
        self.assertTrue(config.get('features.multi_az'))
    
    def test_resource_sizing_differences(self):
        """Test that resource sizing differs across environments"""
        dev_config = ConfigurationManager(environment='dev')
        prod_config = ConfigurationManager(environment='prod')
        
        dev_memory = dev_config.get('resources.lambda.memory_mb')
        prod_memory = prod_config.get('resources.lambda.memory_mb')
        
        # Production should have equal or more resources
        self.assertGreaterEqual(prod_memory, dev_memory)
        
        dev_concurrency = dev_config.get('resources.lambda.reserved_concurrency')
        prod_concurrency = prod_config.get('resources.lambda.reserved_concurrency')
        
        self.assertGreater(prod_concurrency, dev_concurrency)


class TestConfigurationValidation(unittest.TestCase):
    """Test configuration validation"""
    
    def test_invalid_environment(self):
        """Test loading invalid environment raises error"""
        with self.assertRaises(ConfigurationError):
            ConfigurationManager(environment='invalid')
    
    def test_schema_validation(self):
        """Test schema validation works"""
        # This should not raise an error
        config = ConfigurationManager(environment='dev')
        self.assertIsNotNone(config.schema)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestConfigurationManager))
    suite.addTests(loader.loadTestsFromTestCase(TestResourceNamer))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentConfigs))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigurationValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
