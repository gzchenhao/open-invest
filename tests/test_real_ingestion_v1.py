"""P3-7 Production Ingestion 专项测试（READ-ONLY Trust API；FAIL-CLOSED 全覆盖）。

覆盖：
- Verification Gate 1–10 失败路径
- Duplicate Rule A/B/C/D
- ID >= 121 / 101–120 保护
- 并发 ID allocation race（无重复 ID）
- atomic write 失败保护
- 不调用 record_human_verification / 不产生 verification_status="verified"
- src/trust 0 修改（静态）

所有测试使用临时 dataset / 临时 snapshot，绝不触碰生产 real_policies.json。
"""

import json
import os
import threading

import pytest

from global_policy_aggregator.pipeline.fetcher import compute_content_hash
from global_policy_aggregator.pipeline.real_ingestion import (
    PRODUCTION_REAL_POLICIES_PATH,
    IngestionRejected,
    ingest_verified_evidence,
    record_revoked_after_ingest,
)


# ---------------------------------------------------------------------------
# Fake Trust service（仅 read-only；record_human_verification 显式禁止）
# ---------------------------------------------------------------------------

class FakeTrustService:
    def __init__(self):
        self.evidence = {}
        self.validity = {}
        self.record_human_verification_called = False

    def get_evidence(self, evidence_id):
        ev = self.evidence.get(evidence_id)
        if ev is None:
            return {"success": False, "error": "Evidence not found"}
        return {"success": True, "evidence": ev}

    def check_verified_validity(self, evidence_id):
        v = self.validity.get(evidence_id)
        if v is None:
            return {"is_valid": False, "reasons": ["no validity"],
                    "latest_verified_event": None}
        return v

    def get_verification_history(self, evidence_id):
        return {"success": True, "event_count": 0, "events": []}

    def record_human_verification(self, *args, **kwargs):
        # P3-7 绝不调用；若被调用立即暴露。
        self.record_human_verification_called = True
        raise AssertionError("P3-7 must NOT call record_human_verification()")


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def make_evidence(evidence_id, content_identity, snapshot_ref, source_url,
                  verified_event_id="evt-1", verification_status="VERIFIED",
                  is_mock_meta=False, with_provenance=True):
    meta = {
        "policy_content_identity": content_identity,
        "snapshot_ref": snapshot_ref,
        "candidate_id": "cand-" + evidence_id,
        "source_url": source_url,
    }
    if with_provenance:
        meta["provenance"] = {"snapshot_ref": snapshot_ref, "source_url": source_url}
    if is_mock_meta:
        meta["is_mock"] = True
    return {
        "id": evidence_id,
        "type": "policy",
        "source": "openinvest-pipeline",
        "source_reference": snapshot_ref,
        "verification_status": verification_status,
        "confidence_score": 0.0,
        "metadata": meta,
    }


