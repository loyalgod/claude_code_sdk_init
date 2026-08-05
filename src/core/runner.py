"""Agent 编排核心：封装 Claude Agent SDK 的完整运行生命周期。

职责：
- 组装 ``ClaudeAgentOptions``（模型、提示词、工具、MCP server、权限、恢复会话）；
- 通过 ``ClaudeSDKClient`` 发送用户消息并分发流式事件；
- 归一化结果、处理超时与中断。
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from typing import Any

import claude_agent_sdk as sdk

from core.config import Settings
from core.events import (
    EVENT_TEXT_DELTA,
    EVENT_THINKING_DELTA,
    EVENT_TOOL_COMPLETED,
    EVENT_TOOL_STARTED,
    EmitFunc,
)
from core.mcp import build_mcp_server
from core.models import AgentRunResult, TurnJob
from core.permissions import DefaultPermissionPolicy
from core.prompts import build_system_prompt
from core.sessions import SessionStore
from core.tools import build_default_registry
from core.utils import sanitize


class AgentRunError(RuntimeError):
    """Agent 运行失败（超时、SDK 错误、无结果等）。"""


class ClaudeAgentRunner:
    """无共享可变运行状态的编排器，可支撑 Web 并发场景。

    说明：当前 ``interrupt`` 只作用于最近一次 run；若需要按会话精确中断，
    请将 client 实例登记到会话维度（模板预留扩展点）。
    """

    def __init__(self, settings: Settings, sessions: SessionStore | None = None) -> None:
        self.settings = settings
        self.sessions = sessions
        self._client: sdk.ClaudeSDKClient | None = None
        self._interrupted = False

    async def interrupt(self) -> None:
        """中断当前正在执行的 run。"""
        self._interrupted = True
        if self._client is not None:
            try:
                await self._client.interrupt()
            except Exception:
                return

    async def run(self, *, job: TurnJob, emit: EmitFunc) -> AgentRunResult:
        """执行一轮对话，事件通过 ``emit`` 回调输出。"""
        self._interrupted = False
        registry = build_default_registry()
        mcp_tool_names = [
            f"mcp__{self.settings.mcp_server_name}__{name}" for name in registry.names
        ]
        policy = DefaultPermissionPolicy(self.settings)
        mcp_server = build_mcp_server(
            registry,
            name=self.settings.mcp_server_name,
            version=self.settings.app_version,
        )

        options = sdk.ClaudeAgentOptions(
            model=self.settings.agent_model,
            system_prompt=build_system_prompt(self.settings.agent_name),
            tools=[*self.settings.allowed_builtin_tools, "AskUserQuestion", *mcp_tool_names],
            allowed_tools=mcp_tool_names,
            disallowed_tools=self.settings.disallowed_tools,
            permission_mode=self.settings.permission_mode,
            mcp_servers={self.settings.mcp_server_name: mcp_server},
            strict_mcp_config=True,
            can_use_tool=policy.can_use_tool,
            max_turns=self.settings.max_turns,
            resume=job.session_id,
            cwd=str(self.settings.agent_cwd.resolve()),
            env=self.settings.claude_env(),
            setting_sources=[],
            skills=[],
            include_partial_messages=True,
        )

        assistant_text: list[str] = []
        final_text = ""
        session_id = job.session_id
        started_tools: dict[str, tuple[str, float]] = {}

        try:
            async with asyncio.timeout(self.settings.agent_timeout_seconds):
                async with sdk.ClaudeSDKClient(options) as client:
                    self._client = client
                    await client.query(self._message_stream(job))
                    async for message in client.receive_response():
                        if self._interrupted:
                            raise asyncio.CancelledError
                        await self._dispatch(
                            message,
                            emit,
                            assistant_text,
                            started_tools,
                            refs={"streamed_text": False, "streamed_thinking": False},
                        )
                        if isinstance(message, sdk.ResultMessage):
                            session_id = message.session_id or session_id
                            if message.is_error:
                                detail = (
                                    message.result
                                    or "; ".join(message.errors or [])
                                    or message.subtype
                                )
                                raise AgentRunError(detail)
                            final_text = (message.result or "").strip()
        except TimeoutError as exc:
            raise AgentRunError(
                f"Agent 单轮执行超过 {self.settings.agent_timeout_seconds} 秒。"
            ) from exc
        finally:
            self._client = None

        final_text = final_text or "".join(assistant_text).strip()
        if not final_text:
            raise AgentRunError("Agent 未返回有效结果。")
        if self.sessions is not None and session_id:
            self.sessions.upsert(session_id)
        return AgentRunResult(text=final_text, session_id=session_id)

    async def _dispatch(
        self,
        message: Any,
        emit: EmitFunc,
        assistant_text: list[str],
        started_tools: dict[str, tuple[str, float]],
        *,
        refs: dict[str, bool],
    ) -> None:
        """把 SDK 消息归一化为模板事件并回调。"""
        # 流式增量：text_delta / thinking_delta
        if isinstance(message, sdk.StreamEvent):
            event = message.event
            if event.get("type") != "content_block_delta":
                return
            delta = event.get("delta") or {}
            if delta.get("type") == "text_delta" and delta.get("text"):
                refs["streamed_text"] = True
                text = str(delta["text"])
                assistant_text.append(text)
                await emit(EVENT_TEXT_DELTA, {"text": text})
            elif delta.get("type") == "thinking_delta" and delta.get("thinking"):
                refs["streamed_thinking"] = True
                await emit(EVENT_THINKING_DELTA, {"text": str(delta["thinking"])})
            return

        # 助手消息：思考块 / 工具调用 / 文本块
        if isinstance(message, sdk.AssistantMessage):
            for block in message.content:
                if isinstance(block, sdk.ThinkingBlock) and not refs["streamed_thinking"]:
                    await emit(EVENT_THINKING_DELTA, {"text": block.thinking})
                elif isinstance(block, sdk.ToolUseBlock):
                    if block.id not in started_tools:
                        started_tools[block.id] = (block.name, time.perf_counter())
                        await emit(
                            EVENT_TOOL_STARTED,
                            {
                                "tool_use_id": block.id,
                                "name": block.name,
                                "input": sanitize(block.input),
                            },
                        )
                elif isinstance(block, sdk.TextBlock) and not refs["streamed_text"]:
                    assistant_text.append(block.text)
                    await emit(EVENT_TEXT_DELTA, {"text": block.text})
            return

        # 工具结果：tool_completed
        content = getattr(message, "content", None)
        if isinstance(content, list):
            for block in content:
                if isinstance(block, sdk.ToolResultBlock):
                    meta = started_tools.pop(block.tool_use_id, None)
                    if meta:
                        await emit(
                            EVENT_TOOL_COMPLETED,
                            {
                                "tool_use_id": block.tool_use_id,
                                "name": meta[0],
                                "is_error": bool(block.is_error),
                                "duration_ms": round((time.perf_counter() - meta[1]) * 1000),
                            },
                        )

    async def _message_stream(self, job: TurnJob) -> AsyncIterator[dict[str, Any]]:
        """构造发送给 SDK 的用户消息流。"""
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": job.text}],
            },
            "parent_tool_use_id": None,
        }
