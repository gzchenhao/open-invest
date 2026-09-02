"""Shared pytest fixtures.

P2-0B.3: interactive_ai_server 的端点会产生 P2-0 实验事件。已有测试通过
TestClient 触发这些端点时，会在未 patch 的模块实例上写入真实 records/ 目录。
本 fixture 将测试进程内 lazy 创建的 store 重定向到一次性 tmp 目录，
保证实验数据（p2_0_experimental/records/）只来自真实行为，不被测试噪音污染。
"""

import pytest


@pytest.fixture(autouse=True)
def _p2_0_records_dir_isolation(tmp_path, monkeypatch):
    monkeypatch.setenv("P2_0_RECORDS_DIR", str(tmp_path / "p2_0_records_default"))
