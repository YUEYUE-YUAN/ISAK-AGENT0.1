# ISAK-Agent0.1

一个具备多工具路由、Persona、知识库检索、DeepAgents 任务分解与多入口体验的 LangGraph 智能体示例。

## 🚀 功能总览

- **多智能体路由**：`src/agent/graph.py` 使用 `KnowledgeRouter` 按需求将请求派发给对话、摘要、调研、规划或文档子 Agent。
- **Persona 支持**：`src/agent/personas/registry.yaml` 配置多种角色语气，路由后的请求会自动注入对应 Persona。
- **自动任务分解**：`src/agent/agents/planner.py` 借助 DeepAgents 的 `write_todos` 与 `task` 自动生成子任务及子 Agent，`/plan` 指令或 LangGraph 节点会直接复用。
- **知识库检索**：`src/agent/memory/vector.py` + `src/agent/tools/docs.py` 提供离线向量搜索，首次读取 `data/kb/` 文档时会自动构建索引。
- **多种界面**：
  - CLI：`main.py` 支持 `/summarize`、`/search`、`/plan`、`/research`、`/report`、`/schedule`、`/agenda`、`/task`、`/tasks`、`/remind`、`/history`、`/clear`、`exit/quit`。
  - Streamlit：`streamlit_app.py` 在浏览器内提供与 CLI 一致的命令与历史展示。
  - HTTP/异步：`src/api_server.py` 暴露 `/chat` API，`src/run_async_client.py` 演示异步调用。
- **工具生态**：`src/agent/tools` 下的 calendar/docs/tasks/web 等模块提供摘要、搜索、日程、文档、提醒等能力，并通过 `tools.py` 暴露统一入口。
- **会话与事件记忆**：`memory.py` 支持内存/本地/云端多种历史存储；`src/agent/memory/events.py` 维护事件时间线。
- **任务与日程管理**：`src/agent/tools/calendar.py` 与 `src/agent/tools/tasks.py` 基于 SQLite/JSON 记录日程和待办，并与 DeepAgents 拆解结果衔接。
- **后台执行**：`src/agent/queue` + `src/bg_worker.py` 提供 SQLite + asyncio 的轻量队列以批量处理任务。

## 📁 项目结构

```
ISAK-AGENT0.1/
├─ langgraph.json
├─ pyproject.toml
├─ requirements.txt
├─ README.md
├─ config.py
├─ graph_config.py
├─ main.py
├─ memory.py
├─ tools.py
├─ conftest.py
├─ data/
│  └─ kb/
│     └─ getting_started.md
├─ src/
│  ├─ agent/
│  │  ├─ __init__.py
│  │  ├─ graph.py
│  │  ├─ nodes.py
│  │  ├─ routing.py
│  │  ├─ agents/
│  │  │  ├─ docgen.py
│  │  │  ├─ planner.py
│  │  │  ├─ research.py
│  │  │  └─ summarize.py
│  │  ├─ memory/
│  │  │  ├─ convo.py
│  │  │  ├─ events.py
│  │  │  └─ vector.py
│  │  ├─ personas/
│  │  │  ├─ __init__.py
│  │  │  ├─ loader.py
│  │  │  └─ registry.yaml
│  │  ├─ tools/
│  │  │  ├─ calendar.py
│  │  │  ├─ docs.py
│  │  │  ├─ io_utils.py
│  │  │  ├─ tasks.py
│  │  │  └─ web.py
│  │  └─ queue/
│  │     ├─ __init__.py
│  │     ├─ engine.py
│  │     └─ models.py
│  ├─ api_server.py
│  └─ run_async_client.py
├─ src/bg_worker.py
├─ static/
│  └─ studio_ui.png
└─ tests/
   ├─ test_cli.py
   ├─ test_graph.py
   ├─ test_graph_config.py
   ├─ test_routing.py
   └─ test_utilities.py
```

## 🛠️ 安装与配置

1. **创建虚拟环境并安装依赖**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **准备环境变量**
   ```bash
   cp .env.example .env
   # 在 .env 中写入 OPENAI_API_KEY；可选：OPENAI_API_BASE、DEFAULT_MODEL、MAX_TOKENS、TEMPERATURE 等
   ```
3. **（可选）准备知识库**：把自定义文档放入 `data/kb/`，首次运行时会自动向量化并缓存。

