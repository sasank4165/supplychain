"""SQL Agent for natural language to SQL query conversion and execution"""
import boto3
import json
import time
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

class SQLAgent(BaseAgent):
    """Agent that converts natural language to SQL and executes queries on Athena"""
    
    def __init__(self, persona: str, region: str = "us-east-1"):
        super().__init__(f"sql_agent_{persona}", persona, region)
        self.athena_client = boto3.client('athena', region_name=region)
        
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return SQL execution tool"""
        return [{
            "toolSpec": {
                "name": "execute_sql_query",
                "description": "Execute SQL query on Athena to retrieve supply chain data. Use this to answer questions about inventory, orders, products, suppliers, etc.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "sql_query": {
                                "type": "string",
                                "description": "The SQL query to execute on Athena"
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Brief explanation of what the query does"
                            }
                        },
                        "required": ["sql_query"]
                    }
                }
            }
        }]
    
    def get_schema_context(self) -> str:
        """Get schema information for the persona"""
        from config import SCHEMA_TABLES, PERSONA_TABLE_ACCESS, Persona, ATHENA_DATABASE
        
        persona_enum = Persona(self.persona)
        allowed_tables = PERSONA_TABLE_ACCESS[persona_enum]
        
        schema_info = f"Database: {ATHENA_DATABASE}\n\nAvailable Tables:\n\n"
        for table_name in allowed_tables:
            if table_name in SCHEMA_TABLES:
                table_info = SCHEMA_TABLES[table_name]
                schema_info += f"Table: {table_name}\n"
                schema_info += f"Description: {table_info['description']}\n"
                schema_info += f"Columns: {', '.join(table_info['columns'])}\n\n"
        
        return schema_info
    
    def natural_language_to_sql(self, query: str) -> Dict[str, str]:
        """Convert natural language query to SQL"""
        from config import ATHENA_DATABASE
        
        schema_context = self.get_schema_context()
        
        system_prompt = f"""You are a SQL expert for a supply chain database. Convert natural language queries to SQL.

{schema_context}

Rules:
1. Always use fully qualified table names: {ATHENA_DATABASE}.table_name
2. Use appropriate WHERE clauses to filter data
3. Use JOINs when data from multiple tables is needed
4. Return only valid SQL queries
5. Use aggregations (COUNT, SUM, AVG) when appropriate
6. Add ORDER BY and LIMIT clauses for better results
7. Handle date comparisons properly (dates are stored as bigint in YYYYMMDD format)
8. Column names with 'bigint' suffix are numeric, 'double' suffix are decimal numbers

Return response in JSON format:
{{"sql": "SELECT ...", "explanation": "Brief explanation"}}"""
        
        prompt = f"Convert this question to SQL: {query}"
        
        response = self.invoke_bedrock_model(prompt, system_prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # Fallback: extract SQL from response
            return {"sql": response, "explanation": "Generated SQL query"}
    
    def execute_athena_query(self, sql_query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute SQL query on Athena with table access validation"""
        from config import ATHENA_OUTPUT_LOCATION, ATHENA_DATABASE, PERSONA_TABLE_ACCESS, Persona
        
        # Validate table access if context provided
        if context and 'groups' in context:
            # Extract table names from SQL query
            tables_in_query = self._extract_tables_from_sql(sql_query)
            
            # Get allowed tables for user's persona
            persona = context.get('persona')
            try:
                persona_enum = Persona(persona)
                allowed_tables = PERSONA_TABLE_ACCESS.get(persona_enum, [])
                
                # Check if all tables in query are allowed
                for table in tables_in_query:
                    if table not in allowed_tables:
                        return {
                            "error": f"Access denied to table: {table}. Your role ({persona}) doesn't have permission to access this table.",
                            "status": 403
                        }
            except:
                return {"error": "Invalid persona", "status": 403}
        
        try:
            # Start query execution
            response = self.athena_client.start_query_execution(
                QueryString=sql_query,
                QueryExecutionContext={'Database': ATHENA_DATABASE},
                ResultConfiguration={'OutputLocation': ATHENA_OUTPUT_LOCATION}
            )
            
            query_execution_id = response['QueryExecutionId']
            
            # Wait for query to complete
            max_attempts = 30
            for _ in range(max_attempts):
                query_status = self.athena_client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )
                status = query_status['QueryExecution']['Status']['State']
                
                if status == 'SUCCEEDED':
                    break
                elif status in ['FAILED', 'CANCELLED']:
                    error_msg = query_status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                    return {"error": f"Query failed: {error_msg}"}
                
                time.sleep(1)
            
            # Get query results
            results = self.athena_client.get_query_results(
                QueryExecutionId=query_execution_id,
                MaxResults=100
            )
            
            # Parse results
            rows = results['ResultSet']['Rows']
            if len(rows) == 0:
                return {"data": [], "columns": []}
            
            # Extract column names
            columns = [col['VarCharValue'] for col in rows[0]['Data']]
            
            # Extract data rows
            data = []
            for row in rows[1:]:
                row_data = {}
                for i, col in enumerate(row['Data']):
                    row_data[columns[i]] = col.get('VarCharValue', '')
                data.append(row_data)
            
            return {
                "data": data,
                "columns": columns,
                "row_count": len(data)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def process_query(self, query: str, session_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process natural language query with access control"""
        
        # Convert to SQL
        sql_result = self.natural_language_to_sql(query)
        sql_query = sql_result.get("sql", "")
        explanation = sql_result.get("explanation", "")
        
        # Execute query with access control
        query_results = self.execute_athena_query(sql_query, context)
        
        # Format response
        if "error" in query_results:
            return {
                "success": False,
                "error": query_results["error"],
                "sql": sql_query,
                "explanation": explanation
            }
        
        return {
            "success": True,
            "sql": sql_query,
            "explanation": explanation,
            "results": query_results["data"],
            "columns": query_results["columns"],
            "row_count": query_results["row_count"]
        }

    
    def _extract_tables_from_sql(self, sql_query: str) -> List[str]:
        """Extract table names from SQL query"""
        import re
        
        # Simple regex to extract table names (after FROM and JOIN)
        # Format: database.table or just table
        pattern = r'(?:FROM|JOIN)\s+(?:`?[\w-]+`?\.)?`?([\w_]+)`?'
        matches = re.findall(pattern, sql_query, re.IGNORECASE)
        
        # Remove database prefix if present and deduplicate
        tables = list(set(matches))
        return tables
