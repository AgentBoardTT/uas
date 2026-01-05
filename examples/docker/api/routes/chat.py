"""Chat endpoints with SSE streaming."""

import logging
from typing import AsyncIterator

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse

from ..container_manager import container_manager
from ..models import ChatRequest
from ..session_manager import SessionNotFoundError, session_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


async def stream_response(
    session_id: str,
    message: str,
) -> AsyncIterator[str]:
    """Stream responses from the agent container."""
    try:
        session = await session_manager.get_session(session_id)
    except SessionNotFoundError:
        yield f"data: {{'error': 'Session not found'}}\n\n"
        return

    # Add user message to history
    session.add_message("user", message)

    try:
        # Stream from container
        async for line in container_manager.execute_query(
            container_info=session.container_info,
            message=message,
            history=session.conversation_history[:-1],  # Exclude current message
        ):
            yield f"{line}\n"

            # Extract assistant response for history
            if line.startswith("data: ") and '"type": "text"' in line:
                # This is a simplification - actual parsing would be more complex
                pass

        # Mark session as active
        session.touch()

    except Exception as e:
        logger.error(f"Error streaming response: {e}")
        yield f"data: {{'error': '{str(e)}'}}\n\n"


@router.post("")
async def chat(
    request: ChatRequest,
    x_session_id: str | None = Header(None),
):
    """Send a message and stream the response."""
    session_id = request.session_id or x_session_id

    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")

    return StreamingResponse(
        stream_response(session_id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history for a session."""
    try:
        session = await session_manager.get_session(session_id)
        return {
            "session_id": session_id,
            "messages": session.conversation_history,
            "message_count": session.message_count,
        }
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
