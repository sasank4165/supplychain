# Query Cache and Conversation Memory

This module provides query result caching and conversation memory management for the Supply Chain AI MVP.

## Features

### Query Cache (`query_cache.py`)
- **LRU Eviction**: Automatically evicts least recently used entries when cache is full
- **TTL Support**: Time-to-live expiration for cached entries
- **Thread-Safe**: Safe for concurrent access from multiple threads
- **Cache Key Generation**: Automatic key generation from query parameters
- **Statistics Tracking**: Hit/miss rates, evictions, expirations

### Cache Statistics (`cache_stats.py`)
- **Historical Snapshots**: Track cache performance over time
- **Aggregated Statistics**: Average hit rates, utilization metrics
- **Performance Ratings**: Automatic performance assessment
- **UI Formatting**: Ready-to-display statistics for user interfaces

### Conversation Memory (`memory/conversation_memory.py`)
- **Session Management**: Create, get, delete conversation sessions
- **History Tracking**: Store last N interactions per session
- **Persona Support**: Associate sessions with user personas
- **Context Preservation**: Maintain referenced entities across interactions
- **Session Timeout**: Automatic cleanup of expired sessions
- **Thread-Safe**: Safe for concurrent access

### Conversation Context (`memory/context.py`)
- **Interaction Model**: Structured storage of query-response pairs
- **Entity References**: Track products, orders, warehouses mentioned in conversation
- **Serialization**: Export/import session data
- **History Summaries**: Generate readable conversation summaries

## Usage

### Basic Cache Usage

```python
from cache.query_cache import QueryCache

# Initialize cache
cache = QueryCache(max_size=1000, default_ttl=300)

# Generate cache key
cache_key = QueryCache.generate_cache_key(
    query="Show me low stock items",
    persona="Warehouse Manager"
)

# Check cache
result = cache.get(cache_key)
if result is None:
    # Cache miss - process query
    result = process_query(query)
    # Store in cache
    cache.set(cache_key, result, ttl=300)

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1f}%")
```

### Basic Memory Usage

```python
from memory.conversation_memory import ConversationMemory
from memory.context import Persona

# Initialize memory
memory = ConversationMemory(max_history=10)

# Create session
session_id = "user123"
context = memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)

# Add interaction
memory.add_interaction(
    session_id,
    query="Show me low stock items",
    response="Low stock items: Widget A, Widget B",
    intent="SQL_QUERY"
)

# Get conversation history
history = memory.get_history(session_id, n=5)  # Last 5 interactions

# Switch persona (clears history)
memory.switch_persona(session_id, Persona.FIELD_ENGINEER, clear_history=True)
```

### Integration with Orchestrator

```python
from cache.query_cache import QueryCache
from memory.conversation_memory import ConversationMemory
from orchestrator.query_orchestrator import QueryOrchestrator

# Initialize components
cache = QueryCache(max_size=1000, default_ttl=300)
memory = ConversationMemory(max_history=10)

# Create orchestrator with cache
orchestrator = QueryOrchestrator(
    intent_classifier=intent_classifier,
    agent_router=agent_router,
    query_cache=cache,
    logger=logger
)

# Process query (automatically uses cache and memory)
response = orchestrator.process_query(
    query="Show me low stock items",
    persona="Warehouse Manager",
    session_id="user123"
)

# Check if response was cached
if response.cached:
    print("Response served from cache!")
```

### Cache Statistics Tracking

```python
from cache.cache_stats import CacheStatsTracker, format_cache_stats_for_ui

# Initialize tracker
tracker = CacheStatsTracker(max_snapshots=100)

# Record snapshots periodically
stats = cache.get_stats()
snapshot = tracker.record_snapshot(stats)

# Get performance summary
summary = tracker.get_performance_summary()
print(summary)

# Format for UI display
ui_stats = format_cache_stats_for_ui(stats)
print(ui_stats)
```

### Session Management

