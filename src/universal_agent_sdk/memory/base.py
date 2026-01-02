"""Base memory interface for Universal Agent SDK."""

from abc import ABC, abstractmethod
from typing import Any

from ..types import MemoryEntry, MemorySearchResult, Message


class BaseMemory(ABC):
    """Abstract base class for memory implementations.

    Memory systems allow agents to store and retrieve information
    across conversations and sessions.

    Subclasses implement specific storage backends:
    - ConversationMemory: In-memory conversation history
    - PersistentMemory: Durable storage (file, database)
    - VectorMemory: Semantic search with embeddings
    """

    @abstractmethod
    async def add(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Add an entry to memory.

        Args:
            content: The content to store
            metadata: Optional metadata for the entry

        Returns:
            ID of the created entry
        """
        ...

    @abstractmethod
    async def get(self, entry_id: str) -> MemoryEntry | None:
        """Retrieve an entry by ID.

        Args:
            entry_id: The entry ID

        Returns:
            MemoryEntry if found, None otherwise
        """
        ...

    @abstractmethod
    async def search(
        self, query: str, limit: int = 10, **kwargs: Any
    ) -> list[MemorySearchResult]:
        """Search memory for relevant entries.

        Args:
            query: Search query
            limit: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
            List of MemorySearchResult sorted by relevance
        """
        ...

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Delete an entry by ID.

        Args:
            entry_id: The entry ID

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries from memory."""
        ...

    async def add_message(self, message: Message) -> str:
        """Add a message to memory.

        Args:
            message: Message to store

        Returns:
            ID of the created entry
        """
        from ..types import AssistantMessage, SystemMessage, TextBlock, UserMessage

        # Extract content from message
        if isinstance(message, UserMessage):
            if isinstance(message.content, str):
                content = message.content
            else:
                texts = [b.text for b in message.content if isinstance(b, TextBlock)]
                content = " ".join(texts)
            metadata = {"role": "user", "uuid": message.uuid}
        elif isinstance(message, AssistantMessage):
            texts = [b.text for b in message.content if isinstance(b, TextBlock)]
            content = " ".join(texts)
            metadata = {"role": "assistant", "model": message.model}
        elif isinstance(message, SystemMessage):
            content = message.content
            metadata = {"role": "system"}
        else:
            content = str(message)
            metadata = {"role": "unknown"}

        return await self.add(content, metadata)

    async def get_context(self, query: str, max_tokens: int = 2000) -> str:
        """Get relevant context for a query.

        Args:
            query: The query to find context for
            max_tokens: Approximate token limit

        Returns:
            Concatenated relevant context
        """
        results = await self.search(query)

        context_parts = []
        current_length = 0

        for result in results:
            entry_length = len(result.entry.content.split())
            if current_length + entry_length > max_tokens:
                break
            context_parts.append(result.entry.content)
            current_length += entry_length

        return "\n\n".join(context_parts)

    @property
    @abstractmethod
    def size(self) -> int:
        """Get the number of entries in memory."""
        ...
