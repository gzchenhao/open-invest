"""P3-4 Staging v1 — 测试（JUDGE 批准范围）。

不修改 P3-1/P3-2/P3-3；不写 real_policies.json；不调用 LLM；不启用 crawler。
所有用例真实执行，无 skip / xfail 掩盖。staging 落盘一律重定向到 tmp（autouse fixture）。
"""

import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import global_policy_aggregator.pipeline.staging as staging

from global_policy_aggregator.pipeline.candidate import Candidate
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
    export_staged,
    compute_candidate_content_identity,
    HUMAN_APPROVAL_ROLES,
    STAGED_DIR,
)
from global_policy_aggregator.pipeline.states import (
    can_transition,
    InvalidTransitionError,
)
from global_policy_aggregator.pipeline.fetcher import compute_content_hash, FetchResult
from global_policy_aggregator.pipeline.normalizer import run_pipeline

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


from urllib.parse import urlparse  # noqa: E402  (after _build reference)


def _validated(tmp_path):
    """返回 (VALIDATED candidate, PASS result, snapshots_dir)。"""
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS, res.errors
    promote_to_validated(cand, res)
    assert cand.pipeline_state == "validated"
    return cand, res, sd


@pytest.fixture(autouse=True)
def _staged_tmp(tmp_path, monkeypatch):
    """所有 staging 落盘重定向到 tmp，避免污染 repo 与真实 staging 目录。"""
    monkeypatch.setattr(
        "global_policy_aggregator.pipeline.staging.STAGED_DIR", tmp_path / "staged"
    )


# ── 1. VALIDATED + PASS → STAGED ────────────────────────────────────────
def test_validated_pass_to_staged(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    assert cand.pipeline_state == "staged"


# ── 2. 非 VALIDATED → STAGED 拒绝 ───────────────────────────────────────
def test_non_validated_to_staged_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS
    assert cand.pipeline_state == "normalized"
    with pytest.raises(InvalidTransitionError):
        promote_to_staged(cand, res, snapshots_dir=sd)
    assert cand.pipeline_state == "normalized"


# ── 3. REJECTED result → STAGED 拒绝 ────────────────────────────────────
def test_rejected_result_to_staged_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    cand.title = None
    bad = validate(cand, snapshots_dir=sd)
    assert bad.status == STATUS_REJECTED
    with pytest.raises(InvalidTransitionError):
        promote_to_staged(cand, bad, snapshots_dir=sd)
    assert cand.pipeline_state == "validated"


# ── 4. NEED_HUMAN_REVIEW result → STAGED 拒绝 ───────────────────────────
def test_review_result_to_staged_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    review = validate(cand, snapshots_dir=sd)  # 无 fetch_result → REVIEW
    assert review.status == STATUS_REVIEW
    with pytest.raises(InvalidTransitionError):
        promote_to_staged(cand, review, snapshots_dir=sd)
    assert cand.pipeline_state == "validated"


# ── 5. None result → STAGED 拒绝 ────────────────────────────────────────
def test_none_result_to_staged_rejected(tmp_path):
    cand, _res, sd = _validated(tmp_path)
    with pytest.raises(InvalidTransitionError):
        promote_to_staged(cand, None, snapshots_dir=sd)
    assert cand.pipeline_state == "validated"


# ── 6. 旧 ValidationResult / content identity mismatch → STAGED 拒绝 ─────
def test_stale_result_content_mismatch_to_staged_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    # 篡改磁盘 snapshot 内容（同 snapshot_ref），使 Candidate 当前内容身份变化
    host = urlparse(VALID_URL).netloc
    snap_path = sd / host / f"{res.observed_content_hash}.html"
    assert snap_path.exists()
    snap_path.write_bytes(b"<html>DIFFERENT CONTENT tampered qqq</html>")
    with pytest.raises(InvalidTransitionError):
        promote_to_staged(cand, res, snapshots_dir=sd)
    assert cand.pipeline_state == "validated"


# ── 7. 正确 content identity → STAGED 允许 ──────────────────────────────
def test_correct_content_identity_to_staged(tmp_path):
    cand, res, sd = _validated(tmp_path)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    assert ident == res.observed_content_hash
    promote_to_staged(cand, res, snapshots_dir=sd)
    assert cand.pipeline_state == "staged"


# ── 8. STAGED + 合法 approval → HUMAN_APPROVED ──────────────────────────
def test_staged_legal_approval_to_human_approved(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval(
        verifier_id="rev-001", verifier_role="human_reviewer",
        approval_evidence="manual review of snapshot + source",
        content_identity=ident, approved_at=_utc(),
    )
    human_approve(cand, approval, snapshots_dir=sd)
    assert cand.pipeline_state == "human_approved"


# ── 9. approval=None → 拒绝 ─────────────────────────────────────────────
def test_approval_none_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    with pytest.raises(InvalidTransitionError):
        human_approve(cand, None, snapshots_dir=sd)
    assert cand.pipeline_state == "staged"


# ── 10. verifier_id 缺失 → 拒绝 ─────────────────────────────────────────
def test_verifier_id_missing_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("", "human_reviewer", "ev", ident, _utc())
    with pytest.raises(InvalidTransitionError):
        human_approve(cand, approval, snapshots_dir=sd)


# ── 11. verifier_role 非 allowlist → 拒绝 ───────────────────────────────
def test_verifier_role_not_allowlist_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "bot", "ev", ident, _utc())
    with pytest.raises(InvalidTransitionError):
        human_approve(cand, approval, snapshots_dir=sd)


# ── 12. approval_evidence 缺失 → 拒绝 ───────────────────────────────────
def test_approval_evidence_missing_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "", ident, _utc())
    with pytest.raises(InvalidTransitionError):
        human_approve(cand, approval, snapshots_dir=sd)


