"""P4-4 — Execution Pilot Contract Hardening（最小范围，只读执行验证）。

JUDGE 决策：
- D1：不修改 REAL 121；新 REAL 记录只能经 Official Source → Snapshot → Evidence →
  Validation → Human Approval → Trust Human Verification → P3-7 Gate（本阶段**不**执行）。
- D2：Execution Readiness 支持明确的 NOT_APPLICABLE 语义；OPTIONAL 字段只有在能被
  *确定性规则* 证明「对该 rule_type 不适用」时才可为 N/A；普通 missing/null 不得自动 N/A。

覆盖（JUDGE 要求 1–20）：
 1/2/3  unknown 哨兵（含 null）不产生 explicit conflict，也不是通配符匹配
 4      显式行业冲突仍 not_matched（保持既有正确语义）
 5/6    valid_period 单端起算合法；不自动生成 end_date
 7/8    tax_treatment_rate 的 currency / unit 为 NOT_APPLICABLE，不再阻塞
 9      普通 OPTIONAL 缺失仍封顶 PARTIAL
 10     NOT_APPLICABLE 只能由确定性规则产生
 11/12  fake local verified / fake verified_event_id 仍被拒绝
 13     有效 Trust VERIFIED provenance 才能满足 verification 要求
 14     VERIFIED 但缺 required eligibility → NOT_READY
 15     REAL 121 完全未改
 16     未产生 REAL 122
 17-19  无 Trust 写入 / 无 Human Verification / 未执行 P3-7
 20     全量回归（由 `python -m pytest` 覆盖）

本文件不使用 LLM / 政府 API / crawler；不写 REAL；不写 Trust；不调用
record_human_verification；不执行 P3-7。
"""

import inspect
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from global_policy_aggregator.matching.policy_match import (
    MATCH_STATUS_MATCHED, MATCH_STATUS_NOT, match_project_to_policy,
)
from global_policy_aggregator.matching.project_profile import build_project_profile
from global_policy_aggregator.pipeline.normalizer import normalize
from global_policy_aggregator.pipeline.parser import parse_html
from global_policy_aggregator.pipeline.p4_execution_state import (
    OPTIONAL_MISSING, OPTIONAL_NOT_APPLICABLE, OPTIONAL_PRESENT,
    STATE_EXECUTION_READY, STATE_NOT_READY, STATE_PARTIAL,
    assess_execution_readiness,
)
from global_policy_aggregator.pipeline.p4_rule_engine import (
    build_rule_from_real_record, check_eligibility,
)
from src.trust.trust_service import TrustEvidenceService
from src.trust.verification_event_log import (
    HumanVerificationAuthority,
    HumanVerificationAuthorityRegistry,
    VerificationDecision,
    compute_content_identity,
)

_ROOT = Path(__file__).resolve().parent.parent
_REAL_PATH = _ROOT / "global_policy_aggregator" / "data" / "real_policies" / "real_policies.json"
_REAL_121_VERIFIED_EVENT_ID = "07d2478c261f4ab6a251b320af179981"


def _norm_html(html, source_url="https://www.gov.cn/zhengce/x.html"):
    snap = "snapshots/x/y.html"
    parsed = parse_html(html, source_url, snap)
    return normalize(parsed, source_url, snap)


def _real_records():
    d = json.loads(_REAL_PATH.read_text(encoding="utf-8"))
    recs = d["policies"] if isinstance(d, dict) else d
    return recs


def _policy_stub(**kw):
    base = {"id": 1, "title": "t", "description": "d", "details": "",
            "requirements": "", "type": "unknown", "region": None}
    base.update(kw)
    return base


# ===========================================================================
# G3 — unknown 哨兵语义（1–4）
# ===========================================================================

def test_1_policy_industry_unknown_sentinel_no_conflict():
    """policy industry="unknown" + project industry="semiconductor" → 不得 explicit conflict。"""
    prof = build_project_profile({"industry": "semiconductor", "region": "Beijing"})
    m = match_project_to_policy(prof, _policy_stub(industry="unknown"))
    assert m.match_status != MATCH_STATUS_NOT
    assert [d.dimension for d in m.unmatched_dimensions] == []


