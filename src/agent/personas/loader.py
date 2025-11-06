"""Persona registry loader."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class Persona:
    id: str
    name: str
    description: str
    style: str


class PersonaRegistry:
    def __init__(self, registry_path: Path) -> None:
        self.registry_path = registry_path
        self._personas: Dict[str, Persona] = {}

    def load(self) -> None:
        if not self.registry_path.exists():
            raise FileNotFoundError(self.registry_path)
        raw_text = self.registry_path.read_text(encoding="utf-8")
        data = _parse_registry(raw_text)
        self._personas = {item["id"]: Persona(**item) for item in data}

    def get(self, persona_id: str) -> Persona:
        return self._personas[persona_id]

    def find(self, persona_id: str) -> Optional[Persona]:
        return self._personas.get(persona_id)

    def all(self) -> List[Persona]:
        return list(self._personas.values())

    def __iter__(self) -> Iterable[Persona]:  # pragma: no cover
        yield from self._personas.values()


def _parse_registry(text: str) -> List[Dict[str, str]]:
    personas: List[Dict[str, str]] = []
    current: Dict[str, str] | None = None
    collecting_key: Optional[str] = None
    collecting_lines: List[str] = []

    def flush_block() -> None:
        nonlocal collecting_key, collecting_lines, current
        if collecting_key and current is not None:
            current[collecting_key] = "\n".join(collecting_lines).strip()
        collecting_key = None
        collecting_lines = []

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current is not None:
                flush_block()
                personas.append(current)
            current = {}
            stripped = stripped[2:]
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value == "|" or value == "":
                flush_block()
                collecting_key = key
                collecting_lines = []
            else:
                if current is None:
                    current = {}
                current[key] = value
                collecting_key = None
                collecting_lines = []
        elif collecting_key is not None:
            collecting_lines.append(stripped)
    if current is not None:
        flush_block()
        personas.append(current)
    return personas
