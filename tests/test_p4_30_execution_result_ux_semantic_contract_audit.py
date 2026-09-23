"""P4-30 — EXECUTION RESULT UX / SEMANTIC CONTRACT AUDIT（AUDIT-FIRST，零实现改动）。

面向**最终用户语义清晰度 / 可误解性**的端到端语义契约审计。不重新设计 Rule Engine、
不修改生产逻辑、不修改 src/trust / real_policies / 历史测试。

真实驱动方式与 P4-29 一致：每个 Case 用确定性 FakeProvider（仅把显式用户文本映射为合法
user-facts JSON，绝不模拟 Eligibility/Benefit），注入 ``assess()``，断言**真实** NL→Result 链路。

本文件断言全部基于既有行为；发现的语义/UX 风险仅记录为 NON_BLOCKER（并在报告给代码位置 + 测试证据）。
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
_TRUST_CI = "b4012feb48e86e999b3149eb42fd62d91f1a8049e22daeda24d9dd4a89292937"
_EVENT_LOG = os.path.join(REPO_ROOT, "trust_config", "production_trust_events.jsonl")
# 真正暗示「政府批准/已提交/保付/自动拨付」的字段名（KEY 级精确匹配，不做子串）。
# 说明：``approved``（rule_type_status.approved，Rule Type 人工批准）、``verified``/
# ``Trust VERIFIED``（Trust human verifier 验证状态）属合法治理字段，非政府审批，
# 不做禁用；其可能的用户误读作为 NON_BLOCKER 在报告中记录。
_BANNED_APP_KEYS = {
    "government_approved", "application_submitted", "guaranteed_payment",
    "automatically_approved", "automatically_paid",
}


def _all_keys(obj):
    """递归产出所有 dict 的 KEY（用于字段级精确禁用检查）。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _all_keys(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _all_keys(v)

# 已知状态词表（D5 校验用，防止出现 ad-hoc 状态串）
_VOCAB = {
    "PASS", "FAIL", "UNKNOWN", "N/A",
    "calculated", "unable_to_calculate",
    "NOT_READY", "READY", "EXECUTION_READY", "PARTIAL",
    "matched", "partial_match", "insufficient_evidence", "not_matched",
    "MATCHED", "INSUFFICIENT_EVIDENCE", "NO_MATCH",
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


# ───────── providers（自包含，与 P4-29 一致）─────────
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
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "我们公司"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"}]
        return json.dumps({"facts": facts, "unresolved": ["用户声称符合政策，但未提供逐人 eligibility 事实"]})


class _CaseCProv:
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
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "企业"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"},
                 {"field": "user_stated_eligible_count", "value": 10, "source": "user", "source_text": "10个人都符合"}]
        for i in range(10):
            facts.append({"field": "target_group", "value": None, "source": "user", "source_text": "", "person_index": i})
        return json.dumps({"facts": facts, "unresolved": []})


class _CaseFProv:
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
    def complete(self, *, system, user):
        raise ProviderUnavailable("simulated unavailable")


# ───────── D1：eligibility.overall 仅项目级；per_person_eligibility 才是逐人 ─────────
def test_d1_eligibility_overall_is_project_level_only():
    out, _ = _run(_CaseBProv())
    e = _entry(out)
    el = e["eligibility"]
    # overall 仅由项目级条件（entity_scope）决定
    assert el["overall"] == "PASS"
    cond_ids = {c["condition_id"] for c in el["conditions"]}
    assert cond_ids == {"entity_scope"}  # 不含任何 per_person 条件
    # 逐人资格在独立字段 per_person_eligibility，不与 eligibility.overall 合并
    assert e["per_person_eligibility"] is not None
    pp_ids = {c["condition_id"] for p in e["per_person_eligibility"]["persons"]
              for c in p["conditions"]}
    assert pp_ids == {"hired_target_group_in_scope", "labor_contract_signed",
                      "employment_insurance_paid_months", "execution_period"}
    # 两层字段名物理分离（避免 UI 把 project PASS 误读为全员合格）
    assert "entity_scope" not in pp_ids and "hired_target_group_in_scope" not in cond_ids


def test_d1_eligible_count_reflects_per_person_not_project_overall():
    b, _ = _run(_CaseBProv())
    a, _ = _run(_CaseAProv())
    # 即便 eligibility.overall=PASS（项目级），benefit 用逐人派生计数（B=0，A=10）
    assert _entry(b)["benefit"]["input_values"]["eligible_hired_persons"] == 0
    assert _entry(a)["benefit"]["input_values"]["eligible_hired_persons"] == 10
    # benefit 金额与逐人计数一致，不随 eligibility.overall 走
    assert _entry(b)["benefit"]["calculated_amount"] == 0
    assert _entry(a)["benefit"]["calculated_amount"] == 15000


# ───────── D2：Benefit status 语义 ─────────
def test_d2_benefit_status_vocabulary():
    a, _ = _run(_CaseAProv())
    b, _ = _run(_CaseBProv())
    c, _ = _run(_CaseCProv())
    d, _ = _run(_CaseDProv())
    assert _entry(a)["benefit"]["calculation_status"] == "calculated"
    assert _entry(a)["benefit"]["calculated_amount"] == 15000
    assert _entry(b)["benefit"]["calculation_status"] == "calculated"
    assert _entry(b)["benefit"]["calculated_amount"] == 0
    assert _entry(c)["benefit"]["calculation_status"] == "unable_to_calculate"
    assert _entry(c)["benefit"]["calculated_amount"] is None
    assert _entry(d)["benefit"]["calculation_status"] == "calculated"
    assert _entry(d)["benefit"]["calculated_amount"] == 10500
    # 不存在 PARTIAL / unknown 等中间 benefit 状态
    for prov in (a, b, c, d):
        assert _entry(prov)["benefit"]["calculation_status"] in ("calculated", "unable_to_calculate")


def test_d2_calculated_zero_signal_completeness_via_per_person():
    b, _ = _run(_CaseBProv())
    e = _entry(b)
    # calculated+0 可能读成「已算完=0」；系统通过 per_person_eligibility 揭示不完整
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["benefit"]["calculated_amount"] == 0
    assert all(p["overall"] == "UNKNOWN" for p in e["per_person_eligibility"]["persons"])


# ───────── D3：Missing-input contract（可推导下一步补什么）─────────
def test_d3_missing_per_person_fields_derivable():
    b, _ = _run(_CaseBProv())
    pp = _entry(b)["per_person_eligibility"]
    missing = set()
    for p in pp["persons"]:
        for c in p["conditions"]:
            if c["status"] == "UNKNOWN":
                assert c["expected"] is not None
                missing.add(c["source_field"])
    assert missing == {"target_group", "labor_contract_signed",
                        "employment_insurance_paid_months", "hire_date"}


def test_d3_benefit_unable_triggered_by_project_level_not_per_person():
    c, _ = _run(_CaseCProv())
    # entity 冲突（项目级）→ eligibility FAIL → benefit UNABLE；
    # 注意：逐人事实缺失（Case B）并不触发 benefit UNABLE（其 benefit=calculated/0）。
    assert _entry(c)["eligibility"]["overall"] == "FAIL"
    assert _entry(c)["benefit"]["calculation_status"] == "unable_to_calculate"
    b, _ = _run(_CaseBProv())
    assert _entry(b)["benefit"]["calculation_status"] != "unable_to_calculate"


# ───────── D4：三层关系（Match advisory / Eligibility 独立 / Benefit 确定性）─────────
def test_d4_match_advisory_not_eligibility_benefit():
    a, _ = _run(_CaseAProv())
    m = _entry(a)["match"]
    assert m is not None
    assert "eligibility" not in m and "benefit" not in m
    assert "不构成政府资格认定" in m["explanation"]


def test_d4_eligibility_independent_of_benefit():
    b, _ = _run(_CaseBProv())
    e = _entry(b)
    # eligibility.overall=PASS（项目级）但 benefit 金额=0（逐人派生），二者解耦
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculated_amount"] == 0
    assert e["benefit"]["calculation_status"] == "calculated"


def test_d4_benefit_only_when_deterministic():
    c, _ = _run(_CaseCProv())
    # eligibility != PASS → benefit 不计算（fail-closed，不猜测）
    assert _entry(c)["eligibility"]["overall"] == "FAIL"
    assert _entry(c)["benefit"]["calculation_status"] == "unable_to_calculate"
    assert _entry(c)["benefit"]["calculated_amount"] is None


# ───────── D5：状态词表 ─────────
def test_d5_status_vocabulary_known():
    for prov in (_CaseAProv(), _CaseBProv(), _CaseCProv(), _CaseDProv(), _CaseEProv()):
        out, _ = _run(prov)
        e = _entry(out)
        # eligibility.overall / per_person overall / condition status
        assert e["eligibility"]["overall"] in ("PASS", "FAIL", "UNKNOWN", "N/A")
        for p in e["per_person_eligibility"]["persons"]:
            assert p["overall"] in ("PASS", "FAIL", "UNKNOWN")
            for c in p["conditions"]:
                assert c["status"] in ("PASS", "FAIL", "UNKNOWN", "N/A")
        assert e["benefit"]["calculation_status"] in ("calculated", "unable_to_calculate")
        assert e["readiness_state"] in ("NOT_READY", "PARTIAL", "EXECUTION_READY")
        assert e["application_readiness"] in ("NOT_READY", "READY")
        assert e["match"]["match_status"] in _VOCAB


# ───────── D6：Provenance 呈现（Policy CI ≠ Trust CI；无政府审批暗示）─────────
def test_d6_policy_ci_trust_ci_independent():
    a, _ = _run(_CaseAProv())
    prov = _entry(a)["provenance"]
    assert prov["policy_content_identity"] == _POLICY_CI
    assert prov["trust_content_identity"] == _TRUST_CI
    assert prov["policy_content_identity"] != prov["trust_content_identity"]
    # 顶层 content_identity 恒为 Policy CI
    assert _entry(a)["content_identity"] == _POLICY_CI


def test_d6_no_gov_approval_in_provenance():
    a, _ = _run(_CaseAProv())
    keys = set(_all_keys(_entry(a)["provenance"]))
    assert not (_BANNED_APP_KEYS & keys)
    # trust_verification_status 仅表示 Trust VERIFIED（human verifier），非政府审批
    assert _entry(a)["provenance"]["trust_verification_status"] is not None


def test_d6_policy_provenance_present_without_trust():
    h, _ = _run(_CaseAProv(), trust=False)  # Case H：Trust 不可用
    e = _entry(h)
    # Policy provenance 仍完整；Trust provenance 不伪造（None）
    assert e["provenance"]["policy_content_identity"] == _POLICY_CI
    assert e["provenance"]["trust_content_identity"] is None
    assert e["provenance"]["verification_event_id"] is None
    assert e["provenance"]["verifier_id"] is None


# ───────── D7：Application boundary ─────────
def test_d7_application_readiness_not_ready_everywhere():
    for prov, trust in ((_CaseAProv(), True), (_CaseBProv(), True), (_CaseCProv(), True),
                        (_CaseDProv(), True), (_CaseEProv(), True), (_CaseAProv(), False)):
        out, _ = _run(prov, trust=trust)
        e = _entry(out)
        assert e["application_readiness"] == "NOT_READY"
        assert e["readiness_state"] in ("NOT_READY", "PARTIAL", "EXECUTION_READY")


def test_d7_no_government_claim_in_full_response():
    a, _ = _run(_CaseAProv())
    keys = set(_all_keys(a))
    assert not (_BANNED_APP_KEYS & keys)


# ───────── D8：逐 Case 用户可误解性检查 ─────────
def test_d8a_complete_not_misleading():
    a, _ = _run(_CaseAProv())
    e = _entry(a)
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 10
    assert e["benefit"]["calculated_amount"] == 15000
    assert sum(1 for p in e["per_person_eligibility"]["persons"] if p["overall"] == "PASS") == 10


def test_d8b_missing_facts_not_misleading():
    b, _ = _run(_CaseBProv())
    e = _entry(b)
    # 不把「符合政策」当 proof：eligible=0、benefit=0、逐人全 UNKNOWN
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 0
    assert e["benefit"]["calculated_amount"] == 0
    assert all(p["overall"] == "UNKNOWN" for p in e["per_person_eligibility"]["persons"])
    # 抽取事实中无“符合政策”被当作 eligibility 证据
    assert "符合政策" not in json.dumps(e["per_person_eligibility"], ensure_ascii=False)


def test_d8c_conflict_clear_fail():
    c, _ = _run(_CaseCProv())
    e = _entry(c)
    assert e["eligibility"]["overall"] == "FAIL"
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"
    by_id = {x["condition_id"]: x for x in e["eligibility"]["conditions"]}
    assert by_id["entity_scope"]["status"] == "FAIL"


def test_d8d_partial_explained():
    d, _ = _run(_CaseDProv())
    e = _entry(d)
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 7
    assert e["benefit"]["calculated_amount"] == 10500
    n_pass = sum(1 for p in e["per_person_eligibility"]["persons"] if p["overall"] == "PASS")
    n_unk = sum(1 for p in e["per_person_eligibility"]["persons"] if p["overall"] == "UNKNOWN")
    assert n_pass == 7 and n_unk == 3
    for p in e["per_person_eligibility"]["persons"]:
        if p["overall"] != "PASS":
            for c in p["conditions"]:
                assert c["status"] == "UNKNOWN" and c["expected"] is not None


def test_d8e_self_claim_no_fake_benefit():
    e_out, _ = _run(_CaseEProv())
    e = _entry(e_out)
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 0
    assert e["benefit"]["calculated_amount"] == 0
    # user_stated 仅作 metadata，不进入 authoritative eligible
    assert e_out["project_inputs"].get("user_stated_eligible_count") == 10
    assert all(p["overall"] == "UNKNOWN" for p in e["per_person_eligibility"]["persons"])


def test_d8f_forbidden_blocked():
    f, _ = _run(_CaseFProv())
    assert f["extraction"]["status"] == "EXTRACTION_FAILED"
    assert f["execution"] is None


def test_d8g_provider_unavailable_fail_closed():
    g, _ = _run(_CaseGProv())
    assert g["extraction"]["status"] == "EXTRACTION_FAILED"
    assert g["execution"] is None


def test_d8h_trust_unavailable_no_fake():
    h, _ = _run(_CaseAProv(), trust=False)
    e = _entry(h)
    assert e["match"] is None and e["benefit"] is None
    assert e["provenance"]["trust_content_identity"] is None
    # 但 Policy 层如实可消费（非伪造）
    assert e["provenance"]["policy_content_identity"] == _POLICY_CI


# ───────── D9：Governance（纯只读；不改动 production）─────────
def test_d9_event_log_still_one():
    n = sum(1 for ln in open(_EVENT_LOG, encoding="utf-8") if ln.strip())
    assert n == 1


def test_d9_no_real_123_plus():
    data = json.load(open(os.path.join(
        REPO_ROOT, "global_policy_aggregator", "data", "real_policies",
        "real_policies.json"), encoding="utf-8"))
    reals = [p["id"] for p in data if p.get("is_mock") is False]
    assert max(reals) == 122 and not any(i > 122 for i in reals)


def test_d9_assess_does_not_mutate_event_log():
    before = sum(1 for ln in open(_EVENT_LOG, encoding="utf-8") if ln.strip())
    _run(_CaseAProv())
    after = sum(1 for ln in open(_EVENT_LOG, encoding="utf-8") if ln.strip())
    assert before == after == 1
