#!/usr/bin/env python3
"""
Setup Glue Catalog Database and Table Schemas

This script creates the AWS Glue Data Catalog database and table definitions
for the supply chain MVP. It defines schemas for all 6 tables:
- product
- warehouse_product
- sales_order_header
- sales_order_line
- purchase_order_header
- purchase_order_line

Usage:
    python setup_glue_catalog.py --database supply_chain_catalog --region us-east-1
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
from botocore.exceptions import ClientError


def create_glue_database(glue_client, database_name: str, description: str = None):
    """Create Glue Catalog database if it doesn't exist."""
    try:
        glue_client.get_database(Name=database_name)
        print(f"✓ Database '{database_name}' already exists")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityNotFoundException':
            # Database doesn't exist, create it
            try:
                glue_client.create_database(
                    DatabaseInput={
                        'Name': database_name,
                        'Description': description or 'Supply Chain MVP Database'
                    }
                )
                print(f"✓ Created database '{database_name}'")
                return True
            except ClientError as create_error:
                print(f"✗ Error creating database: {create_error}")
                return False
        else:
            print(f"✗ Error checking database: {e}")
            return False


def create_product_table(glue_client, database_name: str):
    """Create product table schema in Glue Catalog."""
    table_input = {
        'Name': 'product',
        'Description': 'Product master data',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'product_code', 'Type': 'string', 'Comment': 'Unique product identifier'},
                {'Name': 'product_name', 'Type': 'string', 'Comment': 'Product name'},
                {'Name': 'product_group', 'Type': 'string', 'Comment': 'Product category/group'},
                {'Name': 'unit_cost', 'Type': 'decimal(10,2)', 'Comment': 'Cost per unit'},
                {'Name': 'unit_price', 'Type': 'decimal(10,2)', 'Comment': 'Selling price per unit'},
                {'Name': 'supplier_code', 'Type': 'string', 'Comment': 'Default supplier code'},
                {'Name': 'supplier_name', 'Type': 'string', 'Comment': 'Default supplier name'},
                {'Name': 'created_date', 'Type': 'date', 'Comment': 'Record creation date'},
                {'Name': 'updated_date', 'Type': 'date', 'Comment': 'Last update date'}
            ],
            'Location': '',  # Will be set when data is loaded
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
            }
        },
        'TableType': 'EXTERNAL_TABLE'
    }
    
    try:
        glue_client.create_table(DatabaseName=database_name, TableInput=table_input)
        print(f"✓ Created table 'product'")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            print(f"✓ Table 'product' already exists")
            return True
        else:
            print(f"✗ Error creating table 'product': {e}")
            return False


def create_warehouse_product_table(glue_client, database_name: str):
    """Create warehouse_product table schema in Glue Catalog."""
    table_input = {
        'Name': 'warehouse_product',
        'Description': 'Inventory levels by warehouse and product',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'warehouse_code', 'Type': 'string', 'Comment': 'Warehouse identifier'},
                {'Name': 'product_code', 'Type': 'string', 'Comment': 'Product identifier'},
                {'Name': 'current_stock', 'Type': 'int', 'Comment': 'Current stock quantity'},
                {'Name': 'minimum_stock', 'Type': 'int', 'Comment': 'Minimum stock level'},
                {'Name': 'maximum_stock', 'Type': 'int', 'Comment': 'Maximum stock level'},
                {'Name': 'reorder_point', 'Type': 'int', 'Comment': 'Reorder point quantity'},
                {'Name': 'lead_time_days', 'Type': 'int', 'Comment': 'Lead time in days'},
                {'Name': 'last_restock_date', 'Type': 'date', 'Comment': 'Last restock date'}
            ],
            'Location': '',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
            }
        },
        'TableType': 'EXTERNAL_TABLE'
    }
    
    try:
        glue_client.create_table(DatabaseName=database_name, TableInput=table_input)
        print(f"✓ Created table 'warehouse_product'")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            print(f"✓ Table 'warehouse_product' already exists")
            return True
        else:
            print(f"✗ Error creating table 'warehouse_product': {e}")
            return False


