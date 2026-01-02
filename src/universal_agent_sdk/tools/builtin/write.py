"""Write tool for creating or overwriting files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...types import ToolDefinition


class WriteTool:
    """Write content to a file.

    This tool creates new files or overwrites existing files with the
    provided content. It automatically creates parent directories if needed.
    """

    name = "Write"
    description = """Writes content to a file on the local filesystem.

Usage:
- The file_path parameter must be an absolute path
- This tool will overwrite existing files
- Parent directories are created automatically
- Use Edit tool for modifying existing files instead of full rewrites
"""

    def __init__(
        self,
        cwd: str | Path | None = None,
        create_dirs: bool = True,
    ):
        """Initialize the Write tool.

        Args:
            cwd: Working directory for relative paths
            create_dirs: Whether to create parent directories if needed
        """
        self.cwd = Path(cwd) if cwd else Path.cwd()
        self.create_dirs = create_dirs

    @property
    def input_schema(self) -> dict[str, Any]:
        """Get the input schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file",
                },
            },
            "required": ["file_path", "content"],
        }

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a file path, handling relative paths."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.cwd / path
        return path.resolve()

    async def __call__(
        self,
        file_path: str,
        content: str,
    ) -> str:
        """Write content to a file.

        Args:
            file_path: Path to the file to write
            content: Content to write

        Returns:
            Success or error message
        """
        try:
            path = self._resolve_path(file_path)

            # Create parent directories if needed
            if self.create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Check if parent exists
            if not path.parent.exists():
                return f"Error: Parent directory does not exist: {path.parent}"

            # Write the file
            path.write_text(content)

            return f"Successfully wrote {len(content)} characters to {file_path}"

        except PermissionError:
            return f"Error: Permission denied: {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to a ToolDefinition for use with agents."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.__call__,
        )
