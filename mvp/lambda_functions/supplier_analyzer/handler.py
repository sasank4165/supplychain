"""
Lambda handler for Supplier Analyzer agent.

Provides supplier analysis tools for Procurement Specialists:
- analyze_supplier_performance: Analyze supplier performance metrics
- compare_supplier_costs: Compare costs across suppliers
- identify_cost_savings: Identify cost savings opportunities
- analyze_purchase_trends: Analyze purchase order trends
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
    Handle supplier analysis requests.
    
    Expected event format:
    {
        "action": "analyze_supplier_performance" | "compare_supplier_costs" | "identify_cost_savings" | "analyze_purchase_trends",
        "supplier_code": "SUP-001",
        "days": 90,
        "product_group": "Electronics",
        "suppliers": ["SUP-001", "SUP-002"],
        "threshold_percent": 10.0,
        "group_by": "month"
    }
    """
    try:
        action = event.get('action')
        
        if not action:
            return error_response("Missing 'action' parameter")
        
        # Route to appropriate handler
        if action == 'analyze_supplier_performance':
            return analyze_supplier_performance(event)
        elif action == 'compare_supplier_costs':
            return compare_supplier_costs(event)
        elif action == 'identify_cost_savings':
            return identify_cost_savings(event)
        elif action == 'analyze_purchase_trends':
            return analyze_purchase_trends(event)
        else:
            return error_response(f"Unknown action: {action}")
    
    except Exception as e:
        return error_response(f"Error processing request: {str(e)}")


