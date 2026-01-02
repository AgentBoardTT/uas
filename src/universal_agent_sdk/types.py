"""Type definitions for Universal Agent SDK."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal, TypedDict

if TYPE_CHECKING:
    pass

from typing_extensions import NotRequired

# =============================================================================
# Enums
# =============================================================================


class Role(str, Enum):
    """Message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class FinishReason(str, Enum):
    """Reasons for completion finishing."""

    STOP = "stop"
    LENGTH = "length"
    TOOL_USE = "tool_use"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"


class ContentType(str, Enum):
    """Content block types."""

    TEXT = "text"
    IMAGE = "image"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    THINKING = "thinking"


# =============================================================================
# Content Blocks
# =============================================================================


@dataclass
class TextBlock:
    """Text content block."""

    text: str
    type: Literal["text"] = "text"


@dataclass
class ImageBlock:
    """Image content block."""

    source: str  # URL or base64
    media_type: str = "image/png"
    type: Literal["image"] = "image"


@dataclass
class ThinkingBlock:
    """Thinking/reasoning content block."""

    thinking: str
    signature: str | None = None
    type: Literal["thinking"] = "thinking"


@dataclass
class ToolUseBlock:
    """Tool use request block."""

    id: str
    name: str
    input: dict[str, Any]
    type: Literal["tool_use"] = "tool_use"


@dataclass
class ToolResultBlock:
    """Tool result block."""

    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool = False
    type: Literal["tool_result"] = "tool_result"


ContentBlock = TextBlock | ImageBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock


# =============================================================================
# Messages
# =============================================================================


@dataclass
class UserMessage:
    """User message."""

    content: str | list[ContentBlock]
    role: Literal["user"] = "user"
    name: str | None = None
    uuid: str | None = None


@dataclass
class AssistantMessage:
    """Assistant message with content blocks."""

    content: list[ContentBlock]
    role: Literal["assistant"] = "assistant"
    model: str | None = None
    finish_reason: FinishReason | None = None
    uuid: str | None = None


@dataclass
class SystemMessage:
    """System message."""

    content: str
    role: Literal["system"] = "system"
    name: str | None = None


@dataclass
class ToolMessage:
    """Tool result message (for OpenAI-style API)."""

    content: str
    tool_call_id: str
    role: Literal["tool"] = "tool"
    name: str | None = None


Message = UserMessage | AssistantMessage | SystemMessage | ToolMessage


# =============================================================================
# Result and Streaming
# =============================================================================


