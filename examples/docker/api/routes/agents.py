"""Agent management endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..config_loader import get_default_config, load_config_by_id
from ..container_manager import container_manager
from ..models import (
    LaunchAgentRequest,
    LaunchAgentResponse,
    SessionInfo,
    SessionStatus,
)
from ..session_manager import SessionNotFoundError, session_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/launch", response_model=LaunchAgentResponse)
async def launch_agent(request: LaunchAgentRequest):
    """Launch a new agent session."""
    try:
        # Load configuration
        if request.config_id:
            config = load_config_by_id(request.config_id)
        elif request.config:
            config = request.config
        else:
            config = get_default_config()

        config_id = config.get("id")
        config_name = config.get("name", "Agent")

        # Create session placeholder
        session = await session_manager.create_session(
            api_key=request.api_key,
            config_id=config_id,
            config_name=config_name,
            container_info={},  # Will be updated
        )

        # Create container
        container_info = await container_manager.create_agent_container(
            session_id=session.session_id,
            agent_id=session.agent_id,
            config=config,
            api_key=request.api_key,
        )

        # Update session with container info
        session.container_info = container_info

        return LaunchAgentResponse(
            session_id=session.session_id,
            agent_id=session.agent_id,
            config_id=config_id,
            status=SessionStatus.RUNNING,
            created_at=session.created_at,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error launching agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions():
    """List all active sessions."""
    return await session_manager.list_sessions()


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get information about a specific session."""
    try:
        session = await session_manager.get_session(session_id)
        return session.to_info()
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.delete("/sessions/{session_id}")
async def stop_session(session_id: str):
    """Stop and cleanup a session."""
    try:
        await session_manager.get_session(session_id)  # Verify exists
        await session_manager.cleanup_session(session_id)
        return {"status": "stopped", "session_id": session_id}
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
