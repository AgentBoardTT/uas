"""Memory Tool for Universal Agent SDK.

This module implements the Anthropic Memory Tool specification, which enables
Claude to store and retrieve information across conversations through a
file-based memory directory.

The memory tool supports these commands:
- view: Show directory contents or file contents
- create: Create a new file
- str_replace: Replace text in a file
- insert: Insert text at a specific line
- delete: Delete a file or directory
- rename: Rename or move a file/directory

Example usage:
    ```python
    from universal_agent_sdk.tools.memory import FileSystemMemoryTool

    # Create memory tool with a custom directory
    memory_tool = FileSystemMemoryTool(memory_dir="./my_memories")

    # Use it with an agent
    options = AgentOptions(
        tools=[memory_tool.to_tool_definition()],
    )
    ```

Reference: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
"""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import unquote

from ..types import ToolDefinition

# =============================================================================
# Memory Command Types
# =============================================================================


@dataclass
class MemoryViewCommand:
    """View directory contents or file contents."""

    command: Literal["view"]
    path: str
    view_range: list[int] | None = None  # [start_line, end_line]


@dataclass
class MemoryCreateCommand:
    """Create a new file."""

    command: Literal["create"]
    path: str
    file_text: str


@dataclass
class MemoryStrReplaceCommand:
    """Replace text in a file."""

    command: Literal["str_replace"]
    path: str
    old_str: str
    new_str: str


@dataclass
class MemoryInsertCommand:
    """Insert text at a specific line."""

    command: Literal["insert"]
    path: str
    insert_line: int
    insert_text: str


@dataclass
class MemoryDeleteCommand:
    """Delete a file or directory."""

    command: Literal["delete"]
    path: str


@dataclass
class MemoryRenameCommand:
    """Rename or move a file/directory."""

    command: Literal["rename"]
    old_path: str
    new_path: str


MemoryCommand = (
    MemoryViewCommand
    | MemoryCreateCommand
    | MemoryStrReplaceCommand
    | MemoryInsertCommand
    | MemoryDeleteCommand
    | MemoryRenameCommand
)


# =============================================================================
# Memory Tool Input Schema
# =============================================================================


MEMORY_TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "enum": ["view", "create", "str_replace", "insert", "delete", "rename"],
            "description": "The memory operation to perform",
        },
        "path": {
            "type": "string",
            "description": "Path to view, create, edit, or delete (relative to /memories)",
        },
        "view_range": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "Optional line range [start, end] for viewing file contents",
        },
        "file_text": {
            "type": "string",
            "description": "Content for creating a new file",
        },
        "old_str": {
            "type": "string",
            "description": "Text to find and replace",
        },
        "new_str": {
            "type": "string",
            "description": "Replacement text",
        },
        "insert_line": {
            "type": "integer",
            "description": "Line number to insert text at (0-indexed)",
        },
        "insert_text": {
            "type": "string",
            "description": "Text to insert",
        },
        "old_path": {
            "type": "string",
            "description": "Source path for rename operation",
        },
        "new_path": {
            "type": "string",
            "description": "Destination path for rename operation",
        },
    },
    "required": ["command"],
}


# =============================================================================
# Base Memory Tool
# =============================================================================


