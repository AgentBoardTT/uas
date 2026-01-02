# API Reference

Complete reference for all public classes, functions, and types in the Universal Agent SDK.

## Core Functions

### query()

```python
async def query(
    prompt: str | list[Message],
    options: AgentOptions | None = None,
    **kwargs,
) -> AsyncIterator[AnyMessage]
```

Execute a one-shot query with optional tool execution.

**Parameters:**
- `prompt`: Query text or list of messages
- `options`: Configuration options
- `**kwargs`: Additional options passed to AgentOptions

**Yields:**
- `AssistantMessage`: Model responses
- `StreamEvent`: Streaming deltas (if streaming enabled)
- `ToolMessage`: Tool execution results
- `ResultMessage`: Final execution statistics

**Example:**
```python
async for msg in query("What is 2+2?"):
    print(msg)
```

### complete()

```python
async def complete(
    prompt: str | list[Message],
    options: AgentOptions | None = None,
    **kwargs,
) -> AssistantMessage
```

Execute a query and return only the final response.

**Parameters:**
- `prompt`: Query text or list of messages
- `options`: Configuration options

**Returns:**
- `AssistantMessage`: The model's response

**Example:**
```python
response = await complete("What is Python?")
print(response.content[0].text)
```

## UniversalAgentClient

```python
class UniversalAgentClient:
    def __init__(self, options: AgentOptions | None = None)
```

Multi-turn conversation client with streaming support.

### Methods

#### connect()
```python
async def connect() -> None
```
Connect to the LLM provider.

#### disconnect()
```python
async def disconnect() -> None
```
Disconnect from the provider.

#### send()
```python
async def send(message: str | Message) -> None
```
Send a message to the LLM.

#### receive()
```python
async def receive() -> AsyncIterator[AnyMessage]
```
Receive streaming responses.

#### receive_all()
```python
async def receive_all() -> list[AnyMessage]
```
Collect all responses at once.

#### query()
```python
async def query(message: str | Message) -> AsyncIterator[AnyMessage]
```
Combined send and receive.

#### get_text_response()
```python
def get_text_response() -> str
```
Extract text from last assistant message.

#### clear_history()
```python
def clear_history() -> None
```
Clear conversation history.

#### set_provider()
```python
def set_provider(provider: str, config: dict | None = None) -> None
```
Switch LLM provider.

#### set_model()
```python
def set_model(model: str) -> None
```
Change model.

### Properties

- `session_id: str` - Unique session identifier
- `messages: list[Message]` - Conversation history (read-only)
- `is_connected: bool` - Connection status

### Context Manager

```python
async with UniversalAgentClient(options) as client:
    await client.send("Hello")
    async for msg in client.receive():
        print(msg)
```

## AgentOptions

```python
@dataclass
class AgentOptions:
    # Provider
    provider: str = "claude"
    provider_config: dict | None = None
    model: str | None = None
    fallback_model: str | None = None

    # Generation
    system_prompt: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None

    # Tools
    tools: list[ToolDefinition] = field(default_factory=list)
    tool_choice: Literal["auto", "required", "none"] | str | None = None
    can_use_tool: CanUseTool | None = None

    # Skills
    setting_sources: list[SettingSource] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)

    # Agents
    agents: dict[str, AgentDefinition] = field(default_factory=dict)
    max_turns: int | None = None

    # Memory
    memory_enabled: bool = False
    memory_type: Literal["conversation", "vector", "persistent"] = "conversation"
    memory_config: dict = field(default_factory=dict)

    # Session
    session_id: str | None = None
    continue_conversation: bool = False

    # Hooks
    hooks: dict[HookEvent, list[HookMatcher]] | None = None

    # Streaming
    stream: bool = True
    include_usage: bool = True

    # Cost
    max_budget_usd: float | None = None

    # Extended
    enable_thinking: bool = False
    max_thinking_tokens: int | None = None

    # Environment
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)

    # Debug
    debug: bool = False
    stderr_callback: Callable[[str], None] | None = None
```

## Message Types

### UserMessage

```python
@dataclass
class UserMessage:
    content: str | list[ContentBlock]
    name: str | None = None
```

### AssistantMessage