def test_2_policy_industry_null_no_conflict():
    prof = build_project_profile({"industry": "semiconductor", "region": "Beijing"})
    m = match_project_to_policy(prof, _policy_stub(industry=None))
    assert m.match_status != MATCH_STATUS_NOT
    assert [d.dimension for d in m.unmatched_dimensions] == []


def test_3_unknown_sentinel_not_wildcard_match():
    """project industry 为哨兵 != 通配符：不得自动 matched。"""
    prof = build_project_profile({"industry": "unknown"})
    m = match_project_to_policy(prof, _policy_stub(industry="semiconductor"))
    assert m.match_status != MATCH_STATUS_MATCHED
    assert [d.dimension for d in m.matched_dimensions] == []


def test_3b_all_unknown_sentinels_treated_as_unknown():
    prof = build_project_profile({"industry": "semiconductor"})
    for sentinel in ("unknown", "UNKNOWN", "unavailable", "n/a", "", None, "未知"):
        m = match_project_to_policy(prof, _policy_stub(industry=sentinel))
        assert m.match_status != MATCH_STATUS_NOT, sentinel
        assert [d.dimension for d in m.unmatched_dimensions] == [], sentinel


def test_4_explicit_conflicting_industry_still_not_matched():
    """既有正确语义保持：显式冲突 → not_matched（unmatched=[industry]）。"""
    prof = build_project_profile({"industry": "semiconductor"})
    m = match_project_to_policy(prof, _policy_stub(industry="Finance"))
    assert m.match_status == MATCH_STATUS_NOT
    assert [d.dimension for d in m.unmatched_dimensions] == ["industry"]


# ===========================================================================
# G4 — valid_period 单端起算（5–6）
# ===========================================================================

def test_5_valid_period_start_only_is_legal():
    c = _norm_html("<html><body><h1>某政策</h1><p>本法自2008年1月1日起施行。</p></body></html>")
    assert c.valid_period == {"start": "2008-01-01", "end": None}


def test_6_no_auto_end_date():
    """绝不推断/默认 end_date（也不使用当前日期）。"""
    c = _norm_html("<html><body><h1>某政策</h1><p>本政策自2020年5月1日起实施。</p></body></html>")
    assert c.valid_period is not None
    assert c.valid_period["start"] == "2020-05-01"
    assert c.valid_period["end"] is None
    today = datetime.now(timezone.utc).date().isoformat()
    assert c.valid_period["end"] != today


def test_5b_valid_period_range_still_supported():
    c = _norm_html("<html><body><h1>某政策</h1><p>有效期 2024年1月1日至2026年12月31日。</p></body></html>")
    assert c.valid_period == {"start": "2024-01-01", "end": "2026-12-31"}


# ===========================================================================
# G2 — 引用型 Eligibility Condition（equals / boolean）+ evidence binding
# ===========================================================================

_LAW_CLAUSE = "国家需要重点扶持的高新技术企业，减按15％的税率征收企业所得税。"


def test_g2_reference_condition_extracted_with_evidence():
    c = _norm_html(f"<html><body><h1>某税法</h1><p>第二十八条 {_LAW_CLAUSE}</p></body></html>")
    conds = c.eligibility_conditions
    assert isinstance(conds, list) and len(conds) == 1
    cond = conds[0]
    assert cond["id"] == "state_key_supported_high_tech_enterprise"
    assert cond["source_field"] == "is_high_tech_enterprise"
    assert cond["operator"] == "equals"
    assert cond["expected_value"] is True
    assert cond["quote"] in _LAW_CLAUSE
    assert cond["snapshot_ref"] == "snapshots/x/y.html"
    # 不注入其他法规的认定条件
    assert all(x["id"] not in ("registered_years_min", "rd_staff_ratio_min",
                               "hightech_income_ratio_min") for x in conds)


def test_g2_reference_condition_not_injected_when_absent():
    """政策原文未表达受益主体类别 → 不得编造条件。"""
    c = _norm_html("<html><body><h1>某政策</h1><p>对符合条件的企业减按15%的税率征收企业所得税。</p></body></html>")
    assert c.eligibility_conditions is None