class BaseMemoryTool(ABC):
    """Abstract base class for memory tool implementations.

    Subclass this to create custom memory storage backends (database,
    cloud storage, encrypted files, etc.).
    """

    name: str = "memory"
    description: str = (
        "A tool for storing and retrieving information across conversations. "
        "Supports viewing, creating, editing, and deleting files in the /memories directory."
    )

    @abstractmethod
    async def view(self, command: MemoryViewCommand) -> str:
        """View directory contents or file contents."""
        ...

    @abstractmethod
    async def create(self, command: MemoryCreateCommand) -> str:
        """Create a new file."""
        ...

    @abstractmethod
    async def str_replace(self, command: MemoryStrReplaceCommand) -> str:
        """Replace text in a file."""
        ...

    @abstractmethod
    async def insert(self, command: MemoryInsertCommand) -> str:
        """Insert text at a specific line."""
        ...

    @abstractmethod
    async def delete(self, command: MemoryDeleteCommand) -> str:
        """Delete a file or directory."""
        ...

    @abstractmethod
    async def rename(self, command: MemoryRenameCommand) -> str:
        """Rename or move a file/directory."""
        ...

    async def execute(self, input_data: dict[str, Any]) -> str:
        """Execute a memory command and return the result.

        Args:
            input_data: Raw input dictionary from tool call

        Returns:
            Result string for the tool response
        """
        command_type = input_data.get("command")

        if command_type == "view":
            view_cmd = MemoryViewCommand(
                command="view",
                path=input_data.get("path", "/memories"),
                view_range=input_data.get("view_range"),
            )
            return await self.view(view_cmd)

        elif command_type == "create":
            create_cmd = MemoryCreateCommand(
                command="create",
                path=input_data["path"],
                file_text=input_data["file_text"],
            )
            return await self.create(create_cmd)

        elif command_type == "str_replace":
            replace_cmd = MemoryStrReplaceCommand(
                command="str_replace",
                path=input_data["path"],
                old_str=input_data["old_str"],
                new_str=input_data["new_str"],
            )
            return await self.str_replace(replace_cmd)

        elif command_type == "insert":
            insert_cmd = MemoryInsertCommand(
                command="insert",
                path=input_data["path"],
                insert_line=input_data["insert_line"],
                insert_text=input_data["insert_text"],
            )
            return await self.insert(insert_cmd)

        elif command_type == "delete":
            delete_cmd = MemoryDeleteCommand(
                command="delete",
                path=input_data["path"],
            )
            return await self.delete(delete_cmd)

        elif command_type == "rename":
            rename_cmd = MemoryRenameCommand(
                command="rename",
                old_path=input_data["old_path"],
                new_path=input_data["new_path"],
            )
            return await self.rename(rename_cmd)

        else:
            return f"Error: Unknown command '{command_type}'"

    async def __call__(self, **kwargs: Any) -> str:
        """Allow calling the tool directly."""
        return await self.execute(kwargs)

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to a ToolDefinition for use with agents."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=MEMORY_TOOL_SCHEMA,
            handler=self.__call__,
        )

    def to_anthropic_tool(self) -> dict[str, Any]:
        """Convert to Anthropic's beta memory tool format.

        Use this when making requests to the Anthropic API with the
        context-management-2025-06-27 beta header.
        """
        return {
            "type": "memory_20250818",
            "name": self.name,
        }


# =============================================================================
# File System Memory Tool
# =============================================================================


