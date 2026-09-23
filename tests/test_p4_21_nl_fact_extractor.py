"""P4-21 — NATURAL LANGUAGE FACT EXTRACTOR MVP 的 deterministic 测试。

对象：REAL 122（39号通知 Context A：一次性扩岗补助）
目标：验证 NL → user facts → 现有确定性执行链的最小装配，且：
- LLM 只抽取用户明确事实，绝不决定 eligibility / benefit / eligible_hired_persons。
- 禁止字段（eligible_hired_persons / eligibility / benefit / ...）被 fail-closed 拒绝。
- 抽取失败（非法 JSON / provider 不可用 / 空输入）不猜测、不 fallback。
- P4-18 回归（结构化输入直连 orchestrator）继续成立：A PASS/15000、B UNKNOWN/UNABLE、
  C FAIL/UNABLE、D 7/10500，且 LLM 抽取不能绕过现有 Eligibility Engine。

Provider 测试全部离线：用 FakeProvider（确定性 test double）模拟 LLM 结构化输出，
绝不调用真实 LLM API；FakeProvider 仅模拟抽取（不模拟 Eligibility/Benefit）。
"""
import json
import os

import pytest

from global_policy_aggregator.nl_extraction import (
    NaturalLanguageFactExtractor, FakeProvider, OpenAICompatibleProvider,
    ProviderUnavailable, ExtractionResult, ForbiddenFieldError,
    to_orchestrator_inputs, extract_and_evaluate, EXTRACTION_FAILED,
    NO_FACTS_EXTRACTED, EXTRACTION_OK, FORBIDDEN_FIELDS,
)
from global_policy_aggregator.pipeline.p4_execution_orchestrator import (
    evaluate_project_against_policies,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_PATH = os.path.join(
    REPO, "global_policy_aggregator", "data", "real_policies", "real_policies.json"
)


def _real122():
    d = json.loads(open(REAL_PATH, encoding="utf-8").read())
    return next(e for e in d if e["id"] == 122)


def _persons(n, eligible):
    return [
        {
            "target_group": "grad_2026" if i < eligible else "other",
            "labor_contract_signed": i < eligible,
            "employment_insurance_paid_months": 5 if i < eligible else 0,
            "hire_date": "2026-05-01" if i < eligible else "2025-05-01",
        }
        for i in range(n)
    ]


def _profile(entity="企业"):
    return {"applicant_entity_type": entity}


class _VerifiedTrustStub:
    """Faithful VERIFIED stub（同 P4-17）；不读写任何 Trust 文件。"""

    def __init__(self, evidence_id, verified_event_id):
        self._eid = evidence_id
        self._veid = verified_event_id

    def check_verified_validity(self, evidence_id):
        if evidence_id == self._eid:
            return {"is_valid": True,
                    "latest_verified_event": {"event_id": self._veid}}
        return {"is_valid": False, "reasons": ["evidence not verified"]}


def _trust():
    r = _real122()
    return _VerifiedTrustStub(r["evidence_id"], r["verified_event_id"])


def _extract(nl_text):
    """通过 extract_and_evaluate（注入 FakeProvider）得到 (extraction, execution)。"""
    out = extract_and_evaluate(nl_text, [_real122()], trust_service=_trust(),
                               provider=FakeProvider())
    return out["extraction"], out["execution"]


# ===================== A. 企业 + 10人（无逐人明细） =====================
def test_a_enterprise_10_persons():
    res, exec_ = _extract("我们是一家企业，今年招了10个人。")
    assert res.status == EXTRACTION_OK
    fields = {f.field: f.value for f in res.facts}
    assert fields["applicant_entity_type"] == "企业"
    assert fields["hired_persons"] == 10
    # LLM 只抽事实，未抽取任何资格/金额
    assert not any(f.field in FORBIDDEN_FIELDS for f in res.facts)

    e = exec_[0]
    # entity_scope PASS；10 人全无逐人明细 → 派生 eligible=0 → benefit=0（绝不 15000）
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["benefit"]["calculated_amount"] == 0
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 0
    # 证明：LLM 抽取不能把 10 人直接当成 eligible
    assert e["benefit"]["calculated_amount"] != 15000


# ===================== B. 10人 + 用户称7符合（不得直接当 eligible） =====================
def test_b_user_stated_7_not_eligible():
    res, exec_ = _extract("我们今年招了10个人，其中7个人已经符合政策规定。")
    assert res.status == EXTRACTION_OK
    fields = {f.field: f.value for f in res.facts}
    assert fields["hired_persons"] == 10
    assert fields["user_stated_eligible_count"] == 7
    # 用户声明 7 符合，但绝不映射成 eligible_hired_persons
    assert "eligible_hired_persons" not in fields

    e = exec_[0]
    # 未提供主体类型 → entity_scope UNKNOWN → 整体 UNKNOWN → benefit UNABLE
    assert e["eligibility"]["overall"] == "UNKNOWN"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"
    # 引擎执行输入中只保留 user_stated_eligible_count 元数据，不含 eligible_hired_persons
    prof, inputs = to_orchestrator_inputs(res)
    assert inputs.get("user_stated_eligible_count") == 7
    assert "eligible_hired_persons" not in inputs


# ===================== C. 个体工商户 + 10人（LLM 不得自判 FAIL） =====================
def test_c_individual_business_fail():
    res, exec_ = _extract("我们是个体工商户，今年招了10个人。")
    assert res.status == EXTRACTION_OK
    fields = {f.field: f.value for f in res.facts}
    assert fields["applicant_entity_type"] == "个体工商户"
    # LLM 只抽主体类型，未输出 FAIL 判定
    assert not any(f.field in FORBIDDEN_FIELDS for f in res.facts)

    e = exec_[0]
    # 由现有 Eligibility Engine 判定冲突 → FAIL
    assert e["eligibility"]["overall"] == "FAIL"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"


# ===================== D. 10人 + 其余自己判断（缺事实） =====================
def test_d_other_decide_unknown():
    res, exec_ = _extract("我们今年招了10个人，其他情况你自己判断。")
    assert res.status == EXTRACTION_OK
    fields = {f.field: f.value for f in res.facts}
    assert fields["hired_persons"] == 10
    assert res.unresolved  # 模型未补全，仅记录未提供

    e = exec_[0]
    assert e["eligibility"]["overall"] == "UNKNOWN"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"


# ===================== 禁止字段 fail-closed =====================
class _ReturningProvider:
    def __init__(self, payload):
        self._payload = payload

    def complete(self, *, system, user):
        return json.dumps(self._payload, ensure_ascii=False)


@pytest.mark.parametrize("bad_field", [
    "eligible_hired_persons", "eligibility", "benefit", "benefit_amount",
    "verification_status", "verified", "trust_verified", "government_approved",
    "real_policy_id", "approved", "policy_truth",
])
def test_forbidden_field_rejected_by_extractor(bad_field):
    payload = {"facts": [{"field": bad_field, "value": 10,
                          "source": "user", "source_text": "x"}], "unresolved": []}
    res = NaturalLanguageFactExtractor(_ReturningProvider(payload)).extract("任意文本")
    assert res.status == EXTRACTION_FAILED
    assert "禁止字段" in (res.error or "")


def test_forbidden_field_rejected_by_adapter():
    # 即使手工构造 ExtractionResult 混入禁止字段，adapter 也必须拒绝（深度防御）
    bad = ExtractionResult(EXTRACTION_OK, facts=[
        type("F", (), {"field": "eligible_hired_persons", "value": 10,
                       "source": "user", "source_text": "", "person_index": None})()
    ])
    with pytest.raises(ForbiddenFieldError):
        to_orchestrator_inputs(bad)


def test_unknown_field_rejected():
    payload = {"facts": [{"field": "mysterious_field", "value": 1,
                          "source": "user", "source_text": "x"}], "unresolved": []}
    res = NaturalLanguageFactExtractor(_ReturningProvider(payload)).extract("x")
    assert res.status == EXTRACTION_FAILED
    assert "契约" in (res.error or "")


def test_source_must_be_user():
    payload = {"facts": [{"field": "hired_persons", "value": 5,
                          "source": "llm_guess", "source_text": "x"}], "unresolved": []}
    res = NaturalLanguageFactExtractor(_ReturningProvider(payload)).extract("x")
    assert res.status == EXTRACTION_FAILED


# ===================== 抽取失败 fail-closed =====================
class _UnavailableProvider:
    def complete(self, *, system, user):
        raise ProviderUnavailable("network down")


def test_provider_unavailable_fail_closed():
    res = NaturalLanguageFactExtractor(_UnavailableProvider()).extract("我们是企业招了10人")
    assert res.status == EXTRACTION_FAILED
    assert "provider unavailable" in (res.error or "")


class _InvalidJsonProvider:
    def complete(self, *, system, user):
        return "这不是 JSON {{{"


def test_invalid_json_fail_closed():
    res = NaturalLanguageFactExtractor(_InvalidJsonProvider()).extract("我们是企业招了10人")
    assert res.status == EXTRACTION_FAILED
    assert "invalid JSON" in (res.error or "")


def test_empty_input_no_facts():
    res = NaturalLanguageFactExtractor(FakeProvider()).extract("   ")
    assert res.status == NO_FACTS_EXTRACTED


def test_openai_provider_requires_env_key():
    # 未设置 key → ProviderUnavailable（不 fallback 到 legacy heuristic）
    import importlib
    import global_policy_aggregator.nl_extraction.provider as P
    saved = os.environ.pop("OPENINVEST_LLM_API_KEY", None)
    try:
        with pytest.raises(ProviderUnavailable):
            P.OpenAICompatibleProvider()
    finally:
        if saved is not None:
            os.environ["OPENINVEST_LLM_API_KEY"] = saved


# ===================== P4-18 回归（结构化输入直连 orchestrator，不放松） =====================
def test_reg_a_full_pass():
    out = evaluate_project_against_policies(
        _profile(), [_real122()],
        project_inputs={"hired_persons": _persons(10, 10)}, trust_service=_trust())
    e = out[0]
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculated_amount"] == 15000
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 10


def test_reg_b_missing_entity_unknown():
    out = evaluate_project_against_policies(
        {}, [_real122()],
        project_inputs={"hired_persons": _persons(10, 10)}, trust_service=_trust())
    e = out[0]
    assert e["eligibility"]["overall"] == "UNKNOWN"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"


def test_reg_c_conflict_fail():
    out = evaluate_project_against_policies(
        _profile("个体工商户"), [_real122()],
        project_inputs={"hired_persons": _persons(10, 10)}, trust_service=_trust())
    e = out[0]
    assert e["eligibility"]["overall"] == "FAIL"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"


def test_reg_d_seven_of_ten():
    out = evaluate_project_against_policies(
        _profile(), [_real122()],
        project_inputs={"hired_persons": _persons(10, 7)}, trust_service=_trust())
    e = out[0]
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculated_amount"] == 10500
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 7


def test_reg_llm_cannot_bypass_engine():
    # NL 抽取（企业 + 10人，无逐人明细）得到 benefit=0；结构化全明细才得 15000。
    # 证明 LLM 抽取不能绕过现有 Eligibility Engine。
    _, nl_exec = _extract("我们是一家企业，今年招了10个人。")
    assert nl_exec[0]["benefit"]["calculated_amount"] == 0

    full = evaluate_project_against_policies(
        _profile(), [_real122()],
        project_inputs={"hired_persons": _persons(10, 10)}, trust_service=_trust())
    assert full[0]["benefit"]["calculated_amount"] == 15000
