"""Skill tool for LLM-driven skill selection and invocation.

This implements the Skill tool pattern from Claude Agent SDK where:
1. Skill tool is registered in the tools array sent to Claude
2. Claude makes a tool_use call with skill name based on user query
3. The tool handler injects skill content as messages into conversation
4. Claude continues with the skill context and pre-approved tools

Flow:
  User: "Extract text from report.pdf"
  Claude: tool_use(name="Skill", input={"skill": "pdf"})
  System: Injects skill messages + context modifier
  Claude: (now has PDF skill context) tool_use(name="Bash", input={"command": "pdftotext..."})
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..tools.base import Tool
from ..types import ToolSchema
from .base import Skill
from .loader import get_bundled_skills
from .registry import SkillRegistry


@dataclass
class SkillMessage:
    """A message to inject into the conversation.

    Attributes:
        role: Message role ("user" or "assistant")
        content: Message content
        is_meta: If True, sent to API but hidden from UI
    """

    role: str
    content: str
    is_meta: bool = False


@dataclass
class SkillInvocationResult:
    """Result of invoking a skill via the Skill tool.

    This follows the Claude Agent SDK pattern where skill invocation:
    1. Returns a success result
    2. Injects messages into the conversation (visible + hidden)
    3. Provides context modifications (allowed tools, model override)

    Attributes:
        success: Whether skill was found and loaded
        skill_name: Name of the invoked skill
        messages: Messages to inject into conversation
        allowed_tools: Tools to pre-approve for this skill
        model_override: Optional model to use for skill execution
        base_dir: Path to skill directory for {baseDir} substitution
        metadata: Additional skill metadata
    """

    success: bool
    skill_name: str
    messages: list[SkillMessage] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    model_override: str | None = None
    base_dir: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def skill_prompt(self) -> str:
        """Get the full skill prompt (hidden message content)."""
        for msg in self.messages:
            if msg.is_meta:
                return msg.content
        return ""

    @property
    def visible_message(self) -> str:
        """Get the visible message content."""
        for msg in self.messages:
            if not msg.is_meta:
                return msg.content
        return ""


class SkillTool(Tool):
    """Tool for skill selection and invocation.

    The SkillTool is registered in Claude's tools array. When Claude
    determines a skill matches the user's intent, it makes a tool_use
    call. The tool then injects skill content as messages.

    Flow:
        1. Claude reads <available_skills> in tool description
        2. Claude reasons about user query and selects a skill
        3. Claude returns: tool_use(name="Skill", input={"skill": "pdf"})
        4. SkillTool.call() returns messages to inject into conversation
        5. System injects: visible "skill is loading" + hidden full prompt
        6. Claude continues with skill context and pre-approved tools

    Example:
        ```python
        from universal_agent_sdk.skills import SkillTool

        # Create skill tool with bundled skills
        skill_tool = SkillTool(include_bundled=True)

        # Add to agent's tools
        options = AgentOptions(tools=[skill_tool.definition])

        # When Claude makes tool_use call to "Skill":
        result = await skill_tool(skill="pdf")

        # Inject messages into conversation
        for msg in result.messages:
            if msg.is_meta:
                # Hidden from UI, sent to API
                conversation.add_hidden_message(msg.role, msg.content)
            else:
                # Visible to user
                conversation.add_message(msg.role, msg.content)

        # Apply context modifications
        if result.allowed_tools:
            context.pre_approve_tools(result.allowed_tools)
        ```
    """

    def __init__(
        self,
        skills: list[Skill] | None = None,
        include_bundled: bool = True,
        include_registry: bool = True,
    ):
        """Initialize the skill tool.

        Args:
            skills: List of skills to make available
            include_bundled: Whether to include bundled skills from package
            include_registry: Whether to include skills from SkillRegistry
        """
        self._skills: dict[str, Skill] = {}

        # Load skills from various sources
        if include_bundled:
            for skill in get_bundled_skills():
                self._skills[skill.name] = skill

        if include_registry:
            for skill in SkillRegistry.all().values():
                self._skills[skill.name] = skill

        if skills:
            for skill in skills:
                self._skills[skill.name] = skill

        # Build the tool definition
        super().__init__(
            name="Skill",
            description=self._build_description(),
            input_schema=self._build_schema(),
            handler=self._invoke_skill,
        )

    def _build_description(self) -> str:
        """Build tool description with available skills list."""
        description = """Execute a skill within the conversation.

Skills are specialized capabilities that extend Claude's abilities.
When a user's request matches a skill's description, invoke this tool.

"""
        if self._skills:
            description += "<available_skills>\n"
            for skill in sorted(self._skills.values(), key=lambda s: s.name):
                # Format: "name": description
                desc = (
                    skill.description[:100] if skill.description else "No description"
                )
                description += f'"{skill.name}": {desc}\n'
            description += "</available_skills>\n"
        else:
            description += "No skills currently available.\n"

        description += """
Usage:
- Invoke with the skill name exactly as shown above
- The skill's instructions will be loaded into context
- Tools specified in the skill will be pre-approved