def create_sales_order_header_table(glue_client, database_name: str):
    """Create sales_order_header table schema in Glue Catalog."""
    table_input = {
        'Name': 'sales_order_header',
        'Description': 'Sales order header information',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'sales_order_prefix', 'Type': 'string', 'Comment': 'Order prefix'},
                {'Name': 'sales_order_number', 'Type': 'string', 'Comment': 'Order number'},
                {'Name': 'order_date', 'Type': 'date', 'Comment': 'Order date'},
                {'Name': 'customer_code', 'Type': 'string', 'Comment': 'Customer identifier'},
                {'Name': 'customer_name', 'Type': 'string', 'Comment': 'Customer name'},
                {'Name': 'warehouse_code', 'Type': 'string', 'Comment': 'Fulfillment warehouse'},
                {'Name': 'delivery_address', 'Type': 'string', 'Comment': 'Delivery address'},
                {'Name': 'delivery_area', 'Type': 'string', 'Comment': 'Delivery area/zone'},
                {'Name': 'delivery_date', 'Type': 'date', 'Comment': 'Expected delivery date'},
                {'Name': 'status', 'Type': 'string', 'Comment': 'Order status'}
            ],
            'Location': '',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
            }
        },
        'TableType': 'EXTERNAL_TABLE'
    }
    
    try:
        glue_client.create_table(DatabaseName=database_name, TableInput=table_input)
        print(f"✓ Created table 'sales_order_header'")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            print(f"✓ Table 'sales_order_header' already exists")
            return True
        else:
            print(f"✗ Error creating table 'sales_order_header': {e}")
            return False


def create_sales_order_line_table(glue_client, database_name: str):
    """Create sales_order_line table schema in Glue Catalog."""
    table_input = {
        'Name': 'sales_order_line',
        'Description': 'Sales order line items',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'sales_order_prefix', 'Type': 'string', 'Comment': 'Order prefix'},
                {'Name': 'sales_order_number', 'Type': 'string', 'Comment': 'Order number'},
                {'Name': 'sales_order_line', 'Type': 'int', 'Comment': 'Line number'},
                {'Name': 'product_code', 'Type': 'string', 'Comment': 'Product identifier'},
                {'Name': 'order_quantity', 'Type': 'int', 'Comment': 'Ordered quantity'},
                {'Name': 'fulfilled_quantity', 'Type': 'int', 'Comment': 'Fulfilled quantity'},
                {'Name': 'unit_price', 'Type': 'decimal(10,2)', 'Comment': 'Unit price'},
                {'Name': 'line_total', 'Type': 'decimal(10,2)', 'Comment': 'Line total amount'},
                {'Name': 'fulfillment_status', 'Type': 'string', 'Comment': 'Fulfillment status'}
            ],
            'Location': '',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
            }
        },
        'TableType': 'EXTERNAL_TABLE'
    }
    
    try:
        glue_client.create_table(DatabaseName=database_name, TableInput=table_input)
        print(f"✓ Created table 'sales_order_line'")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            print(f"✓ Table 'sales_order_line' already exists")
            return True
        else:
            print(f"✗ Error creating table 'sales_order_line': {e}")
            return False


def create_purchase_order_header_table(glue_client, database_name: str):
    """Create purchase_order_header table schema in Glue Catalog."""
    table_input = {
        'Name': 'purchase_order_header',
        'Description': 'Purchase order header information',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'purchase_order_prefix', 'Type': 'string', 'Comment': 'PO prefix'},
                {'Name': 'purchase_order_number', 'Type': 'string', 'Comment': 'PO number'},
                {'Name': 'order_date', 'Type': 'date', 'Comment': 'Order date'},
                {'Name': 'supplier_code', 'Type': 'string', 'Comment': 'Supplier identifier'},
                {'Name': 'supplier_name', 'Type': 'string', 'Comment': 'Supplier name'},
                {'Name': 'warehouse_code', 'Type': 'string', 'Comment': 'Receiving warehouse'},
                {'Name': 'expected_delivery_date', 'Type': 'date', 'Comment': 'Expected delivery date'},
                {'Name': 'actual_delivery_date', 'Type': 'date', 'Comment': 'Actual delivery date'},
                {'Name': 'status', 'Type': 'string', 'Comment': 'PO status'}
            ],
            'Location': '',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
            }
        },
        'TableType': 'EXTERNAL_TABLE'
    }
    
    try:
        glue_client.create_table(DatabaseName=database_name, TableInput=table_input)
        print(f"✓ Created table 'purchase_order_header'")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            print(f"✓ Table 'purchase_order_header' already exists")
            return True
        else:
            print(f"✗ Error creating table 'purchase_order_header': {e}")
            return False


