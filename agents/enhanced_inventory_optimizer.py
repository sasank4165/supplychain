"""Enhanced Inventory Optimizer Agent using Bedrock Agent Core patterns"""
import boto3
import json
import logging
from typing import Dict, Any
from .enhanced_base_agent import EnhancedBaseAgent, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class EnhancedInventoryOptimizerAgent(EnhancedBaseAgent):
    """
    Enhanced inventory optimization agent with improved tool handling
    
    Uses Amazon Bedrock Agent Core patterns for:
    - Structured tool registration
    - Better error handling
    - Conversation memory
    - Observability
    """
    
    def __init__(self, region: str = "us-east-1"):
        super().__init__(
            agent_name="enhanced_inventory_optimizer",
            persona="warehouse_manager",
            region=region,
            max_iterations=10
        )
        self.lambda_client = boto3.client('lambda', region_name=region)
    
    def _register_tools(self):
        """Register inventory optimization tools"""
        
        # Tool 1: Calculate reorder points
        self.tool_registry.register_tool(
            name="calculate_reorder_points",
            description="Calculate optimal reorder points for products based on historical data, lead times, and demand patterns. Use this when asked about reorder levels, safety stock, or when to reorder products.",
            input_schema={
                "type": "object",
                "properties": {
                    "warehouse_code": {
                        "type": "string",
                        "description": "Warehouse code to analyze (e.g., WH01, WH02)"
                    },
                    "product_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of specific product codes to analyze. If not provided, analyzes all products."
                    }
                },
                "required": ["warehouse_code"]
            },
            handler=self._handle_calculate_reorder_points
        )
        
        # Tool 2: Forecast demand
        self.tool_registry.register_tool(
            name="forecast_demand",
            description="Forecast product demand for future periods based on historical sales data. Use this for demand planning, capacity planning, or predicting future needs.",
            input_schema={
                "type": "object",
                "properties": {
                    "product_code": {
                        "type": "string",
                        "description": "Product code to forecast"
                    },
                    "warehouse_code": {
                        "type": "string",
                        "description": "Warehouse code"
                    },
                    "forecast_days": {
                        "type": "integer",
                        "description": "Number of days to forecast (default 30)",
                        "default": 30
                    }
                },
                "required": ["product_code", "warehouse_code"]
            },
            handler=self._handle_forecast_demand
        )
        
        # Tool 3: Identify stockout risks
        self.tool_registry.register_tool(
            name="identify_stockout_risks",
            description="Identify products at risk of stockout based on current inventory levels and demand patterns. Use this to prevent stockouts and ensure product availability.",
            input_schema={
                "type": "object",
                "properties": {
                    "warehouse_code": {
                        "type": "string",
                        "description": "Warehouse code to analyze"
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days to look ahead for risk assessment (default 7)",
                        "default": 7
                    }
                },
                "required": ["warehouse_code"]
            },
            handler=self._handle_identify_stockout_risks
        )
        
        # Tool 4: Optimize stock levels
        self.tool_registry.register_tool(
            name="optimize_stock_levels",
            description="Suggest optimal stock levels (min/max) to minimize costs while maintaining target service levels. Use this for inventory optimization and cost reduction.",
            input_schema={
                "type": "object",
                "properties": {
                    "warehouse_code": {
                        "type": "string",
                        "description": "Warehouse code"
                    },
                    "target_service_level": {
                        "type": "number",
                        "description": "Target service level percentage (default 95)",
                        "default": 95.0
                    }
                },
                "required": ["warehouse_code"]
            },
            handler=self._handle_optimize_stock_levels
        )
    
    def get_system_prompt(self) -> str:
        """Get system prompt for inventory optimizer"""
        return """You are an expert inventory optimization assistant for warehouse management.

Your role is to help warehouse managers:
- Optimize inventory levels
- Prevent stockouts
- Reduce carrying costs
- Forecast demand
- Calculate reorder points

You have access to tools that analyze inventory data and provide recommendations.

When responding:
1. Use tools to get accurate data
2. Provide clear, actionable recommendations
3. Explain the reasoning behind suggestions
4. Include relevant metrics and numbers
5. Prioritize preventing stockouts while minimizing costs

Always be specific with warehouse codes and product codes when using tools."""
    
    def _handle_calculate_reorder_points(self, input_data: Dict) -> Dict[str, Any]:
        """Handle reorder point calculation"""
        from config import LAMBDA_INVENTORY_OPTIMIZER
        
        try:
            # Extract context if provided
            context = input_data.pop('_context', None)
            
            # Validate access if context provided
            if context and 'groups' in context:
                # Access control already handled at orchestrator level
                pass
            
            payload = {
                "tool_name": "calculate_reorder_points",
                "input": input_data
            }
            
            response = self.lambda_client.invoke(
                FunctionName=LAMBDA_INVENTORY_OPTIMIZER,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if 'error' in result:
                raise Exception(result['error'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating reorder points: {str(e)}")
            raise
    
    def _handle_forecast_demand(self, input_data: Dict) -> Dict[str, Any]:
        """Handle demand forecasting"""
        from config import LAMBDA_INVENTORY_OPTIMIZER
        
        try:
            context = input_data.pop('_context', None)
            
            payload = {
                "tool_name": "forecast_demand",
                "input": input_data
            }
            
            response = self.lambda_client.invoke(
                FunctionName=LAMBDA_INVENTORY_OPTIMIZER,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if 'error' in result:
                raise Exception(result['error'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error forecasting demand: {str(e)}")
            raise
    
    def _handle_identify_stockout_risks(self, input_data: Dict) -> Dict[str, Any]:
        """Handle stockout risk identification"""
        from config import LAMBDA_INVENTORY_OPTIMIZER
        
        try:
            context = input_data.pop('_context', None)
            
            payload = {
                "tool_name": "identify_stockout_risks",
                "input": input_data
            }
            
            response = self.lambda_client.invoke(
                FunctionName=LAMBDA_INVENTORY_OPTIMIZER,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if 'error' in result:
                raise Exception(result['error'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error identifying stockout risks: {str(e)}")
            raise
    
    def _handle_optimize_stock_levels(self, input_data: Dict) -> Dict[str, Any]:
        """Handle stock level optimization"""
        from config import LAMBDA_INVENTORY_OPTIMIZER
        
        try:
            context = input_data.pop('_context', None)
            
            payload = {
                "tool_name": "optimize_stock_levels",
                "input": input_data
            }
            
            response = self.lambda_client.invoke(
                FunctionName=LAMBDA_INVENTORY_OPTIMIZER,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if 'error' in result:
                raise Exception(result['error'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing stock levels: {str(e)}")
            raise
