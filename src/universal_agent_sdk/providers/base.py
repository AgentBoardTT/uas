"""Base provider interface for Universal Agent SDK."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from typing import Any

from ..types import (
    AgentOptions,
    AnyMessage,
    AssistantMessage,
    ContentBlock,
    Message,
    ProviderFeatures,
    ToolDefinition,
    Usage,
)


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    name: str = "base"
    config: dict[str, Any]

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the provider with configuration.

        Args:
            config: Provider-specific configuration
        """
        self.config = config or {}
        self._validate_config()

    def _validate_config(self) -> None:  # noqa: B027
        """Validate provider configuration. Override in subclasses."""
        pass

    @abstractmethod
    def get_features(self) -> ProviderFeatures:
        """Get the features supported by this provider.

        Returns:
            ProviderFeatures object describing capabilities
        """
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        options: AgentOptions,
    ) -> AssistantMessage:
        """Generate a completion for the given messages.

        Args:
            messages: List of conversation messages
            options: Agent options including model, temperature, etc.

        Returns:
            AssistantMessage with the completion
        """
        ...

    @abstractmethod
    def stream(
        self,
        messages: list[Message],
        options: AgentOptions,
    ) -> AsyncIterator[AnyMessage]:
        """Stream a completion for the given messages.

        Args:
            messages: List of conversation messages
            options: Agent options including model, temperature, etc.

        Yields:
            Stream of messages including StreamEvents, AssistantMessage, and ResultMessage
        """
        ...

    # ==========================================================================
    # Format Conversion Methods - Override for provider-specific formats
    # ==========================================================================

    def format_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert SDK messages to provider-specific format.

        Args:
            messages: List of SDK Message objects

        Returns:
            List of provider-formatted message dictionaries
        """
        return [self.format_message(msg) for msg in messages]

    def format_message(self, message: Message) -> dict[str, Any]:
        """Convert a single SDK message to provider format.

        Args:
            message: SDK Message object

        Returns:
            Provider-formatted message dictionary
        """
        from ..types import AssistantMessage, SystemMessage, ToolMessage, UserMessage

        if isinstance(message, UserMessage):
            return self._format_user_message(message)
        elif isinstance(message, AssistantMessage):
            return self._format_assistant_message(message)
        elif isinstance(message, SystemMessage):
            return self._format_system_message(message)
        elif isinstance(message, ToolMessage):
            return self._format_tool_message(message)
        else:
            raise ValueError(f"Unknown message type: {type(message)}")

    def _format_user_message(self, message: Any) -> dict[str, Any]:
        """Format user message. Override for provider-specific format."""
        content = message.content
        if isinstance(content, list):
            content = self._format_content_blocks(content)
        return {"role": "user", "content": content}

    def _format_assistant_message(self, message: Any) -> dict[str, Any]:
        """Format assistant message. Override for provider-specific format."""
        content = self._format_content_blocks(message.content)
        return {"role": "assistant", "content": content}

    def _format_system_message(self, message: Any) -> dict[str, Any]:
        """Format system message. Override for provider-specific format."""
        return {"role": "system", "content": message.content}

    def _format_tool_message(self, message: Any) -> dict[str, Any]:
        """Format tool message. Override for provider-specific format."""
        return {
            "role": "tool",
            "content": message.content,
            "tool_call_id": message.tool_call_id,
        }

    def _format_content_blocks(self, blocks: list[ContentBlock]) -> Any:
        """Format content blocks. Override for provider-specific format."""
        from ..types import (
            ImageBlock,
            TextBlock,
            ThinkingBlock,
            ToolResultBlock,
            ToolUseBlock,
        )

        result: list[dict[str, Any]] = []
        for block in blocks:
            if isinstance(block, TextBlock):
                result.append({"type": "text", "text": block.text})
            elif isinstance(block, ImageBlock):
                result.append(
                    {
                        "type": "image",
                        "source": block.source,
                        "media_type": block.media_type,
                    }
                )
            elif isinstance(block, ToolUseBlock):
                result.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
            elif isinstance(block, ToolResultBlock):
                result.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.tool_use_id,
                        "content": block.content,
                        "is_error": block.is_error,
                    }
                )
            elif isinstance(block, ThinkingBlock):
                result.append(
                    {
                        "type": "thinking",
                        "thinking": block.thinking,
                    }
                )
        return result

    def format_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
        """Convert SDK tools to provider-specific format.

        Args:
            tools: List of ToolDefinition objects

        Returns:
            List of provider-formatted tool dictionaries
        """
        return [self.format_tool(tool) for tool in tools]

    def format_tool(self, tool: ToolDefinition) -> dict[str, Any]:
        """Convert a single tool to provider format. Override for provider-specific format."""
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        }

    # ==========================================================================
    # Response Parsing Methods - Override for provider-specific formats
    # ==========================================================================

    def parse_response(self, response: dict[str, Any]) -> AssistantMessage:
        """Parse provider response to SDK AssistantMessage.

        Args:
            response: Raw provider response

        Returns:
            AssistantMessage with parsed content
        """
        raise NotImplementedError("Subclasses must implement parse_response")

    def parse_stream_event(self, event: dict[str, Any]) -> AnyMessage | None:
        """Parse a streaming event to SDK message.

        Args:
            event: Raw streaming event from provider

        Returns:
            Parsed message or None if event should be skipped
        """
        raise NotImplementedError("Subclasses must implement parse_stream_event")

    def parse_usage(self, usage_data: dict[str, Any]) -> Usage:
        """Parse provider usage data to SDK Usage.

        Args:
            usage_data: Raw usage data from provider

        Returns:
            Usage object
        """
        return Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0)
            or usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0)
            or usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

    # ==========================================================================
    # Utility Methods
    # ==========================================================================

    def get_default_model(self) -> str:
        """Get the default model for this provider."""
        return ""

    def supports_feature(self, feature: str) -> bool:
        """Check if provider supports a specific feature.

        Args:
            feature: Feature name (e.g., 'streaming', 'tool_calling', 'vision')

        Returns:
            True if feature is supported
        """
        features = self.get_features()
        return getattr(features, feature, False)


class ProviderRegistry:
    """Registry for managing provider instances."""

    _providers: dict[str, type[BaseProvider]] = {}
    _instances: dict[str, BaseProvider] = {}

    @classmethod
    def register(cls, name: str, provider_class: type[BaseProvider]) -> None:
        """Register a provider class.

        Args:
            name: Provider name (e.g., 'claude', 'openai')
            provider_class: Provider class to register
        """
        cls._providers[name] = provider_class

    @classmethod
    def get(cls, name: str, config: dict[str, Any] | None = None) -> BaseProvider:
        """Get or create a provider instance.

        Args:
            name: Provider name
            config: Optional configuration for new instances

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If provider is not registered
        """
        from ..errors import ProviderNotFoundError

        if name not in cls._providers:
            raise ProviderNotFoundError(name)

        # Create new instance if config provided or no cached instance
        cache_key = f"{name}:{hash(str(config))}" if config else name
        if cache_key not in cls._instances or config:
            cls._instances[cache_key] = cls._providers[name](config)

        return cls._instances[cache_key]

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider names."""
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a provider is registered."""
        return name in cls._providers


def register_provider(name: str) -> Callable[[type[BaseProvider]], type[BaseProvider]]:
    """Decorator to register a provider class.

    Usage:
        @register_provider("my_provider")
        class MyProvider(BaseProvider):
            ...
    """

    def decorator(cls: type[BaseProvider]) -> type[BaseProvider]:
        ProviderRegistry.register(name, cls)
        cls.name = name
        return cls

    return decorator
