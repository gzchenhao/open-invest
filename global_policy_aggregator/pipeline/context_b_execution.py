"""P6-3.11 — Context B（稳岗返还）最小确定性金额执行。

链路（唯一允许的生产链路）：

    Project Input company_size
            ↓  P6-3.10 确定性 selector（select_context_b_variant）
    selected variant → selected percentage
            +  prior_year_ui_premium_paid
            ↓  既有 p4_rule_engine.calculate_benefit（percentage_of_base）
    Context B benefit amount

严格边界（硬约束）：
* **复用** ``p4_rule_engine.calculate_benefit`` 的既有 ``percentage_of_base`` 计算能力；
  **绝不重新实现第二套 percentage calculator**（本模块不含任何乘法 / 舍入逻辑）。
* LLM 不参与 percentage 选择、不参与金额计算（percentage 来自 P6-3.10 确定性 selector）。
* 不做企业划型：``company_size`` 必须来自用户显式陈述，由 selector 判定；
  missing / illegal / conflict → UNKNOWN / CONFLICT → ``benefit_amount=None``
  （绝不默认 30% 或 60%，绝不 winner selection）。
* 基数缺失 → ``amount=None``（明确「缺失」，**绝不当 0 计算**）；
  基数 0 是有效值（按既有引擎语义 → 0.0）。
* 基数为负 → fail-closed（既有引擎不拦截负数，必须在本层拦住，**绝不产生负补助**）。
* 仅 Context B 自身「基数 × 比例」；**绝不与 Context A 相加**；
  aggregation / stacking / interaction 保持 NOT_IMPLEMENTED（生产入口仍
  ``aggregation_status = "NOT_SUPPORTED"``）。
* 不修改 REAL、不创建/修改 Trust Event、不触碰 src/trust / orchestrator / rule_operator。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from global_policy_aggregator.pipeline.context_b_evidence import (
    CONTEXT_B_BASE_REQUIRED_INPUT,
    select_context_b_variant,
)
from global_policy_aggregator.pipeline.p4_rule_engine import (
    PolicyRule,
    calculate_benefit,
)

CONTEXT_B_BASE_INPUT = CONTEXT_B_BASE_REQUIRED_INPUT   # "prior_year_ui_premium_paid"
CONTEXT_B_CONTEXT_ID = "Context B"
CONTEXT_B_RULE_ID = "rule_context_b_stabilization_subsidy"
CONTEXT_B_POLICY_ID = 122

# 政策 Context B 基数原文（仅作留痕 / 说明；不参与数值计算）
CONTEXT_B_BASE_TEXT = "企业及其职工上年度实际缴纳失业保险费"


def build_context_b_rule(selected_percentage: float,
                         policy_id: int = CONTEXT_B_POLICY_ID) -> PolicyRule:
    """构造 Context B 的 ``percentage_of_base`` PolicyRule。

    该 rule 只作为**既有** ``calculate_benefit`` 的输入；
    cap / floor / cap_mode / floor_mode 一律 None（政策未声明 → 不猜测、不套用）。
    """
    return PolicyRule(
        rule_id=CONTEXT_B_RULE_ID,
        policy_id=policy_id,
        rule_type="percentage_of_base",
        formula=(f"calculated_amount = project_input[{CONTEXT_B_BASE_INPUT}] "
                 "* percentage"),
        inputs=[CONTEXT_B_BASE_INPUT],
        percentage=selected_percentage,
        base=CONTEXT_B_BASE_TEXT,
        cap=None,
        floor=None,
        cap_mode=None,
        floor_mode=None,
        currency="CNY",
    )


def _base_result(company_size, sel, base_value) -> Dict[str, Any]:
    return {
        "context_id": CONTEXT_B_CONTEXT_ID,
        "policy_id": CONTEXT_B_POLICY_ID,
        "rule_type": "percentage_of_base",
        "company_size_input": company_size,
        "selector_status": sel["status"],
        "selected_variant": sel["selected_variant"],
        "selected_percentage": sel["percentage"],
        "base_input": CONTEXT_B_BASE_INPUT,
        "base_value": base_value,
        "calculation_status": "unable_to_calculate",
        "benefit_amount": None,
        "currency": "CNY",
        "executed_monetary": False,
        "aggregation_status": "NOT_SUPPORTED",
        "reason": "",
    }


def execute_context_b(project_inputs: Optional[Dict[str, Any]] = None
                      ) -> Dict[str, Any]:
    """执行 Context B 最小确定性金额计算。

    Returns:
        dict: context_id / policy_id / rule_type / company_size_input /
              selector_status / selected_variant / selected_percentage /
              base_input / base_value / calculation_status / benefit_amount /
              currency / executed_monetary / aggregation_status / reason /
              （可选）engine_explanation / input_values / limitations
    """
    project_inputs = project_inputs or {}
    company_size = project_inputs.get("company_size")
    base_value = project_inputs.get(CONTEXT_B_BASE_INPUT)

    # 1) 确定性 selector：company_size → 单一 variant / percentage
    sel = select_context_b_variant(company_size)
    out = _base_result(company_size, sel, base_value)

    # 2) selector 未确定单一 variant（missing / illegal / conflict）→ fail-closed
    #    绝不默认 30% 或 60%，绝不 winner selection
    if sel["status"] != "SELECTED" or sel["percentage"] is None:
        out["reason"] = (f"company_size 未确定为单一 variant"
                         f"（selector_status={sel['status']}）→ 不计算金额")
        return out

    pct = sel["percentage"]

    # 3) 基数缺失（None）→ 金额 None；明确「缺失」，绝不当 0 计算
    if base_value is None:
        out["reason"] = (f"已选定 {pct:.0%}（{sel['selected_variant']}），"
                         f"但缺少基数 {CONTEXT_B_BASE_INPUT} → 不计算金额")
        out["limitations"] = [f"项目未提供基数输入 '{CONTEXT_B_BASE_INPUT}' → 无法计算。"]
        return out

    # 4) 基数非数值 / 负数 → fail-closed（既有引擎不拦截，必须在本层拦住）
    try:
        base_f = float(base_value)
    except (TypeError, ValueError):
        out["reason"] = f"基数 {CONTEXT_B_BASE_INPUT} 非数值 → fail-closed，不计算金额"
        return out
    if base_f < 0:
        out["reason"] = (f"基数 {CONTEXT_B_BASE_INPUT} 为负（{base_f}）"
                         f" → fail-closed，不产生负补助")
        return out

    # 5) 复用既有 percentage_of_base 确定性计算（唯一 calculator）
    rule = build_context_b_rule(pct)
    calc = calculate_benefit(rule, project_inputs)
    out["calculation_status"] = calc.calculation_status
    out["benefit_amount"] = calc.calculated_amount
    out["executed_monetary"] = calc.calculation_status == "calculated"
    out["engine_explanation"] = calc.explanation
    out["input_values"] = dict(calc.input_values)
    out["limitations"] = list(calc.limitations)
    if calc.calculation_status == "calculated":
        out["reason"] = (f"company_size={company_size} → {sel['selected_variant']}"
                         f"（{pct:.0%}）；base × percentage 确定性计算")
    else:
        out["reason"] = f"既有 calculator 返回 {calc.calculation_status} → 不产生金额"
    return out
