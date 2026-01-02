#!/usr/bin/env python3
"""Example of loading filesystem-based agents via setting_sources.

This example demonstrates how to load skills/agents defined in
.claude/skills/ directories using the setting_sources option.

Skills can be loaded from:
- "user": ~/.claude/skills/ (user-level skills)
- "project": .claude/skills/ (project-level skills)

Usage:
./examples/universal_filesystem_agents.py
"""

import asyncio
from pathlib import Path

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    UniversalAgentClient,
)
from universal_agent_sdk.skills import discover_skills, list_skills


async def list_available_skills():
    """List skills available from user and project sources."""
    print("=== Available Skills ===\n")

    # Get the SDK directory
    sdk_dir = Path(__file__).parent.parent

    # Discover skills from project
    project_skills = discover_skills(
        setting_sources=["project"],
        project_dir=sdk_dir,
    )

    print("Project skills (.claude/skills/):")
    if project_skills:
        for skill in project_skills:
            print(
                f"  - {skill.name}: {skill.description[:50] if skill.description else 'No description'}..."
            )
    else:
        print("  (none found)")

    # Discover skills from user
    user_skills = discover_skills(
        setting_sources=["user"],
    )

    print("\nUser skills (~/.claude/skills/):")
    if user_skills:
        for skill in user_skills:
            print(
                f"  - {skill.name}: {skill.description[:50] if skill.description else 'No description'}..."
            )
    else:
        print("  (none found)")

    print()


async def load_skills_example():
    """Example loading skills via setting_sources in AgentOptions."""
    print("=== Loading Skills via setting_sources ===\n")

    sdk_dir = Path(__file__).parent.parent

    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        setting_sources=["project"],  # Load project skills
        allowed_tools=["Skill"],  # Enable skill invocation
        cwd=str(sdk_dir),
    )

    print("Configured with setting_sources=['project']")
    print("Skills are automatically discovered and made available.\n")

    # List skills that would be loaded
    skills = list_skills(setting_sources=["project"], project_dir=sdk_dir)
    print(f"Skills available: {[s.name for s in skills]}\n")

    async with UniversalAgentClient(options) as client:
        print("User: Say hello in exactly 3 words\n")
        await client.send("Say hello in exactly 3 words")

        async for msg in client.receive():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Assistant: {block.text}")
            elif isinstance(msg, ResultMessage):
                print(f"\n[Completed in {msg.num_turns} turns]")

    print()


async def skill_registry_example():
    """Example using the skill registry directly."""
    print("=== Skill Registry Example ===\n")

    from universal_agent_sdk.skills import SkillRegistry, load_skills_to_registry

    # Create a registry
    registry = SkillRegistry()

    # Load skills from project
    sdk_dir = Path(__file__).parent.parent
    skills_loaded = load_skills_to_registry(
        registry,
        setting_sources=["project"],
        project_dir=sdk_dir,
    )

    print(f"Loaded {skills_loaded} skill(s) into registry")

    # List registered skills
    all_skills = registry.list_all()
    for name, skill in all_skills.items():
        print(f"\nSkill: {name}")
        print(f"  Description: {skill.description}")
        if skill.allowed_tools:
            print(f"  Allowed tools: {skill.allowed_tools}")

    print()


async def combined_sources_example():
    """Example combining user and project skills."""
    print("=== Combined Sources Example ===\n")

    sdk_dir = Path(__file__).parent.parent

    # Example configuration combining both user and project sources
    print("Example AgentOptions configuration:")
    print("  setting_sources=['user', 'project']")
    print("  allowed_tools=['Skill']")
    print()

    print("Configured with setting_sources=['user', 'project']")
    print("Skills from both user home and project are available.\n")

    # Show which skills would be available
    skills = list_skills(setting_sources=["user", "project"], project_dir=sdk_dir)
    if skills:
        print("Available skills:")
        for skill in skills:
            source = (
                "user"
                if "~" in str(skill.path) or ".claude" in str(skill.path)
                else "project"
            )
            print(f"  - {skill.name} ({source})")
    else:
        print("No skills found in user or project directories")

    print()


async def main():
    """Run all filesystem agent examples."""
    print("Filesystem Agents / Skills Example")
    print("=" * 60)
    print("\nThis example demonstrates how to:")
    print("1. Discover skills from user and project directories")
    print("2. Load skills via setting_sources option")
    print("3. Use the skill registry directly")
    print("4. Combine multiple skill sources")
    print("=" * 60 + "\n")

    await list_available_skills()
    print("-" * 50 + "\n")

    await skill_registry_example()
    print("-" * 50 + "\n")

    await combined_sources_example()
    print("-" * 50 + "\n")

    await load_skills_example()


if __name__ == "__main__":
    asyncio.run(main())
