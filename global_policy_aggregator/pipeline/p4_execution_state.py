"""P4-3 Execution-readiness assessor (READ-ONLY).

Governance boundary (JUDGE P4-3 + P4-3.1):
- 本模块是**纯函数 / 只读校验器**：判断一条 Policy 是否满足 Execution Contract。
- 不修改任何 schema、不写 REAL production data、不写 src.trust、不调用 Human
  Verification、不产生 VERIFIED。
- 本模块**不引入 src.trust 包**；Trust 验证通过调用方注入的 ``trust_service``
  （只读，仅调用其 ``check_verified_validity``）完成。

P4-3.1 Trust Verification Binding（修复 field_evidence[*].verified 旁路）：
- 执行关键字段（eligibility_conditions / percentage / amount / base / cap / floor）
  必须带有 **Trust-owned VERIFIED provenance** 方可视为已验证。
- 普通 record-local 的 ``field_evidence[field].verified`` **不再是** 验证门控：
  对于生产记录（``is_mock`` 非 True），该标记被忽略；验证只能来自 Trust。
- 仅 ``is_mock is True`` 的测试 fixture 允许沿用旧的 record-local ``verified``
  标记（测试用途，绝非生产旁路；真实 REAL 记录 is_mock 均非 True）。
- 当注入 ``trust_service`` 时，验证依赖其 ``check_verified_validity(evidence_id)``：
    * 必须 is_valid（human 'verified' 事件存在、无后续 revoke、content_identity
      与当前 evidence 一致、非 MOCK、且 authority registry 已绑定）；
    * 且 record 的 ``verified_event_id`` 必须等于当前有效 verified 事件的 event_id
      （防止“有 verified_event_id 即视为全部已验证”及 stale/revoked 冒用）。

Trust 语义（锁死）：
- ``EXECUTION_READY`` 必须建立在 VERIFIED provenance 之上。
- 但 ``VERIFIED != EXECUTION_READY``：VERIFIED policy 仍可 NOT_READY（如尚未抽取
  结构化 eligibility_conditions）；EXECUTION_READY 必须已经具备 VERIFIED provenance。
- 无法获得 Trust VERIFIED provenance 时（trust_service 为 None 且非 mock fixture），
  fail-closed 为 NOT_READY，绝不假设 VERIFIED。

D4（P4-5.1）derived / approved / VERIFIED 三分：
- ``rule_type`` 为**确定性 derived** 时，绝不代表人工批准，更不代表 Trust VERIFIED；
  因此「derived rule_type 存在」**永远不会**使记录成为 EXECUTION_READY。
- 记录若**自称** rule_type 已批准但批准 provenance 不完整/未绑定 Trust
  ``verified_event_id``（伪造或自相矛盾）→ 治理违规 → 强制 NOT_READY（fail-closed）。
- 只有携带合法批准 provenance 的 rule_type 才在 ``rule_type_status`` 中标记为
  ``source="approved"``；即便如此，也仍需 Trust VERIFIED provenance 才能 EXECUTION_READY。
"""

from typing import Any, Dict, List, Optional

from global_policy_aggregator.pipeline.p4_rule_engine import rule_type_approval_status

# 状态枚举
STATE_NOT_READY = "NOT_READY"
STATE_PARTIAL = "PARTIAL"
STATE_EXECUTION_READY = "EXECUTION_READY"
# G5 (P4-17): Application Readiness 独立状态（与 Overall Execution Readiness 解耦）
STATE_READY = "READY"

# 强制 REQUIRED（存在性）
_REQUIRED_PRESENCE = (
    "id",                # policy identity
    "content_identity",
    "source_url",
    "snapshot_ref",
    "field_evidence",
    "rule_type",
    "application_requirements",
)
# Match 维度：至少其一非 null
_MATCH_DIMENSIONS = ("industry", "region", "type")

# G5 (P4-17): Application-only 存在性字段。
# 这些字段缺失只表示「Application Readiness 未就绪」（申请渠道/材料未抽取），
# **不**应阻断 Eligibility / Benefit 的执行（P4-11：C 类 procedural channel 不阻断执行）。
# 它们保留在 ``missing_required`` 中以维持 Overall Execution Readiness = NOT_READY，
# 但被排除在「执行阻断」口径之外。
_APPLICATION_ONLY_PRESENCE = frozenset({"application_requirements"})

# 执行关键字段（须存在且须有已验证 provenance）
_EXECUTION_CRITICAL = ("eligibility_conditions", "percentage", "amount", "base")

_VALID_MODES = ("relative", "absolute")

