"""Multi-provider example for Universal Agent SDK.

This example demonstrates using different LLM providers with the same SDK interface.
"""

import asyncio
import os

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ProviderRegistry,
    TextBlock,
    complete,
    query,
)


async def list_providers():
    """List all registered providers."""
    print("=== Available Providers ===\n")

    providers = ProviderRegistry.list_providers()
    for name in providers:
        print(f"  - {name}")

    print()


async def compare_providers():
    """Compare responses from different providers."""
    print("=== Provider Comparison ===\n")

    prompt = "Explain what an API is in one sentence."

    # Configure providers to test
    provider_configs = [
        {
            "name": "Claude",
            "options": AgentOptions(
                provider="claude",
                model="claude-sonnet-4-20250514",
            ),
        },
        # Uncomment these if you have the API keys configured:
        # {
        #     "name": "OpenAI",
        #     "options": AgentOptions(
        #         provider="openai",
        #         model="gpt-4o",
        #     ),
        # },
        # {
        #     "name": "Azure OpenAI",
        #     "options": AgentOptions(
        #         provider="azure_openai",
        #         model="gpt-4o",  # Your deployment name
        #     ),
        # },
    ]

    for config in provider_configs:
        print(f"--- {config['name']} ---")

        # Check if API key is configured
        provider = config["options"].provider
        if provider == "claude" and not os.environ.get("ANTHROPIC_API_KEY"):
            print("  Skipped: ANTHROPIC_API_KEY not set\n")
            continue
        elif provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
            print("  Skipped: OPENAI_API_KEY not set\n")
            continue
        elif provider == "azure_openai" and not os.environ.get("AZURE_OPENAI_API_KEY"):
            print("  Skipped: AZURE_OPENAI_API_KEY not set\n")
            continue

        try:
            response = await complete(prompt, config["options"])
            for block in response.content:
                if isinstance(block, TextBlock):
                    print(f"  {block.text}")
        except Exception as e:
            print(f"  Error: {e}")

        print()


async def provider_features():
    """Check provider feature support."""
    print("=== Provider Features ===\n")

    providers = ["claude", "openai", "azure_openai"]

    for name in providers:
        try:
            provider = ProviderRegistry.get(name)
            features = provider.get_features()

            print(f"{name}:")
            print(f"  Streaming: {features.streaming}")
            print(f"  Tool calling: {features.tool_calling}")
            print(f"  Vision: {features.vision}")
            print(f"  Thinking: {features.thinking}")
            print(f"  Max context: {features.max_context_length:,}")
            print()
        except Exception as e:
            print(f"{name}: Not available ({e})\n")


async def dynamic_provider_selection():
    """Dynamically select provider based on task."""
    print("=== Dynamic Provider Selection ===\n")

    def select_provider(task: str) -> AgentOptions:
        """Select the best provider for a task."""
        task_lower = task.lower()

        # Claude for code and complex reasoning
        if any(word in task_lower for word in ["code", "program", "analyze", "complex"]):
            return AgentOptions(provider="claude", model="claude-sonnet-4-20250514")

        # OpenAI for general tasks (if available)
        if os.environ.get("OPENAI_API_KEY"):
            return AgentOptions(provider="openai", model="gpt-4o")

        # Default to Claude
        return AgentOptions(provider="claude", model="claude-sonnet-4-20250514")

    tasks = [
        "Write a Python function to sort a list",
        "What is the weather like today?",
        "Analyze this complex algorithm",
    ]

    for task in tasks:
        options = select_provider(task)
        print(f"Task: {task}")
        print(f"Selected: {options.provider} ({options.model})\n")


async def fallback_providers():
    """Implement provider fallback."""
    print("=== Provider Fallback ===\n")

    prompt = "Say hello"

    # Try providers in order
    providers = [
        ("claude", "claude-sonnet-4-20250514"),
        ("openai", "gpt-4o"),
    ]

    for provider, model in providers:
        try:
            options = AgentOptions(provider=provider, model=model)
            response = await complete(prompt, options)

            print(f"Success with {provider}:")
            for block in response.content:
                if isinstance(block, TextBlock):
                    print(f"  {block.text}")
            break

        except Exception as e:
            print(f"Failed with {provider}: {e}")
            continue
    else:
        print("All providers failed!")


if __name__ == "__main__":
    asyncio.run(list_providers())
    asyncio.run(compare_providers())
    asyncio.run(provider_features())
    asyncio.run(dynamic_provider_selection())
    asyncio.run(fallback_providers())
