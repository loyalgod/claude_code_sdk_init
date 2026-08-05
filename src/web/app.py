"""FastAPI 应用工厂。

测试时可注入替换组件：``create_app(runner=FakeRunner())``。
"""

from __future__ import annotations

from fastapi import FastAPI

from core.config import Settings
from core.runner import ClaudeAgentRunner
from core.sessions import SessionStore
from web.routes import router

__version__ = "0.1.0"


def create_app(
    settings: Settings | None = None,
    runner: ClaudeAgentRunner | None = None,
    sessions: SessionStore | None = None,
) -> FastAPI:
    """创建 FastAPI 应用实例。"""
    app = FastAPI(title="my-agent", version=__version__)

    app.state.settings = settings if settings is not None else Settings()
    app.state.sessions = sessions if sessions is not None else SessionStore()
    app.state.runner = (
        runner
        if runner is not None
        else ClaudeAgentRunner(app.state.settings, sessions=app.state.sessions)
    )

    app.include_router(router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
