"""Advanced LangGraph pipeline with routing and specialist agents."""
from __future__ import annotations

from pathlib import Path

from langgraph.graph import StateGraph

from agent.agents.docgen import DocumentGenerationAgent
from agent.agents.planner import PlannerAgent
from agent.agents.research import ResearchAgent
from agent.agents.summarize import SummarizeAgent
from agent.memory.vector import ProjectKnowledgeBase
from agent.nodes import GraphComponents, build_executor_node, build_finalize_node, build_router_node
from agent.personas.loader import PersonaRegistry
from agent.routing import KnowledgeRouter

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

registry = PersonaRegistry(BASE_DIR / "agent" / "personas" / "registry.yaml")
registry.load()

knowledge_base = ProjectKnowledgeBase(DATA_DIR / "kb")
knowledge_base.load()

components = GraphComponents(
    router=KnowledgeRouter(registry),
    summarise=SummarizeAgent(),
    research=ResearchAgent(knowledge_base),
    planner=PlannerAgent(),
    docgen=DocumentGenerationAgent(OUTPUT_DIR),
)

builder = StateGraph(dict)
builder.add_node("route", build_router_node(components))
builder.add_node("execute", build_executor_node(components))
builder.add_node("finalize", build_finalize_node())

builder.set_entry_point("route")
builder.add_edge("route", "execute")
builder.add_edge("execute", "finalize")
builder.set_finish_point("finalize")

graph = builder.compile()

__all__ = ["graph", "components", "knowledge_base", "registry"]
