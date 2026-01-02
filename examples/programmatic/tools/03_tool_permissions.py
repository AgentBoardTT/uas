#!/usr/bin/env python3
"""Example: Tool Permission Callbacks for Universal Agent SDK.

This example demonstrates how to use tool permission callbacks (can_use_tool)
to control which tools the agent can use and modify their inputs.

The can_use_tool callback is called before each tool execution, allowing you to:
- Allow or deny specific tool calls
- Modify tool inputs before execution
- Log tool usage for auditing
- Implement custom security policies
"""

import asyncio
import json

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    TextBlock,
    ToolMessage,
    ToolUseBlock,
    UniversalAgentClient,
    tool,
)
from universal_agent_sdk.types import ToolPermissionContext

# Track tool usage for demonstration
tool_usage_log: list[dict] = []


# Define some tools to work with
@tool
def read_file(path: str) -> str:
    """Read a file from disk."""
    return f"Contents of {path}: Hello, World!"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    return f"Written {len(content)} bytes to {path}"


@tool
def run_command(command: str) -> str:
    """Run a shell command."""
    return f"Executed: {command}\nOutput: Success!"


@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Search results for '{query}': Example result 1, Example result 2"


async def permission_callback(
    tool_name: str,
    input_data: dict,
    context: ToolPermissionContext,
) -> PermissionResultAllow | PermissionResultDeny:
    """Control tool permissions based on tool type and input.

    This callback is called before each tool execution.

    Args:
        tool_name: Name of the tool being called
        input_data: Input parameters for the tool
        context: Context including session_id

    Returns:
        PermissionResultAllow to allow the tool, or PermissionResultDeny to block it
    """
    # Log the tool request
    tool_usage_log.append(
        {
            "tool": tool_name,
            "input": input_data,
            "session_id": context.session_id,
        }
    )

    print(f"\n  [Permission Check: {tool_name}]")
    print(f"   Input: {json.dumps(input_data, indent=2)}")

    # Always allow read operations
    if tool_name in ["read_file", "search_web"]:
        print("   -> Allowed (read-only operation)")
        return PermissionResultAllow()

    # Deny write operations to system directories
    if tool_name == "write_file":
        file_path = input_data.get("path", "")

        # Block writes to sensitive locations
        if any(file_path.startswith(d) for d in ["/etc/", "/usr/", "/bin/", "/sys/"]):
            print(f"   -> Denied (system directory: {file_path})")
            return PermissionResultDeny(
                message=f"Cannot write to system directory: {file_path}"
            )

        # Redirect writes to a safe directory
        if not file_path.startswith("/tmp/") and not file_path.startswith("./"):
            safe_path = f"./safe_output/{file_path.split('/')[-1]}"
            print(f"   -> Allowed with redirect: {file_path} -> {safe_path}")
            modified_input = input_data.copy()
            modified_input["path"] = safe_path
            return PermissionResultAllow(updated_input=modified_input)

        print("   -> Allowed")
        return PermissionResultAllow()

    # Check dangerous bash commands
    if tool_name == "run_command":
        command = input_data.get("command", "")
        dangerous_patterns = [
            "rm -rf",
            "sudo",
            "chmod 777",
            "dd if=",
            "mkfs",
            "> /dev/",
        ]

        for pattern in dangerous_patterns:
            if pattern in command:
                print(f"   -> Denied (dangerous pattern: {pattern})")
                return PermissionResultDeny(
                    message=f"Command contains dangerous pattern: {pattern}"
                )

        print("   -> Allowed")
        return PermissionResultAllow()

    # Allow other tools by default
    print("   -> Allowed (default)")
    return PermissionResultAllow()


async def example_basic_permission():
    """Basic permission callback example."""
    print("=== Basic Permission Callback Example ===\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[
            read_file.definition,
            write_file.definition,
            run_command.definition,
        ],
        can_use_tool=permission_callback,
        max_turns=5,
    )

    async with UniversalAgentClient(options) as client:
        print("User: Read a file called test.txt\n")
        await client.send("Read a file called test.txt")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        print(f"\nAssistant wants to use: {block.name}")
                    elif isinstance(block, TextBlock):
                        print(f"\nAssistant: {block.text}")
            elif isinstance(msg, ToolMessage):
                print(f"Tool result: {msg.content}")
            elif isinstance(msg, ResultMessage):
                print(f"\n[Completed in {msg.num_turns} turns]")

    print()


