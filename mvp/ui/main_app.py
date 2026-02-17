"""
Main Application Interface for Supply Chain AI Assistant

Provides persona selector, query input, and integrates with orchestrator.
"""

import streamlit as st
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator.query_orchestrator import QueryOrchestrator, QueryResponse
from auth.auth_manager import User


def render_main_interface(
    orchestrator: QueryOrchestrator,
    user: User,
    session_id: str
) -> Optional[QueryResponse]:
    """
    Render main application interface with persona selector and query input.
    
    Args:
        orchestrator: Query orchestrator instance
        user: Current authenticated user
        session_id: Current session ID
        
    Returns:
        QueryResponse if query submitted, None otherwise
    """
    # Initialize session state for current persona
    if 'current_persona' not in st.session_state:
        st.session_state.current_persona = user.personas[0] if user.personas else None
    
    # Initialize query history in session state
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    # Initialize loading state
    if 'is_loading' not in st.session_state:
        st.session_state.is_loading = False
    
    # Persona selector
    st.subheader("Select Your Role")
    
    # Get authorized personas for user
    authorized_personas = user.personas
    
    if not authorized_personas:
        st.error("You have no authorized personas. Please contact your administrator.")
        return None
    
    # Persona selector dropdown
    previous_persona = st.session_state.current_persona
    selected_persona = st.selectbox(
        "Persona",
        options=authorized_personas,
        index=authorized_personas.index(st.session_state.current_persona) if st.session_state.current_persona in authorized_personas else 0,
        key="persona_selector",
        help="Select your role to access relevant data and tools"
    )
    
    # Update current persona
    st.session_state.current_persona = selected_persona
    
    # If persona changed, clear conversation history
    if previous_persona != selected_persona and previous_persona is not None:
        orchestrator.switch_persona(session_id, selected_persona)
        st.info(f"Switched to {selected_persona}. Conversation history cleared.")
    
    # Display persona description
    persona_descriptions = {
        "Warehouse Manager": "📦 Manage inventory, track stock levels, and optimize warehouse operations",
        "Field Engineer": "🚚 Track deliveries, optimize routes, and manage order fulfillment",
        "Procurement Specialist": "📊 Analyze suppliers, manage purchase orders, and optimize costs"
    }
    
    if selected_persona in persona_descriptions:
        st.info(persona_descriptions[selected_persona])
    
    st.markdown("---")
    
    # Query input section
    st.subheader("Ask a Question")
    
    # Query input form
    with st.form("query_form", clear_on_submit=True):
        query_input = st.text_area(
            "Enter your query",
            placeholder="e.g., Show me products with low stock levels\ne.g., Calculate reorder points for warehouse WH001\ne.g., Which suppliers have the best performance?",
            height=100,
            max_chars=1000,
            key="query_input"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            submit_button = st.form_submit_button(
                "Submit Query",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            clear_history = st.form_submit_button(
                "Clear History",
                use_container_width=True
            )
        
        with col3:
            # Placeholder for future features
            pass
        
        if clear_history:
            orchestrator.clear_session(session_id)
            st.session_state.query_history = []
            st.success("Conversation history cleared")
            return None
        
        if submit_button:
            if not query_input or not query_input.strip():
                st.error("Please enter a query")
                return None
            
            # Set loading state
            st.session_state.is_loading = True
            
            # Process query
            with st.spinner("Processing your query..."):
                try:
                    response = orchestrator.process_query(
                        query=query_input.strip(),
                        persona=selected_persona,
                        session_id=session_id
                    )
                    
                    # Add to query history
                    st.session_state.query_history.append({
                        'query': query_input.strip(),
                        'persona': selected_persona,
                        'response': response
                    })
                    
                    # Clear loading state
                    st.session_state.is_loading = False
                    
                    return response
                    
                except Exception as e:
                    st.session_state.is_loading = False
                    st.error(f"Error processing query: {str(e)}")
                    return None
    
    return None


def show_loading_indicator():
    """Display loading indicator when query is being processed."""
    if st.session_state.get('is_loading', False):
        with st.spinner("Processing your query..."):
            st.empty()


def get_persona_icon(persona: str) -> str:
    """
    Get icon for persona.
    
    Args:
        persona: Persona name
        
    Returns:
        Icon emoji
    """
    icons = {
        "Warehouse Manager": "📦",
        "Field Engineer": "🚚",
        "Procurement Specialist": "📊"
    }
    return icons.get(persona, "👤")


def show_example_queries(persona: str):
    """
    Display example queries for the selected persona.
    
    Args:
        persona: Current persona
    """
    examples = {
        "Warehouse Manager": [
            "Show me products with stock below minimum levels",
            "Calculate reorder points for all products in warehouse WH001",
            "What products are at risk of stockout in the next 7 days?",
            "Show me inventory levels across all warehouses"
        ],
        "Field Engineer": [
            "Show me orders scheduled for delivery today",
            "Which orders are delayed?",
            "Optimize delivery route for orders in the North region",
            "What is the fulfillment status of order SO-2024-001?"
        ],
        "Procurement Specialist": [
            "Show me top 10 suppliers by order volume",
            "Analyze supplier performance for the last 90 days",
            "Compare costs between suppliers for product group Electronics",
            "Which purchase orders are pending delivery?"
        ]
    }
    
    if persona in examples:
        with st.expander("💡 Example Queries", expanded=False):
            st.markdown("Try these example queries:")
            for example in examples[persona]:
                if st.button(example, key=f"example_{hash(example)}", use_container_width=True):
                    st.session_state.example_query = example
                    st.rerun()


def get_example_query() -> Optional[str]:
    """
    Get example query if one was clicked.
    
    Returns:
        Example query text or None
    """
    if 'example_query' in st.session_state:
        query = st.session_state.example_query
        del st.session_state.example_query
        return query
    return None
