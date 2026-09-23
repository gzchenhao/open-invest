"""P4-2B REAL POLICY END-TO-END READ-ONLY EXECUTION VERIFICATION.

READ-ONLY：不修改 real_policies.json / src.trust / 101–121 / 不产生 VERIFIED。
仅读取 REAL 121 + 构造测试 ProjectProfile/inputs + 调用 p4_rule_operator。

场景：
- CASE A 信息不足：缺失事实 → UNKNOWN / N/A，绝不自动 FAIL，assumptions=[]。
- CASE B 明确冲突：ProjectProfile 与 policy condition 明确冲突 → FAIL（非缺资料）。
- CASE C REAL 121 Tax Treatment：两次执行（无/有 taxable_income）均 unable，无臆造现金。
- Evidence Trace：policy_id / content_identity / source_url / snapshot_ref / evidence_refs。
- Cash subsidy fixture：base×percentage，relative cap / absolute cap / floor / missing mode。
- Legacy boundary：policy_ai_agent 未进入 P4-2 operator/engine 路径。

说明：生产 REAL 数据**所有记录 eligibility_conditions 均为 null**（仅 REAL 121 出现该键且为 null），
故 CASE B（需结构化条件）使用 fixture policy（task 允许：使用现有测试 fixture 即可）。
"""

import ast
import inspect
import json
from pathlib import Path

import pytest

from global_policy_aggregator.matching import REAL_POLICIES_PATH
from global_policy_aggregator.pipeline.p4_rule_engine import (
    build_rule_from_real_record,
    calculate_benefit,
    check_eligibility,
)
from global_policy_aggregator.pipeline.p4_rule_operator import evaluate_policy

_REAL = Path(REAL_POLICIES_PATH)


def _real(id: int) -> dict:
    data = json.loads(_REAL.read_text(encoding="utf-8"))
    recs = data["policies"] if isinstance(data, dict) else data
    return next(r for r in recs if r["id"] == id)


# 复刻企业所得税法「高新技术企业」条件的 fixture policy（生产 REAL 无结构化条件）。
def _tax_break_with_conditions() -> dict:
    return {
        "id": 9001, "title": "高新技术企业税收优惠（fixture）", "type": "tax_break",
        "percentage": 0.15, "base": "应纳税所得额",
        "cap": None, "floor": None, "amount": None,
        "eligibility_conditions": [
            {"id": "registered_years_min", "label": "成立满一年",
             "source_field": "years_registered", "operator": ">=", "threshold": 1.0,
             "quote": "注册成立一年以上"},
            {"id": "rd_staff_ratio_min", "label": "研发人员比例",
             "source_field": "rd_staff_ratio", "operator": ">=", "threshold": 0.10,
             "quote": "科技人员比例不低于10%"},
        ],
        "field_evidence": {},
    }


# ── CASE A — 信息不足 ──

def test_case_a_real_121_insufficient_info():
    # REAL 121 无结构化 eligibility 条件（eligibility_conditions=null）
    rec = _real(121)
    out = evaluate_policy(rec, project_profile={})  # 缺失 eligibility 事实
    # Benefit：税率优惠本就 unable（不依赖项目事实）
    assert out["rule_type"] == "tax_treatment_rate"
    assert out["benefit"]["calculation_status"] == "unable_to_calculate"
    assert out["benefit"]["calculated_amount"] is None
    assert out["benefit"]["assumptions"] == []
    # Eligibility：无结构化条件 → N/A（绝不 FAIL）
    assert out["eligibility"]["overall"] == "N/A"
    assert out["eligibility"]["assumptions"] == [] if "assumptions" in out["eligibility"] \
        else True


def test_case_a_fixture_unknown_not_fail():
    # 有结构化条件但 ProjectProfile 缺失关键事实 → UNKNOWN（不得 FAIL）
    rec = _tax_break_with_conditions()
    out = evaluate_policy(rec, project_profile={})
    assert out["eligibility"]["overall"] == "UNKNOWN"
    assert all(c["status"] == "UNKNOWN" for c in out["eligibility"]["conditions"])
    assert "UNKNOWN" in out["eligibility"]["explanation"]
    assert out["benefit"]["assumptions"] == []


def test_case_a_cash_missing_base_unable():
    # 现金补贴（fixture）缺失基数输入 → benefit unable，assumptions=[]
    rec = {
        "id": 9002, "type": "subsidy", "title": "首台套保险补偿（fixture）",
        "percentage": 0.80, "base": "实际投保年度保费",
        "cap": 0.03, "cap_mode": "relative", "floor": None, "amount": None,
        "eligibility_conditions": [],
        "field_evidence": {
            "percentage": {"value": 0.80}, "base": {"value": "实际投保年度保费"},
            "cap": {"value": 0.03},
        },
    }
    out = evaluate_policy(rec, project_inputs={})  # 缺失 annual_premium
    assert out["rule_type"] == "percentage_of_base"
    assert out["benefit"]["calculation_status"] == "unable_to_calculate"
    assert out["benefit"]["calculated_amount"] is None
    assert out["benefit"]["assumptions"] == []


# ── CASE B — 明确冲突 ──