@dataclass
class Usage:
    """Token usage information."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    # Provider-specific fields
    cache_read_tokens: int | None = None
    cache_creation_tokens: int | None = None


@dataclass
class ResultMessage:
    """Result message with cost and usage information."""

    is_error: bool = False
    duration_ms: int = 0
    num_turns: int = 1
    session_id: str | None = None
    total_cost_usd: float | None = None
    usage: Usage | None = None
    result: str | None = None
    finish_reason: FinishReason | None = None


@dataclass
class StreamEvent:
    """Stream event for partial message updates."""

    event_type: str  # e.g., "content_block_delta", "message_delta"
    index: int | None = None
    delta: dict[str, Any] | None = None
    content_block: ContentBlock | None = None


# Union of all message types including streaming
AnyMessage = Message | ResultMessage | StreamEvent


# =============================================================================
# Tool Definitions
# =============================================================================


class ToolParameter(TypedDict, total=False):
    """Tool parameter definition."""

    type: str
    description: str
    enum: list[str]
    default: Any
    items: dict[str, Any]  # For array types
    properties: dict[str, "ToolParameter"]  # For object types
    required: list[str]  # For object types


class ToolSchema(TypedDict, total=False):
    """Tool JSON Schema definition."""

    type: str
    properties: dict[str, ToolParameter]
    required: list[str]
    additionalProperties: bool


@dataclass
class ToolDefinition:
    """Tool definition for the SDK."""

    name: str
    description: str
    input_schema: ToolSchema | dict[str, Any]
    handler: Callable[..., Awaitable[Any] | Any] | None = None


# =============================================================================
# Tool Permission Types
# =============================================================================


@dataclass
class ToolPermissionContext:
    """Context information for tool permission callbacks."""

    session_id: str | None = None
    signal: Any | None = None


@dataclass
class PermissionResultAllow:
    """Allow permission result."""

    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] | None = None


@dataclass
class PermissionResultDeny:
    """Deny permission result."""

    behavior: Literal["deny"] = "deny"
    message: str = ""
    interrupt: bool = False


PermissionResult = PermissionResultAllow | PermissionResultDeny

CanUseTool = Callable[
    [str, dict[str, Any], ToolPermissionContext], Awaitable[PermissionResult]
]


# =============================================================================
# Hook Types
# =============================================================================


HookEvent = Literal[
    "SessionStart",
    "PreToolUse",
    "PostToolUse",
    "PreCompletion",
    "PostCompletion",
    "OnError",
]


class HookContext(TypedDict):
    """Context passed to hook callbacks."""

    session_id: str
    tool_use_id: str | None


class BaseHookInput(TypedDict):
    """Base hook input fields."""

    session_id: str


class SessionStartHookInput(BaseHookInput):
    """Input for SessionStart hook."""

    hook_event_name: Literal["SessionStart"]


class PreToolUseHookInput(BaseHookInput):
    """Input for PreToolUse hook."""

    hook_event_name: Literal["PreToolUse"]
    tool_name: str
    tool_input: dict[str, Any]


class PostToolUseHookInput(BaseHookInput):
    """Input for PostToolUse hook."""

    hook_event_name: Literal["PostToolUse"]
    tool_name: str
    tool_input: dict[str, Any]
    tool_response: Any


class PreCompletionHookInput(BaseHookInput):
    """Input for PreCompletion hook."""

    hook_event_name: Literal["PreCompletion"]
    messages: list[dict[str, Any]]


class PostCompletionHookInput(BaseHookInput):
    """Input for PostCompletion hook."""

    hook_event_name: Literal["PostCompletion"]
    response: AssistantMessage


class OnErrorHookInput(BaseHookInput):
    """Input for OnError hook."""

    hook_event_name: Literal["OnError"]
    error: str
    error_type: str


HookInput = (
    SessionStartHookInput
    | PreToolUseHookInput
    | PostToolUseHookInput
    | PreCompletionHookInput
    | PostCompletionHookInput
    | OnErrorHookInput
)


class HookSpecificOutput(TypedDict, total=False):
    """Hook-specific output fields."""

    hookEventName: str
    permissionDecision: Literal["allow", "deny"] | None
    permissionDecisionReason: str | None
    additionalContext: str | None


class HookOutput(TypedDict, total=False):
    """Hook callback output.

    Fields:
        continue_: Whether to continue execution (False stops the agent)
        stopReason: Reason for stopping (when continue_=False)
        reason: General reason/explanation for the hook's decision
        systemMessage: Message to display to the user
        modified_input: Modified tool/completion input
        hookSpecificOutput: Event-specific output fields
    """

    continue_: bool
    stopReason: str | None
    reason: str | None
    systemMessage: str | None
    modified_input: dict[str, Any] | None
    hookSpecificOutput: HookSpecificOutput | None


# Hook callback signature: (input_data, tool_use_id, context) -> HookOutput
HookCallback = Callable[
    [HookInput, str | None, HookContext],
    Awaitable[HookOutput],
]


@dataclass
class HookMatcher:
    """Hook matcher configuration.

    Attributes:
        matcher: Pattern to match (e.g., tool name). None matches all.
        hooks: List of hook callback functions to execute.
        timeout: Optional timeout in seconds for hook execution.
    """

    matcher: str | None = None
    hooks: list[HookCallback] = field(default_factory=list)
    timeout: float | None = None


# =============================================================================
# Agent Types
# =============================================================================


@dataclass
class AgentDefinition:
    """Agent definition configuration."""

    name: str
    description: str
    system_prompt: str | None = None
    tools: list[str] | None = None
    model: str | None = None
    provider: str | None = None
    max_turns: int | None = None


# =============================================================================
# Memory Types
# =============================================================================


@dataclass
class MemoryEntry:
    """A single memory entry."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    timestamp: float | None = None


@dataclass
class MemorySearchResult:
    """Result from memory search."""

    entry: MemoryEntry
    score: float


# =============================================================================
# Provider Configuration
# =============================================================================


class ProviderConfig(TypedDict, total=False):
    """Base provider configuration."""

    api_key: str
    base_url: str
    timeout: float
    max_retries: int


class ClaudeProviderConfig(ProviderConfig):
    """Claude-specific configuration."""

    anthropic_version: NotRequired[str]


class OpenAIProviderConfig(ProviderConfig):
    """OpenAI-specific configuration."""

    organization: NotRequired[str]
    project: NotRequired[str]


