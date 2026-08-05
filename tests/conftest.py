"""测试公共 fixture。"""

from __future__ import annotations

import os

import pytest

from core.config import Settings


@pytest.fixture
def settings() -> Settings:
    """不读取 .env 的 Settings（仍读取真实环境变量，适合单测）。"""
    return Settings(_env_file=None)


@pytest.fixture
def has_api_key():
    """无 API Key 时跳过真实联调类测试。"""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("未配置 ANTHROPIC_API_KEY，跳过真实联调测试")
