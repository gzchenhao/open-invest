"""P4-5.2 — Rule Context Split + Project Input Contract Audit（READ-ONLY）。

P4-5.1 已硬化「整篇政策 → 扁平 rule_type」的抽取层，但一条政策若同时承载多个互相竞争的
受益规则（人社部发〔2026〕39号：一次性扩岗补助 = 固定 1500 元/人；稳岗返还 = 比例 × 基数），
扁平 schema 只能 fail-closed 为 ``unsupported``。本模块提供显式 Rule Context 拆分，使每个
受益规则拥有独立、可证据追溯、可独立评估就绪度的上下文。本阶段**不修 parser/normalizer**，
只在既有 Evidence 之上做消费/审计：不补值、不猜测。

拆分机制（确定性，禁止语义推断）
1. ``segment_clauses``：仅按公文**结构性编号**（行首 ``一、`` ``二、``…）切分。
2. ``assign_to_clause``：字段 ``char_span`` **完整落在**某条款内才归属；否则排除
   （fail-closed，绝不硬塞、绝不跨条款借证据）。
3. 每个含受益信号的条款生成一个 Rule Context，``rule_type`` 只由该条款自身字段判定。
4. 政策级共享属性（``valid_period``）仅当条款原文显式使用「本通知」等整体指代时下发。

规则语义 ≠ 可执行性（本模块的核心修正）
- **规则语义** ``rule_type``：由条款内受益结构判定。比例 + 基数 + 显式受益谓词
  （返还/补助/补贴/…）→ ``percentage_of_base``。基数未进入 ``BASE_INPUT_MAP`` 时**不改写**
  语义，只记 ``base_input_mapping=None``。
- **可执行性**：由 ``contract_gaps`` / readiness 表达（降级、blocking）。

Project Input Contract 治理纪律
- 政策原文只能**要求**项目事实，永远不能**提供**其取值 → ``derivable_from_policy`` 恒 False。
- 政策自身给出的数值（「12 个月以上」「20%」「30 人（含）以下」）是条件参数，进入
  ``conditions[*].threshold``，**不是**项目输入。
- 契约中每个 key 必须携带非空 ``policy_requirement_quote``；缺失一律 MISSING → NOT_READY。
  禁止为了 ``calculation_supported=true`` 而虚构 key。
- ``granularity``：政策按**每个招用人员**设条件时为 ``per_hired_person``，而 ProjectProfile
  是企业级 → 契约根本性缺口，必须显式暴露。

信任边界：不 import src/trust、不写 real_policies.json、不产生 VERIFIED/approved；
record-local ``verified``/``approved`` 不构成证据；``rule_type_approval`` 非法 → 治理违规。
就绪度语义：``derived ≠ approved ≠ VERIFIED``。
"""

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from global_policy_aggregator.matching.project_profile import KNOWN_FIELDS
from global_policy_aggregator.pipeline.p4_rule_engine import (
    _BASE_TAX_INPUTS,
    BASE_INPUT_MAP,
    rule_type_approval_status,
)

SCHEMA_VERSION = "p4-5.2-rule-context-v1"

RD_READY, RD_PARTIAL, RD_NOT_READY = "READY", "PARTIAL", "NOT_READY"
INPUT_PRESENT, INPUT_MISSING = "PRESENT", "MISSING"

# ── 条文切分：仅行首结构性编号 ──
_CLAUSE_NUMERALS = "一二三四五六七八九十"
_TOP_CLAUSE_RE = re.compile(
    r"^[ \t\u3000]*([" + _CLAUSE_NUMERALS + r"]{1,3})[、.．][ \t\u3000]*", re.M)
_POLICY_SCOPE_TOKENS = ("本通知", "本意见", "本方案")

_BENEFIT_FIELDS = ("amount", "unit", "currency", "percentage", "base", "cap", "floor")

# 受益谓词：条款显式表达「受益如何产生」→ 用于规则**语义**判定（非可执行性）
_BENEFIT_PREDICATE_RE = re.compile(
    r"(返还|退还|补助|补贴|资助|奖励|贴息|减免|免征|减征|加计扣除|扣除)")

# 分档受益（企业规模）；分档必须分别建模，禁止用扁平 percentage/cap 表达
_VARIANT_SUBJECTS = ("大型企业", "中型企业", "小型企业", "微型企业",
                     "中小微企业", "中小型企业")
_VARIANT_RE = re.compile(
    r"(?P<subject>" + "|".join(_VARIANT_SUBJECTS) + r")"
    r"按(?:不超过|不高于|按照|按)?(?P<base>[^，。；、]{0,40}?)(?:的)?"
    r"(?P<pct>\d+(?:\.\d+)?)\s*[%％]\s*返还")
_COMPANY_SIZE_INPUT = "company_size"
_BASE_INPUT = "prior_year_ui_premium_paid"

# per-unit（按人次）计量：金额是单位额度，不是一次性总额
_PER_UNIT_RE = re.compile(
    r"(?P<object>每(?P<unit_subject>招用\s*\d+\s*人|人|户|名|个|台|辆))"
    r"(?P<capped>不超过|不高于)?(?P<amount>\d+(?:\.\d+)?)\s*元")
_PER_UNIT_UNIT = "元/人"

