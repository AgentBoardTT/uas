#!/usr/bin/env python3
"""
Comprehensive examples of using UniversalAgentClient for streaming mode.

This file demonstrates various patterns for building applications with
the UniversalAgentClient streaming interface.

The queries are intentionally simplistic. In reality, a query can be a more
complex task that uses the SDK's agentic capabilities and tools to accomplish.

Usage:
./examples/universal_streaming_mode.py - List the examples
./examples/universal_streaming_mode.py all - Run all examples
./examples/universal_streaming_mode.py basic_streaming - Run a specific example
"""

import asyncio
import sys

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ToolMessage,
    ToolUseBlock,
    UniversalAgentClient,
    UserMessage,
    tool,
)


def display_message(msg):
    """Standardized message display function.

    - UserMessage: "User: <content>"
    - AssistantMessage: "Assistant: <content>"
    - SystemMessage: ignored
    - ResultMessage: "Result ended" + stats
    """
    if isinstance(msg, UserMessage):
        if isinstance(msg.content, str):
            print(f"User: {msg.content}")
        else:
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(f"User: {block.text}")
    elif isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"Assistant: {block.text}")
    elif isinstance(msg, SystemMessage):
        # Ignore system messages
        pass
    elif isinstance(msg, ResultMessage):
        print(f"[Result: {msg.num_turns} turns]")


async def example_basic_streaming():
    """Basic streaming with context manager."""
    print("=== Basic Streaming Example ===")

    async with UniversalAgentClient() as client:
        print("User: What is 2+2?")
        await client.send("What is 2+2?")

        async for msg in client.receive():
            display_message(msg)

    print("\n")


async def example_multi_turn_conversation():
    """Multi-turn conversation maintaining context."""
    print("=== Multi-Turn Conversation Example ===")

    async with UniversalAgentClient() as client:
        # First turn
        print("User: What's the capital of France?")
        await client.send("What's the capital of France?")

        async for msg in client.receive():
            display_message(msg)

        # Second turn - follow-up (context is preserved)
        print("\nUser: What's the population of that city?")
        await client.send("What's the population of that city?")

        async for msg in client.receive():
            display_message(msg)

    print("\n")


async def example_streaming_text():
    """Stream text character by character as it arrives."""
    print("=== Real-time Streaming Text Example ===")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stream=True,
    )

    async with UniversalAgentClient(options) as client:
        print("User: Tell me a short story about a robot.\n")
        print("Assistant: ", end="", flush=True)

        await client.send("Tell me a very short story about a robot in 3 sentences.")

        async for msg in client.receive():
            if isinstance(msg, StreamEvent):
                # Print streaming text as it arrives
                if msg.delta and msg.delta.get("type") == "text_delta":
                    print(msg.delta.get("text", ""), end="", flush=True)
            elif isinstance(msg, AssistantMessage):
                # Full message at the end (for non-streaming providers)
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="")
            elif isinstance(msg, ResultMessage):
                print("\n")

    print("\n")


async def example_with_tools():
    """Using tools in streaming mode."""
    print("=== Tools in Streaming Example ===")

    # Define a tool
    @tool
    def calculate(expression: str) -> str:
        """Evaluate a mathematical expression."""
        try:
            # Safe evaluation for simple math
            allowed = set("0123456789+-*/(). ")
            if all(c in allowed for c in expression):
                result = eval(expression)  # noqa: S307
                return f"Result: {result}"
            return "Error: Invalid expression"
        except Exception as e:
            return f"Error: {e}"

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[calculate.definition],
    )

    async with UniversalAgentClient(options) as client:
        print("User: What is (15 * 3) + (42 / 2)?")
        await client.send("What is (15 * 3) + (42 / 2)?")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Assistant: {block.text}")
                    elif isinstance(block, ToolUseBlock):
                        print(f"[Tool: {block.name}({block.input})]")
            elif isinstance(msg, ToolMessage):
                print(f"[Tool Result: {msg.content}]")
            elif isinstance(msg, ResultMessage):
                print(f"[Completed in {msg.num_turns} turns]")

    print("\n")


async def example_manual_message_handling():
    """Manually handle message stream for custom logic."""
    print("=== Manual Message Handling Example ===")

    async with UniversalAgentClient() as client:
        await client.send("List 5 programming languages and their main use cases")

        # Manually process messages with custom logic
        languages_found = []

        async for message in client.receive():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text = block.text
                        print(f"Assistant: {text}")
                        # Custom logic: extract language names
                        for lang in [
                            "Python",
                            "JavaScript",
                            "Java",
                            "C++",
                            "Go",
                            "Rust",
                            "Ruby",
                            "TypeScript",
                        ]:
                            if lang in text and lang not in languages_found:
                                languages_found.append(lang)
            elif isinstance(message, ResultMessage):
                print(f"\nTotal languages mentioned: {len(languages_found)}")
                print(f"Languages: {', '.join(languages_found)}")

    print("\n")


