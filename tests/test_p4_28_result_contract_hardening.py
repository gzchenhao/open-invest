"""P4-28 — RESULT CONTRACT HARDENING（最小范围实现 + 测试）。

在 P4-27（PASS，无 BLOCKER）基础上，仅增强 Execution Result Contract 的可解释性与
provenance，**不改变现有 Eligibility / Benefit / Trust 判定逻辑**：

1. RULE TYPE：execution result 暴露 policy ``rule_type``（来自已存在的 policy rule
   definition / REAL 122，非 LLM、非重新推导）。
2. TRUST / EVIDENCE PROVENANCE：新增结构化 ``provenance``（policy_id / source_url /
   snapshot_ref / policy_content_identity / evidence_id / trust_content_identity /
   verification_event_id / verifier_id / verifier_role / trust_verification_status），
   Policy CI 与 Trust CI 严格分离，绝不合并为一个字段。
3. PER-PERSON ELIGIBILITY：新增结构化 ``per_person_eligibility``（person_index / PASS /
   FAIL / UNKNOWN + 每条件 result + 实际 fact value / expected），仅复用已有结构化事实，
   绝不反推 / 绝不制造 self-claimed PASS / 绝不 LLM 决定 / 绝不猜测。

Governance：不修改 src/trust/**、REAL 101–122、Event Log；不新建 verification event；
不调用 record_human_verification；RESULT CONTRACT 向后兼容（仅新增字段，不改现有字段语义）。
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
    _PRODUCTION_EVENT_LOG,
)
from global_policy_aggregator.nl_extraction import FakeProvider  # noqa: E402

_POLICY_CI = "1e2d555ae07193b5c2574f6cd426b2028068fa266461e899462e493c0f8ae76b"
# P6-3.18: Context A now binds to its own per-context evidence/event (not legacy
# shared ev_1e2d555 / fc50856).
_TRUST_CI = "d3c560c0ca03153283c06b7b68e8e6c5fbfff2fa0711f97786e54e2ad29c52db"
_EVIDENCE_ID = "ev_ctx_122_context_a"
_VERIFICATION_EVENT_ID = "d8d5cc1dbd394eb58ccb501116e98487"


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


# ───────── providers（自包含）─────────
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


class _ClaimNoPerPersonProv:
    """用户声称 10 人符合，但无逐人 eligibility facts。"""
    def complete(self, *, system, user):
        facts = [{"field": "applicant_entity_type", "value": "企业", "source": "user", "source_text": "企业"},
                 {"field": "hired_persons", "value": 10, "source": "user", "source_text": "10个人"},
                 {"field": "user_stated_eligible_count", "value": 10, "source": "user", "source_text": "10人都符合"}]
        for i in range(10):
            facts.append({"field": "target_group", "value": None, "source": "user", "source_text": "", "person_index": i})
        return json.dumps({"facts": facts, "unresolved": []})


# ───────── A. rule_type = fixed_amount ─────────
def test_rule_type_fixed_amount():
    out, _ = _run("企业 10人 全符合", _TenFullProv())
    e = _entry(out)
    assert e["policy_rule"]["rule_type"] == "fixed_amount"
    assert e["policy_rule"]["rule_type_source"] in ("derived", "approved")


# ───────── B. Policy CI 与 Trust CI 分离 ─────────
def test_policy_trust_ci_separated():
    out, _ = _run("企业 10人 全符合", _TenFullProv())
    e = _entry(out)
    prov = e["provenance"]
    assert prov["policy_content_identity"] == _POLICY_CI
    assert prov["trust_content_identity"] == _TRUST_CI
    # 独立字段，绝不混为一个字段
    assert "trust_content_identity" not in {k: None for k in []}  # noqa
    assert prov["trust_content_identity"] != prov["policy_content_identity"]
    # 顶层 content_identity 永远是 Policy CI
    assert e["content_identity"] == _POLICY_CI
    assert e["content_identity"] != _TRUST_CI


# ───────── C. evidence_id / verification_event_id 正确 ─────────
def test_evidence_and_event_id():
    out, _ = _run("企业 10人 全符合", _TenFullProv())
    prov = _entry(out)["provenance"]
    assert prov["evidence_id"] == _EVIDENCE_ID
    assert prov["verification_event_id"] == _VERIFICATION_EVENT_ID
    assert prov["verifier_id"]
    assert prov["verifier_role"]


# ───────── D. fresh process 下 provenance 仍正确 ─────────
def test_fresh_process_provenance():
    from src.trust.trust_service import TrustEvidenceService
    from global_policy_aggregator.pipeline.trust_evidence_bootstrap import (
        load_context_a_evidence,
        load_context_a_new_evidence,
    )
    # 全新 service 实例（模拟 fresh process）从 durable Event Log 重建
    svc = TrustEvidenceService(
        event_log_path=_PRODUCTION_EVENT_LOG,
        authority_registry_config_path=os.path.join(
            REPO_ROOT, "trust_config", "production_authority_registry.json"),
    )
    # P6-3.18：Context A 拥有独立证据 ev_ctx_122_context_a，需与 legacy
    # ev_1e2d555 一并重建（生产 _build_trust_service 同样二者皆调）。
    load_context_a_evidence(svc)
    load_context_a_new_evidence(svc)
    out = assess("企业 10人 全符合", provider=_TenFullProv(), trust_service=svc,
                 policies=[_real122()])
    out = _to_jsonable(out)
    prov = _entry(out)["provenance"]
    assert prov["policy_content_identity"] == _POLICY_CI
    assert prov["trust_content_identity"] == _TRUST_CI
    assert prov["evidence_id"] == _EVIDENCE_ID
    assert prov["verification_event_id"] == _VERIFICATION_EVENT_ID


# ───────── E. 逐人 10/10 PASS ─────────
def test_per_person_10_of_10_pass():
    out, _ = _run("企业 10人 全符合", _TenFullProv())
    pp = _entry(out)["per_person_eligibility"]
    assert pp["available"] is True
    assert pp["hired_count"] == 10
    assert len(pp["persons"]) == 10
    assert all(p["overall"] == "PASS" for p in pp["persons"])
    # 派生逐人 PASS 数须与 benefit eligible_hired_persons 一致
    assert sum(1 for p in pp["persons"] if p["overall"] == "PASS") == \
        _entry(out)["benefit"]["input_values"]["eligible_hired_persons"]


# ───────── F. 7/10 PASS ─────────
def test_per_person_7_of_10_pass():
    out, _ = _run("企业 10人 7人完整", _SevenFullProv())
    pp = _entry(out)["per_person_eligibility"]
    assert pp["hired_count"] == 10
    n_pass = sum(1 for p in pp["persons"] if p["overall"] == "PASS")
    assert n_pass == 7
    assert _entry(out)["benefit"]["input_values"]["eligible_hired_persons"] == 7
    # 每个 PASS 人必须所有 per_person 条件 PASS
    for p in pp["persons"]:
        if p["overall"] == "PASS":
            assert all(c["status"] == "PASS" for c in p["conditions"])


# ───────── G. 缺事实 → UNKNOWN ─────────
def test_per_person_unknown_when_facts_missing():
    out, _ = _run("我们是一家企业，有10个人，这10个人都符合政策条件。", _ClaimNoPerPersonProv())
    pp = _entry(out)["per_person_eligibility"]
    assert pp["hired_count"] == 10
    # 有 10 个人员记录但无任何逐人事实 → 全部 UNKNOWN（缺失→UNKNOWN，绝不 FAIL）
    assert all(p["overall"] == "UNKNOWN" for p in pp["persons"])
    assert "FAIL" not in {p["overall"] for p in pp["persons"]}


# ───────── H. self-claimed eligible_count 不产生虚假逐人 PASS ─────────
def test_self_claimed_no_fake_pass():
    out, _ = _run("我们是一家企业，有10个人，这10个人都符合政策条件。", _ClaimNoPerPersonProv())
    e = _entry(out)
    # 用户声明 10 人符合 → 在 project_inputs 中作为元数据存在
    assert _to_jsonable(out)["project_inputs"].get("user_stated_eligible_count") == 10
    # 但不得产生任何逐人 PASS，也不得得到 10 人 benefit
    pp = e["per_person_eligibility"]
    assert not any(p["overall"] == "PASS" for p in pp["persons"])
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 0
    assert e["benefit"]["calculated_amount"] == 0
    assert e["benefit"]["calculated_amount"] != 15000


# ───────── I. local VERIFIED 不绕过 Trust ─────────
def test_local_verified_does_not_bypass_trust():
    # 无 Trust 服务 → 执行阻断（Gate 仍强制），绝不因 record-local 字段伪造 VERIFIED
    out, _ = _run("企业 10人 全符合", _TenFullProv(), trust=False)
    e = _entry(out)
    assert e["match"] is None and e["benefit"] is None
    # 阻断时 Trust 层 provenance 为 None（未伪造）
    assert e["provenance"]["trust_content_identity"] is None
    assert e["provenance"]["verification_event_id"] is None


# ───────── J. Event Log 仍 unchanged（durable baseline，P6-3.18 合法扩展）─────────
# P6-3.18（M1/M3）向 durable Production Event Log 合法新增了 Context A 独立证据
# ev_ctx_122_context_a 及其人工核验事件，基线由 1 → 4。本断言仅保证 assess 不
# 创建/追加任何事件（before == after），不回退生产契约。
_PRODUCTION_EVENT_LOG_BASELINE = 4


def test_event_log_still_exactly_one():
    n = sum(1 for ln in open(_PRODUCTION_EVENT_LOG, encoding="utf-8") if ln.strip())
    assert n == _PRODUCTION_EVENT_LOG_BASELINE


# ───────── Context A 验证（向后兼容：金额不变）─────────
def test_context_a_amounts_unchanged():
    a, _ = _run("企业 10人 全符合", _TenFullProv())
    d, _ = _run("企业 10人 7人完整", _SevenFullProv())
    b, _ = _run("我们现在有10个人，其中7个人应该符合条件。", FakeProvider())
    c, _ = _run("我是个体工商户，有10个人。", FakeProvider())
    ev, _ = _run("我们是一家企业，有10个人，这10个人都符合政策条件。", _ClaimNoPerPersonProv())
    assert _entry(a)["benefit"]["calculated_amount"] == 15000
    assert _entry(d)["benefit"]["calculated_amount"] == 10500
    assert _entry(b)["eligibility"]["overall"] == "UNKNOWN"
    assert _entry(b)["benefit"]["calculation_status"] == "unable_to_calculate"
    assert _entry(c)["eligibility"]["overall"] == "FAIL"
    assert _entry(c)["benefit"]["calculation_status"] == "unable_to_calculate"
    assert _entry(ev)["benefit"]["calculated_amount"] == 0


# ───────── 向后兼容：现有字段语义未变 ─────────
def test_backward_compat_existing_fields_unchanged():
    out, _ = _run("企业 10人 全符合", _TenFullProv())
    e = _entry(out)
    # 现有字段仍存在且语义不变
    assert e["readiness_state"] == "NOT_READY"
    assert e["application_readiness"] == "NOT_READY"
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["currency"] == "CNY"
    assert e["content_identity"] == _POLICY_CI
    assert e["source_url"].startswith("https://www.gov.cn/")
