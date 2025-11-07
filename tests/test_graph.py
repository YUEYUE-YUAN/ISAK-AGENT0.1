from __future__ import annotations

import types

import config
import memory
from agent import graph as agent_graph


class DummyCompletion:
    def __init__(self, content: str) -> None:
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=content))]


def stub_completion(text: str):
    def _create(*_, **__):
        return DummyCompletion(text)

    return _create


def test_graph_routes_to_summary(monkeypatch):
    memory.clear_history()
    monkeypatch.setattr(agent_graph.components.summarise, "summariser", lambda text: "摘要:" + text)
    result = agent_graph.graph.invoke({"input": "请帮我summary 这一段文字"})
    assert result["response"].startswith("摘要:")
    assert result["metadata"]["route_confidence"] > 0


def test_graph_chat_uses_openai(monkeypatch):
    memory.clear_history()
    monkeypatch.setattr(
        config.client.chat.completions,
        "create",
        stub_completion("模型回复"),
    )
    result = agent_graph.graph.invoke({"input": "普通对话"})
    assert result["response"] == "模型回复"
    assert result["artifacts"]["model"] == config.DEFAULT_MODEL


def test_graph_research(monkeypatch):
    memory.clear_history()
    monkeypatch.setattr(agent_graph.components.research.knowledge_base.store, "similarity_search", lambda query, k=3: [])
    findings = agent_graph.components.research.run("LangGraph 是什么？")
    assert isinstance(findings, list)
