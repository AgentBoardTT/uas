"""Claude (Anthropic) provider implementation."""

import os
from collections.abc import AsyncIterator
from typing import Any

from ..errors import AuthenticationError, ProviderError, RateLimitError
from ..types import (
    AgentOptions,
    AnyMessage,
    AssistantMessage,
    ContentBlock,
    FinishReason,
    ImageBlock,
    Message,
    ProviderFeatures,
    ResultMessage,
    StreamEvent,
    TextBlock,
    ThinkingBlock,
    ToolDefinition,
    ToolResultBlock,
    ToolUseBlock,
    Usage,
)
from .base import BaseProvider, ProviderRegistry, register_provider

try:
    import anthropic  # type: ignore[import-not-found]
    from anthropic import AsyncAnthropic

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    anthropic = None
    AsyncAnthropic = None


@register_provider("claude")
class ClaudeProvider(BaseProvider):
    """Anthropic Claude provider implementation."""

    name = "claude"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._client: Any = None

    def _validate_config(self) -> None:
        if not HAS_ANTHROPIC:
            raise ImportError(
                "anthropic package is required for Claude provider. "
                "Install it with: pip install anthropic"
            )

    def _get_client(self) -> Any:
        """Get or create the Anthropic client."""
        if self._client is None:
            api_key = self.config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise AuthenticationError(
                    "claude",
                    "ANTHROPIC_API_KEY environment variable or api_key config required",
                )

            self._client = AsyncAnthropic(
                api_key=api_key,
                base_url=self.config.get("base_url"),
                timeout=self.config.get("timeout", 600.0),
                max_retries=self.config.get("max_retries", 2),
            )
        return self._client

    def get_features(self) -> ProviderFeatures:
        return ProviderFeatures(
            streaming=True,
            tool_calling=True,
            vision=True,
            thinking=True,
            json_mode=True,
            max_context_length=200000,
            supports_system_message=True,
        )

    def get_default_model(self) -> str:
        return "claude-sonnet-4-20250514"

    # ==========================================================================
    # Message Formatting (SDK -> Anthropic)
    # ==========================================================================

    def format_messages(  # type: ignore[override]
        self, messages: list[Message]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert SDK messages to Anthropic format.

        Returns:
            Tuple of (system_prompt, messages_list)
        """
        system_prompt: str | None = None
        formatted: list[dict[str, Any]] = []

        from ..types import AssistantMessage, SystemMessage, ToolMessage, UserMessage

        for msg in messages:
            if isinstance(msg, SystemMessage):
                # Anthropic uses separate system parameter
                system_prompt = msg.content
            elif isinstance(msg, UserMessage):
                formatted.append(self._format_user_message(msg))
            elif isinstance(msg, AssistantMessage):
                formatted.append(self._format_assistant_message(msg))
            elif isinstance(msg, ToolMessage):
                # Anthropic expects tool results as user messages with tool_result content
                formatted.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id,
                                "content": msg.content,
                            }
                        ],
                    }
                )

        return system_prompt, formatted

    def _format_user_message(self, message: Any) -> dict[str, Any]:
        content = message.content
        if isinstance(content, str):
            return {"role": "user", "content": content}
        else:
            return {"role": "user", "content": self._format_content_blocks(content)}

    def _format_assistant_message(self, message: Any) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": self._format_content_blocks(message.content),
        }

    def _format_content_blocks(
        self, blocks: list[ContentBlock]
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for block in blocks:
            if isinstance(block, TextBlock):
                result.append({"type": "text", "text": block.text})
            elif isinstance(block, ImageBlock):
                # Anthropic image format
                if block.source.startswith("data:"):
                    # Base64 encoded
                    result.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": block.media_type,
                                "data": block.source.split(",", 1)[1]
                                if "," in block.source
                                else block.source,
                            },
                        }
                    )
                else:
                    # URL
                    result.append(
                        {
                            "type": "image",
                            "source": {"type": "url", "url": block.source},
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
                thinking_block: dict[str, Any] = {
                    "type": "thinking",
                    "thinking": block.thinking,
                }
                # Include signature if present (required for multi-turn conversations)
                if block.signature:
                    thinking_block["signature"] = block.signature
                result.append(thinking_block)
        return result

    def format_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
        """Convert tools to Anthropic format."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in tools
        ]

    # ==========================================================================
    # Response Parsing (Anthropic -> SDK)
    # ==========================================================================

    def parse_response(self, response: Any) -> AssistantMessage:
        """Parse Anthropic response to SDK AssistantMessage."""
        content_blocks: list[ContentBlock] = []

        for block in response.content:
            if block.type == "text":
                content_blocks.append(TextBlock(text=block.text))
            elif block.type == "tool_use":
                content_blocks.append(
                    ToolUseBlock(
                        id=block.id,
                        name=block.name,
                        input=block.input,
                    )
                )
            elif block.type == "thinking":
                content_blocks.append(
                    ThinkingBlock(
                        thinking=block.thinking,
                        signature=getattr(block, "signature", None),
                    )
                )

        # Map stop reason
        finish_reason = self._map_stop_reason(response.stop_reason)

        return AssistantMessage(
            content=content_blocks,
            model=response.model,
            finish_reason=finish_reason,
        )

    def _map_stop_reason(self, stop_reason: str | None) -> FinishReason | None:
        if stop_reason is None:
            return None
        mapping = {
            "end_turn": FinishReason.STOP,
            "max_tokens": FinishReason.LENGTH,
            "tool_use": FinishReason.TOOL_USE,
            "stop_sequence": FinishReason.STOP,
        }
        return mapping.get(stop_reason, FinishReason.STOP)

    def parse_usage(self, usage: Any) -> Usage:
        """Parse Anthropic usage to SDK Usage."""
        return Usage(
            prompt_tokens=getattr(usage, "input_tokens", 0),
            completion_tokens=getattr(usage, "output_tokens", 0),
            total_tokens=getattr(usage, "input_tokens", 0)
            + getattr(usage, "output_tokens", 0),
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", None),
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", None),
        )

    # ==========================================================================
    # Core Methods
    # ==========================================================================

    async def complete(
        self,
        messages: list[Message],
        options: AgentOptions,
    ) -> AssistantMessage:
        """Generate a completion using Claude."""
        client = self._get_client()

        system_prompt, formatted_messages = self.format_messages(messages)

        kwargs: dict[str, Any] = {
            "model": options.model or self.get_default_model(),
            "messages": formatted_messages,
            "max_tokens": options.max_tokens or 4096,
        }

        if system_prompt or options.system_prompt:
            kwargs["system"] = options.system_prompt or system_prompt

        if options.temperature is not None:
            kwargs["temperature"] = options.temperature

        if options.top_p is not None:
            kwargs["top_p"] = options.top_p

        if options.tools:
            kwargs["tools"] = self.format_tools(options.tools)
            if options.tool_choice:
                if options.tool_choice == "required":
                    kwargs["tool_choice"] = {"type": "any"}
                elif options.tool_choice == "none":
                    kwargs["tool_choice"] = {"type": "none"}
                elif options.tool_choice == "auto":
                    kwargs["tool_choice"] = {"type": "auto"}
                else:
                    kwargs["tool_choice"] = {
                        "type": "tool",
                        "name": options.tool_choice,
                    }

        if options.enable_thinking and options.max_thinking_tokens:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": options.max_thinking_tokens,
            }

        try:
            response = await client.messages.create(**kwargs)
            return self.parse_response(response)
        except anthropic.AuthenticationError as e:
            raise AuthenticationError("claude", str(e)) from e
        except anthropic.RateLimitError as e:
            raise RateLimitError("claude", message=str(e)) from e
        except anthropic.APIError as e:
            raise ProviderError(
                str(e),
                provider="claude",
                status_code=getattr(e, "status_code", None),
            ) from e

    async def stream(
        self,
        messages: list[Message],
        options: AgentOptions,
    ) -> AsyncIterator[AnyMessage]:
        """Stream a completion using Claude."""
        client = self._get_client()

        system_prompt, formatted_messages = self.format_messages(messages)

        kwargs: dict[str, Any] = {
            "model": options.model or self.get_default_model(),
            "messages": formatted_messages,
            "max_tokens": options.max_tokens or 4096,
        }

        if system_prompt or options.system_prompt:
            kwargs["system"] = options.system_prompt or system_prompt

        if options.temperature is not None:
            kwargs["temperature"] = options.temperature

        if options.top_p is not None:
            kwargs["top_p"] = options.top_p

        if options.tools:
            kwargs["tools"] = self.format_tools(options.tools)
            if options.tool_choice:
                if options.tool_choice == "required":
                    kwargs["tool_choice"] = {"type": "any"}
                elif options.tool_choice == "none":
                    kwargs["tool_choice"] = {"type": "none"}
                elif options.tool_choice == "auto":
                    kwargs["tool_choice"] = {"type": "auto"}
                else:
                    kwargs["tool_choice"] = {
                        "type": "tool",
                        "name": options.tool_choice,
                    }

        if options.enable_thinking and options.max_thinking_tokens:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": options.max_thinking_tokens,
            }

        try:
            # Collect content blocks during streaming
            content_blocks: list[ContentBlock] = []
            current_text = ""
            current_tool_use: dict[str, Any] | None = None
            current_thinking = ""
            current_thinking_signature = ""
            model = ""
            usage: Usage | None = None
            stop_reason: str | None = None

            async with client.messages.stream(**kwargs) as stream:
                async for event in stream:
                    if event.type == "message_start":
                        model = event.message.model
                        if hasattr(event.message, "usage"):
                            usage = self.parse_usage(event.message.usage)

                    elif event.type == "content_block_start":
                        block = event.content_block
                        if block.type == "text":
                            current_text = ""
                        elif block.type == "tool_use":
                            current_tool_use = {
                                "id": block.id,
                                "name": block.name,
                                "input": "",
                            }
                        elif block.type == "thinking":
                            current_thinking = ""

                        # Include tool name and id for tool_use blocks
                        delta_info = {"type": block.type}
                        if block.type == "tool_use":
                            delta_info["id"] = block.id
                            delta_info["name"] = block.name

                        yield StreamEvent(
                            event_type="content_block_start",
                            index=event.index,
                            delta=delta_info,
                        )

                    elif event.type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta":
                            current_text += delta.text
                            yield StreamEvent(
                                event_type="content_block_delta",
                                index=event.index,
                                delta={"type": "text_delta", "text": delta.text},
                            )
                        elif delta.type == "input_json_delta":
                            if current_tool_use:
                                current_tool_use["input"] += delta.partial_json
                            yield StreamEvent(
                                event_type="content_block_delta",
                                index=event.index,
                                delta={
                                    "type": "input_json_delta",
                                    "partial_json": delta.partial_json,
                                },
                            )
                        elif delta.type == "thinking_delta":
                            current_thinking += delta.thinking
                            yield StreamEvent(
                                event_type="content_block_delta",
                                index=event.index,
                                delta={"type": "thinking_delta", "thinking": delta.thinking},
                            )
                        elif delta.type == "signature_delta":
                            # Capture thinking signature for multi-turn conversations
                            current_thinking_signature = getattr(delta, "signature", "")
                            yield StreamEvent(
                                event_type="content_block_delta",
                                index=event.index,
                                delta={"type": "signature_delta", "signature": current_thinking_signature},
                            )

                    elif event.type == "content_block_stop":
                        # Finalize current block
                        if current_text:
                            content_blocks.append(TextBlock(text=current_text))
                            current_text = ""
                        elif current_tool_use:
                            import json

                            try:
                                input_data = json.loads(current_tool_use["input"])
                            except json.JSONDecodeError:
                                input_data = {}
                            content_blocks.append(
                                ToolUseBlock(
                                    id=current_tool_use["id"],
                                    name=current_tool_use["name"],
                                    input=input_data,
                                )
                            )
                            current_tool_use = None
                        elif current_thinking:
                            content_blocks.append(
                                ThinkingBlock(
                                    thinking=current_thinking,
                                    signature=current_thinking_signature or None,
                                )
                            )
                            current_thinking = ""
                            current_thinking_signature = ""

                        yield StreamEvent(
                            event_type="content_block_stop",
                            index=event.index,
                        )

                    elif event.type == "message_delta":
                        stop_reason = event.delta.stop_reason
                        if hasattr(event, "usage"):
                            usage = self.parse_usage(event.usage)

                    elif event.type == "message_stop":
                        pass

            # Yield final AssistantMessage
            yield AssistantMessage(
                content=content_blocks,
                model=model,
                finish_reason=self._map_stop_reason(stop_reason),
            )

            # Yield ResultMessage
            yield ResultMessage(
                is_error=False,
                usage=usage,
                finish_reason=self._map_stop_reason(stop_reason),
            )

        except anthropic.AuthenticationError as e:
            raise AuthenticationError("claude", str(e)) from e
        except anthropic.RateLimitError as e:
            raise RateLimitError("claude", message=str(e)) from e
        except anthropic.APIError as e:
            raise ProviderError(
                str(e),
                provider="claude",
                status_code=getattr(e, "status_code", None),
            ) from e


# Register "anthropic" as an alias for the Claude provider
ProviderRegistry.register("anthropic", ClaudeProvider)
