"""配置加载测试。"""

from __future__ import annotations

from core.config import Settings


def test_defaults(settings: Settings) -> None:
    assert settings.max_turns == 20
    assert settings.agent_model == "claude-sonnet-4-20250514"
    assert settings.mcp_server_name == "myagent"
    assert "Read" in settings.allowed_builtin_tools


def test_env_override(monkeypatch) -> None:
    monkeypatch.setenv("MAX_TURNS", "5")
    monkeypatch.setenv("MCP_SERVER_NAME", "custom")
    settings = Settings(_env_file=None)
    assert settings.max_turns == 5
    assert settings.mcp_server_name == "custom"


def test_claude_env_no_key(settings: Settings) -> None:
    # 未配置 Key 时 claude_env 不应注入空 Key
    if settings.api_key() is None:
        assert settings.claude_env() == {}
