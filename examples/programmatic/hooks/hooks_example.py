#!/usr/bin/env python
"""Example of using hooks with Universal Agent SDK.

This file demonstrates various hook patterns using the hooks parameter
in AgentOptions. Hooks allow you to intercept and modify agent behavior
at various points in the execution lifecycle.

Hook Events:
- SessionStart: Called when a session begins
- PreToolUse: Called before a tool is executed
- PostToolUse: Called after a tool is executed
- OnError: Called when an error occurs

Usage:
    python examples/universal_hooks.py - List the examples
    python examples/universal_hooks.py all - Run all examples
    python examples/universal_hooks.py PreToolUse - Run a specific example
"""

import asyncio
import logging
import sys

from universal_agent_sdk import (
    AgentOptions,
    HookContext,
    HookInput,
    HookMatcher,
    HookOutput,
    UniversalAgentClient,
    tool,
)
from universal_agent_sdk.types import (
    AssistantMessage,
    Message,
    ResultMessage,
    TextBlock,
)

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# Sample Tools
# =============================================================================


@tool
def run_command(command: str) -> str:
    """Simulate running a bash command."""
    if "foo.sh" in command:
        return "Error: foo.sh not found"
    return f"Executed: {command}\nOutput: Success!"


@tool
def write_file(file_path: str, content: str) -> str:
    """Simulate writing to a file."""
    return f"Written {len(content)} bytes to {file_path}"


@tool
def read_file(file_path: str) -> str:
    """Simulate reading a file."""
    return f"Contents of {file_path}: Hello, World!"


# =============================================================================
# Display Helper
# =============================================================================


def display_message(msg: Message) -> None:
    """Standardized message display function."""
    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"Assistant: {block.text}")
    elif isinstance(msg, ResultMessage):
        print(f"[Result: {msg.num_turns} turns]")


# =============================================================================
# Hook Callbacks
# =============================================================================


async def check_command_hook(
    input_data: HookInput, tool_use_id: str | None, context: HookContext
) -> HookOutput:
    """Prevent certain commands from being executed."""
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name != "run_command":
        return {}

    command = tool_input.get("command", "")
    block_patterns = ["foo.sh", "rm -rf", "sudo"]

    for pattern in block_patterns:
        if pattern in command:
            logger.warning(f"Blocked command: {command}")
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Command contains blocked pattern: {pattern}",
                }
            }

    return {}


async def add_custom_context_hook(
    input_data: HookInput, tool_use_id: str | None, context: HookContext
) -> HookOutput:
    """Add custom context when a session starts."""
    logger.info("SessionStart hook: Adding custom context")
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "The user's favorite programming language is Python.",
        }
    }


async def review_tool_output_hook(
    input_data: HookInput, tool_use_id: str | None, context: HookContext
) -> HookOutput:
    """Review tool output and provide additional context or warnings."""
    tool_response = input_data.get("tool_response", "")

    # If the tool produced an error, add helpful context
    if "error" in str(tool_response).lower():
        logger.warning("Tool produced an error - adding context")
        return {
            "reason": "Tool execution failed",
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "The command encountered an error. Consider trying a different approach.",
            },
        }

    return {}


async def strict_file_access_hook(
    input_data: HookInput, tool_use_id: str | None, context: HookContext
) -> HookOutput:
    """Demonstrates using permissionDecision to control tool execution."""
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Block writes to certain files
    if tool_name == "write_file":
        file_path = tool_input.get("file_path", "")
        if "important" in file_path.lower() or "config" in file_path.lower():
            logger.warning(f"Blocked write to: {file_path}")
            return {
                "reason": "Security policy blocks writes to important/config files",
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "Writes to important/config files are blocked",
                },
            }

    # Allow everything else explicitly
    return {
        "reason": "Tool use approved after security review",
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Tool passed security checks",
        },
    }


async def stop_on_critical_error_hook(
    input_data: HookInput, tool_use_id: str | None, context: HookContext
) -> HookOutput:
    """Demonstrates using continue_=False to stop execution on certain conditions."""
    tool_response = input_data.get("tool_response", "")

    # Stop execution if we see a critical error
    if "critical" in str(tool_response).lower():
        logger.error("Critical error detected - stopping execution")
        return {
            "continue_": False,
            "stopReason": "Critical error detected in tool output - execution halted for safety",
        }

    return {"continue_": True}