# ── 13. content_identity mismatch → 拒绝 ────────────────────────────────
def test_content_identity_mismatch_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "ev", "wrong-hash", _utc())
    with pytest.raises(InvalidTransitionError):
        human_approve(cand, approval, snapshots_dir=sd)


# ── 14. approved_at 非法 → 拒绝 ──────────────────────────────────────────
def test_approved_at_invalid_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "ev", ident, "not-a-date")
    with pytest.raises(InvalidTransitionError):
        human_approve(cand, approval, snapshots_dir=sd)


# ── 15. MOCK candidate → 拒绝 ───────────────────────────────────────────
def test_mock_candidate_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    cand.is_mock = True
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "ev", ident, _utc())
    with pytest.raises(InvalidTransitionError):
        human_approve(cand, approval, snapshots_dir=sd)


# ── 16. verification_status != unverified → 拒绝 ────────────────────────
def test_verification_status_not_unverified_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    cand.verification_status = "verified"
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "ev", ident, _utc())
    with pytest.raises(InvalidTransitionError):
        human_approve(cand, approval, snapshots_dir=sd)


# ── 17. HUMAN_APPROVED 后 verification_status 仍为 unverified ────────────
def test_human_approved_stays_unverified(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "ev", ident, _utc())
    human_approve(cand, approval, snapshots_dir=sd)
    assert cand.verification_status == "unverified"


# ── 18. contact 仍为 null ───────────────────────────────────────────────
def test_contact_stays_null(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "ev", ident, _utc())
    human_approve(cand, approval, snapshots_dir=sd)
    assert cand.contact is None


# ── 19. 不存在 promote_to_real() ────────────────────────────────────────
def test_no_promote_to_real():
    import global_policy_aggregator.pipeline.staging as staging
    assert not hasattr(staging, "promote_to_real")


# ── 20. HUMAN_APPROVED → REAL transition 拒绝 ───────────────────────────
def test_human_approved_to_real_rejected(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "ev", ident, _utc())
    human_approve(cand, approval, snapshots_dir=sd)
    assert not can_transition("human_approved", "real")
    with pytest.raises(InvalidTransitionError):
        from global_policy_aggregator.pipeline.states import try_transition
        try_transition(cand, "real")


# ── 21. staging 不写 real_policies.json ─────────────────────────────────
def test_staging_does_not_write_real_policies(tmp_path):
    before = REAL_POLICIES.read_bytes()
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "ev", ident, _utc())
    human_approve(cand, approval, snapshots_dir=sd)
    after = REAL_POLICIES.read_bytes()
    assert before == after


