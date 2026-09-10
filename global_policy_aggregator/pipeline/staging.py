"""P3-4 Staging v1 — VALIDATED → STAGED → HUMAN_APPROVED（受控推进 + 人审闸门）。

职责边界（JUDGE P3-4 最终决策）：
- 只实现 pipeline 侧 staging 推进；不实现 HUMAN_APPROVED → REAL（id 121+）。
- 绝不产生 VERIFIED；绝不写 real_policies.json；不调用 LLM；不启用 crawler。
- HUMAN_APPROVED ≠ VERIFIED：本模块的人审仅表示“人工批准该 Candidate 进入后续
  staging / ingestion 流程”，与 Trust 层官方核验 / VERIFIED 完全正交；
  verification_status 恒为 "unverified"。
- 复用 P3-1/P3-3 已有原语（compute_content_hash / resolve_snapshot_path / states），
  不修改 P3-1/P3-2/P3-3 任何文件。

Content-identity 防重放（DECISION 1）：
- promote_to_staged 必须绑定 ValidationResult 与当前 Candidate 的快照内容身份：
  重算 candidate.provenance.snapshot_ref 的 sha256，与 result.observed_content_hash 比对；
  不一致 / 无法确认 / None → fail-closed，不允许 STAGED。
- human_approve 同样要求 approval.content_identity 与当前 Candidate 内容身份一致。

Staging 持久化（DECISION 2）：
- 固定写入 data/raw_policies/staged/（gitignored runtime artifact），append-only JSONL；
- 不提供任意 output path 参数；绝不写入 real_policies.json。
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# 复用 P3-1 / P3-3 已有原语（不重复实现、不修改）：
from global_policy_aggregator.pipeline.fetcher import (
    compute_content_hash,
    DEFAULT_SNAPSHOTS_DIR,
)
from global_policy_aggregator.pipeline.validator import (
    ValidationResult,
    STATUS_PASS,
    resolve_snapshot_path,
)
from global_policy_aggregator.pipeline.candidate import Candidate
from global_policy_aggregator.pipeline.states import (
    PipelineState,
    try_transition,
    InvalidTransitionError,
)

# 固定 staging 目录（runtime artifact，gitignored，见 .gitignore）。
STAGED_DIR = DEFAULT_SNAPSHOTS_DIR.parent / "staged"

# 人审角色 allowlist（应用层权限边界标识，非身份鉴权；与 Trust HumanVerificationGate 无关）。
HUMAN_APPROVAL_ROLES = frozenset({
    "human_reviewer",
    "policy_editor",
    "compliance_officer",
})

STAGING_SCHEMA_VERSION = "pipeline-staging-v1"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_utc(value: Optional[str]):
    """宽松校验合法 UTC timestamp（必须带时区）。非法/缺失 → None。"""
    if not value:
        return None
    text = value
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt


def compute_candidate_content_identity(candidate: Candidate,
                                        snapshots_dir=None) -> Optional[str]:
    """从 Candidate 当前引用的 snapshot 重算内容身份（sha256）。

    复用 P3-3 resolve_snapshot_path（traversal-safe）+ P3-1 compute_content_hash。
    无法可靠确认（缺 provenance / snapshot_ref / 文件缺失 / 解析失败）→ 返回 None，
    调用方须 fail-closed（禁止旧 ValidationResult 重放到不同内容）。
    """
    prov = candidate.provenance
    if prov is None or not prov.snapshot_ref:
        return None
    snapshots_dir = snapshots_dir or DEFAULT_SNAPSHOTS_DIR
    try:
        p = resolve_snapshot_path(prov.snapshot_ref, snapshots_dir)
    except ValueError:
        return None
    if not p.exists():
        return None
    try:
        raw = p.read_bytes()
    except Exception:
        return None
    return compute_content_hash(raw)


def promote_to_staged(candidate: Candidate,
                      result: ValidationResult,
                      snapshots_dir=None) -> Candidate:
    """VALIDATED → STAGED（fail-closed）。

    条件：
    1) result 非 None 且 result.status == PASS；
    2) candidate 须处于 VALIDATED（由 try_transition 强制合法转移）；
    3) result.observed_content_hash 与当前 Candidate 快照内容身份一致（防旧 result 重放）。

    仅修改 pipeline_state + pipeline_history；不修改业务字段、不产生 VERIFIED。
    成功后 append-only 落盘 staging record。
    """
    if result is None or result.status != STATUS_PASS:
        raise InvalidTransitionError("cannot promote to staged without PASS validation")
    current_identity = compute_candidate_content_identity(candidate, snapshots_dir)
    if not current_identity or current_identity != result.observed_content_hash:
        raise InvalidTransitionError(
            "content identity mismatch: ValidationResult not bound to current Candidate snapshot"
        )
    cand = try_transition(candidate, PipelineState.STAGED.value)
    export_staged(cand, snapshots_dir=snapshots_dir)
    return cand


@dataclass
class HumanApproval:
    """人工批准记录（pipeline 就绪闸门，非 Trust 核验 / VERIFIED）。"""
    verifier_id: str
    verifier_role: str
    approval_evidence: str
    content_identity: str
    approved_at: str


def human_approve(candidate: Candidate,
                  approval: HumanApproval,
                  snapshots_dir=None) -> Candidate:
    """STAGED → HUMAN_APPROVED（fail-closed，必须显式人工审批）。

    任一条件不满足 → 拒绝；绝不可以通过空 approval / None / 字符串 / 默认值绕过。
    成功仅修改 pipeline_state + pipeline_history（追加人审事件）；
    不修改 verification_status（恒 "unverified"）、不生成 VERIFIED / contact。
    """
    if candidate.pipeline_state != PipelineState.STAGED.value:
        raise InvalidTransitionError("human approval requires STAGED state")
    if approval is None:
        raise InvalidTransitionError("human approval required (no approval provided)")
    if not approval.verifier_id or not approval.verifier_id.strip():
        raise InvalidTransitionError("approval verifier_id missing")
    if approval.verifier_role not in HUMAN_APPROVAL_ROLES:
        raise InvalidTransitionError("approval verifier_role not in allowlist")
    if not approval.approval_evidence or not approval.approval_evidence.strip():
        raise InvalidTransitionError("approval evidence missing")
    # 绑定 content identity：approval 必须对应当前 Candidate 快照内容身份
    current_identity = compute_candidate_content_identity(candidate, snapshots_dir)
    if not current_identity or current_identity != approval.content_identity:
        raise InvalidTransitionError("approval content_identity mismatch")
    if _parse_utc(approval.approved_at) is None:
        raise InvalidTransitionError("approval approved_at invalid UTC timestamp")
    if candidate.is_mock is not False:
        raise InvalidTransitionError("mock candidate cannot be human approved")
    if candidate.verification_status != "unverified":
        raise InvalidTransitionError("verification_status must remain unverified")

    cand = try_transition(candidate, PipelineState.HUMAN_APPROVED.value)
    cand.pipeline_history.append({
        "stage": "human_approval",
        "at": _utcnow(),
        "verifier_id": approval.verifier_id,
        "verifier_role": approval.verifier_role,
        "note": "human approved for staging/ingestion (NOT VERIFIED)",
    })
    export_staged(cand, approval=approval, snapshots_dir=snapshots_dir)
    return cand


def export_staged(candidate: Candidate,
                  approval: Optional[HumanApproval] = None,
                  snapshots_dir=None) -> Path:
    """Append-only 写 staging record 到固定 STAGED_DIR。返回写入的文件路径。

    固定目录、无 output path 参数；绝不写 real_policies.json。
    同一 candidate_id 多次写入只会追加新行，绝不覆盖已有 record。
    """
    STAGED_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": STAGING_SCHEMA_VERSION,
        "candidate_id": candidate.candidate_id,
        "pipeline_state": candidate.pipeline_state,
        "content_identity": compute_candidate_content_identity(candidate, snapshots_dir),
        "provenance_ref": candidate.provenance.snapshot_ref if candidate.provenance else None,
        "source_url": candidate.source_url,
        "title": candidate.title,
        "is_mock": candidate.is_mock,
        "verification_status": candidate.verification_status,
        "written_at": _utcnow(),
    }
    if approval is not None:
        record["approval"] = {
            "verifier_id": approval.verifier_id,
            "verifier_role": approval.verifier_role,
            "approval_evidence": approval.approval_evidence,
            "content_identity": approval.content_identity,
            "approved_at": approval.approved_at,
        }
    path = STAGED_DIR / f"{candidate.candidate_id}.jsonl"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return path
