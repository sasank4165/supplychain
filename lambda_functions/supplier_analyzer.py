"""Lambda function for supplier analysis tools"""
import json
import boto3

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

def analyze_supplier_performance(supplier_code: str = None, time_period_days: int = 90):
    """Analyze supplier performance"""
    supplier_filter = f"AND poh.supplier_code = '{supplier_code}'" if supplier_code else ""
    
    query = f"""
    SELECT 
        poh.supplier_code,
        COUNT(DISTINCT poh.purchase_order_number) as total_orders,
        COUNT(DISTINCT CASE WHEN poh.order_status = 'COMPLETED' THEN poh.purchase_order_number END) as completed_orders,
        SUM(pol.line_valuedouble) as total_value,
        AVG(pol.unit_price_oudouble) as avg_unit_price,
        SUM(pol.received_qty_oudouble) as total_received_qty,
        SUM(pol.qty_oudouble) as total_ordered_qty,
        CAST(SUM(pol.received_qty_oudouble) AS DOUBLE) / NULLIF(SUM(pol.qty_oudouble), 0) as fill_rate,
        COUNT(DISTINCT pol.product_code) as unique_products
    FROM {ATHENA_DATABASE}.purchase_order_header poh
    JOIN {ATHENA_DATABASE}.purchase_order_line pol 
        ON poh.purchase_order_prefix = pol.purchase_order_prefix 
        AND poh.purchase_order_numberbigint = pol.purchase_order_numberbigint
    WHERE poh.order_raised_date >= CAST(DATE_FORMAT(DATE_ADD('day', -{time_period_days}, CURRENT_DATE), '%Y%m%d') AS BIGINT)
        {supplier_filter}
    GROUP BY poh.supplier_code
    ORDER BY total_value DESC
    LIMIT 50
    """
    
    results = execute_athena_query(query)
    
    for supplier in results:
        fill_rate = float(supplier.get('fill_rate', 0))
        supplier['fill_rate_pct'] = round(fill_rate * 100, 2)
        supplier['performance_score'] = round(fill_rate * 100, 2)  # Simplified score
    
    return {
        "time_period_days": time_period_days,
        "supplier_code": supplier_code,
        "suppliers": results,
        "total_suppliers": len(results)
    }

def compare_supplier_costs(product_group: str, supplier_codes: list = None):
    """Compare costs across suppliers"""
    supplier_filter = ""
    if supplier_codes:
        codes = "','".join(supplier_codes)
        supplier_filter = f"AND p.supplier_code1 IN ('{codes}')"
    
    query = f"""
    SELECT 
        p.supplier_code1 as supplier_code,
        p.product_group,
        COUNT(DISTINCT p.product_code) as product_count,
        AVG(p.standard_cost) as avg_standard_cost,
        MIN(p.standard_cost) as min_cost,
        MAX(p.standard_cost) as max_cost,
        AVG(pol.unit_price_oudouble) as avg_purchase_price
    FROM {ATHENA_DATABASE}.product p
    LEFT JOIN {ATHENA_DATABASE}.purchase_order_line pol ON p.product_code = pol.product_code
    WHERE p.product_group = '{product_group}'
        {supplier_filter}
    GROUP BY p.supplier_code1, p.product_group
    ORDER BY avg_standard_cost
    """
    
    results = execute_athena_query(query)
    
    if results:
        min_avg_cost = min(float(r.get('avg_standard_cost', 999999)) for r in results)
        for supplier in results:
            avg_cost = float(supplier.get('avg_standard_cost', 0))
            if min_avg_cost > 0:
                supplier['cost_vs_best'] = round(((avg_cost - min_avg_cost) / min_avg_cost) * 100, 2)
    
    return {
        "product_group": product_group,
        "supplier_comparison": results,
        "total_suppliers": len(results)
    }

