"""Local calendar client used for synchronising events and reminders."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional

SUPPORTED_DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d",
)


@dataclass
class CalendarEvent:
    title: str
    start: datetime
    end: datetime
    location: Optional[str] = None
    description: Optional[str] = None


class CalendarClient:
    """Persist events inside a small SQLite database."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start TIMESTAMP NOT NULL,
                end TIMESTAMP NOT NULL,
                location TEXT,
                description TEXT
            )
            """
        )
        self._connection.commit()

    def add_event(self, event: CalendarEvent) -> int:
        cursor = self._connection.cursor()
        cursor.execute(
            "INSERT INTO events (title, start, end, location, description) VALUES (?, ?, ?, ?, ?)",
            (event.title, event.start.isoformat(), event.end.isoformat(), event.location, event.description),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def list_events(self, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[CalendarEvent]:
        query = "SELECT title, start, end, location, description FROM events"
        params: List[str] = []
        clauses: List[str] = []
        if start is not None:
            clauses.append("start >= ?")
            params.append(start.isoformat())
        if end is not None:
            clauses.append("end <= ?")
            params.append(end.isoformat())
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY start ASC"
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        events: List[CalendarEvent] = []
        for title, start_str, end_str, location, description in rows:
            events.append(
                CalendarEvent(
                    title=title,
                    start=datetime.fromisoformat(start_str),
                    end=datetime.fromisoformat(end_str),
                    location=location,
                    description=description,
                )
            )
        return events

    def upcoming(self, within: timedelta = timedelta(days=7)) -> List[CalendarEvent]:
        now = datetime.now()
        return self.list_events(start=now, end=now + within)

    def import_events(self, events: Iterable[CalendarEvent]) -> None:
        for event in events:
            self.add_event(event)

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "CalendarClient":  # pragma: no cover - convenience
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - convenience
        self.close()


def parse_datetime(value: str) -> datetime:
    """Parse common date/time formats from user input."""

    cleaned = value.strip()
    if not cleaned:
        raise ValueError("时间不能为空")
    last_error: Optional[Exception] = None
    for fmt in SUPPORTED_DATETIME_FORMATS:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            if fmt == "%Y-%m-%d":
                # Assume start of day when only date provided.
                return parsed.replace(hour=9, minute=0)
            return parsed
        except ValueError as exc:
            last_error = exc
            continue
    raise ValueError(f"无法解析时间 '{value}'，请使用 YYYY-MM-DD HH:MM 格式") from last_error


def format_event(event: CalendarEvent) -> str:
    start = event.start.strftime("%Y-%m-%d %H:%M")
    end = event.end.strftime("%Y-%m-%d %H:%M")
    details = [f"{start} - {end}"]
    if event.location:
        details.append(f"地点: {event.location}")
    if event.description:
        details.append(event.description)
    detail_text = " | ".join(details)
    return f"{event.title} ({detail_text})"
