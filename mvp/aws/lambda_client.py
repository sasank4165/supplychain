"""
AWS Lambda Client Wrapper

Provides a simplified interface for invoking Lambda functions.
"""

import boto3
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class LambdaResponse:
    """Response from Lambda function invocation."""
    status_code: int
    payload: Dict[str, Any]
    function_error: Optional[str] = None
    log_result: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Check if invocation was successful."""
        return self.status_code == 200 and self.function_error is None


class LambdaClientError(Exception):
    """Raised when Lambda invocation fails."""
    pass


class LambdaClient:
    """Client for AWS Lambda function invocations."""
    
    def __init__(self, region: str):
        """
        Initialize Lambda client.
        
        Args:
            region: AWS region
        """
        self.region = region
        
        try:
            self.client = boto3.client('lambda', region_name=region)
        except Exception as e:
            raise LambdaClientError(f"Failed to initialize Lambda client: {e}")
    
    def invoke(
        self,
        function_name: str,
        payload: Dict[str, Any],
        invocation_type: str = 'RequestResponse'
    ) -> LambdaResponse:
        """
        Invoke a Lambda function.
        
        Args:
            function_name: Name or ARN of Lambda function
            payload: Input payload for the function
            invocation_type: 'RequestResponse' (synchronous) or 'Event' (asynchronous)
            
        Returns:
            LambdaResponse with function output
            
        Raises:
            LambdaClientError: If invocation fails
        """
        try:
            # Invoke Lambda function
            response = self.client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload)
            )
            
            # Extract response
            status_code = response['StatusCode']
            function_error = response.get('FunctionError')
            log_result = response.get('LogResult')
            
            # Parse payload
            payload_bytes = response['Payload'].read()
            response_payload = json.loads(payload_bytes) if payload_bytes else {}
            
            return LambdaResponse(
                status_code=status_code,
                payload=response_payload,
                function_error=function_error,
                log_result=log_result
            )
            
        except self.client.exceptions.ServiceException as e:
            raise LambdaClientError(f"Lambda service error: {e}")
        except self.client.exceptions.TooManyRequestsException as e:
            raise LambdaClientError(f"Lambda throttled: {e}")
        except json.JSONDecodeError as e:
            raise LambdaClientError(f"Invalid JSON in Lambda response: {e}")
        except Exception as e:
            raise LambdaClientError(f"Lambda invocation failed: {e}")
    
    def invoke_async(self, function_name: str, payload: Dict[str, Any]) -> bool:
        """
        Invoke a Lambda function asynchronously.
        
        Args:
            function_name: Name or ARN of Lambda function
            payload: Input payload for the function
            
        Returns:
            True if invocation was accepted
            
        Raises:
            LambdaClientError: If invocation fails
        """
        response = self.invoke(
            function_name=function_name,
            payload=payload,
            invocation_type='Event'
        )
        return response.status_code == 202
    
    def invoke_with_retry(
        self,
        function_name: str,
        payload: Dict[str, Any],
        max_retries: int = 3
    ) -> LambdaResponse:
        """
        Invoke Lambda function with automatic retry on failure.
        
        Args:
            function_name: Name or ARN of Lambda function
            payload: Input payload for the function
            max_retries: Maximum number of retry attempts
            
        Returns:
            LambdaResponse with function output
            
        Raises:
            LambdaClientError: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.invoke(function_name, payload)
                
                if response.is_success:
                    return response
                else:
                    last_error = f"Function error: {response.function_error}"
                    
            except LambdaClientError as e:
                last_error = str(e)
                
                # Don't retry on certain errors
                if 'throttled' not in str(e).lower():
                    raise
        
        raise LambdaClientError(
            f"Lambda invocation failed after {max_retries} attempts: {last_error}"
        )
    
    def get_function_info(self, function_name: str) -> Dict[str, Any]:
        """
        Get information about a Lambda function.
        
        Args:
            function_name: Name or ARN of Lambda function
            
        Returns:
            Function configuration
            
        Raises:
            LambdaClientError: If function not found
        """
        try:
            response = self.client.get_function(FunctionName=function_name)
            return response['Configuration']
        except self.client.exceptions.ResourceNotFoundException:
            raise LambdaClientError(f"Lambda function not found: {function_name}")
        except Exception as e:
            raise LambdaClientError(f"Failed to get function info: {e}")
    
    def test_function(self, function_name: str) -> bool:
        """
        Test if a Lambda function exists and is accessible.
        
        Args:
            function_name: Name or ARN of Lambda function
            
        Returns:
            True if function is accessible
        """
        try:
            self.get_function_info(function_name)
            return True
        except LambdaClientError:
            return False