# ── 22. 20 REAL IDs 仍为 101–120 ────────────────────────────────────────
def test_20_real_ids_intact():
    data = json.loads(REAL_POLICIES.read_text(encoding="utf-8"))
    ids = [p["id"] for p in data]
    assert ids == list(range(101, 121))
    assert all(p["verification_status"] == "unverified" for p in data)


# ── 23. staging append-only（不覆盖） ───────────────────────────────────
def test_staging_append_only(tmp_path):
    cand, res, sd = _validated(tmp_path)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "ev", ident, _utc())
    human_approve(cand, approval, snapshots_dir=sd)
    # 再次 export（模拟重复事件）
    export_staged(cand, snapshots_dir=sd)
    path = staging.STAGED_DIR / f"{cand.candidate_id}.jsonl"
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 3  # STAGED + HUMAN_APPROVED + 重复 export
    # 内容未被截断覆盖：首行仍是 STAGED 事件
    assert json.loads(lines[0])["pipeline_state"] == "staged"


# ── 24. 无覆盖已有 staging record（多次推进累计） ───────────────────────
def test_no_overwrite_existing_record(tmp_path):
    cand, res, sd = _validated(tmp_path)
    export_staged(cand, snapshots_dir=sd)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "ev", ident, _utc())
    human_approve(cand, approval, snapshots_dir=sd)
    path = staging.STAGED_DIR / f"{cand.candidate_id}.jsonl"
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 3
    assert json.loads(lines[-1])["pipeline_state"] == "human_approved"


# ── 25. 无任意 output path 写入能力 ─────────────────────────────────────
def test_no_arbitrary_output_path():
    sig = inspect.signature(export_staged)
    assert "staged_dir" not in sig.parameters
    assert "output_path" not in sig.parameters
    assert "path" not in sig.parameters


# ── 26. 无 LLM ──────────────────────────────────────────────────────────
def test_no_llm():
    src = Path(__file__).resolve().parents[1] / "global_policy_aggregator" / "pipeline" / "staging.py"
    import_lines = [ln for ln in src.read_text(encoding="utf-8").splitlines()
                    if ln.strip().startswith(("import ", "from "))]
    joined = " ".join(import_lines).lower()
    for banned in ("openai", "anthropic", "claude", "gpt"):
        assert banned not in joined, f"forbidden LLM import in staging.py: {banned}"


# ── 27. 无 crawler import ───────────────────────────────────────────────
def test_no_crawler_import():
    src = Path(__file__).resolve().parents[1] / "global_policy_aggregator" / "pipeline" / "staging.py"
    import_lines = [ln for ln in src.read_text(encoding="utf-8").splitlines()
                    if ln.strip().startswith(("import ", "from "))]
    joined = " ".join(import_lines).lower()
    assert "crawler" not in joined, "staging.py must not import crawlers"


# ── 28. history append-only ─────────────────────────────────────────────
def test_history_append_only(tmp_path):
    cand, res, sd = _validated(tmp_path)
    before = len(cand.pipeline_history)
    promote_to_staged(cand, res, snapshots_dir=sd)
    ident = compute_candidate_content_identity(cand, snapshots_dir=sd)
    approval = HumanApproval("rev-001", "human_reviewer", "ev", ident, _utc())
    human_approve(cand, approval, snapshots_dir=sd)
    assert len(cand.pipeline_history) >= before + 3  # validate→validated + staged + approval
    # 非法转移仍 fail-closed
    with pytest.raises(InvalidTransitionError):
        from global_policy_aggregator.pipeline.states import try_transition
        try_transition(cand, "real")


# ── 29. 非法 transition fail-closed ─────────────────────────────────────
def test_illegal_transition_fail_closed(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    # NORMALIZED → STAGED 直接跳变：状态机禁止
    assert not can_transition("normalized", "staged")
    with pytest.raises(InvalidTransitionError):
        promote_to_staged(cand, res, snapshots_dir=sd)
    # VALIDATED → HUMAN_APPROVED 跳过 STAGED：禁止
    promote_to_validated(cand, res)
    assert not can_transition("validated", "human_approved")
    with pytest.raises(InvalidTransitionError):
        human_approve(cand, HumanApproval("x", "human_reviewer", "e", "h", _utc()),
                     snapshots_dir=sd)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()
