"""Test fixtures and dependency stubs for the LangGraph project."""
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if "dotenv" not in sys.modules:
    dotenv_module = types.ModuleType("dotenv")

    def load_dotenv():  # pragma: no cover
        return None

    dotenv_module.load_dotenv = load_dotenv
    sys.modules["dotenv"] = dotenv_module


if "langgraph" not in sys.modules:
    langgraph_module = types.ModuleType("langgraph")
    langgraph_graph_module = types.ModuleType("langgraph.graph")

    class DummyStateGraph:
        def __init__(self, _state_type=None):
            self.nodes = {}
            self.entry = None
            self.finish = None
            self.edges = {}

        def add_node(self, name, func):
            self.nodes[name] = func

        def set_entry_point(self, name):
            self.entry = name

        def set_finish_point(self, name):
            self.finish = name

        def add_edge(self, start, end):
            self.edges[start] = end

        def compile(self):
            nodes = self.nodes
            entry = self.entry
            finish = self.finish
            edges = self.edges

            class DummyGraph:
                def invoke(self, state):
                    current = entry
                    data = dict(state)
                    visited = set()
                    while current is not None:
                        visited.add(current)
                        update = nodes[current](data)
                        if update:
                            data.update(update)
                        if current == finish:
                            break
                        current = edges.get(current)
                        if current in visited:
                            break
                    return data

            return DummyGraph()

    langgraph_graph_module.StateGraph = DummyStateGraph
    langgraph_module.graph = langgraph_graph_module
    sys.modules["langgraph"] = langgraph_module
    sys.modules["langgraph.graph"] = langgraph_graph_module


if "openai" not in sys.modules:
    openai_module = types.ModuleType("openai")

    class DummyChatCompletions:
        def __init__(self):
            self._response_text = ""

        def create(self, *_, **__):  # pragma: no cover - patched in tests
            raise NotImplementedError

    class DummyChat:
        def __init__(self):
            self.completions = DummyChatCompletions()

    class DummyOpenAI:
        def __init__(self, *_, **__):
            self.chat = DummyChat()

    openai_module.OpenAI = DummyOpenAI
    sys.modules["openai"] = openai_module