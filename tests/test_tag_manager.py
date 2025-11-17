"""Unit tests for TagManager class"""
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigurationManager, TagManager


class TestTagManager(unittest.TestCase):
    """Test TagManager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ConfigurationManager(environment='dev')
        self.tag_manager = TagManager(self.config)
    
    def test_standard_tags_generated(self):
        """Test that standard tags are generated correctly"""
        standard_tags = self.tag_manager.get_standard_tags()
        
        # Check required standard tags exist
        required_keys = ['Project', 'Environment', 'ManagedBy', 'Owner', 'CostCenter']
        for key in required_keys:
            self.assertIn(key, standard_tags)
            self.assertIsNotNone(standard_tags[key])
    
    def test_custom_tags_loaded(self):
        """Test that custom tags are loaded from configuration"""
        custom_tags = self.tag_manager.get_custom_tags()
        
        # Custom tags should be a dictionary
        self.assertIsInstance(custom_tags, dict)
    
    def test_get_all_tags(self):
        """Test getting all tags (standard + custom)"""
        all_tags = self.tag_manager.get_tags()
        
        # Should contain both standard and custom tags
        self.assertIn('Project', all_tags)
        self.assertIn('Environment', all_tags)
        self.assertGreaterEqual(len(all_tags), 5)
    
    def test_additional_tags_merge(self):
        """Test merging additional tags"""
        additional = {'Component': 'Lambda', 'Function': 'TestFunc'}
        tags = self.tag_manager.get_tags(additional)
        
        # Should contain standard tags plus additional
        self.assertIn('Project', tags)
        self.assertIn('Component', tags)
        self.assertIn('Function', tags)
        self.assertEqual(tags['Component'], 'Lambda')
    
    def test_tag_validation_valid(self):
        """Test validation of valid tags"""
        valid_tags = {
            'Project': 'test-project',
            'Environment': 'dev',
            'Owner': 'team@example.com'
        }
        
        for key, value in valid_tags.items():
            self.assertTrue(self.tag_manager._validate_tag(key, value))
    
    def test_tag_validation_invalid_key_length(self):
        """Test validation rejects keys that are too long"""
        long_key = 'a' * 129  # Max is 128
        self.assertFalse(self.tag_manager._validate_tag(long_key, 'value'))
    
    def test_tag_validation_invalid_value_length(self):
        """Test validation rejects values that are too long"""
        long_value = 'a' * 257  # Max is 256
        self.assertFalse(self.tag_manager._validate_tag('key', long_value))
    
    def test_tag_validation_reserved_prefix(self):
        """Test validation rejects reserved AWS prefixes"""
        self.assertFalse(self.tag_manager._validate_tag('aws:test', 'value'))
        self.assertFalse(self.tag_manager._validate_tag('AWS:test', 'value'))
    
    def test_tag_validation_special_characters(self):
        """Test validation allows valid special characters"""
        valid_chars = {
            'test-key': 'test-value',
            'test_key': 'test_value',
            'test.key': 'test.value',
            'test:key': 'test:value',
            'test/key': 'test/value',
            'test@key': 'test@value'
        }
        
        for key, value in valid_chars.items():
            self.assertTrue(self.tag_manager._validate_tag(key, value))
    
    def test_required_tags_validation_pass(self):
        """Test required tags validation passes with all tags"""
        tags = self.tag_manager.get_tags()
        is_valid, missing = self.tag_manager.validate_required_tags(tags)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)
    
    def test_required_tags_validation_fail(self):
        """Test required tags validation fails with missing tags"""
        incomplete_tags = {'Project': 'test'}
        is_valid, missing = self.tag_manager.validate_required_tags(incomplete_tags)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(missing), 0)
    
    def test_cloudformation_format(self):
        """Test CloudFormation tag format"""
        cf_tags = self.tag_manager.format_tags_for_cloudformation()
        
        # Should be a list of dicts with Key and Value
        self.assertIsInstance(cf_tags, list)
        for tag in cf_tags:
            self.assertIn('Key', tag)
            self.assertIn('Value', tag)
    
    def test_cost_allocation_tags(self):
        """Test cost allocation tags extraction"""
        cost_tags = self.tag_manager.get_cost_allocation_tags()
        
        # Should contain key cost-related tags
        expected_keys = ['CostCenter', 'Environment', 'Project', 'Owner']
        for key in expected_keys:
            self.assertIn(key, cost_tags)
    
    def test_tag_manager_repr(self):
        """Test string representation"""
        repr_str = repr(self.tag_manager)
        self.assertIn('TagManager', repr_str)
        self.assertIn('tags=', repr_str)


class TestTagManagerIntegration(unittest.TestCase):
    """Integration tests for TagManager with different environments"""
    
    def test_dev_environment_tags(self):
        """Test tags for dev environment"""
        config = ConfigurationManager(environment='dev')
        tag_manager = TagManager(config)
        tags = tag_manager.get_tags()
        
        self.assertEqual(tags['Environment'], 'dev')
        self.assertIn('Project', tags)
    
    def test_prod_environment_tags(self):
        """Test tags for prod environment"""
        config = ConfigurationManager(environment='prod')
        tag_manager = TagManager(config)
        tags = tag_manager.get_tags()
        
        self.assertEqual(tags['Environment'], 'prod')
        self.assertIn('Project', tags)
        
        # Prod should have additional compliance tags
        custom_tags = tag_manager.get_custom_tags()
        self.assertIn('Compliance', custom_tags)
        self.assertIn('DataClassification', custom_tags)


if __name__ == '__main__':
    unittest.main()
