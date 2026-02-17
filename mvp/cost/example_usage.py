"""
Example usage of the cost tracking module

This script demonstrates how to use CostTracker and CostLogger
in the Supply Chain AI MVP system.
"""

from datetime import date, timedelta
from cost_tracker import CostTracker, Cost, TokenUsage
from cost_logger import CostLogger


def example_basic_usage():
    """Example: Basic cost tracking"""
    print("=" * 60)
    print("Example 1: Basic Cost Tracking")
    print("=" * 60)
    
    # Initialize tracker with configuration
    config = {
        'enabled': True,
        'bedrock_input_cost_per_1k': 0.003,
        'bedrock_output_cost_per_1k': 0.015,
        'redshift_rpu_cost_per_hour': 0.36,
        'redshift_base_rpus': 8,
        'lambda_cost_per_gb_second': 0.0000166667
    }
    
    tracker = CostTracker(config)
    
    # Simulate a query execution
    tokens = TokenUsage(input_tokens=1500, output_tokens=800)
    cost = tracker.calculate_query_cost(
        bedrock_tokens=tokens,
        redshift_execution_time=3.2,  # seconds
        lambda_duration_ms=450,
        lambda_memory_mb=512
    )
    
    print(f"\nQuery Cost Breakdown:")
    print(f"  Bedrock:  {tracker.format_cost(cost.bedrock_cost)}")
    print(f"  Redshift: {tracker.format_cost(cost.redshift_cost)}")
    print(f"  Lambda:   {tracker.format_cost(cost.lambda_cost)}")
    print(f"  Total:    {tracker.format_cost(cost.total_cost)}")
    print(f"  Tokens:   {cost.tokens_used.input_tokens} in / {cost.tokens_used.output_tokens} out")
    print()


def example_session_tracking():
    """Example: Track costs for multiple queries in a session"""
    print("=" * 60)
    print("Example 2: Session Cost Tracking")
    print("=" * 60)
    
    config = {
        'enabled': True,
        'bedrock_input_cost_per_1k': 0.003,
        'bedrock_output_cost_per_1k': 0.015,
        'redshift_rpu_cost_per_hour': 0.36,
        'redshift_base_rpus': 8,
        'lambda_cost_per_gb_second': 0.0000166667
    }
    
    tracker = CostTracker(config)
    session_id = "user_session_123"
    
    # Simulate multiple queries
    queries = [
        {"tokens": TokenUsage(1200, 600), "redshift_time": 2.1, "lambda_ms": 300},
        {"tokens": TokenUsage(800, 400), "redshift_time": 1.5, "lambda_ms": 0},
        {"tokens": TokenUsage(1500, 900), "redshift_time": 3.8, "lambda_ms": 500},
    ]
    
    print(f"\nProcessing {len(queries)} queries for session {session_id}...\n")
    
    for i, query_data in enumerate(queries, 1):
        cost = tracker.calculate_query_cost(
            bedrock_tokens=query_data["tokens"],
            redshift_execution_time=query_data["redshift_time"],
            lambda_duration_ms=query_data["lambda_ms"],
            lambda_memory_mb=512
        )
        tracker.add_query_cost(session_id, cost)
        print(f"Query {i}: {tracker.format_cost(cost.total_cost)}")
    
    # Get session summary
    print(f"\n{tracker.get_cost_summary(session_id)}")
    print()


