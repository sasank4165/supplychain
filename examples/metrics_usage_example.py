"""Example usage of MetricsCollector for monitoring and analytics

This example demonstrates:
- Recording query metrics
- Recording business metrics
- Error tracking
- Getting statistics
- Integration with orchestrator
"""

import time
from datetime import datetime, timedelta
from metrics_collector import MetricsCollector, create_metrics_collector
from config_manager import ConfigurationManager


def example_basic_usage():
    """Basic metrics collection example"""
    print("=== Basic Metrics Collection ===\n")
    
    # Initialize metrics collector
    metrics = MetricsCollector(region="us-east-1")
    
    # Simulate processing a query
    start_time = time.time()
    
    # ... process query ...
    time.sleep(0.1)  # Simulate processing
    
    latency_ms = (time.time() - start_time) * 1000
    
    # Record metrics
    metrics.record_query(
        persona="warehouse_manager",
        agent="inventory_optimizer",
        query="What items need reordering?",
        latency_ms=latency_ms,
        success=True,
        token_count=1250,
        session_id="session123",
        user_id="user456",
        intent="optimization"
    )
    
    print(f"Recorded query with latency: {latency_ms:.2f}ms")
    print(f"Statistics: {metrics.get_stats()}\n")


def example_with_configuration():
    """Example using configuration manager"""
    print("=== Metrics with Configuration ===\n")
    
    # Load configuration
    config = ConfigurationManager(environment="dev")
    
    # Create metrics collector with config
    metrics = create_metrics_collector(
        region=config.get('environment.region'),
        config=config
    )
    
    print(f"Metrics namespace: {metrics.namespace}")
    print(f"Region: {metrics.region}\n")


def example_tool_execution_metrics():
    """Example recording tool execution metrics"""
    print("=== Tool Execution Metrics ===\n")
    
    metrics = MetricsCollector(region="us-east-1")
    
    # Simulate query with multiple tool executions
    tool_executions = [
        {
            "tool_name": "calculate_reorder_points",
            "duration_ms": 450,
            "success": True
        },
        {
            "tool_name": "forecast_demand",
            "duration_ms": 320,
            "success": True
        },
        {
            "tool_name": "identify_stockout_risks",
            "duration_ms": 280,
            "success": True
        }
    ]
    
    metrics.record_query(
        persona="warehouse_manager",
        agent="inventory_optimizer",
        query="Optimize inventory levels",
        latency_ms=1250.0,
        success=True,
        token_count=1800,
        tool_executions=tool_executions,
        session_id="session789"
    )
    
    print(f"Recorded query with {len(tool_executions)} tool executions")
    print(f"Total tool execution time: {sum(t['duration_ms'] for t in tool_executions)}ms\n")


def example_business_metrics():
    """Example recording custom business metrics"""
    print("=== Business Metrics ===\n")
    
    metrics = MetricsCollector(region="us-east-1")
    
    # Inventory optimization metrics
    metrics.record_business_metric(
        metric_name="ItemsOptimized",
        value=45,
        unit="Count",
        dimensions={
            "Warehouse": "WH-001",
            "Category": "Electronics"
        }
    )
    print("Recorded: 45 items optimized in WH-001")
    
    # Cost savings metric
    metrics.record_business_metric(
        metric_name="EstimatedCostSavings",
        value=12500.50,
        unit="None",
        dimensions={
            "Persona": "procurement_specialist",
            "OptimizationType": "supplier_consolidation"
        }
    )
    print("Recorded: $12,500.50 estimated cost savings")
    
    # Forecast accuracy metric
    metrics.record_business_metric(
        metric_name="ForecastAccuracy",
        value=94.5,
        unit="Percent",
        dimensions={
            "Agent": "inventory_optimizer",
            "TimeHorizon": "30_days"
        }
    )
    print("Recorded: 94.5% forecast accuracy")
    
    # Stockout risk metric
    metrics.record_business_metric(
        metric_name="StockoutRiskItems",
        value=12,
        unit="Count",
        dimensions={
            "Warehouse": "WH-001",
            "Severity": "High"
        }
    )
    print("Recorded: 12 high-risk stockout items\n")


def example_error_tracking():
    """Example error tracking with context"""
    print("=== Error Tracking ===\n")
    
    metrics = MetricsCollector(region="us-east-1")
    
    # Database timeout error
    metrics.record_error(
        persona="field_engineer",
        agent="logistics_agent",
        error_type="database_timeout",
        error_message="Query execution exceeded 30 second timeout",
        context={
            "query": "Complex route optimization query",
            "session_id": "session789",
            "user_id": "user456",
            "table": "shipments",
            "timeout_seconds": 30,
            "row_count_attempted": 50000
        }
    )
    print("Recorded: Database timeout error with context")
    
    # Validation error
    metrics.record_error(
        persona="warehouse_manager",
        agent="sql_agent",
        error_type="validation_error",
        error_message="Invalid warehouse code format",
        context={
            "warehouse_code": "INVALID",
            "expected_format": "WH-XXX",
            "user_input": "invalid123"
        }
    )
    print("Recorded: Validation error with context")
    
    # Model error
    metrics.record_error(
        persona="procurement_specialist",
        agent="supplier_analyzer",
        error_type="model_error",
        error_message="Bedrock throttling exception",
        context={
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "retry_count": 3,
            "backoff_seconds": 8
        }
    )
    print("Recorded: Model error with retry context\n")


