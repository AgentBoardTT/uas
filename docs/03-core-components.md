# Core Components

This guide covers the core components of the Universal Agent SDK: the client, query functions, and type system.

## UniversalAgentClient

The `UniversalAgentClient` is designed for multi-turn, interactive conversations with LLMs.

### Basic Usage

```python
import asyncio
from universal_agent_sdk import UniversalAgentClient, AssistantMessage, TextBlock

async def main():
    # Using context manager (recommended)
    async with UniversalAgentClient() as client:
        await client.send("Hello!")
        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)

asyncio.run(main())
```

### Manual Connection Management

```python
from universal_agent_sdk import UniversalAgentClient

client = UniversalAgentClient()

try:
    await client.connect()
    # ... use client
finally:
    await client.disconnect()
```

### Client Methods

#### `send(message)`

Send a message to the LLM:

```python
# Send a string
await client.send("What is Python?")

# Send a Message object
from universal_agent_sdk import UserMessage
await client.send(UserMessage(content="What is Python?"))

# Send with content blocks
from universal_agent_sdk import TextBlock, ImageBlock
await client.send(UserMessage(content=[
    TextBlock(text="Describe this image:"),
    ImageBlock(source="base64-data...", media_type="image/png"),
]))
```

#### `receive()`

Receive streaming messages:

```python
async for msg in client.receive():
    if isinstance(msg, StreamEvent):
        # Real-time delta
        print(msg.delta)
    elif isinstance(msg, AssistantMessage):
        # Complete message
        print(msg.content)
    elif isinstance(msg, ToolMessage):
        # Tool result
        print(msg.content)
    elif isinstance(msg, ResultMessage):
        # Final result with stats
        print(f"Turns: {msg.num_turns}")
```

#### `receive_all()`

Collect all messages at once (non-streaming):

```python
messages = await client.receive_all()
for msg in messages:
    print(msg)
```

#### `query(message)`

Shorthand for `send()` + `receive()`:

```python
async for msg in client.query("What is 2+2?"):
    print(msg)
```

#### `get_text_response()`

Extract text from the last assistant message:

```python
await client.send("Hello")
async for _ in client.receive():
    pass

text = client.get_text_response()
print(text)  # The assistant's response as a string
```

#### `clear_history()`

Clear conversation history (keeps system prompt):

```python
client.clear_history()
print(len(client.messages))  # Only system message remains
```

#### `set_provider()` / `set_model()`

Switch provider or model mid-conversation:

```python
# Switch provider
client.set_provider("openai", {"api_key": "sk-..."})

# Change model
client.set_model("gpt-4o")
```

### Client Properties

```python
# Unique session ID
print(client.session_id)  # "abc123..."

# Connection status
print(client.is_connected)  # True/False

# Conversation history (read-only copy)
for msg in client.messages:
    print(msg)
```

## Query Functions

For simpler, one-shot queries without multi-turn context.

### `query()`

Async iterator that yields messages:

```python
from universal_agent_sdk import query, AgentOptions

options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
)

async for msg in query("What is Python?", options):
    print(msg)
```

### `complete()`

Returns only the final `AssistantMessage`:

```python
from universal_agent_sdk import complete, AgentOptions

options = AgentOptions(provider="anthropic")
response = await complete("What is 2+2?", options)
print(response.content[0].text)  # "4"
```

### Query with Tools

When tools are configured, `query()` automatically handles the tool execution loop:

```python
from universal_agent_sdk import query, tool, AgentOptions

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

options = AgentOptions(
    tools=[add.definition],
    max_turns=5,  # Limit tool execution rounds
)

async for msg in query("What is 15 + 27?", options):
    print(msg)
```

## Message Types

### UserMessage

```python
from universal_agent_sdk import UserMessage, TextBlock

# Simple string content
msg = UserMessage(content="Hello")

# Content blocks
msg = UserMessage(content=[
    TextBlock(text="Hello"),
])

# With name
msg = UserMessage(content="Hello", name="Alice")
```

### AssistantMessage

```python
from universal_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock

# Access content
for block in message.content:
    if isinstance(block, TextBlock):
        print(block.text)
    elif isinstance(block, ToolUseBlock):
        print(f"Tool: {block.name}")
        print(f"Input: {block.input}")

# Check finish reason
from universal_agent_sdk import FinishReason
if message.finish_reason == FinishReason.STOP:
    print("Normal completion")
elif message.finish_reason == FinishReason.TOOL_USE:
    print("Wants to use a tool")
```

