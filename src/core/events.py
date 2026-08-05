"""事件协议：CLI 与 Web 入口共同遵循的事件名与回调类型。

入口侧实现 ``EmitFunc``，把事件输出到终端或桥接为 SSE 帧。
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

EmitFunc = Callable[[str, dict], Awaitable[None]]

# 事件名常量
EVENT_TEXT_DELTA = "text_delta"  # 文本增量
EVENT_THINKING_DELTA = "thinking_delta"  # 思考增量
EVENT_TOOL_STARTED = "tool_started"  # 工具开始
EVENT_TOOL_COMPLETED = "tool_completed"  # 工具完成
EVENT_RESULT = "result"  # 最终结果（含 session_id）
EVENT_ERROR = "error"  # 运行错误
