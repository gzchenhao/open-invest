"""P4-1 Policy Match Engine (consumption layer).

回答：“这个项目与该政策的公开文本有哪些明确对应关系？”（建议，非资格认定）。

P4-0 locked conditions:
- 不 import/reuse agents.policy_ai_agent / crawlers。
- 不修改 real_policies.json / src.trust。
- 缺失数据 fail-closed: insufficient_evidence；严禁猜测、自动补全、LLM 臆测。
- Match 仅表达“基于公开政策证据的匹配建议”，不构成政府资格认定。
- 不实现 Benefit Calculation / Eligibility Pre-check（推迟 P4-2+）。

本模块只读取已存在的 Policy / Evidence；不调用 Trust、不写 REAL、不产生 VERIFIED。
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from global_policy_aggregator.matching.project_profile import ProjectProfile, _norm

SCHEMA_VERSION = "p4-1-policy-match-v1"
MATCH_ID_PREFIX = "match_"

_MODULE_DIR = Path(__file__).resolve().parent
REAL_POLICIES_PATH = _MODULE_DIR.parent / "data" / "real_policies" / "real_policies.json"
MATCH_RESULTS_PATH = _MODULE_DIR.parent / "data" / "match_results" / "match_results.jsonl"

MATCH_STATUS_MATCHED = "matched"
MATCH_STATUS_PARTIAL = "partial_match"
MATCH_STATUS_INSUFFICIENT = "insufficient_evidence"
MATCH_STATUS_NOT = "not_matched"

DISCLAIMER = (
    "该匹配结果仅基于公开政策信息，不构成政府资格认定或审批结果。"
)

# (dimension, policy_field) —— 仅比较 Policy 已结构化提供的字段
_STRUCTURED_DIMENSIONS = (
    ("industry", "industry"),
    ("region", "region"),
    ("type", "type"),
)


@dataclass
class EvidenceRef:
    """匹配判断追溯到 Policy Evidence 的引用。"""

    policy_id: Any
    field: str
    policy_value: Any
    quote: str
    source_url: Optional[str]
    policy_content_identity: Optional[str] = None
    snapshot_ref: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DimensionResult:
    dimension: str
    policy_value: Any
    project_value: Any
    evidence: Optional[EvidenceRef] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MatchResult:
    match_id: str
    project_profile_id: str
    policy_id: Any
    match_status: str
    matched_dimensions: List[DimensionResult] = field(default_factory=list)
    unmatched_dimensions: List[DimensionResult] = field(default_factory=list)
    unknown_dimensions: List[str] = field(default_factory=list)
    # 弱文本信号（topic/keyword 重叠）：证据绑定但非强匹配，不驱动 matched / 不压过明确冲突
    suggested_dimensions: List[DimensionResult] = field(default_factory=list)
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    explanation: str = ""
    score: Optional[float] = None
    created_at: Optional[str] = None
    policy_content_identity: Optional[str] = None
    source_url: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _policy_evidence(policy: Dict[str, Any], field_name: str, value: Any) -> EvidenceRef:
    return EvidenceRef(
        policy_id=policy.get("id"),
        field=field_name,
        policy_value=value,
        quote=str(value) if value is not None else "",
        source_url=policy.get("source_url"),
        policy_content_identity=policy.get("content_identity"),
        snapshot_ref=policy.get("snapshot_ref"),
    )


def _quote_in_text(needle: Optional[str], text: str, window: int = 40) -> str:
    if not needle or not text:
        return ""
    idx = text.lower().find(str(needle).lower())
    if idx < 0:
        return ""
    start = max(0, idx - window)
    end = min(len(text), idx + len(str(needle)) + window)
    return text[start:end]


def _cmp_dimension(
    profile_val: Any, policy_val: Any, dimension: str, policy: Dict[str, Any]
) -> str:
    """返回 'matched' / 'unmatched' / 'unknown'（仅基于明确值）。

    - policy 缺字段 -> unknown（无法判定）
    - project 缺字段 -> unknown（Unknown ≠ False）
    - G3: 语义上的缺失/未知哨兵（null/""/"unknown"/"unavailable"/…，见
      project_profile.MISSING_VALUE_SENTINELS）经 _norm 归一为 None，因此表现为
      「未知」：既不被当作具体值参与冲突，也不被当作通配符自动匹配。
    """
    pv = _norm(profile_val)
    cv = _norm(policy_val)
    if cv is None:
        return "unknown"
    if pv is None:
        return "unknown"
    if pv == cv:
        return "matched"
    return "unmatched"


def match_project_to_policy(profile: ProjectProfile, policy: Dict[str, Any]) -> MatchResult:
    """对单条 Policy 计算 MatchResult（fail-closed，证据绑定）。

    Semantic/topic similarity ≠ Policy applicability ≠ Eligibility。
    - matched_dimensions：仅结构化字段明确相等（industry/region/type 等同、funding 双方均有值）。
    - suggested_dimensions：弱文本信号（industry 关键词在政策文本出现），证据绑定但不构成强匹配，
      不驱动 matched、不被明确冲突覆盖。
    """
    matched: List[DimensionResult] = []
    unmatched: List[DimensionResult] = []
    unknown: List[str] = []
    suggested: List[DimensionResult] = []

    for dimension, pfield in _STRUCTURED_DIMENSIONS:
        profile_val = getattr(profile, dimension, None)
        policy_val = policy.get(pfield)
        status = _cmp_dimension(profile_val, policy_val, dimension, policy)
        if status == "unknown":
            unknown.append(dimension)
        elif status == "matched":
            matched.append(
                DimensionResult(dimension, policy_val, profile_val,
                                _policy_evidence(policy, pfield, policy_val))
            )
        else:  # unmatched = 明确冲突
            unmatched.append(
                DimensionResult(dimension, policy_val, profile_val,
                                _policy_evidence(policy, pfield, policy_val))
            )

    # funding：两者皆存在时为建议性匹配（无法可靠比较结构化阈值，不臆测具体金额）
    if profile.funding_need is not None and policy.get("amount") is not None:
        matched.append(
            DimensionResult("funding", policy.get("amount"), profile.funding_need,
                            _policy_evidence(policy, "amount", policy.get("amount")))
        )
    elif profile.funding_need is not None or policy.get("amount") is not None:
        unknown.append("funding")

    # 弱文本信号（证据绑定，非强匹配、非资格结论）：industry 关键词出现在政策文本中。
    # 仅进入 suggested_dimensions，不驱动 matched、不被明确冲突覆盖。
    if profile.industry and _norm(profile.industry) is not None:
        hay = " ".join(str(policy.get(k, "")) for k in ("title", "description", "details", "requirements"))
        q = _quote_in_text(profile.industry, hay)
        if q:
            suggested.append(
                DimensionResult(
                    "topic", profile.industry, profile.industry,
                    EvidenceRef(
                        policy_id=policy.get("id"),
                        field="topic",
                        policy_value=profile.industry,
                        quote=q,
                        source_url=policy.get("source_url"),
                        policy_content_identity=policy.get("content_identity"),
                        snapshot_ref=policy.get("snapshot_ref"),
                    ),
                )
            )

    # 状态判定（核心治理：insufficient_evidence ≠ not_matched）
    # - 强匹配（结构化字段相等）才驱动 matched
    # - 仅有 topic 弱信号且无强匹配 -> partial_match（建议性，非确认）
    # - 明确冲突（unmatched）且无强匹配 -> not_matched（topic 弱信号不覆盖冲突）
    has_strong = bool(matched)
    has_suggested = bool(suggested)
    if has_strong and not unmatched:
        status = MATCH_STATUS_MATCHED if not unknown else MATCH_STATUS_PARTIAL
    elif not has_strong and not unmatched:
        status = MATCH_STATUS_PARTIAL if has_suggested else MATCH_STATUS_INSUFFICIENT
    elif not has_strong and unmatched:
        status = MATCH_STATUS_NOT
    else:  # has_strong and unmatched -> 部分对齐但存在冲突
        status = MATCH_STATUS_PARTIAL

    # score 仅为排序/推荐信号；分母含 suggested 以削弱关键词重叠权重，分子仅计强匹配。
    denom = len(matched) + len(unmatched) + len(unknown) + len(suggested)
    score = (len(matched) / denom) if denom else None

    evidence_refs = [d.evidence for d in matched if d.evidence] + \
                    [d.evidence for d in suggested if d.evidence]

    explanation = _build_explanation(matched, unmatched, unknown, suggested)

    return MatchResult(
        match_id=f"{MATCH_ID_PREFIX}{uuid.uuid4().hex[:12]}",
        project_profile_id=profile.profile_id,
        policy_id=policy.get("id"),
        match_status=status,
        matched_dimensions=matched,
        unmatched_dimensions=unmatched,
        unknown_dimensions=unknown,
        suggested_dimensions=suggested,
        evidence_refs=evidence_refs,
        explanation=explanation,
        score=score,
        created_at=_now(),
        policy_content_identity=policy.get("content_identity"),
        source_url=policy.get("source_url"),
    )


def _build_explanation(
    matched: List[DimensionResult],
    unmatched: List[DimensionResult],
    unknown: List[str],
    suggested: List[DimensionResult],
) -> str:
    parts: List[str] = []
    for d in matched:
        if d.evidence:
            parts.append(
                f"匹配维度 {d.dimension}: 项目={d.project_value} / 政策={d.policy_value}；"
                f"证据 policy field '{d.evidence.field}'={d.evidence.quote!r} "
                f"来源 {d.evidence.source_url}"
            )
        else:
            parts.append(f"匹配维度 {d.dimension}: 项目={d.project_value} / 政策={d.policy_value}")
    for d in unmatched:
        parts.append(
            f"冲突维度 {d.dimension}: 项目={d.project_value} / 政策={d.policy_value}（明确不一致）"
        )
    if suggested:
        for d in suggested:
            parts.append(
                f"建议性文本信号 {d.dimension}: 关键词 '{d.project_value}' 出现在政策文本"
                f"（{d.evidence.quote!r} 来源 {d.evidence.source_url}）；"
                f"此为弱证据，不构成强匹配或资格依据"
            )
    if unknown:
        parts.append(
            "未知维度（政策未提供或项目未提供，无法判定，不等于不匹配）: " + ", ".join(unknown)
        )
    parts.append(DISCLAIMER)
    return "\n".join(parts)


def match_project_to_policies(
    profile: ProjectProfile, policies: List[Dict[str, Any]]
) -> List[MatchResult]:
    """对所有 Policy 计算 Match（按 score 降序；score=None 置后）。"""
    results = [match_project_to_policy(profile, p) for p in policies]
    results.sort(key=lambda r: (r.score is not None, r.score if r.score is not None else 0.0),
                 reverse=True)
    return results


class PolicyMatcher:
    """消费层匹配器：仅读取已存在的 Policy / Evidence。"""

    def __init__(self, policies: List[Dict[str, Any]]):
        self.policies = policies

    @classmethod
    def from_real_policies(cls, path: Any = None) -> "PolicyMatcher":
        p = Path(path or REAL_POLICIES_PATH)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("real_policies must be a JSON array")
        return cls(data)

    def match(self, profile: ProjectProfile) -> List[MatchResult]:
        return match_project_to_policies(profile, self.policies)


def save_match(result: MatchResult, path: Any = None) -> None:
    """持久化 Match 结果（append-only，独立于 Policy/Trust/Evidence 数据）。"""
    out = Path(path or MATCH_RESULTS_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", encoding="utf-8") as f:
        f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")


def load_matches(path: Any = None) -> List[Dict[str, Any]]:
    p = Path(path or MATCH_RESULTS_PATH)
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