```python
@dataclass
class AssistantMessage:
    content: list[ContentBlock]
    model: str | None = None
    finish_reason: FinishReason | None = None
```

### SystemMessage

```python
@dataclass
class SystemMessage:
    content: str
```

### ToolMessage

```python
@dataclass
class ToolMessage:
    content: str
    tool_call_id: str
```

### ResultMessage

```python
@dataclass
class ResultMessage:
    num_turns: int
    is_error: bool = False
    stop_reason: str | None = None
    usage: Usage | None = None
    total_cost_usd: float | None = None
```

### StreamEvent

```python
@dataclass
class StreamEvent:
    type: str
    delta: dict | None = None
    index: int | None = None
```

## Content Blocks

### TextBlock

```python
@dataclass
class TextBlock:
    text: str
```

### ImageBlock

```python
@dataclass
class ImageBlock:
    source: str  # Base64 or URL
    media_type: str  # e.g., "image/png"
```

### ThinkingBlock

```python
@dataclass
class ThinkingBlock:
    thinking: str
    signature: str | None = None
```

### ToolUseBlock

```python
@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict
```

### ToolResultBlock

```python
@dataclass
class ToolResultBlock:
    tool_use_id: str
    content: str | list
    is_error: bool = False
```

## Tool Types

### ToolDefinition

```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: ToolSchema | dict
    handler: Callable | None = None
```

### Tool Class

```python
class Tool:
    name: str
    description: str
    input_schema: ToolSchema | dict
    handler: Callable | None

    @property
    def definition(self) -> ToolDefinition

    async def __call__(self, **kwargs) -> Any
```

### @tool Decorator

```python
def tool(
    func: Callable | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    input_schema: dict | None = None,
) -> Tool | Callable[[Callable], Tool]
```

**Example:**
```python
@tool
def my_tool(arg: str) -> str:
    """Description from docstring."""
    return arg

@tool(name="custom_name", description="Custom description")
def another_tool(arg: str) -> str:
    return arg
```

### ToolRegistry

```python
class ToolRegistry:
    def register(self, tool: Tool) -> None
    def unregister(self, name: str) -> None
    def get(self, name: str) -> Tool
    def has(self, name: str) -> bool
    def list(self) -> list[str]
    def get_all(self) -> list[Tool]
    def get_definitions(self) -> list[ToolDefinition]
    def clear(self) -> None

    # Class methods
    @classmethod
    def register_global(cls, tool: Tool) -> None
    @classmethod
    def get_global(cls, name: str) -> Tool
    @classmethod
    def list_global(cls) -> list[str]
```

## Built-in Tools

### ReadTool

```python
class ReadTool:
    name = "read_file"

    def to_tool_definition(self) -> ToolDefinition
    async def __call__(
        self,
        file_path: str,
        offset: int | None = None,
        limit: int | None = None,
    ) -> str
```

### WriteTool

```python
class WriteTool:
    name = "write_file"

    def to_tool_definition(self) -> ToolDefinition
    async def __call__(
        self,
        file_path: str,
        file_text: str,
    ) -> str
```

### EditTool

```python
class EditTool:
    name = "edit_file"

    def to_tool_definition(self) -> ToolDefinition
    async def __call__(
        self,
        file_path: str,
        old_str: str,
        new_str: str,
    ) -> str
```

### BashTool

```python
class BashTool:
    name = "bash"

    def to_tool_definition(self) -> ToolDefinition
    async def __call__(
        self,
        command: str,
        timeout: int = 120,
        description: str | None = None,
    ) -> str
```

### GlobTool

```python
class GlobTool:
    name = "glob"

    def to_tool_definition(self) -> ToolDefinition
    async def __call__(
        self,
        pattern: str,
        path: str | None = None,
    ) -> list[str]
```

### GrepTool

```python
class GrepTool:
    name = "grep"

    def to_tool_definition(self) -> ToolDefinition
    async def __call__(
        self,
        pattern: str,
        path: str | None = None,
        file_glob: str | None = None,
        output_mode: str = "content",
    ) -> str
```

## Permission Types

### PermissionResultAllow

```python
@dataclass
class PermissionResultAllow:
    behavior: str = "allow"
    updated_input: dict | None = None
```

### PermissionResultDeny

