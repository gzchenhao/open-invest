"""P6-3.19 — Unified Per-Context Execution Result Contract 实现测试。

覆盖设计文档要求的 T1–T12：
T1  Context A result 含 context_key == "context_a"
T2  Context B result 含 context_key == "ctx_122_stabilization_subsidy"
T3  A readiness 与 A provenance 使用相同 evidence identity
T4  B readiness 与 B provenance 使用相同 evidence identity
T5  A 不得解析到 B evidence
T6  B 不得解析到 A evidence
T7  Context B 不再依赖 standalone production call 即可得到统一 result
T8  两个 context 的 benefit 保持独立（无 aggregation）
T9  aggregation / stacking / interaction / winner 仍为 NOT_SUPPORTED
T10 legacy Context A fallback 仍有效（无 trust_bindings 政策 single context）
T11 unknown context fail-closed
T12 pipeline 不 import src/trust（只读，不修改）
"""
import inspect
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from global_policy_aggregator.pipeline.p4_execution_orchestrator import (  # noqa: E402
    evaluate_project_against_policies,
)
from global_policy_aggregator.pipeline.p4_execution_state import (  # noqa: E402
    assess_execution_readiness,
    _resolve_trust_identity,
)
from global_policy_aggregator.pipeline.context_b_execution import execute_context_b  # noqa: E402

REAL_PATH = os.path.join(REPO_ROOT, "global_policy_aggregator", "data",
                          "real_policies", "real_policies.json")
A_EVIDENCE_ID = "ev_ctx_122_context_a"
B_EVIDENCE_ID = "ev_ctx_122_stabilization_subsidy"


