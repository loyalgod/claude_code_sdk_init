"""会话元数据表。

真实对话状态由 SDK 内部维护（通过 ``resume`` 续跑），本表只记录会话的
元信息（创建/最后活跃时间、轮次），为 Web 侧提供会话列表与生命周期管理，
并预留替换为 Redis/DB 的持久化接口。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class SessionRecord:
    session_id: str
    created_at: datetime
    last_turn_at: datetime
    turn_count: int = 0


class SessionStore:
    """内存会话表；复用时替换为持久化实现。"""

    def __init__(self) -> None:
        self._records: dict[str, SessionRecord] = {}

    def get(self, session_id: str) -> SessionRecord | None:
        return self._records.get(session_id)

    def upsert(self, session_id: str) -> SessionRecord:
        """新增或更新（touch）一条会话记录。"""
        now = datetime.now(timezone.utc)
        record = self._records.get(session_id)
        if record is None:
            record = SessionRecord(
                session_id=session_id,
                created_at=now,
                last_turn_at=now,
                turn_count=0,
            )
            self._records[session_id] = record
        record.last_turn_at = now
        record.turn_count += 1
        return record

    def delete(self, session_id: str) -> None:
        self._records.pop(session_id, None)

    def list(self) -> list[SessionRecord]:
        return sorted(
            self._records.values(),
            key=lambda record: record.last_turn_at,
            reverse=True,
        )

    @staticmethod
    def new_session_id() -> str:
        return f"session-{uuid.uuid4().hex[:12]}"
