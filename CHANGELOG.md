# Changelog

All notable changes to the Universal Agent SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-XX-XX

### Added

- Initial release of Universal Agent SDK
- **Multi-Provider Support**
  - Claude (Anthropic) provider
  - OpenAI provider
  - Azure OpenAI provider
  - Gemini (Google) provider
  - Ollama (local) provider
- **Core Components**
  - `UniversalAgentClient` for multi-turn conversations
  - `query()` function for one-shot queries
  - `complete()` function for simple completions
  - `AgentOptions` configuration dataclass
- **Tool System**
  - `@tool` decorator for creating custom tools
  - `ToolRegistry` for managing tools
  - Built-in tools: Read, Write, Edit, Bash, Glob, Grep, NotebookEdit
  - Tool permission callbacks
- **Skills System**
  - `Skill` class for reusable configurations
  - `SkillRegistry` for managing skills
  - Skill discovery and loading
  - Skill composition with `combine_skills()`
- **Hooks System**
  - Pre/post tool execution hooks
  - Session lifecycle hooks
  - Error handling hooks
  - `HookMatcher` for event filtering
- **Agents System**
  - `Agent` and `SubAgent` classes
  - `AgentDefinition` for declarative agents
  - `AgentRegistry` for managing agents
  - Agent inheritance and tool sharing
- **Memory System**
  - `ConversationMemory` for session memory
  - `PersistentMemory` for cross-session storage
  - `FileSystemMemoryTool` for file-based memory
  - Memory search and retrieval
- **Type Safety**
  - Full type hints throughout
  - Pydantic models for validation
  - Dataclass configuration
- **Documentation**
  - Comprehensive documentation
  - API reference
  - Migration guide from Claude SDK
  - Working examples

### Notes

- Extracted from Claude Agent SDK as standalone package
- Designed for multi-provider LLM agent development
