"""Agent registry for Universal Agent SDK."""

from builtins import list as _list
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..errors import AgentError
from ..types import AgentDefinition
from .base import Agent


class AgentRegistry:
    """Registry for managing agents.

    The AgentRegistry provides a centralized way to register, retrieve,
    and manage agents that can be used in the SDK.

    Example:
        ```python
        registry = AgentRegistry()

        # Register agents
        registry.register(code_reviewer_agent)
        registry.register(test_writer_agent)

        # Get an agent
        reviewer = registry.get("code_reviewer")
        result = await reviewer.run("Review this code...")
        ```
    """

    _global_registry: dict[str, Agent] = {}

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        """Register an agent.

        Args:
            agent: Agent instance to register
        """
        self._agents[agent.name] = agent

    def unregister(self, name: str) -> None:
        """Unregister an agent.

        Args:
            name: Agent name to unregister
        """
        if name in self._agents:
            del self._agents[name]

    def get(self, name: str) -> Agent:
        """Get an agent by name.

        Args:
            name: Agent name

        Returns:
            Agent instance

        Raises:
            AgentError: If agent is not found
        """
        if name in self._agents:
            return self._agents[name]
        raise AgentError(f"Agent not found: {name}")

    def has(self, name: str) -> bool:
        """Check if an agent is registered.

        Args:
            name: Agent name

        Returns:
            True if agent exists
        """
        return name in self._agents

    def list(self) -> list[str]:
        """List all registered agent names.

        Returns:
            List of agent names
        """
        return list(self._agents.keys())

    def get_all(self) -> _list[Agent]:
        """Get all registered agents.

        Returns:
            List of Agent instances
        """
        return list(self._agents.values())

    def get_definitions(self) -> dict[str, AgentDefinition]:
        """Get AgentDefinitions for all registered agents.

        Returns:
            Dictionary mapping agent names to their definitions
        """
        return {agent.name: agent.definition for agent in self._agents.values()}

    def clear(self) -> None:
        """Remove all registered agents."""
        self._agents.clear()

    def load_from_file(self, path: str | Path) -> None:
        """Load agent definitions from a file.

        Supports YAML and JSON formats.

        Args:
            path: Path to the agent definitions file
        """
        path = Path(path)

        if not path.exists():
            raise AgentError(f"Agent file not found: {path}")

        content = path.read_text()

        if path.suffix in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore[import-untyped]

                data = yaml.safe_load(content)
            except ImportError as e:
                raise ImportError(
                    "PyYAML is required for YAML agent files. "
                    "Install it with: pip install pyyaml"
                ) from e
        elif path.suffix == ".json":
            import json

            data = json.loads(content)
        else:
            raise AgentError(f"Unsupported file format: {path.suffix}")

        self._load_agents_from_dict(data)

    def load_from_directory(self, directory: str | Path) -> None:
        """Load all agent definitions from a directory.

        Args:
            directory: Path to directory containing agent definition files
        """
        directory = Path(directory)

        if not directory.is_dir():
            raise AgentError(f"Not a directory: {directory}")

        for path in directory.glob("*.yaml"):
            self.load_from_file(path)
        for path in directory.glob("*.yml"):
            self.load_from_file(path)
        for path in directory.glob("*.json"):
            self.load_from_file(path)

    def _load_agents_from_dict(self, data: dict[str, Any]) -> None:
        """Load agents from a dictionary.

        Args:
            data: Dictionary containing agent definitions
        """
        agents_data = data.get("agents", data)

        for name, agent_def in agents_data.items():
            if isinstance(agent_def, dict):
                agent = Agent(
                    name=name,
                    description=agent_def.get("description", f"Agent: {name}"),
                    system_prompt=agent_def.get("system_prompt"),
                    model=agent_def.get("model"),
                    provider=agent_def.get("provider"),
                    max_turns=agent_def.get("max_turns"),
                )
                self.register(agent)

    # Class methods for global registry
    @classmethod
    def register_global(cls, agent: Agent) -> None:
        """Register an agent globally.

        Args:
            agent: Agent instance to register
        """
        cls._global_registry[agent.name] = agent

    @classmethod
    def get_global(cls, name: str) -> Agent:
        """Get an agent from global registry.

        Args:
            name: Agent name

        Returns:
            Agent instance

        Raises:
            AgentError: If agent is not found
        """
        if name in cls._global_registry:
            return cls._global_registry[name]
        raise AgentError(f"Agent not found: {name}")

    @classmethod
    def list_global(cls) -> _list[str]:
        """List all globally registered agent names.

        Returns:
            List of agent names
        """
        return list(cls._global_registry.keys())

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        return name in self._agents

    def __iter__(self) -> Iterator[Agent]:
        return iter(self._agents.values())
