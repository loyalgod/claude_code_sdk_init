"""CLI 调试入口（console script: ``my-agent``）。

定位：本地调试/演示工具，产品入口是 ``web/``。
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

from core.config import Settings
from core.events import (
    EVENT_TEXT_DELTA,
    EVENT_THINKING_DELTA,
    EVENT_TOOL_COMPLETED,
    EVENT_TOOL_STARTED,
)
from core.models import TurnJob
from core.runner import AgentRunError, ClaudeAgentRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="my-agent", description="Claude Agent SDK 模板 CLI")
    parser.add_argument("text", nargs="?", default="你好，介绍一下你自己。")
    parser.add_argument("--model", help="覆盖 AGENT_MODEL 配置")
    parser.add_argument("--resume", help="恢复已有会话的 session_id")
    parser.add_argument("--max-turns", type=int, help="覆盖 MAX_TURNS 配置")
    parser.add_argument("--no-stream", action="store_true", help="关闭流式输出")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings()
    if args.model:
        settings.agent_model = args.model
    if args.max_turns:
        settings.max_turns = args.max_turns

    runner = ClaudeAgentRunner(settings)
    job = TurnJob(text=args.text, session_id=args.resume)

    async def _emit(event: str, data: dict[str, Any]) -> None:
        if event == EVENT_TEXT_DELTA:
            print(data.get("text", ""), end="", flush=True)
        elif event == EVENT_THINKING_DELTA:
            print(f"\n[思考] {data.get('text', '')}", file=sys.stderr, flush=True)
        elif event == EVENT_TOOL_STARTED:
            name = data.get("name", "?")
            print(f"\n[工具] {name} {data.get('input') or ''}", file=sys.stderr, flush=True)
        elif event == EVENT_TOOL_COMPLETED:
            name = data.get("name", "?")
            is_error = data.get("is_error")
            print(f"[工具完成] {name} is_error={is_error}", file=sys.stderr, flush=True)

    async def _run() -> int:
        try:
            result = await runner.run(job=job, emit=_emit)
            if not args.no_stream:
                print()
            print(f"\n[session_id] {result.session_id}")
            return 0
        except AgentRunError as exc:
            print(f"\n[错误] {exc}", file=sys.stderr)
            return 1

    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())
