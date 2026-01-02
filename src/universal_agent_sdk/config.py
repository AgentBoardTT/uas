"""Configuration and secrets management for Universal Agent SDK.

This module provides a simple, secure way to manage API keys and configuration
across different providers with support for:
- Environment variables
- .env files (via python-dotenv)
- Direct configuration
- Secret managers (AWS, GCP, Azure)

Example:
    ```python
    from universal_agent_sdk.config import Config

    # Auto-loads from .env and environment variables
    config = Config()

    # Get API key for a provider
    api_key = config.get_api_key("claude")

    # Or use with the SDK directly
    from universal_agent_sdk import query, AgentOptions

    options = AgentOptions(
        provider="claude",
        provider_config=config.get_provider_config("claude"),
    )
    ```
"""

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Provider name mappings
PROVIDER_ENV_VARS: dict[str, dict[str, str]] = {
    "claude": {
        "api_key": "ANTHROPIC_API_KEY",
        "base_url": "ANTHROPIC_BASE_URL",
    },
    "anthropic": {
        "api_key": "ANTHROPIC_API_KEY",
        "base_url": "ANTHROPIC_BASE_URL",
    },
    "openai": {
        "api_key": "OPENAI_API_KEY",
        "base_url": "OPENAI_BASE_URL",
        "organization": "OPENAI_ORG_ID",
    },
    "azure_openai": {
        "api_key": "AZURE_OPENAI_API_KEY",
        "azure_endpoint": "AZURE_OPENAI_ENDPOINT",
        "api_version": "AZURE_OPENAI_API_VERSION",
        "deployment_name": "AZURE_OPENAI_DEPLOYMENT",
    },
    "gemini": {
        "api_key": "GOOGLE_API_KEY",
        "project_id": "GOOGLE_PROJECT_ID",
        "location": "GOOGLE_LOCATION",
    },
    "ollama": {
        "base_url": "OLLAMA_BASE_URL",
    },
}

# Default values
DEFAULTS: dict[str, dict[str, str]] = {
    "azure_openai": {
        "api_version": "2024-02-01",
    },
    "ollama": {
        "base_url": "http://localhost:11434",
    },
}


def _load_dotenv(env_file: str | Path | None = None) -> bool:
    """Load environment variables from .env file.

    Args:
        env_file: Path to .env file. If None, searches current and parent dirs.

    Returns:
        True if .env file was loaded, False otherwise.
    """
    try:
        from dotenv import load_dotenv

        if env_file:
            return load_dotenv(env_file)
        else:
            # Search for .env in current and parent directories
            current = Path.cwd()
            for path in [current, *current.parents]:
                env_path = path / ".env"
                if env_path.exists():
                    return load_dotenv(env_path)
            return False
    except ImportError:
        return False


