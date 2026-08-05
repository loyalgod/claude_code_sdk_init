"""权限策略测试。"""

from __future__ import annotations

import asyncio

import claude_agent_sdk as sdk

from core.config import Settings
from core.permissions import DefaultPermissionPolicy


def _run_policy(settings: Settings, tool_name: str) -> sdk.PermissionResult:
    policy = DefaultPermissionPolicy(settings)
    return asyncio.run(policy.can_use_tool(tool_name, {}, None))


def test_allows_builtin_whitelist(settings: Settings) -> None:
    assert isinstance(_run_policy(settings, "Read"), sdk.PermissionResultAllow)
    assert isinstance(_run_policy(settings, "Grep"), sdk.PermissionResultAllow)


def test_denies_disallowed_tool(settings: Settings) -> None:
    assert isinstance(_run_policy(settings, "Write"), sdk.PermissionResultDeny)


def test_denies_unknown_tool(settings: Settings) -> None:
    assert isinstance(_run_policy(settings, "SomeRandomTool"), sdk.PermissionResultDeny)


def test_denies_ask_user_by_default(settings: Settings) -> None:
    assert isinstance(_run_policy(settings, "AskUserQuestion"), sdk.PermissionResultDeny)
