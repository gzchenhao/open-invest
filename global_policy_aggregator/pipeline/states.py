"""P3-3 Pipeline State Machine（JUDGE 批准的状态枚举 + 转移守卫）。

设计纪律：
- 主链路：DISCOVERED → FETCHED → PARSED → NORMALIZED → VALIDATED →
  STAGED → HUMAN_APPROVED。外加 NEED_HUMAN_REVIEW / REJECTED 终止态。
- 禁止跳跃（如 NORMALIZED → STAGED）。
- 禁止任何自动 → REAL；HUMAN_APPROVED 只能由人工流程执行。
- VALIDATED ≠ VERIFIED；HUMAN_APPROVED ≠ 官方核验。
- 所有非法转移 fail-closed（can_transition 返回 False，try_transition 抛错）。
- P3-3 只负责把状态推到 VALIDATED；不执行 STAGED 及以后。
"""

from enum import Enum
from typing import Dict, FrozenSet


class PipelineState(str, Enum):
    DISCOVERED = "discovered"
    FETCHED = "fetched"
    PARSED = "parsed"
    NORMALIZED = "normalized"
    VALIDATED = "validated"
    STAGED = "staged"
    HUMAN_APPROVED = "human_approved"
    NEED_HUMAN_REVIEW = "need_human_review"
    REJECTED = "rejected"

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls._value2member_map_


# 主链路 + 人工复核/拒绝的允许转移表。fail-closed：未在表中的转移一律禁止。
_ALLOWED_TRANSITIONS: Dict[PipelineState, FrozenSet[PipelineState]] = {
    PipelineState.DISCOVERED: frozenset({PipelineState.FETCHED}),
    PipelineState.FETCHED: frozenset({PipelineState.PARSED}),
    PipelineState.PARSED: frozenset({PipelineState.NORMALIZED}),
    # P3-3 唯一允许执行的推进：NORMALIZED → VALIDATED
    PipelineState.NORMALIZED: frozenset({
        PipelineState.VALIDATED,
        PipelineState.NEED_HUMAN_REVIEW,
        PipelineState.REJECTED,
    }),
    PipelineState.VALIDATED: frozenset({
        PipelineState.STAGED,
        PipelineState.NEED_HUMAN_REVIEW,
        PipelineState.REJECTED,
    }),
    PipelineState.STAGED: frozenset({
        PipelineState.HUMAN_APPROVED,
        PipelineState.NEED_HUMAN_REVIEW,
        PipelineState.REJECTED,
    }),
    # HUMAN_APPROVED 只能由人工流程执行；代码侧只允许拒绝（如后续复核发现问题）
    PipelineState.HUMAN_APPROVED: frozenset({PipelineState.REJECTED}),
    PipelineState.NEED_HUMAN_REVIEW: frozenset({
        PipelineState.VALIDATED,
        PipelineState.REJECTED,
    }),
    PipelineState.REJECTED: frozenset(),
}


class InvalidTransitionError(Exception):
    """fail-closed：非法状态转移时抛出。"""


def can_transition(current: str, target: str) -> bool:
    """当前状态是否允许转移到 target（不抛错，返回布尔）。"""
    if not PipelineState.is_valid(current) or not PipelineState.is_valid(target):
        return False
    return PipelineState(target) in _ALLOWED_TRANSITIONS.get(PipelineState(current), frozenset())


def legal_targets(current: str) -> FrozenSet[str]:
    if not PipelineState.is_valid(current):
        return frozenset()
    return {s.value for s in _ALLOWED_TRANSITIONS.get(PipelineState(current), frozenset())}


def try_transition(candidate, target: str):
    """fail-closed 转移：非法则抛 InvalidTransitionError，合法则更新状态并追加 history。

    注意：P3-3 仅应把 target 用于 ``validated``；其余目标由后续阶段/人工流程负责。
    """
    if not can_transition(candidate.pipeline_state, target):
        raise InvalidTransitionError(
            f"illegal transition {candidate.pipeline_state} -> {target}"
        )
    candidate.pipeline_state = target
    candidate.pipeline_history.append({
        "stage": "transition",
        "at": _utcnow(),
        "note": f"{candidate.pipeline_state} -> {target}",
    })
    return candidate


def _utcnow() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
