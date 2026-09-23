"""P4-23 — Production NL Entry 接线测试（离线 FakeProvider，不调用真实 LLM）。

验证：production entry 把 NL 接入已验证的确定性执行链：
- 入口只做接线，不重算 eligibility / benefit / eligible_hired_persons
- user_stated_eligible_count 绝不变成 eligible_hired_persons
- 抽取层禁止字段 fail-closed
- 不 import legacy agent（agents.policy_ai_agent / ai_agent_interface）

所有 LLM 调用均使用离线 test double（FakeProvider 或自定义 Provider）。
"""
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from global_policy_aggregator.web.production_nl_entry import (  # noqa: E402
    assess, load_real_policies, app,
)
from global_policy_aggregator.nl_extraction import FakeProvider  # noqa: E402


def _real122() -> dict:
    data = json.load(open(os.path.join(
        REPO_ROOT, "global_policy_aggregator", "data", "real_policies",
        "real_policies.json"), encoding="utf-8"))
    return next(e for e in data if e["id"] == 122)


class _VerifiedTrustStub:
    """生产 Trust 门禁的只读 stub（与 P4-21 一致）：仅对 REAL 122 evidence_id 返回有效。"""

    def __init__(self, evidence_id, event_id):
        self._ev, self._eid = evidence_id, event_id

    def check_verified_validity(self, evidence_id):
        if evidence_id == self._ev:
            return {"is_valid": True,
                    "latest_verified_event": {"event_id": self._eid}}
        return {"is_valid": False, "reasons": ["not verified"]}


def _trust():
    r = _real122()
    return _VerifiedTrustStub(r["evidence_id"], r["verified_event_id"])


def _exec_for(out, pid=122):
    return next(e for e in out["execution"] if e["policy_id"] == pid)


# ── E2E A：企业 + 10人，无逐人事实 ──
def test_e2e_A_enterprise_10_persons_no_detail():
    out = assess("我们是一家企业，目前有10个人，但暂时没有每个人的具体资料。",
                 provider=FakeProvider(), trust_service=_trust(), policies=[_real122()])
    assert out["extraction"].status == "ok"
    facts = [(f.field, f.value) for f in out["extraction"].facts]
    assert ("applicant_entity_type", "企业") in facts
    assert ("hired_persons", 10) in facts
    # 抽取事实均来自用户（provenance）
    assert all(f.source == "user" for f in out["extraction"].facts)
    e = _exec_for(out)
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["benefit"]["calculated_amount"] == 0
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 0
    # 绝不能变成 15000
    assert e["benefit"]["calculated_amount"] != 15000


# ── E2E B：缺主体类型，声称 7人符合 → 保持 UNKNOWN / UNABLE ──
def test_e2e_B_missing_entity_unknown():
    out = assess("我们现在有10个人，其中7个人应该符合条件。",
                 provider=FakeProvider(), trust_service=_trust(), policies=[_real122()])
    e = _exec_for(out)
    assert e["eligibility"]["overall"] == "UNKNOWN"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"
    # 即便有 user_stated_eligible_count，也不能变成 qualified
    assert e["benefit"]["input_values"].get("eligible_hired_persons", 0) == 0


# ── 反绕过：user_stated_eligible_count=7 不得成为 eligible_hired_persons ──
def test_user_stated_eligible_count_not_bypass():
    class _Prov:
        def complete(self, *, system, user):
            facts = [
                {"field": "applicant_entity_type", "value": "企业",
                 "source": "user", "source_text": "企业"},
                {"field": "hired_persons", "value": 10,
                 "source": "user", "source_text": "10个人"},
                {"field": "user_stated_eligible_count", "value": 7,
                 "source": "user", "source_text": "7人符合"},
            ]
            return json.dumps({"facts": facts, "unresolved": []})

    out = assess("企业 10人 7人符合", provider=_Prov(),
                 trust_service=_trust(), policies=[_real122()])
    e = _exec_for(out)
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculated_amount"] == 0
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 0
    # 关键断言：入口/抽取层不得把用户声明数当作最终合格人数
    assert e["benefit"]["input_values"].get("eligible_hired_persons") != 7
    # user_stated_eligible_count 仅作为元数据保留，不是执行输入
    assert "user_stated_eligible_count" in out["project_inputs"]


# ── E2E C：个体工商户 → FAIL / UNABLE ──
def test_e2e_C_individual_fail():
    out = assess("我是个体工商户，有10个人。",
                 provider=FakeProvider(), trust_service=_trust(), policies=[_real122()])
    e = _exec_for(out)
    assert e["eligibility"]["overall"] == "FAIL"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"


# ── E2E D：企业 + 10人，7人完整逐人事实 → PASS / 7 / 10500 ──
def test_e2e_D_per_person_full():
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

    out = assess("企业 10人 7人完整", provider=_DPersonProv(),
                 trust_service=_trust(), policies=[_real122()])
    e = _exec_for(out)
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["benefit"]["calculated_amount"] == 10500
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 7


# ── 回归：入口不得自行计算 eligibility / benefit / eligible_hired_persons ──
def test_entry_does_not_self_compute():
    out = assess("我们是一家企业，目前有10个人，但暂时没有每个人的具体资料。",
                 provider=FakeProvider(), trust_service=_trust(), policies=[_real122()])
    e = _exec_for(out)
    # benefit 由确定性引擎产出（含 calculation_status / limitations / input_values），
    # 而非入口硬编码
    assert "calculation_status" in e["benefit"]
    assert "limitations" in e
    assert "input_values" in e["benefit"]
    # 入口未注入任何自算的 eligible_hired_persons（值来自 derive_eligible_hired_persons）
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 0


# ── 入口不得 import legacy agent ──
def test_no_legacy_agent_import():
    import global_policy_aggregator.web.production_nl_entry as mod
    src = open(mod.__file__, encoding="utf-8").read()
    # 仅校验未出现实际 import 语句（docstring 中仅作说明性引用）
    assert "import agents.policy_ai_agent" not in src
    assert "from agents.policy_ai_agent" not in src
    assert "import ai_agent_interface" not in src
    assert "from ai_agent_interface" not in src
    assert "investment_capacity_usd" not in src


# ── FastAPI 路由已注册 ──
def test_app_routes_registered():
    paths = [getattr(r, "path", None) for r in app.routes]
    assert "/api/nl/assess" in paths
    assert "/health" in paths


# ── load_real_policies 仅返回 REAL（is_mock=False）──
def test_load_real_policies_only_real():
    pols = load_real_policies()
    assert pols
    assert all(p.get("is_mock") is False for p in pols)
    assert any(p["id"] == 122 for p in pols)


# ── 生产边界：真实 LLM 不可用（缺 key）→ 结构化 fail-closed，不 500 / 不 fallback ──
def test_provider_unavailable_fail_closed():
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

    assert resp.status_code == 200
    body = resp.json()
    assert body["extraction"]["status"] == "EXTRACTION_FAILED"
    assert body["execution"] is None
    assert "provider unavailable" in body["extraction"]["error"].lower()

