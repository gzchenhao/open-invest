# -*- coding: utf-8 -*-
"""P4-5.2 — Rule Context Split + Project Input Contract Audit（回归套件）。

只读消费既有 Evidence，不补值、不猜测；不触碰 real_policies.json / REAL 101–121 /
REAL 122 / Trust / src/trust / commit。固定回归 §2 三条设计决策。
"""
import hashlib
import io
import json
import os

import pytest

from global_policy_aggregator.pipeline.parser import parse_html
from global_policy_aggregator.pipeline.normalizer import normalize
from global_policy_aggregator.pipeline.rule_context import (
    GAP_BASE_UNMAPPED,
    GAP_PER_UNIT,
    GAP_TIERED,
    RD_NOT_READY,
    audit_policy_rule_contexts,
    assess_context_readiness,
    segment_clauses,
    split_rule_contexts,
)

FIX = "tests/fixtures/pipeline/notice39_rule_structure.html"
REAL = "global_policy_aggregator/data/real_policies/real_policies.json"
# 权威生效 URL（2026-07 发文页）；P4-5.1 捕获时记录的 202601/content_39.htm 为失效路径，
# 本阶段在 fixture 级校正 provenance（不触碰 REAL/生产）。
URL = "https://www.gov.cn/zhengce/zhengceku/202607/content_7074139.htm"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _build_record():
    with io.open(os.path.join(ROOT, FIX), encoding="utf-8") as f:
        html = f.read()
    ci = hashlib.sha256(html.encode("utf-8")).hexdigest()
    parsed = parse_html(html, URL, snapshot_ref=f"snapshots/{ci}.html")
    cand = normalize(parsed, URL, snapshot_ref=f"snapshots/{ci}.html")
    rec = dict(cand.to_dict())
    rec["content_identity"] = ci
    rec["source_url"] = URL
    rec["snapshot_ref"] = f"snapshots/{ci}.html"
    return rec, parsed.clean_text, ci


@pytest.fixture(scope="module")
def audit():
    rec, clean, ci = _build_record()
    return audit_policy_rule_contexts(rec, clean, policy_ref="39hao"), rec, clean, ci


# ── A. 条文切分（§3 第 1 条）─────────────────────────────────────────────
def test_clause_segmentation(audit):
    rep, rec, clean, _ = audit
    clauses = segment_clauses(clean)
    assert len(clauses) == 3, clauses
    assert rep["clause_count"] == 3
    assert rep["context_count"] == 2, "两条带受益信号的条款 → 两个 Rule Context"
    # char_span 包住条款（Clause.text 已 strip 尾随空白）→ 比对去尾后逐字一致
    for c in clauses:
        assert clean[c.char_span[0]:c.char_span[1]].strip() == c.text, c.clause_id


# ── B. 拆分正确性（决策 1：rule_type 语义 ≠ 可执行性，§3 第 2 条）────────
def test_rule_type_split(audit):
    rep, _, _, _ = audit
    assert rep["rule_types"] == ["percentage_of_base", "fixed_amount"], rep["rule_types"]
    by_rt = {c["rule_type"]: c for c in rep["contexts"]}
    # Context B（稳岗返还）基数未进 BASE_INPUT_MAP 仍须是 percentage_of_base，
    # 不得退化成 unsupported（这是 P4-5.1 返工点）
    ctx_b = by_rt["percentage_of_base"]
    assert ctx_b["base_input_mapping"] is None
    assert GAP_BASE_UNMAPPED in ctx_b["contract_gaps"]
    assert ctx_b["rule_type_source"] == "derived"
    # Context A（扩岗补助）
    ctx_a = by_rt["fixed_amount"]
    assert ctx_a["amount"] == 1500
    assert ctx_a["unit"] == "元/人"


# ── C. 分档（决策 2：禁止外露扁平 percentage/cap，§3 第 3 条）────────────
def test_tiered_variants(audit):
    rep, _, _, _ = audit
    ctx_b = next(c for c in rep["contexts"] if c["rule_type"] == "percentage_of_base")
    variants = ctx_b["benefit_variants"]
    assert len(variants) == 2, "大型 / 中小微 两档"
    assert [v["applies_when"]["source_field"] for v in variants] == ["company_size", "company_size"]
    assert [v["applies_when"]["equals"] for v in variants] == ["大型企业", "中小微企业"]
    assert [v["percentage"] for v in variants] == [0.3, 0.6]
    assert variants[1]["base_inherited_from"] == variants[0]["variant_id"]  # 同句省略基数
    # 扁平字段对分档规则必须置 None（否则另一档被误读为 cap）
    assert ctx_b["percentage"] is None
    assert ctx_b["cap"] is None
    assert GAP_TIERED in ctx_b["contract_gaps"]
    assert "禁止用于计算" in ctx_b["flat_schema_observed"].get("note", "")
    assert ctx_b["flat_schema_warning"]


