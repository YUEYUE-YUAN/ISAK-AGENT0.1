"""Planning agent that breaks requests into actionable steps."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class PlanStep:
    description: str
    depends_on: List[int]


@dataclass
class PlannerAgent:
    def run(self, goal: str) -> List[PlanStep]:
        chunks = [chunk.strip() for chunk in goal.replace("然后", ".").split(".") if chunk.strip()]
        steps: List[PlanStep] = []
        for index, chunk in enumerate(chunks, start=1):
            depends = [index - 1] if index > 1 else []
            steps.append(PlanStep(description=chunk, depends_on=depends))
        if not steps:
            steps.append(PlanStep(description=goal or "Clarify the request", depends_on=[]))
        return steps
