"""
Tests for Error Handler

Tests error categorization, user-friendly messages, retry logic,
and error logging functionality.
"""

import pytest
import logging
import time
from unittest.mock import Mock, patch
from utils.error_handler import (
    ErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    ErrorResponse,
    SupplyChainError,
    AuthenticationError,
    AuthorizationError,
    QueryError,
    DatabaseError,
    AgentError,
    BedrockError,
    LambdaError,
    ConfigurationError,
    ValidationError,
    retry_with_backoff,
    handle_errors,
    get_error_handler
)


class TestErrorCategorization:
    """Test error categorization logic."""
    
    def test_categorize_authentication_error(self):
        """Test authentication error categorization."""
        handler = ErrorHandler()
        error = Exception("Authentication failed")
        category, severity = handler._categorize_error(error)
        
        assert category == ErrorCategory.AUTHENTICATION
        assert severity == ErrorSeverity.HIGH
    
    def test_categorize_authorization_error(self):
        """Test authorization error categorization."""
        handler = ErrorHandler()
        error = Exception("Access denied - insufficient permissions")
        category, severity = handler._categorize_error(error)
        
        assert category == ErrorCategory.AUTHORIZATION
        assert severity == ErrorSeverity.HIGH
    
    def test_categorize_database_error(self):
        """Test database error categorization."""
        handler = ErrorHandler()
        error = Exception("Redshift query failed")
        category, severity = handler._categorize_error(error)
        
        assert category == ErrorCategory.DATABASE
        assert severity == ErrorSeverity.HIGH
    
    def test_categorize_bedrock_error(self):
        """Test Bedrock error categorization."""
        handler = ErrorHandler()
        error = Exception("Bedrock model invocation failed")
        category, severity = handler._categorize_error(error)
        
        assert category == ErrorCategory.BEDROCK
        assert severity == ErrorSeverity.HIGH
    
    def test_categorize_lambda_error(self):
        """Test Lambda error categorization."""
        handler = ErrorHandler()
        error = Exception("Lambda function execution failed")
        category, severity = handler._categorize_error(error)
        
        assert category == ErrorCategory.LAMBDA
        assert severity == ErrorSeverity.MEDIUM
    
    def test_categorize_configuration_error(self):
        """Test configuration error categorization."""
        handler = ErrorHandler()
        error = Exception("Missing required config parameter")
        category, severity = handler._categorize_error(error)
        
        assert category == ErrorCategory.CONFIGURATION
        assert severity == ErrorSeverity.CRITICAL
    
    def test_categorize_validation_error(self):
        """Test validation error categorization."""
        handler = ErrorHandler()
        error = ValueError("Invalid input format")
        category, severity = handler._categorize_error(error)
        
        assert category == ErrorCategory.VALIDATION
        assert severity == ErrorSeverity.LOW
    
    def test_categorize_network_error(self):
        """Test network error categorization."""
        handler = ErrorHandler()
        error = Exception("Connection timeout")
        category, severity = handler._categorize_error(error)
        
        assert category == ErrorCategory.NETWORK
        assert severity == ErrorSeverity.MEDIUM
    
    def test_categorize_query_error(self):
        """Test query error categorization."""
        handler = ErrorHandler()
        error = Exception("Failed to parse query")
        category, severity = handler._categorize_error(error)
        
        assert category == ErrorCategory.QUERY
        assert severity == ErrorSeverity.MEDIUM
    
    def test_categorize_supply_chain_error(self):
        """Test SupplyChainError categorization."""
        handler = ErrorHandler()
        error = AuthenticationError("Invalid credentials")
        category, severity = handler._categorize_error(error)
        
        assert category == ErrorCategory.AUTHENTICATION
        assert severity == ErrorSeverity.HIGH