# 该类政策 eligibility 条件模式（仅本文原文明确表达时抽取；不注入其他法规条件）
# (id, label, source_field, operator, regex)
_NUMERIC_CONDITIONS = [
    ("ui_paid_months_min", "足额缴纳失业保险费满一定月数",
     "ui_paid_months", ">=", r"足额缴纳失业保险费\s*(?P<v>\d+)\s*个月以上"),
    ("layoff_rate_control_target_max", "裁员率不高于上年度全国城镇调查失业率控制目标",
     "layoff_rate", "<=", r"裁员率不高于上年度全国城镇调查失业率控制目标"),
    ("layoff_rate_carveout_max", "小规模参保企业裁员率上限（条件性）",
     "layoff_rate", "<=", r"裁员率不高于参保职工总数\s*(?P<v>\d+(?:\.\d+)?)\s*%"),
    ("employment_insurance_paid_months_min", "足额缴纳失业、工伤、职工养老保险费满一定月数",
     "employment_insurance_paid_months", ">=",
     r"足额缴纳\s*(?P<v>\d+)\s*个月以上失业、工伤、职工养老保险费"),
]
# 条件性前置：仅前置成立时才评估该条件
_CONDITION_PRECONDITIONS = [
    ("layoff_rate_carveout_max", "insured_employee_count", "<=", 30.0,
     r"(?P<v>\d+)\s*人（含）以下"),
]
# 引用型条件（operator=equals）
_REFERENCE_CONDITIONS = [
    ("labor_contract_signed", "已签订劳动合同", "labor_contract_signed", True,
     r"签订劳动合同"),
    ("applicant_entity_in_scope", "申请主体属企业和社会组织",
     "applicant_entity_type", "企业和社会组织", r"(?P<v>企业和社会组织)"),
    ("hired_target_group_in_scope", "招用对象属指定群体之一", "hired_target_group",
     ["毕业年度或离校两年内未就业高校毕业生", "16—24岁登记失业青年"],
     r"招用(?P<v>毕业年度及离校两年内未就业高校毕业生、16—24岁登记失业青年)"),
]

# 扁平 schema / 当前引擎不可表达性探测
_OR_DISJUNCTION_RE = re.compile(r"未裁员或|或裁员率|或者")

# 项目输入取值类型：(value_type, allowed_values, granularity)
_INPUT_TYPES: Dict[str, Tuple[str, Optional[List[str]], str]] = {
    "company_size": ("string_enum",
                     ["大型企业", "中型企业", "小型企业", "微型企业"], "project"),
    "prior_year_ui_premium_paid": ("number", None, "project"),
    "ui_paid_months": ("number", None, "project"),
    "layoff_rate": ("number", None, "project"),
    "insured_employee_count": ("number", None, "project"),
    "hired_person_count": ("number", None, "project"),
    "applicant_entity_type": ("string_enum", ["企业", "社会组织"], "project"),
    # 政策对「每个被招用人员」分别设条件 → 人员级；ProjectProfile 是企业级
    "hired_target_group": ("string_enum",
                           ["毕业年度或离校两年内未就业高校毕业生",
                            "16—24岁登记失业青年"], "per_hired_person"),
    "labor_contract_signed": ("boolean", None, "per_hired_person"),
    "employment_insurance_paid_months": ("number", None, "per_hired_person"),
}

GAP_UNSUPPORTED = "RULE_TYPE_UNSUPPORTED"
GAP_TIERED = "TIERED_PERCENTAGE_NOT_EXPRESSIBLE_IN_FLAT_SCHEMA"
GAP_PER_UNIT = "PER_UNIT_AMOUNT_NOT_EXPRESSIBLE_AS_TOTAL"
GAP_BASE_UNMAPPED = "BASE_NOT_IN_BASE_INPUT_MAP"
GAP_OR = "OR_DISJUNCTION_NOT_EXPRESSIBLE"
GAP_PRECONDITION = "CONDITION_PRECONDITION_NOT_EXPRESSIBLE"
GAP_EXTERNAL_THRESHOLD = "CONDITION_THRESHOLD_EXTERNAL_UNKNOWN"
GAP_PER_PERSON = "CONTRACT_GRANULARITY_PER_PERSON_VS_PROJECT_PROFILE"


# ── 数据类 ──────────────────────────────────────────────────────────────

@dataclass
class Clause:
    clause_id: str
    ordinal: int
    marker: str
    text: str
    char_span: Tuple[int, int]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["char_span"] = list(self.char_span)
        return d


@dataclass
class ContextField:
    """归属某 Rule Context 的字段 + 完整证据链。"""

    name: str
    value: Any
    quote: Optional[str] = None
    char_span: Optional[Tuple[int, int]] = None
    method: Optional[str] = None
    clause_id: Optional[str] = None
    snapshot_ref: Optional[str] = None
    content_identity: Optional[str] = None
    source_url: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["char_span"] = list(self.char_span) if self.char_span else None
        return d


@dataclass
class BenefitVariant:
    """条款内分档受益。分档必须各自绑定官方条款与项目取值；绝不默认取任一档。"""

    variant_id: str
    applies_when: Dict[str, Any]
    percentage: Optional[float] = None
    base: Optional[str] = None
    base_inherited_from: Optional[str] = None
    cap: Optional[float] = None
    cap_mode: Optional[str] = None
    quote: Optional[str] = None
    char_span: Optional[Tuple[int, int]] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["char_span"] = list(self.char_span) if self.char_span else None
        return d


@dataclass
class ProjectInputRequirement:
    """Project Input Contract 单项。绝不含默认值；``derivable_from_policy`` 恒 False。"""

    input_key: str
    purpose: str
    value_type: str
    allowed_values: Optional[List[str]]
    granularity: str
    policy_requirement_quote: str
    policy_requirement_span: Optional[Tuple[int, int]] = None
    declared_in_profile: bool = False
    profile_storage: str = "absent"
    derivable_from_policy: bool = False
    blocking: bool = True
    status: str = INPUT_MISSING
    supplied_value: Any = None

    def to_dict(self) -> dict:
        d = asdict(self)
        sp = self.policy_requirement_span
        d["policy_requirement_span"] = list(sp) if sp else None
        return d


