#!/usr/bin/env python3
"""Example of using custom agents with Universal Agent SDK.

This example demonstrates how to define and use custom agents with specific
tools, prompts, and configurations. Agents in Universal SDK are predefined
configurations that can be invoked for specific tasks.

Usage:
./examples/universal_agents.py - Run all examples
"""

import asyncio

from universal_agent_sdk import (
    AgentDefinition,
    AgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    query,
    tool,
)


# Define tools that agents can use
@tool
def read_file(path: str) -> str:
    """Read a file's contents."""
    return f"Contents of {path}: [sample code content]"


@tool
def search_code(pattern: str) -> str:
    """Search for code patterns."""
    return f"Found matches for '{pattern}' in 3 files"


@tool
def analyze_code(code: str) -> str:
    """Analyze code for issues."""
    issues = []
    if "eval(" in code:
        issues.append("Security: Avoid using eval()")
    if "import *" in code:
        issues.append("Style: Avoid wildcard imports")
    return "\n".join(issues) if issues else "No issues found"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    return f"Written {len(content)} bytes to {path}"


async def code_reviewer_example():
    """Example using a code reviewer agent definition."""
    print("=== Code Reviewer Agent Example ===\n")

    # Define a code reviewer agent
    code_reviewer = AgentDefinition(
        name="code-reviewer",
        description="Reviews code for best practices and potential issues",
        system_prompt=(
            "You are a code reviewer. Analyze code for bugs, performance issues, "
            "security vulnerabilities, and adherence to best practices. "
            "Provide constructive feedback with specific suggestions."
        ),
        tools=["read_file", "search_code", "analyze_code"],
        model="claude-sonnet-4-20250514",
        max_turns=5,
    )

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[
            read_file.definition,
            search_code.definition,
            analyze_code.definition,
        ],
        agents={"code-reviewer": code_reviewer},
        system_prompt=code_reviewer.system_prompt,
        max_turns=5,
    )

    code_to_review = """
def process_data(data):
    from os import *
    result = eval(data)
    return result
"""

    print(f"Code to review:\n{code_to_review}\n")
    print("User: Please review this code for issues.\n")

    async for message in query(
        f"Please analyze this code and tell me what issues you find:\n```python{code_to_review}```",
        options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def documentation_writer_example():
    """Example using a documentation writer agent."""
    print("=== Documentation Writer Agent Example ===\n")

    doc_writer = AgentDefinition(
        name="doc-writer",
        description="Writes comprehensive documentation",
        system_prompt=(
            "You are a technical documentation expert. Write clear, comprehensive "
            "documentation with examples. Focus on clarity and completeness. "
            "Use markdown formatting for structure."
        ),
        model="claude-sonnet-4-20250514",
    )

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[read_file.definition, write_file.definition],
        agents={"doc-writer": doc_writer},
        system_prompt=doc_writer.system_prompt,
        max_turns=3,
    )

    print(
        "User: Write documentation for a 'calculate' function that adds two numbers.\n"
    )

    async for message in query(
        "Write brief documentation for a function called 'calculate' that takes two numbers and returns their sum. Include a usage example.",
        options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def multiple_agents_example():
    """Example with multiple agent definitions."""
    print("=== Multiple Agents Example ===\n")

    # Define multiple agents
    analyzer = AgentDefinition(
        name="analyzer",
        description="Analyzes code structure and patterns",
        system_prompt="You are a code analyzer. Examine code structure, patterns, and architecture.",
    )

    tester = AgentDefinition(
        name="tester",
        description="Creates and runs tests",
        system_prompt="You are a testing expert. Suggest test cases and ensure code quality.",
    )

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[read_file.definition, analyze_code.definition],
        agents={
            "analyzer": analyzer,
            "tester": tester,
        },
        # Use analyzer's prompt by default
        system_prompt=analyzer.system_prompt,
        max_turns=3,
    )

    print("User: Analyze this simple function.\n")

    code = """
def add(a, b):
    return a + b
"""

    async for message in query(
        f"Analyze this function and suggest test cases:\n```python{code}```",
        options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def agent_with_tools_example():
    """Example showing agent with tool execution."""
    print("=== Agent with Tools Example ===\n")

    helper = AgentDefinition(
        name="helper",
        description="A helpful coding assistant",
        system_prompt="You are a helpful coding assistant. Use tools when needed.",
    )

    @tool
    def get_time() -> str:
        """Get the current time."""
        from datetime import datetime

        return datetime.now().strftime("%H:%M:%S")

    @tool
    def calculate(expression: str) -> str:
        """Calculate a math expression."""
        try:
            allowed = set("0123456789+-*/(). ")
            if all(c in allowed for c in expression):
                return str(eval(expression))  # noqa: S307
            return "Invalid expression"
        except Exception as e:
            return f"Error: {e}"

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[get_time.definition, calculate.definition],
        agents={"helper": helper},
        system_prompt=helper.system_prompt,
        max_turns=5,
    )

    print("User: What time is it, and what's 15 * 4?\n")

    async for message in query(
        "What time is it, and what's 15 * 4?",
        options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def main():
    """Run all agent examples."""
    await code_reviewer_example()
    print("-" * 50 + "\n")

    await documentation_writer_example()
    print("-" * 50 + "\n")

    await multiple_agents_example()
    print("-" * 50 + "\n")

    await agent_with_tools_example()


if __name__ == "__main__":
    asyncio.run(main())
