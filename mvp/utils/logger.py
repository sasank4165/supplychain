"""
Logging Infrastructure for Supply Chain AI MVP

Provides centralized logging with rotating file handler and configurable log levels.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class LoggerSetupError(Exception):
    """Raised when logger setup fails."""
    pass


def setup_logger(
    name: str,
    log_file: str,
    level: str = 'INFO',
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with rotating file handler and optional console output.
    
    Args:
        name: Logger name
        log_file: Path to log file
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        log_format: Custom log format string
        date_format: Custom date format string
        console_output: Whether to also log to console
        
    Returns:
        Configured logger instance
        
    Raises:
        LoggerSetupError: If logger setup fails
    """
    try:
        # Create logger
        logger = logging.getLogger(name)
        
        # Set log level
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # Clear existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up log format
        if log_format is None:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        if date_format is None:
            date_format = '%Y-%m-%d %H:%M:%S'
        
        formatter = logging.Formatter(log_format, datefmt=date_format)
        
        # Add rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Add console handler if requested
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger
        
    except Exception as e:
        raise LoggerSetupError(f"Failed to set up logger: {e}")


def setup_application_logger(config: dict) -> logging.Logger:
    """
    Set up the main application logger from configuration.
    
    Args:
        config: Configuration dictionary with logging settings
        
    Returns:
        Configured application logger
    """
    logging_config = config.get('logging', {})
    
    return setup_logger(
        name='supply_chain_ai',
        log_file=logging_config.get('file', 'logs/app.log'),
        level=logging_config.get('level', 'INFO'),
        max_bytes=logging_config.get('max_bytes', 10485760),
        backup_count=logging_config.get('backup_count', 5),
        log_format=logging_config.get('format'),
        date_format=logging_config.get('date_format'),
        console_output=True
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for temporary log level changes."""
    
    def __init__(self, logger: logging.Logger, level: str):
        """
        Initialize log context.
        
        Args:
            logger: Logger to modify
            level: Temporary log level
        """
        self.logger = logger
        self.new_level = getattr(logging, level.upper())
        self.old_level = None
    
    def __enter__(self):
        """Enter context and change log level."""
        self.old_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore original log level."""
        self.logger.setLevel(self.old_level)


def log_function_call(logger: logging.Logger):
    """
    Decorator to log function calls with arguments and results.
    
    Args:
        logger: Logger to use for logging
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned: {result}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised exception: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


def log_exception(logger: logging.Logger, message: str = "An error occurred"):
    """
    Decorator to log exceptions with stack trace.
    
    Args:
        logger: Logger to use for logging
        message: Custom error message
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{message} in {func.__name__}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


class StructuredLogger:
    """Logger with structured logging support."""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize structured logger.
        
        Args:
            logger: Base logger instance
        """
        self.logger = logger
    
    def log_event(
        self,
        level: str,
        event: str,
        **kwargs
    ):
        """
        Log a structured event.
        
        Args:
            level: Log level
            event: Event name
            **kwargs: Additional event data
        """
        log_level = getattr(logging, level.upper())
        message = f"[{event}]"
        
        if kwargs:
            details = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            message += f" {details}"
        
        self.logger.log(log_level, message)
    
    def log_query(self, query: str, persona: str, execution_time: float, success: bool):
        """Log a query execution event."""
        self.log_event(
            'INFO',
            'QUERY_EXECUTED',
            persona=persona,
            execution_time=f"{execution_time:.2f}s",
            success=success,
            query_length=len(query)
        )
    
    def log_api_call(self, service: str, operation: str, duration: float, success: bool):
        """Log an API call event."""
        self.log_event(
            'INFO',
            'API_CALL',
            service=service,
            operation=operation,
            duration=f"{duration:.3f}s",
            success=success
        )
    
    def log_cost(self, service: str, cost: float, details: str = ""):
        """Log a cost event."""
        self.log_event(
            'INFO',
            'COST_TRACKED',
            service=service,
            cost=f"${cost:.4f}",
            details=details
        )
    
    def log_auth(self, event: str, username: str, success: bool):
        """Log an authentication event."""
        self.log_event(
            'INFO',
            f'AUTH_{event.upper()}',
            username=username,
            success=success
        )
    
    def log_error(self, error_type: str, message: str, **kwargs):
        """Log an error event."""
        self.log_event(
            'ERROR',
            f'ERROR_{error_type.upper()}',
            message=message,
            **kwargs
        )