# ---- G5 (P4-4): OPTIONAL 字段三态语义（PRESENT / MISSING / NOT_APPLICABLE）----
# 治理纪律（JUDGE D2）：
# - 只有能被 *确定性规则* 证明「对该 rule_type 不适用」的 OPTIONAL 字段才可为
#   NOT_APPLICABLE；绝不因为「当前没有数据」而自动标记 N/A。
# - OPTIONAL 缺失（MISSING）仍旧阻止 EXECUTION_READY（状态封顶 PARTIAL）。
OPTIONAL_PRESENT = "PRESENT"
OPTIONAL_MISSING = "MISSING"
OPTIONAL_NOT_APPLICABLE = "NOT_APPLICABLE"

OPTIONAL_FIELDS = ("region", "valid_period", "unit", "currency")

# 确定性 NOT_APPLICABLE 规则表：rule_type -> 明确不使用的 OPTIONAL 字段集合。
# tax_treatment_rate = 税率待遇（非现金补贴）：不存在货币金额 → 不需要币种 / 计量单位。
# 纪律：region 与 valid_period 始终「相关」——除非有官方 scope / 时效证据，
#       否则一律保持 MISSING（不得猜测「全国适用」或「永久有效」）。
_NOT_APPLICABLE_OPTIONAL = {
    "tax_treatment_rate": frozenset({"currency", "unit"}),
}


def _optional_status(record: Dict[str, Any], field: str) -> str:
    """OPTIONAL 字段三态判定（确定性，fail-closed）。

    PRESENT        : 有明确非空值（含 valid_period 单端起算 {"start":…, "end":None}）。
    NOT_APPLICABLE : 由 rule_type 的确定性语义证明该字段不适用。
    MISSING        : 其余（无数据 / 未知）—— 仍旧阻止 EXECUTION_READY。
    """
    if not _is_empty(record.get(field)):
        return OPTIONAL_PRESENT
    na_fields = _NOT_APPLICABLE_OPTIONAL.get(record.get("rule_type")) or frozenset()
    if field in na_fields:
        return OPTIONAL_NOT_APPLICABLE
    return OPTIONAL_MISSING


def _is_empty(v: Any) -> bool:
    """空值判定（[] / 0 不算空；仅 None / '' / 空 dict 算空）。"""
    return v is None or v == "" or (isinstance(v, dict) and len(v) == 0)


def _fe_entry(record: Dict[str, Any], field: str) -> Optional[Dict[str, Any]]:
    fe = record.get("field_evidence") or {}
    entry = fe.get(field)
    return entry if isinstance(entry, dict) else None


def _evidence_complete(entry: Dict[str, Any]) -> bool:
    """Evidence 链是否完整（可追溯到 quote/snapshot/content_identity/source_url）。"""
    return bool(entry.get("content_identity")) and bool(entry.get("source_url")) \
        and bool(entry.get("snapshot_ref"))


def _is_verified(entry: Dict[str, Any]) -> bool:
    """（仅测试 fixture 沿用）record-local verified 标记。生产记录忽略此标记。"""
    return entry.get("verified") is True


def _resolve_trust_identity(
    record: Dict[str, Any],
    context_key: Optional[str],
) -> "tuple[str, str]":
    """解析用于 Trust provenance 校验的 ``(evidence_id, verified_event_id)``。

    per-context binding 优先：当 ``context_key`` 为有效 key 且
    ``trust_bindings[context_key]`` 含完整 binding 时，使用该 binding（P6-3.18：
    Context A / B 各自独立 evidence）；否则回退到顶层 legacy ``evidence_id`` /
    ``verified_event_id``（无 trust_bindings 的旧政策保持既有行为，避免无关政策
    regression）。

    不允许跨 context 继承：本函数只读取“请求 context”的 binding 或顶层 legacy，
    绝不把 Context B binding 当作 Context A 使用。
    """
    tb = record.get("trust_bindings") or {}
    if context_key and isinstance(tb.get(context_key), dict):
        b = tb[context_key]
        ev = b.get("evidence_id")
        ve = b.get("verified_event_id")
        if ev and ve:
            return ev, ve
    return record.get("evidence_id"), record.get("verified_event_id")


