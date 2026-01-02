#!/usr/bin/env python3
"""Example demonstrating setting sources control.

This example shows how to use the setting_sources option to control which
settings (skills, configurations) are loaded in Universal Agent SDK.

Setting sources determine where the SDK loads configurations from:
- "user": Global user settings (~/.claude/skills/)
- "project": Project-level settings (.claude/skills/ in project)

By controlling which sources are loaded, you can:
- Create isolated environments with no custom settings (default)
- Load only user settings, excluding project-specific configurations
- Combine multiple sources as needed

Usage:
./examples/universal_setting_sources.py - List the examples
./examples/universal_setting_sources.py all - Run all examples
./examples/universal_setting_sources.py default - Run a specific example
"""

import asyncio
import sys
from pathlib import Path

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    UniversalAgentClient,
)
from universal_agent_sdk.skills import list_skills


async def example_default():
    """Default behavior - no settings loaded."""
    print("=== Default Behavior Example ===")
    print("Setting sources: [] (empty - default)")
    print("Expected: No custom skills will be loaded\n")

    sdk_dir = Path(__file__).parent.parent

    # Example configuration with no setting sources
    print("Example AgentOptions: setting_sources=[]")
    print()

    # Check what skills would be loaded
    skills = list_skills(setting_sources=[], project_dir=sdk_dir)
    print(f"Skills available: {[s.name for s in skills]}")

    if not skills:
        print("No custom skills loaded (expected for isolated environment)")
    else:
        print(f"Unexpected: Found {len(skills)} skills")

    print()


async def example_user_only():
    """Load only user-level settings, excluding project settings."""
    print("=== User Settings Only Example ===")
    print("Setting sources: ['user']")
    print("Expected: Only user skills from ~/.claude/skills/\n")

    # Example configuration with user-only sources
    print("Example AgentOptions: setting_sources=['user']")
    print()

    # Check what skills are available
    skills = list_skills(setting_sources=["user"])
    print(f"User skills available: {[s.name for s in skills]}")

    if skills:
        for skill in skills:
            print(
                f"  - {skill.name}: {skill.description[:50] if skill.description else 'No description'}..."
            )
    else:
        print("  (no user skills found)")

    print()


async def example_project_only():
    """Load only project-level settings."""
    print("=== Project Settings Only Example ===")
    print("Setting sources: ['project']")
    print("Expected: Only project skills from .claude/skills/\n")

    sdk_dir = Path(__file__).parent.parent

    # Example configuration with project-only sources
    print("Example AgentOptions: setting_sources=['project']")
    print()

    # Check what skills are available
    skills = list_skills(setting_sources=["project"], project_dir=sdk_dir)
    print(f"Project skills available: {[s.name for s in skills]}")

    if skills:
        for skill in skills:
            print(
                f"  - {skill.name}: {skill.description[:50] if skill.description else 'No description'}..."
            )
    else:
        print("  (no project skills found)")

    print()


async def example_project_and_user():
    """Load both project and user settings."""
    print("=== Project + User Settings Example ===")
    print("Setting sources: ['user', 'project']")
    print("Expected: Skills from both sources\n")

    sdk_dir = Path(__file__).parent.parent

    # Example configuration combining both sources
    print("Example AgentOptions: setting_sources=['user', 'project']")
    print()

    # Check what skills are available
    skills = list_skills(setting_sources=["user", "project"], project_dir=sdk_dir)
    print(f"Total skills available: {len(skills)}")

    if skills:
        for skill in skills:
            print(
                f"  - {skill.name}: {skill.description[:50] if skill.description else 'No description'}..."
            )
    else:
        print("  (no skills found)")

    print()


async def example_with_query():
    """Run a query with specific setting sources."""
    print("=== Query with Setting Sources Example ===")
    print("Setting sources: ['project']\n")

    sdk_dir = Path(__file__).parent.parent

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        setting_sources=["project"],
        allowed_tools=["Skill"],
        cwd=str(sdk_dir),
    )

    # Show available skills
    skills = list_skills(setting_sources=["project"], project_dir=sdk_dir)
    print(f"Available skills: {[s.name for s in skills]}")

    async with UniversalAgentClient(options) as client:
        print("\nUser: Say hello in exactly 3 words\n")
        await client.send("Say hello in exactly 3 words")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Assistant: {block.text}")
            elif isinstance(msg, ResultMessage):
                print(f"\n[Completed in {msg.num_turns} turns]")

    print()


async def main():
    """Run all examples or a specific example based on command line argument."""
    examples = {
        "default": example_default,
        "user_only": example_user_only,
        "project_only": example_project_only,
        "project_and_user": example_project_and_user,
        "with_query": example_with_query,
    }

    if len(sys.argv) < 2:
        print("Usage: python universal_setting_sources.py <example_name>")
        print("\nAvailable examples:")
        print("  all - Run all examples")
        for name in examples:
            print(f"  {name}")
        sys.exit(0)

    example_name = sys.argv[1]

    if example_name == "all":
        for name, example in examples.items():
            print(f"\n{'=' * 60}")
            print(f"Running: {name}")
            print("=" * 60 + "\n")
            try:
                await example()
            except Exception as e:
                print(f"Error: {e}")
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
    print("Universal Agent SDK Setting Sources Examples")
    print("=" * 60 + "\n")
    asyncio.run(main())
