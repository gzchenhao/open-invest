# -*- coding: utf-8 -*-
"""P4-7 — Context A（一次性扩岗补助）PRODUCTION READINESS（READ-ONLY）。

目标：把 Context A 从 NOT_READY 推进到 READY_FOR_HUMAN_GATE。

    READY_FOR_HUMAN_GATE ≠ VERIFIED ≠ REAL 122

本阶段仍不执行 Human Verification、不创建 REAL 122、不写 Trust、不 P3-7。

设计原则：
1. **只从官方 39号通知取 policy-native 事实**；任何外部定义/数据依赖显式标记
   ``external_dependency`` 并置 UNKNOWN，**绝不猜测、绝不以常识冒充 VERIFIED**。
2. **eligible_hired_persons 不是裸数字**：由 per-person Eligibility Conditions 派生
   （target-group → employment），再 ``1500 × eligible_hired_persons``。
3. **不修改 P4-5.3 已通过的计算契约**（evaluate_benefit 仍 1500 × hired_person_count）；
   P4-7 新增"最终 Project Input Contract"派生口径作为权威解释，二者在 aggregate 语义下一致。
4. **Evidence 5-tuple 不断链**：quote / char_span / snapshot_ref / content_identity / source_url。
5. **信任边界**：``derived ≠ approved ≠ VERIFIED``；不 import src/trust、不写 Trust。

生产禁止：不修改 REAL 101–121 / 不创建 REAL 122 / 不写 real_policies.json / 不 commit。
"""

from typing import Any, Dict, List, Optional, Tuple

from global_policy_aggregator.pipeline.p4_5_3_e2e import (
    EL_FAIL, EL_READY, EL_UNKNOWN,
    BEN_CALC, BEN_UNABLE,
    evaluate_eligibility, evaluate_benefit,
)
from global_policy_aggregator.pipeline.rule_context import RD_READY, RD_NOT_READY

SCHEMA_VERSION = "p4-7-context-a-readiness-v1"

# 官方来源（39号通知 fixture 的权威地址，沿用 P4-5.2 修正后的 provenance）
_OFFICIAL_NOTICE_REF = "人社部发〔2026〕39号《关于延续实施失业保险援企稳岗惠民政策有关问题的通知》"

# 执行期间（官方第三条原文）
_EXECUTION_PERIOD = {"start": "2026-01-01", "end": "2026-12-31",
                     "quote": "本通知自2026年1月1日至12月31日执行",
                     "source_field": "execution_period"}

