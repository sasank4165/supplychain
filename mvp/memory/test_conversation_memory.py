"""
Test Conversation Memory Implementation

Tests for conversation memory with session management.
"""

import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.conversation_memory import ConversationMemory
from memory.context import ConversationContext, Interaction, Persona


def test_create_session():
    """Test session creation."""
    print("\n=== Test: Create Session ===")
    
    memory = ConversationMemory(max_history=10)
    
    # Create session
    context = memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    
    assert context.session_id == "session1"
    assert context.persona == Persona.WAREHOUSE_MANAGER
    assert len(context.history) == 0
    print("✓ Session created successfully")
    
    # Get session
    retrieved = memory.get_session("session1")
    assert retrieved is not None
    assert retrieved.session_id == "session1"
    print("✓ Session retrieved successfully")


def test_add_interaction():
    """Test adding interactions to session."""
    print("\n=== Test: Add Interaction ===")
    
    memory = ConversationMemory(max_history=10)
    context = memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    
    # Add interaction
    memory.add_interaction(
        "session1",
        "Show me low stock items",
        "Here are the low stock items: ...",
        intent="SQL_QUERY"
    )
    
    # Check history
    history = memory.get_history("session1")
    assert len(history) == 1
    assert history[0].query == "Show me low stock items"
    print("✓ Interaction added successfully")
    
    # Add more interactions
    for i in range(5):
        memory.add_interaction(
            "session1",
            f"Query {i}",
            f"Response {i}"
        )
    
    history = memory.get_history("session1")
    assert len(history) == 6
    print(f"✓ Multiple interactions added: {len(history)} total")


def test_max_history_limit():
    """Test that history is trimmed to max_history."""
    print("\n=== Test: Max History Limit ===")
    
    memory = ConversationMemory(max_history=5)
    context = memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    
    # Add more than max_history interactions
    for i in range(10):
        memory.add_interaction(
            "session1",
            f"Query {i}",
            f"Response {i}"
        )
    
    # Check that only last 5 are kept
    history = memory.get_history("session1")
    assert len(history) == 5
    assert history[0].query == "Query 5"  # First kept should be query 5
    assert history[-1].query == "Query 9"  # Last should be query 9
    print(f"✓ History trimmed to max_history: {len(history)} interactions")


def test_get_recent_history():
    """Test getting recent history."""
    print("\n=== Test: Get Recent History ===")
    
    memory = ConversationMemory(max_history=10)
    context = memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    
    # Add interactions
    for i in range(10):
        memory.add_interaction(
            "session1",
            f"Query {i}",
            f"Response {i}"
        )
    
    # Get last 3
    recent = memory.get_history("session1", n=3)
    assert len(recent) == 3
    assert recent[0].query == "Query 7"
    assert recent[-1].query == "Query 9"
    print(f"✓ Retrieved {len(recent)} recent interactions")


def test_clear_session():
    """Test clearing session history."""
    print("\n=== Test: Clear Session ===")
    
    memory = ConversationMemory(max_history=10)
    context = memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    
    # Add interactions
    for i in range(5):
        memory.add_interaction("session1", f"Query {i}", f"Response {i}")
    
    assert len(memory.get_history("session1")) == 5
    print("✓ Added 5 interactions")
    
    # Clear session
    result = memory.clear_session("session1")
    assert result is True
    assert len(memory.get_history("session1")) == 0
    print("✓ Session history cleared")


def test_delete_session():
    """Test deleting a session."""
    print("\n=== Test: Delete Session ===")
    
    memory = ConversationMemory(max_history=10)
    memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    memory.create_session("session2", Persona.FIELD_ENGINEER)
    
    assert memory.get_session_count() == 2
    print("✓ Created 2 sessions")
    
    # Delete session1
    result = memory.delete_session("session1")
    assert result is True
    assert memory.get_session_count() == 1
    assert memory.get_session("session1") is None
    assert memory.get_session("session2") is not None
    print("✓ Session deleted successfully")


def test_switch_persona():
    """Test switching persona."""
    print("\n=== Test: Switch Persona ===")
    
    memory = ConversationMemory(max_history=10)
    context = memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    
    # Add some history
    memory.add_interaction("session1", "Query 1", "Response 1")
    
    # Switch persona with clear history
    result = memory.switch_persona("session1", Persona.FIELD_ENGINEER, clear_history=True)
    assert result is True
    
    context = memory.get_session("session1")
    assert context.persona == Persona.FIELD_ENGINEER
    assert len(context.history) == 0
    print("✓ Persona switched with history cleared")
    
    # Add new history
    memory.add_interaction("session1", "Query 2", "Response 2")
    
    # Switch persona without clearing history
    memory.switch_persona("session1", Persona.PROCUREMENT_SPECIALIST, clear_history=False)
    
    context = memory.get_session("session1")
    assert context.persona == Persona.PROCUREMENT_SPECIALIST
    assert len(context.history) == 1
    print("✓ Persona switched with history retained")


