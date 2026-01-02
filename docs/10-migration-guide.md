# Migration Guide

This guide helps you migrate from the Claude Agent SDK to the Universal Agent SDK.

## Why Migrate?

The Universal Agent SDK provides:
- **Multi-provider support**: Use Claude, OpenAI, Azure, Gemini, and more
- **Unified API**: Same code works across providers
- **Enhanced features**: Skills, hooks, memory, and agents
- **Better maintainability**: Cleaner architecture and types

## Quick Migration Checklist

- [ ] Update imports from `claude_agent_sdk` to `universal_agent_sdk`
- [ ] Replace `ClaudeSDKClient` with `UniversalAgentClient`
- [ ] Replace `ClaudeAgentOptions` with `AgentOptions`
- [ ] Add `provider="anthropic"` to options
- [ ] Update async patterns (`anyio.run` → `asyncio.run`)
- [ ] Update tool definitions to use `@tool` decorator

## Import Changes

### Before (Claude SDK)

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    query,
    tool,
)
```

### After (Universal SDK)

```python
from universal_agent_sdk import (
    UniversalAgentClient,
    AgentOptions,
    query,
    tool,
)
```

### Full Import Mapping

| Claude SDK | Universal SDK |
|------------|---------------|
| `ClaudeSDKClient` | `UniversalAgentClient` |
| `ClaudeAgentOptions` | `AgentOptions` |
| `ClaudeMessage` | `AssistantMessage` |
| `query` | `query` (same) |
| `tool` | `tool` (same) |

## Client Migration

### Before

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import anyio

async def main():
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-20250514",
        system_prompt="You are helpful.",
    )

    async with ClaudeSDKClient(options) as client:
        await client.send("Hello")
        async for msg in client.receive():
            print(msg)

anyio.run(main)
```

### After

```python
from universal_agent_sdk import UniversalAgentClient, AgentOptions
import asyncio

async def main():
    options = AgentOptions(
        provider="anthropic",  # New: specify provider
        model="claude-sonnet-4-20250514",
        system_prompt="You are helpful.",
    )

    async with UniversalAgentClient(options) as client:
        await client.send("Hello")
        async for msg in client.receive():
            print(msg)

asyncio.run(main())  # Changed from anyio.run
```

## Query Migration

### Before

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(model="claude-sonnet-4-20250514")

async for msg in query("Hello", options):
    print(msg)
```

### After

```python
from universal_agent_sdk import query, AgentOptions

options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
)

async for msg in query("Hello", options):
    print(msg)
```

## Tool Migration

### Before

```python
from claude_agent_sdk import tool

@tool
def my_tool(arg: str) -> str:
    """Tool description."""
    return f"Result: {arg}"

# Usage
options = ClaudeAgentOptions(
    tools=[my_tool.definition],
)
```

### After

```python
from universal_agent_sdk import tool

@tool
def my_tool(arg: str) -> str:
    """Tool description."""
    return f"Result: {arg}"

# Usage (same)
options = AgentOptions(
    provider="anthropic",
    tools=[my_tool.definition],
)
```

The `@tool` decorator API is unchanged.

## Options Migration

### Before

```python
options = ClaudeAgentOptions(
    model="claude-sonnet-4-20250514",
    system_prompt="You are helpful.",
    max_tokens=4096,
    temperature=0.7,
    tools=[my_tool.definition],
    max_turns=10,
)
```

### After

```python
options = AgentOptions(
    provider="anthropic",        # New required field
    model="claude-sonnet-4-20250514",
    system_prompt="You are helpful.",
    max_tokens=4096,
    temperature=0.7,
    tools=[my_tool.definition],
    max_turns=10,
)
```

### New Options Available

```python
options = AgentOptions(
    # Provider selection
    provider="anthropic",        # or "openai", "azure_openai", "gemini"
    provider_config={},          # Provider-specific config

    # Skills
    setting_sources=["project"], # Load skills
    allowed_tools=["Skill"],     # Enable skill invocation

    # Agents
    agents={"name": agent_def},  # Define agents

    # Hooks
    hooks={
        "PreToolUse": [HookMatcher(...)],
    },

    # Memory
    memory_enabled=True,
    memory_type="persistent",

    # Cost control
    max_budget_usd=1.0,

    # Extended thinking (Claude)
    enable_thinking=True,
    max_thinking_tokens=1024,
)
```

## Message Type Changes

### Before

```python
from claude_agent_sdk import ClaudeMessage

for msg in messages:
    if msg.role == "assistant":
        print(msg.content)
```

### After

```python
from universal_agent_sdk import AssistantMessage, TextBlock

for msg in messages:
    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(block.text)
```

## Async Pattern Changes

### Before (anyio)

```python
import anyio

async def main():
    # ... code ...

anyio.run(main)
```

### After (asyncio)

```python
import asyncio

async def main():
    # ... code ...

