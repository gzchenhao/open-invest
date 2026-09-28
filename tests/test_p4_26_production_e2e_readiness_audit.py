"""P4-26 — PRODUCTION E2E GATE / READINESS AUDIT（AUDIT-FIRST，仅新增测试 + 报告）。

本阶段**不修改** production logic / REAL data / src.trust / Authority Registry / Event Log。
只做 READ-ONLY 完整 Production E2E 验证：

A. PRODUCTION ENTRY   — /api/nl/assess 真实进入 production_nl_entry；无 legacy 混入；
                          FakeProvider 仅测试；provider 不可用 fail-closed（不 500）。
B. TRUST RUNTIME       — fresh Python process 重建 EvidenceObject(UNVERIFIED)，
                          Event Log 仍 1 条，check_verified_validity 通过；不合成、不绕过、不新建 event。
C. REAL 122 EXECUTION  — Case A/B/C/D 真实 production chain。
D. EVIDENCE/PROVENANCE— Policy content_identity 与 Trust Evidence content_identity 区分正确。
E. READINESS BOUNDARY — Execution Readiness ≠ Application Readiness ≠ “政府已批准/可自动申请”。
F. ANTI-BYPASS         — 缺失 source / snapshot_ref / event log / local VERIFIED / 用户声称数。
G. GOVERNANCE          — src/trust zero diff；REAL 未改；Event Log 仍 1 条。
"""
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.trust.trust_service import TrustEvidenceService  # noqa: E402
from global_policy_aggregator.pipeline.trust_evidence_bootstrap import (  # noqa: E402
    load_context_a_evidence,
    load_context_a_new_evidence,
)
from global_policy_aggregator.web.production_nl_entry import (  # noqa: E402
    assess, load_real_policies, _build_trust_service, app,
)
from global_policy_aggregator.nl_extraction import FakeProvider, ProviderUnavailable  # noqa: E402
from global_policy_aggregator.nl_extraction import extract_and_evaluate  # noqa: E402

_REAL_EVENT_LOG = os.path.join(REPO_ROOT, "trust_config", "production_trust_events.jsonl")
_REAL_REGISTRY = os.path.join(REPO_ROOT, "trust_config", "production_authority_registry.json")
# legacy（保留用于 anti-bypass 测试）
_CONTEXT_A = "ev_1e2d555ae07193b5c257"
_VERIFIED_EVENT_ID = "fc50856de78547df8dc5d9f29b4b270d"
_POLICY_CONTENT_IDENTITY = "1e2d555ae07193b5c2574f6cd426b2028068fa266461e899462e493c0f8ae76b"
_TRUST_CONTENT_IDENTITY = "b4012feb48e86e999b3149eb42fd62d91f1a8049e22daeda24d9dd4a89292937"
# P6-3.18：Context A 现拥有独立证据及其 Trust 绑定（取代 legacy 共享绑定）
_CONTEXT_A_NEW = "ev_ctx_122_context_a"
_VERIFIED_EVENT_ID_NEW = "d8d5cc1dbd394eb58ccb501116e98487"
_TRUST_CONTENT_IDENTITY_NEW = "d3c560c0ca03153283c06b7b68e8e6c5fbfff2fa0711f97786e54e2ad29c52db"
# P6-3.18（M1/M3）向 durable Production Event Log 合法新增 Context A 独立证据及其
# 人工核验事件，基线由 1 → 4。审计仅保证日志不被运行时追加（== baseline），不回退生产契约。
_EVENT_LOG_BASELINE = 4


def _real122() -> dict:
    data = json.load(open(os.path.join(
        REPO_ROOT, "global_policy_aggregator", "data", "real_policies",
        "real_policies.json"), encoding="utf-8"))
    return next(e for e in data if e["id"] == 122)


def _exec_for(out, pid=122):
    return next(e for e in out["execution"] if e["policy_id"] == pid)


def _event_log_count():
    n = 0
    for line in open(_REAL_EVENT_LOG, encoding="utf-8"):
        if line.strip():
            n += 1
    return n


# ───────────────────────── A. PRODUCTION ENTRY ─────────────────────────
def test_entry_has_production_routes():
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/api/nl/assess" in paths
    assert "/health" in paths


def test_entry_no_legacy_agent_import():
    import global_policy_aggregator.web.production_nl_entry as mod
    src = open(mod.__file__, encoding="utf-8").read()
    assert "import agents.policy_ai_agent" not in src
    assert "from agents.policy_ai_agent" not in src
    assert "import ai_agent_interface" not in src
    assert "from ai_agent_interface" not in src
    assert "investment_capacity_usd" not in src


