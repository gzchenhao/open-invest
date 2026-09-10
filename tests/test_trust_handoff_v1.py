"""P3-6 Verification Handoff — 测试（JUDGE 批准范围）。

HUMAN_APPROVED → Trust EvidenceObject intake / registration。不实现 VERIFIED / REAL /
real_policies.json 写入 / 自动 human verification。所有用例真实执行，无 skip / xfail 掩盖。
staging 落盘一律重定向到 tmp（autouse fixture）。
"""

import inspect
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pytest

import global_policy_aggregator.pipeline.trust_handoff as trust_handoff
from global_policy_aggregator.pipeline.staging import (
    STAGED_DIR,
    HumanApproval,
    compute_candidate_content_identity,
    human_approve,
    promote_to_staged,
)
from global_policy_aggregator.pipeline.states import InvalidTransitionError
from global_policy_aggregator.pipeline.validator import (
    STATUS_PASS,
    promote_to_validated,
    resolve_snapshot_path,
    validate,
)
from global_policy_aggregator.pipeline.fetcher import FetchResult, compute_content_hash
from global_policy_aggregator.pipeline.normalizer import run_pipeline
from src.trust.trust_service import TrustEvidenceService

REPO_ROOT = Path(__file__).resolve().parents[1]
FIX = REPO_ROOT / "tests" / "fixtures" / "pipeline"
VALID_URL = "https://www.gov.cn/zhengce/2026-03/01/content_p3_3.html"
REAL_POLICIES = (
    REPO_ROOT / "global_policy_aggregator" / "data" / "real_policies" / "real_policies.json"
)


def _read(name):
    return (FIX / name).read_text(encoding="utf-8")


def _build(url, html, snapshots_dir: Path):
    """构造 Candidate + FetchResult，并把 snapshot 字节写入 snapshots_dir。"""
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    host = urlparse(url).netloc
    raw = html.encode("utf-8")
    ch = compute_content_hash(raw)
    snapshot_ref = f"snapshots/{host}/{ch}.html"
    (snapshots_dir / host).mkdir(parents=True, exist_ok=True)
    (snapshots_dir / host / f"{ch}.html").write_bytes(raw)
    cand = run_pipeline(html, url, snapshot_ref)
    fr = FetchResult(
        url=url, status="ok", failure_type=None, http_status=200,
        attempts=1, source_id="gov_cn_zhengceku",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        content_hash=ch, snapshot_ref=snapshot_ref, snapshot_deduped=False,
        size_bytes=len(raw), error_message=None,
    )
    return cand, fr


def _human_approved(tmp_path):
    """返回 (HUMAN_APPROVED candidate, approval, snapshots_dir)。"""
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS, res.errors
    promote_to_validated(cand, res)
    promote_to_staged(cand, res, snapshots_dir=sd)
    identity = compute_candidate_content_identity(cand, sd)
    approval = HumanApproval(
        verifier_id="rev-001",
        verifier_role="human_reviewer",
        approval_evidence="manual review ok",
        content_identity=identity,
        approved_at=datetime.now(timezone.utc).isoformat(),
    )
    human_approve(cand, approval, snapshots_dir=sd)
    assert cand.pipeline_state == "human_approved"
    return cand, approval, sd


class _StubTrust:
    """测试桩：仅实现 create_evidence；若被误调用 record_human_verification 则直接炸。"""

    def __init__(self):
        self.calls = []

    def create_evidence(self, evidence_data):
        self.calls.append(evidence_data)
        return {
            "success": True,
            "evidence_id": evidence_data.get("id"),
            "evidence_type": evidence_data.get("type"),
            "verification_status": evidence_data.get("verification_status"),
            "message": "stub",
        }

    def record_human_verification(self, *a, **k):
        raise AssertionError("adapter must NOT call record_human_verification()")


@pytest.fixture(autouse=True)
def _staged_tmp(tmp_path, monkeypatch):
    """所有 staging 落盘重定向到 tmp，避免污染 repo 与真实 staging 目录。"""
    monkeypatch.setattr(
        "global_policy_aggregator.pipeline.staging.STAGED_DIR", tmp_path / "staged"
    )


# ── 1. HUMAN_APPROVED → 成功 Handoff ───────────────────────────────────────
def test_human_approved_to_handoff_success(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    identity = approval.content_identity
    ho = trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)
    assert ho.handoff_status == "created"
    assert ho.content_identity == identity
    assert ho.candidate_id == cand.candidate_id
    assert ho.snapshot_ref == cand.provenance.snapshot_ref
    assert ho.human_approval["content_identity"] == identity


