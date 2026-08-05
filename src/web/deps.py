"""依赖注入：从 FastAPI app.state 读取共享组件，供路由 ``Depends`` 使用。"""

from __future__ import annotations

from fastapi import Request

from core.config import Settings
from core.runner import ClaudeAgentRunner
from core.sessions import SessionStore


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_runner(request: Request) -> ClaudeAgentRunner:
    return request.app.state.runner


def get_sessions(request: Request) -> SessionStore:
    return request.app.state.sessions
