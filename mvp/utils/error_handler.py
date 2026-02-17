"""
Error Handler for Supply Chain AI MVP

Provides comprehensive error handling with categorization, user-friendly messages,
retry logic with exponential backoff, and detailed error logging.
"""

import logging
import time
import traceback
from enum import Enum
from typing import Optional, Callable, Any, Dict, Tuple
from dataclasses import dataclass
from functools import wraps


class ErrorCategory(Enum):
    """Error categories for classification."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    QUERY = "query"
    DATABASE = "database"
    AGENT = "agent"
    BEDROCK = "bedrock"
    LAMBDA = "lambda"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    VALIDATION = "validation"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for error handling."""
    user: Optional[str] = None
    persona: Optional[str] = None
    query: Optional[str] = None
    session_id: Optional[str] = None
    operation: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


@dataclass
class ErrorResponse:
    """Structured error response."""
    category: ErrorCategory
    severity: ErrorSeverity
    user_message: str
    technical_message: str
    error_code: Optional[str] = None
    retry_possible: bool = False
    remediation_steps: Optional[list] = None
    timestamp: Optional[float] = None


class SupplyChainError(Exception):
    """Base exception for Supply Chain AI application."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.original_error = original_error


class AuthenticationError(SupplyChainError):
    """Authentication-related errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            original_error=original_error
        )


class AuthorizationError(SupplyChainError):
    """Authorization-related errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            original_error=original_error
        )


class QueryError(SupplyChainError):
    """Query processing errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            category=ErrorCategory.QUERY,
            severity=ErrorSeverity.MEDIUM,
            original_error=original_error
        )


class DatabaseError(SupplyChainError):
    """Database-related errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            original_error=original_error
        )


class AgentError(SupplyChainError):
    """Agent execution errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            category=ErrorCategory.AGENT,
            severity=ErrorSeverity.MEDIUM,
            original_error=original_error
        )


class BedrockError(SupplyChainError):
    """Bedrock API errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            category=ErrorCategory.BEDROCK,
            severity=ErrorSeverity.HIGH,
            original_error=original_error
        )


class LambdaError(SupplyChainError):
    """Lambda invocation errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            category=ErrorCategory.LAMBDA,
            severity=ErrorSeverity.MEDIUM,
            original_error=original_error
        )


class ConfigurationError(SupplyChainError):
    """Configuration errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            original_error=original_error
        )


class ValidationError(SupplyChainError):
    """Input validation errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            original_error=original_error
        )


