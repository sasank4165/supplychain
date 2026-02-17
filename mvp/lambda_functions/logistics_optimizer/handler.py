"""
Lambda handler for Logistics Optimizer agent.

Provides logistics optimization tools for Field Engineers:
- optimize_delivery_route: Optimize delivery routes for orders
- check_fulfillment_status: Get detailed order fulfillment status
- identify_delayed_orders: Find orders past their delivery date
- calculate_warehouse_capacity: Calculate warehouse capacity utilization
"""

import json
import os
import boto3
from typing import Dict, Any, List
from datetime import datetime, timedelta


# Initialize Redshift Data API client
redshift_client = boto3.client('redshift-data')

# Get configuration from environment variables
WORKGROUP_NAME = os.environ.get('REDSHIFT_WORKGROUP_NAME', 'supply-chain-mvp')
DATABASE = os.environ.get('REDSHIFT_DATABASE', 'supply_chain_db')


def lambda_handler(event, context):
    """
    Handle logistics optimization requests.
    
    Expected event format:
    {
        "action": "optimize_delivery_route" | "check_fulfillment_status" | "identify_delayed_orders" | "calculate_warehouse_capacity",
        "order_ids": ["SO-001", "SO-002"],
        "order_id": "SO-001",
        "warehouse_code": "WH-001",
        "days": 7
    }
    """
    try:
        action = event.get('action')
        
        if not action:
            return error_response("Missing 'action' parameter")
        
        # Route to appropriate handler
        if action == 'optimize_delivery_route':
            return optimize_delivery_route(event)
        elif action == 'check_fulfillment_status':
            return check_fulfillment_status(event)
        elif action == 'identify_delayed_orders':
            return identify_delayed_orders(event)
        elif action == 'calculate_warehouse_capacity':
            return calculate_warehouse_capacity(event)
        else:
            return error_response(f"Unknown action: {action}")
    
    except Exception as e:
        return error_response(f"Error processing request: {str(e)}")


