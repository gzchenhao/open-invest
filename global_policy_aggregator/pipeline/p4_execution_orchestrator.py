"""P4-3 Execution orchestration (READ-ONLY).

流程：
    ProjectProfile
        → Policy readiness assessment (p4_execution_state)
        → Policy Match (复用 global_policy_aggregator.matching)
        → Eligibility (复用 p4_rule_engine.check_eligibility / p4_rule_operator)
        → Benefit (复用 p4_rule_engine.calculate_benefit / p4_rule_operator)
        → Evidence-bound result

治理边界（JUDGE P4-3）：
- 仅复用既有 matching / p4_rule_engine / p4_rule_operator；不重新实现 Rule Engine。
- 不修改 REAL、不写 src.trust、不 ingestion、不 verification、不调用 LLM 决策。
- NOT_READY → 不执行 Benefit；PARTIAL → 执行但显式记录 readiness gaps，
  若执行关键字段缺失则引擎自然返回 unable_to_calculate（不补默认 policy facts）。
- 任何计算/匹配/资格结果均携带 evidence trace。
"""

import dataclasses
from typing import Any, Dict, List, Optional

from global_policy_aggregator.matching import (
    build_project_profile,
    match_project_to_policy,
)
from global_policy_aggregator.pipeline.p4_execution_state import (
    assess_execution_readiness,
    execution_blocking_ready,
    _resolve_trust_identity,
)
from global_policy_aggregator.pipeline.p4_rule_operator import evaluate_policy


def _active_context_key(record: Dict[str, Any]) -> Optional[str]:
    """决定该 policy 默认执行上下文对应的 trust_bindings key（P6-3.18）。

    REAL122 同时存在 Context A（primary / 顶层 rule_type）与 Context B（variant）。
    默认执行上下文为 A：若 policy 声明了 ``trust_bindings['context_a']`` 则使用它，
    否则回退顶层 legacy（返回 None）。Context B 由独立路径（context_b_execution）
    处理，不会在此被当作 A 的 binding，也不允许跨 context 继承。
    """
    tb = record.get("trust_bindings") or {}
    if "context_a" in tb:
        return "context_a"
    return None


def _build_provenance(pol: Dict[str, Any],
                      trust_service: Optional[Any],
                      context_key: Optional[str] = None) -> Dict[str, Any]:
    """构建可供 UI 消费的完整 provenance（只读；绝不创建 verification event）。

    Policy 层字段来自 REAL record（恒可用）；Trust 层字段来自正式 Trust 服务的
    只读 ``check_verified_validity``（严格的 VERIFIED gate，不推断、不新建）。

    信任绑定解析（P6-3.18，与 ``_trust_provenance_valid`` 完全一致）：
    优先读取 ``trust_bindings[context_key]`` 的 per-context ``evidence_id``，否则
    回退顶层 legacy ``evidence_id``。``evidence_id`` 字段与后续 Trust 校验均使用
    解析后的 id，从而保证 provenance **报告**与 readiness **门禁**一致地反映 Context
    A 的独立证据（``ev_ctx_122_context_a``），而非共享 legacy 证据。

    跨上下文隔离守卫（Case G）：当请求 ``context_key`` 时，被绑定 evidence 的
    ``metadata.context_id`` 必须等于 ``context_key``，否则 fail-closed（不报告任何
    Trust VERIFIED provenance）。

    严格区分：
    - ``policy_content_identity`` = REAL record content_identity（Policy CI）
    - ``trust_content_identity``  = 正式 Trust verification event 的 content_identity（Trust CI）

    二者**绝不合并为同一字段**。record-local verification_status 不被当作 Trust VERIFIED。
    """
    # per-context binding 优先，否则回退顶层 legacy（与 gate 同一解析函数）
    resolved_evidence_id, _claimed_event_id = _resolve_trust_identity(pol, context_key)
    prov: Dict[str, Any] = {
        "policy_id": pol.get("id"),
        "source_url": pol.get("source_url"),
        "snapshot_ref": pol.get("snapshot_ref"),
        "policy_content_identity": pol.get("content_identity"),
        "evidence_id": resolved_evidence_id,
        "trust_content_identity": None,
        "verification_event_id": None,
        "verifier_id": None,
        "verifier_role": None,
        "trust_verification_status": None,
    }
    if trust_service is not None and resolved_evidence_id:
        # Case G 隔离守卫（与 _trust_provenance_valid 一致）：被绑定 evidence 的
        # metadata.context_id 必须等于请求的 context_key，否则 fail-closed。
        if context_key:
            try:
                ev_obj = trust_service.get_evidence(resolved_evidence_id)
                if ev_obj.get("success"):
                    ctx = (ev_obj.get("evidence") or {}).get("metadata", {}).get("context_id")
                    if ctx and ctx != context_key:
                        prov["trust_verification_status"] = "REJECTED_CROSS_CONTEXT"
                        prov["trust_verification_status_detail"] = (
                            f"跨上下文绑定被拒绝：evidence context_id={ctx} "
                            f"不等于请求 context_key={context_key}（fail-closed）")
                        trust_service = None
            except Exception:
                pass
        if trust_service is not None:
            try:
                vr = trust_service.check_verified_validity(resolved_evidence_id)
                prov["trust_verification_status"] = vr.get("current_verification_status")
                prov["trust_content_identity"] = vr.get("current_content_identity")
                latest = vr.get("latest_verified_event")
                if isinstance(latest, dict):
                    prov["verification_event_id"] = latest.get("event_id")
                    if latest.get("content_identity"):
                        prov["trust_content_identity"] = latest["content_identity"]
                    prov["verifier_id"] = latest.get("actor")
                    prov["verifier_role"] = latest.get("actor_role")
            except Exception:
                # 只读失败 → 不伪造 Trust provenance；Policy 层字段仍保留
                pass
    # P4-31-4：明确 Trust VERIFIED 语义（OpenInvest Trust Layer 内部人工内容核验，
    # 非政府审批/认定/保证/自动拨付）。不新增 verification event，不调用 Human Verification 记录。
    prov["trust_layer"] = "OpenInvest Trust Layer (human-verified content provenance)"
    prov["trust_verification_clarification"] = (
        "trust_verification_status=VERIFIED 表示 OpenInvest Trust Layer 的**内部人工内容核验**"
        "（由 OpenInvest 指定 verifier 完成政策内容真实性验证），"
        "非政府审批、非政府资格认定、不构成补贴保证或自动拨付。"
    )
    return prov


