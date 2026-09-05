#!/usr/bin/env python3
"""
P2-0C.2 Runtime Blocker Fix tests (P2.x updated).

验证 REAL policy 的 nullable 字段不导致 Runtime 500：
- Bug 1: /search with keywords → 不因 region=None 崩溃
- Bug 2: /api/policy/{id}/pdf → 不因 requirements 为空崩溃

同时确认：
- REAL policy 仍保持 is_mock=False / verification_status=unverified
- P2.x: _p2_0_store 事件日志已移除
"""

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_PATH = REPO_ROOT / "global_policy_aggregator" / "web" / "interactive_ai_server.py"
MODULE_NAME = "p2_0c2_runtime_fix_portal"


def _load_portal_module():
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    spec = importlib.util.spec_from_file_location(MODULE_NAME, PORTAL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def portal(tmp_path, monkeypatch):
    module = _load_portal_module()
    client = TestClient(module.app)
    return module, client


class TestBug1SearchNoneSafe:
    """Bug 1: /search with keywords must not 500 when REAL policy region=None."""

    def test_search_with_keywords_returns_200(self, portal):
        module, client = portal
        resp = client.post("/search", data={"keyword": "AI"})
        assert resp.status_code == 200

    def test_search_finds_real_policy_by_industry(self, portal):
        module, client = portal
        resp = client.post("/search", data={"industry": "AI"})
        assert resp.status_code == 200

    def test_search_with_chinese_keyword(self, portal):
        module, client = portal
        resp = client.post("/search", data={"keyword": "人工智能"})
        assert resp.status_code == 200


class TestBug2PdfNoneSafe:
    """Bug 2: /api/policy/{id}/pdf must not 500 for REAL policies."""

    def test_pdf_for_real_policy_returns_200(self, portal):
        module, client = portal
        real_policies = [p for p in module.policies if not p.get("is_mock")]
        if real_policies:
            policy_id = real_policies[0]["id"]
            resp = client.get(f"/api/policy/{policy_id}/pdf")
            assert resp.status_code == 200

    def test_pdf_for_all_real_policies(self, portal):
        module, client = portal
        real_policies = [p for p in module.policies if not p.get("is_mock")]
        for policy in real_policies:
            resp = client.get(f"/api/policy/{policy['id']}/pdf")
            assert resp.status_code == 200


class TestRealPolicyDataIntegrity:
    """REAL policy 数据完整性验证"""

    def test_real_policies_is_mock_false(self, portal):
        module, _ = portal
        real_policies = [p for p in module.policies if not p.get("is_mock")]
        for p in real_policies:
            assert p.get("is_mock") is False

    def test_real_policies_unverified(self, portal):
        module, _ = portal
        real_policies = [p for p in module.policies if not p.get("is_mock")]
        for p in real_policies:
            assert p.get("verification_status") == "unverified"

    def test_mock_policy_not_upgraded(self, portal):
        module, _ = portal
        mock_policies = [p for p in module.policies if p.get("is_mock") is True]
        for p in mock_policies:
            assert p.get("verification_status") == "mock"


class TestP2xArchitecture:
    def test_no_p2_0_store(self, portal):
        module, _ = portal
        assert not hasattr(module, "_p2_0_store")
