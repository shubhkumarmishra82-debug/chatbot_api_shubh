"""
Abstract interface every AI provider implements. This is what makes the
router modular -- adding a new provider later means writing one new file
that implements this interface, nothing else changes.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """Non-streaming: returns the full reply text."""
        ...

    @abstractmethod
    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncIterator[str]:
        """Streaming: yields text chunks as they arrive."""
        ...
        yield ""  # pragma: no cover -- keeps this an async generator for subclasses
