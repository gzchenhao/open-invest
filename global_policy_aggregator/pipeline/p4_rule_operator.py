"""P4-2 READ-ONLY Rule Engine Operator.

消费层入口：REAL policy record + 项目事实 → 确定性 Benefit/Eligibility 结果 + Evidence trace。

治理边界（JUDGE P4-2A）：
- 本 operator 仅调用 p4_rule_engine 的确定性函数；不调用 LLM、不估算、不猜测。
- 不修改 real_policies.json、不写 src/trust、不产生 verification 状态、不执行 ingestion。
- 不调用 legacy ``policy_ai_agent``（其 ``investment_capacity_usd * 0.15`` 等 heuristic
  与 P4-2 确定性治理冲突，禁止在本 operator 中使用）。
- 所有证据溯源沿用 record 的 field_evidence（record-level trace）。

注意：``global_policy_aggregator/agents/policy_ai_agent.py`` 为 legacy/mock 路径（含 MOCK 数据声明），
其收益/资格 heuristic 不属于 P4-2 确定性路径，本 operator 不 import、不调用它。

Evidence trace 至少能回答：
- 使用了哪条 policy（policy_id）
- 使用了哪一个 content_identity
- 使用了哪个 snapshot（snapshot_ref）
- 使用了哪个 source_url
- 使用了哪些 field_evidence（evidence_refs）
"""

from dataclasses import asdict
from typing import Any, Dict, Optional

from global_policy_aggregator.pipeline.p4_rule_engine import (
    build_rule_from_real_record,
    calculate_benefit,
    check_eligibility,
    explain_per_person_eligibility,
)


def evaluate_policy(record: Dict[str, Any],
                    project_inputs: Optional[Dict[str, Any]] = None,
                    project_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """READ-ONLY 评估单条 REAL 政策的 Benefit + Eligibility。

    Args:
        record: REAL policy 记录（已 Evidence-bound；本函数不修改它）。
        project_inputs: 计算所需基数（如 ``{"taxable_income": 1_000_000}`` /
            ``{"annual_premium": 100_000}``）。
            对于 tax_treatment_rate，即使提供基数也不计算现金（返回 policy_outcome）。
        project_profile: Eligibility 条件所需项目事实（dict，键对应 condition.source_field）。
            可直接传入 ProjectProfile.other_explicit_facts。

    Returns:
        dict 含 policy_id / content_identity / snapshot_ref / source_url / rule_type /
            benefit(CalculationResult) / eligibility(EligibilityResult) / evidence_refs。
    """
    rule = build_rule_from_real_record(record)
    eligibility = check_eligibility(rule, project_profile=project_profile)
    benefit = calculate_benefit(rule, project_inputs=project_inputs,
                                eligibility_overall=eligibility.overall)
    # snapshot_ref：优先取 record 顶层；REAL 记录顶层未必含 snapshot_ref，
    # 此时回退到 field_evidence（evidence_refs）中的 snapshot，保证 trace 完整。
    snap = record.get("snapshot_ref")
    if not snap and benefit.evidence_refs:
        snap = benefit.evidence_refs[0].get("snapshot_ref")
    return {
        "policy_id": record.get("id"),
        "content_identity": record.get("content_identity"),
        "snapshot_ref": snap,
        "source_url": record.get("source_url"),
        # D4：显式分离 rule_type 的来源（derived ≠ approved ≠ Trust VERIFIED）
        "rule_type": rule.rule_type,
        "rule_type_source": rule.rule_type_source,
        "rule_type_derived": rule.rule_type_derived,
        "rule_type_approved": rule.rule_type_approved,
        "human_approved": rule.human_approved,
        "benefit": asdict(benefit),
        "eligibility": asdict(eligibility),
        # 结构化逐人 eligibility 解释（只读解释层；不改判定逻辑；计数须与
        # derive_eligible_hired_persons 一致）
        "per_person_eligibility": explain_per_person_eligibility(rule, project_inputs),
        "evidence_refs": benefit.evidence_refs,
    }
