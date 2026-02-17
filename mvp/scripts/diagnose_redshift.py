#!/usr/bin/env python3
"""
Diagnose Redshift Serverless Connection Issues

This script helps identify why the connection to Redshift Serverless is failing.
"""

import boto3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_redshift_workgroup(region: str, workgroup_name: str):
    """Check if Redshift workgroup exists and its status."""
    print(f"\n{'='*60}")
    print("Checking Redshift Serverless Workgroup")
    print(f"{'='*60}")
    
    try:
        client = boto3.client('redshift-serverless', region_name=region)
        
        # Get workgroup details
        response = client.get_workgroup(workgroupName=workgroup_name)
        workgroup = response['workgroup']
        
        print(f"✓ Workgroup found: {workgroup_name}")
        print(f"  Status: {workgroup['status']}")
        print(f"  Endpoint: {workgroup.get('endpoint', {}).get('address', 'N/A')}")
        print(f"  Base Capacity: {workgroup.get('baseCapacity', 'N/A')} RPUs")
        print(f"  Namespace: {workgroup.get('namespaceName', 'N/A')}")
        
        if workgroup['status'] != 'AVAILABLE':
            print(f"\n⚠ WARNING: Workgroup status is '{workgroup['status']}'")
            print("  The workgroup must be in 'AVAILABLE' status to accept queries.")
            print("  Please wait a few minutes and try again.")
            return False
        
        return True
        
    except client.exceptions.ResourceNotFoundException:
        print(f"✗ Workgroup '{workgroup_name}' not found")
        print("\nAvailable workgroups:")
        try:
            response = client.list_workgroups()
            workgroups = response.get('workgroups', [])
            if workgroups:
                for wg in workgroups:
                    print(f"  - {wg['workgroupName']} (Status: {wg['status']})")
            else:
                print("  No workgroups found")
        except Exception as e:
            print(f"  Could not list workgroups: {e}")
        return False
        
    except Exception as e:
        print(f"✗ Error checking workgroup: {e}")
        return False


def check_iam_permissions(region: str):
    """Check IAM permissions for the current role."""
    print(f"\n{'='*60}")
    print("Checking IAM Permissions")
    print(f"{'='*60}")
    
    try:
        sts = boto3.client('sts', region_name=region)
        identity = sts.get_caller_identity()
        
        print(f"✓ Current identity:")
        print(f"  Account: {identity['Account']}")
        print(f"  ARN: {identity['Arn']}")
        print(f"  User ID: {identity['UserId']}")
        
        # Try to check if we can access Redshift Data API
        print(f"\n  Testing Redshift Data API access...")
        redshift_data = boto3.client('redshift-data', region_name=region)
        
        # This will fail if we don't have permissions, but that's okay
        try:
            redshift_data.list_statements(MaxResults=1)
            print(f"  ✓ Can access Redshift Data API")
        except Exception as e:
            if 'AccessDenied' in str(e):
                print(f"  ✗ Access denied to Redshift Data API")
                print(f"    Error: {e}")
                return False
            else:
                # Other errors are okay for this test
                print(f"  ✓ Can access Redshift Data API (got expected error)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking IAM permissions: {e}")
        return False


def check_redshift_namespace(region: str, namespace_name: str):
    """Check if Redshift namespace exists."""
    print(f"\n{'='*60}")
    print("Checking Redshift Serverless Namespace")
    print(f"{'='*60}")
    
    try:
        client = boto3.client('redshift-serverless', region_name=region)
        
        # Get namespace details
        response = client.get_namespace(namespaceName=namespace_name)
        namespace = response['namespace']
        
        print(f"✓ Namespace found: {namespace_name}")
        print(f"  Status: {namespace['status']}")
        print(f"  Database: {namespace.get('dbName', 'N/A')}")
        print(f"  Admin Username: {namespace.get('adminUsername', 'N/A')}")
        
        if namespace['status'] != 'AVAILABLE':
            print(f"\n⚠ WARNING: Namespace status is '{namespace['status']}'")
            print("  The namespace must be in 'AVAILABLE' status.")
            return False
        
        return True
        
    except client.exceptions.ResourceNotFoundException:
        print(f"✗ Namespace '{namespace_name}' not found")
        return False
        
    except Exception as e:
        print(f"✗ Error checking namespace: {e}")
        return False


def test_simple_query(region: str, workgroup_name: str, database: str):
    """Test a simple query with extended timeout."""
    print(f"\n{'='*60}")
    print("Testing Simple Query")
    print(f"{'='*60}")
    
    try:
        from aws.redshift_client import RedshiftClient
        
        # Create client with longer timeout
        print(f"Creating Redshift client with 120 second timeout...")
        client = RedshiftClient(
            region=region,
            workgroup_name=workgroup_name,
            database=database,
            timeout=120  # 2 minutes
        )
        
        print(f"Executing test query: SELECT 1 as test")
        print(f"This may take up to 2 minutes on first query...")
        
        result = client.execute_query("SELECT 1 as test")
        
        print(f"✓ Query successful!")
        print(f"  Execution time: {result.execution_time:.2f} seconds")
        print(f"  Result: {result.rows}")
        
        return True
        
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return False


def main():
    """Main diagnostic function."""
    print("\n" + "="*60)
    print("Redshift Serverless Connection Diagnostics")
    print("="*60)
    
    # Get parameters
    region = input("\nEnter AWS region (default: us-east-1): ").strip() or "us-east-1"
    workgroup_name = input("Enter workgroup name (default: supply-chain-mvp): ").strip() or "supply-chain-mvp"
    database = input("Enter database name (default: supply_chain_db): ").strip() or "supply_chain_db"
    
    # Derive namespace name (usually workgroup-name + "-namespace")
    namespace_name = f"{workgroup_name}-namespace"
    
    print(f"\nConfiguration:")
    print(f"  Region: {region}")
    print(f"  Workgroup: {workgroup_name}")
    print(f"  Database: {database}")
    print(f"  Namespace: {namespace_name}")
    
    # Run checks
    checks_passed = 0
    total_checks = 4
    
    if check_iam_permissions(region):
        checks_passed += 1
    
    if check_redshift_namespace(region, namespace_name):
        checks_passed += 1
    
    if check_redshift_workgroup(region, workgroup_name):
        checks_passed += 1
    
    if checks_passed == 3:
        if test_simple_query(region, workgroup_name, database):
            checks_passed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("Diagnostic Summary")
    print(f"{'='*60}")
    print(f"Checks passed: {checks_passed}/{total_checks}")
    
    if checks_passed == total_checks:
        print("\n✓ All checks passed! Your Redshift connection should work.")
        print("\nYou can now run:")
        print(f"  python scripts/generate_sample_data.py --load-redshift \\")
        print(f"    --workgroup {workgroup_name} \\")
        print(f"    --database {database} \\")
        print(f"    --region {region}")
    else:
        print("\n✗ Some checks failed. Please address the issues above.")
        print("\nCommon solutions:")
        print("  1. Wait 5-10 minutes for Redshift workgroup to become AVAILABLE")
        print("  2. Check IAM role permissions for SageMaker")
        print("  3. Verify workgroup and database names are correct")
        print("  4. Check AWS Console for any error messages")


if __name__ == '__main__':
    main()