def test_production_default_provider_is_real_not_fake():
    # 未注入 provider 时，extract_and_evaluate 必须尝试真实 OpenAICompatibleProvider
    # （缺 key → ProviderUnavailable），绝不默认用 FakeProvider。
    saved = os.environ.pop("OPENINVEST_LLM_API_KEY", None)
    try:
        with pytest.raises(ProviderUnavailable):
            extract_and_evaluate("企业 10人", load_real_policies())
    finally:
        if saved is not None:
            os.environ["OPENINVEST_LLM_API_KEY"] = saved


def test_provider_unavailable_fail_closed_not_500():
    import os
    from fastapi.testclient import TestClient

    saved = os.environ.pop("OPENINVEST_LLM_API_KEY", None)
    try:
        client = TestClient(app)
        resp = client.post("/api/nl/assess",
                           json={"nl_text": "我们是一家企业，目前有10个人。"})
    finally:
        if saved is not None:
            os.environ["OPENINVEST_LLM_API_KEY"] = saved
    # 不是 500，不是 fallback legacy，不是自行计算
    assert resp.status_code == 200
    body = resp.json()
    assert body["extraction"]["status"] == "EXTRACTION_FAILED"
    assert body["execution"] is None
    assert "provider unavailable" in body["extraction"]["error"].lower()


# ───────────────────────── B. TRUST RUNTIME ─────────────────────────
def test_fresh_runtime_bootstrap_gate():
    svc = TrustEvidenceService(
        event_log_path=_REAL_EVENT_LOG,
        authority_registry_config_path=_REAL_REGISTRY,
    )
    r = load_context_a_evidence(svc)  # legacy ev_1e2d555（保留）
    assert r["success"] is True
    r2 = load_context_a_new_evidence(svc)  # P6-3.18 独立 Context A 证据
    assert r2["success"] is True
    assert r2["verification_status"] == "UNVERIFIED"  # 初始强制 UNVERIFIED

    ge = svc.get_evidence(_CONTEXT_A_NEW)
    assert ge["success"] is True
    assert ge["verification_status"] == "UNVERIFIED"

    cv = svc.check_verified_validity(_CONTEXT_A_NEW)
    assert cv["is_valid"] is True
    assert cv["reasons"] == []
    # Trust Evidence content_identity（与独立 Context A 验证事件一致）
    assert cv["current_content_identity"] == _TRUST_CONTENT_IDENTITY_NEW
    assert cv["latest_verified_event"]["event_id"] == _VERIFIED_EVENT_ID_NEW

    # 绝不从 Event Log 合成 Evidence；durable Event Log 基线（P6-3.18 合法扩展）为 4 条
    assert svc.get_verification_history(_CONTEXT_A_NEW)["event_count"] == 1
    assert _event_log_count() == _EVENT_LOG_BASELINE


def test_trust_no_event_log_synthesis():
    svc = TrustEvidenceService(
        event_log_path=_REAL_EVENT_LOG,
        authority_registry_config_path=_REAL_REGISTRY,
    )
    # 不调用 load_context_a_evidence → EvidenceGraph 空
    cv = svc.check_verified_validity(_CONTEXT_A)
    assert cv["is_valid"] is False
    assert "not found" in cv["reasons"][0].lower()


def test_trust_local_verified_cannot_bypass():
    svc = TrustEvidenceService(authority_registry_config_path=_REAL_REGISTRY)
    svc.create_evidence({
        "id": _CONTEXT_A, "type": "policy",
        "source": "openinvest-pipeline",
        "source_reference": _real122()["snapshot_ref"],
        "verification_status": "VERIFIED", "confidence_score": 0.0,
    })
    # 本地标 VERIFIED 但无 durable verified event → Gate 不通过
    assert svc.get_evidence(_CONTEXT_A)["verification_status"] == "VERIFIED"
    cv = svc.check_verified_validity(_CONTEXT_A)
    assert cv["is_valid"] is False


# ───────────────────────── C. REAL 122 EXECUTION E2E ─────────────────────────
class _TenFullProv:
    """10 人，逐人事实全部满足 → eligible 10。"""
    def complete(self, *, system, user):
        facts = [
            {"field": "applicant_entity_type", "value": "企业",
             "source": "user", "source_text": "企业"},
            {"field": "hired_persons", "value": 10,
             "source": "user", "source_text": "10个人"},
        ]
        for i in range(10):
            facts += [
                {"field": "target_group", "value": "grad_2026",
                 "source": "user", "source_text": "x", "person_index": i},
                {"field": "labor_contract_signed", "value": True,
                 "source": "user", "source_text": "x", "person_index": i},
                {"field": "employment_insurance_paid_months", "value": 5,
                 "source": "user", "source_text": "x", "person_index": i},
                {"field": "hire_date", "value": "2026-05-01",
                 "source": "user", "source_text": "x", "person_index": i},
            ]
        return json.dumps({"facts": facts, "unresolved": []})


