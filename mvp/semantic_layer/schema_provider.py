"""
Schema Provider - Fetches schema metadata from AWS Glue Data Catalog

Provides schema information to the semantic layer for SQL generation.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from aws.glue_client import GlueClient, TableMetadata, ColumnMetadata, GlueClientError
except ImportError:
    # For standalone testing
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from aws.glue_client import GlueClient, TableMetadata, ColumnMetadata, GlueClientError


@dataclass
class TableSchema:
    """Simplified table schema for semantic layer."""
    name: str
    columns: Dict[str, str]  # column_name -> data_type
    description: Optional[str] = None
    primary_keys: Optional[List[str]] = None
    foreign_keys: Optional[Dict[str, str]] = None  # column -> referenced_table.column


class SchemaProvider:
    """Provides schema metadata from Glue Data Catalog."""
    
    def __init__(self, glue_client: GlueClient):
        """
        Initialize schema provider.
        
        Args:
            glue_client: Configured GlueClient instance
        """
        self.glue_client = glue_client
        self._schema_cache: Dict[str, TableSchema] = {}
        self._all_tables_cache: Optional[List[str]] = None
    
    def get_table_schema(self, table_name: str) -> TableSchema:
        """
        Get schema for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            TableSchema with column information
            
        Raises:
            GlueClientError: If table not found
        """
        # Check cache first
        if table_name in self._schema_cache:
            return self._schema_cache[table_name]
        
        # Fetch from Glue Catalog
        table_metadata = self.glue_client.get_table(table_name)
        
        # Convert to simplified schema
        columns = {col.name: col.type for col in table_metadata.columns}
        
        schema = TableSchema(
            name=table_metadata.name,
            columns=columns,
            description=table_metadata.description,
            primary_keys=self._extract_primary_keys(table_metadata),
            foreign_keys=self._extract_foreign_keys(table_metadata)
        )
        
        # Cache the schema
        self._schema_cache[table_name] = schema
        
        return schema
    
    def get_all_table_schemas(self) -> Dict[str, TableSchema]:
        """
        Get schemas for all tables in the database.
        
        Returns:
            Dictionary mapping table names to their schemas
        """
        table_names = self.list_tables()
        schemas = {}
        
        for table_name in table_names:
            try:
                schemas[table_name] = self.get_table_schema(table_name)
            except GlueClientError as e:
                print(f"Warning: Failed to get schema for {table_name}: {e}")
        
        return schemas
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        
        Returns:
            List of table names
        """
        if self._all_tables_cache is None:
            self._all_tables_cache = self.glue_client.list_tables()
        
        return self._all_tables_cache
    
    def get_column_type(self, table_name: str, column_name: str) -> Optional[str]:
        """
        Get data type for a specific column.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            
        Returns:
            Data type string or None if not found
        """
        schema = self.get_table_schema(table_name)
        return schema.columns.get(column_name)
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Get list of column names for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column names
        """
        schema = self.get_table_schema(table_name)
        return list(schema.columns.keys())
    
    def get_tables_with_column(self, column_name: str) -> List[str]:
        """
        Find all tables that contain a specific column.
        
        Args:
            column_name: Name of the column to search for
            
        Returns:
            List of table names containing the column
        """
        tables_with_column = []
        
        for table_name in self.list_tables():
            schema = self.get_table_schema(table_name)
            if column_name in schema.columns:
                tables_with_column.append(table_name)
        
        return tables_with_column
    
    def get_related_tables(self, table_name: str) -> List[str]:
        """
        Get tables related to the given table through foreign keys.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of related table names
        """
        schema = self.get_table_schema(table_name)
        related_tables = []
        
        if schema.foreign_keys:
            for fk_ref in schema.foreign_keys.values():
                # Extract table name from "table.column" format
                if '.' in fk_ref:
                    related_table = fk_ref.split('.')[0]
                    if related_table not in related_tables:
                        related_tables.append(related_table)
        
        return related_tables
    
    def generate_table_context(self, table_name: str) -> str:
        """
        Generate human-readable context about a table for LLM prompts.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Formatted string describing the table
        """
        schema = self.get_table_schema(table_name)
        
        context = f"Table: {schema.name}\n"
        
        if schema.description:
            context += f"Description: {schema.description}\n"
        
        context += "Columns:\n"
        for col_name, col_type in schema.columns.items():
            context += f"  - {col_name} ({col_type})\n"
        
        if schema.primary_keys:
            context += f"Primary Keys: {', '.join(schema.primary_keys)}\n"
        
        if schema.foreign_keys:
            context += "Foreign Keys:\n"
            for col, ref in schema.foreign_keys.items():
                context += f"  - {col} -> {ref}\n"
        
        return context
    
    def generate_all_tables_context(self, tables: Optional[List[str]] = None) -> str:
        """
        Generate context for multiple tables.
        
        Args:
            tables: List of table names (all tables if None)
            
        Returns:
            Formatted string describing all tables
        """
        if tables is None:
            tables = self.list_tables()
        
        context = "Database Schema:\n\n"
        
        for table_name in tables:
            context += self.generate_table_context(table_name)
            context += "\n"
        
        return context
    
    def clear_cache(self):
        """Clear the schema cache."""
        self._schema_cache.clear()
        self._all_tables_cache = None
    
    def _extract_primary_keys(self, table_metadata: TableMetadata) -> Optional[List[str]]:
        """
        Extract primary key columns from table metadata.
        
        Args:
            table_metadata: Table metadata from Glue
            
        Returns:
            List of primary key column names or None
        """
        # Check table parameters for primary key information
        if table_metadata.parameters:
            pk_param = table_metadata.parameters.get('primary_keys')
            if pk_param:
                return [pk.strip() for pk in pk_param.split(',')]
        
        # Default primary keys based on table name conventions
        pk_mapping = {
            'product': ['product_code'],
            'warehouse_product': ['warehouse_code', 'product_code'],
            'sales_order_header': ['sales_order_prefix', 'sales_order_number'],
            'sales_order_line': ['sales_order_prefix', 'sales_order_number', 'sales_order_line'],
            'purchase_order_header': ['purchase_order_prefix', 'purchase_order_number'],
            'purchase_order_line': ['purchase_order_prefix', 'purchase_order_number', 'purchase_order_line']
        }
        
        return pk_mapping.get(table_metadata.name)
    
    def _extract_foreign_keys(self, table_metadata: TableMetadata) -> Optional[Dict[str, str]]:
        """
        Extract foreign key relationships from table metadata.
        
        Args:
            table_metadata: Table metadata from Glue
            
        Returns:
            Dictionary mapping column names to referenced table.column
        """
        # Check table parameters for foreign key information
        if table_metadata.parameters:
            fk_param = table_metadata.parameters.get('foreign_keys')
            if fk_param:
                fks = {}
                for fk in fk_param.split(';'):
                    if '->' in fk:
                        col, ref = fk.split('->')
                        fks[col.strip()] = ref.strip()
                return fks if fks else None
        
        # Default foreign keys based on table name conventions
        fk_mapping = {
            'warehouse_product': {
                'product_code': 'product.product_code'
            },
            'sales_order_line': {
                'sales_order_prefix': 'sales_order_header.sales_order_prefix',
                'sales_order_number': 'sales_order_header.sales_order_number',
                'product_code': 'product.product_code'
            },
            'purchase_order_line': {
                'purchase_order_prefix': 'purchase_order_header.purchase_order_prefix',
                'purchase_order_number': 'purchase_order_header.purchase_order_number',
                'product_code': 'product.product_code'
            }
        }
        
        return fk_mapping.get(table_metadata.name)
