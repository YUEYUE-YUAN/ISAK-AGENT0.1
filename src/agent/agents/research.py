"""Research agent combining internal knowledge and offline web search."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from agent.memory.vector import ProjectKnowledgeBase
from agent.tools.web import search_web


@dataclass
class ResearchAgent:
    knowledge_base: ProjectKnowledgeBase

    def run(self, query: str, web_k: int = 2, kb_k: int = 2) -> List[dict]:
        kb_results = [
            {"source": doc.metadata.get("path", "kb"), "snippet": doc.content, "score": score}
            for doc, score in self.knowledge_base.search(query, k=kb_k)
        ]
        web_results = search_web(query, k=web_k)
        return kb_results + web_results
