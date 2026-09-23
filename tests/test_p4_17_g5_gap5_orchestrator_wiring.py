"""P4-17 — G5 + GAP-5 ORCHESTRATOR WIRING 的 deterministic 回归测试。

对象：REAL 122（39号通知 Context A：一次性扩岗补助）
目标：证明 orchestrator 不再因 Application Readiness = NOT_READY 而在最前面短路，
      而是仅当存在「执行阻断」缺口（Policy Contract / Trust VERIFIED /
      execution-critical Evidence / governance violation）才阻止。

G5（P4-17）：application_requirements="" / ext_procedural_channel=UNKNOWN 属 Application-only
            缺口，不阻断 Eligibility / Benefit；Eligibility/Benefit 在 Application NOT_READY
            时仍可经 orchestrator 真实执行。
GAP-5（P4-17）：REAL 122 补 field_evidence["eligibility_conditions"]（复用 amount 真实
            provenance），解除 execution-critical Evidence 缺口。

纪律：
- Trust Gate 不被降低：本文件用 faithful VERIFIED stub 驱动 P4-3.1 的
  ``_trust_provenance_valid``（is_valid + latest_verified_event.event_id == verified_event_id）；
  测试 #10 以 trust_service=None（生产默认 fail-closed）证明 Trust 未 VERIFIED 时仍阻断。
- 不修改 real_policies.json / src.trust / production event log；不调用 Human Verification。
- 不因测试而放宽任何 Trust / Evidence / Eligibility 规则。
"""
import json
import os

import pytest