async def log_all_tool_calls_hook(
    input_data: HookInput, tool_use_id: str | None, context: HookContext
) -> HookOutput:
    """Log all tool calls for auditing purposes."""
    tool_name = input_data.get("tool_name", "unknown")
    tool_input = input_data.get("tool_input", {})
    session_id = context.get("session_id", "unknown")

    logger.info(
        f"[AUDIT] Session {session_id}: Tool '{tool_name}' called with {tool_input}"
    )
    return {}


# =============================================================================
# Example Functions
# =============================================================================


async def example_pretooluse() -> None:
    """Basic example demonstrating PreToolUse hook protection."""
    print("=== PreToolUse Example ===")
    print("This example shows how PreToolUse can block dangerous commands.\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[run_command.definition],
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="run_command", hooks=[check_command_hook]),
            ],
        },
    )

    async with UniversalAgentClient(options=options) as client:
        # Test 1: Command with forbidden pattern (will be blocked)
        print("Test 1: Trying a command that should be blocked...")
        print("User: Run the command ./foo.sh")
        await client.send("Run the command: ./foo.sh")
        async for msg in client.receive():
            display_message(msg)

        print("\n" + "=" * 50 + "\n")

        # Test 2: Safe command that should work
        print("Test 2: Trying a safe command...")
        print("User: Run the command echo hello")
        await client.send("Run the command: echo hello")
        async for msg in client.receive():
            display_message(msg)

    print("\n")


async def example_session_start() -> None:
    """Demonstrate SessionStart hook for adding context."""
    print("=== SessionStart Example ===")
    print("This example shows how SessionStart adds context to the conversation.\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        hooks={
            "SessionStart": [
                HookMatcher(matcher=None, hooks=[add_custom_context_hook]),
            ],
        },
    )

    async with UniversalAgentClient(options=options) as client:
        print("User: What's my favorite programming language?")
        await client.send("What's my favorite programming language?")
        async for msg in client.receive():
            display_message(msg)

    print("\n")


async def example_posttooluse() -> None:
    """Demonstrate PostToolUse hook with feedback."""
    print("=== PostToolUse Example ===")
    print("This example shows how PostToolUse can add context after tool execution.\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[run_command.definition],
        hooks={
            "PostToolUse": [
                HookMatcher(matcher="run_command", hooks=[review_tool_output_hook]),
            ],
        },
    )

    async with UniversalAgentClient(options=options) as client:
        print("User: Run a command that will produce an error")
        await client.send("Run the command: cat /nonexistent_file")
        async for msg in client.receive():
            display_message(msg)

    print("\n")


async def example_permission_decision() -> None:
    """Demonstrate permissionDecision for fine-grained access control."""
    print("=== Permission Decision Example ===")
    print("This example shows permissionDecision='allow'/'deny' for access control.\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[write_file.definition, read_file.definition],
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="write_file", hooks=[strict_file_access_hook]),
            ],
        },
    )

    async with UniversalAgentClient(options=options) as client:
        # Test 1: Try to write to a blocked file
        print("Test 1: Trying to write to important_config.txt (should be blocked)...")
        await client.send("Write 'test' to a file called important_config.txt")
        async for msg in client.receive():
            display_message(msg)

        print("\n" + "=" * 50 + "\n")

        # Test 2: Write to a regular file (should work)
        print("Test 2: Trying to write to regular.txt (should be allowed)...")
        await client.send("Write 'hello' to a file called regular.txt")
        async for msg in client.receive():
            display_message(msg)

    print("\n")


async def example_stop_control() -> None:
    """Demonstrate continue_=False for execution control."""
    print("=== Stop Control Example ===")
    print(
        "This example shows how continue_=False stops execution on critical errors.\n"
    )

    @tool
    def check_status() -> str:
        """Check system status."""
        return "CRITICAL ERROR: System failure detected!"

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[check_status.definition],
        hooks={
            "PostToolUse": [
                HookMatcher(
                    matcher="check_status", hooks=[stop_on_critical_error_hook]
                ),
            ],
        },
    )

    async with UniversalAgentClient(options=options) as client:
        print("User: Check the system status")
        await client.send("Check the system status and report any issues")
        async for msg in client.receive():
            display_message(msg)

    print("\n")


