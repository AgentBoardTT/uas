"""One-shot query function for Universal Agent SDK."""

from collections.abc import AsyncIterator
from typing import Any

from .config import get_config
from .providers import ProviderRegistry
from .types import (
    AgentOptions,
    AnyMessage,
    AssistantMessage,
    Message,
    ResultMessage,
    SystemMessage,
    ToolMessage,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


async def query(
    prompt: str | list[Message],
    options: AgentOptions | None = None,
    **kwargs: Any,
) -> AsyncIterator[AnyMessage]:
    """Execute a one-shot query with an LLM provider.

    This is the simplest way to interact with an LLM. For multi-turn
    conversations, use UniversalAgentClient instead.

    Args:
        prompt: Either a string message or a list of Message objects
        options: AgentOptions for configuring the query
        **kwargs: Additional options to merge with AgentOptions

    Yields:
        Messages from the LLM including AssistantMessage, StreamEvent, and ResultMessage

    Example:
        Basic usage:
        ```python
        async for message in query("What is the capital of France?"):
            if isinstance(message, AssistantMessage):
                print(message.content[0].text)
        ```

        With options:
        ```python
        options = AgentOptions(
            provider="openai",
            model="gpt-4o",
            temperature=0.7,
        )
        async for message in query("Hello", options):
            print(message)
        ```

        With tools:
        ```python
        from universal_agent_sdk import tool

        @tool(
            name="get_weather",
            description="Get current weather",
            input_schema={"type": "object", "properties": {"city": {"type": "string"}}}
        )
        async def get_weather(city: str) -> str:
            return f"Weather in {city}: Sunny, 72F"

        options = AgentOptions(tools=[get_weather.definition])
        async for message in query("What's the weather in Paris?", options):
            print(message)
        ```
    """
    if options is None:
        options = AgentOptions()

    # Merge kwargs into options
    if kwargs:
        for key, value in kwargs.items():
            if hasattr(options, key):
                setattr(options, key, value)

    # Load config and get provider config if not provided
    config = get_config()
    provider_config = options.provider_config
    if provider_config is None:
        provider_config = config.get_provider_config(options.provider)

    # Get provider
    provider = ProviderRegistry.get(options.provider, provider_config)

    # Build messages
    messages: list[Message] = []

    if options.system_prompt:
        messages.append(SystemMessage(content=options.system_prompt))

    if isinstance(prompt, str):
        messages.append(UserMessage(content=prompt))
    else:
        messages.extend(prompt)

    # Execute with tool loop if tools are configured
    if options.tools:
        async for msg in _query_with_tools(provider, messages, options):
            yield msg
    else:
        # Simple query without tools
        if options.stream:
            async for msg in provider.stream(messages, options):
                yield msg
        else:
            result = await provider.complete(messages, options)
            yield result
            yield ResultMessage(is_error=False, finish_reason=result.finish_reason)


async def _query_with_tools(
    provider: Any,
    messages: list[Message],
    options: AgentOptions,
) -> AsyncIterator[AnyMessage]:
    """Execute query with automatic tool execution loop."""
    turns = 0
    max_turns = options.max_turns or 10

    while turns < max_turns:
        turns += 1

        # Get response from provider
        if options.stream:
            response: AssistantMessage | None = None
            async for msg in provider.stream(messages, options):
                yield msg
                if isinstance(msg, AssistantMessage):
                    response = msg
        else:
            response = await provider.complete(messages, options)
            yield response

        if response is None:
            break

        # Check for tool use
        tool_uses = [
            block for block in response.content if isinstance(block, ToolUseBlock)
        ]

        if not tool_uses:
            # No tool calls, we're done
            if not options.stream:
                yield ResultMessage(is_error=False, num_turns=turns)
            break

        # Execute tools
        messages.append(response)
        tool_results: list[ToolResultBlock] = []

        for tool_use in tool_uses:
            # Check permission callback
            if options.can_use_tool:
                from .types import (
                    PermissionResult,
                    PermissionResultDeny,
                    ToolPermissionContext,
                )

                context = ToolPermissionContext(session_id=options.session_id)
                perm_result_raw = options.can_use_tool(
                    tool_use.name, tool_use.input, context
                )
                perm_result: PermissionResult
                if hasattr(perm_result_raw, "__await__"):
                    perm_result = await perm_result_raw
                else:
                    perm_result = perm_result_raw  # type: ignore[assignment]

                if isinstance(perm_result, PermissionResultDeny):
                    tool_results.append(
                        ToolResultBlock(
                            tool_use_id=tool_use.id,
                            content=f"Permission denied: {perm_result.message}",
                            is_error=True,
                        )
                    )
                    continue

            # Find and execute tool
            tool_def = next((t for t in options.tools if t.name == tool_use.name), None)

            if tool_def is None or tool_def.handler is None:
                tool_results.append(
                    ToolResultBlock(
                        tool_use_id=tool_use.id,
                        content=f"Tool '{tool_use.name}' not found or has no handler",
                        is_error=True,
                    )
                )
                continue

            try:
                # Execute tool handler
                tool_result = tool_def.handler(**tool_use.input)
                if hasattr(tool_result, "__await__"):
                    tool_result = await tool_result

                # Convert result to string
                if isinstance(tool_result, str):
                    content = tool_result
                else:
                    import json

                    content = json.dumps(tool_result)

                tool_results.append(
                    ToolResultBlock(
                        tool_use_id=tool_use.id,
                        content=content,
                        is_error=False,
                    )
                )
            except Exception as e:
                tool_results.append(
                    ToolResultBlock(
                        tool_use_id=tool_use.id,
                        content=f"Error executing tool: {e!s}",
                        is_error=True,
                    )
                )

        # Add tool results to messages
        # For providers that expect tool messages (OpenAI style)
        for result in tool_results:
            # Convert content to string if needed
            content_str: str
            if result.content is None:
                content_str = ""
            elif isinstance(result.content, str):
                content_str = result.content
            else:
                import json

                content_str = json.dumps(result.content)

            messages.append(
                ToolMessage(
                    content=content_str,
                    tool_call_id=result.tool_use_id,
                )
            )

    # Final result message if we hit max turns
    if turns >= max_turns:
        yield ResultMessage(is_error=False, num_turns=turns)


async def complete(
    prompt: str | list[Message],
    options: AgentOptions | None = None,
    **kwargs: Any,
) -> AssistantMessage:
    """Execute a one-shot completion and return the final response.

    This is a convenience function that collects all messages and returns
    just the final AssistantMessage.

    Args:
        prompt: Either a string message or a list of Message objects
        options: AgentOptions for configuring the query
        **kwargs: Additional options

    Returns:
        The final AssistantMessage from the query

    Example:
        ```python
        response = await complete("What is 2 + 2?")
        print(response.content[0].text)
        ```
    """
    response: AssistantMessage | None = None
    async for msg in query(prompt, options, **kwargs):
        if isinstance(msg, AssistantMessage):
            response = msg

    if response is None:
        raise RuntimeError("No response received from provider")

    return response
