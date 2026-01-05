# Skills System

Skills are reusable, composable agent configurations that combine system prompts, tools, and settings into cohesive capabilities. They allow you to create specialized agents for specific tasks.

## What is a Skill?

A Skill packages together:
- **System prompt**: Instructions for the agent
- **Tools**: Capabilities available to the skill
- **Settings**: Temperature, max tokens, etc.
- **Metadata**: Version, author, tags

## Creating Skills

### Programmatic Creation

```python
from universal_agent_sdk import Skill, ToolDefinition

# Create a skill
code_reviewer = Skill(
    name="code_reviewer",
    description="Reviews code for bugs, security issues, and best practices",
    system_prompt="""You are an expert code reviewer. When reviewing code:
1. Look for bugs and logic errors
2. Check for security vulnerabilities
3. Suggest performance improvements
4. Ensure code follows best practices
5. Provide constructive feedback

Be thorough but kind in your feedback.""",
    tools=[],  # Add tool definitions if needed
    temperature=0.3,  # Lower temperature for more focused analysis
    max_tokens=4096,
)
```

### From SKILL.md File

Skills can be defined in markdown files:

```markdown
# Code Reviewer

Expert code review assistant.

## System Prompt

You are an expert code reviewer...

## Metadata

- version: 1.0.0
- author: Your Name
- tags: code, review, quality
- allowed_tools: Read, Grep

## Tools

- ReadTool
- GrepTool
```

Load the skill:

```python
from universal_agent_sdk import Skill

skill = Skill.from_file("./skills/code_reviewer/SKILL.md")
```

## Using Skills

### Convert to AgentOptions

```python
from universal_agent_sdk import query

# Create options from skill
options = code_reviewer.create_options(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
)

async for msg in query("Review this code: ...", options):
    print(msg)
```

### With Additional Configuration

```python
options = code_reviewer.create_options(
    provider="openai",
    model="gpt-4o",
    max_turns=10,
    debug=True,
)
```

## Skill Composition

### Adding Tools to a Skill

```python
from universal_agent_sdk import Skill, ReadTool, GrepTool

# Original skill
base_skill = Skill(
    name="analyzer",
    description="Code analyzer",
    system_prompt="You analyze code...",
)

# Add tools
enhanced = base_skill.with_tools(
    ReadTool().to_tool_definition(),
    GrepTool().to_tool_definition(),
)
```

### Extending Prompts

```python
# Add additional instructions
specialized = base_skill.with_prompt("""

Additionally, focus on:
- Memory safety
- Thread safety
- Error handling
""")
```

### Combining Multiple Skills

```python
from universal_agent_sdk import combine_skills

# Combine skills
full_stack = combine_skills(
    code_reviewer,
    security_auditor,
    performance_analyzer,
    name="full_stack_reviewer",
)

# The combined skill has:
# - Merged system prompts
# - All tools from all skills
# - Averaged temperature
```

## Built-in Skills

The SDK includes several built-in skills:

### Document Processing

```python
from universal_agent_sdk import (
    PDFSkill,
    DocxSkill,
    PPTXSkill,
    XLSXSkill,
)

# PDF processing
pdf_skill = PDFSkill()
options = pdf_skill.create_options()

async for msg in query("Extract key points from this PDF: ...", options):
    print(msg)

# Word documents
docx_skill = DocxSkill()

# PowerPoint
pptx_skill = PPTXSkill()

# Excel
xlsx_skill = XLSXSkill()
```

### Development Skills

```python
from universal_agent_sdk import (
    FrontendDesignSkill,
    WebArtifactsBuilderSkill,
    WebappTestingSkill,
    MCPBuilderSkill,
)

# Frontend development
frontend = FrontendDesignSkill()

# Web artifacts
web_builder = WebArtifactsBuilderSkill()

# Testing
tester = WebappTestingSkill()

# MCP server building
mcp_builder = MCPBuilderSkill()
```

### Creative Skills

```python
from universal_agent_sdk import (
    CanvasDesignSkill,
    AlgorithmicArtSkill,
    ThemeFactorySkill,
    SlackGifCreatorSkill,
)

# Canvas/graphics
canvas = CanvasDesignSkill()

# Algorithmic art
art = AlgorithmicArtSkill()

# Theme creation
themes = ThemeFactorySkill()

# Slack GIFs
gifs = SlackGifCreatorSkill()
```

### Business Skills