class AzureOpenAIProviderConfig(ProviderConfig):
    """Azure OpenAI-specific configuration."""

    api_version: str
    deployment_name: NotRequired[str]
    azure_ad_token: NotRequired[str]


class GeminiProviderConfig(ProviderConfig):
    """Gemini-specific configuration."""

    project_id: NotRequired[str]
    location: NotRequired[str]


class OllamaProviderConfig(ProviderConfig):
    """Ollama-specific configuration."""

    host: NotRequired[str]


# =============================================================================
# Main Options
# =============================================================================


# Type alias for setting sources
SettingSource = Literal["user", "project", "local"]


# =============================================================================
# MCP Server Configuration
# =============================================================================


@dataclass
class MCPServerConfig:
    """MCP (Model Context Protocol) server configuration.

    Supports both stdio and SSE transport types.
    """

    type: Literal["stdio", "sse"] = "stdio"
    command: str | None = None  # For stdio: command to run
    args: list[str] = field(default_factory=list)  # For stdio: command arguments
    url: str | None = None  # For sse: server URL
    env: dict[str, str] = field(default_factory=dict)  # Environment variables


# =============================================================================
# Resource Limits Configuration
# =============================================================================


@dataclass
class ResourceLimits:
    """Resource limits for agent execution."""

    cpu_quota: int | None = None  # CPU quota in microseconds (e.g., 300000 = 3 CPUs)
    memory_limit: str | None = None  # Memory limit (e.g., "8g", "512m")
    storage_limit: str | None = None  # Storage limit (e.g., "20g")
    timeout_seconds: int | None = None  # Execution timeout


# =============================================================================
# System Prompt Preset Configuration
# =============================================================================

# Built-in preset names
SystemPromptPresetName = Literal[
    "claude_code",
    "assistant",
    "developer",
    "researcher",
]


@dataclass
class SystemPromptPreset:
    """System prompt configuration using a preset with optional append.

    Example:
        system_prompt:
          type: preset
          preset: claude_code
          append: |
            Custom instructions here...
    """

    type: Literal["preset"] = "preset"
    preset: str = "assistant"  # Preset name (e.g., "claude_code", "assistant")
    append: str | None = None  # Additional instructions to append


# Union type for system prompt - can be string or preset config
SystemPromptConfig = str | SystemPromptPreset


# =============================================================================
# Permission Mode
# =============================================================================

PermissionMode = Literal[
    "ask",  # Ask user for permission on each tool use
    "auto_allow",  # Automatically allow all tool uses
    "acceptEdits",  # Auto-allow edits but ask for other operations
    "deny_all",  # Deny all tool uses
]


@dataclass
class AgentOptions:
    """Universal agent options."""

    # Provider settings
    provider: str = "claude"  # claude, openai, azure_openai, gemini, ollama
    provider_config: dict[str, Any] | None = None
    model: str | None = None
    fallback_model: str | None = None

    # System configuration
    system_prompt: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None

    # Tool configuration
    tools: list[ToolDefinition] = field(default_factory=list)
    tool_choice: Literal["auto", "required", "none"] | str | None = None
    can_use_tool: CanUseTool | None = None

    # Skills configuration
    # Sources to load skills from: "user" (~/.claude/skills/), "project" (.claude/skills/)
    setting_sources: list[SettingSource] = field(default_factory=list)
    # List of allowed tools including "Skill" to enable skill invocation
    allowed_tools: list[str] = field(default_factory=list)
    # List of skill names to enable
    skills: list[str] = field(default_factory=list)

    # Agent configuration
    agents: dict[str, AgentDefinition] = field(default_factory=dict)
    max_turns: int | None = None

    # Memory configuration
    memory_enabled: bool = False
    memory_type: Literal["conversation", "vector", "persistent"] = "conversation"
    memory_config: dict[str, Any] = field(default_factory=dict)

    # Session configuration
    session_id: str | None = None
    continue_conversation: bool = False

    # Hook configuration
    hooks: dict[HookEvent, list[HookMatcher]] | None = None

    # Streaming configuration
    stream: bool = True
    include_usage: bool = True

    # Cost/budget configuration
    max_budget_usd: float | None = None

    # Extended features
    enable_thinking: bool = False
    max_thinking_tokens: int | None = None

    # Environment
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)

    # MCP (Model Context Protocol) servers
    mcp_servers: dict[str, MCPServerConfig] = field(default_factory=dict)

    # Resource limits
    resource_limits: ResourceLimits | None = None

    # Permission mode for tool usage
    permission_mode: PermissionMode | None = None

    # Debug/logging
    debug: bool = False
    stderr_callback: Callable[[str], None] | None = None


