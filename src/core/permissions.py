"""``can_use_tool`` 权限策略。

SDK 会为**未列入 allowed_tools** 的工具调用本钩子。模板策略：
- MCP 工具已在 ``allowed_tools`` 中放行，不会走到这里；
- SDK 内置工具按 ``Settings.allowed_builtin_tools`` 白名单放行；
- ``AskUserQuestion`` 默认拒绝（未配置反问处理）；
- 其余一律拒绝。
"""

from __future__ import annotations

from typing import Any

import claude_agent_sdk as sdk

from core.config import Settings


class DefaultPermissionPolicy:
    """默认权限策略；复用时继承并覆盖 ``can_use_tool``。"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def can_use_tool(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        context: Any,
    ) -> sdk.PermissionResult:
        """返回 Allow/Deny；``context`` 为 ``ToolPermissionContext``。"""
        if tool_name == "AskUserQuestion":
            return sdk.PermissionResultDeny(
                message="模板默认未启用 AskUserQuestion，请自行实现反问处理。"
            )
        if tool_name in self.settings.allowed_builtin_tools:
            return sdk.PermissionResultAllow()
        return sdk.PermissionResultDeny(message=f"模板默认不允许调用工具 {tool_name}。")