def _trust_provenance_valid(
    record: Dict[str, Any],
    trust_service: Any,
    context_key: Optional[str] = None,
) -> bool:
    """Trust-owned VERIFIED provenance 绑定（fail-closed）。

    绑定规则：
    - trust_service 必须注入（调用方提供真实 Trust 服务；本模块不引入 src.trust）。
    - 通过 ``_resolve_trust_identity`` 解析 ``(evidence_id, verified_event_id)``：
      优先 per-context binding（``trust_bindings[context_key]``），否则顶层 legacy
      字段（P3-7 绑定）。
    - trust_service.check_verified_validity(evidence_id) 必须 is_valid（覆盖：
      human 'verified' 事件存在、无后续 revoke、content_identity 与当前 evidence
      一致、非 MOCK、authority registry 已绑定）。
    - 解析出的 verified_event_id 必须等于当前有效 verified 事件的 event_id
      （防止“有 verified_event_id 即视为全部已验证”及 stale/revoked 冒用）。
    """
    if trust_service is None:
        return False
    evidence_id, claimed_event_id = _resolve_trust_identity(record, context_key)
    if not evidence_id or not claimed_event_id:
        return False
    # per-context binding 隔离保证（Case G）：被绑定 evidence 的 metadata.context_id
    # 必须与请求的 context_key 一致；否则视为非法 cross-context binding，直接 fail-closed。
    # legacy 回退（context_key 为 None / 顶层 binding）不触发此检查。
    if context_key:
        try:
            ev_obj = trust_service.get_evidence(evidence_id)
            if ev_obj.get("success"):
                ctx = (ev_obj.get("evidence") or {}).get("metadata", {}).get("context_id")
                if ctx and ctx != context_key:
                    return False
        except Exception:
            pass
    try:
        res = trust_service.check_verified_validity(evidence_id)
    except Exception:
        return False
    if not res.get("is_valid"):
        return False
    latest = res.get("latest_verified_event") or {}
    if not latest.get("event_id"):
        return False
    if latest.get("event_id") != claimed_event_id:
        return False
    return True


def _field_verified(
    record: Dict[str, Any],
    field: str,
    trust_service: Any,
    context_key: Optional[str] = None,
) -> bool:
    """执行关键字段是否可视为已验证。

    - 注入 trust_service：仅当整条 record 的 Trust VERIFIED provenance 有效时成立；
      provenance 按 ``context_key`` 解析（per-context binding 优先，否则顶层 legacy）。
    - 未注入 trust_service：生产记录 fail-closed（False）；仅 is_mock fixture 沿用
      record-local ``verified`` 标记（测试用途，非生产旁路）。
    - 字段必须有完整可追溯的 field_evidence 方可验证。
    """
    entry = _fe_entry(record, field)
    if entry is None or not _evidence_complete(entry):
        return False
    if trust_service is not None:
        return _trust_provenance_valid(record, trust_service, context_key=context_key)
    if record.get("is_mock") is True:
        return _is_verified(entry)
    return False


def _critical_applies(record: Dict[str, Any], field: str) -> bool:
    """该执行关键字段是否适用于当前 rule_type（避免把不适用字段当作缺失）。"""
    rt = record.get("rule_type")
    if field == "percentage":
        return rt in ("percentage_of_base", "tax_treatment_rate")
    if field == "amount":
        return rt == "fixed_amount"
    if field == "base":
        return rt in ("percentage_of_base", "tax_treatment_rate")
    return True  # eligibility_conditions 始终适用