async def example_with_options():
    """Use AgentOptions to configure the client."""
    print("=== Custom Options Example ===")

    # Define a file tool
    @tool
    def write_file(path: str, content: str) -> str:
        """Write content to a file."""
        return f"Written {len(content)} bytes to {path}"

    @tool
    def read_file(path: str) -> str:
        """Read content from a file."""
        return f"Contents of {path}: Hello, World!"

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[write_file.definition, read_file.definition],
        system_prompt="You are a helpful coding assistant.",
        max_turns=3,
    )

    async with UniversalAgentClient(options) as client:
        print("User: Create a simple hello.txt file with a greeting message")
        await client.send("Create a simple hello.txt file with a greeting message")

        tool_uses = []
        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Assistant: {block.text}")
                    elif isinstance(block, ToolUseBlock):
                        tool_uses.append(block.name)
                        print(f"[Using tool: {block.name}]")
            elif isinstance(msg, ToolMessage):
                print(f"[Tool result: {msg.content}]")
            elif isinstance(msg, ResultMessage) and tool_uses:
                print(f"Tools used: {', '.join(tool_uses)}")

    print("\n")


async def example_provider_switching():
    """Switch providers mid-conversation."""
    print("=== Provider Switching Example ===")

    async with UniversalAgentClient() as client:
        # Start with Claude (default)
        print("[Using Claude]")
        print("User: What's 2+2?")
        await client.send("What's 2+2?")

        async for msg in client.receive():
            display_message(msg)

        # Switch provider (if you have OpenAI key configured)
        # client.set_provider("openai")
        # client.set_model("gpt-4o")
        # print("\n[Switched to OpenAI]")

        # Continue with same context
        print("\nUser: What about 3+3?")
        await client.send("What about 3+3?")

        async for msg in client.receive():
            display_message(msg)

    print("\n")


async def example_conversation_history():
    """Access and use conversation history."""
    print("=== Conversation History Example ===")

    async with UniversalAgentClient() as client:
        # Build up a conversation
        await client.send("My name is Alice and I love Python.")
        async for _ in client.receive():
            pass

        await client.send("What programming language did I say I love?")
        async for msg in client.receive():
            display_message(msg)

        # Access conversation history
        print("\n--- Conversation History ---")
        for i, msg in enumerate(client.messages):
            role = type(msg).__name__.replace("Message", "")
            if hasattr(msg, "content"):
                if isinstance(msg.content, str):
                    content = msg.content[:40]
                elif isinstance(msg.content, list) and msg.content:
                    first = msg.content[0]
                    if isinstance(first, TextBlock):
                        content = first.text[:40]
                    else:
                        content = str(first)[:40]
                else:
                    content = str(msg.content)[:40]
                print(f"  {i + 1}. [{role}] {content}...")

        # Clear history but keep system prompt
        client.clear_history()
        print(f"\nAfter clear: {len(client.messages)} messages (system only)")

    print("\n")


async def example_non_streaming():
    """Non-streaming mode for simpler handling."""
    print("=== Non-Streaming Mode Example ===")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stream=False,  # Disable streaming
    )

    async with UniversalAgentClient(options) as client:
        print("User: What's the meaning of life in one sentence?")
        await client.send("What's the meaning of life in one sentence?")

        # In non-streaming mode, you get complete messages
        messages = await client.receive_all()

        for msg in messages:
            if isinstance(msg, AssistantMessage):
                text = client.get_text_response()
                print(f"Assistant: {text}")
            elif isinstance(msg, ResultMessage):
                print(f"[Completed in {msg.num_turns} turns]")

    print("\n")


async def example_error_handling():
    """Demonstrate proper error handling."""
    print("=== Error Handling Example ===")

    client = UniversalAgentClient()

    try:
        await client.connect()

        print("User: Calculate something complex")
        await client.send("What is the factorial of 10?")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Assistant: {block.text}")
            elif isinstance(msg, ResultMessage):
                display_message(msg)
                if msg.is_error:
                    print("Note: Response contained an error")

    except ConnectionError as e:
        print(f"Connection error: {e}")
    except RuntimeError as e:
        print(f"Runtime error: {e}")
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
    finally:
        await client.disconnect()

    print("\n")


async def example_query_shorthand():
    """Using the query() method for single turns."""
    print("=== Query Shorthand Example ===")

    async with UniversalAgentClient() as client:
        # query() combines send() and receive()
        print("User: What's the square root of 144?")

        async for msg in client.query("What's the square root of 144?"):
            display_message(msg)

    print("\n")


async def main():
    """Run all examples or a specific example based on command line argument."""
    examples = {
        "basic_streaming": example_basic_streaming,
        "multi_turn_conversation": example_multi_turn_conversation,
        "streaming_text": example_streaming_text,
        "with_tools": example_with_tools,
        "manual_message_handling": example_manual_message_handling,
        "with_options": example_with_options,
        "provider_switching": example_provider_switching,
        "conversation_history": example_conversation_history,
        "non_streaming": example_non_streaming,
        "error_handling": example_error_handling,
        "query_shorthand": example_query_shorthand,
    }

    if len(sys.argv) < 2:
        print("Usage: python universal_streaming_mode.py <example_name>")
        print("\nAvailable examples:")
        print("  all - Run all examples")
        for name in examples:
            print(f"  {name}")
        sys.exit(0)

    example_name = sys.argv[1]

    if example_name == "all":
        for name, example in examples.items():
            print(f"\n{'=' * 60}")
            print(f"Running: {name}")
            print("=" * 60 + "\n")
            try:
                await example()
            except Exception as e:
                print(f"Error in {name}: {e}")
            print("-" * 50 + "\n")
    elif example_name in examples:
        await examples[example_name]()
    else:
        print(f"Error: Unknown example '{example_name}'")
        print("\nAvailable examples:")
        print("  all - Run all examples")
        for name in examples:
            print(f"  {name}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
