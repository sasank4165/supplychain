#!/usr/bin/env python3
"""
Generate Sample Data for Supply Chain MVP

This script generates realistic sample data for all 6 tables:
- 100+ products across multiple product groups
- 3 warehouses with inventory levels
- 90 days of sales orders and purchase orders

The data is generated in-memory and can be exported to CSV or loaded directly
into Redshift Serverless.

Usage:
    # Generate data and save to CSV files
    python generate_sample_data.py --output-dir ./sample_data
    
    # Generate data and load into Redshift
    python generate_sample_data.py --load-redshift --workgroup supply-chain-mvp --database supply_chain_db
"""

import argparse
import sys
import os
import random
import csv
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Sample data constants
PRODUCT_GROUPS = [
    'Electronics', 'Hardware', 'Tools', 'Safety Equipment', 
    'Office Supplies', 'Industrial Parts', 'Chemicals', 'Packaging'
]

WAREHOUSES = [
    {'code': 'WH001', 'name': 'North Warehouse', 'area': 'North'},
    {'code': 'WH002', 'name': 'South Warehouse', 'area': 'South'},
    {'code': 'WH003', 'name': 'Central Warehouse', 'area': 'Central'}
]

SUPPLIERS = [
    {'code': 'SUP001', 'name': 'TechSupply Inc'},
    {'code': 'SUP002', 'name': 'Industrial Parts Co'},
    {'code': 'SUP003', 'name': 'Global Electronics'},
    {'code': 'SUP004', 'name': 'Safety First Ltd'},
    {'code': 'SUP005', 'name': 'Office Depot Pro'},
    {'code': 'SUP006', 'name': 'Chemical Solutions'},
    {'code': 'SUP007', 'name': 'Hardware Wholesale'},
    {'code': 'SUP008', 'name': 'Packaging Masters'}
]

CUSTOMERS = [
    {'code': 'CUST001', 'name': 'ABC Manufacturing'},
    {'code': 'CUST002', 'name': 'XYZ Industries'},
    {'code': 'CUST003', 'name': 'Tech Solutions Ltd'},
    {'code': 'CUST004', 'name': 'BuildRight Construction'},
    {'code': 'CUST005', 'name': 'SafeWork Corp'},
    {'code': 'CUST006', 'name': 'Office Pro Services'},
    {'code': 'CUST007', 'name': 'Industrial Systems Inc'},
    {'code': 'CUST008', 'name': 'Green Energy Co'},
    {'code': 'CUST009', 'name': 'Metro Logistics'},
    {'code': 'CUST010', 'name': 'Quality Assurance Ltd'}
]

DELIVERY_AREAS = ['North', 'South', 'East', 'West', 'Central', 'Downtown', 'Suburbs']

ORDER_STATUSES = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
FULFILLMENT_STATUSES = ['Pending', 'Partial', 'Complete', 'Cancelled']
PO_STATUSES = ['Draft', 'Submitted', 'Approved', 'Received', 'Closed']
RECEIPT_STATUSES = ['Pending', 'Partial', 'Complete']


def generate_products(num_products: int = 150) -> List[Dict[str, Any]]:
    """Generate product master data."""
    products = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(1, num_products + 1):
        product_code = f"PROD{i:04d}"
        product_group = random.choice(PRODUCT_GROUPS)
        supplier = random.choice(SUPPLIERS)
        
        # Generate realistic costs and prices
        unit_cost = round(random.uniform(5.0, 500.0), 2)
        markup = random.uniform(1.2, 2.5)
        unit_price = round(unit_cost * markup, 2)
        
        created_date = base_date + timedelta(days=random.randint(0, 300))
        updated_date = created_date + timedelta(days=random.randint(0, 60))
        
        products.append({
            'product_code': product_code,
            'product_name': f"{product_group} Item {i}",
            'product_group': product_group,
            'unit_cost': unit_cost,
            'unit_price': unit_price,
            'supplier_code': supplier['code'],
            'supplier_name': supplier['name'],
            'created_date': created_date.strftime('%Y-%m-%d'),
            'updated_date': updated_date.strftime('%Y-%m-%d')
        })
    
    return products


