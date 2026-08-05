"""集中配置：从环境变量 / .env 加载，字段名大写即环境变量名。"""

from __future__ import annotations

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Agent 全局配置。

    环境变量不区分大小写与字段名匹配，例如 ``ANTHROPIC_API_KEY`` 对应
    ``anthropic_api_key``；列表类字段需传 JSON 数组字符串。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Anthropic API Key（SDK 也从该环境变量读取）
    anthropic_api_key: SecretStr = SecretStr("")

    # 模型与 Agent 名称
    agent_model: str = "claude-sonnet-4-20250514"
    agent_name: str = "my-agent"

    # MCP 工具服务器
    mcp_server_name: str = "myagent"
    app_version: str = "0.1.0"

    # 运行参数
    max_turns: int = 20
    agent_timeout_seconds: int = 300
    permission_mode: str = "default"
    agent_cwd: Path = Path.cwd()

    # SDK 内置工具权限
    allowed_builtin_tools: list[str] = ["Read", "Glob", "Grep"]
    disallowed_tools: list[str] = [
        "Write",
        "Edit",
        "Bash",
        "NotebookEdit",
        "WebFetch",
        "WebSearch",
        "Task",
        "Agent",
    ]

    def api_key(self) -> str | None:
        """返回明文 API Key；未配置时返回 None。"""
        resolved = self.anthropic_api_key.get_secret_value().strip()
        return resolved or None

    def claude_env(self) -> dict[str, str]:
        """传给 SDK 子进程的环境变量（当前仅注入 API Key）。"""
        env: dict[str, str] = {}
        key = self.api_key()
        if key:
            env["ANTHROPIC_API_KEY"] = key
        return env
