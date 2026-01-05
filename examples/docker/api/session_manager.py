"""Session management for agent containers."""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import AsyncIterator

from .config import settings
from .models import SessionInfo, SessionStatus

logger = logging.getLogger(__name__)


class AgentSession:
    """Represents an active agent session."""

    def __init__(
        self,
        session_id: str,
        agent_id: str,
        config_id: str | None,
        config_name: str,
        api_key: str,
        container_info: dict,
    ):
        self.session_id = session_id
        self.agent_id = agent_id
        self.config_id = config_id
        self.config_name = config_name
        self.api_key = api_key
        self.container_info = container_info
        self.status = SessionStatus.RUNNING
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.message_count = 0
        self.conversation_history: list[dict] = []

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.message_count += 1
        self.touch()

    def to_info(self) -> SessionInfo:
        """Convert to SessionInfo model."""
        return SessionInfo(
            session_id=self.session_id,
            agent_id=self.agent_id,
            config_id=self.config_id,
            config_name=self.config_name,
            status=self.status,
            created_at=self.created_at,
            last_activity=self.last_activity,
            message_count=self.message_count,
        )


class SessionNotFoundError(Exception):
    """Raised when a session is not found."""

    pass


class SessionManager:
    """Manages agent sessions and their lifecycle."""

    def __init__(self):
        self.sessions: dict[str, AgentSession] = {}
        self._cleanup_task: asyncio.Task | None = None
        self._container_manager = None

    def set_container_manager(self, container_manager) -> None:
        """Set the container manager reference."""
        self._container_manager = container_manager

    async def start(self) -> None:
        """Start the session manager and cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Session manager started")

    async def stop(self) -> None:
        """Stop the session manager and cleanup all sessions."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Cleanup all sessions
        for session_id in list(self.sessions.keys()):
            await self.cleanup_session(session_id)

        logger.info("Session manager stopped")

    async def create_session(
        self,
        api_key: str,
        config_id: str | None,
        config_name: str,
        container_info: dict,
    ) -> AgentSession:
        """Create a new agent session."""
        session_id = f"sess-{uuid.uuid4().hex[:12]}"
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"

        session = AgentSession(
            session_id=session_id,
            agent_id=agent_id,
            config_id=config_id,
            config_name=config_name,
            api_key=api_key,
            container_info=container_info,
        )

        self.sessions[session_id] = session
        logger.info(f"Created session {session_id} with config {config_id or 'inline'}")

        return session

    async def get_session(self, session_id: str) -> AgentSession:
        """Get a session by ID."""
        session = self.sessions.get(session_id)
        if not session:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        return session

    async def list_sessions(self) -> list[SessionInfo]:
        """List all active sessions."""
        return [session.to_info() for session in self.sessions.values()]

    async def cleanup_session(self, session_id: str) -> None:
        """Cleanup and remove a session."""
        session = self.sessions.pop(session_id, None)
        if session and self._container_manager:
            try:
                await self._container_manager.stop_container(session.container_info)
                logger.info(f"Cleaned up session {session_id}")
            except Exception as e:
                logger.error(f"Error cleaning up session {session_id}: {e}")

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup idle sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_idle_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_idle_sessions(self) -> None:
        """Cleanup sessions that have been idle too long."""
        timeout = timedelta(minutes=settings.session_idle_timeout_minutes)
        now = datetime.utcnow()

        idle_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if now - session.last_activity > timeout
        ]

        for session_id in idle_sessions:
            logger.info(f"Cleaning up idle session {session_id}")
            await self.cleanup_session(session_id)


# Global session manager instance
session_manager = SessionManager()
