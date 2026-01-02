"""SubAgent for hierarchical agent delegation."""

from typing import Any

from ..types import AnyMessage, AssistantMessage, ResultMessage, TextBlock
from .base import Agent


class SubAgent(Agent):
    """A SubAgent that can be spawned by a parent agent.

    SubAgents are specialized agents designed to handle specific subtasks
    delegated by a parent agent. They can:
    - Focus on a specialized domain
    - Use a different model or provider
    - Return results to the parent agent

    Example:
        ```python
        # Parent agent can spawn sub-agents for specialized tasks
        code_agent = SubAgent(
            name="code_writer",
            description="Writes Python code",
            system_prompt="You are an expert Python developer...",
            parent=main_agent,
        )

        result = await code_agent.run("Write a function to calculate factorial")
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
        parent: Agent | None = None,
        inherit_tools: bool = False,
        inherit_context: bool = False,
    ):
        """Initialize a SubAgent.

        Args:
            name: Agent identifier
            description: Human-readable description
            system_prompt: System instructions for the agent
            tools: List of tools the agent can use
            model: Model to use (defaults to parent's model)
            provider: LLM provider (defaults to parent's provider)
            max_turns: Maximum conversation turns
            parent: Parent agent (if any)
            inherit_tools: Whether to inherit parent's tools
            inherit_context: Whether to inherit parent's conversation context
        """
        # Inherit from parent if not specified
        if parent:
            model = model or parent.model
            provider = provider or parent.provider

            if inherit_tools:
                parent_tools = parent.tools.copy()
                tools = (tools or []) + parent_tools

        super().__init__(
            name=name,
            description=description,
            system_prompt=system_prompt,
            tools=tools,
            model=model,
            provider=provider,
            max_turns=max_turns or 5,
        )

        self.parent = parent
        self.inherit_context = inherit_context
        self._result: str | None = None

    @property
    def result(self) -> str | None:
        """Get the last execution result."""
        return self._result

    async def run(self, task: str) -> str:
        """Execute a task and return the result.

        Args:
            task: The task description

        Returns:
            The agent's text response
        """
        self._result = await super().run(task)
        return self._result

    async def run_and_report(self, task: str) -> dict[str, Any]:
        """Execute a task and return a structured report.

        Args:
            task: The task description

        Returns:
            Dictionary with result, status, and metadata
        """
        messages: list[AnyMessage] = []
        async for msg in self.stream(task):
            messages.append(msg)

        # Extract result
        result_text = ""
        for msg in reversed(messages):
            if isinstance(msg, AssistantMessage):
                texts = [
                    block.text for block in msg.content if isinstance(block, TextBlock)
                ]
                result_text = "".join(texts)
                break

        # Get result message
        result_msg = None
        for msg in messages:
            if isinstance(msg, ResultMessage):
                result_msg = msg
                break

        self._result = result_text

        return {
            "agent": self.name,
            "task": task,
            "result": result_text,
            "is_error": result_msg.is_error if result_msg else False,
            "num_turns": result_msg.num_turns if result_msg else 0,
            "session_id": result_msg.session_id if result_msg else self._agent_id,
        }


def create_subagent(
    parent: Agent,
    name: str,
    description: str,
    system_prompt: str | None = None,
    tools: list[Any] | None = None,
    inherit_tools: bool = False,
) -> SubAgent:
    """Factory function to create a SubAgent from a parent agent.

    Args:
        parent: Parent agent
        name: SubAgent name
        description: SubAgent description
        system_prompt: System prompt (optional)
        tools: Additional tools (optional)
        inherit_tools: Whether to inherit parent's tools

    Returns:
        Configured SubAgent
    """
    return SubAgent(
        name=name,
        description=description,
        system_prompt=system_prompt,
        tools=tools,
        parent=parent,
        inherit_tools=inherit_tools,
    )