@dataclass
class RuleContext:
    """一个可独立执行 / 独立评估的受益规则上下文。"""

    context_id: str
    policy_ref: str
    rule_type: str
    clause_id: str
    clause_ordinal: int
    clause_quote: str
    clause_char_span: Optional[Tuple[int, int]] = None

    amount: Optional[float] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    percentage: Optional[float] = None
    base: Optional[str] = None
    cap: Optional[float] = None
    cap_mode: Optional[str] = None
    floor: Optional[float] = None
    floor_mode: Optional[str] = None

    benefit_basis: Dict[str, Any] = field(default_factory=dict)
    benefit_variants: List[BenefitVariant] = field(default_factory=list)
    flat_schema_warning: Optional[str] = None
    # 分档规则下，扁平字段的**原始观测值**（仅留痕；不得用于计算，见 flat_schema_warning）
    flat_schema_observed: Dict[str, Any] = field(default_factory=dict)

    conditions: List[dict] = field(default_factory=list)
    shared_attributes: Dict[str, Any] = field(default_factory=dict)
    fields: Dict[str, ContextField] = field(default_factory=dict)
    required_inputs: List[ProjectInputRequirement] = field(default_factory=list)
    evidence_refs: List[dict] = field(default_factory=list)

    base_input_mapping: Optional[str] = None
    contract_gaps: List[str] = field(default_factory=list)

    rule_type_source: str = "derived"
    human_approved: bool = False
    governance_violations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        span = self.clause_char_span
        d["clause_char_span"] = list(span) if span else None
        d["fields"] = {k: v.to_dict() for k, v in self.fields.items()}
        d["benefit_variants"] = [v.to_dict() for v in self.benefit_variants]
        d["required_inputs"] = [i.to_dict() for i in self.required_inputs]
        return d


# ── 1. 条文切分 / 归属 ───────────────────────────────────────────────────

def segment_clauses(clean_text: str) -> List[Clause]:
    """按行首结构性编号切分条文；无标记 → 空列表（调用方 fail-closed）。"""
    if not clean_text:
        return []
    marks = [(m.start(), m.group(1)) for m in _TOP_CLAUSE_RE.finditer(clean_text)]
    if not marks:
        return []
    out: List[Clause] = []
    for i, (start, numeral) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(clean_text)
        text = clean_text[start:end].strip()
        if text:
            out.append(Clause(f"clause_{i + 1}", i + 1, f"{numeral}、", text, (start, end)))
    return out


def assign_to_clause(char_span: Optional[Tuple[int, int]],
                     clauses: List[Clause]) -> Optional[Clause]:
    """证据偏移必须**完整落在**某条款内，否则 None（fail-closed）。"""
    if not char_span or not clauses:
        return None
    start, end = char_span
    if start is None or end is None:
        return None
    for c in clauses:
        if c.char_span[0] <= start and end <= c.char_span[1]:
            return c
    return None


# ── 2. Evidence 归一化（兼容 FieldEvidence dataclass 与 dict）─────────────

def _ev_dict(entry: Any) -> Optional[dict]:
    if entry is None:
        return None
    if isinstance(entry, dict):
        return entry
    if hasattr(entry, "value") and hasattr(entry, "quote"):
        return {"value": entry.value, "quote": entry.quote,
                "char_span": getattr(entry, "char_span", None),
                "method": getattr(entry, "method", None),
                "snapshot_ref": getattr(entry, "snapshot_ref", None)}
    return None


def _evidence_map(record: Dict[str, Any]) -> Dict[str, dict]:
    """统一 evidence 容器（REAL: field_evidence；Candidate: extracted_fields_evidence）。"""
    raw = record.get("field_evidence") or record.get("extracted_fields_evidence") or {}
    out: Dict[str, dict] = {}
    for name, entry in raw.items():
        ev = _ev_dict(entry)
        if ev is not None:
            out[name] = ev
    return out


def _span(ev: dict) -> Optional[Tuple[int, int]]:
    s = ev.get("char_span")
    if isinstance(s, (list, tuple)) and len(s) == 2 and s[0] is not None:
        return (int(s[0]), int(s[1]))
    return None


# ── 3. 分档受益 / per-unit ───────────────────────────────────────────────

def _extract_variants(clause: Clause) -> List[BenefitVariant]:
    """确定性抽取条款内分档受益，逐档绑定原文。

    后续档省略基数（「中小微企业按不超过60%返还」）时继承**同条款**内前一档已显式写出的
    基数，并以 ``base_inherited_from`` 标记（同句省略，非语义推断）。
    """
    variants: List[BenefitVariant] = []
    prev_base: Optional[str] = None
    prev_id: Optional[str] = None
    rel = clause.char_span[0]
    for i, m in enumerate(_VARIANT_RE.finditer(clause.text), start=1):
        subject = m.group("subject")
        base = (m.group("base") or "").strip() or None
        inherited = None
        if base is None:
            base, inherited = prev_base, prev_id
        else:
            prev_base = base
        vid = f"variant_{i}_{subject}"
        prev_id = vid
        variants.append(BenefitVariant(
            variant_id=vid,
            applies_when={"source_field": _COMPANY_SIZE_INPUT, "equals": subject,
                          "quote": subject,
                          "char_span": [rel + m.start("subject"), rel + m.end("subject")]},
            percentage=float(m.group("pct")) / 100.0,
            base=base, base_inherited_from=inherited,
            cap=float(m.group("pct")) / 100.0,   # 「按不超过 N% 返还」→ N% 即上限
            cap_mode="relative",
            quote=m.group(0),
            char_span=(rel + m.start(), rel + m.end())))
    return variants


