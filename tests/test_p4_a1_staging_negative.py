"""P6-4 A1 ROUND 1 — staging negative-test coverage (COMMITTED).

Scope: P3-4 staging fail-closed behaviour. No production code modified.
Named ``tests/test_p4_*`` to escape the global ``.gitignore`` ``test_*.py`` trap.
All staging writes are redirected to tmp via the autouse fixture.
"""

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pytest

import global_policy_aggregator.pipeline.staging as staging
from global_policy_aggregator.pipeline.validator import (
    validate,
    promote_to_validated,
    STATUS_PASS,
    STATUS_REJECTED,
    STATUS_REVIEW,
)
from global_policy_aggregator.pipeline.staging import (
    promote_to_staged,
    human_approve,
    HumanApproval,
    compute_candidate_content_identity,
    STAGED_DIR,
)
from global_policy_aggregator.pipeline.states import can_transition, InvalidTransitionError
from global_policy_aggregator.pipeline.fetcher import compute_content_hash, FetchResult
from global_policy_aggregator.pipeline.normalizer import run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[1]
FIX = REPO_ROOT / "tests" / "fixtures" / "pipeline"
VALID_URL = "https://www.gov.cn/zhengce/2026-03/01/content_p3_3.html"


def _read(name):
    return (FIX / name).read_text(encoding="utf-8")


def _build(url, html, snapshots_dir):
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


def _validated(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS, res.errors
    promote_to_validated(cand, res)
    return cand, res, sd


def _utc():
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture(autouse=True)
def _staged_tmp(tmp_path, monkeypatch):
    """所有 staging 落盘重定向到 tmp，避免污染 repo / 真实 staging 目录。"""
    monkeypatch.setattr(staging, "STAGED_DIR", tmp_path / "staged")


def test_not_caught_by_gitignore_trap():
    import subprocess

    here = Path(__file__).resolve()
    r = subprocess.run(
        ["git", "check-ignore", str(here)],
        cwd=str(here.parents[1]), capture_output=True, text=True,
    )
    assert r.returncode == 1


# 1. promote_to_staged with non-PASS result → InvalidTransitionError
def test_promote_staged_none_result_rejected(tmp_path):
    cand, _res, sd = _validated(tmp_path)
    with pytest.raises(InvalidTransitionError):
        promote_to_staged(cand, None, snapshots_dir=sd)
    assert cand.pipeline_state == "validated"


def test_promote_staged_rejected_result_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    cand.title = None
    bad = validate(cand, snapshots_dir=sd)
    assert bad.status == STATUS_REJECTED
    with pytest.raises(InvalidTransitionError):
        promote_to_staged(cand, bad, snapshots_dir=sd)
    assert cand.pipeline_state == "validated"


def test_promote_staged_review_result_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    review = validate(cand, snapshots_dir=sd)
    assert review.status == STATUS_REVIEW
    with pytest.raises(InvalidTransitionError):
        promote_to_staged(cand, review, snapshots_dir=sd)
    assert cand.pipeline_state == "validated"


# 2. content_identity mismatch → InvalidTransitionError
def test_content_identity_mismatch_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    host = urlparse(VALID_URL).netloc
    snap = sd / host / f"{res.observed_content_hash}.html"
    snap.write_bytes(b"<html>tampered content qqq</html>")
    with pytest.raises(InvalidTransitionError):
        promote_to_staged(cand, res, snapshots_dir=sd)
    assert cand.pipeline_state == "validated"


# 3. human_approve missing approval (None) → InvalidTransitionError
def test_human_approve_none_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    with pytest.raises(InvalidTransitionError):
        human_approve(cand, None, snapshots_dir=sd)
    assert cand.pipeline_state == "staged"


# 4. verifier / role 不符合要求 → InvalidTransitionError
def test_verifier_id_missing_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    with pytest.raises(InvalidTransitionError):
        human_approve(
            cand, HumanApproval("", "human_reviewer", "ev", ident, _utc()),
            snapshots_dir=sd)


def test_verifier_role_not_allowlist_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    with pytest.raises(InvalidTransitionError):
        human_approve(
            cand, HumanApproval("rev-1", "bot", "ev", ident, _utc()),
            snapshots_dir=sd)


def test_approval_evidence_missing_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    with pytest.raises(InvalidTransitionError):
        human_approve(
            cand, HumanApproval("rev-1", "human_reviewer", "", ident, _utc()),
            snapshots_dir=sd)


# 5. is_mock=True → InvalidTransitionError
def test_mock_candidate_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    cand.is_mock = True
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    with pytest.raises(InvalidTransitionError):
        human_approve(
            cand, HumanApproval("rev-1", "human_reviewer", "ev", ident, _utc()),
            snapshots_dir=sd)


# 6. verification_status != unverified → InvalidTransitionError
def test_verification_status_not_unverified_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    cand.verification_status = "verified"
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    with pytest.raises(InvalidTransitionError):
        human_approve(
            cand, HumanApproval("rev-1", "human_reviewer", "ev", ident, _utc()),
            snapshots_dir=sd)


# 7. identity mismatch (approval.content_identity wrong) → InvalidTransitionError
def test_approval_identity_mismatch_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    with pytest.raises(InvalidTransitionError):
        human_approve(
            cand, HumanApproval("rev-1", "human_reviewer", "ev", "wrong-hash", _utc()),
            snapshots_dir=sd)


# 8. illegal state transition → InvalidTransitionError
def test_illegal_state_transition_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    # NORMALIZED → STAGED 跳变非法
    assert not can_transition("normalized", "staged")
    with pytest.raises(InvalidTransitionError):
        promote_to_staged(cand, res, snapshots_dir=sd)
    # VALIDATED → HUMAN_APPROVED 跳过 STAGED 非法
    promote_to_validated(cand, res)
    assert not can_transition("validated", "human_approved")
    with pytest.raises(InvalidTransitionError):
        human_approve(
            cand, HumanApproval("x", "human_reviewer", "e", "h", _utc()),
            snapshots_dir=sd)


# 9. fail-closed: human_approve on non-STAGED state raises
def test_human_approve_non_staged_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    # candidate 处于 VALIDATED，非 STAGED
    with pytest.raises(InvalidTransitionError):
        human_approve(
            cand, HumanApproval("x", "human_reviewer", "e", "h", _utc()),
            snapshots_dir=sd)


# 10. legal path still works (sanity anchor; stays unverified)
def test_legal_staged_to_human_approved(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    human_approve(
        cand, HumanApproval("rev-1", "human_reviewer", "ev", ident, _utc()),
        snapshots_dir=sd)
    assert cand.pipeline_state == "human_approved"
    assert cand.verification_status == "unverified"
