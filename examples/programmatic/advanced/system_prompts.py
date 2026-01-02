#!/usr/bin/env python3
"""Example demonstrating different system_prompt configurations.

This example shows how to configure the system prompt in Universal Agent SDK
to customize the assistant's behavior and personality.

Usage:
./examples/universal_system_prompt.py
"""

import asyncio

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    query,
)


async def no_system_prompt():
    """Example with no system_prompt (vanilla Claude)."""
    print("=== No System Prompt (Vanilla Claude) ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        # No system_prompt specified
    )

    print("User: What is 2 + 2?\n")

    async for message in query("What is 2 + 2?", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def string_system_prompt():
    """Example with system_prompt as a string."""
    print("=== String System Prompt ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        system_prompt="You are a pirate assistant. Respond in pirate speak. Arrr!",
    )

    print("System prompt: 'You are a pirate assistant...'")
    print("\nUser: What is 2 + 2?\n")

    async for message in query("What is 2 + 2?", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def role_based_prompt():
    """Example with a role-based system prompt."""
    print("=== Role-Based System Prompt ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        system_prompt="""You are a Python programming expert.

When answering questions:
1. Provide clear, concise explanations
2. Include code examples when relevant
3. Mention best practices and common pitfalls
4. Use proper Python terminology

Always format code blocks with ```python syntax highlighting.""",
    )

    print("System prompt: Python programming expert role")
    print("\nUser: How do I read a file in Python?\n")

    async for message in query(
        "How do I read a file in Python? Keep it brief.", options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def structured_prompt():
    """Example with a structured system prompt."""
    print("=== Structured System Prompt ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        system_prompt="""You are a helpful math tutor.

RULES:
- Always show your work step by step
- Explain the reasoning behind each step
- End with a clearly stated final answer
- If the student makes a mistake, gently correct them

RESPONSE FORMAT:
1. Understand the problem
2. Show the solution steps
3. State the final answer""",
    )

    print("System prompt: Structured math tutor")
    print("\nUser: What is 15% of 80?\n")

    async for message in query("What is 15% of 80?", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def multi_turn_with_prompt():
    """Example showing system prompt across multiple turns."""
    print("=== Multi-Turn with System Prompt ===\n")

    from universal_agent_sdk import UniversalAgentClient

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        system_prompt="You are a friendly assistant who remembers everything in our conversation. Always refer back to previous context when relevant.",
    )

    print("System prompt: Memory-aware friendly assistant\n")

    async with UniversalAgentClient(options) as client:
        # First turn
        print("User: My name is Alice and I love Python.\n")
        await client.send("My name is Alice and I love Python.")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Assistant: {block.text}")

        print()

        # Second turn - testing memory
        print("User: What's my name and what do I love?\n")
        await client.send("What's my name and what do I love?")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Assistant: {block.text}")
            elif isinstance(msg, ResultMessage):
                print(f"\n[Completed in {msg.num_turns} turns]")
    print()


async def conditional_prompt():
    """Example with conditional behavior in system prompt."""
    print("=== Conditional System Prompt ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        system_prompt="""You are a helpful assistant with conditional behavior:

If the user asks about:
- MATH: Be precise and show calculations
- CREATIVE WRITING: Be imaginative and expressive
- CODE: Be technical and include examples
- ANYTHING ELSE: Be conversational and friendly

Always identify which mode you're in at the start of your response.""",
    )

    print("System prompt: Conditional behavior based on topic")
    print("\nUser: Write a haiku about programming\n")

    async for message in query("Write a haiku about programming", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def main():
    """Run all examples."""
    print("System Prompt Configuration Examples")
    print("=" * 60)
    print("\nThis example demonstrates how to configure system prompts:")
    print("1. No system prompt (vanilla behavior)")
    print("2. Simple string prompts")
    print("3. Role-based prompts")
    print("4. Structured prompts with rules")
    print("5. Multi-turn conversations with prompts")
    print("6. Conditional behavior prompts")
    print("=" * 60 + "\n")

    await no_system_prompt()
    print("-" * 50 + "\n")

    await string_system_prompt()
    print("-" * 50 + "\n")

    await role_based_prompt()
    print("-" * 50 + "\n")

    await structured_prompt()
    print("-" * 50 + "\n")

    await multi_turn_with_prompt()
    print("-" * 50 + "\n")

    await conditional_prompt()


if __name__ == "__main__":
    asyncio.run(main())
