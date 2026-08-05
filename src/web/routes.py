"""Web 路由：``POST /v1/chat`` 以 SSE 流返回 Agent 事件；``GET /v1/sessions`` 列出会话。"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.events import EVENT_ERROR, EVENT_RESULT
from core.models import TurnJob
from core.runner import ClaudeAgentRunner
from core.sessions import SessionStore
from web.deps import get_runner, get_sessions
from web.sse import sse_frame

router = APIRouter(prefix="/v1")


class ChatRequest(BaseModel):
    """对话请求体。"""

    text: str = Field(..., min_length=1, description="用户输入")
    session_id: str | None = Field(default=None, description="恢复会话时传入")


class ChatResponse(BaseModel):
    """非流式响应（预留）。"""

    session_id: str
    text: str


class SessionInfo(BaseModel):
    """会话元信息。"""

    session_id: str
    turn_count: int
    created_at: str
    last_turn_at: str


@router.post("/chat")
async def chat(
    body: ChatRequest,
    runner: ClaudeAgentRunner = Depends(get_runner),
) -> StreamingResponse:
    """启动一轮对话，返回 SSE 事件流。

    事件序列：``start`` → （``text_delta``/``thinking_delta``/``tool_started``/
    ``tool_completed``…）→ ``result`` 或 ``error``。
    """
    queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()

    async def emit(event: str, data: dict[str, Any]) -> None:
        await queue.put((event, data))

    async def run_agent() -> None:
        job = TurnJob(text=body.text, session_id=body.session_id)
        try:
            result = await runner.run(job=job, emit=emit)
            await emit(EVENT_RESULT, {"session_id": result.session_id, "text": result.text})
        except Exception as exc:  # noqa: BLE001 - 兜底输出到 SSE
            await emit(EVENT_ERROR, {"message": str(exc)})

    async def event_stream() -> Any:
        await queue.put(("start", {"session_id": body.session_id}))
        task = asyncio.create_task(run_agent())
        try:
            while True:
                name, data = await queue.get()
                yield sse_frame(name, data)
                if name in {EVENT_RESULT, EVENT_ERROR}:
                    break
        finally:
            task.cancel()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions(sessions: SessionStore = Depends(get_sessions)) -> list[SessionInfo]:
    """列出会话元信息（按最后活跃时间倒序）。"""
    return [
        SessionInfo(
            session_id=record.session_id,
            turn_count=record.turn_count,
            created_at=record.created_at.isoformat(),
            last_turn_at=record.last_turn_at.isoformat(),
        )
        for record in sessions.list()
    ]
