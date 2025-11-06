from __future__ import annotations

import types

import graph_config


def test_generate_response_delegates(monkeypatch):
    dummy = types.SimpleNamespace(invoke=lambda payload: {"response": "ok", "metadata": {"route": "chat"}})
    monkeypatch.setattr(graph_config, "_advanced_graph", dummy)
    monkeypatch.setattr(graph_config, "graph", dummy)
    result = graph_config.generate_response({"input": "hi"})
    assert result["response"] == "ok"
    assert result["metadata"]["route"] == "chat"


def test_generate_response_requires_input():
    assert graph_config.generate_response({}) == {"response": "请提供输入内容。"}
