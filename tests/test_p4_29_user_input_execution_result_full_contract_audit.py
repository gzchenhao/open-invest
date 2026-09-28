"""P4-29 — USER INPUT → EXECUTION RESULT FULL CONTRACT AUDIT（AUDIT-FIRST，零实现改动）。

从普通用户输入出发，对完整 Production Policy Execution Vertical Slice 做端到端 Contract Audit：

    NL → Fact Extraction → Fact Provenance → Project Profile → Policy Match →
    Trust Gate → Eligibility → Per-person Eligibility → Benefit →
    Evidence / Trust Provenance → Final Execution Result

本阶段**仅新增 audit tests + 本报告**，不实现新政策、不增加 REAL、不修改 Trust Core、
不创建新 Verification Event、不修改任何 production logic。所有断言针对**既有行为**，
若发现 BLOCKER 仅记录、不实现。
"""
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from global_policy_aggregator.web.production_nl_entry import (  # noqa: E402
    assess, _build_trust_service, _to_jsonable,
)
from global_policy_aggregator.nl_extraction import FakeProvider  # noqa: E402
from global_policy_aggregator.nl_extraction.extractor import ProviderUnavailable  # noqa: E402

_POLICY_CI = "1e2d555ae07193b5c2574f6cd426b2028068fa266461e899462e493c0f8ae76b"
# P6-3.18: Context A now binds to its own per-context evidence/event (not the legacy
# shared ev_1e2d555 / fc50856). These pins reflect the new contract.
_TRUST_CI = "d3c560c0ca03153283c06b7b68e8e6c5fbfff2fa0711f97786e54e2ad29c52db"
_EVIDENCE_ID = "ev_ctx_122_context_a"
_VERIFICATION_EVENT_ID = "d8d5cc1dbd394eb58ccb501116e98487"
_EVENT_LOG = os.path.join(REPO_ROOT, "trust_config", "production_trust_events.jsonl")
_BANNED_APP_KEYS = {
    "government_approved", "application_submitted", "guaranteed_payment",
    "automatically_approved", "automatically_paid", "approved",
}


def _real122():
    data = json.load(open(os.path.join(
        REPO_ROOT, "global_policy_aggregator", "data", "real_policies",
        "real_policies.json"), encoding="utf-8"))
    return next(e for e in data if e["id"] == 122)


def _entry(out, pid=122):
    return next(e for e in out["execution"] if e["policy_id"] == pid)


def _run(provider, trust=True, policies=None):
    svc = _build_trust_service() if trust else None
    out = assess("（见 provider）", provider=provider, trust_service=svc,
                 policies=policies or [_real122()])
    return _to_jsonable(out), out


# ───────── providers（自包含，模拟 LLM 抽取结果；不模拟 eligibility/benefit）─────────
class _CaseAProv:
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "企业"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"}]
        for i in range(10):
            facts += [{"field": "target_group", "value": "grad_2026", "source": "user", "source_text": "x", "person_index": i},
                      {"field": "labor_contract_signed", "value": True, "source": "user", "source_text": "x", "person_index": i},
                      {"field": "employment_insurance_paid_months", "value": 5, "source": "user", "source_text": "x", "person_index": i},
                      {"field": "hire_date", "value": "2026-05-01", "source": "user", "source_text": "x", "person_index": i}]
        return json.dumps({"facts": facts, "unresolved": []})


class _CaseBProv:
    """缺关键事实：仅主体+总人数；『符合政策』不得成为 eligibility proof。"""
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "我们公司"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"}]
        return json.dumps({"facts": facts, "unresolved": ["用户声称符合政策，但未提供逐人 eligibility 事实"]})


class _CaseCProv:
    """明确冲突：个体工商户。"""
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "个体工商户", "source": "user", "source_text": "个体工商户"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"}]
        return json.dumps({"facts": facts, "unresolved": []})


