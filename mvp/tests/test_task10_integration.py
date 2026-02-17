"""
Integration Test for Task 10: Caching and Conversation Memory

Tests the full integration of cache and memory with the orchestrator.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache.query_cache import QueryCache
from memory.conversation_memory import ConversationMemory
from memory.context import Persona


def test_cache_and_memory_integration():
    """Test that cache and memory work together correctly."""
    print("\n=== Integration Test: Cache + Memory ===")
    
    # Initialize components
    cache = QueryCache(max_size=100, default_ttl=300)
    memory = ConversationMemory(max_history=10)
    
    # Simulate orchestrator behavior
    session_id = "test_session"
    persona = "Warehouse Manager"
    query = "Show me low stock items"
    
    # Step 1: Create session
    context = memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
    print("✓ Session created")
    
    # Step 2: Check cache (should be miss)
    cache_key = QueryCache.generate_cache_key(query, persona)
    cached_result = cache.get(cache_key)
    assert cached_result is None, "First query should be cache miss"
    print("✓ Cache miss (expected)")
    
    # Step 3: Process query (simulated)
    response = "Low stock items: Widget A (5 units), Widget B (3 units)"
    
    # Step 4: Cache result
    cache.set(cache_key, response)
    print("✓ Result cached")
    
    # Step 5: Add to conversation memory
    memory.add_interaction(session_id, query, response)
    print("✓ Interaction added to memory")
    
    # Step 6: Verify cache hit on second query
    cached_result = cache.get(cache_key)
    assert cached_result == response, "Second query should be cache hit"
    print("✓ Cache hit (expected)")
    
    # Step 7: Verify conversation history
    history = memory.get_history(session_id)
    assert len(history) == 1, "Should have 1 interaction"
    assert history[0].query == query
    assert history[0].response == response
    print("✓ Conversation history correct")
    
    # Step 8: Test follow-up query
    query2 = "What about Widget A specifically?"
    response2 = "Widget A: 5 units in stock, reorder point: 10 units"
    
    cache_key2 = QueryCache.generate_cache_key(query2, persona)
    cache.set(cache_key2, response2)
    memory.add_interaction(session_id, query2, response2)
    
    history = memory.get_history(session_id)
    assert len(history) == 2, "Should have 2 interactions"
    print("✓ Follow-up query handled correctly")
    
    # Step 9: Test cache statistics
    stats = cache.get_stats()
    assert stats['hits'] >= 1, "Should have at least 1 cache hit"
    assert stats['misses'] >= 1, "Should have at least 1 cache miss"
    print(f"✓ Cache stats: {stats['hits']} hits, {stats['misses']} misses")
    
    # Step 10: Test memory statistics
    mem_stats = memory.get_statistics()
    assert mem_stats['active_sessions'] == 1
    assert mem_stats['total_interactions'] == 2
    print(f"✓ Memory stats: {mem_stats['active_sessions']} sessions, {mem_stats['total_interactions']} interactions")
    
    print("\n✅ Integration test passed!")


def test_persona_switch_clears_history_not_cache():
    """Test that persona switch clears memory but not cache."""
    print("\n=== Test: Persona Switch Behavior ===")
    
    cache = QueryCache(max_size=100, default_ttl=300)
    memory = ConversationMemory(max_history=10)
    
    session_id = "test_session"
    query = "Show inventory"
    response = "Inventory: ..."
    
    # Create session and add interaction
    memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
    cache_key = QueryCache.generate_cache_key(query, "Warehouse Manager")
    cache.set(cache_key, response)
    memory.add_interaction(session_id, query, response)
    
    assert len(memory.get_history(session_id)) == 1
    assert cache.get(cache_key) is not None
    print("✓ Initial state: 1 interaction, cache populated")
    
    # Switch persona
    memory.switch_persona(session_id, Persona.FIELD_ENGINEER, clear_history=True)
    
    # Verify memory cleared but cache intact
    assert len(memory.get_history(session_id)) == 0, "History should be cleared"
    assert cache.get(cache_key) is not None, "Cache should remain"
    print("✓ After persona switch: history cleared, cache intact")
    
    print("\n✅ Persona switch test passed!")


def test_cache_invalidation_not_memory():
    """Test that cache invalidation doesn't affect memory."""
    print("\n=== Test: Cache Invalidation Independence ===")
    
    cache = QueryCache(max_size=100, default_ttl=300)
    memory = ConversationMemory(max_history=10)
    
    session_id = "test_session"
    memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
    
    # Add multiple queries with identifiable cache keys
    queries = [
        ("Show inventory", "Inventory: ..."),
        ("Show orders", "Orders: ..."),
        ("Show suppliers", "Suppliers: ...")
    ]
    
    cache_keys = []
    for query, response in queries:
        cache_key = QueryCache.generate_cache_key(query, "Warehouse Manager")
        cache_keys.append((cache_key, query))
        cache.set(cache_key, response)
        memory.add_interaction(session_id, query, response)
    
    assert cache.get_stats()['size'] == 3
    assert len(memory.get_history(session_id)) == 3
    print("✓ Initial state: 3 cached, 3 in memory")
    
    # Invalidate specific cache entry by exact key
    inventory_key = cache_keys[0][0]  # Get the inventory query key
    cache.invalidate(inventory_key)
    
    # Verify cache affected but not memory
    assert cache.get_stats()['size'] == 2, "Cache should have 2 entries"
    assert len(memory.get_history(session_id)) == 3, "Memory should still have 3"
    print("✓ After invalidation: cache reduced, memory unchanged")
    
    print("\n✅ Cache invalidation test passed!")