def example_daily_tracking():
    """Example: Track daily costs across multiple sessions"""
    print("=" * 60)
    print("Example 3: Daily Cost Tracking")
    print("=" * 60)
    
    config = {
        'enabled': True,
        'bedrock_input_cost_per_1k': 0.003,
        'bedrock_output_cost_per_1k': 0.015,
        'redshift_rpu_cost_per_hour': 0.36,
        'redshift_base_rpus': 8,
        'lambda_cost_per_gb_second': 0.0000166667
    }
    
    tracker = CostTracker(config)
    
    # Simulate queries from different sessions
    sessions = ["session_1", "session_2", "session_3"]
    
    print(f"\nSimulating queries from {len(sessions)} different sessions...\n")
    
    for session_id in sessions:
        # Each session has 2-3 queries
        for _ in range(2):
            tokens = TokenUsage(input_tokens=1000, output_tokens=500)
            cost = tracker.calculate_query_cost(
                bedrock_tokens=tokens,
                redshift_execution_time=2.0,
                lambda_duration_ms=300,
                lambda_memory_mb=512
            )
            tracker.add_query_cost(session_id, cost)
    
    # Get daily summary
    print(tracker.get_cost_summary())
    
    # Get monthly estimate
    monthly_estimate = tracker.get_monthly_estimate()
    print(f"\nEstimated Monthly Cost: {tracker.format_cost(monthly_estimate)}")
    print()


def example_cost_logging():
    """Example: Log costs to file"""
    print("=" * 60)
    print("Example 4: Cost Logging")
    print("=" * 60)
    
    import tempfile
    import os
    
    # Create temporary log file
    temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
    temp_log.close()
    
    try:
        logger = CostLogger(temp_log.name, enabled=True)
        
        # Log some query costs
        cost1 = Cost(
            bedrock_cost=0.0123,
            redshift_cost=0.0045,
            lambda_cost=0.0008,
            total_cost=0.0176,
            tokens_used=TokenUsage(1000, 500)
        )
        
        logger.log_query_cost(
            session_id="session_123",
            persona="Warehouse Manager",
            query="Show me products with low stock levels",
            cost=cost1,
            execution_time=2.3,
            cached=False,
            query_type="SQL_QUERY"
        )
        
        cost2 = Cost(
            bedrock_cost=0.0089,
            redshift_cost=0.0032,
            lambda_cost=0.0012,
            total_cost=0.0133,
            tokens_used=TokenUsage(800, 400)
        )
        
        logger.log_query_cost(
            session_id="session_456",
            persona="Field Engineer",
            query="Optimize delivery route for today's orders",
            cost=cost2,
            execution_time=3.1,
            cached=False,
            query_type="OPTIMIZATION"
        )
        
        print(f"\nLogged 2 queries to: {temp_log.name}")
        
        # Read log entries
        entries = logger.read_log_entries()
        print(f"Found {len(entries)} log entries")
        
        # Display first entry
        if entries:
            print(f"\nFirst entry:")
            print(f"  Session: {entries[0]['session_id']}")
            print(f"  Persona: {entries[0]['persona']}")
            print(f"  Query: {entries[0]['query']}")
            print(f"  Total Cost: ${entries[0]['costs']['total']:.4f}")
        
        # Generate cost breakdown
        print(f"\n{logger.generate_cost_breakdown(cost1)}")
        
    finally:
        # Cleanup
        for handler in logger.logger.handlers[:]:
            handler.close()
            logger.logger.removeHandler(handler)
        try:
            os.unlink(temp_log.name)
        except:
            pass
    
    print()


def example_cost_reporting():
    """Example: Generate cost reports"""
    print("=" * 60)
    print("Example 5: Cost Reporting")
    print("=" * 60)
    
    import tempfile
    import os
    
    temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
    temp_log.close()
    
    try:
        logger = CostLogger(temp_log.name, enabled=True)
        
        # Create sample cost data for multiple days
        cost_data = {}
        today = date.today()
        
        for i in range(7):
            day = today - timedelta(days=i)
            cost_data[day] = Cost(
                bedrock_cost=0.5 + (i * 0.1),
                redshift_cost=0.3 + (i * 0.05),
                lambda_cost=0.1 + (i * 0.02),
                total_cost=0.9 + (i * 0.17),
                tokens_used=TokenUsage(10000 + (i * 1000), 5000 + (i * 500))
            )
        
        # Generate report
        start_date = today - timedelta(days=6)
        end_date = today
        
        report = logger.generate_cost_report(start_date, end_date, cost_data)
        print(f"\n{report}")
        
    finally:
        # Cleanup
        for handler in logger.logger.handlers[:]:
            handler.close()
            logger.logger.removeHandler(handler)
        try:
            os.unlink(temp_log.name)
        except:
            pass
    
    print()


