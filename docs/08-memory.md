# Memory System

The Memory system enables agents to retain information across conversations and sessions. This includes conversation memory, persistent storage, and the Memory Tool for file-based memory.

## Memory Types

| Type | Persistence | Use Case |
|------|-------------|----------|
| Conversation Memory | Session only | Short-term context |
| Persistent Memory | Across sessions | Long-term storage |
| Memory Tool | File-based | User-accessible notes |

## Conversation Memory

Manages conversation history within a session:

```python
from universal_agent_sdk import UniversalAgentClient

async with UniversalAgentClient() as client:
    # Messages are automatically stored
    await client.send("My name is Alice")
    async for _ in client.receive():
        pass

    # Context is preserved
    await client.send("What's my name?")
    async for msg in client.receive():
        print(msg)  # Will remember "Alice"

    # Access conversation history
    for msg in client.messages:
        print(f"{type(msg).__name__}: {msg.content}")

    # Clear history (keeps system prompt)
    client.clear_history()
```

### ConversationMemory Class

```python
from universal_agent_sdk import ConversationMemory

memory = ConversationMemory()

# Add messages
message_id = await memory.add(
    content="User said hello",
    metadata={"role": "user", "timestamp": "2024-01-01"},
)

# Retrieve by ID
entry = await memory.get(message_id)
print(entry.content)  # "User said hello"

# Search memory
results = await memory.search(
    query="hello",
    limit=10,
)
for result in results:
    print(f"Score: {result.score}, Content: {result.entry.content}")

# Delete entry
await memory.delete(message_id)

# Clear all
await memory.clear()
```

## Persistent Memory

For storage that survives across sessions:

```python
from universal_agent_sdk import PersistentMemory

# Create with storage path
memory = PersistentMemory(storage_path="./memory_store")

# Add with metadata
entry_id = await memory.add(
    content="Important fact: The project uses Python 3.11",
    metadata={
        "category": "project_info",
        "importance": "high",
    },
)

# Retrieve later (even after restart)
entry = await memory.get(entry_id)

# Search across all stored memories
results = await memory.search("Python version")
```

### Memory Entry Structure

```python
from universal_agent_sdk import MemoryEntry

entry = MemoryEntry(
    id="mem_123",
    content="The content to remember",
    metadata={
        "category": "notes",
        "tags": ["python", "setup"],
    },
    embedding=None,  # Optional vector embedding
    timestamp="2024-01-01T00:00:00Z",
)
```

### Search Results

```python
from universal_agent_sdk import MemorySearchResult

# Search returns scored results
results: list[MemorySearchResult] = await memory.search("query")

for result in results:
    print(f"ID: {result.entry.id}")
    print(f"Content: {result.entry.content}")
    print(f"Score: {result.score}")  # Relevance score
```

## Memory Tool

The Memory Tool provides file-based memory following Anthropic's specification. It allows agents to create, read, update, and delete notes in a structured way.

### FileSystemMemoryTool

```python
from universal_agent_sdk import FileSystemMemoryTool, AgentOptions

# Create memory tool with storage directory
memory_tool = FileSystemMemoryTool(memory_dir="./memories")

options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    tools=[memory_tool.to_tool_definition()],
    system_prompt="""You have a memory tool to store notes.
Use it to remember important information across conversations.""",
)
```

### Memory Tool Operations

The Memory Tool supports these operations:

#### View

View directory contents or file:

```python
# View directory
result = await memory_tool.view(MemoryViewCommand(path="/"))

# View file with line range
result = await memory_tool.view(MemoryViewCommand(
    path="/notes/project.md",
    view_range=[1, 50],  # Lines 1-50
))
```

#### Create

Create a new file:

```python
result = await memory_tool.create(MemoryCreateCommand(
    path="/notes/project.md",
    file_text="""# Project Notes

## Setup
- Python 3.11 required
- Use virtual environment

## Key Decisions
- Using FastAPI for backend
""",
))
```

#### String Replace

Edit file with string replacement:

```python
result = await memory_tool.str_replace(MemoryStrReplaceCommand(
    path="/notes/project.md",
    old_str="Python 3.11 required",
    new_str="Python 3.12 required",
))
```

#### Insert

Insert text at a specific line:

```python
result = await memory_tool.insert(MemoryInsertCommand(
    path="/notes/project.md",
    insert_line=10,
    insert_text="- New item to remember\n",
))
```

#### Delete

Delete a file or directory:

```python
result = await memory_tool.delete(MemoryDeleteCommand(
    path="/notes/old_notes.md",
))
```

#### Rename

Rename or move a file:

```python
result = await memory_tool.rename(MemoryRenameCommand(
    old_path="/notes/draft.md",
    new_path="/notes/final.md",
))
```

### Memory Tool Configuration

```python
memory_tool = FileSystemMemoryTool(
    memory_dir="./memories",      # Storage directory
    max_depth=2,                  # Max directory depth
    max_line_limit=999999,        # Max lines to read
)
```

## Using Memory with Agents

### Example: Note-Taking Agent

```python
from universal_agent_sdk import (
    query,
    AgentOptions,
    FileSystemMemoryTool,
)

memory_tool = FileSystemMemoryTool(memory_dir="./agent_notes")

options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    tools=[memory_tool.to_tool_definition()],
    system_prompt="""You are a helpful assistant with memory capabilities.

Use your memory tool to:
- Store important information the user shares
- Recall information when asked
- Organize notes by topic

Memory structure:
/notes/ - General notes
/projects/ - Project-specific information
/people/ - Information about people
""",
)

async for msg in query(
    "Remember that my favorite color is blue and I'm working on a Python project called DataFlow",
    options,
):
    print(msg)
```

