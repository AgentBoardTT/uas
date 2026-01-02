# VS Code Extension

A GitHub Copilot-like VS Code extension built with Universal Agent SDK.

## Overview

This example demonstrates building an AI-powered VS Code extension with:
- Inline code completions
- Chat sidebar panel
- Code explanation and refactoring
- Multi-file context awareness

## Status

**Coming Soon** - This example is under development.

## Planned Features

- [ ] Inline code completions (ghost text)
- [ ] Chat panel with conversation history
- [ ] Code actions (explain, refactor, fix, document)
- [ ] Multi-file context using workspace indexing
- [ ] Tool execution for file operations
- [ ] Multiple provider support
- [ ] Settings configuration

## Architecture

```
vscode-extension/
├── package.json              # Extension manifest
├── src/
│   ├── extension.ts          # Extension entry point
│   ├── completions/
│   │   └── provider.ts       # Completion provider
│   ├── chat/
│   │   ├── panel.ts          # Chat webview panel
│   │   └── provider.ts       # Chat handler
│   ├── actions/
│   │   └── codeActions.ts    # Code action provider
│   └── sdk/
│       └── client.ts         # SDK integration (Python subprocess or WASM)
└── webview/
    └── chat/                 # Chat UI (React/Svelte)
```

## Development

```bash
# Install dependencies
npm install

# Build extension
npm run build

# Package for distribution
npm run package
```
