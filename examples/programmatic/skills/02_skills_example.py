#!/usr/bin/env python3
"""Example demonstrating Skills usage with Universal Agent SDK.

Skills are specialized capabilities that extend Claude's abilities.
They are loaded from:
- Bundled skills: Pre-packaged skills from Anthropic's official repository
- User skills: ~/.claude/skills/ (personal skills)
- Project skills: <cwd>/.claude/skills/ (project-specific skills)

When Claude determines a user request matches a skill's description,
it invokes the Skill tool to load the skill's instructions and tools.
"""

import asyncio

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

# Import skills utilities from universal_agent_sdk
# (Skills module provides skill discovery, loading, and invocation)
from universal_agent_sdk.skills import (
    SkillTool,
    create_skill_tool,
    discover_skills,
    get_bundled_skill,
    list_bundled_skills,
)


async def list_available_skills():
    """List all bundled skills available in the SDK."""
    print("=== Available Bundled Skills ===")

    skills = list_bundled_skills()
    print(f"Found {len(skills)} bundled skills:\n")

    for name in sorted(skills):
        skill = get_bundled_skill(name)
        if skill:
            desc = skill.description[:60] + "..." if len(skill.description) > 60 else skill.description
            print(f"  - {name}: {desc}")

    print()


async def basic_skill_usage():
    """Basic example: Using skills with query().

    When you include "Skill" in allowed_tools and set setting_sources,
    Claude can automatically invoke skills based on your request.
    """
    print("=== Basic Skill Usage ===")
    print("Note: This example shows how to configure skills.")
    print("In a real scenario, Claude would invoke the PDF skill for PDF-related tasks.\n")

    # Configure options to enable skills
    options = AgentOptions(
        provider="anthropic",
        cwd=".",  # Project directory
        setting_sources=["user", "project"],  # Load skills from filesystem
        allowed_tools=["Skill", "Read", "Bash"],  # Enable Skill tool
    )

    # In a real scenario with a PDF file:
    # async for message in query(
    #     prompt="Extract text from invoice.pdf",
    #     options=options
    # ):
    #     if isinstance(message, AssistantMessage):
    #         for block in message.content:
    #             if isinstance(block, TextBlock):
    #                 print(f"Claude: {block.text}")
    #             elif isinstance(block, ToolUseBlock):
    #                 if block.name == "Skill":
    #                     print(f"Invoking skill: {block.input.get('skill')}")

    print("Options configured:")
    print(f"  - cwd: {options.cwd}")
    print(f"  - setting_sources: {options.setting_sources}")
    print(f"  - allowed_tools: {options.allowed_tools}")
    print()


async def skill_tool_direct_usage():
    """Example: Using SkillTool directly.

    You can use SkillTool directly to invoke skills programmatically.
    This is useful for custom agent implementations.
    """
    print("=== Direct SkillTool Usage ===")

    # Create a SkillTool with bundled skills
    skill_tool = SkillTool(include_bundled=True, include_registry=False)

    print(f"Loaded {len(skill_tool.list_skills())} skills")
    print(f"Available skills: {', '.join(sorted(skill_tool.list_skills())[:5])}...")
    print()

    # Invoke the PDF skill
    result = await skill_tool(skill="pdf")

    print(f"Invoked skill: {result.skill_name}")
    print(f"Success: {result.success}")
    print(f"Base directory: {result.base_dir}")
    print(f"Allowed tools: {result.allowed_tools}")
    print()

    # Show message structure
    print("Messages to inject into conversation:")
    for i, msg in enumerate(result.messages, 1):
        visibility = "hidden (is_meta=True)" if msg.is_meta else "visible"
        content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        print(f"  {i}. [{msg.role}] ({visibility})")
        print(f"     {content_preview}")
    print()


async def skill_with_args():
    """Example: Invoking a skill with arguments."""
    print("=== Skill with Arguments ===")

    skill_tool = SkillTool(include_bundled=True, include_registry=False)

    # Invoke skill with arguments
    result = await skill_tool(skill="pdf", args="Process invoice.pdf and extract all text")

    print(f"Skill: {result.skill_name}")
    print(f"Visible message:\n{result.visible_message}")
    print()

    # The args are included in both visible message and skill prompt
    print("Args appear in:")
    print(f"  - Visible: {'<command-args>' in result.visible_message}")
    print(f"  - Prompt: {'Process invoice.pdf' in result.skill_prompt}")
    print()


async def discover_project_skills():
    """Example: Discovering skills from filesystem."""
    print("=== Discover Skills from Filesystem ===")

    # Discover skills from various sources
    # - include_bundled=True: Include bundled skills from package
    # - setting_sources=["user"]: Load from ~/.claude/skills/
    # - setting_sources=["project"]: Load from <cwd>/.claude/skills/

    bundled_skills = discover_skills(include_bundled=True)
    print(f"Bundled skills: {len(bundled_skills)}")

    # To discover user/project skills:
    # user_skills = discover_skills(
    #     setting_sources=["user"],
    #     include_bundled=False
    # )
    #
    # project_skills = discover_skills(
    #     cwd="/path/to/project",
    #     setting_sources=["project"],
    #     include_bundled=False
    # )

    print()


async def create_custom_skill_tool():
    """Example: Creating a SkillTool with specific configuration."""
    print("=== Custom SkillTool Configuration ===")

    # Create skill tool with skills from filesystem
    skill_tool = create_skill_tool(
        cwd=".",  # Project directory
        setting_sources=["user", "project"],  # Load user and project skills
        include_bundled=True,  # Also include bundled skills
    )

    print(f"Total skills available: {len(skill_tool.list_skills())}")
    print()

    # Get tool definition for agent integration
    definition = skill_tool.definition
    print(f"Tool name: {definition.name}")
    print(f"Input schema properties: {list(definition.input_schema.get('properties', {}).keys())}")
    print()


async def main():
    """Run all skill examples."""
    await list_available_skills()
    await basic_skill_usage()
    await skill_tool_direct_usage()
    await skill_with_args()
    await discover_project_skills()
    await create_custom_skill_tool()


if __name__ == "__main__":
    asyncio.run(main())
