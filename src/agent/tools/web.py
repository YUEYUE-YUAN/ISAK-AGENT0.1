"""Simple offline-friendly web search shim."""
from __future__ import annotations

from typing import List

from .docs import Document, DocumentVectorStore


_DEFAULT_CORPUS = [
    Document(
        content="LangGraph orchestrates tool usage by modeling the workflow as a graph.",
        metadata={"source": "langgraph"},
    ),
    Document(
        content="FAISS and Chroma are common vector stores used for retrieval augmented generation.",
        metadata={"source": "rag"},
    ),
    Document(
        content="Task queues allow delegating long running jobs to background workers.",
        metadata={"source": "queues"},
    ),
]


class OfflineWebSearch:
    def __init__(self) -> None:
        self._store = DocumentVectorStore()
        self._store.replace_documents(_DEFAULT_CORPUS)

    def search(self, query: str, k: int = 3) -> List[dict]:
        results = []
        for doc, score in self._store.similarity_search(query, k=k):
            results.append({"snippet": doc.content, "source": doc.metadata.get("source", "local"), "score": score})
        return results


_default_search = OfflineWebSearch()


def search_web(query: str, k: int = 3) -> List[dict]:
    """Perform a lightweight similarity search against the bundled corpus."""

    if not query:
        return []
    return _default_search.search(query, k=k)
