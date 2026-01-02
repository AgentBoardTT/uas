# Getting Started

This guide will help you get up and running with the Universal Agent SDK.

## Installation

### Basic Installation

```bash
pip install universal-agent-sdk
```

### With Optional Dependencies

```bash
# All providers and features
pip install universal-agent-sdk[all]

# Specific providers
pip install universal-agent-sdk[openai]    # OpenAI support
pip install universal-agent-sdk[azure]     # Azure OpenAI support
pip install universal-agent-sdk[gemini]    # Google Gemini support
pip install universal-agent-sdk[ollama]    # Ollama local models
```

## Environment Setup

### API Keys

Set up your preferred provider's API key as an environment variable:

```bash
# Claude (Anthropic) - Default provider
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Azure OpenAI
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"

# Google Gemini
export GOOGLE_API_KEY="your-key"
```

### Using a .env File

Create a `.env` file in your project root:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
```

The SDK automatically loads `.env` files.

## Your First Query

### Simple One-Shot Query

```python
import asyncio
from universal_agent_sdk import query, AssistantMessage, TextBlock

async def main():
    async for message in query("What is Python?"):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)

asyncio.run(main())
```

### Query with Options

```python
import asyncio
from universal_agent_sdk import query, AgentOptions, AssistantMessage, TextBlock

async def main():
    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        system_prompt="You are a helpful assistant. Be concise.",
        max_turns=1,
    )

    async for message in query("Explain recursion in one sentence.", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")

asyncio.run(main())
```

## Multi-Turn Conversations

For multi-turn conversations that maintain context, use `UniversalAgentClient`:

```python
import asyncio
from universal_agent_sdk import UniversalAgentClient, AssistantMessage, TextBlock

async def main():
    async with UniversalAgentClient() as client:
        # First turn
        await client.send("My name is Alice and I love Python.")
        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Assistant: {block.text}")

        # Second turn - context is preserved
        await client.send("What's my name and what language do I love?")
        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Assistant: {block.text}")

asyncio.run(main())
```

## Using Different Providers

### Claude (Default)

```python
options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
)
```

### OpenAI

```python
options = AgentOptions(
    provider="openai",
    model="gpt-4o",
)
```

### Azure OpenAI

```python
options = AgentOptions(
    provider="azure_openai",
    model="gpt-4o",
    provider_config={
        "api_version": "2024-02-01",
        "deployment_name": "your-deployment",
    },
)
```

### Gemini

```python
options = AgentOptions(
    provider="gemini",
    model="gemini-pro",
)
```

### Ollama (Local)

```python
options = AgentOptions(
    provider="ollama",
    model="llama2",
    provider_config={
        "base_url": "http://localhost:11434",
    },
)
```

## Adding Tools

Tools extend your agent's capabilities:

```python
import asyncio
from universal_agent_sdk import query, tool, AgentOptions, AssistantMessage, TextBlock

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression)  # Use with caution in production
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"

@tool
def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def main():
    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[calculate.definition, get_current_time.definition],
    )

    async for message in query("What is 15 * 7 and what time is it?", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")

asyncio.run(main())
```

## Streaming Responses

For real-time output as the model generates:

```python
import asyncio
from universal_agent_sdk import UniversalAgentClient, AgentOptions, StreamEvent

async def main():
    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stream=True,
    )

    async with UniversalAgentClient(options) as client:
        await client.send("Tell me a short story about a robot.")

        async for msg in client.receive():
            if isinstance(msg, StreamEvent):
                if msg.delta and msg.delta.get("type") == "text_delta":
                    print(msg.delta.get("text", ""), end="", flush=True)

        print()  # Newline at end

asyncio.run(main())
```

## Error Handling

```python
import asyncio
from universal_agent_sdk import (
    query,
    AgentOptions,
    AuthenticationError,
    RateLimitError,
    ProviderError,
)

async def main():
    options = AgentOptions(
        provider="openai",
        model="gpt-4o",
    )

    try:
        async for message in query("Hello", options):
            print(message)
    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
    except RateLimitError as e:
        print(f"Rate limited. Retry after: {e.retry_after}s")
    except ProviderError as e:
        print(f"Provider error ({e.provider}): {e.message}")

asyncio.run(main())
```

## Next Steps

- [Configuration & Providers](./02-configuration-providers.md) - Deep dive into provider configuration
- [Core Components](./03-core-components.md) - Learn about Client, Query, and Types
- [Tools System](./04-tools.md) - Create powerful custom tools
