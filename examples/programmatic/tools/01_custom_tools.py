"""Tool decorator example for Universal Agent SDK.

This example shows how to create tools using the @tool decorator
and use them with queries.
"""

import asyncio
import json
from datetime import datetime

from universal_agent_sdk import (
    AgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    query,
    tool,
)


# Simple tool with inferred schema from type hints
@tool
def get_current_time() -> str:
    """Get the current time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Tool with parameters
@tool
def calculate(expression: str) -> str:
    """Calculate a mathematical expression.

    Args:
        expression: A math expression like "2 + 2" or "10 * 5"
    """
    try:
        # Note: In production, use a safe expression evaluator
        result = eval(expression)  # noqa: S307
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"


# Tool with explicit schema
@tool(
    name="get_weather",
    description="Get the current weather for a city",
    input_schema={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"},
            "units": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature units",
            },
        },
        "required": ["city"],
    },
)
def get_weather(city: str, units: str = "celsius") -> str:
    """Get weather for a city (mock implementation)."""
    # Mock weather data
    weather_data = {
        "paris": {"temp": 18, "condition": "Partly cloudy"},
        "tokyo": {"temp": 25, "condition": "Sunny"},
        "new york": {"temp": 22, "condition": "Clear"},
    }

    city_lower = city.lower()
    if city_lower in weather_data:
        data = weather_data[city_lower]
        temp = data["temp"]
        if units == "fahrenheit":
            temp = temp * 9 / 5 + 32
            unit_symbol = "°F"
        else:
            unit_symbol = "°C"
        return f"Weather in {city}: {data['condition']}, {temp}{unit_symbol}"
    else:
        return f"Weather data not available for {city}"


# Async tool
@tool
async def fetch_data(url: str) -> str:
    """Fetch data from a URL (mock implementation).

    Args:
        url: The URL to fetch
    """
    # Mock implementation - in reality you'd use httpx or aiohttp
    await asyncio.sleep(0.1)  # Simulate network delay
    return f"Fetched data from {url}: {{status: 'ok', data: 'example'}}"


async def main():
    """Demonstrate tool usage."""
    print("=== Tool Usage Example ===\n")

    # Create options with tools
    options = AgentOptions(
        tools=[
            get_current_time.definition,
            calculate.definition,
            get_weather.definition,
            fetch_data.definition,
        ],
        max_turns=5,
    )

    # Test 1: Current time
    print("--- Testing get_current_time ---")
    print("User: What time is it?\n")

    async for msg in query("What time is it?", options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    print(f"Tool call: {block.name}({json.dumps(block.input)})")
                elif isinstance(block, TextBlock):
                    print(f"Response: {block.text}")
    print()

    # Test 2: Calculator
    print("--- Testing calculate ---")
    print("User: What is 15 * 7 + 23?\n")

    async for msg in query("What is 15 * 7 + 23?", options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    print(f"Tool call: {block.name}({json.dumps(block.input)})")
                elif isinstance(block, TextBlock):
                    print(f"Response: {block.text}")
    print()

    # Test 3: Weather
    print("--- Testing get_weather ---")
    print("User: What's the weather in Paris?\n")

    async for msg in query("What's the weather in Paris?", options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    print(f"Tool call: {block.name}({json.dumps(block.input)})")
                elif isinstance(block, TextBlock):
                    print(f"Response: {block.text}")
    print()

    # Test 4: Multiple tool calls
    print("--- Testing multiple tools ---")
    print("User: What time is it, and what's 42 * 2?\n")

    async for msg in query("What time is it, and what's 42 * 2?", options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    print(f"Tool call: {block.name}({json.dumps(block.input)})")
                elif isinstance(block, TextBlock):
                    print(f"Response: {block.text}")


if __name__ == "__main__":
    asyncio.run(main())
