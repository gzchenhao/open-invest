# -*- coding: utf-8 -*-
"""P4-5.3 — Rule Context → Project Input → Eligibility → Benefit E2E（READ-ONLY）。

消费 P4-5.2 产出的 ``RuleContext``（来自 ``audit_policy_rule_contexts["contexts"]``），
输入项目事实（fixture / read-only），确定性地跑通：

    Project Input Contract（事实供给）
        → Eligibility（READY / UNKNOWN / FAIL）
        → Benefit Calculation（CALCULATED 金额 / UNABLE）

设计原则（与 P4-5.2 一致，且新增 fail-closed 语义）：
1. **禁止猜测 / 默认值**：缺事实 → Eligibility=UNKNOWN、Benefit=UNABLE；分档缺
   企业规模 → 绝不默认 large/SME。
2. **决策延续**：per-unit（元/人）按 ``数量 × 单位额度`` 计算，不当一次性总额；
   分档用 ``benefit_variants`` 选档，扁平 ``percentage``/``cap`` 仅留痕、不用于计算。
3. **Evidence 5-tuple 不断链**：policy 字段（amount/percentage/base/variant）继续携带
   quote/char_span/snapshot_ref/content_identity/source_url；项目事实显式标注为 fixture
   提供，不与官方 policy 字段混淆。
4. **信任边界**：``derived ≠ approved ≠ VERIFIED``。record-local ``verified``/``approved``
   **不构成**证据，不得绕过缺失事实检查或 provenance 判定。本模块**不 import src/trust、
   不写 Trust、不调用 Human Verification**。

生产禁止：不修改 REAL 101–121 / 不创建 REAL 122 / 不写 real_policies.json / 不 commit。
"""

from typing import Any, Dict, List, Optional, Tuple

# 复用 P4-5.2 的治理判定（record-local 批准/verified 非法 → 治理违规）
from global_policy_aggregator.pipeline.rule_context import (
    RD_NOT_READY, RD_READY, _BASE_INPUT, _COMPANY_SIZE_INPUT,
)

SCHEMA_VERSION = "p4-5.3-e2e-v1"

# Eligibility 状态
EL_READY, EL_UNKNOWN, EL_NOT_READY, EL_FAIL = "READY", "UNKNOWN", "NOT_READY", "FAIL"
# Benefit 状态
BEN_CALC, BEN_UNABLE = "CALCULATED", "UNABLE"

# 外部官方统计（政策引用但未给数值）通过独立参数注入（read-only，来自 fixture），
# 不混入 project_facts（project_facts 仅承载企业自身事实）。
_EXT_TARGET_KEY = "layoff_rate_control_target_max"


def _cmp(value: Any, op: str, threshold: float) -> bool:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False
    if op in (">=", "≥"):
        return v >= threshold
    if op in ("<=", "≤"):
        return v <= threshold
    if op in (">", "＞"):
        return v > threshold
    if op in ("<", "＜"):
        return v < threshold
    if op in ("==", "="):
        return v == threshold
    return False


def _matches(value: Any, expected: Any) -> bool:
    if isinstance(expected, (list, tuple, set)):
        return value in expected
    return value == expected


