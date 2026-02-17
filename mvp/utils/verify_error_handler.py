"""
Verification Script for Error Handler

Quick verification that error handler is working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handler import (
    ErrorHandler,
    ErrorContext,
    AuthenticationError,
    DatabaseError,
    QueryError,
    ValidationError,
    retry_with_backoff,
    get_error_handler
)


def verify_basic_functionality():
    """Verify basic error handling."""
    print("Testing basic error handling...")
    
    handler = ErrorHandler()
    
    # Test authentication error
    try:
        raise AuthenticationError("Invalid credentials")
    except Exception as e:
        response = handler.handle_error(e)
        assert response.category.value == "authentication"
        assert "username or password" in response.user_message.lower()
        print("  ✓ Authentication error handling works")
    
    # Test database error
    try:
        raise DatabaseError("Connection failed")
    except Exception as e:
        response = handler.handle_error(e)
        assert response.category.value == "database"
        assert response.retry_possible is True
        print("  ✓ Database error handling works")
    
    # Test validation error
    try:
        raise ValidationError("Invalid input")
    except Exception as e:
        response = handler.handle_error(e)
        assert response.category.value == "validation"
        assert response.severity.value == "low"
        print("  ✓ Validation error handling works")


def verify_retry_logic():
    """Verify retry with exponential backoff."""
    print("\nTesting retry logic...")
    
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
    print("  ✓ Retry logic works")
    
    # Test non-transient error (should not retry)
    attempt_count[0] = 0
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def validation_error():
        attempt_count[0] += 1
        raise ValidationError("Invalid")
    
    try:
        validation_error()
    except ValidationError:
        pass
    
    assert attempt_count[0] == 1  # Should not retry
    print("  ✓ Non-transient errors are not retried")


def verify_error_context():
    """Verify error context handling."""
    print("\nTesting error context...")
    
    handler = ErrorHandler()
    
    context = ErrorContext(
        user="test_user",
        persona="Warehouse Manager",
        query="Test query",
        session_id="session123"
    )
    
    try:
        raise QueryError("Query failed")
    except Exception as e:
        response = handler.handle_error(e, context)
        assert response.category.value == "query"
        print("  ✓ Error context handling works")


def verify_error_statistics():
    """Verify error statistics tracking."""
    print("\nTesting error statistics...")
    
    handler = ErrorHandler()
    
    # Generate some errors
    handler.handle_error(AuthenticationError("Error 1"))
    handler.handle_error(AuthenticationError("Error 2"))
    handler.handle_error(DatabaseError("Error 3"))
    
    stats = handler.get_error_stats()
    assert stats["authentication"] == 2
    assert stats["database"] == 1
    print("  ✓ Error statistics tracking works")
    
    # Test reset
    handler.reset_stats()
    assert len(handler.get_error_stats()) == 0
    print("  ✓ Statistics reset works")


def verify_global_handler():
    """Verify global error handler."""
    print("\nTesting global error handler...")
    
    handler1 = get_error_handler()
    handler2 = get_error_handler()
    
    assert handler1 is handler2
    print("  ✓ Global error handler is singleton")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Error Handler Verification")
    print("=" * 60)
    
    try:
        verify_basic_functionality()
        verify_retry_logic()
        verify_error_context()
        verify_error_statistics()
        verify_global_handler()
        
        print("\n" + "=" * 60)
        print("All verification tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Verification failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
