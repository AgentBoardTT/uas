"""Tests for skills module."""

from pathlib import Path

import pytest

from universal_agent_sdk.skills import (
    Skill,
    SkillInvocationResult,
    SkillRegistry,
    SkillTool,
    create_skill_tool,
    discover_skills,
    get_bundled_skill,
    get_bundled_skills,
    list_bundled_skills,
    parse_skill_md,
)


class TestSkillMetadata:
    """Test SKILL.md parsing."""

    def test_parse_skill_md_with_frontmatter(self):
        """Test parsing SKILL.md with YAML frontmatter."""
        content = """---
name: test-skill
description: A test skill for testing
allowed-tools:
  - Read
  - Write
version: "1.0.0"
author: Test Author
tags:
  - test
  - example
---

# Test Skill

This is the skill content.

## Instructions

Do testing things.
"""
        metadata, prompt = parse_skill_md(content)

        assert metadata.name == "test-skill"
        assert metadata.description == "A test skill for testing"
        assert metadata.allowed_tools == ["Read", "Write"]
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert metadata.tags == ["test", "example"]
        assert "# Test Skill" in prompt
        assert "Do testing things" in prompt

    def test_parse_skill_md_without_frontmatter(self):
        """Test parsing SKILL.md without frontmatter."""
        content = """# Simple Skill

Just content without frontmatter.
"""
        metadata, prompt = parse_skill_md(content, default_name="simple")

        assert metadata.name == "simple"
        assert metadata.description == ""
        assert "# Simple Skill" in prompt


class TestBundledSkills:
    """Test bundled skills loading."""

    def test_list_bundled_skills(self):
        """Test listing bundled skill names."""
        skills = list_bundled_skills()

        assert len(skills) == 16
        assert "pdf" in skills
        assert "docx" in skills
        assert "pptx" in skills
        assert "xlsx" in skills
        assert "frontend-design" in skills
        assert "canvas-design" in skills
        assert "mcp-builder" in skills

    def test_get_bundled_skills(self):
        """Test getting all bundled skills."""
        skills = get_bundled_skills()

        assert len(skills) == 16
        assert all(isinstance(s, Skill) for s in skills)

    def test_get_bundled_skill(self):
        """Test getting a specific bundled skill."""
        pdf_skill = get_bundled_skill("pdf")

        assert pdf_skill is not None
        assert pdf_skill.name == "pdf"
        assert "PDF" in pdf_skill.description or "pdf" in pdf_skill.description.lower()
        assert pdf_skill.system_prompt  # Has content
        assert pdf_skill.metadata.get("bundled") is True

    def test_get_bundled_skill_not_found(self):
        """Test getting non-existent bundled skill."""
        result = get_bundled_skill("nonexistent")
        assert result is None

    def test_bundled_skill_has_source_metadata(self):
        """Test that bundled skills have source directory in metadata."""
        pdf_skill = get_bundled_skill("pdf")

        assert pdf_skill is not None
        source = pdf_skill.metadata.get("source")
        assert source is not None
        assert Path(source).exists()
        assert (Path(source) / "SKILL.md").exists()

    def test_bundled_skill_scripts_exist(self):
        """Test that bundled skills with scripts have the files."""
        pdf_skill = get_bundled_skill("pdf")
        assert pdf_skill is not None

        source = Path(pdf_skill.metadata.get("source", ""))
        scripts_dir = source / "scripts"

        assert scripts_dir.exists()
        assert any(scripts_dir.iterdir())  # Has files


class TestSkillRegistry:
    """Test skill registry."""

    def setup_method(self):
        """Clear registry before each test."""
        SkillRegistry.clear()

    def test_register_and_get_skill(self):
        """Test registering and retrieving a skill."""
        skill = Skill(
            name="test",
            description="Test skill",
            system_prompt="You are a test assistant.",
        )

        SkillRegistry.register(skill)
        retrieved = SkillRegistry.get("test")

        assert retrieved.name == "test"
        assert retrieved.description == "Test skill"

    def test_get_nonexistent_skill(self):
        """Test getting non-existent skill raises KeyError."""
        with pytest.raises(KeyError):
            SkillRegistry.get("nonexistent")

    def test_list_skills(self):
        """Test listing registered skills."""
        skill1 = Skill(name="skill1", description="First", system_prompt="...")
        skill2 = Skill(name="skill2", description="Second", system_prompt="...")

        SkillRegistry.register(skill1)
        SkillRegistry.register(skill2)

        names = SkillRegistry.list()
        assert "skill1" in names
        assert "skill2" in names


