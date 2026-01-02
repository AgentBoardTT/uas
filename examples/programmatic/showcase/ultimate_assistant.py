#!/usr/bin/env python3
"""Ultimate Virtual Assistant - A powerful AI assistant with all capabilities.

This assistant includes:
- All built-in tools (Read, Write, Edit, Bash, Glob, Grep, NotebookEdit)
- All bundled skills (PDF, DOCX, PPTX, XLSX, Frontend Design, etc.)
- Persistent memory with FileSystemMemoryTool
- Web search and web crawl capabilities
- Date/time, calculations, weather, notes, timers
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    StreamEvent,
    UniversalAgentClient,
    tool,
)

# Import built-in tools
from universal_agent_sdk.tools import (
    BashTool,
    EditTool,
    FileSystemMemoryTool,
    GlobTool,
    GrepTool,
    NotebookEditTool,
    ReadTool,
    WriteTool,
    get_memory_system_prompt,
)

# Import skills
from universal_agent_sdk.skills import SkillTool

# ============================================================================
# Custom Tools for the Virtual Assistant
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
async def get_weather(city: str) -> str:
    """Get current weather information for a city.

    Args:
        city: The city name to get weather for (e.g., "London", "Tokyo", "New York")

    Returns real-time weather data from wttr.in API.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Use wttr.in API - free, no API key required
            response = await client.get(
                f"https://wttr.in/{city}?format=j1",
                headers={"User-Agent": "curl/7.68.0"},
                timeout=10.0,
            )

            if response.status_code != 200:
                return json.dumps({
                    "error": f"Failed to get weather: HTTP {response.status_code}",
                    "city": city,
                })

            data = response.json()
            current = data.get("current_condition", [{}])[0]
            location = data.get("nearest_area", [{}])[0]

            # Extract location info
            area_name = location.get("areaName", [{}])[0].get("value", city)
            country = location.get("country", [{}])[0].get("value", "")
            region = location.get("region", [{}])[0].get("value", "")

            return json.dumps({
                "city": area_name,
                "region": region,
                "country": country,
                "condition": current.get("weatherDesc", [{}])[0].get("value", "Unknown"),
                "temperature_celsius": int(current.get("temp_C", 0)),
                "temperature_fahrenheit": int(current.get("temp_F", 0)),
                "feels_like_celsius": int(current.get("FeelsLikeC", 0)),
                "feels_like_fahrenheit": int(current.get("FeelsLikeF", 0)),
                "humidity_percent": int(current.get("humidity", 0)),
                "wind_speed_kmh": int(current.get("windspeedKmph", 0)),
                "wind_direction": current.get("winddir16Point", ""),
                "visibility_km": int(current.get("visibility", 0)),
                "uv_index": int(current.get("uvIndex", 0)),
                "observation_time": current.get("observation_time", ""),
            })

    except httpx.TimeoutException:
        return json.dumps({"error": "Request timed out", "city": city})
    except Exception as e:
        return json.dumps({"error": str(e), "city": city})


@tool
async def web_search(query: str, num_results: int = 5) -> str:
    """Search the web for information using DuckDuckGo.

    Args:
        query: The search query
        num_results: Number of results to return (default: 5)

    Returns search results with titles, URLs, and snippets.
    """
    try:
        # Try using duckduckgo-search if available (best option)
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))

            return json.dumps({
                "query": query,
                "results": [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    }
                    for r in results
                ],
                "count": len(results),
            })
        except ImportError:
            pass

        # Fallback: Use DuckDuckGo HTML search and parse results
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query, "b": ""},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                follow_redirects=True,
                timeout=15.0,
            )

            if response.status_code != 200:
                return json.dumps({
                    "error": f"Search failed: HTTP {response.status_code}",
                    "query": query,
                })

            # Try to parse with BeautifulSoup
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(response.text, "html.parser")
                results = []

                # Find all result divs
                for result in soup.select(".result")[:num_results]:
                    title_elem = result.select_one(".result__title a")
                    snippet_elem = result.select_one(".result__snippet")

                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        url = title_elem.get("href", "")
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                        # Clean up DuckDuckGo redirect URL
                        if "uddg=" in url:
                            import urllib.parse
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                            url = parsed.get("uddg", [url])[0]

                        results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet,
                        })

                if results:
                    return json.dumps({
                        "query": query,
                        "results": results,
                        "count": len(results),
                    })

            except ImportError:
                pass

            # Last resort: just indicate search was performed
            return json.dumps({
                "query": query,
                "note": "Search completed but parsing requires beautifulsoup4. Install with: pip install beautifulsoup4",
                "suggestion": "Use web_crawl to fetch specific URLs for detailed information.",
            })

    except httpx.TimeoutException:
        return json.dumps({"error": "Search request timed out", "query": query})
    except Exception as e:
        return json.dumps({"error": str(e), "query": query})