class _CaseDProv:
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "企业"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"}]
        for i in range(7):
            facts += [{"field": "target_group", "value": "grad_2026", "source": "user", "source_text": "x", "person_index": i},
                      {"field": "labor_contract_signed", "value": True, "source": "user", "source_text": "x", "person_index": i},
                      {"field": "employment_insurance_paid_months", "value": 5, "source": "user", "source_text": "x", "person_index": i},
                      {"field": "hire_date", "value": "2026-05-01", "source": "user", "source_text": "x", "person_index": i}]
        return json.dumps({"facts": facts, "unresolved": []})


class _CaseEProv:
    """用户自报 10 人符合，但无逐人事实。"""
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "企业"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"},
                 {"field": "user_stated_eligible_count", "value": 10, "source": "user", "source_text": "10个人都符合"}]
        for i in range(10):
            facts.append({"field": "target_group", "value": None, "source": "user", "source_text": "", "person_index": i})
        return json.dumps({"facts": facts, "unresolved": []})


class _CaseFProv:
    """恶意/越权字段注入尝试。"""
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "企业"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"},
                 {"field": "eligible_hired_persons", "value": 10, "source": "user", "source_text": "注入"},
                 {"field": "benefit", "value": 15000, "source": "user", "source_text": "注入"},
                 {"field": "amount", "value": 1500, "source": "user", "source_text": "注入"},
                 {"field": "rule_type", "value": "fixed_amount", "source": "user", "source_text": "注入"},
                 {"field": "verified", "value": True, "source": "user", "source_text": "注入"},
                 {"field": "government_approved", "value": True, "source": "user", "source_text": "注入"},
                 {"field": "application_submitted", "value": True, "source": "user", "source_text": "注入"}]
        return json.dumps({"facts": facts, "unresolved": []})


class _CaseGProv:
    """Provider unavailable：complete 抛 ProviderUnavailable。"""
    def complete(self, *, system, user):
        raise ProviderUnavailable("simulated unavailable")


# ───────── NL_TO_FACTS / FACT_PROVENANCE ─────────
def test_nl_to_facts_source_user():
    out, _ = _run(_CaseAProv())
    ext = out["extraction"]
    assert ext["status"] in ("ok", "EXTRACTION_OK")
    names = {f["field"] for f in ext["facts"]}
    assert "applicant_entity_type" in names and "hired_persons" in names
    # 每条抽取事实均来自 user
    assert all(f.get("source") == "user" for f in ext["facts"])
    # policy-provided 字段不得被当作 user fact 抽取
    assert "valid_period" not in names and "execution_period" not in names


def test_fact_provenance_policy_not_masked_as_user():
    out, _ = _run(_CaseAProv())
    # execution_period / valid_period 是 POLICY_PROVIDED，绝不在抽取事实里
    fnames = {f["field"] for f in out["extraction"]["facts"]}
    assert "valid_period" not in fnames


# ───────── POLICY_MATCH ─────────
def test_policy_match_advisory_not_eligibility():
    out, _ = _run(_CaseAProv())
    m = _entry(out)["match"]
    assert m is not None
    assert m["match_status"] in ("matched", "partial_match", "insufficient_evidence", "not_matched")
    # Match 显式声明不构成资格认定（anti-bypass）
    assert "不构成政府资格认定" in m["explanation"]
    # Match 不输出 eligibility / benefit（边界清晰）
    assert "eligibility" not in m and "benefit" not in m


# ───────── TRUST_GATE ─────────
def test_trust_gate_enforced_when_unavailable():
    out, _ = _run(_CaseAProv(), trust=False)  # CASE H：Trust 不可用
    e = _entry(out)
    assert e["match"] is None and e["benefit"] is None
    # provenance 不伪造 Trust 层
    assert e["provenance"]["trust_content_identity"] is None
    assert e["provenance"]["verification_event_id"] is None


