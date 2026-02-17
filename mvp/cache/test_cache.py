"""
Test Query Cache Implementation

Tests for query cache with LRU eviction and TTL support.
"""

import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache.query_cache import QueryCache, CachedResult
from cache.cache_stats import CacheStatsTracker, format_cache_stats_for_ui


def test_basic_cache_operations():
    """Test basic cache get/set operations."""
    print("\n=== Test: Basic Cache Operations ===")
    
    cache = QueryCache(max_size=10, default_ttl=300)
    
    # Test set and get
    cache.set("key1", "value1")
    result = cache.get("key1")
    
    assert result == "value1", "Cache get should return stored value"
    print("✓ Basic get/set works")
    
    # Test cache miss
    result = cache.get("nonexistent")
    assert result is None, "Cache miss should return None"
    print("✓ Cache miss returns None")
    
    # Test statistics
    stats = cache.get_stats()
    assert stats["hits"] == 1, "Should have 1 hit"
    assert stats["misses"] == 1, "Should have 1 miss"
    print(f"✓ Statistics: {stats['hits']} hits, {stats['misses']} misses")


def test_ttl_expiration():
    """Test TTL-based expiration."""
    print("\n=== Test: TTL Expiration ===")
    
    cache = QueryCache(max_size=10, default_ttl=1)  # 1 second TTL
    
    # Store value with short TTL
    cache.set("key1", "value1", ttl=1)
    
    # Should be available immediately
    result = cache.get("key1")
    assert result == "value1", "Value should be available immediately"
    print("✓ Value available immediately after set")
    
    # Wait for expiration
    print("  Waiting 2 seconds for expiration...")
    time.sleep(2)
    
    # Should be expired
    result = cache.get("key1")
    assert result is None, "Value should be expired"
    print("✓ Value expired after TTL")
    
    stats = cache.get_stats()
    assert stats["expirations"] == 1, "Should have 1 expiration"
    print(f"✓ Expiration tracked: {stats['expirations']} expirations")


def test_lru_eviction():
    """Test LRU eviction when cache is full."""
    print("\n=== Test: LRU Eviction ===")
    
    cache = QueryCache(max_size=3, default_ttl=300)
    
    # Fill cache
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    stats = cache.get_stats()
    assert stats["size"] == 3, "Cache should be full"
    print("✓ Cache filled to max size (3)")
    
    # Access key1 to make it recently used
    cache.get("key1")
    
    # Add new key, should evict key2 (least recently used)
    cache.set("key4", "value4")
    
    # key2 should be evicted
    result = cache.get("key2")
    assert result is None, "key2 should be evicted"
    print("✓ Least recently used key evicted")
    
    # key1 should still be available
    result = cache.get("key1")
    assert result == "value1", "key1 should still be available"
    print("✓ Recently accessed key retained")
    
    stats = cache.get_stats()
    assert stats["evictions"] == 1, "Should have 1 eviction"
    print(f"✓ Eviction tracked: {stats['evictions']} evictions")


def test_cache_key_generation():
    """Test cache key generation."""
    print("\n=== Test: Cache Key Generation ===")
    
    # Same query and persona should generate same key
    key1 = QueryCache.generate_cache_key("show inventory", "Warehouse Manager")
    key2 = QueryCache.generate_cache_key("show inventory", "Warehouse Manager")
    
    assert key1 == key2, "Same query should generate same key"
    print("✓ Consistent key generation for same query")
    
    # Different query should generate different key
    key3 = QueryCache.generate_cache_key("show orders", "Warehouse Manager")
    assert key1 != key3, "Different query should generate different key"
    print("✓ Different keys for different queries")
    
    # Different persona should generate different key
    key4 = QueryCache.generate_cache_key("show inventory", "Field Engineer")
    assert key1 != key4, "Different persona should generate different key"
    print("✓ Different keys for different personas")
    
    # Case insensitive and whitespace normalized
    key5 = QueryCache.generate_cache_key("  SHOW INVENTORY  ", "Warehouse Manager")
    assert key1 == key5, "Query should be normalized"
    print("✓ Query normalization works")


def test_cache_invalidation():
    """Test cache invalidation."""
    print("\n=== Test: Cache Invalidation ===")
    
    cache = QueryCache(max_size=10, default_ttl=300)
    
    # Add multiple entries
    cache.set("inventory_key1", "value1")
    cache.set("inventory_key2", "value2")
    cache.set("order_key1", "value3")
    
    # Invalidate inventory entries
    invalidated = cache.invalidate("inventory")
    assert invalidated == 2, "Should invalidate 2 entries"
    print(f"✓ Invalidated {invalidated} entries matching pattern")
    
    # Check that inventory entries are gone
    assert cache.get("inventory_key1") is None
    assert cache.get("inventory_key2") is None
    print("✓ Invalidated entries removed")
    
    # Check that order entry is still there
    assert cache.get("order_key1") == "value3"
    print("✓ Non-matching entries retained")


def test_cache_stats_tracker():
    """Test cache statistics tracker."""
    print("\n=== Test: Cache Stats Tracker ===")
    
    cache = QueryCache(max_size=10, default_ttl=300)
    tracker = CacheStatsTracker(max_snapshots=5)
    
    # Add some data and record snapshot
    cache.set("key1", "value1")
    cache.get("key1")
    cache.get("key2")  # miss
    
    snapshot = tracker.record_snapshot(cache.get_stats())
    assert snapshot.hits == 1
    assert snapshot.misses == 1
    print("✓ Snapshot recorded")
    
    # Add more data and record another snapshot
    cache.set("key2", "value2")
    cache.get("key2")
    
    tracker.record_snapshot(cache.get_stats())
    
    # Get aggregated stats
    aggregated = tracker.get_aggregated_stats()
    assert aggregated["total_snapshots"] == 2
    print(f"✓ Aggregated stats: {aggregated['total_snapshots']} snapshots")
    
    # Get performance summary
    summary = tracker.get_performance_summary()
    assert "Cache Performance Summary" in summary
    print("✓ Performance summary generated")


def test_cache_stats_ui_format():
    """Test cache statistics UI formatting."""
    print("\n=== Test: Cache Stats UI Format ===")
    
    cache = QueryCache(max_size=100, default_ttl=300)
    
    # Add some data
    for i in range(10):
        cache.set(f"key{i}", f"value{i}")
    
    # Get some hits and misses
    for i in range(5):
        cache.get(f"key{i}")  # hits
    for i in range(5):
        cache.get(f"missing{i}")  # misses
    
    stats = cache.get_stats()
    formatted = format_cache_stats_for_ui(stats)
    
    assert "Cache Statistics" in formatted
    assert "Hit Rate" in formatted
    print("✓ UI formatted stats generated")
    print(formatted)


def test_thread_safety():
    """Test thread-safe operations."""
    print("\n=== Test: Thread Safety ===")
    
    import threading
    
    cache = QueryCache(max_size=100, default_ttl=300)
    
    def worker(thread_id):
        for i in range(10):
            cache.set(f"thread{thread_id}_key{i}", f"value{i}")
            cache.get(f"thread{thread_id}_key{i}")
    
    # Create multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    stats = cache.get_stats()
    print(f"✓ Thread-safe operations completed: {stats['size']} entries")


def run_all_tests():
    """Run all cache tests."""
    print("\n" + "="*60)
    print("QUERY CACHE TEST SUITE")
    print("="*60)
    
    try:
        test_basic_cache_operations()
        test_ttl_expiration()
        test_lru_eviction()
        test_cache_key_generation()
        test_cache_invalidation()
        test_cache_stats_tracker()
        test_cache_stats_ui_format()
        test_thread_safety()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
