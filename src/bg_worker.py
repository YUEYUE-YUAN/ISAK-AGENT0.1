"""Background worker that pulls tasks from the queue and executes the graph."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict

from agent.graph import graph
from agent.queue.engine import AsyncTaskQueue


async def process_task(queue: AsyncTaskQueue, task_id: int, payload: Dict[str, str]) -> None:
    try:
        result = graph.invoke({"input": payload["input"]})
        await queue.complete(task_id, result)
    except Exception as exc:  # pragma: no cover - defensive
        await queue.fail(task_id, str(exc))


async def worker_loop(db_path: Path) -> None:
    queue = AsyncTaskQueue(db_path)
    try:
        while True:
            task = await queue.acquire()
            if task is None:
                await asyncio.sleep(0.2)
                continue
            await process_task(queue, int(task.id), task.payload)
    finally:
        await queue.close()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(worker_loop(Path("queue.db")))
