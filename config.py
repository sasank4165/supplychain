"""Configuration for Supply Chain Agentic AI Application

This module provides configuration values loaded from environment variables.
All AWS resource names and sensitive values should be provided via environment
variables or AWS Secrets Manager/Parameter Store.
"""
import os
from typing import Dict, List, Optional
from enum import Enum


class Persona(Enum):
    WAREHOUSE_MANAGER = "warehouse_manager"
    FIELD_ENGINEER = "field_engineer"
    PROCUREMENT_SPECIALIST = "procurement_specialist"


class ConfigurationError(Exception):
    """Raised when required configuration is missing"""
    pass


def get_required_env(key: str, description: str = "") -> str:
    """Get required environment variable or raise error
    
    Args:
        key: Environment variable name
        description: Description of the variable for error message
        
    Returns:
        Environment variable value
        
    Raises:
        ConfigurationError: If variable is not set
    """
    value = os.getenv(key)
    if not value:
        desc = f" ({description})" if description else ""
        raise ConfigurationError(
            f"Required environment variable not set: {key}{desc}\n"
            f"Please set this variable before running the application."
        )
    return value


def get_env(key: str, default: str = "", description: str = "") -> str:
    """Get environment variable with default
    
    Args:
        key: Environment variable name
        default: Default value if not set
        description: Description for documentation
        
    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


# AWS Configuration
AWS_REGION = get_env("AWS_REGION", "us-east-1", "AWS region for all services")
BEDROCK_MODEL_ID = get_env(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "Amazon Bedrock model ID"
)

# Athena Configuration
ATHENA_DATABASE = get_env(
    "ATHENA_DATABASE",
    "",
    "Athena database name"
)
ATHENA_CATALOG = get_env("ATHENA_CATALOG", "AwsDataCatalog", "Athena data catalog")
ATHENA_OUTPUT_LOCATION = get_env(
    "ATHENA_OUTPUT_LOCATION",
    "",
    "S3 location for Athena query results"
)

# DynamoDB Tables
DYNAMODB_SESSION_TABLE = get_env(
    "DYNAMODB_SESSION_TABLE",
    "",
    "DynamoDB table for session storage"
)
DYNAMODB_MEMORY_TABLE = get_env(
    "DYNAMODB_MEMORY_TABLE",
    "",
    "DynamoDB table for conversation memory"
)
DYNAMODB_CONVERSATION_TABLE = get_env(
    "DYNAMODB_CONVERSATION_TABLE",
    "",
    "DynamoDB table for conversation history with context management"
)

# Lambda Functions
LAMBDA_SQL_EXECUTOR = get_env(
    "LAMBDA_SQL_EXECUTOR",
    "",
    "Lambda function name for SQL execution"
)
LAMBDA_INVENTORY_OPTIMIZER = get_env(
    "LAMBDA_INVENTORY_OPTIMIZER",
    "",
    "Lambda function name for inventory optimization"
)
LAMBDA_LOGISTICS_OPTIMIZER = get_env(
    "LAMBDA_LOGISTICS_OPTIMIZER",
    "",
    "Lambda function name for logistics optimization"
)
LAMBDA_SUPPLIER_ANALYZER = get_env(
    "LAMBDA_SUPPLIER_ANALYZER",
    "",
    "Lambda function name for supplier analysis"
)

# Cognito Configuration (for authentication)
USER_POOL_ID = get_env("USER_POOL_ID", "", "Cognito User Pool ID")
USER_POOL_CLIENT_ID = get_env("USER_POOL_CLIENT_ID", "", "Cognito User Pool Client ID")

# Application Configuration
SC_AGENT_PREFIX = get_env(
    "SC_AGENT_PREFIX",
    "sc-agent",
    "Prefix for resource naming"
)
ENVIRONMENT = get_env("ENVIRONMENT", "dev", "Environment name (dev/staging/prod)")

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
