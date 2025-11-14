"""Lambda function for inventory optimization tools"""
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any

athena_client = boto3.client('athena')
ATHENA_DATABASE = "aws-gpl-cog-sc-db"
ATHENA_OUTPUT = "s3://your-athena-results-bucket/"

def execute_athena_query(query: str) -> list:
    """Execute Athena query and return results"""
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': ATHENA_DATABASE},
        ResultConfiguration={'OutputLocation': ATHENA_OUTPUT}
    )
    
    query_id = response['QueryExecutionId']
    
    # Wait for completion
    import time
    for _ in range(30):
        status = athena_client.get_query_execution(QueryExecutionId=query_id)
        state = status['QueryExecution']['Status']['State']
        if state == 'SUCCEEDED':
            break
        elif state in ['FAILED', 'CANCELLED']:
            return []
        time.sleep(1)
    
    # Get results
    results = athena_client.get_query_results(QueryExecutionId=query_id, MaxResults=1000)
    rows = results['ResultSet']['Rows']
    
    if len(rows) <= 1:
        return []
    
    # Parse results
    columns = [col['VarCharValue'] for col in rows[0]['Data']]
    data = []
    for row in rows[1:]:
        row_data = {columns[i]: cell.get('VarCharValue', '') for i, cell in enumerate(row['Data'])}
        data.append(row_data)
    
    return data

def calculate_reorder_points(warehouse_code: str, product_codes: list = None) -> Dict[str, Any]:
    """Calculate optimal reorder points"""
    product_filter = ""
    if product_codes:
        codes = "','".join(product_codes)
        product_filter = f"AND wp.product_code IN ('{codes}')"
    
    query = f"""
    SELECT 
        wp.product_code,
        p.short_name,
        wp.physical_stock_su,
        wp.minimum_stock_su,
        wp.maximum_stock_su,
        wp.lead_time_daysbigint as lead_time_days,
        COALESCE(sales.avg_daily_sales, 0) as avg_daily_sales,
        CAST(COALESCE(sales.avg_daily_sales, 0) * wp.lead_time_daysbigint * 1.5 AS INTEGER) as suggested_reorder_point,
        CASE 
            WHEN wp.physical_stock_su < COALESCE(sales.avg_daily_sales, 0) * wp.lead_time_daysbigint * 1.5 
            THEN 'REORDER_NOW'
            WHEN wp.physical_stock_su < wp.minimum_stock_su 
            THEN 'BELOW_MIN'
            ELSE 'OK'
        END as status
    FROM {ATHENA_DATABASE}.warehouse_product wp
    JOIN {ATHENA_DATABASE}.product p ON wp.product_code = p.product_code
    LEFT JOIN (
        SELECT 
            product_code,
            AVG(qty_seludouble) / 30.0 as avg_daily_sales
        FROM {ATHENA_DATABASE}.sales_order_line
        WHERE order_line_status = 'COMPLETED'
        GROUP BY product_code
    ) sales ON wp.product_code = sales.product_code
    WHERE wp.warehouse_code = '{warehouse_code}'
    {product_filter}
    ORDER BY status DESC, avg_daily_sales DESC
    LIMIT 100
    """
    
    results = execute_athena_query(query)
    
    return {
        "warehouse_code": warehouse_code,
        "reorder_recommendations": results,
        "total_products": len(results),
        "products_needing_reorder": len([r for r in results if r.get('status') in ['REORDER_NOW', 'BELOW_MIN']])
    }

def forecast_demand(product_code: str, warehouse_code: str, forecast_days: int = 30) -> Dict[str, Any]:
    """Forecast product demand"""
    query = f"""
    SELECT 
        product_code,
        COUNT(*) as order_count,
        SUM(qty_seludouble) as total_quantity,
        AVG(qty_seludouble) as avg_order_quantity,
        MIN(required_delivery_date) as first_order_date,
        MAX(required_delivery_date) as last_order_date
    FROM {ATHENA_DATABASE}.sales_order_line sol
    JOIN {ATHENA_DATABASE}.sales_order_header soh 
        ON sol.sales_order_prefix = soh.sales_order_prefix 
        AND sol.sales_order_number = soh.sales_order_number
    WHERE sol.product_code = '{product_code}'
        AND soh.warehouse_code = '{warehouse_code}'
        AND sol.order_line_status IN ('COMPLETED', 'SHIPPED')
    GROUP BY product_code
    """
    
    results = execute_athena_query(query)
    
    if not results:
        return {
            "product_code": product_code,
            "forecast_days": forecast_days,
            "forecasted_demand": 0,
            "confidence": "low",
            "message": "Insufficient historical data"
        }
    
    data = results[0]
    avg_daily_demand = float(data.get('total_quantity', 0)) / 90.0  # Assume 90 days of data
    forecasted_demand = avg_daily_demand * forecast_days
    
    return {
        "product_code": product_code,
        "warehouse_code": warehouse_code,
        "forecast_days": forecast_days,
        "forecasted_demand": round(forecasted_demand, 2),
        "avg_daily_demand": round(avg_daily_demand, 2),
        "historical_orders": int(data.get('order_count', 0)),
        "confidence": "medium" if int(data.get('order_count', 0)) > 10 else "low"
    }