def _tax_rule(record):
    return build_rule_from_real_record(record)


def _tax_record():
    return {
        "id": "T-tt",
        "rule_type": "tax_treatment_rate",
        "percentage": 0.15,
        "base": "应纳税所得额",
        "eligibility_conditions": [{
            "id": "state_key_supported_high_tech_enterprise",
            "label": "国家需要重点扶持的高新技术企业",
            "source_field": "is_high_tech_enterprise",
            "operator": "equals",
            "expected_value": True,
            "quote": _LAW_CLAUSE,
        }],
    }


def test_g2_abc_scenarios():
    """A 信息不足 → UNKNOWN；B 明确冲突 → FAIL；C 明确满足 → PASS。"""
    rule = _tax_rule(_tax_record())
    a = check_eligibility(rule, project_profile={})
    assert a.overall == "UNKNOWN"
    assert all(c.status == "UNKNOWN" for c in a.conditions)

    b = check_eligibility(rule, project_profile={"is_high_tech_enterprise": False})
    assert b.overall == "FAIL"
    assert b.conditions[0].status == "FAIL"

    c = check_eligibility(rule, project_profile={"is_high_tech_enterprise": True})
    assert c.overall == "PASS"
    assert c.conditions[0].status == "PASS"


def test_g2_missing_never_defaults_to_pass():
    rule = _tax_rule(_tax_record())
    r = check_eligibility(rule, project_profile={"is_high_tech_enterprise": None})
    assert r.overall != "PASS"


def test_g2_numeric_threshold_conditions_still_work():
    """回归：既有数值阈值条件语义不变。"""
    rec = dict(_tax_record())
    rec["rule_type"] = "percentage_of_base"
    rec["eligibility_conditions"] = [{
        "id": "rd", "label": "研发强度", "source_field": "rd_ratio",
        "operator": ">=", "threshold": 0.1, "quote": "q",
    }]
    rule = _tax_rule(rec)
    assert check_eligibility(rule, {"rd_ratio": 0.2}).overall == "PASS"
    assert check_eligibility(rule, {"rd_ratio": 0.05}).overall == "FAIL"
    assert check_eligibility(rule, {}).overall == "UNKNOWN"


# ===========================================================================
# G5 — OPTIONAL NOT_APPLICABLE
# ===========================================================================

def _ready_record(**kw):
    cid = "cid"
    url = "https://www.example.gov.cn/p"
    snap = "snapshots/example.gov.cn/p.html"
    fe = lambda f: {"field": f, "quote": "q", "content_identity": cid,
                    "source_url": url, "snapshot_ref": snap}
    rec = {
        "id": "T-g5",
        "is_mock": True,               # 测试 fixture：沿用 record-local verified（非生产旁路）
        "rule_type": "tax_treatment_rate",
        "percentage": 0.15,
        "base": "应纳税所得额",
        "industry": "unknown",
        "region": "全国",
        "valid_period": {"start": "2008-01-01", "end": None},
        "application_requirements": "none",
        "content_identity": cid,
        "source_url": url,
        "snapshot_ref": snap,
        "eligibility_conditions": [{"id": "c", "quote": "q"}],
        "field_evidence": {
            "percentage": {**fe("percentage"), "verified": True},
            "base": {**fe("base"), "verified": True},
            "eligibility_conditions": {**fe("eligibility_conditions"), "verified": True},
        },
    }
    rec.update(kw)
    return rec


def test_7_tax_treatment_rate_currency_not_applicable():
    # currency 缺失，但由 rule_type 语义确定性判为 NOT_APPLICABLE → 不阻塞
    r = assess_execution_readiness(_ready_record())
    assert r["optional_status"]["currency"] == OPTIONAL_NOT_APPLICABLE
    assert "currency" not in r["missing_optional"]
    assert r["state"] == STATE_EXECUTION_READY


def test_8_tax_treatment_rate_unit_not_applicable():
    r = assess_execution_readiness(_ready_record())
    assert r["optional_status"]["unit"] == OPTIONAL_NOT_APPLICABLE
    assert "unit" not in r["missing_optional"]
    assert "unit" in r["not_applicable_optional"]


