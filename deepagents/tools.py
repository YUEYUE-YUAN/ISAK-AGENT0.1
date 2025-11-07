"""Utility helpers that mimic the DeepAgents toolkit for local runs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


def _split_tasks(description: str) -> List[str]:
    text = description.strip()
    if not text:
        return []
    separators = [";", "\n", "。", ".", "！", "?", "！", "？"]
    for sep in separators:
        if sep in text:
            pieces = [part.strip() for part in text.replace("\r", "").split(sep)]
            tasks = [piece for piece in pieces if piece]
            if tasks:
                return tasks
    return [text]


def write_todos(task_description: str) -> List[str]:
    """Return a list of todo strings derived from the description."""
    return _split_tasks(task_description)


@dataclass
class DeepAgentTask:
    description: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.description


def task(description: str) -> DeepAgentTask:
    """Create a simple task object for compatibility."""
    cleaned = description.strip() if description else ""
    return DeepAgentTask(description=cleaned or "Pending task")


def ls(path: str = ".") -> List[str]:
    return sorted(str(p) for p in Path(path).expanduser().resolve().iterdir())


def read_file(path: str) -> str:
    return Path(path).expanduser().read_text(encoding="utf-8")


def write_file(path: str, content: str) -> None:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def edit_file(path: str, new_text: str) -> None:
    write_file(path, new_text)


__all__ = [
    "write_todos",
    "task",
    "ls",
    "read_file",
    "write_file",
    "edit_file",
    "DeepAgentTask",
]
