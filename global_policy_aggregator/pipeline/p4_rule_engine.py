"""P4-2 Deterministic Benefit / Eligibility Engine.

设计边界（JUDGE P4-2 / P4-2A）：
- 本模块**仅做确定性计算**；不调用 LLM、不估算、不猜测、不补全 Policy 条件。
- 所有 rule 必须可追溯到 Policy Evidence（field_evidence / quote / snapshot /
  content_identity / source_url）。
- 任一计算所需输入缺失 → ``calculation_status = "unable_to_calculate"``，
  ``calculated_amount = None``，``assumptions = []``。
- 税率优惠（tax_treatment_rate）**不是现金补贴**：不虚构「15% 现金补贴」，
  不推断比较基准税率（如 25%）来计算「节省」。仅报告适用税率（policy outcome）。
- Eligibility：每条件 PASS / FAIL / UNKNOWN；项目事实缺失 → UNKNOWN（≠ FAIL）；
  仅所有 required 条件明确 PASS 才整体 PASS，存在明确冲突则整体 FAIL。

rule_type 判定（确定性，禁止 title 猜测）：
  1. **approved** rule_type：仅当记录携带 ``rule_type_approved`` 且该批准被正确绑定到
     Trust VERIFIED provenance（``rule_type_approval`` 校验通过）时采用。
  2. 否则 **derived** rule_type（确定性推导，READ-ONLY 分析可用）：
     - 记录为「存量语义」记录（无 ``rule_type_derived`` / ``rule_type_approval``
       分离字段）时，显式 ``rule_type`` 字段仍按历史约定生效；
     - 否则按 ``type`` 字段：``tax_break`` → tax_treatment_rate；
     - 否则按「已知基数映射」：
       - 基数为已知税基（应纳税所得额/应纳所得税额/研发费用/研发支出）→ tax_treatment_rate；
       - 基数为已知非税基数（实际投保年度保费/实际保费）→ percentage_of_base；
       - 基数不在已知映射 → 无法确定 rule_type → unsupported（不得猜测）；
     - 结构化固定金额（amount/field_evidence 含 normalized_number）→ fixed_amount；
       **但**若同一记录同时存在「固定金额」与「比例+基数」两套互相竞争的规则信号
       （即同一记录内含多个 rule context）→ 无法确定**单一** rule_type → unsupported
       （fail-closed，绝不静默合并 / 静默丢弃其一）。
     - 其余 → unsupported。

D4（P4-5.1）derived / approved / VERIFIED 三分（绝不混同）：
  - ``derived_rule_type``：确定性推导结果，**不等于** human-approved；ingestion 不得把
    derived 写为 production-approved 事实（ingestion 只写 ``rule_type_derived``，
    ``rule_type_approved`` 保持 None）。
  - ``approved_rule_type``：只能由携带**合法批准 provenance**（approval_event_id 绑定
    Trust ``verified_event_id``、evidence_id / content_identity 一致、approver 非空）的
    记录提供；任何「自称已批准」但 provenance 不完整/伪造的标记 → fail-closed。
  - Trust ``VERIFIED``：由外部 Trust 服务提供，本模块**不产生、不写回** verification 状态；
    derived/approved 均**不等于** VERIFIED。

cap / floor 语义（显式）：
  - ``cap_mode`` / ``floor_mode`` 必须为 ``"relative"`` 或 ``"absolute"``；
  - 若模式不明确 → ``unable_to_calculate``，``assumptions = []``，不得猜测。

本模块不写入 real_policies.json、不调用 src/trust、不产生 verification 状态。
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import date


# ── 基数文本 → 项目输入键 映射（仅确定性已知映射，绝不语义推断未知基数）──
BASE_INPUT_MAP = {
    "应纳税所得额": "taxable_income",
    "应纳所得税额": "taxable_income",
    "实际投保年度保费": "annual_premium",
    "实际保费": "annual_premium",
    "研发费用": "rd_expense",
    "研发支出": "rd_expense",
}

# 确定性已知「税基」：基数为这些输入 → 属于税率优惠（tax treatment），非现金补贴。
_BASE_TAX_INPUTS = {"taxable_income", "rd_expense"}

# 显式现金补贴类型（structured type 字段）：比例应用于基数即现金补贴（可计算）。
_CASH_TYPES = {"subsidy", "grant", "cash", "reward", "补贴", "奖励"}

_VALID_RULE_TYPES = {"fixed_amount", "percentage_of_base", "tax_treatment_rate", "unsupported"}
_VALID_MODES = {"relative", "absolute"}


@dataclass
class PolicyRule:
    """由 REAL 121+ 记录（field_evidence）构建的最小确定性规则。

    D4：``rule_type`` 是**有效**类型（approved 优先，否则 derived），
    ``rule_type_source`` 显式说明来源，绝不把 derived 当作 approved/VERIFIED。
    """

    rule_id: str
    policy_id: int
    rule_type: str                       # fixed_amount | percentage_of_base | tax_treatment_rate
    formula: str
    inputs: List[str] = field(default_factory=list)   # 计算所需项目输入键
    conditions: List[dict] = field(default_factory=list)  # 结构化 eligibility 条件
    percentage: Optional[float] = None
    base: Optional[str] = None
    cap: Optional[float] = None
    floor: Optional[float] = None
    cap_mode: Optional[str] = None       # "relative" | "absolute" | None(未明确)
    floor_mode: Optional[str] = None     # "relative" | "absolute" | None(未明确)
    fixed_amount: Optional[float] = None  # 确定性解析出的固定金额（含证据）
    unit: Optional[str] = None
    currency: str = "CNY"
    granularity: Optional[str] = None        # 受益计量粒度（如 per_hired_person）
    evidence_refs: List[dict] = field(default_factory=list)
    rule_status: str = "active"
    calculation_supported: bool = True
    # ── D4（P4-5.1）：derived / approved / VERIFIED 分离（均为附加字段）──
    rule_type_derived: Optional[str] = None   # 确定性推导（READ-ONLY 分析）
    rule_type_approved: Optional[str] = None  # 仅经合法批准 provenance 的值
    rule_type_source: str = "derived"          # "approved" | "derived"
    human_approved: bool = False               # 该 rule_type 是否经人工批准
    approval_provenance_valid: bool = False    # 批准 provenance 是否被正确绑定


@dataclass
class CalculationResult:
    calculation_status: str             # "calculated" | "unable_to_calculate"
    calculated_amount: Optional[float] = None
    currency: str = "CNY"
    unit: Optional[str] = None
    formula_applied: Optional[str] = None
    input_values: Dict[str, Any] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)   # 必须为空（禁止推断）
    evidence_refs: List[dict] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    explanation: str = ""
    policy_outcome: Optional[dict] = None   # 非货币类政策结果（如适用税率）


@dataclass
class ConditionResult:
    condition_id: str
    label: str
    status: str                          # PASS | FAIL | UNKNOWN | N/A
    detail: str = ""
    quote: Optional[str] = None


@dataclass
class EligibilityResult:
    overall: str                         # PASS | FAIL | UNKNOWN | N/A
    conditions: List[ConditionResult] = field(default_factory=list)
    evidence_refs: List[dict] = field(default_factory=list)
    explanation: str = ""


def _detect_fixed_amount(record: Dict[str, Any],
                         fe: Dict[str, Any]) -> tuple:
    """确定性解析固定金额。

    仅当 amount（或 field_evidence.amount.value）为含 ``normalized_number`` 的结构化对象时
    才返回数值；字符串/None 一律返回 None（不猜测、不解析文本金额）。
    """
    amt = record.get("amount")
    if isinstance(amt, dict) and isinstance(amt.get("normalized_number"), (int, float)):
        return float(amt["normalized_number"]), amt
    ev = fe.get("amount")
    if isinstance(ev, dict):
        v = ev.get("value")
        if isinstance(v, dict) and isinstance(v.get("normalized_number"), (int, float)):
            return float(v["normalized_number"]), v
    return None, None


def _has_separation_keys(record: Dict[str, Any]) -> bool:
    """记录是否已采用 D4 分离语义（携带 derived/approved 分离字段）。

    对这类记录，裸 ``rule_type`` **不再**是被信任的输入（只有合法 approved 才算），
    避免「手改一个 rule_type 字段」即绕过 derived → approved 的治理链。
    """
    return any(k in record for k in
               ("rule_type_derived", "rule_type_approved", "rule_type_approval"))


def rule_type_approval_status(record: Dict[str, Any]) -> str:
    """rule_type 批准状态：``"valid"`` | ``"invalid"`` | ``"none"``（fail-closed）。

    - ``"none"``：记录未声称任何 rule_type 批准（正常：待人工批准）。
    - ``"invalid"``：记录**声称**已批准，但 provenance 不完整 / 与 Trust 事件不绑定 /
      自相矛盾 → 视为伪造，绝不采纳。
    - ``"valid"``：批准 provenance 完整且绑定到 Trust VERIFIED 事件。
    """
    approved = record.get("rule_type_approved")
    approval = record.get("rule_type_approval")
    if approved is None and approval is None:
        return "none"
    if not isinstance(approval, dict) or approval.get("approved") is not True:
        return "invalid"
    if approved not in _VALID_RULE_TYPES:
        return "invalid"
    if approval.get("approved_rule_type") != approved:
        return "invalid"
    if not approval.get("approved_by"):
        return "invalid"
    event_id = approval.get("approval_event_id")
    if not event_id or event_id != record.get("verified_event_id"):
        return "invalid"
    ev_id = approval.get("evidence_id")
    if not ev_id or ev_id != record.get("evidence_id"):
        return "invalid"
    ci = approval.get("content_identity")
    if not ci or (record.get("content_identity") and ci != record.get("content_identity")):
        return "invalid"
    return "valid"


def resolve_approved_rule_type(record: Dict[str, Any]) -> tuple:
    """返回 ``(approved_rule_type | None, status)``；approved 仅当 status == "valid"。"""
    status = rule_type_approval_status(record)
    if status == "valid":
        return record.get("rule_type_approved"), status
    return None, status


def _derive_rule_type(record: Dict[str, Any], fe: Dict[str, Any],
                      fixed_num: Optional[float]) -> str:
    """确定性推导 rule_type（derived；禁止 title 猜测；歧义 → fail-closed）。"""
    if not _has_separation_keys(record):
        explicit = record.get("rule_type")
        if explicit in _VALID_RULE_TYPES:
            return explicit

    ptype = record.get("type")
    percentage = record.get("percentage")
    base = record.get("base")

    if fixed_num is not None:
        # 同一记录同时存在「固定金额」与「比例+基数」→ 两个互相竞争的 rule context，
        # 无法确定单一 rule_type（须由人工批准裁定）→ fail-closed。
        if isinstance(percentage, (int, float)) and base is not None:
            return "unsupported"
        return "fixed_amount"

    if isinstance(percentage, (int, float)) and base is not None:
        if ptype == "tax_break":
            return "tax_treatment_rate"
        if ptype in _CASH_TYPES:
            return "percentage_of_base"
        # type 未明确给出现金/税率信号时，按「已知基数映射」判定：
        # 已知税基 → 税率优惠（非现金补贴）
        base_key = BASE_INPUT_MAP.get(base)
        if base_key in _BASE_TAX_INPUTS:
            return "tax_treatment_rate"
        # 已知非税基数 → 比例现金补贴（可计算）
        if base_key is not None:
            return "percentage_of_base"
        # 基数不在已知映射 → 无法确定 rule_type（不得猜测）→ unsupported
        return "unsupported"

    if isinstance(percentage, (int, float)) and base is None:
        # 有比例无基数：结构上存在，但计算所需基数缺失 → 调用方判 unable
        return "percentage_of_base"

    return "unsupported"


def _resolve_rule_type(record: Dict[str, Any], fe: Dict[str, Any],
                       fixed_num: Optional[float]) -> str:
    """**有效** rule_type：合法 approved 优先，否则确定性 derived（禁止 title 猜测）。

    D4：derived 绝不自动等于 approved；非法/伪造的批准标记一律不采纳（fail-closed）。
    """
    approved, _status = resolve_approved_rule_type(record)
    if approved is not None:
        return approved
    return _derive_rule_type(record, fe, fixed_num)


def build_rule_from_real_record(record: Dict[str, Any]) -> PolicyRule:
    """从 REAL 121+ 记录（field_evidence）构建 PolicyRule。

    仅读取已落库的、Evidence-bound 字段；不推断、不补全。
    """
    fe = record.get("field_evidence") or {}
    policy_id = record.get("id")
    percentage = record.get("percentage")
    base = record.get("base")
    cap = record.get("cap")
    floor = record.get("floor")
    cap_mode = record.get("cap_mode")
    floor_mode = record.get("floor_mode")
    unit = record.get("unit")
    currency = record.get("currency") or "CNY"
    title_blob = " ".join(str(record.get(k) or "") for k in
                          ("title", "description", "eligibility", "requirements"))

    evidence_refs = [v for v in fe.values() if isinstance(v, dict)]
    fixed_num, fixed_val = _detect_fixed_amount(record, fe)

    # ── D4：derived / approved / VERIFIED 三分（绝不混同）──
    # derived 仅用于 READ-ONLY 分析；approved 只在携带合法 Trust 绑定 provenance 时采纳。
    rule_type_derived = _derive_rule_type(record, fe, fixed_num)
    approved_type, approval_status = resolve_approved_rule_type(record)
    approval_provenance_valid = approval_status == "valid"
    rule_type = approved_type if approved_type is not None else rule_type_derived
    rule_type_source = "approved" if approved_type is not None else "derived"

    inputs: List[str] = []
    formula = ""
    if rule_type == "fixed_amount":
        formula = "calculated_amount = amount.normalized_number"
    elif rule_type == "tax_treatment_rate":
        formula = "applicable_tax_rate = percentage (not a cash subsidy)"
    elif rule_type == "percentage_of_base":
        base_key = BASE_INPUT_MAP.get(base)
        formula = (f"calculated_amount = project_input[{base_key}] * percentage"
                   if base_key else "calculated_amount = base_value * percentage")
        inputs = [base_key] if base_key else []
    else:  # unsupported
        formula = ""

    # 结构化固定金额优先取 value 中的 unit/currency（若有）
    if rule_type == "fixed_amount" and isinstance(fixed_val, dict):
        unit = unit or fixed_val.get("unit")
        currency = fixed_val.get("currency") or currency

    calculation_supported = rule_type != "unsupported" and not (
        rule_type == "percentage_of_base" and not inputs)

    return PolicyRule(
        rule_id=f"rule_{policy_id}",
        policy_id=policy_id,
        rule_type=rule_type,
        formula=formula,
        inputs=inputs,
        conditions=record.get("eligibility_conditions") or [],
        percentage=percentage,
        base=base,
        cap=cap,
        floor=floor,
        cap_mode=cap_mode,
        floor_mode=floor_mode,
        fixed_amount=fixed_num,
        unit=unit,
        currency=currency,
        granularity=record.get("granularity"),
        evidence_refs=evidence_refs,
        rule_status="active",
        calculation_supported=calculation_supported,
        rule_type_derived=rule_type_derived,
        rule_type_approved=approved_type,
        rule_type_source=rule_type_source,
        human_approved=approved_type is not None,
        approval_provenance_valid=approval_provenance_valid,
    )


def calculate_benefit(rule: PolicyRule,
                      project_inputs: Optional[Dict[str, Any]] = None,
                      eligibility_overall: Optional[str] = None
                      ) -> CalculationResult:
    """确定性 Benefit 计算。缺失必需输入 → unable_to_calculate。

    严格边界：
    - fixed_amount：政策定义固定金额补贴；仅当证据含 normalized_number 时确定性计算。
    - tax_treatment_rate：政策只定义适用税率，不是现金补贴。不计算「节省」
      （需推断基准税率，违反禁止项）。返回 policy_outcome = 适用税率。
    - percentage_of_base：需项目提供基数（inputs 中 key）；缺失或模式不明 → unable。
    """
    project_inputs = project_inputs or {}
    fe = rule.evidence_refs

    if rule.rule_type == "fixed_amount" and rule.fixed_amount is not None:
        # G3/P4-14：per_hired_person 必须 1500 × eligible_hired_persons（派生，非裸人数）
        if rule.granularity == "per_hired_person":
            if eligibility_overall != "PASS":
                return CalculationResult(
                    calculation_status="unable_to_calculate",
                    calculated_amount=None,
                    currency=rule.currency,
                    unit=rule.unit,
                    formula_applied=rule.formula,
                    input_values={},
                    assumptions=[],
                    evidence_refs=fe,
                    limitations=[f"eligibility={eligibility_overall}（非 PASS 或未提供）→ "
                                 "不计算 Benefit（fail-closed）"],
                    explanation="Eligibility 结果非 PASS，按治理不计算正向 Benefit。",
                )
            eligible, err = derive_eligible_hired_persons(rule, project_inputs)
            if eligible is None:
                return CalculationResult(
                    calculation_status="unable_to_calculate",
                    calculated_amount=None,
                    currency=rule.currency,
                    unit=rule.unit,
                    formula_applied=rule.formula,
                    input_values={},
                    assumptions=[],
                    evidence_refs=fe,
                    limitations=[err],
                    explanation=f"eligible_hired_persons 不可派生：{err}",
                )
            benefit = rule.fixed_amount * eligible
            return CalculationResult(
                calculation_status="calculated",
                calculated_amount=benefit,
                currency=rule.currency,
                unit=rule.unit,
                formula_applied=f"{rule.fixed_amount}(每人) × {eligible}(合格人数)",
                input_values={"eligible_hired_persons": eligible, "granularity": "per_hired_person"},
                assumptions=[],
                evidence_refs=fe,
                limitations=[],
                explanation=f"per-person 固定额度（元/人）× 合格招用人数（per-person 资格派生）："
                           f"{rule.fixed_amount} × {eligible} = {benefit}",
            )
        return CalculationResult(
            calculation_status="calculated",
            calculated_amount=rule.fixed_amount,
            currency=rule.currency,
            unit=rule.unit,
            formula_applied=rule.formula,
            input_values={},
            assumptions=[],
            evidence_refs=fe,
            limitations=[],
            explanation="政策定义固定金额补贴；按原文结构化金额（含 normalized_number 证据）确定性计算。",
        )

    if rule.rule_type == "tax_treatment_rate":
        # 政策为税率优惠（tax treatment），非现金补贴。
        return CalculationResult(
            calculation_status="unable_to_calculate",
            calculated_amount=None,
            currency=rule.currency,
            unit=rule.unit,
            formula_applied=None,
            input_values={},
            assumptions=[],
            evidence_refs=fe,
            limitations=[
                "本政策为税率优惠（tax treatment），非现金补贴；",
                "政策未给出比较基准税率，故不计算『节省』金额；",
                "未提供应纳税所得额时无法计算货币额。",
            ],
            explanation=(
                "根据公开政策文本，符合条件的企业适用企业所得税税率 "
                f"{rule.percentage:.0%}（计税依据：{rule.base}）。"
                "此为税收优惠待遇，不等同于政府现金补贴；最终以主管税务机关审核为准。"),
            policy_outcome={"applicable_tax_rate": rule.percentage,
                            "basis": rule.base},
        )

    if rule.rule_type == "percentage_of_base":
        if not rule.inputs:
            return CalculationResult(
                calculation_status="unable_to_calculate",
                calculated_amount=None,
                currency=rule.currency,
                unit=rule.unit,
                formula_applied=None,
                input_values={},
                assumptions=[],
                evidence_refs=fe,
                limitations=["计算基数未在政策原文中明确表达 → 无法计算。"],
                explanation="政策给出比例但未明确计算基数（base 缺失），"
                            "按治理不得语义推断基数 → unable_to_calculate。",
            )
        key = rule.inputs[0]
        if key not in project_inputs or project_inputs.get(key) is None:
            return CalculationResult(
                calculation_status="unable_to_calculate",
                calculated_amount=None,
                currency=rule.currency,
                unit=rule.unit,
                formula_applied=None,
                input_values={},
                assumptions=[],
                evidence_refs=fe,
                limitations=[f"项目未提供基数输入 '{key}' → 无法计算。"],
                explanation=f"缺少必需项目输入 '{key}'，按治理不得估算 → unable_to_calculate。",
            )
        base_value = float(project_inputs[key])
        amount = base_value * rule.percentage

        if rule.cap is not None:
            if rule.cap_mode == "relative":
                amount = min(amount, base_value * rule.cap)
            elif rule.cap_mode == "absolute":
                amount = min(amount, rule.cap)
            else:
                return CalculationResult(
                    calculation_status="unable_to_calculate",
                    calculated_amount=None,
                    currency=rule.currency,
                    unit=rule.unit,
                    formula_applied=None,
                    input_values={key: base_value},
                    assumptions=[],
                    evidence_refs=fe,
                    limitations=["cap 语义未明确（须为 relative/absolute），按治理不得猜测 → 无法计算。"],
                    explanation="cap 未声明 relative/absolute 模式，按治理不得推断 → unable_to_calculate。",
                )

        if rule.floor is not None:
            if rule.floor_mode == "relative":
                amount = max(amount, base_value * rule.floor)
            elif rule.floor_mode == "absolute":
                amount = max(amount, rule.floor)
            else:
                return CalculationResult(
                    calculation_status="unable_to_calculate",
                    calculated_amount=None,
                    currency=rule.currency,
                    unit=rule.unit,
                    formula_applied=None,
                    input_values={key: base_value},
                    assumptions=[],
                    evidence_refs=fe,
                    limitations=["floor 语义未明确（须为 relative/absolute），按治理不得猜测 → 无法计算。"],
                    explanation="floor 未声明 relative/absolute 模式，按治理不得推断 → unable_to_calculate。",
                )

        return CalculationResult(
            calculation_status="calculated",
            calculated_amount=round(amount, 2),
            currency=rule.currency,
            unit=rule.unit,
            formula_applied=rule.formula,
            input_values={key: base_value},
            assumptions=[],
            evidence_refs=fe,
            limitations=[],
            explanation=f"按政策比例 {rule.percentage:.0%} × 基数 {key}={base_value} 计算"
                       + (f"（上限 {rule.cap:.0%}）" if rule.cap is not None and rule.cap_mode == "relative"
                          else (f"（上限 {rule.cap}）" if rule.cap is not None else "")),
        )

    # unsupported
    return CalculationResult(
        calculation_status="unable_to_calculate",
        calculated_amount=None,
        currency=rule.currency,
        unit=rule.unit,
        formula_applied=None,
        input_values={},
        assumptions=[],
        evidence_refs=fe,
        limitations=["无明确 benefit rule（amount / percentage+base / tax rate）或 rule_type 无法确定。"],
        explanation="政策未提供可计算的受益规则（或 rule_type 无法确定）→ unable_to_calculate。",
    )


def _values_equal(a: Any, b: Any) -> bool:
    """G2: 引用型 / 分类条件的确定性相等比较（数值优先，其次归一化字符串）。

    - 两侧均可解析为数值 → 数值相等（容忍浮点误差，兼容 boolean True/1）。
    - 否则 → 归一化字符串相等（大小写、首尾空白不敏感）。
    治理纪律：仅做确定性相等判断，不做模糊 / 包含 / 推测匹配。
    """
    try:
        return abs(float(a) - float(b)) < 1e-9
    except (TypeError, ValueError):
        pass
    return str(a).strip().lower() == str(b).strip().lower()


def _eval_within_period(value: Any, rng: Dict[str, Any]) -> str:
    """日期区间判定（operator=within_period）：value∈[start,end]→PASS；否则 FAIL；不可解析→UNKNOWN。"""
    try:
        d = date.fromisoformat(str(value))
        start = date.fromisoformat(rng["start"])
        end = date.fromisoformat(rng["end"])
    except Exception:
        return "UNKNOWN"
    return "PASS" if start <= d <= end else "FAIL"


def _eval_condition_value(cond: Dict[str, Any], value: Any) -> str:
    """对单条件值做确定性判定，返回 PASS / FAIL / UNKNOWN。

    兼容：equals/==（_values_equal）、in（集合成员）、数值阈值 >=/<=/>/<、
    within_period（日期区间）。缺值 → UNKNOWN（≠ FAIL，绝不自动转 FAIL）。
    """
    op = cond.get("operator")
    expected = cond.get("expected_value", cond.get("threshold"))
    if value is None:
        return "UNKNOWN"
    if op == "in":
        exp = expected if isinstance(expected, (list, tuple, set)) else [expected]
        if isinstance(value, (list, tuple, set)):
            return "PASS" if any(v in exp for v in value) else "FAIL"
        return "PASS" if value in exp else "FAIL"
    if op in ("equals", "=="):
        return "PASS" if _values_equal(value, expected) else "FAIL"
    if op == "within_period":
        return _eval_within_period(value, expected)
    try:
        val_f = float(value)
        exp_f = float(expected)
    except (TypeError, ValueError):
        return "UNKNOWN"
    if op == ">=":
        ok = val_f >= exp_f
    elif op == "<=":
        ok = val_f <= exp_f
    elif op == ">":
        ok = val_f > exp_f
    elif op == "<":
        ok = val_f < exp_f
    else:
        return "UNKNOWN"
    return "PASS" if ok else "FAIL"


def derive_eligible_hired_persons(rule: "PolicyRule",
                                  project_inputs: Optional[Dict[str, Any]]
                                  ) -> "tuple":
    """由 per_person eligibility 条件 + hired_persons 明细派生合格招用人数。

    eligible_hired_persons 是**派生值**：逐人判定全部 per_person 条件 PASS 才计入；
    绝不直接采用聚合 hired_persons 总数或用户任意声明的 eligible_hired_persons。
    缺 hired_persons 明细 → (None, 原因)（fail-closed）。
    """
    facts = project_inputs or {}
    persons = facts.get("hired_persons")
    if persons is None:
        return None, "缺 hired_persons（per-person 明细）→ 无法派生合格人数"
    per_person = [c for c in rule.conditions if c.get("granularity") == "per_person"]
    if not per_person:
        return None, "eligibility_conditions 未含 per_person 条件 → 无法派生"
    eligible = 0
    for p in persons:
        if not isinstance(p, dict):
            continue
        ok = True
        for cond in per_person:
            if _eval_condition_value(cond, p.get(cond.get("source_field"))) != "PASS":
                ok = False
                break
        if ok:
            eligible += 1
    return eligible, None


def explain_per_person_eligibility(rule: "PolicyRule",
                                   project_inputs: Optional[Dict[str, Any]]
                                   ) -> Dict[str, Any]:
    """结构化逐人 eligibility 解释层（只读，复用现有确定性判定；不改任何现有逻辑）。

    仅使用已有结构化事实（``project_inputs["hired_persons"]`` 与 ``rule.conditions`` 中
    ``granularity == "per_person"`` 的条件），逐人判定每条件 PASS / FAIL / UNKNOWN。

    绝对不：
    - 根据聚合 eligible_count 反推逐人结果；
    - 根据用户 self-claimed eligible_count 制造逐人 PASS；
    - 让 LLM 决定 eligibility；
    - 猜测缺失事实（缺失 → UNKNOWN，绝不 FAIL）。

    本函数是**解释层**：不改变 ``check_eligibility`` / ``calculate_benefit`` / ``derive_…``
    的判定结果；其派生的逐人 PASS 数必须与 ``derive_eligible_hired_persons`` 的计数一致。
    """
    facts = project_inputs or {}
    persons = facts.get("hired_persons")
    per_person = [c for c in rule.conditions if c.get("granularity") == "per_person"]
    out: Dict[str, Any] = {
        "granularity": rule.granularity,
        "hired_count": None,
        "available": False,
        "persons": [],
        "note": "",
    }
    if persons is None:
        out["note"] = "project_inputs 不含 hired_persons 明细 → 无法提供逐人解释"
        return out
    out["hired_count"] = len(persons)
    if not per_person:
        out["note"] = "policy 未定义 per_person eligibility 条件 → 无逐人解释"
        out["available"] = True
        return out
    out["available"] = True
    for i, p in enumerate(persons):
        if not isinstance(p, dict):
            out["persons"].append({
                "person_index": i, "overall": "UNKNOWN",
                "conditions": [], "note": "非结构化人员记录",
            })
            continue
        cond_results = []
        for cond in per_person:
            sf = cond.get("source_field", cond.get("field"))
            val = p.get(sf)
            status = _eval_condition_value(cond, val)
            cond_results.append({
                "condition_id": cond.get("id", cond.get("condition_id", "cond")),
                "source_field": sf,
                "operator": cond.get("operator"),
                "expected": cond.get("expected_value", cond.get("threshold")),
                "value": val,
                "status": status,
            })
        if any(c["status"] == "FAIL" for c in cond_results):
            overall = "FAIL"
        elif all(c["status"] == "PASS" for c in cond_results):
            overall = "PASS"
        else:
            overall = "UNKNOWN"
        out["persons"].append({
            "person_index": i,
            "overall": overall,
            "conditions": cond_results,
        })
    return out


def check_eligibility(rule: PolicyRule,
                      project_profile: Optional[Dict[str, Any]] = None
                      ) -> EligibilityResult:
    """确定性 Eligibility Pre-check。

    每条件：项目事实缺失 → UNKNOWN；明确冲突 → FAIL；满足 → PASS。
    整体：全 PASS → PASS；存在 FAIL → FAIL；否则（含 UNKNOWN）→ UNKNOWN。

    条件表达兼容：
    - 数值阈值：operator ∈ {>=,<=,>,<,==} + threshold
    - G2 引用/分类：operator = equals + expected_value（boolean / 字符串 / 数值）
    """
    project_profile = project_profile or {}
    results: List[ConditionResult] = []
    for cond in rule.conditions:
        # G2/P4-14：per_person 条件由 derive_eligible_hired_persons 派生，不计入项目级 eligibility
        if cond.get("granularity") == "per_person":
            continue
        cid = cond.get("id", cond.get("condition_id", "cond"))
        label = cond.get("label", cid)
        quote = cond.get("quote")
        src = cond.get("source_field", cond.get("field"))
        op = cond.get("operator")
        expected = cond.get("expected_value", cond.get("threshold"))
        if src is None or op is None or expected is None:
            results.append(ConditionResult(cid, label, "N/A",
                                           "条件未结构化", quote))
            continue
        val = project_profile.get(src)
        status = _eval_condition_value(cond, val)
        if val is None:
            detail = f"项目未提供 '{src}'"
        elif status == "PASS":
            detail = f"项目 {src}={val!r} {op} {expected!r} → 满足"
        elif status == "FAIL":
            detail = f"项目 {src}={val!r} {op} {expected!r} → 冲突"
        else:
            detail = f"项目 {src}={val!r} 无法比较/未知"
        results.append(ConditionResult(cid, label, status, detail, quote))

    if not results:
        overall = "N/A"
        explanation = "政策未提供可结构化判定的 eligibility 条件。"
    elif any(r.status == "FAIL" for r in results):
        overall = "FAIL"
        explanation = "存在与政策条件明确冲突的项目事实 → 不符合。"
    elif all(r.status == "PASS" for r in results):
        overall = "PASS"
        explanation = "所有结构化条件均明确满足。"
    else:
        overall = "UNKNOWN"
        explanation = "存在缺失数据的条件（UNKNOWN）；不自动宣布符合。"

    return EligibilityResult(
        overall=overall,
        conditions=results,
        evidence_refs=rule.evidence_refs,
        explanation=explanation,
    )
