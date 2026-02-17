"""
Amazon Redshift Serverless Client Wrapper

Provides a simplified interface for executing queries against Redshift Serverless using Data API.
"""

import boto3
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class QueryResult:
    """Result from a Redshift query."""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time: float
    bytes_scanned: int = 0
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert result to list of dictionaries."""
        return [dict(zip(self.columns, row)) for row in self.rows]


class RedshiftClientError(Exception):
    """Raised when Redshift API call fails."""
    pass


class RedshiftClient:
    """Client for Amazon Redshift Serverless Data API."""
    
    def __init__(
        self,
        region: str,
        workgroup_name: str,
        database: str,
        timeout: int = 30
    ):
        """
        Initialize Redshift client.
        
        Args:
            region: AWS region
            workgroup_name: Redshift Serverless workgroup name
            database: Database name
            timeout: Query timeout in seconds
        """
        self.region = region
        self.workgroup_name = workgroup_name
        self.database = database
        self.timeout = timeout
        
        try:
            self.client = boto3.client('redshift-data', region_name=region)
        except Exception as e:
            raise RedshiftClientError(f"Failed to initialize Redshift client: {e}")
    
    def execute_query(self, sql: str, parameters: Optional[List[Any]] = None) -> QueryResult:
        """
        Execute a SQL query and wait for results.
        
        Args:
            sql: SQL query to execute
            parameters: Optional query parameters for parameterized queries
            
        Returns:
            QueryResult with columns and rows
            
        Raises:
            RedshiftClientError: If query execution fails
        """
        start_time = time.time()
        
        try:
            # Submit query
            response = self.client.execute_statement(
                WorkgroupName=self.workgroup_name,
                Database=self.database,
                Sql=sql
            )
            
            query_id = response['Id']
            
            # Wait for query to complete
            result = self._wait_for_query(query_id)
            
            execution_time = time.time() - start_time
            
            # Get query results
            columns, rows = self._fetch_results(query_id)
            
            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time=execution_time
            )
            
        except self.client.exceptions.ValidationException as e:
            raise RedshiftClientError(f"Invalid SQL query: {e}")
        except Exception as e:
            raise RedshiftClientError(f"Query execution failed: {e}")
    
    def _wait_for_query(self, query_id: str) -> Dict[str, Any]:
        """
        Wait for query to complete.
        
        Args:
            query_id: Query ID from execute_statement
            
        Returns:
            Query status response
            
        Raises:
            RedshiftClientError: If query fails or times out
        """
        start_time = time.time()
        
        while True:
            # Check if timeout exceeded
            if time.time() - start_time > self.timeout:
                raise RedshiftClientError(f"Query timeout after {self.timeout} seconds")
            
            # Get query status
            response = self.client.describe_statement(Id=query_id)
            status = response['Status']
            
            if status == 'FINISHED':
                return response
            elif status == 'FAILED':
                error = response.get('Error', 'Unknown error')
                raise RedshiftClientError(f"Query failed: {error}")
            elif status == 'ABORTED':
                raise RedshiftClientError("Query was aborted")
            
            # Wait before checking again
            time.sleep(0.5)
    
    def _fetch_results(self, query_id: str) -> tuple[List[str], List[List[Any]]]:
        """
        Fetch query results.
        
        Args:
            query_id: Query ID
            
        Returns:
            Tuple of (column_names, rows)
        """
        columns = []
        rows = []
        next_token = None
        
        while True:
            # Get results page
            params = {'Id': query_id}
            if next_token:
                params['NextToken'] = next_token
            
            response = self.client.get_statement_result(**params)
            
            # Extract column names from first page
            if not columns:
                column_metadata = response.get('ColumnMetadata', [])
                columns = [col['name'] for col in column_metadata]
            
            # Extract rows
            records = response.get('Records', [])
            for record in records:
                row = [self._extract_value(field) for field in record]
                rows.append(row)
            
            # Check for more pages
            next_token = response.get('NextToken')
            if not next_token:
                break
        
        return columns, rows
    
    def _extract_value(self, field: Dict[str, Any]) -> Any:
        """
        Extract value from Redshift Data API field.
        
        Args:
            field: Field dictionary from API response
            
        Returns:
            Extracted value
        """
        if 'stringValue' in field:
            return field['stringValue']
        elif 'longValue' in field:
            return field['longValue']
        elif 'doubleValue' in field:
            return field['doubleValue']
        elif 'booleanValue' in field:
            return field['booleanValue']
        elif 'isNull' in field and field['isNull']:
            return None
        else:
            return str(field)
    
    def execute_batch(self, sql_statements: List[str]) -> List[QueryResult]:
        """
        Execute multiple SQL statements.
        
        Args:
            sql_statements: List of SQL statements to execute
            
        Returns:
            List of QueryResult objects
        """
        results = []
        for sql in sql_statements:
            result = self.execute_query(sql)
            results.append(result)
        return results
    
    def test_connection(self) -> bool:
        """
        Test connection to Redshift.
        
        Returns:
            True if connection successful
            
        Raises:
            RedshiftClientError: If connection fails
        """
        try:
            result = self.execute_query("SELECT 1 as test")
            return result.row_count == 1
        except Exception as e:
            raise RedshiftClientError(f"Connection test failed: {e}")
    
    def get_table_info(self, table_name: str) -> QueryResult:
        """
        Get information about a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            QueryResult with table column information
        """
        sql = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
        """
        return self.execute_query(sql)
    
    def list_tables(self, schema: str = 'public') -> QueryResult:
        """
        List all tables in a schema.
        
        Args:
            schema: Schema name (default: public)
            
        Returns:
            QueryResult with table names
        """
        sql = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{schema}'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        return self.execute_query(sql)
