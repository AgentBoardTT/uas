"""Skill loader for discovering and loading skills from filesystem.

Skills are defined as directories containing a SKILL.md file with YAML frontmatter
and Markdown content. This module provides utilities to discover and parse these
skill definitions.

Skills can be loaded from:
- Bundled skills: Pre-packaged skills from Anthropic's official repository
- User skills: ~/.claude/skills/ (personal skills)
- Project skills: <cwd>/.claude/skills/ (project-specific skills)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .base import Skill
from .registry import SkillRegistry

# Path to bundled skills within the package
BUNDLED_SKILLS_DIR = Path(__file__).parent / "bundled"


@dataclass
class SkillMetadata:
    """Metadata parsed from SKILL.md frontmatter.

    Attributes:
        name: Unique identifier for the skill (defaults to directory name)
        description: Brief description that determines when Claude invokes the skill
        allowed_tools: List of tools the skill can use (SDK ignores this)
        version: Optional version string
        author: Optional author information
        tags: Optional list of tags for categorization
    """

    name: str
    description: str
    allowed_tools: list[str] = field(default_factory=list)
    version: str | None = None
    author: str | None = None
    tags: list[str] = field(default_factory=list)


def parse_skill_md(
    content: str, default_name: str = "skill"
) -> tuple[SkillMetadata, str]:
    """Parse a SKILL.md file with YAML frontmatter.

    Args:
        content: The full content of the SKILL.md file
        default_name: Default name to use if not specified in frontmatter

    Returns:
        Tuple of (metadata, markdown_content)

    Raises:
        ValueError: If the file format is invalid
    """
    # Match YAML frontmatter between --- markers
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        # No frontmatter, treat entire content as markdown
        return SkillMetadata(name=default_name, description=""), content.strip()

    yaml_content = match.group(1)
    markdown_content = match.group(2).strip()

    # Parse YAML frontmatter
    try:
        frontmatter: dict[str, Any] = yaml.safe_load(yaml_content) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}") from e

    # Extract metadata
    metadata = SkillMetadata(
        name=frontmatter.get("name", default_name),
        description=frontmatter.get("description", ""),
        allowed_tools=frontmatter.get("allowed-tools", []),
        version=frontmatter.get("version"),
        author=frontmatter.get("author"),
        tags=frontmatter.get("tags", []),
    )

    return metadata, markdown_content


def load_skill_from_path(skill_dir: Path) -> Skill | None:
    """Load a skill from a directory containing SKILL.md.

    Args:
        skill_dir: Path to the skill directory

    Returns:
        Skill instance if valid, None otherwise
    """
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        return None

    try:
        content = skill_file.read_text(encoding="utf-8")
        metadata, system_prompt = parse_skill_md(content, default_name=skill_dir.name)

        return Skill(
            name=metadata.name,
            description=metadata.description,
            system_prompt=system_prompt,
            metadata={
                "source": str(skill_dir),
                "version": metadata.version,
                "author": metadata.author,
                "tags": metadata.tags,
                "allowed_tools": metadata.allowed_tools,
            },
        )
    except (ValueError, OSError):
        return None


def get_bundled_skills() -> list[Skill]:
    """Get all bundled skills from the package.

    Bundled skills are pre-packaged skills from Anthropic's official
    skills repository, included with the SDK.

    Returns:
        List of bundled Skill instances
    """
    skills: list[Skill] = []

    if BUNDLED_SKILLS_DIR.exists() and BUNDLED_SKILLS_DIR.is_dir():
        for skill_dir in BUNDLED_SKILLS_DIR.iterdir():
            if skill_dir.is_dir():
                skill = load_skill_from_path(skill_dir)
                if skill:
                    # Mark as bundled
                    skill.metadata["bundled"] = True
                    skills.append(skill)

    return skills


def list_bundled_skills() -> list[str]:
    """List names of all bundled skills.

    Returns:
        List of bundled skill names
    """
    return [skill.name for skill in get_bundled_skills()]


def get_bundled_skill(name: str) -> Skill | None:
    """Get a specific bundled skill by name.

    Args:
        name: The skill name to look for

    Returns:
        The Skill if found, None otherwise
    """
    skill_dir = BUNDLED_SKILLS_DIR / name
    if skill_dir.exists() and skill_dir.is_dir():
        skill = load_skill_from_path(skill_dir)
        if skill:
            skill.metadata["bundled"] = True
            return skill
    return None


def discover_skills(
    cwd: str | Path | None = None,
    setting_sources: list[str] | None = None,
    include_bundled: bool = False,
) -> list[Skill]:
    """Discover skills from filesystem locations.

    Skills are loaded from:
    - Bundled skills: Pre-packaged skills (when include_bundled=True)
    - User skills: ~/.claude/skills/ (when "user" in setting_sources)
    - Project skills: <cwd>/.claude/skills/ (when "project" in setting_sources)

    Args:
        cwd: Working directory for project skills (defaults to current directory)
        setting_sources: List of sources to load from ("user", "project")
        include_bundled: Whether to include bundled skills from the package

    Returns:
        List of discovered Skill instances
    """
    if setting_sources is None:
        setting_sources = []

    skills: list[Skill] = []
    seen_names: set[str] = set()

    # Bundled skills (from package)
    if include_bundled:
        for skill in get_bundled_skills():
            if skill.name not in seen_names:
                skills.append(skill)
                seen_names.add(skill.name)

    # User skills directory (~/.claude/skills/)
    if "user" in setting_sources:
        user_skills_dir = Path.home() / ".claude" / "skills"
        if user_skills_dir.exists() and user_skills_dir.is_dir():
            for skill_dir in user_skills_dir.iterdir():
                if skill_dir.is_dir():
                    loaded_skill = load_skill_from_path(skill_dir)
                    if loaded_skill and loaded_skill.name not in seen_names:
                        skills.append(loaded_skill)
                        seen_names.add(loaded_skill.name)

    # Project skills directory (<cwd>/.claude/skills/)
    if "project" in setting_sources:
        project_dir = Path(cwd) if cwd else Path.cwd()
        project_skills_dir = project_dir / ".claude" / "skills"
        if project_skills_dir.exists() and project_skills_dir.is_dir():
            for skill_dir in project_skills_dir.iterdir():
                if skill_dir.is_dir():
                    loaded_skill = load_skill_from_path(skill_dir)
                    if loaded_skill and loaded_skill.name not in seen_names:
                        skills.append(loaded_skill)
                        seen_names.add(loaded_skill.name)

    return skills


def load_skills_to_registry(
    cwd: str | Path | None = None,
    setting_sources: list[str] | None = None,
    include_bundled: bool = False,
) -> list[str]:
    """Discover and register skills from filesystem.

    This function discovers skills and registers them in the global SkillRegistry.

    Args:
        cwd: Working directory for project skills
        setting_sources: List of sources to load from
        include_bundled: Whether to include bundled skills from the package

    Returns:
        List of registered skill names
    """
    skills = discover_skills(
        cwd=cwd, setting_sources=setting_sources, include_bundled=include_bundled
    )

    registered_names: list[str] = []
    for skill in skills:
        SkillRegistry.register(skill)
        registered_names.append(skill.name)

    return registered_names