class TestSkillTool:
    """Test SkillTool for LLM integration."""

    def test_skill_tool_with_bundled_skills(self):
        """Test SkillTool loads bundled skills."""
        tool = SkillTool(include_bundled=True, include_registry=False)

        assert tool.name == "Skill"
        assert len(tool.list_skills()) == 16
        assert "pdf" in tool.list_skills()

    def test_skill_tool_description_has_available_skills(self):
        """Test tool description contains available_skills section."""
        tool = SkillTool(include_bundled=True, include_registry=False)

        assert "<available_skills>" in tool.description
        assert "</available_skills>" in tool.description
        assert '"pdf":' in tool.description

    def test_skill_tool_schema_has_skill_enum(self):
        """Test tool schema has skill names as enum in skill property."""
        tool = SkillTool(include_bundled=True, include_registry=False)

        schema = tool.input_schema
        assert "properties" in schema
        assert "skill" in schema["properties"]
        assert "enum" in schema["properties"]["skill"]
        assert "pdf" in schema["properties"]["skill"]["enum"]

    def test_invoke_skill(self):
        """Test invoking a skill returns correct result."""
        import asyncio

        tool = SkillTool(include_bundled=True, include_registry=False)

        result = asyncio.run(tool(skill="pdf"))

        assert isinstance(result, SkillInvocationResult)
        assert result.skill_name == "pdf"
        assert result.skill_prompt  # Has content
        assert result.base_dir  # Has path

    def test_invoke_skill_with_args(self):
        """Test invoking a skill with arguments."""
        import asyncio

        tool = SkillTool(include_bundled=True, include_registry=False)

        result = asyncio.run(tool(skill="pdf", args="Process file.pdf"))

        assert "Process file.pdf" in result.skill_prompt
        # Verify args appear in visible message
        assert "<command-args>Process file.pdf</command-args>" in result.visible_message

    def test_invoke_nonexistent_skill(self):
        """Test invoking non-existent skill raises KeyError."""
        import asyncio

        tool = SkillTool(include_bundled=True, include_registry=False)

        with pytest.raises(KeyError):
            asyncio.run(tool(skill="nonexistent"))

    def test_add_and_remove_skill(self):
        """Test adding and removing skills dynamically."""
        tool = SkillTool(include_bundled=False, include_registry=False)

        assert len(tool.list_skills()) == 0

        skill = Skill(name="custom", description="Custom skill", system_prompt="...")
        tool.add_skill(skill)

        assert "custom" in tool.list_skills()
        assert '"custom":' in tool.description

        tool.remove_skill("custom")
        assert "custom" not in tool.list_skills()

    def test_get_skill_summary(self):
        """Test getting skill summary."""
        tool = SkillTool(include_bundled=True, include_registry=False)

        summary = tool.get_skill_summary()

        assert "Available Skills:" in summary
        assert "pdf" in summary

    def test_skill_tool_definition(self):
        """Test tool definition is valid."""
        tool = SkillTool(include_bundled=True, include_registry=False)

        definition = tool.definition

        assert definition.name == "Skill"
        assert definition.description is not None
        assert definition.input_schema is not None
        assert definition.handler is not None


class TestCreateSkillTool:
    """Test create_skill_tool convenience function."""

    def test_create_skill_tool_with_bundled(self):
        """Test creating skill tool with bundled skills."""
        tool = create_skill_tool(include_bundled=True)

        assert len(tool.list_skills()) == 16

    def test_create_skill_tool_without_bundled(self):
        """Test creating skill tool without bundled skills."""
        tool = create_skill_tool(include_bundled=False)

        # May have skills from setting_sources if they exist
        # but shouldn't have bundled
        skills = tool.list_skills()
        for name in skills:
            skill = tool.get_skill(name)
            assert skill.metadata.get("bundled") is not True


class TestDiscoverSkills:
    """Test skill discovery."""

    def test_discover_bundled_skills(self):
        """Test discovering bundled skills."""
        skills = discover_skills(include_bundled=True)

        assert len(skills) == 16

    def test_discover_without_bundled(self):
        """Test discovering without bundled skills."""
        skills = discover_skills(include_bundled=False)

        # May have user/project skills, but check bundled flag
        for skill in skills:
            assert skill.metadata.get("bundled") is not True


class TestSkillFromFile:
    """Test loading skills from file."""

    def test_skill_from_file_bundled(self):
        """Test loading a bundled skill from file."""
        bundled_dir = (
            Path(__file__).parent.parent
            / "src"
            / "universal_agent_sdk"
            / "skills"
            / "bundled"
            / "pdf"
        )

        skill = Skill.from_file(bundled_dir)

        assert skill.name == "pdf"
        assert skill.description
        assert skill.system_prompt

    def test_skill_from_file_not_found(self):
        """Test loading non-existent skill raises error."""
        with pytest.raises(FileNotFoundError):
            Skill.from_file("/nonexistent/path")


class TestSkillBaseDir:
    """Test {baseDir} substitution in skills."""

    def test_base_dir_in_invocation_result(self):
        """Test that base_dir is provided in invocation result."""
        import asyncio

        tool = SkillTool(include_bundled=True, include_registry=False)

        result = asyncio.run(tool(skill="pdf"))

        assert result.base_dir
        assert Path(result.base_dir).exists()

    def test_base_dir_scripts_accessible(self):
        """Test that scripts are accessible via base_dir."""
        import asyncio

        tool = SkillTool(include_bundled=True, include_registry=False)

        result = asyncio.run(tool(skill="pdf"))

        scripts_dir = Path(result.base_dir) / "scripts"
        assert scripts_dir.exists()
        assert any(scripts_dir.glob("*.py"))

    def test_visible_message_format(self):
        """Test visible message has correct format with command-message and command-name tags."""
        import asyncio

        tool = SkillTool(include_bundled=True, include_registry=False)

        result = asyncio.run(tool(skill="pdf"))

        visible_msg = result.visible_message
        assert (
            '<command-message>The "pdf" skill is loading</command-message>'
            in visible_msg
        )
        assert "<command-name>pdf</command-name>" in visible_msg
