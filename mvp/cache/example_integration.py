"""
Example: Cache and Conversation Memory Integration

Demonstrates how to use query cache and conversation memory together
in the orchestrator.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache.query_cache import QueryCache
from cache.cache_stats import CacheStatsTracker, format_cache_stats_for_ui
from memory.conversation_memory import ConversationMemory
from memory.context import Persona


def example_basic_usage():
    """Example: Basic cache and memory usage."""
    print("\n" + "="*60)
    print("EXAMPLE: Basic Cache and Memory Usage")
    print("="*60)
    
    # Initialize cache and memory
    cache = QueryCache(max_size=100, default_ttl=300)
    memory = ConversationMemory(max_history=10)
    
    # Create a session
    session_id = "user123"
    context = memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
    print(f"\n✓ Created session: {session_id}")
    
    # Simulate a query
    query = "Show me low stock items"
    persona = "Warehouse Manager"
    
    # Check cache
    cache_key = QueryCache.generate_cache_key(query, persona)
    cached_result = cache.get(cache_key)
    
    if cached_result:
        print(f"✓ Cache hit! Returning cached result")
        response = cached_result
    else:
        print(f"✓ Cache miss. Processing query...")
        # Simulate query processing
        response = f"Low stock items: Widget A (5 units), Widget B (3 units)"
        
        # Cache the result
        cache.set(cache_key, response, ttl=300)
        print(f"✓ Cached result for future queries")
    
    # Add to conversation memory
    memory.add_interaction(session_id, query, response)
    print(f"✓ Added interaction to conversation memory")
    
    # Get conversation history
    history = memory.get_history(session_id)
    print(f"\n📝 Conversation History ({len(history)} interactions):")
    for i, interaction in enumerate(history, 1):
        print(f"  {i}. Q: {interaction.query}")
        print(f"     A: {interaction.response[:50]}...")


def example_follow_up_query():
    """Example: Follow-up query using conversation context."""
    print("\n" + "="*60)
    print("EXAMPLE: Follow-up Query with Context")
    print("="*60)
    
    cache = QueryCache(max_size=100, default_ttl=300)
    memory = ConversationMemory(max_history=10)
    
    session_id = "user123"
    context = memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
    
    # First query
    query1 = "Show me products from supplier ABC"
    response1 = "Products from ABC: Widget A, Widget B, Widget C"
    memory.add_interaction(session_id, query1, response1)
    print(f"\n1st Query: {query1}")
    print(f"Response: {response1}")
    
    # Follow-up query (uses context)
    query2 = "What's the stock level for those products?"
    # In real implementation, the agent would use context to know "those products" refers to ABC products
    response2 = "Stock levels: Widget A (50), Widget B (30), Widget C (75)"
    memory.add_interaction(session_id, query2, response2)
    print(f"\n2nd Query: {query2}")
    print(f"Response: {response2}")
    
    # Show conversation history
    history = memory.get_history(session_id)
    print(f"\n📝 Full Conversation ({len(history)} interactions):")
    for i, interaction in enumerate(history, 1):
        print(f"  {i}. Q: {interaction.query}")
        print(f"     A: {interaction.response}")


def example_cache_performance():
    """Example: Cache performance with repeated queries."""
    print("\n" + "="*60)
    print("EXAMPLE: Cache Performance")
    print("="*60)
    
    cache = QueryCache(max_size=100, default_ttl=300)
    tracker = CacheStatsTracker()
    
    # Simulate dashboard queries (repeated frequently)
    dashboard_queries = [
        "Show total inventory value",
        "Show low stock items",
        "Show pending orders"
    ]
    
    print("\nSimulating 20 queries (mix of dashboard and unique queries)...")
    
    for i in range(20):
        # 70% dashboard queries, 30% unique queries
        if i % 10 < 7:
            query = dashboard_queries[i % len(dashboard_queries)]
        else:
            query = f"Unique query {i}"
        
        cache_key = QueryCache.generate_cache_key(query, "Warehouse Manager")
        
        # Check cache
        result = cache.get(cache_key)
        if result is None:
            # Simulate query execution
            result = f"Result for: {query}"
            cache.set(cache_key, result, ttl=900)  # Dashboard TTL: 15 min
    
    # Record snapshot
    snapshot = tracker.record_snapshot(cache.get_stats())
    
    # Display statistics
    print(f"\n{format_cache_stats_for_ui(cache.get_stats())}")
    print(f"Performance: {tracker._get_performance_rating(snapshot.hit_rate)}")


def example_persona_switch():
    """Example: Switching persona clears conversation history."""
    print("\n" + "="*60)
    print("EXAMPLE: Persona Switch")
    print("="*60)
    
    memory = ConversationMemory(max_history=10)
    session_id = "user123"
    
    # Start as Warehouse Manager
    context = memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
    memory.add_interaction(session_id, "Show inventory", "Inventory: ...")
    memory.add_interaction(session_id, "Show low stock", "Low stock: ...")
    
    print(f"\n✓ Warehouse Manager - {len(memory.get_history(session_id))} interactions")
    
    # Switch to Field Engineer
    memory.switch_persona(session_id, Persona.FIELD_ENGINEER, clear_history=True)
    print(f"✓ Switched to Field Engineer")
    print(f"✓ History cleared - {len(memory.get_history(session_id))} interactions")
    
    # Add new interactions
    memory.add_interaction(session_id, "Show deliveries", "Deliveries: ...")
    print(f"✓ Added new interaction - {len(memory.get_history(session_id))} interactions")


def example_session_cleanup():
    """Example: Automatic session cleanup."""
    print("\n" + "="*60)
    print("EXAMPLE: Session Cleanup")
    print("="*60)
    
    memory = ConversationMemory(max_history=10, session_timeout=2)  # 2 second timeout
    
    # Create multiple sessions
    memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    memory.create_session("session2", Persona.FIELD_ENGINEER)
    memory.create_session("session3", Persona.PROCUREMENT_SPECIALIST)
    
    print(f"\n✓ Created 3 sessions")
    print(f"✓ Active sessions: {memory.get_session_count()}")
    
    # Wait for timeout
    print("\n⏳ Waiting 3 seconds for timeout...")
    time.sleep(3)
    
    # Cleanup expired sessions
    removed = memory.cleanup_expired_sessions()
    print(f"\n✓ Cleaned up {removed} expired sessions")
    print(f"✓ Active sessions: {memory.get_session_count()}")


def example_statistics():
    """Example: Getting statistics."""
    print("\n" + "="*60)
    print("EXAMPLE: Statistics")
    print("="*60)
    
    cache = QueryCache(max_size=100, default_ttl=300)
    memory = ConversationMemory(max_history=10)
    
    # Add some data
    for i in range(5):
        session_id = f"session{i}"
        memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
        
        for j in range(3):
            query = f"Query {j} from session {i}"
            cache_key = QueryCache.generate_cache_key(query, "Warehouse Manager")
            
            # Simulate cache hits and misses
            result = cache.get(cache_key)
            if result is None:
                cache.set(cache_key, f"Result {j}")
            
            memory.add_interaction(session_id, query, f"Response {j}")
    
    # Get statistics
    cache_stats = cache.get_stats()
    memory_stats = memory.get_statistics()
    
    print("\n📊 Cache Statistics:")
    print(f"  • Size: {cache_stats['size']}/{cache_stats['max_size']}")
    print(f"  • Hit Rate: {cache_stats['hit_rate']:.1f}%")
    print(f"  • Hits: {cache_stats['hits']}, Misses: {cache_stats['misses']}")
    
    print("\n📊 Memory Statistics:")
    print(f"  • Active Sessions: {memory_stats['active_sessions']}")
    print(f"  • Total Interactions: {memory_stats['total_interactions']}")
    print(f"  • Avg Interactions/Session: {memory_stats['avg_interactions_per_session']:.1f}")


def run_all_examples():
    """Run all integration examples."""
    print("\n" + "="*60)
    print("CACHE AND MEMORY INTEGRATION EXAMPLES")
    print("="*60)
    
    example_basic_usage()
    example_follow_up_query()
    example_cache_performance()
    example_persona_switch()
    example_session_cleanup()
    example_statistics()
    
    print("\n" + "="*60)
    print("✅ ALL EXAMPLES COMPLETED")
    print("="*60)


if __name__ == "__main__":
    run_all_examples()
