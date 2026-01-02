"""Coding Agent example for Universal Agent SDK.

This example demonstrates how to build a coding agent that can:
- Read and analyze code files
- Write and modify code
- Execute Python code safely
- Search for patterns in codebases

The agent uses tools to interact with the filesystem and execute code.
"""

import asyncio
import subprocess
import tempfile
from pathlib import Path

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    query,
    tool,
)


# File system tools
@tool
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: Path to the file to read
    """
    try:
        file_path = Path(path).expanduser()
        if not file_path.exists():
            return f"Error: File not found: {path}"
        if not file_path.is_file():
            return f"Error: Not a file: {path}"
        content = file_path.read_text()
        return content
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file.

    Args:
        path: Path to the file to write
        content: Content to write to the file
    """
    try:
        file_path = Path(path).expanduser()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def list_directory(path: str = ".") -> str:
    """List contents of a directory.

    Args:
        path: Path to the directory to list (defaults to current directory)
    """
    try:
        dir_path = Path(path).expanduser()
        if not dir_path.exists():
            return f"Error: Directory not found: {path}"
        if not dir_path.is_dir():
            return f"Error: Not a directory: {path}"

        entries = []
        for entry in sorted(dir_path.iterdir()):
            if entry.is_dir():
                entries.append(f"[DIR]  {entry.name}/")
            else:
                size = entry.stat().st_size
                entries.append(f"[FILE] {entry.name} ({size} bytes)")

        return "\n".join(entries) if entries else "Directory is empty"
    except Exception as e:
        return f"Error listing directory: {e}"


@tool
def search_files(pattern: str, directory: str = ".") -> str:
    """Search for files matching a pattern.

    Args:
        pattern: Glob pattern to match (e.g., "*.py", "**/*.txt")
        directory: Directory to search in (defaults to current directory)
    """
    try:
        dir_path = Path(directory).expanduser()
        matches = list(dir_path.glob(pattern))
        if not matches:
            return f"No files found matching pattern: {pattern}"
        return "\n".join(str(m) for m in matches[:50])  # Limit to 50 results
    except Exception as e:
        return f"Error searching files: {e}"


@tool
def search_in_files(
    query: str, file_pattern: str = "*.py", directory: str = "."
) -> str:
    """Search for text within files.

    Args:
        query: Text to search for
        file_pattern: Glob pattern for files to search (e.g., "*.py")
        directory: Directory to search in
    """
    try:
        dir_path = Path(directory).expanduser()
        results = []

        for file_path in dir_path.glob(file_pattern):
            if file_path.is_file():
                try:
                    content = file_path.read_text()
                    for i, line in enumerate(content.splitlines(), 1):
                        if query.lower() in line.lower():
                            results.append(f"{file_path}:{i}: {line.strip()}")
                except Exception:
                    continue

        if not results:
            return f"No matches found for '{query}' in {file_pattern} files"
        return "\n".join(results[:100])  # Limit to 100 results
    except Exception as e:
        return f"Error searching in files: {e}"


# Code execution tools
@tool
def run_python(code: str) -> str:
    """Execute Python code in a safe environment.

    Args:
        code: Python code to execute
    """
    try:
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            # Run with timeout
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path.cwd(),
            )

            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            if result.returncode != 0:
                output += f"Exit code: {result.returncode}"

            return output if output else "Code executed successfully (no output)"
        finally:
            Path(temp_path).unlink()

    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (30 second limit)"
    except Exception as e:
        return f"Error executing code: {e}"


@tool
def run_shell(command: str) -> str:
    """Execute a shell command.

    Args:
        command: Shell command to execute
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path.cwd(),
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"

        return output if output else "Command executed successfully (no output)"

    except subprocess.TimeoutExpired:
        return "Error: Command timed out (30 second limit)"
    except Exception as e:
        return f"Error executing command: {e}"


async def main():
    """Run the coding agent example."""
    print("=== Coding Agent Example ===\n")

    # Create options with all coding tools
    options = AgentOptions(
        tools=[
            read_file.definition,
            write_file.definition,
            list_directory.definition,
            search_files.definition,
            search_in_files.definition,
            run_python.definition,
            run_shell.definition,
        ],
        max_turns=10,
        system_prompt="""You are a helpful coding assistant. You can:
- Read and analyze code files
- Write and modify code
- Search for files and patterns
- Execute Python code and shell commands

When asked to complete coding tasks:
1. First understand the requirements
2. Explore the codebase if needed
3. Write clean, well-documented code
4. Test your code when possible
5. Explain what you did

Always be careful with file modifications and code execution.""",
    )

    # Example 1: Explore the codebase
    print("--- Example 1: Explore Codebase ---")
    print("User: What Python files are in the examples directory?\n")

    async for msg in query("What Python files are in the examples directory?", options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[Tool: {block.name}]")
                elif isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
    print("\n")

    # Example 2: Write a simple script
    print("--- Example 2: Write a Script ---")
    print(
        "User: Write a Python function that calculates Fibonacci numbers and save it to /tmp/fibonacci.py\n"
    )

    async for msg in query(
        "Write a Python function that calculates Fibonacci numbers and save it to /tmp/fibonacci.py",
        options,
    ):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[Tool: {block.name}]")
                elif isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
    print("\n")

    # Example 3: Run and test code
    print("--- Example 3: Run Code ---")
    print("User: Run the fibonacci function with n=10 and show the result\n")

    async for msg in query(
        "Run the fibonacci function from /tmp/fibonacci.py with n=10 and show the result",
        options,
    ):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[Tool: {block.name}]")
                elif isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")


if __name__ == "__main__":
    asyncio.run(main())
