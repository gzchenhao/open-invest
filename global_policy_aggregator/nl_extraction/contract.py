"""P4-21 — 最小 Fact Contract（REAL 122 唯一依据）。

以 REAL 122（39号通知 Context A 一次性扩岗补助）当前 ``eligibility_conditions`` 为
唯一事实来源。绝不加政策字段。

允许抽取的用户事实（仅 USER_PROVIDED）：
- project 级：applicant_entity_type
- aggregate 级：hired_persons（总招用人数）、user_stated_eligible_count（用户声称符合数）
- person 级：target_group / labor_contract_signed / employment_insurance_paid_months / hire_date

注意：
- execution_period 是 POLICY_PROVIDED（政策窗口 2026-01-01..2026-12-31），不是 LLM 抽取字段。
- eligible_hired_persons 是引擎派生值，绝不在 contract 中。
"""
from typing import Dict

# field -> {scope, type, required, desc}
ALLOWED_FIELDS: Dict[str, Dict] = {
    "applicant_entity_type": {
        "scope": "project", "type": str, "required": True,
        "desc": "申请/享受主体类型：企业/社会组织/个体工商户/...",
    },
    "hired_persons": {
        "scope": "aggregate", "type": int, "required": True,
        "desc": "用户明确提供的总招用人数（整数）",
    },
    "user_stated_eligible_count": {
        "scope": "aggregate", "type": int, "required": False,
        "desc": "用户声称已符合的人数；绝不直接当作 eligible_hired_persons",
    },
    "target_group": {
        "scope": "person", "type": str, "required": False,
        "desc": "招用对象枚举：grad_2026/leave_school_2y_unemployed/"
                "age_16_24_registered_unemployed",
    },
    "labor_contract_signed": {
        "scope": "person", "type": bool, "required": False,
        "desc": "是否签订劳动合同",
    },
    "employment_insurance_paid_months": {
        "scope": "person", "type": int, "required": False,
        "desc": "足额缴纳失业/工伤/职工养老月数（≥3）",
    },
    "hire_date": {
        "scope": "person", "type": str, "required": False,
        "desc": "招用日期 YYYY-MM-DD（用于 execution_period 判定）",
    },
}

# 一旦出现在抽取结果中即视为越权，必须 fail-closed 拒绝。
FORBIDDEN_FIELDS = frozenset({
    "eligible_hired_persons",
    "eligibility",
    "benefit",
    "benefit_amount",
    "verification_status",
    "verified",
    "trust_verified",
    "government_approved",
    "real_policy_id",
    "approved",
    "policy_truth",
    "pass",
    "fail",
    "unknown",
    "amount",
    "rule_type",
    "percentage",
})

SOURCE_REQUIRED = "user"