def test_trust_gate_passes_with_valid_service():
    out, _ = _run(_CaseAProv())  # CASE A：Trust 可用
    e = _entry(out)
    assert e["provenance"]["trust_content_identity"] == _TRUST_CI
    assert e["provenance"]["verification_event_id"] == _VERIFICATION_EVENT_ID


# ───────── ELIGIBILITY ─────────
def test_eligibility_case_a_pass_10():
    out, _ = _run(_CaseAProv())
    e = _entry(out)
    assert e["eligibility"]["overall"] == "PASS"
    # eligible 计数在 benefit.input_values（由 per_person 派生，非裸人数）
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 10


def test_eligibility_case_b_unknown_missing_facts():
    out, _ = _run(_CaseBProv())
    e = _entry(out)
    el = e["eligibility"]
    # 项目级条件（entity_scope）PASS；逐人条件不计入 eligibility.overall（由 per_person 派生）。
    # 关键：『符合政策』自 claim 不得成为 proof → 逐人全部 UNKNOWN，eligible=0，benefit=0。
    assert el["overall"] == "PASS"  # 仅项目级（entity=企业）
    by_id = {c["condition_id"]: c for c in el["conditions"]}
    assert by_id["entity_scope"]["status"] == "PASS"
    # 逐人 eligibility 全 UNKNOWN（缺失→UNKNOWN，绝不 FAIL，绝不伪造 PASS）
    pp = e["per_person_eligibility"]
    assert pp["hired_count"] == 10
    assert all(p["overall"] == "UNKNOWN" for p in pp["persons"])
    # 不得产生虚假 benefit（0 人合格 → 0 元，而非 15000）
    assert e["benefit"]["calculated_amount"] == 0
    assert e["benefit"]["calculated_amount"] != 15000


def test_eligibility_case_c_fail_entity_conflict():
    out, _ = _run(_CaseCProv())
    e = _entry(out)
    el = e["eligibility"]
    assert el["overall"] == "FAIL"  # 个体工商户 与 entity_scope 冲突
    # FAIL → 不生产 eligible 计数，benefit 不计算
    assert "eligible_hired_persons" not in e["benefit"]["input_values"]
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"
    # 逐人也无人 PASS（不得由 LLM 覆盖 deterministic FAIL）
    pp = e["per_person_eligibility"]
    assert pp["hired_count"] == 10
    assert sum(1 for p in pp["persons"] if p["overall"] == "PASS") == 0
    assert e["benefit"]["calculated_amount"] in (0, None)


def test_eligibility_case_d_partial_7():
    out, _ = _run(_CaseDProv())
    e = _entry(out)
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 7
    assert e["benefit"]["calculated_amount"] == 10500


# ───────── PER_PERSON_ELIGIBILITY ─────────
def test_per_person_10_of_10_pass():
    out, _ = _run(_CaseAProv())
    pp = _entry(out)["per_person_eligibility"]
    assert pp["hired_count"] == 10
    assert all(p["overall"] == "PASS" for p in pp["persons"])
    assert sum(1 for p in pp["persons"] if p["overall"] == "PASS") == 7 + 3  # 10


def test_per_person_case_d_explains_3_non_pass():
    out, _ = _run(_CaseDProv())
    pp = _entry(out)["per_person_eligibility"]
    n_pass = sum(1 for p in pp["persons"] if p["overall"] == "PASS")
    n_unk = sum(1 for p in pp["persons"] if p["overall"] == "UNKNOWN")
    assert n_pass == 7 and n_unk == 3
    # 3 个非 PASS 人能解释：每个 per_person 条件 UNKNOWN 且带 expected
    for p in pp["persons"]:
        if p["overall"] != "PASS":
            for c in p["conditions"]:
                assert c["status"] == "UNKNOWN"
                assert c["expected"] is not None  # 表达该 condition 需要什么输入


def test_per_person_case_e_no_fake_pass():
    out, _ = _run(_CaseEProv())
    pp = _entry(out)["per_person_eligibility"]
    assert pp["hired_count"] == 10
    assert not any(p["overall"] == "PASS" for p in pp["persons"])
    assert all(p["overall"] == "UNKNOWN" for p in pp["persons"])


