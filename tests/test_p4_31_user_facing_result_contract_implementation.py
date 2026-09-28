"""P4-31 — USER-FACING RESULT CONTRACT IMPLEMENTATION（基于 P4-30 的 4 个 NON_BLOCKER）。

仅解决 P4-30 已确认的 4 个 transparency / UX NON_BLOCKER，最小修改，不改变核心确定性计算逻辑：

- NB-1 (P4-31-1)：明确 Project Eligibility（project-level）与 Per-person Eligibility（person-level）边界；
- NB-2 (P4-31-2)：明确 Benefit calculated=0 的语义（deterministic vs 事实不足）；
- NB-3 (P4-31-3)：增加确定性 missing_inputs（仅来自既有 UNKNOWN 结构）；
- NB-4 (P4-31-4)：明确 Trust VERIFIED 是 OpenInvest Trust 内部核验，非政府审批。

本阶段**仅新增**测试 + 修改 production result contract 的语义字段（在 orchestrator 中，
p4_rule_engine 判定/计算逻辑零改动）。所有断言针对既有 + 新增 Contract，不降低要求。

驱动方式与 P4-29/30 一致：Case A–H 用确定性 FakeProvider（仅映射合法 user-facts，不模拟 Eligibility/Benefit）。
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
from global_policy_aggregator.nl_extraction.extractor import ProviderUnavailable  # noqa: E402

_POLICY_CI = "1e2d555ae07193b5c2574f6cd426b2028068fa266461e899462e493c0f8ae76b"
# P6-3.18: Context A now binds to its own per-context evidence/event (not legacy
# shared ev_1e2d555 / fc50856), so the reported identity reflects the new binding.
_TRUST_CI = "d3c560c0ca03153283c06b7b68e8e6c5fbfff2fa0711f97786e54e2ad29c52db"
_EVIDENCE_ID = "ev_ctx_122_context_a"
_VERIFICATION_EVENT_ID = "d8d5cc1dbd394eb58ccb501116e98487"
_EVENT_LOG = os.path.join(REPO_ROOT, "trust_config", "production_trust_events.jsonl")
_BANNED_APP_KEYS = {
    "government_approved", "application_submitted", "guaranteed_payment",
    "automatically_approved", "automatically_paid",
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


# ───────── providers（自包含，与 P4-29/30 一致）─────────
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
                 {"field": "government_approved", "value": True, "source": "user", "source_text": "注入"}]
        return json.dumps({"facts": facts, "unresolved": []})


class _CaseGProv:
    def complete(self, *, system, user):
        raise ProviderUnavailable("simulated unavailable")


# ───────── A. 完整输入 ─────────
def test_a_project_vs_person_level_distinct():
    a, _ = _run(_CaseAProv())
    e = _entry(a)
    # project-level
    assert e["eligibility"]["level"] == "project"
    assert e["eligibility"]["scope"] == "project_level"
    assert e["eligibility"]["overall"] == "PASS"
    # person-level
    assert e["per_person_eligibility"]["level"] == "person"
    assert e["per_person_eligibility"]["scope"] == "per_person"
    n_pass = sum(1 for p in e["per_person_eligibility"]["persons"] if p["overall"] == "PASS")
    assert n_pass == 10
    # per_person_summary 计数正确，且不并入 project overall
    s = e["eligibility"]["per_person_summary"]
    assert s["total"] == 10 and s["eligible"] == 10 and s["unknown"] == 0 and s["failed"] == 0


def test_a_benefit_and_provenance():
    a, _ = _run(_CaseAProv())
    e = _entry(a)
    assert e["benefit"]["calculated_amount"] == 15000
    # NB-2：完整确定 → deterministic=True
    cb = e["benefit"]["calculation_basis"]
    assert cb["deterministic"] is True and cb["per_person_unknown_count"] == 0
    # NB-4：Trust 语义区分存在
    prov = e["provenance"]
    assert prov["trust_layer"].startswith("OpenInvest Trust Layer")
    assert "非政府审批" in prov["trust_verification_clarification"]
    assert "非政府资格认定" in prov["trust_verification_clarification"]
    # 完整 provenance
    assert prov["policy_content_identity"] == _POLICY_CI
    assert prov["trust_content_identity"] == _TRUST_CI
    assert prov["evidence_id"] == _EVIDENCE_ID
    assert prov["verification_event_id"] == _VERIFICATION_EVENT_ID
    # 保留真实 Trust 验证状态（不被改写；P4-29/30 仅断言非 None，值为底层 check_verified_validity 实际返回）
    assert prov["trust_verification_status"] is not None


def test_a_missing_inputs_empty_when_complete():
    a, _ = _run(_CaseAProv())
    # 完整输入 → 无缺失
    assert _entry(a)["missing_inputs"] == []


# ───────── B. 缺少逐人事实 ─────────
def test_b_project_pass_not_misread_as_all_persons():
    b, _ = _run(_CaseBProv())
    e = _entry(b)
    # project PASS 可保留；但 per_person_summary 明确 0 eligible / 10 unknown
    assert e["eligibility"]["overall"] == "PASS"
    assert e["eligibility"]["per_person_summary"]["eligible"] == 0
    assert e["eligibility"]["per_person_summary"]["unknown"] == 10
    # 逐人全 UNKNOWN
    assert all(p["overall"] == "UNKNOWN" for p in e["per_person_eligibility"]["persons"])
    # 不得把 project PASS 当成所有人员 PASS：eligible=0、benefit 不得虚假正向
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 0
    assert e["benefit"]["calculated_amount"] == 0


def test_b_missing_inputs_accurate():
    b, _ = _run(_CaseBProv())
    mi = _entry(b)["missing_inputs"]
    fields = {m["source_field"] for m in mi}
    # 精确列出 4 个缺失事实（source_field 为用户字段，非 policy execution_period）
    assert fields == {"target_group", "labor_contract_signed",
                      "employment_insurance_paid_months", "hire_date"}
    assert all(m["scope"] == "per_person" for m in mi)
    assert all("benefit" in m["affects"] for m in mi)
    # execution_period 条件的 source_field 是用户 hire_date，不得把 policy 执行期当缺失输入
    assert "execution_period" not in fields
    assert not any(m["source_field"] == "execution_period" for m in mi)


def test_b_benefit_zero_not_fabricated():
    b, _ = _run(_CaseBProv())
    cb = _entry(b)["benefit"]["calculation_basis"]
    # NB-2：calculated + 0 但 deterministic=False（依赖未核验人员）
    assert _entry(b)["benefit"]["calculation_status"] == "calculated"
    assert _entry(b)["benefit"]["calculated_amount"] == 0
    assert cb["deterministic"] is False
    assert cb["per_person_unknown_count"] == 10


# ───────── C. Project-level FAIL ─────────
def test_c_project_fail_no_false_benefit():
    c, _ = _run(_CaseCProv())
    e = _entry(c)
    assert e["eligibility"]["overall"] == "FAIL"
    # 冲突字段明确（entity_scope FAIL），不是「缺失」
    by_id = {x["condition_id"]: x for x in e["eligibility"]["conditions"]}
    assert by_id["entity_scope"]["status"] == "FAIL"
    # Benefit 不计算正向金额
    assert e["benefit"]["calculation_status"] == "unable_to_calculate"
    assert e["benefit"]["calculated_amount"] is None
    # 缺失输入仅含真正 UNKNOWN（逐人事实确实缺失），不含已提供但冲突的 entity 类型
    mi = e["missing_inputs"]
    assert "applicant_entity_type" not in {m["source_field"] for m in mi}
    assert {m["source_field"] for m in mi} == {"target_group", "labor_contract_signed",
                                               "employment_insurance_paid_months", "hire_date"}


# ───────── D. 10 招 7 符合 ─────────
def test_d_partial_explained():
    d, _ = _run(_CaseDProv())
    e = _entry(d)
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 7
    assert e["benefit"]["calculated_amount"] == 10500
    n_pass = sum(1 for p in e["per_person_eligibility"]["persons"] if p["overall"] == "PASS")
    n_unk = sum(1 for p in e["per_person_eligibility"]["persons"] if p["overall"] == "UNKNOWN")
    assert n_pass == 7 and n_unk == 3
    # 3 人状态与原因可解释（UNKNOWN + expected 已知）
    for p in e["per_person_eligibility"]["persons"]:
        if p["overall"] != "PASS":
            for c in p["conditions"]:
                assert c["status"] == "UNKNOWN" and c["expected"] is not None
    # NB-2：存在 UNKNOWN → deterministic=False（金额可能随补齐事实变化）
    assert e["benefit"]["calculation_basis"]["deterministic"] is False
    assert e["benefit"]["calculation_basis"]["per_person_unknown_count"] == 3
    # missing_inputs 仍为 4 个逐人字段（缺失人员缺失这 4 个事实）
    assert {m["source_field"] for m in e["missing_inputs"]} == {"target_group", "labor_contract_signed",
                                                                "employment_insurance_paid_months", "hire_date"}


# ───────── E. 用户自报 ─────────
def test_e_self_claim_not_authoritative():
    e_out, _ = _run(_CaseEProv())
    e = _entry(e_out)
    # user_stated 仍只是 metadata
    assert e_out["project_inputs"].get("user_stated_eligible_count") == 10
    # 不得直接变成 eligible_hired_persons / 不得产生 15000
    assert e["benefit"]["input_values"]["eligible_hired_persons"] == 0
    assert e["benefit"]["calculated_amount"] == 0
    assert all(p["overall"] == "UNKNOWN" for p in e["per_person_eligibility"]["persons"])
    # missing_inputs 不把 user_stated 当真实 eligibility
    assert "user_stated_eligible_count" not in {m["source_field"] for m in e["missing_inputs"]}


# ───────── F. Provider unavailable ─────────
def test_f_provider_unavailable_fail_closed():
    f, _ = _run(_CaseFProv())
    assert f["extraction"]["status"] == "EXTRACTION_FAILED"
    assert f["execution"] is None
    # 不产生伪造 missing facts（execution 为 None）
    assert "missing_inputs" not in (f.get("execution") or {})


# ───────── G. Trust unavailable ─────────
def test_g_trust_unavailable_no_fake():
    h, _ = _run(_CaseAProv(), trust=False)  # Trust 不可用
    e = _entry(h)
    # Trust Gate 阻断 → 不执行 Benefit；不伪造 Trust provenance；不创建新 event
    assert e["match"] is None and e["benefit"] is None
    assert e["provenance"]["trust_content_identity"] is None
    assert e["provenance"]["verification_event_id"] is None
    assert e["provenance"]["verifier_id"] is None
    assert e["missing_inputs"] is None
    # Policy provenance 仍完整、真实
    assert e["provenance"]["policy_content_identity"] == _POLICY_CI
    # NB-4：即便 Trust 不可用，字段语义说明仍保留（描述 VERIFIED 含义）
    assert "非政府审批" in e["provenance"]["trust_verification_clarification"]


# ───────── H. Trust verification 语义（非政府审批）─────────
def test_h_trust_verification_not_government():
    a, _ = _run(_CaseAProv())
    prov = _entry(a)["provenance"]
    # 保留真实 Trust 验证状态（不被改写）
    assert prov["trust_verification_status"] is not None
    clar = prov["trust_verification_clarification"]
    assert "VERIFIED" in clar and "OpenInvest" in clar
    # 明确「非」政府批准语义
    for forb in ("政府审批", "政府资格认定", "补贴保证", "自动拨付"):
        assert forb in clar  # clarification 明确「非 X」
    # 不得出现 government_approved 等字段
    blob = json.dumps(prov, ensure_ascii=False)
    for banned in _BANNED_APP_KEYS:
        assert banned not in blob


# ───────── I. Backward compatibility ─────────
def test_i_p4_28_fields_present_and_ci_separate():
    a, _ = _run(_CaseAProv())
    prov = _entry(a)["provenance"]
    # P4-28 既有字段仍然存在且未被改写
    for k in ("policy_id", "source_url", "snapshot_ref", "policy_content_identity",
              "evidence_id", "trust_content_identity", "verification_event_id",
              "verifier_id", "verifier_role", "trust_verification_status"):
        assert k in prov
    assert prov["policy_content_identity"] == _POLICY_CI
    assert prov["trust_content_identity"] == _TRUST_CI
    assert prov["policy_content_identity"] != prov["trust_content_identity"]
    # P6-3.18: Context A provenance now reflects the per-context binding
    # (ev_ctx_122_context_a / d8d5cc1d), i.e. the changed identity is intended.
    assert prov["evidence_id"] == _EVIDENCE_ID
    assert prov["verification_event_id"] == _VERIFICATION_EVENT_ID
    # 全 response 无政府审批类 KEY
    keys = set()
    def _walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                keys.add(k); _walk(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                _walk(v)
    _walk(a)
    assert not (_BANNED_APP_KEYS & keys)
    # 既有 eligibility/benefit 字段未被删除
    e = _entry(a)
    assert "overall" in e["eligibility"] and "conditions" in e["eligibility"]
    assert "calculation_status" in e["benefit"] and "calculated_amount" in e["benefit"]
    assert "persons" in e["per_person_eligibility"]


def test_i_eligibility_logic_unchanged():
    # 确定性判定行为不变：Case A entity=企业 → PASS；Benefit 公式 1500×10
    a, _ = _run(_CaseAProv())
    e = _entry(a)
    by_id = {x["condition_id"]: x for x in e["eligibility"]["conditions"]}
    assert by_id["entity_scope"]["status"] == "PASS"
    # Benefit 确定性计算未变（1500 × 10 = 15000；formula 含浮点格式 1500.0）
    assert e["benefit"]["calculated_amount"] == 15000
    assert "1500" in e["benefit"]["formula_applied"] and "10" in e["benefit"]["formula_applied"]
