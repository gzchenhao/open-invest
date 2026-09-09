"""P3-3 Validation v1 — 测试（JUDGE 批准范围）。

不修改 P3-1/P3-2；不创建 VERIFIED；不写 real_policies.json；不调用 LLM。
所有用例真实执行，无 skip / xfail 掩盖。
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pytest

from global_policy_aggregator.pipeline.validator import (
    validate,
    promote_to_validated,
    try_transition,
    resolve_snapshot_path,
    ALLOWED_METHODS,
    STATUS_PASS,
    STATUS_REVIEW,
    STATUS_REJECTED,
)
from global_policy_aggregator.pipeline.states import (
    can_transition,
    PipelineState,
    InvalidTransitionError,
)
from global_policy_aggregator.pipeline.fetcher import FetchResult, compute_content_hash
from global_policy_aggregator.pipeline.normalizer import run_pipeline
from global_policy_aggregator.pipeline.candidate import FieldEvidence

REPO_ROOT = Path(__file__).resolve().parents[1]
FIX = REPO_ROOT / "tests" / "fixtures" / "pipeline"

VALID_URL = "https://www.gov.cn/zhengce/2026-03/01/content_p3_3.html"
EVIL_URL = "https://example.com/some/policy"


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


def _set_null(cand, name):
    setattr(cand, name, None)
    cand.extracted_fields_evidence[name] = FieldEvidence(
        field_name=name, value=None, null_reason="test_null"
    )


# ── 1. valid candidate → PASS + 合法推进 ──────────────────────────────
def test_valid_candidate_pass_and_transition(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS, res.errors
    assert cand.pipeline_state == "normalized"
    promote_to_validated(cand, res)
    assert cand.pipeline_state == "validated"


# ── 2. missing title → REJECTED ───────────────────────────────────────
def test_missing_title_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.title = None
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("title" in e for e in res.errors)


# ── 3. missing source_url → REJECTED ──────────────────────────────────
def test_missing_source_url_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.source_url = ""
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("source_url" in e for e in res.errors)


# ── 4. invalid URL scheme → REJECTED ──────────────────────────────────
def test_invalid_url_scheme_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.source_url = "ftp://gov.cn/policy"
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("scheme" in e for e in res.errors)


# ── 5. non-allowlisted URL → REJECTED ─────────────────────────────────
def test_non_allowlisted_url_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.source_url = EVIL_URL
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("allowlist" in e for e in res.errors)


# ── 6. snapshot missing → REJECTED ─────────────────────────────────────
def test_snapshot_missing_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    # 不写入 snapshot 文件：直接移除整个 snapshots 目录
    import shutil
    shutil.rmtree(sd, ignore_errors=True)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("snapshot file missing" in e for e in res.errors)


# ── 7. snapshot unreadable (目录占位) → REJECTED ───────────────────────
def test_snapshot_unreadable_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    path = resolve_snapshot_path(cand.provenance.snapshot_ref, sd)
    path.unlink()
    path.mkdir(parents=True, exist_ok=True)  # 用目录替换文件
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("unreadable" in e for e in res.errors)


# ── 8. missing evidence (非 null 无 quote) → REJECTED ──────────────────
def test_missing_evidence_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.extracted_fields_evidence["title"].quote = None
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("no quote" in e for e in res.errors)


# ── 9. quote mismatch → REJECTED ───────────────────────────────────────
def test_quote_mismatch_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.extracted_fields_evidence["title"].quote = "此句不可能出现在快照里xyz123"
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("quote not found" in e for e in res.errors)


# ── 10. char_span mismatch → REJECTED ─────────────────────────────────
def test_char_span_mismatch_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.extracted_fields_evidence["title"].char_span = (0, 3)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("char_span" in e for e in res.errors)


# ── 11. snapshot_ref mismatch → REJECTED ──────────────────────────────
def test_snapshot_ref_mismatch_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.extracted_fields_evidence["title"].snapshot_ref = "snapshots/other/x.html"
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("snapshot_ref mismatch" in e for e in res.errors)


# ── 12. FetchResult hash match → PASS ──────────────────────────────────
def test_fetch_hash_match_pass(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS
    assert res.observed_content_hash == fr.content_hash


# ── 13. FetchResult hash mismatch → REJECTED ──────────────────────────
def test_fetch_hash_mismatch_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    fr.content_hash = "0" * 64
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("content_hash mismatch" in e for e in res.errors)


# ── 14. no FetchResult → NEED_HUMAN_REVIEW ────────────────────────────
def test_no_fetch_result_needs_review(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, snapshots_dir=sd)  # 不传 fetch_result
    assert res.status == STATUS_REVIEW
    assert res.observed_content_hash is not None
    assert any("not fully closed" in w for w in res.warnings)


# ── 15. industry=unknown → PASS ────────────────────────────────────────
def test_industry_unknown_pass(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_industry_unknown.html"), sd)
    assert cand.industry == "unknown"
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS


# ── 16. type=unknown → PASS ────────────────────────────────────────────
def test_type_unknown_pass(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    ev = cand.extracted_fields_evidence["type"]
    ev.value = "unknown"
    ev.quote = None
    ev.char_span = None
    cand.type = "unknown"
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS


# ── 17. requirements=null → PASS ───────────────────────────────────────
def test_requirements_null_pass(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    _set_null(cand, "requirements")
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS


# ── 18. eligibility=null → PASS ────────────────────────────────────────
def test_eligibility_null_pass(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    _set_null(cand, "eligibility")
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS


# ── 19. contact non-null → REJECTED ───────────────────────────────────
def test_contact_non_null_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.contact = {"name": "x"}
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("contact must be null" in e for e in res.errors)


# ── 20. verification_status=verified → REJECTED ───────────────────────
def test_verification_status_verified_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.verification_status = "verified"
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("verification_status" in e for e in res.errors)


# ── 21. is_mock=true → REJECTED ────────────────────────────────────────
def test_is_mock_true_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.is_mock = True
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("is_mock" in e for e in res.errors)


# ── 22. invalid state jump (staged) → REJECTED ────────────────────────
def test_invalid_state_jump_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.pipeline_state = "staged"
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("illegal state transition" in e for e in res.errors)


# ── 23. pipeline_history append-only ───────────────────────────────────
def test_pipeline_history_append_only(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS, res.errors
    before = list(cand.pipeline_history)
    promote_to_validated(cand, res)
    assert len(cand.pipeline_history) == len(before) + 1
    assert cand.pipeline_history[:len(before)] == before


# ── 24. NORMALIZED 不能直接 STAGED ────────────────────────────────────
def test_normalized_cannot_become_staged(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    assert can_transition("normalized", "staged") is False
    with pytest.raises(InvalidTransitionError):
        try_transition(cand, "staged")


# ── 25. NORMALIZED 不能直接 HUMAN_APPROVED ────────────────────────────
def test_normalized_cannot_become_human_approved(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    assert can_transition("normalized", "human_approved") is False
    with pytest.raises(InvalidTransitionError):
        try_transition(cand, "human_approved")


# ── 26/27. real_policies.json 与 20 REAL 未被修改 ─────────────────────
def test_real_policies_20_real_intact():
    path = REPO_ROOT / "global_policy_aggregator" / "data" / "real_policies" / "real_policies.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 20
    ids = [r["id"] for r in data]
    assert ids == list(range(101, 121))
    for r in data:
        assert r.get("is_mock") is False
        assert r.get("verification_status") == "unverified"
    # 确认本测试未触碰文件（仅读取）
    assert path.exists()


# ── 28. 无 LLM / OpenAI / Claude ──────────────────────────────────────
def test_no_llm_calls():
    # 仅检测实际调用/依赖（openai/claude/anthropic/langchain/chatgpt/import llm），
    # 不误匹配 docstring 中的治理性否定声明（如“不调用 LLM”）。
    forbidden = ("openai", "claude", "anthropic", "langchain", "chatgpt", "import llm")
    for mod in ("validator.py", "states.py"):
        src = (REPO_ROOT / "global_policy_aggregator" / "pipeline" / mod).read_text(encoding="utf-8").lower()
        for tok in forbidden:
            assert tok not in src, f"{mod} 包含禁止 token: {tok}"


# ── 29. 不产生 VERIFIED ────────────────────────────────────────────────
def test_no_verified_generated(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status in (STATUS_PASS, STATUS_REVIEW, STATUS_REJECTED)
    assert "VERIFIED" not in res.status
    promote_to_validated(cand, res)
    assert cand.verification_status == "unverified"
    assert cand.pipeline_state == "validated"  # 不是 VERIFIED/human_approved


# ── 额外：structure_changed → NEED_HUMAN_REVIEW ───────────────────────
def test_structure_changed_needs_review(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_structure_changed.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REVIEW
    assert any("structure_changed" in w for w in res.warnings)


# ── 30. snapshot_ref 含 ../ → REJECTED，且不读取 root 外文件（BLOCKER 1） ──
def test_snapshot_path_traversal_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.provenance.snapshot_ref = "snapshots/../../etc/passwd"
    res = validate(cand, snapshots_dir=sd)  # 不传 fetch_result / snapshot_bytes → 走文件解析
    assert res.status == STATUS_REJECTED
    assert any("escapes snapshots root" in e for e in res.errors)


# ── 31. 绝对路径 snapshot_ref → REJECTED（BLOCKER 1） ────────────────────
def test_absolute_snapshot_path_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.provenance.snapshot_ref = "/etc/passwd"
    res = validate(cand, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("escapes snapshots root" in e for e in res.errors)


# ── 32. promote 在 REJECTED 下必须拒绝（BLOCKER 2） ──────────────────────
def test_promote_rejected_without_pass(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    cand.title = None  # 制造 REJECTED
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    with pytest.raises(InvalidTransitionError):
        promote_to_validated(cand, res)
    assert cand.pipeline_state == "normalized"  # 未被推进


# ── 33. promote 在 NEED_HUMAN_REVIEW 下必须拒绝（BLOCKER 2） ─────────────
def test_promote_human_review_without_pass(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, snapshots_dir=sd)  # 无 fetch_result → NEED_HUMAN_REVIEW
    assert res.status == STATUS_REVIEW
    with pytest.raises(InvalidTransitionError):
        promote_to_validated(cand, res)
    assert cand.pipeline_state == "normalized"


# ── 34. promote 在 PASS 下允许 NORMALIZED → VALIDATED ────────────────────
def test_promote_pass_allowed(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    res = validate(cand, fr, snapshots_dir=sd)
    assert res.status == STATUS_PASS
    promote_to_validated(cand, res)
    assert cand.pipeline_state == "validated"


# ── 35. snapshot_bytes 与磁盘 snapshot 冲突 → REJECTED（FINDING 3） ──────
def test_snapshot_source_conflict_rejected(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    # 提供与磁盘 snapshot 内容不同的 bytes，保留同一 snapshot_ref
    snapshot_bytes = b"<html>CONFLICTING BYTES NOT IN DISK SNAPSHOT qqq</html>"
    res = validate(cand, snapshot_bytes=snapshot_bytes, snapshots_dir=sd)
    assert res.status == STATUS_REJECTED
    assert any("snapshot source conflict" in e for e in res.errors)


# ── 36. snapshot_bytes 与磁盘 snapshot 内容一致 → 不因 conflict 拒绝 ─────
def test_snapshot_source_same_content_allowed(tmp_path):
    sd = tmp_path / "snapshots"
    cand, fr = _build(VALID_URL, _read("fixture_normal.html"), sd)
    html = _read("fixture_normal.html").encode("utf-8")
    res = validate(cand, fr, snapshot_bytes=html, snapshots_dir=sd)
    assert res.status == STATUS_PASS
    assert not any("snapshot source conflict" in e for e in res.errors)
