import openai
from langgraph.graph import StateGraph
from config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    DEFAULT_MODEL,
    MAX_TOKENS,
    TEMPERATURE,
)

# 配置 OpenAI 客户端
openai.api_key = OPENAI_API_KEY
openai.api_base = OPENAI_API_BASE

# 示例 Node：调用 OpenAI API 生成回复
def generate_response(state):
    """
    通过 OpenAI ChatCompletion 生成对话回复。
    state: dict, 应包含键 'input'
    返回: dict, 包含键 'response'
    """
    user_input = state.get("input", "")
    if not user_input:
        return {"response": "请提供输入内容。"}

    completion = openai.ChatCompletion.create(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": user_input}],
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )
    reply = completion.choices[0].message.content.strip()
    return {"response": reply}

# 构建 StateGraph
builder = StateGraph()
builder.add_node("generate", generate_response)
# 设定入口与出口节点都是 generate
builder.set_entry_point("generate")
builder.set_finish_point("generate")

# 编译图
graph = builder.compile()

if __name__ == "__main__":
    # 本地测试示例
    input_text = input("User: ")
    result = graph.invoke({"input": input_text})
    print("Bot:", result.get("response"))
