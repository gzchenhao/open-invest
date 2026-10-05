"""P6-1 — MULTI-POLICY RESULT CONTRACT + UI COMPOSITION 实现验证。

仅验证 P6-1 最小实现：
- Result Contract additive 增加 ``aggregation_status = "NOT_SUPPORTED"``，且**不产生任何**
  total / combined / estimated / sum / aggregated 金额字段；
- 多政策独立执行、结果隔离、provenance 隔离、Trust 隔离；
- P5 UI 不再硬编码 policy_id 122，改为动态遍历 execution 集合；
- 单政策向后兼容（assess 原始输出 key 集合不变，仅 _serialize/HTTP 增加聚合声明）。

不修改生产逻辑、不写入 REAL、不调用 Human Verification、不引入 ranking/aggregate。
"""
import copy
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from global_policy_aggregator.pipeline.p4_rule_operator import evaluate_policy  # noqa: E402
from global_policy_aggregator.pipeline.p4_execution_orchestrator import (  # noqa: E402
    evaluate_project_against_policies,
)
from global_policy_aggregator.web.production_nl_entry import (  # noqa: E402
    assess,
    _serialize,
    app,
)
from global_policy_aggregator.nl_extraction import extract_and_evaluate, FakeProvider  # noqa: E402


# ───────────────────────────── fixtures / helpers ─────────────────────────────
def _real122() -> dict:
    data = json.load(open(os.path.join(
        REPO_ROOT, "global_policy_aggregator", "data", "real_policies",
        "real_policies.json"), encoding="utf-8"))
    return next(e for e in data if e["id"] == 122)


def _fixture_B() -> dict:
    """内存确定性 fixture（is_mock=True），不写入 REAL、不 Trust verification。"""
    b = copy.deepcopy(_real122())
    b["id"] = 999
    b["is_mock"] = True
    b["evidence_id"] = "ev_b_fixture"
    b["verified_event_id"] = "evt_b_fixture"
    b["amount"] = {"raw_text": "", "normalized_number": 30000,
                   "currency": "CNY", "unit": "元/人"}
    # P6-3.18：清除从 REAL 122 深拷贝继承来的生产 context_a 绑定；B 是独立 mock
    # 政策，应使用自身顶层 evidence_id（ev_b_fixture），不应继承 A 的 per-context 绑定。
    b.pop("trust_bindings", None)
    return b


def _val_for(cond):
    op = cond.get("operator")
    exp = cond.get("expected_value", cond.get("threshold"))
    if op == "within_period":
        return "2026-06-01"
    if op == "in":
        return exp[0] if isinstance(exp, (list, tuple, set)) else exp
    return exp


def _build_facts(record):
    conds = record.get("eligibility_conditions") or []
    project_profile, hired = {}, []
    for i in range(10):
        person = {}
        for c in conds:
            if c.get("granularity") == "per_person":
                sf = c.get("source_field", c.get("field"))
                person[sf] = _val_for(c)
        hired.append(person)
    for c in conds:
        if c.get("granularity") != "per_person":
            sf = c.get("source_field", c.get("field"))
            project_profile[sf] = _val_for(c)
    return project_profile, {"hired_persons": hired}


