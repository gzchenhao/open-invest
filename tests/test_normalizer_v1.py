"""P3-2 Normalizer 测试：逐字段 null-safe 抽取 + 治理纪律。

覆盖 12 个 fixture，并明确证明：
- 不生成 VERIFIED / 不修改 20 REAL / 不调用 src.trust
- 不生成默认 Shanghai / 默认日期 / 联系人
- 不把普通关键词变成 industry / 比例变成金额 / 背景变成 requirements
- 非 null 字段必须带 quote evidence
"""

import json
from pathlib import Path

from global_policy_aggregator.pipeline import normalizer as N
from global_policy_aggregator.pipeline.normalizer import run_pipeline
from global_policy_aggregator.pipeline.parser import ParseFailure

FIX = Path(__file__).resolve().parent / "fixtures" / "pipeline"
SRC = "https://www.gov.cn/policy/example.html"
SNAP = "snapshots/example/abc.html"

REAL_POLICIES = (
    Path(__file__).resolve().parents[1]
    / "global_policy_aggregator" / "data" / "real_policies" / "real_policies.json"
)


def load(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def norm(name: str):
    return run_pipeline(load(name), SRC, SNAP)


# ── 1. 正常 gov.cn ──────────────────────────────────────────────────────
def test_normal_full():
    c = norm("fixture_normal.html")
    assert c.title == "深圳市人工智能产业发展规划"
    assert c.source_url == SRC
    assert c.description
    assert c.source_organization == "深圳市工业和信息化局"
    assert c.region == "深圳市"
    assert c.type == "plan"
    assert c.issue_date == "2026-03-01"
    assert c.valid_period == {"start": "2026-03-01", "end": "2030-12-31"}
    assert c.industry == "ai"
    assert c.amount["normalized_number"] == 5000000
    assert c.amount["currency"] == "CNY"
    assert "500万元" in c.amount["raw_text"]
    assert "申报条件" in c.requirements
    assert "申报对象" in c.eligibility
    assert c.contact is None
    assert c.evidence_violations() == []
    assert c.verification_status == "unverified"
    assert c.is_mock is False


# ── 2. 缺字段 ──────────────────────────────────────────────────────────
def test_missing_fields_null():
    c = norm("fixture_missing.html")
    assert c.title == "关于推进相关工作的安排"
    assert c.source_organization is None
    assert c.region is None
    assert c.issue_date is None
    assert c.valid_period is None
    assert c.amount is None
    assert c.requirements is None
    assert c.eligibility is None
    assert c.industry == "unknown"
    assert c.evidence_violations() == []
    # null 字段记录了原因
    assert c.extracted_fields_evidence["region"].null_reason


# ── 3. HTML 结构变化 ───────────────────────────────────────────────────
def test_structure_changed_still_extracts():
    c = norm("fixture_structure_changed.html")
    assert c.title == "结构变化下的政策标题"
    assert c.source_organization == "某部门"
    assert c.industry == "ai"
    assert c.evidence_violations() == []


# ── 4. 明确金额 ────────────────────────────────────────────────────────
def test_amount_explicit():
    c = norm("fixture_amount_explicit.html")
    assert c.amount["normalized_number"] == 5000000
    assert c.amount["currency"] == "CNY"


# ── 5. 模糊金额 ────────────────────────────────────────────────────────
def test_amount_ambiguous_null():
    c = norm("fixture_amount_ambiguous.html")
    assert c.amount is None
    assert c.extracted_fields_evidence["amount"].null_reason


# ── 6. 明确 requirements ───────────────────────────────────────────────
def test_requirements_explicit():
    c = norm("fixture_requirements_explicit.html")
    assert c.requirements and "申报条件" in c.requirements


# ── 7. 模糊 requirements ───────────────────────────────────────────────
def test_requirements_ambiguous_null():
    c = norm("fixture_requirements_ambiguous.html")
    assert c.requirements is None


# ── 8. contact 存在但不抽取 ────────────────────────────────────────────
def test_contact_present_but_deferred():
    c = norm("fixture_contact_present.html")
    assert c.contact is None
    assert (c.extracted_fields_evidence["contact"].null_reason
            == "contact_extraction_deferred_to_P3_3")


# ── 9. industry 明确 ──────────────────────────────────────────────────
def test_industry_explicit():
    c = norm("fixture_industry_explicit.html")
    assert c.industry == "ai"


# ── 10. industry 仅普通关键词 ──────────────────────────────────────────
def test_industry_keyword_only_unknown():
    c = norm("fixture_industry_keyword_only.html")
    assert c.industry == "unknown"


# ── 11. unknown industry ───────────────────────────────────────────────
def test_industry_unknown():
    c = norm("fixture_industry_unknown.html")
    assert c.industry == "unknown"


# ── 12. 重复 / 乱码 ────────────────────────────────────────────────────
def test_garbled_no_crash():
    res = norm("fixture_garbled.html")
    assert not isinstance(res, ParseFailure)
    assert res.evidence_violations() == []


# ── 治理测试（section XV） ──────────────────────────────────────────────
def test_no_verified_anywhere():
    for name in [
        "fixture_normal.html", "fixture_missing.html", "fixture_structure_changed.html",
        "fixture_amount_explicit.html", "fixture_amount_ambiguous.html",
        "fixture_requirements_explicit.html", "fixture_requirements_ambiguous.html",
        "fixture_contact_present.html", "fixture_industry_explicit.html",
        "fixture_industry_keyword_only.html", "fixture_industry_unknown.html",
        "fixture_garbled.html",
    ]:
        c = norm(name)
        assert c.verification_status != "VERIFIED"
        assert "VERIFIED" not in json.dumps(c.to_dict(), ensure_ascii=False)


def test_no_default_shanghai():
    c = norm("fixture_missing.html")
    assert c.region is None  # 不是 "Shanghai"/"上海"


def test_no_default_date():
    c = norm("fixture_missing.html")
    assert c.issue_date is None
    assert c.valid_period is None  # 不是 2025-12-31


def test_no_contact_in_any_fixture():
    for name in [
        "fixture_normal.html", "fixture_contact_present.html", "fixture_missing.html",
    ]:
        assert norm(name).contact is None


def test_quote_required_for_nonnull():
    c = norm("fixture_normal.html")
    for field, ev in c.extracted_fields_evidence.items():
        if field in ("industry", "type"):
            continue  # 受控词表分类结果允许 unknown（无 quote）
        if ev.value is not None:
            assert ev.quote, f"{field} 非 null 但缺 quote"


def test_quote_is_verbatim_not_rewritten():
    c = norm("fixture_normal.html")
    assert c.extracted_fields_evidence["title"].quote == c.title
    assert "500万元" in c.extracted_fields_evidence["amount"].quote


def test_real_policies_untouched():
    data = json.loads(REAL_POLICIES.read_text(encoding="utf-8"))
    arr = data["policies"] if isinstance(data, dict) and "policies" in data else data
    assert len(arr) == 20
    ids = {p["id"] for p in arr}
    assert ids == set(range(101, 121))
    for p in arr:
        assert p["is_mock"] is False
        assert p["verification_status"] == "unverified"


def test_no_src_trust_import():
    src = Path(__file__).resolve().parents[1] / "global_policy_aggregator" / "pipeline" / "normalizer.py"
    content = src.read_text(encoding="utf-8")
    assert "src.trust" not in content
    assert "verification_status" not in content or "VERIFIED" not in content
