"""Base Agent class for Universal Agent SDK."""

import uuid
from collections.abc import AsyncIterator
from typing import Any

from ..config import get_config
from ..providers import ProviderRegistry
from ..types import (
    AgentDefinition,
    AgentOptions,
    AnyMessage,
    AssistantMessage,
    Message,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolMessage,
    ToolUseBlock,
    UserMessage,
)


class Agent:
    """Base Agent class for LLM-powered agents.

    An Agent encapsulates a specific personality, capabilities, and behavior
    defined through system prompts, tools, and configuration.

    Agents can:
    - Execute tasks autonomously
    - Use tools to interact with the environment
    - Spawn sub-agents for specialized tasks
    - Maintain conversation context

    Example:
        ```python
        agent = Agent(
            name="code_reviewer",
            description="Reviews code for best practices",
            system_prompt="You are an expert code reviewer...",
            tools=[analyze_code, suggest_fixes],
        )

        result = await agent.run("Review this Python function: def foo(): pass")
        print(result)
        ```
    """

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str | None = None,
        tools: list[Any] | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_turns: int | None = None,
        options: AgentOptions | None = None,
    ):
        """Initialize an Agent.

        Args:
            name: Agent identifier
            description: Human-readable description
            system_prompt: System instructions for the agent
            tools: List of tools the agent can use
            model: Model to use (provider-specific)
            provider: LLM provider name
            max_turns: Maximum conversation turns
            options: Additional AgentOptions
        """
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model = model
        self.provider = provider or "claude"
        self.max_turns = max_turns or 10

        # Initialize options
        self._base_options = options or AgentOptions()
        self._agent_id = str(uuid.uuid4())
        self._messages: list[Message] = []

    @property
    def definition(self) -> AgentDefinition:
        """Get the AgentDefinition for this agent."""
        return AgentDefinition(
            name=self.name,
            description=self.description,
            system_prompt=self.system_prompt,
            tools=[t.name if hasattr(t, "name") else str(t) for t in self.tools],
            model=self.model,
            provider=self.provider,
            max_turns=self.max_turns,
        )

    def _get_options(self) -> AgentOptions:
        """Build AgentOptions for this agent."""
        from ..tools import Tool

        # Get tool definitions
        tool_definitions = []
        for tool in self.tools:
            if isinstance(tool, Tool) or hasattr(tool, "definition"):
                tool_definitions.append(tool.definition)

        return AgentOptions(
            provider=self.provider,
            provider_config=self._base_options.provider_config,
            model=self.model or self._base_options.model,
            system_prompt=self.system_prompt or self._base_options.system_prompt,
            tools=tool_definitions,
            max_turns=self.max_turns,
            stream=self._base_options.stream,
            temperature=self._base_options.temperature,
            max_tokens=self._base_options.max_tokens,
            can_use_tool=self._base_options.can_use_tool,
            hooks=self._base_options.hooks,
        )

    async def run(self, task: str) -> str:
        """Execute a task and return the result.

        This method runs the agent until completion and returns the
        final text response.

        Args:
            task: The task description or prompt

        Returns:
            The agent's text response
        """
        messages: list[AnyMessage] = []
        async for msg in self.stream(task):
            messages.append(msg)

        # Extract text from the last assistant message
        for msg in reversed(messages):
            if isinstance(msg, AssistantMessage):
                texts = [
                    block.text for block in msg.content if isinstance(block, TextBlock)
                ]
                return "".join(texts)

        return ""

    async def stream(self, task: str) -> AsyncIterator[AnyMessage]:
        """Execute a task with streaming responses.

        Args:
            task: The task description or prompt

        Yields:
            Messages from the agent including streaming events
        """
        options = self._get_options()

        # Load config and get provider config if not provided
        config = get_config()
        provider_config = options.provider_config
        if provider_config is None:
            provider_config = config.get_provider_config(options.provider)

        provider = ProviderRegistry.get(options.provider, provider_config)

        # Build initial messages
        messages: list[Message] = []
        if options.system_prompt:
            messages.append(SystemMessage(content=options.system_prompt))
        messages.append(UserMessage(content=task))

        # Run with tool loop
        turns = 0
        while turns < self.max_turns:
            turns += 1

            response: AssistantMessage | None = None
            if options.stream:
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
                yield ResultMessage(
                    is_error=False, num_turns=turns, session_id=self._agent_id
                )
                break

            # Add assistant message
            messages.append(response)

            # Execute tools
            for tool_use in tool_uses:
                result = await self._execute_tool(tool_use, options)
                messages.append(ToolMessage(content=result, tool_call_id=tool_use.id))

    async def _execute_tool(self, tool_use: ToolUseBlock, options: AgentOptions) -> str:
        """Execute a single tool.

        Args:
            tool_use: Tool use block from the model
            options: Agent options

        Returns:
            Tool execution result as string
        """
        from ..tools import Tool

        # Find the tool
        tool_def = None
        for tool in self.tools:
            name = tool.name if hasattr(tool, "name") else str(tool)
            if name == tool_use.name:
                tool_def = tool
                break

        if tool_def is None:
            return f"Tool '{tool_use.name}' not found"

        # Check permission
        if options.can_use_tool:
            from ..types import PermissionResultDeny, ToolPermissionContext

            context = ToolPermissionContext(session_id=self._agent_id)
            result = await options.can_use_tool(tool_use.name, tool_use.input, context)
            if isinstance(result, PermissionResultDeny):
                return f"Permission denied: {result.message}"

        # Execute tool
        try:
            if isinstance(tool_def, Tool):
                result = await tool_def(**tool_use.input)
            elif hasattr(tool_def, "handler") and tool_def.handler:
                result = tool_def.handler(**tool_use.input)
                if hasattr(result, "__await__"):
                    result = await result
            else:
                return f"Tool '{tool_use.name}' has no handler"

            if isinstance(result, str):
                return result
            import json

            return json.dumps(result)
        except Exception as e:
            return f"Error executing tool: {e!s}"

    def reset(self) -> None:
        """Reset the agent's conversation history."""
        self._messages.clear()
        self._agent_id = str(uuid.uuid4())

    def __repr__(self) -> str:
        return f"Agent(name={self.name!r}, description={self.description!r})"
