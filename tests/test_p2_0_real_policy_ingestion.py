#!/usr/bin/env python3
"""
P2-0C.1: REAL/UNVERIFIED Policy Ingestion 防回归测试。

锁定 interactive_ai_server.load_real_policies() 的 graceful 契约与 REAL 条目数据契约：
- 文件缺失 / 非法 JSON / 顶层非 list / 空 list → 一律 []，绝不 crash Portal
- REAL 条目：is_mock 严格 False、verification_status="unverified"、HTTP(S) source_url、
  禁 metadata、联系方式一律 null（宁可 null，不要猜）、id 从 101 起与 MOCK 1-12 不冲突
- 加载过程零副作用：不产生 Experimental Event，不写 p2_0_experimental/records/
P2-0C.1/C.2 边界：real_policies.json 可为空 [] 或包含合法 REAL/UNVERIFIED 政策（id ≥ 101）。
空 list 与非空合法 list 均为合法 ingestion state；测试不绑定具体数据集数量。
通过 importlib 按文件路径加载 web 服务器模块，避免污染全局 pythonpath。
"""

import importlib.util
import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = REPO_ROOT / "global_policy_aggregator" / "web" / "interactive_ai_server.py"
REAL_POLICIES_FILE = REPO_ROOT / "global_policy_aggregator" / "data" / "real_policies" / "real_policies.json"