# ── 2. 非 HUMAN_APPROVED（VALIDATED）candidate 拒绝 ───────────────────────
def test_non_human_approved_validated_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS
    promote_to_validated(cand, res)
    identity = compute_candidate_content_identity(cand, sd)
    approval = HumanApproval(
        verifier_id="rev-001", verifier_role="human_reviewer",
        approval_evidence="x", content_identity=identity,
        approved_at=datetime.now(timezone.utc).isoformat(),
    )
    with pytest.raises(InvalidTransitionError):
        trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)


# ── 3. STAGED（未 human_approve）拒绝 ─────────────────────────────────────
def test_staged_not_human_approved_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    promote_to_validated(cand, res)
    promote_to_staged(cand, res, snapshots_dir=sd)
    assert cand.pipeline_state == "staged"
    approval = HumanApproval(
        verifier_id="rev-001", verifier_role="human_reviewer",
        approval_evidence="x", content_identity="x",
        approved_at=datetime.now(timezone.utc).isoformat(),
    )
    with pytest.raises(InvalidTransitionError):
        trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)


# ── 4. 缺失 HumanApproval 拒绝 ────────────────────────────────────────────
def test_missing_approval_rejected(tmp_path):
    cand, _approval, sd = _human_approved(tmp_path)
    with pytest.raises(InvalidTransitionError):
        trust_handoff.create_verification_handoff(cand, None, snapshots_dir=sd)


# ── 5. 缺失 approval content_identity 拒绝 ───────────────────────────────
def test_missing_approval_content_identity_rejected(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    bad = HumanApproval(
        verifier_id="rev-001", verifier_role="human_reviewer",
        approval_evidence="x", content_identity="",
        approved_at=datetime.now(timezone.utc).isoformat(),
    )
    with pytest.raises(InvalidTransitionError):
        trust_handoff.create_verification_handoff(cand, bad, snapshots_dir=sd)


# ── 6. snapshot 缺失拒绝 ──────────────────────────────────────────────────
def test_snapshot_missing_rejected(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    snap = resolve_snapshot_path(cand.provenance.snapshot_ref, sd)
    snap.unlink()
    with pytest.raises(InvalidTransitionError):
        trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)


# ── 7. snapshot 不可读（hash 无法计算）拒绝 ───────────────────────────────
def test_snapshot_unreadable_rejected(tmp_path, monkeypatch):
    cand, approval, sd = _human_approved(tmp_path)
    monkeypatch.setattr(
        trust_handoff, "compute_candidate_content_identity", lambda *a, **k: None
    )
    with pytest.raises(InvalidTransitionError):
        trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)


# ── 8. approval 后 snapshot 内容被篡改拒绝 ────────────────────────────────
def test_snapshot_changed_after_approval_rejected(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    snap = resolve_snapshot_path(cand.provenance.snapshot_ref, sd)
    snap.write_bytes(b"<html> tampered content </html>")
    with pytest.raises(InvalidTransitionError):
        trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)


