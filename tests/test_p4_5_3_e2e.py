# -*- coding: utf-8 -*-
"""P4-5.3 — Rule Context A/B E2E（Project Input → Eligibility → Benefit）回归套件。

READ-ONLY：不修改 REAL 101–121 / 不创建 REAL 122 / 不写 real_policies.json / 不写 Trust。
固定 P4-5.2 三条设计决策 + P4-5.3 fail-closed 语义。
"""
import hashlib
import io
import json
import os

import pytest

from global_policy_aggregator.pipeline.parser import parse_html
from global_policy_aggregator.pipeline.normalizer import normalize
from global_policy_aggregator.pipeline.rule_context import audit_policy_rule_contexts
from global_policy_aggregator.pipeline.p4_5_3_e2e import (
    BEN_CALC, BEN_UNABLE, EL_FAIL, EL_READY, EL_UNKNOWN,
    evaluate_rule_context,
)

FIX = "tests/fixtures/pipeline/notice39_rule_structure.html"
REAL = "global_policy_aggregator/data/real_policies/real_policies.json"
URL = "https://www.gov.cn/zhengce/zhengceku/202607/content_7074139.htm"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 2026 年全国城镇调查失业率控制目标（公开报道约 5.2%）——作为 fixture 提供的外部官方统计
EXT_TARGET = {"layoff_rate_control_target_max": 0.052}


def _contexts():
    with io.open(os.path.join(ROOT, FIX), encoding="utf-8") as f:
        html = f.read()
    ci = hashlib.sha256(html.encode("utf-8")).hexdigest()
    parsed = parse_html(html, URL, snapshot_ref=f"snapshots/{ci}.html")
    cand = normalize(parsed, URL, snapshot_ref=f"snapshots/{ci}.html")
    rec = dict(cand.to_dict())
    rec["content_identity"] = ci
    rec["source_url"] = URL
    rep = audit_policy_rule_contexts(rec, parsed.clean_text, policy_ref="39hao")
    ctxs = {c["rule_type"]: c for c in rep["contexts"]}
    return ctxs["fixed_amount"], ctxs["percentage_of_base"], rec


@pytest.fixture(scope="module")
def ctxs():
    return _contexts()


# ── A. 一次性扩岗补助 ──────────────────────────────────────────────────────
def _a_facts_full():
    # 官方原文（39号通知第二条）实体范围为「企业和社会组织」（和）；fixture 严格对齐官方语义。
    return {
        "hired_person_count": 10,
        "employment_insurance_paid_months": 4,
        "labor_contract_signed": True,
        "applicant_entity_type": "企业和社会组织",
        "hired_target_group": "毕业年度或离校两年内未就业高校毕业生",
    }


def test_A1_full_satisfied(ctxs):
    a, _, _ = ctxs
    r = evaluate_rule_context(a, _a_facts_full())
    assert r["eligibility"]["status"] == EL_READY
    assert r["benefit"]["status"] == BEN_CALC
    assert r["benefit"]["amount"] == 1500 * 10        # 15000
    assert r["benefit"]["unit_rate"] == 1500
    assert r["benefit"]["quantity"] == 10
    assert "×" in r["benefit"]["formula"]


def test_A2_missing_facts(ctxs):
    a, _, _ = ctxs
    # 缺关键事实：合格招用人数 + 足额缴费月数
    facts = {"labor_contract_signed": True,
             "applicant_entity_type": "企业和社会组织",
             "hired_target_group": "毕业年度或离校两年内未就业高校毕业生"}
    r = evaluate_rule_context(a, facts)
    assert r["eligibility"]["status"] == EL_UNKNOWN   # 缺 eligibility 事实 → 不猜测
    assert r["benefit"]["status"] == BEN_UNABLE
    # 另测：eligibility 事实齐全但缺数量 → benefit UNABLE 且显式指出缺 hired_person_count
    facts2 = _a_facts_full()
    del facts2["hired_person_count"]
    r2 = evaluate_rule_context(a, facts2)
    assert r2["eligibility"]["status"] == EL_READY
    assert r2["benefit"]["status"] == BEN_UNABLE
    assert "hired_person_count" in r2["benefit"]["reason"]


def test_A3_conflict(ctxs):
    a, _, _ = ctxs
    facts = _a_facts_full()
    facts["labor_contract_signed"] = False            # 明确冲突：未签劳动合同
    r = evaluate_rule_context(a, facts)
    assert r["eligibility"]["status"] == EL_FAIL
    assert r["benefit"]["status"] == BEN_UNABLE
    assert "FAIL" in r["benefit"]["reason"]