def _match_to_dict(m) -> Dict[str, Any]:
    """将 MatchResult 转为可序列化 dict（保留 evidence trace）。"""
    return {
        "match_status": m.match_status,
        "score": m.score,
        "matched_dimensions": [d.dimension for d in m.matched_dimensions],
        "unmatched_dimensions": [d.dimension for d in m.unmatched_dimensions],
        "unknown_dimensions": list(m.unknown_dimensions),
        "explanation": m.explanation,
        "evidence_refs": [
            {
                "field": e.field,
                "source_url": e.source_url,
                "policy_content_identity": e.policy_content_identity,
                "snapshot_ref": e.snapshot_ref,
            }
            for e in m.evidence_refs
        ],
    }


# ───────── P4-31：USER-FACING RESULT CONTRACT 语义增强（仅新增结构化字段；
#           不修改 check_eligibility / calculate_benefit 判断与计算逻辑，不伪造状态）─────────
def _enrich_eligibility(eligibility: Any, per_person_eligibility: Optional[Dict[str, Any]]
                        ) -> Dict[str, Any]:
    """P4-31-1：在 project-level eligibility 上附加明确语义字段（**不改**判断逻辑）。

    - 仅新增 level / scope / description 说明其为项目级；
    - 新增 per_person_summary（逐人计数摘要），**不并入** project overall。
    """
    d = dataclasses.asdict(eligibility) if dataclasses.is_dataclass(eligibility) else dict(eligibility)
    d["level"] = "project"
    d["scope"] = "project_level"
    d["description"] = (
        "Project-level eligibility（项目/主体是否符合政策项目级条件，如企业类型）。"
        "仅表示主体层面符合条件；不表示任何招聘人员符合。逐人资格见 per_person_eligibility。"
    )
    if isinstance(per_person_eligibility, dict):
        persons = per_person_eligibility.get("persons") or []
        d["per_person_summary"] = {
            "total": per_person_eligibility.get("hired_count"),
            "eligible": sum(1 for p in persons if p.get("overall") == "PASS"),
            "failed": sum(1 for p in persons if p.get("overall") == "FAIL"),
            "unknown": sum(1 for p in persons if p.get("overall") == "UNKNOWN"),
            "note": "逐人资格计数摘要（来自 per_person_eligibility）；仅供阅读，不并入 project overall。",
        }
    return d


def _enrich_per_person_eligibility(pp: Any) -> Any:
    """P4-31-1：标记 per_person_eligibility 的层级与语义（**不改**判定）。"""
    if not isinstance(pp, dict):
        return pp
    d = dict(pp)
    d["level"] = "person"
    d["scope"] = "per_person"
    d["description"] = (
        "Per-person eligibility（逐人招聘资格判定），与 project-level eligibility 完全独立。"
    )
    return d


