"""Error types for Universal Agent SDK."""

from typing import Any


class UniversalAgentError(Exception):
    """Base exception for all Universal Agent SDK errors."""


class ProviderError(UniversalAgentError):
    """Raised when a provider operation fails."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        status_code: int | None = None,
        response: Any = None,
    ):
        self.provider = provider
        self.status_code = status_code
        self.response = response

        if provider:
            message = f"[{provider}] {message}"
        if status_code:
            message = f"{message} (status: {status_code})"

        super().__init__(message)


class ProviderNotFoundError(ProviderError):
    """Raised when a provider is not found or not configured."""

    def __init__(self, provider: str):
        super().__init__(
            f"Provider '{provider}' not found or not configured", provider=provider
        )


class AuthenticationError(ProviderError):
    """Raised when authentication with a provider fails."""

    def __init__(self, provider: str, message: str = "Authentication failed"):
        super().__init__(message, provider=provider, status_code=401)


class RateLimitError(ProviderError):
    """Raised when rate limited by a provider."""

    def __init__(
        self,
        provider: str,
        retry_after: float | None = None,
        message: str = "Rate limit exceeded",
    ):
        self.retry_after = retry_after
        if retry_after:
            message = f"{message} (retry after {retry_after}s)"
        super().__init__(message, provider=provider, status_code=429)


class ModelNotFoundError(ProviderError):
    """Raised when a model is not found or not available."""

    def __init__(self, provider: str, model: str):
        self.model = model
        super().__init__(
            f"Model '{model}' not found or not available", provider=provider
        )


class ContextLengthError(ProviderError):
    """Raised when context length is exceeded."""

    def __init__(
        self,
        provider: str,
        max_tokens: int | None = None,
        used_tokens: int | None = None,
    ):
        self.max_tokens = max_tokens
        self.used_tokens = used_tokens
        message = "Context length exceeded"
        if max_tokens and used_tokens:
            message = f"{message} (max: {max_tokens}, used: {used_tokens})"
        super().__init__(message, provider=provider)


class ConnectionError(UniversalAgentError):
    """Raised when unable to connect to a provider."""

    def __init__(self, message: str = "Connection failed", provider: str | None = None):
        self.provider = provider
        if provider:
            message = f"[{provider}] {message}"
        super().__init__(message)


class TimeoutError(UniversalAgentError):
    """Raised when an operation times out."""

    def __init__(
        self, message: str = "Operation timed out", timeout: float | None = None
    ):
        self.timeout = timeout
        if timeout:
            message = f"{message} (timeout: {timeout}s)"
        super().__init__(message)


class ToolError(UniversalAgentError):
    """Raised when a tool execution fails."""

    def __init__(self, message: str, tool_name: str | None = None):
        self.tool_name = tool_name
        if tool_name:
            message = f"Tool '{tool_name}': {message}"
        super().__init__(message)


class ToolNotFoundError(ToolError):
    """Raised when a tool is not found."""

    def __init__(self, tool_name: str):
        super().__init__("Tool not found", tool_name=tool_name)


class ToolValidationError(ToolError):
    """Raised when tool input validation fails."""

    def __init__(self, tool_name: str, message: str):
        super().__init__(f"Validation error: {message}", tool_name=tool_name)


class AgentError(UniversalAgentError):
    """Raised when an agent operation fails."""

    def __init__(self, message: str, agent_name: str | None = None):
        self.agent_name = agent_name
        if agent_name:
            message = f"Agent '{agent_name}': {message}"
        super().__init__(message)


class MemoryError(UniversalAgentError):
    """Raised when a memory operation fails."""


class ConfigurationError(UniversalAgentError):
    """Raised when configuration is invalid."""


class MessageParseError(UniversalAgentError):
    """Raised when unable to parse a message."""

    def __init__(self, message: str, data: dict[str, Any] | None = None):
        self.data = data
        super().__init__(message)