def make_validity(is_valid=True, verified_event_id="evt-1", revoked=False):
    return {
        "is_valid": is_valid,
        "reasons": (["revoked after verified"] if revoked
                    else ([] if is_valid else ["not valid"])),
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


def seed_extra(real_policies_path, rid, content_identity, source_url):
    data = json.loads(real_policies_path.read_text(encoding="utf-8"))
    data.append({
        "id": rid,
        "is_mock": False,
        "verification_status": "unverified",
        "content_identity": content_identity,
        "verified_event_id": "evt-seed",
        "source_url": source_url,
        "evidence_id": f"ev-seed-{rid}",
        "candidate_id": None,
        "title": "",
        "region": None, "industry": None, "type": None,
        "amount": None, "issue_date": None, "valid_period": None,
        "official_contact": {"department": None, "phone": None,
                             "email": None, "address": None,
                             "contact_status": "unverified"},
        "description": "", "details": "", "requirements": "",
    })
    real_policies_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def env(tmp_path):
    real_copy = tmp_path / "real_policies.json"
    data = json.loads(PRODUCTION_REAL_POLICIES_PATH.read_text(encoding="utf-8"))
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


def _setup(trust, env, content_identity="<default-ci>", snapshot_ref="snapshots/x/y.html",
           source_url="https://example.com/p1", verified_event_id="evt-1",
           verification_status="VERIFIED", is_mock_meta=False,
           with_provenance=True, validity_is_valid=True, revoked=False):
    trust.evidence["ev-1"] = make_evidence(
        "ev-1", content_identity, snapshot_ref, source_url,
        verified_event_id=verified_event_id,
        verification_status=verification_status,
        is_mock_meta=is_mock_meta, with_provenance=with_provenance)
    trust.validity["ev-1"] = make_validity(
        is_valid=validity_is_valid, verified_event_id=verified_event_id,
        revoked=revoked)


# ---------------------------------------------------------------------------
# Verification Gate failures (1–7, 9)
# ---------------------------------------------------------------------------

def test_gate1_evidence_not_found(env):
    trust = FakeTrustService()
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-missing", trust, **env)


def test_gate2_not_verified(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref,
           verification_status="UNVERIFIED")
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_gate3_validity_false(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref,
           validity_is_valid=False)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_gate4_revoked(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref,
           validity_is_valid=False, revoked=True)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_gate5_snapshot_identity_mismatch(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    # metadata 中 policy_content_identity 与实际重算哈希不符
    _setup(trust, env, content_identity="deadbeef" * 8, snapshot_ref=ref)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_gate5_snapshot_replaced_after_verified(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"], content=b"<html>original</html>")
    _setup(trust, env, content_identity=ci, snapshot_ref=ref)
    # VERIFIED 后同一 snapshot 文件被替换为不同内容（路径不变，内容变化）
    p = env["snapshots_dir"] / "example.com" / f"{ci}.html"
    p.write_bytes(b"<html>replaced</html>")
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_gate6_provenance_missing(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref,
           with_provenance=False)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_gate6_snapshot_ref_missing(env):
    trust = FakeTrustService()
    _setup(trust, env, content_identity="abc", snapshot_ref="",
           with_provenance=False)
    # 无 provenance、无 snapshot_ref → 不可追溯
    trust.evidence["ev-1"]["metadata"].pop("snapshot_ref", None)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_gate7_mock_evidence(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref,
           verification_status="MOCK")
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_gate7_mock_metadata(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref,
           is_mock_meta=True)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


# ---------------------------------------------------------------------------
# Duplicate Rule A/B/C/D
# ---------------------------------------------------------------------------

def test_duplicate_case_a_same_content(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref)
    rid1 = ingest_verified_evidence("ev-1", trust, **env)
    assert rid1 == 121
    # 二次 ingest 同一证据（content_identity 相同）→ Case A
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_duplicate_case_b_same_url_diff_hash(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    seed_extra(env["real_policies_path"], 121, "hash-old", "https://x/p")
    _setup(trust, env, content_identity=ci, snapshot_ref=ref,
           source_url="https://x/p")
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_duplicate_case_c_diff_url_same_hash(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    seed_extra(env["real_policies_path"], 121, ci, "https://x/old")
    _setup(trust, env, content_identity=ci, snapshot_ref=ref,
           source_url="https://x/new")
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_duplicate_case_d_diff_url_diff_hash(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    seed_extra(env["real_policies_path"], 121, "hash-old", "https://x/old")
    _setup(trust, env, content_identity=ci, snapshot_ref=ref,
           source_url="https://x/new")
    rid = ingest_verified_evidence("ev-1", trust, **env)
    assert rid == 122


# ---------------------------------------------------------------------------
# ID rule / 101–120 protection
# ---------------------------------------------------------------------------

def test_gate9_id_less_than_121(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    # 仅存在 id=50 → max+1=51 < 121
    env["real_policies_path"].write_text(json.dumps([{
        "id": 50, "is_mock": False, "verification_status": "unverified",
        "content_identity": "hash-x", "verified_event_id": "e",
        "source_url": "https://x/50", "title": "", "region": None,
        "industry": None, "type": None, "amount": None, "issue_date": None,
        "valid_period": None,
        "official_contact": {"department": None, "phone": None, "email": None,
                             "address": None, "contact_status": "unverified"},
        "description": "", "details": "", "requirements": "",
    }], ensure_ascii=False, indent=2), encoding="utf-8")
    _setup(trust, env, content_identity=ci, snapshot_ref=ref)
    with pytest.raises(IngestionRejected):
        ingest_verified_evidence("ev-1", trust, **env)


def test_101_120_unchanged_after_ingest(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    before = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    _setup(trust, env, content_identity=ci, snapshot_ref=ref)
    rid = ingest_verified_evidence("ev-1", trust, **env)
    assert rid == 121
    after = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    before_by_id = {e["id"]: e for e in before}
    after_by_id = {e["id"]: e for e in after}
    for rid_ in range(101, 121):
        assert rid_ in after_by_id
        assert after_by_id[rid_] == before_by_id[rid_], f"101-120 #{rid_} modified"
    assert len(after) == len(before) + 1


def test_new_real_record_contract(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref,
           source_url="https://x/p1", verified_event_id="evt-42")
    rid = ingest_verified_evidence("ev-1", trust, **env)
    data = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    rec = next(e for e in data if e["id"] == rid)
    assert rec["id"] >= 121
    assert rec["is_mock"] is False
    assert rec["verification_status"] == "unverified"
    assert rec["content_identity"] == ci
    assert rec["verified_event_id"] == "evt-42"
    # 全文件不得出现 verification_status == "verified"
    assert all(e.get("verification_status") != "verified" for e in data)


def test_no_verified_status_anywhere(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref)
    ingest_verified_evidence("ev-1", trust, **env)
    data = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    assert all(e.get("verification_status") != "verified" for e in data)


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------

def test_concurrency_no_duplicate_ids(env):
    trust = FakeTrustService()
    n = 8
    ev_ids = []
    refs = []
    for i in range(n):
        ref, ci = write_snapshot(
            env["snapshots_dir"],
            content=f"<html>policy number {i}</html>".encode())
        eid = f"ev-{i}"
        trust.evidence[eid] = make_evidence(
            eid, ci, ref, f"https://x/p{i}", verified_event_id=f"evt-{i}")
        trust.validity[eid] = make_validity(
            is_valid=True, verified_event_id=f"evt-{i}")
        ev_ids.append(eid)
        refs.append(ref)

    results = []
    errors = []

    def worker(eid):
        try:
            results.append(ingest_verified_evidence(eid, trust, **env))
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(eid,)) for eid in ev_ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"unexpected errors: {errors}"
    assert len(results) == n
    assert len(set(results)) == n, f"duplicate REAL ids: {results}"
    assert min(results) >= 121
    data = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    ids = [e["id"] for e in data]
    assert len(ids) == len(set(ids)), "id collision in dataset"


# ---------------------------------------------------------------------------
# Atomic write failure protection
# ---------------------------------------------------------------------------

def test_atomic_write_failure_keeps_dataset_intact(env, monkeypatch):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref)
    before = env["real_policies_path"].read_text(encoding="utf-8")

    def boom(*args, **kwargs):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(Exception):
        ingest_verified_evidence("ev-1", trust, **env)
    # 原 dataset 未损坏
    after = env["real_policies_path"].read_text(encoding="utf-8")
    assert after == before
    assert json.loads(after), "dataset still valid JSON"
    # 无残留 .tmp 半写文件
    assert not list(env["real_policies_path"].parent.glob("*.tmp"))


# ---------------------------------------------------------------------------
# Revoke 后处理（DD-2）：不删 REAL，仅记 audit
# ---------------------------------------------------------------------------

def test_revoked_after_ingest_audit_only(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref)
    rid = ingest_verified_evidence("ev-1", trust, **env)
    # 之后 Trust revoke
    trust.validity["ev-1"] = make_validity(is_valid=False, revoked=True)
    wrote = record_revoked_after_ingest(
        rid, "ev-1", trust,
        real_policies_path=env["real_policies_path"],
        audit_path=env["audit_path"])
    assert wrote is True
    # REAL dataset 未改动
    data = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    assert any(e["id"] == rid for e in data)
    # audit 含 revoked_after_ingest
    lines = env["audit_path"].read_text(encoding="utf-8").strip().splitlines()
    assert any(json.loads(l)["status"] == "revoked_after_ingest" for l in lines)


# ---------------------------------------------------------------------------
# Boundary static checks
# ---------------------------------------------------------------------------

def test_no_record_human_verification_called(env):
    trust = FakeTrustService()
    ref, ci = write_snapshot(env["snapshots_dir"])
    _setup(trust, env, content_identity=ci, snapshot_ref=ref)
    ingest_verified_evidence("ev-1", trust, **env)
    assert trust.record_human_verification_called is False


def test_src_trust_zero_diff_static():
    import inspect
    from global_policy_aggregator.pipeline import real_ingestion
    module_src = inspect.getsource(real_ingestion)
    assert "import src.trust" not in module_src
    assert "from src.trust" not in module_src
    # 不得出现对 record_human_verification 的调用（仅允许文档/拒绝说明，不含 "()" 调用形态）
    assert "record_human_verification(" not in module_src
