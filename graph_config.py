"""Compatibility wrapper around the advanced graph implementation."""
from __future__ import annotations

from agent.graph import graph as _advanced_graph


def generate_response(state):
    user_input = state.get("input", "")
    if not user_input:
        return {"response": "请提供输入内容。"}
    result = _advanced_graph.invoke({"input": user_input})
    return {"response": result.get("response", ""), "metadata": result.get("metadata", {})}


graph = _advanced_graph


if __name__ == "__main__":  # pragma: no cover
    input_text = input("User: ")
    result = graph.invoke({"input": input_text})
    print("Bot:", result.get("response"))
