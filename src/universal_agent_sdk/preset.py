"""Preset loader for agent configurations.

Load agent presets from YAML or JSON configuration files.

Example usage:
    ```python
    from universal_agent_sdk import load_preset, UniversalAgentClient

    # Load preset from file
    preset = load_preset("/path/to/preset.yaml")

    # Convert to agent options
    options = preset.to_agent_options()

    # Use with client
    async with UniversalAgentClient(options) as client:
        await client.send("Hello!")
        async for msg in client.receive():
            print(msg)
    ```
"""

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from .types import (
    AgentDefinition,
    AgentOptions,
    AgentPreset,
    MCPServerConfig,
    PermissionMode,
    ResourceLimits,
    SettingSource,
    SystemPromptPreset,
    ToolDefinition,
)

if TYPE_CHECKING:
    from .client import UniversalAgentClient

# Try to import yaml, but make it optional
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class PresetLoadError(Exception):
    """Error loading a preset configuration."""

    pass


def load_preset(path: str | Path) -> AgentPreset:
    """Load an agent preset from a YAML or JSON file.

    Args:
        path: Path to the preset file (.yaml, .yml, or .json)

    Returns:
        AgentPreset object

    Raises:
        PresetLoadError: If the file cannot be loaded or parsed
        FileNotFoundError: If the file does not exist
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Preset file not found: {path}")

    suffix = path.suffix.lower()

    with open(path, encoding="utf-8") as f:
        if suffix in (".yaml", ".yml"):
            if not YAML_AVAILABLE:
                raise PresetLoadError(
                    "PyYAML is required to load YAML presets. "
                    "Install it with: pip install pyyaml"
                )
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise PresetLoadError(f"Failed to parse YAML: {e}") from e
        elif suffix == ".json":
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise PresetLoadError(f"Failed to parse JSON: {e}") from e
        else:
            raise PresetLoadError(
                f"Unsupported file format: {suffix}. Use .yaml, .yml, or .json"
            )

    return parse_preset_data(data, source_path=str(path))


def load_preset_from_string(
    content: str, format: str = "yaml", source_path: str | None = None
) -> AgentPreset:
    """Load an agent preset from a string.

    Args:
        content: The preset content as a string
        format: The format ("yaml" or "json")
        source_path: Optional path for error messages

    Returns:
        AgentPreset object

    Raises:
        PresetLoadError: If the content cannot be parsed
    """
    try:
        if format.lower() in ("yaml", "yml"):
            if not YAML_AVAILABLE:
                raise PresetLoadError(
                    "PyYAML is required to load YAML presets. "
                    "Install it with: pip install pyyaml"
                )
            data = yaml.safe_load(content)
        elif format.lower() == "json":
            data = json.loads(content)
        else:
            raise PresetLoadError(f"Unsupported format: {format}")
    except Exception as e:
        raise PresetLoadError(f"Failed to parse {format}: {e}") from e

    return parse_preset_data(data, source_path=source_path)


def parse_preset_data(
    data: dict[str, Any], source_path: str | None = None
) -> AgentPreset:
    """Parse preset data into an AgentPreset object.

    Args:
        data: Dictionary of preset configuration
        source_path: Optional source path for error messages

    Returns:
        AgentPreset object

    Raises:
        PresetLoadError: If required fields are missing or invalid
    """
    if not isinstance(data, dict):
        raise PresetLoadError(f"Preset must be a dictionary, got {type(data).__name__}")

    # Required fields
    if "id" not in data:
        raise PresetLoadError("Preset must have an 'id' field")
    if "name" not in data:
        raise PresetLoadError("Preset must have a 'name' field")

    # Parse system prompt
    system_prompt = _parse_system_prompt(data.get("system_prompt"))

    # Parse resource limits
    resource_limits = _parse_resource_limits(data.get("resource_limits"))

    # Parse MCP servers
    mcp_servers = _parse_mcp_servers(data.get("mcp_servers", {}))

    # Parse agents
    agents = _parse_agents(data.get("agents", {}))

    # Parse setting sources
    setting_sources = _parse_setting_sources(data.get("setting_sources", []))

    # Parse permission mode
    permission_mode = _parse_permission_mode(data.get("permission_mode"))

    # Expand environment variables in env dict
    env = _expand_env_vars(data.get("env", {}))

    # Parse provider_config (with env var expansion for values like base_url)
    provider_config = _expand_env_vars(data.get("provider_config", {}))

    return AgentPreset(
        id=data["id"],
        name=data["name"],
        description=data.get("description"),
        version=data.get("version"),
        system_prompt=system_prompt,
        allowed_tools=data.get("allowed_tools", []),
        skills=data.get("skills", []),
        permission_mode=permission_mode,
        resource_limits=resource_limits,
        setting_sources=setting_sources,
        env=env,
        mcp_servers=mcp_servers,
        agents=agents,
        model=data.get("model"),
        provider=data.get("provider", "claude"),
        provider_config=provider_config,
        max_turns=data.get("max_turns"),
        cwd=data.get("cwd"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


def _parse_system_prompt(
    data: str | dict[str, Any] | None,
) -> str | SystemPromptPreset | None:
    """Parse system prompt configuration."""
    if data is None:
        return None
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        if data.get("type") == "preset":
            return SystemPromptPreset(
                type="preset",
                preset=data.get("preset", "assistant"),
                append=data.get("append"),
            )
        raise PresetLoadError(
            f"Invalid system_prompt type: {data.get('type')}. Must be 'preset'"
        )
    raise PresetLoadError(
        f"system_prompt must be string or dict, got {type(data).__name__}"
    )


def _parse_resource_limits(data: dict[str, Any] | None) -> ResourceLimits | None:
    """Parse resource limits configuration."""
    if data is None:
        return None
    if not isinstance(data, dict):
        raise PresetLoadError(
            f"resource_limits must be a dict, got {type(data).__name__}"
        )
    return ResourceLimits(
        cpu_quota=data.get("cpu_quota"),
        memory_limit=data.get("memory_limit"),
        storage_limit=data.get("storage_limit"),
        timeout_seconds=data.get("timeout_seconds"),
    )


def _parse_mcp_servers(data: dict[str, Any]) -> dict[str, MCPServerConfig]:
    """Parse MCP server configurations."""
    if not isinstance(data, dict):
        raise PresetLoadError(f"mcp_servers must be a dict, got {type(data).__name__}")

    servers: dict[str, MCPServerConfig] = {}
    for name, config in data.items():
        if not isinstance(config, dict):
            raise PresetLoadError(
                f"MCP server '{name}' config must be a dict, got {type(config).__name__}"
            )

        server_type = config.get("type", "stdio")
        if server_type not in ("stdio", "sse"):
            raise PresetLoadError(
                f"MCP server '{name}' has invalid type: {server_type}. Must be 'stdio' or 'sse'"
            )

        # Expand environment variables in args and env
        args = config.get("args", [])
        if isinstance(args, list):
            args = [_expand_env_var(str(a)) for a in args]

        env = _expand_env_vars(config.get("env", {}))

        servers[name] = MCPServerConfig(
            type=server_type,
            command=config.get("command"),
            args=args,
            url=config.get("url"),
            env=env,
        )

    return servers


def _parse_agents(data: dict[str, Any]) -> dict[str, AgentDefinition]:
    """Parse sub-agent configurations."""
    if not isinstance(data, dict):
        raise PresetLoadError(f"agents must be a dict, got {type(data).__name__}")

    agents: dict[str, AgentDefinition] = {}
    for name, config in data.items():
        if not isinstance(config, dict):
            raise PresetLoadError(
                f"Agent '{name}' config must be a dict, got {type(config).__name__}"
            )

        # Required field: description
        if "description" not in config:
            raise PresetLoadError(f"Agent '{name}' must have a 'description' field")

        agents[name] = AgentDefinition(
            name=name,
            description=config["description"],
            system_prompt=config.get("prompt"),
            tools=config.get("tools"),
            model=config.get("model"),
            provider=config.get("provider"),
            max_turns=config.get("max_turns"),
        )

    return agents


def _parse_setting_sources(data: list[Any]) -> list[SettingSource]:
    """Parse setting sources list."""
    if not isinstance(data, list):
        raise PresetLoadError(
            f"setting_sources must be a list, got {type(data).__name__}"
        )

    valid_sources: set[str] = {"user", "project", "local"}
    sources: list[SettingSource] = []

    for source in data:
        if source not in valid_sources:
            raise PresetLoadError(
                f"Invalid setting source: {source}. Must be one of: {valid_sources}"
            )
        sources.append(source)  # type: ignore[arg-type]

    return sources


def _parse_permission_mode(data: str | None) -> PermissionMode | None:
    """Parse permission mode."""
    if data is None:
        return None

    valid_modes: set[str] = {"ask", "auto_allow", "acceptEdits", "deny_all"}
    if data not in valid_modes:
        raise PresetLoadError(
            f"Invalid permission_mode: {data}. Must be one of: {valid_modes}"
        )

    return data  # type: ignore[return-value]


def _expand_env_var(value: str) -> str:
    """Expand environment variables in a string.

    Supports ${VAR} syntax.
    """
    if "${" not in value:
        return value

    result = value
    import re

    for match in re.finditer(r"\$\{([^}]+)\}", value):
        var_name = match.group(1)
        var_value = os.environ.get(var_name, "")
        result = result.replace(match.group(0), var_value)

    return result


def _expand_env_vars(data: dict[str, str]) -> dict[str, str]:
    """Expand environment variables in a dictionary of values."""
    return {k: _expand_env_var(str(v)) for k, v in data.items()}


def discover_presets(
    search_paths: list[str | Path] | None = None,
) -> dict[str, AgentPreset]:
    """Discover and load all presets from search paths.

    Args:
        search_paths: List of directories to search. If None, searches:
            - ~/.claude/presets/
            - ./.claude/presets/

    Returns:
        Dictionary mapping preset IDs to AgentPreset objects
    """
    if search_paths is None:
        search_paths = [
            Path.home() / ".claude" / "presets",
            Path.cwd() / ".claude" / "presets",
        ]

    presets: dict[str, AgentPreset] = {}

    for search_path in search_paths:
        path = Path(search_path)
        if not path.exists() or not path.is_dir():
            continue

        for file_path in path.iterdir():
            if file_path.suffix.lower() in (".yaml", ".yml", ".json"):
                try:
                    preset = load_preset(file_path)
                    presets[preset.id] = preset
                except (PresetLoadError, FileNotFoundError) as e:
                    # Log warning but continue
                    import logging

                    logging.warning(f"Failed to load preset {file_path}: {e}")

    return presets


def get_preset(
    preset_id: str,
    search_paths: list[str | Path] | None = None,
) -> AgentPreset | None:
    """Get a specific preset by ID.

    Args:
        preset_id: The preset ID to find
        search_paths: Optional list of directories to search

    Returns:
        AgentPreset if found, None otherwise
    """
    presets = discover_presets(search_paths)
    return presets.get(preset_id)


def create_client_from_preset(
    preset: AgentPreset | str | Path,
    system_prompt_resolver: Callable[[str], str] | None = None,
    include_builtin_tools: bool = True,
) -> "UniversalAgentClient":
    """Create a UniversalAgentClient from a preset.

    Args:
        preset: AgentPreset object, preset ID, or path to preset file
        system_prompt_resolver: Optional function to resolve preset names to prompts
        include_builtin_tools: Whether to auto-load built-in tools (default: True)

    Returns:
        Configured UniversalAgentClient

    Raises:
        PresetLoadError: If preset cannot be loaded
        FileNotFoundError: If preset file not found
    """
    from .client import UniversalAgentClient

    # Load preset if needed
    if isinstance(preset, (str, Path)):
        path = Path(preset)
        if path.exists():
            preset = load_preset(path)
        else:
            # Try to find by ID
            found = get_preset(str(preset))
            if found is None:
                raise PresetLoadError(f"Preset not found: {preset}")
            preset = found

    # Convert to options with tools auto-loaded
    options = preset_to_options_with_tools(
        preset,
        system_prompt_resolver=system_prompt_resolver,
        include_builtin_tools=include_builtin_tools,
    )

    return UniversalAgentClient(options)


def get_builtin_tool(tool_name: str) -> ToolDefinition | None:
    """Get a built-in tool by name.

    Args:
        tool_name: Name of the built-in tool (e.g., "Read", "Write", "Bash", "WebSearch")

    Returns:
        ToolDefinition for the tool, or None if not found
    """
    # Import here to avoid circular imports
    from .tools.builtin import (
        BashTool,
        DateTimeTool,
        EditTool,
        GlobTool,
        GrepTool,
        NotebookEditTool,
        ReadTool,
        WebFetchTool,
        WebSearchTool,
        WriteTool,
    )

    # Map tool names to their classes
    tool_classes: dict[str, type] = {
        "Read": ReadTool,
        "ReadTool": ReadTool,
        "Write": WriteTool,
        "WriteTool": WriteTool,
        "Edit": EditTool,
        "EditTool": EditTool,
        "Bash": BashTool,
        "BashTool": BashTool,
        "Glob": GlobTool,
        "GlobTool": GlobTool,
        "Grep": GrepTool,
        "GrepTool": GrepTool,
        "NotebookEdit": NotebookEditTool,
        "NotebookEditTool": NotebookEditTool,
        "WebSearch": WebSearchTool,
        "WebSearchTool": WebSearchTool,
        "WebFetch": WebFetchTool,
        "WebFetchTool": WebFetchTool,
        "DateTime": DateTimeTool,
        "DateTimeTool": DateTimeTool,
    }

    tool_class = tool_classes.get(tool_name)
    if tool_class is None:
        return None

    # Instantiate the tool and convert to definition
    tool_instance = tool_class()
    return cast(ToolDefinition, tool_instance.to_tool_definition())


def get_builtin_tools(tool_names: list[str]) -> list[ToolDefinition]:
    """Get multiple built-in tools by name.

    Args:
        tool_names: List of tool names (e.g., ["Read", "Write", "WebSearch"])

    Returns:
        List of ToolDefinitions for found tools (unrecognized names are skipped)
    """
    tools: list[ToolDefinition] = []
    for name in tool_names:
        tool = get_builtin_tool(name)
        if tool is not None:
            tools.append(tool)
    return tools


def preset_to_options_with_tools(
    preset: AgentPreset,
    system_prompt_resolver: Callable[[str], str] | None = None,
    include_builtin_tools: bool = True,
    include_datetime_tool: bool = True,
) -> AgentOptions:
    """Convert a preset to AgentOptions with tools auto-loaded.

    This is a convenience function that:
    1. Converts the preset to AgentOptions
    2. Auto-loads built-in tools based on allowed_tools
    3. Always includes DateTimeTool so the LLM knows the current date/time

    Args:
        preset: The AgentPreset to convert
        system_prompt_resolver: Optional function to resolve preset names to prompts
        include_builtin_tools: Whether to auto-load built-in tools (default: True)
        include_datetime_tool: Whether to always include DateTimeTool (default: True)

    Returns:
        AgentOptions with tools populated
    """
    options = preset.to_agent_options(system_prompt_resolver)

    existing_tool_names = {t.name for t in options.tools}

    # Always include DateTimeTool so the LLM can know the current date/time
    if include_datetime_tool and "DateTime" not in existing_tool_names:
        datetime_tool = get_builtin_tool("DateTime")
        if datetime_tool:
            options.tools.append(datetime_tool)
            existing_tool_names.add("DateTime")

    if include_builtin_tools and preset.allowed_tools:
        builtin_tools = get_builtin_tools(preset.allowed_tools)
        # Merge with any existing tools
        for tool in builtin_tools:
            if tool.name not in existing_tool_names:
                options.tools.append(tool)
                existing_tool_names.add(tool.name)

    return options
