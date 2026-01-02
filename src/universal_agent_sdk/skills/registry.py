"""Skill registry for managing and discovering skills."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Skill


class SkillRegistry:
    """Registry for managing skills.

    Provides a central place to register, discover, and retrieve skills.

    Example:
        ```python
        from universal_agent_sdk.skills import SkillRegistry, Skill

        # Register a custom skill
        my_skill = Skill(name="my_skill", ...)
        SkillRegistry.register(my_skill)

        # Get a skill by name
        skill = SkillRegistry.get("my_skill")

        # List all skills
        for name in SkillRegistry.list():
            print(name)
        ```
    """

    _skills: dict[str, "Skill"] = {}

    @classmethod
    def register(cls, skill: "Skill") -> None:
        """Register a skill.

        Args:
            skill: The skill to register
        """
        cls._skills[skill.name] = skill

    @classmethod
    def get(cls, name: str) -> "Skill":
        """Get a skill by name.

        Args:
            name: The skill name

        Returns:
            The skill instance

        Raises:
            KeyError: If skill is not found
        """
        if name not in cls._skills:
            raise KeyError(
                f"Skill '{name}' not found. Available: {list(cls._skills.keys())}"
            )
        return cls._skills[name]

    @classmethod
    def list(cls) -> list[str]:
        """List all registered skill names.

        Returns:
            List of skill names
        """
        return list(cls._skills.keys())

    @classmethod
    def all(cls) -> dict[str, "Skill"]:
        """Get all registered skills.

        Returns:
            Dictionary of skill name to skill instance
        """
        return cls._skills.copy()

    @classmethod
    def clear(cls) -> None:
        """Clear all registered skills."""
        cls._skills.clear()


# Convenience functions
def register_skill(skill: "Skill") -> "Skill":
    """Register a skill and return it (for use as decorator-style).

    Args:
        skill: The skill to register

    Returns:
        The same skill instance
    """
    SkillRegistry.register(skill)
    return skill


def get_skill(name: str) -> "Skill":
    """Get a skill by name.

    Args:
        name: The skill name

    Returns:
        The skill instance
    """
    return SkillRegistry.get(name)


def list_skills() -> list[str]:
    """List all registered skill names.

    Returns:
        List of skill names
    """
    return SkillRegistry.list()
