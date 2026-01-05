"""Read tool for reading file contents."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any

from ...types import ToolDefinition


class ReadTool:
    """Read file contents with line numbers.

    This tool reads files from the filesystem and returns their contents
    with line numbers. It supports text files, images (as base64), and
    can read specific line ranges for large files.
    """

    name = "Read"
    description = """Reads a file from the local filesystem.

Usage:
- The file_path parameter must be an absolute path
- By default reads up to 2000 lines from the beginning
- Can specify offset and limit for large files
- Lines longer than 2000 characters are truncated
- Results returned with line numbers starting at 1
- Can read images (PNG, JPG, etc.) which are returned as base64
- Can read PDF files (text extraction)
"""

    def __init__(
        self,
        max_lines: int = 2000,
        max_line_length: int = 2000,
        cwd: str | Path | None = None,
    ):
        """Initialize the Read tool.

        Args:
            max_lines: Maximum number of lines to read (default 2000)
            max_line_length: Maximum characters per line before truncation
            cwd: Working directory for relative paths
        """
        self.max_lines = max_lines
        self.max_line_length = max_line_length
        self.cwd = Path(cwd) if cwd else Path.cwd()

    @property
    def input_schema(self) -> dict[str, Any]:
        """Get the input schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to read",
                },
                "offset": {
                    "type": "integer",
                    "description": "Line number to start reading from (1-indexed). Only needed for large files.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of lines to read. Only needed for large files.",
                },
            },
            "required": ["file_path"],
        }

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a file path, handling relative paths."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.cwd / path
        return path.resolve()

    def _is_binary(self, path: Path) -> bool:
        """Check if a file is binary."""
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type:
            if mime_type.startswith("image/"):
                return True
            if mime_type == "application/pdf":
                return True
        # Try reading first chunk to detect binary
        try:
            with path.open("rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk:
                    return True
        except Exception:
            pass
        return False

    def _read_image(self, path: Path) -> str:
        """Read an image file and return as base64."""
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "application/octet-stream"

        with path.open("rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")

        return f"[Image: {path.name}]\nMIME type: {mime_type}\nBase64 data: {data[:100]}... (truncated)"

    def _read_pdf(self, path: Path) -> str:
        """Read a PDF file and extract text."""
        try:
            import pdfplumber  # type: ignore[import-not-found]

            text_parts = []
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages[:20], 1):  # Limit to 20 pages
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"=== Page {i} ===\n{text}")

            return (
                "\n\n".join(text_parts)
                if text_parts
                else "(No text extracted from PDF)"
            )
        except ImportError:
            return "Error: pdfplumber not installed. Run: pip install pdfplumber"
        except Exception as e:
            return f"Error reading PDF: {e}"

    async def __call__(
        self,
        file_path: str,
        offset: int | None = None,
        limit: int | None = None,
    ) -> str:
        """Read a file and return its contents.

        Args:
            file_path: Path to the file to read
            offset: Line number to start from (1-indexed)
            limit: Number of lines to read

        Returns:
            File contents with line numbers
        """
        try:
            path = self._resolve_path(file_path)

            if not path.exists():
                return f"Error: File not found: {file_path}"

            if not path.is_file():
                return f"Error: Not a file: {file_path}"

            # Handle images
            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type and mime_type.startswith("image/"):
                return self._read_image(path)

            # Handle PDFs
            if path.suffix.lower() == ".pdf":
                return self._read_pdf(path)

            # Handle binary files
            if self._is_binary(path):
                return f"Error: Cannot read binary file: {file_path}"

            # Read text file
            with path.open(encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)

            # Apply offset and limit
            start_line = 1
            end_line = total_lines
            max_read = limit or self.max_lines

            if offset:
                start_line = max(1, offset)

            end_line = min(start_line + max_read - 1, total_lines)

            # Format with line numbers
            result_lines = []
            for i in range(start_line - 1, end_line):
                line = lines[i].rstrip("\n\r")
                # Truncate long lines
                if len(line) > self.max_line_length:
                    line = line[: self.max_line_length] + "..."
                result_lines.append(f"{i + 1:6}\t{line}")

            # Add metadata if partial read
            if start_line > 1 or end_line < total_lines:
                header = f"[Lines {start_line}-{end_line} of {total_lines}]"
                result_lines.insert(0, header)

            return "\n".join(result_lines)

        except PermissionError:
            return f"Error: Permission denied: {file_path}"
        except Exception as e:
            return f"Error reading file: {e}"

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to a ToolDefinition for use with agents."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.__call__,
        )
