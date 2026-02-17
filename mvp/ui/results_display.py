"""
Results Display for Supply Chain AI Assistant

Formats and displays query results with table and chart visualizations.
"""

import streamlit as st
import pandas as pd
from typing import Any, Dict, Optional
import json
import sys
import os
from io import StringIO

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator.query_orchestrator import QueryResponse
from orchestrator.intent_classifier import Intent


def display_query_response(response: QueryResponse):
    """
    Display query response with formatted results.
    
    Args:
        response: QueryResponse from orchestrator
    """
    # Display query info
    st.markdown("### Query Results")
    
    # Show if cached
    if response.cached:
        st.success("✓ Results retrieved from cache")
    
    # Display intent badge
    intent_colors = {
        Intent.SQL_QUERY: "blue",
        Intent.OPTIMIZATION: "green",
        Intent.HYBRID: "orange"
    }
    intent_color = intent_colors.get(response.intent, "gray")
    st.markdown(f"**Intent:** :{intent_color}[{response.intent.value}]")
    
    # Display execution time
    st.caption(f"⏱️ Execution time: {response.total_execution_time:.2f}s")
    
    st.markdown("---")
    
    # Check if query was successful
    if not response.agent_response.success:
        st.error("❌ Query Failed")
        st.error(response.agent_response.content)
        return
    
    # Display success message
    st.success("✓ Query executed successfully")
    
    # Display response content
    if response.agent_response.content:
        st.markdown("#### Response")
        st.markdown(response.agent_response.content)
    
    # Display data if available
    if response.agent_response.data:
        display_data(response.agent_response.data, response.intent)
    
    # Display metadata if available
    if response.agent_response.metadata:
        display_metadata(response.agent_response.metadata)


def display_data(data: Any, intent: Intent):
    """
    Display data with appropriate visualization.
    
    Args:
        data: Data to display (DataFrame, dict, list, etc.)
        intent: Query intent for context
    """
    st.markdown("#### Data")
    
    # Handle different data types
    if isinstance(data, pd.DataFrame):
        display_dataframe(data)
    elif isinstance(data, dict):
        display_dict_data(data, intent)
    elif isinstance(data, list):
        display_list_data(data)
    else:
        # Fallback: display as text
        st.text(str(data))


def display_dataframe(df: pd.DataFrame):
    """
    Display DataFrame with table and optional charts.
    
    Args:
        df: Pandas DataFrame to display
    """
    if df.empty:
        st.info("No data returned")
        return
    
    # Display row count
    st.caption(f"📊 {len(df)} rows returned")
    
    # Display dataframe
    st.dataframe(df, use_container_width=True, hide_index=False)
    
    # Add export button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="query_results.csv",
        mime="text/csv",
        key=f"download_{id(df)}"
    )
    
    # Try to create visualizations if appropriate
    if len(df) > 0 and len(df.columns) >= 2:
        create_visualizations(df)


def display_dict_data(data: Dict, intent: Intent):
    """
    Display dictionary data.
    
    Args:
        data: Dictionary data
        intent: Query intent
    """
    # Check if it's a result set with rows
    if 'rows' in data and isinstance(data['rows'], list):
        # Convert to DataFrame
        df = pd.DataFrame(data['rows'])
        if 'columns' in data:
            df.columns = data['columns']
        display_dataframe(df)
    else:
        # Display as JSON
        st.json(data)
        
        # Add export button
        json_str = json.dumps(data, indent=2)
        st.download_button(
            label="📥 Download as JSON",
            data=json_str,
            file_name="query_results.json",
            mime="application/json",
            key=f"download_{id(data)}"
        )


def display_list_data(data: list):
    """
    Display list data.
    
    Args:
        data: List data
    """
    if not data:
        st.info("No data returned")
        return
    
    # Check if list of dicts (can convert to DataFrame)
    if all(isinstance(item, dict) for item in data):
        df = pd.DataFrame(data)
        display_dataframe(df)
    else:
        # Display as bullet list
        for item in data:
            st.markdown(f"- {item}")


def create_visualizations(df: pd.DataFrame):
    """
    Create automatic visualizations based on DataFrame content.
    
    Args:
        df: Pandas DataFrame
    """
    with st.expander("📈 Visualizations", expanded=False):
        # Detect numeric columns
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if not numeric_cols:
            st.info("No numeric columns available for visualization")
            return
        
        # Create tabs for different chart types
        tab1, tab2, tab3 = st.tabs(["Bar Chart", "Line Chart", "Summary Stats"])
        
        with tab1:
            create_bar_chart(df, numeric_cols)
        
        with tab2:
            create_line_chart(df, numeric_cols)
        
        with tab3:
            create_summary_stats(df, numeric_cols)


