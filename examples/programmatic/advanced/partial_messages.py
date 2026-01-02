#!/usr/bin/env python3
"""
Example of streaming partial messages from Universal Agent SDK.

This example demonstrates how to receive streaming responses that show
text incrementally as it's being generated. This is useful for:
- Building real-time UIs that show text as it's being generated
- Providing immediate feedback to users
- Monitoring response progress

Usage:
./examples/universal_include_partial_messages.py
"""

import asyncio

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ResultMessage,
    StreamEvent,
    TextBlock,
    UniversalAgentClient,
)


async def basic_streaming():
    """Basic streaming example showing incremental text."""
    print("=== Basic Streaming Example ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stream=True,  # Enable streaming
    )

    async with UniversalAgentClient(options) as client:
        print("User: Tell me a short story about a robot.\n")
        print("Assistant: ", end="", flush=True)

        await client.send("Tell me a very short story about a robot in 3 sentences.")

        async for msg in client.receive():
            if isinstance(msg, StreamEvent):
                # StreamEvent contains incremental updates
                if msg.delta:
                    delta_type = msg.delta.get("type", "")
                    if delta_type == "text_delta":
                        # Print text as it arrives
                        text = msg.delta.get("text", "")
                        print(text, end="", flush=True)
            elif isinstance(msg, AssistantMessage):
                # Final complete message
                pass
            elif isinstance(msg, ResultMessage):
                print(f"\n\n[Completed in {msg.num_turns} turns]")

    print()


async def streaming_with_thinking():
    """Streaming with thinking/reasoning visible."""
    print("=== Streaming with Thinking Example ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stream=True,
        enable_thinking=True,  # Enable thinking blocks
        max_thinking_tokens=2000,
    )

    async with UniversalAgentClient(options) as client:
        print("User: What's 15% of 80? Think through this step by step.\n")

        await client.send("What's 15% of 80? Think through this step by step.")

        current_block_type = None

        async for msg in client.receive():
            if isinstance(msg, StreamEvent):
                if msg.delta:
                    delta_type = msg.delta.get("type", "")

                    if delta_type == "thinking_delta":
                        if current_block_type != "thinking":
                            print("[Thinking]", flush=True)
                            current_block_type = "thinking"
                        text = msg.delta.get("thinking", "")
                        print(text, end="", flush=True)

                    elif delta_type == "text_delta":
                        if current_block_type != "text":
                            print("\n[Response]", flush=True)
                            current_block_type = "text"
                        text = msg.delta.get("text", "")
                        print(text, end="", flush=True)

            elif isinstance(msg, ResultMessage):
                print(f"\n\n[Completed in {msg.num_turns} turns]")

    print()


async def streaming_message_types():
    """Show different message types during streaming."""
    print("=== Streaming Message Types Example ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stream=True,
    )

    message_types: dict[str, int] = {}

    async with UniversalAgentClient(options) as client:
        print("User: What is 2 + 2?\n")

        await client.send("What is 2 + 2?")

        async for msg in client.receive():
            msg_type = type(msg).__name__
            message_types[msg_type] = message_types.get(msg_type, 0) + 1

            if isinstance(msg, StreamEvent):
                if msg.delta and msg.delta.get("type") == "text_delta":
                    text = msg.delta.get("text", "")
                    print(text, end="", flush=True)
            elif isinstance(msg, AssistantMessage):
                pass  # Already printed via streaming
            elif isinstance(msg, ResultMessage):
                print()

    print("\n\nMessage types received:")
    for msg_type, count in message_types.items():
        print(f"  {msg_type}: {count}")

    print()


async def non_streaming_comparison():
    """Compare streaming vs non-streaming mode."""
    print("=== Streaming vs Non-Streaming Comparison ===\n")

    # Non-streaming
    print("--- Non-Streaming Mode ---")
    options_non_stream = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stream=False,
    )

    print("User: Say hello\n")

    async with UniversalAgentClient(options_non_stream) as client:
        await client.send("Say hello")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"[Complete message received] {block.text}")
            elif isinstance(msg, ResultMessage):
                print(f"[Completed in {msg.num_turns} turns]")

    print()

    # Streaming
    print("--- Streaming Mode ---")
    options_stream = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stream=True,
    )

    print("User: Say hello\n")
    print("Streaming: ", end="", flush=True)

    async with UniversalAgentClient(options_stream) as client:
        await client.send("Say hello")

        async for msg in client.receive():
            if isinstance(msg, StreamEvent):
                if msg.delta and msg.delta.get("type") == "text_delta":
                    print(msg.delta.get("text", ""), end="", flush=True)
            elif isinstance(msg, ResultMessage):
                print(f"\n[Completed in {msg.num_turns} turns]")

    print()


async def main():
    """Run all streaming examples."""
    print("Partial Message Streaming Examples")
    print("=" * 60)
    print("\nThis example demonstrates streaming partial messages")
    print("for real-time response display.")
    print("=" * 60 + "\n")

    await basic_streaming()
    print("-" * 50 + "\n")

    await streaming_message_types()
    print("-" * 50 + "\n")

    await non_streaming_comparison()
    print("-" * 50 + "\n")

    # Only run thinking example if provider supports it
    try:
        await streaming_with_thinking()
    except Exception as e:
        print(f"Thinking example skipped: {e}")


if __name__ == "__main__":
    asyncio.run(main())
