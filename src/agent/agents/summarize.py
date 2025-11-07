"""Summary sub-agent."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from tools import summarize_text


@dataclass
class SummarizeAgent:
    summariser: Callable[[str], str] = summarize_text

    def run(self, text: str) -> str:
        return self.summariser(text)
