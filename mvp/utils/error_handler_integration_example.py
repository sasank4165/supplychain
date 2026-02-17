"""
Error Handler Integration Examples

Shows how to integrate the error handler with existing MVP components.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handler import (
    ErrorHandler,
    ErrorContext,
    DatabaseError,
    BedrockError,
    QueryError,
    retry_with_backoff,
    handle_errors
)
from utils.logger import setup_logger


# Example 1: Integration with Redshift Client
class RedshiftClientWithErrorHandling:
    """Redshift client with integrated error handling."""
    
    def __init__(self, logger):
        self.logger = logger
        self.error_handler = ErrorHandler(logger)
    
    @retry_with_backoff(max_attempts=3, initial_delay=1.0)
    def execute_query(self, sql, context=None):
        """Execute SQL query with automatic retry on transient errors."""
        try:
            # Simulate query execution
            print(f"Executing query: {sql[:50]}...")
            
            # Simulate potential errors
            if "timeout" in sql.lower():
                raise Exception("Query execution timeout")
            
            # Success
            return {"rows": 42, "columns": ["col1", "col2"]}
            
        except Exception as e:
            # Convert to DatabaseError for proper categorization
            db_error = DatabaseError(f"Query execution failed: {e}", original_error=e)
            
            # Handle error with context
            error_response = self.error_handler.handle_error(db_error, context)
            
            # Re-raise for retry logic to work
            raise db_error


# Example 2: Integration with Bedrock Client
class BedrockClientWithErrorHandling:
    """Bedrock client with integrated error handling."""
    
    def __init__(self, logger):
        self.logger = logger
        self.error_handler = ErrorHandler(logger)
    
    @retry_with_backoff(max_attempts=3, initial_delay=2.0, backoff_factor=2.0)
    def invoke_model(self, prompt, context=None):
        """Invoke Bedrock model with automatic retry."""
        try:
            # Simulate model invocation
            print(f"Invoking Bedrock with prompt: {prompt[:50]}...")
            
            # Simulate potential errors
            if "throttle" in prompt.lower():
                raise Exception("ThrottlingException: Rate limit exceeded")
            
            # Success
            return {"response": "AI generated response"}
            
        except Exception as e:
            # Convert to BedrockError
            bedrock_error = BedrockError(f"Model invocation failed: {e}", original_error=e)
            
            # Handle error
            error_response = self.error_handler.handle_error(bedrock_error, context)
            
            # Re-raise for retry
            raise bedrock_error


# Example 3: Integration with SQL Agent
class SQLAgentWithErrorHandling:
    """SQL Agent with integrated error handling."""
    
    def __init__(self, logger, redshift_client, bedrock_client):
        self.logger = logger
        self.error_handler = ErrorHandler(logger)
        self.redshift_client = redshift_client
        self.bedrock_client = bedrock_client
    
    def process_query(self, query, user, persona, session_id):
        """Process user query with comprehensive error handling."""
        context = ErrorContext(
            user=user,
            persona=persona,
            query=query,
            session_id=session_id,
            operation="query_processing"
        )
        
        try:
            # Step 1: Generate SQL using Bedrock
            print(f"\nProcessing query for {persona}: {query}")
            
            sql_prompt = f"Convert to SQL: {query}"
            bedrock_response = self.bedrock_client.invoke_model(sql_prompt, context)
            
            # Step 2: Execute SQL
            sql = "SELECT * FROM products WHERE category = 'Electronics'"
            result = self.redshift_client.execute_query(sql, context)
            
            # Success
            return {
                "success": True,
                "result": result,
                "message": "Query executed successfully"
            }
            
        except DatabaseError as e:
            error_response = self.error_handler.handle_error(e, context)
            return {
                "success": False,
                "error_category": error_response.category.value,
                "message": error_response.user_message,
                "retry_possible": error_response.retry_possible,
                "remediation_steps": error_response.remediation_steps
            }
            
        except BedrockError as e:
            error_response = self.error_handler.handle_error(e, context)
            return {
                "success": False,
                "error_category": error_response.category.value,
                "message": error_response.user_message,
                "retry_possible": error_response.retry_possible
            }
            
        except Exception as e:
            # Catch-all for unexpected errors
            error_response = self.error_handler.handle_error(e, context)
            return {
                "success": False,
                "error_category": error_response.category.value,
                "message": error_response.user_message
            }


# Example 4: Integration with Orchestrator
class QueryOrchestratorWithErrorHandling:
    """Query orchestrator with integrated error handling."""
    
    def __init__(self, logger):
        self.logger = logger
        self.error_handler = ErrorHandler(logger)
        
        # Initialize clients with error handling
        self.redshift_client = RedshiftClientWithErrorHandling(logger)
        self.bedrock_client = BedrockClientWithErrorHandling(logger)
        self.sql_agent = SQLAgentWithErrorHandling(
            logger,
            self.redshift_client,
            self.bedrock_client
        )
    
    def process_user_request(self, query, user, persona, session_id):
        """Process user request with error handling at orchestrator level."""
        print(f"\n{'='*60}")
        print(f"Orchestrator processing request")
        print(f"User: {user}, Persona: {persona}")
        print(f"{'='*60}")
        
        # Delegate to SQL agent
        result = self.sql_agent.process_query(query, user, persona, session_id)
        
        # Display result
        if result["success"]:
            print(f"\nSuccess: {result['message']}")
            print(f"Rows returned: {result['result']['rows']}")
        else:
            print(f"\nError: {result['message']}")
            print(f"Category: {result['error_category']}")
            
            if result.get("retry_possible"):
                print("Retry: This error may be temporary. Please try again.")
            
            if result.get("remediation_steps"):
                print("\nRemediation steps:")
                for step in result["remediation_steps"]:
                    print(f"  - {step}")
        
        return result


def demo_integration():
    """Demonstrate error handler integration."""
    print("=" * 60)
    print("Error Handler Integration Demo")
    print("=" * 60)
    
    # Set up logger
    logger = setup_logger(
        name="integration_demo",
        log_file="logs/integration_demo.log",
        level="INFO"
    )
    
    # Create orchestrator
    orchestrator = QueryOrchestratorWithErrorHandling(logger)
    
    # Test scenarios
    scenarios = [
        {
            "query": "Show all products in Electronics category",
            "user": "john_doe",
            "persona": "Warehouse Manager",
            "session_id": "session_001"
        },
        {
            "query": "Show products with timeout in query",
            "user": "jane_smith",
            "persona": "Field Engineer",
            "session_id": "session_002"
        },
        {
            "query": "Generate SQL with throttle error",
            "user": "bob_jones",
            "persona": "Procurement Specialist",
            "session_id": "session_003"
        }
    ]
    
    for scenario in scenarios:
        try:
            result = orchestrator.process_user_request(
                scenario["query"],
                scenario["user"],
                scenario["persona"],
                scenario["session_id"]
            )
        except Exception as e:
            print(f"\nUnexpected error: {e}")
    
    # Show error statistics
    print(f"\n{'='*60}")
    print("Error Statistics")
    print(f"{'='*60}")
    stats = orchestrator.error_handler.get_error_stats()
    if stats:
        for category, count in stats.items():
            print(f"{category}: {count}")
    else:
        print("No errors recorded")


if __name__ == "__main__":
    demo_integration()