@dataclass
class Config:
    """Configuration manager for Universal Agent SDK.

    Provides a unified interface for managing API keys and configuration
    across multiple LLM providers.

    Attributes:
        auto_load_dotenv: Automatically load .env file on init
        env_file: Path to specific .env file
        secret_fetcher: Custom function to fetch secrets (for secret managers)

    Example:
        ```python
        # Basic usage - auto-loads from environment
        config = Config()
        api_key = config.get_api_key("claude")

        # With custom .env file
        config = Config(env_file=".env.production")

        # With AWS Secrets Manager
        config = Config(secret_fetcher=my_aws_secret_fetcher)
        ```
    """

    auto_load_dotenv: bool = True
    env_file: str | Path | None = None
    secret_fetcher: Callable[[str], str | None] | None = None
    _overrides: dict[str, dict[str, str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.auto_load_dotenv:
            _load_dotenv(self.env_file)

    def get_api_key(self, provider: str) -> str | None:
        """Get API key for a provider.

        Args:
            provider: Provider name (claude, openai, azure_openai, gemini, ollama)

        Returns:
            API key string or None if not found
        """
        return self._get_value(provider, "api_key")

    def get_provider_config(self, provider: str) -> dict[str, Any]:
        """Get full configuration for a provider.

        Args:
            provider: Provider name

        Returns:
            Dictionary with all available configuration for the provider
        """
        provider = provider.lower()
        env_vars = PROVIDER_ENV_VARS.get(provider, {})
        defaults = DEFAULTS.get(provider, {})
        overrides = self._overrides.get(provider, {})

        config: dict[str, Any] = {}

        # Apply defaults first
        config.update(defaults)

        # Then environment variables
        for config_key in env_vars:
            value = self._get_value(provider, config_key)
            if value is not None:
                config[config_key] = value

        # Finally overrides
        config.update(overrides)

        return config

    def set(self, provider: str, key: str, value: str) -> "Config":
        """Set a configuration value (override).

        Args:
            provider: Provider name
            key: Configuration key (e.g., 'api_key', 'base_url')
            value: Configuration value

        Returns:
            Self for chaining
        """
        provider = provider.lower()
        if provider not in self._overrides:
            self._overrides[provider] = {}
        self._overrides[provider][key] = value
        return self

    def set_api_key(self, provider: str, api_key: str) -> "Config":
        """Set API key for a provider.

        Args:
            provider: Provider name
            api_key: API key value

        Returns:
            Self for chaining
        """
        return self.set(provider, "api_key", api_key)

    def _get_value(self, provider: str, key: str) -> str | None:
        """Get a configuration value from various sources.

        Priority: overrides > secret_fetcher > environment > defaults
        """
        provider = provider.lower()

        # Check overrides first
        if provider in self._overrides and key in self._overrides[provider]:
            return self._overrides[provider][key]

        # Get env var name
        env_vars = PROVIDER_ENV_VARS.get(provider, {})
        env_var = env_vars.get(key)

        # Try secret fetcher
        if self.secret_fetcher and env_var:
            secret = self.secret_fetcher(env_var)
            if secret:
                return secret

        # Try environment variable
        if env_var:
            value = os.environ.get(env_var)
            if value:
                return value

        # Try defaults
        defaults = DEFAULTS.get(provider, {})
        return defaults.get(key)

    def validate(self, provider: str) -> list[str]:
        """Validate configuration for a provider.

        Args:
            provider: Provider name

        Returns:
            List of missing required configuration keys
        """
        provider = provider.lower()
        missing: list[str] = []

        # Check required keys
        if provider in (
            "claude",
            "anthropic",
            "openai",
            "gemini",
        ) and not self.get_api_key(provider):
            missing.append("api_key")

        if provider == "azure_openai":
            if not self.get_api_key(provider):
                missing.append("api_key")
            config = self.get_provider_config(provider)
            if not config.get("azure_endpoint"):
                missing.append("azure_endpoint")

        return missing

    def is_configured(self, provider: str) -> bool:
        """Check if a provider is properly configured.

        Args:
            provider: Provider name

        Returns:
            True if all required configuration is present
        """
        return len(self.validate(provider)) == 0

    def list_configured_providers(self) -> list[str]:
        """List all properly configured providers.

        Returns:
            List of provider names that are ready to use
        """
        configured = []
        for provider in PROVIDER_ENV_VARS:
            if self.is_configured(provider):
                configured.append(provider)
        return configured

    @classmethod
    def from_dict(cls, config_dict: dict[str, dict[str, str]]) -> "Config":
        """Create Config from a dictionary.

        Args:
            config_dict: Dictionary mapping provider names to their config

        Returns:
            Configured Config instance

        Example:
            ```python
            config = Config.from_dict({
                "claude": {"api_key": "sk-ant-..."},
                "openai": {"api_key": "sk-..."},
            })
            ```
        """
        instance = cls(auto_load_dotenv=False)
        instance._overrides = config_dict.copy()
        return instance


# Convenience functions
_default_config: Config | None = None


def get_config() -> Config:
    """Get the default global configuration instance.

    Returns:
        Global Config instance (creates one if needed)
    """
    global _default_config
    if _default_config is None:
        _default_config = Config()
    return _default_config


def get_api_key(provider: str) -> str | None:
    """Get API key for a provider using default config.

    Args:
        provider: Provider name

    Returns:
        API key or None
    """
    return get_config().get_api_key(provider)


def get_provider_config(provider: str) -> dict[str, Any]:
    """Get provider configuration using default config.

    Args:
        provider: Provider name

    Returns:
        Provider configuration dictionary
    """
    return get_config().get_provider_config(provider)


# Secret manager helpers
def aws_secret_fetcher(secret_name: str) -> str | None:
    """Fetch secrets from AWS Secrets Manager.

    Args:
        secret_name: Name of the secret in AWS

    Returns:
        Secret value or None
    """
    try:
        import boto3  # type: ignore[import-not-found]

        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get("SecretString")
        return str(secret_string) if secret_string is not None else None
    except Exception:
        return None


def gcp_secret_fetcher(secret_name: str, project_id: str | None = None) -> str | None:
    """Fetch secrets from Google Cloud Secret Manager.

    Args:
        secret_name: Name of the secret
        project_id: GCP project ID (uses default if None)

    Returns:
        Secret value or None
    """
    try:
        from google.cloud import secretmanager  # type: ignore[import-not-found]

        client = secretmanager.SecretManagerServiceClient()
        project = project_id or os.environ.get("GOOGLE_PROJECT_ID", "")
        name = f"projects/{project}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        secret_data: str = response.payload.data.decode("UTF-8")
        return secret_data
    except Exception:
        return None


def azure_keyvault_fetcher(
    vault_url: str | None = None,
) -> Callable[[str], str | None]:
    """Create a fetcher for Azure Key Vault.

    Args:
        vault_url: Key Vault URL (uses AZURE_KEYVAULT_URL env var if None)

    Returns:
        Secret fetcher function
    """

    def fetcher(secret_name: str) -> str | None:
        try:
            from azure.identity import (  # type: ignore[import-not-found]
                DefaultAzureCredential,
            )
            from azure.keyvault.secrets import (  # type: ignore[import-not-found]
                SecretClient,
            )

            url = vault_url or os.environ.get("AZURE_KEYVAULT_URL", "")
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=url, credential=credential)
            secret = client.get_secret(secret_name)
            secret_value = secret.value
            return str(secret_value) if secret_value is not None else None
        except Exception:
            return None

    return fetcher
