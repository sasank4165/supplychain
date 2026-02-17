"""
Warehouse Manager SQL Agent

Specialized SQL agent for Warehouse Manager persona with access to
inventory and sales order data.
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


class WarehouseSQLAgent(SQLAgent):
    """
    SQL Agent for Warehouse Manager persona.
    
    Provides access to:
    - product: Product master data
    - warehouse_product: Inventory levels and stock information
    - sales_order_header: Sales order information
    - sales_order_line: Sales order line items
    
    Specialized for inventory management queries such as:
    - Stock levels and availability
    - Low stock identification
    - Reorder point analysis
    - Product movement and turnover
    """
    
    def __init__(
        self,
        bedrock_client: BedrockClient,
        redshift_client: RedshiftClient,
        semantic_layer: SemanticLayer,
        logger=None
    ):
        """
        Initialize Warehouse Manager SQL agent.
        
        Args:
            bedrock_client: Bedrock client for SQL generation
            redshift_client: Redshift client for query execution
            semantic_layer: Semantic layer configured for Warehouse Manager
            logger: Optional logger
        """
        super().__init__(
            agent_name="WarehouseManagerSQLAgent",
            persona=Persona.WAREHOUSE_MANAGER,
            bedrock_client=bedrock_client,
            redshift_client=redshift_client,
            semantic_layer=semantic_layer,
            logger=logger
        )
    
    def _build_system_prompt(self, enriched_context) -> str:
        """
        Build system prompt with Warehouse Manager specific context.
        
        Args:
            enriched_context: Enriched context from semantic layer
            
        Returns:
            System prompt string
        """
        # Get base system prompt
        base_prompt = super()._build_system_prompt(enriched_context)
        
        # Add Warehouse Manager specific guidance
        warehouse_guidance = """
WAREHOUSE MANAGER SPECIFIC GUIDANCE:

You are helping a Warehouse Manager who is responsible for:
- Monitoring inventory levels across warehouses
- Identifying low stock and stockout risks
- Managing reorder points and safety stock
- Tracking product movement and turnover
- Analyzing sales order fulfillment

Common query patterns:
- "Show me low stock items" -> Check where current_stock < minimum_stock or current_stock < reorder_point
- "Which products need reordering?" -> Check reorder point thresholds
- "What's the stock level for product X?" -> Query warehouse_product table
- "Show unfulfilled orders" -> Check sales orders where fulfilled_quantity < order_quantity
- "Which warehouses have product X?" -> Query warehouse_product with product filter

Key metrics:
- Low stock: current_stock < minimum_stock
- Stockout risk: current_stock < reorder_point
- Stock availability: current_stock > 0
- Fulfillment rate: fulfilled_quantity / order_quantity

Always consider:
- Filter by warehouse_code when user mentions a specific warehouse
- Join with product table to show product names and details
- Use appropriate date filters for time-based queries
- Show stock levels in context (current vs minimum vs maximum)

"""
        
        return base_prompt + warehouse_guidance
    
    def format_results(self, result, original_query: str) -> str:
        """
        Format results with Warehouse Manager context.
        
        Args:
            result: Query result from Redshift
            original_query: Original user query
            
        Returns:
            Formatted response string
        """
        if result.row_count == 0:
            return "No results found. All inventory levels may be adequate, or try adjusting your query criteria."
        
        # Check if this is an inventory-related query
        query_lower = original_query.lower()
        is_inventory_query = any(term in query_lower for term in 
                                ['stock', 'inventory', 'warehouse', 'reorder'])
        
        # Create formatted response
        summary = f"Found {result.row_count} result{'s' if result.row_count != 1 else ''}.\n\n"
        
        # Add context-specific summary
        if is_inventory_query and result.row_count > 0:
            # Check for low stock indicators
            data = result.to_dict_list()
            low_stock_count = sum(1 for row in data 
                                 if 'current_stock' in row and 'minimum_stock' in row 
                                 and row.get('current_stock', float('inf')) < row.get('minimum_stock', 0))
            
            if low_stock_count > 0:
                summary += f"⚠️  {low_stock_count} item(s) below minimum stock level.\n\n"
        
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
        Format a single row with inventory context.
        
        Args:
            row_dict: Row as dictionary
            
        Returns:
            Formatted row string
        """
        # Prioritize important fields for inventory
        priority_fields = [
            'product_code', 'product_name', 'warehouse_code',
            'current_stock', 'minimum_stock', 'maximum_stock', 'reorder_point',
            'order_quantity', 'fulfilled_quantity', 'fulfillment_status'
        ]
        
        # Format priority fields first
        parts = []
        for field in priority_fields:
            if field in row_dict:
                value = row_dict[field]
                
                # Add visual indicators for stock levels
                if field == 'current_stock' and 'minimum_stock' in row_dict:
                    min_stock = row_dict['minimum_stock']
                    if value < min_stock:
                        parts.append(f"{field}: {value} ⚠️ (below minimum: {min_stock})")
                        continue
                
                parts.append(f"{field}: {value}")
        
        # Add remaining fields
        for key, value in row_dict.items():
            if key not in priority_fields:
                parts.append(f"{key}: {value}")
        
        return "- " + ", ".join(parts)
