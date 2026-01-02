"""WebSearch tool for searching the web."""

from __future__ import annotations

import json
from typing import Any

from ...types import ToolDefinition


class WebSearchTool:
    """Search the web using DuckDuckGo.

    This tool performs web searches and returns results with titles,
    URLs, and snippets.
    """

    name = "WebSearch"
    description = """Search the web for information using DuckDuckGo.

Args:
    query: The search query
    num_results: Number of results to return (default: 5, max: 10)

Returns search results with titles, URLs, and snippets.
"""

    def __init__(self, num_results: int = 5):
        """Initialize the WebSearch tool.

        Args:
            num_results: Default number of results to return
        """
        self.default_num_results = min(num_results, 10)

    @property
    def input_schema(self) -> dict[str, Any]:
        """Get the input schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5, max: 10)",
                    "default": self.default_num_results,
                },
            },
            "required": ["query"],
        }

    async def __call__(
        self,
        query: str,
        num_results: int | None = None,
    ) -> str:
        """Search the web for information.

        Args:
            query: The search query
            num_results: Number of results to return

        Returns:
            JSON string with search results
        """
        import httpx

        num_results = min(num_results or self.default_num_results, 10)

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
                    "suggestion": "Use WebFetch to fetch specific URLs for detailed information.",
                })

        except Exception as e:
            return json.dumps({"error": str(e), "query": query})

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to a ToolDefinition for use with agents."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            handler=self.__call__,
        )