def _per_unit_info(clause: Clause, amount_value: Optional[float]) -> Optional[dict]:
    """判定条款内金额是否为 per-unit（「每招用1人不超过1500元」）。"""
    m = _PER_UNIT_RE.search(clause.text)
    if not m:
        return None
    rel = clause.char_span[0]
    return {"kind": "per_unit_rate", "rate": amount_value, "unit": _PER_UNIT_UNIT,
            "is_upper_bound": bool(m.group("capped")),
            "applicable_object": m.group("object").strip(),
            "quantity_input": "hired_person_count",
            "quote": m.group(0),
            "char_span": [rel + m.start(), rel + m.end()]}


# ── 4. 条件结构化 ────────────────────────────────────────────────────────

def _conditions_in_clause(clause: Clause) -> List[dict]:
    """确定性结构化条款内 eligibility 条件（无 → 空列表，不猜）。"""
    base = clause.char_span[0]
    out: List[dict] = []
    for cid, label, src, op, pat in _NUMERIC_CONDITIONS:
        m = re.search(pat, clause.text)
        if not m:
            continue
        threshold: Optional[float] = None
        if m.groupdict().get("v") is not None:
            try:
                raw = float(m.group("v"))
                threshold = raw / 100.0 if "%" in m.group(0) else raw
            except ValueError:
                threshold = None
        cond = {"id": cid, "label": label, "source_field": src, "operator": op,
                "threshold": threshold, "quote": m.group(0).strip(),
                "char_span": [base + m.start(), base + m.end()],
                "enforcement": "hard", "evaluable": threshold is not None}
        if threshold is None:
            # 原文引用**外部官方统计**（「上年度全国城镇调查失业率控制目标」）而未给数值
            # → 不得猜测；须取得该官方统计后才可评估。
            cond["threshold_source"] = "external_official_statistic_not_in_policy"
        out.append(cond)
    for cid, src, op, thr, pat in _CONDITION_PRECONDITIONS:
        m = re.search(pat, clause.text)
        if not m:
            continue
        for cond in out:
            if cond["id"] == cid:
                cond["precondition"] = {"source_field": src, "operator": op,
                                        "threshold": thr, "quote": m.group(0).strip(),
                                        "char_span": [base + m.start(), base + m.end()]}
                cond["enforcement"] = "conditional"
    for cid, label, src, expected, pat in _REFERENCE_CONDITIONS:
        m = re.search(pat, clause.text)
        if not m:
            continue
        out.append({"id": cid, "label": label, "source_field": src, "operator": "equals",
                    "expected_value": expected, "quote": m.group(0).strip(),
                    "char_span": [base + m.start(), base + m.end()],
                    "enforcement": "hard", "evaluable": True})
    seen, deduped = set(), []
    for c in out:
        if c["id"] not in seen:
            seen.add(c["id"])
            deduped.append(c)
    return deduped


# ── 5. Rule Context 生成 ─────────────────────────────────────────────────

def _derive_context_rule_type(clause: Clause, cfields: Dict[str, ContextField],
                              variants: List[BenefitVariant]) -> str:
    """条款**内**确定性判定 rule_type（绝不跨条款借字段）。

    语义与可执行性分离：基数未进 ``BASE_INPUT_MAP`` 时，只要条款显式表达受益谓词
    （「…30%返还」），语义仍是 ``percentage_of_base``；能否解析项目入力由
    ``base_input_mapping`` / readiness 表达。
    """
    amount = cfields.get("amount")
    pct = cfields.get("percentage")
    base = cfields.get("base")
    has_amount = amount is not None and amount.value is not None
    has_pct = pct is not None and pct.value is not None
    has_base = base is not None and base.value is not None
    if has_amount and not has_pct:
        return "fixed_amount"
    if has_pct and has_base:
        base_key = BASE_INPUT_MAP.get(base.value)
        if base_key in _BASE_TAX_INPUTS:
            return "tax_treatment_rate"
        if base_key is not None:
            return "percentage_of_base"
        return "percentage_of_base" if _BENEFIT_PREDICATE_RE.search(clause.text) \
            else "unsupported"
    if variants and has_base:
        return "percentage_of_base"
    return "unsupported"


def _detect_contract_gaps(clause: Clause, rule_type: str, variants: List[BenefitVariant],
                          base_input_mapping: Optional[str], conditions: List[dict],
                          per_unit: Optional[dict], reqs: List[ProjectInputRequirement]) -> List[str]:
    """探测当前扁平 schema / 引擎**无法表达**的契约缺口（只报，不改）。"""
    gaps: List[str] = []
    if rule_type == "unsupported":
        gaps.append(GAP_UNSUPPORTED)
    if len(variants) > 1:
        gaps.append(GAP_TIERED)
    if per_unit is not None:
        gaps.append(GAP_PER_UNIT)
    if rule_type == "percentage_of_base" and base_input_mapping is None:
        gaps.append(GAP_BASE_UNMAPPED)
    if _OR_DISJUNCTION_RE.search(clause.text):
        gaps.append(GAP_OR)
    if any(c.get("precondition") for c in conditions):
        gaps.append(GAP_PRECONDITION)
    if any(not c.get("evaluable", True) for c in conditions):
        gaps.append(GAP_EXTERNAL_THRESHOLD)
    if any(r.granularity == "per_hired_person" for r in reqs):
        gaps.append(GAP_PER_PERSON)
    return gaps


