"""Test script for ToolExecutor functionality

This script tests the asynchronous tool execution framework.
"""
import asyncio
from tool_executor import ToolExecutor, ToolExecutionRequest, ToolExecutionStatus


def test_tool_executor_basic():
    """Test basic ToolExecutor functionality"""
    print("Testing ToolExecutor basic functionality...")
    
    # Initialize ToolExecutor
    executor = ToolExecutor(region="us-east-1", max_workers=5)
    
    print(f"✓ ToolExecutor initialized")
    
    # Test execution stats (should be empty initially)
    stats = executor.get_execution_stats()
    print(f"✓ Initial stats: {stats}")
    
    assert stats["total_executions"] == 0, "Initial execution count should be 0"
    print("✓ All basic tests passed!")


def test_tool_execution_request():
    """Test ToolExecutionRequest creation"""
    print("\nTesting ToolExecutionRequest...")
    
    request = ToolExecutionRequest(
        tool_name="test_tool",
        function_name="test-lambda-function",
        input_data={"param1": "value1"},
        timeout_seconds=30,
        max_retries=3,
        metadata={"test": "metadata"}
    )
    
    print(f"✓ Created request: {request.tool_name}")
    assert request.tool_name == "test_tool"
    assert request.timeout_seconds == 30
    assert request.max_retries == 3
    print("✓ ToolExecutionRequest tests passed!")


def test_parallel_execution_structure():
    """Test parallel execution structure (without actual Lambda calls)"""
    print("\nTesting parallel execution structure...")
    
    executor = ToolExecutor(region="us-east-1", max_workers=3)
    
    # Create multiple requests
    requests = [
        ToolExecutionRequest(
            tool_name=f"tool_{i}",
            function_name="test-function",
            input_data={"index": i},
            timeout_seconds=10,
            max_retries=2
        )
        for i in range(3)
    ]
    
    print(f"✓ Created {len(requests)} tool execution requests")
    
    # Verify request structure
    for i, req in enumerate(requests):
        assert req.tool_name == f"tool_{i}"
        assert req.input_data["index"] == i
    
    print("✓ Parallel execution structure tests passed!")


def test_execution_result():
    """Test ToolExecutionResult structure"""
    print("\nTesting ToolExecutionResult...")
    
    from tool_executor import ToolExecutionResult
    
    # Test success result
    success_result = ToolExecutionResult(
        tool_name="test_tool",
        status=ToolExecutionStatus.SUCCESS,
        result={"data": "test"},
        execution_time_ms=150.5,
        attempts=1
    )
    
    assert success_result.is_success()
    assert success_result.status == ToolExecutionStatus.SUCCESS
    print("✓ Success result created")
    
    # Test failure result
    failure_result = ToolExecutionResult(
        tool_name="test_tool",
        status=ToolExecutionStatus.FAILED,
        error="Test error",
        execution_time_ms=100.0,
        attempts=3
    )
    
    assert not failure_result.is_success()
    assert failure_result.error == "Test error"
    print("✓ Failure result created")
    
    # Test to_dict conversion
    result_dict = success_result.to_dict()
    assert result_dict["tool_name"] == "test_tool"
    assert result_dict["status"] == "success"
    print("✓ Result to_dict conversion works")
    
    print("✓ ToolExecutionResult tests passed!")


def test_stats_tracking():
    """Test execution statistics tracking"""
    print("\nTesting statistics tracking...")
    
    from tool_executor import ToolExecutionResult
    
    executor = ToolExecutor(region="us-east-1")
    
    # Manually add some results to history for testing
    executor.execution_history.append(
        ToolExecutionResult(
            tool_name="tool_1",
            status=ToolExecutionStatus.SUCCESS,
            result={"data": "test"},
            execution_time_ms=100.0,
            attempts=1
        )
    )
    
    executor.execution_history.append(
        ToolExecutionResult(
            tool_name="tool_1",
            status=ToolExecutionStatus.FAILED,
            error="Test error",
            execution_time_ms=200.0,
            attempts=3
        )
    )
    
    executor.execution_history.append(
        ToolExecutionResult(
            tool_name="tool_2",
            status=ToolExecutionStatus.SUCCESS,
            result={"data": "test2"},
            execution_time_ms=150.0,
            attempts=1
        )
    )
    
    # Test overall stats
    stats = executor.get_execution_stats()
    assert stats["total_executions"] == 3
    assert stats["success_count"] == 2
    assert stats["failure_count"] == 1
    assert stats["success_rate"] == (2/3) * 100
    print(f"✓ Overall stats: {stats}")
    
    # Test tool-specific stats
    tool1_stats = executor.get_tool_stats("tool_1")
    assert tool1_stats["total_executions"] == 2
    assert tool1_stats["success_count"] == 1
    print(f"✓ Tool-specific stats: {tool1_stats}")
    
    # Test recent executions
    recent = executor.get_recent_executions(limit=2)
    assert len(recent) == 2
    print(f"✓ Recent executions: {len(recent)} items")
    
    # Test clear history
    executor.clear_history()
    stats_after_clear = executor.get_execution_stats()
    assert stats_after_clear["total_executions"] == 0
    print("✓ History cleared successfully")
    
    print("✓ Statistics tracking tests passed!")


def main():
    """Run all tests"""
    print("=" * 60)
    print("ToolExecutor Test Suite")
    print("=" * 60)
    
    try:
        test_tool_executor_basic()
        test_tool_execution_request()
        test_parallel_execution_structure()
        test_execution_result()
        test_stats_tracking()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
