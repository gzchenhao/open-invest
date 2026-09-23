"""P4-2A.1 extractor hardening regression tests (JUDGE-approved).

三个修复的 minimal 必要测试：
1. TITLE PRIORITY — 官方 <title>/<h1> 优先于正文《...》交叉引用。
2. PERCENTAGE EXTRACTION — clause-anchored，排除法定基准税率，优先优惠税率（减按），
   多优惠税率取最后一个（最具体）。
3. SOURCE ORGANIZATION — 优先页面正文发布机关字段；无 body evidence 时宁可 null。

仅使用 ParsedContent 单元测试，不依赖真实网络。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from global_policy_aggregator.pipeline.parser import ParsedContent
from global_policy_aggregator.pipeline.normalizer import (
    extract_title,
    extract_percentage,
    extract_source_organization,
)

SNAP = "snapshots/test_p4_extractor_hardening"


def _parsed(title_raw, h1_raw, clean_text):
    return ParsedContent(
        source_url="https://example.gov.cn/p.html",
        snapshot_ref=SNAP,
        clean_text=clean_text,
        title_raw=title_raw,
        h1_raw=h1_raw,
    )


def test_title_priority_over_booktitle_crossreference():
    # 正文含《税收征收管理法》交叉引用，但官方 <title> 是企业所得税法
    clean = (
        "中华人民共和国企业所得税法\n"
        "第一章 总则\n"
        "相关法规参见《中华人民共和国税收征收管理法》。\n"
        "第二十八条 国家需要重点扶持的高新技术企业，减按15％的税率征收企业所得税。"
    )
    p = _parsed(title_raw="中华人民共和国企业所得税法", h1_raw=None, clean_text=clean)
    fe = extract_title(p, SNAP)
    assert fe.value == "中华人民共和国企业所得税法"
    assert "税收征收管理法" not in fe.value
    assert fe.char_span is not None  # quote 必须在 clean text 中可定位


def test_percentage_clause_anchored_excludes_standard_rate():
    # Article 4 标准税率 25%（税率为X%），Article 28 优惠税率（减按）20% 与 15%
    clean = (
        "第一条 在中华人民共和国境内...企业所得税。\n"
        "第四条 企业所得税的税率为25%。\n"
        "第二十八条 符合条件的小型微利企业，减按20%的税率征收企业所得税。"
        "国家需要重点扶持的高新技术企业，减按15％的税率征收企业所得税。"
    )
    p = _parsed(title_raw="中华人民共和国企业所得税法", h1_raw=None, clean_text=clean)
    fe = extract_percentage(p, SNAP)
    assert fe.value == 0.15
    assert "减按15％的税率征收企业所得税" in fe.quote
    assert fe.char_span is not None
    # 必须排除无关基准税率 25%
    assert "25" not in fe.quote


def test_source_organization_from_body_label():
    clean = "发布机关：财政部\n发文日期：2007年3月19日\n正文..."
    p = _parsed(title_raw="x", h1_raw=None, clean_text=clean)
    fe = extract_source_organization(p, SNAP)
    assert fe.value == "财政部"
    assert fe.char_span is not None


def test_source_organization_null_when_only_footer_evidence():
    # 正文无发布机关字段（footer 模板在解析阶段已被剥离，不进入 clean text）
    clean = "第一章 总则\n第二条 企业分为居民企业和非居民企业。\n正文..."
    p = _parsed(title_raw="中华人民共和国企业所得税法", h1_raw=None, clean_text=clean)
    fe = extract_source_organization(p, SNAP)
    assert fe.value is None
    assert fe.null_reason == "no_explicit_publisher"
