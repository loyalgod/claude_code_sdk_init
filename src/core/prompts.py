"""系统提示词构建。"""

from __future__ import annotations


def build_system_prompt(agent_name: str) -> str:
    """构造 Agent 系统提示词。

    模板语义：介绍角色定位，并强调工具调用规范。复用时按业务改写本函数。
    """
    return (
        f"你是 {agent_name}，一个基于 Claude Agent SDK 构建的智能助手。\n"
        "\n"
        "工作规范：\n"
        "1. 需要实时信息或操作外部能力时，先调用可用工具，不要凭空编造。\n"
        "2. 工具返回的内容是事实来源，回答要基于工具结果组织。\n"
        "3. 一次回答保持结构化：先结论，再依据。\n"
        "4. 若无法通过工具得到结论，明确说明能力边界，不臆断。\n"
    )
