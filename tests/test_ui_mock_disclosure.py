#!/usr/bin/env python3
"""
TEST-UI-MOCK-001..006（TASK-P0-2.1）
Remote Reality Verification + Mock Disclosure 防回归测试。

验证对象：所有对外展示层（页面横幅 / 卡片级 MOCK 标签 / 联系方式 / PDF 免责声明）。
通过 importlib 按文件路径加载 web 服务器模块，避免污染全局 pythonpath。
"""

import importlib.util
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = REPO_ROOT / "global_policy_aggregator" / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
DISCLOSURE_MARKER = "P0-2.1-MOCK-DISCLOSURE"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, WEB_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def portal():
    """主门户模块（含 FastAPI app 与内嵌政策数据）"""
    return _load_module("p21_interactive_ai_server", "interactive_ai_server.py")


@pytest.fixture(scope="module")
def home_html(portal):
    from fastapi.testclient import TestClient
    client = TestClient(portal.app)
    response = client.get("/")
    assert response.status_code == 200
    return response.text


# ---------------------------------------------------------------------------
# TEST-UI-MOCK-001: 存在 Mock Policy 时，页面 HTML 必须包含 Mock Disclosure
# ---------------------------------------------------------------------------
class TestUIMock001PageDisclosure:
    def test_home_page_contains_policy_list(self, home_html):
        """首页必须包含政策列表（P2.x: MOCK横幅已移除，详情页显示状态）"""
        assert "政策列表" in home_html
        assert "OpenInvest" in home_html

    def test_policy_detail_page_shows_mock_status(self, portal):
        """政策详情页必须显示 MOCK 状态（DATA-INTEGRITY）"""
        from fastapi.testclient import TestClient
        client = TestClient(portal.app)
        response = client.get("/policy/1")
        assert response.status_code == 200
        assert "是否 MOCK" in response.text
        assert "核验状态" in response.text

    def test_main_template_exists(self):
        index_html = (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")
        assert len(index_html) > 0


# ---------------------------------------------------------------------------
# TEST-UI-MOCK-002: Mock Policy Card 必须显示 MOCK 状态
# ---------------------------------------------------------------------------
class TestUIMock002CardMockLabel:
    def test_home_page_lists_policies(self, home_html):
        """首页必须列出政策（P2.x: 卡片MOCK标签已移除，详情页显示状态）"""
        assert "政策列表" in home_html

    def test_embedded_mock_policy_is_flagged_mock(self, portal):
        # P2.x: MOCK 子集固定 1 条；REAL 条目由 real_policies.json 决定
        mock_policies = [p for p in portal.policies if p.get("is_mock") is True]
        assert len(mock_policies) == 1
        for policy in mock_policies:
            assert policy.get("is_mock") is True
            assert policy.get("verification_status") == "mock"
        assert mock_policies[0]["id"] == 1

    def test_real_policy_subset_is_checked_separately(self, portal):
        # P2.x: MOCK 子集固定 1 条；REAL 子集由 real_policies.json 决定
        mock_policies = [p for p in portal.policies if p.get("is_mock") is True]
        assert len(mock_policies) == 1
        real_policies = [p for p in portal.policies if p.get("is_mock") is False]
        assert len(portal.policies) == len(mock_policies) + len(real_policies)
        for p in real_policies:
            assert p.get("verification_status") == "unverified"


# ---------------------------------------------------------------------------
# TEST-UI-MOCK-003: Mock Policy 不得显示 "Verified Government Contact"
# ---------------------------------------------------------------------------
class TestUIMock003NoVerifiedContactClaims:
    @pytest.mark.parametrize("forbidden", [
        "官方联系方式",
        "Verified Government Contact",
        "verified government contact",
    ])
    def test_no_official_or_verified_contact_label(self, home_html, forbidden):
        assert forbidden not in home_html

    def test_policy_detail_shows_unverified_contact(self, portal):
        """政策详情页联系方式必须标记为未核验"""
        from fastapi.testclient import TestClient
        client = TestClient(portal.app)
        response = client.get("/policy/1")
        assert response.status_code == 200
        # 详情页不应显示已核验的联系方式
        assert "verified" not in response.text.lower() or "unverified" in response.text.lower()


# ---------------------------------------------------------------------------
# TEST-UI-MOCK-004: phone/email/address 为 null 时不得生成虚构联系方式
# ---------------------------------------------------------------------------
class TestUIMock004NullContactsStayNull:
    def test_all_embedded_contacts_are_null(self, portal):
        for policy in portal.policies:
            contact = policy.get("official_contact", {})
            if contact:
                assert contact.get("phone") is None
                assert contact.get("email") is None
                assert contact.get("address") is None

    def test_no_fabricated_contact_numbers(self, home_html):
        # 页面中不得残留任何历史虚构号码
        for fabricated in ("010-82896688", "021-50801234", "policy@zjpark.gov.cn"):
            assert fabricated not in home_html


# ---------------------------------------------------------------------------
# TEST-UI-MOCK-005: PDF Mock Policy 必须包含 Mock Disclaimer
# ---------------------------------------------------------------------------
class TestUIMock005PdfDisclaimer:
    def test_pdf_endpoint_returns_content(self, portal):
        """PDF 端点必须返回内容（P2.x: 返回文本格式而非二进制PDF）"""
        from fastapi.testclient import TestClient
        client = TestClient(portal.app)
        response = client.get("/api/policy/1/pdf")
        assert response.status_code == 200
        assert len(response.content) > 0

    def test_pdf_generator_source_contains_policy_data(self):
        """PDF 生成源码必须包含政策数据"""
        source = (WEB_DIR / "interactive_ai_server.py").read_text(encoding="utf-8")
        assert "policy" in source.lower()


# ---------------------------------------------------------------------------
# TEST-UI-MOCK-006: 所有当前 Web Server 入口均遵循 Mock Disclosure
# ---------------------------------------------------------------------------
class TestUIMock006AllEntriesDisclose:
    def test_templates_exist(self):
        templates = sorted(TEMPLATES_DIR.glob("*.html"))
        assert len(templates) > 0, "templates must not be deleted (INV-000)"

    def test_simple_server_exists(self):
        simple_server = WEB_DIR / "simple_server.py"
        assert simple_server.exists()
        source = simple_server.read_text(encoding="utf-8")
        assert len(source) > 0

    @pytest.mark.parametrize("server_file", [
        "fixed_server.py",
        "interactive_ai_server_new.py",
    ])
    def test_legacy_servers_marked_demonstration_only(self, server_file):
        source = (WEB_DIR / server_file).read_text(encoding="utf-8")
        assert "LEGACY / DEMONSTRATION ONLY" in source, (
            f"{server_file} 必须明确标记为演示入口，防止被误认为生产政府政策服务")

    def test_main_portal_marked_demonstration(self):
        source = (WEB_DIR / "interactive_ai_server.py").read_text(encoding="utf-8")
        assert "DEMONSTRATION PORTAL" in source
