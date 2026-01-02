# Hooks System

Hooks allow you to intercept and modify agent behavior at key points in the execution lifecycle. Use hooks for logging, security, input validation, and custom logic.

## Hook Events

The SDK supports these hook events:

| Event | When Triggered | Use Cases |
|-------|----------------|-----------|
| `SessionStart` | When a session begins | Initialization, logging |
| `PreToolUse` | Before tool execution | Validation, permission, modification |
| `PostToolUse` | After tool execution | Logging, result modification |
| `PreCompletion` | Before LLM call | Message modification |
| `PostCompletion` | After LLM response | Response processing |
| `OnError` | When an error occurs | Error handling, logging |

## Basic Hook Structure

```python
from universal_agent_sdk.types import HookContext, HookInput, HookOutput

async def my_hook(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Hook function signature.

    Args:
        input_data: Event-specific input data
        tool_use_id: ID of the tool use (if applicable)
        context: Session context with session_id

    Returns:
        HookOutput dict with control instructions
    """
    return {
        "continue_": True,  # Continue execution
    }
```

## Configuring Hooks

```python
from universal_agent_sdk import AgentOptions, HookMatcher

options = AgentOptions(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    hooks={
        "PreToolUse": [
            HookMatcher(
                matcher=None,  # Match all tools
                hooks=[my_pre_tool_hook],
                timeout=10.0,  # Timeout in seconds
            ),
        ],
        "PostToolUse": [
            HookMatcher(
                matcher="read_file",  # Match specific tool
                hooks=[log_read_operations],
            ),
        ],
        "OnError": [
            HookMatcher(
                matcher=None,
                hooks=[error_handler],
            ),
        ],
    },
)
```

## HookMatcher

The `HookMatcher` configures which hooks run for which events:

```python
from universal_agent_sdk import HookMatcher

# Match all tools/events
all_matcher = HookMatcher(
    matcher=None,
    hooks=[hook1, hook2],
)

# Match specific tool name
tool_matcher = HookMatcher(
    matcher="bash",  # Only for bash tool
    hooks=[bash_validator],
)

# With timeout
timed_matcher = HookMatcher(
    matcher=None,
    hooks=[slow_hook],
    timeout=30.0,  # 30 second timeout
)
```

## Hook Input Types

### SessionStart

```python
async def session_start_hook(
    input_data: dict,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Called when session starts."""
    session_id = context.session_id
    print(f"Session started: {session_id}")

    return {"continue_": True}
```

### PreToolUse

```python
async def pre_tool_hook(
    input_data: dict,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Called before tool execution."""
    tool_name = input_data.get("tool_name")
    tool_input = input_data.get("tool_input", {})

    print(f"About to use: {tool_name}")
    print(f"Input: {tool_input}")

    return {"continue_": True}
```

### PostToolUse

```python
async def post_tool_hook(
    input_data: dict,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Called after tool execution."""
    tool_name = input_data.get("tool_name")
    tool_result = input_data.get("tool_result")

    print(f"Tool {tool_name} returned: {tool_result[:100]}...")

    return {"continue_": True}
```

### OnError

```python
async def error_hook(
    input_data: dict,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Called when an error occurs."""
    error = input_data.get("error")
    error_type = input_data.get("error_type")

    print(f"Error ({error_type}): {error}")

    # Log to monitoring system
    await log_error(context.session_id, error)

    return {"continue_": True}
```

## Hook Output

The `HookOutput` dict controls execution flow:

```python
# Continue normally
return {"continue_": True}

# Stop execution
return {
    "continue_": False,
    "stopReason": "validation_failed",
    "reason": "Input validation failed",
}

# Modify tool input (PreToolUse only)
return {
    "continue_": True,
    "modified_input": {
        "path": "/safe/path/file.txt",  # Modified input
    },
}

# Add system message
return {
    "continue_": True,
    "systemMessage": "Additional context for the agent...",
}

# Hook-specific output
return {
    "continue_": True,
    "hookSpecificOutput": {
        "permissionDecision": "allow",
        "permissionDecisionReason": "User approved",
        "additionalContext": "Extra info",
    },
}
```

## Common Hook Patterns

### Logging Hook

```python
import logging
from datetime import datetime

logger = logging.getLogger("agent")

async def logging_hook(
    input_data: dict,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Log all tool usage."""
    timestamp = datetime.now().isoformat()
    tool_name = input_data.get("tool_name", "unknown")

    logger.info(f"[{timestamp}] Session {context.session_id}: {tool_name}")

    return {"continue_": True}

options = AgentOptions(
    hooks={
        "PreToolUse": [HookMatcher(matcher=None, hooks=[logging_hook])],
    },
)
```

### Security Validation Hook

```python
BLOCKED_COMMANDS = ["rm -rf", "sudo", "chmod 777", "> /dev/"]

async def security_hook(
    input_data: dict,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Block dangerous commands."""
    tool_name = input_data.get("tool_name")

    if tool_name == "bash":
        command = input_data.get("tool_input", {}).get("command", "")

        for blocked in BLOCKED_COMMANDS:
            if blocked in command:
                return {
                    "continue_": False,
                    "stopReason": "security_violation",
                    "reason": f"Blocked dangerous pattern: {blocked}",
                }

    return {"continue_": True}

options = AgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="bash", hooks=[security_hook]),
        ],
    },
)
```

### Input Sanitization Hook

