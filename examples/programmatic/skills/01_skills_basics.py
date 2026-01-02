"""Skills example for Universal Agent SDK.

Skills in the SDK are:
1. **Defined as filesystem artifacts**: Created as `SKILL.md` files in `.claude/skills/`
2. **Loaded from filesystem**: Skills are loaded via `setting_sources` configuration
3. **Automatically discovered**: Skill metadata is discovered from user and project directories
4. **Model-invoked**: Claude autonomously chooses when to use them based on context
5. **Enabled via allowed_tools**: Add `"Skill"` to your `allowed_tools` to enable Skills

This example demonstrates how to work with skills following the official SDK pattern.
"""

import asyncio
from pathlib import Path

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    TextBlock,
    query,
)
from universal_agent_sdk.skills import (
    Skill,
    discover_skills,
    list_skills,
    load_skills_to_registry,
)

# =============================================================================
# Example 1: Loading Skills from Filesystem
# =============================================================================


async def filesystem_skills_example():
    """Demonstrate loading skills from filesystem (official SDK pattern).

    Skills are loaded from:
    - User skills: ~/.claude/skills/ (when "user" in setting_sources)
    - Project skills: <cwd>/.claude/skills/ (when "project" in setting_sources)
    """
    print("=== Filesystem Skills Example ===\n")

    # Get the directory containing example skills
    example_dir = Path(__file__).parent

    # Discover skills from filesystem
    skills = discover_skills(
        cwd=example_dir,
        setting_sources=["project"],  # Load from .claude/skills/ in this directory
    )

    print(f"Discovered {len(skills)} skill(s) from filesystem:")
    for skill in skills:
        print(f"  - {skill.name}: {skill.description}")
        print(f"    Source: {skill.metadata.get('source', 'unknown')}")
    print()

    # Use the official SDK pattern with AgentOptions
    if skills:
        print("Using skill with AgentOptions (official SDK pattern):\n")
        options = AgentOptions(
            cwd=str(example_dir),
            setting_sources=["project"],
            allowed_tools=["Skill", "Read", "Write"],
            max_tokens=500,
        )

        async for msg in query(
            "What skills are available? List them briefly.",
            options,
        ):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
    print("\n")


# =============================================================================
# Example 2: Loading a Single Skill from File
# =============================================================================


async def single_skill_example():
    """Demonstrate loading a single skill from a SKILL.md file."""
    print("=== Single Skill Loading Example ===\n")

    example_dir = Path(__file__).parent
    skill_path = example_dir / ".claude" / "skills" / "pdf-processor"

    if skill_path.exists():
        # Load skill from file directly
        skill = Skill.from_file(skill_path)

        print(f"Loaded skill: {skill.name}")
        print(f"Description: {skill.description}")
        print(f"Version: {skill.metadata.get('version', 'unknown')}")
        print(f"Tags: {skill.metadata.get('tags', [])}")
        print()

        # Use the skill
        options = skill.create_options(max_tokens=300)

        print("Using loaded skill:\n")
        async for msg in query(
            "What can you help me with regarding PDF documents? Be brief.",
            options,
        ):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
    else:
        print(f"Skill not found at: {skill_path}")
        print("Run this example from the examples/skills directory.")
    print("\n")


# =============================================================================
# Example 3: Registering Skills to Global Registry
# =============================================================================


async def registry_example():
    """Demonstrate registering skills to the global registry."""
    print("=== Skill Registry Example ===\n")

    example_dir = Path(__file__).parent

    # Load all skills and register them globally
    registered = load_skills_to_registry(cwd=example_dir, setting_sources=["project"])

    print(f"Registered {len(registered)} skill(s):")
    for name in registered:
        print(f"  - {name}")

    # List all registered skills
    all_skills = list_skills()
    print(f"\nAll registered skills: {all_skills}")
    print("\n")


# =============================================================================
# Example 4: Creating Skills Programmatically (for development)
# =============================================================================


async def programmatic_skill_example():
    """Demonstrate creating skills programmatically.

    Note: The official SDK recommends creating skills as SKILL.md files.
    Programmatic creation is useful for development and testing.
    """
    print("=== Programmatic Skill Example ===\n")

    # Create a skill programmatically
    code_reviewer = Skill(
        name="code_reviewer",
        description="Review code for best practices, bugs, and improvements",
        system_prompt="""You are an expert code reviewer. You help users by:
- Identifying potential bugs and issues
- Suggesting improvements for readability
- Recommending best practices
- Explaining complex code patterns

Be constructive and specific in your feedback.""",
        temperature=0.3,
        max_tokens=2000,
        metadata={"category": "development", "version": "1.0.0"},
    )

    print(f"Created skill: {code_reviewer.name}")
    print(f"Description: {code_reviewer.description}")
    print()

    # Use the skill
    options = code_reviewer.create_options(max_tokens=300)

    print("Using programmatic skill:\n")
    async for msg in query(
        "What are 3 key things you look for when reviewing Python code?",
        options,
    ):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(block.text)
    print("\n")


# =============================================================================
# Main
# =============================================================================


async def main():
    """Run all skill examples."""
    print("=" * 60)
    print("Universal Agent SDK - Skills Examples")
    print("=" * 60)
    print()
    print("Skills are filesystem artifacts (SKILL.md files) that extend")
    print("Claude with specialized capabilities.")
    print()

    await filesystem_skills_example()
    await single_skill_example()
    await registry_example()
    await programmatic_skill_example()


if __name__ == "__main__":
    asyncio.run(main())