def _all_keys(obj, acc):
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.add(k)
            _all_keys(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _all_keys(v, acc)


_FORBIDDEN_AGG = {"total_benefit", "combined_benefit", "estimated_total",
                  "sum_of_benefits", "aggregated_benefit"}
_FORBIDDEN_RANK = {"ranking", "recommended", "score", "tier", "winner",
                   "best_policy", "highest_benefit"}


# ───────────────────────────── A. 单政策向后兼容 ─────────────────────────────
def test_assess_raw_output_keys_unchanged():
    # assess() 返回 extract_and_evaluate 原始输出，不应含 aggregation_status
    out = assess("我们是一家企业，有10个人。", provider=FakeProvider(),
                 trust_service=None, policies=[_real122()])
    assert set(out.keys()) == {"extraction", "execution", "project_profile", "project_inputs"}
    assert "aggregation_status" not in out


def test_single_policy_backward_compat():
    out = assess("我们是一家企业，有10个人。", provider=FakeProvider(),
                 trust_service=None, policies=[_real122()])
    ser = _serialize(out)
    # P6-3.19：单政策 REAL122 现在产出 2 个 per-context execution entries
    # （context_a + ctx_122_stabilization_subsidy），而非旧的单一 entry
    ctx_keys = {e["context_key"] for e in ser["execution"]}
    assert ctx_keys == {"context_a", "ctx_122_stabilization_subsidy"}
    # 既有顶层 key 集合与 aggregation 护栏不变（向后兼容）
    assert "aggregation_status" not in out
    assert ser["aggregation_status"] == "NOT_SUPPORTED"


# ─────────────── B/C. 两政策独立执行 + 渲染 ───────────────
def test_two_policies_render_independently():
    A, B = _real122(), _fixture_B()
    execs = evaluate_project_against_policies({}, [A, B], trust_service=None)
    # REAL122 → 2 contexts；fixture B（无 trust_bindings）→ 1 legacy context
    assert len(execs) == 3
    by_pid = {}
    for e in execs:
        by_pid.setdefault(e["policy_id"], []).append(e["context_key"])
    assert set(by_pid[122]) == {"context_a", "ctx_122_stabilization_subsidy"}
    assert set(by_pid[999]) == {None}
    # 两政策 result 互不污染：context_key / context_id 来自各自声明，policy_id 隔离
    assert all(e["policy_id"] in (122, 999) for e in execs)


# ─────────────── D. A=15000 / B=300000 ───────────────
def test_policy_amounts_independent():
    A, B = _real122(), _fixture_B()
    proj, pins = _build_facts(A)
    ea = evaluate_policy(A, project_inputs=pins, project_profile=proj)
    eb = evaluate_policy(B, project_inputs=pins, project_profile=proj)
    assert (ea["benefit"] or {}).get("calculated_amount") == 15000
    assert (eb["benefit"] or {}).get("calculated_amount") == 300000


# ─────────────── E/F/G/H. 不存在 aggregate 字段 ───────────────
def test_no_aggregate_fields_in_contract():
    A, B = _real122(), _fixture_B()
    proj, pins = _build_facts(A)
    execs = evaluate_project_against_policies(proj, [A, B], project_inputs=pins,
                                              trust_service=None)
    fake_out = {"extraction": {"status": "ok"}, "execution": execs,
                "project_profile": proj, "project_inputs": pins}
    ser = _serialize(fake_out)
    keys = set()
    _all_keys(ser, keys)
    assert not (_FORBIDDEN_AGG & keys), f"出现聚合字段: {_FORBIDDEN_AGG & keys}"
    # 明确不存在多政策求和金额
    assert 315000 not in [v for v in _flat_values(ser) if isinstance(v, (int, float))]


def _flat_values(obj, acc=None):
    acc = acc if acc is not None else []
    if isinstance(obj, dict):
        for v in obj.values():
            _flat_values(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _flat_values(v, acc)
    else:
        acc.append(obj)
    return acc


# ─────────────── I/J. aggregation_status == NOT_SUPPORTED 且 ≠ 0 / ≠ NOT_CALCULATED ───────────────
def test_aggregation_status_not_supported():
    A, B = _real122(), _fixture_B()
    proj, pins = _build_facts(A)
    execs = evaluate_project_against_policies(proj, [A, B], project_inputs=pins,
                                              trust_service=None)
    ser = _serialize({"extraction": {"status": "ok"}, "execution": execs,
                      "project_profile": proj, "project_inputs": pins})
    assert ser["aggregation_status"] == "NOT_SUPPORTED"
    assert ser["aggregation_status"] != 0
    assert ser["aggregation_status"] != "0"
    assert ser["aggregation_status"] != "NOT_CALCULATED"


# ─────────────── K/L/M. Policy Result 隔离 ───────────────
def test_policy_result_isolation():
    A, B = _real122(), _fixture_B()
    proj, pins = _build_facts(A)
    execs = evaluate_project_against_policies(proj, [A, B], project_inputs=pins,
                                              trust_service=None)
    by = {e["policy_id"]: e for e in execs}
    a, b = by[122], by[999]
    # NOT_READY 路径下 benefit/eligibility/missing_inputs 均为 None，故以恒可获得的
    # 身份字段证明隔离（绝不合并身份）。注意：fixture B 是 A 的副本，其 content_identity
    # 与 A 相同属正常（不同政策可同源），系统以 policy_id + evidence_id 区分身份。
    assert a["policy_id"] != b["policy_id"]
    assert a["provenance"]["evidence_id"] != b["provenance"]["evidence_id"]
    assert a["provenance"] != b["provenance"]
    # 即便 READY（evaluate_policy 直接计算）也各自独立金额，互不污染
    ea = evaluate_policy(A, project_inputs=pins, project_profile=proj)
    eb = evaluate_policy(B, project_inputs=pins, project_profile=proj)
    assert (ea["benefit"] or {}).get("calculated_amount") != (
        eb["benefit"] or {}).get("calculated_amount")


# ─────────────── N/O. 无 ranking + Trust 隔离 ───────────────
def test_no_policy_ranking():
    A, B = _real122(), _fixture_B()
    proj, pins = _build_facts(A)
    execs = evaluate_project_against_policies(proj, [A, B], project_inputs=pins,
                                              trust_service=None)
    ser = _serialize({"extraction": {"status": "ok"}, "execution": execs,
                      "project_profile": proj, "project_inputs": pins})
    keys = set()
    _all_keys(ser, keys)
    assert not (_FORBIDDEN_RANK & keys), f"出现 ranking 字段: {_FORBIDDEN_RANK & keys}"


class _VerifiedTrustStub:
    """只读 Trust stub（与 P5-6 一致）：仅对给定 evidence_id 返回有效。"""

    def __init__(self, evidence_id, event_id):
        self._ev, self._eid = evidence_id, event_id

    def check_verified_validity(self, evidence_id):
        if evidence_id == self._ev:
            return {"is_valid": True,
                    "latest_verified_event": {"event_id": self._eid}}
        return {"is_valid": False, "reasons": ["unverified"]}


def test_trust_isolation_across_policies():
    # Trust 逐 policy 绑定于 evidence_id：同一 trust_service 下，仅被验证 evidence_id
    # 的政策获得 verification_event_id；另一政策（不同 evidence_id）仍为 None。
    from global_policy_aggregator.pipeline.p4_execution_orchestrator import _build_provenance

    B = _fixture_B()
    A2 = copy.deepcopy(_real122())
    A2["verified_event_id"] = "evt_a"  # 仅用于本测试内存对象，不修改 REAL 文件
    stub = _VerifiedTrustStub(A2["evidence_id"], "evt_a")
    pa = _build_provenance(A2, stub)
    pb = _build_provenance(B, stub)
    # A 已被验证（携带 verification event）；B 未经该 evidence_id 验证
    assert pa["verification_event_id"] == "evt_a"
    assert pb["verification_event_id"] is None
    assert pa != pb
    # 反向：若 stub 只验证 B 的 evidence_id，则 A 不被验证（验证不扩散）
    stub2 = _VerifiedTrustStub(B["evidence_id"], "evt_b")
    pa2 = _build_provenance(A2, stub2)
    pb2 = _build_provenance(B, stub2)
    assert pa2["verification_event_id"] is None
    assert pb2["verification_event_id"] == "evt_b"


# ─────────────── HTTP contract: aggregation_status 在响应顶层 ───────────────
def test_http_response_has_aggregation_status():
    import os
    from fastapi.testclient import TestClient

    saved = os.environ.pop("OPENINVEST_LLM_API_KEY", None)
    try:
        client = TestClient(app)
        resp = client.post("/api/nl/assess",
                           json={"nl_text": "我们是一家企业，有10个人。"})
    finally:
        if saved is not None:
            os.environ["OPENINVEST_LLM_API_KEY"] = saved

    assert resp.status_code == 200
    body = resp.json()
    assert body["extraction"]["status"] == "EXTRACTION_FAILED"
    assert body["aggregation_status"] == "NOT_SUPPORTED"
    assert "total_benefit" not in body
