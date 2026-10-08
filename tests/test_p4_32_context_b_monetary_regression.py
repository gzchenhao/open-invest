# -*- coding: utf-8 -*-
"""P6-4 B1 — Context B（稳岗返还）committed monetary regression coverage.

Context B 生产代码（context_b_execution.py / context_b_evidence.py）已正确 fail-closed；
但既有 test_p6_3_* 测试被 .gitignore 的全局 test_*.py 陷阱忽略，无 durable coverage。
本文件以 tests/test_p4_* 命名，规避 ignore 陷阱，提供对真实 production monetary
boundary 的 committed 回归覆盖。

覆盖的 production security / correctness 边界：
  * missing input → unable_to_calculate（不把缺失当 0）
  * base=None ≠ 0.0；base=0 → 合法的确定性 0.0
  * base<0 → fail-closed（不产生负补贴）
  * variant selector：missing / illegal / conflict → UNKNOWN / CONFLICT，
    绝不默认 30% / 60%，绝不 winner selection，绝不 policy stacking
  * 合法 base × percentage → deterministic result（不经由 LLM 决定金额）

本文件只 import production 代码并断言其行为；不修改任何 production / trust / real /
P5 / B2 / B3 / .gitignore。
"""
from global_policy_aggregator.pipeline.context_b_execution import execute_context_b
from global_policy_aggregator.pipeline.context_b_evidence import select_context_b_variant


# ── 1. unable_to_calculate priority（关键 input 缺失）─────────────────────
def test_unable_to_calculate_when_company_size_missing():
    """company_size 缺失 → selector UNKNOWN → unable_to_calculate，金额 None。"""
    res = execute_context_b({"prior_year_ui_premium_paid": 10000.0})
    assert res["selector_status"] == "UNKNOWN"
    assert res["calculation_status"] == "unable_to_calculate"
    assert res["benefit_amount"] is None
    assert res["executed_monetary"] is False
    # 不得把缺失当作 0 去计算
    assert res["benefit_amount"] != 0


def test_unable_to_calculate_when_base_missing():
    """selector 已确定（大型企业），但基数缺失 → unable_to_calculate，金额 None。"""
    res = execute_context_b({"company_size": "大型企业"})
    assert res["selector_status"] == "SELECTED"
    assert res["selected_percentage"] == 0.30
    assert res["calculation_status"] == "unable_to_calculate"
    assert res["benefit_amount"] is None
    assert res["executed_monetary"] is False


# ── 2. null ≠ zero ────────────────────────────────────────────────────────
def test_base_none_is_not_zero():
    """base=None 必须得到 None，绝不能静默当作 0 计算。"""
    res = execute_context_b({"company_size": "大型企业",
                              "prior_year_ui_premium_paid": None})
    assert res["calculation_status"] == "unable_to_calculate"
    assert res["benefit_amount"] is None
    assert res["benefit_amount"] != 0


def test_base_zero_is_valid_deterministic_zero():
    """base=0 是合法值（≠ None），确定性得到 0.0，且 executed_monetary 成功。"""
    res = execute_context_b({"company_size": "大型企业",
                              "prior_year_ui_premium_paid": 0})
    assert res["calculation_status"] == "calculated"
    assert res["benefit_amount"] == 0.0
    assert res["executed_monetary"] is True
    # 与 base=None 的结果严格区分
    assert res["benefit_amount"] is not None


# ── 3. negative base fail-closed ──────────────────────────────────────────
def test_negative_base_fail_closed():
    """base<0 → fail-closed，不计算负补贴，不产生成功 monetary execution。"""
    res = execute_context_b({"company_size": "大型企业",
                              "prior_year_ui_premium_paid": -100.0})
    assert res["calculation_status"] == "unable_to_calculate"
    assert res["benefit_amount"] is None
    assert res["executed_monetary"] is False
    # 不产生负补助
    assert res["benefit_amount"] != -30.0


# ── 4. Context B variant conflict / missing / illegal ─────────────────────
def test_variant_selector_missing_is_unknown():
    sel = select_context_b_variant(None)
    assert sel["status"] == "UNKNOWN"
    assert sel["selected_variant"] is None
    assert sel["percentage"] is None


def test_variant_selector_noncanonical_is_unknown():
    """非 canonical 取值（如 超大型企业）不得默认归入任一档。"""
    sel = select_context_b_variant("超大型企业")
    assert sel["status"] == "UNKNOWN"
    assert sel["selected_variant"] is None
    assert sel["percentage"] is None


def test_variant_selector_conflict_is_conflict():
    sel = select_context_b_variant(["大型企业", "中小微企业"])
    assert sel["status"] == "CONFLICT"
    assert sel["selected_variant"] is None
    assert sel["percentage"] is None


def test_execute_context_b_variant_conflict_no_winner():
    """conflicting company_size → 不默认 30%/60%，不 winner selection，金额 None。"""
    res = execute_context_b({"company_size": ["大型企业", "中小微企业"],
                              "prior_year_ui_premium_paid": 10000.0})
    assert res["selector_status"] == "CONFLICT"
    assert res["calculation_status"] == "unable_to_calculate"
    assert res["benefit_amount"] is None
    assert res["executed_monetary"] is False
    # 明确不得出现 stacking / 相加 / winner
    assert res["aggregation_status"] == "NOT_SUPPORTED"


# ── 5. deterministic monetary calculation ─────────────────────────────────
def test_deterministic_calculation_large_enterprise():
    """大型企业 30%：base × 0.30 确定性结果，不经 LLM。"""
    res = execute_context_b({"company_size": "大型企业",
                              "prior_year_ui_premium_paid": 10000.0})
    assert res["selector_status"] == "SELECTED"
    assert res["selected_percentage"] == 0.30
    assert res["calculation_status"] == "calculated"
    assert res["benefit_amount"] == 3000.0
    assert res["executed_monetary"] is True
    assert res["aggregation_status"] == "NOT_SUPPORTED"


def test_deterministic_calculation_sme():
    """中小微企业 60%：base × 0.60 确定性结果。"""
    res = execute_context_b({"company_size": "中小微企业",
                              "prior_year_ui_premium_paid": 10000.0})
    assert res["selected_percentage"] == 0.60
    assert res["calculation_status"] == "calculated"
    assert res["benefit_amount"] == 6000.0
    assert res["executed_monetary"] is True
