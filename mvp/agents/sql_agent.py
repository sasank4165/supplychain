"""
SQL Agent - Converts natural language to SQL and executes queries

Base SQL agent class that integrates with Bedrock for SQL generation,
semantic layer for business context, and Redshift for query execution.
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, AgentResponse
from aws.bedrock_client import BedrockClient, BedrockResponse, BedrockClientError
from aws.redshift_client import RedshiftClient, QueryResult, RedshiftClientError
from semantic_layer.semantic_layer import SemanticLayer, EnrichedContext
from semantic_layer.business_metrics import Persona

# Import ConversationContext from memory module
from memory.context import ConversationContext


@dataclass
class SQLResponse:
    """Response from SQL agent."""
    query: str
    sql: str
    results: Optional[QueryResult]
    formatted_response: str
    execution_time: float
    cached: bool = False


class SQLAgent(BaseAgent):
    """
    SQL Agent that converts natural language to SQL and executes queries.
    
    Integrates with:
    - Bedrock for SQL generation
    - Semantic layer for business context
    - Redshift for query execution
    """
    
    def __init__(
        self,
        agent_name: str,
        persona: Persona,
        bedrock_client: BedrockClient,
        redshift_client: RedshiftClient,
        semantic_layer: SemanticLayer,
        logger=None
    ):
        """
        Initialize SQL agent.
        
        Args:
            agent_name: Name of the agent
            persona: User persona for this agent
            bedrock_client: Bedrock client for SQL generation
            redshift_client: Redshift client for query execution
            semantic_layer: Semantic layer for business context
            logger: Optional logger
        """
        super().__init__(agent_name, logger)
        self.persona = persona
        self.bedrock_client = bedrock_client
        self.redshift_client = redshift_client
        self.semantic_layer = semantic_layer
    
    def process_query(
        self,
        query: str,
        context: Optional[ConversationContext] = None
    ) -> AgentResponse:
        """
        Process a natural language query.
        
        Args:
            query: Natural language query from user
            context: Optional conversation context
            
        Returns:
            AgentResponse with SQL results
        """
        start_time = time.time()
        
        try:
            self.log_info(f"Processing query: {query}")
            
            # Generate SQL from natural language
            sql = self.generate_sql(query, context)
            self.log_debug(f"Generated SQL: {sql}")
            
            # Validate SQL
            if not self._validate_sql(sql):
                return self.create_error_response(
                    "Generated SQL failed validation. Please rephrase your query.",
                    execution_time=time.time() - start_time
                )
            
            # Execute SQL
            result = self.execute_sql(sql)
            self.log_info(f"Query returned {result.row_count} rows in {result.execution_time:.2f}s")
            
            # Format results
            formatted_response = self.format_results(result, query)
            
            execution_time = time.time() - start_time
            
            # Create SQL response
            sql_response = SQLResponse(
                query=query,
                sql=sql,
                results=result,
                formatted_response=formatted_response,
                execution_time=execution_time,
                cached=False
            )
            
            return self.create_success_response(
                content=formatted_response,
                data=sql_response,
                execution_time=execution_time,
                metadata={
                    'sql': sql,
                    'row_count': result.row_count,
                    'persona': self.persona.value
                }
            )
            
        except BedrockClientError as e:
            return self.handle_exception(e, "generating SQL", time.time() - start_time)
        except RedshiftClientError as e:
            return self.handle_exception(e, "executing query", time.time() - start_time)
        except Exception as e:
            return self.handle_exception(e, "processing query", time.time() - start_time)
    
    def generate_sql(
        self,
        query: str,
        context: Optional[ConversationContext] = None
    ) -> str:
        """
        Generate SQL from natural language query.
        
        Args:
            query: Natural language query
            context: Optional conversation context
            
        Returns:
            Generated SQL query
            
        Raises:
            BedrockClientError: If SQL generation fails
        """
        # Get enriched context from semantic layer
        enriched_context = self.semantic_layer.enrich_query_context(query)
        
        # Build system prompt with schema and business context
        system_prompt = self._build_system_prompt(enriched_context)
        
        # Build user prompt with query and conversation context
        user_prompt = self._build_user_prompt(query, context, enriched_context)
        
        # Call Bedrock to generate SQL
        response = self.bedrock_client.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt
        )
        
        # Extract SQL from response
        sql = self._extract_sql_from_response(response.content)
        
        return sql
    
    def execute_sql(self, sql: str) -> QueryResult:
        """
        Execute SQL query against Redshift.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            QueryResult with data
            
        Raises:
            RedshiftClientError: If query execution fails
        """
        return self.redshift_client.execute_query(sql)
    
    def format_results(self, result: QueryResult, original_query: str) -> str:
        """
        Format query results for display.
        
        Args:
            result: Query result from Redshift
            original_query: Original user query
            
        Returns:
            Formatted response string
        """
        if result.row_count == 0:
            return "No results found for your query."
        
        # Create a summary
        summary = f"Found {result.row_count} result{'s' if result.row_count != 1 else ''}.\n\n"
        
        # For small result sets, include the data
        if result.row_count <= 10:
            summary += "Results:\n"
            for row_dict in result.to_dict_list():
                summary += "- " + ", ".join(f"{k}: {v}" for k, v in row_dict.items()) + "\n"
        else:
            summary += f"Showing first 10 of {result.row_count} results:\n"
            for row_dict in result.to_dict_list()[:10]:
                summary += "- " + ", ".join(f"{k}: {v}" for k, v in row_dict.items()) + "\n"
            summary += f"\n... and {result.row_count - 10} more rows."
        
        return summary
    
    def _build_system_prompt(self, enriched_context: EnrichedContext) -> str:
        """
        Build system prompt for SQL generation.
        
        Args:
            enriched_context: Enriched context from semantic layer
            
        Returns:
            System prompt string
        """
        prompt = f"""You are a SQL expert helping a {self.persona.value} query their supply chain database.

