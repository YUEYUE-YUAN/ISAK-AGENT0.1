# ISAK-Agent0.1

一个具备多工具路由、Persona、知识库检索与后台队列的 LangGraph 智能体。

由于饱受复杂工作流程，信息碎片化，信息隐私困扰，所以自己写了这个人agent的代码，可在CLI运行，解放生产力。

下一个版本会加入：
*语音识别/合成（Whisper + TTS）和图像理解节点，用于语音助手或场景识别

## 🚀 当前能力一览

- **多智能体路由**：`src/agent/graph.py` 通过 `KnowledgeRouter` 识别需求并将请求分发给对话、摘要、调研、规划或文档生成子 Agent。
- **Persona 支持**：`src/agent/personas/registry.yaml` 定义了多种语气与角色，路由结果会注入对应 Persona 风格到模型提示词。
- **知识库检索**：`src/agent/memory/vector.py` 基于轻量向量存储实现项目级知识库，配合 `tools/docs.py` 提供离线相似度搜索。
- **命令行体验**：`main.py` 在原有 `/summarize`、`/search`、`/history`、`/clear` 之上新增 `/plan`、`/research`、`/report`、`/schedule`、`/agenda`、`/task`、`/tasks`、`/remind` 等指令，便于直接调用专用子 Agent 与日程/任务助手。
- **工具生态**：`src/agent/tools` 下提供摘要复用、离线 Web 搜索、PDF 生成、日程同步等实用工具，`tools.py` 通过统一入口复用这些能力。
- **事件与任务管理**：`src/agent/memory/events.py`、`src/agent/tools/calendar.py` 与 `src/agent/tools/tasks.py` 使用 SQLite/JSON 维护事件时间线、日程与待办任务，并支持提醒。
- **异步任务队列**：`src/agent/queue` 提供 SQLite + asyncio 的轻量队列，`src/bg_worker.py` 可持续消费任务执行 LangGraph。
- **HTTP API & 异步客户端**：`src/api_server.py` 暴露 `/chat` 接口，`src/run_async_client.py` 演示如何异步调用图。

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
2. **配置 OpenAI 凭据**
 ```bash
  cp .env.example .env
  # 在 .env 中写入 OPENAI_API_KEY、可选的 OPENAI_API_BASE/DEFAULT_MODEL 等
  ```
3. **（可选）加载知识库**：将项目文档放入 `data/kb/`，首次运行时会自动构建向量索引。

## 💾 会话历史存储

- **默认（内存）**：`HISTORY_BACKEND` 留空或设为 `memory` 时，对话仅保存在运行时内存中，适合一次性会话。
- **本地持久化**：将 `.env` 中的 `HISTORY_BACKEND` 设为 `file`，并可通过 `HISTORY_FILE_PATH` 指定保存路径（默认 `outputs/history.json`）。历史记录会以 JSON 形式写入磁盘，可在后续会话或其他脚本中直接读取。
- **同步个人云端**：将 `HISTORY_BACKEND` 设为 `cloud`，并提供 `HISTORY_CLOUD_URL`（POST/GET/DELETE 对话记录的 HTTP 接口）以及可选的 `HISTORY_CLOUD_TOKEN`（Bearer Token）。
  - 程序会在每次写入时向云端发送 JSON 对象，同时根据 `HISTORY_CLOUD_FALLBACK_PATH`（或默认的 `HISTORY_FILE_PATH`）保留一份本地备份，离线时会自动切换到备份存储。
  - 读取和清空历史记录会优先访问云端接口，失败时同样退回到本地备份，保证随时可查。

通过这些配置，你可以在 CLI、HTTP API 或自定义脚本中随时复用相同的历史记录，实现多终端共享或长期归档。

## 📚 向量知识库存储

- **默认（内存）**：`KB_BACKEND` 留空或设为 `memory` 时，向量化后的知识库仅存在于运行内存中。
- **本地文件**：设为 `file` 并通过 `KB_FILE_PATH` 指定保存位置（默认 `outputs/vector_store.json`）。程序会在加载 `data/kb/` 文档后自动写入该文件，后续启动会直接复用缓存。
- **个人云端**：设为 `cloud`，提供 `KB_CLOUD_URL`（需支持 `GET`/`PUT` 返回/接收 JSON 列表）以及可选的 `KB_CLOUD_TOKEN`。
  - 同时可配置 `KB_CLOUD_FALLBACK_PATH`（默认使用 `KB_FILE_PATH`），离线或请求失败时会自动落盘，下一次启动会先读取本地备份再尝试同步云端。
  - `KB_CLOUD_TIMEOUT` 用于自定义网络超时时间（秒），默认 5s。

无论从命令行还是通过 LangGraph 管线访问知识库，相同的配置都会保证向量索引被写入并从指定存储位置加载，实现多端共享或快速恢复。

## 🗓️ 日程与任务助手

- **存储位置**：
  - `CALENDAR_DB_PATH`（默认 `outputs/calendar.db`）用于持久化 `/schedule`、`/agenda`、`/remind` 命令涉及的日程信息，基于 SQLite 自动创建数据库。
  - `TASKS_FILE_PATH`（默认 `outputs/tasks.json`）用于保存 `/task`、`/tasks`、`/remind` 命令记录的待办事项，采用 JSON 文本方便同步或备份。
- **添加日程**：`/schedule 标题; 开始时间; 结束时间; [地点]; [描述]`，时间支持 `YYYY-MM-DD HH:MM`、`YYYY-MM-DDTHH:MM` 以及仅日期（默认 09:00/18:00）。
- **查看行程**：`/agenda [天数]` 列出未来 N 天的日程，`/remind [天数]` 会同时给出即将到期的任务、逾期任务以及日程提醒。
- **管理任务**：
  - `/task add 标题; [截止时间]; [备注]` 创建任务，截止时间同样支持常见的日期/时间格式。
  - `/task done <任务ID>` 标记完成，`/tasks` 查看未完成任务，`/tasks all` 包含已完成条目。

这些命令与 CLI 其他功能共享会话上下文，可随时结合 LangGraph 生成的规划/调研结果继续调度日程。

## 💬 使用方式

- **命令行模式**
  ```bash
  python main.py
  ```
  支持 `/summarize`、`/search`、`/plan`、`/research`、`/report`、`/schedule`、`/agenda`、`/task`、`/tasks`、`/remind`、`/history`、`/clear`、`exit/quit`。

- **Python 调用 LangGraph**
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

- **异步队列/后台任务**
  ```bash
  python -m src.bg_worker
  ```
  使用 `AsyncTaskQueue.enqueue` 将请求写入 SQLite 队列，worker 会自动调用 LangGraph。

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
