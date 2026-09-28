"""P4-14 — REAL 122 EXECUTION CONTRACT WIRING 的 deterministic 回归测试。

对象：REAL 122（39号通知 Context A：一次性扩岗补助）
校验：G1 结构化 eligibility_conditions / G2 接入现有 Eligibility Engine /
     G3 修正 Benefit = 1500 × eligible_hired_persons / G4 granularity 证据 /
     G5 Application Readiness 保持 NOT_READY / Trust provenance 不变 /
     101–121 byte-level 不变 / Production Event Log 仍为 1 条 verification event。

执行语义纪律：
- 全部必要条件满足 → PASS；明确冲突 → FAIL；缺项目事实/外部定义 → UNKNOWN
- UNKNOWN 不得自动转 FAIL
- eligible_hired_persons 必须由 per_person 条件派生，绝不直接采用聚合 hired_persons
- eligibility != PASS 或缺合格人数 → Benefit = UNABLE_TO_CALCULATE
"""
import json
import hashlib
import os

import pytest

from global_policy_aggregator.pipeline.p4_rule_engine import (
    build_rule_from_real_record,
    check_eligibility,
    calculate_benefit,
    derive_eligible_hired_persons,
)
from global_policy_aggregator.pipeline.p4_rule_operator import evaluate_policy
from global_policy_aggregator.pipeline.p4_execution_state import assess_execution_readiness

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_PATH = os.path.join(
    REPO, "global_policy_aggregator", "data", "real_policies", "real_policies.json"
)
EVENT_LOG = os.path.join(REPO, "trust_config", "production_trust_events.jsonl")

SUBSET121_SHA = "b3dc6f47e72951545c80b117f9c803c7e5ea5e50916fe0e66fe1a158a0246da3"


def _real122():
    d = json.loads(open(REAL_PATH, encoding="utf-8").read())
    return next(e for e in d if e["id"] == 122)


def _persons(n, eligible):
    ps = []
    for i in range(n):
        ok = i < eligible
        ps.append(
            {
                "target_group": "grad_2026" if ok else "other",
                "labor_contract_signed": ok,
                "employment_insurance_paid_months": 5 if ok else 0,
                "hire_date": "2026-05-01" if ok else "2025-05-01",
            }
        )
    return ps


def _profile(entity="企业"):
    return {"applicant_entity_type": entity}


# ---------------- G1 ----------------
def test_g1_eligibility_conditions_structured():
    r = _real122()
    ec = r["eligibility_conditions"]
    assert isinstance(ec, list) and len(ec) == 5
    ids = {c["id"] for c in ec}
    assert ids == {
        "entity_scope",
        "hired_target_group_in_scope",
        "labor_contract_signed",
        "employment_insurance_paid_months",
        "execution_period",
    }
    assert any(c.get("granularity") == "project" for c in ec)
    assert sum(1 for c in ec if c.get("granularity") == "per_person") == 4
    for c in ec:  # 每条件都需可追溯
        assert c.get("quote"), c["id"]
        assert c.get("char_span"), c["id"]


# ---------------- A. Eligibility ----------------
def test_a_eligibility_all_pass():
    rule = build_rule_from_real_record(_real122())
    assert check_eligibility(rule, project_profile=_profile()).overall == "PASS"


def test_a_eligibility_missing_fact_unknown():
    rule = build_rule_from_real_record(_real122())
    assert check_eligibility(rule, project_profile={}).overall == "UNKNOWN"


def test_a_eligibility_conflict_fail():
    rule = build_rule_from_real_record(_real122())
    assert check_eligibility(rule, project_profile=_profile("个体户")).overall == "FAIL"


def test_a_unknown_not_auto_fail():
    rule = build_rule_from_real_record(_real122())
    res = check_eligibility(rule, project_profile={})
    assert res.overall == "UNKNOWN"
    assert res.overall != "FAIL"


# ---------------- B. eligible_hired_persons 派生 ----------------
def test_b_derive_1():
    rule = build_rule_from_real_record(_real122())
    n, err = derive_eligible_hired_persons(rule, {"hired_persons": _persons(1, 1)})
    assert n == 1 and err is None


def test_b_derive_10():
    rule = build_rule_from_real_record(_real122())
    n, err = derive_eligible_hired_persons(rule, {"hired_persons": _persons(10, 10)})
    assert n == 10


def test_b_raw_not_used():
    # 10 人但仅 7 合格 → 派生 7，绝不直接用聚合 hired_persons=10
    rule = build_rule_from_real_record(_real122())
    n, err = derive_eligible_hired_persons(rule, {"hired_persons": _persons(10, 7)})
    assert n == 7


def test_b_missing_persons_fail_closed():
    rule = build_rule_from_real_record(_real122())
    n, err = derive_eligible_hired_persons(rule, {})
    assert n is None and err


# ---------------- C. Benefit ----------------
def test_c_pass_1():
    rule = build_rule_from_real_record(_real122())
    b = calculate_benefit(
        rule, project_inputs={"hired_persons": _persons(1, 1)}, eligibility_overall="PASS"
    )
    assert b.calculation_status == "calculated" and b.calculated_amount == 1500


