"""P6-3.3 — Context B（稳岗返还）Evidence Foundation（INTERNAL / DERIVED，非生产执行）。

本模块建立一个**只读、派生、内部**的 Context B 证据基础，为未来 Human Trust Verification
准备可追溯、fail-closed 的证据包。

设计边界（硬约束）：
* 复用 ``rule_context.ContextField`` 作为字段级证据链结构；
* 复用 ``rule_context.GAP_BASE_UNMAPPED`` 表达基数未映射；
* 证据锚定到 REAL 122 的**已验证 policy snapshot**（content_identity / snapshot_ref /
  source_url **直接取自 REAL 122 记录**），**绝不**使用 fixture 快照 ``de6780...``；
* 显式 ``trust_status = NOT_TRUST_COVERED``；**绝不**继承 Context A 的
  ``verified_event_id``（``fc50856...``）；
* **不**写 ``real_policies.json``、**不**创建 Trust Event、**不**修改 production execution；
* **不**实现 Context B 执行 / 计算 / stacking / aggregation / interaction；
* 全程 fail-closed：缺 quote / 缺快照 / 缺 content_identity / 缺 base 映射 / 外部依赖未解
  → 只能 ``UNKNOWN`` / ``UNVERIFIED`` / ``NOT_READY``，绝不 ``VERIFIED`` / ``READY`` /
  ``EXECUTABLE``。

Context B 语义（源自 P6-3.1 / P6-3.2，不重新猜测）：
    稳岗返还（一、）：rule_type = percentage_of_base
        大型企业  percentage = 0.30
        中小微企业 percentage = 0.60
        base      = 企业及其职工上年度实际缴纳失业保险费
        eligibility（3 项，project 粒度）：
            ui_paid_months_min(≥12) / layoff_rate_control_target_max /
            layoff_rate_carveout_max（前置：insured_employee_count ≤ 30）
        company_size 仅作 selector，其划型标准属 EXTERNAL_DEPENDENCY。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from global_policy_aggregator.pipeline.rule_context import (
    GAP_BASE_UNMAPPED,
    ContextField,
)

# ── 常量 ────────────────────────────────────────────────────────────────
CONTEXT_B_ID = "ctx_122_stabilization_subsidy"          # 稳定、内部使用的 Context B 身份
CONTEXT_B_RULE_TYPE = "percentage_of_base"
CONTEXT_B_BASE_REQUIRED_INPUT = "prior_year_ui_premium_paid"
COMPANY_SIZE_INPUT = "company_size"

TRUST_NOT_COVERED = "NOT_TRUST_COVERED"
EVIDENCE_DERIVED = "DERIVED"          # 已从官方文本派生（≠ VERIFIED，≠ READY）
EVIDENCE_UNKNOWN = "UNKNOWN"          # 缺 quote / 缺锚定 → fail-closed
EXEC_READINESS_NOT_READY = "NOT_READY"
EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"

# Context B BenefitVariant selector 单一来源（selector 与 evidence 共用）。
# 直接对齐 REAL 122「大型企业→30% / 中小微企业→60%」；严禁第三套表示。
CONTEXT_B_VARIANT_SPECS = [
    {
        "variant_id": "variant_large_enterprise",
        "source_field": COMPANY_SIZE_INPUT,
        "equals": "大型企业",
        "percentage": 0.30,
    },
    {
        "variant_id": "variant_sme",
        "source_field": COMPANY_SIZE_INPUT,
        "equals": "中小微企业",
        "percentage": 0.60,
    },
]

# Context A 的 Trust Event——本阶段**不得**继承到 B。
CONTEXT_A_VERIFIED_EVENT_ID = "fc50856de78547df8dc5d9f29b4b270d"

# Real 122 已验证快照身份（用于断言：派生证据必须锚定到此，而非 fixture 的 de6780...）。
REAL_122_VERIFIED_CONTENT_IDENTITY_PREFIX = "1e2d555"


# ── 从官方正文（REAL 122 description）抽取逐字段 quote ──
# 每个 tuple: (field_key, 候选 quote 子串)
# 说明：quote 取自 REAL 122 记录的 ``description``（完整官方正文）。
# 每条 ContextField 显式绑定 REAL 122 的 snapshot_ref / content_identity / source_url，
# 因此证据链锚定在**已验证 policy snapshot**，而非 fixture。
# 条款一内可直接定位的字段（取自 description 官方正文）。
# 注意：REAL 122 的 description 在「三、本通知自」处被截断，执行期文本不在其中；
# 执行期改由 policy 级 valid_period 元数据溯源（见 _build_execution_period_field）。
_FIELD_QUOTE_SPECS = [
    ("rule_type", "大型企业按不超过企业及其职工上年度实际缴纳失业保险费的30%返还，中小微企业按不超过60%返还"),
    ("percentage_large", "大型企业按不超过企业及其职工上年度实际缴纳失业保险费的30%返还"),
    ("percentage_sme", "中小微企业按不超过60%返还"),
    ("base", "企业及其职工上年度实际缴纳失业保险费"),
    ("elig_ui_paid_months", "参保企业足额缴纳失业保险费12个月以上"),
    ("elig_layoff_control", "上年度未裁员或裁员率不高于上年度全国城镇调查失业率控制目标"),
    ("elig_layoff_carveout", "30人（含）以下的参保企业裁员率不高于参保职工总数20%"),
    ("company_size_selector", "大型企业"),
]

# 执行期溯源：优先从 description 的「三、本通知自…执行」取原文；
# 否则（REAL 122 description 被截断）回退到 policy 级 valid_period 元数据。
_EXEC_PERIOD_DESC_QUOTE = "本通知自2026年1月1日至12月31日执行"


@dataclass
class ContextBEvidenceFoundation:
    """Context B 证据基础（内部派生，非生产执行契约）。"""

    policy_id: int
    context_id: str
    rule_type: str
    source_url: str
    snapshot_ref: str
    content_identity: str
    fields: Dict[str, ContextField]
    variants: List[Dict[str, Any]]
    base_required_input: str
    base_input_mapping: str                      # = GAP_BASE_UNMAPPED（fail-closed）
    company_size_external_dependency: bool
    company_size_definition: str                 # EXTERNAL_DEPENDENCY
    trust_status: str                           # = NOT_TRUST_COVERED
    verification_event_id: Optional[str]         # 显式 None；不得继承 fc50856...
    evidence_status: str                        # DERIVED / UNKNOWN
    execution_readiness: str                    # = NOT_READY（本阶段未授权执行）
    evidence_package: List[Dict[str, Any]]

    def to_dict(self) -> dict:
        d = asdict(self)
        # ContextField 已自带 to_dict（asdict 会展开）；此处仅确保 serializable。
        return d


def _locate(text: str, quote: str) -> Optional[List[int]]:
    idx = text.find(quote)
    if idx < 0:
        return None
    return [idx, idx + len(quote)]


def _build_execution_period_field(
        real_record: dict) -> ContextField:
    """执行期溯源：优先 description 原文；否则回退 valid_period 元数据。"""
    description = real_record.get("description") or ""
    source_url = real_record.get("source_url")
    snapshot_ref = real_record.get("snapshot_ref")
    content_identity = real_record.get("content_identity")
    span = _locate(description, _EXEC_PERIOD_DESC_QUOTE)
    if span is not None:
        return ContextField(
            name="execution_period", value=_EXEC_PERIOD_DESC_QUOTE,
            quote=_EXEC_PERIOD_DESC_QUOTE, char_span=tuple(span),
            method="derived_from_policy_text",
            clause_id="三、执行期",
            snapshot_ref=snapshot_ref, content_identity=content_identity,
            source_url=source_url,
        )
    # 回退：policy 级 valid_period（REAL 122 description 已截断，但有效）
    vp = real_record.get("valid_period")
    if vp:
        return ContextField(
            name="execution_period", value=vp, quote=str(vp),
            char_span=None,
            method="derived_from_policy_valid_period",
            clause_id="三、执行期",
            snapshot_ref=snapshot_ref, content_identity=content_identity,
            source_url=source_url,
        )
    # 两者皆缺 → fail-closed
    return ContextField(
        name="execution_period", value=None, quote=None, char_span=None,
        method="derived_from_policy_text_FAILED", clause_id="三、执行期",
        snapshot_ref=snapshot_ref, content_identity=content_identity,
        source_url=source_url,
    )


def build_context_b_evidence(real_record: dict) -> ContextBEvidenceFoundation:
    """从 REAL 122 记录（只读）构建 Context B 证据基础。

    不修改 real_record；仅读取 description / 出处 / 验证状态。
    """
    policy_id = real_record.get("id")
    description = real_record.get("description") or ""
    source_url = real_record.get("source_url")
    snapshot_ref = real_record.get("snapshot_ref")
    content_identity = real_record.get("content_identity")
    verified_event_id = real_record.get("verified_event_id")  # 仅用于显式 NOT 继承

    # 硬断言：证据必须锚定到 REAL 122 已验证快照（1e2d555...），
    # 绝不允许锚定到 fixture 快照（de6780...）。
    if content_identity is None or not content_identity.startswith(
            REAL_122_VERIFIED_CONTENT_IDENTITY_PREFIX):
        raise AssertionError(
            "Context B evidence must anchor to REAL 122 verified snapshot "
            f"(content_identity starts with {REAL_122_VERIFIED_CONTENT_IDENTITY_PREFIX!r}); "
            f"got {content_identity!r}")

    fields: Dict[str, ContextField] = {}
    missing_quote = False
    for key, quote in _FIELD_QUOTE_SPECS:
        span = _locate(description, quote)
        if span is None:
            missing_quote = True
            cf = ContextField(
                name=key, value=None, quote=None, char_span=None,
                method="derived_from_policy_text_FAILED",
                clause_id="一、稳岗返还",
                snapshot_ref=snapshot_ref, content_identity=content_identity,
                source_url=source_url,
            )
        else:
            cf = ContextField(
                name=key, value=quote, quote=quote, char_span=tuple(span),
                method="derived_from_policy_text",
                clause_id="一、稳岗返还",
                snapshot_ref=snapshot_ref, content_identity=content_identity,
                source_url=source_url,
            )
        fields[key] = cf

    # 执行期：独立溯源（可能回退 valid_period，char_span=None 属正常）
    exec_field = _build_execution_period_field(real_record)
    if exec_field.quote is None:
        missing_quote = True
    fields["execution_period"] = exec_field

    # 两个 percentage variant（各自独立 quote / locator / selector）。
    # 单一来源：由 CONTEXT_B_VARIANT_SPECS 派生，selector 与 evidence 共用同一 applies_when。
    variants = []
    for _spec in CONTEXT_B_VARIANT_SPECS:
        _is_large = _spec["variant_id"] == "variant_large_enterprise"
        _qf = "percentage_large" if _is_large else "percentage_sme"
        variants.append({
            "variant_id": _spec["variant_id"],
            "applies_when": {"source_field": _spec["source_field"],
                             "equals": _spec["equals"]},
            "percentage": _spec["percentage"],
            "quote": fields[_qf].quote,
            "char_span": list(fields[_qf].char_span)
            if fields[_qf].char_span else None,
            "base_inherited_from": None if _is_large else "variant_large_enterprise",
        })

    # base_input_mapping：确定性 fail-closed。
    # 规则需要项目输入 prior_year_ui_premium_paid；当前无任何 project input 契约
    # 唯一确定该基数（禁止用 payroll / revenue / tax / hired_persons 等替代）。
    base_input_mapping = GAP_BASE_UNMAPPED

    evidence_status = EVIDENCE_UNKNOWN if missing_quote else EVIDENCE_DERIVED

    foundation = ContextBEvidenceFoundation(
        policy_id=policy_id,
        context_id=CONTEXT_B_ID,
        rule_type=CONTEXT_B_RULE_TYPE,
        source_url=source_url,
        snapshot_ref=snapshot_ref,
        content_identity=content_identity,
        fields=fields,
        variants=variants,
        base_required_input=CONTEXT_B_BASE_REQUIRED_INPUT,
        base_input_mapping=base_input_mapping,
        company_size_external_dependency=True,
        company_size_definition=EXTERNAL_DEPENDENCY,
        trust_status=TRUST_NOT_COVERED,
        # 显式不继承 Context A 的 verification_event_id（fc50856...）。
        verification_event_id=None,
        evidence_status=evidence_status,
        execution_readiness=EXEC_READINESS_NOT_READY,
        evidence_package=_build_evidence_package(
            fields, variants, source_url, snapshot_ref, content_identity),
    )
    # 防御性不变量：任何情况下都不允许把 A 的 Trust Event 注入 B。
    assert foundation.verification_event_id != CONTEXT_A_VERIFIED_EVENT_ID
    return foundation


def _build_evidence_package(
        fields: Dict[str, ContextField],
        variants: List[Dict[str, Any]],
        source_url: str, snapshot_ref: str, content_identity: str,
) -> List[Dict[str, Any]]:
    """为未来 Human Reviewer 准备的可追溯证据包（10 项）。"""

    def _item(no: int, label: str, cf: Optional[ContextField],
              note: str = "") -> Dict[str, Any]:
        return {
            "item": no,
            "label": label,
            "quote": cf.quote if cf else None,
            "char_span": list(cf.char_span) if cf and cf.char_span else None,
            "source_url": source_url,
            "snapshot_ref": snapshot_ref,
            "content_identity": content_identity,
            "evidence_status": "DERIVED" if (cf and cf.quote) else "UNKNOWN",
            "note": note,
        }

    pkg = [
        _item(1, "Context B rule identity (一、稳岗返还 / 人社部发〔2026〕39号)",
              fields["rule_type"]),
        _item(2, "Large enterprise percentage = 0.30", fields["percentage_large"]),
        _item(3, "SME percentage = 0.60", fields["percentage_sme"]),
        _item(4, "Base = 企业及其职工上年度实际缴纳失业保险费", fields["base"]),
        _item(5, "Eligibility #1: ui_paid_months_min (≥12)",
              fields["elig_ui_paid_months"]),
        _item(6, "Eligibility #2: layoff_rate_control_target_max",
              fields["elig_layoff_control"]),
        _item(7, "Eligibility #3: layoff_rate_carveout_max (≤20%, 前置≤30人)",
              fields["elig_layoff_carveout"]),
        _item(8, "Execution period (2026-01-01~12-31)",
              fields["execution_period"]),
        {
            "item": 9,
            "label": "Company-size external dependency",
            "quote": None,
            "char_span": None,
            "source_url": source_url,
            "snapshot_ref": snapshot_ref,
            "content_identity": content_identity,
            "evidence_status": "EXTERNAL_DEPENDENCY",
            "note": ("'大型企业'/'中小微企业' 仅作 selector；划型标准依赖外部法规 "
                     "(工信部联企业〔2011〕300号 等)，政策文本未定义，禁止本阶段自行认定。"),
        },
        {
            "item": 10,
            "label": "Snapshot / content identity (anchored to REAL 122 verified snapshot)",
            "quote": None,
            "char_span": None,
            "source_url": source_url,
            "snapshot_ref": snapshot_ref,
            "content_identity": content_identity,
            "evidence_status": "ANCHORED",
            "note": ("content_identity 必须 == REAL 122 已验证快照（以 1e2d555 前缀标识）；"
                     "fixture 快照不得冒充 production verified snapshot。"),
        },
    ]
    return pkg


def load_real_122(real_json_path: str) -> dict:
    """只读加载 REAL 122 记录。"""
    with open(real_json_path, encoding="utf-8-sig") as f:
        data = json.load(f)
    for rec in data:
        if rec.get("id") == 122:
            return rec
    raise KeyError("REAL 122 not found")


# ── Deterministic BenefitVariant selector（仅选择，不计算金额）────────────
# 复用 CONTEXT_B_VARIANT_SPECS 作为唯一来源；与 build_context_b_evidence 完全一致。
_MISSING_VALUE_SENTINELS = frozenset({
    "unknown", "unk", "unspecified", "n/a", "na", "none", "null", "",
    "未知", "不详", "待定", "未明确", "未提供",
})


def _variant_selection(status: str, variant, percentage, matched, reason: str) -> Dict[str, Any]:
    return {
        "status": status,                  # SELECTED | UNKNOWN | CONFLICT
        "selected_variant": variant,       # variant_id | None
        "percentage": percentage,          # 0.30 | 0.60 | None（仅为选择器元数据，非金额计算）
        "source_field": COMPANY_SIZE_INPUT,
        "matched_equals": matched,         # 大型企业 | 中小微企业 | None
        "reason": reason,
    }


def select_context_b_variant(company_size_value) -> Dict[str, Any]:
    """根据 Project Input ``company_size`` 确定性选择 Context B BenefitVariant。

    职责边界（硬约束）：
    * 只做 exact equality 匹配（selector = 选择 ONLY）；
    * 不做企业划型 / LLM 推理 / 法规解释 / 人数·营收·工资推断；
    * 不做 base × percentage 金额计算（MONETARY_BENEFIT_CALCULATION = NOT_IMPLEMENTED）。

    Returns:
        _variant_selection(...) 形态字典：status / selected_variant / percentage /
        source_field / matched_equals / reason。
    """
    src = COMPANY_SIZE_INPUT

    # 标量 None / 空 / 缺失哨兵 → UNKNOWN
    if company_size_value is None:
        return _variant_selection("UNKNOWN", None, None, None,
                                   "company_size is None/missing")
    if isinstance(company_size_value, str):
        v = company_size_value.strip()
        if v == "" or v.lower() in _MISSING_VALUE_SENTINELS:
            return _variant_selection("UNKNOWN", None, None, None,
                                       "company_size missing/unknown sentinel")
        for spec in CONTEXT_B_VARIANT_SPECS:
            if v == spec["equals"]:
                return _variant_selection(
                    "SELECTED", spec["variant_id"], spec["percentage"],
                    spec["equals"], "exact equality match on company_size")
        # 非 canonical（如 超大型企业 / 中型企业）→ 不支持，UNKNOWN（绝不默认归入任一档）
        return _variant_selection(
            "UNKNOWN", None, None, None,
            f"company_size={v!r} not in canonical set; unsupported → UNKNOWN")

    # 集合/多值（list/tuple/set）→ 检测 conflict
    if isinstance(company_size_value, (list, tuple, set)):
        matched_ids = set()
        for item in company_size_value:
            if item is None:
                continue
            s = item.strip() if isinstance(item, str) else item
            if s == "" or (isinstance(s, str) and s.lower() in _MISSING_VALUE_SENTINELS):
                continue
            for spec in CONTEXT_B_VARIANT_SPECS:
                if s == spec["equals"]:
                    matched_ids.add(spec["variant_id"])
        if len(matched_ids) > 1:
            return _variant_selection(
                "CONFLICT", None, None, None,
                "contradictory company_size values in project input")
        if len(matched_ids) == 1:
            spec = next(s for s in CONTEXT_B_VARIANT_SPECS
                        if s["variant_id"] in matched_ids)
            return _variant_selection(
                "SELECTED", spec["variant_id"], spec["percentage"],
                spec["equals"], "exact equality match on company_size")
        return _variant_selection("UNKNOWN", None, None, None,
                                   "no canonical company_size in collection")

    # 其他类型（int / float 等）→ 不支持
    return _variant_selection(
        "UNKNOWN", None, None, None,
        f"company_size type {type(company_size_value).__name__} unsupported")