@tool
async def web_crawl(url: str, extract_text: bool = True) -> str:
    """Fetch and extract content from a web page.

    Args:
        url: The URL to crawl
        extract_text: Whether to extract clean text content (default: True)

    Returns the page content, title, and meta description.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; UltimateAssistant/1.0)"},
                follow_redirects=True,
                timeout=15.0,
            )

            content = response.text

            if extract_text:
                # Try to extract text using BeautifulSoup
                try:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(content, "html.parser")

                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()

                    # Get text
                    text = soup.get_text(separator="\n", strip=True)

                    # Get title
                    title = soup.title.string if soup.title else ""

                    # Get meta description
                    meta_desc = ""
                    meta_tag = soup.find("meta", attrs={"name": "description"})
                    if meta_tag:
                        meta_desc = meta_tag.get("content", "")

                    # Truncate if too long
                    if len(text) > 10000:
                        text = text[:10000] + "...[truncated]"

                    return json.dumps({
                        "url": url,
                        "title": title,
                        "description": meta_desc,
                        "content": text,
                        "status_code": response.status_code,
                    })

                except ImportError:
                    # BeautifulSoup not available, return raw HTML
                    if len(content) > 10000:
                        content = content[:10000] + "...[truncated]"

                    return json.dumps({
                        "url": url,
                        "raw_html": content,
                        "status_code": response.status_code,
                        "note": "Install beautifulsoup4 for better text extraction: pip install beautifulsoup4",
                    })
            else:
                if len(content) > 10000:
                    content = content[:10000] + "...[truncated]"

                return json.dumps({
                    "url": url,
                    "raw_html": content,
                    "status_code": response.status_code,
                })

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "url": url,
        })


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

def build_system_prompt(memory_prompt: str = "") -> str:
    """Build the system prompt with memory instructions."""
    base_prompt = """You are a helpful, smart, and powerful virtual assistant. Your name is Nova.

You have access to a comprehensive set of capabilities:

## Core Tools
- **Date & Time**: Get current date, time, day of week
- **Calculations**: Perform mathematical calculations (basic math, trigonometry, logarithms)
- **Weather**: Check weather for any city

