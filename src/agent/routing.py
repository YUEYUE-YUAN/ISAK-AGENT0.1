"""Routing logic for delegating tasks to specialised agents."""
from __future__ import annotations

from dataclasses import dataclass

from agent.personas.loader import Persona, PersonaRegistry


@dataclass
class RoutingDecision:
    persona: Persona
    route: str
    confidence: float


class KnowledgeRouter:
    def __init__(self, registry: PersonaRegistry) -> None:
        self.registry = registry

    def select(self, user_input: str) -> RoutingDecision:
        lowered = user_input.lower()
        if any(keyword in lowered for keyword in ["总结", "summary", "总结一下"]):
            persona = self.registry.get("generalist")
            return RoutingDecision(persona=persona, route="summarise", confidence=0.8)
        if any(keyword in lowered for keyword in ["调研", "research", "资料"]):
            persona = self.registry.get("researcher")
            return RoutingDecision(persona=persona, route="research", confidence=0.7)
        if any(keyword in lowered for keyword in ["计划", "规划", "plan"]):
            persona = self.registry.get("planner")
            return RoutingDecision(persona=persona, route="plan", confidence=0.75)
        persona = self.registry.get("generalist")
        return RoutingDecision(persona=persona, route="chat", confidence=0.6)