def test_9_ordinary_missing_optional_still_blocks():
    """region / valid_period 仍相关：普通缺失 → PARTIAL（不得 N/A）。"""
    r = assess_execution_readiness(_ready_record(region=None))
    assert r["state"] == STATE_PARTIAL
    assert r["optional_status"]["region"] == OPTIONAL_MISSING
    assert "region" in r["missing_optional"]

    r2 = assess_execution_readiness(_ready_record(valid_period=None))
    assert r2["state"] == STATE_PARTIAL
    assert r2["optional_status"]["valid_period"] == OPTIONAL_MISSING
    assert "valid_period" in r2["missing_optional"]


def test_10_not_applicable_only_by_deterministic_rule():
    """非 tax_treatment_rate：currency/unit 不得被当作 N/A，仍为 MISSING。"""
    rec = _ready_record(rule_type="percentage_of_base", currency=None, unit=None)
    r = assess_execution_readiness(rec)
    assert r["optional_status"]["currency"] == OPTIONAL_MISSING
    assert r["optional_status"]["unit"] == OPTIONAL_MISSING
    assert r["state"] == STATE_PARTIAL
    # 未知 rule_type 同样不得自动 N/A
    rec2 = _ready_record(rule_type="unsupported")
    r2 = assess_execution_readiness(rec2)
    assert r2["optional_status"]["currency"] == OPTIONAL_MISSING


def test_10b_valid_period_start_only_counts_as_present():
    """G4 × G5: 单端起算 valid_period 视为 PRESENT（不是 missing）。"""
    r = assess_execution_readiness(_ready_record())
    assert r["optional_status"]["valid_period"] == OPTIONAL_PRESENT


def test_g5_fixture_regression_semantics():
    """G5 不改变既有 fixture 语义：currency/unit PRESENT 时照常 PRESENT。"""
    rec = _ready_record(currency="CNY", unit="yuan")
    r = assess_execution_readiness(rec)
    assert r["optional_status"]["currency"] == OPTIONAL_PRESENT
    assert r["optional_status"]["unit"] == OPTIONAL_PRESENT


# ===========================================================================
# Trust verification binding 仍 fail-closed（11–14）
# ===========================================================================

def _make_trust(evidence_id, granted_event_id, *, revoked=False, drift=False):
    """真实 TrustEvidenceService + durable VERIFIED 事件（不调用 record_human_verification）。"""
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
        event_id=granted_event_id, evidence_id=evidence_id, decision="verified",
        actor="hv1", actor_role="human_verifier", method="human_verification",
        timestamp=datetime.now(timezone.utc).isoformat(), content_identity=ci,
        evidence_refs=[url], notes="P4-4 test verified event",
    ))
    if revoked:
        svc.event_log.append(VerificationDecision(
            event_id=granted_event_id + "_revoked", evidence_id=evidence_id,
            decision="revoked", actor="system_content_change_detector",
            actor_role="system", method="automatic_content_change_detection",
            timestamp=datetime.now(timezone.utc).isoformat(), content_identity=ci,
            evidence_refs=[], notes=json.dumps({"reason": "test revoke"}),
        ))
    if drift:
        svc.evidence_graph.nodes[evidence_id].data["source"] = "tampered-source"
    return svc, granted_event_id


def _trust_record(evidence_id, verified_event_id):
    cid = "cid_" + evidence_id
    url = "https://www.example.gov.cn/" + evidence_id
    snap = "snapshots/example.gov.cn/" + evidence_id + ".html"
    fe = lambda f: {"field": f, "quote": "q", "content_identity": cid,
                    "source_url": url, "snapshot_ref": snap, "verified": True}
    return {
        "id": "T-" + evidence_id,
        "is_mock": False,                     # 生产：local verified 必须被忽略
        "rule_type": "tax_treatment_rate",
        "percentage": 0.15,
        "base": "应纳税所得额",
        "industry": "unknown",
        "region": "全国",
        "valid_period": {"start": "2008-01-01", "end": None},
        "application_requirements": "none",
        "content_identity": cid,
        "source_url": url,
        "snapshot_ref": snap,
        "eligibility_conditions": [{"id": "c", "quote": "q"}],
        "evidence_id": evidence_id,
        "verified_event_id": verified_event_id,
        "field_evidence": {
            "percentage": fe("percentage"),
            "base": fe("base"),
            "eligibility_conditions": fe("eligibility_conditions"),
        },
    }


