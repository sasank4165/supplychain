"""
Cost Dashboard for Supply Chain AI Assistant

Displays per-query and daily costs with service breakdown.
"""

import streamlit as st
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cost.cost_tracker import CostTracker, Cost


def display_cost_dashboard(
    cost_tracker: CostTracker,
    session_id: Optional[str] = None,
    show_session_costs: bool = True
):
    """
    Display cost dashboard with per-query and daily costs.
    
    Args:
        cost_tracker: CostTracker instance
        session_id: Current session ID (optional)
        show_session_costs: Whether to show session-level costs
    """
    st.markdown("### 💰 Cost Tracker")
    
    if not cost_tracker.enabled:
        st.info("Cost tracking is disabled")
        return
    
    # Get costs
    daily_cost = cost_tracker.get_daily_cost()
    session_cost = cost_tracker.get_session_cost(session_id) if session_id else Cost()
    monthly_estimate = cost_tracker.get_monthly_estimate()
    
    # Display metrics in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Today's Cost",
            value=f"${daily_cost.total_cost:.4f}",
            help="Total cost for all queries today"
        )
    
    with col2:
        if show_session_costs and session_id:
            st.metric(
                label="Session Cost",
                value=f"${session_cost.total_cost:.4f}",
                help="Total cost for your current session"
            )
        else:
            st.metric(
                label="Monthly Estimate",
                value=f"${monthly_estimate:.2f}",
                help="Estimated monthly cost based on today's usage"
            )
    
    with col3:
        st.metric(
            label="Tokens Used Today",
            value=f"{daily_cost.tokens_used.input_tokens + daily_cost.tokens_used.output_tokens:,}",
            help="Total Bedrock tokens used today"
        )
    
    # Cost breakdown
    with st.expander("📊 Cost Breakdown", expanded=False):
        display_cost_breakdown(cost_tracker, session_id, show_session_costs)
    
    # Monthly estimate details
    with st.expander("📅 Monthly Estimate", expanded=False):
        display_monthly_estimate(cost_tracker, daily_cost, monthly_estimate)


def display_cost_breakdown(
    cost_tracker: CostTracker,
    session_id: Optional[str],
    show_session_costs: bool
):
    """
    Display detailed cost breakdown by service.
    
    Args:
        cost_tracker: CostTracker instance
        session_id: Current session ID
        show_session_costs: Whether to show session costs
    """
    # Get costs
    daily_cost = cost_tracker.get_daily_cost()
    session_cost = cost_tracker.get_session_cost(session_id) if session_id else Cost()
    
    # Create tabs for different views
    if show_session_costs and session_id:
        tab1, tab2 = st.tabs(["Daily Breakdown", "Session Breakdown"])
    else:
        tab1 = st.container()
        tab2 = None
    
    with tab1:
        st.markdown("**Daily Cost Breakdown**")
        display_service_breakdown(daily_cost)
    
    if tab2:
        with tab2:
            st.markdown("**Session Cost Breakdown**")
            display_service_breakdown(session_cost)


def display_service_breakdown(cost: Cost):
    """
    Display cost breakdown by service.
    
    Args:
        cost: Cost object
    """
    # Create metrics for each service
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🤖 Bedrock",
            value=f"${cost.bedrock_cost:.4f}",
            help="Amazon Bedrock API costs"
        )
        if cost.tokens_used.input_tokens > 0 or cost.tokens_used.output_tokens > 0:
            st.caption(f"In: {cost.tokens_used.input_tokens:,} | Out: {cost.tokens_used.output_tokens:,}")
    
    with col2:
        st.metric(
            label="🗄️ Redshift",
            value=f"${cost.redshift_cost:.4f}",
            help="Redshift Serverless query costs"
        )
    
    with col3:
        st.metric(
            label="⚡ Lambda",
            value=f"${cost.lambda_cost:.4f}",
            help="AWS Lambda execution costs"
        )
    
    # Show percentage breakdown
    if cost.total_cost > 0:
        st.markdown("**Cost Distribution**")
        
        bedrock_pct = (cost.bedrock_cost / cost.total_cost) * 100
        redshift_pct = (cost.redshift_cost / cost.total_cost) * 100
        lambda_pct = (cost.lambda_cost / cost.total_cost) * 100
        
        st.progress(bedrock_pct / 100, text=f"Bedrock: {bedrock_pct:.1f}%")
        st.progress(redshift_pct / 100, text=f"Redshift: {redshift_pct:.1f}%")
        st.progress(lambda_pct / 100, text=f"Lambda: {lambda_pct:.1f}%")


