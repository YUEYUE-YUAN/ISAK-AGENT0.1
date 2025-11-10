"""Asynchronous task queue implemented with SQLite."""
from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Task, TaskStatus


class AsyncTaskQueue:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
        self._ensure_schema()
        self._lock = asyncio.Lock()

    def _ensure_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    async def enqueue(self, payload: dict) -> int:
        async with self._lock:
            cursor = self._connection.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO tasks (payload, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (json.dumps(payload), TaskStatus.PENDING.value, now, now),
            )
            self._connection.commit()
            return int(cursor.lastrowid)

    async def acquire(self) -> Optional[Task]:
        async with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at ASC LIMIT 1",
                (TaskStatus.PENDING.value,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            cursor.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (TaskStatus.IN_PROGRESS.value, datetime.utcnow().isoformat(), row["id"]),
            )
            self._connection.commit()
            return Task(
                id=row["id"],
                payload=json.loads(row["payload"]),
                status=TaskStatus.IN_PROGRESS,
                result=json.loads(row["result"]) if row["result"] else None,
                error=row["error"],
            )

    async def complete(self, task_id: int, result: dict) -> None:
        async with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                "UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?",
                (
                    TaskStatus.COMPLETED.value,
                    json.dumps(result),
                    datetime.utcnow().isoformat(),
                    task_id,
                ),
            )
            self._connection.commit()

    async def fail(self, task_id: int, error: str) -> None:
        async with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                "UPDATE tasks SET status = ?, error = ?, updated_at = ? WHERE id = ?",
                (
                    TaskStatus.FAILED.value,
                    error,
                    datetime.utcnow().isoformat(),
                    task_id,
                ),
            )
            self._connection.commit()

    async def pending_count(self) -> int:
        async with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM tasks WHERE status IN (?, ?)",
                (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value),
            )
            (count,) = cursor.fetchone()
            return int(count)

    async def close(self) -> None:
        self._connection.close()

    async def __aenter__(self) -> "AsyncTaskQueue":  # pragma: no cover - convenience
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - convenience
        await self.close()