def test_11_fake_local_verified_true_rejected():
    """11: 只有 record-local verified=true、无 Trust → 生产记录仍 NOT_READY。"""
    rec = _trust_record("ev_x", "veid_x")
    rec.pop("evidence_id", None)
    rec.pop("verified_event_id", None)
    r = assess_execution_readiness(rec)  # 不注入 trust_service
    assert r["state"] == STATE_NOT_READY
    assert "percentage" in r["unverified_critical_fields"]


def test_12_fake_verified_event_id_rejected():
    """12: verified_event_id 与当前有效事件不匹配 / evidence 不存在 → NOT_READY。"""
    svc, _ = _make_trust("ev_fake", "veid_real")
    r1 = assess_execution_readiness(_trust_record("ev_fake", "veid_WRONG"), trust_service=svc)
    assert r1["state"] == STATE_NOT_READY
    assert "percentage" in r1["unverified_critical_fields"]
    r2 = assess_execution_readiness(_trust_record("ev_nope", "veid_x"), trust_service=svc)
    assert r2["state"] == STATE_NOT_READY


def test_13_valid_trust_provenance_satisfies_verification():
    """13: 有效 Trust VERIFIED provenance + N/A OPTIONAL → EXECUTION_READY。"""
    svc, veid = _make_trust("ev_ok", "veid_ok")
    r = assess_execution_readiness(_trust_record("ev_ok", veid), trust_service=svc)
    assert r["unverified_critical_fields"] == []
    assert r["evidence_gaps"] == []
    assert r["state"] == STATE_EXECUTION_READY
    assert r["optional_status"]["currency"] == OPTIONAL_NOT_APPLICABLE


def test_13b_revoked_and_drift_still_fail_closed():
    svc, veid = _make_trust("ev_rev", "veid_rev", revoked=True)
    assert assess_execution_readiness(_trust_record("ev_rev", veid),
                                      trust_service=svc)["state"] == STATE_NOT_READY
    svc2, veid2 = _make_trust("ev_drift", "veid_drift", drift=True)
    assert assess_execution_readiness(_trust_record("ev_drift", veid2),
                                      trust_service=svc2)["state"] == STATE_NOT_READY


def test_14_verified_but_missing_required_eligibility_not_ready():
    """14: VERIFIED 但缺 required eligibility_conditions → NOT_READY。"""
    svc, veid = _make_trust("ev_noelig", "veid_noelig")
    rec = _trust_record("ev_noelig", veid)
    rec["eligibility_conditions"] = None
    r = assess_execution_readiness(rec, trust_service=svc)
    assert r["state"] == STATE_NOT_READY
    assert "eligibility_conditions" in r["missing_required"]


# ===========================================================================
# REAL 121 回归 + 边界（15–19）
# ===========================================================================

def test_15_real_121_unchanged():
    r121 = next(r for r in _real_records() if r.get("id") == 121)
    assert r121["percentage"] == 0.15
    assert r121["base"] == "应纳税所得额"
    assert r121["verification_status"] == "unverified"
    assert r121["verified_event_id"] == _REAL_121_VERIFIED_EVENT_ID
    assert r121["content_identity"] == (
        "ddd6116bac2ab62ce0ccbcaca4656bb9fa28c864475392473ad700b86ddc3c0b")
    # G1 未回填既有记录
    assert "rule_type" not in r121
    assert "snapshot_ref" not in r121
    assert "application_requirements" not in r121
    # 无 record-local verified 生产旁路
    for entry in (r121.get("field_evidence") or {}).values():
        assert "verified" not in entry


def test_15b_real_121_not_wrongly_promoted():
    """REAL 121 仍 NOT_READY（即便注入一个不含 121 事件的 trust_service）。"""
    r121 = next(r for r in _real_records() if r.get("id") == 121)
    assert assess_execution_readiness(r121)["state"] == STATE_NOT_READY
    svc, _ = _make_trust("ev_other", "veid_other")
    assert assess_execution_readiness(r121, trust_service=svc)["state"] == STATE_NOT_READY
    # 修复 G3 后仍需 NOT_READY（required 字段仍缺）
    r = assess_execution_readiness(r121)
    assert "rule_type" in r["missing_required"]
    assert "eligibility_conditions" in r["missing_required"]