async def example_audit_logging() -> None:
    """Demonstrate using hooks for audit logging."""
    print("=== Audit Logging Example ===")
    print("This example shows how to use PreToolUse hooks for auditing.\n")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tools=[run_command.definition, read_file.definition],
        hooks={
            "PreToolUse": [
                # Log all tool calls (matcher=None matches everything)
                HookMatcher(matcher=None, hooks=[log_all_tool_calls_hook]),
            ],
        },
    )

    async with UniversalAgentClient(options=options) as client:
        print("User: Run 'ls' and then read config.txt")
        await client.send("First run the command 'ls', then read the file config.txt")
        async for msg in client.receive():
            display_message(msg)

    print("\n")


async def example_without_api() -> None:
    """Demonstrate hooks without calling the API (for testing)."""
    print("=== Local Hook Testing Example ===")
    print("This example tests hooks without making API calls.\n")

    from universal_agent_sdk.types import (
        HookContext,
        PostToolUseHookInput,
        PreToolUseHookInput,
        SessionStartHookInput,
    )

    # Test SessionStart hook
    print("Testing SessionStart hook...")
    session_input: SessionStartHookInput = {
        "session_id": "test-session",
        "hook_event_name": "SessionStart",
    }
    context: HookContext = {"session_id": "test-session", "tool_use_id": None}
    result = await add_custom_context_hook(session_input, None, context)
    print(f"  Result: {result}")

    # Test PreToolUse hook - blocked command
    print("\nTesting PreToolUse hook (blocked command)...")
    pre_input: PreToolUseHookInput = {
        "session_id": "test-session",
        "hook_event_name": "PreToolUse",
        "tool_name": "run_command",
        "tool_input": {"command": "./foo.sh"},
    }
    result = await check_command_hook(pre_input, "tool-123", context)
    print(f"  Result: {result}")

    # Test PreToolUse hook - allowed command
    print("\nTesting PreToolUse hook (allowed command)...")
    pre_input["tool_input"] = {"command": "echo hello"}
    result = await check_command_hook(pre_input, "tool-123", context)
    print(f"  Result: {result}")

    # Test PostToolUse hook - error case
    print("\nTesting PostToolUse hook (error response)...")
    post_input: PostToolUseHookInput = {
        "session_id": "test-session",
        "hook_event_name": "PostToolUse",
        "tool_name": "run_command",
        "tool_input": {"command": "test"},
        "tool_response": "Error: command not found",
    }
    result = await review_tool_output_hook(post_input, "tool-123", context)
    print(f"  Result: {result}")

    print("\n")


# =============================================================================
# Main
# =============================================================================


async def main() -> None:
    """Run all examples or a specific example based on command line argument."""
    examples = {
        "PreToolUse": example_pretooluse,
        "SessionStart": example_session_start,
        "PostToolUse": example_posttooluse,
        "PermissionDecision": example_permission_decision,
        "StopControl": example_stop_control,
        "AuditLogging": example_audit_logging,
        "LocalTest": example_without_api,
    }

    if len(sys.argv) < 2:
        print("Usage: python universal_hooks.py <example_name>")
        print("\nAvailable examples:")
        print("  all       - Run all examples (requires API)")
        print("  LocalTest - Run local test without API")
        for name in examples:
            if name != "LocalTest":
                print(f"  {name}")
        print("\nExample descriptions:")
        print("  PreToolUse         - Block commands using PreToolUse hook")
        print("  SessionStart       - Add context at session start")
        print("  PostToolUse        - Review tool output and add context")
        print("  PermissionDecision - Use permissionDecision='allow'/'deny'")
        print("  StopControl        - Stop execution with continue_=False")
        print("  AuditLogging       - Log all tool calls for auditing")
        print("  LocalTest          - Test hooks locally without API")
        sys.exit(0)

    example_name = sys.argv[1]

    if example_name == "all":
        # Run all examples except LocalTest
        for name, example in examples.items():
            if name != "LocalTest":
                try:
                    await example()
                except Exception as e:
                    print(f"Error in {name}: {e}")
                print("-" * 50 + "\n")
    elif example_name in examples:
        await examples[example_name]()
    else:
        print(f"Error: Unknown example '{example_name}'")
        print("\nAvailable examples:")
        print("  all - Run all examples")
        for name in examples:
            print(f"  {name}")
        sys.exit(1)


if __name__ == "__main__":
    print("Universal Agent SDK - Hooks Examples")
    print("=" * 50 + "\n")
    asyncio.run(main())
