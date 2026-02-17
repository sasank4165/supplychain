# Error Handler

Comprehensive error handling system for the Supply Chain AI MVP with categorization, user-friendly messages, retry logic with exponential backoff, and detailed error logging.

## Features

- **Error Categorization**: Automatically categorizes errors into predefined categories (Authentication, Database, Bedrock, etc.)
- **User-Friendly Messages**: Converts technical errors into clear, actionable messages for users
- **Retry Logic**: Automatic retry with exponential backoff for transient errors
- **Error Logging**: Detailed logging with stack traces and context information
- **Error Statistics**: Track error counts by category for monitoring
- **Custom Error Classes**: Specialized exception classes for different error types

## Error Categories

- `AUTHENTICATION`: Login and credential errors
- `AUTHORIZATION`: Permission and access control errors
- `QUERY`: Query processing and parsing errors
- `DATABASE`: Redshift and database connection errors
- `AGENT`: Agent execution errors
- `BEDROCK`: Bedrock API errors
- `LAMBDA`: Lambda function invocation errors
- `CONFIGURATION`: Configuration and setup errors
- `NETWORK`: Network and connection errors
- `VALIDATION`: Input validation errors
- `SYSTEM`: General system errors
- `UNKNOWN`: Uncategorized errors

## Error Severity Levels

- `LOW`: Minor issues that don't significantly impact functionality
- `MEDIUM`: Moderate issues that may affect some operations
- `HIGH`: Serious issues that prevent operations from completing
- `CRITICAL`: Critical issues that require immediate attention

## Usage

### Basic Error Handling

```python
from mvp.utils.error_handler import ErrorHandler, ErrorContext

# Create error handler
handler = ErrorHandler(logger)

# Handle an error
try:
    # Some operation that might fail
    result = risky_operation()
except Exception as e:
    # Create context
    context = ErrorContext(
        user="john_doe",
        persona="Warehouse Manager",
        query="Show inventory",
        session_id="session123"
    )
    
    # Handle the error
    error_response = handler.handle_error(e, context)
    
    # Display user-friendly message
    print(error_response.user_message)
    
    # Show remediation steps if available
    if error_response.remediation_steps:
        print("Try these steps:")
        for step in error_response.remediation_steps:
            print(f"  - {step}")
```

### Using Custom Error Classes

```python
from mvp.utils.error_handler import (
    AuthenticationError,
    DatabaseError,
    QueryError,
    ValidationError
)

# Raise specific errors
if not user_authenticated:
    raise AuthenticationError("Invalid credentials")

if query_invalid:
    raise ValidationError("Query exceeds maximum length")

if db_connection_failed:
    raise DatabaseError("Unable to connect to Redshift")
```

### Retry with Exponential Backoff

```python
from mvp.utils.error_handler import retry_with_backoff

# Retry a function up to 3 times with exponential backoff
@retry_with_backoff(
    max_attempts=3,
    initial_delay=1.0,
    backoff_factor=2.0,
    max_delay=60.0
)
def call_bedrock_api():
    # API call that might fail transiently
    response = bedrock_client.invoke_model(...)
    return response

# The function will automatically retry on transient errors
result = call_bedrock_api()
```

### Handle Errors Decorator

```python
from mvp.utils.error_handler import handle_errors, ErrorHandler

handler = ErrorHandler(logger)

# Automatically handle errors in a function
@handle_errors(error_handler=handler, reraise=False)
def process_query(query):
    # Query processing logic
    result = execute_query(query)
    return result

# If an error occurs, it returns an ErrorResponse instead of raising
response = process_query("SELECT * FROM products")
if isinstance(response, ErrorResponse):
    print(response.user_message)
```

### Global Error Handler

```python
from mvp.utils.error_handler import get_error_handler, set_error_handler

# Get the global error handler instance
handler = get_error_handler(logger)

# Use it throughout your application
error_response = handler.handle_error(exception)

# Or set a custom global handler
custom_handler = ErrorHandler(custom_logger)
set_error_handler(custom_handler)
```

### Error Statistics

```python
from mvp.utils.error_handler import ErrorHandler

handler = ErrorHandler(logger)

# Handle some errors
handler.handle_error(AuthenticationError("Login failed"))
handler.handle_error(DatabaseError("Connection timeout"))
handler.handle_error(DatabaseError("Query failed"))

# Get error statistics
stats = handler.get_error_stats()
print(stats)
# Output: {'authentication': 1, 'database': 2}

# Reset statistics
handler.reset_stats()
```

## Error Response Structure

The `ErrorResponse` object contains:

