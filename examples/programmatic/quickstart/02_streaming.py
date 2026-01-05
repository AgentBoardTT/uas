"""Streaming client example for multi-turn conversations.

This example shows how to use UniversalAgentClient for interactive,
multi-turn conversations with streaming responses.
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


async def basic_conversation():
    """Basic multi-turn conversation."""
    print("=== Multi-turn Conversation ===\n")

    async with UniversalAgentClient() as client:
        # First turn
        print("User: What is Python?")
        await client.send("What is Python?")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                text = "".join(
                    block.text for block in msg.content if isinstance(block, TextBlock)
                )
                print(f"Assistant: {text}\n")
            elif isinstance(msg, ResultMessage):
                if msg.usage:
                    print(f"[Tokens: {msg.usage.total_tokens}]")

        # Follow-up (context is maintained)
        print("\nUser: What are its main features?")
        await client.send("What are its main features?")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                text = "".join(
                    block.text for block in msg.content if isinstance(block, TextBlock)
                )
                print(f"Assistant: {text}\n")


async def streaming_output():
    """Show streaming text as it arrives."""
    print("\n=== Streaming Output ===\n")

    options = AgentOptions(stream=True)

    async with UniversalAgentClient(options) as client:
        print("User: Tell me a short story about a robot.\n")
        print("Assistant: ", end="", flush=True)

        await client.send("Tell me a very short story about a robot in 3 sentences.")

        async for msg in client.receive():
            if isinstance(msg, StreamEvent):
                # Print streaming text as it arrives
                if msg.delta and msg.delta.get("type") == "text_delta":
                    print(msg.delta.get("text", ""), end="", flush=True)
            elif isinstance(msg, ResultMessage):
                print("\n")


async def with_provider_switching():
    """Switch providers mid-conversation."""
    print("\n=== Provider Switching ===\n")

    async with UniversalAgentClient() as client:
        # Start with Claude
        print("[Using Claude]")
        print("User: What's 2+2?")
        await client.send("What's 2+2?")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                text = "".join(
                    block.text for block in msg.content if isinstance(block, TextBlock)
                )
                print(f"Assistant: {text}\n")

        # Switch to OpenAI (if configured)
        # client.set_provider("openai")
        # client.set_model("gpt-4o")

        # Continue conversation
        print("User: What about 3+3?")
        await client.send("What about 3+3?")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                text = "".join(
                    block.text for block in msg.content if isinstance(block, TextBlock)
                )
                print(f"Assistant: {text}")


async def conversation_history():
    """Access conversation history."""
    print("\n=== Conversation History ===\n")

    async with UniversalAgentClient() as client:
        await client.send("My favorite color is blue.")
        async for _ in client.receive():
            pass

        await client.send("What's my favorite color?")
        async for _ in client.receive():
            pass

        print("Conversation history:")
        for i, msg in enumerate(client.messages):
            role = type(msg).__name__.replace("Message", "")
            if hasattr(msg, "content"):
                if isinstance(msg.content, str):
                    content = msg.content[:50]
                else:
                    content = str(msg.content)[:50]
                print(f"  {i+1}. [{role}] {content}...")


if __name__ == "__main__":
    asyncio.run(basic_conversation())
    asyncio.run(streaming_output())
    asyncio.run(with_provider_switching())
    asyncio.run(conversation_history())
