#!/usr/bin/env python3
"""Generate sample supply chain data for testing"""
import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

fake = Faker()

# Data size configurations
SIZES = {
    'small': {
        'products': 100,
        'warehouses': 2,
        'customers': 50,
        'suppliers': 10,
        'sales_orders': 500,
        'purchase_orders': 200
    },
    'medium': {
        'products': 1000,
        'warehouses': 5,
        'customers': 200,
        'suppliers': 30,
        'sales_orders': 5000,
        'purchase_orders': 2000
    },
    'large': {
        'products': 10000,
        'warehouses': 10,
        'customers': 1000,
        'suppliers': 100,
        'sales_orders': 50000,
        'purchase_orders': 20000
    }
}

def generate_date(days_ago=0, days_range=30):
    """Generate date in YYYYMMDD format"""
    base_date = datetime.now() - timedelta(days=days_ago)
    random_days = random.randint(0, days_range)
    date = base_date - timedelta(days=random_days)
    return int(date.strftime('%Y%m%d'))

def generate_products(count, output_dir):
    """Generate product master data"""
    print(f"Generating {count} products...")
    
    product_groups = ['WIDGETS', 'GADGETS', 'TOOLS', 'PARTS', 'ACCESSORIES']
    sub_groups = ['STANDARD', 'PREMIUM', 'ECONOMY', 'PROFESSIONAL']
    
    products = []
    for i in range(1, count + 1):
        product = {
            'product_code': f'P{i:06d}',
            'short_name': f'{fake.word().title()} {fake.word().title()}',
            'product_description': fake.catch_phrase(),
            'product_group': random.choice(product_groups),
            'supplier_code1': f'SUP{random.randint(1, 100):03d}',
            'stock_account': f'STK{random.randint(1, 10):03d}',
            'date_created': generate_date(days_ago=365, days_range=365),
            'date_amended': generate_date(days_ago=0, days_range=90),
            'tax_code': 'TAX1',
            'standard_cost': round(random.uniform(5.0, 500.0), 2),
            'standard_height': round(random.uniform(1.0, 50.0), 2),
            'standard_weight': round(random.uniform(0.5, 100.0), 2),
            'standard_length': round(random.uniform(5.0, 100.0), 2),
            'standard_width': round(random.uniform(5.0, 100.0), 2),
            'stocking_units': 'EA',
            'standard_rrp': round(random.uniform(10.0, 1000.0), 2),
            'order_units': 'EA',
            'stock_item': 'Y',
            'cost_indicator': 'STD',
            'back_order': random.choice(['Y', 'N']),
            'sop_product': 'Y',
            'manufactured': random.choice(['Y', 'N']),
            'sub_product_group': random.choice(sub_groups),
            'analysis_code': f'AN{random.randint(1, 10):03d}',
            'inner_qty_su': 1,
            'outer_qty_su': random.choice([5, 10, 20, 50]),
            'qty_on_order_su': 0,
            'freight_class': f'FC{random.randint(1, 5)}',
            'product_capacity_type': random.choice(['STANDARD', 'FRAGILE', 'HAZMAT']),
            'min_suggestion_qty_su': random.choice([1, 5, 10, 20]),
            'conversion_factor': 1.0
        }
        products.append(product)
    
    # Write to CSV
    output_file = output_dir / 'product.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=products[0].keys())
        writer.writeheader()
        writer.writerows(products)
    
    print(f"✓ Created {output_file}")
    return [p['product_code'] for p in products]

