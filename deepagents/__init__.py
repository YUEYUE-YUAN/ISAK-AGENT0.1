"""Lightweight DeepAgents compatibility shim for local development/tests."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .memory import Store


class Agent:
    """Minimal agent wrapper that exposes a memory store."""

    def __init__(self, memory: Optional[Store] = None) -> None:
        self.memory = memory or Store(Path(".deepagents-memory"))


__all__ = ["Agent", "Store"]