def _load_server(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _records_snapshot():
    records_dir = Path(os.environ["P2_0_RECORDS_DIR"])
    if not records_dir.exists():
        return []
    return sorted(str(p.relative_to(records_dir)) for p in records_dir.rglob("*"))


def _valid_real_policy(policy_id: int = 101):
    """符合 P2-0C.1 数据契约的最小 REAL 样本（仅用于测试，不是生产数据）。"""
    return {
        "id": policy_id,
        "is_mock": False,
        "verification_status": "unverified",
        "title": "契约测试用样本条目",
        "region": "北京市",
        "industry": "AI",
        "type": "补贴",
        "amount": "最高 500 万元",
        "issue_date": "2026-01-01",
        "valid_period": "2026-01-01 至 2028-12-31",
        "source_url": "https://example-official.gov.cn/policy/101",
        "official_contact": {
            "department": None,
            "phone": None,
            "email": None,
            "address": None,
            "contact_status": "unverified",
        },
        "description": "契约测试用样本描述",
        "details": "",
        "requirements": "",
    }


def _assert_real_policy_contract(policy):
    """REAL 条目最小契约（Portal 展示层）。违规即 AssertionError。"""
    assert isinstance(policy["is_mock"], bool), "is_mock 必须是严格 bool"
    assert policy["is_mock"] is False
    assert policy["verification_status"] == "unverified"
    source_url = policy["source_url"]
    assert isinstance(source_url, str) and source_url.startswith(("http://", "https://")), (
        "source_url 必须是真实 HTTP(S) URL（不允许本地 PDF 路径）")
    assert "metadata" not in policy, "REAL 条目不允许 metadata"
    contact = policy["official_contact"]
    assert contact["phone"] is None, "宁可 null，不要猜（phone）"
    assert contact["email"] is None, "宁可 null，不要猜（email）"
    assert contact["address"] is None, "宁可 null，不要猜（address）"
    for field in ("title", "description", "industry"):
        assert isinstance(policy[field], str), f"{field} 必须是 string（search_policies 会调用 .lower()）"
    assert isinstance(policy["id"], int) and policy["id"] >= 101, "REAL id 从 101 起"


@pytest.fixture(scope="module")
def portal():
    return _load_server("p2_0c1_interactive_ai_server")


class TestProductionFileBoundary:
    def test_real_policies_file_exists_and_is_valid_list(self):
        """生产 real_policies.json 必须存在且为合法 list（空或非空均合法）。"""
        assert REAL_POLICIES_FILE.exists()
        data = json.loads(REAL_POLICIES_FILE.read_text(encoding="utf-8"))
        assert isinstance(data, list), "real_policies.json 顶层必须是 list"

    def test_portal_loads_production_file_without_error(self, portal):
        """Portal 必须能加载生产 real_policies.json（无论空或非空），不崩溃。"""
        loaded = portal.load_real_policies()
        assert isinstance(loaded, list)
        # 生产文件中的 REAL 条目（若有）必须满足 REAL 契约
        for p in loaded:
            _assert_real_policy_contract(p)

    def test_portal_loads_non_empty_legal_real_dataset_via_tmp(self, portal, tmp_path, monkeypatch):
        """非空合法 REAL Policy dataset 必须能正常加载（ingestion boundary）。
        使用 synthetic fixture，不是生产数据。"""
        sample = _valid_real_policy(101)
        target = tmp_path / "real_policies.json"
        target.write_text(json.dumps([sample], ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(portal, "_REAL_POLICIES_FILE", target)
        loaded = portal.load_real_policies()
        assert len(loaded) == 1
        assert loaded[0]["id"] == 101
        _assert_real_policy_contract(loaded[0])

    def test_portal_module_loads_cleanly(self, portal):
        assert callable(portal.load_real_policies)
        assert len(portal.policies) >= 12


class TestLoaderGracefulDegradation:
    @staticmethod
    def _load_with(portal, monkeypatch, tmp_path, content=None, create=True):
        target = tmp_path / "real_policies.json"
        if create:
            target.write_text(content, encoding="utf-8")
        monkeypatch.setattr(portal, "_REAL_POLICIES_FILE", target)
        return portal.load_real_policies()

    def test_missing_file_returns_empty_list(self, portal, tmp_path, monkeypatch):
        assert self._load_with(portal, monkeypatch, tmp_path, create=False) == []

    def test_invalid_json_returns_empty_list(self, portal, tmp_path, monkeypatch):
        assert self._load_with(portal, monkeypatch, tmp_path, content="{not-valid-json") == []

    def test_top_level_object_returns_empty_list(self, portal, tmp_path, monkeypatch):
        assert self._load_with(portal, monkeypatch, tmp_path, content='{"policies": []}') == []

    def test_top_level_string_returns_empty_list(self, portal, tmp_path, monkeypatch):
        assert self._load_with(portal, monkeypatch, tmp_path, content='"policies"') == []

    def test_empty_list_returns_empty_list(self, portal, tmp_path, monkeypatch):
        assert self._load_with(portal, monkeypatch, tmp_path, content="[]") == []


class TestRealPolicyDataContract:
    def test_real_subset_satisfies_contract(self, portal):
        for policy in (p for p in portal.policies if p.get("is_mock") is False):
            _assert_real_policy_contract(policy)

    def test_valid_sample_satisfies_contract(self):
        _assert_real_policy_contract(_valid_real_policy(101))

    def test_is_mock_must_be_strict_bool(self):
        policy = _valid_real_policy(101)
        policy["is_mock"] = 0
        with pytest.raises(AssertionError):
            _assert_real_policy_contract(policy)

    def test_is_mock_true_rejected(self):
        policy = _valid_real_policy(101)
        policy["is_mock"] = True
        with pytest.raises(AssertionError):
            _assert_real_policy_contract(policy)

    def test_verified_status_rejected(self):
        policy = _valid_real_policy(101)
        policy["verification_status"] = "verified"
        with pytest.raises(AssertionError):
            _assert_real_policy_contract(policy)

    def test_rejected_status_rejected(self):
        policy = _valid_real_policy(101)
        policy["verification_status"] = "rejected"
        with pytest.raises(AssertionError):
            _assert_real_policy_contract(policy)

    def test_local_pdf_source_url_rejected(self):
        policy = _valid_real_policy(101)
        policy["source_url"] = "/policies/local.pdf"
        with pytest.raises(AssertionError):
            _assert_real_policy_contract(policy)

    def test_metadata_forbidden(self):
        policy = _valid_real_policy(101)
        policy["metadata"] = {"anything": True}
        with pytest.raises(AssertionError):
            _assert_real_policy_contract(policy)

    def test_contacts_must_stay_null(self):
        policy = _valid_real_policy(101)
        policy["official_contact"]["phone"] = "010-00000000"
        with pytest.raises(AssertionError):
            _assert_real_policy_contract(policy)

    def test_real_id_below_101_rejected(self):
        policy = _valid_real_policy(13)
        with pytest.raises(AssertionError):
            _assert_real_policy_contract(policy)


class TestMockPoliciesUntouched:
    def test_twelve_mock_policies_with_ids_1_to_12(self, portal):
        mock_policies = [p for p in portal.policies if p.get("is_mock") is True]
        assert len(mock_policies) == 12
        assert [p["id"] for p in mock_policies] == list(range(1, 13))

    def test_mock_policy_content_invariants_unchanged(self, portal):
        mock_policies = [p for p in portal.policies if p.get("is_mock") is True]
        for policy in mock_policies:
            assert policy["is_mock"] is True
            assert policy["verification_status"] == "mock"
            assert isinstance(policy["title"], str) and policy["title"]
            assert isinstance(policy["description"], str) and policy["description"]
            assert isinstance(policy["source_url"], str) and policy["source_url"]
            contact = policy["official_contact"]
            assert contact["phone"] is None
            assert contact["email"] is None
            assert contact["address"] is None
            assert contact["contact_status"] == "unverified"

    def test_real_ids_do_not_conflict_with_mock_ids(self, portal):
        mock_ids = {p["id"] for p in portal.policies if p.get("is_mock") is True}
        real_ids = {p["id"] for p in portal.policies if p.get("is_mock") is False}
        assert mock_ids == set(range(1, 13))
        assert mock_ids.isdisjoint(real_ids)

    def test_first_real_id_101_disjoint_from_mock(self, portal):
        sample = _valid_real_policy(101)
        mock_ids = {p["id"] for p in portal.policies if p.get("is_mock") is True}
        assert mock_ids.isdisjoint({sample["id"]})


class TestLoaderSideEffectFree:
    def test_module_import_writes_no_records_or_events(self):
        before = _records_snapshot()
        _load_server("p2_0c1_interactive_ai_server_fresh")
        assert _records_snapshot() == before

    def test_loader_call_writes_no_records_or_events(self, portal):
        before = _records_snapshot()
        portal.load_real_policies()
        assert _records_snapshot() == before

    def test_loading_never_initializes_experimental_store(self, portal):
        assert portal._p2_0_store is None
        portal.load_real_policies()
        assert portal._p2_0_store is None

    def test_module_level_has_no_experimental_import(self, portal):
        assert "p2_0_experimental" not in vars(portal)
        assert "jsonl_store" not in vars(portal)


class TestExperimentalLayerCompat:
    def test_real_policy_record_passes_validate_policy(self):
        from p2_0_experimental.record_validator import validate_policy

        portal_policy = _valid_real_policy(101)
        record = {
            "record_type": "POLICY",
            "policy_id": f"real_{portal_policy['id']}",
            "title": portal_policy["title"],
            "source_url": portal_policy["source_url"],
            "is_mock": False,
            "verification_status": "UNVERIFIED",
            "created_at": "2026-09-03T00:00:00+08:00",
            "source": "manual_collection",
        }
        valid, errors = validate_policy(record)
        assert valid, errors

    def test_verified_record_rejected_by_validate_policy(self):
        from p2_0_experimental.record_validator import validate_policy

        record = {
            "record_type": "POLICY",
            "policy_id": "real_101",
            "title": "契约测试用样本条目",
            "source_url": "https://example-official.gov.cn/policy/101",
            "is_mock": False,
            "verification_status": "VERIFIED",
            "created_at": "2026-09-03T00:00:00+08:00",
            "source": "manual_collection",
        }
        valid, errors = validate_policy(record)
        assert not valid
        assert any("UNVERIFIED" in e for e in errors)

    def test_metadata_record_rejected_by_validate_policy(self):
        from p2_0_experimental.record_validator import validate_policy

        record = {
            "record_type": "POLICY",
            "policy_id": "real_101",
            "title": "契约测试用样本条目",
            "source_url": "https://example-official.gov.cn/policy/101",
            "is_mock": False,
            "verification_status": "UNVERIFIED",
            "created_at": "2026-09-03T00:00:00+08:00",
            "source": "manual_collection",
            "metadata": {"x": 1},
        }
        valid, errors = validate_policy(record)
        assert not valid
