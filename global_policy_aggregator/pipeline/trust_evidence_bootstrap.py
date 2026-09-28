"""P4-25 — Production Evidence Runtime Bootstrap (minimal, read-only loader).

职责（仅加载，不证明）：
- 从**持久化（durable）** 的 REAL 122 Policy Evidence 重建 Context A 的 Trust
  ``EvidenceObject``，语义与 P4-12F ``trust_handoff.register_evidence_object`` 一致；
- 注册到当前 runtime 的 ``TrustEvidenceService.evidence_graph``；
- 初始状态强制 ``UNVERIFIED``；
- 绝不创建任何 Verification Event，绝不调用 ``record_human_verification``；
- 绝不从 Event Log 合成 EvidenceObject（Event Log 只作 Verification Event 审计记录）。

安全边界（JUDGE 约束）：
- EvidenceObject 必须来自真实 durable Policy/Pipeline Evidence（REAL 122 的
  ``evidence_id`` + ``snapshot_ref``），不根据 ``verifier_id`` / ``event_id`` /
  ``verification_evidence`` / event timestamp 猜测；
- 加载与"证明 VERIFIED"是两个独立步骤；VERIFIED 仍由已有 Trust Gate
  （``check_verified_validity``）依据 Event Log / Authority / content identity / revocation
  派生。本模块不做任何 VERIFIED 判定。
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context A = REAL 122（生产一次性扩岗补助政策）。这是 durable 锚点，
# 与 P4-12F/G 的 evidence_id 一致，不从 Event Log 推测。
_CONTEXT_A_EVIDENCE_ID = "ev_1e2d555ae07193b5c257"

# Context B = REAL 122 稳岗返还（percentage_of_base）。使用既有 canonical
# context id（与 context_b_evidence.CONTEXT_B_ID 一致），禁止第二套命名。
# Context B 拥有**独立** evidence_id，绝不复用 Context A 的 ev_1e2d555…，
# 以此实现结构隔离（Option B：A/B 各自 evidence_id + verified_event_id）。
_CONTEXT_B_EVIDENCE_ID = "ev_ctx_122_stabilization_subsidy"
_CONTEXT_B_BINDING_KEY = "ctx_122_stabilization_subsidy"

# Context A 的新独立 evidence（P6-3.18 M1）：与 legacy ``ev_1e2d555…`` 及 B 的
# ``ev_ctx_122_stabilization_subsidy`` 均不同，从而实现结构隔离（Option B）。
# 其 canonical 字段与 legacy A / B 同源 REAL 122（snapshot_ref 等），仅 evidence_id
# 与 metadata.context_id 不同，故 ``compute_content_identity`` 产生独立且稳定的
# Trust Evidence CI，且 Event Log 中 Context A 的 verification event 只会落在此独立
# evidence 上，绝不再被 P6-3.5 遗留 ``70cdc162``（共享 ev_1e2d555…）污染 latest 选择。
_CONTEXT_A_NEW_EVIDENCE_ID = "ev_ctx_122_context_a"
_CONTEXT_A_BINDING_KEY = "context_a"

_DEFAULT_REAL_POLICIES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "global_policy_aggregator", "data", "real_policies", "real_policies.json",
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _find_context_a_record(real_policies_path: str) -> Optional[Dict[str, Any]]:
    """从 durable REAL 政策数据定位 Context A 记录（is_mock=False 且 evidence_id 匹配）。

    找不到（文件缺失 / 非列表 / 记录不存在）→ 返回 None（调用方必须 fail-closed）。
    """
    try:
        with open(real_policies_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if not isinstance(data, list):
        return None
    for rec in data:
        if rec.get("is_mock") is not False:
            continue
        if rec.get("evidence_id") == _CONTEXT_A_EVIDENCE_ID:
            return rec
    return None


def load_context_a_evidence(
    trust_service: Any,
    real_policies_path: Optional[str] = None,
) -> Dict[str, Any]:
    """把 Context A 的 durable Policy Evidence 重建为 EvidenceObject 并注册到运行时图。

    返回 {"success": bool, "evidence_id": str, ...}。

    任何 durable source 缺失 / 不完整 → 不创建 Evidence、不创建 Event，返回
    ``success=False``（fail-closed）。已加载则幂等跳过（支持 production entry
    每请求重建 trust_service）。
    """
    if trust_service is None:
        return {
            "success": False,
            "evidence_id": _CONTEXT_A_EVIDENCE_ID,
            "error": "no_trust_service",
            "verification_status": "UNVERIFIED",
            "message": "trust_service is None — cannot load evidence (fail-closed)",
        }

    # 1) 已加载则幂等跳过（同一 service 实例复用场景）
    try:
        existing = trust_service.get_evidence(_CONTEXT_A_EVIDENCE_ID)
        if existing.get("success"):
            return {
                "success": True,
                "evidence_id": _CONTEXT_A_EVIDENCE_ID,
                "already_loaded": True,
                "verification_status": existing.get("verification_status", "UNVERIFIED"),
                "message": "Context A evidence already present in runtime graph",
            }
    except Exception:
        pass

    # 2) 定位 durable source
    path = real_policies_path or _DEFAULT_REAL_POLICIES
    rec = _find_context_a_record(path)
    if rec is None:
        return {
            "success": False,
            "evidence_id": _CONTEXT_A_EVIDENCE_ID,
            "error": "context_a_source_not_found",
            "verification_status": "UNVERIFIED",
            "message": "Context A durable policy evidence not found (fail-closed)",
        }

    evidence_id = rec.get("evidence_id")
    snapshot_ref = rec.get("snapshot_ref")
    source_url = rec.get("source_url", "")
    policy_content_identity = rec.get("trust_content_identity") or rec.get("content_identity")
    candidate_id = rec.get("candidate_id")

    # 3) 校验 durable 字段（缺失即 fail-closed，绝不猜测/合成）
    if not evidence_id or not str(evidence_id).startswith("ev_"):
        return {
            "success": False,
            "evidence_id": evidence_id,
            "error": "missing_evidence_id",
            "verification_status": "UNVERIFIED",
            "message": "Context A record missing valid evidence_id (fail-closed)",
        }
    if not snapshot_ref or not str(snapshot_ref).strip():
        return {
            "success": False,
            "evidence_id": evidence_id,
            "error": "missing_snapshot_ref",
            "verification_status": "UNVERIFIED",
            "message": "Context A record missing snapshot_ref (fail-closed)",
        }

    # 4) 按 P4-12F register_evidence_object 语义重建
    #    （id 来自 snapshot content_identity 前缀；source=openinvest-pipeline；
    #     source_reference=snapshot_ref；verification_status 强制 UNVERIFIED）
    evidence_data: Dict[str, Any] = {
        "id": evidence_id,
        "type": "policy",
        "source": "openinvest-pipeline",
        "source_reference": snapshot_ref,
        "verification_status": "UNVERIFIED",
        "confidence_score": 0.0,
        "metadata": {
            "policy_content_identity": policy_content_identity,
            "snapshot_ref": snapshot_ref,
            "candidate_id": candidate_id,
            "source_url": source_url,
            "reconstructed_by": "P4-25 production evidence bootstrap",
            "reconstructed_at": _utcnow(),
            "bootstrap_source": "REAL_122_policy_evidence",
        },
    }

    # 5) 注册到运行时图（仅 create_evidence；不创建 Verification Event，不 VERIFIED）
    return trust_service.create_evidence(evidence_data)


def build_context_b_evidence_data(
    real_policies_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """构造 Context B 的 durable Policy Evidence 数据（与 load_context_a_evidence 同源 REAL 122）。

    返回 None（fail-closed）当 durable source 缺失 / 不完整。evidence 的 canonical
    字段（id/type/source/source_reference/confidence_score）与 Context A 仅 ``id`` 不同，
    因此 ``compute_content_identity`` 产生**独立且稳定**的 Trust Evidence CI，绝不混入
    policy snapshot CI（1e2d555…）。
    """
    path = real_policies_path or _DEFAULT_REAL_POLICIES
    rec = _find_context_a_record(path)
    if rec is None:
        return None
    snapshot_ref = rec.get("snapshot_ref")
    source_url = rec.get("source_url", "")
    policy_content_identity = rec.get("trust_content_identity") or rec.get("content_identity")
    candidate_id = rec.get("candidate_id")
    if not snapshot_ref or not str(snapshot_ref).strip():
        return None
    return {
        "id": _CONTEXT_B_EVIDENCE_ID,
        "type": "policy",
        "source": "openinvest-pipeline",
        "source_reference": snapshot_ref,
        "verification_status": "UNVERIFIED",
        "confidence_score": 0.0,
        "metadata": {
            "context_id": _CONTEXT_B_BINDING_KEY,
            "policy_content_identity": policy_content_identity,
            "snapshot_ref": snapshot_ref,
            "candidate_id": candidate_id,
            "source_url": source_url,
            "reconstructed_by": "P4-25 production evidence bootstrap (Context B)",
            "reconstructed_at": _utcnow(),
            "bootstrap_source": "REAL_122_policy_evidence_context_b",
        },
    }


def load_context_b_evidence(
    trust_service: Any,
    real_policies_path: Optional[str] = None,
) -> Dict[str, Any]:
    """把 Context B 的 durable Policy Evidence 重建为 EvidenceObject 并注册到运行时图。

    与 load_context_a_evidence 完全平行、彼此独立：使用**不同** evidence_id
    （``_CONTEXT_B_EVIDENCE_ID``），因此 Event Log 中 Context B 的 verification event
    只会落在 B 的 evidence 上，绝不会污染 Context A 的 latest 选择。

    幂等：已加载则跳过。任何 durable source 缺失 → 返回 success=False（fail-closed）。
    绝不创建 Verification Event，绝不调用 record_human_verification。
    """
    if trust_service is None:
        return {
            "success": False,
            "evidence_id": _CONTEXT_B_EVIDENCE_ID,
            "error": "no_trust_service",
            "verification_status": "UNVERIFIED",
            "message": "trust_service is None — cannot load Context B evidence (fail-closed)",
        }

    try:
        existing = trust_service.get_evidence(_CONTEXT_B_EVIDENCE_ID)
        if existing.get("success"):
            return {
                "success": True,
                "evidence_id": _CONTEXT_B_EVIDENCE_ID,
                "already_loaded": True,
                "verification_status": existing.get("verification_status", "UNVERIFIED"),
                "message": "Context B evidence already present in runtime graph",
            }
    except Exception:
        pass

    data = build_context_b_evidence_data(real_policies_path)
    if data is None:
        return {
            "success": False,
            "evidence_id": _CONTEXT_B_EVIDENCE_ID,
            "error": "context_b_source_not_found",
            "verification_status": "UNVERIFIED",
            "message": "Context B durable policy evidence not found (fail-closed)",
        }

    return trust_service.create_evidence(data)


def build_context_a_evidence_data(
    real_policies_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """构造 Context A 的**新独立** Evidence 数据（与 load_context_a_evidence / B 同源 REAL 122，
    按 P4-12F ``register_evidence_object`` 语义重建）。

    与 legacy ``ev_1e2d555…`` 的区别仅在于独立 evidence_id（``_CONTEXT_A_NEW_EVIDENCE_ID``）
    与 ``metadata.context_id="context_a"``，因此 ``compute_content_identity`` 产生**独立且稳定**
    的 Trust Evidence CI，且 Event Log 中 Context A 的 verification event 只会落在新的独立
    evidence 上，绝不会再被 P6-3.5 遗留的 ``70cdc162``（共享 ev_1e2d555…）污染 latest 选择。

    任何 durable source 缺失 / 不完整 → 返回 None（fail-closed），绝不合成 / 猜测。
    """
    path = real_policies_path or _DEFAULT_REAL_POLICIES
    rec = _find_context_a_record(path)
    if rec is None:
        return None
    snapshot_ref = rec.get("snapshot_ref")
    source_url = rec.get("source_url", "")
    policy_content_identity = rec.get("trust_content_identity") or rec.get("content_identity")
    candidate_id = rec.get("candidate_id")
    if not snapshot_ref or not str(snapshot_ref).strip():
        return None
    return {
        "id": _CONTEXT_A_NEW_EVIDENCE_ID,
        "type": "policy",
        "source": "openinvest-pipeline",
        "source_reference": snapshot_ref,
        "verification_status": "UNVERIFIED",
        "confidence_score": 0.0,
        "metadata": {
            "context_id": _CONTEXT_A_BINDING_KEY,
            "policy_content_identity": policy_content_identity,
            "snapshot_ref": snapshot_ref,
            "candidate_id": candidate_id,
            "source_url": source_url,
            "reconstructed_by": "P4-25 production evidence bootstrap (Context A new)",
            "reconstructed_at": _utcnow(),
            "bootstrap_source": "REAL_122_policy_evidence_context_a",
        },
    }


def load_context_a_new_evidence(
    trust_service: Any,
    real_policies_path: Optional[str] = None,
) -> Dict[str, Any]:
    """把 Context A 的**新独立** EvidenceObject 注册到运行时图。

    与 ``load_context_a_evidence``（legacy ev_1e2d555…）/ ``load_context_b_evidence``（B）
    三者并存、彼此 evidence_id 不同。幂等：已加载则跳过。任何 durable source 缺失 →
    返回 ``success=False``（fail-closed）。绝不创建 Verification Event，绝不调用
    ``record_human_verification``。
    """
    if trust_service is None:
        return {
            "success": False,
            "evidence_id": _CONTEXT_A_NEW_EVIDENCE_ID,
            "error": "no_trust_service",
            "verification_status": "UNVERIFIED",
            "message": "trust_service is None — cannot load Context A new evidence (fail-closed)",
        }
    try:
        existing = trust_service.get_evidence(_CONTEXT_A_NEW_EVIDENCE_ID)
        if existing.get("success"):
            return {
                "success": True,
                "evidence_id": _CONTEXT_A_NEW_EVIDENCE_ID,
                "already_loaded": True,
                "verification_status": existing.get("verification_status", "UNVERIFIED"),
                "message": "Context A new evidence already present in runtime graph",
            }
    except Exception:
        pass
    data = build_context_a_evidence_data(real_policies_path)
    if data is None:
        return {
            "success": False,
            "evidence_id": _CONTEXT_A_NEW_EVIDENCE_ID,
            "error": "context_a_source_not_found",
            "verification_status": "UNVERIFIED",
            "message": "Context A durable policy evidence not found (fail-closed)",
        }
    return trust_service.create_evidence(data)
