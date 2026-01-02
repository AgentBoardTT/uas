#!/usr/bin/env python
"""Example demonstrating the builtin tools in Universal Agent SDK.

This example shows how to use the builtin tools that mirror Claude Code CLI's
functionality: Read, Write, Edit, Bash, Glob, Grep, and NotebookEdit.

Usage:
    python examples/builtin_tools_example.py
"""

import asyncio
import os
import tempfile
from pathlib import Path

from universal_agent_sdk import AgentOptions, query
from universal_agent_sdk.tools import (
    BashTool,
    EditTool,
    GlobTool,
    GrepTool,
    NotebookEditTool,
    ReadTool,
    WriteTool,
)


async def demo_read_tool(temp_dir: Path) -> None:
    """Demonstrate the ReadTool."""
    print("\n" + "=" * 60)
    print("ReadTool Demo")
    print("=" * 60)

    # Create a sample file
    sample_file = temp_dir / "sample.py"
    sample_file.write_text("""#!/usr/bin/env python
\"\"\"Sample Python file for testing.\"\"\"

def greet(name: str) -> str:
    \"\"\"Return a greeting message.\"\"\"
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b

if __name__ == "__main__":
    print(greet("World"))
    print(f"2 + 3 = {add(2, 3)}")
""")

    # Use the ReadTool
    read_tool = ReadTool(cwd=temp_dir)
    result = await read_tool(str(sample_file))
    print(f"\nReading {sample_file.name}:")
    print(result)


async def demo_write_tool(temp_dir: Path) -> None:
    """Demonstrate the WriteTool."""
    print("\n" + "=" * 60)
    print("WriteTool Demo")
    print("=" * 60)

    write_tool = WriteTool(cwd=temp_dir)

    # Write a new file
    new_file = temp_dir / "output.txt"
    result = await write_tool(str(new_file), "Hello from WriteTool!\nThis is line 2.")
    print(f"\n{result}")

    # Verify the file was created
    print(f"File contents: {new_file.read_text()}")


async def demo_edit_tool(temp_dir: Path) -> None:
    """Demonstrate the EditTool."""
    print("\n" + "=" * 60)
    print("EditTool Demo")
    print("=" * 60)

    # Create a file to edit
    edit_file = temp_dir / "to_edit.txt"
    edit_file.write_text("The quick brown fox jumps over the lazy dog.\nThis is a sample text file.\n")

    edit_tool = EditTool(cwd=temp_dir)

    # Edit the file
    result = await edit_tool(
        str(edit_file),
        old_string="brown fox",
        new_string="red fox",
    )
    print(f"\n{result}")

    # Show the result
    print(f"\nFile after edit: {edit_file.read_text()}")


async def demo_bash_tool(temp_dir: Path) -> None:
    """Demonstrate the BashTool."""
    print("\n" + "=" * 60)
    print("BashTool Demo")
    print("=" * 60)

    bash_tool = BashTool(cwd=temp_dir, timeout=30)

    # Run some commands
    commands = [
        ("pwd", "Show current directory"),
        ("ls -la", "List directory contents"),
        ("echo 'Hello from Bash!' > bash_output.txt && cat bash_output.txt", "Write and read file"),
    ]

    for cmd, description in commands:
        print(f"\n{description} ({cmd}):")
        result = await bash_tool(cmd, description=description)
        print(result)


async def demo_glob_tool(temp_dir: Path) -> None:
    """Demonstrate the GlobTool."""
    print("\n" + "=" * 60)
    print("GlobTool Demo")
    print("=" * 60)

    # Create some files
    (temp_dir / "src").mkdir(exist_ok=True)
    (temp_dir / "src" / "main.py").write_text("# Main module")
    (temp_dir / "src" / "utils.py").write_text("# Utilities")
    (temp_dir / "tests").mkdir(exist_ok=True)
    (temp_dir / "tests" / "test_main.py").write_text("# Tests for main")
    (temp_dir / "README.md").write_text("# Project README")

    glob_tool = GlobTool(cwd=temp_dir)

    # Find Python files
    print("\nFinding all Python files (**/*.py):")
    result = await glob_tool("**/*.py")
    print(result)

    # Find markdown files
    print("\nFinding markdown files (*.md):")
    result = await glob_tool("*.md")
    print(result)


