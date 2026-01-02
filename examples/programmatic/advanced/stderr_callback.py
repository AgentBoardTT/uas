#!/usr/bin/env python3
"""Simple example demonstrating stderr callback for capturing debug output.

This example shows how to use the stderr_callback option in Universal Agent SDK
to capture and process debug/error messages during agent execution.

The stderr_callback is useful for:
- Capturing debug information during development
- Logging errors for monitoring
- Debugging provider-specific issues

Usage:
./examples/universal_stderr_callback.py
"""

import asyncio

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    query,
)


async def basic_stderr_callback():
    """Basic stderr callback example."""
    print("=== Basic stderr Callback Example ===\n")

    # Collect stderr messages
    stderr_messages: list[str] = []

    def stderr_callback(message: str) -> None:
        """Callback that receives stderr output."""
        stderr_messages.append(message)
        # Only print errors
        if "error" in message.lower() or "warn" in message.lower():
            print(f"[STDERR] {message}")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stderr_callback=stderr_callback,
        debug=True,  # Enable debug mode
    )

    print("Running query with stderr capture...")
    print("User: What is 2+2?\n")

    async for message in query("What is 2+2?", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")

    print(f"\nCaptured {len(stderr_messages)} stderr lines")
    if stderr_messages:
        print("Sample stderr output:")
        for msg in stderr_messages[:3]:
            print(f"  - {msg[:80]}...")

    print()


async def error_tracking_callback():
    """Example tracking only errors."""
    print("=== Error Tracking Callback Example ===\n")

    errors: list[str] = []
    warnings: list[str] = []

    def categorize_stderr(message: str) -> None:
        """Categorize stderr messages by severity."""
        msg_lower = message.lower()
        if "error" in msg_lower:
            errors.append(message)
        elif "warning" in msg_lower or "warn" in msg_lower:
            warnings.append(message)

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stderr_callback=categorize_stderr,
        debug=True,
    )

    print("User: What is the meaning of life?\n")

    async for message in query("What is the meaning of life? Be brief.", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")

    print("\nError summary:")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")

    if errors:
        print("\nErrors found:")
        for err in errors[:3]:
            print(f"  - {err[:80]}...")

    print()


async def debug_logging_callback():
    """Example with full debug logging."""
    print("=== Debug Logging Callback Example ===\n")

    log_entries: list[str] = []

    def log_stderr(message: str) -> None:
        """Log all stderr to a list (simulating file)."""
        import time

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        log_entries.append(entry)

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stderr_callback=log_stderr,
        debug=True,
    )

    print("User: Calculate 15 * 7\n")

    async for message in query("Calculate 15 * 7", options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"\n[Completed in {message.num_turns} turns]")

    print(f"\nCollected {len(log_entries)} log entries")
    if log_entries:
        print("Last 3 entries:")
        for entry in log_entries[-3:]:
            print(f"  {entry[:100]}...")

    print()


async def conditional_callback():
    """Example with conditional stderr processing."""
    print("=== Conditional Callback Example ===\n")

    from universal_agent_sdk import UniversalAgentClient

    important_messages: list[str] = []

    def filter_important(message: str) -> None:
        """Only capture important messages."""
        keywords = ["error", "failed", "timeout", "retry", "exception"]
        if any(kw in message.lower() for kw in keywords):
            important_messages.append(message)
            print(f"[IMPORTANT] {message[:60]}...")

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        stderr_callback=filter_important,
        debug=True,
    )

    async with UniversalAgentClient(options) as client:
        print("User: Hello, how are you?\n")
        await client.send("Hello, how are you?")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Assistant: {block.text}")
            elif isinstance(msg, ResultMessage):
                print(f"\n[Completed in {msg.num_turns} turns]")

    print(f"\nImportant messages captured: {len(important_messages)}")

    print()


async def main():
    """Run all stderr callback examples."""
    print("stderr Callback Examples")
    print("=" * 60)
    print("\nThis example demonstrates how to use stderr_callback")
    print("to capture and process debug/error output.")
    print("=" * 60 + "\n")

    await basic_stderr_callback()
    print("-" * 50 + "\n")

    await error_tracking_callback()
    print("-" * 50 + "\n")

    await debug_logging_callback()
    print("-" * 50 + "\n")

    await conditional_callback()


if __name__ == "__main__":
    asyncio.run(main())