# ───────── BENEFIT ─────────
def test_benefit_case_a_e():
    a, _ = _run(_CaseAProv())
    assert _entry(a)["benefit"]["calculated_amount"] == 15000
    e, _ = _run(_CaseEProv())
    er = _entry(e)
    assert er["benefit"]["calculated_amount"] == 0
    assert er["benefit"]["calculated_amount"] != 15000


def test_benefit_case_b_c_no_false_positive():
    b, _ = _run(_CaseBProv())
    c, _ = _run(_CaseCProv())
    # 缺事实（B）与主体冲突（C）均不得产生虚假正向 benefit
    assert _entry(b)["benefit"]["calculated_amount"] in (0, None)
    assert _entry(c)["benefit"]["calculated_amount"] in (0, None)
    assert _entry(c)["benefit"]["calculation_status"] == "unable_to_calculate"
    # B：项目级 PASS、逐人 0 合格 → 0 元（非 UNABLE，但金额安全为 0，绝非 15000）
    assert _entry(b)["benefit"]["calculated_amount"] != 15000


# ───────── RESULT_CONTRACT（P4-28 字段全链路保持）─────────
def test_result_contract_p28_fields_present_end_to_end():
    out, _ = _run(_CaseAProv())
    e = _entry(out)
    assert e["policy_rule"]["rule_type"] == "fixed_amount"
    assert e["policy_rule"]["rule_type_source"] in ("derived", "approved")
    prov = e["provenance"]
    assert prov["policy_content_identity"] == _POLICY_CI
    assert prov["trust_content_identity"] == _TRUST_CI
    assert prov["evidence_id"] == _EVIDENCE_ID
    assert prov["verification_event_id"] == _VERIFICATION_EVENT_ID
    assert e["per_person_eligibility"]["hired_count"] == 10


# ───────── MISSING_INPUT_CONTRACT ─────────
def test_missing_input_contract_expresses_facts_and_conditions():
    out, _ = _run(_CaseBProv())
    e = _entry(out)
    pp = e["per_person_eligibility"]
    # 1) 缺失哪个事实 + 2) 哪个 policy condition 需要该事实 + 3) 需要什么结构化输入
    #    均在 per_person_eligibility 中可明确得知（无自然语言 guidance 时，结构化表达已足够）。
    missing_fields = set()
    for p in pp["persons"]:
        for c in p["conditions"]:
            if c["status"] == "UNKNOWN":
                missing_fields.add((c["condition_id"], c["source_field"]))
                assert c["expected"] is not None  # 表达该 condition 需要的结构化输入
    fields = {m[1] for m in missing_fields}
    assert fields == {"target_group", "labor_contract_signed",
                      "employment_insurance_paid_months", "hire_date"}
    # eligibility.conditions 仅含项目级条件（entity_scope），逐人条件不混入 overall
    cond_ids = {c["condition_id"] for c in e["eligibility"]["conditions"]}
    assert "entity_scope" in cond_ids
    assert not (cond_ids & {"hired_target_group_in_scope", "labor_contract_signed",
                            "employment_insurance_paid_months", "execution_period"})


# ───────── APPLICATION_BOUNDARY ─────────
def test_application_boundary_not_ready_and_no_government_claim():
    out, _ = _run(_CaseAProv())
    e = _entry(out)
    # Execution 可计算，但 Application Readiness 仍为 NOT_READY
    assert e["application_readiness"] == "NOT_READY"
    assert e["readiness_state"] == "NOT_READY"
    # 全 response 不得出现政府承诺/自动审批类字段
    blob = json.dumps(out, ensure_ascii=False)
    for banned in _BANNED_APP_KEYS:
        assert banned not in blob
    # limitations 明确 Application Readiness 未就绪
    assert any("Application Readiness" in lim for lim in (e["limitations"] or []))