class InventoryOptimizerClient:
    """Client for Inventory Optimizer Lambda function."""
    
    def __init__(self, lambda_client: LambdaClient, function_name: str):
        """
        Initialize Inventory Optimizer client.
        
        Args:
            lambda_client: LambdaClient instance
            function_name: Name of inventory optimizer Lambda function
        """
        self.lambda_client = lambda_client
        self.function_name = function_name
    
    def calculate_reorder_point(self, product_code: str, warehouse_code: str) -> Dict[str, Any]:
        """Calculate reorder point for a product."""
        payload = {
            'action': 'calculate_reorder_point',
            'product_code': product_code,
            'warehouse_code': warehouse_code
        }
        response = self.lambda_client.invoke(self.function_name, payload)
        return response.payload
    
    def identify_low_stock(self, warehouse_code: str, threshold: float) -> Dict[str, Any]:
        """Identify products with low stock."""
        payload = {
            'action': 'identify_low_stock',
            'warehouse_code': warehouse_code,
            'threshold': threshold
        }
        response = self.lambda_client.invoke(self.function_name, payload)
        return response.payload
    
    def forecast_demand(self, product_code: str, days: int) -> Dict[str, Any]:
        """Forecast demand for a product."""
        payload = {
            'action': 'forecast_demand',
            'product_code': product_code,
            'days': days
        }
        response = self.lambda_client.invoke(self.function_name, payload)
        return response.payload


class LogisticsOptimizerClient:
    """Client for Logistics Optimizer Lambda function."""
    
    def __init__(self, lambda_client: LambdaClient, function_name: str):
        """
        Initialize Logistics Optimizer client.
        
        Args:
            lambda_client: LambdaClient instance
            function_name: Name of logistics optimizer Lambda function
        """
        self.lambda_client = lambda_client
        self.function_name = function_name
    
    def optimize_delivery_route(self, order_ids: List[str], warehouse_code: str) -> Dict[str, Any]:
        """Optimize delivery route for orders."""
        payload = {
            'action': 'optimize_delivery_route',
            'order_ids': order_ids,
            'warehouse_code': warehouse_code
        }
        response = self.lambda_client.invoke(self.function_name, payload)
        return response.payload
    
    def check_fulfillment_status(self, order_id: str) -> Dict[str, Any]:
        """Check fulfillment status of an order."""
        payload = {
            'action': 'check_fulfillment_status',
            'order_id': order_id
        }
        response = self.lambda_client.invoke(self.function_name, payload)
        return response.payload


class SupplierAnalyzerClient:
    """Client for Supplier Analyzer Lambda function."""
    
    def __init__(self, lambda_client: LambdaClient, function_name: str):
        """
        Initialize Supplier Analyzer client.
        
        Args:
            lambda_client: LambdaClient instance
            function_name: Name of supplier analyzer Lambda function
        """
        self.lambda_client = lambda_client
        self.function_name = function_name
    
    def analyze_supplier_performance(self, supplier_code: str, days: int) -> Dict[str, Any]:
        """Analyze supplier performance."""
        payload = {
            'action': 'analyze_supplier_performance',
            'supplier_code': supplier_code,
            'days': days
        }
        response = self.lambda_client.invoke(self.function_name, payload)
        return response.payload
    
    def compare_supplier_costs(self, product_group: str, suppliers: List[str]) -> Dict[str, Any]:
        """Compare costs across suppliers."""
        payload = {
            'action': 'compare_supplier_costs',
            'product_group': product_group,
            'suppliers': suppliers
        }
        response = self.lambda_client.invoke(self.function_name, payload)
        return response.payload
