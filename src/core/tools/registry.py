"""工具注册表：统一收集 ``@sdk.tool`` 装饰器产出的工具定义。"""

from __future__ import annotations

from typing import Any

import claude_agent_sdk as sdk

SdkMcpTool = sdk.SdkMcpTool[Any]


class ToolRegistry:
    """工具注册表，保证工具名唯一，供 MCP server 组装使用。"""

    def __init__(self) -> None:
        self._tools: dict[str, SdkMcpTool] = {}

    def register(self, tool: SdkMcpTool) -> SdkMcpTool:
        if tool.name in self._tools:
            raise ValueError(f"工具名冲突：{tool.name}")
        self._tools[tool.name] = tool
        return tool

    @property
    def tools(self) -> list[SdkMcpTool]:
        return list(self._tools.values())

    @property
    def names(self) -> list[str]:
        return list(self._tools)
