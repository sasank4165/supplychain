"""
Query Tips and Best Practices

Provides helpful guidance to users on how to ask effective questions.
"""

import streamlit as st
from typing import Dict, List


def display_query_tips(persona: str):
    """
    Display query tips and best practices for the selected persona.
    
    Args:
        persona: Current user persona
    """
    with st.expander("💡 Query Tips & Best Practices", expanded=False):
        st.markdown("### How to Ask Effective Questions")
        
        # General tips
        st.markdown("#### General Guidelines")
        st.markdown("""
        - **Be specific**: Include warehouse codes, product codes, or date ranges
        - **Follow-up questions**: The system remembers your conversation, so you can ask follow-ups like "What about warehouse WH002?"
        - **One entity at a time**: For optimization tasks, ask about specific warehouses or products
        - **Use SQL for comparisons**: For comparing multiple entities, use data retrieval queries
        """)
        
        # Persona-specific tips
        st.markdown(f"#### Tips for {persona}")
        
        tips = get_persona_tips(persona)
        for tip_category, tip_list in tips.items():
            st.markdown(f"**{tip_category}:**")
            for tip in tip_list:
                st.markdown(f"- {tip}")
        
        # Common codes
        st.markdown("#### Example Codes to Try")
        codes = get_example_codes()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Warehouses:**")
            for code in codes['warehouses']:
                st.code(code, language=None)
        
        with col2:
            st.markdown("**Products:**")
            for code in codes['products'][:3]:
                st.code(code, language=None)
        
        # Limitations
        st.markdown("#### Current Limitations")
        st.markdown("""
        - **Comparative analysis**: Tools can only analyze one warehouse/product at a time
        - **Empty results**: If you get empty results, the entity may not exist or have no data
        - **Multi-step reasoning**: For complex comparisons, break your question into multiple queries
        """)
        
        # What works well
        st.markdown("#### What Works Well ✅")
        st.markdown("""
        - "Show me products with low stock in warehouse WH001"
        - "Calculate reorder point for product PROD001 at warehouse WH001"
        - "What about warehouse WH002?" (after asking about WH001)
        - "Show me all warehouses and their inventory levels"
        """)
        
        # What doesn't work yet
        st.markdown("#### What Needs Improvement ⚠️")
        st.markdown("""
        - "Which warehouse is at more risk?" (requires comparing multiple warehouses)
        - "Compare all suppliers" (need to specify which suppliers or product group)
        - Questions without specific codes when optimization is needed
        """)


def get_persona_tips(persona: str) -> Dict[str, List[str]]:
    """
    Get tips specific to a persona.
    
    Args:
        persona: User persona
        
    Returns:
        Dictionary of tip categories and tips
    """
    tips = {
        "Warehouse Manager": {
            "Data Queries": [
                "Ask about specific warehouses (e.g., WH001, WH002)",
                "Request inventory levels, stock status, or product lists",
                "Use date ranges for historical data"
            ],
            "Optimization Tasks": [
                "Calculate reorder points for specific products and warehouses",
                "Identify low stock products at a specific warehouse",
                "Forecast demand for individual products",
                "Check stockout risk for one warehouse at a time"
            ],
            "Follow-up Questions": [
                "After getting results for WH001, ask 'What about WH002?'",
                "Ask for more details about specific products from the results",
                "Request calculations based on the data you just retrieved"
            ]
        },
        "Field Engineer": {
            "Data Queries": [
                "Ask about specific orders or delivery areas",
                "Request order status, delivery schedules, or fulfillment data",
                "Query by date ranges or regions"
            ],
            "Optimization Tasks": [
                "Check fulfillment status for specific order IDs",
                "Identify delayed orders at a specific warehouse",
                "Calculate warehouse capacity for one warehouse",
                "Optimize routes for specific order lists"
            ],
            "Follow-up Questions": [
                "After seeing delayed orders, ask about specific order details",
                "Request route optimization for orders you just retrieved",
                "Ask about different warehouses or regions"
            ]
        },
        "Procurement Specialist": {
            "Data Queries": [
                "Ask about specific suppliers or product groups",
                "Request purchase order data, supplier lists, or cost information",
                "Query by time periods or spending thresholds"
            ],
            "Optimization Tasks": [
                "Analyze performance for specific suppliers",
                "Compare costs for a specific product group across suppliers",
                "Identify cost savings opportunities with threshold percentages",
                "Analyze purchase trends by supplier or product group"
            ],
            "Follow-up Questions": [
                "After seeing supplier data, ask for performance analysis",
                "Request cost comparisons for specific product groups",
                "Ask about trends over different time periods"
            ]
        }
    }
    
    return tips.get(persona, {})


def get_example_codes() -> Dict[str, List[str]]:
    """
    Get example codes that users can try.
    
    Returns:
        Dictionary of entity types and example codes
    """
    return {
        "warehouses": ["WH001", "WH002", "WH003"],
        "products": ["PROD001", "PROD002", "PROD003", "PROD095"],
        "suppliers": ["SUP001", "SUP002", "SUP003"],
        "orders": ["SO-2024-001", "SO-2024-002"],
        "product_groups": ["Electronics", "Hardware", "Software"]
    }


def show_quick_tips_banner():
    """Display a quick tips banner at the top of the page."""
    st.info("""
    💡 **Quick Tips**: 
    • Be specific with codes (WH001, PROD001) 
    • Ask follow-up questions naturally 
    • For comparisons, ask about each entity separately 
    • Check the tips section below for examples
    """)


def get_suggestion_for_empty_result(query: str, persona: str) -> str:
    """
    Generate a helpful suggestion when a query returns empty results.
    
    Args:
        query: The query that returned empty results
        persona: User persona
        
    Returns:
        Suggestion text
    """
    suggestions = []
    
    # Check if query mentions specific codes
    if "WH" not in query.upper() and persona == "Warehouse Manager":
        suggestions.append("Try specifying a warehouse code like WH001 or WH002")
    
    if "PROD" not in query.upper() and "product" in query.lower():
        suggestions.append("Try specifying a product code like PROD001")
    
    if "SUP" not in query.upper() and persona == "Procurement Specialist":
        suggestions.append("Try specifying a supplier code like SUP001")
    
    if not suggestions:
        suggestions.append("The entity you're asking about may not exist in the system")
        suggestions.append("Try asking for a list of available entities first")
    
    return " • ".join(suggestions)


def display_contextual_help(query: str, persona: str):
    """
    Display contextual help based on the query.
    
    Args:
        query: User's query
        persona: User persona
    """
    query_lower = query.lower()
    
    # Detect comparative questions
    if any(word in query_lower for word in ["which", "compare", "best", "worst", "most", "least"]):
        st.warning("""
        ⚠️ **Comparative Question Detected**: 
        This question requires comparing multiple entities. For best results:
        1. First, retrieve data for all entities using a SQL query
        2. Then ask about specific entities for detailed analysis
        3. Or ask about each entity separately and compare the results yourself
        """)
    
    # Detect missing codes
    if persona == "Warehouse Manager" and "warehouse" in query_lower and "WH" not in query.upper():
        st.info("💡 **Tip**: Include a warehouse code (e.g., WH001) for more specific results")
    
    if "product" in query_lower and "PROD" not in query.upper():
        st.info("💡 **Tip**: Include a product code (e.g., PROD001) for specific product analysis")
