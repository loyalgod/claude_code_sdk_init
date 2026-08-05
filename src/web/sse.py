"""SSE 帧编码与流式响应工具。"""

from __future__ import annotations

import json
from typing import Any


def sse_frame(event: str, data: dict[str, Any]) -> bytes:
    """把事件序列化为一个 SSE 帧：``event: <name>\\ndata: <json>\\n\\n``。"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")