def _enrich_benefit(benefit: Any, per_person_eligibility: Optional[Dict[str, Any]]
                   ) -> Dict[str, Any]:
    """P4-31-2：在 Benefit 上附加 calculation_basis（**不改**计算 / 不伪造状态）。

    仅用既有确定性结构（per_person_eligibility 的 PASS/UNKNOWN 计数）说明当前
    calculated_amount 的确定性程度；不改变 calculation_status（calculated / unable_to_calculate）。
    """
    d = dataclasses.asdict(benefit) if dataclasses.is_dataclass(benefit) else dict(benefit)
    status = d.get("calculation_status")
    eligible = (d.get("input_values") or {}).get("eligible_hired_persons")
    n_unknown = 0
    if isinstance(per_person_eligibility, dict):
        n_unknown = sum(1 for p in (per_person_eligibility.get("persons") or [])
                        if p.get("overall") == "UNKNOWN")
    if status == "calculated":
        deterministic = (n_unknown == 0)
        reason = ("逐人资格已全部确定（无 UNKNOWN），calculated_amount 为确定性结果。"
                  if deterministic else
                  f"calculated_amount={d.get('calculated_amount')} 由 eligible_hired_persons={eligible} "
                  f"确定性算出，但其中有 {n_unknown} 人逐人资格为 UNKNOWN（事实不足），"
                  "该金额依赖未核验人员；补齐逐人事实后可重新计算。")
        d["calculation_basis"] = {
            "eligible_hired_persons": eligible,
            "per_person_unknown_count": n_unknown,
            "deterministic": deterministic,
            "reason": reason,
        }
    else:  # unable_to_calculate：无确定金额，给出缺失原因（保持 benefit schema 稳定）
        d["calculation_basis"] = {
            "eligible_hired_persons": eligible,
            "per_person_unknown_count": n_unknown if isinstance(per_person_eligibility, dict) else None,
            "deterministic": None,
            "reason": "Benefit unable_to_calculate（输入/模式缺失或 eligibility 非 PASS）；无确定金额，不猜测。",
        }
    return d


