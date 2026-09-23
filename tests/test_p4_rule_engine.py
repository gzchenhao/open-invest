"""P4-2 Deterministic Benefit / Eligibility Engine tests.

覆盖：
- tax_treatment_rate 不得错误建模为 15% 现金补贴（REAL 121 同构）
- percentage_of_base 计算 + cap(relative) 应用
- 缺失基数输入 → unable_to_calculate
- 缺失项目事实 → UNKNOWN（≠ FAIL）
- 明确冲突 → FAIL
- 全 PASS → overall PASS
- assumptions 必须为空
- rule_type 确定性（移除 title 猜测；type=tax_break / 已知税基 → tax_treatment_rate）
- missing rate → unsupported / unable
- base=None → unable
- fixed_amount 确定性成功（含 normalized_number 证据）
- fixed_amount insufficient（字符串金额不可猜）→ unable
- floor(absolute) 应用
- absolute cap 应用
- cap mode 未明确 → unable
- rule_type 无法确定（未知基数）→ unsupported
- evidence_refs provenance（content_identity / source_url / snapshot_ref）
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from global_policy_aggregator.pipeline.p4_rule_engine import (
    build_rule_from_real_record,
    calculate_benefit,
    check_eligibility,
)


def _fe(value, quote="q", method="m"):
    return {"value": value, "quote": quote, "char_span": [0, 1],
            "snapshot_ref": "snapshots/x/y.html", "method": method,
            "content_identity": "ci", "source_url": "https://gov.cn/p"}


def _hightech_record():
    return {
        "id": 121,
        "title": "高新技术企业税收优惠",
        "type": "tax_break",
        "description": "减按15%税率征收企业所得税",
        "percentage": 0.15,
        "base": "应纳税所得额",
        "cap": None, "floor": None, "amount": None,
        "eligibility_conditions": [
            {"id": "registered_years_min", "label": "成立满一年",
             "source_field": "years_registered", "operator": ">=",
             "threshold": 1.0, "quote": "注册成立一年以上",
             "char_span": [0, 1], "snapshot_ref": "snapshots/x/y.html"},
            {"id": "rd_staff_ratio_min", "label": "研发人员比例",
             "source_field": "rd_staff_ratio", "operator": ">=",
             "threshold": 0.10, "quote": "科技人员比例不低于10%",
             "char_span": [0, 1], "snapshot_ref": "snapshots/x/y.html"},
        ],
        "field_evidence": {
            "percentage": _fe(0.15, quote="减按15%的税率"),
            "base": _fe("应纳税所得额", quote="以应纳税所得额为计税依据"),
        },
    }


def _firstset_record():
    # cap 语义必须显式声明：relative（cap 为 base 的比例上限）
    return {
        "id": 122,
        "title": "首台套保险补偿",
        "type": "subsidy",
        "description": "按保费的80%补贴，费率上限3%",
        "percentage": 0.80,
        "base": "实际投保年度保费",
        "cap": 0.03, "cap_mode": "relative", "floor": None,
        "amount": None,
        "eligibility_conditions": [],
        "field_evidence": {
            "percentage": _fe(0.80, quote="80%给予补贴"),
            "base": _fe("实际投保年度保费", quote="实际投保年度保费"),
            "cap": _fe(0.03, quote="费率上限3%"),
        },
    }


def _nopct_record():
    return {
        "id": 124, "title": "某补贴", "type": "subsidy",
        "percentage": None, "base": "应纳税所得额",
        "cap": None, "floor": None, "amount": None,
        "eligibility_conditions": [], "field_evidence": {},
    }


def _nobase_record():
    return {
        "id": 125, "title": "某比例补贴", "type": "subsidy",
        "percentage": 0.20, "base": None,
        "cap": None, "floor": None, "amount": None,
        "eligibility_conditions": [], "field_evidence": {},
    }


def _fixed_record():
    return {
        "id": 126, "title": "固定金额补贴", "type": "subsidy",
        "percentage": None, "base": None,
        "cap": None, "floor": None,
        "amount": {"normalized_number": 5_000_000.0, "raw": "500万元", "currency": "CNY"},
        "currency": "CNY", "unit": "元",
        "eligibility_conditions": [],
        "field_evidence": {
            "amount": {"value": {"normalized_number": 5_000_000.0, "raw": "500万元"},
                       "quote": "500万元", "snapshot_ref": "s",
                       "content_identity": "c", "source_url": "u"},
        },
    }


def _fixed_insufficient_record():
    # amount 仅为字符串，无 normalized_number → 不得猜测
    return {
        "id": 127, "title": "模糊金额补贴", "type": "subsidy",
        "percentage": None, "base": None,
        "cap": None, "floor": None, "amount": "最高5000万元",
        "eligibility_conditions": [],
        "field_evidence": {
            "amount": {"value": "最高5000万元", "quote": "最高5000万元",
                       "snapshot_ref": "s", "content_identity": "c", "source_url": "u"},
        },
    }


def _floor_record():
    # 使用非税基数（保费），明确为现金补贴，避免与税基判定冲突
    return {
        "id": 128, "title": "带下限补贴", "type": "subsidy",
        "percentage": 0.50, "base": "实际投保年度保费", "cap": None,
        "floor": 1000.0, "floor_mode": "absolute",
        "amount": None, "eligibility_conditions": [],
        "field_evidence": {
            "percentage": _fe(0.50), "base": _fe("实际投保年度保费"),
            "floor": _fe(1000.0),
        },
    }


def _abs_cap_record():
    return {
        "id": 129, "title": "绝对上限补贴", "type": "subsidy",
        "percentage": 0.80, "base": "实际投保年度保费",
        "cap": 5000.0, "cap_mode": "absolute", "floor": None,
        "amount": None, "eligibility_conditions": [],
        "field_evidence": {
            "percentage": _fe(0.80), "base": _fe("实际投保年度保费"),
            "cap": _fe(5000.0),
        },
    }


def _nocapmode_record():
    return {
        "id": 130, "title": "无 cap mode 补贴", "type": "subsidy",
        "percentage": 0.80, "base": "实际投保年度保费",
        "cap": 0.03, "cap_mode": None, "floor": None,
        "amount": None, "eligibility_conditions": [],
        "field_evidence": {},
    }


def _unkbase_record():
    # type 未明确现金/税率信号，且基数不在已知映射 → rule_type 无法确定 → unsupported
    return {
        "id": 131, "title": "未知基数政策", "type": "unknown",
        "percentage": 0.30, "base": "营业收入",
        "cap": None, "floor": None, "amount": None,
        "eligibility_conditions": [], "field_evidence": {},
    }


def test_tax_treatment_not_modeled_as_cash_subsidy():
    rec = _hightech_record()
    rule = build_rule_from_real_record(rec)
    assert rule.rule_type == "tax_treatment_rate"
    res = calculate_benefit(rule, project_inputs={"taxable_income": 1_000_000})
    # 税率优惠不是现金补贴：不计算「节省」，calculated_amount 仍为 None
    assert res.calculation_status == "unable_to_calculate"
    assert res.calculated_amount is None
    assert res.policy_outcome == {"applicable_tax_rate": 0.15,
                                  "basis": "应纳税所得额"}
    # 严禁把 15% 当作现金补贴来计算金额：explanation 必须明确是税率优惠，
    # 且不得给出任何补贴金额（"补贴"仅以否定形式出现 = 正确澄清）。
    assert "税率" in res.explanation
    assert "15%" in res.explanation
    assert res.assumptions == []


def test_percentage_of_base_with_cap():
    rec = _firstset_record()
    rule = build_rule_from_real_record(rec)
    assert rule.rule_type == "percentage_of_base"
    assert rule.inputs == ["annual_premium"]
    res = calculate_benefit(rule, project_inputs={"annual_premium": 100_000})
    assert res.calculation_status == "calculated"
    # 100000 * 0.80 = 80000，但 cap = base*3% = 3000 → 应用上限
    assert res.calculated_amount == 3000.0
    assert res.assumptions == []


def test_percentage_of_base_missing_input_unable():
    rec = _firstset_record()
    rule = build_rule_from_real_record(rec)
    res = calculate_benefit(rule, project_inputs={})
    assert res.calculation_status == "unable_to_calculate"
    assert res.calculated_amount is None
    assert res.assumptions == []


def test_eligibility_unknown_not_fail():
    rec = _hightech_record()
    rule = build_rule_from_real_record(rec)
    # 项目未提供任何字段 → 全部 UNKNOWN，整体 UNKNOWN（不得 FAIL）
    res = check_eligibility(rule, project_profile={})
    assert all(c.status == "UNKNOWN" for c in res.conditions)
    assert res.overall == "UNKNOWN"
    assert "UNKNOWN" in res.explanation


def test_eligibility_partial_pass_unknown():
    rec = _hightech_record()
    rule = build_rule_from_real_record(rec)
    res = check_eligibility(rule, project_profile={
        "years_registered": 3,           # PASS
        "rd_staff_ratio": None,          # UNKNOWN
    })
    statuses = {c.condition_id: c.status for c in res.conditions}
    assert statuses["registered_years_min"] == "PASS"
    assert statuses["rd_staff_ratio_min"] == "UNKNOWN"
    assert res.overall == "UNKNOWN"


def test_eligibility_conflict_fail():
    rec = _hightech_record()
    rule = build_rule_from_real_record(rec)
    res = check_eligibility(rule, project_profile={
        "years_registered": 0.5,         # 冲突 → FAIL
        "rd_staff_ratio": 0.20,          # PASS
    })
    statuses = {c.condition_id: c.status for c in res.conditions}
    assert statuses["registered_years_min"] == "FAIL"
    assert res.overall == "FAIL"


def test_eligibility_all_pass():
    rec = _hightech_record()
    rule = build_rule_from_real_record(rec)
    res = check_eligibility(rule, project_profile={
        "years_registered": 5,
        "rd_staff_ratio": 0.20,
    })
    assert all(c.status == "PASS" for c in res.conditions)
    assert res.overall == "PASS"


# ── 审计缺口补齐 ──

def test_missing_rate_unsupported():
    rec = _nopct_record()
    rule = build_rule_from_real_record(rec)
    assert rule.rule_type == "unsupported"
    res = calculate_benefit(rule)
    assert res.calculation_status == "unable_to_calculate"
    assert res.assumptions == []


def test_base_none_unable():
    rec = _nobase_record()
    rule = build_rule_from_real_record(rec)
    assert rule.rule_type == "percentage_of_base"
    assert rule.inputs == []
    res = calculate_benefit(rule, project_inputs={"taxable_income": 100})
    assert res.calculation_status == "unable_to_calculate"
    assert res.assumptions == []


def test_fixed_amount_success():
    rec = _fixed_record()
    rule = build_rule_from_real_record(rec)
    assert rule.rule_type == "fixed_amount"
    res = calculate_benefit(rule)
    assert res.calculation_status == "calculated"
    assert res.calculated_amount == 5_000_000.0
    assert res.assumptions == []


def test_fixed_amount_insufficient_evidence():
    rec = _fixed_insufficient_record()
    rule = build_rule_from_real_record(rec)
    # 字符串金额无 normalized_number → 不得猜测 → unsupported
    assert rule.rule_type == "unsupported"
    res = calculate_benefit(rule)
    assert res.calculation_status == "unable_to_calculate"
    assert res.assumptions == []


def test_floor_absolute_applied():
    rec = _floor_record()
    rule = build_rule_from_real_record(rec)
    assert rule.rule_type == "percentage_of_base"
    res = calculate_benefit(rule, project_inputs={"annual_premium": 100})
    # 100*0.5=50 < floor 1000 → 取 1000
    assert res.calculated_amount == 1000.0
    assert res.assumptions == []


def test_absolute_cap_applied():
    rec = _abs_cap_record()
    rule = build_rule_from_real_record(rec)
    assert rule.rule_type == "percentage_of_base"
    res = calculate_benefit(rule, project_inputs={"annual_premium": 100_000})
    # 80000 绝对上限 5000 → 取 5000
    assert res.calculated_amount == 5000.0
    assert res.assumptions == []


def test_missing_cap_mode_unable():
    rec = _nocapmode_record()
    rule = build_rule_from_real_record(rec)
    assert rule.rule_type == "percentage_of_base"
    res = calculate_benefit(rule, project_inputs={"annual_premium": 100_000})
    assert res.calculation_status == "unable_to_calculate"
    assert any("cap" in lim.lower() for lim in res.limitations)
    assert res.assumptions == []


def test_unknown_base_unsupported():
    rec = _unkbase_record()
    rule = build_rule_from_real_record(rec)
    # 基数不在已知映射 → rule_type 无法确定 → unsupported（不得猜测）
    assert rule.rule_type == "unsupported"
    res = calculate_benefit(rule, project_inputs={"营业收入": 100})
    assert res.calculation_status == "unable_to_calculate"
    assert res.assumptions == []


def test_evidence_refs_provenance():
    rec = _hightech_record()
    rule = build_rule_from_real_record(rec)
    res = calculate_benefit(rule, project_inputs={"taxable_income": 1_000_000})
    assert res.evidence_refs
    for ev in res.evidence_refs:
        assert ev.get("content_identity")
        assert ev.get("source_url")
        assert ev.get("snapshot_ref")