class TestErrorHandling:
    """Test error handling functionality."""
    
    def test_handle_error_returns_response(self):
        """Test that handle_error returns ErrorResponse."""
        handler = ErrorHandler()
        error = Exception("Test error")
        
        response = handler.handle_error(error)
        
        assert isinstance(response, ErrorResponse)
        assert response.category is not None
        assert response.severity is not None
        assert response.user_message is not None
        assert response.technical_message == "Test error"
    
    def test_handle_error_with_context(self):
        """Test error handling with context."""
        logger = Mock()
        handler = ErrorHandler(logger)
        
        context = ErrorContext(
            user="test_user",
            persona="Warehouse Manager",
            query="Show inventory",
            session_id="session123"
        )
        
        error = QueryError("Query failed")
        response = handler.handle_error(error, context)
        
        assert response.category == ErrorCategory.QUERY
        assert logger.warning.called
    
    def test_user_friendly_messages(self):
        """Test user-friendly error messages."""
        handler = ErrorHandler()
        
        # Test authentication error message
        error = AuthenticationError("Invalid password")
        response = handler.handle_error(error)
        assert "username or password" in response.user_message.lower()
        
        # Test database error message
        error = DatabaseError("Connection failed")
        response = handler.handle_error(error)
        assert "database" in response.user_message.lower()
        assert "try again" in response.user_message.lower()
    
    def test_remediation_steps(self):
        """Test remediation steps are provided."""
        handler = ErrorHandler()
        
        error = AuthenticationError("Login failed")
        response = handler.handle_error(error)
        
        assert response.remediation_steps is not None
        assert len(response.remediation_steps) > 0
        assert any("username" in step.lower() for step in response.remediation_steps)
    
    def test_error_tracking(self):
        """Test error count tracking."""
        handler = ErrorHandler()
        
        # Handle multiple errors
        handler.handle_error(AuthenticationError("Error 1"))
        handler.handle_error(AuthenticationError("Error 2"))
        handler.handle_error(DatabaseError("Error 3"))
        
        stats = handler.get_error_stats()
        
        assert stats[ErrorCategory.AUTHENTICATION.value] == 2
        assert stats[ErrorCategory.DATABASE.value] == 1
    
    def test_reset_stats(self):
        """Test resetting error statistics."""
        handler = ErrorHandler()
        
        handler.handle_error(AuthenticationError("Error"))
        assert len(handler.get_error_stats()) > 0
        
        handler.reset_stats()
        assert len(handler.get_error_stats()) == 0


class TestTransientErrors:
    """Test transient error detection."""
    
    def test_timeout_is_transient(self):
        """Test timeout errors are marked as transient."""
        handler = ErrorHandler()
        error = Exception("Request timeout")
        
        assert handler._is_transient_error(error) is True
    
    def test_throttling_is_transient(self):
        """Test throttling errors are marked as transient."""
        handler = ErrorHandler()
        error = Exception("Rate limit exceeded")
        
        assert handler._is_transient_error(error) is True
    
    def test_503_is_transient(self):
        """Test 503 errors are marked as transient."""
        handler = ErrorHandler()
        error = Exception("503 Service Unavailable")
        
        assert handler._is_transient_error(error) is True
    
    def test_validation_not_transient(self):
        """Test validation errors are not transient."""
        handler = ErrorHandler()
        error = ValidationError("Invalid input")
        
        assert handler._is_transient_error(error) is False


class TestRetryWithBackoff:
    """Test retry with exponential backoff."""
    
    def test_retry_succeeds_on_second_attempt(self):
        """Test function succeeds on retry."""
        attempt_count = [0]
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1)
        def flaky_function():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise Exception("Temporary timeout")
            return "success"
        
        result = flaky_function()
        
        assert result == "success"
        assert attempt_count[0] == 2
    
    def test_retry_fails_after_max_attempts(self):
        """Test function fails after max attempts."""
        attempt_count = [0]
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1)
        def always_fails():
            attempt_count[0] += 1
            raise Exception("Connection timeout")
        
        with pytest.raises(Exception) as exc_info:
            always_fails()
        
        assert "timeout" in str(exc_info.value).lower()
        assert attempt_count[0] == 3
    
    def test_retry_non_transient_error_no_retry(self):
        """Test non-transient errors are not retried."""
        attempt_count = [0]
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1)
        def validation_error():
            attempt_count[0] += 1
            raise ValidationError("Invalid input")
        
        with pytest.raises(ValidationError):
            validation_error()
        
        # Should fail immediately without retry
        assert attempt_count[0] == 1
    
    def test_retry_exponential_backoff(self):
        """Test exponential backoff timing."""
        attempt_times = []
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1, backoff_factor=2.0)
        def timed_failure():
            attempt_times.append(time.time())
            raise Exception("Throttling error")
        
        with pytest.raises(Exception):
            timed_failure()
        
        # Check that delays increase exponentially
        assert len(attempt_times) == 3
        
        # First to second attempt should be ~0.1s
        delay1 = attempt_times[1] - attempt_times[0]
        assert 0.08 < delay1 < 0.15
        
        # Second to third attempt should be ~0.2s (2x)
        delay2 = attempt_times[2] - attempt_times[1]
        assert 0.18 < delay2 < 0.25
    
    def test_retry_max_delay(self):
        """Test max delay is respected."""
        @retry_with_backoff(
            max_attempts=5,
            initial_delay=10.0,
            backoff_factor=10.0,
            max_delay=0.2
        )
        def fails():
            raise Exception("timeout")
        
        start = time.time()
        with pytest.raises(Exception):
            fails()
        duration = time.time() - start
        
        # With max_delay=0.2, total time should be ~0.8s (4 delays)
        # Without max_delay, it would be much longer
        assert duration < 1.5