def create_bar_chart(df: pd.DataFrame, numeric_cols: list):
    """Create bar chart visualization."""
    if len(df) > 20:
        st.info("Showing top 20 rows for visualization")
        df_viz = df.head(20)
    else:
        df_viz = df
    
    # Select columns for chart
    col1, col2 = st.columns(2)
    
    with col1:
        x_col = st.selectbox(
            "X-axis",
            options=df.columns.tolist(),
            key="bar_x"
        )
    
    with col2:
        y_col = st.selectbox(
            "Y-axis",
            options=numeric_cols,
            key="bar_y"
        )
    
    if x_col and y_col:
        try:
            st.bar_chart(df_viz.set_index(x_col)[y_col])
        except Exception as e:
            st.error(f"Could not create bar chart: {str(e)}")


def create_line_chart(df: pd.DataFrame, numeric_cols: list):
    """Create line chart visualization."""
    if len(df) > 50:
        st.info("Showing top 50 rows for visualization")
        df_viz = df.head(50)
    else:
        df_viz = df
    
    # Select columns for chart
    col1, col2 = st.columns(2)
    
    with col1:
        x_col = st.selectbox(
            "X-axis",
            options=df.columns.tolist(),
            key="line_x"
        )
    
    with col2:
        y_col = st.selectbox(
            "Y-axis",
            options=numeric_cols,
            key="line_y"
        )
    
    if x_col and y_col:
        try:
            st.line_chart(df_viz.set_index(x_col)[y_col])
        except Exception as e:
            st.error(f"Could not create line chart: {str(e)}")


def create_summary_stats(df: pd.DataFrame, numeric_cols: list):
    """Create summary statistics."""
    if numeric_cols:
        st.markdown("**Summary Statistics**")
        st.dataframe(df[numeric_cols].describe(), use_container_width=True)
    else:
        st.info("No numeric columns for summary statistics")


def display_metadata(metadata: Dict):
    """
    Display metadata information.
    
    Args:
        metadata: Metadata dictionary
    """
    with st.expander("ℹ️ Additional Information", expanded=False):
        # Display SQL query if available
        if 'sql_query' in metadata:
            st.markdown("**SQL Query:**")
            st.code(metadata['sql_query'], language='sql')
        
        # Display tool calls if available
        if 'tool_calls' in metadata:
            st.markdown("**Tools Used:**")
            for tool in metadata['tool_calls']:
                st.markdown(f"- {tool}")
        
        # Display any other metadata
        other_metadata = {k: v for k, v in metadata.items() 
                         if k not in ['sql_query', 'tool_calls']}
        
        if other_metadata:
            st.markdown("**Other Metadata:**")
            st.json(other_metadata)


def display_error(error_message: str):
    """
    Display error message.
    
    Args:
        error_message: Error message to display
    """
    st.error("❌ Error")
    st.error(error_message)


def display_query_history(history: list):
    """
    Display query history.
    
    Args:
        history: List of previous queries and responses
    """
    if not history:
        st.info("No query history yet")
        return
    
    st.markdown("### Recent Queries")
    
    for i, item in enumerate(reversed(history[-10:])):  # Show last 10
        with st.expander(f"Query {len(history) - i}: {item['query'][:50]}...", expanded=False):
            st.markdown(f"**Persona:** {item['persona']}")
            st.markdown(f"**Query:** {item['query']}")
            
            if item['response']:
                response = item['response']
                st.markdown(f"**Status:** {'✓ Success' if response.agent_response.success else '❌ Failed'}")
                st.markdown(f"**Execution Time:** {response.total_execution_time:.2f}s")
                
                if response.agent_response.content:
                    st.markdown("**Response:**")
                    st.text(response.agent_response.content[:200] + "..." if len(response.agent_response.content) > 200 else response.agent_response.content)


def format_number(value: Any) -> str:
    """
    Format number for display.
    
    Args:
        value: Value to format
        
    Returns:
        Formatted string
    """
    if isinstance(value, (int, float)):
        if isinstance(value, float):
            return f"{value:,.2f}"
        else:
            return f"{value:,}"
    return str(value)


def create_metric_cards(metrics: Dict[str, Any]):
    """
    Create metric cards for key values.
    
    Args:
        metrics: Dictionary of metric name to value
    """
    if not metrics:
        return
    
    # Create columns for metrics
    num_metrics = len(metrics)
    cols = st.columns(min(num_metrics, 4))
    
    for i, (label, value) in enumerate(metrics.items()):
        with cols[i % 4]:
            st.metric(label=label, value=format_number(value))
