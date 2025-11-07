"""Configurable conversation history backends."""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Dict, List, Optional

from deepagents.tools import edit_file, ls, read_file, write_file

try:  # pragma: no cover - optional dependency
    import requests
except ImportError:  # pragma: no cover
    class _RequestsStub:
        class Session:  # type: ignore[override]
            def __init__(self, *args, **kwargs) -> None:
                raise RuntimeError(
                    "使用 cloud 历史存储需要安装 requests 包 (pip install requests)。"
                )

    requests = _RequestsStub()  # type: ignore

from config import (
    HISTORY_BACKEND,
    HISTORY_CLOUD_FALLBACK_PATH,
    HISTORY_CLOUD_TIMEOUT,
    HISTORY_CLOUD_TOKEN,
    HISTORY_CLOUD_URL,
    HISTORY_FILE_PATH,
)

logger = logging.getLogger(__name__)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_entry(entry: Dict[str, str]) -> Dict[str, str]:
    role = entry.get("role", "")
    content = entry.get("content", "")
    timestamp = entry.get("timestamp") or _timestamp()
    return {"role": role, "content": content, "timestamp": timestamp}


class BaseHistoryStore(ABC):
    """Protocol for conversation history storage backends."""

    @abstractmethod
    def save_message(self, role: str, content: str) -> None:
        ...

    @abstractmethod
    def get_history(self) -> List[Dict[str, str]]:
        ...

    @abstractmethod
    def clear_history(self) -> None:
        ...

    def get_recent_history(self, n: int = 10) -> List[Dict[str, str]]:
        history = self.get_history()
        if n <= 0:
            return []
        return history[-n:]


class InMemoryHistoryStore(BaseHistoryStore):
    """Simple in-memory list suitable for tests or ephemeral runs."""

    def __init__(self) -> None:
        self._history: List[Dict[str, str]] = []
        self._lock = RLock()

    def save_message(self, role: str, content: str) -> None:
        with self._lock:
            self._history.append(_normalize_entry({"role": role, "content": content}))

    def get_history(self) -> List[Dict[str, str]]:
        with self._lock:
            return list(self._history)

    def clear_history(self) -> None:
        with self._lock:
            self._history.clear()


class LocalFileHistoryStore(BaseHistoryStore):
    """Persists history to a JSON file on disk."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._history: List[Dict[str, str]] = self._load()

    def _load(self) -> List[Dict[str, str]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [_normalize_entry(item) for item in data if isinstance(item, dict)]
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("加载历史记录失败，将创建新的文件: %s", exc)
        return []

    def _flush(self) -> None:
        self.path.write_text(json.dumps(self._history, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_message(self, role: str, content: str) -> None:
        with self._lock:
            entry = _normalize_entry({"role": role, "content": content})
            self._history.append(entry)
            self._flush()

    def get_history(self) -> List[Dict[str, str]]:
        with self._lock:
            return list(self._history)

    def clear_history(self) -> None:
        with self._lock:
            self._history.clear()
            if self.path.exists():
                self.path.unlink()


class CloudHistoryStore(BaseHistoryStore):
    """Stores history by calling a remote HTTP endpoint with local fallback."""

    def __init__(
        self,
        endpoint: str,
        *,
        token: Optional[str] = None,
        fallback: Optional[BaseHistoryStore] = None,
        timeout: float = 5.0,
    ) -> None:
        if not endpoint:
            raise ValueError("endpoint is required for CloudHistoryStore")
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._session = requests.Session()
        self._fallback = fallback or InMemoryHistoryStore()

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_remote_failure(self, exc: Exception) -> None:
        logger.warning("云端同步失败，使用回退存储：%s", exc)

    def save_message(self, role: str, content: str) -> None:
        entry = _normalize_entry({"role": role, "content": content})
        try:
            response = self._session.post(
                self.endpoint,
                json=entry,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - network failure fallback
            self._handle_remote_failure(exc)
        finally:
            if self._fallback:
                self._fallback.save_message(role, content)

    def get_history(self) -> List[Dict[str, str]]:
        try:
            response = self._session.get(
                self.endpoint,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return [_normalize_entry(item) for item in data if isinstance(item, dict)]
        except Exception as exc:  # pragma: no cover - network failure fallback
            self._handle_remote_failure(exc)
        return self._fallback.get_history() if self._fallback else []

    def clear_history(self) -> None:
        try:
            response = self._session.delete(
                self.endpoint,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - network failure fallback
            self._handle_remote_failure(exc)
        finally:
            if self._fallback:
                self._fallback.clear_history()


class DeepAgentFileMemory:
    def list_files(self, path: str = "."):
        return ls(path)

    def read(self, path: str):
        return read_file(path)

    def write(self, path: str, content: str):
        write_file(path, content)

    def edit(self, path: str, new_text: str):
        edit_file(path, new_text)


def _create_history_store() -> BaseHistoryStore:
    backend = (HISTORY_BACKEND or "memory").strip().lower()
    if backend == "file":
        return LocalFileHistoryStore(Path(HISTORY_FILE_PATH))
    if backend == "cloud":
        if not HISTORY_CLOUD_URL:
            raise RuntimeError("选择 cloud 历史存储时必须提供 HISTORY_CLOUD_URL")
        fallback_store: Optional[BaseHistoryStore] = None
        fallback_path = HISTORY_CLOUD_FALLBACK_PATH or HISTORY_FILE_PATH
        if fallback_path:
            fallback_store = LocalFileHistoryStore(Path(fallback_path))
        return CloudHistoryStore(
            HISTORY_CLOUD_URL,
            token=HISTORY_CLOUD_TOKEN,
            fallback=fallback_store,
            timeout=HISTORY_CLOUD_TIMEOUT,
        )
    return InMemoryHistoryStore()


_history_store: BaseHistoryStore = _create_history_store()


def set_history_store(store: BaseHistoryStore) -> None:
    global _history_store
    _history_store = store


def get_history_store() -> BaseHistoryStore:
    return _history_store


def save_message(role: str, content: str) -> None:
    _history_store.save_message(role, content)


def get_history() -> List[Dict[str, str]]:
    return _history_store.get_history()


def clear_history() -> None:
    _history_store.clear_history()


def get_recent_history(n: int = 10) -> List[Dict[str, str]]:
    return _history_store.get_recent_history(n)


__all__ = [
    "BaseHistoryStore",
    "InMemoryHistoryStore",
    "LocalFileHistoryStore",
    "CloudHistoryStore",
    "save_message",
    "get_history",
    "clear_history",
    "get_recent_history",
    "set_history_store",
    "get_history_store",
    "DeepAgentFileMemory",
]
