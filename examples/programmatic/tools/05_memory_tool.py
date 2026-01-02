#!/usr/bin/env python3
"""Memory Tool Example - Demonstrate persistent memory across conversations.

This example shows how to use the FileSystemMemoryTool to enable Claude to
store and retrieve information across conversation turns.

The memory tool allows Claude to:
- View the memory directory to check for previous context
- Create files to store information
- Edit files using str_replace or insert commands
- Delete files when they're no longer needed
- Rename/move files for better organization

Reference: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
"""

import asyncio
import shutil
import tempfile
from pathlib import Path

from anthropic import Anthropic

from universal_agent_sdk.config import Config
from universal_agent_sdk.tools.memory import (
    FileSystemMemoryTool,
    get_memory_system_prompt,
)

# Create a temporary directory for this example
EXAMPLE_MEMORY_DIR = Path(tempfile.mkdtemp(prefix="memory_example_"))


async def demo_memory_tool_standalone():
    """Demonstrate the memory tool in isolation (no LLM)."""
    print("=" * 70)
    print("STANDALONE MEMORY TOOL DEMO")
    print("=" * 70)

    memory = FileSystemMemoryTool(memory_dir=EXAMPLE_MEMORY_DIR / "standalone")
    print(f"\nMemory directory: {memory.memory_dir}")

    # 1. View empty directory
    print("\n1. View empty memory directory:")
    result = await memory.execute({"command": "view", "path": "/memories"})
    print(result)

    # 2. Create a file
    print("\n2. Create a project notes file:")
    result = await memory.execute({
        "command": "create",
        "path": "/memories/project_notes.md",
        "file_text": """# Project Notes

## Goals
- Build a robust memory system
- Enable cross-session learning

## Progress
- [x] Implemented basic commands
- [ ] Add encryption support
""",
    })
    print(result)

    # 3. View the file
    print("\n3. View the created file:")
    result = await memory.execute({
        "command": "view",
        "path": "/memories/project_notes.md",
    })
    print(result)

    # 4. Replace text
    print("\n4. Update progress (str_replace):")
    result = await memory.execute({
        "command": "str_replace",
        "path": "/memories/project_notes.md",
        "old_str": "- [ ] Add encryption support",
        "new_str": "- [x] Add encryption support",
    })
    print(result)

    # 5. Insert text (at end of file, line 9 = after line 9)
    print("\n5. Insert new task:")
    result = await memory.execute({
        "command": "insert",
        "path": "/memories/project_notes.md",
        "insert_line": 9,
        "insert_text": "- [ ] Write documentation\n",
    })
    print(result)

    # 6. View updated file
    print("\n6. View updated file:")
    result = await memory.execute({
        "command": "view",
        "path": "/memories/project_notes.md",
    })
    print(result)

    # 7. Create subdirectory and file
    print("\n7. Create a file in a subdirectory:")
    result = await memory.execute({
        "command": "create",
        "path": "/memories/sessions/session_001.log",
        "file_text": "Session started at 2024-01-01 10:00:00\nUser discussed project goals.\n",
    })
    print(result)

    # 8. View directory structure
    print("\n8. View directory structure:")
    result = await memory.execute({"command": "view", "path": "/memories"})
    print(result)

    # 9. Rename file
    print("\n9. Rename file:")
    result = await memory.execute({
        "command": "rename",
        "old_path": "/memories/project_notes.md",
        "new_path": "/memories/archived/project_notes_v1.md",
    })
    print(result)

    # 10. Delete session log
    print("\n10. Delete session log:")
    result = await memory.execute({
        "command": "delete",
        "path": "/memories/sessions",
    })
    print(result)

    # Final view
    print("\n11. Final directory state:")
    result = await memory.execute({"command": "view", "path": "/memories"})
    print(result)


