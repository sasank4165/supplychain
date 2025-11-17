"""Conversation Context Management System

This module provides conversation history management with:
- DynamoDB-based conversation storage with TTL
- Configurable context window sizes
- Conversation summarization when context exceeds token limits
- Session-based context retrieval
- Integration with ConfigurationManager
"""

import boto3
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from config_manager import ConfigurationManager


class ConversationContextManager:
    """Manage conversation history and context
    
    Provides conversation history storage, retrieval, and summarization
    capabilities for multi-turn agent interactions.
    """
    
    def __init__(
        self,
        config: ConfigurationManager,
        region: str = "us-east-1",
        model_manager = None
    ):
        """Initialize conversation context manager
        
        Args:
            config: ConfigurationManager instance
            region: AWS region
            model_manager: Optional ModelManager for summarization
        """
        self.config = config
        self.region = region
        self.model_manager = model_manager
        
        # Get DynamoDB table name from config or environment
        import os
        table_name = config.get('dynamodb.conversation_table')
        if not table_name:
            # Try environment variable
            table_name = os.getenv('CONVERSATION_TABLE') or os.getenv('DYNAMODB_CONVERSATION_TABLE')
        if not table_name:
            # Fallback to resource namer
            from config_manager import ResourceNamer
            namer = ResourceNamer(config)
            table_name = namer.dynamodb_table('conversations')
        
        self.table_name = table_name
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        
        # Get configuration values
        self.context_window_size = config.get('agents.context_window_size', 10)
        self.conversation_retention_days = config.get('agents.conversation_retention_days', 30)
        self.max_tokens_per_context = config.get('agents.max_tokens_per_context', 4000)
        
        # Initialize Bedrock client for summarization
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        persona: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add message to conversation history
        
        Args:
            session_id: Unique session identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata (agent name, tools used, etc.)
            persona: Optional persona identifier
            
        Returns:
            Dictionary with message details
            
        Example:
            >>> context_manager.add_message(
            ...     session_id='sess-123',
            ...     role='user',
            ...     content='Show me inventory levels',
            ...     persona='warehouse_manager'
            ... )
        """
        timestamp = datetime.utcnow().isoformat()
        message_id = f"{session_id}#{timestamp}"
        
        # Calculate TTL (retention days from now)
        ttl = int((datetime.utcnow() + timedelta(days=self.conversation_retention_days)).timestamp())
        
        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        token_count = len(content) // 4
        
        item = {
            'message_id': message_id,
            'session_id': session_id,
            'timestamp': timestamp,
            'role': role,
            'content': content,
            'token_count': token_count,
            'ttl': ttl
        }
        
        # Add optional fields
        if metadata:
            item['metadata'] = self._convert_floats_to_decimal(metadata)
        
        if persona:
            item['persona'] = persona
        
        try:
            self.table.put_item(Item=item)
            return {
                'success': True,
                'message_id': message_id,
                'timestamp': timestamp,
                'token_count': token_count
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_context(
        self,
        session_id: str,
        max_messages: Optional[int] = None,
        include_system: bool = True
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation context for a session
        
        Args:
            session_id: Session identifier
            max_messages: Maximum number of messages to retrieve (defaults to context_window_size)
            include_system: Whether to include system messages
            
        Returns:
            List of message dictionaries ordered by timestamp
            
        Example:
            >>> messages = context_manager.get_context('sess-123', max_messages=5)
            >>> for msg in messages:
            ...     print(f"{msg['role']}: {msg['content']}")
        """
        max_messages = max_messages or self.context_window_size
        
        try:
            # Query messages for this session
            response = self.table.query(
                IndexName='session-timestamp-index',
                KeyConditionExpression='session_id = :sid',
                ExpressionAttributeValues={
                    ':sid': session_id
                },
                ScanIndexForward=False,  # Most recent first
                Limit=max_messages * 2  # Get extra in case we filter system messages
            )
            
            messages = response.get('Items', [])
            
            # Filter system messages if requested
            if not include_system:
                messages = [msg for msg in messages if msg.get('role') != 'system']
            
            # Limit to max_messages
            messages = messages[:max_messages]
            
            # Reverse to get chronological order
            messages.reverse()
            
            # Convert Decimal to float for JSON serialization
            messages = [self._convert_decimals_to_float(msg) for msg in messages]
            
            # Check if summarization is needed
            total_tokens = sum(msg.get('token_count', 0) for msg in messages)
            if total_tokens > self.max_tokens_per_context:
                messages = self._summarize_context(session_id, messages)
            
            return messages
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []
    
    def get_recent_messages(
        self,
        session_id: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """Get the most recent messages from a session
        
        Args:
            session_id: Session identifier
            count: Number of recent messages to retrieve
            
        Returns:
            List of recent message dictionaries
        """
        return self.get_context(session_id, max_messages=count)
    
    def _summarize_context(
        self,
        session_id: str,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Summarize conversation when context exceeds token limits
        
        Args:
            session_id: Session identifier
            messages: List of messages to summarize
            
        Returns:
            List with summary message and recent messages
        """
        if not self.model_manager and not self.bedrock_runtime:
            # Can't summarize without model access, just truncate
            return messages[-self.context_window_size:]
        
        try:
            # Keep the most recent messages, summarize the older ones
            recent_count = max(3, self.context_window_size // 2)
            messages_to_summarize = messages[:-recent_count]
            recent_messages = messages[-recent_count:]
            
            if not messages_to_summarize:
                return messages
            
            # Build conversation text for summarization
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in messages_to_summarize
            ])
            
            # Get model ID for summarization
            if self.model_manager:
                model_id = self.model_manager.get_model_for_agent('default')
            else:
                model_id = self.config.get(
                    'agents.default_model',
                    'anthropic.claude-3-5-sonnet-20241022-v2:0'
                )
            
            # Create summarization prompt
            system_prompt = """You are a conversation summarizer. Summarize the following conversation 
            concisely while preserving key information, decisions, and context. Focus on facts, 
            data points, and important details that would be needed for future conversation turns."""
            
            messages_payload = [{
                "role": "user",
                "content": [{
                    "text": f"Summarize this conversation:\n\n{conversation_text}"
                }]
            }]
            
            # Call Bedrock for summarization
            response = self.bedrock_runtime.converse(
                modelId=model_id,
                messages=messages_payload,
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": 500,
                    "temperature": 0.3
                }
            )
            
            summary = response['output']['message']['content'][0]['text']
            
            # Create summary message
            summary_message = {
                'message_id': f"{session_id}#summary#{int(time.time())}",
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'role': 'system',
                'content': f"[Conversation Summary]: {summary}",
                'token_count': len(summary) // 4,
                'metadata': {
                    'is_summary': True,
                    'summarized_messages': len(messages_to_summarize)
                }
            }
            
            # Store summary in DynamoDB
            self.add_message(
                session_id=session_id,
                role='system',
                content=summary_message['content'],
                metadata=summary_message['metadata']
            )
            
            # Return summary + recent messages
            return [summary_message] + recent_messages
            
        except Exception as e:
            print(f"Error summarizing context: {e}")
            # Fallback to truncation
            return messages[-self.context_window_size:]
    
    def clear_context(self, session_id: str) -> Dict[str, Any]:
        """Clear conversation history for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Query all messages for this session
            response = self.table.query(
                IndexName='session-timestamp-index',
                KeyConditionExpression='session_id = :sid',
                ExpressionAttributeValues={
                    ':sid': session_id
                }
            )
            
            messages = response.get('Items', [])
            
            # Delete each message
            deleted_count = 0
            with self.table.batch_writer() as batch:
                for message in messages:
                    batch.delete_item(
                        Key={
                            'message_id': message['message_id'],
                            'timestamp': message['timestamp']
                        }
                    )
                    deleted_count += 1
            
            return {
                'success': True,
                'deleted_count': deleted_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session statistics
        """
        try:
            messages = self.get_context(session_id, max_messages=1000)
            
            total_messages = len(messages)
            total_tokens = sum(msg.get('token_count', 0) for msg in messages)
            
            role_counts = {}
            for msg in messages:
                role = msg.get('role', 'unknown')
                role_counts[role] = role_counts.get(role, 0) + 1
            
            first_message = messages[0] if messages else None
            last_message = messages[-1] if messages else None
            
            return {
                'session_id': session_id,
                'total_messages': total_messages,
                'total_tokens': total_tokens,
                'role_counts': role_counts,
                'first_message_time': first_message['timestamp'] if first_message else None,
                'last_message_time': last_message['timestamp'] if last_message else None
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def get_context_for_agent(
        self,
        session_id: str,
        agent_name: str,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation context filtered for a specific agent
        
        Args:
            session_id: Session identifier
            agent_name: Name of the agent
            max_messages: Maximum number of messages
            
        Returns:
            List of relevant messages for the agent
        """
        messages = self.get_context(session_id, max_messages)
        
        # Filter messages relevant to this agent
        # Include all user messages and assistant messages from this agent
        relevant_messages = []
        for msg in messages:
            if msg.get('role') == 'user':
                relevant_messages.append(msg)
            elif msg.get('role') == 'assistant':
                metadata = msg.get('metadata', {})
                if metadata.get('agent_name') == agent_name:
                    relevant_messages.append(msg)
            elif msg.get('role') == 'system':
                # Include system messages (like summaries)
                relevant_messages.append(msg)
        
        return relevant_messages
    
    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """Convert floats to Decimal for DynamoDB storage
        
        Args:
            obj: Object to convert
            
        Returns:
            Object with floats converted to Decimal
        """
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        return obj
    
    def _convert_decimals_to_float(self, obj: Any) -> Any:
        """Convert Decimal to float for JSON serialization
        
        Args:
            obj: Object to convert
            
        Returns:
            Object with Decimals converted to float
        """
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimals_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals_to_float(item) for item in obj]
        return obj
    
    def __repr__(self) -> str:
        return f"ConversationContextManager(table='{self.table_name}', window_size={self.context_window_size})"


# Convenience function
def create_context_manager(
    config: ConfigurationManager = None,
    region: str = "us-east-1"
) -> ConversationContextManager:
    """Create a ConversationContextManager instance
    
    Args:
        config: Optional ConfigurationManager instance
        region: AWS region
        
    Returns:
        ConversationContextManager instance
    """
    if config is None:
        config = ConfigurationManager()
    
    return ConversationContextManager(config, region)
