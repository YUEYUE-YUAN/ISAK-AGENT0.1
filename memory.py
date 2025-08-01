from typing import List, Dict

# 简单的内存存储：会话历史列表
conversation_history: List[Dict[str, str]] = []


def save_message(role: str, content: str) -> None:
    """
    将一条消息保存到对话历史中。
    role: 消息角色，通常为 'user' 或 'bot'
    content: 消息内容
    """
    conversation_history.append({"role": role, "content": content})


def get_history() -> List[Dict[str, str]]:
    """
    获取完整的对话历史。

    Returns:
        List[Dict[str, str]]: 每条消息是包含 'role' 和 'content' 的字典
    """
    return conversation_history


def clear_history() -> None:
    """
    清空对话历史。
    """
    conversation_history.clear()


def get_recent_history(n: int = 10) -> List[Dict[str, str]]:
    """
    获取最近 n 条消息。

    Args:
        n: 要返回的消息条数，默认 10

    Returns:
        List[Dict[str, str]]: 最近 n 条消息
    """
    return conversation_history[-n:]
