"""Conversation memory for Universal Agent SDK."""

import time
import uuid
from typing import Any

from ..types import MemoryEntry, MemorySearchResult
from .base import BaseMemory


class ConversationMemory(BaseMemory):
    """In-memory conversation history storage.

    ConversationMemory provides fast, ephemeral storage for conversation
    history. Data is lost when the process ends.

    Features:
    - Fast in-memory storage
    - Basic keyword search
    - Automatic timestamp tracking
    - Memory limits with automatic pruning

    Example:
        ```python
        memory = ConversationMemory(max_entries=100)

        # Add entries
        await memory.add("User asked about Python")
        await memory.add("Assistant explained decorators")

        # Search
        results = await memory.search("decorators")
        for result in results:
            print(f"{result.score:.2f}: {result.entry.content}")
        ```
    """

    def __init__(self, max_entries: int | None = None):
        """Initialize conversation memory.

        Args:
            max_entries: Maximum number of entries to store.
                        Oldest entries are pruned when exceeded.
        """
        self.max_entries = max_entries
        self._entries: dict[str, MemoryEntry] = {}
        self._order: list[str] = []  # Track insertion order for pruning

    async def add(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Add an entry to memory.

        Args:
            content: The content to store
            metadata: Optional metadata

        Returns:
            ID of the created entry
        """
        entry_id = str(uuid.uuid4())
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            metadata=metadata or {},
            timestamp=time.time(),
        )

        self._entries[entry_id] = entry
        self._order.append(entry_id)

        # Prune if over limit
        if self.max_entries and len(self._entries) > self.max_entries:
            oldest_id = self._order.pop(0)
            del self._entries[oldest_id]

        return entry_id

    async def get(self, entry_id: str) -> MemoryEntry | None:
        """Retrieve an entry by ID.

        Args:
            entry_id: The entry ID

        Returns:
            MemoryEntry if found, None otherwise
        """
        return self._entries.get(entry_id)

    async def search(
        self, query: str, limit: int = 10, **kwargs: Any
    ) -> list[MemorySearchResult]:
        """Search memory using keyword matching.

        Args:
            query: Search query
            limit: Maximum number of results
            **kwargs: Unused

        Returns:
            List of MemorySearchResult sorted by relevance
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results: list[MemorySearchResult] = []

        for entry in self._entries.values():
            content_lower = entry.content.lower()
            content_words = set(content_lower.split())

            # Calculate simple keyword overlap score
            matching_words = query_words & content_words
            if matching_words:
                # Score based on percentage of query words found
                score = len(matching_words) / len(query_words)

                # Boost if query appears as substring
                if query_lower in content_lower:
                    score = min(1.0, score + 0.2)

                results.append(MemorySearchResult(entry=entry, score=score))

        # Sort by score descending, then by timestamp
        results.sort(key=lambda r: (-r.score, -(r.entry.timestamp or 0)))

        return results[:limit]

    async def delete(self, entry_id: str) -> bool:
        """Delete an entry by ID.

        Args:
            entry_id: The entry ID

        Returns:
            True if deleted, False if not found
        """
        if entry_id in self._entries:
            del self._entries[entry_id]
            self._order.remove(entry_id)
            return True
        return False

    async def clear(self) -> None:
        """Clear all entries from memory."""
        self._entries.clear()
        self._order.clear()

    @property
    def size(self) -> int:
        """Get the number of entries in memory."""
        return len(self._entries)

    def get_recent(self, limit: int = 10) -> list[MemoryEntry]:
        """Get the most recent entries.

        Args:
            limit: Maximum number of entries

        Returns:
            List of MemoryEntry in reverse chronological order
        """
        recent_ids = self._order[-limit:][::-1]
        return [self._entries[eid] for eid in recent_ids if eid in self._entries]

    def get_by_role(self, role: str) -> list[MemoryEntry]:
        """Get entries by role (user, assistant, system).

        Args:
            role: The role to filter by

        Returns:
            List of MemoryEntry with matching role
        """
        return [
            entry
            for entry in self._entries.values()
            if entry.metadata.get("role") == role
        ]
