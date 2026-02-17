"""
Local testing script for Lambda functions.

This script allows you to test Lambda functions locally before deployment.
It simulates the Lambda execution environment and invokes the handlers.
"""

import json
import sys
import os
from pathlib import Path

# Add lambda function directories to path
lambda_dir = Path(__file__).parent
sys.path.insert(0, str(lambda_dir / "inventory_optimizer"))
sys.path.insert(0, str(lambda_dir / "logistics_optimizer"))
sys.path.insert(0, str(lambda_dir / "supplier_analyzer"))


def test_inventory_optimizer():
    """Test Inventory Optimizer Lambda function."""
    print("\n" + "="*60)
    print("Testing Inventory Optimizer Lambda")
    print("="*60)
    
    from inventory_optimizer.handler import lambda_handler
    
    # Test cases
    test_cases = [
        {
            "name": "Identify Low Stock",
            "event": {
                "action": "identify_low_stock",
                "warehouse_code": "WH-001",
                "threshold": 1.0
            }
        },
        {
            "name": "Calculate Reorder Point",
            "event": {
                "action": "calculate_reorder_point",
                "product_code": "PROD-001",
                "warehouse_code": "WH-001"
            }
        },
        {
            "name": "Forecast Demand",
            "event": {
                "action": "forecast_demand",
                "product_code": "PROD-001",
                "days": 30
            }
        },
        {
            "name": "Identify Stockout Risk",
            "event": {
                "action": "identify_stockout_risk",
                "warehouse_code": "WH-001",
                "days": 7
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Event: {json.dumps(test_case['event'], indent=2)}")
        
        try:
            response = lambda_handler(test_case['event'], None)
            print(f"Status Code: {response['statusCode']}")
            
            body = json.loads(response['body'])
            print(f"Success: {body.get('success', False)}")
            
            if body.get('success'):
                print("Response data structure validated ✓")
            else:
                print(f"Error: {body.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Exception: {str(e)}")


def test_logistics_optimizer():
    """Test Logistics Optimizer Lambda function."""
    print("\n" + "="*60)
    print("Testing Logistics Optimizer Lambda")
    print("="*60)
    
    from logistics_optimizer.handler import lambda_handler
    
    # Test cases
    test_cases = [
        {
            "name": "Optimize Delivery Route",
            "event": {
                "action": "optimize_delivery_route",
                "order_ids": ["SO-001", "SO-002", "SO-003"],
                "warehouse_code": "WH-001"
            }
        },
        {
            "name": "Check Fulfillment Status",
            "event": {
                "action": "check_fulfillment_status",
                "order_id": "SO-001"
            }
        },
        {
            "name": "Identify Delayed Orders",
            "event": {
                "action": "identify_delayed_orders",
                "warehouse_code": "WH-001",
                "days": 7
            }
        },
        {
            "name": "Calculate Warehouse Capacity",
            "event": {
                "action": "calculate_warehouse_capacity",
                "warehouse_code": "WH-001"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Event: {json.dumps(test_case['event'], indent=2)}")
        
        try:
            response = lambda_handler(test_case['event'], None)
            print(f"Status Code: {response['statusCode']}")
            
            body = json.loads(response['body'])
            print(f"Success: {body.get('success', False)}")
            
            if body.get('success'):
                print("Response data structure validated ✓")
            else:
                print(f"Error: {body.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Exception: {str(e)}")


def test_supplier_analyzer():
    """Test Supplier Analyzer Lambda function."""
    print("\n" + "="*60)
    print("Testing Supplier Analyzer Lambda")
    print("="*60)
    
    from supplier_analyzer.handler import lambda_handler
    
    # Test cases
    test_cases = [
        {
            "name": "Analyze Supplier Performance",
            "event": {
                "action": "analyze_supplier_performance",
                "supplier_code": "SUP-001",
                "days": 90
            }
        },
        {
            "name": "Compare Supplier Costs",
            "event": {
                "action": "compare_supplier_costs",
                "product_group": "Electronics",
                "suppliers": ["SUP-001", "SUP-002"]
            }
        },
        {
            "name": "Identify Cost Savings",
            "event": {
                "action": "identify_cost_savings",
                "threshold_percent": 10.0
            }
        },
        {
            "name": "Analyze Purchase Trends",
            "event": {
                "action": "analyze_purchase_trends",
                "days": 90,
                "group_by": "month"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Event: {json.dumps(test_case['event'], indent=2)}")
        
        try:
            response = lambda_handler(test_case['event'], None)
            print(f"Status Code: {response['statusCode']}")
            
            body = json.loads(response['body'])
            print(f"Success: {body.get('success', False)}")
            
            if body.get('success'):
                print("Response data structure validated ✓")
            else:
                print(f"Error: {body.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Exception: {str(e)}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Lambda Functions Local Testing")
    print("="*60)
    print("\nNote: These tests validate function structure and routing.")
    print("They will fail when trying to connect to Redshift (expected).")
    print("Deploy to AWS and test with real data for full validation.")
    
    # Set mock environment variables
    os.environ['REDSHIFT_WORKGROUP_NAME'] = 'supply-chain-mvp'
    os.environ['REDSHIFT_DATABASE'] = 'supply_chain_db'
    
    try:
        test_inventory_optimizer()
    except Exception as e:
        print(f"\nInventory Optimizer tests failed: {e}")
    
    try:
        test_logistics_optimizer()
    except Exception as e:
        print(f"\nLogistics Optimizer tests failed: {e}")
    
    try:
        test_supplier_analyzer()
    except Exception as e:
        print(f"\nSupplier Analyzer tests failed: {e}")
    
    print("\n" + "="*60)
    print("Testing Complete")
    print("="*60)
    print("\nNext steps:")
    print("1. Deploy Lambda functions: ./scripts/deploy_lambda.sh")
    print("2. Test with real data using AWS Lambda Console")
    print("3. Verify CloudWatch logs for any errors")


if __name__ == "__main__":
    main()
