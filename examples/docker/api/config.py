"""Application configuration and settings."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # Container Settings
    container_provider: str = "docker"  # docker, subprocess
    agent_image: str = "uas/agent:latest"
    container_network: str = "uas-network"

    # Session Settings
    session_idle_timeout_minutes: int = 30
    max_sessions_per_user: int = 10

    # Paths
    # Default paths work for local dev; UAS_CONFIGS_DIR and UAS_PRESETS_DIR env vars override for Docker
    # Path(__file__) = examples/docker/api/config.py
    # parent.parent.parent.parent = repo root
    configs_dir: Path = Path(os.environ.get("UAS_CONFIGS_DIR", str(Path(__file__).parent.parent.parent.parent / "presets")))
    presets_dir: Path = Path(os.environ.get("UAS_PRESETS_DIR", str(Path(__file__).parent.parent.parent.parent / "presets")))

    # Storage
    workspace_base_dir: Path = Path("/tmp/uas-workspaces")

    class Config:
        env_prefix = "UAS_"
        env_file = ".env"


settings = Settings()

# Ensure directories exist
settings.workspace_base_dir.mkdir(parents=True, exist_ok=True)