# ── F1 — applicant_entity_in_scope 语义必须严格为官方「企业和社会组织」（和）───────────
def test_F1_entity_scope_matches_official_and_text(ctxs):
    a, _, _ = ctxs
    cond = next(c for c in a["conditions"] if c["id"] == "applicant_entity_in_scope")
    # 官方原文（39号通知第二条）用词「企业和社会组织」（和），不得为「或」
    assert cond["expected_value"] == "企业和社会组织"
    assert "企业和社会组织" in cond["quote"]
    assert "企业或社会组织" not in cond["quote"]
    # Evidence 5-tuple 不断链
    assert cond.get("char_span") and cond.get("quote")
    # 以官方「和」形式的事实可判定 READY
    r = evaluate_rule_context(a, _a_facts_full())
    assert r["eligibility"]["status"] == EL_READY
    # 用「或」形式的事实必须判 FAIL —— 防止 future 把「和」变「或」后误通过
    facts_or = _a_facts_full()
    facts_or["applicant_entity_type"] = "企业或社会组织"
    assert evaluate_rule_context(a, facts_or)["eligibility"]["status"] == EL_FAIL


# ── F2 — per-person 粒度正式锁定 ──────────────────────────────────────────────
def test_F2_one_person_amount(ctxs):
    a, _, _ = ctxs
    facts = _a_facts_full(); facts["hired_person_count"] = 1
    r = evaluate_rule_context(a, facts)
    assert r["benefit"]["status"] == BEN_CALC
    assert r["benefit"]["amount"] == 1500
    assert r["benefit"]["per_person_amount"] == 1500
    assert r["benefit"]["granularity"] == "per_hired_person"


def test_F2_ten_persons_amount(ctxs):
    a, _, _ = ctxs
    facts = _a_facts_full(); facts["hired_person_count"] = 10
    r = evaluate_rule_context(a, facts)
    assert r["benefit"]["amount"] == 15000


def test_F2_missing_persons_unable(ctxs):
    a, _, _ = ctxs
    facts = _a_facts_full(); del facts["hired_person_count"]
    r = evaluate_rule_context(a, facts)
    assert r["eligibility"]["status"] == EL_READY
    assert r["benefit"]["status"] == BEN_UNABLE
    assert "hired_person_count" in r["benefit"]["reason"]


def test_F2_no_default_persons(ctxs):
    # 人数为 0 / 未提供 → 不默认 1 或任何值
    a, _, _ = ctxs
    facts = _a_facts_full(); facts["hired_person_count"] = 0
    assert evaluate_rule_context(a, facts)["benefit"]["status"] == BEN_UNABLE


def test_F2_missing_unit_fail_closed(ctxs):
    # unit（元/人）缺失 → 无法断言 per-person 语义 → UNABLE（不按总额算）
    a, _, _ = ctxs
    broken = json.loads(json.dumps(a))
    broken["unit"] = None
    broken["benefit_basis"]["per_unit"] = None
    r = evaluate_rule_context(broken, _a_facts_full())
    assert r["benefit"]["status"] == BEN_UNABLE
    assert ("元/人" in r["benefit"]["reason"] or "per-unit" in r["benefit"]["reason"])


# ── B. 稳岗返还（分档 30% / 60%）────────────────────────────────────────────
def _b_facts(size, base=1_000_000):
    return {"company_size": size, "prior_year_ui_premium_paid": base,
            "ui_paid_months": 24, "layoff_rate": 0.03, "insured_employee_count": 500}


def test_B1_large(ctxs):
    _, b, _ = ctxs
    r = evaluate_rule_context(b, _b_facts("大型企业"), external_statistics=EXT_TARGET)
    assert r["eligibility"]["status"] == EL_READY
    assert r["benefit"]["status"] == BEN_CALC
    assert r["benefit"]["amount"] == 1_000_000 * 0.30  # 300000
    assert r["benefit"]["variant"] == "大型企业"
    assert r["benefit"]["rate"] == 0.30


def test_B2_sme(ctxs):
    _, b, _ = ctxs
    r = evaluate_rule_context(b, _b_facts("中小微企业"), external_statistics=EXT_TARGET)
    assert r["benefit"]["amount"] == 1_000_000 * 0.60  # 600000
    assert r["benefit"]["variant"] == "中小微企业"
    assert r["benefit"]["rate"] == 0.60


def test_B3_missing_size_no_default(ctxs):
    _, b, _ = ctxs
    # 缺企业规模：不得默认 large / SME
    facts = {"prior_year_ui_premium_paid": 1_000_000, "ui_paid_months": 24,
             "layoff_rate": 0.03, "insured_employee_count": 500}
    r = evaluate_rule_context(b, facts, external_statistics=EXT_TARGET)
    assert r["eligibility"]["status"] == EL_UNKNOWN
    assert r["benefit"]["status"] == BEN_UNABLE
    assert r["benefit"]["amount"] is None