def assess_execution_readiness(
    record: Dict[str, Any],
    trust_service: Optional[Any] = None,
    context_key: Optional[str] = None,
) -> Dict[str, Any]:
    """只读评估一条 Policy 的 Execution 就绪状态。

    Args:
        record: Policy 记录（不修改）。
        trust_service: 可选注入的 Trust 服务（只读），用于核实 VERIFIED provenance。
            生产环境应注入真实 TrustEvidenceService；不注入时生产记录 fail-closed。
        context_key: 可选 per-context binding key（如 ``"context_a"`` /
            ``"ctx_122_stabilization_subsidy"``）。提供时，Trust provenance 优先
            读取 ``trust_bindings[context_key]``；否则回退顶层 legacy 字段。
            ``None`` 时保持 P6-3.18 前的 legacy 行为（顶层 evidence_id/verified_event_id）。

    Returns:
        {
          "state": NOT_READY | PARTIAL | EXECUTION_READY,
          "missing_required": [...],
          "missing_optional": [...],            # 仅真正 MISSING 的 OPTIONAL 字段
          "not_applicable_optional": [...],     # G5: 经确定性规则证明不适用的 OPTIONAL
          "optional_status": {field: PRESENT|MISSING|NOT_APPLICABLE},  # G5
          "unverified_critical_fields": [...],
          "evidence_gaps": [...],
          "governance_violations": [...],       # D4: 伪造/矛盾批准标记（非空 → NOT_READY）
          "rule_type_status": {...},            # D4: derived / approved / 非 VERIFIED 分离
          "reasons": [...],
        }

    G5 (P4-4) OPTIONAL 三态：
        EXECUTION_READY 要求所有 OPTIONAL 要么 PRESENT、要么被确定性证明 NOT_APPLICABLE；
        普通 missing/null **不会**被自动当作 NOT_APPLICABLE（仍封顶 PARTIAL）。
    """
    missing_required: List[str] = []
    missing_optional: List[str] = []
    unverified_critical_fields: List[str] = []
    evidence_gaps: List[str] = []
    reasons: List[str] = []
    optional_status: Dict[str, str] = {}
    not_applicable_optional: List[str] = []
    governance_violations: List[str] = []

    rt = record.get("rule_type")

    # ---- 0. D4: derived / approved / VERIFIED 三分治理门 ----
    approval_status = rule_type_approval_status(record)
    if approval_status == "invalid":
        governance_violations.append(
            "rule_type_approval_invalid: 记录声称 rule_type 已人工批准，但批准 provenance "
            "不完整 / 未绑定 Trust verified_event_id / 自相矛盾 —— 该批准不得采纳")
    rule_type_status = {
        "effective": rt,
        "derived": record.get("rule_type_derived"),
        # 仅当批准 provenance 合法时才回显 approved（否则一律 None）
        "approved": (record.get("rule_type_approved")
                     if approval_status == "valid" else None),
        "source": "approved" if approval_status == "valid" else "derived",
        "approval_status": approval_status,
        "human_approved": approval_status == "valid",
        # 纪律：derived / approved 均 **不等于** Trust VERIFIED
        # （VERIFIED 只能来自 Trust-owned provenance，见 _trust_provenance_valid）。
        "derived_equals_verified": False,
        "approved_equals_verified": False,
    }
    if rt is not None and rule_type_status["source"] == "derived":
        reasons.append(
            f"rule_type={rt} 来自**确定性 derived**（非人工批准，且不等于 Trust VERIFIED）")

    # ---- 1. REQUIRED 存在性 ----
    for f in _REQUIRED_PRESENCE:
        if _is_empty(record.get(f)):
            missing_required.append(f)

    if all(_is_empty(record.get(d)) for d in _MATCH_DIMENSIONS):
        missing_required.append("match_dimension(industry|region|type)")

    # eligibility_conditions 必须显式为 list（null → NOT_READY）
    if record.get("eligibility_conditions") is None:
        missing_required.append("eligibility_conditions")

    # percentage / amount / base 依 rule_type
    if _critical_applies(record, "base") and _is_empty(record.get("base")):
        missing_required.append("base")
    if _critical_applies(record, "amount") and _is_empty(record.get("amount")):
        missing_required.append("amount")
    if (rt in ("percentage_of_base", "tax_treatment_rate")
            and _is_empty(record.get("percentage"))):
        missing_required.append("percentage")
    if rt == "fixed_amount" and _is_empty(record.get("amount")):
        missing_required.append("amount")
    if rt not in ("percentage_of_base", "tax_treatment_rate", "fixed_amount"):
        # rule_type 未知 → 退而求其次需要 percentage 或 amount 之一
        if _is_empty(record.get("percentage")) and _is_empty(record.get("amount")):
            missing_required.append("percentage_or_amount")

    # cap / floor 模式条件 REQUIRED
    if record.get("cap") is not None and record.get("cap_mode") not in _VALID_MODES:
        missing_required.append("cap_mode")
    if record.get("floor") is not None and record.get("floor_mode") not in _VALID_MODES:
        missing_required.append("floor_mode")

    # ---- 2. 执行关键字段 provenance 校验（仅 Trust-owned） ----
    critical = list(_EXECUTION_CRITICAL)
    if record.get("cap") is not None:
        critical.append("cap")
    if record.get("floor") is not None:
        critical.append("floor")
    for f in critical:
        if not _critical_applies(record, f):
            continue  # 不适用于本 rule_type → 不影响就绪
        val = record.get(f)
        if val is None:
            continue  # 缺失由 REQUIRED 存在性段处理（已加入 missing_required）
        entry = _fe_entry(record, f)
        if entry is None:
            evidence_gaps.append(f)
            unverified_critical_fields.append(f)
            continue
        if not _evidence_complete(entry):
            evidence_gaps.append(f)
        if not _field_verified(record, f, trust_service, context_key=context_key):
            unverified_critical_fields.append(f)

    # ---- 3. OPTIONAL 三态（PRESENT / MISSING / NOT_APPLICABLE）----
    # 仅 MISSING 阻止 EXECUTION_READY；NOT_APPLICABLE 必须由确定性规则证明（见 _optional_status）。
    for f in OPTIONAL_FIELDS:
        st = _optional_status(record, f)
        optional_status[f] = st
        if st == OPTIONAL_MISSING:
            missing_optional.append(f)
        elif st == OPTIONAL_NOT_APPLICABLE:
            not_applicable_optional.append(f)

    # ---- 4. 状态判定 ----
    if governance_violations:
        # D4：伪造/自相矛盾的 rule_type 批准标记 → fail-closed NOT_READY。
        state = STATE_NOT_READY
        reasons.insert(0, "治理违规（fail-closed）: " + "; ".join(governance_violations))
    elif missing_required or unverified_critical_fields or evidence_gaps:
        state = STATE_NOT_READY
        if missing_required:
            reasons.append("缺失 REQUIRED 字段: " + ", ".join(missing_required))
        if unverified_critical_fields:
            reasons.append("执行关键字段缺 Human-Verified provenance: "
                           + ", ".join(unverified_critical_fields))
        if evidence_gaps:
            reasons.append("Evidence 链不完整: " + ", ".join(evidence_gaps))
    elif missing_optional:
        state = STATE_PARTIAL
        reasons.append("仅缺非关键 OPTIONAL 字段: " + ", ".join(missing_optional)
                       + "（执行关键字段已完整且已验证）")
    else:
        state = STATE_EXECUTION_READY
        reasons.append("全部 REQUIRED 与执行关键字段完整且已 Human-Verified，"
                       "Evidence 链完整（建立在 VERIFIED provenance 之上）")
        if not_applicable_optional:
            reasons.append("OPTIONAL 字段经确定性规则判定为 NOT_APPLICABLE: "
                           + ", ".join(not_applicable_optional))

    # ---- G5 (P4-17): Application-only 缺口分类（不阻断 Eligibility/Benefit 执行）----
    # execution_blocking_missing：去掉 Application-only 项后的「执行阻断」缺失字段。
    execution_blocking_missing = [
        f for f in missing_required if f not in _APPLICATION_ONLY_PRESENCE
    ]
    application_gaps = []
    if _is_empty(record.get("application_requirements")):
        application_gaps.append("application_requirements")
    _chan = record.get("ext_procedural_channel")
    if _chan is None or _chan == "" or (
        isinstance(_chan, str) and _chan.strip().upper() == "UNKNOWN"
    ):
        application_gaps.append("ext_procedural_channel")
    # Application Readiness 与 Overall Execution Readiness 解耦：
    # 前者仅由 Application-only 缺口决定；后者仍包含 Application 缺口（保持 NOT_READY）。
    application_readiness = STATE_NOT_READY if application_gaps else STATE_READY

    return {
        "state": state,
        "missing_required": missing_required,
        "execution_blocking_missing": execution_blocking_missing,
        "missing_optional": missing_optional,
        "not_applicable_optional": not_applicable_optional,
        "optional_status": optional_status,
        "unverified_critical_fields": unverified_critical_fields,
        "evidence_gaps": evidence_gaps,
        "governance_violations": governance_violations,
        "application_readiness": application_readiness,
        "application_gaps": application_gaps,
        "rule_type_status": rule_type_status,
        "reasons": reasons,
    }


