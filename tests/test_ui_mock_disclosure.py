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
    def test_home_page_contains_mock_banner(self, home_html):
        assert "MOCK 演示数据" in home_html, "首页必须包含 MOCK 披露横幅"
        assert "未经官方来源核验" in home_html

    def test_home_banner_appears_before_policy_content(self, home_html):
        banner_pos = home_html.find("数据声明")
        results_pos = home_html.find('id="results"')
        assert banner_pos != -1 and results_pos != -1
        assert banner_pos < results_pos, "横幅必须在政策内容之前（页面顶部）"

    def test_main_template_contains_disclosure_marker(self):
        index_html = (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")
        assert DISCLOSURE_MARKER in index_html
        assert "DEMONSTRATION DATA" in index_html


# ---------------------------------------------------------------------------
# TEST-UI-MOCK-002: Mock Policy Card 必须显示 MOCK 状态
# ---------------------------------------------------------------------------
class TestUIMock002CardMockLabel:
    def test_card_renderer_shows_mock_badge_when_is_mock(self, home_html):
        # 卡片渲染逻辑必须依据 is_mock 输出醒目标签
        assert "policy.is_mock" in home_html
        assert "MOCK / 演示数据 · 未经官方来源核验" in home_html

    def test_all_embedded_policies_are_flagged_mock(self, portal):
        assert len(portal.policies) == 12
        for policy in portal.policies:
            assert policy.get("is_mock") is True
            assert policy.get("verification_status") == "mock"


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

    def test_contact_section_labeled_unverified(self, home_html):
        assert "联系方式：未核验" in home_html


# ---------------------------------------------------------------------------
# TEST-UI-MOCK-004: phone/email/address 为 null 时不得生成虚构联系方式
# ---------------------------------------------------------------------------
class TestUIMock004NullContactsStayNull:
    def test_all_embedded_contacts_are_null(self, portal):
        for policy in portal.policies:
            contact = policy.get("official_contact", {})
            assert contact.get("phone") is None
            assert contact.get("email") is None
            assert contact.get("address") is None
            assert contact.get("contact_status") == "unverified"

    def test_rendering_falls_back_to_unverified_text(self, home_html):
        # JS 渲染必须对 null 字段显示"未核验"，而不是任何占位号码
        assert "未核验（待官方认领后提供）" in home_html
        # 页面中不得残留任何历史虚构号码
        for fabricated in ("010-82896688", "021-50801234", "policy@zjpark.gov.cn"):
            assert fabricated not in home_html


# ---------------------------------------------------------------------------
# TEST-UI-MOCK-005: PDF Mock Policy 必须包含 Mock Disclaimer
# ---------------------------------------------------------------------------
class TestUIMock005PdfDisclaimer:
    def test_pdf_endpoint_returns_valid_pdf(self, portal):
        from fastapi.testclient import TestClient
        client = TestClient(portal.app)
        response = client.get("/api/policy/1/pdf")
        assert response.status_code == 200
        assert response.content[:4] == b"%PDF"

    def test_pdf_generator_source_contains_disclaimer(self):
        # PDF 生成源码必须在正文区输出免责声明（压缩流内文本不可直接检索，
        # 因此以源码断言 + 上方运行时端点证据共同构成验收）
        source = (WEB_DIR / "interactive_ai_server.py").read_text(encoding="utf-8")
        assert "MOCK / DEMONSTRATION DATA" in source
        assert "官方联系方式" not in source, "PDF 不得再使用'官方联系方式'表述"


# ---------------------------------------------------------------------------
# TEST-UI-MOCK-006: 所有当前 Web Server 入口均遵循 Mock Disclosure
# ---------------------------------------------------------------------------
class TestUIMock006AllEntriesDisclose:
    def test_all_templates_carry_disclosure_banner(self):
        templates = sorted(TEMPLATES_DIR.glob("*.html"))
        assert len(templates) >= 8, "templates must not be deleted (INV-000)"
        for template in templates:
            content = template.read_text(encoding="utf-8")
            assert DISCLOSURE_MARKER in content, f"{template.name} 缺少 MOCK 披露横幅"

    def test_simple_server_inline_html_discloses(self):
        source = (WEB_DIR / "simple_server.py").read_text(encoding="utf-8")
        assert DISCLOSURE_MARKER in source
        assert "LEGACY / DEMONSTRATION ONLY" in source

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