def identify_stockout_risks(warehouse_code: str, days_ahead: int = 7) -> Dict[str, Any]:
    """Identify products at risk of stockout"""
    query = f"""
    SELECT 
        wp.product_code,
        p.short_name,
        wp.physical_stock_su,
        wp.free_stock_su,
        wp.allocated_stock_su,
        COALESCE(sales.avg_daily_sales, 0) as avg_daily_sales,
        CAST(wp.free_stock_su / NULLIF(sales.avg_daily_sales, 0) AS INTEGER) as days_of_stock,
        CASE 
            WHEN wp.free_stock_su <= 0 THEN 'OUT_OF_STOCK'
            WHEN wp.free_stock_su / NULLIF(sales.avg_daily_sales, 0) < {days_ahead} THEN 'HIGH_RISK'
            WHEN wp.free_stock_su < wp.minimum_stock_su THEN 'MEDIUM_RISK'
            ELSE 'LOW_RISK'
        END as risk_level
    FROM {ATHENA_DATABASE}.warehouse_product wp
    JOIN {ATHENA_DATABASE}.product p ON wp.product_code = p.product_code
    LEFT JOIN (
        SELECT 
            product_code,
            AVG(qty_seludouble) / 30.0 as avg_daily_sales
        FROM {ATHENA_DATABASE}.sales_order_line
        WHERE order_line_status IN ('COMPLETED', 'SHIPPED')
        GROUP BY product_code
    ) sales ON wp.product_code = sales.product_code
    WHERE wp.warehouse_code = '{warehouse_code}'
        AND (wp.free_stock_su <= 0 
             OR wp.free_stock_su / NULLIF(sales.avg_daily_sales, 0) < {days_ahead}
             OR wp.free_stock_su < wp.minimum_stock_su)
    ORDER BY risk_level, days_of_stock
    LIMIT 50
    """
    
    results = execute_athena_query(query)
    
    return {
        "warehouse_code": warehouse_code,
        "days_ahead": days_ahead,
        "at_risk_products": results,
        "total_at_risk": len(results),
        "out_of_stock": len([r for r in results if r.get('risk_level') == 'OUT_OF_STOCK']),
        "high_risk": len([r for r in results if r.get('risk_level') == 'HIGH_RISK'])
    }

def optimize_stock_levels(warehouse_code: str, target_service_level: float = 95.0) -> Dict[str, Any]:
    """Optimize stock levels"""
    # Simplified optimization - in production, use more sophisticated algorithms
    query = f"""
    SELECT 
        wp.product_code,
        p.short_name,
        wp.physical_stock_su as current_stock,
        wp.minimum_stock_su as current_min,
        wp.maximum_stock_su as current_max,
        COALESCE(sales.avg_daily_sales, 0) as avg_daily_sales,
        COALESCE(sales.std_dev_sales, 0) as std_dev_sales,
        wp.lead_time_daysbigint as lead_time,
        wp.standard_cost
    FROM {ATHENA_DATABASE}.warehouse_product wp
    JOIN {ATHENA_DATABASE}.product p ON wp.product_code = p.product_code
    LEFT JOIN (
        SELECT 
            product_code,
            AVG(qty_seludouble) / 30.0 as avg_daily_sales,
            STDDEV(qty_seludouble) as std_dev_sales
        FROM {ATHENA_DATABASE}.sales_order_line
        WHERE order_line_status IN ('COMPLETED', 'SHIPPED')
        GROUP BY product_code
    ) sales ON wp.product_code = sales.product_code
    WHERE wp.warehouse_code = '{warehouse_code}'
    LIMIT 100
    """
    
    results = execute_athena_query(query)
    
    # Calculate optimal levels (simplified)
    optimized = []
    for item in results:
        avg_sales = float(item.get('avg_daily_sales', 0))
        lead_time = int(item.get('lead_time', 7))
        
        # Safety stock = Z-score * std_dev * sqrt(lead_time)
        # For 95% service level, Z ≈ 1.65
        safety_stock = 1.65 * float(item.get('std_dev_sales', avg_sales * 0.3)) * (lead_time ** 0.5)
        optimal_min = int(avg_sales * lead_time + safety_stock)
        optimal_max = int(optimal_min * 2)
        
        optimized.append({
            "product_code": item['product_code'],
            "short_name": item['short_name'],
            "current_min": item['current_min'],
            "current_max": item['current_max'],
            "suggested_min": optimal_min,
            "suggested_max": optimal_max,
            "potential_savings": abs(int(item['current_stock']) - optimal_min) * float(item.get('standard_cost', 0))
        })
    
    return {
        "warehouse_code": warehouse_code,
        "target_service_level": target_service_level,
        "optimized_levels": optimized,
        "total_products": len(optimized)
    }

def lambda_handler(event, context):
    """Lambda handler"""
    tool_name = event.get('tool_name')
    tool_input = event.get('input', {})
    
    try:
        if tool_name == 'calculate_reorder_points':
            result = calculate_reorder_points(
                tool_input['warehouse_code'],
                tool_input.get('product_codes')
            )
        elif tool_name == 'forecast_demand':
            result = forecast_demand(
                tool_input['product_code'],
                tool_input['warehouse_code'],
                tool_input.get('forecast_days', 30)
            )
        elif tool_name == 'identify_stockout_risks':
            result = identify_stockout_risks(
                tool_input['warehouse_code'],
                tool_input.get('days_ahead', 7)
            )
        elif tool_name == 'optimize_stock_levels':
            result = optimize_stock_levels(
                tool_input['warehouse_code'],
                tool_input.get('target_service_level', 95.0)
            )
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        return result
    except Exception as e:
        return {"error": str(e)}