- `category`: ErrorCategory enum value
- `severity`: ErrorSeverity enum value
- `user_message`: User-friendly error message
- `technical_message`: Technical error details
- `error_code`: Optional error code
- `retry_possible`: Boolean indicating if retry might succeed
- `remediation_steps`: List of suggested remediation steps
- `timestamp`: Error timestamp

## Transient Error Detection

The error handler automatically detects transient errors that should be retried:

- Timeout errors
- Throttling/rate limit errors
- Network connection errors
- 502, 503, 504 HTTP errors
- "Temporarily unavailable" messages

Non-transient errors (like validation errors) are not retried.

## Integration with Logging

The error handler integrates with the logging system:

```python
from mvp.utils.logger import setup_application_logger
from mvp.utils.error_handler import ErrorHandler

# Set up logger
config = load_config()
logger = setup_application_logger(config)

# Create error handler with logger
handler = ErrorHandler(logger)

# Errors are automatically logged with:
# - Error category and severity
# - Full stack trace
# - Context information
# - Appropriate log level (critical, error, warning, info)
```

## Best Practices

1. **Use Specific Error Classes**: Use `AuthenticationError`, `DatabaseError`, etc. instead of generic `Exception`
2. **Provide Context**: Always include `ErrorContext` when handling errors
3. **Check Retry Possibility**: Use `error_response.retry_possible` to determine if retry makes sense
4. **Show Remediation Steps**: Display `remediation_steps` to help users resolve issues
5. **Monitor Error Stats**: Regularly check `get_error_stats()` to identify patterns
6. **Use Decorators**: Use `@retry_with_backoff` and `@handle_errors` for cleaner code
7. **Log Appropriately**: Let the error handler manage logging levels based on severity

## Testing

Run the test suite:

```bash
pytest mvp/utils/test_error_handler.py -v
```

The test suite covers:
- Error categorization
- User-friendly messages
- Retry logic with exponential backoff
- Error logging
- Custom error classes
- Transient error detection
- Error statistics
- Decorators

## Configuration

Error handling behavior can be customized:

```python
# Custom retry configuration
@retry_with_backoff(
    max_attempts=5,        # Try up to 5 times
    initial_delay=2.0,     # Start with 2 second delay
    backoff_factor=3.0,    # Triple delay each time
    max_delay=120.0        # Cap at 2 minutes
)
def my_function():
    pass

# Custom error handler
handler = ErrorHandler(logger)
handler.USER_MESSAGES[ErrorCategory.QUERY] = "Custom query error message"
handler.REMEDIATION_STEPS[ErrorCategory.QUERY] = ["Step 1", "Step 2"]
```

## Error Flow

1. **Exception Occurs**: An error is raised in the application
2. **Categorization**: Error handler categorizes the error
3. **Logging**: Error is logged with full details and context
4. **User Message**: Technical error is converted to user-friendly message
5. **Remediation**: Appropriate remediation steps are identified
6. **Response**: ErrorResponse is returned with all information
7. **Retry Decision**: If transient, retry logic may be applied

## Integration Points

The error handler integrates with:

- **Logger**: For detailed error logging
- **Orchestrator**: For query processing errors
- **Agents**: For agent execution errors
- **AWS Clients**: For Bedrock, Redshift, Lambda errors
- **Authentication**: For login and authorization errors
- **UI**: For displaying user-friendly messages

## Example: Complete Error Handling Flow

```python
from mvp.utils.logger import setup_application_logger
from mvp.utils.error_handler import (
    ErrorHandler,
    ErrorContext,
    retry_with_backoff,
    DatabaseError
)

# Set up
config = load_config()
logger = setup_application_logger(config)
handler = ErrorHandler(logger)

# Function with retry logic
@retry_with_backoff(max_attempts=3, initial_delay=1.0)
def execute_query(sql):
    try:
        result = redshift_client.execute_statement(sql)
        return result
    except Exception as e:
        raise DatabaseError(f"Query execution failed: {e}", original_error=e)

# Handle errors in application
def process_user_query(query, user, persona, session_id):
    context = ErrorContext(
        user=user,
        persona=persona,
        query=query,
        session_id=session_id,
        operation="query_execution"
    )
    
    try:
        # Execute with automatic retry
        result = execute_query(query)
        return result
    except Exception as e:
        # Handle and log error
        error_response = handler.handle_error(e, context)
        
        # Return user-friendly response
        return {
            "success": False,
            "message": error_response.user_message,
            "remediation": error_response.remediation_steps,
            "retry_possible": error_response.retry_possible
        }
```