def _real122():
    with open(REAL_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return next(e for e in data if e["id"] == 122)


def _by_context(results):
    return {e["context_key"]: e for e in results}


class _VerifiedStub:
    """最小 trust_service stub：仅验证给定 (evidence_id, verified_event_id) 对。"""

    def __init__(self, pairs):
        self._pairs = set(pairs)

    def check_verified_validity(self, evidence_id):
        for ev, ve in self._pairs:
            if evidence_id == ev:
                return {"is_valid": True, "latest_verified_event": {"event_id": ve}}
        return {"is_valid": False, "reasons": ["unverified"]}


def _stub_for_122():
    pol = _real122()
    tb = pol["trust_bindings"]
    pairs = [(b["evidence_id"], b["verified_event_id"]) for b in tb.values()]
    return _VerifiedStub(pairs)


# ───────── T1 / T2: per-context context_key present ─────────
def test_t1_context_a_key_present():
    res = evaluate_project_against_policies({}, [_real122()], trust_service=None)
    by = _by_context(res)
    assert "context_a" in by
    assert by["context_a"]["context_key"] == "context_a"
    assert by["context_a"]["context_id"] == "Context A"


def test_t2_context_b_key_present():
    res = evaluate_project_against_policies({}, [_real122()], trust_service=None)
    by = _by_context(res)
    assert "ctx_122_stabilization_subsidy" in by
    assert by["ctx_122_stabilization_subsidy"]["context_key"] == "ctx_122_stabilization_subsidy"
    assert by["ctx_122_stabilization_subsidy"]["context_id"] == "Context B"


# ───────── T3 / T4: readiness & provenance same evidence identity ─────────
def test_t3_t4_readiness_provenance_identity_equal():
    pol = _real122()
    for ck in ("context_a", "ctx_122_stabilization_subsidy"):
        ev_r, _ = _resolve_trust_identity(pol, ck)
        res = evaluate_project_against_policies({}, [pol], trust_service=None)
        entry = _by_context(res)[ck]
        # provenance 使用的 evidence_id 与 readiness 解析到的 identity 完全一致
        assert entry["provenance"]["evidence_id"] == ev_r
        # readiness 与 provenance 同源（identity equality）
        assert entry["provenance"]["evidence_id"] == ev_r


# ───────── T5 / T6: no cross-context evidence leakage ─────────
def test_t5_a_not_resolve_b_evidence():
    pol = _real122()
    by = _by_context(evaluate_project_against_policies({}, [pol], trust_service=None))
    assert by["context_a"]["provenance"]["evidence_id"] == A_EVIDENCE_ID
    assert by["context_a"]["provenance"]["evidence_id"] != B_EVIDENCE_ID


def test_t6_b_not_resolve_a_evidence():
    pol = _real122()
    by = _by_context(evaluate_project_against_policies({}, [pol], trust_service=None))
    assert by["ctx_122_stabilization_subsidy"]["provenance"]["evidence_id"] == B_EVIDENCE_ID
    assert by["ctx_122_stabilization_subsidy"]["provenance"]["evidence_id"] != A_EVIDENCE_ID


# ───────── T7: Context B now in unified pipeline (no standalone call needed) ─────────
def test_t7_context_b_in_unified_pipeline():
    pol = _real122()
    inputs = {"company_size": "大型企业", "prior_year_ui_premium_paid": 1_000_000}
    res = evaluate_project_against_policies(
        {}, [pol], project_inputs=inputs, trust_service=_stub_for_122())
    by = _by_context(res)
    # Context B 已作为统一 entry 出现（不再依赖独立 execute_context_b 调用）
    assert "ctx_122_stabilization_subsidy" in by
    unified_b = by["ctx_122_stabilization_subsidy"]["benefit"]
    standalone = execute_context_b(inputs)
    # 统一 pipeline 内 B 的 benefit 与独立调用结果一致（context-scoped）
    assert unified_b["calculated_amount"] == standalone["benefit_amount"] == 300000.0


# ───────── T8: benefit independence (no aggregation) ─────────
def test_t8_benefits_independent():
    pol = _real122()
    inputs = {"company_size": "大型企业", "prior_year_ui_premium_paid": 1_000_000}
    by = _by_context(evaluate_project_against_policies(
        {}, [pol], project_inputs=inputs, trust_service=_stub_for_122()))
    a_ben = by["context_a"]["benefit"]
    b_ben = by["ctx_122_stabilization_subsidy"]["benefit"]
    # 各自为独立 context-scoped benefit dict
    assert isinstance(a_ben, dict) and isinstance(b_ben, dict)
    # 不存在合并/相加字段
    for e in by.values():
        assert "total_benefit" not in e
        assert "aggregate_benefit" not in e
        assert "combined_benefit" not in e


# ───────── T9: NOT_SUPPORTED guards ─────────
def test_t9_unsupported_capabilities():
    pol = _real122()
    by = _by_context(evaluate_project_against_policies({}, [pol], trust_service=None))
    for e in by.values():
        assert e["aggregation_status"] == "NOT_SUPPORTED"
        assert e["stacking_status"] == "NOT_SUPPORTED"
        assert e["interaction_status"] == "NOT_SUPPORTED"
        assert e["winner_selection"] == "NOT_SUPPORTED"


# ───────── T10: legacy single-context fallback ─────────
def test_t10_legacy_fallback_single_context():
    pol = _real122()
    no_bindings = dict(pol)
    no_bindings.pop("trust_bindings", None)
    res = evaluate_project_against_policies({}, [no_bindings], trust_service=None)
    # 无 trust_bindings → 单一 legacy context（context_key=None → display Context A）
    assert len(res) == 1
    assert res[0]["context_key"] is None
    assert res[0]["context_id"] == "Context A"


# ───────── T11: unknown context fail-closed ─────────
def test_t11_unknown_context_fail_closed():
    pol = _real122()
    # 请求不存在的 context_key：不得解析到 B 的 evidence（隔离）
    ev_r, _ = _resolve_trust_identity(pol, "totally_unknown_context")
    assert ev_r != B_EVIDENCE_ID
    # 该未知 context 的 readiness 不能凭空变为 READY（无 binding → legacy 未验证）
    r = assess_execution_readiness(
        pol, context_key="totally_unknown_context", trust_service=None)
    assert r["state"] == "NOT_READY"


# ───────── T12: pipeline 不 import src/trust（只读，不修改）─────────
def test_t12_no_src_trust_import_in_pipeline():
    from global_policy_aggregator.pipeline import p4_execution_orchestrator as orch
    from global_policy_aggregator.pipeline import context_b_execution as cbe
    for mod in (orch, cbe):
        src = inspect.getsource(mod)
        assert "from src.trust" not in src
        assert "import src.trust" not in src