def create_purchase_order_line_table(glue_client, database_name: str):
    """Create purchase_order_line table schema in Glue Catalog."""
    table_input = {
        'Name': 'purchase_order_line',
        'Description': 'Purchase order line items',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'purchase_order_prefix', 'Type': 'string', 'Comment': 'PO prefix'},
                {'Name': 'purchase_order_number', 'Type': 'string', 'Comment': 'PO number'},
                {'Name': 'purchase_order_line', 'Type': 'int', 'Comment': 'Line number'},
                {'Name': 'product_code', 'Type': 'string', 'Comment': 'Product identifier'},
                {'Name': 'order_quantity', 'Type': 'int', 'Comment': 'Ordered quantity'},
                {'Name': 'received_quantity', 'Type': 'int', 'Comment': 'Received quantity'},
                {'Name': 'unit_cost', 'Type': 'decimal(10,2)', 'Comment': 'Unit cost'},
                {'Name': 'line_total', 'Type': 'decimal(10,2)', 'Comment': 'Line total amount'},
                {'Name': 'receipt_status', 'Type': 'string', 'Comment': 'Receipt status'}
            ],
            'Location': '',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
            }
        },
        'TableType': 'EXTERNAL_TABLE'
    }
    
    try:
        glue_client.create_table(DatabaseName=database_name, TableInput=table_input)
        print(f"✓ Created table 'purchase_order_line'")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            print(f"✓ Table 'purchase_order_line' already exists")
            return True
        else:
            print(f"✗ Error creating table 'purchase_order_line': {e}")
            return False


def main():
    """Main function to set up Glue Catalog."""
    parser = argparse.ArgumentParser(
        description='Setup AWS Glue Data Catalog for Supply Chain MVP'
    )
    parser.add_argument(
        '--database',
        default='supply_chain_catalog',
        help='Glue database name (default: supply_chain_catalog)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--profile',
        default=None,
        help='AWS profile name (optional)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AWS Glue Data Catalog Setup")
    print("=" * 60)
    print(f"Database: {args.database}")
    print(f"Region: {args.region}")
    print("=" * 60)
    print()
    
    # Create Glue client
    session_kwargs = {'region_name': args.region}
    if args.profile:
        session_kwargs['profile_name'] = args.profile
    
    session = boto3.Session(**session_kwargs)
    glue_client = session.client('glue')
    
    # Create database
    print("Step 1: Creating Glue Database")
    print("-" * 60)
    if not create_glue_database(glue_client, args.database):
        print("\n✗ Failed to create database. Exiting.")
        sys.exit(1)
    print()
    
    # Create tables
    print("Step 2: Creating Table Schemas")
    print("-" * 60)
    
    tables_created = []
    tables_failed = []
    
    table_functions = [
        ('product', create_product_table),
        ('warehouse_product', create_warehouse_product_table),
        ('sales_order_header', create_sales_order_header_table),
        ('sales_order_line', create_sales_order_line_table),
        ('purchase_order_header', create_purchase_order_header_table),
        ('purchase_order_line', create_purchase_order_line_table)
    ]
    
    for table_name, create_func in table_functions:
        if create_func(glue_client, args.database):
            tables_created.append(table_name)
        else:
            tables_failed.append(table_name)
    
    print()
    print("=" * 60)
    print("Setup Summary")
    print("=" * 60)
    print(f"Database: {args.database}")
    print(f"Tables created/verified: {len(tables_created)}")
    for table in tables_created:
        print(f"  ✓ {table}")
    
    if tables_failed:
        print(f"\nTables failed: {len(tables_failed)}")
        for table in tables_failed:
            print(f"  ✗ {table}")
        print("\n✗ Setup completed with errors")
        sys.exit(1)
    else:
        print("\n✓ Setup completed successfully!")
        print("\nNext steps:")
        print("  1. Run generate_sample_data.py to create and load sample data")
        print("  2. Verify tables in AWS Glue Console")
        sys.exit(0)


if __name__ == '__main__':
    main()
