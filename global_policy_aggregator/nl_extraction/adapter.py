"""P4-21 — Extraction → Orchestrator 输入适配器（dict 路径，规避 P4-19 GAP-2）。

把 ``ExtractionResult`` 映射为现有 ``evaluate_project_against_policies`` 所需：
- project_profile（dict）：applicant_entity_type
- project_inputs（dict）：hired_persons（N 个空 dict，表示 N 人但无逐人明细）、
  user_stated_eligible_count（仅元数据，绝不变为 eligible_hired_persons）、
  可选的 per_person 事实（按 person_index 落位）

防御：任何禁止字段出现即 ``ForbiddenFieldError``（即使手工构造 ExtractionResult）。
Fail-closed：EXTRACTION_FAILED 状态不得送入执行链。
"""
from typing import Dict, List, Optional, Tuple

from .contract import FORBIDDEN_FIELDS
from .extractor import EXTRACTION_FAILED, EXTRACTION_OK, ExtractionResult


class ForbiddenFieldError(Exception):
    """抽取结果含越权字段，适配器拒绝送入执行链。"""


_PERSON_FIELDS = (
    "target_group", "labor_contract_signed",
    "employment_insurance_paid_months", "hire_date",
)


def to_orchestrator_inputs(result: ExtractionResult) -> Tuple[Dict, Dict]:
    """返回 (project_profile_dict, project_inputs_dict)。

    Args:
        result: 必须 status == EXTRACTION_OK。
    """
    if result.status == EXTRACTION_FAILED:
        raise ValueError("不能把失败抽取结果送入执行链（fail-closed）")
    if result.status != EXTRACTION_OK:
        raise ValueError(f"抽取状态非 ok：{result.status}")

    # 防御：任何禁止字段一律拒绝（深度防御）
    for fct in result.facts:
        if fct.field in FORBIDDEN_FIELDS:
            raise ForbiddenFieldError(f"禁止字段进入执行链：{fct.field}")

    profile: Dict = {}
    inputs: Dict = {}
    n = None
    for fct in result.facts:
        if fct.field == "hired_persons":
            n = fct.value
    persons: List[Dict] = [{} for _ in range(n)] if n is not None else []

    for fct in result.facts:
        if fct.field == "applicant_entity_type":
            profile["applicant_entity_type"] = fct.value
        elif fct.field == "hired_persons":
            inputs["hired_persons"] = persons
        elif fct.field == "user_stated_eligible_count":
            # 仅作用户声明元数据；绝不映射为 eligible_hired_persons
            inputs["user_stated_eligible_count"] = fct.value
        elif fct.field in _PERSON_FIELDS:
            idx = fct.person_index
            if isinstance(idx, int) and 0 <= idx < len(persons):
                persons[idx][fct.field] = fct.value
            # 无 person_index 的逐人事实在 MVP 不自动广播（避免错误归并），
            # 由上层 Missing Facts 追问层处理。
    return profile, inputs
