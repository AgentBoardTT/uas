# Universal Agent SDK Documentation

A comprehensive, multi-provider LLM agent framework for Python that enables building sophisticated AI agents with tools, skills, memory, and hooks.

## Table of Contents

1. [Getting Started](./01-getting-started.md)
2. [Configuration & Providers](./02-configuration-providers.md)
3. [Core Components](./03-core-components.md)
4. [Tools System](./04-tools.md)
5. [Skills System](./05-skills.md)
6. [Hooks System](./06-hooks.md)
7. [Agents System](./07-agents.md)
8. [Memory System](./08-memory.md)
9. [API Reference](./09-api-reference.md)
10. [Migration Guide](./10-migration-guide.md)

## Overview

The Universal Agent SDK is a Python framework designed to work seamlessly with multiple LLM providers including:

- **Claude (Anthropic)** - Full support including extended thinking
- **OpenAI** - GPT-4, GPT-4o, and other models
- **Azure OpenAI** - Enterprise Azure deployments
- **Gemini (Google)** - Google's AI models
- **Ollama** - Local model hosting

### Key Features

- **Multi-Provider Support**: Switch between providers with a single configuration change
- **Tool System**: Create custom tools with a simple decorator or use built-in tools
- **Skills System**: Reusable, composable agent capabilities
- **Hooks System**: Intercept and modify agent behavior at key points
- **Memory System**: Persistent and conversation memory for context retention
- **Streaming Support**: Real-time streaming responses
- **Type Safety**: Full type hints and dataclass-based configuration

### Quick Example

```python
import asyncio
from universal_agent_sdk import query, tool, AgentOptions

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"Weather in {city}: Sunny, 72F"

async def main():
    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[get_weather.definition],
    )

    async for message in query("What's the weather in Paris?", options):
        print(message)

asyncio.run(main())
```

## Repository Structure

```
src/universal_agent_sdk/
├── __init__.py                    # Main exports and version
├── client.py                      # UniversalAgentClient class
├── query.py                       # One-shot query functions
├── types.py                       # Type definitions
├── config.py                      # Configuration management
├── errors.py                      # Exception hierarchy
├── providers/                     # LLM provider implementations
│   ├── base.py                   # BaseProvider abstract class
│   ├── claude.py                 # Claude/Anthropic provider
│   └── openai.py                 # OpenAI/Azure providers
├── tools/                        # Tool system
│   ├── base.py                   # @tool decorator and Tool class
│   ├── registry.py               # ToolRegistry
│   ├── memory.py                 # Memory tool implementation
│   └── builtin/                  # Built-in tools
│       ├── read.py               # ReadTool
│       ├── write.py              # WriteTool
│       ├── edit.py               # EditTool
│       ├── bash.py               # BashTool
│       ├── glob.py               # GlobTool
│       ├── grep.py               # GrepTool
│       └── notebook_edit.py      # NotebookEditTool
├── skills/                       # Skills system
│   ├── base.py                   # Skill dataclass
│   ├── registry.py               # SkillRegistry
│   ├── loader.py                 # Skill discovery
│   └── builtin/                  # Built-in skills
├── agents/                       # Agent system
│   ├── base.py                   # Agent class
│   ├── registry.py               # AgentRegistry
│   └── subagent.py               # SubAgent class
├── memory/                       # Memory system
│   ├── base.py                   # BaseMemory abstract class
│   ├── conversation.py           # ConversationMemory
│   └── persistent.py             # PersistentMemory
└── hooks/                        # Hook system (integrated in client)
```

## Installation

```bash
pip install universal-agent-sdk
```

Or with optional dependencies:

```bash
# For all providers
pip install universal-agent-sdk[all]

# For specific providers
pip install universal-agent-sdk[openai]
pip install universal-agent-sdk[azure]
pip install universal-agent-sdk[gemini]
```

## Environment Setup

Set up your API keys:

```bash
# Claude (Anthropic)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Azure OpenAI
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_API_VERSION="2024-02-01"

# Gemini
export GOOGLE_API_KEY="..."

# Ollama (local)
export OLLAMA_BASE_URL="http://localhost:11434"
```

## Next Steps

- [Getting Started](./01-getting-started.md) - Installation and first steps
- [Configuration & Providers](./02-configuration-providers.md) - Provider setup and switching
- [Core Components](./03-core-components.md) - Client, Query, and Types