def execution_blocking_ready(readiness: Dict[str, Any]) -> bool:
    """G5 (P4-17): 是否仅剩 Application-only 缺口（可放行 Eligibility/Benefit）。

    返回 True 表示**无执行阻断缺口**——即 Policy Contract / Trust VERIFIED /
    execution-critical Evidence / governance violation 均满足；此时即便
    Application Readiness = NOT_READY，仍应允许 Match → Eligibility → Benefit 执行。
    返回 False 表示存在执行阻断缺口，必须硬阻止执行（fail-closed）。

    该函数严格**不降低** Trust Gate：``unverified_critical_fields`` / ``evidence_gaps``
    非空（Trust 未 VERIFIED 或 execution-critical Evidence 未满足）即返回 False。
    """
    return not (
        readiness.get("execution_blocking_missing")
        or readiness.get("unverified_critical_fields")
        or readiness.get("evidence_gaps")
        or readiness.get("governance_violations")
    )


def is_execution_ready(
    record: Dict[str, Any],
    trust_service: Optional[Any] = None,
    context_key: Optional[str] = None,
) -> bool:
    """便捷判断：state == EXECUTION_READY。"""
    return assess_execution_readiness(
        record, trust_service=trust_service, context_key=context_key
    )["state"] == STATE_EXECUTION_READY