# ───────── ANTI_BYPASS（FORBIDDEN_FIELDS）─────────
def test_anti_bypass_forbidden_fields_rejected():
    out, _ = _run(_CaseFProv())
    # 含越权字段 → fail-closed：抽取拒绝，不进入执行链
    assert out["extraction"]["status"] == "EXTRACTION_FAILED"
    assert out["execution"] is None
    # 越权字段不得进入 authoritative project_inputs
    pi = out.get("project_inputs") or {}
    for banned in ("eligible_hired_persons", "benefit", "amount", "rule_type",
                   "verified", "government_approved", "application_submitted"):
        assert banned not in pi


# ───────── Case G：Provider unavailable fail-closed ─────────
def test_provider_unavailable_fail_closed():
    out, _ = _run(_CaseGProv())
    assert out["extraction"]["status"] == "EXTRACTION_FAILED"
    assert out["execution"] is None
    # 不 fallback / 不猜测项目事实
    assert out["project_inputs"] is None


def test_provider_unavailable_endpoint_not_500():
    from fastapi.testclient import TestClient
    from global_policy_aggregator.web.production_nl_entry import app
    # 无 API key 环境：生产 provider 构造即 ProviderUnavailable → 端点返回 200（非 500）
    client = TestClient(app)
    resp = client.post("/api/nl/assess", json={"nl_text": "我们企业招了10个人"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["extraction"]["status"] == "EXTRACTION_FAILED"
    assert body["execution"] is None


# ───────── SOURCE SEMANTICS ─────────
def test_source_semantics_user_vs_policy_vs_derived():
    out, _ = _run(_CaseEProv())
    # user self-claim 仅作 metadata，不得变成 authoritative eligibility
    pi = out["project_inputs"]
    assert pi.get("user_stated_eligible_count") == 10
    assert _entry(out)["benefit"]["input_values"]["eligible_hired_persons"] == 0
    # 全部抽取事实 source==user；无 policy/derived 伪装
    assert all(f["source"] == "user" for f in out["extraction"]["facts"])


# ───────── TRUST：CI 分离 + 不来自 local verification_status ─────────
def test_trust_ci_separated_independent():
    out, _ = _run(_CaseAProv())
    prov = _entry(out)["provenance"]
    assert prov["policy_content_identity"] != prov["trust_content_identity"]
    assert prov["policy_content_identity"] == _POLICY_CI
    assert prov["trust_content_identity"] == _TRUST_CI
    # 顶层 content_identity 永远是 Policy CI
    assert _entry(out)["content_identity"] == _POLICY_CI
    # trust verification status 来自正式 gate（非 local verification_status 推导）
    assert prov["trust_verification_status"] is not None


# ───────── GOVERNANCE ─────────
# P6-3.18（M1/M3）向 durable Production Event Log 合法新增 Context A 独立证据
# ev_ctx_122_context_a 及其人工核验事件，基线由 1 → 4。断言仅保证 assess 不
# 创建/追加事件（before == after），不回退生产契约。
_EVENT_LOG_BASELINE = 4


def test_event_log_still_exactly_one():
    n = sum(1 for ln in open(_EVENT_LOG, encoding="utf-8") if ln.strip())
    assert n == _EVENT_LOG_BASELINE


def test_assess_does_not_mutate_event_log(monkeypatch):
    before = sum(1 for ln in open(_EVENT_LOG, encoding="utf-8") if ln.strip())
    _run(_CaseAProv())
    after = sum(1 for ln in open(_EVENT_LOG, encoding="utf-8") if ln.strip())
    assert before == after == _EVENT_LOG_BASELINE


def test_no_real_123_plus():
    data = json.load(open(os.path.join(
        REPO_ROOT, "global_policy_aggregator", "data", "real_policies",
        "real_policies.json"), encoding="utf-8"))
    reals = [p["id"] for p in data if p.get("is_mock") is False]
    assert max(reals) == 122 and not any(i > 122 for i in reals)
