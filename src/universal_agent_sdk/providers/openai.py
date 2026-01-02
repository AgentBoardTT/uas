"""OpenAI provider implementation."""

import json
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
    ToolDefinition,
    ToolUseBlock,
    Usage,
)
from .base import BaseProvider, register_provider

try:
    import openai  # type: ignore[import-not-found]
    from openai import AsyncOpenAI

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    openai = None
    AsyncOpenAI = None


@register_provider("openai")
class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""

    name = "openai"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._client: Any = None

    def _validate_config(self) -> None:
        if not HAS_OPENAI:
            raise ImportError(
                "openai package is required for OpenAI provider. "
                "Install it with: pip install openai"
            )

    def _get_client(self) -> Any:
        """Get or create the OpenAI client."""
        if self._client is None:
            api_key = self.config.get("api_key") or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise AuthenticationError(
                    "openai",
                    "OPENAI_API_KEY environment variable or api_key config required",
                )

            kwargs: dict[str, Any] = {
                "api_key": api_key,
                "timeout": self.config.get("timeout", 600.0),
                "max_retries": self.config.get("max_retries", 2),
            }

            if self.config.get("base_url"):
                kwargs["base_url"] = self.config["base_url"]
            if self.config.get("organization"):
                kwargs["organization"] = self.config["organization"]

            self._client = AsyncOpenAI(**kwargs)
        return self._client

    def get_features(self) -> ProviderFeatures:
        return ProviderFeatures(
            streaming=True,
            tool_calling=True,
            vision=True,
            thinking=False,  # OpenAI doesn't have explicit thinking blocks
            json_mode=True,
            max_context_length=128000,
            supports_system_message=True,
        )

    def get_default_model(self) -> str:
        return "gpt-4o"

    # ==========================================================================
    # Message Formatting (SDK -> OpenAI)
    # ==========================================================================

    def format_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert SDK messages to OpenAI format."""
        from ..types import AssistantMessage, SystemMessage, ToolMessage, UserMessage

        formatted: list[dict[str, Any]] = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted.append({"role": "system", "content": msg.content})
            elif isinstance(msg, UserMessage):
                formatted.append(self._format_user_message(msg))
            elif isinstance(msg, AssistantMessage):
                formatted.append(self._format_assistant_message(msg))
            elif isinstance(msg, ToolMessage):
                formatted.append(
                    {
                        "role": "tool",
                        "content": msg.content,
                        "tool_call_id": msg.tool_call_id,
                    }
                )

        return formatted

    def _format_user_message(self, message: Any) -> dict[str, Any]:
        content = message.content
        if isinstance(content, str):
            return {"role": "user", "content": content}
        else:
            return {"role": "user", "content": self._format_content_blocks(content)}

    def _format_assistant_message(self, message: Any) -> dict[str, Any]:
        # Check if there are tool uses
        tool_calls = []
        text_content = ""

        for block in message.content:
            if isinstance(block, TextBlock):
                text_content += block.text
            elif isinstance(block, ToolUseBlock):
                tool_calls.append(
                    {
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": json.dumps(block.input),
                        },
                    }
                )

        result: dict[str, Any] = {"role": "assistant"}

        if text_content:
            result["content"] = text_content

        if tool_calls:
            result["tool_calls"] = tool_calls

        return result

    def _format_content_blocks(
        self, blocks: list[ContentBlock]
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for block in blocks:
            if isinstance(block, TextBlock):
                result.append({"type": "text", "text": block.text})
            elif isinstance(block, ImageBlock):
                # OpenAI image format
                if block.source.startswith("data:"):
                    result.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": block.source},
                        }
                    )
                else:
                    result.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": block.source},
                        }
                    )
        return result

    def format_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
        """Convert tools to OpenAI format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in tools
        ]

    # ==========================================================================
    # Response Parsing (OpenAI -> SDK)
    # ==========================================================================

    def parse_response(self, response: Any) -> AssistantMessage:
        """Parse OpenAI response to SDK AssistantMessage."""
        choice = response.choices[0]
        message = choice.message

        content_blocks: list[ContentBlock] = []

        # Add text content if present
        if message.content:
            content_blocks.append(TextBlock(text=message.content))

        # Add tool calls if present
        if message.tool_calls:
            for tool_call in message.tool_calls:
                content_blocks.append(
                    ToolUseBlock(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        input=json.loads(tool_call.function.arguments),
                    )
                )

        # Map finish reason
        finish_reason = self._map_finish_reason(choice.finish_reason)

        return AssistantMessage(
            content=content_blocks,
            model=response.model,
            finish_reason=finish_reason,
        )

    def _map_finish_reason(self, finish_reason: str | None) -> FinishReason | None:
        if finish_reason is None:
            return None
        mapping = {
            "stop": FinishReason.STOP,
            "length": FinishReason.LENGTH,
            "tool_calls": FinishReason.TOOL_USE,
            "content_filter": FinishReason.CONTENT_FILTER,
        }
        return mapping.get(finish_reason, FinishReason.STOP)

    def parse_usage(self, usage: Any) -> Usage:
        """Parse OpenAI usage to SDK Usage."""
        return Usage(
            prompt_tokens=getattr(usage, "prompt_tokens", 0),
            completion_tokens=getattr(usage, "completion_tokens", 0),
            total_tokens=getattr(usage, "total_tokens", 0),
        )

    # ==========================================================================
    # Core Methods
    # ==========================================================================

    async def complete(
        self,
        messages: list[Message],
        options: AgentOptions,
    ) -> AssistantMessage:
        """Generate a completion using OpenAI."""
        client = self._get_client()

        formatted_messages = self.format_messages(messages)

        kwargs: dict[str, Any] = {
            "model": options.model or self.get_default_model(),
            "messages": formatted_messages,
        }

        if options.max_tokens:
            kwargs["max_tokens"] = options.max_tokens

        if options.temperature is not None:
            kwargs["temperature"] = options.temperature

        if options.top_p is not None:
            kwargs["top_p"] = options.top_p

        if options.tools:
            kwargs["tools"] = self.format_tools(options.tools)
            if options.tool_choice:
                if options.tool_choice == "required":
                    kwargs["tool_choice"] = "required"
                elif options.tool_choice == "none":
                    kwargs["tool_choice"] = "none"
                elif options.tool_choice == "auto":
                    kwargs["tool_choice"] = "auto"
                else:
                    kwargs["tool_choice"] = {
                        "type": "function",
                        "function": {"name": options.tool_choice},
                    }

        try:
            response = await client.chat.completions.create(**kwargs)
            return self.parse_response(response)
        except openai.AuthenticationError as e:
            raise AuthenticationError("openai", str(e)) from e
        except openai.RateLimitError as e:
            raise RateLimitError("openai", message=str(e)) from e
        except openai.APIError as e:
            raise ProviderError(
                str(e),
                provider="openai",
                status_code=getattr(e, "status_code", None),
            ) from e

    async def stream(
        self,
        messages: list[Message],
        options: AgentOptions,
    ) -> AsyncIterator[AnyMessage]:
        """Stream a completion using OpenAI."""
        client = self._get_client()

        formatted_messages = self.format_messages(messages)

        kwargs: dict[str, Any] = {
            "model": options.model or self.get_default_model(),
            "messages": formatted_messages,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        if options.max_tokens:
            kwargs["max_tokens"] = options.max_tokens

        if options.temperature is not None:
            kwargs["temperature"] = options.temperature

        if options.top_p is not None:
            kwargs["top_p"] = options.top_p

        if options.tools:
            kwargs["tools"] = self.format_tools(options.tools)
            if options.tool_choice:
                if options.tool_choice == "required":
                    kwargs["tool_choice"] = "required"
                elif options.tool_choice == "none":
                    kwargs["tool_choice"] = "none"
                elif options.tool_choice == "auto":
                    kwargs["tool_choice"] = "auto"
                else:
                    kwargs["tool_choice"] = {
                        "type": "function",
                        "function": {"name": options.tool_choice},
                    }

        try:
            # Track content during streaming
            content_text = ""
            tool_calls: dict[int, dict[str, Any]] = {}
            model = ""
            usage: Usage | None = None
            finish_reason: str | None = None

            async with await client.chat.completions.create(**kwargs) as stream:
                async for chunk in stream:
                    if not chunk.choices:
                        # Usage chunk at the end
                        if chunk.usage:
                            usage = self.parse_usage(chunk.usage)
                        continue

                    choice = chunk.choices[0]
                    delta = choice.delta

                    if chunk.model:
                        model = chunk.model

                    # Handle text content
                    if delta.content:
                        content_text += delta.content
                        yield StreamEvent(
                            event_type="content_block_delta",
                            delta={"type": "text", "text": delta.content},
                        )

                    # Handle tool calls
                    if delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            idx = tool_call.index
                            if idx not in tool_calls:
                                tool_calls[idx] = {
                                    "id": tool_call.id or "",
                                    "name": "",
                                    "arguments": "",
                                }

                            if tool_call.id:
                                tool_calls[idx]["id"] = tool_call.id
                            if tool_call.function:
                                if tool_call.function.name:
                                    tool_calls[idx]["name"] = tool_call.function.name
                                if tool_call.function.arguments:
                                    tool_calls[idx]["arguments"] += (
                                        tool_call.function.arguments
                                    )

                            yield StreamEvent(
                                event_type="tool_call_delta",
                                index=idx,
                                delta={
                                    "type": "tool_call",
                                    "id": tool_call.id,
                                    "name": tool_call.function.name
                                    if tool_call.function
                                    else None,
                                    "arguments": tool_call.function.arguments
                                    if tool_call.function
                                    else None,
                                },
                            )

                    if choice.finish_reason:
                        finish_reason = choice.finish_reason

            # Build content blocks
            content_blocks: list[ContentBlock] = []
            if content_text:
                content_blocks.append(TextBlock(text=content_text))

            for _, tc in sorted(tool_calls.items()):
                try:
                    input_data = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    input_data = {}
                content_blocks.append(
                    ToolUseBlock(
                        id=tc["id"],
                        name=tc["name"],
                        input=input_data,
                    )
                )

            # Yield final AssistantMessage
            yield AssistantMessage(
                content=content_blocks,
                model=model,
                finish_reason=self._map_finish_reason(finish_reason),
            )

            # Yield ResultMessage
            yield ResultMessage(
                is_error=False,
                usage=usage,
                finish_reason=self._map_finish_reason(finish_reason),
            )

        except openai.AuthenticationError as e:
            raise AuthenticationError("openai", str(e)) from e
        except openai.RateLimitError as e:
            raise RateLimitError("openai", message=str(e)) from e
        except openai.APIError as e:
            raise ProviderError(
                str(e),
                provider="openai",
                status_code=getattr(e, "status_code", None),
            ) from e


@register_provider("azure_openai")
class AzureOpenAIProvider(OpenAIProvider):
    """Azure OpenAI provider implementation."""

    name = "azure_openai"

    def _get_client(self) -> Any:
        """Get or create the Azure OpenAI client."""
        if self._client is None:
            from openai import AsyncAzureOpenAI

            api_key = self.config.get("api_key") or os.environ.get(
                "AZURE_OPENAI_API_KEY"
            )
            endpoint = self.config.get("base_url") or os.environ.get(
                "AZURE_OPENAI_ENDPOINT"
            )
            api_version = self.config.get("api_version", "2024-02-15-preview")

            if not api_key:
                raise AuthenticationError(
                    "azure_openai",
                    "AZURE_OPENAI_API_KEY environment variable or api_key config required",
                )
            if not endpoint:
                raise AuthenticationError(
                    "azure_openai",
                    "AZURE_OPENAI_ENDPOINT environment variable or base_url config required",
                )

            kwargs: dict[str, Any] = {
                "api_key": api_key,
                "azure_endpoint": endpoint,
                "api_version": api_version,
                "timeout": self.config.get("timeout", 600.0),
                "max_retries": self.config.get("max_retries", 2),
            }

            # Support Azure AD token authentication
            if self.config.get("azure_ad_token"):
                kwargs["azure_ad_token"] = self.config["azure_ad_token"]

            self._client = AsyncAzureOpenAI(**kwargs)
        return self._client

    def get_default_model(self) -> str:
        # Azure uses deployment names, not model names
        return str(self.config.get("deployment_name", "gpt-4o"))
