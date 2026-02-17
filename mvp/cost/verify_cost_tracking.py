"""
Verification script for cost tracking module
"""

import sys
from datetime import date
from pathlib import Path

# Import directly without relative imports
import cost_tracker
import cost_logger

CostTracker = cost_tracker.CostTracker
Cost = cost_tracker.Cost
TokenUsage = cost_tracker.TokenUsage
CostLogger = cost_logger.CostLogger


def test_token_usage():
    """Test TokenUsage functionality"""
    print("Testing TokenUsage...")
    
    tokens1 = TokenUsage(input_tokens=100, output_tokens=200)
    tokens2 = TokenUsage(input_tokens=50, output_tokens=75)
    result = tokens1 + tokens2
    
    assert result.input_tokens == 150, f"Expected 150, got {result.input_tokens}"
    assert result.output_tokens == 275, f"Expected 275, got {result.output_tokens}"
    
    print("✓ TokenUsage tests passed")


def test_cost():
    """Test Cost functionality"""
    print("Testing Cost...")
    
    cost1 = Cost(
        bedrock_cost=0.01,
        redshift_cost=0.005,
        lambda_cost=0.001,
        total_cost=0.016,
        tokens_used=TokenUsage(100, 200)
    )
    cost2 = Cost(
        bedrock_cost=0.02,
        redshift_cost=0.003,
        lambda_cost=0.002,
        total_cost=0.025,
        tokens_used=TokenUsage(50, 75)
    )
    
    result = cost1 + cost2
    
    assert abs(result.bedrock_cost - 0.03) < 0.0001, f"Expected 0.03, got {result.bedrock_cost}"
    assert abs(result.total_cost - 0.041) < 0.0001, f"Expected 0.041, got {result.total_cost}"
    assert result.tokens_used.input_tokens == 150, f"Expected 150, got {result.tokens_used.input_tokens}"
    
    print("✓ Cost tests passed")


def test_cost_tracker():
    """Test CostTracker functionality"""
    print("Testing CostTracker...")
    
    config = {
        'enabled': True,
        'bedrock_input_cost_per_1k': 0.003,
        'bedrock_output_cost_per_1k': 0.015,
        'redshift_rpu_cost_per_hour': 0.36,
        'redshift_base_rpus': 8,
        'lambda_cost_per_gb_second': 0.0000166667
    }
    
    tracker = CostTracker(config)
    
    # Test Bedrock cost calculation
    bedrock_cost = tracker.calculate_bedrock_cost(1000, 1000)
    expected_bedrock = (1000/1000 * 0.003) + (1000/1000 * 0.015)
    assert abs(bedrock_cost - expected_bedrock) < 0.0001, f"Expected {expected_bedrock}, got {bedrock_cost}"
    
    # Test Redshift cost calculation
    redshift_cost = tracker.calculate_redshift_cost(10.0)
    expected_redshift = 8 * (10/3600) * 0.36
    assert abs(redshift_cost - expected_redshift) < 0.0001, f"Expected {expected_redshift}, got {redshift_cost}"
    
    # Test Lambda cost calculation
    lambda_cost = tracker.calculate_lambda_cost(1000, 512)
    expected_lambda = (512/1024) * 1 * 0.0000166667
    assert abs(lambda_cost - expected_lambda) < 0.000001, f"Expected {expected_lambda}, got {lambda_cost}"
    
    # Test query cost calculation
    tokens = TokenUsage(input_tokens=1000, output_tokens=500)
    query_cost = tracker.calculate_query_cost(
        bedrock_tokens=tokens,
        redshift_execution_time=5.0,
        lambda_duration_ms=500,
        lambda_memory_mb=512
    )
    
    assert query_cost.bedrock_cost > 0, "Bedrock cost should be > 0"
    assert query_cost.redshift_cost > 0, "Redshift cost should be > 0"
    assert query_cost.lambda_cost > 0, "Lambda cost should be > 0"
    assert query_cost.tokens_used.input_tokens == 1000, f"Expected 1000 input tokens, got {query_cost.tokens_used.input_tokens}"
    
    # Test adding query costs
    session_id = "test_session"
    cost = Cost(
        bedrock_cost=0.01,
        redshift_cost=0.005,
        lambda_cost=0.001,
        total_cost=0.016,
        tokens_used=TokenUsage(100, 200)
    )
    
    tracker.add_query_cost(session_id, cost)
    
    session_cost = tracker.get_session_cost(session_id)
    assert abs(session_cost.total_cost - 0.016) < 0.0001, f"Expected 0.016, got {session_cost.total_cost}"
    
    daily_cost = tracker.get_daily_cost()
    assert abs(daily_cost.total_cost - 0.016) < 0.0001, f"Expected 0.016, got {daily_cost.total_cost}"
    
    # Test monthly estimate
    monthly_estimate = tracker.get_monthly_estimate()
    expected_monthly = 0.016 * 30
    assert abs(monthly_estimate - expected_monthly) < 0.001, f"Expected {expected_monthly}, got {monthly_estimate}"
    
    # Test cost breakdown
    breakdown = tracker.get_cost_breakdown(session_id)
    assert 'bedrock' in breakdown, "Breakdown should contain 'bedrock'"
    assert 'redshift' in breakdown, "Breakdown should contain 'redshift'"
    assert 'lambda' in breakdown, "Breakdown should contain 'lambda'"
    assert 'total' in breakdown, "Breakdown should contain 'total'"
    
    # Test cost formatting
    formatted = tracker.format_cost(0.0234)
    assert formatted == "$0.0234", f"Expected '$0.0234', got '{formatted}'"
    
    # Test cost summary
    summary = tracker.get_cost_summary(session_id)
    assert "Session Cost Summary:" in summary, "Summary should contain title"
    assert "Bedrock:" in summary, "Summary should contain Bedrock cost"
    assert "Total:" in summary, "Summary should contain total cost"
    
    print("✓ CostTracker tests passed")


