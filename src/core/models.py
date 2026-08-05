"""跨入口共享的核心数据类型。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TurnJob:
    """一轮对话请求。"""

    text: str
    session_id: str | None = None


@dataclass(frozen=True)
class AgentRunResult:
    """一轮对话的结果。"""

    text: str
    session_id: str | None = None
