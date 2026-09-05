"""P2-0B.6: E3 Outreach Recording tests (P2.x updated).

P2.x: Outreach recording 功能已从生产服务器移除。
本测试验证该功能不再存在，且生产代码不包含相关功能。
"""

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_PATH = REPO_ROOT / "global_policy_aggregator" / "web" / "interactive_ai_server.py"
MODULE_NAME = "p2_0b6_portal_under_test"


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


class TestP2xOutreachArchitecture:
    def test_no_outreach_endpoints(self, portal):
        """P2.x: 外联相关端点不存在"""
        _, client = portal
        # 验证没有外联端点
        resp = client.post("/api/outreach", json={})
        assert resp.status_code == 404

    def test_no_p2_0_store(self, portal):
        """P2.x: 生产代码不再包含 _p2_0_store"""
        module, _ = portal
        assert not hasattr(module, "_p2_0_store")

    def test_search_still_works(self, portal):
        """搜索功能仍然正常"""
        _, client = portal
        resp = client.post("/search", data={"keyword": "AI"})
        assert resp.status_code == 200

    def test_policy_view_still_works(self, portal):
        """政策查看仍然正常"""
        module, client = portal
        policy_id = module.policies[0]["id"]
        resp = client.get(f"/policy/{policy_id}")
        assert resp.status_code == 200

    def test_pdf_download_still_works(self, portal):
        """PDF 下载仍然正常"""
        module, client = portal
        policy_id = module.policies[0]["id"]
        resp = client.get(f"/api/policy/{policy_id}/pdf")
        assert resp.status_code == 200
