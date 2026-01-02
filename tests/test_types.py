"""Tests for Universal Agent SDK type definitions."""

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ResultMessage,
)
from universal_agent_sdk.types import (
    FinishReason,
    HookMatcher,
    MemoryEntry,
    PermissionResultAllow,
    PermissionResultDeny,
    Role,
    TextBlock,
    ThinkingBlock,
    ToolDefinition,
    ToolResultBlock,
    ToolUseBlock,
    Usage,
    UserMessage,
)


class TestEnums:
    """Test enum types."""

    def test_role_enum(self):
        """Test Role enum values."""
        assert Role.USER == "user"
        assert Role.ASSISTANT == "assistant"
        assert Role.SYSTEM == "system"
        assert Role.TOOL == "tool"

    def test_finish_reason_enum(self):
        """Test FinishReason enum values."""
        assert FinishReason.STOP == "stop"
        assert FinishReason.LENGTH == "length"
        assert FinishReason.TOOL_USE == "tool_use"
        assert FinishReason.CONTENT_FILTER == "content_filter"
        assert FinishReason.ERROR == "error"


class TestContentBlocks:
    """Test content block types."""

    def test_text_block(self):
        """Test TextBlock creation."""
        block = TextBlock(text="Hello, world!")
        assert block.text == "Hello, world!"
        assert block.type == "text"

    def test_thinking_block(self):
        """Test ThinkingBlock creation."""
        block = ThinkingBlock(thinking="I'm thinking...", signature="sig-123")
        assert block.thinking == "I'm thinking..."
        assert block.signature == "sig-123"
        assert block.type == "thinking"

    def test_tool_use_block(self):
        """Test ToolUseBlock creation."""
        block = ToolUseBlock(
            id="tool-123", name="Read", input={"file_path": "/test.txt"}
        )
        assert block.id == "tool-123"
        assert block.name == "Read"
        assert block.input["file_path"] == "/test.txt"
        assert block.type == "tool_use"

    def test_tool_result_block(self):
        """Test ToolResultBlock creation."""
        block = ToolResultBlock(
            tool_use_id="tool-123", content="File contents here", is_error=False
        )
        assert block.tool_use_id == "tool-123"
        assert block.content == "File contents here"
        assert block.is_error is False
        assert block.type == "tool_result"


class TestMessageTypes:
    """Test message type creation and validation."""

    def test_user_message_creation(self):
        """Test creating a UserMessage."""
        msg = UserMessage(content="Hello, Claude!")
        assert msg.content == "Hello, Claude!"
        assert msg.role == "user"

    def test_assistant_message_with_text(self):
        """Test creating an AssistantMessage with text content."""
        text_block = TextBlock(text="Hello, human!")
        msg = AssistantMessage(content=[text_block], model="claude-sonnet-4-20250514")
        assert len(msg.content) == 1
        assert msg.content[0].text == "Hello, human!"
        assert msg.role == "assistant"
        assert msg.model == "claude-sonnet-4-20250514"

    def test_assistant_message_with_thinking(self):
        """Test creating an AssistantMessage with thinking content."""
        thinking_block = ThinkingBlock(thinking="I'm thinking...", signature="sig-123")
        msg = AssistantMessage(
            content=[thinking_block], model="claude-sonnet-4-20250514"
        )
        assert len(msg.content) == 1
        assert msg.content[0].thinking == "I'm thinking..."
        assert msg.content[0].signature == "sig-123"

    def test_result_message(self):
        """Test creating a ResultMessage."""
        msg = ResultMessage(
            duration_ms=1500,
            is_error=False,
            num_turns=1,
            session_id="session-123",
            total_cost_usd=0.01,
        )
        assert msg.duration_ms == 1500
        assert msg.total_cost_usd == 0.01
        assert msg.session_id == "session-123"
        assert msg.is_error is False

    def test_result_message_with_usage(self):
        """Test ResultMessage with usage information."""
        usage = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        msg = ResultMessage(
            is_error=False,
            usage=usage,
        )
        assert msg.usage is not None
        assert msg.usage.prompt_tokens == 100
        assert msg.usage.completion_tokens == 50
        assert msg.usage.total_tokens == 150


