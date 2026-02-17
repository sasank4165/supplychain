"""
Conversation Sidebar for Supply Chain AI Assistant

Displays conversation history with clickable past queries and cache statistics.
"""

import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator.query_orchestrator import QueryOrchestrator
from cache.query_cache import QueryCache


def display_conversation_sidebar(
    orchestrator: QueryOrchestrator,
    session_id: str,
    show_cache_stats: bool = True
):
    """
    Display conversation history and cache statistics in sidebar.
    
    Args:
        orchestrator: Query orchestrator instance
        session_id: Current session ID
        show_cache_stats: Whether to show cache statistics
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💬 Conversation History")
    
    # Get conversation history
    history = orchestrator.get_session_history(session_id)
    
    if not history:
        st.sidebar.info("No conversation history yet")
    else:
        display_history_list(history)
    
    # Clear history button
    if history:
        if st.sidebar.button("🗑️ Clear History", use_container_width=True):
            orchestrator.clear_session(session_id)
            st.session_state.query_history = []
            st.rerun()
    
    # Display cache statistics
    if show_cache_stats:
        st.sidebar.markdown("---")
        display_cache_stats_sidebar(orchestrator)


def display_history_list(history: list):
    """
    Display list of conversation history items.
    
    Args:
        history: List of Interaction objects
    """
    # Show last 10 interactions
    recent_history = history[-10:] if len(history) > 10 else history
    
    st.sidebar.caption(f"Showing last {len(recent_history)} of {len(history)} interactions")
    
    for i, interaction in enumerate(reversed(recent_history)):
        display_history_item(interaction, len(recent_history) - i)


def display_history_item(interaction: Any, index: int):
    """
    Display a single history item.
    
    Args:
        interaction: Interaction object
        index: Index number for display
    """
    # Get query text (truncate if too long)
    query_text = interaction.query
    if len(query_text) > 50:
        query_text = query_text[:47] + "..."
    
    # Create expander for each interaction
    with st.sidebar.expander(f"{index}. {query_text}", expanded=False):
        st.markdown(f"**Query:** {interaction.query}")
        
        # Show timestamp if available
        if hasattr(interaction, 'timestamp'):
            timestamp = interaction.timestamp
            if isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
                st.caption(f"🕐 {dt.strftime('%H:%M:%S')}")
        
        # Show response preview
        if interaction.response:
            response_preview = interaction.response
            if len(response_preview) > 100:
                response_preview = response_preview[:97] + "..."
            st.markdown(f"**Response:** {response_preview}")
        
        # Add button to re-run query
        if st.button("🔄 Re-run", key=f"rerun_{index}_{hash(interaction.query)}", use_container_width=True):
            st.session_state.rerun_query = interaction.query
            st.rerun()


def display_cache_stats_sidebar(orchestrator: QueryOrchestrator):
    """
    Display cache statistics in sidebar.
    
    Args:
        orchestrator: Query orchestrator instance
    """
    st.sidebar.markdown("### 📊 Cache Statistics")
    
    # Get cache stats
    cache_stats = orchestrator.get_cache_stats()
    
    if not cache_stats:
        st.sidebar.info("Cache statistics not available")
        return
    
    # Display metrics
    total_requests = cache_stats.get('total_requests', 0)
    cache_hits = cache_stats.get('cache_hits', 0)
    cache_misses = cache_stats.get('cache_misses', 0)
    hit_rate = cache_stats.get('hit_rate', 0.0)
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        st.metric(
            label="Hit Rate",
            value=f"{hit_rate:.1%}",
            help="Percentage of queries served from cache"
        )
    
    with col2:
        st.metric(
            label="Cached",
            value=cache_stats.get('cache_size', 0),
            help="Number of cached queries"
        )
    
    # Show detailed stats in expander
    with st.sidebar.expander("Cache Details", expanded=False):
        st.markdown(f"- **Total Requests:** {total_requests}")
        st.markdown(f"- **Cache Hits:** {cache_hits}")
        st.markdown(f"- **Cache Misses:** {cache_misses}")
        st.markdown(f"- **Hit Rate:** {hit_rate:.1%}")
        
        # Show memory usage if available
        if 'memory_usage' in cache_stats:
            st.markdown(f"- **Memory Usage:** {cache_stats['memory_usage']}")
    
    # Add button to clear cache
    if st.sidebar.button("🗑️ Clear Cache", use_container_width=True):
        orchestrator.invalidate_cache("")
        st.sidebar.success("Cache cleared")
        st.rerun()


def display_full_conversation_history(
    orchestrator: QueryOrchestrator,
    session_id: str
):
    """
    Display full conversation history in main area.
    
    Args:
        orchestrator: Query orchestrator instance
        session_id: Current session ID
    """
    st.markdown("### 💬 Full Conversation History")
    
    # Get conversation history
    history = orchestrator.get_session_history(session_id)
    
    if not history:
        st.info("No conversation history yet. Start by asking a question!")
        return
    
    st.caption(f"Total interactions: {len(history)}")
    
    # Display each interaction
    for i, interaction in enumerate(history, 1):
        with st.expander(f"Interaction {i}: {interaction.query[:50]}...", expanded=False):
            display_full_history_item(interaction, i)


def display_full_history_item(interaction: Any, index: int):
    """
    Display full details of a history item.
    
    Args:
        interaction: Interaction object
        index: Index number
    """
    # Display query
    st.markdown("#### Query")
    st.markdown(interaction.query)
    
    # Display timestamp
    if hasattr(interaction, 'timestamp'):
        timestamp = interaction.timestamp
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
            st.caption(f"🕐 {dt.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Display response
    st.markdown("#### Response")
    st.markdown(interaction.response)
    
    # Add re-run button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Re-run Query", key=f"rerun_full_{index}"):
            st.session_state.rerun_query = interaction.query
            st.rerun()


def get_rerun_query() -> Optional[str]:
    """
    Get query to re-run if one was clicked.
    
    Returns:
        Query text or None
    """
    if 'rerun_query' in st.session_state:
        query = st.session_state.rerun_query
        del st.session_state.rerun_query
        return query
    return None


def display_cache_management(orchestrator: QueryOrchestrator):
    """
    Display cache management interface.
    
    Args:
        orchestrator: Query orchestrator instance
    """
    st.markdown("### 📊 Cache Management")
    
    # Get cache stats
    cache_stats = orchestrator.get_cache_stats()
    
    if not cache_stats:
        st.info("Cache statistics not available")
        return
    
    # Display detailed statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Requests",
            value=cache_stats.get('total_requests', 0)
        )
    
    with col2:
        st.metric(
            label="Cache Hits",
            value=cache_stats.get('cache_hits', 0)
        )
    
    with col3:
        st.metric(
            label="Cache Misses",
            value=cache_stats.get('cache_misses', 0)
        )
    
    with col4:
        st.metric(
            label="Hit Rate",
            value=f"{cache_stats.get('hit_rate', 0.0):.1%}"
        )
    
    # Cache size and capacity
    st.markdown("#### Cache Status")
    
    cache_size = cache_stats.get('cache_size', 0)
    max_size = cache_stats.get('max_size', 1000)
    
    st.progress(cache_size / max_size if max_size > 0 else 0, 
                text=f"Cache Usage: {cache_size} / {max_size} entries")
    
    # Cache management actions
    st.markdown("#### Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear All Cache", use_container_width=True):
            count = orchestrator.invalidate_cache("")
            st.success(f"Cache cleared")
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Stats", use_container_width=True):
            st.rerun()


def show_conversation_tips():
    """Display tips for using conversation history."""
    with st.expander("💡 Conversation Tips", expanded=False):
        st.markdown("""
        **Using Conversation History:**
        - The system remembers your last 10 interactions
        - You can refer to previous queries using context (e.g., "Show me more details about that")
        - Click any past query to re-run it
        - Clear history when switching topics or personas
        
        **Cache Benefits:**
        - Identical queries return instantly from cache
        - Cache expires after 5 minutes for fresh data
        - Dashboard queries cached for 15 minutes
        - High hit rate = faster responses and lower costs
        """)