```python
@dataclass
class PermissionResultDeny:
    behavior: str = "deny"
    message: str | None = None
    interrupt: bool = False
```

### ToolPermissionContext

```python
@dataclass
class ToolPermissionContext:
    session_id: str
    signal: Any | None = None
```

### CanUseTool (Type Alias)

```python
CanUseTool = Callable[
    [str, dict, ToolPermissionContext],
    Awaitable[PermissionResultAllow | PermissionResultDeny],
]
```

## Hook Types

### HookEvent (Enum)

```python
class HookEvent(str, Enum):
    SessionStart = "SessionStart"
    PreToolUse = "PreToolUse"
    PostToolUse = "PostToolUse"
    PreCompletion = "PreCompletion"
    PostCompletion = "PostCompletion"
    OnError = "OnError"
```

### HookMatcher

```python
@dataclass
class HookMatcher:
    matcher: str | None  # Tool name or None for all
    hooks: list[HookCallback]
    timeout: float | None = None
```

### HookContext

```python
@dataclass
class HookContext:
    session_id: str
    tool_use_id: str | None = None
```

### HookCallback (Type Alias)

```python
HookCallback = Callable[
    [HookInput, str | None, HookContext],
    Awaitable[HookOutput],
]
```

### HookOutput (TypedDict)

```python
class HookOutput(TypedDict, total=False):
    continue_: bool
    stopReason: str
    reason: str
    systemMessage: str
    modified_input: dict
    hookSpecificOutput: dict
```

## Agent Types

### AgentDefinition

```python
@dataclass
class AgentDefinition:
    name: str
    description: str = ""
    system_prompt: str = ""
    tools: list[str | ToolDefinition] = field(default_factory=list)
    model: str | None = None
    provider: str = "anthropic"
    max_turns: int = 10
```

### Agent Class

```python
class Agent:
    name: str
    description: str
    system_prompt: str | None
    tools: list[Any]
    model: str | None
    provider: str
    max_turns: int

    @property
    def definition(self) -> AgentDefinition
```

### SubAgent Class

```python
class SubAgent(Agent):
    parent: Agent | None
    inherit_tools: bool
    inherit_context: bool
```

### AgentRegistry

```python
class AgentRegistry:
    def register(self, agent: Agent) -> None
    def unregister(self, name: str) -> None
    def get(self, name: str) -> Agent
    def has(self, name: str) -> bool
    def list(self) -> list[str]
    def get_all(self) -> list[Agent]
    def get_definitions(self) -> dict[str, AgentDefinition]
    def clear(self) -> None
    def load_from_file(self, path: str | Path) -> None
    def load_from_directory(self, directory: str | Path) -> None
```

## Skill Types

### Skill

```python
@dataclass
class Skill:
    name: str
    description: str
    system_prompt: str
    tools: list[ToolDefinition] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 4096
    metadata: dict = field(default_factory=dict)

    def create_options(self, **kwargs) -> AgentOptions
    def with_tools(self, *tools) -> Skill
    def with_prompt(self, additional_prompt: str) -> Skill

    @classmethod
    def from_file(cls, path: str | Path) -> Skill
```

### SkillRegistry

```python
class SkillRegistry:
    @staticmethod
    def register(skill: Skill) -> None
    @staticmethod
    def get(name: str) -> Skill
    @staticmethod
    def list() -> list[str]
    @staticmethod
    def all() -> dict[str, Skill]
    @staticmethod
    def clear() -> None
```

### Skill Functions

```python
def discover_skills(
    setting_sources: list[str],
    project_dir: str | Path | None = None,
) -> list[Skill]

def list_skills(
    setting_sources: list[str] | None = None,
    project_dir: str | Path | None = None,
) -> list[Skill]

def combine_skills(
    *skills: Skill,
    name: str | None = None,
) -> Skill
```

## Memory Types

### MemoryEntry

```python
@dataclass
class MemoryEntry:
    id: str
    content: str
    metadata: dict | None = None
    embedding: list[float] | None = None
    timestamp: str | None = None
```

### MemorySearchResult

```python
@dataclass
class MemorySearchResult:
    entry: MemoryEntry
    score: float
```

### BaseMemory (Abstract)

