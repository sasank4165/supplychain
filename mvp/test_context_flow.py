"""
Test script to verify conversation context flow
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from memory.context import ConversationContext, Persona, Interaction
import time

# Create a test context
context = ConversationContext(
    session_id="test_session",
    persona=Persona.WAREHOUSE_MANAGER,
    history=[]
)

# Add first interaction
context.add_interaction(
    query="Show me products with low stock in warehouse WH001",
    response="Found 5 products with low stock: PROD001, PROD002, PROD003, PROD004, PROD005"
)

print("After first interaction:")
print(f"History length: {len(context.history)}")
print(f"Last query: {context.history[-1].query}")
print(f"Last response: {context.history[-1].response}")
print()

# Add second interaction (follow-up)
context.add_interaction(
    query="What about warehouse WH002?",
    response="Found 3 products with low stock in WH002: PROD010, PROD011, PROD012"
)

print("After second interaction:")
print(f"History length: {len(context.history)}")
print()

# Simulate what the SQL agent sees
print("What SQL agent would see for follow-up query:")
print("Previous conversation:")
for interaction in context.history[-3:]:
    print(f"Q: {interaction.query}")
    print(f"A: {interaction.response[:100]}...")
print()

# Test the intent classifier context
print("What intent classifier would see:")
print("Previous conversation:")
for interaction in context.history[-2:]:
    print(f"Q: {interaction.query}")
    print(f"A: {interaction.response[:100]}...")