def test_cost_logger():
    """Test CostLogger functionality"""
    print("Testing CostLogger...")
    
    import tempfile
    
    # Create temporary log file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_log_file = f.name
    
    try:
        logger = CostLogger(temp_log_file, enabled=True)
        
        # Test logging query cost
        cost = Cost(
            bedrock_cost=0.01,
            redshift_cost=0.005,
            lambda_cost=0.001,
            total_cost=0.016,
            tokens_used=TokenUsage(100, 200)
        )
        
        logger.log_query_cost(
            session_id="test_session",
            persona="Warehouse Manager",
            query="Show me low stock products",
            cost=cost,
            execution_time=2.5,
            cached=False,
            query_type="SQL_QUERY"
        )
        
        # Verify log file was created
        assert Path(temp_log_file).exists(), "Log file should exist"
        
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "test_session" in content, "Log should contain session_id"
            assert "Warehouse Manager" in content, "Log should contain persona"
        
        # Test cost breakdown
        breakdown = logger.generate_cost_breakdown(cost)
        assert "Bedrock:" in breakdown, "Breakdown should contain Bedrock"
        assert "$0.0100" in breakdown, "Breakdown should contain formatted cost"
        
        # Test daily summary
        logger.log_daily_summary(date.today(), cost, query_count=10)
        
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "daily_summary" in content, "Log should contain daily summary"
        
        # Test reading log entries
        entries = logger.read_log_entries()
        assert len(entries) > 0, "Should have log entries"
        assert entries[0]['session_id'] == 'test_session', "Entry should have correct session_id"
        
        print("✓ CostLogger tests passed")
        
    finally:
        # Cleanup - close logger handlers first
        for handler in logger.logger.handlers[:]:
            handler.close()
            logger.logger.removeHandler(handler)
        
        # Now try to delete the file
        try:
            Path(temp_log_file).unlink(missing_ok=True)
        except PermissionError:
            # On Windows, file might still be locked
            pass


def main():
    """Run all tests"""
    print("=" * 60)
    print("Cost Tracking Module Verification")
    print("=" * 60)
    print()
    
    try:
        test_token_usage()
        test_cost()
        test_cost_tracker()
        test_cost_logger()
        
        print()
        print("=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"✗ Test failed: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
