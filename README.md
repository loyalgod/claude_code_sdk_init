# my-agent

基于 Claude Agent SDK（`claude-agent-sdk`）的可复用 Agent 模板。

## 设计目标

- **核心与入口分离**：`runner`/`tools`/`mcp`/`permissions`/`events` 等核心逻辑与界面无关；
  复用时换的只是入口形态（Web、CLI、任务队列…）。
- **两个入口**：CLI 作为本地调试/演示入口；`web/` 为产品入口（FastAPI + SSE，预留网站）。
- **工具可扩展**：新增业务工具只需在 `tools/` 下加一个文件并注册。

## 目录结构

```
src/                 # 包根：core/、web/、cli.py 即顶级模块
├── cli.py           # 入口：CLI 调试（薄壳，console script: my-agent）
├── web/             # 入口：FastAPI + SSE（薄壳）
│   ├── app.py       # create_app 工厂（可注入替换组件）
│   ├── routes.py    # POST /v1/chat（SSE）+ GET /v1/sessions
│   ├── deps.py      # Depends 依赖注入
│   └── sse.py       # SSE 帧编码
└── core/            # 与 Claude Agent SDK 交互的核心（复用时基本不动）
    ├── config.py    # Settings（pydantic-settings，.env 驱动）
    ├── runner.py    # Agent 编排：SDK client 生命周期 + 事件分发
    ├── mcp.py       # 把工具组装为 SDK MCP server
    ├── permissions.py  # can_use_tool 权限策略
    ├── prompts.py   # 系统提示词构建
    ├── events.py    # 事件协议（text_delta 等常量 + EmitFunc）
    ├── sessions.py  # 会话元数据表（支撑 resume，预留持久化）
    ├── models.py    # TurnJob / AgentRunResult
    ├── utils.py     # sanitize 等公共函数
    └── tools/       # 工具层：registry + clock/echo 示例
```

## 快速开始

```bash
# 安装依赖（含 Web 与 dev 组）
uv sync --extra web

# 配置密钥
cp .env.example .env   # 填入 ANTHROPIC_API_KEY

# CLI 跑一轮（调试入口）
uv run my-agent "你好，介绍一下你自己"

# 流式 CLI
uv run my-agent --no-stream=false "..."

# 启动 Web 服务（产品入口）
uv run uvicorn web.app:create_app --factory --reload

# 调用接口（SSE 流）
curl -N -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "你好"}'
```

## 质量检查

```bash
uv run ruff check .
uv run pytest
```

## 模板复用指南

1. 复制项目，把 `pyproject.toml` 里的 `name` 与 `[project.scripts]` 的入口替换成新项目名。
2. 业务工具：在 `src/core/tools/` 新增模块，用 `sdk.tool(...)` 定义工具，
   并在 `core/tools/__init__.py` 的 `build_default_registry()` 里注册。
3. 改行为：编辑 `core/prompts.py`（提示词）、`core/permissions.py`（权限）、`core/config.py`（配置项）。
4. Web 对接：`web/routes.py` 的 `POST /v1/chat` 已输出标准 SSE 事件流，前端按
   `text_delta`/`thinking_delta`/`tool_started`/`tool_completed`/`result`/`error` 事件渲染即可。

## 环境变量

| 变量                    | 说明                                           | 默认值                     |
| ----------------------- | ---------------------------------------------- | -------------------------- |
| `ANTHROPIC_API_KEY`     | Anthropic API Key（必填）                      | -                          |
| `AGENT_MODEL`           | 模型名                                         | `claude-sonnet-4-20250514` |
| `AGENT_NAME`            | Agent 展示名                                   | `my-agent`                 |
| `MCP_SERVER_NAME`       | MCP 服务器名（工具全名 `mcp__<name>__<tool>`） | `myagent`                  |
| `MAX_TURNS`             | 单轮最大工具轮数                               | `20`                       |
| `AGENT_TIMEOUT_SECONDS` | 单轮超时（秒）                                 | `300`                      |
| `PERMISSION_MODE`       | 权限模式                                       | `default`                  |
| `AGENT_CWD`             | Agent 工作目录                                 | 项目根                     |
| `ALLOWED_BUILTIN_TOOLS` | 允许的 SDK 内置工具（JSON 数组）               | `["Read","Glob","Grep"]`   |
| `DISALLOWED_TOOLS`      | 禁止的 SDK 内置工具（JSON 数组）               | 见 `.env.example`          |
