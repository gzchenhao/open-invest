#!/usr/bin/env python3
"""
TEST-PROVENANCE-001..006（TASK-P0-2）
Policy Provenance & Anti-Hallucination Data Governance 测试。

最高纪律：宁可 null，不要猜。宁可 UNVERIFIED，不要 VERIFIED。

通过 importlib 按文件路径加载 global_policy_aggregator/processors/provenance_validator.py，
避免污染全局 pythonpath（该包下模块名与 policy_crawler 存在同名冲突风险）。
"""

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "global_policy_aggregator" / "processors" / "provenance_validator.py"
SEED_DIR = REPO_ROOT / "global_policy_aggregator" / "data" / "seed_data"


def _load_validator():
    spec = importlib.util.spec_from_file_location("provenance_validator", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pv = _load_validator()


# ---------------------------------------------------------------------------
# TEST-PROVENANCE-001: Mock policy 不得被标记为 VERIFIED
# ---------------------------------------------------------------------------
class TestProvenance001MockNotVerified:
    def test_mock_marked_verified_is_rejected(self):
        record = {
            "title": "MOCK POLICY",
            "is_mock": True,
            "verification_status": "verified",
            "source_url": None,
        }
        result = pv.validate_policy_record(record)
        assert result["valid"] is False
        assert any("DATA-INTEGRITY-005" in issue for issue in result["issues"])

    def test_mock_marked_partially_verified_is_rejected(self):
        record = {
            "title": "MOCK POLICY",
            "is_mock": True,
            "verification_status": "partially_verified",
        }
        result = pv.validate_policy_record(record)
        assert result["valid"] is False

    def test_mock_marked_mock_is_valid(self):
        record = {
            "title": "MOCK POLICY",
            "is_mock": True,
            "verification_status": "mock",
            "source_url": None,
        }
        result = pv.validate_policy_record(record)
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# TEST-PROVENANCE-002: Mock policy 可以没有 source_url
# ---------------------------------------------------------------------------
class TestProvenance002MockMayLackSourceUrl:
    def test_mock_without_source_url_is_valid(self):
        record = {"title": "MOCK POLICY", "is_mock": True, "verification_status": "mock"}
        result = pv.validate_policy_record(record)
        assert result["valid"] is True
        assert result["provenance"].source_url is None

    def test_mock_url_status_missing_is_allowed(self):
        check = pv.validate_source_url(None)
        assert check["url_status"] == pv.UrlStatus.MISSING
        assert "allowed for mock data" in check["reason"]


# ---------------------------------------------------------------------------
# TEST-PROVENANCE-003: VERIFIED 政策必须拥有 source_url
# ---------------------------------------------------------------------------
class TestProvenance003VerifiedRequiresSourceUrl:
    def test_verified_without_source_url_is_rejected(self):
        record = {"title": "TEST POLICY", "verification_status": "verified"}
        result = pv.validate_policy_record(record)
        assert result["valid"] is False
        assert any("DATA-INTEGRITY-002" in issue for issue in result["issues"])

    def test_verified_with_valid_source_url_is_accepted(self):
        # 注：使用 IANA 保留的 .invalid 顶级域，避免在测试中引用/伪造任何真实政府 URL；
        # 本用例仅验证 validator 对 URL 格式的技术性判断（格式合法 ≠ 来源真实）。
        record = {
            "title": "TEST POLICY",
            "verification_status": "verified",
            "source_url": "https://verified-source.invalid/policy/doc-001.html",
        }
        result = pv.validate_policy_record(record)
        assert result["valid"] is True

    def test_verified_source_url_from_metadata_also_counts(self):
        record = {
            "title": "TEST POLICY",
            "verification_status": "verified",
            "metadata": {
                "source_url": "https://verified-source.invalid/nw12344/20240101/doc.html",
                "retrieved_at": "2024-01-01T00:00:00",
            },
        }
        result = pv.validate_policy_record(record)
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# TEST-PROVENANCE-004: contact 存在时必须有 provenance 或明确 unverified
# ---------------------------------------------------------------------------
class TestProvenance004ContactProvenance:
    def test_contact_without_provenance_and_marked_verified_is_rejected(self):
        record = {
            "title": "TEST POLICY",
            "official_contact": {
                "phone": "0755-88886666",
                "contact_status": "verified",
            },
        }
        result = pv.validate_policy_record(record)
        assert result["valid"] is False
        assert any("DATA-INTEGRITY-003" in issue for issue in result["issues"])

    def test_contact_with_source_url_is_valid(self):
        record = {
            "title": "TEST POLICY",
            "official_contact": {
                "phone": "0755-88886666",
                "contact_source_url": "https://verified-source.invalid/contact.html",
            },
        }
        result = pv.validate_policy_record(record)
        assert result["valid"] is True

    def test_contact_explicitly_unverified_is_valid(self):
        record = {
            "title": "TEST POLICY",
            "official_contact": {"phone": "0755-88886666", "contact_status": "unverified"},
        }
        result = pv.validate_policy_record(record)
        assert result["valid"] is True

    def test_all_null_contact_is_valid(self):
        # 没有联系方式，比错误联系方式安全一万倍
        record = {
            "title": "TEST POLICY",
            "official_contact": {"phone": None, "email": None, "contact_status": "unverified"},
        }
        result = pv.validate_policy_record(record)
        assert result["valid"] is True

    def test_placeholder_phone_number_is_rejected(self):
        record = {
            "title": "TEST POLICY",
            "official_contact": {"phone": "13800138000", "contact_status": "verified"},
        }
        result = pv.validate_policy_record(record)
        assert result["valid"] is False
        assert any("DATA-INTEGRITY-001" in issue for issue in result["issues"])


# ---------------------------------------------------------------------------
# TEST-PROVENANCE-005: 非法 / placeholder URL 不得成为 VERIFIED source
# ---------------------------------------------------------------------------
class TestProvenance005PlaceholderUrlNotVerified:
    @pytest.mark.parametrize("bad_url", [
        "http://example.com/policy",
        "https://www.example.gov.cn/zhengce",
        "ftp://gov.cn/policy.pdf",
        "not a url at all",
        "https://placeholder-url-here.com",
        "http://localhost:8000/policy",
        "https://www.xxx.com/policy",
    ])
    def test_bad_url_cannot_be_verified_source(self, bad_url):
        record = {"title": "TEST POLICY", "verification_status": "verified", "source_url": bad_url}
        result = pv.validate_policy_record(record)
        assert result["valid"] is False

    def test_url_format_valid_does_not_imply_source_verified(self):
        # 第十五条：URL 格式合法 ≠ 来源真实
        check = pv.validate_source_url("https://some-domain.com/page")
        assert check["url_status"] == pv.UrlStatus.VALID_FORMAT
        assert "NOT verified" in check["reason"]


# ---------------------------------------------------------------------------
# TEST-PROVENANCE-006: 旧 Policy Payload 在新增字段后仍然可以正常解析
# ---------------------------------------------------------------------------
class TestProvenance006BackwardCompatibility:
    def test_legacy_payload_without_new_fields_parses(self):
        legacy = {
            "policy_id": "legacy-001",
            "title": "Legacy Policy Payload",
            "metadata": {"source_url": "https://legacy-source.invalid/doc", "crawl_timestamp": "2023-01-01"},
        }
        result = pv.validate_policy_record(legacy)
        # 旧 payload 没有 is_mock / verification_status 字段，应正常解析不抛异常
        assert result["provenance"].is_mock is False
        assert result["provenance"].verification_status is None
        assert result["provenance"].source_url == "https://legacy-source.invalid/doc"

    def test_empty_record_parses(self):
        result = pv.validate_policy_record({})
        assert result["provenance"].is_mock is False
        assert result["provenance"].source_url is None


# ---------------------------------------------------------------------------
# 种子数据回归审计：治理后的数据必须保持 MOCK 且无虚构联系方式
# ---------------------------------------------------------------------------
class TestSeedDataGovernanceRegression:
    @pytest.mark.parametrize("seed_file,expected_count", [
        ("china_policy_seed_data.json", 12),
        ("detailed_china_tech_policies.json", 9),
    ])
    def test_seed_data_all_mock_and_no_governance_violations(self, seed_file, expected_count):
        records = json.loads((SEED_DIR / seed_file).read_text(encoding="utf-8"))
        assert len(records) == expected_count, "records must never be deleted (INV-000)"
        for record in records:
            assert record.get("is_mock") is True, f"{seed_file}: every record must be explicitly mock"
            assert record.get("verification_status") == "mock"
        stats = pv.audit_policy_dataset(records)
        assert stats["governance_violations"] == 0, f"{seed_file}: {stats}"
        assert stats["missing_contact_provenance"] == 0, (
            f"{seed_file}: no contact may retain a phone/email without provenance")