```python
# Get all active sessions
sessions = memory.get_all_sessions()
for session in sessions:
    print(f"Session: {session.session_id}")
    print(f"  Persona: {session.persona.value}")
    print(f"  Interactions: {session.interaction_count}")

# Cleanup expired sessions
removed = memory.cleanup_expired_sessions()
print(f"Removed {removed} expired sessions")

# Export/import sessions
session_data = memory.export_session("user123")
# ... save to file or database ...
memory.import_session(session_data)
```

## Configuration

### Cache Configuration (config.yaml)

```yaml
cache:
  enabled: true
  max_size: 1000              # Maximum cached entries
  default_ttl: 300            # Default TTL in seconds (5 minutes)
  dashboard_ttl: 900          # Dashboard query TTL (15 minutes)
```

### Conversation Configuration (config.yaml)

```yaml
conversation:
  max_history: 10             # Maximum interactions per session
  clear_on_persona_switch: true  # Clear history when switching persona

app:
  session_timeout: 3600       # Session timeout in seconds (1 hour)
```

## Cache Key Generation

Cache keys are generated using SHA256 hash of:
- Query text (normalized: lowercase, trimmed)
- Persona
- Additional parameters (sorted)

This ensures:
- Same query + persona = same cache key
- Case-insensitive matching
- Whitespace normalization

## Performance Considerations

### Cache
- **Hit Rate Target**: Aim for >60% hit rate for good performance
- **Size**: Start with 1000 entries, adjust based on memory usage
- **TTL**: Balance freshness vs. hit rate
  - Short TTL (5 min): Fresh data, lower hit rate
  - Long TTL (15 min): Higher hit rate, potentially stale data

### Memory
- **History Size**: 10 interactions is sufficient for context
- **Session Timeout**: 1 hour balances memory usage and user experience
- **Cleanup**: Run cleanup_expired_sessions() periodically (e.g., every 5 minutes)

## Thread Safety

Both cache and memory modules are thread-safe:
- Use `threading.Lock` for all operations
- Safe for concurrent access from multiple threads
- No race conditions or data corruption

## Testing

Run tests:
```bash
# Test cache
python mvp/cache/test_cache.py

# Test conversation memory
python mvp/memory/test_conversation_memory.py

# Test integration
python mvp/cache/example_integration.py
```

## Architecture Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Query Orchestrator                         │
│  ┌──────────────┐  ┌──────────────────────────────────┐    │
│  │ Query Cache  │  │  Conversation Memory             │    │
│  │ - LRU        │  │  - Session Management            │    │
│  │ - TTL        │  │  - History Tracking              │    │
│  │ - Stats      │  │  - Context Preservation          │    │
│  └──────────────┘  └──────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
                    SQL Agents
```

## Best Practices

1. **Cache Invalidation**: Invalidate cache when data changes
   ```python
   # Invalidate all inventory-related queries
   cache.invalidate("inventory")
   ```

2. **Session Cleanup**: Run periodic cleanup
   ```python
   # In background task or scheduled job
   removed = memory.cleanup_expired_sessions()
   ```

3. **Statistics Monitoring**: Track cache performance
   ```python
   stats = cache.get_stats()
   if stats['hit_rate'] < 30:
       logger.warning("Low cache hit rate!")
   ```

4. **Context Usage**: Use conversation context for follow-up queries
   ```python
   context = memory.get_context(session_id)
   # Pass context to SQL agent for better query understanding
   ```

5. **Persona Switching**: Clear history when switching personas
   ```python
   memory.switch_persona(session_id, new_persona, clear_history=True)
   ```

## Troubleshooting

### Low Cache Hit Rate
- Check if queries are being normalized properly
- Verify TTL is not too short
- Ensure cache size is sufficient

### High Memory Usage
- Reduce max_history per session
- Reduce cache max_size
- Run cleanup_expired_sessions() more frequently

### Session Not Found
- Check if session timeout is too short
- Verify session_id is consistent across requests
- Ensure session is created before use

## Future Enhancements

Potential improvements:
- Persistent cache (Redis, Memcached)
- Distributed cache for multi-instance deployments
- Database-backed conversation memory
- Cache warming strategies
- Advanced cache invalidation patterns
- Conversation memory search/filtering
