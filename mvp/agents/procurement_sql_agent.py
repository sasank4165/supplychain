"""
Procurement Specialist SQL Agent

Specialized SQL agent for Procurement Specialist persona with access to
purchase orders, supplier, and product data.
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


class ProcurementSQLAgent(SQLAgent):
    """
    SQL Agent for Procurement Specialist persona.
    
    Provides access to:
    - product: Product master data with supplier information
    - warehouse_product: Inventory levels for procurement planning
    - purchase_order_header: Purchase order information
    - purchase_order_line: Purchase order line items and receipt status
    
    Specialized for procurement and supplier queries such as:
    - Purchase order status and tracking
    - Supplier performance analysis
    - Cost analysis and variance
    - Pending receipts and deliveries
    - Supplier comparison and selection
    """
    
    def __init__(
        self,
        bedrock_client: BedrockClient,
        redshift_client: RedshiftClient,
        semantic_layer: SemanticLayer,
        logger=None
    ):
        """
        Initialize Procurement Specialist SQL agent.
        
        Args:
            bedrock_client: Bedrock client for SQL generation
            redshift_client: Redshift client for query execution
            semantic_layer: Semantic layer configured for Procurement Specialist
            logger: Optional logger
        """
        super().__init__(
            agent_name="ProcurementSpecialistSQLAgent",
            persona=Persona.PROCUREMENT_SPECIALIST,
            bedrock_client=bedrock_client,
            redshift_client=redshift_client,
            semantic_layer=semantic_layer,
            logger=logger
        )
    
    def _build_system_prompt(self, enriched_context) -> str:
        """
        Build system prompt with Procurement Specialist specific context.
        
        Args:
            enriched_context: Enriched context from semantic layer
            
        Returns:
            System prompt string
        """
        # Get base system prompt
        base_prompt = super()._build_system_prompt(enriched_context)
        
        # Add Procurement Specialist specific guidance
        procurement_guidance = """
PROCUREMENT SPECIALIST SPECIFIC GUIDANCE:

You are helping a Procurement Specialist who is responsible for:
- Managing purchase orders and supplier relationships
- Analyzing supplier performance and costs
- Identifying cost savings opportunities
- Tracking purchase order receipts and deliveries
- Optimizing procurement strategies

Common query patterns:
- "Show me pending purchase orders" -> Filter by status = 'Pending' or 'In Transit'
- "Which suppliers have the best performance?" -> Analyze on-time delivery, quality, costs
- "Show purchase orders from supplier X" -> Filter by supplier_code or supplier_name
- "What's the total spend with supplier Y?" -> SUM(line_total) grouped by supplier
- "Show overdue purchase orders" -> Check where expected_delivery_date < CURRENT_DATE AND status != 'Received'
- "Compare costs across suppliers" -> Group by supplier with cost aggregations

Key metrics:
- Pending POs: status IN ('Pending', 'In Transit', 'Ordered')
- Overdue POs: expected_delivery_date < CURRENT_DATE AND status NOT IN ('Received', 'Cancelled')
- Receipt rate: received_quantity / order_quantity
- On-time delivery: actual_delivery_date <= expected_delivery_date
- Cost variance: Compare unit_cost across suppliers for same products

Always consider:
- Join with product table to show product details
- Group by supplier for performance analysis
- Calculate totals and averages for cost analysis
- Filter by date ranges for trend analysis
- Show receipt status and quantities

Supplier analysis:
- Total spend: SUM(line_total) by supplier
- Order count: COUNT(DISTINCT purchase_order_number) by supplier
- Average order value: AVG(line_total) by supplier
- On-time rate: Compare actual vs expected delivery dates

"""
        
        return base_prompt + procurement_guidance
    
    def format_results(self, result, original_query: str) -> str:
        """
        Format results with Procurement Specialist context.
        
        Args:
            result: Query result from Redshift
            original_query: Original user query
            
        Returns:
            Formatted response string
        """
        if result.row_count == 0:
            return "No results found. Try adjusting your query criteria or date ranges."
        
        # Check if this is a procurement/supplier query
        query_lower = original_query.lower()
        is_procurement_query = any(term in query_lower for term in 
                                  ['purchase', 'supplier', 'po', 'procurement', 'cost', 'spend'])
        
        # Create formatted response
        summary = f"Found {result.row_count} result{'s' if result.row_count != 1 else ''}.\n\n"
        
        # Add context-specific summary
        if is_procurement_query and result.row_count > 0:
            data = result.to_dict_list()
            
            # Check for pending POs
            pending_count = sum(1 for row in data 
                              if 'status' in row and row.get('status') in ['Pending', 'Ordered', 'In Transit'])
            
            if pending_count > 0:
                summary += f"📋 {pending_count} purchase order(s) pending receipt.\n\n"
            
            # Check for partial receipts
            partial_count = sum(1 for row in data 
                              if 'received_quantity' in row and 'order_quantity' in row
                              and 0 < row.get('received_quantity', 0) < row.get('order_quantity', 0))
            
            if partial_count > 0:
                summary += f"📦 {partial_count} order line(s) partially received.\n\n"
            
            # Calculate total spend if cost data present
            if any('line_total' in row or 'unit_cost' in row for row in data):
                total_spend = sum(row.get('line_total', 0) for row in data if 'line_total' in row)
                if total_spend > 0:
                    summary += f"💰 Total value: ${total_spend:,.2f}\n\n"
        
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
        Format a single row with procurement/supplier context.
        
        Args:
            row_dict: Row as dictionary
            
        Returns:
            Formatted row string
        """
        # Prioritize important fields for procurement
        priority_fields = [
            'purchase_order_number', 'supplier_name', 'supplier_code',
            'order_date', 'expected_delivery_date', 'actual_delivery_date', 'status',
            'product_name', 'product_code',
            'order_quantity', 'received_quantity', 'receipt_status',
            'unit_cost', 'line_total', 'warehouse_code'
        ]
        
        # Format priority fields first
        parts = []
        for field in priority_fields:
            if field in row_dict:
                value = row_dict[field]
                
                # Add visual indicators for status
                if field == 'status':
                    if value in ['Pending', 'Ordered']:
                        parts.append(f"{field}: {value} 🔄")
                        continue
                    elif value == 'Received':
                        parts.append(f"{field}: {value} ✓")
                        continue
                    elif value in ['Delayed', 'Overdue']:
                        parts.append(f"{field}: {value} ⚠️")
                        continue
                
                # Add indicators for receipt status
                if field == 'received_quantity' and 'order_quantity' in row_dict:
                    order_qty = row_dict['order_quantity']
                    if value == 0:
                        parts.append(f"{field}: {value}/{order_qty} (not received)")
                        continue
                    elif value < order_qty:
                        parts.append(f"{field}: {value}/{order_qty} (partial)")
                        continue
                
                # Format currency fields
                if field in ['unit_cost', 'line_total'] and isinstance(value, (int, float)):
                    parts.append(f"{field}: ${value:,.2f}")
                    continue
                
                parts.append(f"{field}: {value}")
        
        # Add remaining fields
        for key, value in row_dict.items():
            if key not in priority_fields:
                # Format currency fields
                if key.endswith('_cost') or key.endswith('_total') or key.endswith('_price'):
                    if isinstance(value, (int, float)):
                        parts.append(f"{key}: ${value:,.2f}")
                        continue
                parts.append(f"{key}: {value}")
        
        return "- " + ", ".join(parts)
