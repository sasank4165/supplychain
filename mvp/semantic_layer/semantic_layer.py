"""
Semantic Layer - Maps business terms to SQL patterns

Provides business context and schema metadata to SQL agents for query generation.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from semantic_layer.schema_provider import SchemaProvider, TableSchema
    from semantic_layer.business_metrics import BusinessMetrics, MetricDefinition, Persona
except ImportError:
    # For standalone testing
    from schema_provider import SchemaProvider, TableSchema
    from business_metrics import BusinessMetrics, MetricDefinition, Persona


@dataclass
class EnrichedContext:
    """Enriched query context with business and schema information."""
    original_query: str
    persona: Persona
    relevant_tables: List[str]
    relevant_metrics: List[MetricDefinition]
    table_schemas: Dict[str, TableSchema]
    business_terms: Dict[str, str]
    suggested_joins: List[str]


class SemanticLayer:
    """
    Semantic layer that maps business terms to SQL patterns.
    
    Integrates with Glue Catalog for schema metadata and provides
    persona-specific business context for SQL generation.
    """
    
    def __init__(self, schema_provider: SchemaProvider, persona: Persona):
        """
        Initialize semantic layer.
        
        Args:
            schema_provider: SchemaProvider instance for schema access
            persona: Current user persona
        """
        self.schema_provider = schema_provider
        self.persona = persona
        self.business_metrics = BusinessMetrics()
    
    def enrich_query_context(self, query: str) -> EnrichedContext:
        """
        Enrich a user query with business and schema context.
        
        Args:
            query: Natural language query from user
            
        Returns:
            EnrichedContext with relevant information for SQL generation
        """
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
        # Find relevant metrics
        relevant_metrics = self.business_metrics.find_metric_by_keywords(
            keywords, 
            self.persona
        )
        
        # Determine relevant tables
        relevant_tables = self._identify_relevant_tables(query, relevant_metrics)
        
        # Get schemas for relevant tables
        table_schemas = {}
        for table_name in relevant_tables:
            try:
                table_schemas[table_name] = self.schema_provider.get_table_schema(table_name)
            except Exception as e:
                print(f"Warning: Could not get schema for {table_name}: {e}")
        
        # Get business terms
        business_terms = self._get_relevant_business_terms(query)
        
        # Suggest joins if multiple tables involved
        suggested_joins = self._suggest_joins(relevant_tables)
        
        return EnrichedContext(
            original_query=query,
            persona=self.persona,
            relevant_tables=relevant_tables,
            relevant_metrics=relevant_metrics,
            table_schemas=table_schemas,
            business_terms=business_terms,
            suggested_joins=suggested_joins
        )
    
    def get_business_metrics(self) -> Dict[str, MetricDefinition]:
        """
        Get all business metrics for current persona.
        
        Returns:
            Dictionary of metric name to MetricDefinition
        """
        return self.business_metrics.get_metrics_for_persona(self.persona)
    
    def get_table_schema(self, table_name: str) -> TableSchema:
        """
        Get schema for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            TableSchema with column information
        """
        return self.schema_provider.get_table_schema(table_name)
    
    def get_allowed_tables(self) -> List[str]:
        """
        Get list of tables allowed for current persona.
        
        Returns:
            List of table names
        """
        # Define table access by persona
        table_access = {
            Persona.WAREHOUSE_MANAGER: [
                'product',
                'warehouse_product',
                'sales_order_header',
                'sales_order_line'
            ],
            Persona.FIELD_ENGINEER: [
                'product',
                'warehouse_product',
                'sales_order_header',
                'sales_order_line'
            ],
            Persona.PROCUREMENT_SPECIALIST: [
                'product',
                'warehouse_product',
                'purchase_order_header',
                'purchase_order_line'
            ]
        }
        
        return table_access.get(self.persona, [])
    
    def resolve_business_term(self, term: str) -> Optional[str]:
        """
        Resolve a business term to its SQL pattern.
        
        Args:
            term: Business term (e.g., "low stock", "overdue")
            
        Returns:
            SQL pattern or None if not found
        """
        business_terms = self.business_metrics.get_common_business_terms()
        return business_terms.get(term.lower())
    
    def generate_schema_context_for_llm(self, tables: Optional[List[str]] = None) -> str:
        """
        Generate schema context for LLM prompt.
        
        Args:
            tables: List of table names (uses allowed tables if None)
            
        Returns:
            Formatted string with schema information
        """
        if tables is None:
            tables = self.get_allowed_tables()
        
        context = f"You are helping a {self.persona.value} with their query.\n\n"
        context += "Available Tables:\n\n"
        
        for table_name in tables:
            try:
                context += self.schema_provider.generate_table_context(table_name)
                context += "\n"
            except Exception as e:
                print(f"Warning: Could not generate context for {table_name}: {e}")
        
        return context
    
    def generate_business_metrics_context_for_llm(self) -> str:
        """
        Generate business metrics context for LLM prompt.
        
        Returns:
            Formatted string with business metrics information
        """
        metrics = self.get_business_metrics()
        
        if not metrics:
            return ""
        
        context = f"\nBusiness Metrics for {self.persona.value}:\n\n"
        
        for metric_name, metric in metrics.items():
            context += f"- {metric.name}: {metric.description}\n"
            if metric.example_query:
                context += f"  Example: \"{metric.example_query}\"\n"
            context += f"  SQL Pattern: {metric.sql_pattern}\n"
            context += f"  Tables: {', '.join(metric.tables)}\n\n"
        
        return context
    
    def generate_full_context_for_llm(self, query: str) -> str:
        """
        Generate complete context for LLM including schema and business metrics.
        
        Args:
            query: User's natural language query
            
        Returns:
            Formatted string with all relevant context
        """
        enriched = self.enrich_query_context(query)
        
        context = self.generate_schema_context_for_llm(enriched.relevant_tables)
        context += self.generate_business_metrics_context_for_llm()
        
        # Add business terms if found
        if enriched.business_terms:
            context += "\nRelevant Business Terms:\n"
            for term, sql_pattern in enriched.business_terms.items():
                context += f"- \"{term}\" translates to: {sql_pattern}\n"
            context += "\n"
        
        # Add suggested joins if multiple tables
        if enriched.suggested_joins:
            context += "\nSuggested Table Joins:\n"
            for join in enriched.suggested_joins:
                context += f"- {join}\n"
            context += "\n"
        
        return context
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from query for metric matching.
        
        Args:
            query: Natural language query
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction - split on spaces and remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                     'can', 'could', 'may', 'might', 'must', 'what', 'which', 'who', 'when',
                     'where', 'why', 'how', 'show', 'me', 'my', 'get', 'find', 'list'}
        
        words = query.lower().replace('?', '').replace(',', '').split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def _identify_relevant_tables(self, query: str, metrics: List[MetricDefinition]) -> List[str]:
        """
        Identify relevant tables for a query.
        
        Args:
            query: Natural language query
            metrics: Relevant metrics found
            
        Returns:
            List of table names
        """
        relevant_tables = set()
        
        # Add tables from relevant metrics
        for metric in metrics:
            relevant_tables.update(metric.tables)
        
        # If no metrics matched, use keyword-based table detection
        if not relevant_tables:
            query_lower = query.lower()
            allowed_tables = self.get_allowed_tables()
            
            # Check for table-related keywords
            table_keywords = {
                'product': ['product', 'item', 'sku'],
                'warehouse_product': ['inventory', 'stock', 'warehouse'],
                'sales_order_header': ['order', 'sale', 'customer', 'delivery'],
                'sales_order_line': ['order line', 'order item', 'fulfillment'],
                'purchase_order_header': ['purchase', 'po', 'supplier'],
                'purchase_order_line': ['purchase line', 'receipt']
            }
            
            for table, keywords in table_keywords.items():
                if table in allowed_tables:
                    if any(kw in query_lower for kw in keywords):
                        relevant_tables.add(table)
        
        # If still no tables, default to core tables for persona
        if not relevant_tables:
            if self.persona == Persona.WAREHOUSE_MANAGER:
                relevant_tables = {'warehouse_product', 'product'}
            elif self.persona == Persona.FIELD_ENGINEER:
                relevant_tables = {'sales_order_header', 'sales_order_line'}
            elif self.persona == Persona.PROCUREMENT_SPECIALIST:
                relevant_tables = {'purchase_order_header', 'purchase_order_line'}
        
        return list(relevant_tables)
    
    def _get_relevant_business_terms(self, query: str) -> Dict[str, str]:
        """
        Find business terms in the query.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary of found terms and their SQL patterns
        """
        all_terms = self.business_metrics.get_common_business_terms()
        query_lower = query.lower()
        
        relevant_terms = {}
        for term, sql_pattern in all_terms.items():
            if term in query_lower:
                relevant_terms[term] = sql_pattern
        
        return relevant_terms
    
    def _suggest_joins(self, tables: List[str]) -> List[str]:
        """
        Suggest JOIN clauses for multiple tables.
        
        Args:
            tables: List of table names
            
        Returns:
            List of suggested JOIN statements
        """
        if len(tables) <= 1:
            return []
        
        joins = []
        tables_set = set(tables)
        
        # Define common join patterns
        join_patterns = [
            # Product joins
            ('warehouse_product', 'product', 
             'warehouse_product.product_code = product.product_code'),
            
            # Sales order joins
            ('sales_order_line', 'sales_order_header',
             'sales_order_line.sales_order_prefix = sales_order_header.sales_order_prefix AND '
             'sales_order_line.sales_order_number = sales_order_header.sales_order_number'),
            ('sales_order_line', 'product',
             'sales_order_line.product_code = product.product_code'),
            
            # Purchase order joins
            ('purchase_order_line', 'purchase_order_header',
             'purchase_order_line.purchase_order_prefix = purchase_order_header.purchase_order_prefix AND '
             'purchase_order_line.purchase_order_number = purchase_order_header.purchase_order_number'),
            ('purchase_order_line', 'product',
             'purchase_order_line.product_code = product.product_code'),
        ]
        
        for table1, table2, join_condition in join_patterns:
            if table1 in tables_set and table2 in tables_set:
                joins.append(f"JOIN {table2} ON {join_condition}")
        
        return joins