# ── 9. 当前 hash != approval identity 拒绝 ───────────────────────────────
def test_current_hash_not_eq_approval_rejected(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    bad = HumanApproval(
        verifier_id="rev-001", verifier_role="human_reviewer",
        approval_evidence="x", content_identity="deadbeef" * 8,
        approved_at=datetime.now(timezone.utc).isoformat(),
    )
    with pytest.raises(InvalidTransitionError):
        trust_handoff.create_verification_handoff(cand, bad, snapshots_dir=sd)


# ── 10. Candidate 自带 identity 与该 snapshot 不符拒绝 ────────────────────
def test_candidate_identity_mismatch_rejected(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    cand.content_identity = "wrong-identity-value"
    with pytest.raises(InvalidTransitionError):
        trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)


# ── 11. EvidenceObject metadata 含 policy_content_identity ────────────────
def test_register_metadata_policy_content_identity(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    ho = trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)
    stub = _StubTrust()
    ev_id = trust_handoff.register_evidence_object(ho, stub)
    payload = stub.calls[0]
    assert payload["metadata"]["policy_content_identity"] == ho.content_identity
    assert ev_id == f"ev_{ho.content_identity[:20]}"


# ── 12. EvidenceObject source_reference 含 snapshot_ref ───────────────────
def test_register_source_reference_snapshot_ref(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    ho = trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)
    stub = _StubTrust()
    trust_handoff.register_evidence_object(ho, stub)
    assert stub.calls[0]["source_reference"] == ho.snapshot_ref
    assert stub.calls[0]["source_reference"] == cand.provenance.snapshot_ref


# ── 13. provenance 正确透传 ───────────────────────────────────────────────
def test_register_provenance_propagated(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    ho = trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)
    stub = _StubTrust()
    trust_handoff.register_evidence_object(ho, stub)
    prov = stub.calls[0]["metadata"]["provenance"]
    assert prov["source_url"] == cand.source_url
    assert prov["snapshot_ref"] == cand.provenance.snapshot_ref


# ── 14. extracted_field_evidence 正确透传 ─────────────────────────────────
def test_register_extracted_fields_propagated(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    ho = trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)
    stub = _StubTrust()
    trust_handoff.register_evidence_object(ho, stub)
    fields = stub.calls[0]["metadata"]["extracted_fields"]
    assert isinstance(fields, dict) and len(fields) > 0
    assert "title" in fields


# ── 15. handoff 绑定 candidate_id ────────────────────────────────────────
def test_handoff_binds_candidate_id(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    ho = trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)
    assert ho.candidate_id == cand.candidate_id


# ── 16. handoff 绑定 approval ────────────────────────────────────────────
def test_handoff_binds_approval(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    ho = trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)
    assert ho.human_approval["verifier_id"] == approval.verifier_id
    assert ho.human_approval["verifier_role"] == approval.verifier_role


# ── 17. adapter 绝不调用 record_human_verification() ──────────────────────
def test_adapter_not_call_record_human_verification(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    ho = trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)
    stub = _StubTrust()  # 若误调用 record_human_verification 会直接炸
    ev_id = trust_handoff.register_evidence_object(ho, stub)
    assert stub.calls[0]["verification_status"] == "UNVERIFIED"
    assert ev_id


# ── 18. 不产生 VERIFIED / REAL（真实 Trust 服务集成） ─────────────────────
def test_no_verified_produced(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    ho = trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)
    svc = TrustEvidenceService()  # 内存，无 event_log / 无 registry
    ev_id = trust_handoff.register_evidence_object(ho, svc)
    ev = svc.get_evidence(ev_id)
    assert ev["success"] is True
    assert ev["verification_status"] == "UNVERIFIED"
    assert cand.verification_status == "unverified"
    assert cand.pipeline_state == "human_approved"


# ── 19. 不产生 REAL / 状态不推进 ─────────────────────────────────────────
def test_no_real_promotion_and_state_unchanged(tmp_path):
    cand, approval, sd = _human_approved(tmp_path)
    ho = trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)
    trust_handoff.register_evidence_object(ho, _StubTrust())
    assert cand.pipeline_state == "human_approved"
    src = inspect.getsource(trust_handoff)
    assert "promote_to_real" not in src
    assert "trust_service.record_human_verification" not in src


# ── 20. 不写 real_policies.json ─────────────────────────────────────────
def test_no_real_policies_write(tmp_path):
    before = REAL_POLICIES.read_bytes()
    cand, approval, sd = _human_approved(tmp_path)
    ho = trust_handoff.create_verification_handoff(cand, approval, snapshots_dir=sd)
    trust_handoff.register_evidence_object(ho, _StubTrust())
    after = REAL_POLICIES.read_bytes()
    assert len(before) == len(after)
    assert before == after


# ── 21. src/trust/** 未被修改（相对 HEAD） ────────────────────────────────
def test_src_trust_unchanged():
    r = subprocess.run(
        ["git", "diff", "--quiet", "--", "src/trust"],
        cwd=str(REPO_ROOT), capture_output=True,
    )
    assert r.returncode == 0, "src/trust/** modified by P3-6"


# ── 22. 模块静态边界（无 VERIFIED 赋值 / 无 real_policies.json 引用） ─────
def test_module_boundary_static():
    src = inspect.getsource(trust_handoff)
    # 绝不 import / 调用 src.trust（含 record_human_verification）
    assert "src.trust" not in src
    assert "trust_service.record_human_verification" not in src
    # 不产生 REAL promotion / REAL PipelineState
    assert "promote_to_real" not in src
    # 不产生 VERIFIED（仅允许负向文档提及；不得有 VERIFIED 赋值 / 状态写入）
    assert 'verification_status="VERIFIED"' not in src
    assert "VerificationStatus.VERIFIED" not in src
    assert "verified_at" not in src
    assert "verification_decision" not in src
