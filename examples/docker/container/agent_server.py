"""Agent server that runs inside the container.

This server uses the Universal Agent SDK to handle queries and streams
responses back via SSE.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Add the SDK to path if running locally
sdk_path = Path(__file__).parent.parent.parent.parent / "src"
if sdk_path.exists():
    sys.path.insert(0, str(sdk_path))

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    StreamEvent,
    UniversalAgentClient,
)
from universal_agent_sdk.tools import (
    BashTool,
    DateTimeTool,
    EditTool,
    GlobTool,
    GrepTool,
    ReadTool,
    WebFetchTool,
    WebSearchTool,
    WriteTool,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="UAS Agent Server")

# Load configuration from environment
AGENT_CONFIG = json.loads(os.environ.get("AGENT_CONFIG_JSON", "{}"))
SESSION_ID = os.environ.get("SESSION_ID", "default")
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", "/workspace")

# Global client for conversation persistence
_client: UniversalAgentClient | None = None


class QueryRequest(BaseModel):
    """Query request model."""

    message: str
    history: list[dict] = []


def get_tool_definitions():
    """Get tool definitions based on configuration."""
    allowed_tools = AGENT_CONFIG.get("allowed_tools", [])

    tool_map = {
        "Read": ReadTool,
        "Write": WriteTool,
        "Edit": EditTool,
        "Bash": BashTool,
        "Glob": GlobTool,
        "Grep": GrepTool,
        "WebSearch": WebSearchTool,
        "WebFetch": WebFetchTool,
        "DateTime": DateTimeTool,
    }

    tools = []

    # If no tools specified, include all
    if not allowed_tools:
        allowed_tools = list(tool_map.keys())

    for tool_name in allowed_tools:
        if tool_name in tool_map:
            tools.append(tool_map[tool_name]().to_tool_definition())

    # Always include DateTime for date awareness
    if "DateTime" not in allowed_tools:
        tools.append(DateTimeTool().to_tool_definition())

    return tools


def create_agent_options() -> AgentOptions:
    """Create agent options from configuration."""
    provider = AGENT_CONFIG.get("provider", "claude")
    model = AGENT_CONFIG.get("model")

    # Default models per provider
    if not model:
        if provider == "claude":
            model = "claude-sonnet-4-20250514"
        elif provider == "openai":
            model = "gpt-4o"
        else:
            model = "claude-sonnet-4-20250514"

    system_prompt = AGENT_CONFIG.get("system_prompt", "")
    if not system_prompt:
        system_prompt = f"""You are a helpful AI assistant with access to various tools.
You can read and write files, execute shell commands, search the web, and more.

Current date: {datetime.now().strftime('%Y-%m-%d')}
Working directory: {WORKSPACE_DIR}

