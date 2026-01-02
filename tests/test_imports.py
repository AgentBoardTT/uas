"""Test that all main exports are importable."""

import pytest


def test_main_imports():
    """Test that main module exports are available."""
    from universal_agent_sdk import (
        AgentOptions,
        UniversalAgentClient,
        query,
    )

    assert AgentOptions is not None
    assert UniversalAgentClient is not None
    assert query is not None


def test_tool_imports():
    """Test that tool-related exports are available."""
    from universal_agent_sdk import tool

    assert tool is not None


def test_type_imports():
    """Test that type exports are available."""
    from universal_agent_sdk import (
        AssistantMessage,
        TextBlock,
        ToolResultBlock,
        ToolUseBlock,
        UserMessage,
    )

    assert UserMessage is not None
    assert AssistantMessage is not None
    assert TextBlock is not None
    assert ToolUseBlock is not None
    assert ToolResultBlock is not None


def test_error_imports():
    """Test that error classes are available."""
    from universal_agent_sdk import (
        AuthenticationError,
        ProviderError,
        RateLimitError,
        UniversalAgentError,
    )

    assert UniversalAgentError is not None
    assert ProviderError is not None
    assert AuthenticationError is not None
    assert RateLimitError is not None


def test_agent_options_creation():
    """Test creating AgentOptions with different providers."""
    from universal_agent_sdk import AgentOptions

    # Anthropic
    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
    )
    assert options.provider == "anthropic"

    # OpenAI
    options = AgentOptions(
        provider="openai",
        model="gpt-4o",
    )
    assert options.provider == "openai"


def test_tool_decorator():
    """Test the @tool decorator."""
    from universal_agent_sdk import tool

    @tool
    def my_test_tool(arg: str) -> str:
        """A test tool.

        Args:
            arg: A test argument
        """
        return f"Result: {arg}"

    assert hasattr(my_test_tool, "definition")
    assert my_test_tool.definition is not None