```python
from universal_agent_sdk import (
    BrandGuidelinesSkill,
    InternalCommsSkill,
    DocCoauthoringSkill,
)

# Brand guidelines
brand = BrandGuidelinesSkill()

# Internal communications
comms = InternalCommsSkill()

# Document co-authoring
coauthor = DocCoauthoringSkill()
```

### Meta Skills

```python
from universal_agent_sdk import SkillCreatorSkill

# Create new skills
creator = SkillCreatorSkill()

async for msg in query(
    "Create a skill for data analysis with pandas",
    creator.create_options(),
):
    print(msg)
```

## Skill Registry

Manage collections of skills:

```python
from universal_agent_sdk import SkillRegistry, Skill

# Create registry
registry = SkillRegistry()

# Register skills
registry.register(code_reviewer)
registry.register(security_auditor)

# Retrieve skills
skill = registry.get("code_reviewer")

# List all
print(registry.list())  # ["code_reviewer", "security_auditor"]

# Get all skills
all_skills = registry.all()  # dict[str, Skill]

# Clear registry
registry.clear()
```

### Global Registry

```python
from universal_agent_sdk import register_skill, get_skill, list_skills

# Register globally
register_skill(my_skill)

# Retrieve
skill = get_skill("my_skill")

# List all
print(list_skills())
```

## Skill Discovery

Discover skills from the filesystem:

```python
from universal_agent_sdk import discover_skills, list_skills

# Discover from project directory (.claude/skills/)
project_skills = discover_skills(
    setting_sources=["project"],
    project_dir="/path/to/project",
)

# Discover from user directory (~/.claude/skills/)
user_skills = discover_skills(
    setting_sources=["user"],
)

# Discover from both
all_skills = discover_skills(
    setting_sources=["user", "project"],
    project_dir="/path/to/project",
)

for skill in all_skills:
    print(f"{skill.name}: {skill.description}")
```

### Using setting_sources in AgentOptions

```python
from universal_agent_sdk import AgentOptions

options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    setting_sources=["project"],  # Load project skills
    allowed_tools=["Skill"],      # Enable skill invocation
)
```

## Skill File Structure

### Directory Structure

```
.claude/
└── skills/
    ├── code_reviewer/
    │   ├── SKILL.md
    │   └── templates/
    │       └── review_template.md
    ├── data_analyst/
    │   └── SKILL.md
    └── writer/
        └── SKILL.md
```

### SKILL.md Format

Skills use **YAML frontmatter** followed by markdown content:

```markdown
---
name: code-reviewer
description: Reviews code for bugs, security issues, and best practices
allowed-tools:
  - Read
  - Grep
  - Glob
version: "1.0.0"
author: Your Name
tags:
  - code
  - review
  - quality
---

# Code Reviewer

You are an expert code reviewer. When reviewing code:

1. Look for bugs and logic errors
2. Check for security vulnerabilities
3. Suggest performance improvements
4. Ensure code follows best practices

Be thorough but kind in your feedback.

## Guidelines

- Always explain the reasoning behind suggestions
- Prioritize issues by severity
- Provide code examples when helpful
```

#### Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Skill identifier (required) |
| `description` | string | Brief description shown in skill list |
| `allowed-tools` | list | Tools pre-approved for this skill |
| `model` | string | Model override (e.g., `claude-sonnet-4-20250514`) |
| `version` | string | Semantic version |
| `author` | string | Skill author |
| `tags` | list | Categorization tags |

## Loading Skills to Registry

```python
from universal_agent_sdk import SkillRegistry, load_skills_to_registry

registry = SkillRegistry()

# Load from filesystem
count = load_skills_to_registry(
    registry,
    setting_sources=["project"],
    project_dir="/path/to/project",
)

print(f"Loaded {count} skills")
```

## Skill Invocation Tool

The SDK provides a **Skill tool** that allows the agent to dynamically invoke skills at runtime. This is a "meta-tool" that dispatches to individual skills.

### Basic Usage

```python
from universal_agent_sdk import AgentOptions

options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    setting_sources=["project"],
    allowed_tools=["Skill"],  # Enable Skill tool
)

# Now the agent can invoke skills by name
async for msg in query(
    "Use the code_reviewer skill to review this code: ...",
    options,
):
    print(msg)
```

### How the Skill Tool Works

