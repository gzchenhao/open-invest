"""P3-6 Verification Handoff — HUMAN_APPROVED → Trust EvidenceObject intake (registration only).

JUDGE 边界（P3-6 DESIGN REFINEMENT / IMPLEMENTATION AUTHORIZATION）：
- 只实现 Pipeline 侧 verification handoff 与 Trust intake 注册。
- **绝对禁止** import 或调用 ``src/trust/trust_service.py`` 中的
  ``record_human_verification()``；本模块不得产生 VERIFIED，不得写
  ``real_policies.json``，不得做 REAL promotion，不得新增 REAL PipelineState，
  不得自动 human verification / contact extraction / crawler / LLM。
- 仅将「待验证」Evidence 注册到 Trust（通过调用方注入的 ``trust_service.create_evidence``），
  Pipeline 侧 cross-layer identity（snapshot sha256）以 metadata 透传：
  ``metadata["policy_content_identity"]`` + ``metadata["snapshot_ref"]``。
- 不修改 ``states.py``；``HUMAN_APPROVED`` 仍是 pipeline readiness 终点。
- 不修改 ``src/trust/**``；Trust ownership（Human Verifier → Trust Gate → VERIFIED）不受影响。

Content identity（跨层锚点）：快照字节 sha256（P3-1 ``compute_content_hash``）。
Handoff 时实时重算并与 ``HumanApproval.content_identity`` 比对，一致才放行；
snapshot 缺失 / 不可读 / hash 无法计算 / identity 缺失 / 不匹配 → FAIL CLOSED。
"""

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# 复用 P3-3 / P3-4 已有原语（不重复实现、不修改）：
from global_policy_aggregator.pipeline.staging import (
    HumanApproval,
    compute_candidate_content_identity,
)
from global_policy_aggregator.pipeline.states import (
    InvalidTransitionError,
    PipelineState,
)

HANDOFF_SCHEMA_VERSION = "pipeline-verification-handoff-v1"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class VerificationHandoff:
    """HUMAN_APPROVED Candidate → Trust 待验证 Evidence 的跨层数据产物。

    不是新的 Pipeline lifecycle state；是 verification request / handoff artifact。
    所有关键身份字段必须可追溯到当前 Candidate / 当前 snapshot。
    """

    handoff_id: str
    candidate_id: str
    content_identity: str
    source_url: str
    snapshot_ref: str
    provenance: Dict[str, Any]
    extracted_field_evidence: Dict[str, Any]
    staging_ref: str
    human_approval: Dict[str, Any]
    created_at: str
    handoff_status: str = "created"            # created | registered
    target_evidence_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _provenance_dict(candidate: Any) -> Dict[str, Any]:
    prov = candidate.provenance
    if prov is None:
        return {}
    return asdict(prov)


def create_verification_handoff(
    candidate: Any,
    approval: HumanApproval,
    snapshots_dir=None,
) -> VerificationHandoff:
    """HUMAN_APPROVED → VerificationHandoff（fail-closed，stale-approval 防护）。

    条件：
    1) candidate 处于 HUMAN_APPROVED；
    2) approval 非 None 且 approval.content_identity 非空；
    3) 实时重算当前 snapshot 内容身份：
       - 无法确认（缺 provenance / snapshot_ref / 文件缺失 / 读取异常）→ None → fail-closed；
       - 与 approval.content_identity 不一致 → fail-closed（防 stale / 篡改后重放）；
       - 若 Candidate 自带 content_identity（未来字段）且与当前不一致 → fail-closed。

    返回 Handoff（handoff_status="created"）；不调用 Trust、不产生 VERIFIED。
    """
    if candidate.pipeline_state != PipelineState.HUMAN_APPROVED.value:
        raise InvalidTransitionError(
            "verification handoff requires HUMAN_APPROVED pipeline state")
    if approval is None:
        raise InvalidTransitionError("human approval required for verification handoff")
    if not approval.content_identity or not approval.content_identity.strip():
        raise InvalidTransitionError("approval content_identity missing")

    current_identity = compute_candidate_content_identity(candidate, snapshots_dir)
    if not current_identity:
        raise InvalidTransitionError(
            "cannot confirm current candidate content identity "
            "(snapshot missing / unreadable / hash undecidable)")
    if current_identity != approval.content_identity:
        raise InvalidTransitionError(
            "stale approval: current snapshot identity != approval.content_identity")
    cand_identity = getattr(candidate, "content_identity", None)
    if cand_identity and cand_identity != current_identity:
        raise InvalidTransitionError(
            "content identity mismatch: candidate.content_identity != current snapshot")

    snapshot_ref = (
        candidate.provenance.snapshot_ref if candidate.provenance else None
    ) or ""
    return VerificationHandoff(
        handoff_id=f"ho_{uuid.uuid4().hex}",
        candidate_id=candidate.candidate_id,
        content_identity=current_identity,
        source_url=candidate.source_url or "",
        snapshot_ref=snapshot_ref,
        provenance=_provenance_dict(candidate),
        extracted_field_evidence={
            k: (v.to_dict() if hasattr(v, "to_dict") else v)
            for k, v in candidate.extracted_fields_evidence.items()
        },
        staging_ref=candidate.candidate_id,
        human_approval=asdict(approval),
        created_at=_utcnow(),
        handoff_status="created",
        target_evidence_id=None,
    )


def register_evidence_object(handoff: VerificationHandoff, trust_service: Any) -> str:
    """将待验证 Evidence 注册到 Trust（intake only）。

    只调用 ``trust_service.create_evidence(evidence_data)``；**绝不**调用
    ``record_human_verification()``，绝不产生 VERIFIED / REAL。

    ``trust_service`` 由调用方注入（真实 ``TrustEvidenceService`` 或测试桩），
    本模块不 import ``src/trust``，以保持 Trust ownership 边界。

    EvidenceObject 的 metadata 透传跨层身份锚点：
    - ``metadata["policy_content_identity"]`` = 当前 Pipeline snapshot SHA256
    - ``metadata["snapshot_ref"]`` = 当前 snapshot_ref
    - 附带 provenance / extracted_fields / human_approval（仅作待验证证据，非验证结论）

    verification_status 强制为 ``"UNVERIFIED"``（非 VERIFIED / 非 MOCK）。
    """
    if handoff.handoff_status != "created":
        raise InvalidTransitionError("handoff already registered or invalid status")

    evidence_id = f"ev_{handoff.content_identity[:20]}"
    evidence_data: Dict[str, Any] = {
        "id": evidence_id,
        "type": "policy",
        "source": "openinvest-pipeline",
        "source_reference": handoff.snapshot_ref,
        "verification_status": "UNVERIFIED",
        "confidence_score": 0.0,
        "metadata": {
            "policy_content_identity": handoff.content_identity,
            "snapshot_ref": handoff.snapshot_ref,
            "candidate_id": handoff.candidate_id,
            "source_url": handoff.source_url,
            "handoff_id": handoff.handoff_id,
            "provenance": handoff.provenance,
            "extracted_fields": handoff.extracted_field_evidence,
            "human_approval": handoff.human_approval,
            "handoff_created_at": handoff.created_at,
        },
    }
    result = trust_service.create_evidence(evidence_data)
    if not result.get("success"):
        raise RuntimeError(
            f"trust intake failed: {result.get('error')} "
            f"(verification handoff NOT promoted to VERIFIED)")
    handoff.target_evidence_id = evidence_id
    handoff.handoff_status = "registered"
    return evidence_id
