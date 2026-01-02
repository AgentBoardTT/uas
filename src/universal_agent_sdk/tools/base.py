"""Tool base class and decorator for Universal Agent SDK."""

import functools
import inspect
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, get_type_hints, overload

from ..types import ToolDefinition, ToolSchema

P = ParamSpec("P")
R = TypeVar("R")


class Tool:
    """A tool that can be used by LLM agents.

    Tools are functions that agents can call to perform actions or retrieve
    information. This class wraps a function with metadata for LLM consumption.

    Attributes:
        name: The tool name
        description: Human-readable description
        input_schema: JSON Schema for input validation
        handler: The function to execute
        definition: ToolDefinition for SDK usage
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: ToolSchema | dict[str, Any],
        handler: Callable[..., Any] | None = None,
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler

    @property
    def definition(self) -> ToolDefinition:
        """Get the ToolDefinition for this tool."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.handler,
        )

    async def __call__(self, **kwargs: Any) -> Any:
        """Execute the tool with the given arguments."""
        if self.handler is None:
            raise RuntimeError(f"Tool '{self.name}' has no handler")

        result = self.handler(**kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    def __repr__(self) -> str:
        return f"Tool(name={self.name!r}, description={self.description!r})"


def _infer_schema_from_function(func: Callable[..., Any]) -> dict[str, Any]:
    """Infer JSON Schema from function signature and type hints.

    Args:
        func: Function to analyze

    Returns:
        JSON Schema for the function's parameters
    """
    sig = inspect.signature(func)
    hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        param_schema: dict[str, Any] = {}

        # Get type from hints
        if param_name in hints:
            param_type = hints[param_name]
            param_schema = _python_type_to_json_schema(param_type)

        # Check if required (no default value)
        if param.default is inspect.Parameter.empty:
            required.append(param_name)
        else:
            param_schema["default"] = param.default

        properties[param_name] = param_schema

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }

    if required:
        schema["required"] = required

    return schema


def _python_type_to_json_schema(python_type: Any) -> dict[str, Any]:
    """Convert a Python type to JSON Schema.

    Args:
        python_type: Python type annotation

    Returns:
        JSON Schema for the type
    """
    import types
    from typing import Union, get_args, get_origin

    origin = get_origin(python_type)
    args = get_args(python_type)

    # Handle None/NoneType
    if python_type is type(None):
        return {"type": "null"}

    # Handle basic types
    if python_type is str:
        return {"type": "string"}
    if python_type is int:
        return {"type": "integer"}
    if python_type is float:
        return {"type": "number"}
    if python_type is bool:
        return {"type": "boolean"}

    # Handle list/List
    if origin is list:
        if args:
            return {"type": "array", "items": _python_type_to_json_schema(args[0])}
        return {"type": "array"}

    # Handle dict/Dict
    if origin is dict:
        return {"type": "object"}

    # Handle Optional (Union with None)
    if origin is Union or origin is types.UnionType:
        non_none_types = [t for t in args if t is not type(None)]
        if len(non_none_types) == 1:
            # This is Optional[T]
            return _python_type_to_json_schema(non_none_types[0])
        # Multiple types - use anyOf
        return {"anyOf": [_python_type_to_json_schema(t) for t in non_none_types]}

    # Handle Literal
    if origin is type(None):
        return {"type": "null"}

    # Fallback
    return {"type": "string"}


@overload
def tool(
    func: Callable[P, R],
) -> Tool: ...


@overload
def tool(
    *,
    name: str | None = None,
    description: str | None = None,
    input_schema: ToolSchema | dict[str, Any] | None = None,
) -> Callable[[Callable[P, R]], Tool]: ...


def tool(
    func: Callable[P, R] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    input_schema: ToolSchema | dict[str, Any] | None = None,
) -> Tool | Callable[[Callable[P, R]], Tool]:
    """Decorator to create a Tool from a function.

    Can be used with or without arguments:

    ```python
    @tool
    def my_tool(arg: str) -> str:
        \"\"\"Tool description from docstring.\"\"\"
        return f"Result: {arg}"

    @tool(name="custom_name", description="Custom description")
    def another_tool(arg: str) -> str:
        return f"Result: {arg}"
    ```

    Args:
        func: The function to wrap (when used without arguments)
        name: Tool name (defaults to function name)
        description: Tool description (defaults to docstring)
        input_schema: JSON Schema for inputs (inferred from type hints if not provided)

    Returns:
        Tool instance
    """

    def decorator(fn: Callable[P, R]) -> Tool:
        tool_name = name or fn.__name__
        tool_description = (
            description or (fn.__doc__ or "").strip() or f"Tool: {tool_name}"
        )
        tool_schema = input_schema or _infer_schema_from_function(fn)

        tool_instance = Tool(
            name=tool_name,
            description=tool_description,
            input_schema=tool_schema,
            handler=fn,
        )

        # Preserve function metadata
        functools.update_wrapper(tool_instance, fn)

        return tool_instance

    if func is not None:
        # Called without arguments: @tool
        return decorator(func)
    else:
        # Called with arguments: @tool(name=...)
        return decorator