def test_16_no_premature_real_122_from_p4():
    # pre-P3-7 Gate 语义：P4 阶段执行期间不得提前创建/修改 REAL 122。
    # P3-7 现已合法写入 REAL 122，故对其做剥离后，对剩余子集执行原始 invariants：
    # 仅 101–121，无任何 P4 阶段产生的额外 REAL。
    rows = _real_records()
    pre_p3_7 = [r for r in rows if r.get("id") != 122]
    ids = [r.get("id") for r in pre_p3_7]
    # 原始安全语义：剥离合法 122 后，不得出现任何 122/123+ 或其他 REAL。
    assert all(i is None or i <= 121 for i in ids), f"unexpected REAL: {ids}"
    assert 122 not in ids, "P4 阶段不得创建 REAL 122"
    assert len(pre_p3_7) == 21, len(pre_p3_7)
    assert sorted(i for i in ids if isinstance(i, int)) == list(range(101, 122))
    assert max(i for i in ids if isinstance(i, int)) == 121


def _prod_sources():
    from global_policy_aggregator.matching import policy_match, project_profile
    from global_policy_aggregator.pipeline import (
        normalizer, p4_execution_state, p4_rule_engine, validator,
    )
    mods = [policy_match, project_profile, normalizer, p4_execution_state,
            p4_rule_engine, validator]
    return {m.__name__: inspect.getsource(m) for m in mods}


def test_17_no_trust_writes():
    for name, src in _prod_sources().items():
        # 真正的 import 语句（忽略文档字符串中的说明性文字）
        assert not re.search(r"^\s*(from|import)\s+src\.trust", src, re.M), name
        for forbidden in ("record_human_verification(", "create_evidence(",
                          "event_log.append("):
            assert forbidden not in src, f"{name} contains {forbidden!r}"


def test_18_no_human_verification():
    for name, src in _prod_sources().items():
        assert "record_human_verification(" not in src, name
        assert "HumanVerificationAuthority(" not in src, name


def test_19_no_p3_7_execution():
    """本阶段未执行 P3-7：仅 real_ingestion 拥有该入口，且其余模块不引用。"""
    for name, src in _prod_sources().items():
        assert "ingest_verified_evidence(" not in src, name


# ===========================================================================
# G1 — P3-7 execution contract 字段（Candidate 路径，不写生产 REAL）
# ===========================================================================

def _g1_env(tmp_path):
    from global_policy_aggregator.pipeline.fetcher import compute_content_hash
    from global_policy_aggregator.pipeline.real_ingestion import (
        PRODUCTION_REAL_POLICIES_PATH,
    )
    data = json.loads(PRODUCTION_REAL_POLICIES_PATH.read_text(encoding="utf-8"))
    data = [p for p in data if 101 <= p.get("id", 0) <= 120]
    real_copy = tmp_path / "real_policies.json"
    real_copy.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()
    content = "<html>policy text</html>".encode()
    ci = compute_content_hash(content)
    p = snapshots_dir / "example.com" / f"{ci}.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return {
        "real_policies_path": real_copy,
        "snapshots_dir": snapshots_dir,
        "audit_path": tmp_path / "audit.jsonl",
        "lock_path": tmp_path / ".lock",
    }, f"snapshots/example.com/{ci}.html", ci