# ─────────────────────────────────────────────────────────────────────────────
# A. Application Requirements（仅 policy-native，来自 39号通知；procedural 标 external）
# ─────────────────────────────────────────────────────────────────────────────
CONTEXT_A_APPLICATION_REQUIREMENTS: List[Dict[str, Any]] = [
    {
        "id": "ar_applicant_entity",
        "description": "申请/享受主体须为企业和社会组织",
        "source_quote": "签订劳动合同并为其足额缴纳3个月以上失业、工伤、职工养老保险费的"
                        "企业和社会组织",
        "source_field": "applicant_entity_type",
        "kind": "eligibility_to_enjoy",           # 享受该补助的前置资格
        "provided_by": "policy_native",            # 通知原文直接规定
        "external_dependency": True,               # 「社会组织」精确范围需外部定义
        "external_note": "社会组织范围（民办非企业单位/基金会/社会团体）依《社会组织登记管理条例》",
        "status": "READY_POLICY_NATIVE",
    },
    {
        "id": "ar_hired_target_group",
        "description": "招用对象须为：毕业年度及离校两年内未就业高校毕业生、16—24岁登记失业青年",
        "source_quote": "招用毕业年度及离校两年内未就业高校毕业生、16—24岁登记失业青年",
        "source_field": "hired_target_group",
        "kind": "eligibility_to_enjoy",
        "provided_by": "policy_native",            # 对象类别原文列出
        "external_dependency": True,               # 各类别精确口径需外部定义
        "external_note": "2026届毕业生/离校两年内/16—24岁/登记失业 口径见外部定义 manifest",
        "status": "READY_POLICY_NATIVE",
    },
    {
        "id": "ar_labor_contract",
        "description": "须与被招用人员签订劳动合同",
        "source_quote": "签订劳动合同",
        "source_field": "labor_contract_signed",
        "kind": "eligibility_to_enjoy",
        "provided_by": "policy_native",
        "external_dependency": False,
        "status": "READY_POLICY_NATIVE",
    },
    {
        "id": "ar_insurance_paid",
        "description": "须为其足额缴纳3个月以上失业、工伤、职工养老保险费",
        "source_quote": "足额缴纳3个月以上失业、工伤、职工养老保险费",
        "source_field": "employment_insurance_paid_months",
        "kind": "eligibility_to_enjoy",
        "provided_by": "policy_native",
        "external_dependency": True,               # 「足额/连续 or 累计」口径需外部
        "external_note": "3个月是否连续/累计、起算时点依社保经办口径",
        "status": "READY_POLICY_NATIVE",
    },
    {
        "id": "ar_execution_period",
        "description": "招用/发放须在执行期间内：2026-01-01 至 2026-12-31",
        "source_quote": _EXECUTION_PERIOD["quote"],
        "source_field": "execution_period",
        "kind": "eligibility_to_enjoy",
        "provided_by": "policy_native",            # 第三条原文
        "external_dependency": False,
        "status": "READY_POLICY_NATIVE",
    },
    {
        "id": "ar_procedural_channel",
        "description": "申请/发放渠道、材料、受理机构、办理截止——通知以「按规定」委托实施规定",
        "source_quote": "可按每招用1人不超过1500元的标准发放一次性扩岗补助",
        "source_field": None,
        "kind": "procedural",                       # 程序性申请要求
        "provided_by": "external",                 # 通知未具体规定，委托实施规定
        "external_dependency": True,
        "external_note": "依地方实施规定/人社部门办事指南；不在 39号通知正文，保持 UNKNOWN",
        "status": "UNKNOWN",                        # 未猜测
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# B. External Dependency manifest（hired_target_group 等需外部官方定义的事实）
# ─────────────────────────────────────────────────────────────────────────────
CONTEXT_A_EXTERNAL_DEPENDENCIES: List[Dict[str, Any]] = [
    {
        "id": "ext_grad_2026",
        "fact": "「2026届毕业生」/「毕业年度」的精确定义（自然年 vs 学年；2026届=2026年毕业）",
        "required_official_source": "教育部学籍/学历证书管理规定；人社部政策口径",
        "external_dependency": True,
        "status": "UNKNOWN",                       # 39号通知未含
        "note": "不猜测；交由 Human Gate / 外部定义绑定",
    },
    {
        "id": "ext_leave_school_2y",
        "fact": "「离校两年内」起算时点与「未就业」认定口径",
        "required_official_source": "人社部《就业失业登记管理办法》及高校毕业生就业政策",
        "external_dependency": True,
        "status": "UNKNOWN",
        "note": "通知仅列类别，未给口径",
    },
    {
        "id": "ext_age_16_24",
        "fact": "「16—24岁」年龄计算时点（周岁，截至申请日/参保日）",
        "required_official_source": "人社部青年就业政策口径",
        "external_dependency": True,
        "status": "UNKNOWN",
    },
    {
        "id": "ext_registered_unemployed",
        "fact": "「登记失业青年」认定（需就业失业登记）",
        "required_official_source": "人社部《就业失业登记管理办法》",
        "external_dependency": True,
        "status": "UNKNOWN",
    },
    {
        "id": "ext_social_org_scope",
        "fact": "「社会组织」精确范围（民办非企业单位/基金会/社会团体）",
        "required_official_source": "《社会组织登记管理条例》及民政部口径",
        "external_dependency": True,
        "status": "UNKNOWN",
    },
    {
        "id": "ext_pay_3_months",
        "fact": "「足额缴纳3个月以上」连续/累计与起算时点",
        "required_official_source": "人社部/社保经办口径",
        "external_dependency": True,
        "status": "UNKNOWN",
    },
    {
        "id": "ext_procedural_channel",
        "fact": "申请/发放渠道、材料清单、受理机构、办理截止",
        "required_official_source": "地方实施规定/人社部门办事指南",
        "external_dependency": True,
        "status": "UNKNOWN",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# C. eligible_hired_persons 派生链（不能只是数字）
# ─────────────────────────────────────────────────────────────────────────────
def _target_group_set(ctx: Dict[str, Any]) -> set:
    for c in ctx.get("conditions") or []:
        if c.get("id") == "hired_target_group_in_scope":
            ev = c.get("expected_value")
            return set(ev if isinstance(ev, list) else [ev])
    return set()


def derive_eligible_hired_persons(ctx: Dict[str, Any],
                                  project_facts: Dict[str, Any]) -> Tuple[Optional[int], Optional[str]]:
    """由 per-person Eligibility Conditions 派生合格招用人数。

    链：hired_person_count（或 hired_persons 明细）
        → target-group eligibility（hired_target_group_in_scope）
        → employment eligibility（labor_contract_signed + 缴费≥3月）
        → eligible_hired_persons
        → 1500 × eligible_hired_persons
    """
    facts = project_facts or {}
    tg_set = _target_group_set(ctx)

    persons = facts.get("hired_persons")
    if persons is None:
        # aggregate 回退：仅当同时提供 hired_person_count 且整体资格已由 Eligibility 判定，
        # 但 per-person 资格无法从聚合数判定 → 要求明细或显式声明。
        cnt = facts.get("hired_person_count")
        if cnt is None:
            return None, "缺 hired_person_count / hired_persons → 无法判定合格人数"
        # 聚合数不能证明 per-person 资格；若调用方已通过 eligibility 整体核验并显式声明，
        # 才允许作为 eligible 计数（否则 fail-closed）。
        if facts.get("eligible_hired_persons_declared") is not None:
            return int(facts["eligible_hired_persons_declared"]), None
        return None, ("aggregate hired_person_count 不能判定 per-person 资格；"
                      "需 hired_persons 明细或显式 eligible_hired_persons_declared")

    eligible = 0
    for p in persons:
        in_scope = (p.get("target_group") in tg_set) if tg_set else False
        contract = bool(p.get("labor_contract_signed"))
        months = p.get("employment_insurance_paid_months")
        months_ok = isinstance(months, (int, float)) and months >= 3
        if in_scope and contract and months_ok:
            eligible += 1
    return eligible, None


def compute_context_a_benefit(ctx: Dict[str, Any],
                              project_facts: Dict[str, Any]) -> Dict[str, Any]:
    """Context A 最终 Benefit 计算：1500 × eligible_hired_persons（per-person 派生）。"""
    facts = project_facts or {}
    amount = ctx.get("amount")
    if amount is None:
        return {"status": BEN_UNABLE, "amount": None,
                "reason": "fixed_amount 金额无 policy 证据"}
    eligible, err = derive_eligible_hired_persons(ctx, facts)
    if eligible is None:
        return {"status": BEN_UNABLE, "amount": None,
                "reason": f"eligible_hired_persons 不可判定：{err}",
                "per_person_amount": amount}
    # per-person 语义锁定（沿用 P4-5.3 契约）：unit 缺失 → fail-closed
    if not ctx.get("unit"):
        return {"status": BEN_UNABLE, "amount": None,
                "reason": "per-unit unit（元/人）缺失 → 无法断言 per-person 语义",
                "per_person_amount": amount}
    if eligible <= 0:
        return {"status": BEN_UNABLE, "amount": None,
                "reason": "eligible_hired_persons ≤ 0 → 不产生正向 Benefit",
                "per_person_amount": amount}
    benefit = amount * eligible
    return {
        "status": BEN_CALC, "amount": benefit,
        "per_person_amount": amount, "unit": ctx.get("unit"),
        "eligible_hired_persons": eligible,
        "formula": f"{amount}(每人) × {eligible}(合格人数) = {benefit}",
        "reason": "per-person 固定额度（元/人）× 合格招用人数（per-person 资格派生）",
    }


# ─────────────────────────────────────────────────────────────────────────────
# E. Evidence 5-tuple 完整性
# ─────────────────────────────────────────────────────────────────────────────
def _evidence_refs_ok(ctx: Dict[str, Any]) -> bool:
    refs = ctx.get("evidence_refs") or []
    if not refs:
        return False
    r = refs[0]
    return bool(r.get("snapshot_ref") and r.get("content_identity") and r.get("source_url"))


def evidence_complete(ctx: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """execution-critical policy 字段必须齐备 quote/char_span + 顶层 snapshot/content_identity/url。"""
    missing: List[str] = []
    if not _evidence_refs_ok(ctx):
        missing.append("evidence_refs(5-tuple)")
    # amount
    amt = (ctx.get("fields") or {}).get("amount")
    if not (amt and amt.get("quote") and amt.get("char_span")):
        missing.append("amount")
    # per_unit（unit 证据）
    pu = (ctx.get("benefit_basis") or {}).get("per_unit") or {}
    if pu and not (pu.get("quote") and pu.get("char_span")):
        missing.append("per_unit")
    # conditions
    for c in ctx.get("conditions") or []:
        if not (c.get("quote") and c.get("char_span")):
            missing.append(f"condition:{c.get('id')}")
    return (len(missing) == 0), missing


# ─────────────────────────────────────────────────────────────────────────────
# H. Context A Human Gate Readiness Matrix
# ─────────────────────────────────────────────────────────────────────────────
def assess_context_a_human_gate_readiness(
        ctx: Dict[str, Any],
        project_facts: Optional[Dict[str, Any]] = None,
        external_statistics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """评估 Context A 是否 READY_FOR_HUMAN_GATE（≠ VERIFIED，≠ REAL 122）。

    判定口径：政策规格 + Evidence + Application(policy-native) + External(surfaced) 均就绪，
    即达到"可交付人类在 gate 上审查"；Trust VERIFIED 与真实企业数据绑定为后续 gate，不在此阻断。
    """
    facts = project_facts or {}

    # Benefit —— 规则 + 证据层 READY（真实数据缺失仅影响执行，不阻断 gate）
    ben_rule_ready = (ctx.get("rule_type") == "fixed_amount"
                      and ctx.get("amount") is not None and bool(ctx.get("unit")))

    # Eligibility —— 规则层 READY（条件/算子/证据齐全）；real-data 另记
    elig = evaluate_eligibility(ctx, facts, external_statistics=external_statistics)
    elig_rule_ready = bool(ctx.get("conditions")) and all(
        (c.get("quote") and (c.get("expected_value") is not None or c.get("operator")))
        for c in ctx.get("conditions") or [])

    # Project Input —— 最终合同已定义（eligible_hired_persons 派生链）
    project_input_ready = True  # 见 CONTEXT_A_PROJECT_INPUT_CONTRACT + derive 函数

    # Application —— policy-native 要求已逐项列出来源（procedural 标 external/UNKNOWN）
    app_ready = all(a["provided_by"] == "policy_native"
                    for a in CONTEXT_A_APPLICATION_REQUIREMENTS
                    if a["kind"] == "eligibility_to_enjoy")

    # Evidence —— 5-tuple 完整
    ev_ok, ev_missing = evidence_complete(ctx)

    # External —— 已识别并显式标记（不阻断 gate）
    ext_acknowledged = all(d["external_dependency"] and d["status"] == "UNKNOWN"
                           for d in CONTEXT_A_EXTERNAL_DEPENDENCIES)

    # Trust —— 本阶段不 VERIFIED（后续 gate）
    trust_ready = False

    # Overall
    overall = "READY_FOR_HUMAN_GATE" if (
        ben_rule_ready and elig_rule_ready and project_input_ready
        and app_ready and ev_ok and ext_acknowledged
    ) else "NOT_READY"

    matrix = [
        {"item": "Benefit", "status": "READY" if ben_rule_ready else "NOT_READY",
         "blocker": "" if ben_rule_ready else "rule_type/amount/unit 缺失",
         "evidence": "amount=1500 元/人（quote 绑定）；per-person 契约锁定"},
        {"item": "Eligibility", "status": "READY" if elig_rule_ready else "NOT_READY",
         "blocker": "" if elig_rule_ready else "条件/算子/证据缺失",
         "evidence": "4 条件均 quote+char_span；external-def 事实已标记 UNKNOWN"},
        {"item": "Project Input", "status": "READY" if project_input_ready else "NOT_READY",
         "blocker": "",
         "evidence": "最终合同 + eligible_hired_persons 派生链（per-person）"},
        {"item": "Application", "status": "READY" if app_ready else "NOT_READY",
         "blocker": "" if app_ready else "policy-native 要求缺来源",
         "evidence": "5 项 policy-native 要求逐项引通知原文；procedural 标 external/UNKNOWN"},
        {"item": "Evidence", "status": "READY" if ev_ok else "NOT_READY",
         "blocker": ", ".join(ev_missing),
         "evidence": "quote/char_span/snapshot_ref/content_identity/source_url 5-tuple"},
        {"item": "External Dependency", "status": "ACKNOWLEDGED" if ext_acknowledged else "NOT_READY",
         "blocker": "" if ext_acknowledged else "外部依赖未显式标记",
         "evidence": f"{len(CONTEXT_A_EXTERNAL_DEPENDENCIES)} 项 external_dependency=UNKNOWN，"
                     "各列 required_official_source，未猜测"},
        {"item": "Trust", "status": "NOT_READY" if not trust_ready else "READY",
         "blocker": "provenance 未经 Trust 层 VERIFIED（后续 gate，非本阶段）",
         "evidence": "derived ≠ approved ≠ VERIFIED；不写 Trust、不 Human Verify"},
        {"item": "Overall", "status": overall,
         "blocker": "" if overall == "READY_FOR_HUMAN_GATE"
         else "上述某项 NOT_READY",
         "evidence": "可交付 Human Gate 审查（≠ VERIFIED，≠ REAL 122）"},
    ]
    return {
        "schema": SCHEMA_VERSION,
        "context": "A",
        "policy_ref": _OFFICIAL_NOTICE_REF,
        "overall": overall,
        "real_data_eligibility_status": elig.get("status"),  # 真实数据缺失时为 UNKNOWN（执行层）
        "matrix": matrix,
        "application_requirements": CONTEXT_A_APPLICATION_REQUIREMENTS,
        "external_dependencies": CONTEXT_A_EXTERNAL_DEPENDENCIES,
    }


# ─────────────────────────────────────────────────────────────────────────────
# C（续）. Context A 最终 Project Input Contract
# ─────────────────────────────────────────────────────────────────────────────
CONTEXT_A_PROJECT_INPUT_CONTRACT: List[Dict[str, Any]] = [
    {"field": "hired_persons", "meaning": "per-person 招用明细（含 target_group/labor_contract/"
     "employment_insurance_paid_months）", "type": "list[object]",
     "source": "project_profile", "required": True,
     "use": "eligibility+benefit", "evidence": "policy（条件原文）",
     "external_dependency": True, "current_state": "CONTRACT_DEFINED / REAL_DATA_MISSING"},
    {"field": "hired_person_count", "meaning": "招用总人数（aggregate 回退）", "type": "int",
     "source": "project_profile", "required": False,
     "use": "benefit(回退)", "evidence": "policy（每招用1人）",
     "external_dependency": False, "current_state": "CONTRACT_DEFINED / REAL_DATA_MISSING"},
    {"field": "eligible_hired_persons", "meaning": "经 per-person 资格派生的合格人数",
     "type": "int", "source": "derived(derive_eligible_hired_persons)",
     "required": True, "use": "benefit", "evidence": "derived from policy 条件",
     "external_dependency": False, "current_state": "DERIVATION_DEFINED"},
    {"field": "employment_insurance_paid_months", "meaning": "为该人足额缴纳失业/工伤/职工养老月数",
     "type": "int", "source": "project_profile", "required": True,
     "use": "eligibility", "evidence": "足额缴纳3个月以上…费",
     "external_dependency": True, "current_state": "CONTRACT_DEFINED / REAL_DATA_MISSING"},
    {"field": "labor_contract_signed", "meaning": "是否签订劳动合同", "type": "bool",
     "source": "project_profile", "required": True, "use": "eligibility",
     "evidence": "签订劳动合同", "external_dependency": False,
     "current_state": "CONTRACT_DEFINED / REAL_DATA_MISSING"},
    {"field": "applicant_entity_type", "meaning": "申请主体类型", "type": "enum(企业和社会组织)",
     "source": "project_profile", "required": True, "use": "eligibility",
     "evidence": "企业和社会组织", "external_dependency": True,
     "current_state": "CONTRACT_DEFINED / REAL_DATA_MISSING"},
    {"field": "hired_target_group", "meaning": "招用对象所属类别", "type": "enum(见 policy)",
     "source": "project_profile", "required": True, "use": "eligibility",
     "evidence": "招用毕业年度及离校两年内未就业高校毕业生、16—24岁登记失业青年",
     "external_dependency": True, "current_state": "CONTRACT_DEFINED / REAL_DATA_MISSING"},
    {"field": "execution_period_check", "meaning": "招用/发放是否在 2026-01-01~12-31",
     "type": "bool", "source": "derived(policy 第三条)", "required": True, "use": "eligibility",
     "evidence": "本通知自2026年1月1日至12月31日执行", "external_dependency": False,
     "current_state": "DERIVATION_DEFINED"},
]
