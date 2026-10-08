"""P6-4 A1 ROUND 1 — validator negative-test coverage (COMMITTED).

Scope: P3-3 validation fail-closed behaviour. Pure negative coverage; no
production code modified. File is intentionally named ``tests/test_p4_*`` to
escape the global ``.gitignore`` ``test_*.py`` trap (only ``tests/test_p4_*.py``
is re-included by the negation rule).
"""

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pytest

from global_policy_aggregator.pipeline.validator import (
    validate,
    promote_to_validated,
    STATUS_PASS,
    STATUS_REJECTED,
    STATUS_REVIEW,
)
from global_policy_aggregator.pipeline.states import InvalidTransitionError
from global_policy_aggregator.pipeline.fetcher import FetchResult, compute_content_hash
from global_policy_aggregator.pipeline.normalizer import run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[1]
FIX = REPO_ROOT / "tests" / "fixtures" / "pipeline"
VALID_URL = "https://www.gov.cn/zhengce/2026-03/01/content_p3_3.html"
EVIL_URL = "https://example.com/some/policy"


def _read(name):
    return (FIX / name).read_text(encoding="utf-8")


def _build(url, html, snapshots_dir):
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


def test_not_caught_by_gitignore_trap():
    """A1 test file must be a committed-test candidate (not ignored)."""
    import subprocess

    here = Path(__file__).resolve()
    r = subprocess.run(
        ["git", "check-ignore", str(here)],
        cwd=str(here.parents[1]), capture_output=True, text=True,
    )
    # returncode 1 == NOT ignored (trackable). 0 == ignored (trap!).
    assert r.returncode == 1, f"A1 validator test caught by .gitignore trap: {here}"


# 1. title 缺失 → REJECTED
def test_title_missing_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.title = None
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("title" in e for e in res.errors)


# 2. source_url scheme 非 http/https → REJECTED
def test_scheme_not_http_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.source_url = "ftp://gov.cn/policy"
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("scheme" in e for e in res.errors)


# 3. source_url domain 不在 allowlist → REJECTED
def test_domain_not_allowlisted_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.source_url = EVIL_URL
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("allowlist" in e for e in res.errors)


# 4. content_hash mismatch → REJECTED
def test_content_hash_mismatch_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    fr.content_hash = "0" * 64
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("content_hash mismatch" in e for e in res.errors)


# 5. snapshot path traversal → REJECTED (and no out-of-root read)
def test_snapshot_path_traversal_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.provenance.snapshot_ref = "snapshots/../../etc/passwd"
    res = validate(cand, snapshots_dir=sd)  # 走文件解析分支
    assert res.status == STATUS_REJECTED
    assert any("escapes snapshots root" in e for e in res.errors)


def test_absolute_snapshot_path_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.provenance.snapshot_ref = "/etc/passwd"
    res = validate(cand, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("escapes snapshots root" in e for e in res.errors)


# 6. verification_status != unverified → REJECTED
def test_verification_status_not_unverified_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.verification_status = "verified"
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("verification_status" in e for e in res.errors)


# 7. is_mock=True → REJECTED
def test_is_mock_true_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.is_mock = True
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("is_mock" in e for e in res.errors)


# 8a. NEED_HUMAN_REVIEW branch (no fetch_result) — not PASS, promote refused
def test_need_human_review_branch(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, snapshots_dir=sd)
    assert res.status == STATUS_REVIEW
    assert res.observed_content_hash is not None
    with pytest.raises(InvalidTransitionError):
        promote_to_validated(cand, res)
    assert cand.pipeline_state == "normalized"


# 8b. REJECTED branch — promote refused (BLOCKER 2)
def test_rejected_branch_and_promote_refused(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.title = None
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    with pytest.raises(InvalidTransitionError):
        promote_to_validated(cand, res)
    assert cand.pipeline_state == "normalized"


# 9. fail-closed: validator never raises on bad input; returns explicit REJECTED
def test_validator_never_raises_fail_closed(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.title = None
    cand.source_url = "ftp://x"
    cand.verification_status = "verified"
    cand.is_mock = True
    res = validate(cand, fr, snapshots_dir=sd)  # 绝不应抛异常
    assert res.status == STATUS_REJECTED
    assert len(res.errors) >= 4


# 10. illegal state jump (staged) → REJECTED
def test_invalid_state_jump_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.pipeline_state = "staged"
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("illegal state transition" in e for e in res.errors)
