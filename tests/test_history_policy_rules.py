#!/usr/bin/env python3
"""
TEST-HISTORY-001..003（TASK-P0-2.2）
Historical Data Exposure Audit 的防回归守护测试。

最高原则：宁可发现风险，不要掩盖风险。
- TEST-HISTORY-001: 当前代码不得新增虚构政府联系方式（隔离清单外零容忍）
- TEST-HISTORY-002: VERIFIED 政策必须有 source_url；当前数据集 0 条 VERIFIED
- TEST-HISTORY-003: MOCK 政策必须显示 disclaimer

隔离清单（QUARANTINE_MANIFEST）来自 docs/Historical_Data_Exposure_Audit_20260824.md
§5 H2：这些文件是审计已知的历史残留风险，只记录不删除；清单之外的任何新增命中
都会导致测试失败。对外服务层（web/）零容忍、无豁免。
"""

import importlib.util
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = REPO_ROOT / "global_policy_aggregator" / "web"
SEED_DIR = REPO_ROOT / "global_policy_aggregator" / "data" / "seed_data"
VALIDATOR_PATH = REPO_ROOT / "global_policy_aggregator" / "processors" / "provenance_validator.py"

# 审计确认的虚构联系方式/邮箱（历史伪造值，非任何真实机构信息）
FABRICATED_TOKENS = [
    "021-12345678",
    "010-82896688",
    "021-50800880",
    "021-50801234",
    "0755-86543210",
    "010-12345678",
    "quantum@shanghai.gov.cn",
    "policy@zjpark.gov.cn",
]

# 生产代码扫描范围（排除 tests/ 与 docs/：测试负向断言与审计证据引用是刻意保留的）
SCAN_DIRS = ["global_policy_aggregator", "policy_crawler"]
SCAN_EXTS = {".py", ".json", ".txt", ".html", ".sql", ".md", ".js", ".css"}
SKIP_PARTS = {"__pycache__", ".pytest_cache", "node_modules"}

# 对外服务层：虚构联系方式零容忍，无任何豁免
ZERO_TOLERANCE_DIRS = [WEB_DIR]

# TASK-P0-2.2 审计已知残留（只记录，不删除；删除/标注需人工批准）
QUARANTINE_MANIFEST = {
    "global_policy_aggregator/agents/policy_ai_agent.py",
    "global_policy_aggregator/data/raw_policies/shanghai_ai_policy_2024.txt",
    "global_policy_aggregator/scripts/populate_china_policies.py",
    "global_policy_aggregator/scripts/update_policy_data.py",
    "global_policy_aggregator/test_frontend_data.html",
    "policy_crawler/crawlers/china_crawler.py",
    "policy_crawler/data/raw_policies/sample_raw_policies.py",
    "policy_crawler/data/raw_policies/sample_shanghai_policy.txt",
    "policy_crawler/data/raw_policies/shanghai_ai_policy.txt",
    "policy_crawler/data/raw_policies/shanghai_policies_sample.json",
    "policy_crawler/data/raw_policies/shanghai_pudong_ai_policy.txt",
    "policy_crawler/data/raw_policies/shanghai_quantum_policy.txt",
    "policy_crawler/data/raw_policies/shanghai_zhangjiang_tax_policy.txt",
    "policy_crawler/data/raw_policies/shenzhen_autonomous_driving_requirements.txt",
    "policy_crawler/data/structured_policies/shanghai-qingpu-ai-hub-2024.json",
}


def _iter_scan_files():
    for d in SCAN_DIRS:
        for p in (REPO_ROOT / d).rglob("*"):
            if not p.is_file() or p.suffix.lower() not in SCAN_EXTS:
                continue
            if any(part in SKIP_PARTS for part in p.parts):
                continue
            yield p


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk", errors="replace")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# TEST-HISTORY-001: 当前代码不存在（新增的）fake government contacts
# ---------------------------------------------------------------------------
class TestHistory001NoFabricatedContacts:
    def test_web_serving_layer_has_zero_fabricated_contacts(self):
        """对外服务层（templates + web 服务器）对虚构联系方式零容忍、无豁免。"""
        violations = []
        for base in ZERO_TOLERANCE_DIRS:
            for p in base.rglob("*"):
                if not p.is_file() or p.suffix.lower() not in SCAN_EXTS:
                    continue
                if any(part in SKIP_PARTS for part in p.parts):
                    continue
                text = _read_text(p)
                for token in FABRICATED_TOKENS:
                    if token in text:
                        violations.append(f"{p.relative_to(REPO_ROOT).as_posix()}: {token}")
        assert not violations, "对外服务层发现虚构政府联系方式：" + "; ".join(violations)

    def test_no_new_fabricated_contact_files_outside_quarantine(self):
        """隔离清单之外的生产文件不得包含任何已知虚构联系方式。"""
        new_violations = []
        for p in _iter_scan_files():
            text = _read_text(p)
            found = [t for t in FABRICATED_TOKENS if t in text]
            if not found:
                continue
            rel = p.relative_to(REPO_ROOT).as_posix()
            if rel not in QUARANTINE_MANIFEST:
                new_violations.append(f"{rel}: {', '.join(found)}")
        assert not new_violations, (
            "发现隔离清单之外的虚构政府联系方式（新增风险，禁止合入）："
            + "; ".join(new_violations)
        )

    def test_quarantine_manifest_is_minimal(self):
        """清单内文件若已不再含虚构数据，应从清单移除（风险已消除须及时销账）。"""
        stale = []
        actual = {}
        for p in _iter_scan_files():
            rel = p.relative_to(REPO_ROOT).as_posix()
            if rel in QUARANTINE_MANIFEST:
                actual[rel] = True
                if not any(t in _read_text(p) for t in FABRICATED_TOKENS):
                    stale.append(rel)
        missing = QUARANTINE_MANIFEST - set(actual)
        assert not missing, f"隔离清单包含不存在的文件：{sorted(missing)}"
        assert not stale, f"以下文件已无虚构数据，请从隔离清单移除：{sorted(stale)}"


