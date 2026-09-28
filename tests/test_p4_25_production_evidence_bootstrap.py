"""P4-25 — Production Evidence Runtime Bootstrap 测试（fresh process 实证）。

验证：
- P4-25 bootstrap 在 fresh runtime 把 Context A 的 durable Policy Evidence 重建为
  EvidenceObject 并注册进图；初始 UNVERIFIED；Gate 通过（is_valid=True）；
- 反安全绕过 A/B/C/D/E：缺失 durable source、缺失 snapshot_ref、缺 event log、
  local VERIFIED 均不能绕过正式 Trust Gate；
- Production NL Entry E2E（A/D）使用**真实** Production Trust Service（非 stub），
  REAL 122 经 Gate 判定 READY，benefit 正确计算。

不修改 src/trust、不创建 Verification Event、不修改 REAL / Event Log。
"""
import json
import os
import sys
import tempfile

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
    assess, _build_trust_service,
)
from global_policy_aggregator.nl_extraction import FakeProvider  # noqa: E402

_REAL_EVENT_LOG = os.path.join(REPO_ROOT, "trust_config", "production_trust_events.jsonl")
_REAL_REGISTRY = os.path.join(REPO_ROOT, "trust_config", "production_authority_registry.json")
# legacy（保留；P6-3.18 后 ev_1e2d555 因 Context B 事件 70cdc162 落在同 id 上而不再干净可验证）
_CONTEXT_A = "ev_1e2d555ae07193b5c257"
_VERIFIED_EVENT_ID = "fc50856de78547df8dc5d9f29b4b270d"
_VERIFIED_CONTENT_IDENTITY = "b4012feb48e86e999b3149eb42fd62d91f1a8049e22daeda24d9dd4a89292937"
# P6-3.18：Context A 现拥有独立证据及其 Trust 绑定（取代 legacy 共享绑定）
_CONTEXT_A_NEW = "ev_ctx_122_context_a"
_VERIFIED_EVENT_ID_NEW = "d8d5cc1dbd394eb58ccb501116e98487"
_VERIFIED_CONTENT_IDENTITY_NEW = "d3c560c0ca03153283c06b7b68e8e6c5fbfff2fa0711f97786e54e2ad29c52db"


def _real122() -> dict:
    data = json.load(open(os.path.join(
        REPO_ROOT, "global_policy_aggregator", "data", "real_policies",
        "real_policies.json"), encoding="utf-8"))
    return next(e for e in data if e["id"] == 122)


def _exec_for(out, pid=122):
    return next(e for e in out["execution"] if e["policy_id"] == pid)


def _snapshot_ref():
    return _real122()["snapshot_ref"]


# ── 主测试：fresh runtime bootstrap + Gate 通过 ──
def test_fresh_runtime_bootstrap_loads_and_gate_passes():
    svc = TrustEvidenceService(
        event_log_path=_REAL_EVENT_LOG,
        authority_registry_config_path=_REAL_REGISTRY,
    )
    r = load_context_a_evidence(svc)  # legacy（保留）
    assert r["success"] is True
    r2 = load_context_a_new_evidence(svc)  # P6-3.18 独立 Context A 证据
    assert r2["success"] is True
    assert r2["verification_status"] == "UNVERIFIED"

    ge = svc.get_evidence(_CONTEXT_A_NEW)
    assert ge["success"] is True
    assert ge["verification_status"] == "UNVERIFIED"
    assert ge["evidence"]["source"] == "openinvest-pipeline"
    assert ge["evidence"]["source_reference"] == _snapshot_ref()

    cv = svc.check_verified_validity(_CONTEXT_A_NEW)
    assert cv["is_valid"] is True
    assert cv["reasons"] == []
    assert cv["current_content_identity"] == _VERIFIED_CONTENT_IDENTITY_NEW

    hist = svc.get_verification_history(_CONTEXT_A_NEW)
    assert hist["event_count"] == 1
    assert hist["events"][0]["event_id"] == _VERIFIED_EVENT_ID_NEW


# ── 反绕过 A：durable source 缺失 → fail-closed，不创建 Evidence / Event ──
def test_antbypass_A_missing_source_fail_closed():
    tmp = tempfile.mkdtemp()
    bad = os.path.join(tmp, "real_policies.json")
    # 没有 Context A 记录（evidence_id 不匹配）
    with open(bad, "w", encoding="utf-8") as f:
        json.dump([{"id": 122, "is_mock": False,
                    "evidence_id": "ev_other", "snapshot_ref": "x.html"}], f)

    svc = TrustEvidenceService(
        event_log_path=_REAL_EVENT_LOG,
        authority_registry_config_path=_REAL_REGISTRY,
    )
    r = load_context_a_evidence(svc, real_policies_path=bad)
    assert r["success"] is False
    assert r["error"] == "context_a_source_not_found"

    assert svc.get_evidence(_CONTEXT_A)["success"] is False
    cv = svc.check_verified_validity(_CONTEXT_A)
    assert cv["is_valid"] is False

    # 加载不得创建任何 Verification Event（ev_1e2d555 已有 2 条 durable 事件：fc50856 + 70cdc162）
    assert svc.get_verification_history(_CONTEXT_A)["event_count"] == 2