### Example: Project Context Agent

```python
options = AgentOptions(
    provider="anthropic",
    tools=[memory_tool.to_tool_definition()],
    system_prompt="""You are a project assistant.

At the start of each session:
1. Check /context/project.md for project details
2. Review /context/recent.md for recent work

When learning new information:
1. Update relevant context files
2. Keep notes organized and concise

Context structure:
/context/
  project.md - Project overview
  recent.md - Recent activities
  decisions.md - Key decisions
/tasks/
  active.md - Current tasks
  completed.md - Done tasks
""",
)
```

## Memory Patterns

### Pattern 1: Session Summary

Summarize sessions for future reference:

```python
async def save_session_summary(client, memory_tool):
    """Save a summary of the current session."""
    # Get conversation text
    conversation = "\n".join([
        f"{type(m).__name__}: {m.content}"
        for m in client.messages
    ])

    # Ask agent to summarize
    await client.send(f"""Summarize this conversation and save it to memory:

{conversation}

Save to /sessions/session_{datetime.now().strftime('%Y%m%d_%H%M')}.md
""")

    async for _ in client.receive():
        pass
```

### Pattern 2: Learning Memory

Agent learns and remembers preferences:

```python
options = AgentOptions(
    tools=[memory_tool.to_tool_definition()],
    system_prompt="""You are a personalized assistant.

When the user expresses a preference:
1. Note it in /preferences/user_prefs.md
2. Apply it in future interactions

Example preferences to track:
- Communication style (formal/casual)
- Technical level (beginner/expert)
- Topics of interest
- Formatting preferences
""",
)
```

### Pattern 3: Knowledge Base

Build a searchable knowledge base:

```python
options = AgentOptions(
    tools=[
        memory_tool.to_tool_definition(),
        GrepTool().to_tool_definition(),  # For searching
    ],
    system_prompt="""You manage a knowledge base.

Structure:
/kb/
  concepts/ - Concept explanations
  howto/ - How-to guides
  reference/ - Quick reference

When adding knowledge:
1. Check if related entries exist
2. Link related topics
3. Use clear headings and formatting
""",
)
```

## BaseMemory Interface

Create custom memory implementations:

```python
from universal_agent_sdk import BaseMemory, MemoryEntry, MemorySearchResult

class RedisMemory(BaseMemory):
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)

    async def add(
        self,
        content: str,
        metadata: dict | None = None,
    ) -> str:
        entry_id = str(uuid.uuid4())
        # Store in Redis
        await self.redis.set(f"memory:{entry_id}", json.dumps({
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }))
        return entry_id

    async def get(self, entry_id: str) -> MemoryEntry | None:
        data = await self.redis.get(f"memory:{entry_id}")
        if data:
            parsed = json.loads(data)
            return MemoryEntry(
                id=entry_id,
                content=parsed["content"],
                metadata=parsed["metadata"],
                timestamp=parsed["timestamp"],
            )
        return None

    async def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[MemorySearchResult]:
        # Implement search logic
        pass

    async def delete(self, entry_id: str) -> bool:
        result = await self.redis.delete(f"memory:{entry_id}")
        return result > 0

    async def clear(self) -> None:
        # Clear all memory entries
        keys = await self.redis.keys("memory:*")
        if keys:
            await self.redis.delete(*keys)
```

## Memory Configuration in AgentOptions

```python
options = AgentOptions(
    # Enable memory
    memory_enabled=True,

    # Memory type
    memory_type="conversation",  # or "vector", "persistent"

    # Memory configuration
    memory_config={
        "storage_path": "./memories",
        "max_entries": 1000,
        "embedding_model": "text-embedding-3-small",
    },
)
```

## Best Practices

### 1. Structure Your Memory

```
/memories/
├── context/          # Persistent context
│   ├── user.md      # User information
│   └── project.md   # Project details
├── notes/           # General notes
│   └── meetings/    # Meeting notes
├── tasks/           # Task tracking
│   ├── active.md
│   └── archive/
└── knowledge/       # Reference knowledge
    └── concepts/
```

### 2. Keep Entries Focused

```python
# Good: Focused entry
await memory.add(
    content="User prefers TypeScript over JavaScript",
    metadata={"category": "preferences", "topic": "languages"},
)

# Avoid: Too broad
await memory.add(
    content="User said many things about programming...",
    metadata={"category": "general"},
)
```

### 3. Use Metadata for Organization

```python
await memory.add(
    content="Project deadline is March 15",
    metadata={
        "category": "project",
        "type": "deadline",
        "project": "DataFlow",
        "importance": "high",
    },
)
```

### 4. Clean Up Old Memory

```python
# Remove outdated entries
old_entries = await memory.search("TODO", limit=100)
for result in old_entries:
    if is_completed(result.entry):
        await memory.delete(result.entry.id)
```

### 5. Provide Clear Instructions

```python
options = AgentOptions(
    system_prompt="""You have memory capabilities.

SAVING: Save important facts, preferences, and context.
RETRIEVING: Check memory before answering questions.
UPDATING: Keep memory current and remove outdated info.

Always explain when you're using memory.""",
)
```

## Next Steps

- [API Reference](./09-api-reference.md) - Complete API documentation
- [Migration Guide](./10-migration-guide.md) - Migrate existing code
