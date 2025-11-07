from __future__ import annotations

from agent.tools.docs import Document, DocumentVectorStore


class _FailingSession:
    def __init__(self) -> None:
        self.put_calls = 0
        self.get_calls = 0

    def put(self, *args, **kwargs):  # noqa: D401 - mimic requests interface
        self.put_calls += 1
        raise RuntimeError("offline")

    def get(self, *args, **kwargs):
        self.get_calls += 1
        raise RuntimeError("offline")


def test_vector_store_file_backend_roundtrip(tmp_path):
    file_path = tmp_path / "kb.json"
    store = DocumentVectorStore(backend="file", file_path=file_path)
    docs = [
        Document(content="LangGraph builds orchestrations", metadata={"id": "1"}),
        Document(content="Calendars coordinate events", metadata={"id": "2"}),
    ]
    store.replace_documents(docs)
    assert file_path.exists()

    reloaded = DocumentVectorStore(backend="file", file_path=file_path)
    matches = reloaded.similarity_search("orchestrations", k=1)
    assert matches and matches[0][0].metadata["id"] == "1"


def test_vector_store_cloud_backend_falls_back_to_local(tmp_path):
    fallback_path = tmp_path / "kb_backup.json"
    docs = [
        Document(content="Graph agent handles research", metadata={"id": "alpha"}),
        Document(content="Calendar agent schedules", metadata={"id": "beta"}),
    ]

    # First run: cloud calls fail, so the data should be written to fallback file.
    session = _FailingSession()
    store = DocumentVectorStore(
        backend="cloud",
        cloud_url="https://example.com/vector-store",
        fallback_path=fallback_path,
        session=session,
    )
    store.replace_documents(docs)
    assert fallback_path.exists()
    assert session.put_calls == 1

    # Second run: loading should consume the fallback file when cloud is unreachable.
    reloaded = DocumentVectorStore(
        backend="cloud",
        cloud_url="https://example.com/vector-store",
        fallback_path=fallback_path,
        session=_FailingSession(),
    )
    matches = reloaded.similarity_search("schedules", k=1)
    assert matches and matches[0][0].metadata["id"] == "beta"
