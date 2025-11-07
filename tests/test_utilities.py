from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import types

import config
from agent.queue.engine import AsyncTaskQueue
from agent.tools.calendar import CalendarClient, CalendarEvent
from agent.tools.docs import Document, DocumentVectorStore
from agent.tools.io_utils import generate_pdf
import tools


class DummyCompletion:
    def __init__(self, text: str) -> None:
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=text))]


def stub_completion(text: str):
    def _create(*_, **__):
        return DummyCompletion(text)

    return _create


def test_document_vector_store(tmp_path):
    store = DocumentVectorStore()
    store.add_documents(
        [
            Document(content="LangGraph builds graphs", metadata={"id": "1"}),
            Document(content="Calendars keep track of events", metadata={"id": "2"}),
        ]
    )
    matches = store.similarity_search("graph workflow", k=1)
    assert matches and matches[0][0].metadata["id"] == "1"


def test_generate_pdf(tmp_path):
    pdf_path = tmp_path / "report.pdf"
    generate_pdf("hello", pdf_path)
    assert pdf_path.exists()


def test_calendar_client(tmp_path):
    db_path = tmp_path / "cal.db"
    client = CalendarClient(db_path)
    event = CalendarEvent(
        title="Kickoff",
        start=datetime.now(timezone.utc),
        end=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    client.add_event(event)
    events = client.list_events()
    assert len(events) == 1 and events[0].title == "Kickoff"
    client.close()


def test_summarize_text(monkeypatch):
    monkeypatch.setattr(config.client.chat.completions, "create", stub_completion("摘要"))
    assert tools.summarize_text("内容") == "摘要"


def test_web_search_returns_formatted():
    results = tools.web_search("LangGraph")
    assert results and "LangGraph" in results[0]


def test_async_task_queue(tmp_path):
    async def _run():
        queue = AsyncTaskQueue(tmp_path / "tasks.db")
        task_id = await queue.enqueue({"input": "hi"})
        task = await queue.acquire()
        assert task is not None and task.id == task_id
        await queue.complete(task_id, {"response": "ok"})
        assert await queue.pending_count() == 0
        await queue.close()

    asyncio.run(_run())