def _required_inputs_for(rule_type: str, conditions: List[dict],
                         cfields: Dict[str, ContextField],
                         variants: List[BenefitVariant], per_unit: Optional[dict],
                         clause: Clause) -> List[ProjectInputRequirement]:
    """构建 Project Input Contract（每项必须有原文依据；缺失 → MISSING）。"""
    reqs: List[ProjectInputRequirement] = []

    def add(key: str, purpose: str, quote: str,
            span: Optional[Tuple[int, int]], blocking: bool = True) -> None:
        vtype, allowed, granularity = _INPUT_TYPES.get(key, ("string", None, "project"))
        declared = key in KNOWN_FIELDS
        reqs.append(ProjectInputRequirement(
            input_key=key, purpose=purpose, value_type=vtype, allowed_values=allowed,
            granularity=granularity, policy_requirement_quote=quote,
            policy_requirement_span=span, declared_in_profile=declared,
            # 未在 KNOWN_FIELDS：ProjectProfile 仅能经 other_explicit_facts 承载（无类型/
            # 词表/校验）→ 记为 other_explicit_facts，绝不视为「已具备契约」。
            profile_storage="known_field" if declared else "other_explicit_facts",
            derivable_from_policy=False, blocking=blocking))

    if rule_type == "fixed_amount":
        if per_unit is not None:
            add(per_unit["quantity_input"], "benefit_quantity", per_unit["quote"],
                tuple(per_unit["char_span"]) if per_unit.get("char_span") else None)
        elif cfields.get("amount") is not None:
            ev = cfields["amount"]
            add("benefit_quantity", "benefit_quantity", ev.quote or clause.text,
                ev.char_span, blocking=False)
    if rule_type == "percentage_of_base":
        if variants:
            add(_COMPANY_SIZE_INPUT, "variant_selector",
                variants[0].quote or clause.text, variants[0].char_span)
        be = cfields.get("base")
        if be is not None and be.value:
            add(_BASE_INPUT, "benefit_base", be.quote or clause.text, be.char_span)
    for cond in conditions:
        src = cond.get("source_field")
        if not src:
            continue
        add(src, "eligibility", cond.get("quote") or clause.text,
            tuple(cond["char_span"]) if cond.get("char_span") else None)
        pre = cond.get("precondition")
        if pre and pre.get("source_field"):
            add(pre["source_field"], "eligibility", pre.get("quote") or clause.text,
                tuple(pre["char_span"]) if pre.get("char_span") else None)
    seen, deduped = set(), []
    for r in reqs:
        if r.input_key not in seen:
            seen.add(r.input_key)
            deduped.append(r)
    return deduped


