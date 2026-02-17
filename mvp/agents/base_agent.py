"""
Base Agent Class

Provides common functionality for all agents in the supply chain AI system.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging


@dataclass
class AgentResponse:
    """Response from an agent."""
    success: bool
    content: str
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent:
    """
    Base class for all agents.
    
    Provides common functionality like logging, error handling,
    and response formatting.
    """
    
    def __init__(self, agent_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize base agent.
        
        Args:
            agent_name: Name of the agent for logging
            logger: Optional logger instance
        """
        self.agent_name = agent_name
        self.logger = logger or logging.getLogger(agent_name)
    
    def log_info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(f"[{self.agent_name}] {message}")
    
    def log_error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log error message."""
        if error:
            self.logger.error(f"[{self.agent_name}] {message}: {error}", exc_info=True)
        else:
            self.logger.error(f"[{self.agent_name}] {message}")
    
    def log_debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(f"[{self.agent_name}] {message}")
    
    def create_success_response(
        self,
        content: str,
        data: Optional[Any] = None,
        execution_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Create a success response.
        
        Args:
            content: Response content/message
            data: Optional data payload
            execution_time: Execution time in seconds
            metadata: Optional metadata
            
        Returns:
            AgentResponse with success=True
        """
        return AgentResponse(
            success=True,
            content=content,
            data=data,
            error=None,
            execution_time=execution_time,
            metadata=metadata or {}
        )
    
    def create_error_response(
        self,
        error_message: str,
        execution_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Create an error response.
        
        Args:
            error_message: Error message
            execution_time: Execution time in seconds
            metadata: Optional metadata
            
        Returns:
            AgentResponse with success=False
        """
        return AgentResponse(
            success=False,
            content="",
            data=None,
            error=error_message,
            execution_time=execution_time,
            metadata=metadata or {}
        )
    
    def handle_exception(
        self,
        exception: Exception,
        context: str,
        execution_time: float = 0.0
    ) -> AgentResponse:
        """
        Handle an exception and create error response.
        
        Args:
            exception: The exception that occurred
            context: Context description for logging
            execution_time: Execution time in seconds
            
        Returns:
            AgentResponse with error information
        """
        error_message = f"{context}: {str(exception)}"
        self.log_error(error_message, exception)
        
        # Create user-friendly error message
        user_message = self._create_user_friendly_error(exception, context)
        
        return self.create_error_response(
            error_message=user_message,
            execution_time=execution_time,
            metadata={'original_error': str(exception)}
        )
    
    def _create_user_friendly_error(self, exception: Exception, context: str) -> str:
        """
        Create a user-friendly error message.
        
        Args:
            exception: The exception
            context: Context description
            
        Returns:
            User-friendly error message
        """
        error_type = type(exception).__name__
        
        # Map technical errors to user-friendly messages
        if 'timeout' in str(exception).lower():
            return "The request took too long to complete. Please try again."
        elif 'connection' in str(exception).lower():
            return "Unable to connect to the service. Please check your connection."
        elif 'permission' in str(exception).lower() or 'access' in str(exception).lower():
            return "You don't have permission to perform this action."
        elif 'not found' in str(exception).lower():
            return "The requested resource was not found."
        else:
            return f"An error occurred while {context}. Please try again or contact support."
