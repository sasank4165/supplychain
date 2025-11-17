"""Test script for ConversationContextManager

This script tests the conversation context management functionality
without requiring actual AWS resources.
"""

import sys
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime


def test_conversation_context_manager():
    """Test ConversationContextManager initialization and basic functionality"""
    
    print("Testing ConversationContextManager...")
    
    # Mock boto3 and DynamoDB
    with patch('conversation_context_manager.boto3') as mock_boto3:
        # Setup mocks
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_boto3.resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.client.return_value = MagicMock()
        
        # Mock ConfigurationManager
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default=None: {
            'dynamodb.conversation_table': 'test-conversations',
            'agents.context_window_size': 10,
            'agents.conversation_retention_days': 30,
            'agents.max_tokens_per_context': 4000,
            'agents.default_model': 'anthropic.claude-3-5-sonnet-20241022-v2:0'
        }.get(key, default)
        
        # Import after mocking
        from conversation_context_manager import ConversationContextManager
        
        # Test initialization
        context_manager = ConversationContextManager(
            config=mock_config,
            region='us-east-1'
        )
        
        print(f"✓ ConversationContextManager initialized: {context_manager}")
        print(f"  - Table name: {context_manager.table_name}")
        print(f"  - Context window size: {context_manager.context_window_size}")
        print(f"  - Retention days: {context_manager.conversation_retention_days}")
        print(f"  - Max tokens: {context_manager.max_tokens_per_context}")
        
        # Test add_message
        mock_table.put_item.return_value = {}
        result = context_manager.add_message(
            session_id='test-session-123',
            role='user',
            content='Show me inventory levels',
            persona='warehouse_manager'
        )
        
        print(f"\n✓ add_message result: {result}")
        assert result['success'] == True
        assert 'message_id' in result
        assert 'timestamp' in result
        
        # Test get_context
        mock_table.query.return_value = {
            'Items': [
                {
                    'message_id': 'test-session-123#2024-01-01T10:00:00',
                    'session_id': 'test-session-123',
                    'timestamp': '2024-01-01T10:00:00',
                    'role': 'user',
                    'content': 'Show me inventory levels',
                    'token_count': 5,
                    'persona': 'warehouse_manager'
                }
            ]
        }
        
        messages = context_manager.get_context('test-session-123')
        print(f"\n✓ get_context returned {len(messages)} messages")
        
        # Test clear_context
        mock_table.batch_writer.return_value.__enter__.return_value = MagicMock()
        result = context_manager.clear_context('test-session-123')
        print(f"\n✓ clear_context result: {result}")
        
        # Test get_session_summary
        summary = context_manager.get_session_summary('test-session-123')
        print(f"\n✓ get_session_summary: {summary}")
        
        print("\n✅ All ConversationContextManager tests passed!")
        return True


def test_orchestrator_integration():
    """Test orchestrator integration with ConversationContextManager"""
    
    print("\n\nTesting Orchestrator integration...")
    
    with patch('orchestrator.boto3') as mock_boto3, \
         patch('conversation_context_manager.boto3') as mock_ccm_boto3:
        
        # Setup mocks
        mock_boto3.client.return_value = MagicMock()
        mock_ccm_boto3.resource.return_value = MagicMock()
        mock_ccm_boto3.client.return_value = MagicMock()
        
        # Mock ConfigurationManager
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default=None: {
            'dynamodb.conversation_table': 'test-conversations',
            'agents.context_window_size': 10,
            'agents.conversation_retention_days': 30,
            'agents.max_tokens_per_context': 4000,
            'agents.default_model': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'project.prefix': 'test-agent'
        }.get(key, default)
        
        # Import after mocking
        from orchestrator import SupplyChainOrchestrator
        
        # Test initialization
        orchestrator = SupplyChainOrchestrator(region='us-east-1', config=mock_config)
        
        print(f"✓ Orchestrator initialized")
        print(f"  - Has context_manager: {orchestrator.context_manager is not None}")
        print(f"  - Has model_manager: {orchestrator.model_manager is not None}")
        
        # Test conversation history methods
        if orchestrator.context_manager:
            print("\n✓ Orchestrator has ConversationContextManager")
            
            # Test get_conversation_history
            history = orchestrator.get_conversation_history('test-session')
            print(f"  - get_conversation_history: {type(history)}")
            
            # Test get_session_summary
            summary = orchestrator.get_session_summary('test-session')
            print(f"  - get_session_summary: {type(summary)}")
        
        print("\n✅ All Orchestrator integration tests passed!")
        return True


def test_config_updates():
    """Test configuration file updates"""
    
    print("\n\nTesting configuration updates...")
    
    import yaml
    
    # Test dev.yaml
    with open('config/dev.yaml', 'r') as f:
        dev_config = yaml.safe_load(f)
    
    # Check conversation settings
    assert 'agents' in dev_config
    assert 'context_window_size' in dev_config['agents']
    assert 'conversation_retention_days' in dev_config['agents']
    assert 'max_tokens_per_context' in dev_config['agents']
    
    print("✓ dev.yaml has conversation context settings:")
    print(f"  - context_window_size: {dev_config['agents']['context_window_size']}")
    print(f"  - conversation_retention_days: {dev_config['agents']['conversation_retention_days']}")
    print(f"  - max_tokens_per_context: {dev_config['agents']['max_tokens_per_context']}")
    
    # Check DynamoDB table config
    assert 'dynamodb' in dev_config['resources']
    assert 'conversation_table' in dev_config['resources']['dynamodb']
    print(f"  - conversation_table: {dev_config['resources']['dynamodb']['conversation_table']}")
    
    print("\n✅ All configuration tests passed!")
    return True


if __name__ == '__main__':
    try:
        # Run tests
        test_conversation_context_manager()
        test_orchestrator_integration()
        test_config_updates()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
