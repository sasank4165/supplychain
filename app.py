"""Streamlit application for Supply Chain Agentic AI with Authentication"""
import streamlit as st
import json
import uuid
import os
from datetime import datetime
from orchestrator import SupplyChainOrchestrator
from config import Persona
from auth.auth_manager import AuthManager
from auth.login_ui import (
    render_login_page,
    render_user_profile,
    render_change_password_dialog,
    check_authentication,
    get_current_user
)
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Supply Chain AI Assistant",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize orchestrator
@st.cache_resource
def get_orchestrator():
    return SupplyChainOrchestrator()

# Initialize auth manager
@st.cache_resource
def get_auth_manager():
    user_pool_id = os.getenv("USER_POOL_ID", "us-east-1_xxxxx")
    client_id = os.getenv("USER_POOL_CLIENT_ID", "xxxxx")
    region = os.getenv("AWS_REGION", "us-east-1")
    return AuthManager(user_pool_id, client_id, region)

orchestrator = get_orchestrator()
auth_manager = get_auth_manager()

# Session state initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Check authentication
if not check_authentication():
    render_login_page(auth_manager)
    st.stop()

# Get current user
current_user = get_current_user()
if not current_user:
    st.error("Session expired. Please login again.")
    st.session_state.authenticated = False
    st.rerun()

# Set persona from user's role
st.session_state.persona = current_user['persona']

# Sidebar
with st.sidebar:
    st.title("📦 Supply Chain AI")
    st.markdown("---")
    
    # Display user role (read-only, based on authentication)
    st.subheader("Your Role")
    persona_display = {
        "warehouse_manager": "Warehouse Manager",
        "field_engineer": "Field Engineer",
        "procurement_specialist": "Procurement Specialist"
    }
    
    st.info(f"🎭 {persona_display.get(st.session_state.persona, 'Unknown')}")
    st.caption("Role is determined by your user group")
    
    st.markdown("---")
    
    # Show agent capabilities
    st.subheader("Available Agents")
    capabilities = orchestrator.get_agent_capabilities(st.session_state.persona)
    
    st.markdown("**SQL Agent**")
    st.caption("Natural language queries for data retrieval")
    
    st.markdown("**Specialist Agent**")
    if "specialist_agent" in capabilities:
        st.caption(capabilities["specialist_agent"]["name"].replace("_", " ").title())
        with st.expander("Available Tools"):
            for tool in capabilities["specialist_agent"]["tools"]:
                st.text(f"• {tool.replace('_', ' ').title()}")
    
    st.markdown("---")
    
    # Session info
    st.subheader("Session Info")
    st.caption(f"Session ID: {st.session_state.session_id[:8]}...")
    st.caption(f"Messages: {len(st.session_state.messages)}")
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    
    # User profile and logout
    render_user_profile(auth_manager)

# Change password dialog
if st.session_state.get('show_change_password'):
    render_change_password_dialog(auth_manager)

# Main content
st.title("Supply Chain AI Assistant")
st.markdown(f"**Logged in as:** {current_user['username']} ({persona_display.get(st.session_state.persona)})")

# Example queries based on persona
with st.expander("💡 Example Queries"):
    if st.session_state.persona == "warehouse_manager":
        st.markdown("""
        - Show me current stock levels for all products in warehouse WH01
        - Which products are below minimum stock levels?
        - Forecast demand for product P12345 for the next 30 days
        - Suggest optimal reorder points for warehouse WH01
        - What are the top 10 products by sales volume?
        """)
    elif st.session_state.persona == "field_engineer":
        st.markdown("""
        - Show me all pending orders for delivery today
        - Which orders are delayed or at risk?
        - Optimize delivery route for orders SO001, SO002, SO003
        - Check fulfillment status of order SO12345
        - Calculate warehouse capacity for WH01
        """)
    else:  # procurement_specialist
        st.markdown("""
        - Show me all purchase orders from supplier SUP001
        - Analyze supplier performance for the last 90 days
        - Compare costs across suppliers for product group PG01
        - Identify cost savings opportunities
        - What are the purchase order trends for the last 6 months?
        """)

# Chat interface
chat_container = st.container()

with chat_container:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display additional data if available
            if "data" in message:
                if message["data"].get("sql_response"):
                    sql_resp = message["data"]["sql_response"]
                    if sql_resp.get("success") and sql_resp.get("results"):
                        st.markdown("**Query Results:**")
                        df = pd.DataFrame(sql_resp["results"])
                        st.dataframe(df, use_container_width=True)
                        st.caption(f"SQL: `{sql_resp.get('sql', '')}`")

# Chat input
if prompt := st.chat_input("Ask me anything about your supply chain..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process query with authentication context
    with st.chat_message("assistant"):
        with st.spinner("Processing your query..."):
            # Add user context for access control
            user_context = {
                "username": current_user['username'],
                "groups": current_user['groups'],
                "persona": current_user['persona']
            }
            
            result = orchestrator.process_query(
                query=prompt,
                persona=st.session_state.persona,
                session_id=st.session_state.session_id,
                context=user_context
            )
            
            # Format response
            if result.get("success"):
                response_text = ""
                
                # SQL response
                if "sql_response" in result:
                    sql_resp = result["sql_response"]
                    if sql_resp.get("success"):
                        response_text += f"**Data Retrieved:** {sql_resp.get('row_count', 0)} rows\n\n"
                        if sql_resp.get("results"):
                            df = pd.DataFrame(sql_resp["results"])
                            st.dataframe(df, use_container_width=True)
                            st.caption(f"SQL: `{sql_resp.get('sql', '')}`")
                
                # Specialist response
                if "specialist_response" in result:
                    spec_resp = result["specialist_response"]
                    if spec_resp.get("response"):
                        response_text += spec_resp["response"]
                
                if not response_text:
                    response_text = "Query processed successfully."
                
                st.markdown(response_text)
                
                # Save assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "data": result
                })
            else:
                error_msg = result.get("error", "An error occurred processing your query.")
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ {error_msg}"
                })

# Footer
st.markdown("---")
st.caption("Powered by AWS Bedrock, Athena, and Lambda")