class ErrorHandler:
    """
    Centralized error handler with categorization, user-friendly messages,
    and retry logic.
    """
    
    # User-friendly error messages by category
    USER_MESSAGES = {
        ErrorCategory.AUTHENTICATION: "Invalid username or password. Please try again.",
        ErrorCategory.AUTHORIZATION: "You don't have permission to access this feature.",
        ErrorCategory.QUERY: "Unable to process your query. Please rephrase and try again.",
        ErrorCategory.DATABASE: "Database temporarily unavailable. Please try again in a moment.",
        ErrorCategory.AGENT: "Unable to complete the requested operation. Please try again.",
        ErrorCategory.BEDROCK: "AI service temporarily unavailable. Please try again shortly.",
        ErrorCategory.LAMBDA: "Processing service temporarily unavailable. Please try again.",
        ErrorCategory.CONFIGURATION: "System configuration error. Please contact support.",
        ErrorCategory.NETWORK: "Network connection error. Please check your connection.",
        ErrorCategory.VALIDATION: "Invalid input. Please check your request and try again.",
        ErrorCategory.SYSTEM: "System error occurred. Please try again or contact support.",
        ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again."
    }
    
    # Remediation steps by category
    REMEDIATION_STEPS = {
        ErrorCategory.AUTHENTICATION: [
            "Verify your username and password",
            "Check if your account is active",
            "Contact administrator if problem persists"
        ],
        ErrorCategory.AUTHORIZATION: [
            "Verify you have access to the selected persona",
            "Contact administrator to request access"
        ],
        ErrorCategory.QUERY: [
            "Simplify your query",
            "Try asking in a different way",
            "Check for typos or unclear terms"
        ],
        ErrorCategory.DATABASE: [
            "Wait a moment and try again",
            "Check if the system is under maintenance"
        ],
        ErrorCategory.BEDROCK: [
            "Wait a moment and try again",
            "Simplify your request to reduce processing time"
        ],
        ErrorCategory.VALIDATION: [
            "Check your input for errors",
            "Ensure all required fields are filled",
            "Verify input format is correct"
        ]
    }
    
    # Transient error patterns that should be retried
    TRANSIENT_ERROR_PATTERNS = [
        "timeout",
        "throttl",
        "rate limit",
        "temporarily unavailable",
        "connection",
        "network",
        "503",
        "502",
        "504"
    ]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize error handler.
        
        Args:
            logger: Logger instance for error logging
        """
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts: Dict[ErrorCategory, int] = {}
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None
    ) -> ErrorResponse:
        """
        Handle an error with categorization and logging.
        
        Args:
            error: The exception to handle
            context: Additional context information
            
        Returns:
            ErrorResponse with user-friendly message and details
        """
        # Categorize the error
        category, severity = self._categorize_error(error)
        
        # Track error count
        self.error_counts[category] = self.error_counts.get(category, 0) + 1
        
        # Get user-friendly message
        user_message = self._get_user_message(error, category)
        
        # Get technical message
        technical_message = str(error)
        
        # Determine if retry is possible
        retry_possible = self._is_transient_error(error)
        
        # Get remediation steps
        remediation_steps = self.REMEDIATION_STEPS.get(category)
        
        # Log the error
        self._log_error(error, category, severity, context)
        
        # Create error response
        response = ErrorResponse(
            category=category,
            severity=severity,
            user_message=user_message,
            technical_message=technical_message,
            retry_possible=retry_possible,
            remediation_steps=remediation_steps,
            timestamp=time.time()
        )
        
        return response
    
    def _categorize_error(
        self,
        error: Exception
    ) -> Tuple[ErrorCategory, ErrorSeverity]:
        """
        Categorize an error and determine its severity.
        
        Args:
            error: The exception to categorize
            
        Returns:
            Tuple of (ErrorCategory, ErrorSeverity)
        """
        # Check if it's already a SupplyChainError
        if isinstance(error, SupplyChainError):
            return error.category, error.severity
        
        # Categorize by exception type
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Authentication errors
        if "authentication" in error_message or "login" in error_message:
            return ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH
        
        # Authorization errors
        if "authorization" in error_message or "permission" in error_message or "access denied" in error_message:
            return ErrorCategory.AUTHORIZATION, ErrorSeverity.HIGH
        
        # Database errors
        if "redshift" in error_message or "database" in error_message or "sql" in error_message:
            return ErrorCategory.DATABASE, ErrorSeverity.HIGH
        
        # Bedrock errors
        if "bedrock" in error_message or "claude" in error_message or "model" in error_message:
            return ErrorCategory.BEDROCK, ErrorSeverity.HIGH
        
        # Lambda errors
        if "lambda" in error_message or "function" in error_message:
            return ErrorCategory.LAMBDA, ErrorSeverity.MEDIUM
        
        # Configuration errors
        if "config" in error_message or error_type.endswith("ConfigError"):
            return ErrorCategory.CONFIGURATION, ErrorSeverity.CRITICAL
        
        # Network errors
        if "network" in error_message or "connection" in error_message or "timeout" in error_message:
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
        
        # Validation errors
        if "validation" in error_message or "invalid" in error_message or error_type == "ValueError":
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW
        
        # Query errors
        if "query" in error_message or "parse" in error_message:
            return ErrorCategory.QUERY, ErrorSeverity.MEDIUM
        
        # Default to unknown
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM
    
    def _get_user_message(
        self,
        error: Exception,
        category: ErrorCategory
    ) -> str:
        """
        Get user-friendly error message.
        
        Args:
            error: The exception
            category: Error category
            
        Returns:
            User-friendly error message
        """
        # Check if error has a custom user message
        if isinstance(error, SupplyChainError) and hasattr(error, 'user_message'):
            return error.user_message
        
        # Get default message for category
        return self.USER_MESSAGES.get(category, self.USER_MESSAGES[ErrorCategory.UNKNOWN])
    
    def _is_transient_error(self, error: Exception) -> bool:
        """
        Determine if an error is transient and should be retried.
        
        Args:
            error: The exception to check
            
        Returns:
            True if error is transient
        """
        error_message = str(error).lower()
        
        for pattern in self.TRANSIENT_ERROR_PATTERNS:
            if pattern in error_message:
                return True
        
        return False
    
    def _log_error(
        self,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: Optional[ErrorContext] = None
    ):
        """
        Log error with full details and stack trace.
        
        Args:
            error: The exception
            category: Error category
            severity: Error severity
            context: Additional context
        """
        # Build log message
        log_parts = [
            f"[{category.value.upper()}]",
            f"[{severity.value.upper()}]",
            str(error)
        ]
        
        # Add context information
        if context:
            context_parts = []
            if context.user:
                context_parts.append(f"user={context.user}")
            if context.persona:
                context_parts.append(f"persona={context.persona}")
            if context.operation:
                context_parts.append(f"operation={context.operation}")
            if context.session_id:
                context_parts.append(f"session={context.session_id}")
            
            if context_parts:
                log_parts.append(f"({', '.join(context_parts)})")
        
        log_message = " ".join(log_parts)
        
        # Log with appropriate level
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, exc_info=True)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, exc_info=True)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, exc_info=True)
        else:
            self.logger.info(log_message, exc_info=True)
        
        # Log stack trace separately for better readability
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Stack trace:\n{traceback.format_exc()}")
    
    def get_error_stats(self) -> Dict[str, int]:
        """
        Get error statistics.
        
        Returns:
            Dictionary of error counts by category
        """
        return {
            category.value: count
            for category, count in self.error_counts.items()
        }
    
    def reset_stats(self):
        """Reset error statistics."""
        self.error_counts.clear()


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple = (Exception,),
    logger: Optional[logging.Logger] = None
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each attempt
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry
        logger: Logger for retry messages
        
    Returns:
        Decorated function
        
    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def call_api():
            # API call that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # Check if this is a transient error
                    error_handler = ErrorHandler(logger)
                    if not error_handler._is_transient_error(e):
                        # Not transient, don't retry
                        raise
                    
                    if attempt == max_attempts:
                        # Last attempt, raise the error
                        if logger:
                            logger.error(
                                f"{func.__name__} failed after {max_attempts} attempts: {e}"
                            )
                        raise
                    
                    # Log retry attempt
                    if logger:
                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                    
                    # Wait before retry
                    time.sleep(delay)
                    
                    # Calculate next delay with exponential backoff
                    delay = min(delay * backoff_factor, max_delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def handle_errors(
    error_handler: Optional[ErrorHandler] = None,
    context: Optional[ErrorContext] = None,
    reraise: bool = True
):
    """
    Decorator to handle errors with ErrorHandler.
    
    Args:
        error_handler: ErrorHandler instance
        context: Error context
        reraise: Whether to reraise the exception after handling
        
    Returns:
        Decorated function
        
    Example:
        @handle_errors(error_handler=handler, reraise=False)
        def process_query(query):
            # Query processing
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = error_handler or ErrorHandler()
                error_response = handler.handle_error(e, context)
                
                if reraise:
                    raise
                
                return error_response
        
        return wrapper
    return decorator


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler(logger: Optional[logging.Logger] = None) -> ErrorHandler:
    """
    Get or create global error handler instance.
    
    Args:
        logger: Logger instance
        
    Returns:
        ErrorHandler instance
    """
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(logger)
    
    return _global_error_handler


def set_error_handler(handler: ErrorHandler):
    """
    Set global error handler instance.
    
    Args:
        handler: ErrorHandler instance
    """
    global _global_error_handler
    _global_error_handler = handler
