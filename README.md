<h1 align="center">
  Universal Agent SDK
</h1>

<p align="center">
  <strong>Build powerful AI agents that work across any LLM provider</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/universal-agent-sdk/"><img src="https://img.shields.io/pypi/v/universal-agent-sdk?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square" alt="Python 3.10+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs Welcome"></a>
</p>

<p align="center">
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#examples">Examples</a> •
  <a href="#documentation">Docs</a> •
  <a href="#contributing">Contributing</a>
</p>

---

Universal Agent SDK is a provider-agnostic Python framework for building LLM-powered agents. Write your agent logic once and run it on **Claude**, **OpenAI**, **Azure OpenAI**, **Gemini**, or any other provider—with zero code changes.

```python
from universal_agent_sdk import query, AgentOptions

# Works with any provider - just change the config
options = AgentOptions(provider="openai", model="gpt-4o")

async for message in query("Explain quantum computing", options):
    print(message)
```

## Why Universal Agent SDK?

- **🔄 Provider Agnostic** - Switch between Claude, GPT-4, Gemini with one line
- **🛠️ Batteries Included** - Built-in tools for file ops, web search, shell commands
- **📦 Preset Configs** - Load agent configurations from YAML/JSON files
- **🎣 Hooks System** - Intercept and modify behavior at any point
- **🧠 Memory System** - Conversation and persistent memory out of the box
- **🔒 Type Safe** - Full type hints and dataclass configuration

---

## Installation

```bash
pip install universal-agent-sdk
```

**With specific providers:**

```bash
pip install universal-agent-sdk[openai]      # OpenAI/Azure
pip install universal-agent-sdk[google]      # Gemini
pip install universal-agent-sdk[all]         # All providers
```

**Development installation:**

```bash
git clone https://github.com/your-org/universal-agent-sdk-python.git
cd universal-agent-sdk-python
pip install -e ".[dev]"
```

---

## Quick Start

### 1. Set up your API key

```bash
cp .env.sample .env
# Edit .env with your API keys
```

### 2. Simple Query

```python
import asyncio
from universal_agent_sdk import query, AgentOptions

async def main():
    options = AgentOptions(
        provider="claude",
        model="claude-sonnet-4-20250514",
    )

    async for message in query("What is the capital of France?", options):
        print(message)

asyncio.run(main())
```

### 3. Interactive Conversation

```python
import asyncio
from universal_agent_sdk import UniversalAgentClient, AgentOptions

async def main():
    options = AgentOptions(
        provider="openai",
        model="gpt-4o",
        system_prompt="You are a helpful coding assistant.",
    )

    async with UniversalAgentClient(options) as client:
        # First message
        await client.send("Write a Python function to reverse a string")
        async for msg in client.receive():
            print(msg)

        # Follow-up (context is maintained)
        await client.send("Now add type hints to it")
        async for msg in client.receive():
            print(msg)

asyncio.run(main())
```

### 4. Using Presets

```bash
# List available presets
uv run python examples/programmatic/showcase/preset_loader.py --list

# Run with a preset
uv run python examples/programmatic/showcase/preset_loader.py --preset virtual-assistant
```

---

## Features

### Multi-Provider Support

Switch providers with a single config change:

```python
# Claude (Anthropic)
options = AgentOptions(provider="claude", model="claude-sonnet-4-20250514")

# OpenAI
options = AgentOptions(provider="openai", model="gpt-4o")

# Azure OpenAI
options = AgentOptions(
    provider="azure_openai",
    model="gpt-4o",
    provider_config={
        "endpoint": "https://your-resource.openai.azure.com",
        "deployment_name": "your-deployment",
    },
)

# Google Gemini
options = AgentOptions(provider="gemini", model="gemini-pro")
```

### Built-in Tools

Ready-to-use tools for common operations:

| Tool | Description |
|------|-------------|
| `ReadTool` | Read file contents with line numbers |
| `WriteTool` | Create or overwrite files |
| `EditTool` | Edit files using string replacement |
| `BashTool` | Execute shell commands |
| `GlobTool` | Find files by pattern matching |
| `GrepTool` | Search file contents with regex |
| `WebSearchTool` | Search the web via DuckDuckGo |
| `WebFetchTool` | Fetch and extract web page content |
| `DateTimeTool` | Get current date and time |
| `NotebookEditTool` | Edit Jupyter notebooks |

```python
from universal_agent_sdk import AgentOptions
from universal_agent_sdk.tools import ReadTool, BashTool, WebSearchTool

options = AgentOptions(
    provider="claude",
    tools=[
        ReadTool().to_tool_definition(),
        BashTool().to_tool_definition(),
        WebSearchTool().to_tool_definition(),
    ],
)
```

### Custom Tools

Create tools with the simple `@tool` decorator:

```python
from universal_agent_sdk import tool, query, AgentOptions

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The city name (e.g., "London", "Tokyo")
    """
    # Your implementation here
    return f"Weather in {city}: Sunny, 72°F"

@tool
async def fetch_stock_price(symbol: str) -> str:
    """Fetch the current stock price.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL")
    """
    # Async tools are supported!
    return f"{symbol}: $150.00"

options = AgentOptions(
    tools=[get_weather.definition, fetch_stock_price.definition],
)
```

