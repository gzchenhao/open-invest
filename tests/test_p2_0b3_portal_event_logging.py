"""P2-0B.3: Portal API tests (P2.x updated).

验证 interactive_ai_server 的当前生产行为：
- POST /search -> 搜索政策
- GET /api/policy/{id}/pdf (found) -> 返回政策内容
- GET /api/policy/{id}/pdf (not found) -> 返回错误
P2.x: _p2_0_store 事件日志已移除，不再产生 POLICY_SEARCHED/POLICY_VIEWED 事件。
"""

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_PATH = REPO_ROOT / "global_policy_aggregator" / "web" / "interactive_ai_server.py"
MODULE_NAME = "p2_0b3_portal_under_test"


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


class TestSearchEndpoint:
    def test_search_returns_200(self, portal):
        """POST /search 必须返回 200"""
        module, client = portal
        resp = client.post("/search", data={"keyword": "补贴"})
        assert resp.status_code == 200

    def test_search_with_empty_keyword(self, portal):
        """空关键词搜索仍返回 200"""
        module, client = portal
        resp = client.post("/search", data={"keyword": ""})
        assert resp.status_code == 200

    def test_homepage_still_200(self, portal):
        """首页仍返回 200"""
        _, client = portal
        resp = client.get("/")
        assert resp.status_code == 200
        assert "OpenInvest" in resp.text

    def test_no_event_logging_store(self, portal):
        """P2.x: 生产代码不再包含 _p2_0_store"""
        module, _ = portal
        assert not hasattr(module, "_p2_0_store")
        assert not hasattr(module, "_get_p2_0_store")


class TestPolicyPdf:
    def test_pdf_found_returns_200(self, portal):
        """GET /api/policy/{id}/pdf 找到政策时返回 200"""
        module, client = portal
        policy_id = module.policies[0]["id"]
        resp = client.get(f"/api/policy/{policy_id}/pdf")
        assert resp.status_code == 200

    def test_pdf_not_found_returns_error(self, portal):
        """GET /api/policy/{id}/pdf 未找到政策时返回 404"""
        _, client = portal
        resp = client.get("/api/policy/999999/pdf")
        assert resp.status_code == 404