def test_case_b_conflict_fail():
    rec = _tax_break_with_conditions()
    # 明确冲突：成立 0.5 年（<1），研发人员 5%（<10%）
    out = evaluate_policy(rec, project_profile={
        "years_registered": 0.5, "rd_staff_ratio": 0.05})
    assert out["eligibility"]["overall"] == "FAIL"
    statuses = {c["condition_id"]: c["status"] for c in out["eligibility"]["conditions"]}
    assert statuses["registered_years_min"] == "FAIL"
    assert statuses["rd_staff_ratio_min"] == "FAIL"
    # FAIL 源于明确冲突，而非缺资料
    assert "冲突" in out["eligibility"]["explanation"]
    assert out["benefit"]["assumptions"] == []


# ── CASE C — REAL 121 Tax Treatment（两次）──

def _assert_tax_treatment(out):
    assert out["rule_type"] == "tax_treatment_rate"
    assert out["benefit"]["calculation_status"] == "unable_to_calculate"
    assert out["benefit"]["calculated_amount"] is None
    assert out["benefit"]["policy_outcome"]["applicable_tax_rate"] == 0.15
    assert out["benefit"]["policy_outcome"]["basis"] == "应纳税所得额"
    # 绝不输出臆造 cash benefit（如 150000）
    assert out["benefit"]["calculated_amount"] != 150000
    assert "150000" not in json.dumps(out["benefit"], ensure_ascii=False)
    assert out["benefit"]["assumptions"] == []


def test_case_c_no_taxable_income():
    rec = _real(121)
    out = evaluate_policy(rec)  # 不提供 taxable_income
    _assert_tax_treatment(out)


def test_case_c_with_taxable_income():
    rec = _real(121)
    out = evaluate_policy(rec, project_inputs={"taxable_income": 1_000_000})
    # 即使提供基数，税率优惠也不计算现金，assumptions 仍为空
    _assert_tax_treatment(out)


# ── 三、Evidence Trace（REAL 121）──

def test_evidence_trace_real_121():
    rec = _real(121)
    out = evaluate_policy(rec)
    assert out["policy_id"] == 121
    assert out["content_identity"] == \
        "ddd6116bac2ab62ce0ccbcaca4656bb9fa28c864475392473ad700b86ddc3c0b"
    assert out["source_url"].startswith("https://www.mof.gov.cn")
    assert out["snapshot_ref"] is not None
    assert out["snapshot_ref"].startswith("snapshots/www.mof.gov.cn")
    assert isinstance(out["evidence_refs"], list) and out["evidence_refs"]
    for ev in out["evidence_refs"]:
        assert ev.get("content_identity")
        assert ev.get("source_url")
        assert ev.get("snapshot_ref")


# ── 四、Cash subsidy fixture（base × percentage）──

def _cash_rec(cap=None, cap_mode=None, floor=None, floor_mode=None):
    return {
        "id": 9003, "type": "subsidy", "title": "测试现金补贴",
        "percentage": 0.80, "base": "实际投保年度保费",
        "cap": cap, "cap_mode": cap_mode, "floor": floor, "floor_mode": floor_mode,
        "amount": None, "eligibility_conditions": [],
        "field_evidence": {},
    }


def test_cash_subsidy_normal_and_caps():
    # normal: 100000 * 0.80 = 80000
    res = calculate_benefit(build_rule_from_real_record(_cash_rec()),
                            project_inputs={"annual_premium": 100_000})
    assert res.calculated_amount == 80000.0
    assert res.calculation_status == "calculated"

    # relative cap: min(80000, 100000*0.03=3000) = 3000
    res = calculate_benefit(build_rule_from_real_record(_cash_rec(cap=0.03, cap_mode="relative")),
                            project_inputs={"annual_premium": 100_000})
    assert res.calculated_amount == 3000.0

    # absolute cap: min(80000, 5000) = 5000
    res = calculate_benefit(build_rule_from_real_record(_cash_rec(cap=5000.0, cap_mode="absolute")),
                            project_inputs={"annual_premium": 100_000})
    assert res.calculated_amount == 5000.0

    # floor: max(100*0.80=80, 1000) = 1000
    res = calculate_benefit(build_rule_from_real_record(_cash_rec(floor=1000.0, floor_mode="absolute")),
                            project_inputs={"annual_premium": 100})
    assert res.calculated_amount == 1000.0

    # missing cap mode → unable（不猜）
    res = calculate_benefit(build_rule_from_real_record(_cash_rec(cap=0.03, cap_mode=None)),
                            project_inputs={"annual_premium": 100_000})
    assert res.calculation_status == "unable_to_calculate"
    assert res.calculated_amount is None
    assert res.assumptions == []


# ── 五、Legacy agent boundary（静态确认未进入 P4-2 path）──

def test_legacy_agent_not_in_p4_path():
    import global_policy_aggregator.pipeline.p4_rule_operator as op
    import global_policy_aggregator.pipeline.p4_rule_engine as eng
    # 用 AST 检查「真实代码引用」（docstring 中为说明用途提及 legacy agent 是允许的）。
    for mod in (op, eng):
        tree = ast.parse(inspect.getsource(mod))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod_name = node.module or ""
                for n in node.names:
                    assert "policy_ai_agent" not in (mod_name + "." + n.name)
            if isinstance(node, ast.Name):
                assert node.id != "investment_capacity_usd"
                assert node.id != "policy_ai_agent"
            if isinstance(node, ast.Attribute):
                assert node.attr != "investment_capacity_usd"
                assert node.attr != "policy_ai_agent"