### Preset Configurations

Define agent configurations in YAML:

```yaml
# presets/research-agent.yaml
id: research-agent
name: Research Agent
description: Web research specialist

provider: claude
model: claude-sonnet-4-20250514

system_prompt: |
  You are a research assistant specialized in finding
  and analyzing information from web sources.

allowed_tools:
  - WebSearch
  - WebFetch
  - Read
  - Write

permission_mode: acceptEdits
max_turns: 50
```

Load and use:

```python
from universal_agent_sdk import load_preset, preset_to_options_with_tools

preset = load_preset("presets/research-agent.yaml")
options = preset_to_options_with_tools(preset)  # Auto-loads tools!
```

### Hooks System

Intercept and modify agent behavior:

```python
from universal_agent_sdk import AgentOptions, HookMatcher

async def log_tool_use(input_data, tool_use_id, context):
    print(f"Tool called: {input_data['tool_name']}")
    return {}  # Continue execution

async def approve_dangerous_tools(input_data, tool_use_id, context):
    if input_data["tool_name"] == "Bash":
        # Could prompt user for approval here
        return {"hookSpecificOutput": {"permissionDecision": "allow"}}
    return {}

options = AgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(hooks=[log_tool_use]),
            HookMatcher(matcher="Bash", hooks=[approve_dangerous_tools]),
        ],
    },
)
```

### Memory System

```python
from universal_agent_sdk import AgentOptions
from universal_agent_sdk.memory import ConversationMemory, PersistentMemory

# In-memory conversation history
options = AgentOptions(
    memory_enabled=True,
    memory_type="conversation",
)

# Persistent memory with file storage
options = AgentOptions(
    memory_enabled=True,
    memory_type="persistent",
    memory_config={"storage_path": "./memory"},
)
```

---

## Examples

The `examples/` directory is organized for easy navigation:

```
examples/
├── programmatic/              # Direct SDK usage
│   ├── quickstart/            # Getting started
│   │   ├── 01_basic_query.py
│   │   ├── 02_streaming.py
│   │   ├── 03_options_demo.py
│   │   ├── 04_interactive_chat.py
│   │   └── 05_streaming_modes.py
│   ├── tools/                 # Tool examples
│   ├── memory/                # Memory system
│   ├── skills/                # Skills framework
│   ├── hooks/                 # Hook system
│   ├── agents/                # Agent patterns
│   ├── providers/             # Multi-provider
│   ├── advanced/              # Advanced features
│   ├── presets/               # YAML configurations
│   └── showcase/              # Full demos
│       ├── ultimate_assistant.py
│       ├── preset_loader.py
│       └── coding_agent.py
│
├── cli-tool/                  # Claude Code-like CLI (coming soon)
├── vscode-extension/          # Copilot-like extension (coming soon)
├── desktop-ide/               # Cursor-like IDE (coming soon)
└── web-backend/               # FastAPI/Streamlit backend (coming soon)
```

### Run Examples

```bash
# Basic query
uv run python examples/programmatic/quickstart/01_basic_query.py

# Interactive chat with presets
uv run python examples/programmatic/showcase/preset_loader.py --preset virtual-assistant

# Full-featured assistant
uv run python examples/programmatic/showcase/ultimate_assistant.py
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](./docs/01-getting-started.md) | Installation and first steps |
| [Configuration](./docs/02-configuration-providers.md) | Provider setup and options |
| [Core Components](./docs/03-core-components.md) | Client, query, messages |
| [Tools](./docs/04-tools.md) | Built-in and custom tools |
| [Skills](./docs/05-skills.md) | Reusable agent components |
| [Hooks](./docs/06-hooks.md) | Behavior modification |
| [Agents](./docs/07-agents.md) | Agent patterns and sub-agents |
| [Memory](./docs/08-memory.md) | Conversation and persistence |
| [API Reference](./docs/09-api-reference.md) | Complete API documentation |

---

## Configuration

### Environment Variables

Copy `.env.sample` to `.env` and configure:

```bash
# Required: At least one provider API key
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Optional: Azure, Google, AWS
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
GOOGLE_API_KEY=...
```

### AgentOptions Reference

```python
AgentOptions(
    # Provider
    provider="claude",              # claude, openai, azure_openai, gemini
    model="claude-sonnet-4-20250514",

    # Prompts
    system_prompt="You are helpful.",

    # Tools
    tools=[...],                    # List of ToolDefinition
    tool_choice="auto",             # auto, required, none

    # Behavior
    max_tokens=4096,
    temperature=0.7,
    max_turns=10,

    # Memory
    memory_enabled=False,
    memory_type="conversation",

    # Streaming
    stream=True,

    # Hooks
    hooks={...},
)
```

---

## Development

```bash
# Clone and install
git clone https://github.com/your-org/universal-agent-sdk-python.git
cd universal-agent-sdk-python
uv sync --all-extras

# Run linting
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type checking
uv run mypy src/

# Run tests
uv run pytest tests/ -v
```

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

<p align="center">
  Made with ❤️ by the Universal Agent SDK team
</p>
