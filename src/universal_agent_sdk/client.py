"""Universal Agent Client for multi-turn conversations."""

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any

from .config import get_config
from .providers import BaseProvider, ProviderRegistry
from .types import (
    AgentOptions,
    AnyMessage,
    AssistantMessage,
    HookContext,
    HookEvent,
    HookInput,
    HookOutput,
    Message,
    OnErrorHookInput,
    PostToolUseHookInput,
    PreToolUseHookInput,
    ResultMessage,
    SessionStartHookInput,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ToolMessage,
    ToolUseBlock,
    UserMessage,
)

logger = logging.getLogger(__name__)


class UniversalAgentClient:
    """
    Client for multi-turn, interactive conversations with LLMs.

    This client maintains conversation state and provides full control
    over the conversation flow. For simple one-shot queries, use the
    query() function instead.

    Features:
        - Multi-turn conversations with memory
        - Streaming responses
        - Tool execution
        - Provider switching mid-conversation
        - Session management

    Example:
        ```python
        async with UniversalAgentClient() as client:
            # First turn
            await client.send("Hello, I'm working on a Python project.")
            async for msg in client.receive():
                print(msg)

            # Follow-up (context is maintained)
            await client.send("Can you help me write a test?")
            async for msg in client.receive():
                print(msg)
        ```
    """

    def __init__(
        self,
        options: AgentOptions | None = None,
    ):
        """Initialize the Universal Agent Client.

        Args:
            options: Configuration options for the client
        """
        self.options = options or AgentOptions()
        self._provider: BaseProvider | None = None
        self._messages: list[Message] = []
        self._session_id = self.options.session_id or str(uuid.uuid4())
        self._connected = False
        self._pending_response: AsyncIterator[AnyMessage] | None = None

    @property
    def session_id(self) -> str:
        """Get the current session ID."""
        return self._session_id

    @property
    def messages(self) -> list[Message]:
        """Get the conversation history."""
        return self._messages.copy()

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._connected

    async def _execute_hooks(
        self,
        event: HookEvent,
        input_data: HookInput,
        tool_use_id: str | None = None,
        tool_name: str | None = None,
    ) -> HookOutput:
        """Execute all matching hooks for an event.

        Args:
            event: The hook event type
            input_data: Input data for the hooks
            tool_use_id: Optional tool use ID for tool-related hooks
            tool_name: Optional tool name for matching

        Returns:
            Combined HookOutput from all hooks
        """
        if not self.options.hooks or event not in self.options.hooks:
            return {}

        matchers = self.options.hooks[event]
        combined_output: HookOutput = {}
        context: HookContext = {
            "session_id": self._session_id,
            "tool_use_id": tool_use_id,
        }

        for matcher in matchers:
            # Check if matcher matches this tool/event
            # Skip if matcher is set, tool_name is set, and they don't match
            if (
                matcher.matcher is not None
                and tool_name is not None
                and matcher.matcher != tool_name
            ):
                continue

            # Execute all hooks in this matcher
            for hook in matcher.hooks:
                try:
                    if matcher.timeout:
                        output = await asyncio.wait_for(
                            hook(input_data, tool_use_id, context),
                            timeout=matcher.timeout,
                        )
                    else:
                        output = await hook(input_data, tool_use_id, context)

                    # Merge outputs (later hooks override earlier ones)
                    if output:
                        combined_output.update(output)

                        # Check for immediate stop
                        if output.get("continue_") is False:
                            return combined_output

                except asyncio.TimeoutError:
                    logger.warning(f"Hook timed out for event {event}")
                except Exception as e:
                    logger.error(f"Hook error for event {event}: {e}")

        return combined_output

    async def connect(self) -> None:
        """Connect to the LLM provider.

        This initializes the provider and prepares the client for conversations.
        """
        if self._connected:
            return

        # Load config and get provider config if not provided
        config = get_config()
        provider_config = self.options.provider_config
        if provider_config is None:
            provider_config = config.get_provider_config(self.options.provider)

        self._provider = ProviderRegistry.get(self.options.provider, provider_config)

        # Add system prompt if configured
        if self.options.system_prompt:
            self._messages.append(SystemMessage(content=self.options.system_prompt))

        self._connected = True

        # Execute SessionStart hooks
        session_start_input: SessionStartHookInput = {
            "session_id": self._session_id,
            "hook_event_name": "SessionStart",
        }
        hook_output = await self._execute_hooks("SessionStart", session_start_input)

        # Add additional context from hook if provided
        hook_specific = hook_output.get("hookSpecificOutput")
        if hook_specific is not None:
            additional_context = hook_specific.get("additionalContext")
            if additional_context:
                self._messages.append(SystemMessage(content=additional_context))

    async def disconnect(self) -> None:
        """Disconnect from the LLM provider."""
        self._connected = False
        self._provider = None
        self._pending_response = None

    async def send(self, message: str | Message) -> None:
        """Send a message to the LLM.

        Args:
            message: Either a string or a Message object

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or self._provider is None:
            raise RuntimeError("Not connected. Call connect() first.")

        # Convert string to UserMessage
        user_msg = UserMessage(content=message) if isinstance(message, str) else message

        self._messages.append(user_msg)

        # Start the response generation
        if self.options.stream:
            self._pending_response = self._stream_with_tools()
        else:
            self._pending_response = self._complete_with_tools()

    async def receive(self) -> AsyncIterator[AnyMessage]:
        """Receive messages from the LLM.

        Yields messages until a ResultMessage is received.

        Yields:
            Messages from the LLM

        Raises:
            RuntimeError: If no pending response
        """
        if self._pending_response is None:
            raise RuntimeError("No pending response. Call send() first.")

        async for msg in self._pending_response:
            yield msg
            if isinstance(msg, ResultMessage):
                self._pending_response = None
                return

    async def receive_all(self) -> list[AnyMessage]:
        """Receive all messages from the current response.

        Returns:
            List of all messages from the response
        """
        messages: list[AnyMessage] = []
        async for msg in self.receive():
            messages.append(msg)
        return messages

    async def query(self, message: str | Message) -> AsyncIterator[AnyMessage]:
        """Send a message and receive the response.

        This is a convenience method that combines send() and receive().

        Args:
            message: The message to send

        Yields:
            Messages from the LLM
        """
        await self.send(message)
        async for msg in self.receive():
            yield msg

    async def _stream_with_tools(self) -> AsyncIterator[AnyMessage]:
        """Stream response with tool execution."""
        assert self._provider is not None

        turns = 0
        max_turns = self.options.max_turns or 10

        while turns < max_turns:
            turns += 1

            response: AssistantMessage | None = None
            async for msg in self._provider.stream(self._messages, self.options):
                # Don't yield ResultMessage from provider - we'll yield our own after tool execution
                if isinstance(msg, ResultMessage):
                    continue
                yield msg
                if isinstance(msg, AssistantMessage):
                    response = msg

            if response is None:
                break

            # Check for tool use
            tool_uses = [
                block for block in response.content if isinstance(block, ToolUseBlock)
            ]

            if not tool_uses:
                yield ResultMessage(
                    is_error=False, num_turns=turns, session_id=self._session_id
                )
                break

            # Add assistant message to history
            self._messages.append(response)

            # Execute tools and yield events for each
            should_continue = True
            async for event in self._execute_tools_with_events(tool_uses):
                if isinstance(event, StreamEvent):
                    yield event
                elif isinstance(event, bool):
                    should_continue = event
            if not should_continue:
                yield ResultMessage(
                    is_error=False, num_turns=turns, session_id=self._session_id
                )
                break

        if turns >= max_turns:
            yield ResultMessage(
                is_error=False, num_turns=turns, session_id=self._session_id
            )

    async def _complete_with_tools(self) -> AsyncIterator[AnyMessage]:
        """Complete response with tool execution."""
        assert self._provider is not None

        turns = 0
        max_turns = self.options.max_turns or 10

        while turns < max_turns:
            turns += 1

            response = await self._provider.complete(self._messages, self.options)
            yield response

            # Check for tool use
            tool_uses = [
                block for block in response.content if isinstance(block, ToolUseBlock)
            ]

            if not tool_uses:
                yield ResultMessage(
                    is_error=False, num_turns=turns, session_id=self._session_id
                )
                break

            # Add assistant message to history
            self._messages.append(response)

            # Execute tools and add results
            should_continue = await self._execute_tools(tool_uses)
            if not should_continue:
                yield ResultMessage(
                    is_error=False, num_turns=turns, session_id=self._session_id
                )
                break

        if turns >= max_turns:
            yield ResultMessage(
                is_error=False, num_turns=turns, session_id=self._session_id
            )

    async def _execute_tools(self, tool_uses: list[ToolUseBlock]) -> bool:
        """Execute tools and add results to message history.

        Args:
            tool_uses: List of tool use blocks to execute

        Returns:
            True if execution should continue, False if stopped by hook
        """
        for tool_use in tool_uses:
            # Execute PreToolUse hooks
            pre_tool_input: PreToolUseHookInput = {
                "session_id": self._session_id,
                "hook_event_name": "PreToolUse",
                "tool_name": tool_use.name,
                "tool_input": tool_use.input,
            }
            pre_hook_output = await self._execute_hooks(
                "PreToolUse",
                pre_tool_input,
                tool_use_id=tool_use.id,
                tool_name=tool_use.name,
            )

            # Check if hook wants to stop execution
            if pre_hook_output.get("continue_") is False:
                stop_reason = pre_hook_output.get(
                    "stopReason", "Stopped by PreToolUse hook"
                )
                logger.info(f"Execution stopped: {stop_reason}")
                return False

            # Check permission decision from hook
            hook_specific = pre_hook_output.get("hookSpecificOutput") or {}
            permission_decision = hook_specific.get("permissionDecision")
            if permission_decision == "deny":
                reason = hook_specific.get(
                    "permissionDecisionReason", "Denied by PreToolUse hook"
                )
                self._messages.append(
                    ToolMessage(
                        content=f"Permission denied: {reason}",
                        tool_call_id=tool_use.id,
                    )
                )
                continue

            # Check permission callback (fallback if no hook decision)
            if self.options.can_use_tool and not permission_decision:
                from .types import (
                    PermissionResult,
                    PermissionResultDeny,
                    ToolPermissionContext,
                )

                context = ToolPermissionContext(session_id=self._session_id)
                perm_result_raw = self.options.can_use_tool(
                    tool_use.name, tool_use.input, context
                )
                perm_result: PermissionResult
                if hasattr(perm_result_raw, "__await__"):
                    perm_result = await perm_result_raw
                else:
                    perm_result = perm_result_raw  # type: ignore[assignment]

                if isinstance(perm_result, PermissionResultDeny):
                    self._messages.append(
                        ToolMessage(
                            content=f"Permission denied: {perm_result.message}",
                            tool_call_id=tool_use.id,
                        )
                    )
                    continue

            # Find tool definition
            tool_def = next(
                (t for t in self.options.tools if t.name == tool_use.name), None
            )

            if tool_def is None or tool_def.handler is None:
                self._messages.append(
                    ToolMessage(
                        content=f"Tool '{tool_use.name}' not found or has no handler",
                        tool_call_id=tool_use.id,
                    )
                )
                continue

            # Use modified input from hook if provided
            tool_input = pre_hook_output.get("modified_input") or tool_use.input

            try:
                # Execute tool handler
                tool_result = tool_def.handler(**tool_input)
                if hasattr(tool_result, "__await__"):
                    tool_result = await tool_result

                # Convert result to string
                if isinstance(tool_result, str):
                    content = tool_result
                else:
                    import json

                    content = json.dumps(tool_result)

                # Execute PostToolUse hooks
                post_tool_input: PostToolUseHookInput = {
                    "session_id": self._session_id,
                    "hook_event_name": "PostToolUse",
                    "tool_name": tool_use.name,
                    "tool_input": tool_input,
                    "tool_response": content,
                }
                post_hook_output = await self._execute_hooks(
                    "PostToolUse",
                    post_tool_input,
                    tool_use_id=tool_use.id,
                    tool_name=tool_use.name,
                )

                # Check if hook wants to stop execution
                if post_hook_output.get("continue_") is False:
                    stop_reason = post_hook_output.get(
                        "stopReason", "Stopped by PostToolUse hook"
                    )
                    logger.info(f"Execution stopped: {stop_reason}")
                    self._messages.append(
                        ToolMessage(content=content, tool_call_id=tool_use.id)
                    )
                    return False

                # Add additional context from PostToolUse hook
                post_specific = post_hook_output.get("hookSpecificOutput") or {}
                additional_context = post_specific.get("additionalContext")
                if additional_context:
                    content += f"\n\n[Hook note: {additional_context}]"

                self._messages.append(
                    ToolMessage(content=content, tool_call_id=tool_use.id)
                )

            except Exception as e:
                # Execute OnError hook
                error_input: OnErrorHookInput = {
                    "session_id": self._session_id,
                    "hook_event_name": "OnError",
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
                await self._execute_hooks(
                    "OnError",
                    error_input,
                    tool_use_id=tool_use.id,
                    tool_name=tool_use.name,
                )

                self._messages.append(
                    ToolMessage(
                        content=f"Error executing tool: {e!s}",
                        tool_call_id=tool_use.id,
                    )
                )

        return True

    async def _execute_tools_with_events(
        self, tool_uses: list[ToolUseBlock]
    ) -> AsyncIterator[StreamEvent | bool]:
        """Execute tools and yield events for each execution.

        Args:
            tool_uses: List of tool use blocks to execute

        Yields:
            StreamEvent for tool execution start/complete, or bool for continue status
        """
        import json as json_module
        import time

        for tool_use in tool_uses:
            start_time = time.time()

            # Yield tool execution start event
            yield StreamEvent(
                event_type="tool_execution_start",
                delta={
                    "type": "tool_execution_start",
                    "tool_use_id": tool_use.id,
                    "tool_name": tool_use.name,
                    "tool_input": tool_use.input,
                },
            )

            # Execute PreToolUse hooks
            pre_tool_input: PreToolUseHookInput = {
                "session_id": self._session_id,
                "hook_event_name": "PreToolUse",
                "tool_name": tool_use.name,
                "tool_input": tool_use.input,
            }
            pre_hook_output = await self._execute_hooks(
                "PreToolUse",
                pre_tool_input,
                tool_use_id=tool_use.id,
                tool_name=tool_use.name,
            )

            # Check if hook wants to stop execution
            if pre_hook_output.get("continue_") is False:
                stop_reason = pre_hook_output.get(
                    "stopReason", "Stopped by PreToolUse hook"
                )
                logger.info(f"Execution stopped: {stop_reason}")
                yield StreamEvent(
                    event_type="tool_execution_complete",
                    delta={
                        "type": "tool_execution_error",
                        "tool_use_id": tool_use.id,
                        "tool_name": tool_use.name,
                        "error": stop_reason,
                        "duration_ms": int((time.time() - start_time) * 1000),
                    },
                )
                yield False
                return

            # Check permission decision from hook
            hook_specific = pre_hook_output.get("hookSpecificOutput") or {}
            permission_decision = hook_specific.get("permissionDecision")
            if permission_decision == "deny":
                reason = hook_specific.get(
                    "permissionDecisionReason", "Denied by PreToolUse hook"
                )
                self._messages.append(
                    ToolMessage(
                        content=f"Permission denied: {reason}",
                        tool_call_id=tool_use.id,
                    )
                )
                yield StreamEvent(
                    event_type="tool_execution_complete",
                    delta={
                        "type": "tool_execution_error",
                        "tool_use_id": tool_use.id,
                        "tool_name": tool_use.name,
                        "error": f"Permission denied: {reason}",
                        "duration_ms": int((time.time() - start_time) * 1000),
                    },
                )
                continue

            # Check permission callback (fallback if no hook decision)
            if self.options.can_use_tool and not permission_decision:
                from .types import (
                    PermissionResult,
                    PermissionResultDeny,
                    ToolPermissionContext,
                )

                context = ToolPermissionContext(session_id=self._session_id)
                perm_result_raw = self.options.can_use_tool(
                    tool_use.name, tool_use.input, context
                )
                perm_result: PermissionResult
                if hasattr(perm_result_raw, "__await__"):
                    perm_result = await perm_result_raw
                else:
                    perm_result = perm_result_raw  # type: ignore[assignment]

                if isinstance(perm_result, PermissionResultDeny):
                    self._messages.append(
                        ToolMessage(
                            content=f"Permission denied: {perm_result.message}",
                            tool_call_id=tool_use.id,
                        )
                    )
                    yield StreamEvent(
                        event_type="tool_execution_complete",
                        delta={
                            "type": "tool_execution_error",
                            "tool_use_id": tool_use.id,
                            "tool_name": tool_use.name,
                            "error": f"Permission denied: {perm_result.message}",
                            "duration_ms": int((time.time() - start_time) * 1000),
                        },
                    )
                    continue

            # Find tool definition
            tool_def = next(
                (t for t in self.options.tools if t.name == tool_use.name), None
            )

            if tool_def is None or tool_def.handler is None:
                self._messages.append(
                    ToolMessage(
                        content=f"Tool '{tool_use.name}' not found or has no handler",
                        tool_call_id=tool_use.id,
                    )
                )
                yield StreamEvent(
                    event_type="tool_execution_complete",
                    delta={
                        "type": "tool_execution_error",
                        "tool_use_id": tool_use.id,
                        "tool_name": tool_use.name,
                        "error": f"Tool '{tool_use.name}' not found",
                        "duration_ms": int((time.time() - start_time) * 1000),
                    },
                )
                continue

            # Use modified input from hook if provided
            tool_input = pre_hook_output.get("modified_input") or tool_use.input

            try:
                # Execute tool handler
                tool_result = tool_def.handler(**tool_input)
                if hasattr(tool_result, "__await__"):
                    tool_result = await tool_result

                # Convert result to string
                if isinstance(tool_result, str):
                    content = tool_result
                else:
                    content = json_module.dumps(tool_result)

                # Execute PostToolUse hooks
                post_tool_input: PostToolUseHookInput = {
                    "session_id": self._session_id,
                    "hook_event_name": "PostToolUse",
                    "tool_name": tool_use.name,
                    "tool_input": tool_input,
                    "tool_response": content,
                }
                post_hook_output = await self._execute_hooks(
                    "PostToolUse",
                    post_tool_input,
                    tool_use_id=tool_use.id,
                    tool_name=tool_use.name,
                )

                # Check if hook wants to stop execution
                if post_hook_output.get("continue_") is False:
                    stop_reason = post_hook_output.get(
                        "stopReason", "Stopped by PostToolUse hook"
                    )
                    logger.info(f"Execution stopped: {stop_reason}")
                    self._messages.append(
                        ToolMessage(content=content, tool_call_id=tool_use.id)
                    )
                    yield StreamEvent(
                        event_type="tool_execution_complete",
                        delta={
                            "type": "tool_execution_complete",
                            "tool_use_id": tool_use.id,
                            "tool_name": tool_use.name,
                            "output": content[:500] if len(content) > 500 else content,
                            "duration_ms": int((time.time() - start_time) * 1000),
                        },
                    )
                    yield False
                    return

                # Add additional context from PostToolUse hook
                post_specific = post_hook_output.get("hookSpecificOutput") or {}
                additional_context = post_specific.get("additionalContext")
                if additional_context:
                    content += f"\n\n[Hook note: {additional_context}]"

                self._messages.append(
                    ToolMessage(content=content, tool_call_id=tool_use.id)
                )

                # Yield tool execution complete event
                yield StreamEvent(
                    event_type="tool_execution_complete",
                    delta={
                        "type": "tool_execution_complete",
                        "tool_use_id": tool_use.id,
                        "tool_name": tool_use.name,
                        "output": content[:500] if len(content) > 500 else content,
                        "duration_ms": int((time.time() - start_time) * 1000),
                    },
                )

            except Exception as e:
                # Execute OnError hook
                error_input: OnErrorHookInput = {
                    "session_id": self._session_id,
                    "hook_event_name": "OnError",
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
                await self._execute_hooks(
                    "OnError",
                    error_input,
                    tool_use_id=tool_use.id,
                    tool_name=tool_use.name,
                )

                self._messages.append(
                    ToolMessage(
                        content=f"Error executing tool: {e!s}",
                        tool_call_id=tool_use.id,
                    )
                )

                # Yield tool execution error event
                yield StreamEvent(
                    event_type="tool_execution_complete",
                    delta={
                        "type": "tool_execution_error",
                        "tool_use_id": tool_use.id,
                        "tool_name": tool_use.name,
                        "error": str(e),
                        "duration_ms": int((time.time() - start_time) * 1000),
                    },
                )

        yield True

    def set_provider(self, provider: str, config: dict[str, Any] | None = None) -> None:
        """Switch to a different provider.

        Args:
            provider: Provider name (e.g., 'claude', 'openai')
            config: Optional provider configuration
        """
        self.options.provider = provider
        if config:
            self.options.provider_config = config
        self._provider = ProviderRegistry.get(provider, config)

    def set_model(self, model: str) -> None:
        """Set the model to use.

        Args:
            model: Model identifier
        """
        self.options.model = model

    def clear_history(self) -> None:
        """Clear conversation history while preserving system prompt."""
        system_messages: list[Message] = [
            m for m in self._messages if isinstance(m, SystemMessage)
        ]
        self._messages = system_messages

    def get_text_response(self) -> str:
        """Get the text content from the last assistant message.

        Returns:
            Concatenated text from all TextBlocks in the last assistant message
        """
        for msg in reversed(self._messages):
            if isinstance(msg, AssistantMessage):
                texts = [
                    block.text for block in msg.content if isinstance(block, TextBlock)
                ]
                return "".join(texts)
        return ""

    async def __aenter__(self) -> "UniversalAgentClient":
        """Enter async context - connects automatically."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Exit async context - disconnects."""
        await self.disconnect()
        return False
