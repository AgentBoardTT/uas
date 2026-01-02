"""NotebookEdit tool for modifying Jupyter notebooks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from ...types import ToolDefinition


class NotebookEditTool:
    """Edit Jupyter notebook cells.

    This tool allows editing, inserting, and deleting cells in Jupyter
    notebooks (.ipynb files). It works with cell indices and supports
    both code and markdown cells.
    """

    name = "NotebookEdit"
    description = """Edit Jupyter notebook cells.

Usage:
- Replace cell contents with edit_mode="replace" (default)
- Insert new cells with edit_mode="insert"
- Delete cells with edit_mode="delete"
- cell_number is 0-indexed
- cell_type can be "code" or "markdown"
"""

    def __init__(self, cwd: str | Path | None = None):
        """Initialize the NotebookEdit tool.

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
                "notebook_path": {
                    "type": "string",
                    "description": "The absolute path to the Jupyter notebook file",
                },
                "cell_number": {
                    "type": "integer",
                    "description": "The 0-indexed cell number to edit",
                },
                "new_source": {
                    "type": "string",
                    "description": "The new source content for the cell",
                },
                "cell_type": {
                    "type": "string",
                    "enum": ["code", "markdown"],
                    "description": "The type of cell (code or markdown)",
                },
                "edit_mode": {
                    "type": "string",
                    "enum": ["replace", "insert", "delete"],
                    "description": "The edit mode: replace, insert, or delete",
                },
            },
            "required": ["notebook_path", "new_source"],
        }

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a file path, handling relative paths."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.cwd / path
        return path.resolve()

    def _read_notebook(self, path: Path) -> dict[str, Any]:
        """Read and parse a Jupyter notebook."""
        content = path.read_text()
        result: dict[str, Any] = json.loads(content)
        return result

    def _write_notebook(self, path: Path, notebook: dict[str, Any]) -> None:
        """Write a notebook back to disk."""
        content = json.dumps(notebook, indent=1, ensure_ascii=False)
        path.write_text(content)

    def _create_cell(
        self,
        cell_type: Literal["code", "markdown"],
        source: str,
    ) -> dict[str, Any]:
        """Create a new notebook cell."""
        cell: dict[str, Any] = {
            "cell_type": cell_type,
            "metadata": {},
            "source": source.splitlines(keepends=True),
        }

        if cell_type == "code":
            cell["execution_count"] = None
            cell["outputs"] = []

        return cell

    async def __call__(
        self,
        notebook_path: str,
        new_source: str,
        cell_number: int | None = None,
        cell_type: Literal["code", "markdown"] | None = None,
        edit_mode: Literal["replace", "insert", "delete"] = "replace",
    ) -> str:
        """Edit a Jupyter notebook cell.

        Args:
            notebook_path: Path to the notebook file
            new_source: New content for the cell
            cell_number: 0-indexed cell number (defaults to 0)
            cell_type: Type of cell (code/markdown), required for insert
            edit_mode: The edit operation to perform

        Returns:
            Success message or error
        """
        try:
            path = self._resolve_path(notebook_path)

            if not path.exists():
                return f"Error: Notebook not found: {notebook_path}"

            if path.suffix != ".ipynb":
                return f"Error: Not a Jupyter notebook: {notebook_path}"

            # Read the notebook
            notebook = self._read_notebook(path)

            if "cells" not in notebook:
                return "Error: Invalid notebook format - no cells found"

            cells = notebook["cells"]
            cell_idx = cell_number if cell_number is not None else 0

            if edit_mode == "delete":
                # Delete a cell
                if cell_idx < 0 or cell_idx >= len(cells):
                    return f"Error: Cell index {cell_idx} out of range (0-{len(cells) - 1})"

                deleted_cell = cells.pop(cell_idx)
                self._write_notebook(path, notebook)
                return f"Deleted cell {cell_idx} ({deleted_cell.get('cell_type', 'unknown')} cell)"

            elif edit_mode == "insert":
                # Insert a new cell
                if cell_type is None:
                    return "Error: cell_type is required for insert mode"

                if cell_idx < 0 or cell_idx > len(cells):
                    return f"Error: Cell index {cell_idx} out of range for insert (0-{len(cells)})"

                new_cell = self._create_cell(cell_type, new_source)
                cells.insert(cell_idx, new_cell)
                self._write_notebook(path, notebook)
                return f"Inserted new {cell_type} cell at position {cell_idx}"

            else:  # replace
                if cell_idx < 0 or cell_idx >= len(cells):
                    return f"Error: Cell index {cell_idx} out of range (0-{len(cells) - 1})"

                cell = cells[cell_idx]
                old_type = cell.get("cell_type", "code")

                # Update cell type if specified
                if cell_type and cell_type != old_type:
                    cell["cell_type"] = cell_type
                    if cell_type == "code":
                        cell["execution_count"] = None
                        cell["outputs"] = []
                    elif "outputs" in cell:
                        del cell["outputs"]
                    if "execution_count" in cell and cell_type != "code":
                        del cell["execution_count"]

                # Update source
                cell["source"] = new_source.splitlines(keepends=True)

                self._write_notebook(path, notebook)

                # Show a snippet of the new content
                lines = new_source.splitlines()
                preview = "\n".join(lines[:5])
                if len(lines) > 5:
                    preview += f"\n... ({len(lines)} lines total)"

                return f"Replaced cell {cell_idx} content:\n\n{preview}"

        except json.JSONDecodeError as e:
            return f"Error: Invalid notebook JSON: {e}"
        except PermissionError:
            return f"Error: Permission denied: {notebook_path}"
        except Exception as e:
            return f"Error editing notebook: {e}"

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to a ToolDefinition for use with agents."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.__call__,
        )
