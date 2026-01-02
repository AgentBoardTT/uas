"""Tests for Universal Agent SDK error handling."""

from universal_agent_sdk import (
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


class TestBaseError:
    """Test base error types."""

    def test_universal_agent_error(self):
        """Test base UniversalAgentError."""
        error = UniversalAgentError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert isinstance(error, Exception)


class TestProviderErrors:
    """Test provider-related error types."""

    def test_provider_error(self):
        """Test ProviderError."""
        error = ProviderError("Request failed", provider="openai", status_code=500)
        assert isinstance(error, UniversalAgentError)
        assert error.provider == "openai"
        assert error.status_code == 500
        assert "[openai]" in str(error)
        assert "500" in str(error)

    def test_provider_not_found_error(self):
        """Test ProviderNotFoundError."""
        error = ProviderNotFoundError("unknown_provider")
        assert isinstance(error, ProviderError)
        assert "unknown_provider" in str(error)
        assert error.provider == "unknown_provider"

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("openai", "Invalid API key")
        assert isinstance(error, ProviderError)
        assert error.status_code == 401
        assert "openai" in str(error)
        assert "Invalid API key" in str(error)

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("anthropic", retry_after=30.0)
        assert isinstance(error, ProviderError)
        assert error.status_code == 429
        assert error.retry_after == 30.0
        assert "30" in str(error)

    def test_model_not_found_error(self):
        """Test ModelNotFoundError."""
        error = ModelNotFoundError("openai", "gpt-5-turbo")
        assert isinstance(error, ProviderError)
        assert error.model == "gpt-5-turbo"
        assert "gpt-5-turbo" in str(error)

    def test_context_length_error(self):
        """Test ContextLengthError."""
        error = ContextLengthError("anthropic", max_tokens=100000, used_tokens=150000)
        assert isinstance(error, ProviderError)
        assert error.max_tokens == 100000
        assert error.used_tokens == 150000
        assert "100000" in str(error)
        assert "150000" in str(error)


class TestConnectionErrors:
    """Test connection-related error types."""

    def test_connection_error(self):
        """Test ConnectionError."""
        error = ConnectionError("Failed to connect", provider="gemini")
        assert isinstance(error, UniversalAgentError)
        assert error.provider == "gemini"
        assert "[gemini]" in str(error)

    def test_timeout_error(self):
        """Test TimeoutError."""
        error = TimeoutError("Request timed out", timeout=30.0)
        assert isinstance(error, UniversalAgentError)
        assert error.timeout == 30.0
        assert "30" in str(error)


class TestToolErrors:
    """Test tool-related error types."""

    def test_tool_error(self):
        """Test ToolError."""
        error = ToolError("Execution failed", tool_name="calculate")
        assert isinstance(error, UniversalAgentError)
        assert error.tool_name == "calculate"
        assert "calculate" in str(error)

    def test_tool_not_found_error(self):
        """Test ToolNotFoundError."""
        error = ToolNotFoundError("unknown_tool")
        assert isinstance(error, ToolError)
        assert error.tool_name == "unknown_tool"
        assert "unknown_tool" in str(error)
        assert "not found" in str(error).lower()

    def test_tool_validation_error(self):
        """Test ToolValidationError."""
        error = ToolValidationError("get_weather", "Missing required parameter: city")
        assert isinstance(error, ToolError)
        assert error.tool_name == "get_weather"
        assert "city" in str(error)
        assert "validation" in str(error).lower()


class TestAgentErrors:
    """Test agent-related error types."""

    def test_agent_error(self):
        """Test AgentError."""
        error = AgentError("Agent failed", agent_name="coding_agent")
        assert isinstance(error, UniversalAgentError)
        assert error.agent_name == "coding_agent"
        assert "coding_agent" in str(error)


class TestConfigurationErrors:
    """Test configuration error types."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid configuration")
        assert isinstance(error, UniversalAgentError)
        assert "Invalid configuration" in str(error)

    def test_message_parse_error(self):
        """Test MessageParseError."""
        error = MessageParseError("Invalid JSON", data={"raw": "invalid"})
        assert isinstance(error, UniversalAgentError)
        assert error.data == {"raw": "invalid"}
        assert "Invalid JSON" in str(error)


class TestErrorHierarchy:
    """Test error inheritance hierarchy."""

    def test_all_errors_inherit_from_base(self):
        """Test that all errors inherit from UniversalAgentError."""
        errors = [
            ProviderError("test"),
            ProviderNotFoundError("test"),
            AuthenticationError("test"),
            RateLimitError("test"),
            ModelNotFoundError("test", "model"),
            ContextLengthError("test"),
            ConnectionError("test"),
            TimeoutError("test"),
            ToolError("test"),
            ToolNotFoundError("test"),
            ToolValidationError("test", "msg"),
            AgentError("test"),
            ConfigurationError("test"),
            MessageParseError("test"),
        ]

        for error in errors:
            assert isinstance(error, UniversalAgentError), (
                f"{type(error).__name__} should inherit from UniversalAgentError"
            )

    def test_provider_errors_inherit_from_provider_error(self):
        """Test that provider-specific errors inherit from ProviderError."""
        errors = [
            ProviderNotFoundError("test"),
            AuthenticationError("test"),
            RateLimitError("test"),
            ModelNotFoundError("test", "model"),
            ContextLengthError("test"),
        ]

        for error in errors:
            assert isinstance(error, ProviderError), (
                f"{type(error).__name__} should inherit from ProviderError"
            )

    def test_tool_errors_inherit_from_tool_error(self):
        """Test that tool-specific errors inherit from ToolError."""
        errors = [
            ToolNotFoundError("test"),
            ToolValidationError("test", "msg"),
        ]

        for error in errors:
            assert isinstance(error, ToolError), (
                f"{type(error).__name__} should inherit from ToolError"
            )
