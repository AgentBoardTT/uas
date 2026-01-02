# Tools System

Tools extend your agent's capabilities by allowing it to execute functions, access files, run commands, and more. The Universal Agent SDK provides a powerful tool system with a simple decorator-based API and several built-in tools.

## Creating Tools with @tool Decorator

### Basic Tool

```python
from universal_agent_sdk import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The city name to get weather for
    """
    # Your implementation
    return f"Weather in {city}: Sunny, 72F"

# Access the tool definition
print(get_weather.definition)  # ToolDefinition object

# Call the tool directly
result = get_weather(city="Paris")
print(result)  # "Weather in Paris: Sunny, 72F"
```

### Async Tools

```python
@tool
async def fetch_data(url: str) -> str:
    """Fetch data from a URL."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

### Tools with Multiple Parameters

```python
@tool
def calculate(
    expression: str,
    precision: int = 2,
) -> str:
    """Calculate a mathematical expression.

    Args:
        expression: The math expression to evaluate
        precision: Decimal precision for the result
    """
    result = eval(expression)  # Use with caution
    return f"{result:.{precision}f}"
```

### Custom Tool Name and Description

```python
@tool(
    name="weather_lookup",
    description="Look up weather conditions for any city worldwide"
)
def get_weather(city: str) -> str:
    """Original docstring (ignored when description is provided)."""
    return f"Weather: Sunny in {city}"
```

### Explicit Input Schema

```python
@tool(input_schema={
    "type": "object",
    "properties": {
        "city": {
            "type": "string",
            "description": "City name"
        },
        "units": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"],
            "default": "celsius"
        }
    },
    "required": ["city"]
})
def get_weather(city: str, units: str = "celsius") -> str:
    """Get weather with units."""
    return f"Weather in {city}: 22{units[0].upper()}"
```

## Type Inference

The `@tool` decorator automatically infers JSON Schema from Python type hints:

| Python Type | JSON Schema Type |
|-------------|------------------|
| `str` | `"string"` |
| `int` | `"integer"` |
| `float` | `"number"` |
| `bool` | `"boolean"` |
| `list` | `"array"` |
| `dict` | `"object"` |
| `Optional[T]` | Type T, not required |
| `T | None` | Type T, not required |

```python
from typing import Optional

@tool
def process_data(
    text: str,                    # required string
    count: int,                   # required integer
    threshold: float = 0.5,       # optional number with default
    enabled: bool = True,         # optional boolean
    tags: list = None,            # optional array
    metadata: Optional[dict] = None,  # optional object
) -> str:
    """Process data with various types."""
    return "processed"
```

## Using Tools with Queries

```python
from universal_agent_sdk import query, AgentOptions

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    tools=[add.definition, multiply.definition],
    max_turns=5,  # Limit tool execution loops
)

async for msg in query("What is 15 + 27, then multiply the result by 3?", options):
    print(msg)
```

## Tool Choice

Control when tools are used:

```python
# Let the model decide (default)
options = AgentOptions(
    tools=[my_tool.definition],
    tool_choice="auto",
)

# Force tool use
options = AgentOptions(
    tools=[my_tool.definition],
    tool_choice="required",
)

# Disable tool use
options = AgentOptions(
    tools=[my_tool.definition],
    tool_choice="none",
)

# Force specific tool
options = AgentOptions(
    tools=[tool1.definition, tool2.definition],
    tool_choice="tool1",  # Must use tool1
)
```

## Tool Registry

Manage collections of tools:

```python
from universal_agent_sdk import ToolRegistry, tool

registry = ToolRegistry()

@tool
def tool1(x: str) -> str:
    """Tool 1."""
    return x

@tool
def tool2(y: int) -> int:
    """Tool 2."""
    return y

# Register tools
registry.register(tool1)
registry.register(tool2)

# Check and retrieve
print(registry.has("tool1"))  # True
print(registry.list())  # ["tool1", "tool2"]

