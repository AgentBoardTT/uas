# CLI Tool

A Claude Code-like terminal application built with Universal Agent SDK.

## Overview

This example demonstrates building a full-featured CLI tool similar to Claude Code, with:
- Interactive REPL interface
- Tool execution with permission prompts
- Streaming responses
- Session management
- Configuration via presets

## Status

**Coming Soon** - This example is under development.

## Planned Features

- [ ] Interactive terminal interface with rich formatting
- [ ] Command history and auto-completion
- [ ] Tool approval prompts
- [ ] Session persistence
- [ ] Multiple provider support
- [ ] Preset configuration loading
- [ ] Slash commands (/help, /clear, /model, etc.)

## Usage (Planned)

```bash
# Start interactive session
uv run python -m examples.cli_tool

# With specific preset
uv run python -m examples.cli_tool --preset code-assistant

# With specific provider
uv run python -m examples.cli_tool --provider openai --model gpt-4o
```

## Architecture

```
cli-tool/
├── __main__.py          # Entry point
├── app.py               # Main application
├── repl.py              # REPL interface
├── commands.py          # Slash commands
├── permissions.py       # Tool permission handling
└── ui/
    ├── terminal.py      # Terminal UI
    └── formatting.py    # Output formatting
```