class _SevenFullProv:
    def complete(self, *, system, user):
        facts = [
            {"field": "applicant_entity_type", "value": "企业",
             "source": "user", "source_text": "企业"},
            {"field": "hired_persons", "value": 10,
             "source": "user", "source_text": "10个人"},
        ]
        for i in range(7):
            facts += [
                {"field": "target_group", "value": "grad_2026",
                 "source": "user", "source_text": "x", "person_index": i},
                {"field": "labor_contract_signed", "value": True,
                 "source": "user", "source_text": "x", "person_index": i},
                {"field": "employment_insurance_paid_months", "value": 5,
                 "source": "user", "source_text": "x", "person_index": i},
                {"field": "hire_date", "value": "2026-05-01",
                 "source": "user", "source_text": "x", "person_index": i},
            ]
        return json.dumps({"facts": facts, "unresolved": []})


def test_case_A_ten_full():
    svc = _build_trust_service()
    out = assess("企业 10人 全符合", provider=_TenFullProv(),
                 trust_service=svc, policies=[_real122()])
    e = _exec_for(out)
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 10
    assert e["benefit"]["calculated_amount"] == 15000  # 1500 * 10


def test_case_B_missing_facts_unknown():
    svc = _build_trust_service()
    out = assess("我们现在有10个人，其中7个人应该符合条件。",
                 provider=FakeProvider(), trust_service=svc, policies=[_real122()])
    e = _exec_for(out)
    assert e["eligibility"]["overall"] == "UNKNOWN"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"


def test_case_C_out_of_scope_fail():
    svc = _build_trust_service()
    out = assess("我是个体工商户，有10个人。",
                 provider=FakeProvider(), trust_service=svc, policies=[_real122()])
    e = _exec_for(out)
    assert e["eligibility"]["overall"] == "FAIL"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"


def test_case_D_seven_full():
    svc = _build_trust_service()
    out = assess("企业 10人 7人完整", provider=_SevenFullProv(),
                 trust_service=svc, policies=[_real122()])
    e = _exec_for(out)
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 7
    assert e["benefit"]["calculated_amount"] == 10500  # 1500 * 7


# ───────────────────────── D. EVIDENCE / PROVENANCE ─────────────────────────
def test_provenance_trace_policy_vs_trust_identity():
    svc = _build_trust_service()
    out = assess("企业 10人 全符合", provider=_TenFullProv(),
                 trust_service=svc, policies=[_real122()])
    e = _exec_for(out)
    r122 = _real122()

    # Policy 层 provenance（来自 REAL 122 记录）
    assert e["content_identity"] == _POLICY_CONTENT_IDENTITY
    assert e["snapshot_ref"] == r122["snapshot_ref"]
    assert e["source_url"] == r122["source_url"]

    # evidence_refs 可追溯到 policy content_identity / snapshot_ref / source_url
    refs = e.get("evidence_refs") or []
    assert refs, "evidence_refs 不能为空"
    assert any(
        ref.get("content_identity") == _POLICY_CONTENT_IDENTITY
        and ref.get("snapshot_ref") == r122["snapshot_ref"]
        and ref.get("source_url") == r122["source_url"]
        for ref in refs
    )

    # Trust Evidence content_identity（独立 Context A 的 d3c560c0）与 Policy
    # content_identity（1e2d555）区分正确
    cv = svc.check_verified_validity(_CONTEXT_A_NEW)
    assert cv["current_content_identity"] == _TRUST_CONTENT_IDENTITY_NEW
    assert _TRUST_CONTENT_IDENTITY_NEW != _POLICY_CONTENT_IDENTITY
    # 两者通过独立 Context A evidence_id 关联
    assert cv["latest_verified_event"]["event_id"] == _VERIFIED_EVENT_ID_NEW


# ───────────────────────── E. READINESS BOUNDARY ─────────────────────────
def test_readiness_boundary_execution_vs_application():
    svc = _build_trust_service()
    out = assess("企业 10人 全符合", provider=_TenFullProv(),
                 trust_service=svc, policies=[_real122()])
    e = _exec_for(out)
    # Execution 可执行（benefit 已算），但整体 Execution Readiness 因 Application-only
    # 缺口（application_requirements 为空）而 NOT_READY；G5 解耦：该缺口不阻断 Eligibility/Benefit。
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["application_readiness"] == "NOT_READY"
    assert e["readiness_state"] == "NOT_READY"
    # 绝不宣称“政府已批准 / 可自动申请”
    flat = json.dumps(_to_jsonable(e), ensure_ascii=False).lower()
    assert "government_approved" not in flat
    assert "auto_apply" not in flat
    assert "application_submitted" not in flat