def analyze_supplier_performance(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze supplier performance metrics over a time period.
    
    Metrics include:
    - Fill rate (orders fulfilled completely)
    - On-time delivery rate
    - Total orders and value
    - Average order value
    """
    supplier_code = event.get('supplier_code')
    days = event.get('days', 90)  # Default: 90 days
    
    if not supplier_code:
        return error_response("Missing supplier_code")
    
    try:
        # Get supplier info
        supplier_sql = f"""
        SELECT DISTINCT supplier_name
        FROM product
        WHERE supplier_code = '{supplier_code}'
        LIMIT 1
        """
        
        supplier_result = execute_query(supplier_sql)
        
        if not supplier_result:
            return error_response(f"Supplier {supplier_code} not found")
        
        supplier_name = supplier_result[0]['supplier_name']
        
        # Get purchase order statistics
        po_sql = f"""
        SELECT 
            COUNT(DISTINCT poh.purchase_order_prefix || '-' || poh.purchase_order_number) as total_orders,
            SUM(pol.line_total) as total_value,
            AVG(pol.line_total) as avg_order_value,
            SUM(pol.order_quantity) as total_quantity_ordered,
            SUM(pol.received_quantity) as total_quantity_received,
            SUM(CASE WHEN pol.receipt_status = 'Received' THEN 1 ELSE 0 END) as fully_received_lines,
            COUNT(pol.purchase_order_line) as total_lines,
            SUM(CASE WHEN poh.actual_delivery_date <= poh.expected_delivery_date THEN 1 ELSE 0 END) as on_time_deliveries,
            COUNT(CASE WHEN poh.actual_delivery_date IS NOT NULL THEN 1 END) as completed_deliveries
        FROM purchase_order_header poh
        JOIN purchase_order_line pol ON poh.purchase_order_prefix = pol.purchase_order_prefix 
            AND poh.purchase_order_number = pol.purchase_order_number
        WHERE poh.supplier_code = '{supplier_code}'
        AND poh.order_date >= CURRENT_DATE - INTERVAL '{days} days'
        """
        
        po_result = execute_query(po_sql)
        
        if not po_result or not po_result[0]['total_orders']:
            return error_response(f"No purchase orders found for supplier {supplier_code} in the last {days} days")
        
        row = po_result[0]
        
        # Calculate metrics
        total_orders = int(row['total_orders']) if row['total_orders'] else 0
        total_value = float(row['total_value']) if row['total_value'] else 0.0
        avg_order_value = float(row['avg_order_value']) if row['avg_order_value'] else 0.0
        total_ordered = int(row['total_quantity_ordered']) if row['total_quantity_ordered'] else 0
        total_received = int(row['total_quantity_received']) if row['total_quantity_received'] else 0
        fully_received_lines = int(row['fully_received_lines']) if row['fully_received_lines'] else 0
        total_lines = int(row['total_lines']) if row['total_lines'] else 0
        on_time_deliveries = int(row['on_time_deliveries']) if row['on_time_deliveries'] else 0
        completed_deliveries = int(row['completed_deliveries']) if row['completed_deliveries'] else 0
        
        # Calculate rates
        fill_rate = (total_received / total_ordered * 100) if total_ordered > 0 else 0
        line_fill_rate = (fully_received_lines / total_lines * 100) if total_lines > 0 else 0
        on_time_rate = (on_time_deliveries / completed_deliveries * 100) if completed_deliveries > 0 else 0
        
        # Calculate supplier score (weighted)
        supplier_score = (
            (fill_rate / 100) * 0.3 +
            (on_time_rate / 100) * 0.3 +
            0.2 +  # Quality rate (placeholder - would need quality data)
            0.2    # Cost competitiveness (placeholder - would need market data)
        )
        
        # Get top products from this supplier
        products_sql = f"""
        SELECT 
            pol.product_code,
            p.product_name,
            p.product_group,
            SUM(pol.order_quantity) as total_ordered,
            SUM(pol.line_total) as total_spent
        FROM purchase_order_line pol
        JOIN purchase_order_header poh ON pol.purchase_order_prefix = poh.purchase_order_prefix 
            AND pol.purchase_order_number = poh.purchase_order_number
        JOIN product p ON pol.product_code = p.product_code
        WHERE poh.supplier_code = '{supplier_code}'
        AND poh.order_date >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY pol.product_code, p.product_name, p.product_group
        ORDER BY total_spent DESC
        LIMIT 10
        """
        
        products_result = execute_query(products_sql)
        
        top_products = []
        for prod_row in products_result:
            top_products.append({
                'product_code': prod_row['product_code'],
                'product_name': prod_row['product_name'],
                'product_group': prod_row['product_group'],
                'total_ordered': int(prod_row['total_ordered']) if prod_row['total_ordered'] else 0,
                'total_spent': round(float(prod_row['total_spent']), 2) if prod_row['total_spent'] else 0.0
            })
        
        # Determine performance rating
        if supplier_score >= 0.9:
            rating = 'Excellent'
        elif supplier_score >= 0.8:
            rating = 'Good'
        elif supplier_score >= 0.7:
            rating = 'Fair'
        else:
            rating = 'Needs Improvement'
        
        return success_response({
            'supplier_code': supplier_code,
            'supplier_name': supplier_name,
            'analysis_period_days': days,
            'total_orders': total_orders,
            'total_value': round(total_value, 2),
            'avg_order_value': round(avg_order_value, 2),
            'fill_rate_percentage': round(fill_rate, 2),
            'line_fill_rate_percentage': round(line_fill_rate, 2),
            'on_time_delivery_rate_percentage': round(on_time_rate, 2),
            'supplier_score': round(supplier_score, 3),
            'performance_rating': rating,
            'total_quantity_ordered': total_ordered,
            'total_quantity_received': total_received,
            'completed_deliveries': completed_deliveries,
            'on_time_deliveries': on_time_deliveries,
            'top_products': top_products
        })
    
    except Exception as e:
        return error_response(f"Error analyzing supplier performance: {str(e)}")


def compare_supplier_costs(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare costs across multiple suppliers for a product group.
    """
    product_group = event.get('product_group')
    suppliers = event.get('suppliers', [])
    
    if not product_group:
        return error_response("Missing product_group")
    
    try:
        # If no specific suppliers provided, get all suppliers for the product group
        if not suppliers:
            suppliers_sql = f"""
            SELECT DISTINCT p.supplier_code, p.supplier_name
            FROM product p
            WHERE p.product_group = '{product_group}'
            AND p.supplier_code IS NOT NULL
            """
            
            suppliers_result = execute_query(suppliers_sql)
            suppliers = [row['supplier_code'] for row in suppliers_result]
        
        if not suppliers:
            return error_response(f"No suppliers found for product group {product_group}")
        
        # Get cost comparison data
        supplier_comparisons = []
        
        for supplier_code in suppliers:
            sql = f"""
            SELECT 
                p.supplier_code,
                p.supplier_name,
                COUNT(DISTINCT p.product_code) as product_count,
                AVG(pol.unit_cost) as avg_unit_cost,
                SUM(pol.line_total) as total_spent,
                SUM(pol.order_quantity) as total_quantity
            FROM product p
            JOIN purchase_order_line pol ON p.product_code = pol.product_code
            JOIN purchase_order_header poh ON pol.purchase_order_prefix = poh.purchase_order_prefix 
                AND pol.purchase_order_number = poh.purchase_order_number
            WHERE p.product_group = '{product_group}'
            AND p.supplier_code = '{supplier_code}'
            AND poh.order_date >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY p.supplier_code, p.supplier_name
            """
            
            result = execute_query(sql)
            
            if result:
                row = result[0]
                supplier_comparisons.append({
                    'supplier_code': row['supplier_code'],
                    'supplier_name': row['supplier_name'],
                    'product_count': int(row['product_count']) if row['product_count'] else 0,
                    'avg_unit_cost': round(float(row['avg_unit_cost']), 2) if row['avg_unit_cost'] else 0.0,
                    'total_spent': round(float(row['total_spent']), 2) if row['total_spent'] else 0.0,
                    'total_quantity': int(row['total_quantity']) if row['total_quantity'] else 0
                })
        
        if not supplier_comparisons:
            return error_response(f"No cost data found for product group {product_group}")
        
        # Sort by average unit cost
        supplier_comparisons.sort(key=lambda x: x['avg_unit_cost'])
        
        # Identify lowest cost supplier
        lowest_cost_supplier = supplier_comparisons[0]
        
        # Calculate cost differences
        for supplier in supplier_comparisons:
            cost_diff = supplier['avg_unit_cost'] - lowest_cost_supplier['avg_unit_cost']
            cost_diff_pct = (cost_diff / lowest_cost_supplier['avg_unit_cost'] * 100) if lowest_cost_supplier['avg_unit_cost'] > 0 else 0
            supplier['cost_difference'] = round(cost_diff, 2)
            supplier['cost_difference_percentage'] = round(cost_diff_pct, 2)
            supplier['is_lowest_cost'] = (supplier['supplier_code'] == lowest_cost_supplier['supplier_code'])
        
        return success_response({
            'product_group': product_group,
            'suppliers_compared': len(supplier_comparisons),
            'lowest_cost_supplier': lowest_cost_supplier['supplier_code'],
            'lowest_avg_unit_cost': lowest_cost_supplier['avg_unit_cost'],
            'supplier_comparisons': supplier_comparisons
        })
    
    except Exception as e:
        return error_response(f"Error comparing supplier costs: {str(e)}")


def identify_cost_savings(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify cost savings opportunities by finding products with significant price differences.
    """
    threshold_percent = event.get('threshold_percent', 10.0)  # Default: 10% difference
    
    try:
        # Find products available from multiple suppliers with cost differences
        sql = f"""
        WITH supplier_costs AS (
            SELECT 
                p.product_code,
                p.product_name,
                p.product_group,
                p.supplier_code,
                p.supplier_name,
                AVG(pol.unit_cost) as avg_unit_cost,
                SUM(pol.order_quantity) as total_quantity
            FROM product p
            JOIN purchase_order_line pol ON p.product_code = pol.product_code
            JOIN purchase_order_header poh ON pol.purchase_order_prefix = poh.purchase_order_prefix 
                AND pol.purchase_order_number = poh.purchase_order_number
            WHERE poh.order_date >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY p.product_code, p.product_name, p.product_group, p.supplier_code, p.supplier_name
        ),
        cost_ranges AS (
            SELECT 
                product_code,
                product_name,
                product_group,
                MIN(avg_unit_cost) as min_cost,
                MAX(avg_unit_cost) as max_cost,
                COUNT(DISTINCT supplier_code) as supplier_count
            FROM supplier_costs
            GROUP BY product_code, product_name, product_group
            HAVING COUNT(DISTINCT supplier_code) > 1
        )
        SELECT 
            cr.product_code,
            cr.product_name,
            cr.product_group,
            cr.min_cost,
            cr.max_cost,
            cr.supplier_count,
            ROUND(((cr.max_cost - cr.min_cost) / cr.min_cost * 100), 2) as cost_difference_pct,
            ROUND(cr.max_cost - cr.min_cost, 2) as cost_difference
        FROM cost_ranges cr
        WHERE ((cr.max_cost - cr.min_cost) / cr.min_cost * 100) >= {threshold_percent}
        ORDER BY cost_difference_pct DESC
        LIMIT 50
        """
        
        results = execute_query(sql)
        
        savings_opportunities = []
        total_potential_savings = 0.0
        
        for row in results:
            cost_diff = float(row['cost_difference']) if row['cost_difference'] else 0.0
            cost_diff_pct = float(row['cost_difference_pct']) if row['cost_difference_pct'] else 0.0
            
            # Get current supplier and alternative
            suppliers_sql = f"""
            SELECT 
                p.supplier_code,
                p.supplier_name,
                AVG(pol.unit_cost) as avg_unit_cost
            FROM product p
            JOIN purchase_order_line pol ON p.product_code = pol.product_code
            JOIN purchase_order_header poh ON pol.purchase_order_prefix = poh.purchase_order_prefix 
                AND pol.purchase_order_number = poh.purchase_order_number
            WHERE p.product_code = '{row['product_code']}'
            AND poh.order_date >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY p.supplier_code, p.supplier_name
            ORDER BY avg_unit_cost ASC
            """
            
            suppliers_result = execute_query(suppliers_sql)
            
            if len(suppliers_result) >= 2:
                lowest_cost = suppliers_result[0]
                highest_cost = suppliers_result[-1]
                
                # Estimate annual savings (assuming current volume)
                volume_sql = f"""
                SELECT SUM(order_quantity) as annual_volume
                FROM purchase_order_line pol
                JOIN purchase_order_header poh ON pol.purchase_order_prefix = poh.purchase_order_prefix 
                    AND pol.purchase_order_number = poh.purchase_order_number
                WHERE pol.product_code = '{row['product_code']}'
                AND poh.order_date >= CURRENT_DATE - INTERVAL '365 days'
                """
                
                volume_result = execute_query(volume_sql)
                annual_volume = int(volume_result[0]['annual_volume']) if volume_result and volume_result[0]['annual_volume'] else 0
                
                potential_savings = cost_diff * annual_volume
                total_potential_savings += potential_savings
                
                savings_opportunities.append({
                    'product_code': row['product_code'],
                    'product_name': row['product_name'],
                    'product_group': row['product_group'],
                    'current_supplier': highest_cost['supplier_code'],
                    'current_supplier_name': highest_cost['supplier_name'],
                    'current_avg_cost': round(float(highest_cost['avg_unit_cost']), 2),
                    'alternative_supplier': lowest_cost['supplier_code'],
                    'alternative_supplier_name': lowest_cost['supplier_name'],
                    'alternative_avg_cost': round(float(lowest_cost['avg_unit_cost']), 2),
                    'cost_difference': round(cost_diff, 2),
                    'cost_difference_percentage': round(cost_diff_pct, 2),
                    'annual_volume': annual_volume,
                    'potential_annual_savings': round(potential_savings, 2)
                })
        
        return success_response({
            'threshold_percentage': threshold_percent,
            'opportunities_found': len(savings_opportunities),
            'total_potential_annual_savings': round(total_potential_savings, 2),
            'savings_opportunities': savings_opportunities
        })
    
    except Exception as e:
        return error_response(f"Error identifying cost savings: {str(e)}")


def analyze_purchase_trends(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze purchase order trends over time.
    """
    days = event.get('days', 90)  # Default: 90 days
    group_by = event.get('group_by', 'month')  # 'day', 'week', 'month'
    
    try:
        # Determine date truncation based on grouping
        if group_by == 'day':
            date_trunc = 'day'
            interval = '1 day'
        elif group_by == 'week':
            date_trunc = 'week'
            interval = '7 days'
        else:  # month
            date_trunc = 'month'
            interval = '30 days'
        
        # Get purchase trends
        sql = f"""
        SELECT 
            DATE_TRUNC('{date_trunc}', poh.order_date) as period,
            COUNT(DISTINCT poh.purchase_order_prefix || '-' || poh.purchase_order_number) as order_count,
            SUM(pol.line_total) as total_value,
            SUM(pol.order_quantity) as total_quantity,
            COUNT(DISTINCT poh.supplier_code) as unique_suppliers,
            AVG(pol.unit_cost) as avg_unit_cost
        FROM purchase_order_header poh
        JOIN purchase_order_line pol ON poh.purchase_order_prefix = pol.purchase_order_prefix 
            AND poh.purchase_order_number = pol.purchase_order_number
        WHERE poh.order_date >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY DATE_TRUNC('{date_trunc}', poh.order_date)
        ORDER BY period ASC
        """
        
        results = execute_query(sql)
        
        trends = []
        total_orders = 0
        total_value = 0.0
        
        for row in results:
            order_count = int(row['order_count']) if row['order_count'] else 0
            period_value = float(row['total_value']) if row['total_value'] else 0.0
            
            total_orders += order_count
            total_value += period_value
            
            trends.append({
                'period': row['period'],
                'order_count': order_count,
                'total_value': round(period_value, 2),
                'total_quantity': int(row['total_quantity']) if row['total_quantity'] else 0,
                'unique_suppliers': int(row['unique_suppliers']) if row['unique_suppliers'] else 0,
                'avg_unit_cost': round(float(row['avg_unit_cost']), 2) if row['avg_unit_cost'] else 0.0
            })
        
        # Get top suppliers by value
        suppliers_sql = f"""
        SELECT 
            poh.supplier_code,
            p.supplier_name,
            COUNT(DISTINCT poh.purchase_order_prefix || '-' || poh.purchase_order_number) as order_count,
            SUM(pol.line_total) as total_value
        FROM purchase_order_header poh
        JOIN purchase_order_line pol ON poh.purchase_order_prefix = pol.purchase_order_prefix 
            AND poh.purchase_order_number = pol.purchase_order_number
        JOIN product p ON pol.product_code = p.product_code
        WHERE poh.order_date >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY poh.supplier_code, p.supplier_name
        ORDER BY total_value DESC
        LIMIT 10
        """
        
        suppliers_result = execute_query(suppliers_sql)
        
        top_suppliers = []
        for supp_row in suppliers_result:
            top_suppliers.append({
                'supplier_code': supp_row['supplier_code'],
                'supplier_name': supp_row['supplier_name'],
                'order_count': int(supp_row['order_count']) if supp_row['order_count'] else 0,
                'total_value': round(float(supp_row['total_value']), 2) if supp_row['total_value'] else 0.0
            })
        
        # Get top product groups
        groups_sql = f"""
        SELECT 
            p.product_group,
            COUNT(DISTINCT poh.purchase_order_prefix || '-' || poh.purchase_order_number) as order_count,
            SUM(pol.line_total) as total_value,
            SUM(pol.order_quantity) as total_quantity
        FROM purchase_order_header poh
        JOIN purchase_order_line pol ON poh.purchase_order_prefix = pol.purchase_order_prefix 
            AND poh.purchase_order_number = pol.purchase_order_number
        JOIN product p ON pol.product_code = p.product_code
        WHERE poh.order_date >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY p.product_group
        ORDER BY total_value DESC
        LIMIT 10
        """
        
        groups_result = execute_query(groups_sql)
        
        top_product_groups = []
        for group_row in groups_result:
            top_product_groups.append({
                'product_group': group_row['product_group'],
                'order_count': int(group_row['order_count']) if group_row['order_count'] else 0,
                'total_value': round(float(group_row['total_value']), 2) if group_row['total_value'] else 0.0,
                'total_quantity': int(group_row['total_quantity']) if group_row['total_quantity'] else 0
            })
        
        return success_response({
            'analysis_period_days': days,
            'group_by': group_by,
            'total_orders': total_orders,
            'total_value': round(total_value, 2),
            'avg_order_value': round(total_value / total_orders, 2) if total_orders > 0 else 0.0,
            'trends': trends,
            'top_suppliers': top_suppliers,
            'top_product_groups': top_product_groups
        })
    
    except Exception as e:
        return error_response(f"Error analyzing purchase trends: {str(e)}")


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
