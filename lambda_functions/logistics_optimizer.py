"""Lambda function for logistics optimization tools"""
import json
import os
import boto3
from datetime import datetime

# Initialize clients
athena_client = boto3.client('athena')

# Load configuration from environment variables
ATHENA_DATABASE = os.environ.get('ATHENA_DATABASE')
ATHENA_OUTPUT = os.environ.get('ATHENA_OUTPUT_LOCATION')

if not ATHENA_DATABASE or not ATHENA_OUTPUT:
    raise ValueError(
        "Required environment variables not set: ATHENA_DATABASE, ATHENA_OUTPUT_LOCATION"
    )

def execute_athena_query(query: str) -> list:
    """Execute Athena query and return results"""
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': ATHENA_DATABASE},
        ResultConfiguration={'OutputLocation': ATHENA_OUTPUT}
    )
    
    query_id = response['QueryExecutionId']
    
    import time
    for _ in range(30):
        status = athena_client.get_query_execution(QueryExecutionId=query_id)
        state = status['QueryExecution']['Status']['State']
        if state == 'SUCCEEDED':
            break
        elif state in ['FAILED', 'CANCELLED']:
            return []
        time.sleep(1)
    
    results = athena_client.get_query_results(QueryExecutionId=query_id, MaxResults=1000)
    rows = results['ResultSet']['Rows']
    
    if len(rows) <= 1:
        return []
    
    columns = [col['VarCharValue'] for col in rows[0]['Data']]
    data = []
    for row in rows[1:]:
        row_data = {columns[i]: cell.get('VarCharValue', '') for i, cell in enumerate(row['Data'])}
        data.append(row_data)
    
    return data

def optimize_delivery_route(warehouse_code: str, sales_order_numbers: list = None, delivery_date: str = None):
    """Optimize delivery routes"""
    order_filter = ""
    if sales_order_numbers:
        orders = "','".join(sales_order_numbers)
        order_filter = f"AND soh.sales_order_number IN ('{orders}')"
    
    date_filter = ""
    if delivery_date:
        date_filter = f"AND soh.pref_del_date = '{delivery_date}'"
    
    query = f"""
    SELECT 
        soh.sales_order_number,
        soh.customer_code,
        soh.deliver_to_address_no,
        soh.del_area_code,
        soh.del_seq_number,
        soh.pref_del_date,
        COUNT(sol.sales_order_line) as line_count,
        SUM(sol.qty_seludouble) as total_quantity,
        soh.order_status
    FROM {ATHENA_DATABASE}.sales_order_header soh
    JOIN {ATHENA_DATABASE}.sales_order_line sol 
        ON soh.sales_order_prefix = sol.sales_order_prefix 
        AND soh.sales_order_number = sol.sales_order_number
    WHERE soh.warehouse_code = '{warehouse_code}'
        AND soh.order_status IN ('READY', 'PICKING', 'PACKED')
        {order_filter}
        {date_filter}
    GROUP BY soh.sales_order_number, soh.customer_code, soh.deliver_to_address_no,
             soh.del_area_code, soh.del_seq_number, soh.pref_del_date, soh.order_status
    ORDER BY soh.del_area_code, soh.del_seq_number
    LIMIT 50
    """
    
    results = execute_athena_query(query)
    
    # Group by delivery area for route optimization
    routes = {}
    for order in results:
        area = order.get('del_area_code', 'UNKNOWN')
        if area not in routes:
            routes[area] = []
        routes[area].append(order)
    
    optimized_routes = []
    for area, orders in routes.items():
        optimized_routes.append({
            "delivery_area": area,
            "order_count": len(orders),
            "total_quantity": sum(float(o.get('total_quantity', 0)) for o in orders),
            "orders": orders,
            "suggested_sequence": [o['sales_order_number'] for o in orders]
        })
    
    return {
        "warehouse_code": warehouse_code,
        "delivery_date": delivery_date,
        "total_orders": len(results),
        "routes": optimized_routes,
        "route_count": len(optimized_routes)
    }

def check_order_fulfillment_status(sales_order_number: str):
    """Check order fulfillment status"""
    query = f"""
    SELECT 
        sol.sales_order_number,
        sol.sales_order_line,
        sol.product_code,
        p.short_name,
        sol.qty_ordered_su,
        sol.allocated_qty_su,
        sol.picked_qty_su,
        sol.despatched_qty_su,
        sol.order_line_status,
        sol.required_delivery_date,
        soh.warehouse_code,
        soh.order_status as header_status
    FROM {ATHENA_DATABASE}.sales_order_line sol
    JOIN {ATHENA_DATABASE}.sales_order_header soh 
        ON sol.sales_order_prefix = soh.sales_order_prefix 
        AND sol.sales_order_number = soh.sales_order_number
    JOIN {ATHENA_DATABASE}.product p ON sol.product_code = p.product_code
    WHERE sol.sales_order_number = '{sales_order_number}'
    ORDER BY sol.sales_order_line
    """
    
    results = execute_athena_query(query)
    
    if not results:
        return {"error": f"Order {sales_order_number} not found"}
    
    total_lines = len(results)
    fully_picked = sum(1 for r in results if float(r.get('picked_qty_su', 0)) >= float(r.get('qty_ordered_su', 0)))
    fully_despatched = sum(1 for r in results if float(r.get('despatched_qty_su', 0)) >= float(r.get('qty_ordered_su', 0)))
    
    return {
        "sales_order_number": sales_order_number,
        "warehouse_code": results[0].get('warehouse_code'),
        "order_status": results[0].get('header_status'),
        "total_lines": total_lines,
        "lines_fully_picked": fully_picked,
        "lines_fully_despatched": fully_despatched,
        "completion_percentage": round((fully_despatched / total_lines) * 100, 2),
        "line_details": results
    }