Your task is to convert natural language queries into valid Redshift SQL.

IMPORTANT RULES:
1. Generate ONLY valid Redshift SQL syntax
2. Use ONLY the tables and columns provided in the schema
3. Always use proper JOIN conditions when joining tables
4. Use appropriate WHERE clauses to filter data
5. Return the SQL query wrapped in ```sql code blocks
6. Do NOT include any explanations, only the SQL query
7. DO NOT use DELETE, UPDATE, DROP, or other destructive operations
8. Use LIMIT clauses for queries that might return many rows
9. CRITICAL: If the user asks a follow-up question (e.g., "what about X?" or "show me more"), refer to the previous conversation to understand the context and maintain continuity

"""
        
        # Add schema context
        prompt += self.semantic_layer.generate_schema_context_for_llm(
            enriched_context.relevant_tables
        )
        
        # Add business metrics context
        prompt += self.semantic_layer.generate_business_metrics_context_for_llm()
        
        return prompt
    
    def _build_user_prompt(
        self,
        query: str,
        context: Optional[ConversationContext],
        enriched_context: EnrichedContext
    ) -> str:
        """
        Build user prompt for SQL generation.
        
        Args:
            query: User's natural language query
            context: Conversation context
            enriched_context: Enriched context from semantic layer
            
        Returns:
            User prompt string
        """
        prompt = f"Convert this query to SQL: {query}\n\n"
        
        # Add conversation context if available
        if context and context.history:
            prompt += "Previous conversation:\n"
            for interaction in context.history[-3:]:  # Last 3 interactions
                prompt += f"Q: {interaction.query}\n"
                # Truncate response to avoid overwhelming context
                response_preview = interaction.response[:200] + "..." if len(interaction.response) > 200 else interaction.response
                prompt += f"A: {response_preview}\n"
            prompt += "\n"
        
        # Add business terms if found
        if enriched_context.business_terms:
            prompt += "Relevant business terms:\n"
            for term, sql_pattern in enriched_context.business_terms.items():
                prompt += f"- '{term}' means: {sql_pattern}\n"
            prompt += "\n"
        
        # Add suggested joins if multiple tables
        if enriched_context.suggested_joins:
            prompt += "Suggested joins:\n"
            for join in enriched_context.suggested_joins:
                prompt += f"- {join}\n"
            prompt += "\n"
        
        prompt += "Generate the SQL query now:"
        
        return prompt
    
    def _extract_sql_from_response(self, response: str) -> str:
        """
        Extract SQL query from Bedrock response.
        
        Args:
            response: Response text from Bedrock
            
        Returns:
            Extracted SQL query
        """
        # Look for SQL in code blocks
        if "```sql" in response:
            start = response.find("```sql") + 6
            end = response.find("```", start)
            sql = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            sql = response[start:end].strip()
        else:
            # No code blocks, use the whole response
            sql = response.strip()
        
        # Remove any trailing semicolons
        sql = sql.rstrip(';').strip()
        
        return sql
    
    def _validate_sql(self, sql: str) -> bool:
        """
        Validate SQL query for safety.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            True if valid, False otherwise
        """
        sql_upper = sql.upper()
        
        # Check for destructive operations
        destructive_keywords = ['DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
        for keyword in destructive_keywords:
            if keyword in sql_upper:
                self.log_error(f"SQL validation failed: Contains destructive keyword '{keyword}'")
                return False
        
        # Check that it's a SELECT query
        if not sql_upper.strip().startswith('SELECT'):
            self.log_error("SQL validation failed: Not a SELECT query")
            return False
        
        # Check for allowed tables
        allowed_tables = self.semantic_layer.get_allowed_tables()
        
        # Basic check - ensure query references at least one allowed table
        has_allowed_table = any(table in sql_upper for table in [t.upper() for t in allowed_tables])
        
        if not has_allowed_table:
            self.log_error("SQL validation failed: No allowed tables referenced")
            return False
        
        return True
    
    def get_persona(self) -> Persona:
        """Get the persona for this agent."""
        return self.persona
    
    def get_allowed_tables(self) -> List[str]:
        """Get list of allowed tables for this agent's persona."""
        return self.semantic_layer.get_allowed_tables()
