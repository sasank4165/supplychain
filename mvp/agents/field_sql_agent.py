"""
Field Engineer SQL Agent

Specialized SQL agent for Field Engineer persona with access to
sales orders, delivery, and product data.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.sql_agent import SQLAgent, ConversationContext
from aws.bedrock_client import BedrockClient
from aws.redshift_client import RedshiftClient
from semantic_layer.semantic_layer import SemanticLayer
from semantic_layer.business_metrics import Persona


class FieldEngineerSQLAgent(SQLAgent):
    """
    SQL Agent for Field Engineer persona.
    
    Provides access to:
    - product: Product master data
    - warehouse_product: Inventory availability
    - sales_order_header: Sales order and delivery information
    - sales_order_line: Order line items and fulfillment status
    
    Specialized for logistics and delivery queries such as:
    - Order status and tracking
    - Delivery schedules and routes
    - Overdue and delayed orders
    - Order fulfillment status
    - Warehouse capacity and availability
    """
    
    def __init__(
        self,
        bedrock_client: BedrockClient,
        redshift_client: RedshiftClient,
        semantic_layer: SemanticLayer,
        logger=None
    ):
        """
        Initialize Field Engineer SQL agent.
        
        Args:
            bedrock_client: Bedrock client for SQL generation
            redshift_client: Redshift client for query execution
            semantic_layer: Semantic layer configured for Field Engineer
            logger: Optional logger
        """
        super().__init__(
            agent_name="FieldEngineerSQLAgent",
            persona=Persona.FIELD_ENGINEER,
            bedrock_client=bedrock_client,
            redshift_client=redshift_client,
            semantic_layer=semantic_layer,
            logger=logger
        )
    
    def _build_system_prompt(self, enriched_context) -> str:
        """
        Build system prompt with Field Engineer specific context.
        
        Args:
            enriched_context: Enriched context from semantic layer
            
        Returns:
            System prompt string
        """
        # Get base system prompt
        base_prompt = super()._build_system_prompt(enriched_context)
        
        # Add Field Engineer specific guidance
        field_guidance = """
FIELD ENGINEER SPECIFIC GUIDANCE:

You are helping a Field Engineer who is responsible for:
- Managing order deliveries and logistics
- Tracking order fulfillment status
- Identifying delayed or overdue orders
- Planning delivery routes and schedules
- Coordinating with warehouses for order fulfillment

Common query patterns:
- "Show me today's deliveries" -> Filter by delivery_date = CURRENT_DATE
- "Which orders are overdue?" -> Check where delivery_date < CURRENT_DATE AND status != 'Delivered'
- "Show orders for delivery area X" -> Filter by delivery_area
- "What's the status of order Y?" -> Query sales_order_header with order number
- "Show unfulfilled orders" -> Check where fulfilled_quantity < order_quantity
- "Which orders are delayed?" -> Check delivery_date vs order_date with status

Key metrics:
- Overdue orders: delivery_date < CURRENT_DATE AND status NOT IN ('Delivered', 'Cancelled')
- Fulfillment rate: fulfilled_quantity / order_quantity
- On-time delivery: status = 'Delivered' AND actual_delivery <= delivery_date
- Pending orders: status IN ('Pending', 'Processing', 'In Transit')

Always consider:
- Filter by delivery_date for time-based queries
- Join with product table to show product details
- Group by delivery_area for route planning
- Show order status and fulfillment information
- Include customer information when relevant

Date handling:
- Use CURRENT_DATE for today's date
- Use date comparisons for overdue/upcoming deliveries
- Consider status field in conjunction with dates

"""
        
        return base_prompt + field_guidance
    
    def format_results(self, result, original_query: str) -> str:
        """
        Format results with Field Engineer context.
        
        Args:
            result: Query result from Redshift
            original_query: Original user query
            
        Returns:
            Formatted response string
        """
        if result.row_count == 0:
            return "No results found. All orders may be on track, or try adjusting your query criteria."
        
        # Check if this is a delivery/order query
        query_lower = original_query.lower()
        is_delivery_query = any(term in query_lower for term in 
                               ['delivery', 'order', 'overdue', 'delayed', 'fulfillment'])
        
        # Create formatted response
        summary = f"Found {result.row_count} result{'s' if result.row_count != 1 else ''}.\n\n"
        
        # Add context-specific summary
        if is_delivery_query and result.row_count > 0:
            data = result.to_dict_list()
            
            # Check for overdue orders
            overdue_count = sum(1 for row in data 
                              if 'status' in row and row.get('status') not in ['Delivered', 'Cancelled'])
            
            if overdue_count > 0:
                summary += f"⚠️  {overdue_count} order(s) require attention.\n\n"
            
            # Check for unfulfilled items
            unfulfilled_count = sum(1 for row in data 
                                   if 'fulfilled_quantity' in row and 'order_quantity' in row
                                   and row.get('fulfilled_quantity', 0) < row.get('order_quantity', 0))
            
            if unfulfilled_count > 0:
                summary += f"📦 {unfulfilled_count} order line(s) partially fulfilled.\n\n"
        
        # Format the data
        if result.row_count <= 10:
            summary += "Results:\n"
            for row_dict in result.to_dict_list():
                summary += self._format_row(row_dict) + "\n"
        else:
            summary += f"Showing first 10 of {result.row_count} results:\n"
            for row_dict in result.to_dict_list()[:10]:
                summary += self._format_row(row_dict) + "\n"
            summary += f"\n... and {result.row_count - 10} more rows."
        
        return summary
    
    def _format_row(self, row_dict: dict) -> str:
        """
        Format a single row with delivery/order context.
        
        Args:
            row_dict: Row as dictionary
            
        Returns:
            Formatted row string
        """
        # Prioritize important fields for delivery/orders
        priority_fields = [
            'sales_order_number', 'order_date', 'delivery_date', 'status',
            'customer_name', 'delivery_area', 'delivery_address',
            'product_name', 'order_quantity', 'fulfilled_quantity', 'fulfillment_status',
            'warehouse_code'
        ]
        
        # Format priority fields first
        parts = []
        for field in priority_fields:
            if field in row_dict:
                value = row_dict[field]
                
                # Add visual indicators for status
                if field == 'status':
                    if value in ['Pending', 'Processing']:
                        parts.append(f"{field}: {value} 🔄")
                        continue
                    elif value == 'Delivered':
                        parts.append(f"{field}: {value} ✓")
                        continue
                    elif value in ['Delayed', 'Overdue']:
                        parts.append(f"{field}: {value} ⚠️")
                        continue
                
                # Add indicators for fulfillment
                if field == 'fulfilled_quantity' and 'order_quantity' in row_dict:
                    order_qty = row_dict['order_quantity']
                    if value < order_qty:
                        parts.append(f"{field}: {value}/{order_qty} (partial)")
                        continue
                
                parts.append(f"{field}: {value}")
        
        # Add remaining fields
        for key, value in row_dict.items():
            if key not in priority_fields:
                parts.append(f"{key}: {value}")
        
        return "- " + ", ".join(parts)
