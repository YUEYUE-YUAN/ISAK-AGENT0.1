"""Async example client for the LangGraph agent."""
from __future__ import annotations

import asyncio

from agent.graph import graph


async def main() -> None:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, graph.invoke, {"input": "帮我规划一次发布流程"})
    print(result["response"])


if __name__ == "__main__":
    asyncio.run(main())
