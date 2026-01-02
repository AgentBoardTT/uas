"""Persistent memory for Universal Agent SDK."""

import json
import time
import uuid
from pathlib import Path
from typing import Any

from ..errors import MemoryError
from ..types import MemoryEntry, MemorySearchResult
from .base import BaseMemory


class PersistentMemory(BaseMemory):
    """File-based persistent memory storage.

    PersistentMemory stores entries to disk, allowing data to persist
    across process restarts.

    Features:
    - File-based storage (JSON)
    - Automatic persistence
    - Keyword search
    - Session isolation

    Example:
        ```python
        memory = PersistentMemory("./memory/session_1.json")

        # Add entries (automatically saved)
        await memory.add("Important context about the project")

        # Later, in a new process
        memory = PersistentMemory("./memory/session_1.json")
        results = await memory.search("project")
        ```
    """

    def __init__(
        self,
        path: str | Path,
        auto_save: bool = True,
    ):
        """Initialize persistent memory.

        Args:
            path: Path to the storage file
            auto_save: Whether to automatically save on changes
        """
        self.path = Path(path)
        self.auto_save = auto_save
        self._entries: dict[str, MemoryEntry] = {}
        self._modified = False

        # Load existing data
        self._load()

    def _load(self) -> None:
        """Load entries from disk."""
        if not self.path.exists():
            return

        try:
            data = json.loads(self.path.read_text())
            for entry_data in data.get("entries", []):
                entry = MemoryEntry(
                    id=entry_data["id"],
                    content=entry_data["content"],
                    metadata=entry_data.get("metadata", {}),
                    embedding=entry_data.get("embedding"),
                    timestamp=entry_data.get("timestamp"),
                )
                self._entries[entry.id] = entry
        except Exception as e:
            raise MemoryError(f"Failed to load memory from {self.path}: {e}") from e

    def _save(self) -> None:
        """Save entries to disk."""
        if not self._modified:
            return

        # Ensure parent directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)

        entries_data = [
            {
                "id": entry.id,
                "content": entry.content,
                "metadata": entry.metadata,
                "embedding": entry.embedding,
                "timestamp": entry.timestamp,
            }
            for entry in self._entries.values()
        ]

        data = {"entries": entries_data, "updated_at": time.time()}

        try:
            self.path.write_text(json.dumps(data, indent=2))
            self._modified = False
        except Exception as e:
            raise MemoryError(f"Failed to save memory to {self.path}: {e}") from e

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
        self._modified = True

        if self.auto_save:
            self._save()

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
                score = len(matching_words) / len(query_words)

                if query_lower in content_lower:
                    score = min(1.0, score + 0.2)

                results.append(MemorySearchResult(entry=entry, score=score))

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
            self._modified = True

            if self.auto_save:
                self._save()

            return True
        return False

    async def clear(self) -> None:
        """Clear all entries from memory."""
        self._entries.clear()
        self._modified = True

        if self.auto_save:
            self._save()

    @property
    def size(self) -> int:
        """Get the number of entries in memory."""
        return len(self._entries)

    def save(self) -> None:
        """Manually save to disk."""
        self._modified = True
        self._save()

    def reload(self) -> None:
        """Reload from disk, discarding unsaved changes."""
        self._entries.clear()
        self._modified = False
        self._load()
