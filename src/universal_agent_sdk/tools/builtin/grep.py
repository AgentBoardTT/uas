"""Grep tool for searching file contents."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Literal

from ...types import ToolDefinition


class GrepTool:
    """Search file contents using regular expressions.

    This tool searches for patterns in files, similar to ripgrep (rg).
    It supports regex patterns, file type filtering, and various output modes.
    """

    name = "Grep"
    description = """Search tool for finding patterns in file contents.

Usage:
- Supports full regex syntax (e.g., "log.*Error", "function\\s+\\w+")
- Filter files with glob parameter (e.g., "*.js") or type parameter (e.g., "py")
- Output modes: "content" (matching lines), "files_with_matches" (file paths only), "count"
- Use for finding code patterns, function definitions, imports, etc.
"""

    MAX_RESULTS = 1000
    MAX_CONTEXT_LINES = 10

    # Common file type extensions
    TYPE_EXTENSIONS = {
        "py": [".py", ".pyi"],
        "js": [".js", ".mjs", ".cjs"],
        "ts": [".ts", ".tsx", ".mts", ".cts"],
        "jsx": [".jsx"],
        "tsx": [".tsx"],
        "rust": [".rs"],
        "go": [".go"],
        "java": [".java"],
        "c": [".c", ".h"],
        "cpp": [".cpp", ".hpp", ".cc", ".hh", ".cxx", ".hxx"],
        "ruby": [".rb"],
        "php": [".php"],
        "swift": [".swift"],
        "kotlin": [".kt", ".kts"],
        "scala": [".scala"],
        "html": [".html", ".htm"],
        "css": [".css"],
        "scss": [".scss", ".sass"],
        "json": [".json"],
        "yaml": [".yaml", ".yml"],
        "xml": [".xml"],
        "md": [".md", ".markdown"],
        "txt": [".txt"],
        "sh": [".sh", ".bash"],
        "sql": [".sql"],
    }

    def __init__(
        self,
        cwd: str | Path | None = None,
        max_results: int | None = None,
    ):
        """Initialize the Grep tool.

        Args:
            cwd: Working directory for searches
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
                    "description": "The regex pattern to search for",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in (defaults to current directory)",
                },
                "glob": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g., '*.py', '*.{ts,tsx}')",
                },
                "type": {
                    "type": "string",
                    "description": "File type to search (e.g., 'py', 'js', 'rust')",
                },
                "output_mode": {
                    "type": "string",
                    "enum": ["content", "files_with_matches", "count"],
                    "description": "Output mode: content (matching lines), files_with_matches (paths only), count",
                },
                "-i": {
                    "type": "boolean",
                    "description": "Case insensitive search",
                },
                "-n": {
                    "type": "boolean",
                    "description": "Show line numbers (default true for content mode)",
                },
                "-A": {
                    "type": "integer",
                    "description": "Number of lines to show after each match",
                },
                "-B": {
                    "type": "integer",
                    "description": "Number of lines to show before each match",
                },
                "-C": {
                    "type": "integer",
                    "description": "Number of lines of context (before and after)",
                },
                "multiline": {
                    "type": "boolean",
                    "description": "Enable multiline mode where . matches newlines",
                },
                "head_limit": {
                    "type": "integer",
                    "description": "Limit output to first N results",
                },
            },
            "required": ["pattern"],
        }

    def _matches_type(self, path: Path, file_type: str) -> bool:
        """Check if a file matches the specified type."""
        extensions = self.TYPE_EXTENSIONS.get(file_type.lower(), [f".{file_type}"])
        return path.suffix.lower() in extensions

    def _matches_glob(self, path: Path, glob_pattern: str) -> bool:
        """Check if a file matches the glob pattern."""
        import fnmatch

        return fnmatch.fnmatch(path.name, glob_pattern)

    def _search_file(
        self,
        path: Path,
        regex: re.Pattern[str],
        context_before: int = 0,
        context_after: int = 0,
        show_line_numbers: bool = True,
    ) -> list[dict[str, Any]]:
        """Search a single file for matches."""
        results = []
        try:
            content = path.read_text(errors="replace")
            lines = content.splitlines()

            for i, line in enumerate(lines):
                if regex.search(line):
                    match_info: dict[str, Any] = {
                        "file": str(path),
                        "line_number": i + 1,
                        "line": line,
                    }

                    # Add context if requested
                    if context_before > 0:
                        start = max(0, i - context_before)
                        match_info["context_before"] = [
                            (j + 1, lines[j]) for j in range(start, i)
                        ]

                    if context_after > 0:
                        end = min(len(lines), i + context_after + 1)
                        match_info["context_after"] = [
                            (j + 1, lines[j]) for j in range(i + 1, end)
                        ]

                    results.append(match_info)

        except (OSError, UnicodeDecodeError, PermissionError):
            pass

        return results

    async def __call__(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
        type: str | None = None,
        output_mode: Literal[
            "content", "files_with_matches", "count"
        ] = "files_with_matches",
        multiline: bool = False,
        head_limit: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Search for a pattern in files.

        Args:
            pattern: Regex pattern to search for
            path: File or directory to search
            glob: Glob pattern to filter files
            type: File type to filter
            output_mode: How to format output
            multiline: Enable multiline matching
            head_limit: Limit number of results
            **kwargs: Additional options (-i, -n, -A, -B, -C)

        Returns:
            Search results formatted according to output_mode
        """
        # Parse kwargs
        case_insensitive = kwargs.get("-i", False)
        show_line_numbers = kwargs.get("-n", output_mode == "content")
        context_before = min(kwargs.get("-B", 0), self.MAX_CONTEXT_LINES)
        context_after = min(kwargs.get("-A", 0), self.MAX_CONTEXT_LINES)
        context = kwargs.get("-C", 0)
        if context:
            context_before = min(context, self.MAX_CONTEXT_LINES)
            context_after = min(context, self.MAX_CONTEXT_LINES)

        # Compile regex
        flags = 0
        if case_insensitive:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.MULTILINE | re.DOTALL

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return f"Error: Invalid regex pattern: {e}"

        # Determine search path
        search_path = Path(path) if path else self.cwd
        if not search_path.is_absolute():
            search_path = self.cwd / search_path
        search_path = search_path.resolve()

        if not search_path.exists():
            return f"Error: Path not found: {path or '.'}"

        # Collect files to search
        files_to_search: list[Path] = []

        if search_path.is_file():
            files_to_search = [search_path]
        else:
            # Recursively find files
            for root, dirs, files in os.walk(search_path):
                # Skip hidden directories and common non-code directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d
                    not in ("node_modules", "__pycache__", ".git", "venv", ".venv")
                ]

                for f in files:
                    if f.startswith("."):
                        continue

                    file_path = Path(root) / f

                    # Apply type filter
                    if type and not self._matches_type(file_path, type):
                        continue

                    # Apply glob filter
                    if glob and not self._matches_glob(file_path, glob):
                        continue

                    files_to_search.append(file_path)

        # Search files
        all_results: list[dict[str, Any]] = []
        files_with_matches: set[str] = set()

        for file_path in files_to_search:
            matches = self._search_file(
                file_path,
                regex,
                context_before=context_before if output_mode == "content" else 0,
                context_after=context_after if output_mode == "content" else 0,
            )

            if matches:
                files_with_matches.add(str(file_path))
                all_results.extend(matches)

                # Early exit if we have enough results
                if len(all_results) >= self.max_results:
                    break

        # Apply head limit
        limit = head_limit or self.max_results
        truncated = len(all_results) > limit
        all_results = all_results[:limit]

        # Format output based on mode
        if output_mode == "files_with_matches":
            sorted_files = sorted(files_with_matches)[:limit]
            if not sorted_files:
                return f"No matches found for pattern: {pattern}"
            result = "\n".join(sorted_files)
            if truncated:
                result += f"\n\n... ({len(files_with_matches)} files total)"
            return result

        elif output_mode == "count":
            counts: dict[str, int] = {}
            for match in all_results:
                file = match["file"]
                counts[file] = counts.get(file, 0) + 1
            sorted_counts = sorted(counts.items())[:limit]
            if not sorted_counts:
                return f"No matches found for pattern: {pattern}"
            return "\n".join(f"{file}: {count}" for file, count in sorted_counts)

        else:  # content
            if not all_results:
                return f"No matches found for pattern: {pattern}"

            output_lines = []
            current_file = None

            for match in all_results:
                file = match["file"]
                if file != current_file:
                    if current_file is not None:
                        output_lines.append("")  # Blank line between files
                    output_lines.append(f"=== {file} ===")
                    current_file = file

                # Add context before
                for line_num, line in match.get("context_before", []):
                    output_lines.append(f"{line_num:6}-\t{line}")

                # Add matching line
                line_num = match["line_number"]
                line = match["line"]
                if show_line_numbers:
                    output_lines.append(f"{line_num:6}:\t{line}")
                else:
                    output_lines.append(line)

                # Add context after
                for line_num, line in match.get("context_after", []):
                    output_lines.append(f"{line_num:6}-\t{line}")

            if truncated:
                output_lines.append(f"\n... (truncated at {limit} results)")

            return "\n".join(output_lines)

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to a ToolDefinition for use with agents."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.__call__,
        )