## 💾 会话历史存储

- **内存模式**：`HISTORY_BACKEND` 留空或设为 `memory`，历史仅在运行期间保留。
- **本地文件**：设置 `HISTORY_BACKEND=file`，可通过 `HISTORY_FILE_PATH` 指定 JSON 输出位置（默认 `outputs/history.json`）。
- **云端同步**：设置 `HISTORY_BACKEND=cloud` 并配置 `HISTORY_CLOUD_URL`、可选的 `HISTORY_CLOUD_TOKEN`。写入会同时更新本地备份（`HISTORY_CLOUD_FALLBACK_PATH` 或 `HISTORY_FILE_PATH`），离线时自动回退到本地。

CLI、Streamlit、API 等入口共享同一套接口，因此配置一次即可在多终端复用历史。

## 📚 向量知识库存储

- **内存模式**：`KB_BACKEND=memory`（默认）仅在运行期维护索引。
- **本地文件**：设置 `KB_BACKEND=file` 并通过 `KB_FILE_PATH` 指定缓存路径（默认 `outputs/vector_store.json`）。
- **云端同步**：设置 `KB_BACKEND=cloud`，提供 `KB_CLOUD_URL`、可选的 `KB_CLOUD_TOKEN`、`KB_CLOUD_TIMEOUT` 以及 `KB_CLOUD_FALLBACK_PATH`。失败时同样自动落盘并回退读取。

所有入口都会读取相同的向量存储设置，保证知识库的一致性。

## 🗓️ 日程与任务助手

- **存储配置**：
  - `CALENDAR_DB_PATH`（默认 `outputs/calendar.db`）用 SQLite 记录日程，供 `/schedule`、`/agenda`、`/remind` 使用。
  - `TASKS_FILE_PATH`（默认 `outputs/tasks.json`）保存待办事项，供 `/task`、`/tasks`、`/remind` 读取。
- **常用命令**：
  - `/schedule 标题; 开始时间; 结束时间; [地点]; [描述]`
  - `/agenda [天数]`、`/remind [天数]`
  - `/task add 标题; [截止时间]; [备注]`
  - `/task done <任务ID>`、`/tasks`、`/tasks all`
- **与 DeepAgents 联动**：`/plan` 会通过 `plan_tasks()` 自动拆解子任务并生成子 Agent；命令行或 Streamlit 中可直接把这些结果录入日程/任务列表。若 DeepAgents 不可用，系统会回退到原始输入确保流程不中断。

这些命令与 CLI 其他功能共享会话上下文，可随时结合 LangGraph 生成的规划/调研结果继续调度日程。

## 💬 使用方式

- **命令行模式**
  ```bash
  python main.py
  ```
  终端会展示所有可用命令，输入 `exit`/`quit` 结束会话。

- **Streamlit Web UI**
  ```bash
  streamlit run streamlit_app.py
  ```
  浏览器端与 CLI 共用一套处理逻辑，可直接执行全部命令。

- **Python 集成**
  ```python
  from graph_config import graph
  result = graph.invoke({"input": "给我一个发布计划"})
  print(result["response"])
  ```

- **HTTP API**
  ```bash
  python -m src.api_server
  curl -X POST http://localhost:8080/chat -d '{"input": "总结以下内容"}'
  ```

- **后台队列**
  ```bash
  python -m src.bg_worker
  ```
  使用 `AsyncTaskQueue.enqueue` 将请求写入 SQLite 队列，worker 会自动执行。

## 🧪 测试

项目提供覆盖 CLI、图路由、工具模块与队列的单元测试：
```bash
pytest
```
测试夹具在 `conftest.py` 中为 `langgraph`、`openai` 提供桩实现，保证在无外部依赖的环境下也能运行。

## 📦 扩展建议

- 接入真实的向量数据库（FAISS/Chroma）或 Web 搜索 API，以替换默认的离线实现。
- 将 `CalendarClient`、`TimelineStore` 替换为云服务或团队共享数据库，打造协作型记忆。
- 基于 `AsyncTaskQueue` 扩展优先级、重试与并发调度策略。
- 为 `Personas` 增加更多角色配置，并结合 planner/research 子 Agent 构建更复杂的 Orchestrator。

以上模块均已在仓库中落地，可按需组合或替换，以快速搭建自定义的 LangGraph 智能体应用。