from global_policy_aggregator.pipeline.p4_execution_state import (
    STATE_NOT_READY,
    STATE_READY,
    assess_execution_readiness,
    execution_blocking_ready,
)
from global_policy_aggregator.pipeline.p4_execution_orchestrator import (
    evaluate_project_against_policies,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_PATH = os.path.join(
    REPO, "global_policy_aggregator", "data", "real_policies", "real_policies.json"
)
EVENT_LOG = os.path.join(REPO, "trust_config", "production_trust_events.jsonl")


def _real122():
    d = json.loads(open(REAL_PATH, encoding="utf-8").read())
    return next(e for e in d if e["id"] == 122)


def _persons(n, eligible):
    return [
        {
            "target_group": "grad_2026" if i < eligible else "other",
            "labor_contract_signed": i < eligible,
            "employment_insurance_paid_months": 5 if i < eligible else 0,
            "hire_date": "2026-05-01" if i < eligible else "2025-05-01",
        }
        for i in range(n)
    ]


def _profile(entity="企业"):
    return {"applicant_entity_type": entity}


class _VerifiedTrustStub:
    """Faithful stand-in for the production TrustEvidenceService VERIFIED binding.

    仅返回 P4-3.1 ``_trust_provenance_valid`` 所依赖的形状：is_valid=True 且
    latest_verified_event.event_id == record.verified_event_id。不读取/不写入任何
    Trust 文件、不产生任何 Trust event。其它 evidence_id 一律 invalid（fail-closed）。
    """

    def __init__(self, evidence_id, verified_event_id):
        self._eid = evidence_id
        self._veid = verified_event_id

    def check_verified_validity(self, evidence_id):
        if evidence_id == self._eid:
            return {
                "is_valid": True,
                "latest_verified_event": {"event_id": self._veid},
            }
        return {"is_valid": False, "reasons": ["evidence not verified"]}


def _trust():
    r = _real122()
    return _VerifiedTrustStub(r["evidence_id"], r["verified_event_id"])


# ===================== A. orchestrator 全满足 =====================
def test_1_orchestrator_full_pass():
    out = evaluate_project_against_policies(
        _profile(), [_real122()],
        project_inputs={"hired_persons": _persons(10, 10)},
        trust_service=_trust(),
    )
    e = out[0]
    # Overall 与 Application 仍 NOT_READY（不伪造）
    assert e["readiness_state"] == STATE_NOT_READY
    assert e["application_readiness"] == STATE_NOT_READY
    assert "application_requirements" in e["application_gaps"]
    assert "ext_procedural_channel" in e["application_gaps"]
    # 但 Match / Eligibility / Benefit 已真实执行
    assert e["match"] is not None
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["benefit"]["calculated_amount"] == 15000
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 10


# ===================== B. 缺事实 → UNKNOWN / UNABLE =====================
def test_2_missing_fact_unknown():
    out = evaluate_project_against_policies(
        {}, [_real122()],
        project_inputs={"hired_persons": _persons(10, 10)},
        trust_service=_trust(),
    )
    e = out[0]
    assert e["eligibility"]["overall"] == "UNKNOWN"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"
    assert e["application_readiness"] == STATE_NOT_READY
    assert e["readiness_state"] == STATE_NOT_READY


# ===================== C. 明确冲突 → FAIL / UNABLE =====================
def test_3_conflict_fail():
    out = evaluate_project_against_policies(
        _profile("个体户"), [_real122()],
        project_inputs={"hired_persons": _persons(10, 10)},
        trust_service=_trust(),
    )
    e = out[0]
    assert e["eligibility"]["overall"] == "FAIL"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"


# ===================== D. 10 hired / 7 eligible =====================
def test_4_seven_of_ten():
    out = evaluate_project_against_policies(
        _profile(), [_real122()],
        project_inputs={"hired_persons": _persons(10, 7)},
        trust_service=_trust(),
    )
    e = out[0]
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculated_amount"] == 10500
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 7


# ===================== 5. application_requirements 空不阻断 =====================
def test_5_application_requirements_empty_not_blocking():
    r = _real122()
    assert r["application_requirements"] == ""
    res = assess_execution_readiness(r, trust_service=_trust())
    # execution_blocking_missing 必须排除 application_requirements
    assert "application_requirements" not in res["execution_blocking_missing"]
    # Application Readiness 仍 NOT_READY，但执行可放行
    assert res["application_readiness"] == STATE_NOT_READY
    assert execution_blocking_ready(res) is True


# ===================== 6. ext_procedural_channel UNKNOWN 不阻断 =====================
def test_6_ext_procedural_channel_unknown_not_blocking():
    r = _real122()
    assert r.get("ext_procedural_channel") in (None, "", "UNKNOWN")
    res = assess_execution_readiness(r, trust_service=_trust())
    assert "ext_procedural_channel" in res["application_gaps"]
    assert res["application_readiness"] == STATE_NOT_READY
    assert execution_blocking_ready(res) is True


# ===================== 7. eligibility_conditions 顶层 Evidence 完整 =====================
def test_7_eligibility_conditions_top_evidence():
    r = _real122()
    fe = r["field_evidence"]["eligibility_conditions"]
    assert fe.get("quote"), "eligibility_conditions 缺 quote（GAP-5）"
    assert fe.get("char_span") and fe["char_span"][0] is not None, "缺 char_span（GAP-5）"
    assert fe["content_identity"] == r["content_identity"]
    assert fe["source_url"] == r["source_url"]
    assert fe["snapshot_ref"] == r["snapshot_ref"]
    # Trust VERIFIED 后不再出现在 evidence_gaps / unverified
    res = assess_execution_readiness(r, trust_service=_trust())
    assert "eligibility_conditions" not in res["evidence_gaps"]
    assert "eligibility_conditions" not in res["unverified_critical_fields"]


# ===================== 8. amount Evidence 完整 =====================
def test_8_amount_evidence_complete():
    fe = _real122()["field_evidence"]["amount"]
    assert fe.get("quote") and fe.get("char_span") and fe.get("char_span")[0] is not None
    assert fe.get("content_identity") and fe.get("source_url") and fe.get("snapshot_ref")


# ===================== 9. granularity Evidence 完整 =====================
def test_9_granularity_evidence_complete():
    fe = _real122()["field_evidence"]["granularity"]
    assert fe.get("quote"), "granularity 缺 quote（G4）"
    assert fe.get("char_span") and fe["char_span"][0] is not None, "granularity 缺 char_span（G4）"
    assert fe.get("snapshot_ref") and fe.get("content_identity") and fe.get("source_url")


# ===================== 10. Trust 未 VERIFIED 时仍阻止执行 =====================
def test_10_trust_not_verified_still_blocks():
    # 不注入 trust_service（生产默认 fail-closed）
    out = evaluate_project_against_policies(
        _profile(), [_real122()],
        project_inputs={"hired_persons": _persons(10, 10)},
    )
    e = out[0]
    assert e["match"] is None
    assert e["eligibility"] is None
    assert e["benefit"] is None
    # 证明阻断来自执行层（unverified_critical_fields），非 Application 层
    res = assess_execution_readiness(_real122())
    assert execution_blocking_ready(res) is False
    assert res["unverified_critical_fields"], "Trust 未注入时应有 unverified_critical_fields"


# ===================== 11. 不产生新的 Trust Event =====================
def test_11_no_new_trust_event():
    events = [
        json.loads(l)
        for l in open(EVENT_LOG, encoding="utf-8").read().splitlines()
        if l.strip()
    ]
    verified = [
        e for e in events
        if e.get("event_type") == "verification" or e.get("decision") == "verified"
    ]
    assert len(verified) == 1, f"production verification event 数应为 1，实际 {len(verified)}"


# ===================== 12. raw hired_persons 不得冒充 eligible =====================
def test_12_raw_hired_persons_not_used():
    svc = _trust()
    # 10 人仅 7 合格 → benefit 必须用派生 7，绝不直接用聚合 hired_persons=10
    out = evaluate_project_against_policies(
        _profile(), [_real122()],
        project_inputs={"hired_persons": _persons(10, 7)},
        trust_service=svc,
    )
    e = out[0]
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 7
    assert e["benefit"]["calculated_amount"] == 10500
    # 10 人 0 合格 → 0（引擎派生，非读取聚合）
    out0 = evaluate_project_against_policies(
        _profile(), [_real122()],
        project_inputs={"hired_persons": _persons(10, 0)},
        trust_service=svc,
    )
    assert out0[0]["benefit"]["input_values"]["eligible_hired_persons"] == 0
    assert out0[0]["benefit"]["calculated_amount"] == 0
