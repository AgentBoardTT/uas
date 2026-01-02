# Configuration & Providers

The Universal Agent SDK supports multiple LLM providers with a unified interface. This guide covers provider configuration, switching, and advanced setup.

## Supported Providers

| Provider | Name | Default Model | Features |
|----------|------|---------------|----------|
| Claude (Anthropic) | `anthropic` or `claude` | claude-sonnet-4-20250514 | Streaming, Tools, Vision, Thinking |
| OpenAI | `openai` | gpt-4o | Streaming, Tools, Vision, JSON Mode |
| Azure OpenAI | `azure_openai` | gpt-4o | Streaming, Tools, Vision |
| Google Gemini | `gemini` | gemini-pro | Streaming, Tools |
| Ollama | `ollama` | llama2 | Streaming, Local hosting |

## Environment Variables

### Claude (Anthropic)

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_BASE_URL=https://api.anthropic.com  # Optional, for proxies
```

### OpenAI

```bash
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
OPENAI_ORG_ID=org-...  # Optional, for organization
```

### Azure OpenAI

```bash
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

### Google Gemini

```bash
GOOGLE_API_KEY=your-key
GOOGLE_PROJECT_ID=your-project  # Optional, for Vertex AI
GOOGLE_LOCATION=us-central1     # Optional, for Vertex AI
```

### Ollama

```bash
OLLAMA_BASE_URL=http://localhost:11434  # Default
```

## AgentOptions Configuration

The `AgentOptions` dataclass is the primary way to configure the SDK:

```python
from universal_agent_sdk import AgentOptions

options = AgentOptions(
    # Provider Settings
    provider="anthropic",           # Provider name
    model="claude-sonnet-4-20250514",  # Model to use
    provider_config={},             # Provider-specific config
    fallback_model=None,            # Fallback if primary fails

    # Generation Settings
    system_prompt=None,             # System prompt
    max_tokens=4096,                # Max response tokens
    temperature=0.7,                # Creativity (0.0-1.0)
    top_p=None,                     # Nucleus sampling

    # Tool Settings
    tools=[],                       # List of ToolDefinitions
    tool_choice="auto",             # "auto", "required", "none"
    can_use_tool=None,              # Permission callback

    # Session Settings
    session_id=None,                # Custom session ID
    max_turns=10,                   # Max tool execution turns

    # Streaming Settings
    stream=True,                    # Enable streaming
    include_usage=True,             # Include token usage

    # Cost Control
    max_budget_usd=None,            # Budget limit

    # Extended Features
    enable_thinking=False,          # Claude extended thinking
    max_thinking_tokens=None,       # Thinking token limit

    # Environment
    cwd=None,                       # Working directory
    env={},                         # Environment variables

    # Debug
    debug=False,                    # Enable debug mode
    stderr_callback=None,           # Debug output callback
)
```

## Provider-Specific Configuration

### Claude Configuration

```python
from universal_agent_sdk import AgentOptions

options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",  # or claude-opus-4-20250514
    provider_config={
        "api_key": "sk-ant-...",     # Override env var
        "base_url": "https://api.anthropic.com",
        "timeout": 60.0,
        "max_retries": 3,
    },
    # Claude-specific features
    enable_thinking=True,            # Extended thinking
    max_thinking_tokens=1024,
)
```

**Available Claude Models:**
- `claude-opus-4-20250514` - Most capable
- `claude-sonnet-4-20250514` - Balanced performance
- `claude-haiku-3-5-20241022` - Fast and efficient

### OpenAI Configuration

```python
options = AgentOptions(
    provider="openai",
    model="gpt-4o",
    provider_config={
        "api_key": "sk-...",
        "organization": "org-...",
        "base_url": "https://api.openai.com/v1",
        "timeout": 60.0,
    },
)
```

**Available OpenAI Models:**
- `gpt-4o` - Latest GPT-4 Omni
- `gpt-4o-mini` - Smaller, faster
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-3.5-turbo` - Fast and economical

### Azure OpenAI Configuration

```python
options = AgentOptions(
    provider="azure_openai",
    model="gpt-4o",
    provider_config={
        "api_key": "your-azure-key",
        "endpoint": "https://your-resource.openai.azure.com",
        "api_version": "2024-02-01",
        "deployment_name": "your-deployment",
    },
)
```

### Gemini Configuration

```python
options = AgentOptions(
    provider="gemini",
    model="gemini-pro",
    provider_config={
        "api_key": "your-google-key",
        # For Vertex AI:
        "project_id": "your-project",
        "location": "us-central1",
    },
)
```

### Ollama Configuration (Local)

```python
options = AgentOptions(
    provider="ollama",
    model="llama2",  # or codellama, mistral, etc.
    provider_config={
        "base_url": "http://localhost:11434",
    },
)
```

## Using the Config Class

For more control over configuration:

```python
from universal_agent_sdk import Config, get_config

