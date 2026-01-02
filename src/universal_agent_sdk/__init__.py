"""Universal Agent SDK - Multi-provider LLM Agent Framework.

A provider-agnostic SDK for building LLM-powered agents that works with
Claude, OpenAI, Azure OpenAI, Gemini, and other providers.

Example:
    Basic query:
    ```python
    from universal_agent_sdk import query, AgentOptions

    async for msg in query("What is the capital of France?"):
        print(msg)
    ```

    With provider selection:
    ```python
    options = AgentOptions(provider="openai", model="gpt-4o")
    async for msg in query("Hello", options):
        print(msg)
    ```

    Multi-turn conversation:
    ```python
    from universal_agent_sdk import UniversalAgentClient

    async with UniversalAgentClient() as client:
        await client.send("Hello")
        async for msg in client.receive():
            print(msg)
    ```

    With tools:
    ```python
    from universal_agent_sdk import tool, query, AgentOptions

    @tool
    def get_weather(city: str) -> str:
        \"\"\"Get the weather for a city.\"\"\"
        return f"Weather in {city}: Sunny, 72F"

    options = AgentOptions(tools=[get_weather.definition])
    async for msg in query("What's the weather in Paris?", options):
        print(msg)
    ```
"""

__version__ = "0.1.0"

# Core query and client
# Agents
from .agents import Agent, AgentRegistry, SubAgent
from .client import UniversalAgentClient

# Configuration
from .config import (
    Config,
    aws_secret_fetcher,
    azure_keyvault_fetcher,
    gcp_secret_fetcher,
    get_api_key,
    get_config,
    get_provider_config,
)

# Errors
from .errors import (
    AgentError,
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    ContextLengthError,
    MessageParseError,
    ModelNotFoundError,
    ProviderError,
    ProviderNotFoundError,
    RateLimitError,
    TimeoutError,
    ToolError,
    ToolNotFoundError,
    ToolValidationError,
    UniversalAgentError,
)

# Memory
from .memory import BaseMemory, ConversationMemory, PersistentMemory

# Preset loading
from .preset import (
    PresetLoadError,
    create_client_from_preset,
    discover_presets,
    get_builtin_tool,
    get_builtin_tools,
    get_preset,
    load_preset,
    load_preset_from_string,
    parse_preset_data,
    preset_to_options_with_tools,
)

# Providers
from .providers import (
    AzureOpenAIProvider,
    BaseProvider,
    ClaudeProvider,
    OpenAIProvider,
    ProviderRegistry,
    register_provider,
)
from .query import complete, query

# Skills (also available as universal_agent_sdk.skills)
from .skills import (
    Skill,
    SkillMetadata,
    SkillRegistry,
    combine_skills,
    discover_skills,
    get_skill,
    list_skills,
    load_skill_from_path,
    load_skills_to_registry,
)

# Tools
from .tools import (
    BaseMemoryTool,
    BashTool,
    DateTimeTool,
    EditTool,
    FileSystemMemoryTool,
    GlobTool,
    GrepTool,
    NotebookEditTool,
    ReadTool,
    Tool,
    ToolRegistry,
    WebFetchTool,
    WebSearchTool,
    WriteTool,
    get_memory_system_prompt,
    tool,
)

# Types
from .types import (
    AgentDefinition,
    AgentOptions,
    AgentPreset,
    AnyMessage,
    AssistantMessage,
    ContentBlock,
    FinishReason,
    HookCallback,
    HookContext,
    HookEvent,
    HookInput,
    HookMatcher,
    HookOutput,
    HookSpecificOutput,
    ImageBlock,
    MCPServerConfig,
    MemoryEntry,
    MemorySearchResult,
    Message,
    PermissionMode,
    PermissionResult,
    PermissionResultAllow,
    PermissionResultDeny,
    ProviderConfig,
    ProviderFeatures,
    ResourceLimits,
    ResultMessage,
    Role,
    SettingSource,
    StreamEvent,
    SystemMessage,
    SystemPromptPreset,
    TextBlock,
    ThinkingBlock,
    ToolDefinition,
    ToolMessage,
    ToolResultBlock,
    ToolUseBlock,
    Usage,
    UserMessage,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "query",
    "complete",
    "UniversalAgentClient",
    # Configuration
    "Config",
    "get_config",
    "get_api_key",
    "get_provider_config",
    "aws_secret_fetcher",
    "gcp_secret_fetcher",
    "azure_keyvault_fetcher",
    # Preset Loading
    "load_preset",
    "load_preset_from_string",
    "parse_preset_data",
    "discover_presets",
    "get_preset",
    "create_client_from_preset",
    "preset_to_options_with_tools",
    "get_builtin_tool",
    "get_builtin_tools",
    "PresetLoadError",
    # Types
    "AgentOptions",
    "AgentDefinition",
    "AgentPreset",
    "Message",
    "AnyMessage",
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "ToolMessage",
    "ResultMessage",
    "StreamEvent",
    "ContentBlock",
    "TextBlock",
    "ImageBlock",
    "ThinkingBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    "ToolDefinition",
    "Usage",
    "Role",
    "FinishReason",
    "ProviderConfig",
    "ProviderFeatures",
    "SettingSource",
    "MemoryEntry",
    "MemorySearchResult",
    "HookEvent",
    "HookCallback",
    "HookContext",
    "HookInput",
    "HookOutput",
    "HookSpecificOutput",
    "HookMatcher",
    "PermissionResult",
    "PermissionResultAllow",
    "PermissionResultDeny",
    "PermissionMode",
    # MCP and Resource Types
    "MCPServerConfig",
    "ResourceLimits",
    "SystemPromptPreset",
    # Errors
    "UniversalAgentError",
    "ProviderError",
    "ProviderNotFoundError",
    "AuthenticationError",
    "RateLimitError",
    "ModelNotFoundError",
    "ContextLengthError",
    "ConnectionError",
    "TimeoutError",
    "ToolError",
    "ToolNotFoundError",
    "ToolValidationError",
    "AgentError",
    "ConfigurationError",
    "MessageParseError",
    # Tools
    "tool",
    "Tool",
    "ToolRegistry",
    "BaseMemoryTool",
    "FileSystemMemoryTool",
    "get_memory_system_prompt",
    # Builtin Tools
    "ReadTool",
    "WriteTool",
    "EditTool",
    "BashTool",
    "GlobTool",
    "GrepTool",
    "NotebookEditTool",
    "WebSearchTool",
    "WebFetchTool",
    "DateTimeTool",
    # Skills
    "Skill",
    "SkillMetadata",
    "SkillRegistry",
    "combine_skills",
    "discover_skills",
    "get_skill",
    "list_skills",
    "load_skill_from_path",
    "load_skills_to_registry",
    # Agents
    "Agent",
    "SubAgent",
    "AgentRegistry",
    # Memory
    "BaseMemory",
    "ConversationMemory",
    "PersistentMemory",
    # Providers
    "BaseProvider",
    "ProviderRegistry",
    "register_provider",
    "ClaudeProvider",
    "OpenAIProvider",
    "AzureOpenAIProvider",
]
