"""Asynchronous tool execution framework for agent tools

This module provides parallel tool execution with retry logic, timeout handling,
and status tracking for Lambda-based agent tools.

Requirements: 17.1, 17.2, 17.3, 17.4, 17.5
"""
import asyncio
import boto3
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from config_manager import ConfigurationManager

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ToolExecutionStatus(Enum):
    """Tool execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


@dataclass
class ToolExecutionResult:
    """Result of a tool execution"""
    tool_name: str
    status: ToolExecutionStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    attempts: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tool_name": self.tool_name,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "attempts": self.attempts,
            "metadata": self.metadata
        }
    
    def is_success(self) -> bool:
        """Check if execution was successful"""
        return self.status == ToolExecutionStatus.SUCCESS


@dataclass
class ToolExecutionRequest:
    """Request for tool execution"""
    tool_name: str
    function_name: str
    input_data: Dict[str, Any]
    timeout_seconds: int = 30
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolExecutor:
    """
    Execute agent tools asynchronously with parallel execution support
    
    Features:
    - Parallel tool execution using asyncio
    - Automatic retry with exponential backoff
    - Timeout handling for long-running tools
    - Tool execution status tracking
    - Lambda function invocation
    
    Requirements:
    - 17.1: Parallel tool execution
    - 17.2: Timeout handling
    - 17.3: Retry logic with exponential backoff
    - 17.4: Tool execution status tracking
    - 17.5: Fallback responses on failure
    """
    
    def __init__(
        self,
        region: str = "us-east-1",
        config: Optional[ConfigurationManager] = None,
        max_workers: int = 10
    ):
        """Initialize tool executor
        
        Args:
            region: AWS region
            config: Optional ConfigurationManager instance
            max_workers: Maximum number of parallel workers
        """
        self.region = region
        self.config = config
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Tool execution tracking
        self.execution_history: List[ToolExecutionResult] = []
        
        # Configuration
        self.default_timeout = 30
        self.default_max_retries = 3
        self.base_backoff_seconds = 1
        
        if config:
            self.default_timeout = config.get("agents.tool_timeout_seconds", 30)
            self.default_max_retries = config.get("agents.tool_max_retries", 3)
        
        logger.info(f"Initialized ToolExecutor with {max_workers} workers")
    
    async def execute_tools_parallel(
        self,
        tools: List[ToolExecutionRequest],
        timeout: Optional[int] = None
    ) -> List[ToolExecutionResult]:
        """Execute multiple tools in parallel
        
        Requirement 17.1: Support parallel tool execution
        
        Args:
            tools: List of tool execution requests
            timeout: Optional overall timeout for all tools
            
        Returns:
            List of tool execution results
        """
        if not tools:
            return []
        
        logger.info(f"Executing {len(tools)} tools in parallel")
        
        # Create tasks for all tools
        tasks = [self._execute_tool_async(tool) for tool in tools]
        
        # Execute with optional timeout
        try:
            if timeout:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout
                )
            else:
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Handle exception
                    processed_results.append(ToolExecutionResult(
                        tool_name=tools[i].tool_name,
                        status=ToolExecutionStatus.FAILED,
                        error=str(result),
                        metadata=tools[i].metadata
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except asyncio.TimeoutError:
            logger.error(f"Overall timeout ({timeout}s) exceeded for parallel execution")
            # Return timeout results for all tools
            return [
                ToolExecutionResult(
                    tool_name=tool.tool_name,
                    status=ToolExecutionStatus.TIMEOUT,
                    error=f"Overall timeout ({timeout}s) exceeded",
                    metadata=tool.metadata
                )
                for tool in tools
            ]
    
    async def _execute_tool_async(
        self,
        request: ToolExecutionRequest
    ) -> ToolExecutionResult:
        """Execute a single tool asynchronously with retry logic
        
        Requirements:
        - 17.2: Timeout handling
        - 17.3: Retry logic with exponential backoff
        
        Args:
            request: Tool execution request
            
        Returns:
            Tool execution result
        """
        start_time = time.time()
        attempts = 0
        last_error = None
        
        timeout = request.timeout_seconds or self.default_timeout
        max_retries = request.max_retries or self.default_max_retries
        
        while attempts < max_retries:
            attempts += 1
            
            try:
                logger.info(
                    f"Executing tool '{request.tool_name}' "
                    f"(attempt {attempts}/{max_retries})"
                )
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    self._invoke_lambda(request),
                    timeout=timeout
                )
                
                execution_time = (time.time() - start_time) * 1000
                
                # Success
                tool_result = ToolExecutionResult(
                    tool_name=request.tool_name,
                    status=ToolExecutionStatus.SUCCESS,
                    result=result,
                    execution_time_ms=execution_time,
                    attempts=attempts,
                    metadata=request.metadata
                )
                
                # Track execution
                self.execution_history.append(tool_result)
                
                logger.info(
                    f"Tool '{request.tool_name}' succeeded in "
                    f"{execution_time:.2f}ms (attempt {attempts})"
                )
                
                return tool_result
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {timeout}s"
                logger.warning(
                    f"Tool '{request.tool_name}' timed out "
                    f"(attempt {attempts}/{max_retries})"
                )
                
                if attempts >= max_retries:
                    execution_time = (time.time() - start_time) * 1000
                    tool_result = ToolExecutionResult(
                        tool_name=request.tool_name,
                        status=ToolExecutionStatus.TIMEOUT,
                        error=last_error,
                        execution_time_ms=execution_time,
                        attempts=attempts,
                        metadata=request.metadata
                    )
                    self.execution_history.append(tool_result)
                    return tool_result
                
            except Exception as e:
                last_error = str(e)
                logger.error(
                    f"Tool '{request.tool_name}' failed: {last_error} "
                    f"(attempt {attempts}/{max_retries})"
                )
                
                if attempts >= max_retries:
                    execution_time = (time.time() - start_time) * 1000
                    tool_result = ToolExecutionResult(
                        tool_name=request.tool_name,
                        status=ToolExecutionStatus.FAILED,
                        error=last_error,
                        execution_time_ms=execution_time,
                        attempts=attempts,
                        metadata=request.metadata
                    )
                    self.execution_history.append(tool_result)
                    return tool_result
            
            # Exponential backoff before retry
            if attempts < max_retries:
                backoff_time = self.base_backoff_seconds * (2 ** (attempts - 1))
                logger.info(f"Retrying in {backoff_time}s...")
                await asyncio.sleep(backoff_time)
        
        # Should not reach here, but handle it
        execution_time = (time.time() - start_time) * 1000
        tool_result = ToolExecutionResult(
            tool_name=request.tool_name,
            status=ToolExecutionStatus.FAILED,
            error=last_error or "Unknown error",
            execution_time_ms=execution_time,
            attempts=attempts,
            metadata=request.metadata
        )
        self.execution_history.append(tool_result)
        return tool_result
    
    async def _invoke_lambda(
        self,
        request: ToolExecutionRequest
    ) -> Dict[str, Any]:
        """Invoke Lambda function asynchronously
        
        Args:
            request: Tool execution request
            
        Returns:
            Lambda function result
        """
        # Prepare payload
        payload = {
            "tool_name": request.tool_name,
            "input": request.input_data
        }
        
        # Run Lambda invocation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            lambda: self.lambda_client.invoke(
                FunctionName=request.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        # Check for Lambda errors
        if 'FunctionError' in response:
            raise Exception(f"Lambda error: {response_payload}")
        
        # Check for application errors
        if isinstance(response_payload, dict) and 'error' in response_payload:
            raise Exception(response_payload['error'])
        
        return response_payload
    
    def execute_tool_sync(
        self,
        request: ToolExecutionRequest
    ) -> ToolExecutionResult:
        """Execute a single tool synchronously
        
        Convenience method for synchronous execution
        
        Args:
            request: Tool execution request
            
        Returns:
            Tool execution result
        """
        return asyncio.run(self._execute_tool_async(request))
    
    def execute_tools_sync(
        self,
        tools: List[ToolExecutionRequest],
        timeout: Optional[int] = None
    ) -> List[ToolExecutionResult]:
        """Execute multiple tools synchronously
        
        Convenience method for synchronous parallel execution
        
        Args:
            tools: List of tool execution requests
            timeout: Optional overall timeout
            
        Returns:
            List of tool execution results
        """
        return asyncio.run(self.execute_tools_parallel(tools, timeout))
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics
        
        Requirement 17.4: Tool execution status tracking
        
        Returns:
            Dictionary with execution statistics
        """
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_count": 0,
                "failure_count": 0,
                "timeout_count": 0,
                "success_rate": 0.0,
                "avg_execution_time_ms": 0.0,
                "avg_attempts": 0.0
            }
        
        total = len(self.execution_history)
        success = sum(1 for r in self.execution_history if r.is_success())
        failed = sum(1 for r in self.execution_history if r.status == ToolExecutionStatus.FAILED)
        timeout = sum(1 for r in self.execution_history if r.status == ToolExecutionStatus.TIMEOUT)
        
        avg_time = sum(r.execution_time_ms for r in self.execution_history) / total
        avg_attempts = sum(r.attempts for r in self.execution_history) / total
        
        return {
            "total_executions": total,
            "success_count": success,
            "failure_count": failed,
            "timeout_count": timeout,
            "success_rate": (success / total) * 100,
            "avg_execution_time_ms": round(avg_time, 2),
            "avg_attempts": round(avg_attempts, 2)
        }
    
    def get_tool_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get statistics for a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with tool-specific statistics
        """
        tool_executions = [
            r for r in self.execution_history
            if r.tool_name == tool_name
        ]
        
        if not tool_executions:
            return {
                "tool_name": tool_name,
                "total_executions": 0
            }
        
        total = len(tool_executions)
        success = sum(1 for r in tool_executions if r.is_success())
        
        return {
            "tool_name": tool_name,
            "total_executions": total,
            "success_count": success,
            "failure_count": total - success,
            "success_rate": (success / total) * 100,
            "avg_execution_time_ms": round(
                sum(r.execution_time_ms for r in tool_executions) / total, 2
            ),
            "avg_attempts": round(
                sum(r.attempts for r in tool_executions) / total, 2
            )
        }
    
    def clear_history(self):
        """Clear execution history"""
        self.execution_history = []
        logger.info("Cleared execution history")
    
    def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tool executions
        
        Args:
            limit: Maximum number of executions to return
            
        Returns:
            List of recent execution results
        """
        recent = self.execution_history[-limit:]
        return [r.to_dict() for r in recent]
