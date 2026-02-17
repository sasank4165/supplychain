"""
AWS Glue Data Catalog Client Wrapper

Provides a simplified interface for accessing Glue Data Catalog metadata.
"""

import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ColumnMetadata:
    """Column metadata from Glue Catalog."""
    name: str
    type: str
    comment: Optional[str] = None


@dataclass
class TableMetadata:
    """Table metadata from Glue Catalog."""
    name: str
    database: str
    columns: List[ColumnMetadata]
    location: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, str]] = None


class GlueClientError(Exception):
    """Raised when Glue API call fails."""
    pass


class GlueClient:
    """Client for AWS Glue Data Catalog."""
    
    def __init__(self, region: str, catalog_id: Optional[str] = None, database: str = None):
        """
        Initialize Glue client.
        
        Args:
            region: AWS region
            catalog_id: AWS account ID (optional, defaults to current account)
            database: Default database name
        """
        self.region = region
        self.catalog_id = catalog_id
        self.database = database
        
        try:
            self.client = boto3.client('glue', region_name=region)
        except Exception as e:
            raise GlueClientError(f"Failed to initialize Glue client: {e}")
    
    def get_table(self, table_name: str, database: Optional[str] = None) -> TableMetadata:
        """
        Get table metadata from Glue Catalog.
        
        Args:
            table_name: Name of the table
            database: Database name (uses default if not provided)
            
        Returns:
            TableMetadata with table information
            
        Raises:
            GlueClientError: If table not found or API call fails
        """
        db_name = database or self.database
        if not db_name:
            raise GlueClientError("Database name must be provided")
        
        try:
            params = {
                'DatabaseName': db_name,
                'Name': table_name
            }
            if self.catalog_id:
                params['CatalogId'] = self.catalog_id
            
            response = self.client.get_table(**params)
            table = response['Table']
            
            # Extract column metadata
            columns = []
            for col in table['StorageDescriptor']['Columns']:
                columns.append(ColumnMetadata(
                    name=col['Name'],
                    type=col['Type'],
                    comment=col.get('Comment')
                ))
            
            # Add partition columns if present
            for col in table.get('PartitionKeys', []):
                columns.append(ColumnMetadata(
                    name=col['Name'],
                    type=col['Type'],
                    comment=col.get('Comment')
                ))
            
            return TableMetadata(
                name=table['Name'],
                database=db_name,
                columns=columns,
                location=table['StorageDescriptor'].get('Location'),
                description=table.get('Description'),
                parameters=table.get('Parameters')
            )
            
        except self.client.exceptions.EntityNotFoundException:
            raise GlueClientError(f"Table not found: {table_name} in database {db_name}")
        except Exception as e:
            raise GlueClientError(f"Failed to get table metadata: {e}")
    
    def list_tables(self, database: Optional[str] = None) -> List[str]:
        """
        List all tables in a database.
        
        Args:
            database: Database name (uses default if not provided)
            
        Returns:
            List of table names
            
        Raises:
            GlueClientError: If database not found or API call fails
        """
        db_name = database or self.database
        if not db_name:
            raise GlueClientError("Database name must be provided")
        
        try:
            params = {'DatabaseName': db_name}
            if self.catalog_id:
                params['CatalogId'] = self.catalog_id
            
            tables = []
            next_token = None
            
            while True:
                if next_token:
                    params['NextToken'] = next_token
                
                response = self.client.get_tables(**params)
                
                for table in response['TableList']:
                    tables.append(table['Name'])
                
                next_token = response.get('NextToken')
                if not next_token:
                    break
            
            return tables
            
        except self.client.exceptions.EntityNotFoundException:
            raise GlueClientError(f"Database not found: {db_name}")
        except Exception as e:
            raise GlueClientError(f"Failed to list tables: {e}")
    
    def get_database(self, database: Optional[str] = None) -> Dict[str, Any]:
        """
        Get database metadata.
        
        Args:
            database: Database name (uses default if not provided)
            
        Returns:
            Database metadata dictionary
            
        Raises:
            GlueClientError: If database not found or API call fails
        """
        db_name = database or self.database
        if not db_name:
            raise GlueClientError("Database name must be provided")
        
        try:
            params = {'Name': db_name}
            if self.catalog_id:
                params['CatalogId'] = self.catalog_id
            
            response = self.client.get_database(**params)
            return response['Database']
            
        except self.client.exceptions.EntityNotFoundException:
            raise GlueClientError(f"Database not found: {db_name}")
        except Exception as e:
            raise GlueClientError(f"Failed to get database metadata: {e}")
    
    def get_table_schema(self, table_name: str, database: Optional[str] = None) -> Dict[str, str]:
        """
        Get table schema as a dictionary of column names to types.
        
        Args:
            table_name: Name of the table
            database: Database name (uses default if not provided)
            
        Returns:
            Dictionary mapping column names to data types
        """
        table_metadata = self.get_table(table_name, database)
        return {col.name: col.type for col in table_metadata.columns}
    
    def get_all_table_schemas(self, database: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """
        Get schemas for all tables in a database.
        
        Args:
            database: Database name (uses default if not provided)
            
        Returns:
            Dictionary mapping table names to their schemas
        """
        table_names = self.list_tables(database)
        schemas = {}
        
        for table_name in table_names:
            try:
                schemas[table_name] = self.get_table_schema(table_name, database)
            except GlueClientError as e:
                # Log error but continue with other tables
                print(f"Warning: Failed to get schema for {table_name}: {e}")
        
        return schemas
    
    def test_connection(self) -> bool:
        """
        Test connection to Glue Catalog.
        
        Returns:
            True if connection successful
            
        Raises:
            GlueClientError: If connection fails
        """
        try:
            if self.database:
                self.get_database()
            else:
                # Just list databases to test connection
                params = {}
                if self.catalog_id:
                    params['CatalogId'] = self.catalog_id
                self.client.get_databases(**params)
            return True
        except Exception as e:
            raise GlueClientError(f"Connection test failed: {e}")
    
    def get_table_ddl(self, table_name: str, database: Optional[str] = None) -> str:
        """
        Generate CREATE TABLE DDL for a table.
        
        Args:
            table_name: Name of the table
            database: Database name (uses default if not provided)
            
        Returns:
            CREATE TABLE DDL statement
        """
        table_metadata = self.get_table(table_name, database)
        
        columns_ddl = []
        for col in table_metadata.columns:
            col_def = f"  {col.name} {col.type}"
            if col.comment:
                col_def += f" COMMENT '{col.comment}'"
            columns_ddl.append(col_def)
        
        ddl = f"CREATE TABLE {table_metadata.name} (\n"
        ddl += ",\n".join(columns_ddl)
        ddl += "\n)"
        
        if table_metadata.description:
            ddl += f"\nCOMMENT '{table_metadata.description}'"
        
        return ddl
