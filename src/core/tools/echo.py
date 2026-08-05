"""示例工具：原样回显文本，演示参数校验与结果返回规范。"""

from __future__ import annotations

import claude_agent_sdk as sdk


@sdk.tool(
    "echo",
    "原样返回你传入的 text 参数，用于演示工具的参数校验与返回规范。",
    {"text": str},
)
async def echo(args: dict) -> dict:
    text = str(args.get("text") or "")
    return {"content": [{"type": "text", "text": text}]}
