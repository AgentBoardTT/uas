"""WebFetch tool for fetching and extracting content from web pages."""

from __future__ import annotations

import json
from typing import Any

from ...types import ToolDefinition


class WebFetchTool:
    """Fetch and extract content from web pages.

    This tool fetches a URL and extracts clean text content,
    title, and meta description.
    """

    name = "WebFetch"
    description = """Fetch and extract content from a web page.

Args:
    url: The URL to fetch
    extract_text: Whether to extract clean text content (default: True)

Returns the page content, title, and meta description.
Useful for reading articles, documentation, or any web content.
"""

    def __init__(self, max_content_length: int = 10000):
        """Initialize the WebFetch tool.

        Args:
            max_content_length: Maximum characters of content to return
        """
        self.max_content_length = max_content_length

    @property
    def input_schema(self) -> dict[str, Any]:
        """Get the input schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch",
                },
                "extract_text": {
                    "type": "boolean",
                    "description": "Whether to extract clean text content (default: True)",
                    "default": True,
                },
            },
            "required": ["url"],
        }

    async def __call__(
        self,
        url: str,
        extract_text: bool = True,
    ) -> str:
        """Fetch and extract content from a web page.

        Args:
            url: The URL to fetch
            extract_text: Whether to extract clean text

        Returns:
            JSON string with page content
        """
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; UniversalAgentSDK/1.0)"
                    },
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
                        for element in soup(
                            ["script", "style", "nav", "footer", "header", "aside"]
                        ):
                            element.decompose()

                        # Get text
                        text = soup.get_text(separator="\n", strip=True)

                        # Clean up multiple newlines
                        import re

                        text = re.sub(r"\n{3,}", "\n\n", text)

                        # Get title
                        title = soup.title.string if soup.title else ""

                        # Get meta description
                        meta_desc = ""
                        meta_tag = soup.find("meta", attrs={"name": "description"})
                        if meta_tag:
                            meta_content = meta_tag.get("content", "")
                            meta_desc = str(meta_content) if meta_content else ""

                        # Truncate if too long
                        if len(text) > self.max_content_length:
                            text = (
                                text[: self.max_content_length]
                                + "\n\n...[content truncated]"
                            )

                        return json.dumps(
                            {
                                "url": url,
                                "title": title,
                                "description": meta_desc,
                                "content": text,
                                "status_code": response.status_code,
                            }
                        )

                    except ImportError:
                        # BeautifulSoup not available, return raw HTML
                        if len(content) > self.max_content_length:
                            content = (
                                content[: self.max_content_length] + "...[truncated]"
                            )

                        return json.dumps(
                            {
                                "url": url,
                                "raw_html": content,
                                "status_code": response.status_code,
                                "note": "Install beautifulsoup4 for better text extraction: pip install beautifulsoup4",
                            }
                        )
                else:
                    if len(content) > self.max_content_length:
                        content = content[: self.max_content_length] + "...[truncated]"

                    return json.dumps(
                        {
                            "url": url,
                            "raw_html": content,
                            "status_code": response.status_code,
                        }
                    )

        except Exception as e:
            return json.dumps(
                {
                    "error": str(e),
                    "url": url,
                }
            )

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to a ToolDefinition for use with agents."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.__call__,
        )