t = registry.get("tool1")
print(t.name)  # "tool1"

# Get all definitions for AgentOptions
definitions = registry.get_definitions()
options = AgentOptions(tools=definitions)

# Unregister
registry.unregister("tool1")

# Clear all
registry.clear()
```

### Global Registry

```python
from universal_agent_sdk import ToolRegistry

# Register globally
ToolRegistry.register_global(my_tool)

# Access globally
tool = ToolRegistry.get_global("my_tool")
all_tools = ToolRegistry.list_global()
```

## Built-in Tools

### ReadTool

Read files with line numbers:

```python
from universal_agent_sdk import ReadTool, AgentOptions

read_tool = ReadTool()

options = AgentOptions(
    tools=[read_tool.to_tool_definition()],
)

# Tool parameters:
# - file_path: str (required) - Path to read
# - offset: int (optional) - Start line
# - limit: int (optional) - Number of lines
```

### WriteTool

Create or overwrite files:

```python
from universal_agent_sdk import WriteTool

write_tool = WriteTool()

# Tool parameters:
# - file_path: str (required) - Path to write
# - file_text: str (required) - Content to write
```

### EditTool

Edit files using string replacement:

```python
from universal_agent_sdk import EditTool

edit_tool = EditTool()

# Tool parameters:
# - file_path: str (required) - File to edit
# - old_str: str (required) - Text to find (must be unique)
# - new_str: str (required) - Replacement text
```

### BashTool

Execute shell commands:

```python
from universal_agent_sdk import BashTool

bash_tool = BashTool()

# Tool parameters:
# - command: str (required) - Command to execute
# - timeout: int (optional) - Timeout in seconds (default: 120, max: 600)
# - description: str (optional) - What the command does
```

### GlobTool

Find files by pattern:

```python
from universal_agent_sdk import GlobTool

glob_tool = GlobTool()

# Tool parameters:
# - pattern: str (required) - Glob pattern (e.g., "**/*.py")
# - path: str (optional) - Base directory
```

### GrepTool

Search file contents:

```python
from universal_agent_sdk import GrepTool

grep_tool = GrepTool()

# Tool parameters:
# - pattern: str (required) - Regex pattern
# - path: str (optional) - Directory to search
# - file_glob: str (optional) - File pattern filter
# - output_mode: str (optional) - "content", "files_with_matches", "count"
```

### NotebookEditTool

Edit Jupyter notebooks:

```python
from universal_agent_sdk import NotebookEditTool

notebook_tool = NotebookEditTool()

# Operations: create, replace, delete cells
```

### Using Multiple Built-in Tools

```python
from universal_agent_sdk import (
    ReadTool, WriteTool, EditTool,
    BashTool, GlobTool, GrepTool,
    AgentOptions,
)

options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    tools=[
        ReadTool().to_tool_definition(),
        WriteTool().to_tool_definition(),
        EditTool().to_tool_definition(),
        BashTool().to_tool_definition(),
        GlobTool().to_tool_definition(),
        GrepTool().to_tool_definition(),
    ],
)
```

## Tool Permission Callbacks

Control and modify tool execution with `can_use_tool`:

```python
from universal_agent_sdk import (
    AgentOptions,
    PermissionResultAllow,
    PermissionResultDeny,
)
from universal_agent_sdk.types import ToolPermissionContext

async def permission_callback(
    tool_name: str,
    input_data: dict,
    context: ToolPermissionContext,
) -> PermissionResultAllow | PermissionResultDeny:
    """Control tool permissions."""

    # Log all tool calls
    print(f"Tool: {tool_name}, Input: {input_data}")

    # Block dangerous commands
    if tool_name == "bash":
        command = input_data.get("command", "")
        if "rm -rf" in command or "sudo" in command:
            return PermissionResultDeny(
                message="Dangerous command blocked"
            )

    # Block writes to system directories
    if tool_name == "write_file":
        path = input_data.get("path", "")
        if path.startswith("/etc/") or path.startswith("/usr/"):
            return PermissionResultDeny(
                message=f"Cannot write to system directory: {path}"
            )

    # Modify inputs (redirect to safe location)
    if tool_name == "write_file":
        path = input_data.get("path", "")
        if not path.startswith("./"):
            modified = input_data.copy()
            modified["path"] = f"./safe_output/{path.split('/')[-1]}"
            return PermissionResultAllow(updated_input=modified)

    # Allow by default
    return PermissionResultAllow()

