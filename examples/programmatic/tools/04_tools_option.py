#!/usr/bin/env python3
"""Example demonstrating the tools option in Universal Agent SDK.

This example shows different ways to configure tools:
1. Using the @tool decorator to create custom tools
2. Using built-in tools from the SDK
3. Combining multiple tools
"""

import asyncio

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolMessage,
    ToolUseBlock,
    query,
    tool,
)


# Define custom tools using @tool decorator
@tool
def get_time() -> str:
    """Get the current time."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculator(expression: str) -> str:
    """Calculate a mathematical expression.

    Args:
        expression: A math expression like "2 + 2"
    """
    try:
        allowed = set("0123456789+-*/().% ")
        if all(c in allowed for c in expression):
            result = eval(expression)  # noqa: S307
            return str(result)
        return "Error: Invalid characters in expression"
    except Exception as e:
        return f"Error: {e}"


@tool
def string_utils(text: str, operation: str) -> str:
    """Perform string operations.

    Args:
        text: The text to operate on
        operation: One of: upper, lower, reverse, length
    """
    operations = {
        "upper": lambda t: t.upper(),
        "lower": lambda t: t.lower(),
        "reverse": lambda t: t[::-1],
        "length": lambda t: str(len(t)),
    }
    if operation in operations:
        return operations[operation](text)
    return f"Unknown operation: {operation}. Available: {list(operations.keys())}"


async def single_tool_example():
    """Example with a single tool."""
    print("=== Single Tool Example ===")
    print("Using: get_time\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[get_time.definition],
        max_turns=3,
    )

    print("User: What time is it right now?\n")

    async for message in query("What time is it right now?", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[Tool call: {block.name}]")
                elif isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ToolMessage):
            print(f"[Tool result: {message.content}]")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def multiple_tools_example():
    """Example with multiple tools."""
    print("=== Multiple Tools Example ===")
    print("Using: get_time, calculator, string_utils\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[
            get_time.definition,
            calculator.definition,
            string_utils.definition,
        ],
        max_turns=5,
    )

    print("User: What's 15 * 7, and reverse the word 'hello'?\n")

    async for message in query("What's 15 * 7, and reverse the word 'hello'?", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[Tool call: {block.name}({block.input})]")
                elif isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ToolMessage):
            print(f"[Tool result: {message.content}]")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def no_tools_example():
    """Example with no tools (pure conversation)."""
    print("=== No Tools Example ===")
    print("Using: no tools (tools=[])\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[],  # Empty list = no tools
        max_turns=1,
    )

    print("User: What tools do you have available?\n")

    async for message in query("What tools do you have available?", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def builtin_tools_example():
    """Example using built-in tools from the SDK."""
    print("=== Built-in Tools Example ===")
    print("Using: ReadTool, GlobTool\n")

    from universal_agent_sdk import GlobTool, ReadTool

    # Initialize built-in tools
    read_tool = ReadTool()
    glob_tool = GlobTool()

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[
            read_tool.to_tool_definition(),
            glob_tool.to_tool_definition(),
        ],
        max_turns=3,
    )

    print("User: Find and read any .py file in the current directory\n")

    async for message in query(
        "List .py files in the examples directory using glob, then read the first one you find",
        options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[Tool call: {block.name}]")
                elif isinstance(block, TextBlock):
                    # Truncate long responses
                    text = block.text
                    if len(text) > 200:
                        text = text[:200] + "..."
                    print(f"Assistant: {text}")
        elif isinstance(message, ToolMessage):
            content = message.content
            if len(content) > 100:
                content = content[:100] + "..."
            print(f"[Tool result: {content}]")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def tool_choice_example():
    """Example demonstrating tool_choice option."""
    print("=== Tool Choice Example ===")
    print("Using tool_choice to control tool usage\n")

    options_auto = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[calculator.definition],
        tool_choice="auto",  # Let the model decide
        max_turns=3,
    )

    print("--- tool_choice='auto' ---")
    print("User: Just say hello\n")

    async for message in query("Just say hello", options_auto):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[Tool call: {block.name}]")
                elif isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")

    print()

    # With tool_choice="required", the model must use a tool
    options_required = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[calculator.definition],
        tool_choice="required",  # Must use a tool
        max_turns=3,
    )

    print("--- tool_choice='required' ---")
    print("User: Calculate 100 / 4\n")

    async for message in query("Calculate 100 / 4", options_required):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[Tool call: {block.name}({block.input})]")
                elif isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ToolMessage):
            print(f"[Tool result: {message.content}]")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")
    print()


async def main():
    """Run all examples."""
    await single_tool_example()
    print("-" * 50 + "\n")

    await multiple_tools_example()
    print("-" * 50 + "\n")

    await no_tools_example()
    print("-" * 50 + "\n")

    await builtin_tools_example()
    print("-" * 50 + "\n")

    await tool_choice_example()


if __name__ == "__main__":
    asyncio.run(main())
