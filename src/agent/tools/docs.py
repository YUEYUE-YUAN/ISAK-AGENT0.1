"""Utilities for loading documents and running vector similarity search."""
from __future__ import annotations

import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:  # pragma: no cover - optional dependency guard
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore


logger = logging.getLogger(__name__)


_TOKEN_RE = re.compile(r"[A-Za-z\d']+")


@dataclass
class Document:
    """Simple container describing a knowledge base document."""

    content: str
    metadata: Dict[str, str] = field(default_factory=dict)


def _tokenize(text: str) -> List[str]:
    tokens: List[str] = []
    for token in _TOKEN_RE.findall(text):
        lowered = token.lower()
        tokens.append(lowered)
        if lowered.endswith("s") and len(lowered) > 3:
            tokens.append(lowered[:-1])
    return tokens


def _build_vector(tokens: Sequence[str], vocabulary: Dict[str, int]) -> Dict[int, float]:
    counts = Counter(tokens)
    vector: Dict[int, float] = {}
    total = sum(counts.values()) or 1
    for token, count in counts.items():
        if token not in vocabulary:
            continue
        vector[vocabulary[token]] = float(count) / float(total)
    return vector


def _cosine_similarity(vec_a: Dict[int, float], vec_b: Dict[int, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(value * vec_b.get(index, 0.0) for index, value in vec_a.items())
    norm_a = sqrt(sum(value * value for value in vec_a.values()))
    norm_b = sqrt(sum(value * value for value in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class DocumentVectorStore:
    """Lightweight vector store with optional local/remote persistence."""

    def __init__(
        self,
        backend: str = "memory",
        *,
        file_path: Optional[Path] = None,
        cloud_url: Optional[str] = None,
        cloud_token: Optional[str] = None,
        cloud_timeout: float = 5.0,
        fallback_path: Optional[Path] = None,
        session: Any | None = None,
    ) -> None:
        self.backend = (backend or "memory").strip().lower()
        self._documents: List[Document] = []
        self._vocabulary: Dict[str, int] = {}
        self._matrix: List[Dict[int, float]] = []
        self._lock = RLock()

        self._file_path = file_path
        if self._file_path:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

        self._cloud_url = cloud_url.rstrip("/") if cloud_url else None
        self._cloud_token = cloud_token
        self._cloud_timeout = cloud_timeout
        self._fallback_path = fallback_path
        if self._fallback_path:
            self._fallback_path.parent.mkdir(parents=True, exist_ok=True)

        self._session = session

        if self.backend == "file" and not self._file_path:
            raise ValueError("file backend requires file_path")

        if self.backend == "cloud":
            if not self._cloud_url:
                raise ValueError("cloud backend requires cloud_url")
            if self._session is None:
                if requests is None:
                    raise RuntimeError(
                        "使用 cloud 向量存储需要安装 requests 包 (pip install requests)。"
                    )
                self._session = requests.Session()

        self._load_from_backend()

    @property
    def documents(self) -> Sequence[Document]:
        with self._lock:
            return tuple(self._documents)

    def add_documents(self, docs: Iterable[Document]) -> None:
        new_docs = [doc for doc in docs]
        if not new_docs:
            return
        with self._lock:
            self._documents.extend(new_docs)
            self._rebuild_vectors()
            self._persist_if_needed()

    def replace_documents(self, docs: Iterable[Document]) -> None:
        with self._lock:
            self._documents = list(docs)
            self._rebuild_vectors()
            self._persist_if_needed()

    def similarity_search(self, query: str, k: int = 3) -> List[Tuple[Document, float]]:
        if not query:
            return []
        with self._lock:
            if not self._matrix:
                return []
            query_vector = _build_vector(_tokenize(query), self._vocabulary)
            if not query_vector:
                return []
            scores = [
                _cosine_similarity(doc_vector, query_vector) for doc_vector in self._matrix
            ]
            sorted_pairs = sorted(
                zip(self._documents, scores), key=lambda item: item[1], reverse=True
            )
            return sorted_pairs[:k]

    def _rebuild_vectors(self) -> None:
        self._vocabulary = {}
        for doc in self._documents:
            for token in _tokenize(doc.content):
                if token not in self._vocabulary:
                    self._vocabulary[token] = len(self._vocabulary)
        if not self._documents:
            self._matrix = []
            return
        self._matrix = [
            _build_vector(_tokenize(doc.content), self._vocabulary) for doc in self._documents
        ]

    def _serialize_documents(self) -> List[Dict[str, Any]]:
        return [
            {"content": doc.content, "metadata": dict(doc.metadata)}
            for doc in self._documents
        ]

    def _deserialize_documents(self, payload: Iterable[Any]) -> List[Document]:
        documents: List[Document] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, str):
                continue
            metadata_raw = item.get("metadata", {})
            metadata: Dict[str, str] = {}
            if isinstance(metadata_raw, dict):
                metadata = {str(key): str(value) for key, value in metadata_raw.items()}
            documents.append(Document(content=content, metadata=metadata))
        return documents

    def _persist_if_needed(self) -> None:
        payload = self._serialize_documents()
        if self.backend == "file" and self._file_path:
            self._write_file(self._file_path, payload)
        elif self.backend == "cloud" and self._cloud_url:
            self._persist_to_cloud(payload)

    def _write_file(self, path: Path, payload: List[Dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _read_file(self, path: Path) -> List[Document]:
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("加载向量知识库失败，将忽略该文件: %s", exc)
            return []
        if isinstance(data, list):
            return self._deserialize_documents(data)
        return []

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._cloud_token:
            headers["Authorization"] = f"Bearer {self._cloud_token}"
        return headers

    def _persist_to_cloud(self, payload: List[Dict[str, Any]]) -> None:
        if not self._session:
            return
        try:
            response = self._session.put(
                self._cloud_url,
                json=payload,
                headers=self._headers(),
                timeout=self._cloud_timeout,
            )
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - network failure fallback
            self._handle_cloud_failure(exc)
        finally:
            if self._fallback_path:
                self._write_file(self._fallback_path, payload)

    def _load_from_cloud(self) -> List[Document]:
        if not self._session or not self._cloud_url:
            return []
        try:
            response = self._session.get(
                self._cloud_url,
                headers=self._headers(),
                timeout=self._cloud_timeout,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return self._deserialize_documents(data)
        except Exception as exc:  # pragma: no cover - network failure fallback
            self._handle_cloud_failure(exc)
        return []

    def _load_from_backend(self) -> None:
        documents: List[Document] = []
        if self.backend == "file" and self._file_path:
            documents = self._read_file(self._file_path)
        elif self.backend == "cloud":
            documents = self._load_from_cloud()
            if not documents and self._fallback_path:
                documents = self._read_file(self._fallback_path)
        if documents:
            self._documents = documents
            self._rebuild_vectors()

    def _handle_cloud_failure(self, exc: Exception) -> None:
        logger.warning("云端向量知识库同步失败：%s", exc)


def load_documents_from_directory(directory: Path, suffixes: Optional[Sequence[str]] = None) -> List[Document]:
    suffixes = tuple(suffixes or (".txt", ".md"))
    if not directory.exists():
        return []
    documents: List[Document] = []
    for path in directory.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")
        documents.append(Document(content=content, metadata={"path": str(path)}))
    return documents