# Get the global config
config = get_config()

# Check if a provider is configured
if config.is_configured("openai"):
    print("OpenAI is ready")

# List configured providers
providers = config.list_configured_providers()
print(f"Available: {providers}")

# Set configuration programmatically
config.set("openai", "api_key", "sk-...")
config.set("openai", "organization", "org-...")

# Get provider config for AgentOptions
options = AgentOptions(
    provider="openai",
    provider_config=config.get_provider_config("openai"),
)
```

## Secret Manager Integration

### AWS Secrets Manager

```python
from universal_agent_sdk import Config, aws_secret_fetcher

def my_fetcher(secret_name: str) -> str | None:
    return aws_secret_fetcher(f"prod/api-keys/{secret_name}")

config = Config(secret_fetcher=my_fetcher)
# API keys are fetched from AWS Secrets Manager
```

### Google Cloud Secret Manager

```python
from universal_agent_sdk import gcp_secret_fetcher

def my_fetcher(secret_name: str) -> str | None:
    return gcp_secret_fetcher(secret_name, project_id="my-project")

config = Config(secret_fetcher=my_fetcher)
```

### Azure Key Vault

```python
from universal_agent_sdk import azure_keyvault_fetcher

fetcher = azure_keyvault_fetcher("https://my-vault.vault.azure.net/")
config = Config(secret_fetcher=fetcher)
```

## Switching Providers Mid-Conversation

```python
import asyncio
from universal_agent_sdk import UniversalAgentClient, AgentOptions

async def main():
    # Start with Claude
    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
    )

    async with UniversalAgentClient(options) as client:
        await client.send("Hello from Claude!")
        async for msg in client.receive():
            print(msg)

        # Switch to OpenAI mid-conversation
        client.set_provider("openai", {"api_key": "sk-..."})
        client.set_model("gpt-4o")

        await client.send("Now I'm using GPT-4!")
        async for msg in client.receive():
            print(msg)

asyncio.run(main())
```

## Provider Features

Check what features a provider supports:

```python
from universal_agent_sdk.providers import ProviderRegistry

# Get provider instance
provider = ProviderRegistry.get("anthropic")

# Check features
features = provider.get_features()
print(f"Streaming: {features.streaming}")
print(f"Tool Calling: {features.tool_calling}")
print(f"Vision: {features.vision}")
print(f"Thinking: {features.thinking}")
print(f"JSON Mode: {features.json_mode}")
print(f"Max Context: {features.max_context_length}")
```

### Feature Matrix

| Feature | Claude | OpenAI | Azure | Gemini | Ollama |
|---------|--------|--------|-------|--------|--------|
| Streaming | Yes | Yes | Yes | Yes | Yes |
| Tool Calling | Yes | Yes | Yes | Yes | Varies |
| Vision | Yes | Yes | Yes | Yes | Varies |
| Extended Thinking | Yes | No | No | No | No |
| JSON Mode | Yes | Yes | Yes | No | Varies |
| Max Context | 200K | 128K | 128K | 32K | Varies |

## Custom Provider Implementation

You can create custom providers by extending `BaseProvider`:

```python
from universal_agent_sdk.providers import BaseProvider, register_provider, ProviderFeatures

@register_provider("my_provider")
class MyProvider(BaseProvider):
    def get_features(self) -> ProviderFeatures:
        return ProviderFeatures(
            streaming=True,
            tool_calling=True,
            vision=False,
            max_context_length=4096,
        )

    async def complete(self, messages, options):
        # Implement completion logic
        pass

    async def stream(self, messages, options):
        # Implement streaming logic
        pass

# Use your custom provider
options = AgentOptions(provider="my_provider")
```

## Next Steps

- [Core Components](./03-core-components.md) - Learn about Client, Query, and Types
- [Tools System](./04-tools.md) - Add capabilities to your agents