class TestHandleErrorsDecorator:
    """Test handle_errors decorator."""
    
    def test_decorator_catches_error(self):
        """Test decorator catches and handles errors."""
        handler = ErrorHandler()
        
        @handle_errors(error_handler=handler, reraise=False)
        def failing_function():
            raise DatabaseError("Connection failed")
        
        result = failing_function()
        
        assert isinstance(result, ErrorResponse)
        assert result.category == ErrorCategory.DATABASE
    
    def test_decorator_reraises_error(self):
        """Test decorator reraises errors when configured."""
        handler = ErrorHandler()
        
        @handle_errors(error_handler=handler, reraise=True)
        def failing_function():
            raise QueryError("Parse error")
        
        with pytest.raises(QueryError):
            failing_function()


class TestCustomErrors:
    """Test custom error classes."""
    
    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid credentials")
        
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.severity == ErrorSeverity.HIGH
        assert str(error) == "Invalid credentials"
    
    def test_authorization_error(self):
        """Test AuthorizationError."""
        error = AuthorizationError("Access denied")
        
        assert error.category == ErrorCategory.AUTHORIZATION
        assert error.severity == ErrorSeverity.HIGH
    
    def test_query_error(self):
        """Test QueryError."""
        error = QueryError("Invalid query")
        
        assert error.category == ErrorCategory.QUERY
        assert error.severity == ErrorSeverity.MEDIUM
    
    def test_database_error(self):
        """Test DatabaseError."""
        error = DatabaseError("Connection failed")
        
        assert error.category == ErrorCategory.DATABASE
        assert error.severity == ErrorSeverity.HIGH
    
    def test_bedrock_error(self):
        """Test BedrockError."""
        error = BedrockError("Model invocation failed")
        
        assert error.category == ErrorCategory.BEDROCK
        assert error.severity == ErrorSeverity.HIGH
    
    def test_lambda_error(self):
        """Test LambdaError."""
        error = LambdaError("Function failed")
        
        assert error.category == ErrorCategory.LAMBDA
        assert error.severity == ErrorSeverity.MEDIUM
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Missing config")
        
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.severity == ErrorSeverity.CRITICAL
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid input")
        
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.LOW


class TestGlobalErrorHandler:
    """Test global error handler functions."""
    
    def test_get_error_handler(self):
        """Test getting global error handler."""
        handler = get_error_handler()
        
        assert isinstance(handler, ErrorHandler)
    
    def test_get_error_handler_singleton(self):
        """Test global error handler is singleton."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is handler2


class TestErrorLogging:
    """Test error logging functionality."""
    
    def test_error_logged_with_severity(self):
        """Test errors are logged with appropriate severity."""
        logger = Mock()
        handler = ErrorHandler(logger)
        
        # Critical error
        handler.handle_error(ConfigurationError("Config missing"))
        assert logger.critical.called
        
        # High severity error
        logger.reset_mock()
        handler.handle_error(DatabaseError("DB failed"))
        assert logger.error.called
        
        # Medium severity error
        logger.reset_mock()
        handler.handle_error(QueryError("Query failed"))
        assert logger.warning.called
    
    def test_error_logged_with_context(self):
        """Test errors are logged with context information."""
        logger = Mock()
        handler = ErrorHandler(logger)
        
        context = ErrorContext(
            user="test_user",
            persona="Warehouse Manager",
            operation="query_execution"
        )
        
        handler.handle_error(QueryError("Failed"), context)
        
        # Check that logger was called
        assert logger.warning.called
        
        # Check that context info is in the log message
        call_args = logger.warning.call_args[0][0]
        assert "test_user" in call_args
        assert "Warehouse Manager" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