async def example_blocking_dangerous_commands():
    """Example showing dangerous command blocking."""
    print("=== Blocking Dangerous Commands Example ===\n")

    tool_usage_log.clear()

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[run_command.definition],
        can_use_tool=permission_callback,
        max_turns=5,
    )

    async with UniversalAgentClient(options) as client:
        print("User: Run 'rm -rf /' to clean up the system\n")
        await client.send("Run the command 'rm -rf /' to clean up the system")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        print(f"\nAssistant wants to use: {block.name}({block.input})")
                    elif isinstance(block, TextBlock):
                        print(f"\nAssistant: {block.text}")
            elif isinstance(msg, ToolMessage):
                print(f"Tool result: {msg.content}")
            elif isinstance(msg, ResultMessage):
                print(f"\n[Completed in {msg.num_turns} turns]")

    print()


async def example_input_modification():
    """Example showing input modification."""
    print("=== Input Modification Example ===\n")

    tool_usage_log.clear()

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[write_file.definition],
        can_use_tool=permission_callback,
        max_turns=5,
    )

    async with UniversalAgentClient(options) as client:
        print("User: Write 'Hello' to /home/user/important.txt\n")
        await client.send(
            "Write the text 'Hello' to a file at /home/user/important.txt"
        )

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        print(f"\nAssistant wants to use: {block.name}")
                        print(f"  Original input: {block.input}")
                    elif isinstance(block, TextBlock):
                        print(f"\nAssistant: {block.text}")
            elif isinstance(msg, ToolMessage):
                print(f"Tool result: {msg.content}")
            elif isinstance(msg, ResultMessage):
                print(f"\n[Completed in {msg.num_turns} turns]")

    print()


async def example_audit_logging():
    """Example showing audit logging."""
    print("=== Audit Logging Example ===\n")

    tool_usage_log.clear()

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[
            read_file.definition,
            search_web.definition,
        ],
        can_use_tool=permission_callback,
        max_turns=5,
    )

    async with UniversalAgentClient(options) as client:
        print("User: Search for Python tutorials and read config.txt\n")
        await client.send(
            "Search the web for 'Python tutorials' and then read the file config.txt"
        )

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"\nAssistant: {block.text}")
            elif isinstance(msg, ResultMessage):
                print(f"\n[Completed in {msg.num_turns} turns]")

    # Print audit log
    print("\n" + "=" * 50)
    print("Tool Usage Audit Log")
    print("=" * 50)
    for i, entry in enumerate(tool_usage_log, 1):
        print(f"\n{i}. Tool: {entry['tool']}")
        print(f"   Input: {json.dumps(entry['input'], indent=6)}")
        print(f"   Session: {entry['session_id']}")

    print()


async def example_combined_with_hooks():
    """Example combining permission callback with hooks."""
    print("=== Permission Callback + Hooks Example ===\n")

    from universal_agent_sdk import HookMatcher
    from universal_agent_sdk.types import HookContext, HookInput, HookOutput

    async def log_hook(
        input_data: HookInput,
        tool_use_id: str | None,
        context: HookContext,
    ) -> HookOutput:
        """Log all tool calls via hooks (in addition to permission callback)."""
        tool_name = input_data.get("tool_name", "unknown")
        print(f"   [Hook: PreToolUse triggered for {tool_name}]")
        return {}

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[read_file.definition, write_file.definition],
        can_use_tool=permission_callback,
        hooks={
            "PreToolUse": [
                HookMatcher(matcher=None, hooks=[log_hook]),
            ],
        },
        max_turns=5,
    )

    async with UniversalAgentClient(options) as client:
        print("User: Read test.txt and write to output.txt\n")
        await client.send("Read test.txt and write the content to output.txt")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"\nAssistant: {block.text}")
            elif isinstance(msg, ResultMessage):
                print(f"\n[Completed in {msg.num_turns} turns]")

    print()


async def main():
    """Run all permission callback examples."""
    print("Tool Permission Callback Examples")
    print("=" * 60)
    print("\nThis example demonstrates how to:")
    print("1. Allow/deny tools based on type and input")
    print("2. Modify tool inputs for safety (redirect paths)")
    print("3. Block dangerous commands")
    print("4. Log tool usage for auditing")
    print("5. Combine with hooks for comprehensive control")
    print("=" * 60 + "\n")

    await example_basic_permission()
    print("-" * 50 + "\n")

    await example_blocking_dangerous_commands()
    print("-" * 50 + "\n")

    await example_input_modification()
    print("-" * 50 + "\n")

    await example_audit_logging()
    print("-" * 50 + "\n")

    await example_combined_with_hooks()


if __name__ == "__main__":
    asyncio.run(main())
