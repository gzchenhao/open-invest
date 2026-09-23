"""P4-2 First Pilot Runner — Operator Integration Tool.

本脚本是「运维集成入口」，串联完整 vertical slice：
  Official Snapshot → P3-2 Normalize → P3-3 Validate → P3-4 Staged/HumanApprove
  → P3-6 Trust Handoff → Trust Human Verification → P3-7 Production Gate → REAL 121+

治理边界：
- 本文件是 operator tool，**不是 pipeline 核心模块**；`real_ingestion.py` 仍 0 import src.trust。
- Trust 人审（VERIFIED）由真实 Human Verifier 通过本工具的 `record_human_verification`
  调用完成；生产 verifier 配置来自外部（authority_registry_config_path），
  **不得在本仓库内置任何生产审核人身份**。
- 仅用于第一条 pilot 演示；生产 REAL 121+ 写入受 P3-7 Gate + 101–120 冻结保护。
- 本工具不修改 src/trust/**，不自动编造 verifier，不自动 VERIFIED。

用法（示例）：
  python -m global_policy_aggregator.scripts.run_p4_pilot \
      --html tests/fixtures/policy_hightech_15pct.html \
      --source-url "https://www.gov.cn/.../qiye_income_tax.html" \
      --authority-config /tmp/dev_authorities.json \
      --event-log /tmp/trust_events.jsonl \
      --pipeline-approver "pilot-reviewer-001" \
      --trust-verifier-id "hr-001" --trust-verifier-role human_verifier \
      --verification-evidence "https://www.gov.cn/.../qiye_income_tax.html"
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

# 复用既有 pipeline 原语（不修改）
from global_policy_aggregator.pipeline.fetcher import compute_content_hash, DEFAULT_SNAPSHOTS_DIR, FetchResult
from global_policy_aggregator.pipeline.parser import parse_html
from global_policy_aggregator.pipeline.normalizer import normalize
from global_policy_aggregator.pipeline.validator import validate, STATUS_PASS, promote_to_validated
from global_policy_aggregator.pipeline.staging import (
    HumanApproval,
    promote_to_staged,
    human_approve,
)
from global_policy_aggregator.pipeline.trust_handoff import (
    create_verification_handoff,
    register_evidence_object,
)
from global_policy_aggregator.pipeline.real_ingestion import (
    PRODUCTION_REAL_POLICIES_PATH,
    ingest_verified_evidence,
)

SCHEMA_DIR = Path(__file__).resolve().parents[2]  # open-invest-protocol/


def _save_snapshot(html_bytes: bytes, source_url: str, snapshots_dir: Path) -> str:
    host = urlparse(source_url).netloc.lower().replace(":", "_")
    ci = compute_content_hash(html_bytes)
    ext = ".html"
    path = snapshots_dir / host / f"{ci}{ext}"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(html_bytes)
    return f"snapshots/{host}/{ci}{ext}", ci


def run(html_text: str, source_url: str, *,
        snapshots_dir: Path,
        real_policies_path: Path,
        authority_config: str,
        event_log: str,
        pipeline_approver: str,
        trust_verifier_id: str,
        trust_verifier_role: str,
        verification_evidence: str,
        audit_path=None,
        lock_path=None) -> dict:
    """执行完整 vertical slice，返回结果摘要。"""
    html_bytes = html_text.encode("utf-8")
    snapshot_ref, ci = _save_snapshot(html_bytes, source_url, snapshots_dir)

    # P3-2 Normalize
    parsed = parse_html(html_text, source_url, snapshot_ref)
    candidate = normalize(parsed, source_url, snapshot_ref,
                          fetched_at=_now())

    # P3-3 Validate（传入 FetchResult 以闭合 provenance / content_hash）
    fetch_result = FetchResult(
        url=source_url, status="ok", failure_type=None, http_status=200,
        attempts=1, source_id=None, retrieved_at=_now(), content_hash=ci,
        snapshot_ref=snapshot_ref, snapshot_deduped=False,
        size_bytes=len(html_bytes), error_message=None,
    )
    result = validate(candidate, fetch_result=fetch_result,
                      snapshot_bytes=html_bytes, snapshots_dir=snapshots_dir)
    if result.status != STATUS_PASS:
        raise RuntimeError(f"P3-3 validation not PASS: {result.status} {result.errors}")
    candidate = promote_to_validated(candidate, result)

    # P3-4 Staged + Human Approval（pipeline 侧人审闸门）
    candidate = promote_to_staged(candidate, result, snapshots_dir=snapshots_dir)
    approval = HumanApproval(
        verifier_id=pipeline_approver,
        verifier_role="human_reviewer",
        approval_evidence=f"pipeline human approval for {source_url}",
        content_identity=ci,
        approved_at=_now(),
    )
    candidate = human_approve(candidate, approval, snapshots_dir=snapshots_dir)

    # P3-6 Trust Handoff（注册 UNVERIFIED EvidenceObject）
    handoff = create_verification_handoff(candidate, approval, snapshots_dir=snapshots_dir)
    trust = _build_trust_service(authority_config, event_log)
    evidence_id = register_evidence_object(handoff, trust)
    if not evidence_id:
        raise RuntimeError("Trust handoff registration failed")

    # Trust Human Verification（真实 Human Verifier 授予 VERIFIED）
    vres = trust.record_human_verification(
        evidence_id=evidence_id,
        verifier_id=trust_verifier_id,
        verifier_role=trust_verifier_role,
        verification_evidence=[verification_evidence],
        notes=f"Human verification of {source_url}",
    )
    if not vres.get("success"):
        raise RuntimeError(f"Trust human verification failed: {vres}")

    # P3-7 Production Gate → REAL 121+
    new_id = ingest_verified_evidence(
        evidence_id, trust,
        real_policies_path=real_policies_path,
        snapshots_dir=snapshots_dir,
        audit_path=audit_path,
        lock_path=lock_path,
    )
    return {
        "new_real_id": new_id,
        "evidence_id": evidence_id,
        "verified_event_id": vres.get("event_id"),
        "content_identity": ci,
        "snapshot_ref": snapshot_ref,
        "verification_status": vres.get("verification_status"),
    }


def _build_trust_service(authority_config: str, event_log: str):
    """惰性导入 src.trust（仅本 operator 工具；pipeline 核心模块不依赖 src.trust）。"""
    src_dir = str(SCHEMA_DIR / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from trust.trust_service import TrustEvidenceService
    return TrustEvidenceService(
        event_log_path=event_log,
        authority_registry_config_path=authority_config,
    )


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def main(argv=None):
    ap = argparse.ArgumentParser(description="P4-2 First Pilot Runner")
    ap.add_argument("--html", required=True)
    ap.add_argument("--source-url", required=True)
    ap.add_argument("--authority-config", required=True,
                    help="DEV/TEST authority registry config (NOT a production verifier)")
    ap.add_argument("--event-log", required=True)
    ap.add_argument("--real-policies", default=str(PRODUCTION_REAL_POLICIES_PATH))
    ap.add_argument("--snapshots-dir", default=str(DEFAULT_SNAPSHOTS_DIR))
    ap.add_argument("--pipeline-approver", default="pilot-reviewer-001")
    ap.add_argument("--trust-verifier-id", required=True)
    ap.add_argument("--trust-verifier-role", default="human_verifier")
    ap.add_argument("--verification-evidence", dest="verification_evidence", required=True)
    args = ap.parse_args(argv)

    html_text = Path(args.html).read_text(encoding="utf-8")
    summary = run(
        html_text, args.source_url,
        snapshots_dir=Path(args.snapshots_dir),
        real_policies_path=Path(args.real_policies),
        authority_config=args.authority_config,
        event_log=args.event_log,
        pipeline_approver=args.pipeline_approver,
        trust_verifier_id=args.trust_verifier_id,
        trust_verifier_role=args.trust_verifier_role,
        verification_evidence=args.verification_evidence,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    main()
