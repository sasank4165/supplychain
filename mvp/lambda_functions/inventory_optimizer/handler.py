"""
Lambda handler for Inventory Optimizer agent.

Provides inventory optimization tools for Warehouse Managers:
- calculate_reorder_point: Calculate optimal reorder point for a product
- identify_low_stock: Find products below stock threshold
- forecast_demand: Forecast future demand for a product
- identify_stockout_risk: Identify products at risk of stockout
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
    Handle inventory optimization requests.
    
    Expected event format:
    {
        "action": "calculate_reorder_point" | "identify_low_stock" | "forecast_demand" | "identify_stockout_risk",
        "product_code": "string",
        "warehouse_code": "string",
        "threshold": float,
        "days": int
    }
    """
    try:
        action = event.get('action')
        
        if not action:
            return error_response("Missing 'action' parameter")
        
        # Route to appropriate handler
        if action == 'calculate_reorder_point':
            return calculate_reorder_point(event)
        elif action == 'identify_low_stock':
            return identify_low_stock(event)
        elif action == 'forecast_demand':
            return forecast_demand(event)
        elif action == 'identify_stockout_risk':
            return identify_stockout_risk(event)
        else:
            return error_response(f"Unknown action: {action}")
    
    except Exception as e:
        return error_response(f"Error processing request: {str(e)}")


