"""Planning agent that breaks requests into actionable steps."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from deepagents.tools import task as create_task, write_todos as generate_todos


@dataclass
class PlanStep:
    description: str
    depends_on: List[int]


def plan_tasks(task_description: str) -> List[object]:
    """使用 DeepAgents 进行任务自动分解与子智能体调度"""
    try:
        todos = generate_todos(task_description)
        print("[DeepAgents] 自动生成任务清单：")
        for i, todo in enumerate(todos, 1):
            print(f"{i}. {todo}")
        subagents = []
        for subtask in todos:
            sub = create_task(subtask)
            subagents.append(sub)
            print(f"子Agent已创建: {subtask}")
        return subagents
    except Exception as exc:
        print("DeepAgents 任务规划失败：", exc)
        return []


@dataclass
class PlannerAgent:
    def run(self, goal: str) -> List[PlanStep]:
        subagents = plan_tasks(goal)
        steps: List[PlanStep] = []
        if subagents:
            for index, sub in enumerate(subagents, start=1):
                description = getattr(sub, "description", None) or getattr(sub, "task", None)
                if not description:
                    description = str(sub)
                depends = [index - 1] if index > 1 else []
                steps.append(PlanStep(description=description, depends_on=depends))
        if not steps:
            steps.append(PlanStep(description=goal or "Clarify the request", depends_on=[]))
        return steps
