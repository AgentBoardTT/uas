# Universal Agent SDK Examples

This directory contains examples demonstrating how to use the Universal Agent SDK.

## Directory Structure

```
examples/
├── programmatic/          # Direct SDK usage (Python library)
│   ├── quickstart/        # Getting started examples
│   ├── tools/             # Tool usage examples
│   ├── memory/            # Memory system examples
│   ├── skills/            # Skills framework examples
│   ├── hooks/             # Hook system examples
│   ├── agents/            # Agent and sub-agent examples
│   ├── providers/         # Multi-provider examples
│   ├── advanced/          # Advanced feature examples
│   │                      # (presets moved to repo root /presets)
│   └── showcase/          # Full-featured demo applications
│
├── docker/                # Docker web application (AVAILABLE)
│   ├── api/               # FastAPI backend
│   ├── container/         # Agent container server
│   ├── ui/                # Next.js frontend
│   └── configs/           # Agent presets
│
├── cli-tool/              # Claude Code-like terminal application
├── vscode-extension/      # GitHub Copilot-like VS Code extension
├── desktop-ide/           # Cursor-like desktop IDE
└── web-backend/           # Replit/Lovable-like web backend
```

## Quick Start

### 1. Basic Query
```bash
uv run python examples/programmatic/quickstart/01_basic_query.py
```

### 2. Interactive Chat
```bash
uv run python examples/programmatic/quickstart/04_interactive_chat.py
```

### 3. Using Presets
```bash
# List available presets
uv run python examples/programmatic/showcase/preset_loader.py --list

# Run with a preset
uv run python examples/programmatic/showcase/preset_loader.py --preset virtual-assistant
```

### 4. Ultimate Assistant (Full-featured)
```bash
uv run python examples/programmatic/showcase/ultimate_assistant.py
```

## Programmatic Examples

### Quickstart
- `01_basic_query.py` - Simple one-shot query
- `02_streaming.py` - Streaming responses
- `03_options_demo.py` - AgentOptions configuration
- `04_interactive_chat.py` - Multi-turn conversation
- `05_streaming_modes.py` - Different streaming modes

### Tools
- `01_custom_tools.py` - Creating custom tools with @tool decorator
- `02_builtin_tools.py` - Using built-in tools (Read, Write, Bash, etc.)
- `03_tool_permissions.py` - Tool permission callbacks
- `04_tools_option.py` - Configuring tools via AgentOptions
- `05_memory_tool.py` - Using the memory tool

### Memory
- `memory_example.py` - Conversation and persistent memory

### Skills
- `01_skills_basics.py` - Skill fundamentals
- `02_skills_example.py` - Complete skill examples

### Hooks
- `hooks_example.py` - Pre/post tool hooks, session hooks

### Agents
- `01_basic_agent.py` - Basic agent setup
- `02_agents_example.py` - Agent configuration
- `03_filesystem_agents.py` - File system agent

### Providers
- `provider_switching.py` - Switching between Claude, OpenAI, etc.

### Advanced
- `partial_messages.py` - Including partial messages
- `budget_limits.py` - Setting budget limits
- `setting_sources.py` - Configuration sources
- `stderr_callback.py` - Stderr callbacks
- `system_prompts.py` - System prompt configuration

### Presets (at repo root `/presets`)
YAML configuration files for pre-configured agents:
- `virtual-assistant.yaml` - General-purpose assistant (OpenAI)
- `code-assistant.yaml` - Code development assistant
- `research-agent.yaml` - Web research specialist
- `data-analysis.yaml` - Data analysis specialist
- `creative-developer.yaml` - Creative coding agent
- `fullstack-team.yaml` - Multi-agent development team

### Showcase
Full-featured demo applications:
- `ultimate_assistant.py` - Complete assistant with all tools and skills
- `virtual_assistant.py` - Virtual assistant demo
- `coding_agent.py` - Specialized coding agent
- `preset_loader.py` - Interactive preset-based chat

## Application Examples

### Docker Web Application (Available)
A full-featured web application with multi-session support. See `docker/README.md`.

```bash
# Start with Docker Compose
cd examples/docker
docker-compose up -d

# Access at http://localhost:3000
```

Features:
- Multiple preset configurations
- Session management (create, resume, stop)
- Real-time streaming chat
- Docker-isolated agent containers
- Modern Next.js 15 + React 19 UI

### CLI Tool (Coming Soon)
A Claude Code-like terminal application. See `cli-tool/README.md`.

### VS Code Extension (Coming Soon)
A GitHub Copilot-like VS Code extension. See `vscode-extension/README.md`.

### Desktop IDE (Coming Soon)
A Cursor-like desktop IDE application. See `desktop-ide/README.md`.

### Web Backend (Coming Soon)
A Replit/Lovable-like web backend. See `web-backend/README.md`.
