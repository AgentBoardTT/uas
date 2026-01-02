"""Pytest configuration and fixtures for Universal Agent SDK tests."""

import pytest


@pytest.fixture
def sample_options():
    """Provide sample AgentOptions for testing."""
    from universal_agent_sdk import AgentOptions

    return AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        system_prompt="You are a helpful assistant.",
    )


@pytest.fixture
def mock_api_key(monkeypatch):
    """Set mock API key for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