# =============================================================================
# Provider Features
# =============================================================================


@dataclass
class ProviderFeatures:
    """Features supported by a provider."""

    streaming: bool = True
    tool_calling: bool = True
    vision: bool = False
    thinking: bool = False
    json_mode: bool = False
    max_context_length: int = 128000
    supports_system_message: bool = True


# =============================================================================
# Agent Preset Configuration
# =============================================================================


@dataclass
class AgentPreset:
    """Agent preset configuration loaded from YAML/JSON files.

    This represents a complete agent configuration that can be loaded
    from a preset file and converted to AgentOptions.

    Example YAML:
        ```yaml
        id: creative-developer
        name: Creative Developer
        description: Full-featured creative development agent

        system_prompt:
          type: preset
          preset: claude_code
          append: |
            Custom instructions...

        allowed_tools:
          - Read
          - Write
          - Bash

        mcp_servers:
          filesystem:
            type: stdio
            command: npx
            args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]

        agents:
          helper:
            description: Helper agent
            prompt: You are a helpful assistant
            tools: [Read, Write]
            model: sonnet
        ```
    """

    # Required identifiers
    id: str
    name: str

    # Optional metadata
    description: str | None = None
    version: str | None = None

    # System prompt - can be string or preset config
    system_prompt: SystemPromptConfig | None = None

    # Tool and skill configuration
    allowed_tools: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)

    # Permission mode
    permission_mode: PermissionMode | None = None

    # Resource limits
    resource_limits: ResourceLimits | None = None

    # Setting sources for loading additional configs
    setting_sources: list[SettingSource] = field(default_factory=list)

    # Environment variables
    env: dict[str, str] = field(default_factory=dict)

    # MCP servers
    mcp_servers: dict[str, MCPServerConfig] = field(default_factory=dict)

    # Sub-agents
    agents: dict[str, AgentDefinition] = field(default_factory=dict)

    # Model configuration
    model: str | None = None
    provider: str = "claude"
    max_turns: int | None = None

    # Working directory
    cwd: str | None = None

    # Timestamps
    created_at: str | None = None
    updated_at: str | None = None

    def to_agent_options(
        self,
        system_prompt_resolver: Callable[[str], str] | None = None,
    ) -> AgentOptions:
        """Convert preset to AgentOptions.

        Args:
            system_prompt_resolver: Optional function to resolve preset names
                to actual system prompts. If not provided, preset prompts
                will use default templates.

        Returns:
            AgentOptions configured from this preset
        """
        # Resolve system prompt
        resolved_system_prompt: str | None = None
        if isinstance(self.system_prompt, str):
            resolved_system_prompt = self.system_prompt
        elif isinstance(self.system_prompt, SystemPromptPreset):
            base_prompt = ""
            if system_prompt_resolver:
                base_prompt = system_prompt_resolver(self.system_prompt.preset)
            else:
                base_prompt = _get_default_system_prompt(self.system_prompt.preset)

            if self.system_prompt.append:
                resolved_system_prompt = f"{base_prompt}\n\n{self.system_prompt.append}"
            else:
                resolved_system_prompt = base_prompt

        return AgentOptions(
            provider=self.provider,
            model=self.model,
            system_prompt=resolved_system_prompt,
            allowed_tools=self.allowed_tools,
            skills=self.skills,
            setting_sources=self.setting_sources,
            env=self.env,
            mcp_servers=self.mcp_servers,
            resource_limits=self.resource_limits,
            permission_mode=self.permission_mode,
            agents=self.agents,
            max_turns=self.max_turns,
            cwd=self.cwd,
        )


def _get_default_system_prompt(preset_name: str) -> str:
    """Get default system prompt for a preset name."""
    prompts = {
        "assistant": "You are a helpful AI assistant.",
        "developer": (
            "You are an expert software developer. Help with coding tasks, "
            "debugging, and software architecture questions."
        ),
        "researcher": (
            "You are a research assistant. Help with finding information, "
            "analyzing data, and summarizing complex topics."
        ),
        "claude_code": (
            "You are Claude Code, an AI assistant specialized in software development. "
            "You can read and write files, run shell commands, and help with "
            "coding tasks. Follow best practices and write clean, maintainable code."
        ),
    }
    return prompts.get(preset_name, prompts["assistant"])