def test_c_pass_10():
    rule = build_rule_from_real_record(_real122())
    b = calculate_benefit(
        rule, project_inputs={"hired_persons": _persons(10, 10)}, eligibility_overall="PASS"
    )
    assert b.calculation_status == "calculated" and b.calculated_amount == 15000


def test_c_unknown():
    rule = build_rule_from_real_record(_real122())
    b = calculate_benefit(
        rule, project_inputs={"hired_persons": _persons(10, 10)}, eligibility_overall="UNKNOWN"
    )
    assert b.calculation_status == "unable_to_calculate"


def test_c_fail():
    rule = build_rule_from_real_record(_real122())
    b = calculate_benefit(
        rule, project_inputs={"hired_persons": _persons(10, 10)}, eligibility_overall="FAIL"
    )
    assert b.calculation_status == "unable_to_calculate"


def test_c_missing_eligible():
    rule = build_rule_from_real_record(_real122())
    b = calculate_benefit(rule, project_inputs={}, eligibility_overall="PASS")
    assert b.calculation_status == "unable_to_calculate"


def test_c_end_to_end_evaluate_policy():
    res = evaluate_policy(
        _real122(),
        project_inputs={"hired_persons": _persons(10, 10)},
        project_profile=_profile(),
    )
    assert res["eligibility"]["overall"] == "PASS"
    assert res["benefit"]["calculated_amount"] == 15000
    assert res["benefit"]["input_values"]["eligible_hired_persons"] == 10


# ---------------- D. Evidence ----------------
def test_d_amount_evidence():
    fe = _real122()["field_evidence"]["amount"]
    assert fe.get("quote") and fe.get("char_span") and fe.get("char_span")[0] is not None
    assert fe.get("content_identity") and fe.get("source_url")


def test_d_granularity_evidence():
    fe = _real122()["field_evidence"]["granularity"]
    assert fe.get("quote"), "granularity 缺 quote（G4）"
    assert fe.get("char_span") and fe["char_span"][0] is not None, "granularity 缺 char_span（G4）"
    assert fe.get("snapshot_ref") and fe.get("content_identity") and fe.get("source_url")


def test_d_evidence_chain():
    r = _real122()
    for fld in ("amount", "granularity", "unit"):
        fe = r["field_evidence"][fld]
        assert fe.get("quote") and fe.get("snapshot_ref") and fe.get("content_identity") and fe.get("source_url")


# ---------------- E. Trust / provenance / Event Log ----------------
def test_e_event_log_one_verification():
    events = [
        json.loads(l)
        for l in open(EVENT_LOG, encoding="utf-8").read().splitlines()
        if l.strip()
    ]
    verified = [
        e for e in events if e.get("event_type") == "verification" or e.get("decision") == "verified"
    ]
    # P6-3.18（M1/M3）向 durable Event Log 合法新增 Context A 独立证据及其验证事件，
    # 基线由 1 → 4。本断言仅保证验证事件数 == durable 基线（不被运行时追加）。
    assert len(verified) == 4, f"verification event 数应为 4（P6-3.18 durable 基线），实际 {len(verified)}"


def test_e_real122_provenance_unchanged():
    r = _real122()
    assert r["id"] == 122
    assert r["evidence_id"] == "ev_1e2d555ae07193b5c257"
    assert r["verified_event_id"] == "fc50856de78547df8dc5d9f29b4b270d"
    assert (
        r["content_identity"]
        == "1e2d555ae07193b5c2574f6cd426b2028068fa266461e899462e493c0f8ae76b"
    )
    assert (
        r["trust_content_identity"]
        == "b4012feb48e86e999b3149eb42fd62d91f1a8049e22daeda24d9dd4a89292937"
    )
    assert r["verifier_id"] == "human-reviewer-howard"
    assert r["verifier_role"] == "human_verifier"
    assert (
        r["source_url"]
        == "https://www.gov.cn/zhengce/zhengceku/202607/content_7074139.htm"
    )
    assert (
        r["snapshot_ref"]
        == "snapshots/www.gov.cn/1e2d555ae07193b5c2574f6cd426b2028068fa266461e899462e493c0f8ae76b.html"
    )


def test_e_101_121_byte_level_unchanged():
    d = json.loads(open(REAL_PATH, encoding="utf-8").read())
    sub = [e for e in d if 101 <= e["id"] <= 121]
    assert (
        hashlib.sha256(json.dumps(sub, ensure_ascii=False, indent=2).encode()).hexdigest()
        == SUBSET121_SHA
    )


# ---------------- G5 ----------------
def test_g5_application_readiness_not_ready():
    res = assess_execution_readiness(_real122())
    assert res["state"] == "NOT_READY"
    assert "application_requirements" in res.get("missing_required", [])
    # eligibility_conditions 已结构化，不应再出现在 missing_required
    assert "eligibility_conditions" not in res.get("missing_required", [])