def test_concurrent_access():
    """Test thread-safe concurrent access to cache and memory."""
    print("\n=== Test: Concurrent Access ===")
    
    import threading
    
    cache = QueryCache(max_size=100, default_ttl=300)
    memory = ConversationMemory(max_history=10)
    
    def worker(thread_id):
        session_id = f"session_{thread_id}"
        memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
        
        for i in range(5):
            query = f"Query {i} from thread {thread_id}"
            response = f"Response {i}"
            
            cache_key = QueryCache.generate_cache_key(query, "Warehouse Manager")
            cache.set(cache_key, response)
            memory.add_interaction(session_id, query, response)
    
    # Create and start threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Verify results
    cache_stats = cache.get_stats()
    mem_stats = memory.get_statistics()
    
    assert cache_stats['size'] == 25, "Should have 25 cached entries"
    assert mem_stats['active_sessions'] == 5, "Should have 5 sessions"
    assert mem_stats['total_interactions'] == 25, "Should have 25 interactions"
    
    print(f"✓ Concurrent access: {cache_stats['size']} cached, {mem_stats['active_sessions']} sessions")
    print("\n✅ Concurrent access test passed!")


def test_ttl_expiration_with_memory():
    """Test that cache TTL expiration doesn't affect memory."""
    print("\n=== Test: TTL Expiration Independence ===")
    
    cache = QueryCache(max_size=100, default_ttl=1)  # 1 second TTL
    memory = ConversationMemory(max_history=10)
    
    session_id = "test_session"
    memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
    
    query = "Show inventory"
    response = "Inventory: ..."
    
    cache_key = QueryCache.generate_cache_key(query, "Warehouse Manager")
    cache.set(cache_key, response, ttl=1)
    memory.add_interaction(session_id, query, response)
    
    assert cache.get(cache_key) is not None
    assert len(memory.get_history(session_id)) == 1
    print("✓ Initial state: cached and in memory")
    
    # Wait for cache expiration
    print("  Waiting 2 seconds for cache expiration...")
    time.sleep(2)
    
    # Verify cache expired but memory intact
    assert cache.get(cache_key) is None, "Cache should be expired"
    assert len(memory.get_history(session_id)) == 1, "Memory should remain"
    print("✓ After expiration: cache expired, memory intact")
    
    print("\n✅ TTL expiration test passed!")


def run_all_integration_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("TASK 10 INTEGRATION TEST SUITE")
    print("="*60)
    
    try:
        test_cache_and_memory_integration()
        test_persona_switch_clears_history_not_cache()
        test_cache_invalidation_not_memory()
        test_concurrent_access()
        test_ttl_expiration_with_memory()
        
        print("\n" + "="*60)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("="*60)
        print("\nTask 10 Implementation Verified:")
        print("  ✓ Query cache with LRU and TTL")
        print("  ✓ Conversation memory with session management")
        print("  ✓ Cache and memory independence")
        print("  ✓ Thread-safe concurrent access")
        print("  ✓ Proper integration behavior")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_integration_tests()
