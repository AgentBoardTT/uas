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

```markdown
# Skill Name

Brief description of what the skill does.

## System Prompt

The full system prompt for the skill goes here.
Can be multiple paragraphs.

## Metadata

- version: 1.0.0
- author: Your Name
- tags: tag1, tag2, tag3
- allowed_tools: Tool1, Tool2

## Tools

List of tools this skill uses:
- ReadTool
- WriteTool
- CustomTool

## Examples

Optional examples of how to use the skill.
```

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

The SDK provides a Skill tool that allows the agent to invoke skills:

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