# ---------------------------------------------------------------------------
# TEST-HISTORY-002: VERIFIED policy 必须有 source_url
# ---------------------------------------------------------------------------
class TestHistory002VerifiedRequiresSourceUrl:
    def test_validator_rejects_verified_without_source_url(self):
        pv = _load_module("p22_provenance_validator", VALIDATOR_PATH)
        result = pv.validate_policy_record(
            {"title": "X", "verification_status": "verified"}
        )
        assert result["valid"] is False
        assert any("DATA-INTEGRITY-002" in issue for issue in result["issues"])

    def test_current_datasets_contain_zero_verified_records(self):
        """当前没有任何数据完成了真实核验 —— 数据集必须如实保持 0 条 VERIFIED。"""
        verified_found = []
        for json_file in sorted(SEED_DIR.glob("*.json")):
            data = json.loads(json_file.read_text(encoding="utf-8-sig"))
            records = data if isinstance(data, list) else data.get("policies", [data])
            for i, rec in enumerate(records):
                if isinstance(rec, dict) and rec.get("verification_status") == "verified":
                    verified_found.append(f"{json_file.name}[{i}]")
        for json_file in sorted((REPO_ROOT / "policy_crawler" / "data").rglob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8-sig"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            records = data if isinstance(data, list) else [data]
            for i, rec in enumerate(records):
                if isinstance(rec, dict) and rec.get("verification_status") == "verified":
                    verified_found.append(f"{json_file.relative_to(REPO_ROOT).as_posix()}[{i}]")
        assert not verified_found, (
            "发现 VERIFIED 记录，但真实核验工作流尚未建立（见 docs/Policy_Data_Governance.md）："
            + ", ".join(verified_found)
        )

    def test_portal_embedded_policies_are_not_verified(self):
        portal = _load_module("p22_interactive_ai_server", WEB_DIR / "interactive_ai_server.py")
        for i, policy in enumerate(portal.policies):
            status = policy.get("verification_status")
            assert status != "verified", f"门户内嵌政策 [{i}] 不得为 verified"


# ---------------------------------------------------------------------------
# TEST-HISTORY-003: MOCK policy 必须显示 disclaimer
# ---------------------------------------------------------------------------
class TestHistory003MockMustShowDisclaimer:
    @pytest.fixture(scope="class")
    def home_html(self):
        portal = _load_module("p22b_interactive_ai_server", WEB_DIR / "interactive_ai_server.py")
        from fastapi.testclient import TestClient
        response = TestClient(portal.app).get("/")
        assert response.status_code == 200
        return response.text

    def test_portal_has_mock_policies_and_all_are_disclosed(self, home_html):
        portal = _load_module("p22c_interactive_ai_server", WEB_DIR / "interactive_ai_server.py")
        mock_count = sum(1 for p in portal.policies if p.get("is_mock"))
        assert mock_count == len(portal.policies) > 0, "门户全部政策必须显式标记 mock"
        # 页面级免责声明 + 卡片级 MOCK 徽章渲染逻辑必须存在
        assert "MOCK 演示数据" in home_html, "缺少页面级 MOCK 免责声明"
        assert "policy.is_mock" in home_html, "缺少卡片级 MOCK 标签渲染"

    def test_pdf_download_carries_disclaimer(self):
        portal = _load_module("p22d_interactive_ai_server", WEB_DIR / "interactive_ai_server.py")
        source = Path(portal.__file__).read_text(encoding="utf-8")
        assert re.search(r"MOCK / DEMONSTRATION DATA", source), "PDF 免责声明缺失"

    def test_seed_datasets_with_mock_records_carry_mock_marker(self):
        """含 mock 记录的数据集文件自身必须带可识别的 mock 标记。"""
        for json_file in sorted(SEED_DIR.glob("*.json")):
            text = json_file.read_text(encoding="utf-8-sig")
            if '"is_mock": true' in text or '"is_mock":true' in text:
                assert re.search(r'"verification_status"\s*:\s*"mock"', text), (
                    f"{json_file.name}: is_mock 记录缺少 verification_status=mock"
                )
