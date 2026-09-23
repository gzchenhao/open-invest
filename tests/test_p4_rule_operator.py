"""P4-2A READ-ONLY Operator integration tests.

READ-ONLY：不修改 real_policies.json / src.trust / 101–121 / 不产生 VERIFIED。
仅消费已落库 REAL 记录与确定性 engine。

同时确认 legacy policy_ai_agent 未进入 P4-2 path（本文件不 import 它）。
"""
import json
from pathlib import Path

from global_policy_aggregator.pipeline.p4_rule_operator import evaluate_policy
from global_policy_aggregator.matching import REAL_POLICIES_PATH

_REAL = Path(REAL_POLICIES_PATH)


def _real_121() -> dict:
    data = json.loads(_REAL.read_text(encoding="utf-8"))
    recs = data["policies"] if isinstance(data, dict) else data
    return next(r for r in recs if r["id"] == 121)


def test_operator_real_121_tax_treatment():
    rec = _real_121()
    # 即使提供明确基数，税率优惠也不估算现金；保留 policy_outcome
    out = evaluate_policy(rec, project_inputs={"taxable_income": 1_000_000})
    assert out["policy_id"] == 121
    assert out["rule_type"] == "tax_treatment_rate"
    assert out["benefit"]["calculation_status"] == "unable_to_calculate"
    assert out["benefit"]["calculated_amount"] is None
    assert out["benefit"]["policy_outcome"] == {
        "applicable_tax_rate": 0.15, "basis": "应纳税所得额"}
    assert out["benefit"]["assumptions"] == []


def test_operator_real_121_evidence_trace():
    rec = _real_121()
    out = evaluate_policy(rec)
    # record-level trace：policy / content_identity / snapshot / source_url / field_evidence
    assert out["policy_id"] == 121
    assert out["content_identity"] == \
        "ddd6116bac2ab62ce0ccbcaca4656bb9fa28c864475392473ad700b86ddc3c0b"
    assert out["source_url"].startswith("https://www.mof.gov.cn")
    assert out["snapshot_ref"].startswith("snapshots/www.mof.gov.cn")
    assert isinstance(out["evidence_refs"], list) and out["evidence_refs"]
    ev = out["evidence_refs"][0]
    assert ev.get("content_identity") == out["content_identity"]
    assert ev.get("source_url") == out["source_url"]


def test_operator_percentage_of_base_with_base():
    rec = {
        "id": 122, "type": "subsidy", "title": "首台套保险补偿",
        "percentage": 0.80, "base": "实际投保年度保费",
        "cap": 0.03, "cap_mode": "relative", "floor": None, "amount": None,
        "currency": "CNY", "unit": None, "eligibility_conditions": [],
        "field_evidence": {
            "percentage": {"value": 0.80, "quote": "80%"},
            "base": {"value": "实际投保年度保费", "quote": "保费"},
            "cap": {"value": 0.03, "quote": "3%"},
        },
    }
    out = evaluate_policy(rec, project_inputs={"annual_premium": 100_000})
    assert out["rule_type"] == "percentage_of_base"
    assert out["benefit"]["calculation_status"] == "calculated"
    assert out["benefit"]["calculated_amount"] == 3000.0


def test_operator_eligibility_unknown_not_fail():
    rec = {
        "id": 123, "type": "tax_break", "title": "高新技术企业税收优惠",
        "percentage": 0.15, "base": "应纳税所得额",
        "eligibility_conditions": [
            {"id": "y", "label": "成立满一年", "source_field": "years_registered",
             "operator": ">=", "threshold": 1.0, "quote": "注册成立一年以上"},
        ],
        "field_evidence": {},
    }
    out = evaluate_policy(rec, project_profile={})
    assert out["eligibility"]["overall"] == "UNKNOWN"


def test_operator_eligibility_conflict_fail():
    rec = {
        "id": 123, "type": "tax_break", "title": "高新技术企业税收优惠",
        "percentage": 0.15, "base": "应纳税所得额",
        "eligibility_conditions": [
            {"id": "y", "label": "成立满一年", "source_field": "years_registered",
             "operator": ">=", "threshold": 1.0, "quote": "注册成立一年以上"},
        ],
        "field_evidence": {},
    }
    out = evaluate_policy(rec, project_profile={"years_registered": 0.5})
    assert out["eligibility"]["overall"] == "FAIL"


def test_operator_fixed_amount_insufficient_unable():
    rec = {
        "id": 127, "type": "subsidy", "title": "模糊金额补贴",
        "percentage": None, "base": None, "amount": "最高5000万元",
        "eligibility_conditions": [],
        "field_evidence": {
            "amount": {"value": "最高5000万元", "quote": "最高5000万元",
                       "snapshot_ref": "s", "content_identity": "c", "source_url": "u"},
        },
    }
    out = evaluate_policy(rec)
    assert out["rule_type"] == "unsupported"
    assert out["benefit"]["calculation_status"] == "unable_to_calculate"
    assert out["benefit"]["assumptions"] == []
