"""Skills module for Universal Agent SDK.

Skills are reusable, composable agent capabilities that combine system prompts,
tools, and configuration. This module provides both built-in skills from
Anthropic's official skills repository and utilities for creating custom skills.

Skills in the SDK are:
1. **Defined as filesystem artifacts**: Created as `SKILL.md` files in `.claude/skills/`
2. **Loaded from filesystem**: Skills are loaded via `setting_sources` configuration
3. **Automatically discovered**: Skill metadata is discovered from user and project directories
4. **Model-invoked**: Claude autonomously chooses when to use them based on context
5. **Enabled via allowed_tools**: Add `"Skill"` to your `allowed_tools` to enable Skills

Example:
    ```python
    from universal_agent_sdk import query, AgentOptions

    # Load skills from filesystem
    options = AgentOptions(
        cwd="/path/to/project",  # Project with .claude/skills/
        setting_sources=["user", "project"],  # Load Skills from filesystem
        allowed_tools=["Skill", "Read", "Write", "Bash"]  # Enable Skill tool
    )

    async for msg in query("Help me process this PDF document", options):
        print(msg)
    ```

    ```python
    # Load a skill from file directly
    from universal_agent_sdk.skills import Skill

    skill = Skill.from_file(".claude/skills/my-skill/")
    ```

    ```python
    # Discover all skills from filesystem
    from universal_agent_sdk.skills import discover_skills

    skills = discover_skills(
        cwd="/path/to/project",
        setting_sources=["user", "project"]
    )
    ```
"""

from .base import Skill, combine_skills

# Import all built-in skills
from .builtin import (
    AlgorithmicArtSkill,
    BrandGuidelinesSkill,
    CanvasDesignSkill,
    DocCoauthoringSkill,
    DocxSkill,
    FrontendDesignSkill,
    InternalCommsSkill,
    MCPBuilderSkill,
    PDFSkill,
    PPTXSkill,
    SkillCreatorSkill,
    SlackGifCreatorSkill,
    ThemeFactorySkill,
    WebappTestingSkill,
    WebArtifactsBuilderSkill,
    XLSXSkill,
)
from .loader import (
    SkillMetadata,
    discover_skills,
    get_bundled_skill,
    get_bundled_skills,
    list_bundled_skills,
    load_skill_from_path,
    load_skills_to_registry,
    parse_skill_md,
)
from .registry import SkillRegistry, get_skill, list_skills, register_skill
from .tool import SkillInvocationResult, SkillMessage, SkillTool, create_skill_tool

__all__ = [
    # Base
    "Skill",
    "combine_skills",
    # Registry
    "SkillRegistry",
    "register_skill",
    "get_skill",
    "list_skills",
    # Loader
    "discover_skills",
    "get_bundled_skill",
    "get_bundled_skills",
    "list_bundled_skills",
    "load_skill_from_path",
    "load_skills_to_registry",
    "parse_skill_md",
    "SkillMetadata",
    # Built-in Skills
    "PDFSkill",
    "DocxSkill",
    "PPTXSkill",
    "XLSXSkill",
    "FrontendDesignSkill",
    "CanvasDesignSkill",
    "WebArtifactsBuilderSkill",
    "WebappTestingSkill",
    "MCPBuilderSkill",
    "SkillCreatorSkill",
    "BrandGuidelinesSkill",
    "InternalCommsSkill",
    "DocCoauthoringSkill",
    "AlgorithmicArtSkill",
    "ThemeFactorySkill",
    "SlackGifCreatorSkill",
    # Skill Tool
    "SkillTool",
    "SkillMessage",
    "SkillInvocationResult",
    "create_skill_tool",
]