The Skill tool follows a **meta-tool pattern** - it's a single tool that can dispatch to many different skills:

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Runtime                          │
├─────────────────────────────────────────────────────────────┤
│  Tools: [Read, Write, Bash, Skill]                          │
│                              │                              │
│                              ▼                              │
│                    ┌─────────────────┐                      │
│                    │   Skill Tool    │ ◄── Meta-tool        │
│                    │  (dispatcher)   │                      │
│                    └────────┬────────┘                      │
│                             │                               │
│         ┌───────────────────┼───────────────────┐          │
│         ▼                   ▼                   ▼          │
│    ┌─────────┐        ┌─────────┐        ┌─────────┐       │
│    │   pdf   │        │  docx   │        │  xlsx   │       │
│    └─────────┘        └─────────┘        └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

#### 1. Dynamic Description

The Skill tool's description is **dynamically generated** to include all available skills:

```python
from universal_agent_sdk.skills import SkillTool

tool = SkillTool(include_bundled=True)
print(tool.description)
# Contains:
# <available_skills>
# "pdf": "Comprehensive PDF manipulation toolkit..."
# "docx": "Word document processing..."
# ...
# </available_skills>
```

#### 2. Skill Selection

When the agent decides to use a skill, it calls the Skill tool with:

```python
# The agent makes a tool call like:
{
    "name": "Skill",
    "input": {
        "skill": "pdf",           # Which skill to invoke
        "args": "Extract text"    # Optional arguments
    }
}
```

#### 3. Dual-Message Injection

When a skill is invoked, it injects **two messages** into the conversation:

```python
from universal_agent_sdk.skills import SkillMessage

# Message 1: VISIBLE to user (shown in UI)
SkillMessage(
    role="user",
    content='<command-message>The "pdf" skill is loading</command-message>\n'
            '<command-name>pdf</command-name>',
    is_meta=False  # Visible
)

# Message 2: HIDDEN from UI (sent to API only)
SkillMessage(
    role="user",
    content="[Full skill system prompt with instructions...]",
    is_meta=True   # Hidden
)
```

The `is_meta` flag controls visibility:
- `is_meta=False`: Message appears in the UI
- `is_meta=True`: Message is sent to the API but hidden from the user

#### 4. Context Modification

Skills can modify the agent's context for subsequent turns:

```python
from universal_agent_sdk.skills import SkillInvocationResult

result = SkillInvocationResult(
    skill_name="pdf",
    skill_prompt="...",
    messages=[...],

    # Context modifications:
    allowed_tools=["Read", "Write", "Bash"],  # Pre-approve these tools
    model_override="claude-sonnet-4-20250514",       # Switch model if needed
    base_dir="/path/to/skill/directory",      # For {baseDir} substitution
)
```

| Field | Purpose |
|-------|---------|
| `allowed_tools` | Tools pre-approved for this skill (no permission prompts) |
| `model_override` | Use a different model for this skill's execution |
| `base_dir` | Path for `{baseDir}` variable substitution |

### Using SkillTool Programmatically

```python
from universal_agent_sdk.skills import SkillTool, create_skill_tool

# Create with bundled skills
tool = SkillTool(include_bundled=True)

# Or use the convenience function
tool = create_skill_tool(include_bundled=True)

# List available skills
print(tool.list_skills())  # ['pdf', 'docx', 'xlsx', ...]

# Get skill info
skill = tool.get_skill("pdf")
print(skill.description)

# Invoke a skill (returns SkillInvocationResult)
import asyncio
result = asyncio.run(tool(skill="pdf", args="Extract text from report.pdf"))

print(result.skill_name)      # "pdf"
print(result.skill_prompt)    # Full skill prompt
print(result.allowed_tools)   # ["Read", "Write", "Bash"]
print(result.base_dir)        # "/path/to/skills/bundled/pdf"
```

### Adding Custom Skills to SkillTool

```python
from universal_agent_sdk.skills import SkillTool, Skill

# Create empty tool
tool = SkillTool(include_bundled=False, include_registry=False)

# Add custom skill
my_skill = Skill(
    name="data-analyzer",
    description="Analyzes data files and generates reports",
    system_prompt="You are a data analysis expert...",
)
tool.add_skill(my_skill)

# Remove skill
tool.remove_skill("data-analyzer")
```

## Skills with Scripts

Skills can include helper scripts that are executed by the agent. The `{baseDir}` variable provides the path to the skill's directory.

### Directory Structure

```
.claude/skills/
└── pdf-processor/
    ├── SKILL.md
    ├── scripts/
    │   ├── extract_text.py
    │   ├── merge_pdfs.py
    │   └── convert_to_images.py
    └── templates/
        └── report_template.md
```

### Using {baseDir} in Skill Prompts

In your SKILL.md, reference scripts using `{baseDir}`:

```markdown
---
name: pdf-processor
description: Advanced PDF processing with Python scripts
allowed-tools:
  - Read
  - Write
  - Bash
---

# PDF Processor

You can process PDFs using the following scripts:

## Extract Text
```bash
python {baseDir}/scripts/extract_text.py input.pdf output.txt
```

## Merge PDFs
```bash
python {baseDir}/scripts/merge_pdfs.py file1.pdf file2.pdf merged.pdf
```

## Convert to Images
```bash
python {baseDir}/scripts/convert_to_images.py input.pdf output_dir/
```
```

### How {baseDir} Works

When the skill is invoked, `{baseDir}` is replaced with the actual path:

```python
import asyncio
from universal_agent_sdk.skills import SkillTool

tool = SkillTool(include_bundled=True)
result = asyncio.run(tool(skill="pdf"))

print(result.base_dir)
# Output: /home/user/.claude/skills/pdf-processor

# The skill_prompt will have {baseDir} replaced:
# "python /home/user/.claude/skills/pdf-processor/scripts/extract_text.py"
```

### Script Requirements

Scripts in skill directories should:

1. **Be self-contained**: Include all dependencies or use standard library
2. **Handle errors gracefully**: Return meaningful error messages
3. **Accept command-line arguments**: For flexibility
4. **Output to stdout**: For easy capture by the agent

Example script (`scripts/extract_text.py`):

```python
#!/usr/bin/env python3
"""Extract text from a PDF file."""
import sys

def extract_text(pdf_path: str) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        text = []
        for page in reader.pages:
            text.append(page.extract_text())
        return "\n".join(text)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: extract_text.py <pdf_file>", file=sys.stderr)
        sys.exit(1)
    print(extract_text(sys.argv[1]))
```

## Skill Invocation Flow

Here's the complete flow when an agent invokes a skill:

```
1. DISCOVERY
   ├── Load bundled skills from SDK
   ├── Load user skills from ~/.claude/skills/
   └── Load project skills from .claude/skills/

2. SELECTION
   ├── Agent sees Skill tool in available tools
   ├── Description contains <available_skills> list
   └── Agent calls Skill(skill="pdf", args="...")

3. VALIDATION
   ├── Check skill exists
   └── Parse any arguments

4. MESSAGE INJECTION
   ├── Visible message: <command-message>The "pdf" skill is loading</command-message>
   └── Hidden message: [Full skill system prompt] (is_meta=True)

5. CONTEXT MODIFICATION
   ├── Pre-approve tools from allowed_tools
   ├── Apply model_override if specified
   └── Set base_dir for {baseDir} substitution

6. EXECUTION
   ├── Agent receives skill prompt
   ├── Agent uses pre-approved tools
   └── Scripts run via Bash with {baseDir} paths

7. COMPLETION
   └── Skill execution ends when agent completes task
```

## Best Practices

### 1. Single Responsibility

Each skill should focus on one task:

```python
# Good: Focused skill
code_reviewer = Skill(
    name="code_reviewer",
    description="Reviews code for quality and best practices",
    system_prompt="You are a code reviewer...",
)

# Avoid: Too broad
everything_skill = Skill(
    name="everything",
    description="Does everything",
    system_prompt="You can do anything...",  # Too vague
)
```

### 2. Clear System Prompts

```python
skill = Skill(
    name="sql_expert",
    system_prompt="""You are an SQL expert. Your responsibilities:

1. Write efficient SQL queries
2. Optimize existing queries
3. Design database schemas
4. Explain query execution plans

Guidelines:
- Always use parameterized queries
- Prefer explicit JOINs over implicit
- Include comments for complex queries
- Consider indexing implications""",
)
```

### 3. Version Your Skills

```markdown
## Metadata

- version: 2.1.0
- changelog: Added support for PostgreSQL-specific syntax
```

### 4. Include Examples

```python
skill = Skill(
    name="json_transformer",
    system_prompt="""Transform JSON data according to user specifications.

Example:
Input: {"name": "John", "age": 30}
Request: "Add email field with value john@example.com"
Output: {"name": "John", "age": 30, "email": "john@example.com"}
""",
)
```

### 5. Appropriate Temperature

```python
# Analytical tasks: Lower temperature
analyzer = Skill(
    name="analyzer",
    temperature=0.2,  # More focused
)

# Creative tasks: Higher temperature
writer = Skill(
    name="creative_writer",
    temperature=0.8,  # More creative
)
```

## Next Steps

- [Hooks System](./06-hooks.md) - Intercept skill execution
- [Agents System](./07-agents.md) - Create agent hierarchies
- [Memory System](./08-memory.md) - Add persistence to skills
