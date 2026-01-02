# Migration Plan: Universal Agent SDK Extraction

This document outlines the plan for extracting the Universal Agent SDK into a standalone repository at `/Users/huetuanthi/dev/agents/universal-agent-sdk-python`.

## Overview

**Source Repository:** `/Users/huetuanthi/dev/agents/claude-agent-sdk-python`
**Target Repository:** `/Users/huetuanthi/dev/agents/universal-agent-sdk-python`

## Phase 1: Repository Setup

### 1.1 Create New Repository Structure

```bash
mkdir -p /Users/huetuanthi/dev/agents/universal-agent-sdk-python
cd /Users/huetuanthi/dev/agents/universal-agent-sdk-python

# Initialize git
git init

# Create directory structure
mkdir -p src/universal_agent_sdk
mkdir -p tests
mkdir -p examples
mkdir -p docs
```

### 1.2 Initial Files to Create

```
universal-agent-sdk-python/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── release.yml
│       └── publish.yml
├── src/
│   └── universal_agent_sdk/
│       └── (SDK code)
├── tests/
│   └── (test files)
├── examples/
│   └── (example files)
├── docs/
│   └── (documentation)
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
└── CONTRIBUTING.md
```

## Phase 2: Source Code Migration

### 2.1 Files to Copy

Copy from `claude-agent-sdk-python/src/universal_agent_sdk/` to `universal-agent-sdk-python/src/universal_agent_sdk/`:

```
Source Files:
├── __init__.py              # Main exports
├── client.py                # UniversalAgentClient
├── query.py                 # query(), complete()
├── types.py                 # Type definitions
├── config.py                # Configuration
├── errors.py                # Exceptions
├── providers/               # All provider implementations
│   ├── __init__.py
│   ├── base.py
│   ├── claude.py
│   └── openai.py
├── tools/                   # Tool system
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   ├── memory.py
│   └── builtin/
│       ├── __init__.py
│       ├── read.py
│       ├── write.py
│       ├── edit.py
│       ├── bash.py
│       ├── glob.py
│       ├── grep.py
│       └── notebook_edit.py
├── skills/                  # Skills system
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   ├── loader.py
│   ├── tool.py
│   ├── builtin/
│   └── bundled/
├── agents/                  # Agents system
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   └── subagent.py
├── memory/                  # Memory system
│   ├── __init__.py
│   ├── base.py
│   ├── conversation.py
│   └── persistent.py
├── hooks/                   # Hooks (if separate)
├── cloud/                   # Cloud integrations
└── coding/                  # Coding utilities
```

### 2.2 Migration Commands

```bash
# Copy source files
cp -r /Users/huetuanthi/dev/agents/claude-agent-sdk-python/src/universal_agent_sdk/* \
      /Users/huetuanthi/dev/agents/universal-agent-sdk-python/src/universal_agent_sdk/

# Copy examples (universal_* files)
cp /Users/huetuanthi/dev/agents/claude-agent-sdk-python/examples/universal_*.py \
   /Users/huetuanthi/dev/agents/universal-agent-sdk-python/examples/

# Copy documentation
cp -r /Users/huetuanthi/dev/agents/claude-agent-sdk-python/docs/universal-sdk/* \
      /Users/huetuanthi/dev/agents/universal-agent-sdk-python/docs/
```

## Phase 3: Configuration Files

### 3.1 pyproject.toml

```toml
[project]
name = "universal-agent-sdk"
version = "0.1.0"
description = "Universal Agent SDK - Multi-provider LLM agent framework"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
keywords = [
    "llm",
    "ai",
    "agent",
    "claude",
    "openai",
    "anthropic",
    "multi-provider",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    "anthropic>=0.20.0",
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
openai = ["openai>=1.0.0"]
azure = ["openai>=1.0.0", "azure-identity>=1.14.0"]
gemini = ["google-generativeai>=0.3.0"]
ollama = ["ollama>=0.1.0"]
all = [
    "universal-agent-sdk[openai,azure,gemini,ollama]",
]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "black>=23.0.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/universal-agent-sdk-python"
Documentation = "https://github.com/yourusername/universal-agent-sdk-python/docs"
Repository = "https://github.com/yourusername/universal-agent-sdk-python"
Changelog = "https://github.com/yourusername/universal-agent-sdk-python/blob/main/CHANGELOG.md"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/universal_agent_sdk"]

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "D", "UP", "B", "C4", "SIM"]
ignore = ["D100", "D104", "D107"]

[tool.mypy]
python_version = "3.10"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 3.2 .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/

# Documentation
docs/_build/

# OS
.DS_Store
Thumbs.db

# Project specific
memories/
*.log
```