def generate_warehouse_product(product_codes, warehouse_count, output_dir):
    """Generate warehouse product inventory data"""
    print(f"Generating warehouse product data for {warehouse_count} warehouses...")
    
    warehouses = [f'WH{i:02d}' for i in range(1, warehouse_count + 1)]
    records = []
    
    for warehouse in warehouses:
        for product_code in product_codes:
            # Not all products in all warehouses
            if random.random() < 0.7:  # 70% coverage
                physical_stock = random.randint(0, 500)
                allocated = random.randint(0, min(physical_stock, 50))
                free_stock = physical_stock - allocated
                min_stock = random.randint(10, 50)
                max_stock = min_stock * random.randint(5, 10)
                
                record = {
                    'warehouse_code': warehouse,
                    'product_code': product_code,
                    'stock_account': f'STK{random.randint(1, 10):03d}',
                    'daily_opening_stock_su': physical_stock,
                    'opening_datebigint': generate_date(days_ago=1),
                    'period_opening_stock_su': physical_stock,
                    'physical_stock_su': physical_stock,
                    'free_stock_su': free_stock,
                    'qty_on_order_su': random.randint(0, 100),
                    'minimum_stock_su': min_stock,
                    'maximum_stock_su': max_stock,
                    'allocated_stock_su': allocated,
                    'order_qty_su': random.choice([10, 20, 50, 100]),
                    'standard_ord_qty_su': random.choice([10, 20, 50, 100]),
                    'standard_cost': round(random.uniform(5.0, 500.0), 2),
                    'last_cost': round(random.uniform(5.0, 500.0), 2),
                    'last_datebigint': generate_date(days_ago=0, days_range=30),
                    'lead_time_daysbigint': random.choice([3, 5, 7, 10, 14]),
                    'serial_gi': 'N',
                    'serial_desp': 'N',
                    'expiry_prod': 'N',
                    'small_qty_su': random.randint(1, 5),
                    'handling_code': f'HC{random.randint(1, 5)}',
                    'pick_loc': f'{chr(65+random.randint(0,4))}-{random.randint(1,20):02d}-{random.randint(1,10):02d}',
                    'pick_store_code': f'PS{random.randint(1, 10):02d}',
                    'last_despatch_date': generate_date(days_ago=0, days_range=7),
                    'last_received_date': generate_date(days_ago=0, days_range=14),
                    'minimum_order_qty': random.choice([5, 10, 20]),
                    'maximum_order_qty': random.choice([500, 1000, 2000]),
                    'stock_status': random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'INACTIVE'])
                }
                records.append(record)
    
    # Write to CSV
    output_file = output_dir / 'warehouse_product.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    
    print(f"✓ Created {output_file} with {len(records)} records")

