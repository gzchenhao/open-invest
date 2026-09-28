# -*- coding: utf-8 -*-
"""P4-7 — Context A（一次性扩岗补助）PRODUCTION READINESS 回归套件。

READ-ONLY：不写 Trust / 不修改 REAL 101–121 / 不 commit。REAL 122 已由 P3-7 正式写入（见 P3-7_REAL_122_PRODUCTION_INGESTION_REPORT.md）。
验证：Application Requirements（仅 policy-native）、External Dependency（UNKNOWN 不猜测）、
eligible_hired_persons 派生链、Evidence 5-tuple、Human Gate Readiness Matrix。
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
    BEN_CALC, EL_READY, evaluate_rule_context,
)
from global_policy_aggregator.pipeline.p4_7_context_a_readiness import (
    CONTEXT_A_APPLICATION_REQUIREMENTS, CONTEXT_A_EXTERNAL_DEPENDENCIES,
    CONTEXT_A_PROJECT_INPUT_CONTRACT, compute_context_a_benefit,
    derive_eligible_hired_persons, evidence_complete,
    assess_context_a_human_gate_readiness,
)

FIX = "tests/fixtures/pipeline/notice39_rule_structure.html"
REAL = "global_policy_aggregator/data/real_policies/real_policies.json"
URL = "https://www.gov.cn/zhengce/zhengceku/202607/content_7074139.htm"
# ── Immutable historical (P4-7 / post-P3-7) anchors ──────────────────────────────
# P4-7 baseline: post-P3-7 production state (22 records 101–122, no 123+). IMMUTABLE.
P4_7_BASELINE_SHA = "c9bb01d431df98958f50a7b11e721723e488316d8e36d74c1c0ec4f8fc840988"
# Byte-level SHA of the file region covering REAL 101–121 (all bytes before the first
# occurrence of `"id": 122`). Computed from the P4-7 baseline file. IMMUTABLE anchor.
P4_7_REAL_101_121_PREFIX_SHA = "6a8628030138a8b12ecdd72fa79c1361e058c55ad2d39ad24f9b3ab6ca469e0b"
# P4-17 post-change baseline: production file after the authorized GAP-5 addition of
# REAL 122 field_evidence["eligibility_conditions"]. Computed from the real file
# (0feb4328…); pins the WHOLE current file against any future unauthorized change.
# P6-3.18 refresh: REAL 122 received an *additive* trust_bindings["context_a"] (per-context
# active binding for Context A). No provenance/contract field changed. The whole-file SHA
# therefore legitimately diverged from the P4-17 baseline; this is the new authorized state.
P4_17_BASELINE_SHA = "c3e13fafb09adbc9699009fcd473af4564f8ba9cd199faec4c37ef150478025d"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _ctx_a():
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
    return ctxs["fixed_amount"], rec


@pytest.fixture(scope="module")
def ctx_a():
    return _ctx_a()[0]


# ── A. Application Requirements（仅 policy-native，不猜测）─────────────────────
def test_application_requirements_policy_native_have_quotes():
    native = [a for a in CONTEXT_A_APPLICATION_REQUIREMENTS
              if a["kind"] == "eligibility_to_enjoy"]
    assert len(native) == 5
    for a in native:
        assert a["provided_by"] == "policy_native"
        assert a["source_quote"]           # 每条都引用通知原文
        assert a["status"] == "READY_POLICY_NATIVE"


def test_application_procedural_not_fabricated():
    # 程序性申请要求（渠道/材料）通知未规定 → 必须 UNKNOWN，不得编造
    proc = next(a for a in CONTEXT_A_APPLICATION_REQUIREMENTS
                if a["id"] == "ar_procedural_channel")
    assert proc["provided_by"] == "external"
    assert proc["external_dependency"] is True
    assert proc["status"] == "UNKNOWN"
    # 来源仅指向通知原文补助发放条款（未编造任何渠道/材料/受理机构）
    assert "每招用1人不超过1500元" in proc["source_quote"]


# ── B. External Dependency（hired_target_group 等，UNKNOWN 不猜测）──────────────
def test_external_dependencies_surfaced_unknown():
    assert len(CONTEXT_A_EXTERNAL_DEPENDENCIES) >= 5
    for d in CONTEXT_A_EXTERNAL_DEPENDENCIES:
        assert d["external_dependency"] is True
        assert d["status"] == "UNKNOWN"           # 不猜测
        assert d["required_official_source"]      # 明确需哪个官方来源


def test_hired_target_group_external_def_present():
    ids = {d["id"] for d in CONTEXT_A_EXTERNAL_DEPENDENCIES}
    assert "ext_grad_2026" in ids
    assert "ext_age_16_24" in ids
    assert "ext_registered_unemployed" in ids
    assert "ext_social_org_scope" in ids


# ── C. eligible_hired_persons 派生链（不能只是数字）──────────────────────────
def _person(tg, contract=True, months=4):
    return {"target_group": tg, "labor_contract_signed": contract,
            "employment_insurance_paid_months": months}


def test_eligible_derivation_all_eligible(ctx_a):
    facts = {"hired_persons": [_person("毕业年度或离校两年内未就业高校毕业生")
                               for _ in range(10)]}
    elig, err = derive_eligible_hired_persons(ctx_a, facts)
    assert elig == 10 and err is None
    r = compute_context_a_benefit(ctx_a, facts)
    assert r["status"] == BEN_CALC and r["amount"] == 15000
    assert r["eligible_hired_persons"] == 10


def test_eligible_derivation_partial(ctx_a):
    persons = [_person("毕业年度或离校两年内未就业高校毕业生") for _ in range(8)]
    persons += [_person("与政策无关的其他人员") for _ in range(2)]  # 不满足 target-group
    r = compute_context_a_benefit(ctx_a, {"hired_persons": persons})
    assert r["status"] == BEN_CALC and r["amount"] == 12000
    assert r["eligible_hired_persons"] == 8


def test_eligible_derivation_employment_fail(ctx_a):
    persons = [_person("毕业年度或离校两年内未就业高校毕业生", contract=False)
               for _ in range(5)]
    elig, err = derive_eligible_hired_persons(ctx_a, {"hired_persons": persons})
    assert elig == 0 and err is None          # 派生正确得 0 人
    r = compute_context_a_benefit(ctx_a, {"hired_persons": persons})
    assert r["status"] == "UNABLE"            # 人数≤0 → fail-closed（无正向 Benefit）


def test_eligible_derivation_aggregate_not_a_number(ctx_a):
    # 仅给聚合 hired_person_count，未给 per-person 明细 → 不能判定 per-person 资格
    r = compute_context_a_benefit(ctx_a, {"hired_person_count": 10})
    assert r["status"] == "UNABLE"
    assert "per-person" in r["reason"]


def test_eligible_derivation_missing_unable(ctx_a):
    r = compute_context_a_benefit(ctx_a, {})
    assert r["status"] == "UNABLE"


# ── D/E. Benefit 契约锁定 + Evidence 5-tuple ─────────────────────────────────
def test_benefit_per_person_contract_intact(ctx_a):
    # 1 人 → 1500；仍按 per-person 语义
    facts = {"hired_persons": [_person("16—24岁登记失业青年")]}
    r = compute_context_a_benefit(ctx_a, facts)
    assert r["amount"] == 1500 and r["per_person_amount"] == 1500


def test_evidence_5tuple_complete(ctx_a):
    ok, missing = evidence_complete(ctx_a)
    assert ok, missing
    assert not missing


# ── H. Human Gate Readiness Matrix ──────────────────────────────────────────
def test_human_gate_readiness_matrix(ctx_a):
    res = assess_context_a_human_gate_readiness(ctx_a)
    assert res["overall"] == "READY_FOR_HUMAN_GATE"
    by = {m["item"]: m for m in res["matrix"]}
    assert by["Benefit"]["status"] == "READY"
    assert by["Eligibility"]["status"] == "READY"
    assert by["Project Input"]["status"] == "READY"
    assert by["Application"]["status"] == "READY"
    assert by["Evidence"]["status"] == "READY"
    assert by["External Dependency"]["status"] == "ACKNOWLEDGED"
    # Trust 本阶段不 VERIFIED（后续 gate），不阻断 human gate
    assert by["Trust"]["status"] == "NOT_READY"
    assert "VERIFIED" in by["Trust"]["blocker"]


def test_real_data_eligibility_unknown_without_facts(ctx_a):
    # 未提供真实项目数据 → 执行层 eligibility 为 UNKNOWN（不阻断 gate 规格就绪）
    res = assess_context_a_human_gate_readiness(ctx_a)
    assert res["real_data_eligibility_status"] in ("UNKNOWN", "NOT_READY")


# ── P4-5.3 契约回归（不得被破坏）────────────────────────────────────────────
def test_p4_5_3_contract_intact(ctx_a):
    # 原 E2E 契约：hired_person_count=10 → 15000（aggregate 路径仍可用）
    facts = {"hired_person_count": 10, "employment_insurance_paid_months": 4,
             "labor_contract_signed": True,
             "applicant_entity_type": "企业和社会组织",
             "hired_target_group": "毕业年度或离校两年内未就业高校毕业生"}
    r = evaluate_rule_context(ctx_a, facts)
    assert r["benefit"]["status"] == BEN_CALC
    assert r["benefit"]["amount"] == 15000


# ── REAL 101–121 byte-level invariant + REAL 122 合法 Context A（P4-7 historical anchor）──
def test_real_122_present_and_101_121_byte_level_unchanged():
    # Historical P4-7 invariant (post-P3-7 baseline):
    #  - REAL 101–121 MUST remain byte-level identical to the P4-7 baseline;
    #  - REAL 122 MUST remain a legal Context A record; no REAL 123+;
    #  - the production file legitimately DIVERGED from the P4-7 baseline (GAP-5 on 122).
    path = os.path.join(ROOT, REAL)
    with io.open(path, "rb") as f:
        data = f.read()
    cur_full = hashlib.sha256(data).hexdigest()
    # (1) REAL 101–121 byte-level: every byte before the first `"id": 122` must equal the
    #     P4-7 baseline prefix (P4_7_REAL_101_121_PREFIX_SHA computed from the P4-7 file).
    idx = data.find(b'"id": 122')
    assert idx != -1
    assert hashlib.sha256(data[:idx]).hexdigest() == P4_7_REAL_101_121_PREFIX_SHA
    # (5) historical anchor retained (immutable) — not overwritten by the P4-17 baseline.
    assert P4_7_BASELINE_SHA == "c9bb01d431df98958f50a7b11e721723e488316d8e36d74c1c0ec4f8fc840988"
    # (4) the file legitimately diverged from P4-7 (only the authorized GAP-5 edit on 122).
    assert cur_full != P4_7_BASELINE_SHA
    rows = json.loads(data)
    rs = rows["policies"] if isinstance(rows, dict) else rows
    ids = [int(r["id"]) for r in rs]
    assert len(rs) == 22
    assert 122 in ids
    # 101–121 all present (no record removed in that range)
    assert all(101 <= i <= 121 for i in ids if i < 122), "REAL 101–121 被修改"
    # (3) no REAL 123+
    assert max(ids) == 122
    assert set(ids) == set(range(101, 123)), f"REAL 集合异常: {sorted(ids)}"
    rec122 = next(r for r in rs if r["id"] == 122)
    assert rec122["verification_status"] == "unverified"


# ── P4-17 post-change invariant: only the authorized GAP-5 change on REAL 122 ──────
def test_p4_17_real_122_gap5_field_evidence_invariant():
    # After the authorized GAP-5 addition of REAL 122 field_evidence["eligibility_conditions"],
    # the production file equals the P4-17 baseline (NOT the P4-7 baseline), and REAL 122's
    # ONLY change is that single key — all original provenance/contract fields are unchanged.
    path = os.path.join(ROOT, REAL)
    with io.open(path, "rb") as f:
        data = f.read()
    cur_full = hashlib.sha256(data).hexdigest()
    # (4) current fullfile SHA == P4-17 baseline, and != P4-7 baseline
    assert cur_full == P4_17_BASELINE_SHA
    assert cur_full != P4_7_BASELINE_SHA
    rows = json.loads(data)
    rs = rows["policies"] if isinstance(rows, dict) else rows
    rec122 = next(r for r in rs if r["id"] == 122)
    # (2) 122 original provenance / contract fields UNCHANGED (exact values, not relaxed)
    assert rec122["evidence_id"] == "ev_1e2d555ae07193b5c257"
    assert rec122["verified_event_id"] == "fc50856de78547df8dc5d9f29b4b270d"
    assert rec122["candidate_id"] == "cand_a54ea576e4a3"
    assert rec122["content_identity"] == (
        "1e2d555ae07193b5c2574f6cd426b2028068fa266461e899462e493c0f8ae76b")
    assert rec122["trust_content_identity"] == (
        "b4012feb48e86e999b3149eb42fd62d91f1a8049e22daeda24d9dd4a89292937")
    assert rec122["verifier_id"] == "human-reviewer-howard"
    assert rec122["verifier_role"] == "human_verifier"
    assert rec122["rule_type"] == "fixed_amount"
    assert rec122["granularity"] == "per_hired_person"
    assert rec122["unit"] == "元/人"
    assert rec122["amount"]["normalized_number"] == 1500
    assert rec122["valid_period"] == {"start": "2026-01-01", "end": "2026-12-31"}
    assert len(rec122["eligibility_conditions"]) == 5
    # Context B（稳岗返还）不得混入 REAL 122
    for fld in ("percentage", "base", "cap", "floor"):
        assert rec122.get(fld) is None, f"Context B field leaked into REAL 122: {fld}"
    # field_evidence contains EXACTLY the P4-7 key set + the authorized eligibility_conditions key
    fe = rec122["field_evidence"]
    assert set(fe.keys()) == {
        "amount", "description", "eligibility_conditions", "granularity",
        "industry", "title", "type", "unit", "valid_period",
    }, f"field_evidence keys changed: {set(fe.keys())}"
    # the only delta (eligibility_conditions) matches the GAP-5 spec
    ec = fe["eligibility_conditions"]
    assert isinstance(ec.get("quote"), str) and ec["quote"]
    assert (isinstance(ec.get("char_span"), list) and len(ec["char_span"]) == 2
            and ec["char_span"][0] is not None), "eligibility_conditions char_span invalid"
    assert ec["content_identity"] == rec122["content_identity"]
    assert ec["source_url"] == rec122["source_url"]
    assert ec["snapshot_ref"] == rec122["snapshot_ref"]
    # P6-3.18: REAL 122 now carries per-context trust_bindings (additive; legacy
    # top-level evidence_id/verified_event_id/CI untouched). Context B binding unchanged.
    tb = rec122.get("trust_bindings", {})
    assert set(tb.keys()) == {"ctx_122_stabilization_subsidy", "context_a"}, tb.keys()
    assert tb["ctx_122_stabilization_subsidy"] == {
        "evidence_id": "ev_ctx_122_stabilization_subsidy",
        "verified_event_id": "a060ee6f9d1945bca55e8dbe593f5891",
    }
    assert tb["context_a"]["evidence_id"] == "ev_ctx_122_context_a"
    assert tb["context_a"]["verified_event_id"] == "d8d5cc1dbd394eb58ccb501116e98487"
