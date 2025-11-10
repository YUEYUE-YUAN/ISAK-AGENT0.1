"""Lightweight vector-backed project knowledge base."""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple

from agent.tools.docs import Document, DocumentVectorStore, load_documents_from_directory
from config import (
    KB_BACKEND,
    KB_CLOUD_FALLBACK_PATH,
    KB_CLOUD_TIMEOUT,
    KB_CLOUD_TOKEN,
    KB_CLOUD_URL,
    KB_FILE_PATH,
)


class ProjectKnowledgeBase:
    """Loads project documents into a vector index for retrieval."""

    def __init__(self, data_directory: Path) -> None:
        self.data_directory = data_directory
        backend = (KB_BACKEND or "memory").strip().lower()
        store_kwargs: dict = {}
        if backend == "file":
            store_kwargs["file_path"] = Path(KB_FILE_PATH)
        elif backend == "cloud":
            if not KB_CLOUD_URL:
                raise RuntimeError("选择 cloud 向量存储时必须提供 KB_CLOUD_URL")
            fallback = KB_CLOUD_FALLBACK_PATH or KB_FILE_PATH
            store_kwargs.update(
                {
                    "cloud_url": KB_CLOUD_URL,
                    "cloud_token": KB_CLOUD_TOKEN,
                    "cloud_timeout": KB_CLOUD_TIMEOUT,
                }
            )
            if fallback:
                store_kwargs["fallback_path"] = Path(fallback)
        self.store = DocumentVectorStore(backend=backend, **store_kwargs)

    def load(self, suffixes: Sequence[str] | None = None, *, replace: bool = True) -> None:
        docs = load_documents_from_directory(self.data_directory, suffixes)
        if not docs:
            return
        if replace:
            self.store.replace_documents(docs)
        else:
            self.store.add_documents(docs)

    def search(self, query: str, k: int = 3) -> List[Tuple[Document, float]]:
        return self.store.similarity_search(query, k=k)