def identify_delayed_orders(warehouse_code: str = None, days_overdue: int = 0):
    """Identify delayed orders"""
    warehouse_filter = f"AND soh.warehouse_code = '{warehouse_code}'" if warehouse_code else ""
    
    today = datetime.now().strftime('%Y%m%d')
    
    query = f"""
    SELECT 
        soh.sales_order_number,
        soh.customer_code,
        soh.warehouse_code,
        soh.pref_del_date,
        soh.order_status,
        COUNT(sol.sales_order_line) as total_lines,
        SUM(CASE WHEN sol.order_line_status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_lines,
        CAST({today} AS BIGINT) - soh.pref_del_date as days_overdue
    FROM {ATHENA_DATABASE}.sales_order_header soh
    JOIN {ATHENA_DATABASE}.sales_order_line sol 
        ON soh.sales_order_prefix = sol.sales_order_prefix 
        AND soh.sales_order_number = sol.sales_order_number
    WHERE soh.pref_del_date < CAST({today} AS BIGINT)
        AND soh.order_status NOT IN ('COMPLETED', 'CANCELLED')
        {warehouse_filter}
    GROUP BY soh.sales_order_number, soh.customer_code, soh.warehouse_code,
             soh.pref_del_date, soh.order_status
    HAVING CAST({today} AS BIGINT) - soh.pref_del_date >= {days_overdue}
    ORDER BY days_overdue DESC
    LIMIT 100
    """
    
    results = execute_athena_query(query)
    
    return {
        "warehouse_code": warehouse_code,
        "days_overdue_threshold": days_overdue,
        "delayed_orders": results,
        "total_delayed": len(results)
    }

def calculate_warehouse_capacity(warehouse_code: str):
    """Calculate warehouse capacity"""
    query = f"""
    SELECT 
        COUNT(DISTINCT product_code) as total_products,
        SUM(physical_stock_su) as total_stock_units,
        SUM(free_stock_su) as free_stock_units,
        SUM(allocated_stock_su) as allocated_stock_units,
        SUM(physical_stock_su * standard_cost) as total_inventory_value,
        AVG(CAST(physical_stock_su AS DOUBLE) / NULLIF(maximum_stock_su, 0)) as avg_capacity_utilization
    FROM {ATHENA_DATABASE}.warehouse_product
    WHERE warehouse_code = '{warehouse_code}'
        AND maximum_stock_su > 0
    """
    
    results = execute_athena_query(query)
    
    if not results:
        return {"error": f"Warehouse {warehouse_code} not found"}
    
    data = results[0]
    
    return {
        "warehouse_code": warehouse_code,
        "total_products": int(data.get('total_products', 0)),
        "total_stock_units": float(data.get('total_stock_units', 0)),
        "free_stock_units": float(data.get('free_stock_units', 0)),
        "allocated_stock_units": float(data.get('allocated_stock_units', 0)),
        "total_inventory_value": round(float(data.get('total_inventory_value', 0)), 2),
        "capacity_utilization_pct": round(float(data.get('avg_capacity_utilization', 0)) * 100, 2)
    }

def lambda_handler(event, context):
    """Lambda handler with async invocation support
    
    Supports both synchronous (RequestResponse) and asynchronous (Event) invocations.
    Returns structured responses compatible with ToolExecutor.
    """
    tool_name = event.get('tool_name')
    tool_input = event.get('input', {})
    
    # Track execution metadata
    start_time = datetime.now()
    
    try:
        if tool_name == 'optimize_delivery_route':
            result = optimize_delivery_route(
                tool_input['warehouse_code'],
                tool_input.get('sales_order_numbers'),
                tool_input.get('delivery_date')
            )
        elif tool_name == 'check_order_fulfillment_status':
            result = check_order_fulfillment_status(tool_input['sales_order_number'])
        elif tool_name == 'identify_delayed_orders':
            result = identify_delayed_orders(
                tool_input.get('warehouse_code'),
                tool_input.get('days_overdue', 0)
            )
        elif tool_name == 'calculate_warehouse_capacity':
            result = calculate_warehouse_capacity(tool_input['warehouse_code'])
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "tool_name": tool_name
            }
        
        # Return structured response
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "success": True,
            "result": result,
            "tool_name": tool_name,
            "execution_time_ms": execution_time
        }
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
            "execution_time_ms": execution_time
        }