```python
class BaseMemory(ABC):
    @abstractmethod
    async def add(
        self,
        content: str,
        metadata: dict | None = None,
    ) -> str

    @abstractmethod
    async def get(self, entry_id: str) -> MemoryEntry | None

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        **kwargs,
    ) -> list[MemorySearchResult]

    @abstractmethod
    async def delete(self, entry_id: str) -> bool

    @abstractmethod
    async def clear(self) -> None
```

### FileSystemMemoryTool

```python
class FileSystemMemoryTool:
    def __init__(
        self,
        memory_dir: str = "./memories",
        max_depth: int = 2,
        max_line_limit: int = 999999,
    )

    def to_tool_definition(self) -> ToolDefinition

    async def view(self, command: MemoryViewCommand) -> str
    async def create(self, command: MemoryCreateCommand) -> str
    async def str_replace(self, command: MemoryStrReplaceCommand) -> str
    async def insert(self, command: MemoryInsertCommand) -> str
    async def delete(self, command: MemoryDeleteCommand) -> str
    async def rename(self, command: MemoryRenameCommand) -> str
```

## Configuration

### Config Class

```python
class Config:
    def __init__(self, secret_fetcher: Callable | None = None)

    def get_api_key(self, provider: str) -> str | None
    def get_provider_config(self, provider: str) -> dict[str, Any]
    def set(self, provider: str, key: str, value: str) -> Config
    def set_api_key(self, provider: str, api_key: str) -> Config
    def validate(self, provider: str) -> list[str]
    def is_configured(self, provider: str) -> bool
    def list_configured_providers(self) -> list[str]

    @classmethod
    def from_dict(cls, config_dict: dict) -> Config
```

### Config Functions

```python
def get_config() -> Config
def get_api_key(provider: str) -> str | None
def get_provider_config(provider: str) -> dict[str, Any]
```

### Secret Fetchers

```python
def aws_secret_fetcher(secret_name: str) -> str | None
def gcp_secret_fetcher(secret_name: str, project_id: str) -> str | None
def azure_keyvault_fetcher(vault_url: str) -> Callable[[str], str | None]
```

## Provider Types

### ProviderFeatures

```python
@dataclass
class ProviderFeatures:
    streaming: bool = True
    tool_calling: bool = True
    vision: bool = False
    thinking: bool = False
    json_mode: bool = False
    max_context_length: int = 128000
    supports_system_message: bool = True
```

### BaseProvider (Abstract)

```python
class BaseProvider(ABC):
    @abstractmethod
    def get_features(self) -> ProviderFeatures

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        options: AgentOptions,
    ) -> AssistantMessage

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        options: AgentOptions,
    ) -> AsyncIterator[AnyMessage]
```

### ProviderRegistry

```python
class ProviderRegistry:
    @staticmethod
    def register(name: str, provider_class: type[BaseProvider]) -> None

    @staticmethod
    def get(name: str, config: dict | None = None) -> BaseProvider

    @staticmethod
    def list_providers() -> list[str]

    @staticmethod
    def is_registered(name: str) -> bool
```

## Exceptions

### Base

```python
class UniversalAgentError(Exception): pass
```

### Provider Errors

```python
class ProviderError(UniversalAgentError):
    message: str
    provider: str
    status_code: int | None
    response: dict | None

class ProviderNotFoundError(ProviderError): pass
class AuthenticationError(ProviderError): pass
class RateLimitError(ProviderError):
    retry_after: float | None
class ModelNotFoundError(ProviderError): pass
class ContextLengthError(ProviderError):
    max_tokens: int
    used_tokens: int
class ConnectionError(ProviderError): pass
class TimeoutError(ProviderError):
    timeout: float
```

### Tool Errors

```python
class ToolError(UniversalAgentError):
    tool_name: str | None

class ToolNotFoundError(ToolError): pass
class ToolValidationError(ToolError): pass
```

### Other Errors

```python
class AgentError(UniversalAgentError): pass
class MemoryError(UniversalAgentError): pass
class ConfigurationError(UniversalAgentError): pass
class MessageParseError(UniversalAgentError): pass
```

## Enums

### Role

```python
class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
```

### FinishReason

```python
class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_USE = "tool_use"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
```

### ContentType

```python
class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    THINKING = "thinking"
```

## Usage Statistics

```python
@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
```
