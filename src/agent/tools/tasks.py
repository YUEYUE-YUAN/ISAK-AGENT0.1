"""Task management utilities for the CLI assistant."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import List, Optional

SUPPORTED_DUE_FORMATS = (
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d",
)


def _now_iso() -> str:
    return datetime.now().isoformat()


def parse_due(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    last_error: Optional[Exception] = None
    for fmt in SUPPORTED_DUE_FORMATS:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            if fmt == "%Y-%m-%d":
                return parsed.replace(hour=18, minute=0)
            return parsed
        except ValueError as exc:
            last_error = exc
            continue
    raise ValueError(f"无法解析截止时间 '{value}'，请使用 YYYY-MM-DD HH:MM 格式") from last_error


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"


@dataclass
class Task:
    id: int
    title: str
    status: TaskStatus
    created_at: str
    updated_at: str
    due: Optional[str] = None
    notes: Optional[str] = None

    def mark_completed(self) -> None:
        self.status = TaskStatus.COMPLETED
        self.updated_at = _now_iso()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "due": self.due,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Task":
        return cls(
            id=int(payload.get("id", 0)),
            title=str(payload.get("title", "")),
            status=TaskStatus(payload.get("status", TaskStatus.PENDING.value)),
            created_at=str(payload.get("created_at", _now_iso())),
            updated_at=str(payload.get("updated_at", _now_iso())),
            due=payload.get("due"),
            notes=payload.get("notes"),
        )

    def due_datetime(self) -> Optional[datetime]:
        if not self.due:
            return None
        return datetime.fromisoformat(self.due)

    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED


class TaskManager:
    """Persist tasks in a JSON file with basic querying helpers."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._tasks: List[Task] = self._load()
        self._next_id = (max((task.id for task in self._tasks), default=0) + 1)

    def _load(self) -> List[Task]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []
        tasks: List[Task] = []
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    try:
                        tasks.append(Task.from_dict(entry))
                    except Exception:
                        continue
        return tasks

    def _flush(self) -> None:
        payload = [task.to_dict() for task in self._tasks]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_task(self, title: str, *, due: Optional[datetime] = None, notes: Optional[str] = None) -> Task:
        with self._lock:
            cleaned_title = title.strip()
            if not cleaned_title:
                raise ValueError("任务标题不能为空")
            task = Task(
                id=self._next_id,
                title=cleaned_title,
                status=TaskStatus.PENDING,
                created_at=_now_iso(),
                updated_at=_now_iso(),
                due=due.isoformat() if due else None,
                notes=notes.strip() if notes else None,
            )
            self._tasks.append(task)
            self._next_id += 1
            self._flush()
            return task

    def list_tasks(self, *, include_completed: bool = True) -> List[Task]:
        with self._lock:
            tasks = list(self._tasks)
        if include_completed:
            return sorted(tasks, key=lambda t: (t.is_completed(), t.due is None, t.due or "", t.id))
        return sorted(
            [task for task in tasks if not task.is_completed()],
            key=lambda t: (t.due is None, t.due or "", t.id),
        )

    def get_task(self, task_id: int) -> Optional[Task]:
        with self._lock:
            for task in self._tasks:
                if task.id == task_id:
                    return task
        return None

    def complete_task(self, task_id: int) -> Optional[Task]:
        with self._lock:
            for task in self._tasks:
                if task.id == task_id:
                    if task.is_completed():
                        return task
                    task.mark_completed()
                    self._flush()
                    return task
        return None

    def tasks_due_within(self, days: int, *, now: Optional[datetime] = None) -> List[Task]:
        if days < 0:
            return []
        now_dt = now or datetime.now()
        horizon = now_dt + timedelta(days=days)
        upcoming: List[Task] = []
        for task in self.list_tasks(include_completed=False):
            due = task.due_datetime()
            if due and now_dt <= due <= horizon:
                upcoming.append(task)
        return upcoming

    def overdue_tasks(self, *, now: Optional[datetime] = None) -> List[Task]:
        now_dt = now or datetime.now()
        overdue: List[Task] = []
        for task in self.list_tasks(include_completed=False):
            due = task.due_datetime()
            if due and due < now_dt:
                overdue.append(task)
        return overdue


__all__ = ["Task", "TaskManager", "TaskStatus", "parse_due"]
