"""Memory system example for Universal Agent SDK.

This example shows how to use the memory system for storing
and retrieving conversation context.
"""

import asyncio
import tempfile
from pathlib import Path

from universal_agent_sdk import ConversationMemory, PersistentMemory


async def conversation_memory_example():
    """Demonstrate ConversationMemory usage."""
    print("=== Conversation Memory ===\n")

    # Create in-memory storage
    memory = ConversationMemory(max_entries=100)

    # Add some entries
    await memory.add("User asked about Python programming", metadata={"role": "user"})
    await memory.add("Assistant explained Python basics", metadata={"role": "assistant"})
    await memory.add("User asked about decorators", metadata={"role": "user"})
    await memory.add("Assistant provided decorator examples", metadata={"role": "assistant"})
    await memory.add("User asked about async programming", metadata={"role": "user"})
    await memory.add("Assistant explained async/await patterns", metadata={"role": "assistant"})

    print(f"Memory size: {memory.size} entries\n")

    # Search for relevant context
    print("Searching for 'decorators':")
    results = await memory.search("decorators", limit=3)
    for result in results:
        print(f"  [{result.score:.2f}] {result.entry.content}")

    print("\nSearching for 'async':")
    results = await memory.search("async programming", limit=3)
    for result in results:
        print(f"  [{result.score:.2f}] {result.entry.content}")

    # Get recent entries
    print("\nRecent entries:")
    for entry in memory.get_recent(3):
        role = entry.metadata.get("role", "unknown")
        print(f"  [{role}] {entry.content}")

    # Get context for a query
    print("\nContext for 'What did we discuss about Python?':")
    context = await memory.get_context("What did we discuss about Python?")
    print(f"  {context[:200]}...")


async def persistent_memory_example():
    """Demonstrate PersistentMemory usage."""
    print("\n=== Persistent Memory ===\n")

    # Create a temporary file for this example
    with tempfile.TemporaryDirectory() as tmpdir:
        memory_path = Path(tmpdir) / "memory.json"

        # First session - add data
        print("Session 1: Adding entries...")
        memory = PersistentMemory(memory_path)

        await memory.add("Project requirements discussed", metadata={"topic": "planning"})
        await memory.add("Database schema designed", metadata={"topic": "architecture"})
        await memory.add("API endpoints defined", metadata={"topic": "architecture"})

        print(f"  Added {memory.size} entries")
        print(f"  Saved to {memory_path}")

        # Simulate new session by creating new instance
        print("\nSession 2: Loading saved data...")
        memory2 = PersistentMemory(memory_path)

        print(f"  Loaded {memory2.size} entries")

        # Search
        print("\nSearching for 'architecture':")
        results = await memory2.search("architecture")
        for result in results:
            print(f"  [{result.score:.2f}] {result.entry.content}")

        # Add more in session 2
        await memory2.add("Frontend components implemented", metadata={"topic": "development"})
        print(f"\n  Now have {memory2.size} entries")


async def memory_with_messages():
    """Show memory integration with messages."""
    print("\n=== Memory with Messages ===\n")

    from universal_agent_sdk import AssistantMessage, TextBlock, UserMessage

    memory = ConversationMemory()

    # Add messages directly
    user_msg = UserMessage(content="How do I use async/await in Python?")
    await memory.add_message(user_msg)

    assistant_msg = AssistantMessage(
        content=[
            TextBlock(
                text="Async/await in Python allows you to write asynchronous code..."
            )
        ]
    )
    await memory.add_message(assistant_msg)

    # Query by role
    print("User messages:")
    for entry in memory.get_by_role("user"):
        print(f"  {entry.content}")

    print("\nAssistant messages:")
    for entry in memory.get_by_role("assistant"):
        print(f"  {entry.content}")


async def memory_pruning():
    """Demonstrate automatic memory pruning."""
    print("\n=== Memory Pruning ===\n")

    # Create memory with small limit
    memory = ConversationMemory(max_entries=3)

    print("Adding 5 entries with max_entries=3:")
    for i in range(5):
        entry_id = await memory.add(f"Entry {i+1}")
        print(f"  Added 'Entry {i+1}' (id: {entry_id[:8]}...)")
        print(f"  Current size: {memory.size}")

    print("\nRemaining entries:")
    for entry in memory.get_recent(10):
        print(f"  {entry.content}")


if __name__ == "__main__":
    asyncio.run(conversation_memory_example())
    asyncio.run(persistent_memory_example())
    asyncio.run(memory_with_messages())
    asyncio.run(memory_pruning())
