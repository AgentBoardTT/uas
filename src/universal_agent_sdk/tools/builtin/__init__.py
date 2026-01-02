"""Builtin tools for Universal Agent SDK.

These tools mirror the functionality of Claude Code CLI's builtin tools,
providing file operations, code search, shell execution, and web capabilities.

Available tools:
- ReadTool: Read file contents with line numbers
- WriteTool: Create or overwrite files
- EditTool: Edit files using string replacement
- BashTool: Execute shell commands
- GlobTool: Find files by pattern matching
- GrepTool: Search file contents using regex
- NotebookEditTool: Edit Jupyter notebooks
- WebSearchTool: Search the web using DuckDuckGo
- WebFetchTool: Fetch and extract content from web pages

Example usage:
    ```python
    from universal_agent_sdk.tools.builtin import (
        ReadTool,
        WriteTool,
        BashTool,
        GlobTool,
        GrepTool,
        WebSearchTool,
        WebFetchTool,
    )

    # Create tools
    read = ReadTool()
    bash = BashTool(timeout=30)
    glob = GlobTool()
    grep = GrepTool()
    web_search = WebSearchTool()
    web_fetch = WebFetchTool()

    # Use directly
    content = await read(file_path="/path/to/file.py")
    files = await glob(pattern="**/*.py")
    matches = await grep(pattern="def main", path="src/")
    results = await web_search(query="python async programming")
    page = await web_fetch(url="https://example.com")

    # Use with agents
    options = AgentOptions(
        tools=[
            read.to_tool_definition(),
            bash.to_tool_definition(),
            web_search.to_tool_definition(),
        ],
    )
    ```
"""

from .bash import BashTool
from .datetime_tool import DateTimeTool
from .edit import EditTool
from .glob import GlobTool
from .grep import GrepTool
from .notebook_edit import NotebookEditTool
from .read import ReadTool
from .web_fetch import WebFetchTool
from .web_search import WebSearchTool
from .write import WriteTool

__all__ = [
    "ReadTool",
    "WriteTool",
    "EditTool",
    "BashTool",
    "GlobTool",
    "GrepTool",
    "NotebookEditTool",
    "WebSearchTool",
    "WebFetchTool",
    "DateTimeTool",
]
