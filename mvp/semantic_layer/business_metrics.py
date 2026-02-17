"""
Business Metrics Definitions

Defines business metrics and their SQL patterns for each persona.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class Persona(Enum):
    """User personas."""
    WAREHOUSE_MANAGER = "Warehouse Manager"
    FIELD_ENGINEER = "Field Engineer"
    PROCUREMENT_SPECIALIST = "Procurement Specialist"


@dataclass
class MetricDefinition:
    """Definition of a business metric."""
    name: str
    description: str
    sql_pattern: str
    tables: List[str]
    personas: List[Persona]
    example_query: Optional[str] = None
    parameters: Optional[Dict[str, str]] = None


class BusinessMetrics:
    """Business metrics definitions for all personas."""
    
    # Warehouse Manager Metrics
    WAREHOUSE_MANAGER_METRICS = {
        "low_stock": MetricDefinition(
            name="low_stock",
            description="Products with current stock below minimum stock level",
            sql_pattern="current_stock < minimum_stock",
            tables=["warehouse_product"],
            personas=[Persona.WAREHOUSE_MANAGER],
            example_query="Show me products with low stock",
            parameters={"threshold_column": "minimum_stock"}
        ),
        "stockout_risk": MetricDefinition(
            name="stockout_risk",
            description="Products at risk of stockout based on current stock and reorder point",
            sql_pattern="current_stock <= reorder_point",
            tables=["warehouse_product"],
            personas=[Persona.WAREHOUSE_MANAGER],
            example_query="Which products are at risk of stockout?",
            parameters={"risk_threshold": "reorder_point"}
        ),
        "reorder_needed": MetricDefinition(
            name="reorder_needed",
            description="Products that need to be reordered",
            sql_pattern="current_stock <= reorder_point AND current_stock > 0",
            tables=["warehouse_product"],
            personas=[Persona.WAREHOUSE_MANAGER],
            example_query="What products need to be reordered?",
            parameters={}
        ),
        "out_of_stock": MetricDefinition(
            name="out_of_stock",
            description="Products with zero current stock",
            sql_pattern="current_stock = 0",
            tables=["warehouse_product"],
            personas=[Persona.WAREHOUSE_MANAGER],
            example_query="Show me out of stock products",
            parameters={}
        ),
        "overstock": MetricDefinition(
            name="overstock",
            description="Products with stock exceeding maximum stock level",
            sql_pattern="current_stock > maximum_stock",
            tables=["warehouse_product"],
            personas=[Persona.WAREHOUSE_MANAGER],
            example_query="Which products are overstocked?",
            parameters={}
        ),
        "stock_turnover": MetricDefinition(
            name="stock_turnover",
            description="Products with high or low stock turnover",
            sql_pattern="(fulfilled_quantity / NULLIF(current_stock, 0)) as turnover_ratio",
            tables=["warehouse_product", "sales_order_line"],
            personas=[Persona.WAREHOUSE_MANAGER],
            example_query="Show me stock turnover rates",
            parameters={"period_days": "30"}
        ),
        "inventory_value": MetricDefinition(
            name="inventory_value",
            description="Total value of inventory by warehouse or product",
            sql_pattern="SUM(current_stock * unit_cost) as inventory_value",
            tables=["warehouse_product", "product"],
            personas=[Persona.WAREHOUSE_MANAGER],
            example_query="What is the total inventory value?",
            parameters={}
        )
    }
    
    # Field Engineer Metrics
    FIELD_ENGINEER_METRICS = {
        "overdue_orders": MetricDefinition(
            name="overdue_orders",
            description="Orders past their delivery date that are not delivered",
            sql_pattern="delivery_date < CURRENT_DATE AND status != 'Delivered'",
            tables=["sales_order_header"],
            personas=[Persona.FIELD_ENGINEER],
            example_query="Show me overdue orders",
            parameters={}
        ),
        "delivery_today": MetricDefinition(
            name="delivery_today",
            description="Orders scheduled for delivery today",
            sql_pattern="delivery_date = CURRENT_DATE AND status IN ('Pending', 'In Transit')",
            tables=["sales_order_header"],
            personas=[Persona.FIELD_ENGINEER],
            example_query="What orders need to be delivered today?",
            parameters={}
        ),
        "delayed_shipments": MetricDefinition(
            name="delayed_shipments",
            description="Orders with delivery date in the past but not yet delivered",
            sql_pattern="delivery_date < CURRENT_DATE AND status IN ('Pending', 'In Transit')",
            tables=["sales_order_header"],
            personas=[Persona.FIELD_ENGINEER],
            example_query="Show me delayed shipments",
            parameters={}
        ),
        "pending_orders": MetricDefinition(
            name="pending_orders",
            description="Orders with pending status",
            sql_pattern="status = 'Pending'",
            tables=["sales_order_header"],
            personas=[Persona.FIELD_ENGINEER],
            example_query="What orders are pending?",
            parameters={}
        ),
        "in_transit_orders": MetricDefinition(
            name="in_transit_orders",
            description="Orders currently in transit",
            sql_pattern="status = 'In Transit'",
            tables=["sales_order_header"],
            personas=[Persona.FIELD_ENGINEER],
            example_query="Show me orders in transit",
            parameters={}
        ),
        "unfulfilled_lines": MetricDefinition(
            name="unfulfilled_lines",
            description="Order lines with unfulfilled quantities",
            sql_pattern="fulfilled_quantity < order_quantity",
            tables=["sales_order_line"],
            personas=[Persona.FIELD_ENGINEER],
            example_query="Which order lines are not fully fulfilled?",
            parameters={}
        ),
        "delivery_by_area": MetricDefinition(
            name="delivery_by_area",
            description="Orders grouped by delivery area",
            sql_pattern="GROUP BY delivery_area",
            tables=["sales_order_header"],
            personas=[Persona.FIELD_ENGINEER],
            example_query="Show me orders by delivery area",
            parameters={}
        ),
        "orders_by_warehouse": MetricDefinition(
            name="orders_by_warehouse",
            description="Orders grouped by warehouse",
            sql_pattern="GROUP BY warehouse_code",
            tables=["sales_order_header"],
            personas=[Persona.FIELD_ENGINEER],
            example_query="Show me orders by warehouse",
            parameters={}
        )
    }
    
    # Procurement Specialist Metrics
    PROCUREMENT_SPECIALIST_METRICS = {
        "top_suppliers": MetricDefinition(
            name="top_suppliers",
            description="Suppliers with highest order volume or value",
            sql_pattern="GROUP BY supplier_code ORDER BY SUM(order_quantity) DESC",
            tables=["purchase_order_header", "purchase_order_line"],
            personas=[Persona.PROCUREMENT_SPECIALIST],
            example_query="Who are our top suppliers?",
            parameters={"limit": "10"}
        ),
        "cost_variance": MetricDefinition(
            name="cost_variance",
            description="Variance between expected and actual costs",
            sql_pattern="(unit_cost - expected_cost) / NULLIF(expected_cost, 0) as cost_variance",
            tables=["purchase_order_line", "product"],
            personas=[Persona.PROCUREMENT_SPECIALIST],
            example_query="Show me cost variances",
            parameters={}
        ),
        "pending_pos": MetricDefinition(
            name="pending_pos",
            description="Purchase orders with pending status",
            sql_pattern="status = 'Pending'",
            tables=["purchase_order_header"],
            personas=[Persona.PROCUREMENT_SPECIALIST],
            example_query="What purchase orders are pending?",
            parameters={}
        ),
        "late_deliveries": MetricDefinition(
            name="late_deliveries",
            description="Purchase orders delivered after expected date",
            sql_pattern="actual_delivery_date > expected_delivery_date",
            tables=["purchase_order_header"],
            personas=[Persona.PROCUREMENT_SPECIALIST],
            example_query="Show me late deliveries from suppliers",
            parameters={}
        ),
        "supplier_performance": MetricDefinition(
            name="supplier_performance",
            description="Supplier on-time delivery rate",
            sql_pattern="SUM(CASE WHEN actual_delivery_date <= expected_delivery_date THEN 1 ELSE 0 END) / COUNT(*) as on_time_rate",
            tables=["purchase_order_header"],
            personas=[Persona.PROCUREMENT_SPECIALIST],
            example_query="What is the supplier performance?",
            parameters={"period_days": "90"}
        ),
        "incomplete_receipts": MetricDefinition(
            name="incomplete_receipts",
            description="Purchase order lines with incomplete receipts",
            sql_pattern="received_quantity < order_quantity",
            tables=["purchase_order_line"],
            personas=[Persona.PROCUREMENT_SPECIALIST],
            example_query="Which PO lines have incomplete receipts?",
            parameters={}
        ),
        "purchase_by_product_group": MetricDefinition(
            name="purchase_by_product_group",
            description="Purchase orders grouped by product group",
            sql_pattern="GROUP BY product_group",
            tables=["purchase_order_line", "product"],
            personas=[Persona.PROCUREMENT_SPECIALIST],
            example_query="Show me purchases by product group",
            parameters={}
        ),
        "supplier_cost_comparison": MetricDefinition(
            name="supplier_cost_comparison",
            description="Compare costs across suppliers for same products",
            sql_pattern="GROUP BY supplier_code, product_code ORDER BY unit_cost",
            tables=["product", "purchase_order_line"],
            personas=[Persona.PROCUREMENT_SPECIALIST],
            example_query="Compare supplier costs for products",
            parameters={}
        )
    }
    
    @classmethod
    def get_metrics_for_persona(cls, persona: Persona) -> Dict[str, MetricDefinition]:
        """
        Get all metrics for a specific persona.
        
        Args:
            persona: The persona to get metrics for
            
        Returns:
            Dictionary of metric name to MetricDefinition
        """
        if persona == Persona.WAREHOUSE_MANAGER:
            return cls.WAREHOUSE_MANAGER_METRICS
        elif persona == Persona.FIELD_ENGINEER:
            return cls.FIELD_ENGINEER_METRICS
        elif persona == Persona.PROCUREMENT_SPECIALIST:
            return cls.PROCUREMENT_SPECIALIST_METRICS
        else:
            return {}
    
    @classmethod
    def get_all_metrics(cls) -> Dict[str, MetricDefinition]:
        """
        Get all metrics across all personas.
        
        Returns:
            Dictionary of metric name to MetricDefinition
        """
        all_metrics = {}
        all_metrics.update(cls.WAREHOUSE_MANAGER_METRICS)
        all_metrics.update(cls.FIELD_ENGINEER_METRICS)
        all_metrics.update(cls.PROCUREMENT_SPECIALIST_METRICS)
        return all_metrics
    
    @classmethod
    def find_metric_by_keywords(cls, keywords: List[str], persona: Optional[Persona] = None) -> List[MetricDefinition]:
        """
        Find metrics matching keywords.
        
        Args:
            keywords: List of keywords to search for
            persona: Optional persona to filter by
            
        Returns:
            List of matching MetricDefinitions
        """
        if persona:
            metrics = cls.get_metrics_for_persona(persona)
        else:
            metrics = cls.get_all_metrics()
        
        matching_metrics = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for metric in metrics.values():
            # Check if any keyword matches metric name or description
            metric_text = f"{metric.name} {metric.description}".lower()
            if any(kw in metric_text for kw in keywords_lower):
                matching_metrics.append(metric)
        
        return matching_metrics
    
    @classmethod
    def get_metric(cls, metric_name: str) -> Optional[MetricDefinition]:
        """
        Get a specific metric by name.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            MetricDefinition or None if not found
        """
        all_metrics = cls.get_all_metrics()
        return all_metrics.get(metric_name)
    
    @classmethod
    def get_common_business_terms(cls) -> Dict[str, str]:
        """
        Get common business terms and their SQL equivalents.
        
        Returns:
            Dictionary mapping business terms to SQL patterns
        """
        return {
            "low stock": "current_stock < minimum_stock",
            "out of stock": "current_stock = 0",
            "overstock": "current_stock > maximum_stock",
            "overdue": "delivery_date < CURRENT_DATE AND status != 'Delivered'",
            "today": "CURRENT_DATE",
            "this week": "DATE_TRUNC('week', CURRENT_DATE)",
            "this month": "DATE_TRUNC('month', CURRENT_DATE)",
            "last 30 days": "CURRENT_DATE - INTERVAL '30 days'",
            "last 90 days": "CURRENT_DATE - INTERVAL '90 days'",
            "pending": "status = 'Pending'",
            "in transit": "status = 'In Transit'",
            "delivered": "status = 'Delivered'",
            "late": "actual_delivery_date > expected_delivery_date",
            "on time": "actual_delivery_date <= expected_delivery_date",
            "unfulfilled": "fulfilled_quantity < order_quantity",
            "incomplete": "received_quantity < order_quantity"
        }
