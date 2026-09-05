"""P2-0B.4: E1 Observability tests (P2.x updated).

验证当前生产行为：
- 首页搜索可用
- 政策详情页可用
- PDF 下载可用
P2.x: _p2_0_store 事件日志、/api/event/search、/api/project-intent 已移除。
"""

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_PATH = REPO_ROOT / "global_policy_aggregator" / "web" / "interactive_ai_server.py"
MODULE_NAME = "p2_0b4_portal_under_test"


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


class TestSearchFunctionality:
    def test_search_works(self, portal):
        """搜索功能正常工作"""
        module, client = portal
        resp = client.post("/search", data={"keyword": "AI"})
        assert resp.status_code == 200

    def test_homepage_contains_search_form(self, portal):
        """首页包含搜索表单"""
        _, client = portal
        resp = client.get("/")
        assert resp.status_code == 200
        assert "搜索" in resp.text


class TestPolicyView:
    def test_policy_detail_page(self, portal):
        """政策详情页正常显示"""
        module, client = portal
        policy_id = module.policies[0]["id"]
        resp = client.get(f"/policy/{policy_id}")
        assert resp.status_code == 200

    def test_pdf_download(self, portal):
        """PDF 下载正常"""
        module, client = portal
        policy_id = module.policies[0]["id"]
        resp = client.get(f"/api/policy/{policy_id}/pdf")
        assert resp.status_code == 200


class TestP2xArchitecture:
    def test_no_event_search_endpoint(self, portal):
        """P2.x: /api/event/search 端点不存在"""
        _, client = portal
        resp = client.post("/api/event/search")
        assert resp.status_code == 404

    def test_no_project_intent_endpoint(self, portal):
        """P2.x: /api/project-intent 端点不存在"""
        _, client = portal
        resp = client.post("/api/project-intent", json={"policy_id": "1"})
        assert resp.status_code == 404

    def test_no_p2_0_store(self, portal):
        """P2.x: 生产代码不再包含 _p2_0_store"""
        module, _ = portal
        assert not hasattr(module, "_p2_0_store")