def generate_sales_orders(count, product_codes, warehouse_count, customer_count, output_dir):
    """Generate sales order headers and lines"""
    print(f"Generating {count} sales orders...")
    
    warehouses = [f'WH{i:02d}' for i in range(1, warehouse_count + 1)]
    customers = [f'CUST{i:04d}' for i in range(1, customer_count + 1)]
    statuses = ['OPEN', 'PICKING', 'PACKED', 'SHIPPED', 'COMPLETED']
    
    headers = []
    lines = []
    line_id = 0
    
    for i in range(1, count + 1):
        order_num = f'SO{i:06d}'
        order_date = generate_date(days_ago=0, days_range=90)
        delivery_date = order_date + random.randint(1, 14)
        
        header = {
            'sales_order_prefix': 'SO',
            'sales_order_number': order_num,
            'customer_code': random.choice(customers),
            'customer_ref': f'REF{i:06d}',
            'deliver_to_customer': random.choice(customers),
            'deliver_to_address_no': f'ADDR{random.randint(1, 100):03d}',
            'comment': random.choice(['', 'Rush order', 'Fragile', 'Special handling']),
            'currency_code': 'USD',
            'currency_ratedouble': 1.0,
            'order_raised_date': order_date,
            'pref_del_date': delivery_date,
            'agent_code': f'AG{random.randint(1, 20):03d}',
            'text_code': 'TXT001',
            'carrier_code': f'CARR{random.randint(1, 10):03d}',
            'del_area_code': f'AREA{random.randint(1, 50):02d}',
            'del_seq_number': random.randint(1, 100),
            'posting_year': 2024,
            'posting_period': random.randint(1, 12),
            'last_line_no': random.randint(1, 10),
            'warehouse_code': random.choice(warehouses),
            'order_type': 'STANDARD',
            'forward_order': 'N',
            'acknowledge_order': 'Y',
            'free_format': 'N',
            'order_status': random.choice(statuses),
            'allocate_stock': 'Y',
            'end_cust_name': fake.company(),
            'end_cust_add_line_1': fake.street_address(),
            'end_cust_add_line_2': '',
            'end_cust_add_line_3': fake.city(),
            'end_cust_add_line_4': f'{fake.state_abbr()} {fake.zipcode()}',
            'part_request_seq': 1,
            'sales_product_type': 'STANDARD',
            'patch_id': f'P{random.randint(1, 100):03d}',
            'postcode_sector': fake.zipcode()[:5],
            'customer_id': random.choice(customers),
            'payment_received': random.choice(['Y', 'N']),
            'carriage_charge': round(random.uniform(5.0, 50.0), 2),
            'payment_type': random.choice(['CREDIT', 'CASH', 'INVOICE'])
        }
        headers.append(header)
        
        # Generate 1-5 lines per order
        num_lines = random.randint(1, 5)
        for line_num in range(1, num_lines + 1):
            line_id += 1
            qty = random.randint(1, 50)
            unit_price = round(random.uniform(10.0, 500.0), 2)
            
            line = {
                'sales_order_prefix': 'SO',
                'sales_order_number': order_num,
                'sales_order_line': line_num,
                'product_code': random.choice(product_codes),
                'desc': fake.catch_phrase(),
                'stocking_units': 'EA',
                'selling_units': 'EA',
                'qty_seludouble': qty,
                'required_delivery_date': delivery_date,
                'pick_by_date': delivery_date - 1,
                'unit_price_selu': unit_price,
                'line_value': round(qty * unit_price, 2),
                'prod_disc1_percentage': 0,
                'tax_code': 'TAX1',
                'cost_value': round(qty * unit_price * 0.6, 2),
                'allocated_qty_su': qty if header['order_status'] in ['PICKING', 'PACKED', 'SHIPPED', 'COMPLETED'] else 0,
                'qty_ordered_su': qty,
                'picked_qty_su': qty if header['order_status'] in ['PACKED', 'SHIPPED', 'COMPLETED'] else 0,
                'despatched_qty_su': qty if header['order_status'] in ['SHIPPED', 'COMPLETED'] else 0,
                'invoiced_qty_su': qty if header['order_status'] == 'COMPLETED' else 0,
                'returned_qty_su': 0,
                'qty_cancelled_su': 0,
                'value_ord_notinv': 0 if header['order_status'] == 'COMPLETED' else round(qty * unit_price, 2),
                'kit_parent_code': '',
                'kit': 'N',
                'kit_order_line': 0,
                'warehouse_code': header['warehouse_code'],
                'supply_direct': 'N',
                'linked_for_despatch': 'N',
                'schedule_deliveries': 'N',
                'order_line_status': header['order_status'],
                'order_indicator': 'STD',
                'price_basis': 'LIST',
                'tax_indicator': 'STD',
                'ship_complete': 'N',
                'ordered_product_code': random.choice(product_codes),
                'sales_period_no': random.randint(1, 12),
                'orig_req_qty_su': qty
            }
            lines.append(line)
    
    # Write headers
    output_file = output_dir / 'sales_order_header.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers[0].keys())
        writer.writeheader()
        writer.writerows(headers)
    print(f"✓ Created {output_file}")
    
    # Write lines
    output_file = output_dir / 'sales_order_line.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=lines[0].keys())
        writer.writeheader()
        writer.writerows(lines)
    print(f"✓ Created {output_file} with {len(lines)} lines")

