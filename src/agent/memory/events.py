"""Timeline memory stored inside SQLite."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


@dataclass
class TimelineEvent:
    timestamp: datetime
    label: str
    payload: str


class TimelineStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                label TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def record(self, event: TimelineEvent) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            "INSERT INTO timeline (timestamp, label, payload) VALUES (?, ?, ?)",
            (event.timestamp.isoformat(), event.label, event.payload),
        )
        self._connection.commit()

    def list(self) -> List[TimelineEvent]:
        cursor = self._connection.cursor()
        cursor.execute("SELECT timestamp, label, payload FROM timeline ORDER BY timestamp ASC")
        rows = cursor.fetchall()
        return [TimelineEvent(datetime.fromisoformat(ts), label, payload) for ts, label, payload in rows]

    def extend(self, events: Iterable[TimelineEvent]) -> None:
        for event in events:
            self.record(event)

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "TimelineStore":  # pragma: no cover
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover
        self.close()
