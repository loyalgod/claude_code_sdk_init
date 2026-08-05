"""Web 层测试：用 FakeRunner 注入，验证 SSE 路由与事件桥接。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from core.models import AgentRunResult
from core.sessions import SessionStore
from web.app import create_app


class FakeRunner:
    """不发起真实 API 的替身 runner。"""

    async def run(self, *, job, emit):
        await emit("text_delta", {"text": "你好"})
        return AgentRunResult(text="你好", session_id="fake-session-1")


def _client(sessions: SessionStore | None = None) -> TestClient:
    return TestClient(create_app(runner=FakeRunner(), sessions=sessions))


def test_health() -> None:
    response = _client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_sse_stream() -> None:
    with _client().stream("POST", "/v1/chat", json={"text": "hi"}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())
    assert "event: start" in body
    assert "event: text_delta" in body
    assert "你好" in body
    assert "event: result" in body
    assert "fake-session-1" in body


def test_list_sessions_empty() -> None:
    response = _client().get("/v1/sessions")
    assert response.status_code == 200
    assert response.json() == []


def test_list_sessions_records() -> None:
    store = SessionStore()
    store.upsert("session-abc")
    response = _client(sessions=store).get("/v1/sessions")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["session_id"] == "session-abc"
    assert body[0]["turn_count"] == 1