def identify_cost_savings_opportunities(product_group: str = None, min_savings_percentage: float = 5.0):
    """Identify cost savings opportunities"""
    group_filter = f"AND p.product_group = '{product_group}'" if product_group else ""
    
    query = f"""
    WITH supplier_costs AS (
        SELECT 
            p.product_code,
            p.short_name,
            p.product_group,
            p.supplier_code1,
            p.standard_cost,
            AVG(pol.unit_price_oudouble) as avg_purchase_price,
            SUM(pol.qty_oudouble) as total_qty_purchased
        FROM {ATHENA_DATABASE}.product p
        LEFT JOIN {ATHENA_DATABASE}.purchase_order_line pol ON p.product_code = pol.product_code
        WHERE p.standard_cost > 0
            {group_filter}
        GROUP BY p.product_code, p.short_name, p.product_group, p.supplier_code1, p.standard_cost
    ),
    min_costs AS (
        SELECT 
            product_code,
            MIN(standard_cost) as min_cost
        FROM supplier_costs
        GROUP BY product_code
    )
    SELECT 
        sc.product_code,
        sc.short_name,
        sc.product_group,
        sc.supplier_code1 as current_supplier,
        sc.standard_cost as current_cost,
        mc.min_cost as best_available_cost,
        CAST((sc.standard_cost - mc.min_cost) / sc.standard_cost * 100 AS DECIMAL(10,2)) as savings_percentage,
        sc.total_qty_purchased,
        (sc.standard_cost - mc.min_cost) * sc.total_qty_purchased as potential_annual_savings
    FROM supplier_costs sc
    JOIN min_costs mc ON sc.product_code = mc.product_code
    WHERE sc.standard_cost > mc.min_cost
        AND (sc.standard_cost - mc.min_cost) / sc.standard_cost * 100 >= {min_savings_percentage}
    ORDER BY potential_annual_savings DESC
    LIMIT 50
    """
    
    results = execute_athena_query(query)
    
    total_savings = sum(float(r.get('potential_annual_savings', 0)) for r in results)
    
    return {
        "product_group": product_group,
        "min_savings_percentage": min_savings_percentage,
        "opportunities": results,
        "total_opportunities": len(results),
        "total_potential_savings": round(total_savings, 2)
    }

def analyze_purchase_order_trends(supplier_code: str = None, months: int = 6):
    """Analyze purchase order trends"""
    supplier_filter = f"AND poh.supplier_code = '{supplier_code}'" if supplier_code else ""
    
    query = f"""
    SELECT 
        poh.supplier_code,
        poh.posting_year,
        poh.posting_period,
        COUNT(DISTINCT poh.purchase_order_number) as order_count,
        SUM(pol.line_valuedouble) as total_value,
        AVG(pol.unit_price_oudouble) as avg_unit_price,
        COUNT(DISTINCT pol.product_code) as unique_products
    FROM {ATHENA_DATABASE}.purchase_order_header poh
    JOIN {ATHENA_DATABASE}.purchase_order_line pol 
        ON poh.purchase_order_prefix = pol.purchase_order_prefix 
        AND poh.purchase_order_numberbigint = pol.purchase_order_numberbigint
    WHERE poh.posting_year >= YEAR(DATE_ADD('month', -{months}, CURRENT_DATE))
        {supplier_filter}
    GROUP BY poh.supplier_code, poh.posting_year, poh.posting_period
    ORDER BY poh.posting_year DESC, poh.posting_period DESC
    LIMIT 100
    """
    
    results = execute_athena_query(query)
    
    return {
        "supplier_code": supplier_code,
        "months": months,
        "trends": results,
        "total_periods": len(results)
    }

def lambda_handler(event, context):
    """Lambda handler"""
    tool_name = event.get('tool_name')
    tool_input = event.get('input', {})
    
    try:
        if tool_name == 'analyze_supplier_performance':
            result = analyze_supplier_performance(
                tool_input.get('supplier_code'),
                tool_input.get('time_period_days', 90)
            )
        elif tool_name == 'compare_supplier_costs':
            result = compare_supplier_costs(
                tool_input['product_group'],
                tool_input.get('supplier_codes')
            )
        elif tool_name == 'identify_cost_savings_opportunities':
            result = identify_cost_savings_opportunities(
                tool_input.get('product_group'),
                tool_input.get('min_savings_percentage', 5.0)
            )
        elif tool_name == 'analyze_purchase_order_trends':
            result = analyze_purchase_order_trends(
                tool_input.get('supplier_code'),
                tool_input.get('months', 6)
            )
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        return result
    except Exception as e:
        return {"error": str(e)}
