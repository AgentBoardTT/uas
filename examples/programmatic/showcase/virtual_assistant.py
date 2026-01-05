#!/usr/bin/env python3
"""Virtual Assistant - A smart AI assistant with multiple capabilities.

This assistant can help with:
- Date/time queries
- Calculations and math
- Weather information
- Web searches
- File operations (read, write, list)
- Running shell commands
- Taking notes and reminders
- General knowledge questions
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    StreamEvent,
    TextBlock,
    UniversalAgentClient,
    tool,
)

# ============================================================================
# Tools for the Virtual Assistant
# ============================================================================


@tool
def get_current_datetime() -> str:
    """Get the current date and time.

    Returns the current date, time, day of week, and timezone.
    """
    now = datetime.now()
    return json.dumps({
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p"),
        "timestamp": now.timestamp(),
    })


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Args:
        expression: A mathematical expression to evaluate (e.g., "2 + 2", "sqrt(16)", "sin(3.14)")

    Supports: +, -, *, /, **, sqrt, sin, cos, tan, log, abs, round, min, max
    """
    import math

    # Safe math functions
    safe_dict = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
    }

    try:
        # Remove any potentially dangerous characters
        cleaned = "".join(c for c in expression if c in "0123456789.+-*/() ,sincotaqrlgexpumd")
        result = eval(cleaned, {"__builtins__": {}}, safe_dict)
        return json.dumps({"expression": expression, "result": result})
    except Exception as e:
        return json.dumps({"error": str(e), "expression": expression})


@tool
def get_weather(city: str) -> str:
    """Get current weather information for a city.

    Args:
        city: The city name to get weather for

    Note: This is a simulated weather service. In production, connect to a real API.
    """
    import random

    # Simulated weather data
    conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Clear"]
    condition = random.choice(conditions)
    temp_c = random.randint(10, 30)
    temp_f = int(temp_c * 9 / 5 + 32)
    humidity = random.randint(40, 80)

    return json.dumps({
        "city": city,
        "condition": condition,
        "temperature_celsius": temp_c,
        "temperature_fahrenheit": temp_f,
        "humidity_percent": humidity,
        "note": "Simulated data - connect to real weather API for production use",
    })


@tool
def web_search(query: str) -> str:
    """Search the web for information.

    Args:
        query: The search query

    Note: This is a simulated search. In production, connect to a real search API.
    """
    return json.dumps({
        "query": query,
        "note": "Web search simulation - in production, connect to a search API like Google, Bing, or DuckDuckGo",
        "suggestion": "I can help answer general knowledge questions from my training data instead.",
    })