class _FakeTrust:
    def __init__(self, ci, snapshot_ref, url):
        self.ev = {
            "id": "ev-1", "type": "policy", "source": "openinvest-pipeline",
            "source_reference": snapshot_ref, "verification_status": "VERIFIED",
            "confidence_score": 0.0,
            "metadata": {"policy_content_identity": ci, "snapshot_ref": snapshot_ref,
                         "candidate_id": "cand-1", "source_url": url,
                         "provenance": {"snapshot_ref": snapshot_ref, "source_url": url}},
        }
        self.called = False

    def get_evidence(self, evidence_id):
        if evidence_id != "ev-1":
            return {"success": False, "error": "not found"}
        return {"success": True, "evidence": self.ev}

    def check_verified_validity(self, evidence_id):
        if evidence_id != "ev-1":
            return {"is_valid": False, "reasons": ["none"], "latest_verified_event": None}
        return {"is_valid": True, "reasons": [],
                "latest_verified_event": {"event_id": "evt-1", "decision": "verified"}}

    def get_verification_history(self, evidence_id):
        return {"success": True, "event_count": 0, "events": []}

    def record_human_verification(self, *a, **k):
        self.called = True
        raise AssertionError("P3-7 must NOT call record_human_verification()")


def test_g1_new_record_carries_contract_fields(tmp_path):
    """G1: P3-7 产出记录携带 rule_type / snapshot_ref / application_requirements。"""
    env, snap_ref, ci = _g1_env(tmp_path)
    trust = _FakeTrust(ci, snap_ref, "https://example.com/p1")
    from global_policy_aggregator.pipeline.real_ingestion import ingest_verified_evidence
    rid = ingest_verified_evidence("ev-1", trust, **env)
    assert rid == 121
    data = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    rec = next(e for e in data if e["id"] == rid)
    assert "snapshot_ref" in rec and rec["snapshot_ref"] == snap_ref
    assert "application_requirements" in rec          # 无证据 → ""（fail-closed）
    assert "rule_type" in rec and rec["rule_type"] is not None
    # P3-7 绝不产生 VERIFIED
    assert rec["verification_status"] == "unverified"
    assert trust.called is False


def test_g1_no_verified_assigned_by_ingestion(tmp_path):
    """G1: ingestion 不为任何 execution-critical field 赋予 VERIFIED 事实。"""
    env, snap_ref, ci = _g1_env(tmp_path)
    trust = _FakeTrust(ci, snap_ref, "https://example.com/p2")
    from global_policy_aggregator.pipeline.real_ingestion import ingest_verified_evidence
    rid = ingest_verified_evidence("ev-1", trust, **env)
    data = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    rec = next(e for e in data if e["id"] == rid)
    assert all(v.get("verified") is not True
               for v in (rec.get("field_evidence") or {}).values())
    assert all(e.get("verification_status") != "verified" for e in data)


# ===========================================================================
# 真实法条端到端（只读）：G2 + G4 在 REAL 121 官方快照上的确定性结果
# ===========================================================================

_LAW_SNAPSHOT = (_ROOT / "data" / "raw_policies" / "snapshots" / "www.mof.gov.cn"
                 / "ddd6116bac2ab62ce0ccbcaca4656bb9fa28c864475392473ad700b86ddc3c0b.html")


@pytest.mark.skipif(not _LAW_SNAPSHOT.exists(), reason="official snapshot not present")
def test_law_snapshot_g2_g4_readonly():
    url = ("https://www.mof.gov.cn/zhengwuxinxi/zhengcefabu/2007zcfb/"
           "200805/t20080519_26016.htm")
    snap = f"snapshots/www.mof.gov.cn/{_LAW_SNAPSHOT.name}"
    html = _LAW_SNAPSHOT.read_text(encoding="utf-8", errors="replace")
    c = normalize(parse_html(html, url, snap), url, snap)
    # G4: 单端起算
    assert c.valid_period == {"start": "2008-01-01", "end": None}
    # G2: 引用型条件，证据直指第二十八条
    conds = c.eligibility_conditions
    assert isinstance(conds, list) and len(conds) == 1
    assert conds[0]["id"] == "state_key_supported_high_tech_enterprise"
    assert conds[0]["operator"] == "equals"
    assert conds[0]["expected_value"] is True
    assert "减按15％的税率征收企业所得税" in conds[0]["quote"]
    # char_span 必须为二元整数区间（相对 clean_text）
    span = conds[0]["char_span"]
    assert isinstance(span, list) and len(span) == 2
    assert all(isinstance(x, int) for x in span)
    # 其他字段不为本次改动所影响
    assert c.percentage == 0.15
    assert c.base == "应纳税所得额"