def _build_missing_inputs(eligibility: Dict[str, Any],
                          per_person_eligibility: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """P4-31-3：确定性构造 missing_inputs（**仅**来自既有 UNKNOWN 结构，不 LLM / 不猜测）。

    规则：
    - 仅纳入 status == UNKNOWN 的条件（明确值但冲突 = FAIL 不列入；已提供值 != 缺失）；
    - 逐人层按 source_field 去重聚合（同一字段对所有人员缺失只列一次）；
    - 不把 user_stated_eligible_count 当作真实 eligibility；
    - 不把 policy-provided execution period 当缺失输入（其 source_field 恒为用户 hire_date）。
    """
    missing: List[Dict[str, Any]] = []
    if isinstance(eligibility, dict):
        for c in eligibility.get("conditions", []):
            if c.get("status") == "UNKNOWN":
                missing.append({
                    "field": c.get("condition_id") or c.get("source_field"),
                    "source_field": c.get("source_field"),
                    "expected": c.get("expected"),
                    "scope": "project",
                    "affects": ["project_eligibility"],
                    "reason": "项目级资格需要该事实；当前缺失 → 项目级资格 UNKNOWN。",
                })
    if isinstance(per_person_eligibility, dict):
        seen: Dict[str, Any] = {}
        for p in per_person_eligibility.get("persons", []) or []:
            for c in p.get("conditions", []):
                if c.get("status") == "UNKNOWN":
                    key = c.get("condition_id") or c.get("source_field")
                    if key not in seen:
                        seen[key] = c
        for c in seen.values():
            missing.append({
                "field": c.get("condition_id") or c.get("source_field"),
                "source_field": c.get("source_field"),
                "expected": c.get("expected"),
                "scope": "per_person",
                "affects": ["per_person_eligibility", "benefit"],
                "reason": "逐人资格需要该事实；当前缺失 → 该人资格 UNKNOWN，并影响 eligible_hired_persons 与 Benefit。",
            })
    return missing


def evaluate_project_against_policies(
    project_profile: Any,
    policies: List[Dict[str, Any]],
    project_inputs: Optional[Dict[str, Any]] = None,
    trust_service: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """对一组 Policy 执行 Project → Match → Eligibility → Benefit（只读）。

    Args:
        project_profile: dict（项目事实，含匹配维度 industry/region 与资格事实键）
            或已构建的 ProjectProfile。
        policies: Policy 记录列表（不修改）。
        project_inputs: Benefit 计算所需基数（如 {"rd_expense": 1_000_000}）。

    Returns:
        每条 Policy 一个 evidence-bound 结果 dict。
    """
    if isinstance(project_profile, dict):
        prof = build_project_profile(project_profile)
        facts = project_profile
    else:
        prof = project_profile
        facts = {k: getattr(project_profile, k) for k in ("industry", "region",
                  "funding_need") if getattr(project_profile, k) is not None}

    results: List[Dict[str, Any]] = []
    for pol in policies:
        context_key = _active_context_key(pol)
        readiness = assess_execution_readiness(
            pol, trust_service=trust_service, context_key=context_key)
        state = readiness["state"]
        entry: Dict[str, Any] = {
            "policy_id": pol.get("id"),
            "readiness_state": state,
            "application_readiness": readiness["application_readiness"],
            "application_gaps": readiness["application_gaps"],
            "readiness_detail": {
                "missing_required": readiness["missing_required"],
                "execution_blocking_missing": readiness["execution_blocking_missing"],
                "missing_optional": readiness["missing_optional"],
                "unverified_critical_fields": readiness["unverified_critical_fields"],
                "evidence_gaps": readiness["evidence_gaps"],
                "application_gaps": readiness["application_gaps"],
                "reasons": readiness["reasons"],
            },
            "content_identity": pol.get("content_identity"),
            "snapshot_ref": pol.get("snapshot_ref"),
            "source_url": pol.get("source_url"),
        }

        # G5 (P4-17)：仅当存在「执行阻断」缺口（Policy Contract / Trust VERIFIED /
        # execution-critical Evidence / governance violation）才阻止 Match→Eligibility→
        # Benefit。Application-only 缺口（application_requirements / ext_procedural_channel）
        # 不硬阻断执行，仅进入 Application Readiness limitations（P4-11：C 类 procedural
        # channel 不阻断 Eligibility / Benefit）。Trust Gate 不被降低：unverified_critical_
        # fields / evidence_gaps 非空即视为执行阻断。
        if not execution_blocking_ready(readiness):
            # 执行阻断：不执行 Match / Eligibility / Benefit；保留 readiness 证据
            entry["match"] = None
            entry["eligibility"] = None
            entry["benefit"] = None
            entry["evidence_refs"] = []
            # 解释层字段仍按可用信息填充（Policy 层恒可用；Trust 层在无 gate 时为 None）
            entry["policy_rule"] = None
            entry["provenance"] = _build_provenance(pol, trust_service, context_key)
            entry["per_person_eligibility"] = None
            entry["missing_inputs"] = None
            entry["limitations"] = readiness["reasons"]
            results.append(entry)
            continue

        # PARTIAL 或 EXECUTION_READY → 执行 Match → Eligibility → Benefit
        match = match_project_to_policy(prof, pol)
        ev = evaluate_policy(pol, project_inputs=project_inputs, project_profile=facts)
        pp = ev.get("per_person_eligibility")
        entry["match"] = _match_to_dict(match)
        # P4-31-1 / P4-31-2：项目级 eligibility / benefit 附加明确语义字段（不改判定/计算）
        entry["eligibility"] = _enrich_eligibility(ev["eligibility"], pp)
        entry["benefit"] = _enrich_benefit(ev["benefit"], pp)
        entry["evidence_refs"] = ev.get("evidence_refs")
        # ── P4-28：增强 contract 可解释性与 provenance（仅新增结构化字段）──
        # rule_type 来自已存在的 policy rule definition / REAL 122（非 LLM、非重新推导）
        entry["policy_rule"] = {
            "rule_type": ev.get("rule_type"),
            "rule_type_source": ev.get("rule_type_source"),
        }
        # 完整 provenance：Policy CI 与 Trust CI 在独立字段，严格分离（P4-31-4 附加语义说明）
        entry["provenance"] = _build_provenance(pol, trust_service, context_key)
        # 结构化逐人 eligibility 解释（不改判定逻辑；P4-31-1 附加层级语义）
        entry["per_person_eligibility"] = _enrich_per_person_eligibility(pp)
        # P4-31-3：确定性缺失输入清单（仅来自既有 UNKNOWN 结构）
        entry["missing_inputs"] = _build_missing_inputs(entry["eligibility"], entry["per_person_eligibility"])

        limits = list(readiness["reasons"])
        if readiness["application_gaps"]:
            limits.append("Application Readiness 未就绪（不阻断执行）: "
                           + ", ".join(readiness["application_gaps"]))
        if ev["benefit"].get("calculation_status") == "unable_to_calculate":
            limits.append("Benefit 无法计算（输入/模式缺失），未补任何默认 policy fact")
        entry["limitations"] = limits
        results.append(entry)

    return results
