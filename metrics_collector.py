"""Metrics Collection and Analytics System for Supply Chain Agentic AI Application

This module provides comprehensive monitoring and analytics capabilities:
- CloudWatch metrics publishing for agent performance
- Structured logging for all agent interactions
- Error tracking with context capture
- Custom business metrics per agent type
- Performance analytics and reporting
"""

import boto3
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from config_manager import ConfigurationManager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False


class MetricType(Enum):
    """Types of metrics that can be collected"""
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    TOKEN_USAGE = "token_usage"
    ERROR_RATE = "error_rate"
    TOOL_EXECUTION = "tool_execution"
    QUERY_COUNT = "query_count"
    BUSINESS_METRIC = "business_metric"


@dataclass
class AgentMetrics:
    """Agent performance metrics data structure"""
    persona: str
    agent_name: str
    query: str
    timestamp: datetime
    latency_ms: float
    success: bool
    error_message: Optional[str] = None
    token_count: int = 0
    tool_executions: List[Dict] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    intent: Optional[str] = None
    
    def __post_init__(self):
        if self.tool_executions is None:
            self.tool_executions = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class MetricsCollector:
    """Collect and publish agent metrics to CloudWatch
    
    Provides comprehensive monitoring capabilities including:
    - Performance metrics (latency, success rate)
    - Token usage tracking
    - Error tracking with context
    - Custom business metrics
    - Structured logging
    """
    
    def __init__(
        self,
        region: str = "us-east-1",
        config: Optional['ConfigurationManager'] = None,
        namespace: Optional[str] = None
    ):
        """Initialize metrics collector
        
        Args:
            region: AWS region
            config: Optional ConfigurationManager instance
            namespace: CloudWatch namespace (defaults to config or 'SupplyChainAgent/Metrics')
        """
        self.region = region
        self.config = config
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
        # Determine namespace
        if namespace:
            self.namespace = namespace
        elif config:
            prefix = config.get('project.prefix', 'supply-chain-agent')
            self.namespace = f"{prefix}/Agents"
        else:
            self.namespace = "SupplyChainAgent/Agents"
        
        # Initialize structured logger
        self.logger = self._setup_logger()
        
        # Metrics buffer for batch publishing
        self.metrics_buffer: List[Dict] = []
        self.buffer_size = 20  # Publish when buffer reaches this size
        
        # Statistics tracking
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_latency_ms': 0,
            'total_tokens': 0
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured JSON logger for agent interactions"""
        logger = logging.getLogger('agent_metrics')
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        logger.handlers = []
        
        # Create console handler with JSON formatter
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # JSON formatter for structured logging
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": %(message)s}'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def record_query(
        self,
        persona: str,
        agent: str,
        query: str,
        latency_ms: float,
        success: bool,
        token_count: int = 0,
        error_message: Optional[str] = None,
        tool_executions: Optional[List[Dict]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        intent: Optional[str] = None
    ):
        """Record query metrics and publish to CloudWatch
        
        Args:
            persona: User persona (warehouse_manager, field_engineer, etc.)
            agent: Agent name (sql_agent, inventory_optimizer, etc.)
            query: User query text
            latency_ms: Query processing latency in milliseconds
            success: Whether query was successful
            token_count: Number of tokens used
            error_message: Error message if query failed
            tool_executions: List of tool execution details
            user_id: User identifier
            session_id: Session identifier
            intent: Classified intent (sql_query, optimization, both)
        """
        # Create metrics object
        metrics = AgentMetrics(
            persona=persona,
            agent_name=agent,
            query=query,
            timestamp=datetime.utcnow(),
            latency_ms=latency_ms,
            success=success,
            error_message=error_message,
            token_count=token_count,
            tool_executions=tool_executions or [],
            user_id=user_id,
            session_id=session_id,
            intent=intent
        )
        
        # Log structured data
        self._log_metrics(metrics)
        
        # Publish to CloudWatch
        self._publish_metrics(metrics)
        
        # Update statistics
        self._update_stats(metrics)
    
    def _log_metrics(self, metrics: AgentMetrics):
        """Log metrics as structured JSON"""
        log_data = metrics.to_dict()
        self.logger.info(json.dumps(log_data))
    
    def _publish_metrics(self, metrics: AgentMetrics):
        """Publish metrics to CloudWatch"""
        metric_data = []
        
        # Query latency metric
        metric_data.append({
            'MetricName': 'QueryLatency',
            'Value': metrics.latency_ms,
            'Unit': 'Milliseconds',
            'Timestamp': metrics.timestamp,
            'Dimensions': [
                {'Name': 'Persona', 'Value': metrics.persona},
                {'Name': 'Agent', 'Value': metrics.agent_name}
            ]
        })
        
        # Query count metric
        metric_data.append({
            'MetricName': 'QueryCount',
            'Value': 1,
            'Unit': 'Count',
            'Timestamp': metrics.timestamp,
            'Dimensions': [
                {'Name': 'Persona', 'Value': metrics.persona},
                {'Name': 'Agent', 'Value': metrics.agent_name},
                {'Name': 'Success', 'Value': str(metrics.success)}
            ]
        })
        
        # Token usage metric
        if metrics.token_count > 0:
            metric_data.append({
                'MetricName': 'TokenUsage',
                'Value': metrics.token_count,
                'Unit': 'Count',
                'Timestamp': metrics.timestamp,
                'Dimensions': [
                    {'Name': 'Agent', 'Value': metrics.agent_name},
                    {'Name': 'Persona', 'Value': metrics.persona}
                ]
            })
        
        # Error metric
        if not metrics.success:
            metric_data.append({
                'MetricName': 'ErrorCount',
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': metrics.timestamp,
                'Dimensions': [
                    {'Name': 'Agent', 'Value': metrics.agent_name},
                    {'Name': 'Persona', 'Value': metrics.persona}
                ]
            })
        
        # Tool execution metrics
        if metrics.tool_executions:
            for tool_exec in metrics.tool_executions:
                metric_data.append({
                    'MetricName': 'ToolExecutionTime',
                    'Value': tool_exec.get('duration_ms', 0),
                    'Unit': 'Milliseconds',
                    'Timestamp': metrics.timestamp,
                    'Dimensions': [
                        {'Name': 'ToolName', 'Value': tool_exec.get('tool_name', 'unknown')},
                        {'Name': 'Agent', 'Value': metrics.agent_name},
                        {'Name': 'Success', 'Value': str(tool_exec.get('success', False))}
                    ]
                })
        
        # Intent classification metric
        if metrics.intent:
            metric_data.append({
                'MetricName': 'IntentClassification',
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': metrics.timestamp,
                'Dimensions': [
                    {'Name': 'Intent', 'Value': metrics.intent},
                    {'Name': 'Persona', 'Value': metrics.persona}
                ]
            })
        
        # Add to buffer
        self.metrics_buffer.extend(metric_data)
        
        # Publish if buffer is full
        if len(self.metrics_buffer) >= self.buffer_size:
            self._flush_metrics()
    
    def _flush_metrics(self):
        """Flush metrics buffer to CloudWatch"""
        if not self.metrics_buffer:
            return
        
        try:
            # CloudWatch allows max 1000 metrics per request, but we'll batch smaller
            batch_size = 20
            for i in range(0, len(self.metrics_buffer), batch_size):
                batch = self.metrics_buffer[i:i + batch_size]
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
            
            self.metrics_buffer = []
        except Exception as e:
            self.logger.error(json.dumps({
                'error': 'Failed to publish metrics to CloudWatch',
                'exception': str(e),
                'metrics_count': len(self.metrics_buffer)
            }))
    
    def _update_stats(self, metrics: AgentMetrics):
        """Update internal statistics"""
        self.stats['total_queries'] += 1
        if metrics.success:
            self.stats['successful_queries'] += 1
        else:
            self.stats['failed_queries'] += 1
        self.stats['total_latency_ms'] += metrics.latency_ms
        self.stats['total_tokens'] += metrics.token_count
    
    def record_business_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        dimensions: Dict[str, str],
        timestamp: Optional[datetime] = None
    ):
        """Record custom business metric
        
        Args:
            metric_name: Name of the business metric
            value: Metric value
            unit: CloudWatch unit (Count, Percent, Bytes, etc.)
            dimensions: Dictionary of dimension name-value pairs
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        }
        
        self.metrics_buffer.append(metric_data)
        
        # Log business metric
        self.logger.info(json.dumps({
            'metric_type': 'business_metric',
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'dimensions': dimensions,
            'timestamp': timestamp.isoformat()
        }))
        
        if len(self.metrics_buffer) >= self.buffer_size:
            self._flush_metrics()
    
    def record_error(
        self,
        persona: str,
        agent: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Record error with context for debugging
        
        Args:
            persona: User persona
            agent: Agent name
            error_type: Type/category of error
            error_message: Error message
            context: Additional context (query, session_id, etc.)
        """
        error_data = {
            'error_type': 'agent_error',
            'persona': persona,
            'agent': agent,
            'error_category': error_type,
            'error_message': error_message,
            'timestamp': datetime.utcnow().isoformat(),
            'context': context or {}
        }
        
        self.logger.error(json.dumps(error_data))
        
        # Publish error metric
        metric_data = {
            'MetricName': 'ErrorByType',
            'Value': 1,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'ErrorType', 'Value': error_type},
                {'Name': 'Agent', 'Value': agent},
                {'Name': 'Persona', 'Value': persona}
            ]
        }
        
        self.metrics_buffer.append(metric_data)
        
        if len(self.metrics_buffer) >= self.buffer_size:
            self._flush_metrics()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics
        
        Returns:
            Dictionary with statistics
        """
        avg_latency = (
            self.stats['total_latency_ms'] / self.stats['total_queries']
            if self.stats['total_queries'] > 0 else 0
        )
        
        success_rate = (
            self.stats['successful_queries'] / self.stats['total_queries'] * 100
            if self.stats['total_queries'] > 0 else 0
        )
        
        return {
            'total_queries': self.stats['total_queries'],
            'successful_queries': self.stats['successful_queries'],
            'failed_queries': self.stats['failed_queries'],
            'success_rate_percent': round(success_rate, 2),
            'average_latency_ms': round(avg_latency, 2),
            'total_tokens_used': self.stats['total_tokens'],
            'average_tokens_per_query': round(
                self.stats['total_tokens'] / self.stats['total_queries']
                if self.stats['total_queries'] > 0 else 0,
                2
            )
        }
    
    def get_metrics_summary(
        self,
        start_time: datetime,
        end_time: datetime,
        persona: Optional[str] = None,
        agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get metrics summary from CloudWatch for a time period
        
        Args:
            start_time: Start of time period
            end_time: End of time period
            persona: Optional persona filter
            agent: Optional agent filter
            
        Returns:
            Dictionary with metrics summary
        """
        dimensions = []
        if persona:
            dimensions.append({'Name': 'Persona', 'Value': persona})
        if agent:
            dimensions.append({'Name': 'Agent', 'Value': agent})
        
        try:
            # Get latency statistics
            latency_stats = self.cloudwatch.get_metric_statistics(
                Namespace=self.namespace,
                MetricName='QueryLatency',
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average', 'Minimum', 'Maximum', 'SampleCount']
            )
            
            # Get success rate
            success_count = self.cloudwatch.get_metric_statistics(
                Namespace=self.namespace,
                MetricName='QueryCount',
                Dimensions=dimensions + [{'Name': 'Success', 'Value': 'True'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            # Get error count
            error_count = self.cloudwatch.get_metric_statistics(
                Namespace=self.namespace,
                MetricName='ErrorCount',
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            # Get token usage
            token_usage = self.cloudwatch.get_metric_statistics(
                Namespace=self.namespace,
                MetricName='TokenUsage',
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum', 'Average']
            )
            
            return {
                'time_period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'filters': {
                    'persona': persona,
                    'agent': agent
                },
                'latency': latency_stats.get('Datapoints', []),
                'success_count': success_count.get('Datapoints', []),
                'error_count': error_count.get('Datapoints', []),
                'token_usage': token_usage.get('Datapoints', [])
            }
        except Exception as e:
            self.logger.error(json.dumps({
                'error': 'Failed to retrieve metrics summary',
                'exception': str(e)
            }))
            return {'error': str(e)}
    
    def flush(self):
        """Manually flush metrics buffer"""
        self._flush_metrics()
    
    def __del__(self):
        """Ensure metrics are flushed on cleanup"""
        try:
            self._flush_metrics()
        except:
            pass


# Convenience function
def create_metrics_collector(
    region: str = "us-east-1",
    config: Optional['ConfigurationManager'] = None
) -> MetricsCollector:
    """Create a MetricsCollector instance
    
    Args:
        region: AWS region
        config: Optional ConfigurationManager instance
        
    Returns:
        MetricsCollector instance
    """
    return MetricsCollector(region=region, config=config)
