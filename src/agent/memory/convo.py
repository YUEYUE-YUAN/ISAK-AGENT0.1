"""Conversation memory utilities with buffer and summarisation support."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Deque, List, Tuple


Summariser = Callable[[str], str]


@dataclass
class ConversationMemory:
    """Maintain a rolling window of chat messages and an optional summary."""

    window_size: int = 10
    summariser: Summariser | None = None
    _buffer: Deque[Tuple[str, str]] = field(default_factory=lambda: deque(maxlen=50))
    summary: str = ""

    def append(self, role: str, content: str) -> None:
        self._buffer.append((role, content))
        if len(self._buffer) > self.window_size and self.summariser is not None:
            self.summary = self.summariser(self.render())

    def clear(self) -> None:
        self._buffer.clear()
        self.summary = ""

    def render(self) -> str:
        return "\n".join(f"{role}: {content}" for role, content in self._buffer)

    def recent(self, limit: int | None = None) -> List[Tuple[str, str]]:
        items = list(self._buffer)
        if limit is None:
            return items
        return items[-limit:]