class TestToolDefinition:
    """Test ToolDefinition type."""

    def test_tool_definition_creation(self):
        """Test creating a ToolDefinition."""
        tool = ToolDefinition(
            name="get_weather",
            description="Get weather for a city",
            input_schema={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        )
        assert tool.name == "get_weather"
        assert tool.description == "Get weather for a city"
        assert "properties" in tool.input_schema

    def test_tool_definition_with_handler(self):
        """Test ToolDefinition with handler function."""

        async def handler(city: str) -> str:
            return f"Weather in {city}"

        tool = ToolDefinition(
            name="get_weather",
            description="Get weather",
            input_schema={"type": "object"},
            handler=handler,
        )
        assert tool.handler is handler


class TestAgentOptions:
    """Test AgentOptions configuration."""

    def test_default_options(self):
        """Test AgentOptions with default values."""
        options = AgentOptions()
        assert options.provider == "claude"
        assert options.tools == []
        assert options.system_prompt is None
        assert options.continue_conversation is False
        assert options.stream is True

    def test_options_with_anthropic_provider(self):
        """Test AgentOptions with Anthropic provider."""
        options = AgentOptions(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
        )
        assert options.provider == "anthropic"
        assert options.model == "claude-sonnet-4-20250514"

    def test_options_with_openai_provider(self):
        """Test AgentOptions with OpenAI provider."""
        options = AgentOptions(
            provider="openai",
            model="gpt-4o",
        )
        assert options.provider == "openai"
        assert options.model == "gpt-4o"

    def test_options_with_tools(self):
        """Test AgentOptions with tools."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"},
        )
        options = AgentOptions(tools=[tool])
        assert len(options.tools) == 1
        assert options.tools[0].name == "test_tool"

    def test_options_with_system_prompt(self):
        """Test AgentOptions with system prompt."""
        options = AgentOptions(
            system_prompt="You are a helpful assistant.",
        )
        assert options.system_prompt == "You are a helpful assistant."

    def test_options_with_session_continuation(self):
        """Test AgentOptions with session continuation."""
        options = AgentOptions(
            continue_conversation=True, session_id="session-123"
        )
        assert options.continue_conversation is True
        assert options.session_id == "session-123"

    def test_options_with_model_parameters(self):
        """Test AgentOptions with model parameters."""
        options = AgentOptions(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            temperature=0.7,
            top_p=0.9,
        )
        assert options.model == "claude-sonnet-4-20250514"
        assert options.max_tokens == 1000
        assert options.temperature == 0.7
        assert options.top_p == 0.9

    def test_options_with_budget(self):
        """Test AgentOptions with budget limit."""
        options = AgentOptions(max_budget_usd=1.0)
        assert options.max_budget_usd == 1.0

    def test_options_with_memory(self):
        """Test AgentOptions with memory configuration."""
        options = AgentOptions(
            memory_enabled=True,
            memory_type="conversation",
        )
        assert options.memory_enabled is True
        assert options.memory_type == "conversation"

    def test_options_with_thinking(self):
        """Test AgentOptions with thinking/reasoning enabled."""
        options = AgentOptions(
            enable_thinking=True,
            max_thinking_tokens=2000,
        )
        assert options.enable_thinking is True
        assert options.max_thinking_tokens == 2000


class TestPermissionTypes:
    """Test permission result types."""

    def test_permission_allow(self):
        """Test PermissionResultAllow."""
        result = PermissionResultAllow()
        assert result.behavior == "allow"
        assert result.updated_input is None

    def test_permission_allow_with_updated_input(self):
        """Test PermissionResultAllow with modified input."""
        result = PermissionResultAllow(updated_input={"safe_mode": True})
        assert result.behavior == "allow"
        assert result.updated_input == {"safe_mode": True}

    def test_permission_deny(self):
        """Test PermissionResultDeny."""
        result = PermissionResultDeny(message="Not allowed")
        assert result.behavior == "deny"
        assert result.message == "Not allowed"
        assert result.interrupt is False

    def test_permission_deny_with_interrupt(self):
        """Test PermissionResultDeny with interrupt."""
        result = PermissionResultDeny(message="Security violation", interrupt=True)
        assert result.behavior == "deny"
        assert result.interrupt is True


class TestHookTypes:
    """Test hook-related types."""

    def test_hook_matcher_creation(self):
        """Test HookMatcher creation."""
        matcher = HookMatcher(matcher="Bash", hooks=[], timeout=30.0)
        assert matcher.matcher == "Bash"
        assert matcher.hooks == []
        assert matcher.timeout == 30.0

    def test_hook_matcher_match_all(self):
        """Test HookMatcher that matches all."""
        matcher = HookMatcher(matcher=None, hooks=[])
        assert matcher.matcher is None


class TestMemoryTypes:
    """Test memory-related types."""

    def test_memory_entry(self):
        """Test MemoryEntry creation."""
        entry = MemoryEntry(
            id="mem-123",
            content="Remember this fact",
            metadata={"source": "user"},
        )
        assert entry.id == "mem-123"
        assert entry.content == "Remember this fact"
        assert entry.metadata["source"] == "user"

    def test_memory_entry_with_embedding(self):
        """Test MemoryEntry with embedding."""
        entry = MemoryEntry(
            id="mem-123",
            content="Test",
            embedding=[0.1, 0.2, 0.3],
        )
        assert entry.embedding == [0.1, 0.2, 0.3]


class TestUsage:
    """Test Usage type."""

    def test_usage_creation(self):
        """Test Usage creation."""
        usage = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_usage_with_cache(self):
        """Test Usage with cache tokens."""
        usage = Usage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cache_read_tokens=20,
            cache_creation_tokens=10,
        )
        assert usage.cache_read_tokens == 20
        assert usage.cache_creation_tokens == 10
