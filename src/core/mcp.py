"""把注册的工具组装为 SDK 进程内 MCP server。"""

from __future__ import annotations

import claude_agent_sdk as sdk

from core.tools.registry import ToolRegistry


def build_mcp_server(
    registry: ToolRegistry,
    *,
    name: str,
    version: str = "1.0.0",
) -> sdk.McpSdkServerConfig:
    """基于注册表构建进程内 MCP server 配置。"""
    return sdk.create_sdk_mcp_server(
        name=name,
        version=version,
        tools=registry.tools,
    )
