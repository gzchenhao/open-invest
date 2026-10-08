"""P6-4 A1 ROUND 1 — real_ingestion negative coverage (COMMITTED).

Scope: P3-7 Production Ingestion fail-closed Verification Gates. No production
code modified; real_policies.json is never written (writes go to a tmp copy
via the ``env`` fixture). Named ``tests/test_p4_*`` to escape the global
``.gitignore`` ``test_*.py`` trap.

Every negative case must raise IngestionRejected and must NOT mutate the
production real_policies.json. The ingestion consumes Trust-layer VERIFIED
evidence only; it must never call record_human_verification / grant VERIFIED.
"""

import json
from pathlib import Path

import pytest

from global_policy_aggregator.pipeline.fetcher import compute_content_hash
from global_policy_aggregator.pipeline.real_ingestion import (
    PRODUCTION_REAL_POLICIES_PATH,
    IngestionRejected,
    ingest_verified_evidence,
)


class FakeTrustService:
    """最小 read-only Trust 双（record_human_verification 显式禁止）。"""

    def __init__(self):
        self.evidence = {}
        self.validity = {}
        self.record_human_verification_called = False

    def get_evidence(self, evidence_id):
        ev = self.evidence.get(evidence_id)
        if ev is None:
            return {"success": False, "error": "not found"}
        return {"success": True, "evidence": ev}

    def check_verified_validity(self, evidence_id):
        v = self.validity.get(evidence_id)
        if v is None:
            return {"is_valid": False, "reasons": ["none"],
                    "latest_verified_event": None}
        return v

    def record_human_verification(self, *a, **k):
        self.record_human_verification_called = True
        raise AssertionError("real_ingestion must NOT call record_human_verification")


def make_evidence(eid, ci, ref, url, verified_event_id="evt-1",
                  verification_status="VERIFIED", is_mock_meta=False,
                  with_provenance=True):
    meta = {"policy_content_identity": ci, "snapshot_ref": ref,
            "candidate_id": "cand-" + eid, "source_url": url}
    if with_provenance:
        meta["provenance"] = {"snapshot_ref": ref, "source_url": url}
    if is_mock_meta:
        meta["is_mock"] = True
    return {"id": eid, "type": "policy", "source": "openinvest-pipeline",
            "source_reference": ref, "verification_status": verification_status,
            "confidence_score": 0.0, "metadata": meta}


def make_validity(is_valid=True, verified_event_id="evt-1", revoked=False):
    return {
        "is_valid": is_valid,
        "reasons": (["revoked"] if revoked
                    else ([] if is_valid else ["invalid"])),
        "latest_verified_event": (
            {"event_id": verified_event_id, "decision": "verified"}
            if is_valid else None),
    }


def write_snapshot(snapshots_dir, content=b"<html>policy text</html>"):
    host = "example.com"
    ci = compute_content_hash(content)
    p = snapshots_dir / host / f"{ci}.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return f"snapshots/{host}/{ci}.html", ci


@pytest.fixture
def env(tmp_path):
    real_copy = tmp_path / "real_policies.json"
    data = json.loads(PRODUCTION_REAL_POLICIES_PATH.read_text(encoding="utf-8"))
    # 隔离为 pre-ingestion 基线（仅 grandfather 101–120），不触碰生产文件
    data = [p for p in data if 101 <= p.get("id", 0) <= 120]
    real_copy.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()
    return {
        "real_policies_path": real_copy,
        "snapshots_dir": snapshots_dir,
        "audit_path": tmp_path / "ingestion_audit.jsonl",
        "lock_path": tmp_path / ".ingestion.lock",
    }


def _setup(trust, env, ci="<ci>", ref="snapshots/x/y.html",
           url="https://example.com/p1", verified_event_id="evt-1",
           verification_status="VERIFIED", is_mock_meta=False,
           with_provenance=True, validity_is_valid=True, revoked=False):
    trust.evidence["ev-1"] = make_evidence(
        "ev-1", ci, ref, url, verified_event_id=verified_event_id,
        verification_status=verification_status, is_mock_meta=is_mock_meta,
        with_provenance=with_provenance)
    trust.validity["ev-1"] = make_validity(
        is_valid=validity_is_valid, verified_event_id=verified_event_id,
        revoked=revoked)


def _assert_prod_untouched():
    data = json.loads(PRODUCTION_REAL_POLICIES_PATH.read_text(encoding="utf-8"))
    assert set(range(101, 121)).issubset({p["id"] for p in data})


def test_not_caught_by_gitignore_trap():
    import subprocess

    here = Path(__file__).resolve()
    r = subprocess.run(
        ["git", "check-ignore", str(here)],
        cwd=str(here.parents[1]), capture_output=True, text=True,
    )
    assert r.returncode == 1


# MOCK evidence → IngestionRejected
def test_mock_evidence_rejected(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, ci=ci, ref=ref, verification_status="MOCK")
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)
    _assert_prod_untouched()


# verification_status != VERIFIED → IngestionRejected
def test_not_verified_rejected(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, ci=ci, ref=ref, verification_status="UNVERIFIED")
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)
    _assert_prod_untouched()


# 小写 "verified" 亦被拒（fail-closed 区分大小写）
def test_verification_status_case_sensitive_rejected(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, ci=ci, ref=ref, verification_status="verified")
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)
    _assert_prod_untouched()


# revoked / invalid VERIFIED evidence → IngestionRejected
def test_invalid_validity_rejected(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, ci=ci, ref=ref, validity_is_valid=False)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)
    _assert_prod_untouched()


def test_revoked_evidence_rejected(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, ci=ci, ref=ref, validity_is_valid=False, revoked=True)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)
    _assert_prod_untouched()


# snapshot content hash mismatch → IngestionRejected
def test_snapshot_identity_mismatch_rejected(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, ci="deadbeef" * 8, ref=ref)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)
    _assert_prod_untouched()


def test_snapshot_replaced_after_verified_rejected(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"], content=b"<html>original</html>")
    _setup(trust, env, ci=ci, ref=ref)
    # VERIFIED 后同 snapshot 路径内容被替换
    p = env["snapshots_dir"] / "example.com" / f"{ci}.html"
    p.write_bytes(b"<html>replaced</html>")
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)
    _assert_prod_untouched()


# invalid source / identity mismatch (provenance missing)
def test_provenance_missing_rejected(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, ci=ci, ref=ref, with_provenance=False)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)
    _assert_prod_untouched()


def test_snapshot_ref_missing_rejected(env):
    trust = FakeTrustService()
    _setup(trust, env, ci="abc", ref="", with_provenance=False)
    trust.evidence["ev-1"]["metadata"].pop("snapshot_ref", None)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)
    _assert_prod_untouched()


# ingestion 不得调用 record_human_verification（不得授予 VERIFIED）
def test_no_record_human_verification_called(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, ci=ci, ref=ref, verification_status="MOCK")
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)
    assert trust.record_human_verification_called is False
    _assert_prod_untouched()