## File & Code Operations (Builtin Tools)
- **Read**: Read file contents with line numbers
- **Write**: Create or overwrite files
- **Edit**: Edit files using string replacement
- **Bash**: Execute shell commands
- **Glob**: Find files by pattern matching (e.g., **/*.py)
- **Grep**: Search file contents using regex
- **NotebookEdit**: Edit Jupyter notebooks

## Web Capabilities
- **web_search**: Search the web using DuckDuckGo
- **web_crawl**: Fetch and extract content from any URL

## Document Skills
You have access to specialized skills for document processing:
- **pdf**: Read, extract, and process PDF files
- **docx**: Work with Word documents
- **pptx**: Create and edit PowerPoint presentations
- **xlsx**: Work with Excel spreadsheets
- **webapp-testing**: Test web applications
- **frontend-design**: Create frontend designs
- **canvas-design**: Design graphics
- And many more specialized skills!

## Notes & Memory
- **Notes**: Save, list, and delete notes/reminders
- **Timers**: Set timers with custom messages
- **Memory**: Persistent memory across sessions (use memory tool to remember important information)

## Guidelines
1. Be concise but thorough in your responses
2. Use tools when they would provide accurate, real-time information
3. For general knowledge questions, you can answer directly from your training
4. Always be helpful, friendly, and professional
5. If you're unsure about something, say so
6. When performing file operations or commands, confirm what you're about to do
7. Format responses nicely with markdown when appropriate
8. Use the Skill tool when you need to work with documents (PDF, DOCX, PPTX, XLSX)
9. Use web_search for current information and web_crawl to fetch specific pages
10. Use the memory tool to save important information for future sessions

You're running on the user's local machine, so you can help with local files and commands.
"""

    if memory_prompt:
        base_prompt += f"\n\n## Memory System\n{memory_prompt}"

    return base_prompt


# ============================================================================
# Main Chat Loop
# ============================================================================


async def ultimate_assistant():
    """Run the ultimate virtual assistant."""
    print()
    print("=" * 70)
    print("  NOVA - Ultimate Virtual Assistant")
    print("=" * 70)
    print()
    print("  Capabilities:")
    print("    - Date/time, weather, calculations")
    print("    - File operations (read, write, edit, glob, grep)")
    print("    - Shell commands (bash)")
    print("    - Web search and crawl")
    print("    - Document skills (PDF, DOCX, PPTX, XLSX, and more)")
    print("    - Jupyter notebook editing")
    print("    - Persistent memory")
    print("    - Notes and timers")
    print()
    print("  Type 'quit' or 'exit' to end the conversation.")
    print("  Type 'skills' to list available skills.")
    print("=" * 70)
    print()

    # Get working directory
    cwd = Path.cwd()

    # Create built-in tools
    read_tool = ReadTool(cwd=cwd)
    write_tool = WriteTool(cwd=cwd)
    edit_tool = EditTool(cwd=cwd)
    bash_tool = BashTool(cwd=cwd, timeout=60)
    glob_tool = GlobTool(cwd=cwd)
    grep_tool = GrepTool(cwd=cwd)
    notebook_tool = NotebookEditTool(cwd=cwd)

    # Create memory tool
    memory_dir = Path.home() / ".nova_assistant" / "memory"
    memory_tool = FileSystemMemoryTool(memory_dir=memory_dir)
    memory_prompt = get_memory_system_prompt()

    # Create skill tool with all bundled skills
    skill_tool = SkillTool(include_bundled=True, include_registry=True)

    # Print available skills
    print(f"  Loaded {len(skill_tool.list_skills())} skills:")
    for skill_name in sorted(skill_tool.list_skills()):
        print(f"    - {skill_name}")
    print()

    # Build tool definitions
    tool_definitions = [
        # Custom tools
        get_current_datetime.definition,
        calculate.definition,
        get_weather.definition,
        web_search.definition,
        web_crawl.definition,
        add_note.definition,
        list_notes.definition,
        delete_note.definition,
        set_timer.definition,
        # Built-in tools
        read_tool.to_tool_definition(),
        write_tool.to_tool_definition(),
        edit_tool.to_tool_definition(),
        bash_tool.to_tool_definition(),
        glob_tool.to_tool_definition(),
        grep_tool.to_tool_definition(),
        notebook_tool.to_tool_definition(),
        # Memory tool
        memory_tool.to_tool_definition(),
        # Skill tool
        skill_tool.definition,
    ]

    # Configure the assistant with tools
    options = AgentOptions(
        provider="claude",
        model="claude-sonnet-4-20250514",
        system_prompt=build_system_prompt(memory_prompt),
        tools=tool_definitions,
        stream=True,
        max_turns=20,  # More turns for complex tasks
    )

    async with UniversalAgentClient(options) as client:
        # Initial greeting
        print("Nova: Hello! I'm Nova, your ultimate virtual assistant.")
        print("      I can help with files, code, documents, web searches, and much more!")
        print("      What would you like me to help you with?\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nNova: Goodbye! Have a great day!")
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q", "bye", "goodbye"):
                print("\nNova: Goodbye! Have a great day!")
                break

            if user_input.lower() == "skills":
                print("\nNova: Here are my available skills:")
                print(skill_tool.get_skill_summary())
                print()
                continue

            await client.send(user_input)

            print("\nNova: ", end="", flush=True)

            tool_calls_made = []

            async for msg in client.receive():
                if isinstance(msg, StreamEvent):
                    # Print streaming text
                    if msg.delta and msg.delta.get("type") == "text":
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
    asyncio.run(ultimate_assistant())
