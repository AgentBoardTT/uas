"""Pydantic models for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Session status enum."""

    STARTING = "starting"
    RUNNING = "running"
    IDLE = "idle"
    STOPPED = "stopped"
    ERROR = "error"


class LaunchAgentRequest(BaseModel):
    """Request to launch a new agent session."""

    api_key: str = Field(..., description="LLM provider API key")
    config_id: str | None = Field(None, description="Preset configuration ID")
    config: dict[str, Any] | None = Field(None, description="Inline configuration")
    provider: str | None = Field(None, description="Override container provider")


class LaunchAgentResponse(BaseModel):
    """Response after launching an agent."""

    session_id: str
    agent_id: str
    config_id: str | None
    status: SessionStatus
    created_at: datetime


class SessionInfo(BaseModel):
    """Information about an active session."""

    session_id: str
    agent_id: str
    config_id: str | None
    config_name: str
    status: SessionStatus
    created_at: datetime
    last_activity: datetime
    message_count: int


class ChatRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., description="User message")
    session_id: str = Field(..., description="Session ID")


class ConfigInfo(BaseModel):
    """Configuration information."""

    id: str
    name: str
    description: str | None
    provider: str
    model: str | None
    allowed_tools: list[str]
    is_preset: bool


class FileInfo(BaseModel):
    """File information in workspace."""

    name: str
    path: str
    size: int
    is_directory: bool
    modified_at: datetime | None


class UploadResponse(BaseModel):
    """Response after file upload."""

    uploaded_files: list[str]
    failed_files: list[str]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    active_sessions: int