def split_rule_contexts(record: Dict[str, Any], clean_text: Optional[str] = None,
                        policy_ref: Optional[str] = None) -> List[RuleContext]:
    """把「整篇政策」拆成独立 Rule Context（确定性、evidence-bound、fail-closed）。

    ``record``：携带 Evidence 的记录（REAL dict 或 Candidate ``to_dict()``）。
    ``clean_text``：与 ``char_span`` 同坐标系；省略时回退 ``record["clean_text"]``。
    返回**仅**含带受益信号条款的上下文；无可归属受益条款 → 空列表（调用方 fail-closed）。
    """
    clean_text = clean_text if clean_text is not None else (record.get("clean_text") or "")
    evidence = _evidence_map(record)
    clauses = segment_clauses(clean_text)
    if not clauses:
        return []
    policy = str(policy_ref or record.get("id") or record.get("candidate_id")
                 or record.get("content_identity") or "policy")

    violations: List[str] = []
    if rule_type_approval_status(record) == "invalid":
        violations.append(
            "rule_type_approval_invalid: 声称已人工批准，但批准 provenance 不完整 / 未绑定 "
            "Trust verified_event_id —— 该批准不得采纳")
    if record.get("verified") is True:
        violations.append("record_local_verified_flag: record-local verified=true 不构成证据"
                          "（VERIFIED 只能来自 Trust-owned provenance）")
    if record.get("approved") is True:
        violations.append("record_local_approved_flag: record-local approved=true 不构成证据")

    by_clause: Dict[str, Dict[str, ContextField]] = {c.clause_id: {} for c in clauses}
    unassigned: List[str] = []
    for name, ev in evidence.items():
        if ev.get("value") is None:
            continue
        clause = assign_to_clause(_span(ev), clauses)
        if clause is None:
            unassigned.append(name)
            continue
        by_clause[clause.clause_id][name] = ContextField(
            name=name, value=ev.get("value"), quote=ev.get("quote"), char_span=_span(ev),
            method=ev.get("method"), clause_id=clause.clause_id,
            snapshot_ref=ev.get("snapshot_ref") or record.get("snapshot_ref"),
            content_identity=record.get("content_identity"),
            source_url=record.get("source_url"))

    shared: Dict[str, Any] = {}
    for clause in clauses:
        if not any(tok in clause.text for tok in _POLICY_SCOPE_TOKENS):
            continue
        for name in ("valid_period", "region"):
            cf = by_clause[clause.clause_id].get(name)
            if cf is not None and name not in shared:
                shared[name] = {"value": cf.value, "quote": cf.quote,
                                "char_span": list(cf.char_span) if cf.char_span else None,
                                "clause_id": clause.clause_id,
                                "scope_basis": "policy_level_reference"}

    contexts: List[RuleContext] = []
    for clause in clauses:
        cfields = by_clause[clause.clause_id]
        if not any(n in cfields for n in _BENEFIT_FIELDS):
            continue
        variants = _extract_variants(clause)
        amount_cf = cfields.get("amount")
        amount_obj = amount_cf.value if amount_cf is not None else None
        amount_value = (amount_obj.get("normalized_number")
                        if isinstance(amount_obj, dict) else
                        (float(amount_obj) if isinstance(amount_obj, (int, float)) else None))
        per_unit = _per_unit_info(clause, amount_value)
        rule_type = _derive_context_rule_type(clause, cfields, variants)
        conditions = _conditions_in_clause(clause)

        base_cf = cfields.get("base")
        base_text = (base_cf.value if base_cf is not None and base_cf.value else
                     (variants[0].base if variants else None))
        base_input_mapping = BASE_INPUT_MAP.get(base_text) if base_text else None

        unit_cf, cur_cf = cfields.get("unit"), cfields.get("currency")
        cap_cf, floor_cf = cfields.get("cap"), cfields.get("floor")
        pct_cf = cfields.get("percentage")

        warnings: List[str] = []
        if len(variants) > 1:
            warnings.append(
                "TIERED_BENEFIT: 条款含 " + str(len(variants)) + " 档受益（按 "
                + _COMPANY_SIZE_INPUT + " 区分）；扁平 percentage/cap **无法**表达分档（会"
                "得到单一比例或把另一档误读为上限）→ 必须以 benefit_variants 建模，禁止用"
                "扁平字段计算。")
        if per_unit is not None:
            warnings.append(
                "PER_UNIT_BENEFIT: 金额为 per-unit 单位额度（" + per_unit["unit"]
                + "）；一次性总额需 " + per_unit["quantity_input"]
                + "，禁止把单位额度当总额。")

        ctx = RuleContext(
            context_id=f"ctx_{policy}_{clause.ordinal}_{rule_type}",
            policy_ref=policy, rule_type=rule_type, clause_id=clause.clause_id,
            clause_ordinal=clause.ordinal, clause_quote=clause.text,
            clause_char_span=clause.char_span,
            amount=amount_value,
            unit=(unit_cf.value if unit_cf is not None else
                  (per_unit["unit"] if per_unit else None)),
            currency=(cur_cf.value if cur_cf is not None else
                      (amount_obj.get("currency") if isinstance(amount_obj, dict) else None)),
            # 分档存在时，条款级 percentage 只是多档之一 → 不作为单一比例对外表达
            percentage=(None if len(variants) > 1 else
                        (pct_cf.value if pct_cf is not None else None)),
            base=base_text,
            # 分档规则：扁平 cap 不是「单一比例的上限」（它其实是另一档的比例）→ 不得外露
            # 为 cap，仅留痕于 flat_schema_observed（见 flat_schema_warning）。
            cap=(None if len(variants) > 1
                 else (cap_cf.value if cap_cf is not None else None)),
            cap_mode=(None if len(variants) > 1
                      else ("relative" if cap_cf is not None else None)),
            flat_schema_observed=(
                {"percentage": (pct_cf.value if pct_cf is not None else None),
                 "cap": (cap_cf.value if cap_cf is not None else None),
                 "note": "扁平 percentage/cap 对分档规则有损（另一档被读成上限）→ 仅供留痕，"
                         "禁止用于计算"}
                if len(variants) > 1 else {}),
            floor=(floor_cf.value if floor_cf is not None else None),
            benefit_basis={
                "kind": (per_unit["kind"] if per_unit else
                         ("fixed_total" if rule_type == "fixed_amount" else
                          ("rate_of_base" if rule_type in ("percentage_of_base",
                                                           "tax_treatment_rate")
                           else "unknown"))),
                "per_unit": per_unit, "variants_count": len(variants),
                "basis_evidence_bound": bool(per_unit or base_cf or amount_cf)},
            benefit_variants=variants,
            flat_schema_warning=(" ".join(warnings) or None),
            conditions=conditions, shared_attributes=dict(shared), fields=cfields,
            evidence_refs=[{"field": cf.name, "quote": cf.quote,
                            "char_span": list(cf.char_span) if cf.char_span else None,
                            "snapshot_ref": cf.snapshot_ref,
                            "content_identity": cf.content_identity,
                            "source_url": cf.source_url, "method": cf.method}
                           for cf in cfields.values()],
            base_input_mapping=base_input_mapping,
            rule_type_source="derived", human_approved=False,
            governance_violations=list(violations))
        ctx.required_inputs = _required_inputs_for(
            rule_type, conditions, cfields, variants, per_unit, clause)
        ctx.contract_gaps = _detect_contract_gaps(
            clause, rule_type, variants, base_input_mapping, conditions, per_unit,
            ctx.required_inputs)
        contexts.append(ctx)

    # 归属失败的字段（诊断用；不进入任何上下文，fail-closed）
    if unassigned:
        for ctx in contexts:
            ctx.benefit_basis["unassigned_fields"] = sorted(unassigned)
    return contexts


# ── 6. Project Input Contract 审计 ───────────────────────────────────────

def audit_project_input_contract(contexts: List[RuleContext],
                                 project_facts: Optional[Dict[str, Any]] = None) -> List[dict]:
    """逐上下文审计 Contract。缺失 → MISSING；政策不能提供项目事实取值。"""
    facts = project_facts or {}
    audit: List[dict] = []
    for ctx in contexts:
        rows = []
        for req in ctx.required_inputs:
            supplied = facts.get(req.input_key)
            req.supplied_value = supplied
            req.status = INPUT_MISSING if supplied is None else INPUT_PRESENT
            rows.append(req.to_dict())
        missing = [r["input_key"] for r in rows
                   if r["status"] == INPUT_MISSING and r["blocking"]]
        audit.append({
            "context_id": ctx.context_id, "rule_type": ctx.rule_type, "inputs": rows,
            "satisfied": [r["input_key"] for r in rows if r["status"] == INPUT_PRESENT],
            "missing": missing, "contract_complete": not missing,
            "derivable_from_policy": False,
            "note": ("政策只能*要求*项目事实，不能*提供*其取值；缺失一律 MISSING，禁止猜测、"
                     "禁止默认值。")})
    return audit