async def demo_grep_tool(temp_dir: Path) -> None:
    """Demonstrate the GrepTool."""
    print("\n" + "=" * 60)
    print("GrepTool Demo")
    print("=" * 60)

    # Create files with searchable content
    (temp_dir / "code.py").write_text("""
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

def calculate_product(numbers):
    result = 1
    for num in numbers:
        result *= num
    return result

class Calculator:
    def __init__(self):
        self.history = []

    def add(self, a, b):
        result = a + b
        self.history.append(('add', a, b, result))
        return result
""")

    grep_tool = GrepTool(cwd=temp_dir)

    # Search for function definitions
    print("\nSearching for 'def ' in Python files:")
    result = await grep_tool(
        pattern=r"def \w+",
        type="py",
        output_mode="content",
        **{"-n": True}
    )
    print(result)

    # Count occurrences
    print("\nCounting matches for 'return':")
    result = await grep_tool(
        pattern="return",
        type="py",
        output_mode="count",
    )
    print(result)


async def demo_notebook_edit_tool(temp_dir: Path) -> None:
    """Demonstrate the NotebookEditTool."""
    print("\n" + "=" * 60)
    print("NotebookEditTool Demo")
    print("=" * 60)

    # Create a sample notebook
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Sample Notebook\n", "This is a demo notebook."]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["print('Hello, World!')"]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    import json
    notebook_path = temp_dir / "demo.ipynb"
    notebook_path.write_text(json.dumps(notebook, indent=2))

    notebook_tool = NotebookEditTool(cwd=temp_dir)

    # Edit a cell
    print("\nEditing cell 1 (code cell):")
    result = await notebook_tool(
        str(notebook_path),
        new_source="import numpy as np\nprint(f'NumPy version: {np.__version__}')",
        cell_number=1,
    )
    print(result)

    # Insert a new cell
    print("\nInserting new markdown cell at position 1:")
    result = await notebook_tool(
        str(notebook_path),
        new_source="## Setup\nFirst, we import our libraries.",
        cell_number=1,
        cell_type="markdown",
        edit_mode="insert",
    )
    print(result)


async def demo_with_claude(temp_dir: Path) -> None:
    """Demonstrate using builtin tools with Claude."""
    print("\n" + "=" * 60)
    print("Using Builtin Tools with Claude")
    print("=" * 60)

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\nSkipping Claude demo (ANTHROPIC_API_KEY not set)")
        return

    # Create sample files
    (temp_dir / "project").mkdir(exist_ok=True)
    (temp_dir / "project" / "main.py").write_text("""
def fibonacci(n: int) -> int:
    \"\"\"Calculate the nth Fibonacci number.\"\"\"
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def factorial(n: int) -> int:
    \"\"\"Calculate the factorial of n.\"\"\"
    if n <= 1:
        return 1
    return n * factorial(n - 1)
""")

    # Create tool instances
    read_tool = ReadTool(cwd=temp_dir)
    grep_tool = GrepTool(cwd=temp_dir)
    glob_tool = GlobTool(cwd=temp_dir)

    # Configure agent with builtin tools
    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        system_prompt="""You are a helpful code assistant. You have access to tools for reading files,
searching code, and finding files. Use these tools to help answer questions about the codebase.""",
        tools=[
            read_tool.to_tool_definition(),
            grep_tool.to_tool_definition(),
            glob_tool.to_tool_definition(),
        ],
    )

    print("\nAsking Claude to analyze the codebase...")
    prompt = f"Find all Python files in {temp_dir} and tell me what functions are defined in them."

    async for message in query(prompt, options):
        if hasattr(message, "content"):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)
                elif hasattr(block, "name"):
                    print(f"\n[Tool call: {block.name}]")


async def main() -> None:
    """Run all builtin tools demos."""
    print("Universal Agent SDK - Builtin Tools Demo")
    print("=" * 60)

    # Create a temporary directory for all demos
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"Working directory: {temp_path}")

        # Run each demo
        await demo_read_tool(temp_path)
        await demo_write_tool(temp_path)
        await demo_edit_tool(temp_path)
        await demo_bash_tool(temp_path)
        await demo_glob_tool(temp_path)
        await demo_grep_tool(temp_path)
        await demo_notebook_edit_tool(temp_path)
        await demo_with_claude(temp_path)

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
