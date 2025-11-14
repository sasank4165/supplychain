"""Configuration for Supply Chain Agentic AI Application"""
import os
from typing import Dict, List
from enum import Enum

class Persona(Enum):
    WAREHOUSE_MANAGER = "warehouse_manager"
    FIELD_ENGINEER = "field_engineer"
    PROCUREMENT_SPECIALIST = "procurement_specialist"

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
ATHENA_DATABASE = "aws-gpl-cog-sc-db"
ATHENA_CATALOG = "AwsDataCatalog"
ATHENA_OUTPUT_LOCATION = os.getenv("ATHENA_OUTPUT_LOCATION", "s3://your-athena-results-bucket/")

# DynamoDB Tables
DYNAMODB_SESSION_TABLE = "supply-chain-agent-sessions"
DYNAMODB_MEMORY_TABLE = "supply-chain-agent-memory"

# Lambda Functions
LAMBDA_SQL_EXECUTOR = "supply-chain-sql-executor"
LAMBDA_INVENTORY_OPTIMIZER = "supply-chain-inventory-optimizer"
LAMBDA_LOGISTICS_OPTIMIZER = "supply-chain-logistics-optimizer"
LAMBDA_SUPPLIER_ANALYZER = "supply-chain-supplier-analyzer"

# Schema Definitions
SCHEMA_TABLES = {
    "product": {
        "columns": ["product_code", "short_name", "product_description", "product_group", 
                   "supplier_code1", "stock_account", "standard_cost", "standard_rrp", 
                   "stock_item", "manufactured"],
        "description": "Product master data with details, costs, and supplier information"
    },
    "warehouse_product": {
        "columns": ["warehouse_code", "product_code", "physical_stock_su", "free_stock_su",
                   "qty_on_order_su", "minimum_stock_su", "maximum_stock_su", "allocated_stock_su",
                   "standard_cost", "last_cost", "lead_time_daysbigint"],
        "description": "Warehouse-specific inventory levels and stock management data"
    },
    "purchase_order_header": {
        "columns": ["purchase_order_prefix", "purchase_order_number", "supplier_code",
                   "order_raised_date", "order_status", "invoice_status", "currency_code"],
        "description": "Purchase order header information with supplier and status"
    },
    "purchase_order_line": {
        "columns": ["purchase_order_prefix", "purchase_order_numberbigint", "purchase_order_linebigint",
                   "product_code", "qty_oudouble", "unit_price_oudouble", "line_valuedouble",
                   "received_qty_oudouble", "order_status"],
        "description": "Purchase order line items with quantities, prices, and receipt status"
    },
    "sales_order_header": {
        "columns": ["sales_order_prefix", "sales_order_number", "customer_code",
                   "order_raised_date", "pref_del_date", "warehouse_code", "order_status"],
        "description": "Sales order header with customer and delivery information"
    },
    "sales_order_line": {
        "columns": ["sales_order_prefix", "sales_order_number", "sales_order_line",
                   "product_code", "qty_seludouble", "allocated_qty_su", "picked_qty_su",
                   "despatched_qty_su", "order_line_status"],
        "description": "Sales order line items with quantities and fulfillment status"
    }
}

# Persona-specific table access
PERSONA_TABLE_ACCESS: Dict[Persona, List[str]] = {
    Persona.WAREHOUSE_MANAGER: ["product", "warehouse_product", "sales_order_header", "sales_order_line"],
    Persona.FIELD_ENGINEER: ["product", "warehouse_product", "sales_order_header", "sales_order_line"],
    Persona.PROCUREMENT_SPECIALIST: ["product", "purchase_order_header", "purchase_order_line", "warehouse_product"]
}