options = AgentOptions(
    tools=[...],
    can_use_tool=permission_callback,
)
```

### Permission Result Types

```python
from universal_agent_sdk import PermissionResultAllow, PermissionResultDeny

# Allow with optional input modification
allow = PermissionResultAllow()
allow_modified = PermissionResultAllow(updated_input={"key": "new_value"})

# Deny with message
deny = PermissionResultDeny(message="Not allowed")
deny_interrupt = PermissionResultDeny(
    message="Blocked",
    interrupt=True,  # Stop execution entirely
)
```

## Creating Custom Tool Classes

For more complex tools:

```python
from universal_agent_sdk import Tool, ToolDefinition

class DatabaseTool(Tool):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        super().__init__(
            name="query_database",
            description="Execute SQL queries on the database",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 100,
                        "description": "Max rows to return"
                    }
                },
                "required": ["query"]
            },
            handler=self._execute,
        )

    async def _execute(self, query: str, limit: int = 100) -> str:
        # Connect and execute query
        # Return results as string
        return f"Query results for: {query}"

# Use the custom tool
db_tool = DatabaseTool("postgresql://...")
options = AgentOptions(tools=[db_tool.definition])
```

## Tool Execution Flow

When the agent uses a tool:

1. Agent sends `AssistantMessage` with `ToolUseBlock`
2. SDK checks `can_use_tool` callback (if configured)
3. If allowed, SDK executes the tool handler
4. SDK sends `ToolMessage` with result back to agent
5. Agent processes result and may use more tools
6. Loop continues until agent stops or `max_turns` reached

```python
from universal_agent_sdk import (
    query, AgentOptions, AssistantMessage,
    ToolUseBlock, ToolMessage, ResultMessage,
)

async for msg in query("Use the calculator", options):
    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, ToolUseBlock):
                print(f"Agent wants to use: {block.name}")
                print(f"With input: {block.input}")
    elif isinstance(msg, ToolMessage):
        print(f"Tool result: {msg.content}")
    elif isinstance(msg, ResultMessage):
        print(f"Completed in {msg.num_turns} turns")
```

## Best Practices

### 1. Clear Descriptions

```python
@tool
def search_users(
    query: str,
    limit: int = 10,
) -> str:
    """Search for users in the database.

    Returns a JSON array of user objects matching the query.
    Each user has: id, name, email, created_at.

    Args:
        query: Search term (matches name or email)
        limit: Maximum results to return (1-100)
    """
    pass
```

### 2. Validate Inputs

```python
@tool
def process_file(path: str) -> str:
    """Process a file."""
    import os

    # Validate path
    if not os.path.exists(path):
        return f"Error: File not found: {path}"

    if not path.endswith(('.txt', '.json', '.csv')):
        return "Error: Unsupported file type"

    # Process...
```

### 3. Handle Errors Gracefully

```python
@tool
def api_call(endpoint: str) -> str:
    """Call an API endpoint."""
    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        return "Error: Request timed out"
    except requests.HTTPError as e:
        return f"Error: HTTP {e.response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### 4. Limit Tool Turns

```python
options = AgentOptions(
    tools=[...],
    max_turns=5,  # Prevent infinite loops
)
```

## Next Steps

- [Skills System](./05-skills.md) - Reusable tool+prompt combinations
- [Hooks System](./06-hooks.md) - Pre/post tool execution hooks
- [Memory System](./08-memory.md) - Persistent tool for memory
