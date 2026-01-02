#!/usr/bin/env python3
"""Example demonstrating max_budget_usd option for cost control.

This example shows how to use the max_budget_usd option in Universal Agent SDK
to control and limit API costs during agent execution.

Note: Unlike the Claude SDK CLI which enforces budget limits at the CLI level,
the Universal SDK's budget tracking would need to be implemented based on
usage information returned from API calls.

Usage:
./examples/universal_max_budget_usd.py
"""

import asyncio

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    query,
)


async def without_budget():
    """Example without budget limit."""
    print("=== Without Budget Limit ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        # No max_budget_usd specified
    )

    print("User: What is 2 + 2?\n")

    async for message in query("What is 2 + 2?", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            if message.usage:
                print(f"\nTokens used: {message.usage.total_tokens}")
            if message.total_cost_usd:
                print(f"Total cost: ${message.total_cost_usd:.6f}")
    print()


async def with_reasonable_budget():
    """Example with budget that won't be exceeded."""
    print("=== With Reasonable Budget ($0.10) ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        max_budget_usd=0.10,  # 10 cents - plenty for a simple query
    )

    print(f"Budget set: ${options.max_budget_usd}")
    print("User: What is 2 + 2?\n")

    async for message in query("What is 2 + 2?", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            if message.usage:
                print(f"\nTokens used: {message.usage.total_tokens}")
            if message.total_cost_usd:
                print(f"Total cost: ${message.total_cost_usd:.6f}")
                if options.max_budget_usd:
                    remaining = options.max_budget_usd - message.total_cost_usd
                    print(f"Remaining budget: ${remaining:.6f}")
    print()


async def with_tight_budget():
    """Example with very tight budget."""
    print("=== With Tight Budget ($0.0001) ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        max_budget_usd=0.0001,  # Very small budget
    )

    print(f"Budget set: ${options.max_budget_usd}")
    print("Note: Budget enforcement depends on implementation")
    print("User: What is 2 + 2?\n")

    async for message in query("What is 2 + 2?", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            if message.usage:
                print(f"\nTokens used: {message.usage.total_tokens}")
            if message.total_cost_usd:
                print(f"Total cost: ${message.total_cost_usd:.6f}")
                if (
                    options.max_budget_usd
                    and message.total_cost_usd > options.max_budget_usd
                ):
                    print("Warning: Cost exceeded budget!")
    print()


async def budget_tracking_example():
    """Example showing how to track costs across multiple queries."""
    print("=== Budget Tracking Example ===\n")

    from universal_agent_sdk import UniversalAgentClient

    total_cost = 0.0
    max_budget = 0.05  # 5 cents total budget

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        max_budget_usd=max_budget,
    )

    print(f"Total budget: ${max_budget}")
    print()

    queries = [
        "What is 1 + 1?",
        "What is 2 + 2?",
        "What is 3 + 3?",
    ]

    async with UniversalAgentClient(options) as client:
        for i, q in enumerate(queries, 1):
            if total_cost >= max_budget:
                print(f"Query {i}: Skipped - budget exhausted")
                continue

            print(f"Query {i}: {q}")
            await client.send(q)

            async for msg in client.receive():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(f"  Response: {block.text}")
                elif isinstance(msg, ResultMessage) and msg.total_cost_usd:
                    total_cost += msg.total_cost_usd
                    print(f"  Cost: ${msg.total_cost_usd:.6f}")
                    print(f"  Running total: ${total_cost:.6f}")

            print()

    print(f"Final total cost: ${total_cost:.6f}")
    print(f"Budget remaining: ${max(0, max_budget - total_cost):.6f}")


async def main():
    """Run all examples."""
    print("Max Budget USD Examples")
    print("=" * 60)
    print("\nThis example demonstrates how to use max_budget_usd")
    print("to control and limit API costs during agent execution.")
    print("=" * 60 + "\n")

    await without_budget()
    print("-" * 50 + "\n")

    await with_reasonable_budget()
    print("-" * 50 + "\n")

    await with_tight_budget()
    print("-" * 50 + "\n")

    await budget_tracking_example()


if __name__ == "__main__":
    asyncio.run(main())
