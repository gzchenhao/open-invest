"""P3-2.x Rule Evidence extraction tests.

覆盖：
- 高新技术企业15%：percentage=0.15, base=应纳税所得额, type=tax_break, 3 条结构化条件
- 首台套80%+cap3%：percentage=0.80, base=实际投保年度保费, cap=0.03
- 模糊表述（原则上/适当支持）→ percentage null
- 缺失基数 → base null
- 无明确 cap → cap null
- evidence-bound：每字段带 quote / method
"""

import os
from pathlib import Path

from global_policy_aggregator.pipeline.parser import parse_html
from global_policy_aggregator.pipeline.normalizer import normalize

FIX = Path(__file__).resolve().parent / "fixtures"


def _norm(html_name, source_url="https://www.gov.cn/zhengce/x.html"):
    html = (FIX / html_name).read_text(encoding="utf-8")
    parsed = parse_html(html, source_url, "snapshots/x/y.html")
    return normalize(parsed, source_url, "snapshots/x/y.html")


def test_hightech_percentage_and_base():
    c = _norm("policy_hightech_15pct.html")
    assert c.percentage == 0.15
    assert c.base == "应纳税所得额"
    assert c.type == "tax_break"
    assert c.extracted_fields_evidence["percentage"].method == "regex_percentage"
    # 抽取到 15%（原文含全角％与半角%两种写法，value 必须为 0.15）
    assert c.percentage == 0.15
    assert "15" in (c.extracted_fields_evidence["percentage"].quote or "")


def test_hightech_eligibility_conditions():
    c = _norm("policy_hightech_15pct.html")
    conds = c.eligibility_conditions or []
    ids = {x["id"] for x in conds}
    assert "registered_years_min" in ids
    assert "rd_staff_ratio_min" in ids
    assert "hightech_income_ratio_min" in ids
    for x in conds:
        assert x["quote"]  # evidence-bound


def test_firstset_percentage_base_cap():
    c = _norm("policy_firstset_80pct_cap3.html",
              source_url="https://www.gov.cn/zhengce/firstset.html")
    assert c.percentage == 0.80
    assert c.base == "实际投保年度保费"
    assert c.cap == 0.03
    assert c.floor is None


def test_ambiguous_percentage_null():
    html = "<html><body><p>原则上给予企业15%的补贴支持。</p></body></html>"
    c = _norm_from_html(html)
    assert c.percentage is None
    assert c.extracted_fields_evidence["percentage"].null_reason == "percentage_not_explicit_semantics"


def test_missing_base_null():
    html = "<html><body><p>对符合条件的企业减按15%的税率征收企业所得税。</p></body></html>"
    c = _norm_from_html(html)
    assert c.percentage == 0.15
    # 无明确基数表述 → base null
    assert c.base is None


def test_no_cap_when_absent():
    html = "<html><body><p>国家需要重点扶持的高新技术企业，减按15%的税率征收企业所得税。</p></body></html>"
    c = _norm_from_html(html)
    assert c.cap is None
    assert c.floor is None


def _norm_from_html(html, source_url="https://www.gov.cn/zhengce/x.html"):
    parsed = parse_html(html, source_url, "snapshots/x/y.html")
    return normalize(parsed, source_url, "snapshots/x/y.html")
