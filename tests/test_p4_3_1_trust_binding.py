"""P4-3.1 Trust Verification Binding — read-only audit + hardening regression.

目标：证明 P4-3 Execution Readiness 对 Human Verification 的绑定方式已修复，
field_evidence[*].verified（record-local boolean）不再是绕过 Trust Human
Verification Gate 的旁路。

设计：
- 生产记录（is_mock 非 True）绝不信任 record-local ``verified`` 标记；验证只能来自
  注入的 Trust 服务（只读 check_verified_validity）。
- 验证链：trust_service.check_verified_validity(evidence_id) 必须 is_valid，且
  record.verified_event_id == 当前有效 verified 事件的 event_id。

本文件仅使用真实 TrustEvidenceService + 持久化 event log 构造 VERIFIED/revoked/
content-drift 场景；**不调用 record_human_verification**（Human Verification 由
真实 Human Authority 执行，测试仅模拟 durable event 以验证绑定逻辑）。
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from global_policy_aggregator.pipeline.p4_execution_state import (
    STATE_NOT_READY, STATE_PARTIAL, STATE_EXECUTION_READY,
    assess_execution_readiness,
)
from src.trust.trust_service import TrustEvidenceService
from src.trust.verification_event_log import (
    HumanVerificationAuthority,
    HumanVerificationAuthorityRegistry,
    VerificationDecision,
    compute_content_identity,
)

_REAL_PATH = Path(__file__).resolve().parent.parent \
    / "global_policy_aggregator" / "data" / "real_policies" / "real_policies.json"


def _real_records():
    d = json.loads(_REAL_PATH.read_text(encoding="utf-8"))
    recs = d["policies"] if isinstance(d, dict) else d
    return [r for r in recs if isinstance(r.get("id"), int) and 101 <= r["id"] <= 121]


def _make_trust(evidence_id, granted_event_id, *, revoked=False, drift=False):
    """构造一个真实 TrustEvidenceService，含一个 durable VERIFIED 事件。

    不调用 record_human_verification；直接 append VerificationDecision（模拟
    真实 Human Authority 已授 VERIFIED 的 durable 记录），以验证 P4-3 绑定逻辑。
    """
    d = tempfile.mkdtemp()
    log_path = os.path.join(d, "events.jsonl")
    registry = HumanVerificationAuthorityRegistry([
        HumanVerificationAuthority(verifier_id="hv1", role="human_verifier", active=True),
    ])
    svc = TrustEvidenceService(event_log_path=log_path, authority_registry=registry)
    url = "https://www.example.gov.cn/" + evidence_id
    svc.create_evidence({
        "id": evidence_id, "type": "policy", "source": "official",
        "source_reference": url, "verification_status": "UNVERIFIED", "metadata": {},
    })
    ev = svc.get_evidence(evidence_id)["evidence"]
    ci = compute_content_identity(ev)
    svc.event_log.append(VerificationDecision(
        event_id=granted_event_id,
        evidence_id=evidence_id,
        decision="verified",
        actor="hv1",
        actor_role="human_verifier",
        method="human_verification",
        timestamp=datetime.now(timezone.utc).isoformat(),
        content_identity=ci,
        evidence_refs=[url],
        notes="P4-3.1 test verified event",
    ))
    if revoked:
        svc.event_log.append(VerificationDecision(
            event_id=granted_event_id + "_revoked",
            evidence_id=evidence_id,
            decision="revoked",
            actor="system_content_change_detector",
            actor_role="system",
            method="automatic_content_change_detection",
            timestamp=datetime.now(timezone.utc).isoformat(),
            content_identity=ci,
            evidence_refs=[],
            notes=json.dumps({"reason": "test revoke"}),
        ))
    if drift:
        # 篡改 evidence 内容，使当前 content_identity 与 verified 事件不一致
        svc.evidence_graph.nodes[evidence_id].data["source"] = "tampered-source"
    return svc, granted_event_id


def _valid_record(evidence_id, verified_event_id):
    """构造一条结构完整、非 mock 的 policy 记录（仅缺 verification 需由 Trust 提供）。"""
    cid = "cid_" + evidence_id
    url = "https://www.example.gov.cn/" + evidence_id
    snap = "snapshots/example.gov.cn/" + evidence_id + ".html"
    fe = lambda f: {"field": f, "quote": "q", "content_identity": cid,
                    "source_url": url, "snapshot_ref": snap, "verified": True}

    return {
        "id": "T-" + evidence_id,
        "is_mock": False,                       # 生产记录：local verified 必须被忽略
        "rule_type": "percentage_of_base",
        "percentage": 0.30,
        "base": "研发费用",
        "cap": 0.50,
        "cap_mode": "relative",
        "industry": "AI",
        "region": "Shenzhen",
        "type": "subsidy",
        "application_requirements": "none",
        "valid_period": "2024-01-01 to 2026-12-31",
        "currency": "CNY",
        "unit": "yuan",
        "content_identity": cid,
        "source_url": url,
        "snapshot_ref": snap,
        "eligibility_conditions": [
            {"id": "rd", "label": "研发", "source_field": "rd", "operator": ">=",
             "threshold": 0.1, "unit": "ratio", "quote": "q"}
        ],
        "evidence_id": evidence_id,
        "verified_event_id": verified_event_id,
        "field_evidence": {
            "percentage": fe("percentage"),
            "base": fe("base"),
            "cap": fe("cap"),
            "eligibility_conditions": fe("eligibility_conditions"),
            "title": fe("title"),
        },
    }


# ===================== A. local verified 不再是门控 =====================

def test_1_local_verified_true_without_trust_provenance_not_ready():
    # 生产记录（is_mock=False）仅有 record-local verified，无 Trust → 必须 NOT_READY
    rec = _valid_record("ev_x", "veid_x")
    rec.pop("evidence_id", None)
    rec.pop("verified_event_id", None)
    r = assess_execution_readiness(rec)  # 不注入 trust_service
    assert r["state"] == STATE_NOT_READY
    assert "percentage" in r["unverified_critical_fields"]


# ===================== B. 伪造 verified_event_id =====================

def test_2_fake_verified_event_id_not_ready():
    eid = "ev_fake"
    svc, real_veid = _make_trust(eid, "veid_real")
    # (a) evidence 存在但 verified_event_id 不匹配当前有效事件
    rec = _valid_record(eid, "veid_WRONG")
    r = assess_execution_readiness(rec, trust_service=svc)
    assert r["state"] == STATE_NOT_READY
    assert "percentage" in r["unverified_critical_fields"]
    # (b) evidence 根本不存在于 Trust → is_valid=False
    rec2 = _valid_record("ev_nonexistent", "veid_x")
    r2 = assess_execution_readiness(rec2, trust_service=svc)
    assert r2["state"] == STATE_NOT_READY


# ===================== D. 有效 Trust VERIFIED provenance =====================

def test_3_valid_verified_event_critical_fields_verified():
    eid = "ev_valid"
    svc, veid = _make_trust(eid, "veid_valid")
    rec = _valid_record(eid, veid)
    r = assess_execution_readiness(rec, trust_service=svc)
    assert r["unverified_critical_fields"] == []
    assert r["evidence_gaps"] == []


# ===================== C. revoked / invalid / content mismatch =====================

def test_4_revoked_verified_event_not_ready():
    eid = "ev_rev"
    svc, veid = _make_trust(eid, "veid_rev", revoked=True)
    rec = _valid_record(eid, veid)
    r = assess_execution_readiness(rec, trust_service=svc)
    assert r["state"] == STATE_NOT_READY
    assert "percentage" in r["unverified_critical_fields"]


def test_5_content_identity_mismatch_not_ready():
    eid = "ev_drift"
    svc, veid = _make_trust(eid, "veid_drift", drift=True)
    rec = _valid_record(eid, veid)
    r = assess_execution_readiness(rec, trust_service=svc)
    assert r["state"] == STATE_NOT_READY
    assert "percentage" in r["unverified_critical_fields"]


# ===================== F. VERIFIED 但缺 eligibility → NOT_READY =====================

def test_6_verified_but_missing_eligibility_not_ready():
    eid = "ev_noelig"
    svc, veid = _make_trust(eid, "veid_noelig")
    rec = _valid_record(eid, veid)
    rec["eligibility_conditions"] = None  # 缺 required
    r = assess_execution_readiness(rec, trust_service=svc)
    assert r["state"] == STATE_NOT_READY
    assert "eligibility_conditions" in r["missing_required"]


# ===================== D(全) + 7. 完整 VERIFIED → EXECUTION_READY =====================

def test_7_verified_full_record_execution_ready():
    eid = "ev_full"
    svc, veid = _make_trust(eid, "veid_full")
    rec = _valid_record(eid, veid)
    r = assess_execution_readiness(rec, trust_service=svc)
    assert r["state"] == STATE_EXECUTION_READY


# ===================== 8. EXECUTION_READY 必须依赖 VERIFIED provenance =====================

def test_8_execution_ready_requires_verified_provenance():
    rec = _valid_record("ev_orphan", "veid_orphan")
    # 不注入 trust_service，生产记录 → fail-closed，即便所有字段齐全
    assert assess_execution_readiness(rec)["state"] == STATE_NOT_READY


# ===================== 9. VERIFIED != EXECUTION_READY =====================

def test_9_verified_not_equal_execution_ready():
    eid = "ev_nort"
    svc, veid = _make_trust(eid, "veid_nort")
    rec = _valid_record(eid, veid)
    rec.pop("rule_type", None)  # 缺 required rule_type
    r = assess_execution_readiness(rec, trust_service=svc)
    assert r["state"] == STATE_NOT_READY
    assert "rule_type" in r["missing_required"]


# ===================== 10. REAL 121 重新审计 =====================

def test_10_real_121_reaudit_unchanged_and_not_ready():
    recs = _real_records()
    r121 = next(r for r in recs if r["id"] == 121)
    # 不注入 trust_service（生产默认）→ fail-closed NOT_READY
    assert assess_execution_readiness(r121)["state"] == STATE_NOT_READY
    # 即便注入一个不含 121 有效事件的 trust_service → 仍 NOT_READY（无旁路）
    svc, veid = _make_trust("ev_other", "veid_other")
    assert assess_execution_readiness(r121, trust_service=svc)["state"] == STATE_NOT_READY
    # 不修改 REAL record
    assert r121["verification_status"] == "unverified"
    assert r121["percentage"] == 0.15
    assert r121["base"] == "应纳税所得额"
    assert "field_evidence" in r121  # 结构未变
    # 确认不存在 record-local 绕过：121 的 field_evidence 无 verified 键
    for fe in (r121.get("field_evidence") or {}).values():
        assert "verified" not in fe