def test_get_or_create_session():
    """Test get or create session."""
    print("\n=== Test: Get or Create Session ===")
    
    memory = ConversationMemory(max_history=10)
    
    # Should create new session
    context1 = memory.get_or_create_session("session1", Persona.WAREHOUSE_MANAGER)
    assert context1.session_id == "session1"
    print("✓ New session created")
    
    # Should return existing session
    context2 = memory.get_or_create_session("session1", Persona.FIELD_ENGINEER)
    assert context2.session_id == "session1"
    assert context2.persona == Persona.WAREHOUSE_MANAGER  # Original persona
    print("✓ Existing session returned")


def test_session_timeout():
    """Test session timeout cleanup."""
    print("\n=== Test: Session Timeout ===")
    
    memory = ConversationMemory(max_history=10, session_timeout=2)  # 2 second timeout
    
    # Create sessions
    context1 = memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    context2 = memory.create_session("session2", Persona.FIELD_ENGINEER)
    
    assert memory.get_session_count() == 2
    print("✓ Created 2 sessions")
    
    # Wait for timeout
    print("  Waiting 3 seconds for timeout...")
    time.sleep(3)
    
    # Cleanup expired sessions
    removed = memory.cleanup_expired_sessions()
    assert removed == 2
    assert memory.get_session_count() == 0
    print(f"✓ Removed {removed} expired sessions")


def test_referenced_entities():
    """Test referenced entities in context."""
    print("\n=== Test: Referenced Entities ===")
    
    memory = ConversationMemory(max_history=10)
    context = memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    
    # Add referenced entity
    context.add_referenced_entity("product", "P001", {"name": "Widget A", "stock": 50})
    
    # Retrieve entity
    entity = context.get_referenced_entity("product", "P001")
    assert entity is not None
    assert entity["name"] == "Widget A"
    print("✓ Referenced entity stored and retrieved")


def test_statistics():
    """Test conversation memory statistics."""
    print("\n=== Test: Statistics ===")
    
    memory = ConversationMemory(max_history=10)
    
    # Create sessions and add interactions
    memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    memory.add_interaction("session1", "Query 1", "Response 1")
    memory.add_interaction("session1", "Query 2", "Response 2")
    
    memory.create_session("session2", Persona.FIELD_ENGINEER)
    memory.add_interaction("session2", "Query 3", "Response 3")
    
    # Get statistics
    stats = memory.get_statistics()
    
    assert stats["active_sessions"] == 2
    assert stats["total_interactions"] == 3
    assert stats["avg_interactions_per_session"] == 1.5
    print(f"✓ Statistics: {stats['active_sessions']} sessions, {stats['total_interactions']} interactions")


def test_export_import_session():
    """Test exporting and importing sessions."""
    print("\n=== Test: Export/Import Session ===")
    
    memory = ConversationMemory(max_history=10)
    context = memory.create_session("session1", Persona.WAREHOUSE_MANAGER)
    
    # Add some data
    memory.add_interaction("session1", "Query 1", "Response 1")
    context.add_referenced_entity("product", "P001", {"name": "Widget"})
    
    # Export
    exported = memory.export_session("session1")
    assert exported is not None
    assert exported["session_id"] == "session1"
    print("✓ Session exported")
    
    # Delete and reimport
    memory.delete_session("session1")
    assert memory.get_session("session1") is None
    
    result = memory.import_session(exported)
    assert result is True
    
    # Verify imported data
    context = memory.get_session("session1")
    assert context is not None
    assert len(context.history) == 1
    assert context.get_referenced_entity("product", "P001") is not None
    print("✓ Session imported successfully")


def test_thread_safety():
    """Test thread-safe operations."""
    print("\n=== Test: Thread Safety ===")
    
    import threading
    
    memory = ConversationMemory(max_history=10)
    
    def worker(thread_id):
        session_id = f"session{thread_id}"
        memory.create_session(session_id, Persona.WAREHOUSE_MANAGER)
        
        for i in range(5):
            memory.add_interaction(session_id, f"Query {i}", f"Response {i}")
    
    # Create multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    stats = memory.get_statistics()
    assert stats["active_sessions"] == 5
    assert stats["total_interactions"] == 25
    print(f"✓ Thread-safe operations: {stats['active_sessions']} sessions, {stats['total_interactions']} interactions")


def run_all_tests():
    """Run all conversation memory tests."""
    print("\n" + "="*60)
    print("CONVERSATION MEMORY TEST SUITE")
    print("="*60)
    
    try:
        test_create_session()
        test_add_interaction()
        test_max_history_limit()
        test_get_recent_history()
        test_clear_session()
        test_delete_session()
        test_switch_persona()
        test_get_or_create_session()
        test_session_timeout()
        test_referenced_entities()
        test_statistics()
        test_export_import_session()
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
