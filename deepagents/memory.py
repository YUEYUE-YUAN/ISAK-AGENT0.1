"""Simplified persistent key-value store used by the shim Agent."""
from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Optional


class Store:
    """Tiny JSON-backed store emulating DeepAgents memory interface."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def _path(self, key: str) -> Path:
        safe = key.replace("/", "_")
        return self.root / f"{safe}.json"

    def save(self, key: str, value: str) -> None:
        path = self._path(key)
        with self._lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"value": value}, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, key: str, default: Optional[str] = "") -> str:
        path = self._path(key)
        if not path.exists():
            return default or ""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "value" in data:
                return str(data["value"])
        except Exception:
            return default or ""
        return default or ""

    # Compatibility helpers (optional but handy for tests)
    def clear(self, key: str) -> None:
        path = self._path(key)
        with self._lock:
            if path.exists():
                path.unlink()