```python
import os

async def sanitize_paths_hook(
    input_data: dict,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Sanitize file paths."""
    tool_name = input_data.get("tool_name")
    tool_input = input_data.get("tool_input", {})

    if tool_name in ["read_file", "write_file", "edit_file"]:
        path = tool_input.get("path", "")

        # Resolve to absolute path
        abs_path = os.path.abspath(path)

        # Check allowed directories
        allowed_dirs = ["/tmp/", "/home/user/projects/"]
        if not any(abs_path.startswith(d) for d in allowed_dirs):
            return {
                "continue_": False,
                "reason": f"Path not in allowed directories: {path}",
            }

        # Return sanitized path
        modified = tool_input.copy()
        modified["path"] = abs_path
        return {
            "continue_": True,
            "modified_input": modified,
        }

    return {"continue_": True}
```

### Rate Limiting Hook

```python
from collections import defaultdict
from datetime import datetime, timedelta

call_counts: dict[str, list[datetime]] = defaultdict(list)
RATE_LIMIT = 10  # calls per minute

async def rate_limit_hook(
    input_data: dict,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Rate limit tool calls."""
    session_id = context.session_id
    now = datetime.now()
    cutoff = now - timedelta(minutes=1)

    # Clean old entries
    call_counts[session_id] = [
        t for t in call_counts[session_id] if t > cutoff
    ]

    # Check rate limit
    if len(call_counts[session_id]) >= RATE_LIMIT:
        return {
            "continue_": False,
            "reason": f"Rate limit exceeded: {RATE_LIMIT}/minute",
        }

    # Record call
    call_counts[session_id].append(now)

    return {"continue_": True}
```

### Audit Trail Hook

```python
audit_log: list[dict] = []

async def audit_hook(
    input_data: dict,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Create audit trail."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": context.session_id,
        "tool_use_id": tool_use_id,
        "tool_name": input_data.get("tool_name"),
        "input": input_data.get("tool_input"),
    }

    audit_log.append(entry)

    # Persist to database/file in production
    await save_audit_entry(entry)

    return {"continue_": True}
```

### User Confirmation Hook

```python
async def confirmation_hook(
    input_data: dict,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Require confirmation for sensitive operations."""
    tool_name = input_data.get("tool_name")

    sensitive_tools = ["write_file", "bash", "delete"]

    if tool_name in sensitive_tools:
        # In production, this would prompt the user
        print(f"Confirm {tool_name}? [y/n]")
        response = input().strip().lower()

        if response != "y":
            return {
                "continue_": False,
                "reason": "User declined",
            }

    return {"continue_": True}
```

## Combining Hooks

Multiple hooks run in order:

```python
options = AgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(
                matcher=None,
                hooks=[
                    logging_hook,      # First: log
                    security_hook,     # Second: security check
                    rate_limit_hook,   # Third: rate limit
                    audit_hook,        # Fourth: audit
                ],
            ),
        ],
    },
)
```

If any hook returns `continue_: False`, execution stops.

## Hooks vs Permission Callbacks

Both can control tool execution:

| Feature | Hooks | can_use_tool |
|---------|-------|--------------|
| Timing | Pre/Post/Error | Pre only |
| Session events | Yes | No |
| Input modification | Yes | Yes |
| Multiple handlers | Yes | Single callback |
| Tool matching | Pattern-based | Manual |

**Use hooks when:**
- You need lifecycle events (session start, errors)
- You want pattern-based tool matching
- You need multiple independent handlers

**Use can_use_tool when:**
- You want simple allow/deny logic
- You need to modify inputs
- You want a single point of control

## Combining Hooks with can_use_tool

```python
async def permission_callback(tool_name, input_data, context):
    # Quick allow/deny decisions
    if tool_name == "dangerous_tool":
        return PermissionResultDeny(message="Blocked")
    return PermissionResultAllow()

async def audit_hook(input_data, tool_use_id, context):
    # Detailed logging
    await log_to_audit_system(input_data)
    return {"continue_": True}

options = AgentOptions(
    can_use_tool=permission_callback,  # Quick checks
    hooks={
        "PreToolUse": [
            HookMatcher(matcher=None, hooks=[audit_hook]),  # Logging
        ],
    },
)
```

## Error Handling in Hooks

```python
async def safe_hook(
    input_data: dict,
    tool_use_id: str | None,
    context: HookContext,
) -> HookOutput:
    """Hook with error handling."""
    try:
        # Your hook logic
        result = await process_input(input_data)
        return {"continue_": True}
    except Exception as e:
        # Log error but don't break execution
        logger.error(f"Hook error: {e}")

        # Decide whether to continue
        return {
            "continue_": True,  # Or False to stop
            "hookSpecificOutput": {
                "error": str(e),
            },
        }
```

## Best Practices

1. **Keep hooks fast**: Hooks run synchronously in the execution path
2. **Handle errors gracefully**: Don't let hook errors break the agent
3. **Use timeouts**: Set appropriate timeouts for slow operations
4. **Log everything**: Hooks are ideal for observability
5. **Be specific with matchers**: Target specific tools when possible
6. **Test hooks independently**: Unit test hook logic

## Next Steps

- [Agents System](./07-agents.md) - Create agent hierarchies
- [Memory System](./08-memory.md) - Add persistent memory
- [API Reference](./09-api-reference.md) - Complete API documentation