# ── 反绕过 B：source 记录存在但 snapshot_ref 缺失 → fail-closed ──
def test_antbypass_B_source_missing_snapshot_ref():
    tmp = tempfile.mkdtemp()
    bad = os.path.join(tmp, "real_policies.json")
    with open(bad, "w", encoding="utf-8") as f:
        json.dump([{"id": 122, "is_mock": False,
                    "evidence_id": _CONTEXT_A, "snapshot_ref": ""}], f)

    svc = TrustEvidenceService(
        event_log_path=_REAL_EVENT_LOG,
        authority_registry_config_path=_REAL_REGISTRY,
    )
    r = load_context_a_evidence(svc, real_policies_path=bad)
    assert r["success"] is False
    assert r["error"] == "missing_snapshot_ref"

    assert svc.get_evidence(_CONTEXT_A)["success"] is False
    assert svc.check_verified_validity(_CONTEXT_A)["is_valid"] is False
    # ev_1e2d555 已有 2 条 durable 事件（fc50856 + 70cdc162）；加载不得新增
    assert svc.get_verification_history(_CONTEXT_A)["event_count"] == 2


# ── 反绕过 C：Evidence 存在但 Event Log 缺失 → Gate 不能通过 ──
def test_antbypass_C_evidence_present_event_log_absent():
    # 无 event_log 的 service，但手动注册 evidence（模拟"evidence present"）
    svc = TrustEvidenceService(authority_registry_config_path=_REAL_REGISTRY)
    svc.create_evidence({
        "id": _CONTEXT_A, "type": "policy",
        "source": "openinvest-pipeline",
        "source_reference": _snapshot_ref(),
        "verification_status": "UNVERIFIED", "confidence_score": 0.0,
    })
    assert svc.get_evidence(_CONTEXT_A)["success"] is True
    cv = svc.check_verified_validity(_CONTEXT_A)
    assert cv["is_valid"] is False
    assert "No event log configured" in cv["reasons"]


# ── 反绕过 D：Evidence + Event Log 都存在 → Gate 通过（主测试已覆盖）──
def test_antbypass_D_both_present_passes():
    svc = TrustEvidenceService(
        event_log_path=_REAL_EVENT_LOG,
        authority_registry_config_path=_REAL_REGISTRY,
    )
    load_context_a_evidence(svc)
    load_context_a_new_evidence(svc)  # P6-3.18 独立 Context A 证据
    assert svc.check_verified_validity(_CONTEXT_A_NEW)["is_valid"] is True


# ── 反绕过 E：本地把 Evidence 标成 VERIFIED 也不能绕过正式 Gate ──
def test_antbypass_E_local_verified_cannot_bypass():
    svc = TrustEvidenceService(authority_registry_config_path=_REAL_REGISTRY)
    # 伪造对象为 VERIFIED，但没有任何 verified event
    svc.create_evidence({
        "id": _CONTEXT_A, "type": "policy",
        "source": "openinvest-pipeline",
        "source_reference": _snapshot_ref(),
        "verification_status": "VERIFIED", "confidence_score": 0.0,
    })
    assert svc.get_evidence(_CONTEXT_A)["verification_status"] == "VERIFIED"
    # Gate 仍要求 durable verified event；无 event → 不通过
    cv = svc.check_verified_validity(_CONTEXT_A)
    assert cv["is_valid"] is False


# ── Production NL Entry 使用真实 Trust Service（非 stub）──
def test_production_uses_real_trust_not_stub():
    svc = _build_trust_service()
    assert svc is not None
    assert isinstance(svc, TrustEvidenceService)
    # 确认不是 P4-23 的 _VerifiedTrustStub
    assert not hasattr(svc, "check_verified_validity_stub")
    cv = svc.check_verified_validity(_CONTEXT_A_NEW)
    assert cv["is_valid"] is True
    assert cv["latest_verified_event"]["event_id"] == _VERIFIED_EVENT_ID_NEW


# ── E2E A：企业 + 10人无逐人资料 → eligible 0 / benefit 0（真实 Trust）──
def test_e2e_A_real_trust():
    svc = _build_trust_service()
    out = assess("我们是一家企业，目前有10个人，但暂时没有每个人的具体资料。",
                 provider=FakeProvider(), trust_service=svc, policies=[_real122()])
    assert out["extraction"].status == "ok"
    e = _exec_for(out)
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["benefit"]["calculated_amount"] == 0
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 0
    assert e["benefit"]["calculated_amount"] != 15000


# ── E2E D：企业 + 10人，7人完整 → eligible 7 / benefit 10500（真实 Trust）──
class _DPersonProv:
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


def test_e2e_D_real_trust():
    svc = _build_trust_service()
    out = assess("企业 10人 7人完整", provider=_DPersonProv(),
                 trust_service=svc, policies=[_real122()])
    e = _exec_for(out)
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["benefit"]["calculated_amount"] == 10500
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 7
