"""P4-27 — EXECUTION RESULT CONTRACT AUDIT（AUDIT-FIRST，仅新增测试 + 报告）。

不修改 production logic / REAL data / src.trust / Authority Registry / Event Log / 历史测试。
真实审计 /api/nl/assess 的最终 Production Response Contract（10 项 A–J + Case A–E）。

每项给出 PASS / FAIL / NON_BLOCKER 证据。发现的透明性缺口（rule_type / evidence_id /
Trust content_identity / 逐人解释 / hired_count 未暴露）登记为 NON_BLOCKER（执行正确性不受影响）。
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
from global_policy_aggregator.nl_extraction.contract import FORBIDDEN_FIELDS  # noqa: E402

_POLICY_CI = "1e2d555ae07193b5c2574f6cd426b2028068fa266461e899462e493c0f8ae76b"
# P6-3.18：Context A 现拥有独立证据 ev_ctx_122_context_a，其 Trust content_identity 为
# d3c560c0…（取代 legacy fc50856 / ev_1e2d555 共享绑定）。此为已正式改变的 production
# contract，审计引脚同步更新。
_TRUST_CI = "d3c560c0ca03153283c06b7b68e8e6c5fbfff2fa0711f97786e54e2ad29c52db"

# 过度承诺词（BLOCKER 级别）：出现任一即视为越界
_OVER_CLAIM = [
    "government approved", "guaranteed", "will receive", "application submitted",
    "automatically approved", "automatically paid", "政府批准", "保证获得", "将获得补贴",
    "自动批准", "自动发放", "政府承诺", "已批准发放",
]


def _real122() -> dict:
    data = json.load(open(os.path.join(
        REPO_ROOT, "global_policy_aggregator", "data", "real_policies",
        "real_policies.json"), encoding="utf-8"))
    return next(e for e in data if e["id"] == 122)


def _entry(out, pid=122):
    return next(e for e in out["execution"] if e["policy_id"] == pid)


def _run(text, provider, trust=True, policies=None):
    svc = _build_trust_service() if trust else None
    out = assess(text, provider=provider, trust_service=svc,
                 policies=policies or [_real122()])
    return _to_jsonable(out), out


# ───────── test providers（自包含，避免跨测试脆弱依赖）─────────
class _TenFullProv:
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "企业"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"}]
        for i in range(10):
            facts += [{"field": "target_group", "value": "grad_2026", "source": "user", "source_text": "x", "person_index": i},
                      {"field": "labor_contract_signed", "value": True, "source": "user", "source_text": "x", "person_index": i},
                      {"field": "employment_insurance_paid_months", "value": 5, "source": "user", "source_text": "x", "person_index": i},
                      {"field": "hire_date", "value": "2026-05-01", "source": "user", "source_text": "x", "person_index": i}]
        return json.dumps({"facts": facts, "unresolved": []})


class _SevenFullProv:
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "企业"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"}]
        for i in range(7):
            facts += [{"field": "target_group", "value": "grad_2026", "source": "user", "source_text": "x", "person_index": i},
                      {"field": "labor_contract_signed", "value": True, "source": "user", "source_text": "x", "person_index": i},
                      {"field": "employment_insurance_paid_months", "value": 5, "source": "user", "source_text": "x", "person_index": i},
                      {"field": "hire_date", "value": "2026-05-01", "source": "user", "source_text": "x", "person_index": i}]
        return json.dumps({"facts": facts, "unresolved": []})


class _UserStatedProv:
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "企业"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"},
                 {"field": "user_stated_eligible_count", "value": 10, "source": "user", "source_text": "10人符合"}]
        return json.dumps({"facts": facts, "unresolved": []})


class _ClaimNoPerPersonProv:
    """用户声称 10 人符合，但无逐人 eligibility facts。"""
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "企业"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"},
                 {"field": "user_stated_eligible_count", "value": 10, "source": "user", "source_text": "10人都符合"}]
        for i in range(10):
            facts.append({"field": "target_group", "value": None, "source": "user", "source_text": "", "person_index": i})
        return json.dumps({"facts": facts, "unresolved": []})


# ───────────────────────── A. PROJECT FACTS ─────────────────────────
def test_user_facts_labeled_source_user():
    out, _ = _run("企业 10人 全符合", _TenFullProv())
    for f in out["extraction"]["facts"]:
        assert f["source"] == "user"


def test_derived_facts_not_in_extraction():
    out, _ = _run("企业 10人 全符合", _TenFullProv())
    fields = {f["field"] for f in out["extraction"]["facts"]}
    leak = fields & FORBIDDEN_FIELDS
    assert not leak, f"derived/policy 字段泄漏进 user facts: {leak}"


def test_policy_facts_not_claimed_as_user():
    # 抽取契约禁止 amount/rule_type/percentage 等进入抽取结果
    out, _ = _run("企业 10人 全符合", _TenFullProv())
    fields = {f["field"] for f in out["extraction"]["facts"]}
    assert "amount" not in fields and "rule_type" not in fields and "percentage" not in fields


def test_unknown_facts_expressed():
    out, _ = _run("我们现在有10个人，其中7个人应该符合条件。", FakeProvider())
    e = _entry(out)
    assert e["eligibility"]["overall"] == "UNKNOWN"
    cond = e["eligibility"]["conditions"][0]
    assert cond["status"] == "UNKNOWN"
    assert "未提供" in cond["detail"] or "UNKNOWN" in cond["detail"]


# ───────────────────────── B. ELIGIBILITY RESULT ─────────────────────────
def test_eligibility_outcomes():
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    b, _ = _run("我们现在有10个人，其中7个人应该符合条件。", FakeProvider())
    c, _ = _run("我是个体工商户，有10个人。", FakeProvider())
    assert _entry(a)["eligibility"]["overall"] == "PASS"
    assert _entry(b)["eligibility"]["overall"] == "UNKNOWN"
    assert _entry(c)["eligibility"]["overall"] == "FAIL"


def test_each_condition_result_with_detail():
    c, _ = _run("我是个体工商户，有10个人。", FakeProvider())
    conds = _entry(c)["eligibility"]["conditions"]
    assert conds
    for cd in conds:
        assert "condition_id" in cd and "status" in cd and "detail" in cd
    fail = [cd for cd in conds if cd["status"] == "FAIL"]
    assert fail and "冲突" in fail[0]["detail"]


def test_unknown_not_auto_fail():
    b, _ = _run("我们现在有10个人，其中7个人应该符合条件。", FakeProvider())
    # 缺主体 → UNKNOWN，绝不被自动转成 FAIL
    assert _entry(b)["eligibility"]["overall"] == "UNKNOWN"


# ───────────────────────── C. ELIGIBLE PERSONS ─────────────────────────
def test_eligible_count_exposed():
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    d, _ = _run("企业 10人 7人完整", _SevenFullProv())
    ev, _ = _run("我们是一家企业，有10个人，这10个人都符合政策条件。", _ClaimNoPerPersonProv())
    assert _entry(a)["benefit"]["input_values"]["eligible_hired_persons"] == 10
    assert _entry(d)["benefit"]["input_values"]["eligible_hired_persons"] == 7
    assert _entry(ev)["benefit"]["input_values"]["eligible_hired_persons"] == 0


def test_user_stated_not_authoritative():
    ev, _ = _run("我们是一家企业，有10个人，这10个人都符合政策条件。", _ClaimNoPerPersonProv())
    # 用户声称 10 人符合但无逐人事实 → 不得得到 10 人 benefit
    assert _entry(ev)["benefit"]["calculated_amount"] == 0
    assert _entry(ev)["benefit"]["calculated_amount"] != 15000


def test_hired_count_not_echoed_in_execution_entry():
    # MISSING（NON_BLOCKER）：执行结果未回显 hired_count；仅 eligible 暴露
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    e = _entry(a)
    assert "hired_persons" not in e and "hired_count" not in e
    assert "hired_persons" not in e["benefit"]["input_values"]


def test_per_person_breakdown_absent():
    # MISSING（NON_BLOCKER）：逐人条件被 skip，response 不暴露每人 PASS/FAIL/UNKNOWN
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    conds = _entry(a)["eligibility"]["conditions"]
    per_person_ids = {"hired_target_group_in_scope", "labor_contract_signed",
                      "employment_insurance_paid_months", "execution_period"}
    assert all(c["condition_id"] not in per_person_ids for c in conds)


# ───────────────────────── D. BENEFIT RESULT ─────────────────────────
def test_benefit_amount_currency_unit():
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    b = _entry(a)["benefit"]
    assert b["calculation_status"] == "calculated"
    assert b["calculated_amount"] == 15000
    assert b["currency"] == "CNY"
    assert b["unit"]


def test_benefit_calculation_trace():
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    b = _entry(a)["benefit"]
    assert "1500" in (b["formula_applied"] or "")
    assert b["input_values"]["eligible_hired_persons"] == 10
    assert b["explanation"]
    assert b["evidence_refs"]


def test_rule_type_not_surfaced():
    # MISSING（NON_BLOCKER）：orchestrator 丢弃 evaluate_policy 的 rule_type
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    e = _entry(a)
    assert "rule_type" not in e
    assert "rule_type" not in e["benefit"]


# ───────────────────────── E. EVIDENCE / PROVENANCE ─────────────────────────
def test_policy_provenance_present():
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    e = _entry(a)
    assert e["policy_id"] == 122
    assert e["content_identity"] == _POLICY_CI
    assert e["snapshot_ref"].endswith("1e2d555ae07193b5c2574f6cd426b2028068fa266461e899462e493c0f8ae76b.html")
    assert e["source_url"].startswith("https://www.gov.cn/")


def test_policy_vs_trust_ci_not_mixed():
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    e = _entry(a)
    # Policy CI 与 Trust CI 必须位于**独立字段**，绝不混为一个字段（P4-28 关闭该缺口后，
    # 此断言由「未暴露」升级为「分离暴露」——严格更强，非放宽）。
    assert e["content_identity"] == _POLICY_CI
    assert e["provenance"]["policy_content_identity"] == _POLICY_CI
    assert e["provenance"]["trust_content_identity"] == _TRUST_CI
    # 顶层 content_identity 永远是 Policy CI，绝不可能是 Trust CI
    assert e["content_identity"] != _TRUST_CI
    # 两个 CI 在独立 key，且取值互不相同
    assert e["provenance"]["trust_content_identity"] != e["provenance"]["policy_content_identity"]


def test_trust_link_not_surfaced():
    # MISSING（NON_BLOCKER）：Trust evidence_id / Trust content_identity / verification event id
    # 未暴露在 response（Gate 仍强制，但对外不可见链路）。
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    e = _entry(a)
    assert "evidence_id" not in e
    assert "trust_content_identity" not in e
    assert "verification_event_id" not in e


def test_execution_requires_trust_gate():
    # Trust Gate 生效：trust_service=None → 生产记录 fail-closed → 不执行 Match/Benefit
    out, _ = _run("企业 10人 全符合", _TenFullProv(), trust=False)
    e = _entry(out)
    assert e["match"] is None and e["benefit"] is None


# ───────────────────────── F. TRUST SEMANTICS ─────────────────────────
def test_no_record_local_verified_leak():
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    flat = json.dumps(_to_jsonable(a), ensure_ascii=False).lower()
    for bad in ("verified", "trust_verified", "verification_status"):
        # 顶层不得出现“已验证”误导字段；抽取事实也不得含
        assert bad not in {k.lower() for k in a["execution"][0].keys()}


def test_no_approved_equals_verified_claim():
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    e = _entry(a)
    assert "human_approved" not in e
    assert "rule_type_status" not in e  # D4 分离对象未回显（NON_BLOCKER，但绝不误导）


# ───────────────────────── G. READINESS BOUNDARY ─────────────────────────
def test_three_readiness_independent():
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    e = _entry(a)
    # 执行可跑（benefit 已算）；Application Readiness 独立 = NOT_READY
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["application_readiness"] == "NOT_READY"
    # 整体 readiness 因 Application-only 缺口 = NOT_READY（非“政策不可执行”）
    assert e["readiness_state"] == "NOT_READY"
    flat = json.dumps(e, ensure_ascii=False).lower()
    assert "自动申请" not in flat and "政府已批准" not in flat


def test_application_not_ready_not_policy_unexecutable():
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    e = _entry(a)
    # Application NOT_READY 绝不能输出成“政策不可执行”：benefit 仍被计算
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["benefit"]["calculated_amount"] == 15000


# ───────────────────────── H. USER-FACING CLAIM BOUNDARY ─────────────────────────
@pytest.mark.parametrize("text,prov", [
    ("企业 10人 全符合", _TenFullProv()),
    ("我们现在有10个人，其中7个人应该符合条件。", FakeProvider()),
    ("我是个体工商户，有10个人。", FakeProvider()),
    ("企业 10人 7人完整", _SevenFullProv()),
    ("我们是一家企业，有10个人，这10个人都符合政策条件。", _ClaimNoPerPersonProv()),
])
def test_no_over_claim_in_response(text, prov):
    out, _ = _run(text, prov)
    flat = json.dumps(out, ensure_ascii=False).lower()
    hits = [w for w in _OVER_CLAIM if w in flat]
    assert not hits, f"over-claim words found: {hits}"


# ───────────────────────── I. MISSING INPUT UX CONTRACT ─────────────────────────
def test_unknown_expresses_missing_fact_and_condition():
    b, _ = _run("我们现在有10个人，其中7个人应该符合条件。", FakeProvider())
    e = _entry(b)
    cond = e["eligibility"]["conditions"][0]
    assert cond["status"] == "UNKNOWN" and "未提供" in cond["detail"]
    assert e["readiness_detail"]["missing_required"]


def test_unable_expresses_limitation():
    b, _ = _run("我们现在有10个人，其中7个人应该符合条件。", FakeProvider())
    e = _entry(b)
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"
    assert e["benefit"]["limitations"]


# ───────────────────────── J. API CONTRACT STABILITY ─────────────────────────
def test_stable_schema_keys_across_cases():
    cases = [
        ("企业 10人 全符合", _TenFullProv()),
        ("我们现在有10个人，其中7个人应该符合条件。", FakeProvider()),
        ("我是个体工商户，有10个人。", FakeProvider()),
        ("企业 10人 7人完整", _SevenFullProv()),
        ("我们是一家企业，有10个人，这10个人都符合政策条件。", _ClaimNoPerPersonProv()),
    ]
    keysets = []
    benefit_keysets = []
    for text, prov in cases:
        out, _ = _run(text, prov)
        e = _entry(out)
        keysets.append(frozenset(e.keys()))
        benefit_keysets.append(frozenset(e["benefit"].keys()))
    assert len(set(keysets)) == 1, "execution entry schema 不稳定"
    assert len(set(benefit_keysets)) == 1, "benefit schema 不稳定"
    # 顶层 response 结构稳定
    assert all(set(out.keys()) == {"extraction", "execution", "project_profile", "project_inputs"}
               for out, _ in [_run(t, p) for t, p in cases])
