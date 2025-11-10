"""Streamlit interface for the LangGraph Agent."""
from __future__ import annotations

import streamlit as st

from main import handle_user_input

st.set_page_config(page_title="LangGraph Agent", page_icon="🧠", layout="wide")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "conversation_active" not in st.session_state:
    st.session_state["conversation_active"] = True

st.title("LangGraph Agent")
st.caption(
    "命令行与 Streamlit 共用的智能体。支持 /summarize、/search、/plan、/research、/report、/schedule、/agenda、/task、/tasks、/remind、/history、/clear、exit/quit 等指令。"
)

with st.expander("如何使用？", expanded=False):
    st.markdown(
        """
        - 在下方聊天输入框输入问题或指令，按回车发送。
        - `/plan` 会调用 DeepAgents 自动拆解任务；生成的子任务可继续用 `/schedule` 或 `/task` 管理。
        - 输入 `exit` 或 `quit` 可结束当前会话，之后需刷新页面重新开始。
        """
    )

for role, content in st.session_state["chat_history"]:
    st.chat_message(role).write(content)

if st.session_state["conversation_active"]:
    prompt = st.chat_input("输入消息或指令...")
else:
    st.info("会话已结束。刷新页面即可重新开始新的对话。")
    prompt = None

if prompt:
    st.session_state["chat_history"].append(("user", prompt))
    st.chat_message("user").write(prompt)

    response, should_continue = handle_user_input(prompt)

    if response:
        st.session_state["chat_history"].append(("assistant", response))
        st.chat_message("assistant").write(response)

    if not should_continue:
        st.session_state["conversation_active"] = False
        st.warning("会话已结束。如需继续对话，请刷新页面重新启动会话。")