def generate_purchase_orders(count, product_codes, supplier_count, output_dir):
    """Generate purchase order headers and lines"""
    print(f"Generating {count} purchase orders...")
    
    suppliers = [f'SUP{i:03d}' for i in range(1, supplier_count + 1)]
    statuses = ['OPEN', 'RECEIVED', 'COMPLETED']
    
    headers = []
    lines = []
    
    for i in range(1, count + 1):
        order_num = f'PO{i:06d}'
        order_date = generate_date(days_ago=0, days_range=180)
        
        header = {
            'purchase_order_prefix': 'PO',
            'purchase_order_number': order_num,
            'requisition_number': f'REQ{i:06d}',
            'supplier_code': random.choice(suppliers),
            'supplier_ref': f'SUPREF{i:06d}',
            'delivery_point': f'WH{random.randint(1, 10):02d}',
            'internal_ref': f'INT{i:06d}',
            'comment': random.choice(['', 'Urgent', 'Standard delivery', 'Bulk order']),
            'currency_code': 'USD',
            'authority_code': f'AUTH{random.randint(1, 10):03d}',
            'currency_ratedouble': 1.0,
            'order_raised_date': order_date,
            'posting_year': 2024,
            'posting_period': random.randint(1, 12),
            'last_line_no': random.randint(1, 10),
            'purchase_order_type': random.choice(['STANDARD', 'URGENT', 'BLANKET']),
            'order_status': random.choice(statuses),
            'invoice_status': random.choice(['PENDING', 'RECEIVED', 'PAID']),
            'order_released_date': order_date,
            'order_released_time': f'{random.randint(8, 17):02d}:{random.randint(0, 59):02d}:00',
            'user_id': f'USER{random.randint(1, 50):03d}'
        }
        headers.append(header)
        
        # Generate 1-5 lines per order
        num_lines = random.randint(1, 5)
        for line_num in range(1, num_lines + 1):
            qty = random.randint(10, 500)
            unit_price = round(random.uniform(5.0, 300.0), 2)
            received_qty = qty if header['order_status'] in ['RECEIVED', 'COMPLETED'] else 0
            
            line = {
                'purchase_order_prefix': 'PO',
                'purchase_order_numberbigint': i,
                'purchase_order_linebigint': line_num,
                'requisition_prefix': 'REQ',
                'requisition_number': f'REQ{i:06d}',
                'product_code': random.choice(product_codes),
                'supplier_product_ref': f'SUP-{random.choice(product_codes)}',
                'comment': '',
                'comment_on_receipt': '',
                'method_code': 'STD',
                'order_units': 'EA',
                'qty_oudouble': qty,
                'expected_dely_datebigint': order_date + random.randint(7, 30),
                'original_dely_datebigint': order_date + random.randint(7, 30),
                'unit_price_oudouble': unit_price,
                'line_valuedouble': round(qty * unit_price, 2),
                'credited_value_oudouble': 0,
                'cost_valuedouble': round(qty * unit_price, 2),
                'cost_qty_oudouble': qty,
                'in_receipt_qty_oudouble': 0,
                'received_qty_oudouble': received_qty,
                'invoiced_qty_oudouble': received_qty if header['invoice_status'] == 'RECEIVED' else 0,
                'returned_qty_oudouble': 0,
                'in_receipt_qty_sudouble': 0,
                'received_qty_sudouble': received_qty,
                'returned_qty_sudouble': 0,
                'inspect_comment1': '',
                'completed': 'Y' if header['order_status'] == 'COMPLETED' else 'N',
                'order_status': header['order_status'],
                'price_status': 'CONFIRMED',
                'requisition_linebigint': line_num,
                'ordered_product_code': random.choice(product_codes)
            }
            lines.append(line)
    
    # Write headers
    output_file = output_dir / 'purchase_order_header.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers[0].keys())
        writer.writeheader()
        writer.writerows(headers)
    print(f"✓ Created {output_file}")
    
    # Write lines
    output_file = output_dir / 'purchase_order_line.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=lines[0].keys())
        writer.writeheader()
        writer.writerows(lines)
    print(f"✓ Created {output_file} with {len(lines)} lines")

def main():
    parser = argparse.ArgumentParser(description='Generate sample supply chain data')
    parser.add_argument('--size', choices=['small', 'medium', 'large'], default='medium',
                       help='Data size (small/medium/large)')
    parser.add_argument('--output', default='data/', help='Output directory')
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    # Get size configuration
    config = SIZES[args.size]
    
    print(f"\n{'='*60}")
    print(f"Generating {args.size.upper()} dataset")
    print(f"{'='*60}\n")
    
    # Generate data
    product_codes = generate_products(config['products'], output_dir)
    generate_warehouse_product(product_codes, config['warehouses'], output_dir)
    generate_sales_orders(config['sales_orders'], product_codes, 
                          config['warehouses'], config['customers'], output_dir)
    generate_purchase_orders(config['purchase_orders'], product_codes, 
                            config['suppliers'], output_dir)
    
    print(f"\n{'='*60}")
    print(f"✓ Sample data generated successfully!")
    print(f"{'='*60}\n")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"\nNext steps:")
    print(f"1. Review the generated CSV files")
    print(f"2. Upload to S3: ./scripts/upload_data_to_s3.sh")
    print(f"3. Create Glue tables: ./scripts/create_glue_tables.sh")
    print(f"4. Verify with Athena queries")

if __name__ == '__main__':
    main()