def display_monthly_estimate(
    cost_tracker: CostTracker,
    daily_cost: Cost,
    monthly_estimate: float
):
    """
    Display monthly cost estimate with details.
    
    Args:
        cost_tracker: CostTracker instance
        daily_cost: Today's cost
        monthly_estimate: Estimated monthly cost
    """
    st.markdown("**Monthly Cost Estimate**")
    st.info(f"Based on today's usage: **${monthly_estimate:.2f}** per month")
    
    # Show calculation
    st.caption(f"Calculation: ${daily_cost.total_cost:.4f} (today) × 30 days = ${monthly_estimate:.2f}")
    
    # Show service breakdown for monthly estimate
    st.markdown("**Estimated Monthly Breakdown**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Bedrock",
            value=f"${daily_cost.bedrock_cost * 30:.2f}"
        )
    
    with col2:
        st.metric(
            label="Redshift",
            value=f"${daily_cost.redshift_cost * 30:.2f}"
        )
    
    with col3:
        st.metric(
            label="Lambda",
            value=f"${daily_cost.lambda_cost * 30:.2f}"
        )
    
    with col4:
        st.metric(
            label="Total",
            value=f"${monthly_estimate:.2f}"
        )
    
    # Add note about estimate accuracy
    st.caption("⚠️ This is an estimate based on today's usage. Actual costs may vary based on daily query volume.")


def display_query_cost(cost: Cost, execution_time: float):
    """
    Display cost for a single query.
    
    Args:
        cost: Cost object for the query
        execution_time: Query execution time in seconds
    """
    st.markdown("#### Query Cost")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Total Cost",
            value=f"${cost.total_cost:.4f}",
            help="Total cost for this query"
        )
    
    with col2:
        st.metric(
            label="Execution Time",
            value=f"{execution_time:.2f}s",
            help="Query execution time"
        )
    
    # Show breakdown
    with st.expander("Cost Details", expanded=False):
        st.markdown(f"- **Bedrock:** ${cost.bedrock_cost:.4f}")
        st.markdown(f"- **Redshift:** ${cost.redshift_cost:.4f}")
        st.markdown(f"- **Lambda:** ${cost.lambda_cost:.4f}")
        
        if cost.tokens_used.input_tokens > 0 or cost.tokens_used.output_tokens > 0:
            st.markdown(f"- **Tokens:** {cost.tokens_used.input_tokens:,} in / {cost.tokens_used.output_tokens:,} out")


def display_cost_summary_sidebar(cost_tracker: CostTracker, session_id: Optional[str] = None):
    """
    Display compact cost summary in sidebar.
    
    Args:
        cost_tracker: CostTracker instance
        session_id: Current session ID
    """
    if not cost_tracker.enabled:
        return
    
    st.sidebar.markdown("### 💰 Cost Tracker")
    
    # Get costs
    daily_cost = cost_tracker.get_daily_cost()
    monthly_estimate = cost_tracker.get_monthly_estimate()
    
    # Display compact metrics
    st.sidebar.metric("Today", f"${daily_cost.total_cost:.4f}")
    st.sidebar.metric("Est. Monthly", f"${monthly_estimate:.2f}")
    
    if session_id:
        session_cost = cost_tracker.get_session_cost(session_id)
        st.sidebar.metric("Session", f"${session_cost.total_cost:.4f}")
    
    # Show tokens
    total_tokens = daily_cost.tokens_used.input_tokens + daily_cost.tokens_used.output_tokens
    st.sidebar.caption(f"🎫 Tokens: {total_tokens:,}")


def format_cost(cost: float) -> str:
    """
    Format cost as currency string.
    
    Args:
        cost: Cost in USD
        
    Returns:
        Formatted cost string
    """
    if cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1.0:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def get_cost_color(cost: float, threshold_low: float = 0.05, threshold_high: float = 0.20) -> str:
    """
    Get color for cost display based on thresholds.
    
    Args:
        cost: Cost value
        threshold_low: Low threshold (green)
        threshold_high: High threshold (red)
        
    Returns:
        Color name
    """
    if cost < threshold_low:
        return "green"
    elif cost < threshold_high:
        return "orange"
    else:
        return "red"
