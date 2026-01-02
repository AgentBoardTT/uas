# Agents System

The Agents system allows you to create named, reusable agent configurations with specific capabilities. Agents can be organized into hierarchies with sub-agents for complex task delegation.

## What is an Agent?

An Agent is a named configuration that includes:
- **Name**: Unique identifier
- **Description**: What the agent does
- **System Prompt**: Agent instructions
- **Tools**: Available capabilities
- **Model**: LLM model to use
- **Provider**: Which LLM provider
- **Max Turns**: Execution limits

## Creating Agents

### AgentDefinition

The simplest way to define an agent:

```python
from universal_agent_sdk import AgentDefinition

code_reviewer = AgentDefinition(
    name="code-reviewer",
    description="Reviews code for best practices and potential issues",
    system_prompt="""You are a code reviewer. Analyze code for:
- Bugs and logic errors
- Security vulnerabilities
- Performance issues
- Best practice violations

Provide constructive, actionable feedback.""",
    tools=["read_file", "search_code", "analyze_code"],
    model="claude-sonnet-4-20250514",
    max_turns=5,
)
```

### Agent Class

For more control, use the `Agent` class:

```python
from universal_agent_sdk import Agent, ReadTool, GrepTool

class CodeReviewerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="code_reviewer",
            description="Expert code reviewer",
            system_prompt="You review code thoroughly...",
            tools=[
                ReadTool().to_tool_definition(),
                GrepTool().to_tool_definition(),
            ],
            model="claude-sonnet-4-20250514",
            provider="anthropic",
            max_turns=10,
        )

# Create instance
agent = CodeReviewerAgent()

# Access definition
definition = agent.definition
```

## Using Agents with AgentOptions

```python
from universal_agent_sdk import AgentOptions, query

# Define agents
code_reviewer = AgentDefinition(
    name="code-reviewer",
    description="Reviews code",
    system_prompt="You are a code reviewer...",
    model="claude-sonnet-4-20250514",
)

doc_writer = AgentDefinition(
    name="doc-writer",
    description="Writes documentation",
    system_prompt="You are a documentation expert...",
    model="claude-sonnet-4-20250514",
)

# Use agents in options
options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    agents={
        "code-reviewer": code_reviewer,
        "doc-writer": doc_writer,
    },
    system_prompt=code_reviewer.system_prompt,  # Use one agent's prompt
    max_turns=5,
)

async for msg in query("Review this code: ...", options):
    print(msg)
```

## Agent Registry

Manage collections of agents:

```python
from universal_agent_sdk import AgentRegistry, Agent

# Create registry
registry = AgentRegistry()

# Register agents
registry.register(code_reviewer_agent)
registry.register(doc_writer_agent)

# Retrieve agent
agent = registry.get("code_reviewer")

# Check existence
if registry.has("code_reviewer"):
    print("Agent exists")

# List all agents
print(registry.list())  # ["code_reviewer", "doc_writer"]

# Get all agents
all_agents = registry.get_all()  # List[Agent]

# Get definitions dict
definitions = registry.get_definitions()  # Dict[str, AgentDefinition]

# Unregister
registry.unregister("code_reviewer")

# Clear all
registry.clear()
```

### Global Registry

```python
from universal_agent_sdk import AgentRegistry

# Register globally
AgentRegistry.register_global(my_agent)

# Access globally
agent = AgentRegistry.get_global("my_agent")
all_agents = AgentRegistry.list_global()
```

## Loading Agents from Files

### YAML Format

```yaml
# agents.yaml
code_reviewer:
  name: code_reviewer
  description: Reviews code for quality
  system_prompt: |
    You are an expert code reviewer.
    Focus on bugs, security, and performance.
  model: claude-sonnet-4-20250514
  provider: anthropic
  max_turns: 5

doc_writer:
  name: doc_writer
  description: Writes technical documentation
  system_prompt: |
    You are a documentation expert.
    Write clear, comprehensive docs.
  model: claude-sonnet-4-20250514
```

```python
registry = AgentRegistry()
registry.load_from_file("agents.yaml")

agent = registry.get("code_reviewer")
```

### JSON Format

```json
{
  "code_reviewer": {
    "name": "code_reviewer",
    "description": "Reviews code",
    "system_prompt": "You are a code reviewer...",
    "model": "claude-sonnet-4-20250514"
  }
}
```

### Directory Loading

```python
# Load all YAML/JSON files from directory
registry.load_from_directory("./agents/")
```

## SubAgents

SubAgents are specialized agents that can be spawned by a parent agent for subtasks:

```python
from universal_agent_sdk import Agent, SubAgent

# Parent agent
main_agent = Agent(
    name="main_agent",
    description="Orchestrates development tasks",
    system_prompt="You coordinate development work...",
)

# Sub-agent for testing
test_agent = SubAgent(
    name="test_agent",
    description="Writes and runs tests",
    system_prompt="You are a testing expert...",
    parent=main_agent,
    inherit_tools=True,   # Get parent's tools
    inherit_context=True, # Get conversation context
)

# Sub-agent for documentation
doc_agent = SubAgent(
    name="doc_agent",
    description="Writes documentation",
    system_prompt="You document code...",
    parent=main_agent,
    inherit_tools=False,  # Use own tools only
    inherit_context=True,
)
```

### SubAgent Inheritance