# ── 7. 就绪度（分级、fail-closed）────────────────────────────────────────

def _evidence_chain_complete(ctx: RuleContext, name: str) -> bool:
    """执行关键字段证据链：quote + char_span + snapshot_ref + content_identity +
    source_url 全部具备。"""
    cf = ctx.fields.get(name)
    if cf is None or cf.value is None:
        return False
    return all([cf.quote, cf.char_span, cf.snapshot_ref, cf.content_identity, cf.source_url])


def _rank(state: str) -> int:
    return {RD_READY: 2, RD_PARTIAL: 1, RD_NOT_READY: 0}.get(state, 0)


def _missing_input_keys(ctx: RuleContext, facts: Dict[str, Any],
                        purposes: Tuple[str, ...]) -> List[str]:
    return sorted({r.input_key for r in ctx.required_inputs
                   if r.purpose in purposes and r.blocking
                   and facts.get(r.input_key) is None})


def assess_context_readiness(ctx: RuleContext,
                             project_facts: Optional[Dict[str, Any]] = None,
                             record: Optional[Dict[str, Any]] = None,
                             trust_provenance_valid: bool = False) -> Dict[str, Any]:
    """对单个 Rule Context 做分级就绪度评估（READ-ONLY，fail-closed）。

    维度：benefit / eligibility / evidence / provenance / application / overall；
    另附两个正交归因层：policy_spec_completeness（条款与证据侧）、
    project_input_satisfiability（项目事实侧）。
    """
    record = record or {}
    facts = project_facts or {}
    reasons: List[str] = []
    blocking: List[str] = []

    # ---- evidence ----
    critical = [n for n in ("amount", "percentage", "base", "cap")
                if ctx.fields.get(n) is not None and ctx.fields[n].value is not None]
    # 分档 / per-unit 的受益数值不经扁平字段承载，必须各自校验其证据链
    bad = sorted(n for n in critical if not _evidence_chain_complete(ctx, n))
    if ctx.benefit_variants and not all(v.quote and v.char_span
                                        for v in ctx.benefit_variants):
        bad.append("benefit_variants")
    _pu = ctx.benefit_basis.get("per_unit") or {}
    if _pu and not (_pu.get("quote") and _pu.get("char_span")):
        bad.append("per_unit")
    if not critical and not ctx.benefit_variants and not _pu:
        evidence_state = RD_NOT_READY
        blocking.append("no_execution_critical_field_with_evidence")
        reasons.append("条款内无执行关键字段（amount/percentage/base/cap 及分档/per-unit "
                       "均无证据）")
    elif bad:
        evidence_state = RD_NOT_READY
        blocking.append("evidence_chain_incomplete:" + ",".join(sorted(set(bad))))
        reasons.append("执行关键字段证据链不完整（缺 quote/char_span/snapshot_ref/"
                       "content_identity/source_url）: " + ", ".join(sorted(set(bad))))
    else:
        evidence_state = RD_READY

    # ---- benefit ----
    if ctx.rule_type == "unsupported":
        reasons.append("rule_type = unsupported（条款内无法确定性判定受益结构）→ 不可计算")

    benefit_state = RD_NOT_READY
    if ctx.rule_type == "fixed_amount":
        qty_key = (ctx.benefit_basis.get("per_unit") or {}).get("quantity_input")
        if ctx.amount is None:
            reasons.append("fixed_amount 但金额无证据 → 不可计算")
        elif qty_key and facts.get(qty_key) is None:
            benefit_state = RD_PARTIAL
            reasons.append(
                f"per-unit 单位额度已知（{ctx.amount} {ctx.unit}），但一次性总额需项目提供"
                f" '{qty_key}' → 只报告单位额度，**不**计算总额（禁止把单位额度当总额）")
        else:
            benefit_state = RD_READY
    elif ctx.rule_type == "percentage_of_base":
        missing_benefit: List[str] = []
        if len(ctx.benefit_variants) > 1 and facts.get(_COMPANY_SIZE_INPUT) is None:
            missing_benefit.append(_COMPANY_SIZE_INPUT)
            reasons.append(
                "分档受益需项目提供 '" + _COMPANY_SIZE_INPUT + "' 才能选择档位（"
                + str(len(ctx.benefit_variants)) + " 档："
                + ", ".join(f"{v.applies_when['equals']}={v.percentage:.0%}"
                            for v in ctx.benefit_variants)
                + "）→ 禁止默认取任一档")
        if facts.get(_BASE_INPUT) is None:
            missing_benefit.append(_BASE_INPUT)
            reasons.append(f"受益基数为 '{ctx.base}'，需项目提供 '{_BASE_INPUT}' 的实际值 → "
                           "缺失（政策不能提供该取值）")
        if ctx.base_input_mapping is None and ctx.base:
            reasons.append(f"受益基数 '{ctx.base}' **未**进入 BASE_INPUT_MAP（引擎无法自动"
                           "解析该项目入力）→ 需契约扩展后才能执行")
        # 语义与可执行性分离：值本身可由项目提供（见 Contract），故不因映射缺失把
        # benefit 降为 NOT_READY；映射缺失以 contract_gap 形式 blocking。
        if missing_benefit or ctx.base_input_mapping is None:
            benefit_state = RD_PARTIAL
        else:
            benefit_state = RD_READY
    elif ctx.rule_type == "tax_treatment_rate":
        benefit_state = RD_READY

    # ---- eligibility ----
    if not ctx.conditions:
        eligibility_state = RD_NOT_READY
        reasons.append("资格条件未结构化（conditions 为空）→ 无法判定")
    else:
        cond_missing = sorted({c["source_field"] for c in ctx.conditions
                               if facts.get(c.get("source_field")) is None})
        unevaluable = sorted({c["id"] for c in ctx.conditions
                              if not c.get("evaluable", True)})
        if cond_missing:
            reasons.append("资格条件所需项目事实缺失: " + ", ".join(cond_missing))
        if unevaluable:
            reasons.append("条件缺可评估阈值（政策引用外部官方统计，原文未给数值）: "
                           + ", ".join(unevaluable))
            eligibility_state = RD_NOT_READY
        elif cond_missing:
            eligibility_state = RD_PARTIAL
        else:
            eligibility_state = RD_READY

    # ---- contract gaps → blocking（当前引擎/扁平 schema 不能表达）----
    for gap in ctx.contract_gaps:
        blocking.append("contract_gap:" + gap)
    for key in _missing_input_keys(ctx, facts, ("benefit_base", "benefit_quantity",
                                                "variant_selector", "eligibility")):
        blocking.append("missing_input:" + key)

    # ---- provenance（derived ≠ approved ≠ VERIFIED）----
    if rule_type_approval_status(record) == "invalid":
        blocking.append("invalid_rule_type_approval_provenance")
        reasons.append("rule_type 批准 provenance 非法 → 治理违规（fail-closed）")
    if trust_provenance_valid:
        provenance_state = RD_READY
    else:
        provenance_state = RD_NOT_READY
        blocking.append("no_trust_verified_provenance")
        reasons.append("无 Trust VERIFIED provenance（derived ≠ approved ≠ VERIFIED）")

    # ---- application ----
    if record.get("application_requirements"):
        application_state = RD_READY
    else:
        application_state = RD_NOT_READY
        blocking.append("application_requirements_absent")
        reasons.append("申报要求（application_requirements）缺失 → 不可执行")

    # ---- 归因层 ----
    if ctx.rule_type == "unsupported" or evidence_state == RD_NOT_READY:
        policy_spec = RD_NOT_READY
    elif ctx.contract_gaps:
        policy_spec = RD_PARTIAL
    else:
        policy_spec = RD_READY
    project_satisfied = ("UNSATISFIED" if _missing_input_keys(
        ctx, facts, ("benefit_base", "benefit_quantity", "variant_selector",
                     "eligibility")) else "SATISFIED")

    dims = (benefit_state, eligibility_state, evidence_state, provenance_state,
            application_state)
    # fail-closed：任一维度 NOT_READY 或任一 blocking → overall NOT_READY
    if blocking or RD_NOT_READY in dims:
        overall = RD_NOT_READY
    elif all(d == RD_READY for d in dims):
        overall = RD_READY
    else:
        overall = RD_PARTIAL

    return {"context_id": ctx.context_id, "rule_type": ctx.rule_type,
            "policy_spec_completeness": policy_spec,
            "project_input_satisfiability": project_satisfied,
            "benefit_readiness": benefit_state,
            "eligibility_readiness": eligibility_state,
            "evidence_completeness": evidence_state,
            "provenance_readiness": provenance_state,
            "application_readiness": application_state,
            "overall": overall,
            "blocking": sorted(set(blocking)),
            "reasons": reasons,
            "contract_gaps": list(ctx.contract_gaps),
            "derived_equals_verified": False,
            "approved_equals_verified": False,
            "human_approved": False,
            "governance_violations": list(ctx.governance_violations)}


