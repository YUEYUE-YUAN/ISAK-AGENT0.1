import logging
from datetime import timedelta
from pathlib import Path
from typing import Tuple

from config import CALENDAR_DB_PATH, DEBUG, LOG_LEVEL, TASKS_FILE_PATH
from agent.graph import components
from graph_config import graph
from memory import clear_history, get_history, save_message
from tools import (
    CalendarClient,
    CalendarEvent,
    TaskManager,
    TaskStatus,
    format_event,
    parse_datetime,
    parse_due,
    summarize_text,
    web_search,
)

# 配置日志
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)

calendar_client = CalendarClient(Path(CALENDAR_DB_PATH))
task_manager = TaskManager(Path(TASKS_FILE_PATH))


def handle_user_input(user_input: str) -> Tuple[str, bool]:
    """处理用户输入并返回响应文本以及是否继续对话。"""

    normalized = user_input.strip()
    if not normalized:
        return "请输入内容或输入 'exit' 退出。", True

    lowered = normalized.lower()
    if lowered in {"exit", "quit"}:
        return "再见！", False

    if lowered == "/history":
        history = get_history()
        if not history:
            return "暂无历史记录。", True
        formatted = "\n".join(
            f"{item['role']}: {item['content']}" for item in history
        )
        return formatted, True

    if lowered == "/clear":
        clear_history()
        return "已清空对话历史。", True

    command, _, argument = normalized.partition(" ")
    command_lower = command.lower()

    if command_lower == "/summarize":
        text_to_summarize = argument.strip()
        if not text_to_summarize:
            return "请提供需要摘要的内容。", True
        summary = summarize_text(text_to_summarize)
        return summary, True

    if command_lower == "/search":
        query = argument.strip()
        if not query:
            return "请提供搜索关键词。", True
        results = web_search(query)
        if not results:
            return "未找到相关结果。", True
        formatted_results = "\n".join(
            f"{idx + 1}. {item}" for idx, item in enumerate(results)
        )
        return formatted_results, True

    if command_lower == "/plan":
        goal = argument.strip()
        if not goal:
            return "请描述需要规划的目标。", True
        steps = components.planner.run(goal)
        formatted = "\n".join(
            f"步骤 {idx + 1}. {step.description}" + (f" (依赖 {step.depends_on})" if step.depends_on else "")
            for idx, step in enumerate(steps)
        )
        return formatted, True

    if command_lower == "/research":
        research_query = argument.strip()
        if not research_query:
            return "请提供需要调研的问题。", True
        findings = components.research.run(research_query)
        if not findings:
            return "未检索到相关资料。", True
        formatted = "\n".join(
            f"- {item['snippet']} (来源: {item.get('source', 'local')}, 相关度: {item.get('score', 0):.2f})"
            for item in findings
        )
        return formatted, True

    if command_lower == "/report":
        body = argument.strip()
        if not body:
            return "请提供报告内容。", True
        report_path = components.docgen.create_report("cli_report", body)
        return f"报告已生成：{report_path}", True

    if command_lower == "/schedule":
        parts = [part.strip() for part in argument.split(";") if part.strip()]
        if len(parts) < 3:
            return (
                "用法: /schedule 标题; 开始时间(YYYY-MM-DD HH:MM); 结束时间(YYYY-MM-DD HH:MM); [地点]; [描述]",
                True,
            )
        title, start_raw, end_raw, *rest = parts
        try:
            start_dt = parse_datetime(start_raw)
            end_dt = parse_datetime(end_raw)
        except ValueError as exc:
            return str(exc), True
        if end_dt <= start_dt:
            return "结束时间必须晚于开始时间。", True
        location = rest[0] if rest else None
        description = rest[1] if len(rest) > 1 else None
        event = CalendarEvent(
            title=title,
            start=start_dt,
            end=end_dt,
            location=location,
            description=description,
        )
        event_id = calendar_client.add_event(event)
        return f"已添加日程 (ID {event_id}): {format_event(event)}", True

    if command_lower == "/agenda":
        days = 7
        if argument.strip():
            try:
                days = max(1, int(argument.strip()))
            except ValueError:
                return "请输入数字表示需要查看的天数。", True
        events = calendar_client.upcoming(timedelta(days=days))
        if not events:
            return f"未来 {days} 天内暂无日程。", True
        formatted_events = "\n".join(f"- {format_event(event)}" for event in events)
        return formatted_events, True

    if command_lower == "/task":
        args = argument.strip()
        if not args:
            return "用法: /task add 标题; [截止时间]; [备注] 或 /task done <任务ID>", True
        subcommand, _, payload = args.partition(" ")
        sub = subcommand.lower()
        if sub == "add":
            pieces = [part.strip() for part in payload.split(";") if part.strip()]
            if not pieces:
                return "请提供任务标题。", True
            title = pieces[0]
            due_dt = None
            notes = None
            if len(pieces) > 1:
                try:
                    due_dt = parse_due(pieces[1])
                except ValueError as exc:
                    return str(exc), True
            if len(pieces) > 2:
                notes = pieces[2]
            task = task_manager.add_task(title, due=due_dt, notes=notes)
            due_text = (
                f"，截止 {task.due_datetime().strftime('%Y-%m-%d %H:%M')}"
                if task.due
                else ""
            )
            return f"已添加任务 (ID {task.id}){due_text}。", True
        if sub == "done":
            task_id_raw = payload.strip()
            if not task_id_raw:
                return "请提供任务 ID。", True
            try:
                task_id = int(task_id_raw)
            except ValueError:
                return "任务 ID 需要是数字。", True
            task = task_manager.complete_task(task_id)
            if not task:
                return "未找到对应的任务 ID。", True
            if task.status == TaskStatus.COMPLETED:
                return f"任务 {task_id} 已标记完成。", True
        return "未知的 /task 子命令，请使用 add 或 done。", True

    if command_lower == "/tasks":
        include_completed = argument.strip().lower() == "all"
        tasks = task_manager.list_tasks(include_completed=include_completed)
        if not tasks:
            return "暂无任务。", True
        lines = []
        for task in tasks:
            status = "✅" if task.is_completed() else "⏳"
            due = (
                task.due_datetime().strftime("%Y-%m-%d %H:%M")
                if task.due
                else "未设置"
            )
            notes = f" | 备注: {task.notes}" if task.notes else ""
            lines.append(f"{status} #{task.id} {task.title} (截止: {due}){notes}")
        if not include_completed:
            lines.append("提示: 使用 /tasks all 查看已完成任务。")
        return "\n".join(lines), True

    if command_lower == "/remind":
        days = 1
        if argument.strip():
            try:
                days = max(1, int(argument.strip()))
            except ValueError:
                return "请输入数字表示提醒天数。", True
        upcoming_tasks = task_manager.tasks_due_within(days)
        overdue_tasks = task_manager.overdue_tasks()
        events = calendar_client.upcoming(timedelta(days=days))
        parts = []
        if overdue_tasks:
            parts.append("⚠️ 已逾期任务:")
            parts.extend(
                f"- #{task.id} {task.title} (原定 {task.due_datetime().strftime('%Y-%m-%d %H:%M')})"
                for task in overdue_tasks
            )
        if upcoming_tasks:
            parts.append(f"📌 未来 {days} 天内需完成的任务:")
            parts.extend(
                f"- #{task.id} {task.title} (截止 {task.due_datetime().strftime('%Y-%m-%d %H:%M')})"
                for task in upcoming_tasks
            )
        if events:
            parts.append(f"🗓️ 未来 {days} 天日程:")
            parts.extend(f"- {format_event(event)}" for event in events)
        if not parts:
            return f"未来 {days} 天没有需要提醒的任务或日程。", True
        return "\n".join(parts), True

    save_message("user", user_input)
    result = graph.invoke({"input": user_input})
    response = result.get("response", "")
    if response:
        save_message("bot", response)
    return response, True


def main():
    logger.info("Starting LangGraph Agent...")
    print("=== LangGraph Agent ===")
    print("Type 'exit' or 'quit' to stop.")
    print(
        "Commands: /summarize <text>, /search <query>, /plan <goal>, /research <query>, /report <body>, /schedule <title;start;end>, /agenda [days], /task <add/done>, /tasks [all], /remind [days], /history, /clear"
    )

    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        response, should_continue = handle_user_input(user_input)

        if response:
            print(f"Bot: {response}")
            logger.debug(f"Input: {user_input} | Response: {response}")

        if not should_continue:
            logger.info("Received exit command, shutting down.")
            break

    print("Goodbye!")
    logger.info("Agent stopped.")


if __name__ == "__main__":
    main()