def optimize_delivery_route(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize delivery route for a set of orders.
    
    Groups orders by delivery area and prioritizes by delivery date.
    """
    order_ids = event.get('order_ids', [])
    warehouse_code = event.get('warehouse_code')
    
    if not order_ids:
        return error_response("Missing order_ids")
    
    if not warehouse_code:
        return error_response("Missing warehouse_code")
    
    try:
        # Get order details
        order_ids_str = "', '".join(order_ids)
        sql = f"""
        SELECT 
            soh.sales_order_prefix || '-' || soh.sales_order_number as order_id,
            soh.customer_name,
            soh.delivery_address,
            soh.delivery_area,
            soh.delivery_date,
            soh.status,
            COUNT(sol.sales_order_line) as line_count,
            SUM(sol.order_quantity) as total_quantity
        FROM sales_order_header soh
        LEFT JOIN sales_order_line sol ON soh.sales_order_prefix = sol.sales_order_prefix 
            AND soh.sales_order_number = sol.sales_order_number
        WHERE soh.sales_order_prefix || '-' || soh.sales_order_number IN ('{order_ids_str}')
        AND soh.warehouse_code = '{warehouse_code}'
        GROUP BY soh.sales_order_prefix, soh.sales_order_number, soh.customer_name, 
                 soh.delivery_address, soh.delivery_area, soh.delivery_date, soh.status
        ORDER BY soh.delivery_date ASC, soh.delivery_area ASC
        """
        
        results = execute_query(sql)
        
        if not results:
            return error_response(f"No orders found for warehouse {warehouse_code}")
        
        # Group orders by delivery area
        area_groups = {}
        for row in results:
            area = row['delivery_area'] or 'Unknown'
            if area not in area_groups:
                area_groups[area] = []
            
            area_groups[area].append({
                'order_id': row['order_id'],
                'customer_name': row['customer_name'],
                'delivery_address': row['delivery_address'],
                'delivery_date': row['delivery_date'],
                'status': row['status'],
                'line_count': int(row['line_count']) if row['line_count'] else 0,
                'total_quantity': int(row['total_quantity']) if row['total_quantity'] else 0
            })
        
        # Create optimized route (by area, then by delivery date)
        optimized_sequence = []
        route_summary = []
        
        # Sort areas by number of orders (deliver to areas with most orders first)
        sorted_areas = sorted(area_groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        for area, orders in sorted_areas:
            # Sort orders within area by delivery date
            orders.sort(key=lambda o: o['delivery_date'] if o['delivery_date'] else '9999-12-31')
            
            route_summary.append({
                'delivery_area': area,
                'order_count': len(orders),
                'orders': [o['order_id'] for o in orders]
            })
            
            optimized_sequence.extend([o['order_id'] for o in orders])
        
        # Estimate route metrics
        total_stops = len(results)
        avg_time_per_stop = 0.5  # hours
        estimated_time_hours = total_stops * avg_time_per_stop
        
        return success_response({
            'warehouse_code': warehouse_code,
            'total_orders': len(results),
            'delivery_areas': len(area_groups),
            'optimized_sequence': optimized_sequence,
            'route_summary': route_summary,
            'estimated_time_hours': round(estimated_time_hours, 2),
            'optimization_method': 'Area grouping with date prioritization'
        })
    
    except Exception as e:
        return error_response(f"Error optimizing delivery route: {str(e)}")


def check_fulfillment_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get detailed fulfillment status for an order.
    """
    order_id = event.get('order_id')
    
    if not order_id:
        return error_response("Missing order_id")
    
    try:
        # Parse order ID (format: PREFIX-NUMBER)
        parts = order_id.split('-')
        if len(parts) != 2:
            return error_response(f"Invalid order_id format: {order_id}. Expected format: PREFIX-NUMBER")
        
        prefix, number = parts
        
        # Get order header
        header_sql = f"""
        SELECT 
            sales_order_prefix || '-' || sales_order_number as order_id,
            order_date,
            customer_code,
            customer_name,
            warehouse_code,
            delivery_address,
            delivery_area,
            delivery_date,
            status
        FROM sales_order_header
        WHERE sales_order_prefix = '{prefix}'
        AND sales_order_number = '{number}'
        """
        
        header_result = execute_query(header_sql)
        
        if not header_result:
            return error_response(f"Order {order_id} not found")
        
        header = header_result[0]
        
        # Get order lines
        lines_sql = f"""
        SELECT 
            sol.sales_order_line,
            sol.product_code,
            p.product_name,
            sol.order_quantity,
            sol.fulfilled_quantity,
            sol.unit_price,
            sol.line_total,
            sol.fulfillment_status
        FROM sales_order_line sol
        JOIN product p ON sol.product_code = p.product_code
        WHERE sol.sales_order_prefix = '{prefix}'
        AND sol.sales_order_number = '{number}'
        ORDER BY sol.sales_order_line
        """
        
        lines_result = execute_query(lines_sql)
        
        # Calculate fulfillment metrics
        total_lines = len(lines_result)
        fully_fulfilled_lines = sum(1 for line in lines_result if line['fulfillment_status'] == 'Fulfilled')
        total_ordered = sum(int(line['order_quantity']) for line in lines_result)
        total_fulfilled = sum(int(line['fulfilled_quantity'] or 0) for line in lines_result)
        
        fulfillment_percentage = (total_fulfilled / total_ordered * 100) if total_ordered > 0 else 0
        
        # Format line items
        line_items = []
        for line in lines_result:
            line_items.append({
                'line_number': int(line['sales_order_line']),
                'product_code': line['product_code'],
                'product_name': line['product_name'],
                'order_quantity': int(line['order_quantity']),
                'fulfilled_quantity': int(line['fulfilled_quantity'] or 0),
                'unit_price': float(line['unit_price']) if line['unit_price'] else 0.0,
                'line_total': float(line['line_total']) if line['line_total'] else 0.0,
                'fulfillment_status': line['fulfillment_status']
            })
        
        return success_response({
            'order_id': order_id,
            'order_date': header['order_date'],
            'customer_code': header['customer_code'],
            'customer_name': header['customer_name'],
            'warehouse_code': header['warehouse_code'],
            'delivery_address': header['delivery_address'],
            'delivery_area': header['delivery_area'],
            'delivery_date': header['delivery_date'],
            'status': header['status'],
            'total_lines': total_lines,
            'fully_fulfilled_lines': fully_fulfilled_lines,
            'total_ordered': total_ordered,
            'total_fulfilled': total_fulfilled,
            'fulfillment_percentage': round(fulfillment_percentage, 2),
            'line_items': line_items
        })
    
    except Exception as e:
        return error_response(f"Error checking fulfillment status: {str(e)}")


def identify_delayed_orders(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify orders that are delayed (past delivery date and not delivered).
    """
    warehouse_code = event.get('warehouse_code')
    days = event.get('days', 7)  # Default: look back 7 days
    
    if not warehouse_code:
        return error_response("Missing warehouse_code")
    
    try:
        sql = f"""
        SELECT 
            soh.sales_order_prefix || '-' || soh.sales_order_number as order_id,
            soh.order_date,
            soh.customer_name,
            soh.delivery_address,
            soh.delivery_area,
            soh.delivery_date,
            soh.status,
            CURRENT_DATE - soh.delivery_date as days_delayed,
            COUNT(sol.sales_order_line) as line_count,
            SUM(CASE WHEN sol.fulfillment_status = 'Fulfilled' THEN 1 ELSE 0 END) as fulfilled_lines
        FROM sales_order_header soh
        LEFT JOIN sales_order_line sol ON soh.sales_order_prefix = sol.sales_order_prefix 
            AND soh.sales_order_number = sol.sales_order_number
        WHERE soh.warehouse_code = '{warehouse_code}'
        AND soh.delivery_date < CURRENT_DATE
        AND soh.status != 'Delivered'
        AND soh.delivery_date >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY soh.sales_order_prefix, soh.sales_order_number, soh.order_date, 
                 soh.customer_name, soh.delivery_address, soh.delivery_area, 
                 soh.delivery_date, soh.status
        ORDER BY days_delayed DESC, soh.delivery_date ASC
        LIMIT 100
        """
        
        results = execute_query(sql)
        
        delayed_orders = []
        for row in results:
            days_delayed = int(row['days_delayed']) if row['days_delayed'] else 0
            line_count = int(row['line_count']) if row['line_count'] else 0
            fulfilled_lines = int(row['fulfilled_lines']) if row['fulfilled_lines'] else 0
            
            # Determine priority
            if days_delayed > 5:
                priority = 'Critical'
            elif days_delayed > 2:
                priority = 'High'
            else:
                priority = 'Medium'
            
            delayed_orders.append({
                'order_id': row['order_id'],
                'order_date': row['order_date'],
                'customer_name': row['customer_name'],
                'delivery_address': row['delivery_address'],
                'delivery_area': row['delivery_area'],
                'delivery_date': row['delivery_date'],
                'status': row['status'],
                'days_delayed': days_delayed,
                'line_count': line_count,
                'fulfilled_lines': fulfilled_lines,
                'priority': priority
            })
        
        return success_response({
            'warehouse_code': warehouse_code,
            'lookback_days': days,
            'delayed_count': len(delayed_orders),
            'delayed_orders': delayed_orders
        })
    
    except Exception as e:
        return error_response(f"Error identifying delayed orders: {str(e)}")


def calculate_warehouse_capacity(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate warehouse capacity utilization based on inventory levels.
    """
    warehouse_code = event.get('warehouse_code')
    
    if not warehouse_code:
        return error_response("Missing warehouse_code")
    
    try:
        # Get inventory statistics
        sql = f"""
        SELECT 
            COUNT(*) as total_products,
            SUM(current_stock) as total_current_stock,
            SUM(maximum_stock) as total_maximum_stock,
            SUM(minimum_stock) as total_minimum_stock,
            AVG(current_stock::float / NULLIF(maximum_stock, 0) * 100) as avg_utilization_pct,
            SUM(CASE WHEN current_stock >= maximum_stock THEN 1 ELSE 0 END) as at_capacity_count,
            SUM(CASE WHEN current_stock < minimum_stock THEN 1 ELSE 0 END) as below_minimum_count
        FROM warehouse_product
        WHERE warehouse_code = '{warehouse_code}'
        AND maximum_stock > 0
        """
        
        result = execute_query(sql)
        
        if not result:
            return error_response(f"No inventory data found for warehouse {warehouse_code}")
        
        row = result[0]
        
        total_products = int(row['total_products']) if row['total_products'] else 0
        total_current = int(row['total_current_stock']) if row['total_current_stock'] else 0
        total_maximum = int(row['total_maximum_stock']) if row['total_maximum_stock'] else 0
        total_minimum = int(row['total_minimum_stock']) if row['total_minimum_stock'] else 0
        avg_utilization = float(row['avg_utilization_pct']) if row['avg_utilization_pct'] else 0.0
        at_capacity = int(row['at_capacity_count']) if row['at_capacity_count'] else 0
        below_minimum = int(row['below_minimum_count']) if row['below_minimum_count'] else 0
        
        # Calculate overall capacity
        overall_capacity_pct = (total_current / total_maximum * 100) if total_maximum > 0 else 0
        
        # Determine capacity status
        if overall_capacity_pct > 90:
            capacity_status = 'Critical - Near Full'
        elif overall_capacity_pct > 75:
            capacity_status = 'High - Limited Space'
        elif overall_capacity_pct > 50:
            capacity_status = 'Moderate - Good Space'
        else:
            capacity_status = 'Low - Ample Space'
        
        # Get top product groups by volume
        groups_sql = f"""
        SELECT 
            p.product_group,
            COUNT(*) as product_count,
            SUM(wp.current_stock) as total_stock
        FROM warehouse_product wp
        JOIN product p ON wp.product_code = p.product_code
        WHERE wp.warehouse_code = '{warehouse_code}'
        GROUP BY p.product_group
        ORDER BY total_stock DESC
        LIMIT 10
        """
        
        groups_result = execute_query(groups_sql)
        
        product_groups = []
        for group_row in groups_result:
            product_groups.append({
                'product_group': group_row['product_group'],
                'product_count': int(group_row['product_count']) if group_row['product_count'] else 0,
                'total_stock': int(group_row['total_stock']) if group_row['total_stock'] else 0
            })
        
        return success_response({
            'warehouse_code': warehouse_code,
            'total_products': total_products,
            'total_current_stock': total_current,
            'total_maximum_stock': total_maximum,
            'total_minimum_stock': total_minimum,
            'overall_capacity_percentage': round(overall_capacity_pct, 2),
            'avg_product_utilization_percentage': round(avg_utilization, 2),
            'capacity_status': capacity_status,
            'products_at_capacity': at_capacity,
            'products_below_minimum': below_minimum,
            'top_product_groups': product_groups
        })
    
    except Exception as e:
        return error_response(f"Error calculating warehouse capacity: {str(e)}")


def execute_query(sql: str) -> List[Dict[str, Any]]:
    """
    Execute SQL query against Redshift and return results.
    """
    # Submit query
    response = redshift_client.execute_statement(
        WorkgroupName=WORKGROUP_NAME,
        Database=DATABASE,
        Sql=sql
    )
    
    query_id = response['Id']
    
    # Wait for query to complete
    import time
    max_wait = 30  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status_response = redshift_client.describe_statement(Id=query_id)
        status = status_response['Status']
        
        if status == 'FINISHED':
            break
        elif status in ['FAILED', 'ABORTED']:
            error = status_response.get('Error', 'Unknown error')
            raise Exception(f"Query failed: {error}")
        
        time.sleep(0.5)
    
    # Get results
    result_response = redshift_client.get_statement_result(Id=query_id)
    
    # Parse results
    columns = [col['name'] for col in result_response.get('ColumnMetadata', [])]
    rows = []
    
    for record in result_response.get('Records', []):
        row = {}
        for i, field in enumerate(record):
            col_name = columns[i]
            # Extract value from field
            if 'stringValue' in field:
                row[col_name] = field['stringValue']
            elif 'longValue' in field:
                row[col_name] = field['longValue']
            elif 'doubleValue' in field:
                row[col_name] = field['doubleValue']
            elif 'booleanValue' in field:
                row[col_name] = field['booleanValue']
            elif 'isNull' in field and field['isNull']:
                row[col_name] = None
            else:
                row[col_name] = str(field)
        rows.append(row)
    
    return rows


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return success response."""
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'data': data
        })
    }


def error_response(message: str) -> Dict[str, Any]:
    """Return error response."""
    return {
        'statusCode': 400,
        'body': json.dumps({
            'success': False,
            'error': message
        })
    }