IMPORTANT: Only invoke skills listed in <available_skills> above.
"""
        return description

    def _build_schema(self) -> ToolSchema:
        """Build JSON Schema for skill invocation."""
        skill_names = list(self._skills.keys())

        schema: ToolSchema = {
            "type": "object",
            "properties": {
                "skill": {
                    "type": "string",
                    "description": 'The skill name. E.g., "commit", "review-pr", or "pdf"',
                    "enum": skill_names if skill_names else ["none"],
                },
                "args": {
                    "type": "string",
                    "description": "Optional arguments for the skill",
                },
            },
            "required": ["skill"],
        }
        return schema

    async def _invoke_skill(
        self, skill: str, args: str | None = None
    ) -> SkillInvocationResult:
        """Invoke a skill and return messages to inject.

        This implements the Claude Code pattern:
        1. Validate skill exists
        2. Load skill content
        3. Return messages to inject (visible + hidden)
        4. Return context modifications (allowed tools)

        Args:
            skill: Name of the skill to invoke
            args: Optional arguments for the skill

        Returns:
            SkillInvocationResult with messages and context modifications

        Raises:
            KeyError: If skill is not found
        """
        if skill not in self._skills:
            available = ", ".join(sorted(self._skills.keys()))
            raise KeyError(f"Skill '{skill}' not found. Available skills: {available}")

        skill_obj = self._skills[skill]

        # Get metadata
        base_dir = skill_obj.metadata.get("source", "")
        allowed_tools = skill_obj.metadata.get("allowed_tools", [])
        model_override = skill_obj.metadata.get("model")

        # Build the skill prompt with {baseDir} substitution
        skill_prompt = skill_obj.system_prompt
        if base_dir:
            skill_prompt = skill_prompt.replace("{baseDir}", base_dir)

        # Add args context if provided
        if args:
            skill_prompt += f"\n\n## Skill Arguments\n\n{args}"

        # Build messages to inject (following Claude Code pattern)
        # Message 1: Visible to user with command-message, command-name, command-args tags
        visible_parts = [
            f'<command-message>The "{skill}" skill is loading</command-message>',
            f"<command-name>{skill}</command-name>",
        ]
        if args:
            visible_parts.append(f"<command-args>{args}</command-args>")
        visible_content = "\n".join(visible_parts)

        messages = [
            # Message 1: Visible to user
            SkillMessage(
                role="user",
                content=visible_content,
                is_meta=False,
            ),
            # Message 2: Hidden from UI, contains full skill prompt
            SkillMessage(
                role="user",
                content=skill_prompt,
                is_meta=True,
            ),
        ]

        return SkillInvocationResult(
            success=True,
            skill_name=skill,
            messages=messages,
            allowed_tools=allowed_tools,
            model_override=model_override,
            base_dir=base_dir,
            metadata=skill_obj.metadata,
        )

    def add_skill(self, skill: Skill) -> None:
        """Add a skill to the tool.

        Args:
            skill: Skill to add
        """
        self._skills[skill.name] = skill
        # Rebuild description and schema
        self.description = self._build_description()
        self.input_schema = self._build_schema()

    def remove_skill(self, name: str) -> None:
        """Remove a skill from the tool.

        Args:
            name: Name of skill to remove
        """
        if name in self._skills:
            del self._skills[name]
            # Rebuild description and schema
            self.description = self._build_description()
            self.input_schema = self._build_schema()

    def list_skills(self) -> list[str]:
        """List available skill names.

        Returns:
            List of skill names
        """
        return list(self._skills.keys())

    def get_skill(self, name: str) -> Skill:
        """Get a skill by name.

        Args:
            name: Skill name

        Returns:
            Skill instance

        Raises:
            KeyError: If skill not found
        """
        if name not in self._skills:
            raise KeyError(f"Skill '{name}' not found")
        return self._skills[name]

    def get_skill_summary(self) -> str:
        """Get a formatted summary of available skills.

        Returns:
            Formatted string with skill names and descriptions
        """
        if not self._skills:
            return "No skills available."

        lines = ["Available Skills:", ""]
        for skill in sorted(self._skills.values(), key=lambda s: s.name):
            desc = (
                skill.description[:80] + "..."
                if len(skill.description) > 80
                else skill.description
            )
            lines.append(f"  - {skill.name}: {desc}")

        return "\n".join(lines)


def create_skill_tool(
    cwd: str | Path | None = None,
    setting_sources: list[str] | None = None,
    include_bundled: bool = True,
) -> SkillTool:
    """Create a SkillTool with skills from filesystem.

    This is a convenience function that discovers skills from
    the specified locations and creates a SkillTool.

    Args:
        cwd: Working directory for project skills
        setting_sources: Sources to load from ("user", "project")
        include_bundled: Whether to include bundled skills

    Returns:
        Configured SkillTool instance

    Example:
        ```python
        from universal_agent_sdk.skills import create_skill_tool

        # Create tool with bundled + project skills
        skill_tool = create_skill_tool(
            cwd="/path/to/project",
            setting_sources=["project"],
            include_bundled=True
        )

        # Add to agent options
        options = AgentOptions(tools=[skill_tool.definition])
        ```
    """
    from .loader import discover_skills

    skills = discover_skills(
        cwd=cwd,
        setting_sources=setting_sources or [],
        include_bundled=include_bundled,
    )

    return SkillTool(skills=skills, include_bundled=False, include_registry=False)
