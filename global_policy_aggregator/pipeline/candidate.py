"""P3-2 Candidate + FieldEvidence dataclasses.

PARSE → NORMALIZE 阶段的中间产物。完全独立于
``global_policy_aggregator/data/real_policies/real_policies.json``（Portal 数据契约零接触）。

治理纪律（JUDGE 最终决策）：
- 每一条非 null 的「内容抽取」字段都必须携带 verbatim quote evidence（来自 snapshot）。
- 宁可 null，不要猜；industry/type 的分类结果允许为 ``unknown``（受控词表），不创建新 taxonomy。
- 不产生 VERIFIED；Candidate 恒为 ``is_mock=false, verification_status="unverified"``。
- contact 在 P3-2 第一版不自动抽取，恒为 null。
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

SCHEMA_VERSION = "ingestion-candidate-v1"
PARSER_VERSION = "p3-2-parser-v1"

# industry / type 是受控词表分类结果；当其值为 "unknown" 时属于合法判定，
# 不要求 quote（无原文可引）。其余内容抽取字段一律要求 quote。
CLASSIFICATION_FIELDS = ("industry", "type")


@dataclass
class FieldEvidence:
    """单字段的抽取证据。

    能回答两个问题：
    - 为什么这个值是真的？ → ``quote``（来自 snapshot 的原文片段）+ ``method``
    - 原网页具体哪一句？   → ``quote`` + ``char_span``（在 clean_text 中的起止偏移）
    """

    field_name: str
    value: object = None
    quote: Optional[str] = None          # verbatim 原文片段（不得改写）
    snapshot_ref: Optional[str] = None   # 对应 P3-1 snapshot 引用
    char_span: Optional[tuple] = None    # (start, end) 在 clean_text 中的偏移
    extracted_at: Optional[str] = None   # UTC ISO8601
    method: Optional[str] = None         # 抽取方法，如 "bs4_title" / "regex_amount"
    null_reason: Optional[str] = None    # 当 value 为 null 时的原因

    def is_present(self) -> bool:
        return self.value is not None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Provenance:
    """Candidate 的来源血缘（来自 P3-1 fetch + P3-2 parse）。"""

    source_url: str
    snapshot_ref: Optional[str] = None
    fetched_at: Optional[str] = None
    parser_version: str = PARSER_VERSION
    canonicalizer: str = "canonical_taxonomy-v1"


@dataclass
class Candidate:
    """归一化后的政策候选记录（P3-2 产物，等待 P3-3 validate / staging）。"""

    candidate_id: str
    schema_version: str = SCHEMA_VERSION
    pipeline_state: str = "normalized"          # parsed | normalized
    pipeline_history: List[dict] = field(default_factory=list)

    # ── 抽取字段 ─────────────────────────────────────────────
    title: Optional[str] = None
    source_url: str = ""
    description: Optional[str] = None
    source_organization: Optional[str] = None
    region: Optional[str] = None
    type: Optional[str] = None
    issue_date: Optional[str] = None
    valid_period: Optional[dict] = None         # {"start": ISO, "end": ISO}
    industry: Optional[str] = None              # canonical id 或 "unknown"
    amount: Optional[dict] = None               # {"raw_text", "normalized_number", "currency"}
    requirements: Optional[str] = None
    eligibility: Optional[str] = None
    contact: Optional[dict] = None              # P3-2 恒为 null

    # ── 治理字段 ─────────────────────────────────────────────
    provenance: Optional[Provenance] = None
    extracted_fields_evidence: Dict[str, FieldEvidence] = field(default_factory=dict)

    is_mock: bool = False
    verification_status: str = "unverified"     # 永不出现 "VERIFIED"

    def to_dict(self) -> dict:
        return asdict(self)

    def evidence_violations(self) -> List[str]:
        """返回证据违规项（供测试 / P3-3 校验）。

        - 内容抽取字段非 null 但缺 quote → 违规（CLASSIFICATION_FIELDS 豁免）。
        - contact 非 null → 违规（P3-2 禁止）。
        - verification_status == "VERIFIED" → 违规。
        """
        violations: List[str] = []
        for name, ev in self.extracted_fields_evidence.items():
            if name in CLASSIFICATION_FIELDS:
                continue
            if ev.value is not None and not ev.quote:
                violations.append(f"field '{name}' has value but no quote evidence")
        if self.contact is not None:
            violations.append("contact must be null in P3-2 (extraction deferred)")
        if self.verification_status == "VERIFIED":
            violations.append("verification_status must never be VERIFIED")
        return violations
