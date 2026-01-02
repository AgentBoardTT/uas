"""DateTime tool for getting current date and time."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from ...types import ToolDefinition


class DateTimeTool:
    """Get the current date and time.

    This tool provides the LLM with awareness of the current date and time,
    which is essential for time-relative queries like "news from yesterday"
    or "events in the last week".
    """

    name = "DateTime"
    description = """Get the current date and time.

Returns the current date, time, day of week, timezone, and formatted strings.
Use this tool whenever you need to know the current date or time, especially
for time-relative queries like "recent news", "last week", "yesterday", etc.
"""

    @property
    def input_schema(self) -> dict[str, Any]:
        """Get the input schema for this tool."""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def __call__(self) -> str:
        """Get the current date and time.

        Returns:
            JSON string with current date/time information
        """
        now = datetime.now()
        return json.dumps({
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p"),
            "iso": now.isoformat(),
            "timestamp": now.timestamp(),
            "year": now.year,
            "month": now.month,
            "day": now.day,
        })

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to a ToolDefinition for use with agents."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.__call__,
        )