def calculate_reorder_point(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate optimal reorder point for a product.
    
    Formula: Reorder Point = (Avg Daily Demand × Lead Time) + Safety Stock
    """
    product_code = event.get('product_code')
    warehouse_code = event.get('warehouse_code')
    
    if not product_code or not warehouse_code:
        return error_response("Missing product_code or warehouse_code")
    
    try:
        # Get product and warehouse data
        sql = f"""
        SELECT 
            wp.current_stock,
            wp.minimum_stock,
            wp.reorder_point,
            wp.lead_time_days,
            p.product_name,
            p.product_group
        FROM warehouse_product wp
        JOIN product p ON wp.product_code = p.product_code
        WHERE wp.product_code = '{product_code}'
        AND wp.warehouse_code = '{warehouse_code}'
        """
        
        result = execute_query(sql)
        
        if not result:
            return error_response(f"Product {product_code} not found in warehouse {warehouse_code}")
        
        row = result[0]
        
        # Calculate average daily demand from recent sales
        demand_sql = f"""
        SELECT 
            COALESCE(SUM(sol.order_quantity) / 30.0, 0) as avg_daily_demand
        FROM sales_order_line sol
        JOIN sales_order_header soh ON sol.sales_order_prefix = soh.sales_order_prefix 
            AND sol.sales_order_number = soh.sales_order_number
        WHERE sol.product_code = '{product_code}'
        AND soh.warehouse_code = '{warehouse_code}'
        AND soh.order_date >= CURRENT_DATE - INTERVAL '30 days'
        """
        
        demand_result = execute_query(demand_sql)
        avg_daily_demand = float(demand_result[0]['avg_daily_demand']) if demand_result else 0.0
        
        # Calculate safety stock (20% of lead time demand)
        lead_time_days = int(row['lead_time_days']) if row['lead_time_days'] else 7
        safety_stock = avg_daily_demand * lead_time_days * 0.2
        
        # Calculate reorder point
        calculated_reorder_point = (avg_daily_demand * lead_time_days) + safety_stock
        
        return success_response({
            'product_code': product_code,
            'product_name': row['product_name'],
            'warehouse_code': warehouse_code,
            'current_stock': int(row['current_stock']) if row['current_stock'] else 0,
            'minimum_stock': int(row['minimum_stock']) if row['minimum_stock'] else 0,
            'current_reorder_point': int(row['reorder_point']) if row['reorder_point'] else 0,
            'calculated_reorder_point': round(calculated_reorder_point, 2),
            'avg_daily_demand': round(avg_daily_demand, 2),
            'lead_time_days': lead_time_days,
            'safety_stock': round(safety_stock, 2),
            'recommendation': 'Update reorder point' if abs(calculated_reorder_point - (row['reorder_point'] or 0)) > 10 else 'Current reorder point is optimal'
        })
    
    except Exception as e:
        return error_response(f"Error calculating reorder point: {str(e)}")


def identify_low_stock(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify products with low stock levels.
    
    Returns products where current_stock < minimum_stock * threshold
    """
    warehouse_code = event.get('warehouse_code')
    threshold = event.get('threshold', 1.0)  # Default: at or below minimum
    
    if not warehouse_code:
        return error_response("Missing warehouse_code")
    
    try:
        sql = f"""
        SELECT 
            wp.product_code,
            p.product_name,
            p.product_group,
            wp.current_stock,
            wp.minimum_stock,
            wp.reorder_point,
            wp.lead_time_days,
            ROUND((wp.current_stock::float / NULLIF(wp.minimum_stock, 0)) * 100, 2) as stock_percentage
        FROM warehouse_product wp
        JOIN product p ON wp.product_code = p.product_code
        WHERE wp.warehouse_code = '{warehouse_code}'
        AND wp.current_stock < (wp.minimum_stock * {threshold})
        AND wp.minimum_stock > 0
        ORDER BY stock_percentage ASC, wp.current_stock ASC
        LIMIT 50
        """
        
        results = execute_query(sql)
        
        low_stock_items = []
        for row in results:
            low_stock_items.append({
                'product_code': row['product_code'],
                'product_name': row['product_name'],
                'product_group': row['product_group'],
                'current_stock': int(row['current_stock']) if row['current_stock'] else 0,
                'minimum_stock': int(row['minimum_stock']) if row['minimum_stock'] else 0,
                'reorder_point': int(row['reorder_point']) if row['reorder_point'] else 0,
                'lead_time_days': int(row['lead_time_days']) if row['lead_time_days'] else 0,
                'stock_percentage': float(row['stock_percentage']) if row['stock_percentage'] else 0.0,
                'urgency': 'Critical' if float(row['stock_percentage'] or 0) < 50 else 'High'
            })
        
        return success_response({
            'warehouse_code': warehouse_code,
            'threshold': threshold,
            'low_stock_count': len(low_stock_items),
            'low_stock_items': low_stock_items
        })
    
    except Exception as e:
        return error_response(f"Error identifying low stock: {str(e)}")


def forecast_demand(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Forecast future demand for a product using historical sales data.
    
    Uses simple moving average method.
    """
    product_code = event.get('product_code')
    days = event.get('days', 30)  # Default: 30 days forecast
    
    if not product_code:
        return error_response("Missing product_code")
    
    try:
        # Get historical sales data (last 90 days)
        sql = f"""
        SELECT 
            soh.order_date,
            SUM(sol.order_quantity) as daily_quantity
        FROM sales_order_line sol
        JOIN sales_order_header soh ON sol.sales_order_prefix = soh.sales_order_prefix 
            AND sol.sales_order_number = soh.sales_order_number
        WHERE sol.product_code = '{product_code}'
        AND soh.order_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY soh.order_date
        ORDER BY soh.order_date DESC
        """
        
        results = execute_query(sql)
        
        if not results:
            return error_response(f"No historical sales data found for product {product_code}")
        
        # Calculate statistics
        daily_quantities = [float(row['daily_quantity']) for row in results]
        avg_daily_demand = sum(daily_quantities) / len(daily_quantities)
        max_daily_demand = max(daily_quantities)
        min_daily_demand = min(daily_quantities)
        
        # Simple forecast: use average daily demand
        forecasted_total = avg_daily_demand * days
        
        # Get product info
        product_sql = f"""
        SELECT product_name, product_group
        FROM product
        WHERE product_code = '{product_code}'
        """
        
        product_result = execute_query(product_sql)
        product_name = product_result[0]['product_name'] if product_result else 'Unknown'
        product_group = product_result[0]['product_group'] if product_result else 'Unknown'
        
        return success_response({
            'product_code': product_code,
            'product_name': product_name,
            'product_group': product_group,
            'forecast_days': days,
            'historical_days': len(daily_quantities),
            'avg_daily_demand': round(avg_daily_demand, 2),
            'max_daily_demand': round(max_daily_demand, 2),
            'min_daily_demand': round(min_daily_demand, 2),
            'forecasted_total_demand': round(forecasted_total, 2),
            'confidence': 'Medium' if len(daily_quantities) >= 30 else 'Low'
        })
    
    except Exception as e:
        return error_response(f"Error forecasting demand: {str(e)}")


def identify_stockout_risk(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify products at risk of stockout within specified days.
    
    Risk = current_stock < (avg_daily_demand * days)
    """
    warehouse_code = event.get('warehouse_code')
    days = event.get('days', 7)  # Default: 7 days lookout
    
    if not warehouse_code:
        return error_response("Missing warehouse_code")
    
    try:
        # Get products with current stock and recent demand
        sql = f"""
        WITH recent_demand AS (
            SELECT 
                sol.product_code,
                SUM(sol.order_quantity) / 30.0 as avg_daily_demand
            FROM sales_order_line sol
            JOIN sales_order_header soh ON sol.sales_order_prefix = soh.sales_order_prefix 
                AND sol.sales_order_number = soh.sales_order_number
            WHERE soh.warehouse_code = '{warehouse_code}'
            AND soh.order_date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY sol.product_code
        )
        SELECT 
            wp.product_code,
            p.product_name,
            p.product_group,
            wp.current_stock,
            wp.minimum_stock,
            wp.lead_time_days,
            COALESCE(rd.avg_daily_demand, 0) as avg_daily_demand,
            ROUND(wp.current_stock / NULLIF(rd.avg_daily_demand, 0), 2) as days_of_supply,
            ROUND(rd.avg_daily_demand * {days}, 2) as demand_forecast
        FROM warehouse_product wp
        JOIN product p ON wp.product_code = p.product_code
        LEFT JOIN recent_demand rd ON wp.product_code = rd.product_code
        WHERE wp.warehouse_code = '{warehouse_code}'
        AND rd.avg_daily_demand > 0
        AND wp.current_stock < (rd.avg_daily_demand * {days})
        ORDER BY days_of_supply ASC
        LIMIT 50
        """
        
        results = execute_query(sql)
        
        at_risk_items = []
        for row in results:
            days_of_supply = float(row['days_of_supply']) if row['days_of_supply'] else 0.0
            
            # Determine risk level
            if days_of_supply < 3:
                risk_level = 'Critical'
            elif days_of_supply < 5:
                risk_level = 'High'
            else:
                risk_level = 'Medium'
            
            at_risk_items.append({
                'product_code': row['product_code'],
                'product_name': row['product_name'],
                'product_group': row['product_group'],
                'current_stock': int(row['current_stock']) if row['current_stock'] else 0,
                'minimum_stock': int(row['minimum_stock']) if row['minimum_stock'] else 0,
                'avg_daily_demand': round(float(row['avg_daily_demand']), 2),
                'days_of_supply': round(days_of_supply, 2),
                'demand_forecast': round(float(row['demand_forecast']), 2),
                'lead_time_days': int(row['lead_time_days']) if row['lead_time_days'] else 0,
                'risk_level': risk_level
            })
        
        return success_response({
            'warehouse_code': warehouse_code,
            'lookout_days': days,
            'at_risk_count': len(at_risk_items),
            'at_risk_items': at_risk_items
        })
    
    except Exception as e:
        return error_response(f"Error identifying stockout risk: {str(e)}")


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
