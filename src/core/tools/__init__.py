"""工具层汇总：新业务工具在这里注册进默认注册表。"""

from __future__ import annotations

from core.tools import clock, echo
from core.tools.registry import ToolRegistry


def build_default_registry() -> ToolRegistry:
    """构造默认工具注册表。新增工具时：在 tools/ 下加模块，并在此注册。"""
    registry = ToolRegistry()
    registry.register(clock.get_current_time)
    registry.register(echo.echo)
    return registry