### SystemMessage

```python
from universal_agent_sdk import SystemMessage

msg = SystemMessage(content="You are a helpful assistant.")
```

### ToolMessage

```python
from universal_agent_sdk import ToolMessage

msg = ToolMessage(
    content="Result: 42",
    tool_call_id="tool_123",
)
```

### ResultMessage

Final message with execution statistics:

```python
from universal_agent_sdk import ResultMessage

# Properties
msg.num_turns        # Number of turns taken
msg.is_error         # Whether an error occurred
msg.stop_reason      # Why execution stopped
msg.usage            # Token usage statistics
msg.total_cost_usd   # Estimated cost
```

### StreamEvent

Real-time streaming updates:

```python
from universal_agent_sdk import StreamEvent

if isinstance(msg, StreamEvent):
    if msg.delta and msg.delta.get("type") == "text_delta":
        text = msg.delta.get("text", "")
        print(text, end="", flush=True)
```

## Content Blocks

### TextBlock

```python
from universal_agent_sdk import TextBlock

block = TextBlock(text="Hello, world!")
print(block.text)
```

### ImageBlock

```python
from universal_agent_sdk import ImageBlock

# Base64 encoded image
block = ImageBlock(
    source="base64-encoded-data...",
    media_type="image/png",
)

# URL (some providers support)
block = ImageBlock(
    source="https://example.com/image.png",
    media_type="image/png",
)
```

### ThinkingBlock (Claude)

Extended thinking output:

```python
from universal_agent_sdk import ThinkingBlock

# Access thinking content
if isinstance(block, ThinkingBlock):
    print(f"Thinking: {block.thinking}")
    print(f"Signature: {block.signature}")
```

### ToolUseBlock

Tool invocation request:

```python
from universal_agent_sdk import ToolUseBlock

if isinstance(block, ToolUseBlock):
    print(f"Tool ID: {block.id}")
    print(f"Tool Name: {block.name}")
    print(f"Input: {block.input}")
```

### ToolResultBlock

Tool execution result:

```python
from universal_agent_sdk import ToolResultBlock

block = ToolResultBlock(
    tool_use_id="tool_123",
    content="Result: 42",
    is_error=False,
)
```

## Usage Statistics

```python
from universal_agent_sdk import Usage

# Access usage from ResultMessage
if isinstance(msg, ResultMessage) and msg.usage:
    usage = msg.usage
    print(f"Input tokens: {usage.input_tokens}")
    print(f"Output tokens: {usage.output_tokens}")
    print(f"Total tokens: {usage.total_tokens}")
    print(f"Cache read: {usage.cache_read_input_tokens}")
    print(f"Cache creation: {usage.cache_creation_input_tokens}")
```

## Finish Reasons

```python
from universal_agent_sdk import FinishReason

# Possible values
FinishReason.STOP           # Normal completion
FinishReason.LENGTH         # Max tokens reached
FinishReason.TOOL_USE       # Tool invocation requested
FinishReason.CONTENT_FILTER # Content filtered
FinishReason.ERROR          # Error occurred
```

## Working with Conversation History

```python
async with UniversalAgentClient() as client:
    # Build conversation
    await client.send("My favorite color is blue.")
    async for _ in client.receive():
        pass

    await client.send("What's my favorite color?")
    async for msg in client.receive():
        print(msg)

    # Access history
    print(f"Messages: {len(client.messages)}")
    for i, msg in enumerate(client.messages):
        print(f"{i}: {type(msg).__name__}")

    # Clear and start fresh
    client.clear_history()
```

## Error Types

```python
from universal_agent_sdk import (
    UniversalAgentError,    # Base exception
    ProviderError,          # Provider-level error
    AuthenticationError,    # Auth failure
    RateLimitError,         # Rate limited (429)
    ModelNotFoundError,     # Model unavailable
    ContextLengthError,     # Context exceeded
    ConnectionError,        # Connection failed
    TimeoutError,           # Timeout
    ToolError,              # Tool execution error
    ToolNotFoundError,      # Tool not registered
    ConfigurationError,     # Invalid config
)

try:
    async for msg in query("Hello"):
        pass
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except AuthenticationError as e:
    print(f"Auth failed for {e.provider}")
except ProviderError as e:
    print(f"Error from {e.provider}: {e.message}")
```

## Next Steps

- [Tools System](./04-tools.md) - Create custom tools
- [Skills System](./05-skills.md) - Reusable agent capabilities
- [Hooks System](./06-hooks.md) - Intercept agent behavior
