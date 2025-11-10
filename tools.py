import logging
from typing import List

from agent.tools import (
    CalendarClient,
    CalendarEvent,
    Task,
    TaskManager,
    TaskStatus,
    format_event,
    parse_datetime,
    parse_due,
)
from agent.tools.web import search_web as _search_web
from config import DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE, client

# 获取 logger
logger = logging.getLogger(__name__)


def summarize_text(text: str) -> str:
    """
    使用 OpenAI 模型对给定文本进行摘要。
    Args:
        text (str): 要摘要的原始文本。
    Returns:
        str: 摘要结果。
    """
    prompt = f"请用简洁的语言总结以下内容：\n\n{text}"  
    try:
        resp = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        summary = resp.choices[0].message.content.strip()
        return summary
    except Exception as e:
        logger.error(f"summarize_text 出错: {e}")
        return "[摘要失败]"


def web_search(query: str, max_results: int = 5) -> List[str]:
    """Search the bundled offline corpus and return formatted snippets."""

    logger.info(f"执行 web_search: {query}")
    results = _search_web(query, k=max_results)
    formatted = [
        f"{item['snippet']} (来源: {item.get('source', 'local')}, 相关度: {item.get('score', 0):.2f})"
        for item in results
    ]
    return formatted


def call_custom_tool(tool_name: str, *args, **kwargs):
    """
    动态调用自定义工具函数。
    Args:
        tool_name (str): 工具函数名，例如 'summarize_text'。
    Returns:
        任意: 工具执行结果。
    """
    tools_map = {
        "summarize": summarize_text,
        "search": web_search,
    }
    func = tools_map.get(tool_name)
    if not func:
        raise ValueError(f"未知工具: {tool_name}")
    return func(*args, **kwargs)


__all__ = [
    "summarize_text",
    "web_search",
    "call_custom_tool",
    "CalendarClient",
    "CalendarEvent",
    "Task",
    "TaskManager",
    "TaskStatus",
    "format_event",
    "parse_datetime",
    "parse_due",
]
