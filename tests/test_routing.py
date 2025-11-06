from __future__ import annotations

from agent.personas.loader import PersonaRegistry
from agent.routing import KnowledgeRouter


def test_router_selects_persona(tmp_path):
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        """
- id: generalist
  name: Gen
  description: d
  style: s
- id: researcher
  name: Res
  description: d
  style: s
        """,
        encoding="utf-8",
    )
    registry = PersonaRegistry(registry_path)
    registry.load()
    router = KnowledgeRouter(registry)
    decision = router.select("需要research")
    assert decision.route == "research"
    assert decision.persona.id == "researcher"