```python
# Parent has these tools
parent = Agent(
    name="parent",
    tools=[read_tool, write_tool, bash_tool],
)

# Child inherits tools
child = SubAgent(
    name="child",
    parent=parent,
    inherit_tools=True,
    tools=[grep_tool],  # Also add specific tools
)

# Child will have: read, write, bash, grep
```

## Agent Patterns

### Orchestrator Pattern

One agent coordinates multiple specialized agents:

```python
orchestrator = AgentDefinition(
    name="orchestrator",
    description="Coordinates development tasks",
    system_prompt="""You are a development orchestrator.
You have access to specialized agents:
- code_reviewer: For code review tasks
- test_writer: For writing tests
- doc_writer: For documentation

Delegate tasks to appropriate agents.""",
)

code_reviewer = AgentDefinition(
    name="code_reviewer",
    description="Reviews code",
    system_prompt="You review code for quality...",
)

test_writer = AgentDefinition(
    name="test_writer",
    description="Writes tests",
    system_prompt="You write comprehensive tests...",
)

options = AgentOptions(
    agents={
        "orchestrator": orchestrator,
        "code_reviewer": code_reviewer,
        "test_writer": test_writer,
    },
    system_prompt=orchestrator.system_prompt,
)
```

### Expert Panel Pattern

Multiple agents collaborate on a problem:

```python
security_expert = AgentDefinition(
    name="security_expert",
    description="Security analysis",
    system_prompt="You analyze security implications...",
)

performance_expert = AgentDefinition(
    name="performance_expert",
    description="Performance analysis",
    system_prompt="You analyze performance characteristics...",
)

architecture_expert = AgentDefinition(
    name="architecture_expert",
    description="Architecture review",
    system_prompt="You evaluate architectural decisions...",
)

# Combine expertise
options = AgentOptions(
    agents={
        "security": security_expert,
        "performance": performance_expert,
        "architecture": architecture_expert,
    },
    system_prompt="""You coordinate a panel of experts:
- security_expert: Security analysis
- performance_expert: Performance analysis
- architecture_expert: Architectural review

Consult each expert as needed.""",
)
```

### Specialist Pipeline Pattern

Agents work in sequence:

```python
# Stage 1: Analysis
analyzer = AgentDefinition(
    name="analyzer",
    description="Analyzes requirements",
    system_prompt="You analyze and break down requirements...",
)

# Stage 2: Implementation
implementer = AgentDefinition(
    name="implementer",
    description="Implements solutions",
    system_prompt="You implement code solutions...",
)

# Stage 3: Testing
tester = AgentDefinition(
    name="tester",
    description="Tests implementations",
    system_prompt="You write and run tests...",
)

# Stage 4: Documentation
documenter = AgentDefinition(
    name="documenter",
    description="Documents code",
    system_prompt="You write documentation...",
)
```

## Agent Configuration Options

```python
agent = AgentDefinition(
    # Required
    name="my_agent",

    # Optional with defaults
    description="",                    # Agent description
    system_prompt="",                  # Instructions
    tools=[],                          # Tool names or definitions
    model="claude-sonnet-4-20250514",  # Default model
    provider="anthropic",              # Default provider
    max_turns=10,                      # Max execution turns
)
```

## Multi-Provider Agents

Different agents can use different providers:

```python
claude_agent = AgentDefinition(
    name="claude_agent",
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    system_prompt="You use Claude's capabilities...",
)

gpt_agent = AgentDefinition(
    name="gpt_agent",
    provider="openai",
    model="gpt-4o",
    system_prompt="You use GPT-4's capabilities...",
)

options = AgentOptions(
    provider="anthropic",  # Default
    agents={
        "claude": claude_agent,
        "gpt": gpt_agent,
    },
)
```

## Best Practices

### 1. Clear Agent Boundaries

```python
# Good: Focused agent
test_writer = AgentDefinition(
    name="test_writer",
    description="Writes unit and integration tests",
    system_prompt="""You are a testing expert.
Focus on:
- Unit tests for individual functions
- Integration tests for workflows
- Edge cases and error conditions""",
)

# Avoid: Vague agent
helper = AgentDefinition(
    name="helper",
    description="Helps with stuff",  # Too vague
    system_prompt="You help with things",
)
```

### 2. Appropriate Tool Sets

```python
# Give agents only the tools they need
read_only_agent = AgentDefinition(
    name="analyzer",
    tools=["read_file", "grep", "glob"],  # Read-only tools
)

write_agent = AgentDefinition(
    name="implementer",
    tools=["read_file", "write_file", "edit_file", "bash"],
)
```

### 3. Limit Max Turns

```python
# Prevent runaway execution
agent = AgentDefinition(
    name="bounded_agent",
    max_turns=5,  # Reasonable limit
)
```

### 4. Descriptive Names

```python
# Good: Descriptive names
security_auditor = AgentDefinition(name="security_auditor")
performance_optimizer = AgentDefinition(name="performance_optimizer")

# Avoid: Generic names
agent1 = AgentDefinition(name="agent1")
worker = AgentDefinition(name="worker")
```

### 5. Version Your Agents

```python
agent_v1 = AgentDefinition(
    name="code_reviewer_v1",
    description="Code reviewer version 1.0",
)

agent_v2 = AgentDefinition(
    name="code_reviewer_v2",
    description="Code reviewer version 2.0 - with security focus",
)
```

## Next Steps

- [Memory System](./08-memory.md) - Add memory to agents
- [API Reference](./09-api-reference.md) - Complete API documentation
- [Migration Guide](./10-migration-guide.md) - Migrate existing code