asyncio.run(main())
```

## Built-in Tools

### Before

```python
# Tools were accessed differently
from claude_agent_sdk.tools import ReadFileTool
```

### After

```python
from universal_agent_sdk import ReadTool, WriteTool, EditTool

read_tool = ReadTool()
options = AgentOptions(
    tools=[read_tool.to_tool_definition()],
)
```

## Hooks Migration

### Before

```python
# Hooks had different structure
```

### After

```python
from universal_agent_sdk import AgentOptions, HookMatcher

async def my_hook(input_data, tool_use_id, context):
    return {"continue_": True}

options = AgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher=None, hooks=[my_hook]),
        ],
    },
)
```

## Error Handling

### Before

```python
from claude_agent_sdk import ClaudeError

try:
    # ... code ...
except ClaudeError as e:
    print(f"Error: {e}")
```

### After

```python
from universal_agent_sdk import (
    UniversalAgentError,
    ProviderError,
    AuthenticationError,
    RateLimitError,
)

try:
    # ... code ...
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except AuthenticationError as e:
    print(f"Auth failed for {e.provider}")
except ProviderError as e:
    print(f"Provider error: {e.message}")
except UniversalAgentError as e:
    print(f"SDK error: {e}")
```

## Feature Additions

### Multi-Provider

```python
# Use OpenAI
options = AgentOptions(provider="openai", model="gpt-4o")

# Use Azure
options = AgentOptions(
    provider="azure_openai",
    provider_config={
        "endpoint": "https://...",
        "deployment_name": "...",
    },
)

# Switch mid-conversation
async with UniversalAgentClient() as client:
    # Start with Claude
    await client.send("Hello from Claude")
    async for _ in client.receive(): pass

    # Switch to OpenAI
    client.set_provider("openai")
    client.set_model("gpt-4o")
```

### Skills System

```python
from universal_agent_sdk import Skill, PDFSkill, combine_skills

# Use built-in skill
pdf_skill = PDFSkill()
options = pdf_skill.create_options()

# Combine skills
combined = combine_skills(PDFSkill(), DocxSkill())
```

### Agents System

```python
from universal_agent_sdk import AgentDefinition

code_reviewer = AgentDefinition(
    name="code_reviewer",
    description="Reviews code",
    system_prompt="You review code...",
)

options = AgentOptions(
    agents={"reviewer": code_reviewer},
)
```

### Memory

```python
from universal_agent_sdk import FileSystemMemoryTool

memory = FileSystemMemoryTool(memory_dir="./memories")
options = AgentOptions(
    tools=[memory.to_tool_definition()],
)
```

## Step-by-Step Migration

### Step 1: Update Dependencies

```bash
# Remove old SDK
pip uninstall claude-agent-sdk

# Install new SDK
pip install universal-agent-sdk
```

### Step 2: Find and Replace Imports

```python
# Find all files with claude_agent_sdk imports
grep -r "from claude_agent_sdk" --include="*.py"

# Update each file
```

### Step 3: Update Client Usage

1. Replace `ClaudeSDKClient` → `UniversalAgentClient`
2. Replace `ClaudeAgentOptions` → `AgentOptions`
3. Add `provider="anthropic"` to options

### Step 4: Update Async Patterns

1. Replace `import anyio` → `import asyncio`
2. Replace `anyio.run(main)` → `asyncio.run(main())`

### Step 5: Update Error Handling

1. Replace Claude-specific errors with universal errors
2. Add provider-aware error handling

### Step 6: Test

```bash
# Run your tests
pytest

# Test with different providers (optional)
export OPENAI_API_KEY="..."
pytest --provider=openai
```

## Compatibility Mode

If you need to maintain compatibility during migration:

```python
# compatibility.py
from universal_agent_sdk import (
    UniversalAgentClient as ClaudeSDKClient,
    AgentOptions as ClaudeAgentOptions,
    query,
    tool,
)

# Default to Claude
def create_options(**kwargs):
    return AgentOptions(provider="anthropic", **kwargs)
```

## Common Issues

### Issue: Missing provider

```python
# Error: Provider not specified
options = AgentOptions(model="claude-sonnet-4-20250514")

# Fix: Add provider
options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
)
```

### Issue: anyio not found

```python
# Error: No module named 'anyio'
anyio.run(main)

# Fix: Use asyncio
asyncio.run(main())
```

### Issue: Content access

```python
# Error: 'str' object has no attribute 'text'
print(msg.content)

# Fix: Access content blocks
for block in msg.content:
    if isinstance(block, TextBlock):
        print(block.text)
```

## Getting Help

- Documentation: See other guides in this folder
- Issues: Report at GitHub repository
- Examples: Check the `examples/` directory

## Next Steps

After migration, explore new features:
- [Multi-Provider Support](./02-configuration-providers.md)
- [Skills System](./05-skills.md)
- [Hooks System](./06-hooks.md)
- [Memory System](./08-memory.md)
