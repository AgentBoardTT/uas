#!/usr/bin/env python3
"""Quick start example for Universal Agent SDK.

This example demonstrates basic usage patterns:
1. Simple one-shot queries
2. Queries with custom options
3. Using tools with queries

Usage:
    python examples/universal_quick_start.py
"""

import asyncio

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    query,
    tool,
)


async def basic_example():
    """Basic example - simple question."""
    print("=== Basic Example ===")

    async for message in query("What is 2 + 2?"):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
    print()


async def with_options_example():
    """Example with custom options."""
    print("=== With Options Example ===")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        system_prompt="You are a helpful assistant that explains things simply.",
        max_turns=1,
    )

    async for message in query("Explain what Python is in one sentence.", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
    print()


async def with_tools_example():
    """Example using tools."""
    print("=== With Tools Example ===")

    # Define a simple tool using the @tool decorator
    @tool
    def get_weather(city: str) -> str:
        """Get the current weather for a city."""
        # Simulated weather data
        weather_data = {
            "new york": "Sunny, 72°F",
            "london": "Cloudy, 55°F",
            "tokyo": "Rainy, 65°F",
            "paris": "Partly cloudy, 68°F",
        }
        return weather_data.get(city.lower(), f"Weather data not available for {city}")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[get_weather.definition],
        system_prompt="You are a helpful weather assistant.",
    )

    async for message in query(
        "What's the weather like in Paris?",
        options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\nTurns: {message.num_turns}")
            if message.usage:
                print(f"Tokens: {message.usage.total_tokens}")
    print()


async def multi_provider_example():
    """Example with different providers."""
    print("=== Multi-Provider Example ===")

    # You can switch providers by changing the provider option
    providers = [
        ("anthropic", "claude-sonnet-4-20250514", "Claude"),
        # Uncomment these if you have the API keys:
        # ("openai", "gpt-4o", "OpenAI"),
        # ("azure_openai", "gpt-4o", "Azure OpenAI"),
    ]

    for provider, model, name in providers:
        print(f"\n--- Using {name} ---")
        options = AgentOptions(
            provider=provider,
            model=model,
            max_turns=1,
        )

        try:
            async for message in query("Say hello in exactly 5 words.", options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"{name}: {block.text}")
        except Exception as e:
            print(f"Error with {name}: {e}")

    print()


async def main():
    """Run all examples."""
    await basic_example()
    await with_options_example()
    await with_tools_example()
    await multi_provider_example()


if __name__ == "__main__":
    asyncio.run(main())
