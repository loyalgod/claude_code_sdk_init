"""工具注册与示例工具测试。"""

from __future__ import annotations

import asyncio

import pytest

from core.tools import build_default_registry
from core.tools.clock import get_current_time
from core.tools.echo import echo
from core.tools.registry import ToolRegistry


def test_registry_builds_defaults() -> None:
    registry = build_default_registry()
    assert isinstance(registry, ToolRegistry)
    assert set(registry.names) == {"get_current_time", "echo"}


def test_registry_rejects_duplicate() -> None:
    registry = ToolRegistry()
    registry.register(build_default_registry().tools[0])
    with pytest.raises(ValueError, match="工具名冲突"):
        registry.register(build_default_registry().tools[0])


def test_echo_tool() -> None:
    result = asyncio.run(echo.handler({"text": "hello"}))
    assert result["content"][0]["text"] == "hello"


def test_get_current_time_tool() -> None:
    result = asyncio.run(get_current_time.handler({}))
    text = result["content"][0]["text"]
    assert text.endswith("+08:00")  # Asia/Shanghai
