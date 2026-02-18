"""
Intent Classifier

Classifies user queries into intent types to determine routing strategy.
Uses Bedrock to classify queries as SQL_QUERY, OPTIMIZATION, or HYBRID.
"""

from enum import Enum
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aws.bedrock_client import BedrockClient, BedrockClientError


class Intent(Enum):
    """Query intent types."""
    SQL_QUERY = "SQL_QUERY"  # Data retrieval query
    OPTIMIZATION = "OPTIMIZATION"  # Specialized agent task
    HYBRID = "HYBRID"  # Requires both SQL and specialized agent


class IntentClassifier:
    """
    Classifies user queries into intent types.
    
    Uses Bedrock to determine whether a query needs:
    - SQL_QUERY: Data retrieval from database
    - OPTIMIZATION: Specialized agent tools (calculations, analysis)
    - HYBRID: Both SQL data retrieval and optimization
    """
    
    def __init__(self, bedrock_client: BedrockClient, logger=None):
        """
        Initialize intent classifier.
        
        Args:
            bedrock_client: BedrockClient instance for classification
            logger: Optional logger instance
        """
        self.bedrock_client = bedrock_client
        self.logger = logger
    
    def classify(self, query: str, persona: str, context=None) -> Intent:
        """
        Classify a user query into an intent type.
        
        Args:
            query: User's natural language query
            persona: User's persona (Warehouse Manager, Field Engineer, Procurement Specialist)
            context: Optional conversation context for follow-up questions
            
        Returns:
            Intent enum value
            
        Raises:
            BedrockClientError: If classification fails
        """
        try:
            self._log_info(f"Classifying query for persona '{persona}': {query[:100]}...")
            
            # Build classification prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(query, persona, context)
            
            # Call Bedrock for classification
            response = self.bedrock_client.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            # Parse intent from response
            intent = self._parse_intent(response.content)
            
            self._log_info(f"Classified as: {intent.value}")
            
            return intent
            
        except BedrockClientError as e:
            self._log_error(f"Intent classification failed: {e}")
            # Default to SQL_QUERY on error
            self._log_info("Defaulting to SQL_QUERY intent")
            return Intent.SQL_QUERY
        except Exception as e:
            self._log_error(f"Unexpected error during classification: {e}")
            # Default to SQL_QUERY on error
            return Intent.SQL_QUERY
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for intent classification."""
        return """You are an intent classifier for a supply chain AI assistant.

Your task is to classify user queries into one of three intent types:

1. SQL_QUERY: The query asks for data retrieval from the database
   Examples:
   - "Show me all products with low stock"
   - "What orders are scheduled for delivery today?"
   - "List all suppliers for product group Electronics"
   - "How many orders were placed last month?"

2. OPTIMIZATION: The query asks for calculations, analysis, or recommendations
   Examples:
   - "Calculate the reorder point for product ABC123"
   - "Optimize delivery routes for these orders"
   - "Analyze supplier performance for the last 90 days"
   - "What's the best route for deliveries in the North area?"

3. HYBRID: The query requires both data retrieval AND optimization/analysis
   Examples:
   - "Show me low stock products and calculate their reorder points"
   - "Find delayed orders and suggest optimized routes"
   - "List all suppliers and compare their costs"
   - "Get products below minimum stock and forecast demand"

IMPORTANT:
- Respond with ONLY the intent type: SQL_QUERY, OPTIMIZATION, or HYBRID
- Do not include any explanation or additional text
- If unsure, default to SQL_QUERY"""
    
    def _build_user_prompt(self, query: str, persona: str, context=None) -> str:
        """
        Build user prompt for intent classification.
        
        Args:
            query: User's query
            persona: User's persona
            context: Optional conversation context
            
        Returns:
            User prompt string
        """
        prompt = f"Persona: {persona}\n"
        
        # Add conversation context if available
        if context and hasattr(context, 'history') and context.history:
            prompt += "\nPrevious conversation:\n"
            for interaction in context.history[-2:]:  # Last 2 interactions
                prompt += f"Q: {interaction.query}\n"
                prompt += f"A: {interaction.response[:100]}...\n"
            prompt += "\n"
        
        prompt += f"Query: {query}\n\n"
        prompt += "Classify this query as SQL_QUERY, OPTIMIZATION, or HYBRID.\n"
        prompt += "Respond with only the intent type:"
        
        return prompt
    
    def _parse_intent(self, response: str) -> Intent:
        """
        Parse intent from Bedrock response.
        
        Args:
            response: Response text from Bedrock
            
        Returns:
            Intent enum value
        """
        # Clean up response
        response = response.strip().upper()
        
        # Check for intent keywords
        if "HYBRID" in response:
            return Intent.HYBRID
        elif "OPTIMIZATION" in response:
            return Intent.OPTIMIZATION
        elif "SQL_QUERY" in response or "SQL" in response:
            return Intent.SQL_QUERY
        else:
            # Default to SQL_QUERY if unclear
            self._log_warning(f"Could not parse intent from response: {response}. Defaulting to SQL_QUERY")
            return Intent.SQL_QUERY
    
    def _log_info(self, message: str):
        """Log info message."""
        if self.logger:
            self.logger.info(f"[IntentClassifier] {message}")
    
    def _log_warning(self, message: str):
        """Log warning message."""
        if self.logger:
            self.logger.warning(f"[IntentClassifier] {message}")
    
    def _log_error(self, message: str):
        """Log error message."""
        if self.logger:
            self.logger.error(f"[IntentClassifier] {message}")