def example_integration():
    """Example: Complete integration with query processing"""
    print("=" * 60)
    print("Example 6: Complete Integration")
    print("=" * 60)
    
    import tempfile
    import os
    import time
    
    # Setup
    config = {
        'enabled': True,
        'bedrock_input_cost_per_1k': 0.003,
        'bedrock_output_cost_per_1k': 0.015,
        'redshift_rpu_cost_per_hour': 0.36,
        'redshift_base_rpus': 8,
        'lambda_cost_per_gb_second': 0.0000166667
    }
    
    tracker = CostTracker(config)
    
    temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
    temp_log.close()
    logger = CostLogger(temp_log.name, enabled=True)
    
    try:
        # Simulate query processing
        def process_query(session_id, persona, query, query_type):
            """Simulate processing a query with cost tracking"""
            start_time = time.time()
            
            # Simulate query execution (in real system, this would call Bedrock, Redshift, etc.)
            tokens = TokenUsage(
                input_tokens=1000 + len(query),
                output_tokens=500
            )
            redshift_time = 2.5
            lambda_duration = 300 if query_type == "OPTIMIZATION" else 0
            
            # Calculate cost
            cost = tracker.calculate_query_cost(
                bedrock_tokens=tokens,
                redshift_execution_time=redshift_time,
                lambda_duration_ms=lambda_duration,
                lambda_memory_mb=512
            )
            
            execution_time = time.time() - start_time
            
            # Track and log
            tracker.add_query_cost(session_id, cost)
            logger.log_query_cost(
                session_id=session_id,
                persona=persona,
                query=query,
                cost=cost,
                execution_time=execution_time,
                cached=False,
                query_type=query_type
            )
            
            return cost
        
        # Process some queries
        queries = [
            ("session_1", "Warehouse Manager", "Show low stock products", "SQL_QUERY"),
            ("session_1", "Warehouse Manager", "Calculate reorder points", "OPTIMIZATION"),
            ("session_2", "Field Engineer", "Show today's deliveries", "SQL_QUERY"),
            ("session_2", "Field Engineer", "Optimize delivery routes", "OPTIMIZATION"),
        ]
        
        print("\nProcessing queries with cost tracking...\n")
        
        for session_id, persona, query, query_type in queries:
            cost = process_query(session_id, persona, query, query_type)
            print(f"{persona}: {query}")
            print(f"  Cost: {tracker.format_cost(cost.total_cost)}")
            print()
        
        # Display summaries
        print("Session Summaries:")
        print("-" * 60)
        for session_id in ["session_1", "session_2"]:
            session_cost = tracker.get_session_cost(session_id)
            print(f"{session_id}: {tracker.format_cost(session_cost.total_cost)}")
        
        print()
        print("Daily Summary:")
        print("-" * 60)
        daily_cost = tracker.get_daily_cost()
        print(f"Total: {tracker.format_cost(daily_cost.total_cost)}")
        print(f"Estimated Monthly: {tracker.format_cost(tracker.get_monthly_estimate())}")
        
    finally:
        # Cleanup
        for handler in logger.logger.handlers[:]:
            handler.close()
            logger.logger.removeHandler(handler)
        try:
            os.unlink(temp_log.name)
        except:
            pass
    
    print()


def main():
    """Run all examples"""
    print("\n")
    print("*" * 60)
    print("Cost Tracking Module - Usage Examples")
    print("*" * 60)
    print()
    
    example_basic_usage()
    example_session_tracking()
    example_daily_tracking()
    example_cost_logging()
    example_cost_reporting()
    example_integration()
    
    print("*" * 60)
    print("All examples completed!")
    print("*" * 60)
    print()


if __name__ == '__main__':
    main()
