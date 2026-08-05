"""公共小工具。"""

from __future__ import annotations

from typing import Any


def sanitize(value: Any, max_list: int = 20, max_str: int = 500) -> Any:
    """对事件载荷做脱敏/截断，避免把敏感或超大参数写入日志与前端。"""
    if isinstance(value, dict):
        return {str(key): sanitize(item, max_list, max_str) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item, max_list, max_str) for item in value[:max_list]]
    if isinstance(value, str):
        return value[:max_str]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:max_str]