def evaluate_eligibility(ctx: Dict[str, Any], project_facts: Dict[str, Any],
                         external_statistics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """对单个 Rule Context 做 Eligibility 判定（fail-closed）。

    返回 status（READY/UNKNOWN/FAIL）、逐条件结果、理由。
    """
    facts = project_facts or {}
    ext = external_statistics or {}
    conditions_out: List[Dict[str, Any]] = []
    reasons: List[str] = []
    status = EL_READY

    # 1) 分档规则需要 variant_selector 才能确定适用规则；缺失 → UNKNOWN（禁止默认档位）
    variants = ctx.get("benefit_variants") or []
    if variants:
        vs_field = variants[0].get("applies_when", {}).get("source_field")
        if facts.get(vs_field) is None:
            status = EL_UNKNOWN
            reasons.append(
                f"variant_selector '{vs_field}' 缺失 → 无法解析适用档位，禁止默认取任一档")

    # 2) 逐条件评估
    for cond in ctx.get("conditions") or []:
        cid = cond.get("id")
        src = cond.get("source_field")
        # 2a) 条件性前置：前置不成立 → 该条件不适用（中性，不 fail）
        pre = cond.get("precondition")
        if pre:
            pv = facts.get(pre.get("source_field"))
            if pv is None:
                conditions_out.append({"id": cid, "result": "PRECONDITION_UNKNOWN",
                                       "detail": "前置条件事实缺失"})
                continue
            if not _cmp(pv, pre.get("operator"), float(pre.get("threshold"))):
                conditions_out.append({"id": cid, "result": "NOT_APPLICABLE",
                                       "detail": "前置条件不成立 → 该条件不适用"})
                continue
        # 2b) 外部官方统计阈值（政策未给数值）
        if cond.get("threshold_source") == "external_official_statistic_not_in_policy":
            target = ext.get(cid)
            if target is None:
                conditions_out.append({"id": cid, "result": "DEFERRED",
                                       "detail": "外部官方统计阈值（如全国城镇调查失业率控制目标）"
                                                 "未由 fixture 提供 → 无法核验，标记 UNKNOWN"})
                status = EL_UNKNOWN
                continue
            lv = facts.get(src)
            if lv is None:
                conditions_out.append({"id": cid, "result": "UNKNOWN",
                                       "detail": "项目裁员率缺失"})
                status = EL_UNKNOWN
                continue
            if not _cmp(lv, "<=", target):
                conditions_out.append({"id": cid, "result": "FAIL",
                                       "detail": f"裁员率 {lv} 高于控制目标 {target}"})
                status = EL_FAIL
                continue
            conditions_out.append({"id": cid, "result": "PASS",
                                   "detail": f"裁员率 {lv} ≤ 控制目标 {target}"})
            continue
        # 2c) 普通条件
        val = facts.get(src)
        if val is None:
            conditions_out.append({"id": cid, "result": "UNKNOWN",
                                   "detail": f"资格条件所需项目事实 '{src}' 缺失"})
            status = EL_UNKNOWN
            continue
        if cond.get("operator") == "equals":
            if _matches(val, cond.get("expected_value")):
                conditions_out.append({"id": cid, "result": "PASS", "detail": ""})
            else:
                conditions_out.append({"id": cid, "result": "FAIL",
                                       "detail": f"'{val}' 不满足 {cond.get('label')}"})
                status = EL_FAIL
        else:
            if _cmp(val, cond.get("operator"), float(cond.get("threshold"))):
                conditions_out.append({"id": cid, "result": "PASS", "detail": ""})
            else:
                conditions_out.append({"id": cid, "result": "FAIL",
                                       "detail": f"'{val}' 违反 {cond.get('label')}"})
                status = EL_FAIL

    # 3) 聚合：FAIL 优先；其次 UNKNOWN
    results = {c["result"] for c in conditions_out}
    if EL_FAIL in results:
        status = EL_FAIL
    elif "FAIL" in results:
        status = EL_FAIL
    elif EL_UNKNOWN in results or "UNKNOWN" in results or "DEFERRED" in results \
            or "PRECONDITION_UNKNOWN" in results:
        status = EL_UNKNOWN

    return {"status": status, "conditions": conditions_out, "reasons": reasons}


def _policy_field_evidence(ctx: Dict[str, Any], names: List[str]) -> List[Dict[str, Any]]:
    """提取执行关键 policy 字段的完整 5-tuple 证据（quote/char_span/snapshot_ref/
    content_identity/source_url）。"""
    fields = ctx.get("fields") or {}
    out: List[Dict[str, Any]] = []
    for n in names:
        cf = fields.get(n)
        if not cf:
            continue
        ev = {k: cf.get(k) for k in ("quote", "char_span", "snapshot_ref",
                                      "content_identity", "source_url", "method")}
        ev["field"] = n
        ev["value"] = cf.get("value")
        out.append(ev)
    # 分档：每档绑定其官方条款（content_identity/source_url 取自本上下文 evidence_refs）
    refs = ctx.get("evidence_refs") or [{}]
    for v in ctx.get("benefit_variants") or []:
        out.append({
            "field": f"variant:{v.get('variant_id')}",
            "value": v.get("percentage"),
            "quote": v.get("quote"), "char_span": v.get("char_span"),
            "snapshot_ref": refs[0].get("snapshot_ref"),
            "content_identity": refs[0].get("content_identity"),
            "source_url": refs[0].get("source_url"),
            "method": "variant_regex",
        })
    return out


def evaluate_benefit(ctx: Dict[str, Any], project_facts: Dict[str, Any],
                     eligibility: Dict[str, Any],
                     external_statistics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """对单个 Rule Context 做 Benefit 计算（仅在 Eligibility=READY 时计算；否则 UNABLE）。"""
    facts = project_facts or {}
    rt = ctx.get("rule_type")
    currency = ctx.get("currency") or "CNY"

    if eligibility.get("status") == EL_FAIL:
        return {"status": BEN_UNABLE, "amount": None, "currency": currency,
                "reason": "eligibility FAIL → 不产生正向 Benefit（fail-closed）",
                "evidence": {"policy_field_evidence": [], "project_input_bindings": []}}
    if eligibility.get("status") != EL_READY:
        return {"status": BEN_UNABLE, "amount": None, "currency": currency,
                "reason": f"eligibility={eligibility.get('status')} → 不可计算 Benefit",
                "evidence": {"policy_field_evidence": [], "project_input_bindings": []}}

    # ---- Context A：fixed_amount（per-person / per-unit）----
    if rt == "fixed_amount":
        amount = ctx.get("amount")
        pu = (ctx.get("benefit_basis") or {}).get("per_unit") or {}
        unit = ctx.get("unit")
        qty_key = pu.get("quantity_input") or "hired_person_count"
        if amount is None:
            return {"status": BEN_UNABLE, "amount": None, "currency": currency,
                    "reason": "fixed_amount 金额无 policy 证据", "evidence": {}}
        # per-person 语义锁定：amount 必须显式为「每人」计量；unit 缺失则 fail-closed，
        # 禁止把单位额度误当一次性总额。
        if not unit:
            return {"status": BEN_UNABLE, "amount": None, "currency": currency,
                    "reason": "per-unit unit（元/人）缺失 → 无法断言 per-person 语义，"
                              "禁止按总额计算",
                    "evidence": {"policy_field_evidence": _policy_field_evidence(ctx, ["amount"]),
                                 "project_input_bindings": []}}
        qty = facts.get(qty_key)
        if qty is None:
            return {"status": BEN_UNABLE, "amount": None, "currency": currency,
                    "reason": f"缺项目事实 '{qty_key}'（每人额度 {amount} 元已知，但一次性总额"
                              f"需合格人数）→ 不把单位额度当总额、不默认人数",
                    "evidence": {"policy_field_evidence": _policy_field_evidence(ctx, ["amount"]),
                                 "project_input_bindings": []}}
        if not isinstance(qty, (int, float)) or qty <= 0:
            return {"status": BEN_UNABLE, "amount": None, "currency": currency,
                    "reason": f"合格人数 '{qty_key}'={qty!r} 无效（需正整数）",
                    "evidence": {"policy_field_evidence": _policy_field_evidence(ctx, ["amount"]),
                                 "project_input_bindings": []}}
        # 确定性契约：benefit = 每人额度(amount) × 合格人数(qty)
        #   eligible_hired_persons=1 → amount；=10 → amount×10
        benefit = amount * qty
        return {
            "status": BEN_CALC, "amount": benefit, "currency": currency,
            "unit_rate": amount, "unit": unit, "quantity": qty,
            "per_person_amount": amount, "granularity": "per_hired_person",
            "formula": f"{amount}(每人) × {qty}(合格人数) = {benefit}",
            "reason": "per-person 固定额度（元/人）× 合格招用人数；金额与适用对象仅由政策证明，"
                      "人数由项目事实提供",
            "evidence": {
                "policy_field_evidence": _policy_field_evidence(ctx, ["amount", "unit"]),
                "project_input_bindings": [
                    {"input_key": qty_key, "value": qty, "provided_by": "fixture/project_facts",
                     "note": "合格人数由项目事实提供；政策 Evidence 仅证明『每招用1人不超过1500元』"
                             "（每人额度与适用对象），不证明具体人数"}],
            },
        }

    # ---- Context B：percentage_of_base（分档）----
    if rt == "percentage_of_base":
        variants = ctx.get("benefit_variants") or []
        if not variants:
            return {"status": BEN_UNABLE, "amount": None, "currency": currency,
                    "reason": "percentage_of_base 无分档定义", "evidence": {}}
        vs_field = variants[0].get("applies_when", {}).get("source_field")
        size = facts.get(vs_field)
        variant = next((v for v in variants
                        if v.get("applies_when", {}).get("equals") == size), None)
        if variant is None:
            return {"status": BEN_UNABLE, "amount": None, "currency": currency,
                    "reason": f"无法解析适用档位：'{vs_field}'="
                              f"{size!r} 缺失或不在已知档位（禁止默认 large/SME）",
                    "evidence": {"policy_field_evidence": [], "project_input_bindings": []}}
        base_val = facts.get(_BASE_INPUT)
        if base_val is None:
            return {"status": BEN_UNABLE, "amount": None, "currency": currency,
                    "reason": f"缺项目事实 '{_BASE_INPUT}'（基数 '{ctx.get('base')}' 政策不能提供取值）",
                    "evidence": {
                        "policy_field_evidence": _policy_field_evidence(ctx, ["base"]),
                        "project_input_bindings": [
                            {"input_key": vs_field, "value": size, "provided_by": "fixture",
                             "note": "企业规模由 fixture 提供"}]}}
        pct = variant.get("percentage")
        benefit = base_val * pct
        return {
            "status": BEN_CALC, "amount": benefit, "currency": currency,
            "rate": pct, "base": base_val, "variant": variant.get("applies_when", {}).get("equals"),
            "formula": f"{base_val} × {pct} = {benefit}",
            "reason": "分档比例 × 上年度实际缴纳失业保险费",
            "evidence": {
                "policy_field_evidence": _policy_field_evidence(ctx, ["base"]),
                "project_input_bindings": [
                    {"input_key": vs_field, "value": size, "provided_by": "fixture",
                     "note": "企业规模由 fixture 提供（决定档位）"},
                    {"input_key": _BASE_INPUT, "value": base_val, "provided_by": "fixture/project_facts",
                     "note": "基数实际值由企业事实提供，非官方 policy 字段"}],
            },
        }

    return {"status": BEN_UNABLE, "amount": None, "currency": currency,
            "reason": f"rule_type={rt} 不可直接计算", "evidence": {}}


def evaluate_rule_context(ctx: Dict[str, Any], project_facts: Dict[str, Any],
                          external_statistics: Optional[Dict[str, float]] = None,
                          trust_provenance_valid: bool = False,
                          record: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """端到端评估单个 Rule Context（Eligibility + Benefit + 信任边界叠加）。

    信任边界：``derived ≠ approved ≠ VERIFIED``。
    - ``provenance_readiness`` 仅当 ``trust_provenance_valid=True`` 时为 READY；
      record-local ``verified``/``approved`` **不**提升它、也**不**绕过任何缺失事实检查。
    - ``human_approved`` 恒 False（rule_type 批准必须来自 Trust，非 record-local）。
    - 不写 Trust、不调用 Human Verification。
    """
    record = record or {}
    facts = project_facts or {}

    eligibility = evaluate_eligibility(ctx, facts, external_statistics=external_statistics)
    benefit = evaluate_benefit(ctx, facts, eligibility,
                               external_statistics=external_statistics)

    # 治理：record-local verified/approved 不得被采纳为证据
    record_verified_ignored = bool(record.get("verified") or record.get("approved"))
    provenance_state = RD_READY if trust_provenance_valid else RD_NOT_READY
    application_state = RD_READY if record.get("application_requirements") else RD_NOT_READY

    # E2E 执行就绪度（fail-closed）
    if eligibility.get("status") == EL_FAIL or benefit.get("status") == BEN_UNABLE \
            or provenance_state == RD_NOT_READY or application_state == RD_NOT_READY:
        e2e_readiness = RD_NOT_READY
    else:
        e2e_readiness = RD_READY

    return {
        "schema_version": SCHEMA_VERSION,
        "context_id": ctx.get("context_id"),
        "rule_type": ctx.get("rule_type"),
        "rule_type_source": "derived",
        "human_approved": False,
        "eligibility": eligibility,
        "benefit": benefit,
        "provenance_readiness": provenance_state,
        "application_readiness": application_state,
        "e2e_readiness": e2e_readiness,
        "record_verified_ignored": record_verified_ignored,
        "derived_equals_verified": False,
        "approved_equals_verified": False,
        "trust_boundary": "derived ≠ approved ≠ VERIFIED；record-local verified/approved 不绕过 Trust",
        "note": "本评估为 read-only；不修改 REAL、不写 Trust、不创建 REAL 122。",
    }
