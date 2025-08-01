import logging
import openai
from config import DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE

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
        resp = openai.ChatCompletion.create(
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


def web_search(query: str, max_results: int = 5) -> list:
    """
    Web 搜索工具（占位符实现），返回搜索结果列表。
    生产环境可集成搜索 API（如 SerpAPI、Bing Search）。
    Args:
        query (str): 搜索关键词。
        max_results (int): 最多返回结果数量。
    Returns:
        list: 搜索结果摘要列表，每项为字符串。
    """
    logger.info(f"执行 web_search: {query}")
    # TODO: 实现真实搜索逻辑
    results = [f"结果 {i+1} for '{query}'" for i in range(max_results)]
    return results


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