def generate_warehouse_products(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate inventory levels for each warehouse and product."""
    warehouse_products = []
    
    for warehouse in WAREHOUSES:
        # Each warehouse stocks 70-90% of products
        num_products_in_warehouse = int(len(products) * random.uniform(0.7, 0.9))
        stocked_products = random.sample(products, num_products_in_warehouse)
        
        for product in stocked_products:
            # Generate realistic inventory levels
            minimum_stock = random.randint(10, 50)
            maximum_stock = minimum_stock * random.randint(5, 10)
            reorder_point = int(minimum_stock * random.uniform(1.5, 2.5))
            current_stock = random.randint(0, maximum_stock)
            lead_time_days = random.randint(3, 21)
            
            last_restock_date = datetime.now() - timedelta(days=random.randint(1, 60))
            
            warehouse_products.append({
                'warehouse_code': warehouse['code'],
                'product_code': product['product_code'],
                'current_stock': current_stock,
                'minimum_stock': minimum_stock,
                'maximum_stock': maximum_stock,
                'reorder_point': reorder_point,
                'lead_time_days': lead_time_days,
                'last_restock_date': last_restock_date.strftime('%Y-%m-%d')
            })
    
    return warehouse_products


def generate_sales_orders(products: List[Dict[str, Any]], days: int = 90) -> tuple:
    """Generate sales order headers and lines for the specified number of days."""
    headers = []
    lines = []
    
    start_date = datetime.now() - timedelta(days=days)
    order_counter = 1
    
    # Generate 3-8 orders per day
    for day in range(days):
        order_date = start_date + timedelta(days=day)
        num_orders = random.randint(3, 8)
        
        for _ in range(num_orders):
            order_prefix = 'SO'
            order_number = f"{order_counter:06d}"
            customer = random.choice(CUSTOMERS)
            warehouse = random.choice(WAREHOUSES)
            delivery_area = random.choice(DELIVERY_AREAS)
            
            # Delivery date is 1-14 days after order date
            delivery_date = order_date + timedelta(days=random.randint(1, 14))
            
            # Determine order status based on dates
            days_since_order = (datetime.now() - order_date).days
            if days_since_order < 2:
                status = 'Pending'
            elif days_since_order < 5:
                status = random.choice(['Processing', 'Shipped'])
            elif delivery_date < datetime.now():
                status = random.choice(['Delivered', 'Delivered', 'Delivered', 'Cancelled'])
            else:
                status = 'Shipped'
            
            headers.append({
                'sales_order_prefix': order_prefix,
                'sales_order_number': order_number,
                'order_date': order_date.strftime('%Y-%m-%d'),
                'customer_code': customer['code'],
                'customer_name': customer['name'],
                'warehouse_code': warehouse['code'],
                'delivery_address': f"{random.randint(100, 9999)} Main St, City",
                'delivery_area': delivery_area,
                'delivery_date': delivery_date.strftime('%Y-%m-%d'),
                'status': status
            })
            
            # Generate 1-5 line items per order
            num_lines = random.randint(1, 5)
            order_products = random.sample(products, min(num_lines, len(products)))
            
            for line_num, product in enumerate(order_products, 1):
                order_quantity = random.randint(1, 50)
                
                # Fulfillment based on order status
                if status == 'Delivered':
                    fulfilled_quantity = order_quantity
                    fulfillment_status = 'Complete'
                elif status == 'Shipped':
                    fulfilled_quantity = order_quantity
                    fulfillment_status = 'Complete'
                elif status == 'Processing':
                    fulfilled_quantity = random.randint(0, order_quantity)
                    fulfillment_status = 'Partial' if fulfilled_quantity > 0 else 'Pending'
                elif status == 'Cancelled':
                    fulfilled_quantity = 0
                    fulfillment_status = 'Cancelled'
                else:
                    fulfilled_quantity = 0
                    fulfillment_status = 'Pending'
                
                unit_price = product['unit_price']
                line_total = round(unit_price * order_quantity, 2)
                
                lines.append({
                    'sales_order_prefix': order_prefix,
                    'sales_order_number': order_number,
                    'sales_order_line': line_num,
                    'product_code': product['product_code'],
                    'order_quantity': order_quantity,
                    'fulfilled_quantity': fulfilled_quantity,
                    'unit_price': unit_price,
                    'line_total': line_total,
                    'fulfillment_status': fulfillment_status
                })
            
            order_counter += 1
    
    return headers, lines


def generate_purchase_orders(products: List[Dict[str, Any]], days: int = 90) -> tuple:
    """Generate purchase order headers and lines for the specified number of days."""
    headers = []
    lines = []
    
    start_date = datetime.now() - timedelta(days=days)
    po_counter = 1
    
    # Generate 2-5 POs per week
    for week in range(days // 7):
        week_start = start_date + timedelta(weeks=week)
        num_pos = random.randint(2, 5)
        
        for _ in range(num_pos):
            po_prefix = 'PO'
            po_number = f"{po_counter:06d}"
            order_date = week_start + timedelta(days=random.randint(0, 6))
            supplier = random.choice(SUPPLIERS)
            warehouse = random.choice(WAREHOUSES)
            
            # Expected delivery is 7-21 days after order
            expected_delivery = order_date + timedelta(days=random.randint(7, 21))
            
            # Determine actual delivery and status
            days_since_order = (datetime.now() - order_date).days
            if days_since_order < 7:
                status = random.choice(['Draft', 'Submitted', 'Approved'])
                actual_delivery = None
            elif expected_delivery < datetime.now():
                # Delivered with some variance
                actual_delivery = expected_delivery + timedelta(days=random.randint(-2, 5))
                status = random.choice(['Received', 'Closed'])
            else:
                status = 'Approved'
                actual_delivery = None
            
            headers.append({
                'purchase_order_prefix': po_prefix,
                'purchase_order_number': po_number,
                'order_date': order_date.strftime('%Y-%m-%d'),
                'supplier_code': supplier['code'],
                'supplier_name': supplier['name'],
                'warehouse_code': warehouse['code'],
                'expected_delivery_date': expected_delivery.strftime('%Y-%m-%d'),
                'actual_delivery_date': actual_delivery.strftime('%Y-%m-%d') if actual_delivery else None,
                'status': status
            })
            
            # Generate 2-8 line items per PO
            num_lines = random.randint(2, 8)
            # Filter products from this supplier
            supplier_products = [p for p in products if p['supplier_code'] == supplier['code']]
            if not supplier_products:
                supplier_products = random.sample(products, min(num_lines, len(products)))
            else:
                supplier_products = random.sample(supplier_products, min(num_lines, len(supplier_products)))
            
            for line_num, product in enumerate(supplier_products, 1):
                order_quantity = random.randint(50, 500)
                
                # Receipt based on PO status
                if status in ['Received', 'Closed']:
                    received_quantity = order_quantity + random.randint(-5, 5)
                    received_quantity = max(0, received_quantity)
                    receipt_status = 'Complete'
                elif status == 'Approved':
                    received_quantity = random.randint(0, order_quantity // 2)
                    receipt_status = 'Partial' if received_quantity > 0 else 'Pending'
                else:
                    received_quantity = 0
                    receipt_status = 'Pending'
                
                unit_cost = product['unit_cost']
                line_total = round(unit_cost * order_quantity, 2)
                
                lines.append({
                    'purchase_order_prefix': po_prefix,
                    'purchase_order_number': po_number,
                    'purchase_order_line': line_num,
                    'product_code': product['product_code'],
                    'order_quantity': order_quantity,
                    'received_quantity': received_quantity,
                    'unit_cost': unit_cost,
                    'line_total': line_total,
                    'receipt_status': receipt_status
                })
            
            po_counter += 1
    
    return headers, lines


def save_to_csv(data: List[Dict[str, Any]], filename: str, output_dir: str):
    """Save data to CSV file."""
    if not data:
        print(f"  ⚠ No data to save for {filename}")
        return
    
    filepath = Path(output_dir) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    print(f"  ✓ Saved {len(data)} rows to {filepath}")


def create_redshift_tables(redshift_client):
    """Create Redshift tables if they don't exist."""
    
    # SQL statements to create tables
    create_statements = [
        # Product table
        """
        CREATE TABLE IF NOT EXISTS product (
            product_code VARCHAR(50) PRIMARY KEY,
            product_name VARCHAR(200) NOT NULL,
            product_group VARCHAR(50),
            unit_cost DECIMAL(10,2),
            unit_price DECIMAL(10,2),
            supplier_code VARCHAR(50),
            supplier_name VARCHAR(200),
            created_date DATE,
            updated_date DATE
        )
        """,
        
        # Warehouse product table
        """
        CREATE TABLE IF NOT EXISTS warehouse_product (
            warehouse_code VARCHAR(50),
            product_code VARCHAR(50),
            current_stock INTEGER,
            minimum_stock INTEGER,
            maximum_stock INTEGER,
            reorder_point INTEGER,
            lead_time_days INTEGER,
            last_restock_date DATE,
            PRIMARY KEY (warehouse_code, product_code)
        )
        """,
        
        # Sales order header table
        """
        CREATE TABLE IF NOT EXISTS sales_order_header (
            sales_order_prefix VARCHAR(10),
            sales_order_number VARCHAR(50),
            order_date DATE,
            customer_code VARCHAR(50),
            customer_name VARCHAR(200),
            warehouse_code VARCHAR(50),
            delivery_address VARCHAR(500),
            delivery_area VARCHAR(100),
            delivery_date DATE,
            status VARCHAR(50),
            PRIMARY KEY (sales_order_prefix, sales_order_number)
        )
        """,
        
        # Sales order line table
        """
        CREATE TABLE IF NOT EXISTS sales_order_line (
            sales_order_prefix VARCHAR(10),
            sales_order_number VARCHAR(50),
            sales_order_line INTEGER,
            product_code VARCHAR(50),
            order_quantity INTEGER,
            fulfilled_quantity INTEGER,
            unit_price DECIMAL(10,2),
            line_total DECIMAL(10,2),
            fulfillment_status VARCHAR(50),
            PRIMARY KEY (sales_order_prefix, sales_order_number, sales_order_line)
        )
        """,
        
        # Purchase order header table
        """
        CREATE TABLE IF NOT EXISTS purchase_order_header (
            purchase_order_prefix VARCHAR(10),
            purchase_order_number VARCHAR(50),
            order_date DATE,
            supplier_code VARCHAR(50),
            supplier_name VARCHAR(200),
            warehouse_code VARCHAR(50),
            expected_delivery_date DATE,
            actual_delivery_date DATE,
            status VARCHAR(50),
            PRIMARY KEY (purchase_order_prefix, purchase_order_number)
        )
        """,
        
        # Purchase order line table
        """
        CREATE TABLE IF NOT EXISTS purchase_order_line (
            purchase_order_prefix VARCHAR(10),
            purchase_order_number VARCHAR(50),
            purchase_order_line INTEGER,
            product_code VARCHAR(50),
            order_quantity INTEGER,
            received_quantity INTEGER,
            unit_cost DECIMAL(10,2),
            line_total DECIMAL(10,2),
            receipt_status VARCHAR(50),
            PRIMARY KEY (purchase_order_prefix, purchase_order_number, purchase_order_line)
        )
        """
    ]
    
    print("Creating tables...")
    for i, sql in enumerate(create_statements, 1):
        try:
            redshift_client.execute_query(sql)
            print(f"  ✓ Table {i}/6 created/verified")
        except Exception as e:
            print(f"  ✗ Error creating table {i}: {e}")
            raise
    print()


def load_data_to_redshift(
    redshift_client,
    products: List[Dict],
    warehouse_products: List[Dict],
    so_headers: List[Dict],
    so_lines: List[Dict],
    po_headers: List[Dict],
    po_lines: List[Dict]
):
    """Load generated data into Redshift tables."""
    
    # Create tables first
    create_redshift_tables(redshift_client)
    
    # Clear existing data
    print("Clearing existing data...")
    tables = [
        'sales_order_line',
        'sales_order_header',
        'purchase_order_line',
        'purchase_order_header',
        'warehouse_product',
        'product'
    ]
    
    for table in tables:
        try:
            redshift_client.execute_query(f"DELETE FROM {table}")
            print(f"  ✓ Cleared {table}")
        except Exception as e:
            print(f"  ⚠ Warning clearing {table}: {e}")
    print()
    
    # Load products
    print("Loading products...")
    load_table_data(redshift_client, 'product', products)
    
    # Load warehouse products
    print("Loading warehouse inventory...")
    load_table_data(redshift_client, 'warehouse_product', warehouse_products)
    
    # Load sales order headers
    print("Loading sales order headers...")
    load_table_data(redshift_client, 'sales_order_header', so_headers)
    
    # Load sales order lines
    print("Loading sales order lines...")
    load_table_data(redshift_client, 'sales_order_line', so_lines)
    
    # Load purchase order headers
    print("Loading purchase order headers...")
    load_table_data(redshift_client, 'purchase_order_header', po_headers)
    
    # Load purchase order lines
    print("Loading purchase order lines...")
    load_table_data(redshift_client, 'purchase_order_line', po_lines)
    
    # Verify data loaded
    print("\nVerifying data load...")
    verify_data_load(redshift_client)


def load_table_data(redshift_client, table_name: str, data: List[Dict[str, Any]]):
    """Load data into a specific table using INSERT statements."""
    if not data:
        print(f"  ⚠ No data to load for {table_name}")
        return
    
    # Get column names from first record
    columns = list(data[0].keys())
    column_list = ', '.join(columns)
    
    # Load data in batches to avoid query size limits
    batch_size = 100
    total_batches = (len(data) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(data))
        batch = data[start_idx:end_idx]
        
        # Build INSERT statement with multiple values
        values_list = []
        for row in batch:
            values = []
            for col in columns:
                value = row[col]
                if value is None:
                    values.append('NULL')
                elif isinstance(value, (int, float)):
                    values.append(str(value))
                else:
                    # Escape single quotes
                    escaped = str(value).replace("'", "''")
                    values.append(f"'{escaped}'")
            values_list.append(f"({', '.join(values)})")
        
        values_clause = ',\n'.join(values_list)
        sql = f"INSERT INTO {table_name} ({column_list}) VALUES\n{values_clause}"
        
        try:
            redshift_client.execute_query(sql)
            print(f"  ✓ Loaded batch {batch_num + 1}/{total_batches} ({len(batch)} rows)")
        except Exception as e:
            print(f"  ✗ Error loading batch {batch_num + 1}: {e}")
            raise
    
    print(f"  ✓ Completed loading {len(data)} rows into {table_name}")
    print()


def verify_data_load(redshift_client):
    """Verify that data was loaded correctly."""
    tables = [
        'product',
        'warehouse_product',
        'sales_order_header',
        'sales_order_line',
        'purchase_order_header',
        'purchase_order_line'
    ]
    
    for table in tables:
        try:
            result = redshift_client.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            count = result.rows[0][0] if result.rows else 0
            print(f"  ✓ {table}: {count} rows")
        except Exception as e:
            print(f"  ✗ Error verifying {table}: {e}")
    
    print("\n✓ Data load verification complete!")


def main():
    """Main function to generate sample data."""
    parser = argparse.ArgumentParser(
        description='Generate sample data for Supply Chain MVP'
    )
    parser.add_argument(
        '--output-dir',
        default='./sample_data',
        help='Output directory for CSV files (default: ./sample_data)'
    )
    parser.add_argument(
        '--num-products',
        type=int,
        default=150,
        help='Number of products to generate (default: 150)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Number of days of order history (default: 90)'
    )
    parser.add_argument(
        '--load-redshift',
        action='store_true',
        help='Load data into Redshift Serverless (requires additional args)'
    )
    parser.add_argument(
        '--workgroup',
        help='Redshift Serverless workgroup name'
    )
    parser.add_argument(
        '--database',
        help='Redshift database name'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Sample Data Generation")
    print("=" * 60)
    print(f"Products: {args.num_products}")
    print(f"Warehouses: {len(WAREHOUSES)}")
    print(f"Order history: {args.days} days")
    print("=" * 60)
    print()
    
    # Generate data
    print("Step 1: Generating Products")
    print("-" * 60)
    products = generate_products(args.num_products)
    print(f"✓ Generated {len(products)} products")
    print()
    
    print("Step 2: Generating Warehouse Inventory")
    print("-" * 60)
    warehouse_products = generate_warehouse_products(products)
    print(f"✓ Generated {len(warehouse_products)} warehouse-product records")
    print()
    
    print("Step 3: Generating Sales Orders")
    print("-" * 60)
    so_headers, so_lines = generate_sales_orders(products, args.days)
    print(f"✓ Generated {len(so_headers)} sales orders with {len(so_lines)} line items")
    print()
    
    print("Step 4: Generating Purchase Orders")
    print("-" * 60)
    po_headers, po_lines = generate_purchase_orders(products, args.days)
    print(f"✓ Generated {len(po_headers)} purchase orders with {len(po_lines)} line items")
    print()
    
    # Save to CSV
    print("Step 5: Saving to CSV Files")
    print("-" * 60)
    save_to_csv(products, 'product.csv', args.output_dir)
    save_to_csv(warehouse_products, 'warehouse_product.csv', args.output_dir)
    save_to_csv(so_headers, 'sales_order_header.csv', args.output_dir)
    save_to_csv(so_lines, 'sales_order_line.csv', args.output_dir)
    save_to_csv(po_headers, 'purchase_order_header.csv', args.output_dir)
    save_to_csv(po_lines, 'purchase_order_line.csv', args.output_dir)
    print()
    
    # Load to Redshift if requested
    if args.load_redshift:
        if not args.workgroup or not args.database:
            print("✗ Error: --workgroup and --database are required for --load-redshift")
            sys.exit(1)
        
        print("Step 6: Loading Data into Redshift Serverless")
        print("-" * 60)
        
        try:
            from aws.redshift_client import RedshiftClient, RedshiftClientError
            
            # Initialize Redshift client
            redshift = RedshiftClient(
                region=args.region,
                workgroup_name=args.workgroup,
                database=args.database,
                timeout=60
            )
            
            # Test connection
            print("Testing Redshift connection...")
            redshift.test_connection()
            print("✓ Connection successful")
            print()
            
            # Load data into tables
            load_data_to_redshift(
                redshift,
                products,
                warehouse_products,
                so_headers,
                so_lines,
                po_headers,
                po_lines
            )
            
        except ImportError as e:
            print(f"✗ Error: Could not import RedshiftClient: {e}")
            print("  Make sure you're running from the mvp directory")
            sys.exit(1)
        except RedshiftClientError as e:
            print(f"✗ Redshift error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            sys.exit(1)
        
        print()
    
    print("=" * 60)
    print("Data Generation Summary")
    print("=" * 60)
    print(f"Products: {len(products)}")
    print(f"Warehouse Products: {len(warehouse_products)}")
    print(f"Sales Orders: {len(so_headers)} ({len(so_lines)} lines)")
    print(f"Purchase Orders: {len(po_headers)} ({len(po_lines)} lines)")
    print(f"\nCSV files saved to: {args.output_dir}")
    
    if args.load_redshift:
        print("\n✓ Data successfully loaded into Redshift Serverless!")
        print(f"  Workgroup: {args.workgroup}")
        print(f"  Database: {args.database}")
    else:
        print("\n✓ Data generation completed successfully!")
        print("\nNext steps:")
        print("  1. Review CSV files in the output directory")
        print("  2. Run with --load-redshift to load data into Redshift")
        print("     Example: python generate_sample_data.py --load-redshift \\")
        print(f"              --workgroup {args.workgroup or 'YOUR_WORKGROUP'} \\")
        print(f"              --database {args.database or 'YOUR_DATABASE'}")


if __name__ == '__main__':
    main()
