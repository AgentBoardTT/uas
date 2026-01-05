# Universal Agent SDK - Docker Web Application

A full-featured web application for running AI agents with the Universal Agent SDK. Features multiple preset configurations, session management, and a modern chat interface.

## Features

- **Multi-Preset Support**: Load and switch between different agent configurations
- **Session Management**: Create, resume, and manage multiple agent sessions
- **Real-time Streaming**: SSE-based streaming for responsive chat experience
- **Docker Isolation**: Each agent runs in an isolated container
- **Modern UI**: Next.js 15 with React 19 and Tailwind CSS
- **Provider Agnostic**: Works with Claude, OpenAI, and other providers

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Browser                          │
│                    (Next.js Frontend)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/SSE
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Server                             │
│                 (FastAPI on port 8000)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Sessions   │  │   Configs    │  │   Container Mgr  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/SSE
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent Containers                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Agent 1   │  │   Agent 2   │  │   Agent N   │         │
│  │ (SDK + LLM) │  │ (SDK + LLM) │  │ (SDK + LLM) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- An API key (Anthropic or OpenAI)

### Running with Docker Compose

```bash
# Navigate to the docker example directory
cd examples/docker

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Development Mode

For local development with hot reload:

```bash
# Use the development compose file
docker-compose -f docker-compose.dev.yml up

# Or run services separately:

# Terminal 1: API Server
cd examples/docker
pip install -r api_requirements.txt
UAS_CONTAINER_PROVIDER=subprocess uvicorn api.main:app --reload

# Terminal 2: Frontend
cd examples/docker/ui
npm install
npm run dev
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `UAS_DEBUG` | Enable debug mode | `false` |
| `UAS_CONTAINER_PROVIDER` | Provider type: `docker` or `subprocess` | `docker` |
| `UAS_AGENT_IMAGE` | Docker image for agents | `uas/agent:latest` |
| `UAS_CONTAINER_NETWORK` | Docker network name | `uas-network` |
| `UAS_SESSION_IDLE_TIMEOUT_MINUTES` | Session timeout | `30` |

### Adding Custom Presets

Create a YAML file in `configs/presets/`:

```yaml
id: my-agent
name: My Custom Agent
description: A custom agent configuration

provider: claude  # or openai
model: claude-sonnet-4-20250514

system_prompt: |
  You are a helpful AI assistant specialized in...

allowed_tools:
  - Read
  - Write
  - Bash
  - WebSearch

max_turns: 50
permission_mode: acceptEdits
```

## API Endpoints

### Agents
- `POST /api/agents/launch` - Launch a new agent session
- `GET /api/agents/sessions` - List active sessions
- `GET /api/agents/sessions/{id}` - Get session info
- `DELETE /api/agents/sessions/{id}` - Stop a session

### Chat
- `POST /api/chat` - Send message and stream response (SSE)
- `GET /api/chat/history/{session_id}` - Get conversation history

### Configs
- `GET /api/configs` - List available configurations
- `GET /api/configs/{id}` - Get configuration details

### Files
- `GET /api/files/{session_id}/list` - List workspace files
- `POST /api/files/{session_id}/upload` - Upload files
- `GET /api/files/{session_id}/download` - Download workspace as ZIP

## Directory Structure

```
docker/
├── api/                    # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── config.py           # Settings and configuration
│   ├── models.py           # Pydantic models
│   ├── session_manager.py  # Session lifecycle management
│   ├── container_manager.py# Container orchestration
│   ├── config_loader.py    # Preset loading
│   └── routes/             # API endpoints
│       ├── agents.py       # Agent management
│       ├── chat.py         # Chat with streaming
│       ├── configs.py      # Configuration listing
│       └── files.py        # File operations
├── container/              # Agent container code
│   ├── agent_server.py     # FastAPI server in container
│   └── requirements.txt    # Container dependencies
├── ui/                     # Next.js frontend
│   ├── app/                # Next.js app router
│   │   ├── page.tsx        # Dashboard
│   │   ├── chat/[id]/      # Chat interface
│   │   └── sessions/       # Session management
│   ├── lib/                # Utilities
│   │   ├── api-client.ts   # API client
│   │   └── store.ts        # Zustand state
│   └── package.json
├── configs/
│   └── presets/            # Agent preset configurations
├── docker-compose.yml      # Production compose
├── docker-compose.dev.yml  # Development compose
├── Dockerfile.api          # API server image
├── Dockerfile.agent        # Agent container image
└── Dockerfile.ui           # Frontend image
```

## Security Considerations

1. **API Keys**: Never store API keys on the server. The BYOK (Bring Your Own Key) model ensures keys are only stored client-side.

2. **Container Isolation**: Each agent runs in an isolated Docker container with:
   - Limited CPU and memory
   - Non-root user
   - Separate workspace volume

3. **Session Cleanup**: Idle sessions are automatically cleaned up after the timeout period.

## Troubleshooting

### Agent container fails to start

Check if the agent image was built:
```bash
docker images | grep uas/agent
```

Rebuild if needed:
```bash
docker build -t uas/agent:latest -f Dockerfile.agent ../..
```

### API connection issues

Ensure the API server is running and healthy:
```bash
curl http://localhost:8000/health
```

### Session timeouts

Sessions timeout after 30 minutes of inactivity. Resume a session by visiting its chat URL or launching a new one.

## License

MIT License - see the main project LICENSE file.
