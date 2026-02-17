#!/usr/bin/env python3
"""
Database Migration Script: Redshift Serverless to Amazon Athena

This script orchestrates the complete migration from Redshift Serverless to Athena:
1. Exports data from Redshift to S3 (Parquet format)
2. Creates Glue Catalog database and tables
3. Validates data integrity
4. Generates migration report

Usage:
    python migrate_redshift_to_athena.py --config config.yaml --validate
"""

import boto3
import time
import argparse
import yaml
from typing import List, Dict, Tuple
from datetime import datetime
import pandas as pd


class RedshiftToAthenaMigration:
    """Orchestrates migration from Redshift to Athena"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.redshift_data = boto3.client('redshift-data')
        self.athena = boto3.client('athena')
        self.glue = boto3.client('glue')
        self.s3 = boto3.client('s3')
        
        # Configuration
        self.redshift_workgroup = config['database']['redshift']['workgroup_name']
        self.redshift_database = config['database']['redshift']['database']
        self.athena_database = config['database']['athena']['database']
        self.s3_bucket = config['migration']['s3_bucket']
        self.s3_prefix = config['migration']['s3_prefix']
        self.iam_role = config['migration']['iam_role']
        self.athena_output = config['database']['athena']['output_location']
        
        # Tables to migrate
        self.tables = [
            {'name': 'product', 'partition_by': 'created_date'},
            {'name': 'warehouse_product', 'partition_by': 'warehouse_code'},
            {'name': 'sales_order_header', 'partition_by': 'order_date'},
            {'name': 'sales_order_line', 'partition_by': None},
            {'name': 'purchase_order_header', 'partition_by': 'order_date'},
            {'name': 'purchase_order_line', 'partition_by': None}
        ]
        
        self.migration_report = {
            'start_time': datetime.now(),
            'tables': {},
            'errors': []
        }
    
    def run_migration(self, validate: bool = True) -> Dict:
        """Run complete migration process"""
        print("=" * 80)
        print("REDSHIFT TO ATHENA MIGRATION")
        print("=" * 80)
        print(f"Start Time: {self.migration_report['start_time']}")
        print()
        
        try:
            # Step 1: Export data from Redshift
            print("STEP 1: Exporting data from Redshift to S3...")
            print("-" * 80)
            self.export_all_tables()
            
            # Step 2: Create Athena database and tables
            print("\nSTEP 2: Creating Athena database and tables...")
            print("-" * 80)
            self.create_athena_database()
            self.create_athena_tables()
            
            # Step 3: Validate data (if requested)
            if validate:
                print("\nSTEP 3: Validating data integrity...")
                print("-" * 80)
                self.validate_migration()
            
            # Step 4: Generate report
            self.migration_report['end_time'] = datetime.now()
            self.migration_report['duration'] = (
                self.migration_report['end_time'] - self.migration_report['start_time']
            ).total_seconds()
            
            self.print_migration_report()
            
            return self.migration_report
            
        except Exception as e:
            self.migration_report['errors'].append(str(e))
            print(f"\n❌ Migration failed: {e}")
            raise
    
    def export_all_tables(self):
        """Export all tables from Redshift to S3"""
        for table_info in self.tables:
            table_name = table_info['name']
            partition_by = table_info['partition_by']
            
            try:
                row_count = self.export_table(table_name, partition_by)
                self.migration_report['tables'][table_name] = {
                    'redshift_rows': row_count,
                    'export_status': 'success'
                }
            except Exception as e:
                self.migration_report['tables'][table_name] = {
                    'export_status': 'failed',
                    'error': str(e)
                }
                self.migration_report['errors'].append(f"{table_name}: {e}")
                raise
    
    def export_table(self, table_name: str, partition_by: str = None) -> int:
        """Export single table from Redshift to S3"""
        print(f"  Exporting {table_name}...", end=" ", flush=True)
        
        # Get row count
        count_query = f"SELECT COUNT(*) FROM {table_name}"
        count_result = self.execute_redshift_query(count_query)
        row_count = int(count_result[0][0])
        
        # Build UNLOAD query
        s3_path = f"s3://{self.s3_bucket}/{self.s3_prefix}/{table_name}/"
        
        unload_query = f"""
        UNLOAD ('SELECT * FROM {table_name}')
        TO '{s3_path}'
        IAM_ROLE '{self.iam_role}'
        FORMAT AS PARQUET
        ALLOWOVERWRITE
        """
        
        if partition_by:
            unload_query += f"\nPARTITION BY ({partition_by})"
        
        # Execute UNLOAD
        self.execute_redshift_query(unload_query)
        
        print(f"✓ ({row_count:,} rows)")
        return row_count
    
    def execute_redshift_query(self, sql: str) -> List[List]:
        """Execute query on Redshift and wait for completion"""
        response = self.redshift_data.execute_statement(
            WorkgroupName=self.redshift_workgroup,
            Database=self.redshift_database,
            Sql=sql
        )
        
        query_id = response['Id']
        
        # Wait for completion
        while True:
            status_response = self.redshift_data.describe_statement(Id=query_id)
            status = status_response['Status']
            
            if status == 'FINISHED':
                # Get results if available
                try:
                    result_response = self.redshift_data.get_statement_result(Id=query_id)
                    return [[col['stringValue'] for col in row] for row in result_response['Records']]
                except:
                    return []
            elif status in ['FAILED', 'ABORTED']:
                error = status_response.get('Error', 'Unknown error')
                raise Exception(f"Query failed: {error}")
            
            time.sleep(1)
    
    def create_athena_database(self):
        """Create Glue database for Athena"""
        try:
            self.glue.create_database(
                DatabaseInput={
                    'Name': self.athena_database,
                    'Description': 'Supply Chain data migrated from Redshift'
                }
            )
            print(f"  ✓ Database '{self.athena_database}' created")
        except self.glue.exceptions.AlreadyExistsException:
            print(f"  ℹ Database '{self.athena_database}' already exists")
    
    def create_athena_tables(self):
        """Create all Athena tables"""
        table_ddls = self.get_table_ddls()
        
        for table_name, ddl in table_ddls.items():
            print(f"  Creating table {table_name}...", end=" ", flush=True)
            self.execute_athena_query(ddl)
            print("✓")
    
    def get_table_ddls(self) -> Dict[str, str]:
        """Get CREATE TABLE DDL statements for all tables"""
        s3_location_base = f"s3://{self.s3_bucket}/{self.s3_prefix}"
        
        return {
            'product': f"""
            CREATE EXTERNAL TABLE IF NOT EXISTS {self.athena_database}.product (
                product_code STRING,
                product_name STRING,
                product_group STRING,
                unit_cost DECIMAL(10,2),
                unit_price DECIMAL(10,2),
                supplier_code STRING,
                supplier_name STRING,
                created_date DATE,
                updated_date DATE
            )
            STORED AS PARQUET
            LOCATION '{s3_location_base}/product/'
            """,
            
            'warehouse_product': f"""
            CREATE EXTERNAL TABLE IF NOT EXISTS {self.athena_database}.warehouse_product (
                warehouse_code STRING,
                product_code STRING,
                current_stock INT,
                minimum_stock INT,
                maximum_stock INT,
                reorder_point INT,
                lead_time_days INT,
                last_restock_date DATE
            )
            STORED AS PARQUET
            LOCATION '{s3_location_base}/warehouse_product/'
            """,
            
            'sales_order_header': f"""
            CREATE EXTERNAL TABLE IF NOT EXISTS {self.athena_database}.sales_order_header (
                sales_order_prefix STRING,
                sales_order_number STRING,
                order_date DATE,
                customer_code STRING,
                customer_name STRING,
                warehouse_code STRING,
                delivery_address STRING,
                delivery_area STRING,
                delivery_date DATE,
                status STRING
            )
            STORED AS PARQUET
            LOCATION '{s3_location_base}/sales_order_header/'
            """,
            
            'sales_order_line': f"""
            CREATE EXTERNAL TABLE IF NOT EXISTS {self.athena_database}.sales_order_line (
                sales_order_prefix STRING,
                sales_order_number STRING,
                sales_order_line INT,
                product_code STRING,
                order_quantity INT,
                fulfilled_quantity INT,
                unit_price DECIMAL(10,2),
                line_total DECIMAL(10,2),
                fulfillment_status STRING
            )
            STORED AS PARQUET
            LOCATION '{s3_location_base}/sales_order_line/'
            """,
            
            'purchase_order_header': f"""
            CREATE EXTERNAL TABLE IF NOT EXISTS {self.athena_database}.purchase_order_header (
                purchase_order_prefix STRING,
                purchase_order_number STRING,
                order_date DATE,
                supplier_code STRING,
                supplier_name STRING,
                warehouse_code STRING,
                expected_delivery_date DATE,
                actual_delivery_date DATE,
                status STRING
            )
            STORED AS PARQUET
            LOCATION '{s3_location_base}/purchase_order_header/'
            """,
            
            'purchase_order_line': f"""
            CREATE EXTERNAL TABLE IF NOT EXISTS {self.athena_database}.purchase_order_line (
                purchase_order_prefix STRING,
                purchase_order_number STRING,
                purchase_order_line INT,
                product_code STRING,
                order_quantity INT,
                received_quantity INT,
                unit_cost DECIMAL(10,2),
                line_total DECIMAL(10,2),
                receipt_status STRING
            )
            STORED AS PARQUET
            LOCATION '{s3_location_base}/purchase_order_line/'
            """
        }
    
    def execute_athena_query(self, sql: str) -> List[List]:
        """Execute query on Athena and wait for completion"""
        response = self.athena.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={'Database': self.athena_database},
            ResultConfiguration={'OutputLocation': self.athena_output}
        )
        
        query_id = response['QueryExecutionId']
        
        # Wait for completion
        while True:
            result = self.athena.get_query_execution(QueryExecutionId=query_id)
            status = result['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                # Get results if available
                try:
                    results = self.athena.get_query_results(QueryExecutionId=query_id)
                    rows = []
                    for row in results['ResultSet']['Rows'][1:]:  # Skip header
                        rows.append([field.get('VarCharValue', '') for field in row['Data']])
                    return rows
                except:
                    return []
            elif status in ['FAILED', 'CANCELLED']:
                error = result['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
                raise Exception(f"Query failed: {error}")
            
            time.sleep(1)
    
    def validate_migration(self):
        """Validate data integrity after migration"""
        print("  Validating row counts...")
        
        all_valid = True
        
        for table_name in [t['name'] for t in self.tables]:
            # Get Athena row count
            athena_query = f"SELECT COUNT(*) FROM {self.athena_database}.{table_name}"
            athena_result = self.execute_athena_query(athena_query)
            athena_count = int(athena_result[0][0])
            
            # Compare with Redshift count
            redshift_count = self.migration_report['tables'][table_name]['redshift_rows']
            
            match = athena_count == redshift_count
            status = "✓" if match else "❌"
            
            print(f"    {table_name}: Redshift={redshift_count:,}, Athena={athena_count:,} {status}")
            
            self.migration_report['tables'][table_name]['athena_rows'] = athena_count
            self.migration_report['tables'][table_name]['validation'] = 'passed' if match else 'failed'
            
            if not match:
                all_valid = False
                self.migration_report['errors'].append(
                    f"{table_name}: Row count mismatch (Redshift={redshift_count}, Athena={athena_count})"
                )
        
        if all_valid:
            print("\n  ✓ All tables validated successfully")
        else:
            print("\n  ❌ Validation failed for some tables")
    
    def print_migration_report(self):
        """Print migration summary report"""
        print("\n" + "=" * 80)
        print("MIGRATION REPORT")
        print("=" * 80)
        print(f"Start Time:  {self.migration_report['start_time']}")
        print(f"End Time:    {self.migration_report['end_time']}")
        print(f"Duration:    {self.migration_report['duration']:.2f} seconds")
        print()
        
        print("Table Summary:")
        print("-" * 80)
        for table_name, info in self.migration_report['tables'].items():
            redshift_rows = info.get('redshift_rows', 0)
            athena_rows = info.get('athena_rows', 'N/A')
            validation = info.get('validation', 'N/A')
            
            print(f"  {table_name:25} | Redshift: {redshift_rows:>10,} | Athena: {str(athena_rows):>10} | {validation}")
        
        if self.migration_report['errors']:
            print("\nErrors:")
            print("-" * 80)
            for error in self.migration_report['errors']:
                print(f"  ❌ {error}")
        else:
            print("\n✓ Migration completed successfully with no errors")
        
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Migrate from Redshift to Athena')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--validate', action='store_true', help='Validate data after migration')
    parser.add_argument('--skip-export', action='store_true', help='Skip data export (tables only)')
    
    args = parser.parse_args()
    
    # Load configuration
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Run migration
    migration = RedshiftToAthenaMigration(config)
    migration.run_migration(validate=args.validate)


if __name__ == '__main__':
    main()