def _to_jsonable(o):
    import dataclasses
    if dataclasses.is_dataclass(o) and not isinstance(o, type):
        return dataclasses.asdict(o)
    if isinstance(o, dict):
        return {k: _to_jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_to_jsonable(v) for v in o]
    return o


# ───────────────────────── F. ANTI-BYPASS ─────────────────────────
def _build_service_with_bad_policies(tmp_path, record):
    bad = os.path.join(str(tmp_path), "real_policies.json")
    with open(bad, "w", encoding="utf-8") as f:
        json.dump([record], f)
    svc = TrustEvidenceService(
        event_log_path=_REAL_EVENT_LOG,
        authority_registry_config_path=_REAL_REGISTRY,
    )
    r = load_context_a_evidence(svc, real_policies_path=bad)
    return svc, r


def test_ab1_missing_source_fail_closed(tmp_path):
    svc, r = _build_service_with_bad_policies(
        tmp_path, {"id": 122, "is_mock": False,
                   "evidence_id": "ev_other", "snapshot_ref": "x.html"})
    assert r["success"] is False
    assert r["error"] == "context_a_source_not_found"
    assert svc.get_evidence(_CONTEXT_A)["success"] is False
    assert svc.check_verified_validity(_CONTEXT_A)["is_valid"] is False


def test_ab2_missing_snapshot_ref_fail_closed(tmp_path):
    svc, r = _build_service_with_bad_policies(
        tmp_path, {"id": 122, "is_mock": False,
                   "evidence_id": _CONTEXT_A, "snapshot_ref": ""})
    assert r["success"] is False
    assert r["error"] == "missing_snapshot_ref"
    assert svc.get_evidence(_CONTEXT_A)["success"] is False
    assert svc.check_verified_validity(_CONTEXT_A)["is_valid"] is False


def test_ab3_missing_event_log_gate_fails():
    svc = TrustEvidenceService(authority_registry_config_path=_REAL_REGISTRY)
    svc.create_evidence({
        "id": _CONTEXT_A, "type": "policy",
        "source": "openinvest-pipeline",
        "source_reference": _real122()["snapshot_ref"],
        "verification_status": "UNVERIFIED", "confidence_score": 0.0,
    })
    cv = svc.check_verified_validity(_CONTEXT_A)
    assert cv["is_valid"] is False
    assert "No event log configured" in cv["reasons"]


def test_ab4_local_verified_cannot_bypass():
    svc = TrustEvidenceService(authority_registry_config_path=_REAL_REGISTRY)
    svc.create_evidence({
        "id": _CONTEXT_A, "type": "policy",
        "source": "openinvest-pipeline",
        "source_reference": _real122()["snapshot_ref"],
        "verification_status": "VERIFIED", "confidence_score": 0.0,
    })
    assert svc.check_verified_validity(_CONTEXT_A)["is_valid"] is False


class _UserStatedProv:
    """用户声称 10 人符合，但无逐人事实。"""
    def complete(self, *, system, user):
        facts = [
            {"field": "applicant_entity_type", "value": "企业",
             "source": "user", "source_text": "企业"},
            {"field": "hired_persons", "value": 10,
             "source": "user", "source_text": "10个人"},
            {"field": "user_stated_eligible_count", "value": 10,
             "source": "user", "source_text": "10人符合"},
        ]
        return json.dumps({"facts": facts, "unresolved": []})


def test_ab5_user_stated_count_not_bypass():
    svc = _build_trust_service()
    out = assess("我们是一家企业，有10个人，其中10人符合。",
                 provider=_UserStatedProv(), trust_service=svc, policies=[_real122()])
    e = _exec_for(out)
    # 不得把用户声称的 10 人当 eligible_hired_persons
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 0
    assert e["benefit"]["calculated_amount"] == 0
    assert e["benefit"]["calculated_amount"] != 15000


# ───────────────────────── G. GOVERNANCE ─────────────────────────
def test_governance_event_log_unchanged():
    # 运行若干 E2E 后，生产 Event Log 仍 == durable 基线（P6-3.18 合法扩展为 4 条），
    # 且首条（legacy fc50856）event_id / evidence_id / decision 不变（不被运行时追加/改写）。
    assert _event_log_count() == _EVENT_LOG_BASELINE
    events = [json.loads(l) for l in open(_REAL_EVENT_LOG, encoding="utf-8") if l.strip()]
    assert events[0]["event_id"] == _VERIFIED_EVENT_ID
    assert events[0]["evidence_id"] == _CONTEXT_A
    assert events[0]["decision"] == "verified"


def test_governance_real_only_real():
    pols = load_real_policies()
    assert pols
    assert all(p.get("is_mock") is False for p in pols)
    assert any(p["id"] == 122 for p in pols)
    # 不存在 REAL 123+
    assert not any(p["id"] > 122 for p in pols)
