"""Reusable LangGraph nodes for the advanced agent."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, TypedDict

from config import DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE, client
from memory import get_recent_history
from agent.agents.docgen import DocumentGenerationAgent
from agent.agents.planner import PlannerAgent
from agent.agents.research import ResearchAgent
from agent.agents.summarize import SummarizeAgent
from agent.routing import KnowledgeRouter


class GraphState(TypedDict, total=False):
    input: str
    route: str
    persona_id: str
    persona_style: str
    response: str
    metadata: Dict[str, Any]
    artifacts: Dict[str, Any]


@dataclass
class GraphComponents:
    router: KnowledgeRouter
    summarise: SummarizeAgent
    research: ResearchAgent
    planner: PlannerAgent
    docgen: DocumentGenerationAgent


def build_router_node(components: GraphComponents):
    def node(state: GraphState) -> GraphState:
        decision = components.router.select(state["input"])
        metadata = state.get("metadata", {})
        metadata = {**metadata, "route_confidence": decision.confidence, "persona": decision.persona.id}
        return {
            **state,
            "route": decision.route,
            "persona_id": decision.persona.id,
            "persona_style": decision.persona.style,
            "metadata": metadata,
        }

    return node


def _call_chat_completion(state: GraphState) -> Dict[str, Any]:
    history_messages = [
        {"role": item["role"], "content": item["content"]} for item in get_recent_history()
    ]
    if not history_messages or history_messages[-1]["role"] != "user":
        history_messages.append({"role": "user", "content": state["input"]})
    messages = []
    persona_style = state.get("persona_style")
    if persona_style:
        messages.append({"role": "system", "content": persona_style})
    messages.extend(history_messages)
    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )
    content = completion.choices[0].message.content.strip()
    return {"response": content, "artifacts": {"model": DEFAULT_MODEL}}


def build_executor_node(components: GraphComponents):
    def node(state: GraphState) -> GraphState:
        route = state.get("route", "chat")
        if route == "summarise":
            summary = components.summarise.run(state["input"])
            return {**state, "response": summary, "artifacts": {"summary": summary}}
        if route == "research":
            results = components.research.run(state["input"])
            formatted = "\n".join(
                f"- ({item['score']:.2f}) {item['snippet']} [{item['source']}]" for item in results
            )
            return {**state, "response": formatted or "未找到相关资料。", "artifacts": {"results": results}}
        if route == "plan":
            steps = components.planner.run(state["input"])
            formatted = "\n".join(
                f"步骤 {idx}. {step.description}" + (f" (依赖 {step.depends_on})" if step.depends_on else "")
                for idx, step in enumerate(steps, start=1)
            )
            return {**state, "response": formatted, "artifacts": {"plan": [step.__dict__ for step in steps]}}
        if route == "docgen":
            report_path = components.docgen.create_report("auto_report", state["input"])
            return {**state, "response": f"生成报告: {report_path}", "artifacts": {"report_path": str(report_path)}}
        return {**state, **_call_chat_completion(state)}

    return node


def build_finalize_node():
    def node(state: GraphState) -> GraphState:
        response = state.get("response", "")
        metadata = state.get("metadata", {})
        metadata.setdefault("tokens", len(response))
        return {**state, "response": response, "metadata": metadata}

    return node
