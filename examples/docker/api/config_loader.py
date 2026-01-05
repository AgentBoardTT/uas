"""Configuration loading from preset files."""

import logging
from pathlib import Path
from typing import Any

import yaml

from .config import settings
from .models import ConfigInfo

logger = logging.getLogger(__name__)


def load_config_from_file(path: Path) -> dict[str, Any]:
    """Load a configuration from a YAML or JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(f)
        else:
            import json
            return json.load(f)


def load_config_by_id(config_id: str) -> dict[str, Any]:
    """Load a configuration by its ID.

    Search order:
    1. configs/presets/{config_id}.yaml
    2. configs/presets/{config_id}.yml
    3. configs/presets/{config_id}.json
    """
    # Search in presets directory
    for ext in (".yaml", ".yml", ".json"):
        path = settings.presets_dir / f"{config_id}{ext}"
        if path.exists():
            config = load_config_from_file(path)
            config["id"] = config.get("id", config_id)
            return config

    raise FileNotFoundError(f"Config not found: {config_id}")


def list_available_configs() -> list[ConfigInfo]:
    """List all available configurations."""
    configs = []

    # Load presets
    if settings.presets_dir.exists():
        for path in settings.presets_dir.iterdir():
            if path.suffix in (".yaml", ".yml", ".json"):
                try:
                    config = load_config_from_file(path)
                    config_id = config.get("id", path.stem)
                    configs.append(ConfigInfo(
                        id=config_id,
                        name=config.get("name", config_id),
                        description=config.get("description"),
                        provider=config.get("provider", "claude"),
                        model=config.get("model"),
                        allowed_tools=config.get("allowed_tools", []),
                        is_preset=True,
                    ))
                except Exception as e:
                    logger.error(f"Error loading config {path}: {e}")

    return configs


def get_default_config() -> dict[str, Any]:
    """Get a default configuration."""
    return {
        "id": "default",
        "name": "Default Agent",
        "description": "A general-purpose AI assistant",
        "provider": "claude",
        "model": "claude-sonnet-4-20250514",
        "allowed_tools": [
            "Read",
            "Write",
            "Edit",
            "Bash",
            "Glob",
            "Grep",
            "WebSearch",
            "WebFetch",
            "DateTime",
        ],
        "system_prompt": "You are a helpful AI assistant with access to various tools.",
        "max_turns": 50,
        "permission_mode": "acceptEdits",
    }
