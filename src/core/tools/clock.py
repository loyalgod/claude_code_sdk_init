"""示例工具：获取当前时间（Asia/Shanghai）。"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import claude_agent_sdk as sdk

SHANGHAI = ZoneInfo("Asia/Shanghai")


@sdk.tool(
    "get_current_time",
    "获取当前时间（Asia/Shanghai），返回 ISO 8601 格式字符串。"
    "回答涉及当前时间时调用。",
    {},
)
async def get_current_time(args: dict) -> dict:
    now = datetime.now(SHANGHAI)
    return {"content": [{"type": "text", "text": now.isoformat()}]}