@tool
def read_file(file_path: str) -> str:
    """Read the contents of a file.

    Args:
        file_path: Path to the file to read
    """
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            return json.dumps({"error": f"File not found: {file_path}"})
        if not path.is_file():
            return json.dumps({"error": f"Not a file: {file_path}"})

        content = path.read_text()
        return json.dumps({
            "file": str(path),
            "size_bytes": path.stat().st_size,
            "content": content[:10000] + ("..." if len(content) > 10000 else ""),
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file.

    Args:
        file_path: Path to the file to write
        content: Content to write to the file
    """
    try:
        path = Path(file_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return json.dumps({
            "success": True,
            "file": str(path),
            "size_bytes": len(content),
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def list_directory(directory: str = ".") -> str:
    """List files and directories in a given path.

    Args:
        directory: Path to the directory to list (default: current directory)
    """
    try:
        path = Path(directory).expanduser()
        if not path.exists():
            return json.dumps({"error": f"Directory not found: {directory}"})
        if not path.is_dir():
            return json.dumps({"error": f"Not a directory: {directory}"})

        items = []
        for item in sorted(path.iterdir()):
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })

        return json.dumps({
            "directory": str(path.absolute()),
            "items": items[:100],  # Limit to 100 items
            "total_count": len(list(path.iterdir())),
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def run_command(command: str) -> str:
    """Run a shell command and return the output.

    Args:
        command: The shell command to execute

    Note: Be careful with commands that modify the system.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd(),
        )
        return json.dumps({
            "command": command,
            "stdout": result.stdout[:5000] if result.stdout else "",
            "stderr": result.stderr[:1000] if result.stderr else "",
            "return_code": result.returncode,
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Command timed out after 30 seconds"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# Notes storage (in-memory for this session)
_notes: list[dict] = []


@tool
def add_note(title: str, content: str) -> str:
    """Add a note or reminder.

    Args:
        title: Title of the note
        content: Content of the note
    """
    note = {
        "id": len(_notes) + 1,
        "title": title,
        "content": content,
        "created_at": datetime.now().isoformat(),
    }
    _notes.append(note)
    return json.dumps({"success": True, "note": note})


@tool
def list_notes() -> str:
    """List all saved notes."""
    return json.dumps({
        "notes": _notes,
        "count": len(_notes),
    })


@tool
def delete_note(note_id: int) -> str:
    """Delete a note by its ID.

    Args:
        note_id: The ID of the note to delete
    """
    global _notes
    original_count = len(_notes)
    _notes = [n for n in _notes if n["id"] != note_id]

    if len(_notes) < original_count:
        return json.dumps({"success": True, "message": f"Note {note_id} deleted"})
    else:
        return json.dumps({"error": f"Note {note_id} not found"})


@tool
def set_timer(seconds: int, message: str = "Timer complete!") -> str:
    """Set a timer (note: this is non-blocking, just records the timer).

    Args:
        seconds: Number of seconds for the timer
        message: Message to display when timer completes
    """
    end_time = datetime.now().timestamp() + seconds
    return json.dumps({
        "timer_set": True,
        "duration_seconds": seconds,
        "message": message,
        "ends_at": datetime.fromtimestamp(end_time).strftime("%H:%M:%S"),
        "note": "Timer recorded. In a full implementation, this would trigger a notification.",
    })


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are a helpful, smart, and friendly virtual assistant. Your name is Atlas.

Your capabilities include:
- **Date & Time**: Get current date, time, day of week
- **Calculations**: Perform mathematical calculations (basic math, trigonometry, logarithms)
- **Weather**: Check weather for any city (simulated data)
- **File Operations**: Read, write, and list files and directories
- **Shell Commands**: Execute shell commands when needed
- **Notes**: Save, list, and delete notes/reminders
- **Timers**: Set timers with custom messages
- **General Knowledge**: Answer questions using your training knowledge

Guidelines:
1. Be concise but thorough in your responses
2. Use tools when they would provide accurate, real-time information
3. For general knowledge questions, you can answer directly from your training
4. Always be helpful, friendly, and professional
5. If you're unsure about something, say so
6. When performing file operations or commands, confirm what you're about to do
7. Format responses nicely with markdown when appropriate

You're running on the user's local machine, so you can help with local files and commands.
The current working directory is available via the list_directory tool.
"""

# ============================================================================
# Main Chat Loop
# ============================================================================


async def virtual_assistant():
    """Run the virtual assistant."""
    print()
    print("=" * 70)
    print("  ATLAS - Your Virtual Assistant")
    print("=" * 70)
    print()
    print("  I can help you with:")
    print("    - Date/time queries        - Weather information")
    print("    - Math calculations        - File operations")
    print("    - Running commands         - Taking notes")
    print("    - General questions        - And much more!")
    print()
    print("  Type 'quit' or 'exit' to end the conversation.")
    print("=" * 70)
    print()

    # Configure the assistant with tools
    options = AgentOptions(
        provider="claude",
        model="claude-sonnet-4-20250514",
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_current_datetime.definition,
            calculate.definition,
            get_weather.definition,
            web_search.definition,
            read_file.definition,
            write_file.definition,
            list_directory.definition,
            run_command.definition,
            add_note.definition,
            list_notes.definition,
            delete_note.definition,
            set_timer.definition,
        ],
        stream=True,
        max_turns=10,
    )

    async with UniversalAgentClient(options) as client:
        # Initial greeting
        print("Atlas: Hello! I'm Atlas, your virtual assistant. How can I help you today?\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nAtlas: Goodbye! Have a great day!")
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q", "bye", "goodbye"):
                print("\nAtlas: Goodbye! Have a great day!")
                break

            await client.send(user_input)

            print("\nAtlas: ", end="", flush=True)

            tool_calls_made = []

            async for msg in client.receive():
                if isinstance(msg, StreamEvent):
                    # Print streaming text
                    if msg.delta and msg.delta.get("type") == "text_delta":
                        print(msg.delta.get("text", ""), end="", flush=True)
                    # Track tool calls for display
                    elif msg.delta and msg.delta.get("type") == "tool_use":
                        tool_name = msg.delta.get("name", "")
                        if tool_name and tool_name not in tool_calls_made:
                            tool_calls_made.append(tool_name)

                elif isinstance(msg, AssistantMessage):
                    # Check if there's text content we haven't streamed
                    pass

            print("\n")


if __name__ == "__main__":
    asyncio.run(virtual_assistant())
