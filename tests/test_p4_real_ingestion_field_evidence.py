"""P3-7 P0 fix — business fields + field_evidence are preserved (not lost).

扩展 test_real_ingestion_v1 的 FakeTrustService：在 EvidenceObject metadata 中
注入 extracted_fields，验证 REAL 记录不再整批清空，且每字段可溯源。
所有测试使用临时 dataset / 临时 snapshot，绝不触碰生产 real_policies.json。
"""

import json

import pytest

from global_policy_aggregator.pipeline.fetcher import compute_content_hash
from global_policy_aggregator.pipeline.real_ingestion import (
    PRODUCTION_REAL_POLICIES_PATH,
    IngestionRejected,
    ingest_verified_evidence,
)


class FakeTrustService:
    def __init__(self):
        self.evidence = {}
        self.validity = {}

    def get_evidence(self, evidence_id):
        ev = self.evidence.get(evidence_id)
        if ev is None:
            return {"success": False, "error": "Evidence not found"}
        return {"success": True, "evidence": ev}

    def check_verified_validity(self, evidence_id):
        v = self.validity.get(evidence_id)
        if v is None:
            return {"is_valid": False, "reasons": ["no validity"],
                    "latest_verified_event": None}
        return v

    def get_verification_history(self, evidence_id):
        return {"success": True, "event_count": 0, "events": []}

    def record_human_verification(self, *args, **kwargs):
        raise AssertionError("P3-7 must NOT call record_human_verification()")


def _fe(value, quote="q", method="m"):
    return {"value": value, "quote": quote, "char_span": [0, 1],
            "snapshot_ref": "snapshots/x/y.html", "method": method,
            "extracted_at": "2026-09-10T00:00:00Z"}


def _make_evidence(evidence_id, content_identity, snapshot_ref, source_url,
                   extracted_fields):
    meta = {
        "policy_content_identity": content_identity,
        "snapshot_ref": snapshot_ref,
        "candidate_id": "cand-" + evidence_id,
        "source_url": source_url,
        "provenance": {"snapshot_ref": snapshot_ref, "source_url": source_url},
        "extracted_fields": extracted_fields,
    }
    return {
        "id": evidence_id, "type": "policy",
        "source": "openinvest-pipeline", "source_reference": snapshot_ref,
        "verification_status": "VERIFIED", "confidence_score": 0.0,
        "metadata": meta,
    }


@pytest.fixture
def env(tmp_path):
    real_copy = tmp_path / "real_policies.json"
    data = json.loads(PRODUCTION_REAL_POLICIES_PATH.read_text(encoding="utf-8"))
    # 隔离为 pre-ingestion 基线（仅 grandfather 101–120），
    # 使 P3-7 测试不再依赖已被真实 P3-7 写入的 REAL 121+。
    data = [p for p in data if 101 <= p.get("id", 0) <= 120]
    real_copy.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()
    return {"real_policies_path": real_copy, "snapshots_dir": snapshots_dir,
            "audit_path": tmp_path / "ingestion_audit.jsonl",
            "lock_path": tmp_path / ".ingestion.lock"}


def _write_snapshot(snapshots_dir, content=b"<html>policy</html>"):
    host = "gov.cn"
    ci = compute_content_hash(content)
    p = snapshots_dir / host / f"{ci}.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return f"snapshots/{host}/{ci}.html", ci


def test_p3_7_preserves_business_fields_and_field_evidence(env):
    trust = FakeTrustService()
    ref, ci = _write_snapshot(env["snapshots_dir"])
    src = "https://www.gov.cn/zhengce/qiye.html"
    extracted = {
        "title": _fe("高新技术企业税收优惠", quote="《高新技术企业税收优惠》",
                     method="bs4_title_or_booktitle"),
        "percentage": _fe(0.15, quote="减按15%的税率", method="regex_percentage"),
        "base": _fe("应纳税所得额", quote="以应纳税所得额为计税依据",
                    method="regex_base"),
        "type": _fe("tax_break", quote="税收优惠", method="regex_type_label"),
    }
    trust.evidence["ev-1"] = _make_evidence("ev-1", ci, ref, src, extracted)
    trust.validity["ev-1"] = {
        "is_valid": True, "reasons": [],
        "latest_verified_event": {"event_id": "evt-1", "decision": "verified"}}

    rid = ingest_verified_evidence("ev-1", trust, **env)
    assert rid == 121
    data = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    rec = next(e for e in data if e["id"] == rid)
    # 业务字段已保留（不再清空）
    assert rec["title"] == "高新技术企业税收优惠"
    assert rec["percentage"] == 0.15
    assert rec["base"] == "应纳税所得额"
    assert rec["type"] == "tax_break"
    # 无 Evidence 的字段仍保持 null/空（不臆造）
    assert rec["amount"] is None
    # field_evidence 可溯源
    fe = rec["field_evidence"]
    assert fe["percentage"]["quote"] == "减按15%的税率"
    assert fe["percentage"]["content_identity"] == ci
    assert fe["percentage"]["source_url"] == src
    assert fe["percentage"]["method"] == "regex_percentage"
    # content_identity / source_url 一致
    assert rec["content_identity"] == ci
    assert rec["source_url"] == src


def test_p3_7_no_brute_force_metadata_copy(env):
    """确证只映射白名单业务字段，而非整体复制 metadata。"""
    trust = FakeTrustService()
    ref, ci = _write_snapshot(env["snapshots_dir"])
    src = "https://www.gov.cn/zhengce/qiye.html"
    extracted = {"title": _fe("X")}
    meta_extra = {"some_internal_note": "must-not-leak",
                  "handoff_id": "ho_abc"}
    ev = _make_evidence("ev-1", ci, ref, src, extracted)
    ev["metadata"].update(meta_extra)
    trust.evidence["ev-1"] = ev
    trust.validity["ev-1"] = {
        "is_valid": True, "reasons": [],
        "latest_verified_event": {"event_id": "evt-1", "decision": "verified"}}
    rid = ingest_verified_evidence("ev-1", trust, **env)
    data = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    rec = next(e for e in data if e["id"] == rid)
    # 非白名单的 metadata 不得泄漏到 REAL 记录
    assert "some_internal_note" not in rec
    assert "handoff_id" not in rec


def test_101_120_unchanged_after_field_evidence_ingest(env):
    trust = FakeTrustService()
    ref, ci = _write_snapshot(env["snapshots_dir"])
    src = "https://www.gov.cn/zhengce/qiye.html"
    extracted = {"title": _fe("高新技术企业税收优惠")}
    trust.evidence["ev-1"] = _make_evidence("ev-1", ci, ref, src, extracted)
    trust.validity["ev-1"] = {
        "is_valid": True, "reasons": [],
        "latest_verified_event": {"event_id": "evt-1", "decision": "verified"}}
    before = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    ingest_verified_evidence("ev-1", trust, **env)
    after = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    before_by_id = {e["id"]: e for e in before}
    after_by_id = {e["id"]: e for e in after}
    for rid_ in range(101, 121):
        assert after_by_id[rid_] == before_by_id[rid_]
