"""Glob tool for file pattern matching."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...types import ToolDefinition


class GlobTool:
    """Find files using glob patterns.

    This tool finds files matching glob patterns like "**/*.py" or
    "src/**/*.ts". Results are sorted by modification time (newest first).
    """

    name = "Glob"
    description = """Fast file pattern matching tool.

Usage:
- Supports glob patterns like "**/*.js" or "src/**/*.ts"
- Returns matching file paths sorted by modification time
- Use when you need to find files by name patterns
- Examples:
  - "**/*.py" - all Python files
  - "src/**/*.ts" - TypeScript files in src/
  - "*.md" - Markdown files in current directory
"""

    MAX_RESULTS = 1000

    def __init__(
        self,
        cwd: str | Path | None = None,
        max_results: int | None = None,
    ):
        """Initialize the Glob tool.

        Args:
            cwd: Working directory for relative patterns
            max_results: Maximum number of results to return
        """
        self.cwd = Path(cwd) if cwd else Path.cwd()
        self.max_results = max_results or self.MAX_RESULTS

    @property
    def input_schema(self) -> dict[str, Any]:
        """Get the input schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The glob pattern to match files against (e.g., '**/*.py')",
                },
                "path": {
                    "type": "string",
                    "description": "The directory to search in (defaults to current directory)",
                },
            },
            "required": ["pattern"],
        }

    def _get_mtime(self, path: Path) -> float:
        """Get modification time of a file, returning 0 on error."""
        try:
            return path.stat().st_mtime
        except (OSError, PermissionError):
            return 0.0

    async def __call__(
        self,
        pattern: str,
        path: str | None = None,
    ) -> str:
        """Find files matching a glob pattern.

        Args:
            pattern: Glob pattern to match
            path: Directory to search in (defaults to cwd)

        Returns:
            List of matching file paths, one per line
        """
        search_dir = Path(path) if path else self.cwd
        if not search_dir.is_absolute():
            search_dir = self.cwd / search_dir
        search_dir = search_dir.resolve()

        if not search_dir.exists():
            return f"Error: Directory not found: {path or '.'}"

        if not search_dir.is_dir():
            return f"Error: Not a directory: {path or '.'}"

        try:
            # Use pathlib glob for pattern matching
            if "**" in pattern:
                # Recursive pattern
                matches = list(search_dir.glob(pattern))
            else:
                # Non-recursive pattern
                matches = list(search_dir.glob(pattern))

            # Filter to files only and sort by modification time
            files = [m for m in matches if m.is_file()]
            files.sort(key=self._get_mtime, reverse=True)

            # Limit results
            if len(files) > self.max_results:
                files = files[: self.max_results]
                truncated = True
            else:
                truncated = False

            if not files:
                return f"No files found matching pattern: {pattern}"

            # Format output
            result_lines = []
            for f in files:
                # Show path relative to search dir if possible
                try:
                    rel_path = f.relative_to(search_dir)
                    result_lines.append(str(rel_path))
                except ValueError:
                    result_lines.append(str(f))

            if truncated:
                result_lines.append(f"\n... (showing first {self.max_results} results)")

            return "\n".join(result_lines)

        except Exception as e:
            return f"Error searching files: {e}"

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to a ToolDefinition for use with agents."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.__call__,
        )
