"""Basic query example for Universal Agent SDK.

This example shows the simplest way to use the SDK - making a one-shot query.
"""

import asyncio

from universal_agent_sdk import AgentOptions, AssistantMessage, TextBlock, query


async def main():
    """Basic query example."""
    print("=== Basic Query Example ===\n")

    # Simple query with default provider (Claude)
    print("Asking: What is the capital of France?\n")

    async for message in query("What is the capital of France?"):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Response: {block.text}")


async def with_options():
    """Query with custom options."""
    print("\n=== Query with Options ===\n")

    options = AgentOptions(
        provider="claude",  # or "openai", "azure_openai"
        model="claude-sonnet-4-20250514",
        temperature=0.7,
        max_tokens=500,
    )

    print("Asking: Write a haiku about programming.\n")

    async for message in query("Write a haiku about programming.", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


async def switch_providers():
    """Example showing provider switching."""
    print("\n=== Provider Switching ===\n")

    providers = [
        ("claude", "claude-sonnet-4-20250514"),
        # Uncomment these if you have the API keys configured:
        # ("openai", "gpt-4o"),
        # ("azure_openai", "gpt-4o"),
    ]

    for provider, model in providers:
        print(f"\n--- Using {provider} ({model}) ---")

        options = AgentOptions(provider=provider, model=model)

        try:
            async for message in query("Say hello in one sentence.", options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Response: {block.text}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(with_options())
    asyncio.run(switch_providers())
