"""Tool registry for Universal Agent SDK."""

from builtins import list as _list
from collections.abc import Iterator

from ..errors import ToolNotFoundError
from ..types import ToolDefinition
from .base import Tool


class ToolRegistry:
    """Registry for managing tools.

    The ToolRegistry provides a centralized way to register and retrieve
    tools that can be used by agents.

    Example:
        ```python
        registry = ToolRegistry()

        @tool
        def get_weather(city: str) -> str:
            return f"Weather in {city}: Sunny"

        registry.register(get_weather)

        # Later
        weather_tool = registry.get("get_weather")
        result = await weather_tool(city="Paris")
        ```
    """

    _global_registry: dict[str, Tool] = {}

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool.

        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool.

        Args:
            name: Tool name to unregister
        """
        if name in self._tools:
            del self._tools[name]

    def get(self, name: str) -> Tool:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance

        Raises:
            ToolNotFoundError: If tool is not found
        """
        if name in self._tools:
            return self._tools[name]
        raise ToolNotFoundError(name)

    def has(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: Tool name

        Returns:
            True if tool exists
        """
        return name in self._tools

    def list(self) -> list[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_all(self) -> _list[Tool]:
        """Get all registered tools.

        Returns:
            List of Tool instances
        """
        return list(self._tools.values())

    def get_definitions(self) -> _list[ToolDefinition]:
        """Get ToolDefinitions for all registered tools.

        Returns:
            List of ToolDefinition instances
        """
        return [tool.definition for tool in self._tools.values()]

    def clear(self) -> None:
        """Remove all registered tools."""
        self._tools.clear()

    # Class methods for global registry
    @classmethod
    def register_global(cls, tool: Tool) -> None:
        """Register a tool globally.

        Args:
            tool: Tool instance to register
        """
        cls._global_registry[tool.name] = tool

    @classmethod
    def get_global(cls, name: str) -> Tool:
        """Get a tool from global registry.

        Args:
            name: Tool name

        Returns:
            Tool instance

        Raises:
            ToolNotFoundError: If tool is not found
        """
        if name in cls._global_registry:
            return cls._global_registry[name]
        raise ToolNotFoundError(name)

    @classmethod
    def list_global(cls) -> _list[str]:
        """List all globally registered tool names.

        Returns:
            List of tool names
        """
        return list(cls._global_registry.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __iter__(self) -> Iterator[Tool]:
        return iter(self._tools.values())
