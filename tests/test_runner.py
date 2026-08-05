"""编排层单元测试（不发起真实 API 调用）。"""

from __future__ import annotations

import asyncio

from core.config import Settings
from core.models import TurnJob
from core.runner import ClaudeAgentRunner


def test_message_stream_yields_single_user_message(settings: Settings) -> None:
    runner = ClaudeAgentRunner(settings)
    job = TurnJob(text="hello")

    async def collect() -> list[dict]:
        return [message async for message in runner._message_stream(job)]

    messages = asyncio.run(collect())
    assert len(messages) == 1
    assert messages[0]["type"] == "user"
    assert messages[0]["message"]["content"][0]["text"] == "hello"


def test_interrupt_without_client_is_safe(settings: Settings) -> None:
    runner = ClaudeAgentRunner(settings)
    asyncio.run(runner.interrupt())  # 未连接 client 时不应抛错


def test_build_mcp_tool_names(settings: Settings) -> None:
    from core.tools import build_default_registry

    registry = build_default_registry()
    names = [f"mcp__{settings.mcp_server_name}__{name}" for name in registry.names]
    assert names == [
        f"mcp__{settings.mcp_server_name}__get_current_time",
        f"mcp__{settings.mcp_server_name}__echo",
    ]