# ── D. 资格条件不得当受益比例；per-unit 不得当总额（决策 3，§3 第 4 条）──
def test_conditions_not_benefit(audit):
    rep, _, _, _ = audit
    ctx_b = next(c for c in rep["contexts"] if c["rule_type"] == "percentage_of_base")
    cond_ids = {c["id"] for c in ctx_b["conditions"]}
    # 「裁员率不高于参保职工总数 20%」是 eligibility，且带前置（30人以下）
    assert "layoff_rate_carveout_max" in cond_ids
    carveout = next(c for c in ctx_b["conditions"] if c["id"] == "layoff_rate_carveout_max")
    assert carveout["threshold"] == 0.2
    assert carveout["enforcement"] == "conditional"
    assert carveout["precondition"]["source_field"] == "insured_employee_count"
    assert carveout["precondition"]["threshold"] == 30.0
    assert "20%" not in str([v["percentage"] for v in ctx_b["benefit_variants"]])
    # 外部统计阈值不入 benefit
    ctrl = next(c for c in ctx_b["conditions"] if c["id"] == "layoff_rate_control_target_max")
    assert ctrl["evaluable"] is False
    assert ctrl["threshold_source"] == "external_official_statistic_not_in_policy"

    # Context A per-unit
    ctx_a = next(c for c in rep["contexts"] if c["rule_type"] == "fixed_amount")
    pu = ctx_a["benefit_basis"]["per_unit"]
    assert pu and pu["unit"] == "元/人"
    assert GAP_PER_UNIT in ctx_a["contract_gaps"]
    assert GAP_PER_UNIT in ctx_a["contract_gaps"]


# ── E. 证据链完整性（quote/char_span/snapshot_ref/content_identity/source_url）──
def test_evidence_chain_complete(audit):
    rep, _, _, _ = audit
    for ctx in rep["contexts"]:
        for ev in ctx["evidence_refs"]:
            assert ev["quote"], ev["field"]
            assert ev["char_span"], ev["field"]
            assert ev["snapshot_ref"], ev["field"]
            assert ev["content_identity"], ev["field"]
            assert ev["source_url"] == URL, ev["field"]
        for v in ctx["benefit_variants"]:
            assert v["quote"] and v["char_span"]


# ── F. Project Input Contract（缺失一律 MISSING，无默认值，§3 第 7 条）───
def test_project_input_contract(audit):
    rep, _, _, _ = audit
    missings = [c["missing"] for c in rep["contracts"]]
    flat = sorted({k for m in missings for k in m})
    expected = sorted({
        "company_size", "prior_year_ui_premium_paid", "ui_paid_months",
        "layoff_rate", "insured_employee_count",
        "hired_person_count", "employment_insurance_paid_months",
        "labor_contract_signed", "applicant_entity_type", "hired_target_group",
    })
    assert flat == expected, flat
    for c in rep["contracts"]:
        assert c["contract_complete"] is False
        assert c["derivable_from_policy"] is False
        for r in c["inputs"]:
            assert r["policy_requirement_quote"], r["input_key"]
            assert r["status"] == "MISSING"
            assert r["derivable_from_policy"] is False


# ── G. Readiness（无事实 → NOT_READY；伪造 verified/approved 不得提升，§3 第 8 条）
def test_readiness_not_ready_without_facts(audit):
    rep, _, _, _ = audit
    assert rep["overall_readiness"] == RD_NOT_READY
    for r in rep["readiness"]:
        assert r["overall"] == RD_NOT_READY
        assert r["provenance_readiness"] == RD_NOT_READY
        assert r["application_readiness"] == RD_NOT_READY
        assert "no_trust_verified_provenance" in r["blocking"]
        assert "application_requirements_absent" in r["blocking"]


def test_fabricated_verified_approved_does_not_elevate():
    rec, clean, _ = _build_record()
    rec["verified"] = True
    rec["approved"] = True
    rep = audit_policy_rule_contexts(rec, clean, policy_ref="39hao")
    assert rep["overall_readiness"] == RD_NOT_READY, "derived ≠ approved ≠ VERIFIED"
    for ctx in rep["contexts"]:
        assert ctx["human_approved"] is False
        v = " ".join(ctx["governance_violations"])
        assert "verified" in v and "approved" in v, ctx["governance_violations"]


def test_rule_type_approval_invalid_is_governance_violation():
    rec, clean, _ = _build_record()
    rec["rule_type_approval"] = {"status": "approved", "verified_event_id": None}
    from global_policy_aggregator.pipeline.p4_rule_engine import rule_type_approval_status
    assert rule_type_approval_status(rec) == "invalid"
    rep = audit_policy_rule_contexts(rec, clean, policy_ref="39hao")
    for ctx in rep["contexts"]:
        assert any("rule_type_approval_invalid" in g for g in ctx["governance_violations"])


# ── H. 只读边界：REAL 101–121 不被本阶段改动（§3 第 9 条）──────────────
def test_real_101_121_untouched():
    # 101–121 不被改动；REAL 122 已由 P3-7 正式写入（合法，非本阶段泄露）。
    path = os.path.join(ROOT, REAL)
    with io.open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data["policies"] if isinstance(data, dict) else data
    ids = sorted(int(r["id"]) for r in rows)
    assert len(rows) == 22, len(rows)            # REAL 101–121 = 21 条 + REAL 122 (P3-7)
    assert ids == list(range(101, 123)), ids
    assert 122 in ids, "REAL 122 应由 P3-7 正式写入"
    assert max(ids) == 122


def test_read_only_does_not_write_real(tmp_path):
    """跑全流程后，real_policies.json 字节级未变（落盘前快照比对）。"""
    import shutil
    src = os.path.join(ROOT, REAL)
    snap = tmp_path / "real_policies.snap.json"
    shutil.copy(src, snap)
    before = hashlib.sha256(io.open(src, "rb").read()).hexdigest()
    _build_record()  # 触发解析/拆分/审计，纯内存
    after = hashlib.sha256(io.open(src, "rb").read()).hexdigest()
    assert before == after, "real_policies.json 不应被本阶段写入"
