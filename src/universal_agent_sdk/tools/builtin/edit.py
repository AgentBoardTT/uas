"""Edit tool for modifying files using string replacement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...types import ToolDefinition


class EditTool:
    """Edit files using exact string replacement.

    This tool performs precise text replacements in files. It requires
    the exact text to be replaced (old_string) and the replacement text
    (new_string). The replacement must be unique in the file.
    """

    name = "Edit"
    description = """Performs exact string replacements in files.

Usage:
- old_string must match exactly in the file (including whitespace/indentation)
- The match must be unique unless replace_all is true
- Use replace_all to rename variables or replace all occurrences
- Preserves file encoding and line endings
"""

    def __init__(self, cwd: str | Path | None = None):
        """Initialize the Edit tool.

        Args:
            cwd: Working directory for relative paths
        """
        self.cwd = Path(cwd) if cwd else Path.cwd()

    @property
    def input_schema(self) -> dict[str, Any]:
        """Get the input schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to modify",
                },
                "old_string": {
                    "type": "string",
                    "description": "The exact text to replace",
                },
                "new_string": {
                    "type": "string",
                    "description": "The text to replace it with (must be different from old_string)",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences (default: false)",
                    "default": False,
                },
            },
            "required": ["file_path", "old_string", "new_string"],
        }

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a file path, handling relative paths."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.cwd / path
        return path.resolve()

    def _find_occurrences(self, content: str, old_string: str) -> list[int]:
        """Find all occurrences of a string and return their line numbers."""
        lines = content.splitlines()
        occurrences = []
        for i, line in enumerate(lines, 1):
            if old_string in line or (
                old_string in content
                and content.splitlines()[i - 1 : i + old_string.count("\n")]
            ):
                occurrences.append(i)
        return occurrences

    async def __call__(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> str:
        """Edit a file by replacing text.

        Args:
            file_path: Path to the file to edit
            old_string: Text to find and replace
            new_string: Replacement text
            replace_all: Whether to replace all occurrences

        Returns:
            Success message with snippet or error message
        """
        try:
            path = self._resolve_path(file_path)

            if not path.exists():
                return f"Error: File not found: {file_path}"

            if not path.is_file():
                return f"Error: Not a file: {file_path}"

            if old_string == new_string:
                return "Error: old_string and new_string are identical"

            # Read the file
            content = path.read_text()

            # Count occurrences
            count = content.count(old_string)

            if count == 0:
                return f"Error: old_string not found in {file_path}"

            if count > 1 and not replace_all:
                # Find line numbers
                lines = content.splitlines()
                occurrence_lines = []
                for i, line in enumerate(lines, 1):
                    if old_string in line:
                        occurrence_lines.append(str(i))
                return (
                    f"Error: Found {count} occurrences of old_string in lines: "
                    f"{', '.join(occurrence_lines[:10])}. "
                    "Use replace_all=true or provide more context to make it unique."
                )

            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
            else:
                new_content = content.replace(old_string, new_string, 1)

            # Write back
            path.write_text(new_content)

            # Find the line with the change for the snippet
            new_lines = new_content.splitlines()
            change_line = 0
            for i, line in enumerate(new_lines):
                if new_string in line or (i > 0 and new_string.split("\n")[0] in line):
                    change_line = i
                    break

            # Show context (3 lines before and after)
            start = max(0, change_line - 3)
            end = min(len(new_lines), change_line + 4)

            snippet_lines = []
            for i in range(start, end):
                snippet_lines.append(f"{i + 1:6}\t{new_lines[i]}")

            if replace_all and count > 1:
                result = f"Replaced {count} occurrences.\n\n"
            else:
                result = "Edit successful.\n\n"

            result += "Snippet:\n" + "\n".join(snippet_lines)
            return result

        except PermissionError:
            return f"Error: Permission denied: {file_path}"
        except Exception as e:
            return f"Error editing file: {e}"

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to a ToolDefinition for use with agents."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.__call__,
        )
