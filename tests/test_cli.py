from __future__ import annotations

import types
from datetime import datetime, timedelta
from pathlib import Path

import main
import memory
from agent.tools.calendar import CalendarClient
from agent.tools.tasks import TaskManager


def test_plan_command(monkeypatch, tmp_path):
    steps = [types.SimpleNamespace(description="Step A", depends_on=[])]
    monkeypatch.setattr(main.components, "planner", types.SimpleNamespace(run=lambda goal: steps))
    response, cont = main.handle_user_input("/plan 完成发布")
    assert "Step A" in response
    assert cont


def test_research_command(monkeypatch):
    findings = [
        {"snippet": "doc", "source": "kb", "score": 0.9},
        {"snippet": "web", "source": "web", "score": 0.8},
    ]
    monkeypatch.setattr(main.components, "research", types.SimpleNamespace(run=lambda q: findings))
    response, cont = main.handle_user_input("/research LangGraph")
    assert "doc" in response and "web" in response
    assert cont


def test_report_command(monkeypatch, tmp_path):
    destination = tmp_path / "report.pdf"
    monkeypatch.setattr(main.components, "docgen", types.SimpleNamespace(create_report=lambda name, body: destination))
    response, cont = main.handle_user_input("/report 内容")
    assert str(destination) in response
    assert cont


def test_schedule_and_agenda(tmp_path):
    if hasattr(main.calendar_client, "close"):
        main.calendar_client.close()
    main.calendar_client = CalendarClient(tmp_path / "calendar.db")
    start = datetime.now() + timedelta(days=1)
    end = start + timedelta(hours=1)
    cmd = f"/schedule 团队会议; {start.strftime('%Y-%m-%d %H:%M')}; {end.strftime('%Y-%m-%d %H:%M')}; 会议室A"
    response, cont = main.handle_user_input(cmd)
    assert "已添加日程" in response
    assert cont
    agenda, _ = main.handle_user_input("/agenda 30")
    assert "团队会议" in agenda


def test_task_commands(tmp_path):
    main.task_manager = TaskManager(tmp_path / "tasks.json")
    due = datetime.now() + timedelta(days=2)
    add_response, cont = main.handle_user_input(
        f"/task add 撰写周报; {due.strftime('%Y-%m-%d %H:%M')}; 包含重点"
    )
    assert "已添加任务" in add_response and cont
    list_response, _ = main.handle_user_input("/tasks")
    assert "撰写周报" in list_response
    done_response, _ = main.handle_user_input("/task done 1")
    assert "任务 1" in done_response


def test_remind_combines_tasks_and_events(tmp_path):
    if hasattr(main.calendar_client, "close"):
        main.calendar_client.close()
    main.calendar_client = CalendarClient(tmp_path / "calendar.db")
    main.task_manager = TaskManager(tmp_path / "tasks.json")
    start = datetime.now() + timedelta(days=1)
    end = start + timedelta(hours=1)
    main.handle_user_input(f"/schedule Demo; {start.strftime('%Y-%m-%d %H:%M')}; {end.strftime('%Y-%m-%d %H:%M')}")
    due = start - timedelta(hours=1)
    main.handle_user_input(f"/task add 准备演示; {due.strftime('%Y-%m-%d %H:%M')}")
    remind_response, _ = main.handle_user_input("/remind 2")
    assert "Demo" in remind_response
    assert "准备演示" in remind_response


def test_conversation_flow(monkeypatch):
    memory.clear_history()
    saved = []
    monkeypatch.setattr(main, "save_message", lambda role, content: saved.append((role, content)))
    monkeypatch.setattr(main, "graph", types.SimpleNamespace(invoke=lambda payload: {"response": "OK"}))
    response, cont = main.handle_user_input("你好")
    assert response == "OK"
    assert saved == [("user", "你好"), ("bot", "OK")]
    assert cont
