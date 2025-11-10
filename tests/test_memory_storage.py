from __future__ import annotations
import memory


class DummyResponse:
    def __init__(self, status_code: int, payload=None):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"status {self.status_code}")

    def json(self):
        return self._payload


def test_local_file_store_persists(tmp_path):
    path = tmp_path / "history.json"
    store = memory.LocalFileHistoryStore(path)
    store.save_message("user", "hello")
    store.save_message("bot", "hi")

    disk_copy = memory.LocalFileHistoryStore(path)
    history = disk_copy.get_history()
    assert len(history) == 2
    assert history[-1]["role"] == "bot"
    assert history[-1]["content"] == "hi"

    disk_copy.clear_history()
    assert disk_copy.get_history() == []
    assert not path.exists()


def test_cloud_store_uses_fallback_on_failure(monkeypatch):
    fallback = memory.InMemoryHistoryStore()

    class FailingSession:
        def post(self, *args, **kwargs):
            raise RuntimeError("offline")

        def get(self, *args, **kwargs):
            raise RuntimeError("offline")

        def delete(self, *args, **kwargs):
            raise RuntimeError("offline")

    monkeypatch.setattr(memory.requests, "Session", lambda: FailingSession())

    store = memory.CloudHistoryStore("https://example.com/history", fallback=fallback)
    store.save_message("user", "cloud message")

    history = store.get_history()
    assert history[0]["content"] == "cloud message"

    store.clear_history()
    assert fallback.get_history() == []


def test_cloud_store_syncs_with_remote(monkeypatch):
    records: list[dict[str, str]] = []

    class RecordingSession:
        def post(self, *args, **kwargs):
            records.append(kwargs.get("json"))
            return DummyResponse(201)

        def get(self, *args, **kwargs):
            return DummyResponse(200, list(records))

        def delete(self, *args, **kwargs):
            records.clear()
            return DummyResponse(204)

    monkeypatch.setattr(memory.requests, "Session", lambda: RecordingSession())

    store = memory.CloudHistoryStore("https://example.com/history", fallback=memory.InMemoryHistoryStore())
    store.save_message("user", "persist to cloud")
    assert records[0]["content"] == "persist to cloud"

    fetched = store.get_history()
    assert fetched[0]["content"] == "persist to cloud"

    store.clear_history()
    assert records == []