def audit_policy_rule_contexts(record: Dict[str, Any], clean_text: Optional[str] = None,
                               project_facts: Optional[Dict[str, Any]] = None,
                               policy_ref: Optional[str] = None,
                               trust_provenance_valid: bool = False) -> Dict[str, Any]:
    """端到端只读审计：Rule Context 拆分 + Project Input Contract + 分级就绪度。"""
    clean_text = clean_text if clean_text is not None else (record.get("clean_text") or "")
    contexts = split_rule_contexts(record, clean_text, policy_ref=policy_ref)
    contracts = audit_project_input_contract(contexts, project_facts)
    readiness = [assess_context_readiness(ctx, project_facts, record=record,
                                          trust_provenance_valid=trust_provenance_valid)
                 for ctx in contexts]
    states = [r["overall"] for r in readiness]
    if states and all(s == RD_READY for s in states):
        overall = RD_READY
    elif states and all(s == RD_PARTIAL for s in states):
        overall = RD_PARTIAL
    else:
        overall = RD_NOT_READY
    return {"schema_version": SCHEMA_VERSION,
            "policy_ref": (contexts[0].policy_ref if contexts
                           else str(record.get("id") or record.get("candidate_id"))),
            "clause_count": len(segment_clauses(clean_text)),
            "context_count": len(contexts),
            "rule_types": [c.rule_type for c in contexts],
            "contexts": [c.to_dict() for c in contexts],
            "contracts": contracts,
            "readiness": readiness,
            "overall_readiness": overall,
            "flat_rule_type_insufficient": len(contexts) > 1,
            "governance_violations": sorted({v for c in contexts
                                             for v in c.governance_violations})}