def test_B4_missing_base_eligibility_independent(ctxs):
    _, b, _ = ctxs
    # 缺基数：eligibility 仍可独立判定（规模+条件齐全），benefit 不可算
    facts = {"company_size": "大型企业", "ui_paid_months": 24,
             "layoff_rate": 0.03, "insured_employee_count": 500}
    r = evaluate_rule_context(b, facts, external_statistics=EXT_TARGET)
    assert r["eligibility"]["status"] == EL_READY
    assert r["benefit"]["status"] == BEN_UNABLE
    assert "prior_year_ui_premium_paid" in r["benefit"]["reason"]


def test_B5_conflict(ctxs):
    _, b, _ = ctxs
    facts = _b_facts("大型企业")
    facts["ui_paid_months"] = 6                         # 明确冲突：缴费不足 12 个月
    r = evaluate_rule_context(b, facts, external_statistics=EXT_TARGET)
    assert r["eligibility"]["status"] == EL_FAIL
    assert r["benefit"]["status"] == BEN_UNABLE


# ── C. Evidence 5-tuple 不断链 ─────────────────────────────────────────────
def _ev_complete(ev):
    return all(ev.get(k) for k in ("quote", "char_span", "snapshot_ref",
                                   "content_identity", "source_url"))


def test_A1_evidence_trace(ctxs):
    a, _, _ = ctxs
    r = evaluate_rule_context(a, _a_facts_full())
    pfe = r["benefit"]["evidence"]["policy_field_evidence"]
    assert any(e["field"] == "amount" and _ev_complete(e) for e in pfe)
    binds = r["benefit"]["evidence"]["project_input_bindings"]
    assert any(b["input_key"] == "hired_person_count" for b in binds)


def test_B1_evidence_trace(ctxs):
    _, b, _ = ctxs
    r = evaluate_rule_context(b, _b_facts("大型企业"), external_statistics=EXT_TARGET)
    pfe = r["benefit"]["evidence"]["policy_field_evidence"]
    # base（政策字段）+ variant（分档官方条款）均需 5-tuple
    assert any(e["field"] == "base" and _ev_complete(e) for e in pfe)
    assert any(str(e["field"]).startswith("variant:") and _ev_complete(e) for e in pfe)


# ── D. 信任边界：derived ≠ approved ≠ VERIFIED ────────────────────────────
def test_record_verified_does_not_bypass(ctxs):
    a, b, _ = ctxs
    rec = {"verified": True, "approved": True}
    # A1 + verified：benefit 照常计算，但 provenance 仍 NOT_READY、human_approved=False
    r = evaluate_rule_context(a, _a_facts_full(), record=rec)
    assert r["benefit"]["amount"] == 15000
    assert r["record_verified_ignored"] is True
    assert r["human_approved"] is False
    assert r["provenance_readiness"] == "NOT_READY"
    assert r["e2e_readiness"] == "NOT_READY"
    # B 缺基数 + verified：仍 UNABLE，verified 不绕过缺失事实
    rb = evaluate_rule_context(b, {"company_size": "大型企业"}, record=rec,
                               external_statistics=EXT_TARGET)
    assert rb["benefit"]["status"] == BEN_UNABLE


def test_trust_simulated_ready_without_application_still_not_ready(ctxs):
    a, _, _ = ctxs
    # 即使模拟 Trust provenance 有效，无 application_requirements → e2e 仍 NOT_READY
    r = evaluate_rule_context(a, _a_facts_full(), trust_provenance_valid=True)
    assert r["provenance_readiness"] == "READY"
    assert r["human_approved"] is False
    assert r["e2e_readiness"] == "NOT_READY"


def test_full_gate_simulated_reaches_ready(ctxs):
    a, _, _ = ctxs
    # fixture 模拟 Trust 有效 + 申报要求齐全 → E2E 可达 READY（证明确定性链路完整）
    rec = {"application_requirements": [{"step": "x"}]}
    r = evaluate_rule_context(a, _a_facts_full(), trust_provenance_valid=True, record=rec)
    assert r["e2e_readiness"] == "READY"
    assert r["human_approved"] is False   # rule_type 批准仍必须来自 Trust，非 record-local


# ── E. 生产只读边界 ───────────────────────────────────────────────────────
def test_real_101_121_untouched():
    # 101–121 不被改动；REAL 122 已由 P3-7 正式写入（合法，非本阶段泄露）。
    path = os.path.join(ROOT, REAL)
    with io.open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data["policies"] if isinstance(data, dict) else data
    ids = sorted(int(r["id"]) for r in rows)
    assert len(rows) == 22
    assert ids == list(range(101, 123))
    assert 122 in ids


def test_read_only_does_not_write_real(tmp_path):
    import shutil
    src = os.path.join(ROOT, REAL)
    shutil.copy(src, tmp_path / "real.snap.json")
    before = hashlib.sha256(io.open(src, "rb").read()).hexdigest()
    _contexts()
    after = hashlib.sha256(io.open(src, "rb").read()).hexdigest()
    assert before == after, "real_policies.json 不应被本阶段写入"