Use your tools proactively to help the user with their tasks.
Always use the DateTime tool first when asked about current events or dates.
"""

    # Check if thinking should be enabled (default to False to match SDK behavior)
    enable_thinking = AGENT_CONFIG.get("enable_thinking", False)
    max_thinking_tokens = AGENT_CONFIG.get("max_thinking_tokens", 10000)

    # When extended thinking is enabled:
    # - temperature must be 1
    # - max_tokens must be > thinking.budget_tokens
    temperature = 1.0 if enable_thinking else AGENT_CONFIG.get("temperature", 0.7)
    base_max_tokens = AGENT_CONFIG.get("max_tokens", 4096)
    max_tokens = max(base_max_tokens, max_thinking_tokens + 4096) if enable_thinking else base_max_tokens

    options = AgentOptions(
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        tools=get_tool_definitions(),
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
        enable_thinking=enable_thinking,
        max_thinking_tokens=max_thinking_tokens if enable_thinking else None,
    )

    return options


async def get_client() -> UniversalAgentClient:
    """Get or create the agent client."""
    global _client
    if _client is None:
        options = create_agent_options()
        _client = UniversalAgentClient(options)
        await _client.__aenter__()
        logger.info(f"Created agent client with provider: {options.provider}")
    return _client


async def stream_query(message: str, history: list[dict]) -> AsyncIterator[str]:
    """Stream query responses as SSE events."""
    try:
        client = await get_client()

        # Send the message
        await client.send(message)

        # Track current tool for correlation
        current_tool_id = None
        current_tool_name = None
        tool_input_buffer = ""
        thinking_buffer = ""
        tool_start_time = None

        # Stream responses
        async for msg in client.receive():
            if isinstance(msg, StreamEvent):
                event_type = msg.event_type
                delta = msg.delta or {}
                timestamp = datetime.now().isoformat()

                # Handle tool execution events from SDK
                if event_type == "tool_execution_start":
                    tool_name = delta.get("tool_name", "unknown")
                    tool_use_id = delta.get("tool_use_id", "")
                    tool_input = delta.get("tool_input", {})
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool_name': tool_name, 'tool_use_id': tool_use_id, 'tool_input': tool_input, 'status': 'started', 'timestamp': timestamp})}\n\n"

                elif event_type == "tool_execution_complete":
                    tool_name = delta.get("tool_name", "unknown")
                    tool_use_id = delta.get("tool_use_id", "")
                    duration_ms = delta.get("duration_ms")
                    output = delta.get("output")
                    error = delta.get("error")

                    if delta.get("type") == "tool_execution_error":
                        yield f"data: {json.dumps({'type': 'tool_error', 'tool_name': tool_name, 'tool_use_id': tool_use_id, 'error': error, 'status': 'error', 'duration_ms': duration_ms, 'timestamp': timestamp})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'tool_complete', 'tool_name': tool_name, 'tool_use_id': tool_use_id, 'output': output, 'status': 'completed', 'duration_ms': duration_ms, 'timestamp': timestamp})}\n\n"

                # Handle content block events
                elif event_type == "content_block_start":
                    block_type = delta.get("type", "")
                    if block_type == "thinking":
                        thinking_buffer = ""

                elif event_type == "content_block_delta":
                    delta_type = delta.get("type", "")
                    if delta_type == "thinking_delta":
                        thinking_content = delta.get("thinking", "")
                        thinking_buffer += thinking_content
                        # Emit thinking event
                        yield f"data: {json.dumps({'type': 'thinking', 'content': thinking_content, 'timestamp': timestamp})}\n\n"
                    elif delta_type == "signature_delta":
                        # Signature for thinking - not needed for UI, just log
                        pass
                    elif delta_type == "input_json_delta":
                        # Accumulate tool input (for display purposes)
                        tool_input_buffer += delta.get("partial_json", "")
                    elif delta_type == "text_delta":
                        # Regular text streaming
                        text = delta.get("text", "")
                        yield f"data: {json.dumps({'type': 'stream', 'event_type': 'text_delta', 'delta': {'type': 'text', 'text': text}, 'timestamp': timestamp})}\n\n"

                elif event_type == "content_block_stop":
                    # Reset buffers but don't emit tool_complete here
                    # (tool_execution_complete will handle that)
                    tool_input_buffer = ""
                    thinking_buffer = ""

                else:
                    # Pass through other stream events
                    event_data = {
                        "type": "stream",
                        "event_type": event_type,
                        "timestamp": timestamp,
                    }
                    if delta:
                        event_data["delta"] = delta
                    yield f"data: {json.dumps(event_data)}\n\n"

            elif isinstance(msg, AssistantMessage):
                # Extract text content from message
                content = ""
                if hasattr(msg, "content"):
                    if isinstance(msg.content, str):
                        content = msg.content
                    elif isinstance(msg.content, list):
                        # Handle list of content blocks (TextBlock, etc.)
                        for block in msg.content:
                            if hasattr(block, "text"):
                                content += block.text
                            elif isinstance(block, str):
                                content += block
                            elif isinstance(block, dict) and "text" in block:
                                content += block["text"]
                    else:
                        content = str(msg.content)
                else:
                    content = str(msg)

                event_data = {
                    "type": "message",
                    "role": "assistant",
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                }
                yield f"data: {json.dumps(event_data)}\n\n"

        # Send done event
        yield f"data: {json.dumps({'type': 'done', 'timestamp': datetime.now().isoformat()})}\n\n"

    except Exception as e:
        logger.error(f"Error in stream_query: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"


@app.post("/query")
async def query(request: QueryRequest):
    """Handle a query and stream the response."""
    logger.info(f"Received query: {request.message[:100]}...")

    return StreamingResponse(
        stream_query(request.message, request.history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "session_id": SESSION_ID,
        "config_id": AGENT_CONFIG.get("id", "default"),
        "provider": AGENT_CONFIG.get("provider", "claude"),
    }


@app.get("/config")
async def get_config():
    """Get current agent configuration."""
    return {
        "id": AGENT_CONFIG.get("id"),
        "name": AGENT_CONFIG.get("name"),
        "provider": AGENT_CONFIG.get("provider"),
        "model": AGENT_CONFIG.get("model"),
        "allowed_tools": AGENT_CONFIG.get("allowed_tools", []),
    }


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    global _client
    if _client:
        await _client.__aexit__(None, None, None)
        _client = None
    logger.info("Agent server shutdown complete")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
