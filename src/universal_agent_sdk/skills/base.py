"""Base skill class and utilities."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..types import AgentOptions, ToolDefinition

if TYPE_CHECKING:
    pass


@dataclass
class Skill:
    """A reusable skill that combines prompts, tools, and configuration.

    Skills are the building blocks for creating specialized agents. Each skill
    defines a system prompt that guides the agent's behavior, along with
    optional tools and configuration.

    Attributes:
        name: Unique identifier for the skill
        description: Brief description of what the skill does
        system_prompt: The system prompt that defines the skill's behavior
        tools: List of tools available to the skill
        temperature: Default temperature for responses
        max_tokens: Default max tokens for responses
        metadata: Additional metadata about the skill

    Example:
        ```python
        # Create a custom skill
        my_skill = Skill(
            name="code_reviewer",
            description="Reviews code for best practices",
            system_prompt="You are a code review expert...",
            temperature=0.3,
        )

        # Use with query
        options = my_skill.create_options()
        async for msg in query("Review this code...", options):
            print(msg)
        ```
    """

    name: str
    description: str
    system_prompt: str
    tools: list[ToolDefinition] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 4096
    metadata: dict[str, Any] = field(default_factory=dict)

    def create_options(self, **kwargs: Any) -> AgentOptions:
        """Create AgentOptions from this skill.

        Args:
            **kwargs: Override any skill defaults

        Returns:
            AgentOptions configured with this skill's settings
        """
        return AgentOptions(
            system_prompt=kwargs.pop("system_prompt", self.system_prompt),
            tools=kwargs.pop("tools", self.tools),
            temperature=kwargs.pop("temperature", self.temperature),
            max_tokens=kwargs.pop("max_tokens", self.max_tokens),
            **kwargs,
        )

    def with_tools(self, *tools: ToolDefinition) -> "Skill":
        """Create a new skill with additional tools.

        Args:
            *tools: Tools to add to the skill

        Returns:
            New Skill instance with combined tools
        """
        return Skill(
            name=self.name,
            description=self.description,
            system_prompt=self.system_prompt,
            tools=[*self.tools, *tools],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            metadata=self.metadata.copy(),
        )

    def with_prompt(self, additional_prompt: str) -> "Skill":
        """Create a new skill with additional prompt instructions.

        Args:
            additional_prompt: Additional instructions to append

        Returns:
            New Skill instance with extended prompt
        """
        return Skill(
            name=self.name,
            description=self.description,
            system_prompt=f"{self.system_prompt}\n\n{additional_prompt}",
            tools=self.tools.copy(),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            metadata=self.metadata.copy(),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "Skill":
        """Load a skill from a SKILL.md file or directory.

        Args:
            path: Path to SKILL.md file or directory containing SKILL.md

        Returns:
            Skill instance loaded from the file

        Raises:
            FileNotFoundError: If the skill file doesn't exist
            ValueError: If the file format is invalid

        Example:
            ```python
            # Load from directory
            skill = Skill.from_file(".claude/skills/my-skill/")

            # Load from file directly
            skill = Skill.from_file(".claude/skills/my-skill/SKILL.md")
            ```
        """
        from .loader import parse_skill_md

        skill_path = Path(path)

        # Handle directory path
        if skill_path.is_dir():
            skill_path = skill_path / "SKILL.md"

        if not skill_path.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_path}")

        content = skill_path.read_text(encoding="utf-8")
        default_name = skill_path.parent.name
        metadata, system_prompt = parse_skill_md(content, default_name=default_name)

        return cls(
            name=metadata.name,
            description=metadata.description,
            system_prompt=system_prompt,
            metadata={
                "source": str(skill_path.parent),
                "version": metadata.version,
                "author": metadata.author,
                "tags": metadata.tags,
                "allowed_tools": metadata.allowed_tools,
            },
        )


def combine_skills(*skills: Skill, name: str | None = None) -> Skill:
    """Combine multiple skills into one.

    Creates a new skill that has the combined system prompts and tools
    from all provided skills.

    Args:
        *skills: Skills to combine
        name: Name for the combined skill (auto-generated if not provided)

    Returns:
        New Skill with combined capabilities

    Example:
        ```python
        combined = combine_skills(PDFSkill, DocxSkill, name="document_expert")
        options = combined.create_options()
        ```
    """
    if not skills:
        raise ValueError("At least one skill is required")

    if name is None:
        name = "_".join(s.name for s in skills)

    # Combine system prompts
    combined_prompt = "\n\n".join(
        f"## {skill.name.replace('_', ' ').title()} Capabilities\n\n{skill.system_prompt}"
        for skill in skills
    )

    # Combine tools (deduplicate by name)
    combined_tools: list[ToolDefinition] = []
    seen_names: set[str] = set()
    for skill in skills:
        for tool_def in skill.tools:
            if tool_def.name not in seen_names:
                combined_tools.append(tool_def)
                seen_names.add(tool_def.name)

    # Combine descriptions
    combined_description = " | ".join(s.description for s in skills)

    # Average temperature
    avg_temp = sum(s.temperature for s in skills) / len(skills)

    # Max of max_tokens
    max_tokens = max(s.max_tokens for s in skills)

    return Skill(
        name=name,
        description=combined_description,
        system_prompt=f"You are a versatile assistant with multiple capabilities:\n\n{combined_prompt}",
        tools=combined_tools,
        temperature=avg_temp,
        max_tokens=max_tokens,
        metadata={"combined_from": [s.name for s in skills]},
    )