async def demo_memory_with_claude():
    """Demonstrate memory tool with actual Claude API calls."""
    print("\n" + "=" * 70)
    print("MEMORY TOOL WITH CLAUDE")
    print("=" * 70)

    # Load config and check API key
    config = Config()
    api_key = config.get_api_key("anthropic")
    if not api_key:
        print("\nERROR: ANTHROPIC_API_KEY not found in .env")
        print("Skipping Claude integration demo.")
        return

    # Create memory tool
    memory_dir = EXAMPLE_MEMORY_DIR / "claude_session"
    memory = FileSystemMemoryTool(memory_dir=memory_dir)
    print(f"\nMemory directory: {memory.memory_dir}")

    # Pre-populate some context
    await memory.execute({
        "command": "create",
        "path": "/memories/user_preferences.xml",
        "file_text": """<preferences>
  <communication_style>concise and technical</communication_style>
  <programming_language>Python</programming_language>
  <formatting>use code blocks for examples</formatting>
</preferences>
""",
    })

    await memory.execute({
        "command": "create",
        "path": "/memories/previous_session.md",
        "file_text": """# Previous Session Notes

## Topics Discussed
- User is building a web scraper
- Encountered timeout issues with requests
- Suggested using retry logic with exponential backoff

## Code Reviewed
```python
def fetch_page(url, retries=3):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=5)
            return response.text
        except requests.exceptions.Timeout:
            if i == retries - 1:
                raise
            time.sleep(2 ** i)
```

## Action Items
- User will test the improved retry logic
- Need to discuss caching strategies next session
""",
    })

    print("\nPre-populated memory with user preferences and previous session notes.")

    # Create tool definition for Claude
    tools = [
        {
            "name": "memory",
            "description": memory.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["view", "create", "str_replace", "insert", "delete", "rename"],
                        "description": "The memory operation to perform",
                    },
                    "path": {
                        "type": "string",
                        "description": "Path relative to /memories",
                    },
                    "view_range": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Optional line range [start, end]",
                    },
                    "file_text": {"type": "string", "description": "Content for new file"},
                    "old_str": {"type": "string", "description": "Text to replace"},
                    "new_str": {"type": "string", "description": "Replacement text"},
                    "insert_line": {"type": "integer", "description": "Line to insert at"},
                    "insert_text": {"type": "string", "description": "Text to insert"},
                    "old_path": {"type": "string", "description": "Source path for rename"},
                    "new_path": {"type": "string", "description": "Destination path for rename"},
                },
                "required": ["command"],
            },
        }
    ]

    # Create Claude client
    client = Anthropic(api_key=api_key)

    # Build messages with memory system prompt
    system_prompt = get_memory_system_prompt() + """

You are a helpful coding assistant. Always check your memory first to understand
the user's context and preferences from previous sessions."""

    messages = [
        {
            "role": "user",
            "content": "I'm back to continue our discussion. What did we talk about last time, and what should we work on next?",
        }
    ]

    print("\n" + "-" * 70)
    print("USER: I'm back to continue our discussion. What did we talk about last time, and what should we work on next?")
    print("-" * 70)

    # Run conversation with tool use
    max_turns = 5
    for turn in range(max_turns):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        print(f"\n[Turn {turn + 1}] stop_reason: {response.stop_reason}")

        # Process response
        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"\nClaude: {block.text}")

        if response.stop_reason != "tool_use":
            break

        # Handle tool calls
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for block in response.content:
            if hasattr(block, "name") and block.name == "memory":
                print(f"\n  → Memory command: {block.input.get('command')}")
                if block.input.get("path"):
                    print(f"    Path: {block.input.get('path')}")

                # Execute memory command
                result = await memory.execute(block.input)
                # Truncate for display
                display_result = result[:300] + "..." if len(result) > 300 else result
                print(f"    Result: {display_result}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})

    # Show final memory state
    print("\n" + "-" * 70)
    print("FINAL MEMORY STATE")
    print("-" * 70)
    result = await memory.execute({"command": "view", "path": "/memories"})
    print(result)


async def demo_cross_session_learning():
    """Demonstrate how memory enables learning across sessions."""
    print("\n" + "=" * 70)
    print("CROSS-SESSION LEARNING DEMO")
    print("=" * 70)

    # Create memory tool
    memory_dir = EXAMPLE_MEMORY_DIR / "learning_session"
    memory = FileSystemMemoryTool(memory_dir=memory_dir)

    # Simulate Session 1: User provides preferences
    print("\n[SESSION 1] Recording user preferences...")
    await memory.execute({
        "command": "create",
        "path": "/memories/learned/coding_style.xml",
        "file_text": """<coding_style>
  <language>Python</language>
  <conventions>
    <naming>snake_case for variables and functions</naming>
    <indentation>4 spaces</indentation>
    <docstrings>Google style</docstrings>
    <type_hints>Always use them</type_hints>
  </conventions>
  <preferences>
    <error_handling>Prefer explicit try/except over EAFP</error_handling>
    <testing>pytest with fixtures</testing>
  </preferences>
</coding_style>
""",
    })

    # Simulate Session 2: Record feedback
    print("[SESSION 2] Recording feedback from code review...")
    await memory.execute({
        "command": "create",
        "path": "/memories/feedback/review_001.md",
        "file_text": """# Code Review Feedback - Session 2

## What Worked Well
- User appreciated the detailed type hints
- Async code examples were well-received

## Areas for Improvement
- User prefers more concise explanations
- Reduce use of comments in obvious code

## Specific Requests
- Always show complete, runnable examples
- Include performance considerations
""",
    })

    # Simulate Session 3: Build knowledge base
    print("[SESSION 3] Building domain knowledge...")
    await memory.execute({
        "command": "create",
        "path": "/memories/learned/project_context.md",
        "file_text": """# Project Context

## Project: Web Scraper Pipeline
- **Language**: Python 3.11+
- **Framework**: asyncio with aiohttp
- **Database**: PostgreSQL with asyncpg

## Key Components
1. URL queue manager
2. Rate-limited HTTP client
3. HTML parser with BeautifulSoup
4. Data persistence layer

## Known Issues
- Timeout handling needs improvement
- Memory leaks with large crawls
""",
    })

    # Show accumulated knowledge
    print("\nAccumulated Knowledge Base:")
    result = await memory.execute({"command": "view", "path": "/memories"})
    print(result)

    print("\n[SESSION 4] Agent can now use all this context for better responses!")


async def main():
    print("=" * 70)
    print("UNIVERSAL AGENT SDK - MEMORY TOOL EXAMPLE")
    print("=" * 70)
    print(f"\nUsing temporary directory: {EXAMPLE_MEMORY_DIR}")

    try:
        # Run demos
        await demo_memory_tool_standalone()
        await demo_memory_with_claude()
        await demo_cross_session_learning()

    finally:
        # Cleanup
        print("\n" + "=" * 70)
        print("CLEANUP")
        print("=" * 70)
        if EXAMPLE_MEMORY_DIR.exists():
            shutil.rmtree(EXAMPLE_MEMORY_DIR)
            print(f"Removed temporary directory: {EXAMPLE_MEMORY_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
