"""Model Manager for Multi-Model Support in Supply Chain Agentic AI Application

This module provides centralized model selection, configuration, and fallback logic
for Amazon Bedrock models. It enables per-agent model configuration, compatibility
validation, and usage metrics collection.
"""

import boto3
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

from config_manager import ConfigurationManager


class ModelManagerError(Exception):
    """Raised when model operations fail"""
    pass


@dataclass
class ModelConfig:
    """Configuration for a Bedrock model"""
    model_id: str
    model_family: str  # claude, titan, llama, etc.
    max_tokens: int
    temperature: float
    supports_tools: bool
    supports_streaming: bool
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float


@dataclass
class ModelUsageMetrics:
    """Metrics for model usage"""
    agent_name: str
    model_id: str
    timestamp: datetime
    input_tokens: int
    output_tokens: int
    latency_ms: float
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def get_cost(self, model_config: ModelConfig) -> float:
        """Calculate cost for this usage"""
        input_cost = (self.input_tokens / 1000) * model_config.cost_per_1k_input_tokens
        output_cost = (self.output_tokens / 1000) * model_config.cost_per_1k_output_tokens
        return input_cost + output_cost


class ModelManager:
    """Manage AI model selection, configuration, and usage
    
    Provides centralized model management with:
    - Per-agent model configuration
    - Model fallback logic for unavailable models
    - Model compatibility validation
    - Usage metrics collection
    - Cost tracking
    
    Example:
        >>> config = ConfigurationManager('dev')
        >>> model_manager = ModelManager(config)
        >>> response = model_manager.invoke_model(
        ...     agent_name='sql_agent',
        ...     messages=[{"role": "user", "content": "Hello"}],
        ...     system_prompt="You are a helpful assistant"
        ... )
    """
    
    # Model catalog with capabilities and pricing
    MODEL_CATALOG: Dict[str, ModelConfig] = {
        "anthropic.claude-3-5-sonnet-20241022-v2:0": ModelConfig(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            model_family="claude",
            max_tokens=8192,
            temperature=1.0,
            supports_tools=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.003,
            cost_per_1k_output_tokens=0.015
        ),
        "anthropic.claude-3-5-haiku-20241022-v1:0": ModelConfig(
            model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
            model_family="claude",
            max_tokens=8192,
            temperature=1.0,
            supports_tools=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.001,
            cost_per_1k_output_tokens=0.005
        ),
        "anthropic.claude-3-opus-20240229-v1:0": ModelConfig(
            model_id="anthropic.claude-3-opus-20240229-v1:0",
            model_family="claude",
            max_tokens=4096,
            temperature=1.0,
            supports_tools=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.015,
            cost_per_1k_output_tokens=0.075
        ),
        "amazon.titan-text-premier-v1:0": ModelConfig(
            model_id="amazon.titan-text-premier-v1:0",
            model_family="titan",
            max_tokens=3072,
            temperature=1.0,
            supports_tools=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.0005,
            cost_per_1k_output_tokens=0.0015
        ),
        "meta.llama3-70b-instruct-v1:0": ModelConfig(
            model_id="meta.llama3-70b-instruct-v1:0",
            model_family="llama",
            max_tokens=2048,
            temperature=1.0,
            supports_tools=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.00265,
            cost_per_1k_output_tokens=0.0035
        )
    }
    
    def __init__(self, config: ConfigurationManager, region: Optional[str] = None):
        """Initialize model manager
        
        Args:
            config: ConfigurationManager instance
            region: AWS region (defaults to config region)
        """
        self.config = config
        self.region = region or config.get('environment.region', 'us-east-1')
        
        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=self.region)
        
        # Initialize CloudWatch for metrics
        self.cloudwatch = boto3.client('cloudwatch', region_name=self.region)
        self.metrics_namespace = f"{config.get('project.prefix', 'sc-agent')}/Models"
        
        # Cache for model availability
        self._model_availability_cache: Dict[str, Tuple[bool, float]] = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Usage metrics buffer
        self._metrics_buffer: List[ModelUsageMetrics] = []
        self._metrics_buffer_size = 10
        
        # Validate configured models at startup
        self._validate_configured_models()
    
    def _validate_configured_models(self):
        """Validate that all configured models are available and compatible
        
        Checks model availability and compatibility at startup to fail fast
        if there are configuration issues.
        """
        agents_config = self.config.get('agents', {})
        default_model = agents_config.get('default_model')
        
        models_to_validate = set()
        
        # Add default model
        if default_model:
            models_to_validate.add(default_model)
        
        # Add per-agent models
        for agent_name, agent_config in agents_config.items():
            if isinstance(agent_config, dict) and 'model' in agent_config:
                models_to_validate.add(agent_config['model'])
        
        # Validate each model
        validation_errors = []
        for model_id in models_to_validate:
            if model_id not in self.MODEL_CATALOG:
                validation_errors.append(
                    f"Model '{model_id}' not found in catalog. "
                    f"Available models: {list(self.MODEL_CATALOG.keys())}"
                )
            else:
                # Check if model is accessible
                if not self._check_model_availability(model_id):
                    validation_errors.append(
                        f"Model '{model_id}' is not accessible. "
                        "Ensure Bedrock model access is enabled in your AWS account."
                    )
        
        if validation_errors:
            error_msg = "Model validation failed:\n" + "\n".join(f"  - {err}" for err in validation_errors)
            print(f"Warning: {error_msg}")
            # Don't raise exception, just warn - allow fallback to work
    
    def _check_model_availability(self, model_id: str, use_cache: bool = True) -> bool:
        """Check if a model is available in Bedrock
        
        Args:
            model_id: Bedrock model ID
            use_cache: Whether to use cached availability status
            
        Returns:
            True if model is available, False otherwise
        """
        # Check cache first
        if use_cache and model_id in self._model_availability_cache:
            is_available, cached_time = self._model_availability_cache[model_id]
            if time.time() - cached_time < self._cache_ttl:
                return is_available
        
        # Test model availability with a minimal invocation
        try:
            # Use a minimal test prompt
            test_messages = [{"role": "user", "content": [{"text": "test"}]}]
            
            self.bedrock_runtime.converse(
                modelId=model_id,
                messages=test_messages,
                inferenceConfig={"maxTokens": 10}
            )
            
            # Cache the result
            self._model_availability_cache[model_id] = (True, time.time())
            return True
            
        except Exception as e:
            error_str = str(e)
            # Check if it's an access denied error vs other errors
            if "AccessDeniedException" in error_str or "access" in error_str.lower():
                print(f"Model '{model_id}' access denied: {error_str}")
            else:
                print(f"Model '{model_id}' availability check failed: {error_str}")
            
            # Cache the negative result
            self._model_availability_cache[model_id] = (False, time.time())
            return False
    
    def get_model_for_agent(self, agent_name: str) -> str:
        """Get configured model ID for an agent
        
        Args:
            agent_name: Agent name
            
        Returns:
            Bedrock model ID
            
        Example:
            >>> model_manager.get_model_for_agent('sql_agent')
            'anthropic.claude-3-5-sonnet-20241022-v2:0'
        """
        # Try to get agent-specific model
        agent_config = self.config.get(f'agents.{agent_name}', {})
        
        if isinstance(agent_config, dict) and 'model' in agent_config:
            return agent_config['model']
        
        # Fall back to default model
        default_model = self.config.get('agents.default_model')
        if default_model:
            return default_model
        
        # Ultimate fallback
        return "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def get_fallback_model(self, primary_model_id: str) -> Optional[str]:
        """Get fallback model for a primary model
        
        Fallback strategy:
        1. If primary is Claude Sonnet -> Claude Haiku (cheaper, faster)
        2. If primary is Claude Opus -> Claude Sonnet (cheaper)
        3. If primary is Claude Haiku -> Claude Sonnet (more capable)
        4. Otherwise -> Claude Sonnet (most balanced)
        
        Args:
            primary_model_id: Primary model ID
            
        Returns:
            Fallback model ID or None if no fallback available
        """
        fallback_map = {
            "anthropic.claude-3-5-sonnet-20241022-v2:0": "anthropic.claude-3-5-haiku-20241022-v1:0",
            "anthropic.claude-3-opus-20240229-v1:0": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-5-haiku-20241022-v1:0": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "amazon.titan-text-premier-v1:0": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "meta.llama3-70b-instruct-v1:0": "anthropic.claude-3-5-sonnet-20241022-v2:0"
        }
        
        fallback = fallback_map.get(primary_model_id)
        
        # Verify fallback is available
        if fallback and self._check_model_availability(fallback):
            return fallback
        
        # If fallback not available, try default Claude Sonnet
        default_fallback = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        if fallback != default_fallback and self._check_model_availability(default_fallback):
            return default_fallback
        
        return None
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """Get model configuration
        
        Args:
            model_id: Bedrock model ID
            
        Returns:
            ModelConfig or None if not found
        """
        return self.MODEL_CATALOG.get(model_id)
    
    def validate_model_compatibility(
        self,
        model_id: str,
        requires_tools: bool = False,
        requires_streaming: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Validate model compatibility with requirements
        
        Args:
            model_id: Bedrock model ID
            requires_tools: Whether tools support is required
            requires_streaming: Whether streaming support is required
            
        Returns:
            Tuple of (is_compatible, error_message)
        """
        model_config = self.get_model_config(model_id)
        
        if not model_config:
            return False, f"Model '{model_id}' not found in catalog"
        
        if requires_tools and not model_config.supports_tools:
            return False, f"Model '{model_id}' does not support tools"
        
        if requires_streaming and not model_config.supports_streaming:
            return False, f"Model '{model_id}' does not support streaming"
        
        return True, None

    
    def invoke_model(
        self,
        agent_name: str,
        messages: List[Dict[str, Any]],
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_fallback: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Invoke Bedrock model with automatic fallback support
        
        Args:
            agent_name: Name of the agent making the request
            messages: List of message dictionaries for Converse API
            system_prompt: Optional system prompt
            tools: Optional list of tool definitions
            max_tokens: Maximum tokens to generate (defaults to model config)
            temperature: Temperature for generation (defaults to model config)
            use_fallback: Whether to use fallback model on failure
            **kwargs: Additional parameters for Converse API
            
        Returns:
            Dictionary with response and metadata
            
        Raises:
            ModelManagerError: If invocation fails and no fallback available
            
        Example:
            >>> response = model_manager.invoke_model(
            ...     agent_name='sql_agent',
            ...     messages=[{"role": "user", "content": [{"text": "Hello"}]}],
            ...     system_prompt="You are a SQL expert"
            ... )
        """
        # Get model for agent
        model_id = self.get_model_for_agent(agent_name)
        model_config = self.get_model_config(model_id)
        
        if not model_config:
            raise ModelManagerError(f"Model configuration not found for '{model_id}'")
        
        # Validate compatibility if tools are provided
        if tools:
            is_compatible, error_msg = self.validate_model_compatibility(
                model_id, requires_tools=True
            )
            if not is_compatible:
                raise ModelManagerError(error_msg)
        
        # Try primary model
        start_time = time.time()
        try:
            response = self._invoke_bedrock_converse(
                model_id=model_id,
                messages=messages,
                system_prompt=system_prompt,
                tools=tools,
                max_tokens=max_tokens or model_config.max_tokens,
                temperature=temperature if temperature is not None else 0.0,
                **kwargs
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract token usage
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            
            # Record metrics
            self._record_usage_metrics(
                agent_name=agent_name,
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                success=True
            )
            
            return {
                "success": True,
                "model_id": model_id,
                "response": response,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                },
                "latency_ms": latency_ms,
                "cost": self._calculate_cost(model_config, input_tokens, output_tokens)
            }
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            # Record failed attempt
            self._record_usage_metrics(
                agent_name=agent_name,
                model_id=model_id,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                success=False,
                error_message=error_msg
            )
            
            # Try fallback if enabled
            if use_fallback:
                fallback_model = self.get_fallback_model(model_id)
                if fallback_model:
                    print(f"Primary model '{model_id}' failed, trying fallback '{fallback_model}'")
                    
                    try:
                        return self._invoke_with_fallback(
                            agent_name=agent_name,
                            fallback_model=fallback_model,
                            messages=messages,
                            system_prompt=system_prompt,
                            tools=tools,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            **kwargs
                        )
                    except Exception as fallback_error:
                        raise ModelManagerError(
                            f"Both primary model '{model_id}' and fallback '{fallback_model}' failed. "
                            f"Primary error: {error_msg}. Fallback error: {str(fallback_error)}"
                        )
            
            raise ModelManagerError(f"Model invocation failed: {error_msg}")
    
    def _invoke_with_fallback(
        self,
        agent_name: str,
        fallback_model: str,
        messages: List[Dict[str, Any]],
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Invoke fallback model
        
        Internal method for fallback invocation with metrics tracking.
        """
        model_config = self.get_model_config(fallback_model)
        if not model_config:
            raise ModelManagerError(f"Fallback model configuration not found for '{fallback_model}'")
        
        start_time = time.time()
        
        response = self._invoke_bedrock_converse(
            model_id=fallback_model,
            messages=messages,
            system_prompt=system_prompt,
            tools=tools,
            max_tokens=max_tokens or model_config.max_tokens,
            temperature=temperature if temperature is not None else 0.0,
            **kwargs
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Extract token usage
        usage = response.get('usage', {})
        input_tokens = usage.get('inputTokens', 0)
        output_tokens = usage.get('outputTokens', 0)
        
        # Record metrics
        self._record_usage_metrics(
            agent_name=agent_name,
            model_id=fallback_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=True
        )
        
        return {
            "success": True,
            "model_id": fallback_model,
            "fallback_used": True,
            "response": response,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            },
            "latency_ms": latency_ms,
            "cost": self._calculate_cost(model_config, input_tokens, output_tokens)
        }
    
    def _invoke_bedrock_converse(
        self,
        model_id: str,
        messages: List[Dict[str, Any]],
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        **kwargs
    ) -> Dict[str, Any]:
        """Invoke Bedrock Converse API
        
        Internal method that handles the actual Bedrock API call.
        """
        # Build request parameters
        request_params = {
            "modelId": model_id,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            request_params["system"] = [{"text": system_prompt}]
        
        # Add tools if provided
        if tools:
            request_params["toolConfig"] = {"tools": tools}
        
        # Add any additional parameters
        request_params.update(kwargs)
        
        # Invoke the model
        response = self.bedrock_runtime.converse(**request_params)
        
        return response
    
    def _calculate_cost(
        self,
        model_config: ModelConfig,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for model usage
        
        Args:
            model_config: Model configuration
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        input_cost = (input_tokens / 1000) * model_config.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000) * model_config.cost_per_1k_output_tokens
        return input_cost + output_cost
    
    def _record_usage_metrics(
        self,
        agent_name: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Record model usage metrics
        
        Buffers metrics and publishes to CloudWatch in batches.
        """
        metrics = ModelUsageMetrics(
            agent_name=agent_name,
            model_id=model_id,
            timestamp=datetime.utcnow(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message
        )
        
        # Add to buffer
        self._metrics_buffer.append(metrics)
        
        # Publish if buffer is full
        if len(self._metrics_buffer) >= self._metrics_buffer_size:
            self._publish_metrics()
    
    def _publish_metrics(self):
        """Publish buffered metrics to CloudWatch
        
        Publishes metrics in batch to reduce API calls.
        """
        if not self._metrics_buffer:
            return
        
        try:
            metric_data = []
            
            for metrics in self._metrics_buffer:
                model_config = self.get_model_config(metrics.model_id)
                cost = metrics.get_cost(model_config) if model_config else 0.0
                
                # Latency metric
                metric_data.append({
                    'MetricName': 'ModelLatency',
                    'Value': metrics.latency_ms,
                    'Unit': 'Milliseconds',
                    'Timestamp': metrics.timestamp,
                    'Dimensions': [
                        {'Name': 'Agent', 'Value': metrics.agent_name},
                        {'Name': 'Model', 'Value': metrics.model_id}
                    ]
                })
                
                # Token usage metrics
                metric_data.append({
                    'MetricName': 'InputTokens',
                    'Value': metrics.input_tokens,
                    'Unit': 'Count',
                    'Timestamp': metrics.timestamp,
                    'Dimensions': [
                        {'Name': 'Agent', 'Value': metrics.agent_name},
                        {'Name': 'Model', 'Value': metrics.model_id}
                    ]
                })
                
                metric_data.append({
                    'MetricName': 'OutputTokens',
                    'Value': metrics.output_tokens,
                    'Unit': 'Count',
                    'Timestamp': metrics.timestamp,
                    'Dimensions': [
                        {'Name': 'Agent', 'Value': metrics.agent_name},
                        {'Name': 'Model', 'Value': metrics.model_id}
                    ]
                })
                
                # Success/failure metric
                metric_data.append({
                    'MetricName': 'ModelInvocations',
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': metrics.timestamp,
                    'Dimensions': [
                        {'Name': 'Agent', 'Value': metrics.agent_name},
                        {'Name': 'Model', 'Value': metrics.model_id},
                        {'Name': 'Success', 'Value': str(metrics.success)}
                    ]
                })
                
                # Cost metric
                metric_data.append({
                    'MetricName': 'ModelCost',
                    'Value': cost,
                    'Unit': 'None',
                    'Timestamp': metrics.timestamp,
                    'Dimensions': [
                        {'Name': 'Agent', 'Value': metrics.agent_name},
                        {'Name': 'Model', 'Value': metrics.model_id}
                    ]
                })
            
            # Publish to CloudWatch (max 1000 metrics per call)
            for i in range(0, len(metric_data), 1000):
                batch = metric_data[i:i+1000]
                self.cloudwatch.put_metric_data(
                    Namespace=self.metrics_namespace,
                    MetricData=batch
                )
            
            # Clear buffer
            self._metrics_buffer.clear()
            
        except Exception as e:
            print(f"Warning: Failed to publish metrics to CloudWatch: {str(e)}")
            # Don't raise - metrics publishing failure shouldn't break the application
    
    def flush_metrics(self):
        """Flush any buffered metrics to CloudWatch
        
        Call this before application shutdown to ensure all metrics are published.
        """
        self._publish_metrics()
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of buffered usage metrics
        
        Returns:
            Dictionary with usage statistics
        """
        if not self._metrics_buffer:
            return {"message": "No metrics in buffer"}
        
        total_input_tokens = sum(m.input_tokens for m in self._metrics_buffer)
        total_output_tokens = sum(m.output_tokens for m in self._metrics_buffer)
        total_latency = sum(m.latency_ms for m in self._metrics_buffer)
        success_count = sum(1 for m in self._metrics_buffer if m.success)
        
        # Calculate total cost
        total_cost = 0.0
        for metrics in self._metrics_buffer:
            model_config = self.get_model_config(metrics.model_id)
            if model_config:
                total_cost += metrics.get_cost(model_config)
        
        return {
            "total_invocations": len(self._metrics_buffer),
            "successful_invocations": success_count,
            "failed_invocations": len(self._metrics_buffer) - success_count,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "average_latency_ms": total_latency / len(self._metrics_buffer),
            "total_cost_usd": round(total_cost, 4),
            "models_used": list(set(m.model_id for m in self._metrics_buffer)),
            "agents_used": list(set(m.agent_name for m in self._metrics_buffer))
        }
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models with their capabilities
        
        Returns:
            List of model information dictionaries
        """
        models = []
        for model_id, config in self.MODEL_CATALOG.items():
            models.append({
                "model_id": model_id,
                "model_family": config.model_family,
                "max_tokens": config.max_tokens,
                "supports_tools": config.supports_tools,
                "supports_streaming": config.supports_streaming,
                "cost_per_1k_input_tokens": config.cost_per_1k_input_tokens,
                "cost_per_1k_output_tokens": config.cost_per_1k_output_tokens,
                "available": self._check_model_availability(model_id)
            })
        return models
    
    def __repr__(self) -> str:
        return f"ModelManager(region='{self.region}', models={len(self.MODEL_CATALOG)})"


# Convenience function for quick access
def create_model_manager(config: Optional[ConfigurationManager] = None) -> ModelManager:
    """Create ModelManager instance
    
    Args:
        config: Optional ConfigurationManager instance
        
    Returns:
        ModelManager instance
    """
    if config is None:
        config = ConfigurationManager()
    
    return ModelManager(config)