def example_statistics():
    """Example getting and analyzing statistics"""
    print("=== Statistics Analysis ===\n")
    
    metrics = MetricsCollector(region="us-east-1")
    
    # Simulate multiple queries
    queries = [
        ("warehouse_manager", "inventory_optimizer", True, 1200.0, 1500),
        ("warehouse_manager", "sql_agent", True, 300.0, 800),
        ("field_engineer", "logistics_agent", True, 1800.0, 2000),
        ("field_engineer", "sql_agent", False, 500.0, 0),
        ("procurement_specialist", "supplier_analyzer", True, 1500.0, 1800),
        ("procurement_specialist", "sql_agent", True, 250.0, 600),
    ]
    
    for persona, agent, success, latency, tokens in queries:
        metrics.record_query(
            persona=persona,
            agent=agent,
            query="Test query",
            latency_ms=latency,
            success=success,
            token_count=tokens
        )
    
    # Get statistics
    stats = metrics.get_stats()
    
    print("Overall Statistics:")
    print(f"  Total Queries: {stats['total_queries']}")
    print(f"  Successful: {stats['successful_queries']}")
    print(f"  Failed: {stats['failed_queries']}")
    print(f"  Success Rate: {stats['success_rate_percent']}%")
    print(f"  Average Latency: {stats['average_latency_ms']:.2f}ms")
    print(f"  Total Tokens: {stats['total_tokens_used']}")
    print(f"  Avg Tokens/Query: {stats['average_tokens_per_query']:.2f}\n")


def example_orchestrator_integration():
    """Example integrating with orchestrator"""
    print("=== Orchestrator Integration ===\n")
    
    from orchestrator import SupplyChainOrchestrator
    
    # Initialize
    config = ConfigurationManager(environment="dev")
    orchestrator = SupplyChainOrchestrator(region="us-east-1", config=config)
    metrics = MetricsCollector(region="us-east-1", config=config)
    
    def process_with_metrics(query, persona, session_id, context=None):
        """Process query with automatic metrics collection"""
        start_time = time.time()
        
        try:
            result = orchestrator.process_query(query, persona, session_id, context or {})
            success = result.get("success", False)
            error_message = result.get("error")
            
            # Extract token count
            token_count = 0
            if "sql_response" in result:
                token_count += result["sql_response"].get("token_count", 0)
            if "specialist_response" in result:
                token_count += result["specialist_response"].get("token_count", 0)
            
            # Record metrics
            latency_ms = (time.time() - start_time) * 1000
            metrics.record_query(
                persona=persona,
                agent=result.get("intent", "unknown"),
                query=query,
                latency_ms=latency_ms,
                success=success,
                token_count=token_count,
                error_message=error_message,
                session_id=session_id,
                intent=result.get("intent")
            )
            
            return result
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            metrics.record_query(
                persona=persona,
                agent="orchestrator",
                query=query,
                latency_ms=latency_ms,
                success=False,
                error_message=str(e),
                session_id=session_id
            )
            
            metrics.record_error(
                persona=persona,
                agent="orchestrator",
                error_type="processing_error",
                error_message=str(e),
                context={
                    "query": query,
                    "session_id": session_id
                }
            )
            raise
    
    # Use it
    try:
        result = process_with_metrics(
            query="Show me items with low stock",
            persona="warehouse_manager",
            session_id="session123"
        )
        print(f"Query processed successfully: {result.get('success')}")
        print(f"Intent: {result.get('intent')}")
    except Exception as e:
        print(f"Query failed: {e}")
    
    # Get statistics
    stats = metrics.get_stats()
    print(f"\nMetrics: {stats}\n")


def example_metrics_summary():
    """Example getting metrics summary from CloudWatch"""
    print("=== CloudWatch Metrics Summary ===\n")
    
    metrics = MetricsCollector(region="us-east-1")
    
    # Get summary for last 24 hours
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    try:
        summary = metrics.get_metrics_summary(
            start_time=start_time,
            end_time=end_time,
            persona="warehouse_manager",
            agent="inventory_optimizer"
        )
        
        print("Metrics Summary (Last 24 Hours):")
        print(f"  Time Period: {summary['time_period']['start']} to {summary['time_period']['end']}")
        print(f"  Filters: {summary['filters']}")
        print(f"  Latency Data Points: {len(summary.get('latency', []))}")
        print(f"  Success Count Data Points: {len(summary.get('success_count', []))}")
        print(f"  Error Count Data Points: {len(summary.get('error_count', []))}")
        print(f"  Token Usage Data Points: {len(summary.get('token_usage', []))}\n")
    except Exception as e:
        print(f"Note: CloudWatch query requires actual AWS credentials: {e}\n")


def example_manual_flush():
    """Example manual metrics flushing"""
    print("=== Manual Metrics Flush ===\n")
    
    metrics = MetricsCollector(region="us-east-1")
    
    # Record some metrics
    metrics.record_query(
        persona="warehouse_manager",
        agent="sql_agent",
        query="Test query",
        latency_ms=100.0,
        success=True
    )
    
    print(f"Metrics in buffer: {len(metrics.metrics_buffer)}")
    
    # Manually flush
    metrics.flush()
    
    print(f"Metrics after flush: {len(metrics.metrics_buffer)}")
    print("Metrics published to CloudWatch\n")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("MetricsCollector Usage Examples")
    print("="*60 + "\n")
    
    try:
        example_basic_usage()
        example_with_configuration()
        example_tool_execution_metrics()
        example_business_metrics()
        example_error_tracking()
        example_statistics()
        example_manual_flush()
        
        # These require actual AWS setup
        # example_orchestrator_integration()
        # example_metrics_summary()
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Note: Some examples require AWS credentials and configuration")
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
