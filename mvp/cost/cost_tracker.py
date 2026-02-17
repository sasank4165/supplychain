"""
Cost Tracker Module

This module provides cost calculation and tracking functionality for AWS services
used in the Supply Chain AI MVP system.

Tracks costs for:
- Amazon Bedrock (token-based pricing)
- Amazon Redshift Serverless (RPU-hour pricing)
- AWS Lambda (GB-second pricing)
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, Optional
import threading


@dataclass
class TokenUsage:
    """Token usage information from Bedrock API calls"""
    input_tokens: int = 0
    output_tokens: int = 0
    
    def __add__(self, other: 'TokenUsage') -> 'TokenUsage':
        """Add two TokenUsage objects together"""
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens
        )


@dataclass
class Cost:
    """Cost breakdown for a query or time period"""
    bedrock_cost: float = 0.0
    redshift_cost: float = 0.0
    lambda_cost: float = 0.0
    total_cost: float = 0.0
    tokens_used: TokenUsage = field(default_factory=TokenUsage)
    
    def __add__(self, other: 'Cost') -> 'Cost':
        """Add two Cost objects together"""
        return Cost(
            bedrock_cost=self.bedrock_cost + other.bedrock_cost,
            redshift_cost=self.redshift_cost + other.redshift_cost,
            lambda_cost=self.lambda_cost + other.lambda_cost,
            total_cost=self.total_cost + other.total_cost,
            tokens_used=self.tokens_used + other.tokens_used
        )


class CostTracker:
    """
    Track and calculate AWS costs for the Supply Chain AI MVP system.
    
    This class provides methods to:
    - Calculate costs for individual queries
    - Track daily and session-level costs
    - Provide cost breakdowns by service
    - Estimate monthly costs based on usage
    """
    
    def __init__(self, config: dict):
        """
        Initialize the cost tracker with pricing configuration.
        
        Args:
            config: Configuration dictionary with cost settings
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        
        # Pricing configuration (per 1000 tokens for Bedrock)
        self.bedrock_input_cost_per_1k = config.get('bedrock_input_cost_per_1k', 0.003)
        self.bedrock_output_cost_per_1k = config.get('bedrock_output_cost_per_1k', 0.015)
        
        # Redshift Serverless pricing (per RPU-hour)
        self.redshift_rpu_cost_per_hour = config.get('redshift_rpu_cost_per_hour', 0.36)
        self.redshift_base_rpus = config.get('redshift_base_rpus', 8)
        
        # Lambda pricing (per GB-second)
        self.lambda_cost_per_gb_second = config.get('lambda_cost_per_gb_second', 0.0000166667)
        
        # Cost tracking storage
        self._daily_costs: Dict[date, Cost] = {}
        self._session_costs: Dict[str, Cost] = {}
        self._lock = threading.Lock()
    
    def calculate_bedrock_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for Bedrock API call based on token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        input_cost = (input_tokens / 1000) * self.bedrock_input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.bedrock_output_cost_per_1k
        return input_cost + output_cost
    
    def calculate_redshift_cost(self, execution_time_seconds: float) -> float:
        """
        Calculate cost for Redshift Serverless query execution.
        
        Redshift Serverless charges per RPU-hour. We calculate the cost
        based on the query execution time and base RPU capacity.
        
        Args:
            execution_time_seconds: Query execution time in seconds
            
        Returns:
            Cost in USD
        """
        # Convert seconds to hours
        execution_time_hours = execution_time_seconds / 3600
        
        # Calculate cost: RPUs × hours × cost per RPU-hour
        cost = self.redshift_base_rpus * execution_time_hours * self.redshift_rpu_cost_per_hour
        return cost
    
    def calculate_lambda_cost(self, duration_ms: int, memory_mb: int = 512) -> float:
        """
        Calculate cost for Lambda function invocation.
        
        Lambda charges per GB-second of execution time.
        
        Args:
            duration_ms: Lambda execution duration in milliseconds
            memory_mb: Lambda memory allocation in MB (default: 512)
            
        Returns:
            Cost in USD
        """
        # Convert duration to seconds
        duration_seconds = duration_ms / 1000
        
        # Convert memory to GB
        memory_gb = memory_mb / 1024
        
        # Calculate GB-seconds
        gb_seconds = memory_gb * duration_seconds
        
        # Calculate cost
        cost = gb_seconds * self.lambda_cost_per_gb_second
        return cost
    
    def calculate_query_cost(
        self,
        bedrock_tokens: Optional[TokenUsage] = None,
        redshift_execution_time: float = 0.0,
        lambda_duration_ms: int = 0,
        lambda_memory_mb: int = 512
    ) -> Cost:
        """
        Calculate total cost for a query execution.
        
        Args:
            bedrock_tokens: Token usage from Bedrock API calls
            redshift_execution_time: Redshift query execution time in seconds
            lambda_duration_ms: Lambda execution duration in milliseconds
            lambda_memory_mb: Lambda memory allocation in MB
            
        Returns:
            Cost object with breakdown by service
        """
        if not self.enabled:
            return Cost()
        
        # Calculate individual service costs
        bedrock_cost = 0.0
        tokens = TokenUsage()
        if bedrock_tokens:
            bedrock_cost = self.calculate_bedrock_cost(
                bedrock_tokens.input_tokens,
                bedrock_tokens.output_tokens
            )
            tokens = bedrock_tokens
        
        redshift_cost = self.calculate_redshift_cost(redshift_execution_time)
        lambda_cost = self.calculate_lambda_cost(lambda_duration_ms, lambda_memory_mb)
        
        # Calculate total
        total_cost = bedrock_cost + redshift_cost + lambda_cost
        
        return Cost(
            bedrock_cost=bedrock_cost,
            redshift_cost=redshift_cost,
            lambda_cost=lambda_cost,
            total_cost=total_cost,
            tokens_used=tokens
        )
    
    def add_query_cost(self, session_id: str, cost: Cost) -> None:
        """
        Add a query cost to session and daily totals.
        
        Args:
            session_id: Session identifier
            cost: Cost object for the query
        """
        if not self.enabled:
            return
        
        with self._lock:
            # Add to session costs
            if session_id not in self._session_costs:
                self._session_costs[session_id] = Cost()
            self._session_costs[session_id] = self._session_costs[session_id] + cost
            
            # Add to daily costs
            today = date.today()
            if today not in self._daily_costs:
                self._daily_costs[today] = Cost()
            self._daily_costs[today] = self._daily_costs[today] + cost
    
    def get_session_cost(self, session_id: str) -> Cost:
        """
        Get total cost for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Cost object with session totals
        """
        with self._lock:
            return self._session_costs.get(session_id, Cost())
    
    def get_daily_cost(self, target_date: Optional[date] = None) -> Cost:
        """
        Get total cost for a specific day.
        
        Args:
            target_date: Date to get costs for (default: today)
            
        Returns:
            Cost object with daily totals
        """
        if target_date is None:
            target_date = date.today()
        
        with self._lock:
            return self._daily_costs.get(target_date, Cost())
    
    def get_monthly_estimate(self) -> float:
        """
        Estimate monthly cost based on today's usage.
        
        Calculates average daily cost and multiplies by 30 days.
        
        Returns:
            Estimated monthly cost in USD
        """
        today_cost = self.get_daily_cost()
        return today_cost.total_cost * 30
    
    def get_cost_breakdown(self, session_id: Optional[str] = None) -> Dict[str, float]:
        """
        Get cost breakdown by service.
        
        Args:
            session_id: Session identifier (if None, returns daily breakdown)
            
        Returns:
            Dictionary with cost breakdown by service
        """
        if session_id:
            cost = self.get_session_cost(session_id)
        else:
            cost = self.get_daily_cost()
        
        return {
            'bedrock': cost.bedrock_cost,
            'redshift': cost.redshift_cost,
            'lambda': cost.lambda_cost,
            'total': cost.total_cost
        }
    
    def clear_session_costs(self, session_id: str) -> None:
        """
        Clear cost tracking for a session.
        
        Args:
            session_id: Session identifier
        """
        with self._lock:
            if session_id in self._session_costs:
                del self._session_costs[session_id]
    
    def get_all_daily_costs(self) -> Dict[date, Cost]:
        """
        Get all daily costs.
        
        Returns:
            Dictionary mapping dates to Cost objects
        """
        with self._lock:
            return self._daily_costs.copy()
    
    def format_cost(self, cost: float) -> str:
        """
        Format cost as currency string.
        
        Args:
            cost: Cost in USD
            
        Returns:
            Formatted cost string (e.g., "$0.02")
        """
        return f"${cost:.4f}"
    
    def get_cost_summary(self, session_id: Optional[str] = None) -> str:
        """
        Get a formatted cost summary.
        
        Args:
            session_id: Session identifier (if None, returns daily summary)
            
        Returns:
            Formatted cost summary string
        """
        if session_id:
            cost = self.get_session_cost(session_id)
            title = "Session Cost"
        else:
            cost = self.get_daily_cost()
            title = "Daily Cost"
        
        summary = f"{title} Summary:\n"
        summary += f"  Bedrock: {self.format_cost(cost.bedrock_cost)}\n"
        summary += f"  Redshift: {self.format_cost(cost.redshift_cost)}\n"
        summary += f"  Lambda: {self.format_cost(cost.lambda_cost)}\n"
        summary += f"  Total: {self.format_cost(cost.total_cost)}\n"
        summary += f"  Tokens: {cost.tokens_used.input_tokens} in / {cost.tokens_used.output_tokens} out"
        
        return summary