class FileSystemMemoryTool(BaseMemoryTool):
    """File system-based memory tool implementation.

    Stores memory files in a local directory with path traversal protection.
    """

    MAX_LINE_LIMIT = 999_999

    def __init__(
        self,
        memory_dir: str | Path = "./memories",
        max_depth: int = 2,
    ):
        """Initialize the file system memory tool.

        Args:
            memory_dir: Base directory for memory storage
            max_depth: Maximum directory depth to show in view listings
        """
        self.memory_dir = Path(memory_dir).resolve()
        self.max_depth = max_depth
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str) -> Path:
        """Resolve a memory path to an absolute path with security validation.

        Args:
            path: Path relative to /memories

        Returns:
            Resolved absolute path

        Raises:
            ValueError: If path escapes the memory directory
        """
        # Decode URL-encoded paths
        path = unquote(path)

        # Normalize the path
        if path.startswith("/memories"):
            path = path[len("/memories") :]
        if path.startswith("/"):
            path = path[1:]

        # Reject traversal patterns
        if ".." in path or path.startswith("~"):
            raise ValueError(
                f"Error: Invalid path '{path}' - path traversal not allowed"
            )

        # Resolve and validate
        resolved = (self.memory_dir / path).resolve()

        # Ensure path stays within memory directory
        try:
            resolved.relative_to(self.memory_dir)
        except ValueError:
            raise ValueError(f"Error: Path '{path}' escapes memory directory") from None

        return resolved

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f}K"
        else:
            return f"{size / (1024 * 1024):.1f}M"

    def _list_directory(self, path: Path, depth: int = 0) -> list[tuple[str, int]]:
        """List directory contents recursively up to max_depth.

        Returns list of (path_str, size) tuples.
        """
        entries: list[tuple[str, int]] = []

        if depth > self.max_depth:
            return entries

        try:
            for entry in sorted(path.iterdir()):
                # Skip hidden files and node_modules
                if entry.name.startswith(".") or entry.name == "node_modules":
                    continue

                rel_path = "/memories" + "/" + str(entry.relative_to(self.memory_dir))

                if entry.is_file():
                    entries.append((rel_path, entry.stat().st_size))
                elif entry.is_dir():
                    dir_size = sum(
                        f.stat().st_size for f in entry.rglob("*") if f.is_file()
                    )
                    entries.append((rel_path, dir_size))
                    entries.extend(self._list_directory(entry, depth + 1))
        except PermissionError:
            pass

        return entries

    async def view(self, command: MemoryViewCommand) -> str:
        """View directory contents or file contents."""
        try:
            path = self._resolve_path(command.path)
        except ValueError as e:
            return str(e)

        if not path.exists():
            return (
                f"The path {command.path} does not exist. Please provide a valid path."
            )

        # Directory listing
        if path.is_dir():
            entries = self._list_directory(path)

            # Add the directory itself
            dir_size = sum(size for _, size in entries if not _.endswith("/"))
            lines = [
                f"Here're the files and directories up to 2 levels deep in {command.path}, excluding hidden items and node_modules:"
            ]
            lines.append(f"{self._format_size(dir_size)}\t{command.path}")

            for entry_path, size in entries:
                lines.append(f"{self._format_size(size)}\t{entry_path}")

            return "\n".join(lines)

        # File contents
        try:
            content = path.read_text()
        except Exception as e:
            return f"Error reading file: {e}"

        lines = content.splitlines()

        # Check line limit
        if len(lines) > self.MAX_LINE_LIMIT:
            return f"File {command.path} exceeds maximum line limit of {self.MAX_LINE_LIMIT} lines."

        # Apply view range if specified
        start_line = 1
        end_line = len(lines)
        if command.view_range:
            start_line = max(1, command.view_range[0])
            if len(command.view_range) > 1:
                end_line = min(len(lines), command.view_range[1])

        # Format with line numbers (1-indexed, 6-char width, tab separator)
        result_lines = [f"Here's the content of {command.path} with line numbers:"]
        for i, line in enumerate(lines[start_line - 1 : end_line], start=start_line):
            result_lines.append(f"{i:6}\t{line}")

        return "\n".join(result_lines)

    async def create(self, command: MemoryCreateCommand) -> str:
        """Create a new file."""
        try:
            path = self._resolve_path(command.path)
        except ValueError as e:
            return str(e)

        if path.exists():
            return f"Error: File {command.path} already exists"

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(command.file_text)
            return f"File created successfully at: {command.path}"
        except Exception as e:
            return f"Error creating file: {e}"

    async def str_replace(self, command: MemoryStrReplaceCommand) -> str:
        """Replace text in a file."""
        try:
            path = self._resolve_path(command.path)
        except ValueError as e:
            return str(e)

        if not path.exists() or path.is_dir():
            return f"Error: The path {command.path} does not exist. Please provide a valid path."

        try:
            content = path.read_text()
        except Exception as e:
            return f"Error reading file: {e}"

        # Check for occurrences
        occurrences = content.count(command.old_str)

        if occurrences == 0:
            return f"No replacement was performed, old_str `{command.old_str}` did not appear verbatim in {command.path}."

        if occurrences > 1:
            # Find line numbers of occurrences
            lines = content.splitlines()
            occurrence_lines = []
            for i, line in enumerate(lines, 1):
                if command.old_str in line:
                    occurrence_lines.append(str(i))
            return f"No replacement was performed. Multiple occurrences of old_str `{command.old_str}` in lines: {', '.join(occurrence_lines)}. Please ensure it is unique"

        # Perform replacement
        new_content = content.replace(command.old_str, command.new_str, 1)
        path.write_text(new_content)

        # Show snippet around the change
        new_lines = new_content.splitlines()
        # Find the line with the change
        change_line = 0
        for i, line in enumerate(new_lines):
            if command.new_str in line:
                change_line = i
                break

        # Show context (3 lines before and after)
        start = max(0, change_line - 3)
        end = min(len(new_lines), change_line + 4)

        snippet_lines = ["The memory file has been edited."]
        for i in range(start, end):
            snippet_lines.append(f"{i + 1:6}\t{new_lines[i]}")

        return "\n".join(snippet_lines)

    async def insert(self, command: MemoryInsertCommand) -> str:
        """Insert text at a specific line."""
        try:
            path = self._resolve_path(command.path)
        except ValueError as e:
            return str(e)

        if not path.exists() or path.is_dir():
            return f"Error: The path {command.path} does not exist"

        try:
            content = path.read_text()
        except Exception as e:
            return f"Error reading file: {e}"

        lines = content.splitlines(keepends=True)
        n_lines = len(lines)

        # Validate line number (0-indexed in the spec)
        if command.insert_line < 0 or command.insert_line > n_lines:
            return f"Error: Invalid `insert_line` parameter: {command.insert_line}. It should be within the range of lines of the file: [0, {n_lines}]"

        # Insert the text
        insert_lines = command.insert_text.splitlines(keepends=True)
        if insert_lines and not insert_lines[-1].endswith("\n"):
            insert_lines[-1] += "\n"

        new_lines = (
            lines[: command.insert_line] + insert_lines + lines[command.insert_line :]
        )
        path.write_text("".join(new_lines))

        return f"The file {command.path} has been edited."

    async def delete(self, command: MemoryDeleteCommand) -> str:
        """Delete a file or directory."""
        try:
            path = self._resolve_path(command.path)
        except ValueError as e:
            return str(e)

        if not path.exists():
            return f"Error: The path {command.path} does not exist"

        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            return f"Successfully deleted {command.path}"
        except Exception as e:
            return f"Error deleting: {e}"

    async def rename(self, command: MemoryRenameCommand) -> str:
        """Rename or move a file/directory."""
        try:
            old_path = self._resolve_path(command.old_path)
            new_path = self._resolve_path(command.new_path)
        except ValueError as e:
            return str(e)

        if not old_path.exists():
            return f"Error: The path {command.old_path} does not exist"

        if new_path.exists():
            return f"Error: The destination {command.new_path} already exists"

        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            old_path.rename(new_path)
            return f"Successfully renamed {command.old_path} to {command.new_path}"
        except Exception as e:
            return f"Error renaming: {e}"

    async def clear_all(self) -> str:
        """Clear all memory data."""
        try:
            for item in self.memory_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            return "Successfully cleared all memory"
        except Exception as e:
            return f"Error clearing memory: {e}"


# =============================================================================
# Memory Tool System Prompt
# =============================================================================


MEMORY_SYSTEM_PROMPT = """IMPORTANT: ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE.
MEMORY PROTOCOL:
1. Use the `view` command of your `memory` tool to check for earlier progress.
2. ... (work on the task) ...
   - As you make progress, record status / progress / thoughts etc in your memory.
ASSUME INTERRUPTION: Your context window might be reset at any moment, so you risk losing any progress that is not recorded in your memory directory."""


def get_memory_system_prompt() -> str:
    """Get the recommended system prompt for memory tool usage."""
    return MEMORY_SYSTEM_PROMPT
