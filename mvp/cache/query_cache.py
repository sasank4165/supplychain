"""
Query Result Cache

Implements an in-memory cache for query results with:
- LRU (Least Recently Used) eviction policy
- TTL (Time To Live) support
- Cache key generation from query parameters
"""

import hashlib
import time
from typing import Any, Optional, Dict
from dataclasses import dataclass
from collections import OrderedDict
import threading


@dataclass
class CachedResult:
    """Represents a cached query result."""
    key: str
    value: Any
    created_at: float
    ttl: int
    access_count: int = 0
    last_accessed: float = 0.0
    
    def is_expired(self) -> bool:
        """Check if cached result has expired."""
        if self.ttl <= 0:
            return False  # No expiration
        return time.time() - self.created_at > self.ttl
    
    def access(self):
        """Record an access to this cached result."""
        self.access_count += 1
        self.last_accessed = time.time()


class QueryCache:
    """
    In-memory query result cache with LRU eviction and TTL support.
    
    Features:
    - Thread-safe operations
    - LRU eviction when max_size is reached
    - TTL-based expiration
    - Cache key generation from query parameters
    - Cache statistics tracking
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize query cache.
        
        Args:
            max_size: Maximum number of entries in cache
            default_ttl: Default time-to-live in seconds (0 = no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # OrderedDict for LRU behavior
        self._cache: OrderedDict[str, CachedResult] = OrderedDict()
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0
    
    def get(self, cache_key: str) -> Optional[Any]:
        """
        Get cached result by key.
        
        Args:
            cache_key: Cache key to lookup
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            if cache_key not in self._cache:
                self._misses += 1
                return None
            
            cached_result = self._cache[cache_key]
            
            # Check if expired
            if cached_result.is_expired():
                self._expirations += 1
                self._misses += 1
                del self._cache[cache_key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
            
            # Record access
            cached_result.access()
            
            self._hits += 1
            return cached_result.value
    
    def set(self, cache_key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value in cache.
        
        Args:
            cache_key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default_ttl)
        """
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl
            
            # Check if we need to evict
            if cache_key not in self._cache and len(self._cache) >= self.max_size:
                # Evict least recently used (first item)
                self._cache.popitem(last=False)
                self._evictions += 1
            
            # Create cached result
            cached_result = CachedResult(
                key=cache_key,
                value=value,
                created_at=time.time(),
                ttl=ttl,
                access_count=0,
                last_accessed=time.time()
            )
            
            # Store in cache (or update existing)
            self._cache[cache_key] = cached_result
            
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
    
    def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Pattern to match against cache keys (substring match)
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if pattern in key
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "expirations": self._expirations,
                "total_requests": total_requests
            }
    
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._expirations = 0
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            keys_to_remove = [
                key for key, cached_result in self._cache.items()
                if cached_result.is_expired()
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
                self._expirations += 1
            
            return len(keys_to_remove)
    
    @staticmethod
    def generate_cache_key(query: str, persona: str, **kwargs) -> str:
        """
        Generate cache key from query parameters.
        
        Args:
            query: User query text
            persona: User persona
            **kwargs: Additional parameters to include in key
            
        Returns:
            Cache key (SHA256 hash)
        """
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()
        
        # Create key components
        key_parts = [normalized_query, persona]
        
        # Add additional parameters in sorted order
        for k in sorted(kwargs.keys()):
            key_parts.append(f"{k}={kwargs[k]}")
        
        # Join and hash
        key_string = "|".join(key_parts)
        cache_key = hashlib.sha256(key_string.encode()).hexdigest()
        
        return cache_key


def create_cache_from_config(config: Dict[str, Any]) -> QueryCache:
    """
    Create QueryCache instance from configuration.
    
    Args:
        config: Configuration dictionary with cache settings
        
    Returns:
        Configured QueryCache instance
    """
    cache_config = config.get("cache", {})
    
    max_size = cache_config.get("max_size", 1000)
    default_ttl = cache_config.get("default_ttl", 300)
    
    return QueryCache(max_size=max_size, default_ttl=default_ttl)
