# Web Backend

A Replit/Lovable-like web backend built with Universal Agent SDK.

## Overview

This example demonstrates building AI-powered web backends with:
- REST API endpoints for AI interactions
- WebSocket support for streaming
- Session management
- Multi-user support
- Multiple UI options (FastAPI, Streamlit, Gradio)

## Status

**Coming Soon** - This example is under development.

## Planned Implementations

### FastAPI Backend
Full-featured REST/WebSocket API for AI interactions.

### Streamlit App
Interactive data science and prototyping UI.

### Gradio Interface
Quick demo and testing interface.

## Planned Features

- [ ] REST API for completions
- [ ] WebSocket streaming endpoint
- [ ] Session management with Redis
- [ ] Rate limiting and authentication
- [ ] Multi-provider configuration
- [ ] Tool execution sandbox
- [ ] File upload/download handling

## Architecture

```
web-backend/
├── fastapi/
│   ├── main.py              # FastAPI application
│   ├── routers/
│   │   ├── chat.py          # Chat endpoints
│   │   ├── sessions.py      # Session management
│   │   └── tools.py         # Tool execution
│   ├── services/
│   │   └── agent.py         # SDK integration
│   └── models/
│       └── schemas.py       # Pydantic models
├── streamlit/
│   └── app.py               # Streamlit application
├── gradio/
│   └── app.py               # Gradio interface
└── docker-compose.yml       # Container orchestration
```

## FastAPI Usage (Planned)

```bash
# Run the server
uvicorn examples.web_backend.fastapi.main:app --reload

# API endpoints
POST /api/chat              # Send message
GET  /api/chat/stream       # WebSocket streaming
GET  /api/sessions          # List sessions
POST /api/sessions          # Create session
```

## Streamlit Usage (Planned)

```bash
streamlit run examples/web_backend/streamlit/app.py
```

## Docker Usage (Planned)

```bash
docker-compose up -d
```
