"""
Example Usage of Error Handler

Demonstrates various error handling patterns and best practices.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from utils.error_handler import (
    ErrorHandler,
    ErrorContext,
    ErrorResponse,
    AuthenticationError,
    DatabaseError,
    QueryError,
    ValidationError,
    BedrockError,
    retry_with_backoff,
    handle_errors,
    get_error_handler
)


# Set up logger for examples
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_error_handling():
    """Example: Basic error handling."""
    print("\n=== Example 1: Basic Error Handling ===")
    
    handler = ErrorHandler(logger)
    
    try:
        # Simulate a database error
        raise DatabaseError("Connection to Redshift failed")
    except Exception as e:
        context = ErrorContext(
            user="john_doe",
            persona="Warehouse Manager",
            operation="query_execution"
        )
        
        error_response = handler.handle_error(e, context)
        
        print(f"Category: {error_response.category.value}")
        print(f"Severity: {error_response.severity.value}")
        print(f"User Message: {error_response.user_message}")
        print(f"Retry Possible: {error_response.retry_possible}")
        
        if error_response.remediation_steps:
            print("Remediation Steps:")
            for step in error_response.remediation_steps:
                print(f"  - {step}")


def example_custom_errors():
    """Example: Using custom error classes."""
    print("\n=== Example 2: Custom Error Classes ===")
    
    handler = ErrorHandler(logger)
    
    # Authentication error
    try:
        raise AuthenticationError("Invalid username or password")
    except Exception as e:
        response = handler.handle_error(e)
        print(f"Auth Error: {response.user_message}")
    
    # Validation error
    try:
        raise ValidationError("Query exceeds maximum length of 1000 characters")
    except Exception as e:
        response = handler.handle_error(e)
        print(f"Validation Error: {response.user_message}")
    
    # Query error
    try:
        raise QueryError("Failed to parse natural language query")
    except Exception as e:
        response = handler.handle_error(e)
        print(f"Query Error: {response.user_message}")


def example_retry_with_backoff():
    """Example: Retry with exponential backoff."""
    print("\n=== Example 3: Retry with Exponential Backoff ===")
    
    attempt_count = [0]
    
    @retry_with_backoff(
        max_attempts=3,
        initial_delay=0.5,
        backoff_factor=2.0,
        logger=logger
    )
    def flaky_api_call():
        """Simulates an API call that fails twice then succeeds."""
        attempt_count[0] += 1
        print(f"Attempt {attempt_count[0]}")
        
        if attempt_count[0] < 3:
            raise Exception("Temporary timeout - service unavailable")
        
        return {"status": "success", "data": "result"}
    
    try:
        result = flaky_api_call()
        print(f"Success after {attempt_count[0]} attempts: {result}")
    except Exception as e:
        print(f"Failed after {attempt_count[0]} attempts: {e}")


def example_non_transient_error():
    """Example: Non-transient errors are not retried."""
    print("\n=== Example 4: Non-Transient Errors ===")
    
    attempt_count = [0]
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.1, logger=logger)
    def validation_failure():
        """Validation errors should not be retried."""
        attempt_count[0] += 1
        print(f"Attempt {attempt_count[0]}")
        raise ValidationError("Invalid input format")
    
    try:
        validation_failure()
    except ValidationError as e:
        print(f"Failed immediately (no retry) after {attempt_count[0]} attempt")
        print(f"Error: {e}")


def example_handle_errors_decorator():
    """Example: Using handle_errors decorator."""
    print("\n=== Example 5: Handle Errors Decorator ===")
    
    handler = ErrorHandler(logger)
    
    @handle_errors(error_handler=handler, reraise=False)
    def process_query(query):
        """Process a query with automatic error handling."""
        if len(query) > 1000:
            raise ValidationError("Query too long")
        
        if "DROP" in query.upper():
            raise QueryError("Destructive operations not allowed")
        
        return {"result": "Query processed successfully"}
    
    # Valid query
    result1 = process_query("SELECT * FROM products")
    print(f"Result 1: {result1}")
    
    # Invalid query (too long)
    result2 = process_query("x" * 1001)
    if isinstance(result2, ErrorResponse):
        print(f"Result 2 (error): {result2.user_message}")
    
    # Invalid query (destructive)
    result3 = process_query("DROP TABLE products")
    if isinstance(result3, ErrorResponse):
        print(f"Result 3 (error): {result3.user_message}")


def example_error_statistics():
    """Example: Tracking error statistics."""
    print("\n=== Example 6: Error Statistics ===")
    
    handler = ErrorHandler(logger)
    
    # Simulate various errors
    errors = [
        AuthenticationError("Login failed"),
        AuthenticationError("Invalid token"),
        DatabaseError("Connection timeout"),
        DatabaseError("Query timeout"),
        DatabaseError("Connection lost"),
        QueryError("Parse error"),
        BedrockError("Model invocation failed")
    ]
    
    for error in errors:
        handler.handle_error(error)
    
    # Get statistics
    stats = handler.get_error_stats()
    print("Error Statistics:")
    for category, count in stats.items():
        print(f"  {category}: {count}")
    
    # Reset statistics
    handler.reset_stats()
    print("\nStatistics reset")
    print(f"After reset: {handler.get_error_stats()}")


def example_global_error_handler():
    """Example: Using global error handler."""
    print("\n=== Example 7: Global Error Handler ===")
    
    # Get global handler
    handler = get_error_handler(logger)
    
    # Use it anywhere in the application
    try:
        raise DatabaseError("Redshift query failed")
    except Exception as e:
        response = handler.handle_error(e)
        print(f"Global handler response: {response.user_message}")
    
    # Get the same instance elsewhere
    handler2 = get_error_handler()
    print(f"Same instance: {handler is handler2}")


def example_error_context():
    """Example: Using error context for detailed logging."""
    print("\n=== Example 8: Error Context ===")
    
    handler = ErrorHandler(logger)
    
    # Rich context information
    context = ErrorContext(
        user="jane_smith",
        persona="Field Engineer",
        query="Show orders for delivery today",
        session_id="session_abc123",
        operation="order_query",
        additional_info={
            "warehouse": "WH001",
            "delivery_date": "2024-01-15",
            "order_count": 25
        }
    )
    
    try:
        raise QueryError("Failed to retrieve orders")
    except Exception as e:
        response = handler.handle_error(e, context)
        print(f"Error handled with context")
        print(f"User: {context.user}")
        print(f"Persona: {context.persona}")
        print(f"Operation: {context.operation}")


def example_combined_retry_and_error_handling():
    """Example: Combining retry logic with error handling."""
    print("\n=== Example 9: Combined Retry and Error Handling ===")
    
    handler = ErrorHandler(logger)
    attempt_count = [0]
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.2, logger=logger)
    def call_bedrock_with_retry():
        """Simulate Bedrock API call with retry."""
        attempt_count[0] += 1
        
        if attempt_count[0] < 2:
            # Transient error - will be retried
            raise Exception("ThrottlingException: Rate limit exceeded")
        
        return {"response": "AI generated response"}
    
    context = ErrorContext(
        user="admin",
        persona="Warehouse Manager",
        operation="bedrock_invocation"
    )
    
    try:
        result = call_bedrock_with_retry()
        print(f"Success: {result}")
    except Exception as e:
        response = handler.handle_error(e, context)
        print(f"Failed: {response.user_message}")
        if response.retry_possible:
            print("User could try again later")


def example_real_world_scenario():
    """Example: Real-world query processing scenario."""
    print("\n=== Example 10: Real-World Scenario ===")
    
    handler = ErrorHandler(logger)
    
    def process_user_query(query, user, persona, session_id):
        """Process a user query with comprehensive error handling."""
        context = ErrorContext(
            user=user,
            persona=persona,
            query=query,
            session_id=session_id,
            operation="query_processing"
        )
        
        try:
            # Validate input
            if not query or len(query.strip()) == 0:
                raise ValidationError("Query cannot be empty")
            
            if len(query) > 1000:
                raise ValidationError("Query exceeds maximum length of 1000 characters")
            
            # Simulate query processing
            print(f"Processing query: {query[:50]}...")
            
            # Simulate potential errors
            if "error" in query.lower():
                raise QueryError("Failed to parse query")
            
            if "timeout" in query.lower():
                raise DatabaseError("Query execution timeout")
            
            # Success
            return {
                "success": True,
                "result": "Query executed successfully",
                "rows": 42
            }
            
        except Exception as e:
            error_response = handler.handle_error(e, context)
            
            return {
                "success": False,
                "error_category": error_response.category.value,
                "message": error_response.user_message,
                "retry_possible": error_response.retry_possible,
                "remediation_steps": error_response.remediation_steps
            }
    
    # Test various scenarios
    scenarios = [
        ("Show inventory levels", "john", "Warehouse Manager", "s1"),
        ("", "jane", "Field Engineer", "s2"),  # Empty query
        ("x" * 1001, "bob", "Procurement", "s3"),  # Too long
        ("Show error data", "alice", "Warehouse Manager", "s4"),  # Parse error
        ("Show timeout data", "charlie", "Field Engineer", "s5")  # Timeout
    ]
    
    for query, user, persona, session in scenarios:
        print(f"\nScenario: User={user}, Query='{query[:30]}...'")
        result = process_user_query(query, user, persona, session)
        
        if result["success"]:
            print(f"  Success: {result['result']}")
        else:
            print(f"  Error: {result['message']}")
            if result.get("remediation_steps"):
                print(f"  Remediation: {result['remediation_steps'][0]}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Error Handler Examples")
    print("=" * 60)
    
    example_basic_error_handling()
    example_custom_errors()
    example_retry_with_backoff()
    example_non_transient_error()
    example_handle_errors_decorator()
    example_error_statistics()
    example_global_error_handler()
    example_error_context()
    example_combined_retry_and_error_handling()
    example_real_world_scenario()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
