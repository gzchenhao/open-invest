"""P4-1 Structured Project Profile (consumption layer).

P4-0 locked conditions:
- 仅使用用户明确提供的信息进行结构化；不得从 Policy 反向猜 Project 字段。
- 未提供字段保持 null（宁可 null，不要猜）。
- LLM（如使用）只允许 Natural Language -> Structured Profile，不得做资格判断。
  本模块提供确定性构建器；LLM 适配为可选外部适配器，核心不依赖 LLM、不做决策。
- 所有结构化字段保留 source text / extracted value / extraction method（evidence）。

本模块不 import src.trust / agents.policy_ai_agent / crawlers。
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

SCHEMA_VERSION = "p4-1-project-profile-v1"
PROFILE_ID_PREFIX = "proj_"

# 第一版允许显式结构化的字段；其余键落入 other_explicit_facts。
KNOWN_FIELDS = (
    "project_description",
    "industry",
    "region",
    "technology_stage",
    "company_type",
    "funding_need",
    "use_of_funds",
)

EXTRACTION_METHOD = "explicit_user_input"


@dataclass
class ProfileFieldEvidence:
    """单字段抽取证据（对应 P3 FieldEvidence 的轻量消费层版本）。

    回答：为什么这个值是真的？ -> source_text（用户输入原文片段）+ method。
    """

    field_name: str
    value: Any
    source_text: str
    method: str = EXTRACTION_METHOD
    extracted_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProjectProfile:
    profile_id: str
    schema_version: str = SCHEMA_VERSION
    source_text: str = ""
    project_description: Optional[str] = None
    industry: Optional[str] = None
    region: Optional[str] = None
    technology_stage: Optional[str] = None
    company_type: Optional[str] = None
    funding_need: Optional[float] = None
    use_of_funds: Optional[str] = None
    other_explicit_facts: Dict[str, Any] = field(default_factory=dict)
    extracted_fields_evidence: Dict[str, ProfileFieldEvidence] = field(default_factory=dict)
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# G3: 语义上代表「未知 / 缺失」的哨兵值（含 P3-2 extractor 产出的 "unknown"）。
# 治理纪律：unknown ≠ conflict；unknown ≠ automatic match（绝不作为通配符）。
# 这些值在匹配判断中一律按 fail-closed 处理为「无法判定（unknown）」。
MISSING_VALUE_SENTINELS = frozenset({
    "unknown", "unk", "unavailable", "unspecified", "not specified",
    "not_specified", "n/a", "na", "n.a.", "none", "null", "nil", "tbd",
    "未知", "不详", "待定", "未明确",
})


def _norm(v: Any) -> Any:
    """归一化用于宽松比较；非字符串原样返回（避免臆造）。

    G3: 缺失/未知哨兵（如 "unknown" / "unavailable"）归一为 None，
    使其在匹配中表现为「未知」而非具体值 —— 既不产生冲突、也不构成匹配。
    """
    if isinstance(v, str):
        s = v.strip().lower()
        return None if (not s or s in MISSING_VALUE_SENTINELS) else s
    return v


def _source_text_of(explicit: Dict[str, Any]) -> str:
    src = explicit.get("source_text")
    if isinstance(src, str) and src:
        return src
    try:
        return json.dumps(explicit, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(explicit)


def build_project_profile(input_data: Any) -> ProjectProfile:
    """从用户明确输入构建 Project Profile（确定性，不猜测）。

    Args:
        input_data:
            - dict: 显式字段（KNOWN_FIELDS + 任意 other_explicit_facts）。
            - str: 仅作为 project_description，结构化字段全部为 null。

    Returns:
        ProjectProfile（未提供字段保持 null）。
    """
    if isinstance(input_data, str):
        explicit: Dict[str, Any] = {"project_description": input_data}
        source_text = input_data
    elif isinstance(input_data, dict):
        explicit = dict(input_data)
        source_text = _source_text_of(explicit)
    else:
        raise TypeError("input_data must be str or dict")

    now = _now()
    profile = ProjectProfile(
        profile_id=f"{PROFILE_ID_PREFIX}{uuid.uuid4().hex[:12]}",
        source_text=source_text,
        created_at=now,
    )

    for f in KNOWN_FIELDS:
        if f in explicit and explicit[f] not in (None, ""):
            val = explicit[f]
            if f == "funding_need":
                try:
                    val = float(val)
                except (TypeError, ValueError):
                    # 无法可靠解析为金额 -> 不猜测，放入 other_explicit_facts
                    profile.other_explicit_facts[str(f)] = explicit[f]
                    continue
            setattr(profile, f, val)
            profile.extracted_fields_evidence[f] = ProfileFieldEvidence(
                field_name=f,
                value=val,
                source_text=str(explicit[f]),
                method=EXTRACTION_METHOD,
                extracted_at=now,
            )

    # 其余显式键 -> other_explicit_facts（保留但不臆造结构化维度）
    for k, v in explicit.items():
        if k in KNOWN_FIELDS or k == "source_text":
            continue
        if v not in (None, ""):
            profile.other_explicit_facts[k] = v

    return profile