### 3.3 README.md

```markdown
# Universal Agent SDK

A comprehensive, multi-provider LLM agent framework for Python.

## Features

- **Multi-Provider Support**: Claude, OpenAI, Azure OpenAI, Gemini, Ollama
- **Unified API**: Same code works across all providers
- **Tool System**: Create custom tools with simple decorators
- **Skills System**: Reusable, composable agent configurations
- **Hooks System**: Intercept and modify agent behavior
- **Memory System**: Persistent and conversation memory
- **Type Safety**: Full type hints and dataclass configuration

## Installation

\`\`\`bash
pip install universal-agent-sdk
\`\`\`

With optional providers:

\`\`\`bash
pip install universal-agent-sdk[openai]  # OpenAI support
pip install universal-agent-sdk[all]     # All providers
\`\`\`

## Quick Start

\`\`\`python
import asyncio
from universal_agent_sdk import query, AgentOptions

async def main():
    options = AgentOptions(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
    )

    async for msg in query("What is Python?", options):
        print(msg)

asyncio.run(main())
\`\`\`

## Documentation

See the [documentation](./docs/) for complete guides.

## License

MIT License
```

## Phase 4: Test Migration

### 4.1 Copy and Update Tests

```bash
# Copy relevant tests
cp -r /Users/huetuanthi/dev/agents/claude-agent-sdk-python/tests/test_universal_*.py \
      /Users/huetuanthi/dev/agents/universal-agent-sdk-python/tests/
```

### 4.2 Update Test Imports

Update all test files to use the new package structure:

```python
# Before
from claude_agent_sdk.universal_agent_sdk import ...

# After
from universal_agent_sdk import ...
```

### 4.3 Create Test Configuration

```python
# tests/conftest.py
import pytest
import asyncio

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_provider():
    # Mock provider for testing
    pass
```

## Phase 5: CI/CD Setup

### 5.1 GitHub Actions - CI

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Lint with ruff
        run: ruff check src/ tests/

      - name: Type check with mypy
        run: mypy src/

      - name: Test with pytest
        run: pytest tests/ --cov=src/universal_agent_sdk --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 5.2 GitHub Actions - Publish

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install build tools
        run: pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## Phase 6: Cleanup and Finalization

### 6.1 Remove Internal References

Search and replace any internal references:

```bash
# Find references to old package
grep -r "claude_agent_sdk" src/
grep -r "claude-agent-sdk" src/

# Update all references
```

### 6.2 Update __init__.py Version

```python
# src/universal_agent_sdk/__init__.py
__version__ = "0.1.0"
```

### 6.3 Create CHANGELOG.md

```markdown
# Changelog

## [0.1.0] - 2024-XX-XX

### Added
- Initial release of Universal Agent SDK
- Multi-provider support (Claude, OpenAI, Azure, Gemini, Ollama)
- Tool system with @tool decorator
- Skills system for reusable configurations
- Hooks system for behavior modification
- Memory system (conversation and persistent)
- Agent system with subagent support
- Comprehensive documentation
```

### 6.4 Final Verification

```bash
cd /Users/huetuanthi/dev/agents/universal-agent-sdk-python

# Install in development mode
pip install -e ".[dev]"

# Run linting
ruff check src/ tests/
ruff format src/ tests/

# Run type checking
mypy src/

# Run tests
pytest tests/

# Build package
python -m build

# Test import
python -c "from universal_agent_sdk import query, UniversalAgentClient, AgentOptions; print('OK')"
```

