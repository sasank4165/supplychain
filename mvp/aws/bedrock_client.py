"""
Amazon Bedrock Client Wrapper

Provides a simplified interface for interacting with Amazon Bedrock Converse API.
"""

import boto3
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class TokenUsage:
    """Token usage information from Bedrock API."""
    input_tokens: int
    output_tokens: int
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens


@dataclass
class BedrockResponse:
    """Response from Bedrock API."""
    content: str
    token_usage: TokenUsage
    stop_reason: str
    tool_use: Optional[List[Dict[str, Any]]] = None


class BedrockClientError(Exception):
    """Raised when Bedrock API call fails."""
    pass


class BedrockClient:
    """Client for Amazon Bedrock Converse API."""
    
    def __init__(self, region: str, model_id: str, max_tokens: int = 4096, temperature: float = 0.0):
        """
        Initialize Bedrock client.
        
        Args:
            region: AWS region
            model_id: Bedrock model ID (e.g., anthropic.claude-3-5-sonnet-20241022-v2:0)
            max_tokens: Maximum tokens in response
            temperature: Model temperature (0.0 = deterministic)
        """
        self.region = region
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        try:
            self.client = boto3.client('bedrock-runtime', region_name=region)
        except Exception as e:
            raise BedrockClientError(f"Failed to initialize Bedrock client: {e}")
    
    def converse(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None
    ) -> BedrockResponse:
        """
        Send a conversation request to Bedrock.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system: Optional system prompts
            tools: Optional tool definitions for tool calling
            tool_choice: Optional tool choice configuration
            
        Returns:
            BedrockResponse with content and token usage
            
        Raises:
            BedrockClientError: If API call fails
        """
        try:
            # Build request parameters
            request_params = {
                'modelId': self.model_id,
                'messages': messages,
                'inferenceConfig': {
                    'maxTokens': self.max_tokens,
                    'temperature': self.temperature
                }
            }
            
            # Add system prompts if provided
            if system:
                request_params['system'] = system
            
            # Add tools if provided
            if tools:
                tool_config = {'tools': tools}
                if tool_choice:
                    tool_config['toolChoice'] = tool_choice
                request_params['toolConfig'] = tool_config
            
            # Make API call
            response = self.client.converse(**request_params)
            
            # Extract response content
            output = response.get('output', {})
            message = output.get('message', {})
            content_blocks = message.get('content', [])
            
            # Extract text content
            text_content = ""
            tool_use_blocks = []
            
            for block in content_blocks:
                if 'text' in block:
                    text_content += block['text']
                elif 'toolUse' in block:
                    tool_use_blocks.append(block['toolUse'])
            
            # Extract token usage
            usage = response.get('usage', {})
            token_usage = TokenUsage(
                input_tokens=usage.get('inputTokens', 0),
                output_tokens=usage.get('outputTokens', 0)
            )
            
            # Extract stop reason
            stop_reason = response.get('stopReason', 'unknown')
            
            return BedrockResponse(
                content=text_content,
                token_usage=token_usage,
                stop_reason=stop_reason,
                tool_use=tool_use_blocks if tool_use_blocks else None
            )
            
        except self.client.exceptions.ThrottlingException as e:
            raise BedrockClientError(f"Bedrock API throttled: {e}")
        except self.client.exceptions.ValidationException as e:
            raise BedrockClientError(f"Invalid request to Bedrock: {e}")
        except self.client.exceptions.ModelTimeoutException as e:
            raise BedrockClientError(f"Bedrock model timeout: {e}")
        except Exception as e:
            raise BedrockClientError(f"Bedrock API error: {e}")
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> BedrockResponse:
        """
        Generate text from a simple prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            BedrockResponse with generated text
        """
        messages = [
            {
                'role': 'user',
                'content': [{'text': prompt}]
            }
        ]
        
        system = None
        if system_prompt:
            system = [{'text': system_prompt}]
        
        return self.converse(messages=messages, system=system)
    
    def converse_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system: Optional[List[Dict[str, str]]] = None
    ) -> BedrockResponse:
        """
        Converse with tool calling enabled.
        
        Args:
            messages: Conversation messages
            tools: Tool definitions
            system: Optional system prompts
            
        Returns:
            BedrockResponse with potential tool use
        """
        return self.converse(
            messages=messages,
            system=system,
            tools=tools,
            tool_choice={'auto': {}}
        )
    
    def format_message(self, role: str, content: str) -> Dict[str, Any]:
        """
        Format a message for Bedrock API.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            
        Returns:
            Formatted message dictionary
        """
        return {
            'role': role,
            'content': [{'text': content}]
        }
    
    def format_tool_result(self, tool_use_id: str, content: Any) -> Dict[str, Any]:
        """
        Format a tool result for Bedrock API.
        
        Args:
            tool_use_id: ID of the tool use from previous response
            content: Tool result content
            
        Returns:
            Formatted tool result block
        """
        return {
            'toolResult': {
                'toolUseId': tool_use_id,
                'content': [{'json': content if isinstance(content, dict) else {'result': str(content)}}]
            }
        }