## Phase 7: Migration Script

### Complete Migration Script

```bash
#!/bin/bash
# migrate_universal_sdk.sh

set -e

SOURCE_DIR="/Users/huetuanthi/dev/agents/claude-agent-sdk-python"
TARGET_DIR="/Users/huetuanthi/dev/agents/universal-agent-sdk-python"

echo "=== Universal Agent SDK Migration ==="

# Step 1: Create target directory
echo "Step 1: Creating target directory..."
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

# Step 2: Initialize git
echo "Step 2: Initializing git repository..."
git init

# Step 3: Create directory structure
echo "Step 3: Creating directory structure..."
mkdir -p src/universal_agent_sdk
mkdir -p tests
mkdir -p examples
mkdir -p docs
mkdir -p .github/workflows

# Step 4: Copy source code
echo "Step 4: Copying source code..."
cp -r "$SOURCE_DIR/src/universal_agent_sdk/"* src/universal_agent_sdk/

# Step 5: Copy examples
echo "Step 5: Copying examples..."
cp "$SOURCE_DIR/examples/universal_"*.py examples/ 2>/dev/null || true

# Step 6: Copy documentation
echo "Step 6: Copying documentation..."
cp -r "$SOURCE_DIR/docs/universal-sdk/"* docs/

# Step 7: Create pyproject.toml (manual step - see above)
echo "Step 7: Creating pyproject.toml..."
# Create pyproject.toml with content from Phase 3.1

# Step 8: Create other config files
echo "Step 8: Creating configuration files..."
# Create .gitignore, README.md, etc.

# Step 9: Verify installation
echo "Step 9: Verifying installation..."
pip install -e ".[dev]"

# Step 10: Run tests
echo "Step 10: Running tests..."
ruff check src/ || true
mypy src/ || true
pytest tests/ || true

echo "=== Migration Complete ==="
echo "Target directory: $TARGET_DIR"
echo ""
echo "Next steps:"
echo "1. Review and update pyproject.toml"
echo "2. Update README.md with correct URLs"
echo "3. Set up GitHub repository"
echo "4. Configure secrets for PyPI publishing"
echo "5. Create initial release"
```

## Summary

### Files to Migrate

| Category | Files | Status |
|----------|-------|--------|
| Core | client.py, query.py, types.py, config.py, errors.py | Required |
| Providers | providers/*.py | Required |
| Tools | tools/**/*.py | Required |
| Skills | skills/**/*.py | Required |
| Agents | agents/*.py | Required |
| Memory | memory/*.py | Required |
| Examples | universal_*.py | Required |
| Docs | docs/universal-sdk/*.md | Required |
| Tests | test_universal_*.py | Required |

### Dependencies

| Dependency | Version | Required |
|------------|---------|----------|
| anthropic | >=0.20.0 | Yes |
| httpx | >=0.25.0 | Yes |
| pydantic | >=2.0.0 | Yes |
| python-dotenv | >=1.0.0 | Yes |
| openai | >=1.0.0 | Optional |
| google-generativeai | >=0.3.0 | Optional |
| ollama | >=0.1.0 | Optional |

### Timeline Estimate

| Phase | Tasks | Files |
|-------|-------|-------|
| Phase 1 | Repository Setup | ~10 |
| Phase 2 | Source Migration | ~50+ |
| Phase 3 | Configuration | ~5 |
| Phase 4 | Test Migration | ~10 |
| Phase 5 | CI/CD Setup | ~3 |
| Phase 6 | Finalization | ~5 |

### Post-Migration Tasks

1. **GitHub Repository**
   - Create new repository
   - Push initial code
   - Set up branch protection

2. **PyPI Setup**
   - Reserve package name
   - Configure API token
   - Test publish to TestPyPI

3. **Documentation**
   - Set up GitHub Pages or ReadTheDocs
   - Add badges to README

4. **Deprecation Notice**
   - Add notice to claude-agent-sdk about migration
   - Update import paths in original repo
