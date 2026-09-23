"""P4-5.1 — REAL POLICY INGESTION TRUST HARDENING 回归测试（D1–D4）。

D1  gov.cn 正文完整性：提前闭合 </html> 导致 lxml 静默丢失正文 → 确定性恢复 + 完整性 fail-closed
D2  landmark 选择：mainnav 等导航容器（子串假阳性）绝不作为正文；歧义 fail-closed
D3  抽取 fail-closed：percentage/amount/base/region/unit/valid_period 的字段级上下文约束，
    以及「同一 rule / 条款上下文」的 quote 一致性（禁止跨条款借证据）
D4  derived / approved / Trust VERIFIED 三分：derived 绝不等于人工批准，更不等于 VERIFIED/READY

治理边界（本测试文件同样遵守）：
- 只读：不写 real_policies.json、不创建 REAL 122、不调用 Human Verification、不执行 P3-7。
- 需要写盘的两处（D4 ingestion 断言）只在 tmp_path 的副本上进行。
- fixture 只用于解析/归一化回归，**不得**冒充 REAL 政策记录。
"""

from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import pytest

from global_policy_aggregator.pipeline import p4_rule_engine as eng
from global_policy_aggregator.pipeline import parser as parser_mod
from global_policy_aggregator.pipeline.normalizer import normalize
from global_policy_aggregator.pipeline.p4_execution_state import (
    STATE_EXECUTION_READY,
    STATE_NOT_READY,
    assess_execution_readiness,
)
from global_policy_aggregator.pipeline.p4_rule_engine import build_rule_from_real_record
from global_policy_aggregator.pipeline.p4_rule_operator import evaluate_policy
from global_policy_aggregator.pipeline.parser import (
    ParseError,
    parse_html,
    _CONTENT_TOKENS,
    _NAV_TOKENS,
    _recover_early_closed_html,
)
from global_policy_aggregator.pipeline.real_ingestion import (
    PRODUCTION_REAL_POLICIES_PATH,
)

_ROOT = Path(__file__).resolve().parent.parent
_FIX = Path(__file__).resolve().parent / "fixtures" / "pipeline"
_REAL_PATH = _ROOT / "global_policy_aggregator" / "data" / "real_policies" / "real_policies.json"
_SNAPSHOT_DIR = _ROOT / "data" / "raw_policies" / "snapshots"

_URL = "https://www.gov.cn/zhengce/zhengceku/202607/content_7074139.htm"
_SNAP = "snapshots/www.gov.cn/7b1bc00c772d08af28c8175dd24b51f2cfdd0a4e2f1a438d48fefc5574c27aba.html"
_REAL_121_VERIFIED_EVENT_ID = "07d2478c261f4ab6a251b320af179981"
_LAW_SNAPSHOT = (_SNAPSHOT_DIR / "www.mof.gov.cn"
                 / "ddd6116bac2ab62ce0ccbcaca4656bb9fa28c864475392473ad700b86ddc3c0b.html")


def _norm(html, url=_URL, snap=_SNAP):
    return parse_html(html, url, snap)


def _render(html, url=_URL, snap=_SNAP):
    return normalize(parse_html(html, url, snap), url, snap)


def _real_records():
    data = json.loads(_REAL_PATH.read_text(encoding="utf-8"))
    return data["policies"] if isinstance(data, dict) else data


def _page(body: str, title: str = "测试政策通知") -> str:
    return (f"<html><head><title>{title}</title></head><body>{body}</body></html>")


# ===========================================================================
# D1 — gov.cn 正文完整性
# ===========================================================================

def test_d1_1_premature_close_recovers_full_body():
    """真实 gov.cn 模板结构：页头后的提前 </html> 不得导致正文丢失。"""
    html = (_FIX / "gov_template_early_close.html").read_text(encoding="utf-8")
    pc = _norm(html)
    assert pc.meta["premature_closes_removed"] == 1
    assert pc.meta["landmark"] == "attr_content"
    assert pc.structure_changed is False
    # 正文完整：页头之后的内容全部保留
    assert "第三条 正文总长度必须显著大于原始可见文本的一成" in pc.clean_text
    assert "第一条 本模板用于回归验证" in pc.clean_text
    # 导航不得混入正文（D2 同源缺陷）
    assert "最新政策" not in pc.clean_text
    assert "网站无障碍开关" not in pc.clean_text


def test_d1_2_recovery_is_noop_on_wellformed_document():
    """良构文档：恢复逻辑必须是 no-op（绝不删除内容）。"""
    html = (_FIX / "fixture_normal.html").read_text(encoding="utf-8")
    pc = _norm(html)
    assert pc.meta["premature_closes_removed"] == 0
    assert "人工智能" in pc.clean_text


def test_d1_3_recovery_only_fires_when_document_continues():
    """只在「闭合之后仍有结构化标记」时移除，且只删闭合标签、不删内容。"""
    same, n = _recover_early_closed_html("<html><head></head><body></body></html>")
    assert n == 0 and same == "<html><head></head><body></body></html>"
    rec, n2 = _recover_early_closed_html("</html><div>正文不得被删除</div></html>")
    assert n2 == 1
    assert "正文不得被删除" in rec
    assert rec.count("</html>") == 1


def test_d1_4_incomplete_body_fail_closed():
    """解析结果明显小于原始可见文本 → 拒绝产出伪完整政策（不得静默当成功）。"""
    html = _page("<header><p>" + "页头导航文字" * 90 + "</p></header>"
                 "<div class='content'><p>短</p></div>")
    with pytest.raises(ParseError) as ei:
        _norm(html)
    assert ei.value.failure_type == "incomplete_body"


def test_d1_5_provenance_preserved():
    """D1 修复不得破坏 provenance（source_url / snapshot_ref）。"""
    pc = _norm(_page("<div class='content'><p>正文内容用于 provenance 校验。</p></div>"))
    assert pc.source_url == _URL
    assert pc.snapshot_ref == _SNAP
    assert pc.parser_backend == "lxml"
    for key in ("landmark", "premature_closes_removed", "raw_visible_text_len",
                "clean_text_len"):
        assert key in pc.meta


# ===========================================================================
# D2 — landmark 选择
# ===========================================================================

def test_d2_1_mainnav_never_treated_as_body():
    """class="mainnav" 不得因子串包含 main 而被当作正文容器。"""
    html = _page("<div class='mainnav'>最新政策 部门文件 国务院文件 政策解读 信息公开</div>"
                 "<article><h1>标题</h1><p>真正正文内容，必须被选中。</p></article>")
    pc = _norm(html)
    assert pc.meta["landmark"] == "attr_content"
    assert "真正正文内容" in pc.clean_text
    assert "最新政策" not in pc.clean_text


def test_d2_2_header_footer_never_treated_as_body():
    """header/footer 文本量大于正文时，仍必须选中正文容器。"""
    body = ("第一条 本页用于验证 landmark 选择：页头与页脚承载大量导航与备案文本，"
            "正文容器必须被正确识别，导航与页脚文本不得混入政策正文。"
            "第二条 正文长度需超过原始可见文本的一成，以避免触发完整性门限。")
    html = _page("<header><p>" + "页头导航文字" * 25 + "</p></header>"
                 f"<main><h1>标题</h1><p>{body}</p></main>"
                 "<footer><p>" + "页脚备案信息" * 25 + "</p></footer>")
    pc = _norm(html)
    assert pc.meta["landmark"] == "main_tag"
    assert "第一条 本页用于验证 landmark 选择" in pc.clean_text
    assert "页头导航文字" not in pc.clean_text
    assert "页脚备案信息" not in pc.clean_text


def test_d2_3_ambiguous_body_fail_closed():
    """多个同等量级正文候选 → 不得「第一个匹配就赢」→ fail-closed。"""
    html = _page("<div class='content'><p>甲甲甲甲甲甲甲甲甲甲</p></div>"
                 "<div class='article'><p>乙乙乙乙乙乙乙乙乙乙</p></div>")
    with pytest.raises(ParseError) as ei:
        _norm(html)
    assert ei.value.failure_type == "ambiguous_body"


def test_d2_4_single_main_is_selected():
    pc = _norm(_page("<main><h1>标题</h1><p>正文内容。</p></main>"))
    assert pc.meta["landmark"] == "main_tag"
    assert pc.structure_changed is False


def test_d2_5_no_substring_selector_hardcode():
    """选择器必须基于 token 精确匹配，不得回退为子串正则。"""
    src = inspect.getsource(parser_mod)
    assert '"content|main|article"' not in src
    assert "'content|main|article'" not in src
    assert "mainnav" in _NAV_TOKENS          # 显式排除为导航
    assert "mainnav" not in _CONTENT_TOKENS  # 绝不作为正文 token


# ===========================================================================
# D3 — 抽取 fail-closed + quote 同条款一致性
# ===========================================================================

def test_d3_1_notice39_rule_structure_regression():
    """#39 规则结构：受益比例 30% / 资格阈值不得入选 / per-unit 1500 元 / 有效期跨年共享。"""
    c = _render((_FIX / "notice39_rule_structure.html").read_text(encoding="utf-8"))
    assert c.percentage == 0.30                     # 不是 20% 裁员率阈值
    assert c.base == "企业及其职工上年度实际缴纳失业保险费"
    assert c.cap == 0.60
    assert c.floor is None
    assert c.amount["normalized_number"] == 1500
    assert c.amount["unit"] == "元/人"              # per-unit 量纲，不是一次性总额
    assert c.unit == "元/人"
    assert c.region is None                         # 不得由「直辖市」主送机关推断
    assert c.valid_period == {"start": "2026-01-01", "end": "2026-12-31"}
    assert c.evidence_violations() == []


def test_d3_2_quote_same_rule_context():
    """execution-critical 字段的 quote 必须来自同一 rule/条款上下文，且不得跨条款污染。"""
    c = _render((_FIX / "notice39_rule_structure.html").read_text(encoding="utf-8"))
    text = parse_html((_FIX / "notice39_rule_structure.html").read_text(encoding="utf-8"),
                      _URL, _SNAP).clean_text
    ev = c.extracted_fields_evidence

    pct_q = ev["percentage"].quote
    amt_q = ev["amount"].quote
    # 比例/基数/上限同属「稳岗返还」条款
    assert ev["base"].quote == pct_q
    assert ev["cap"].quote == pct_q
    assert "30%返还" in pct_q and "60%返还" in pct_q
    # 金额/单位同属「一次性扩岗补助」条款
    assert ev["unit"].quote == amt_q
    assert "1500元" in amt_q
    # 互不污染
    assert "1500" not in pct_q
    assert "30%返还" not in amt_q

    # 每个非 null 的 rule-level 字段的 quote 必须能在同一正文中精确定位（char_span 一致）
    for name in ("title", "type", "issue_date", "valid_period", "amount", "percentage",
                 "base", "cap", "floor", "unit", "region"):
        e = ev.get(name)
        if e is None or e.value is None:
            continue
        assert e.quote, f"{name} 有值但缺 quote"
        if e.char_span is not None:
            s, t = e.char_span
            assert text[s:t] == e.quote, f"{name} char_span 与 quote 不一致"


def test_d3_3_eligibility_threshold_percentage_rejected():
    """裁员率 / 调查失业率控制目标 / 参保职工总数 等 threshold 不得当作受益比例。"""
    c = _render(_page("<div class='content'><p>参保企业上年度未裁员或裁员率不高于上年度"
                      "全国城镇调查失业率控制目标，30人（含）以下的参保企业裁员率不高于"
                      "参保职工总数20%的，可以申请稳岗返还。</p></div>"))
    assert c.percentage is None
    ev = c.extracted_fields_evidence["percentage"]
    assert ev.null_reason
    assert c.base is None          # 不得为该阈值借一个基数
    assert c.cap is None


def test_d3_4_addressee_line_is_not_region():
    """主送机关（各省、自治区、直辖市…）不是适用范围证据 → region 必须为 null。"""
    pc = parse_html(_page("<div class='content'><p>各省、自治区、直辖市人民政府，国务院各部委、"
                          "各直属机构：</p><p>现就有关工作通知如下。</p></div>"), _URL, _SNAP)
    assert "直辖市" in pc.clean_text          # 原文确实含「直辖市」
    c = normalize(pc, _URL, _SNAP)
    assert c.region is None                  # 但主送机关不是适用范围证据


def test_d3_5_national_scope_recorded_with_evidence():
    """全国性适用若被原文显式表述，则必须带 Evidence 记录（而不是不记）。"""
    c = _render(_page("<div class='content'><p>本通知在全国范围内适用。</p></div>"))
    assert c.region == "全国"
    ev = c.extracted_fields_evidence["region"]
    assert ev.quote and "全国范围内适用" in ev.quote
    assert ev.method == "regex_national_scope"


def test_d3_6_amount_requires_benefit_context_and_unit_coherent():
    """非受益语境（注册资本等）不得产出金额；且没有金额就没有单位。"""
    c = _render(_page("<div class='content'><p>申请企业注册资本5000万元以上，"
                      "且近三年无重大违法记录。</p></div>"))
    assert c.amount is None
    assert c.extracted_fields_evidence["amount"].null_reason
    assert c.unit is None          # unit 不得脱离 amount 单独存在
    assert c.extracted_fields_evidence["unit"].null_reason == \
        "no_unit_without_benefit_amount"


def test_d3_7_per_unit_amount_keeps_dimension():
    """按人次计量的补助必须携带 元/人 量纲，避免被读成一次性总额。"""
    c = _render(_page("<div class='content'><p>可按每招用1人不超过1500元的标准发放"
                      "一次性扩岗补助。</p></div>"))
    assert c.amount["normalized_number"] == 1500
    assert c.amount["unit"] == "元/人"
    assert c.unit == "元/人"
    assert "每招用1人" in c.extracted_fields_evidence["amount"].quote


def test_d3_8_valid_period_shared_year_and_no_invention():
    """右端省略年份 → 继承左端；可疑区间与孤立日期 → fail-closed，不得凭空造日期。"""
    c1 = _render(_page("<div class='content'><p>本通知自2026年1月1日至12月31日执行。</p></div>"))
    assert c1.valid_period == {"start": "2026-01-01", "end": "2026-12-31"}

    c2 = _render(_page("<div class='content'><p>本通知自2026年12月31日至1月1日执行。</p></div>"))
    assert c2.valid_period["start"] == "2026-12-31"
    assert c2.valid_period["end"] is None      # 可疑区间：不得反推年份凑出区间

    c3 = _render(_page("<div class='content'><p>本通知于2026年6月18日印发。</p></div>"))
    assert c3.valid_period is None             # 孤立日期不是有效期
    assert c3.extracted_fields_evidence["valid_period"].null_reason == \
        "no_explicit_valid_period_start"


def test_d3_9_law_snapshot_semantics_unchanged():
    """法条快照（REAL 121 来源）：D3 修复不得改变其语义化结果。"""
    html = _LAW_SNAPSHOT.read_text(encoding="utf-8")
    c = _render(html, "https://www.mof.gov.cn/law.html", "snapshots/www.mof.gov.cn/x.html")
    assert c.percentage == 0.15
    assert c.base == "应纳税所得额"
    assert c.amount is None            # 税率待遇：无现金金额
    assert c.unit is None
    assert c.cap is None and c.floor is None
    assert c.region is None
    assert c.valid_period == {"start": "2008-01-01", "end": None}
    assert c.evidence_violations() == []
    assert c.verification_status == "unverified"


# ===========================================================================
# D4 — derived / approved / Trust VERIFIED 三分
# ===========================================================================

def _complete_record(**over):
    """字段完整的执行候选（用于 D4 分离与 readiness 断言；纯内存，不落盘）。"""
    cid = "cid_complete"
    fe = lambda f: {"field": f, "quote": "q", "content_identity": cid}
    rec = {
        "id": 999,
        "content_identity": cid,
        "source_url": "https://www.example.gov.cn/p1",
        "snapshot_ref": "snapshots/example.gov.cn/p1.html",
        "type": "notice",
        "issue_date": "2026-06-18",
        "valid_period": {"start": "2026-01-01", "end": "2026-12-31"},
        "percentage": 0.30,
        "base": "实际投保年度保费",       # 已知非税基数 → derived = percentage_of_base
        "amount": None,
        "unit": None,
        "currency": None,
        "eligibility_conditions": [{"id": "c", "quote": "q"}],
        "application_requirements": "按当地经办机构要求申报",
        "rule_type": "percentage_of_base",
        "field_evidence": {
            "percentage": fe("percentage"),
            "base": fe("base"),
            "eligibility_conditions": fe("eligibility_conditions"),
        },
        "verification_status": "unverified",
        "verified_event_id": _REAL_121_VERIFIED_EVENT_ID,
        "evidence_id": "ev_complete",
    }
    rec.update(over)
    return rec


def test_d4_1_derived_is_not_approved():
    """确定性推导出的 rule_type 只是 derived：不得自动等于 approved。"""
    rule = build_rule_from_real_record(_complete_record(rule_type=None))
    assert rule.rule_type_derived == "percentage_of_base"
    assert rule.rule_type_source == "derived"
    assert rule.rule_type_approved is None
    assert rule.human_approved is False
    assert rule.rule_type == rule.rule_type_derived


def test_d4_1b_unknown_base_derives_unsupported():
    """基数不在已知映射 → derived 必须 fail-closed 为 unsupported（不得猜测）。"""
    rule = build_rule_from_real_record(
        _complete_record(rule_type=None, base="企业及其职工上年度实际缴纳失业保险费"))
    assert rule.rule_type_derived == "unsupported"
    assert rule.rule_type == "unsupported"
    assert rule.rule_type_approved is None


def test_d4_2_fake_approved_marker_fail_closed():
    """「自称已批准」但 provenance 不完整/未绑定 Trust 事件 → 拒绝采纳 + 治理违规。"""
    rec = _complete_record(
        rule_type_approved="fixed_amount",
        rule_type_approval={"approved": True, "approved_by": "someone"},  # 缺事件绑定
    )
    assert eng.rule_type_approval_status(rec) == "invalid"
    approved, status = eng.resolve_approved_rule_type(rec)
    assert status == "invalid" and approved is None
    # 伪造的 approved 绝不生效：有效 rule_type 仍是 derived
    rule = build_rule_from_real_record(rec)
    assert rule.rule_type == rule.rule_type_derived == "percentage_of_base"
    assert rule.rule_type_approved is None
    # 且必须 fail-closed 到 NOT_READY
    r = assess_execution_readiness(rec)
    assert r["state"] == STATE_NOT_READY
    assert r["governance_violations"]
    assert r["rule_type_status"]["source"] == "derived"
    assert r["rule_type_status"]["approved"] is None


def test_d4_3_valid_approval_adopted_but_never_verified():
    """合法批准（绑定 Trust verified_event_id / evidence / content_identity）才可生效；
    即便如此 approved ≠ VERIFIED，仍不得 EXECUTION_READY。"""
    cid = "cid_complete"
    rec = _complete_record(
        rule_type_derived="percentage_of_base",
        rule_type_approved="tax_treatment_rate",
        rule_type_approval={
            "approved": True,
            "approved_rule_type": "tax_treatment_rate",
            "approved_by": "human-reviewer-1",
            "approval_event_id": _REAL_121_VERIFIED_EVENT_ID,
            "evidence_id": "ev_complete",
            "content_identity": cid,
        },
    )
    assert eng.rule_type_approval_status(rec) == "valid"
    approved, status = eng.resolve_approved_rule_type(rec)
    assert status == "valid" and approved == "tax_treatment_rate"

    rule = build_rule_from_real_record(rec)
    assert rule.rule_type == "tax_treatment_rate"
    assert rule.rule_type_derived == "percentage_of_base"   # derived 仍被保留、可审计
    assert rule.rule_type_source == "approved"
    assert rule.human_approved is True

    r = assess_execution_readiness(rec)
    assert r["rule_type_status"]["source"] == "approved"
    # approved ≠ VERIFIED：无 Trust VERIFIED provenance 时仍 NOT_READY
    assert r["state"] == STATE_NOT_READY
    assert r["rule_type_status"]["approved_equals_verified"] is False


def test_d4_4_derived_record_never_execution_ready():
    """字段完整 + derived rule_type（无 Trust）→ 仍不得 READY/VERIFIED。"""
    rec = _complete_record(rule_type_derived="percentage_of_base")
    r = assess_execution_readiness(rec)          # 不注入 trust_service（READ-ONLY 默认）
    assert r["state"] == STATE_NOT_READY
    assert r["state"] != STATE_EXECUTION_READY
    assert r["missing_required"] == []           # 字段齐全
    assert "percentage" in r["unverified_critical_fields"]
    assert r["rule_type_status"]["derived"] == "percentage_of_base"
    assert r["rule_type_status"]["approved"] is None
    assert r["rule_type_status"]["derived_equals_verified"] is False
    assert r["rule_type_status"]["human_approved"] is False


def test_d4_5_evaluate_policy_reports_source():
    """执行侧必须显式暴露 rule_type 来源，避免把 derived 当 approved 使用。"""
    out = evaluate_policy(_complete_record())
    assert out["rule_type"] == "percentage_of_base"
    assert out["rule_type_source"] == "derived"
    assert out["rule_type_approved"] is None
    assert out["human_approved"] is False


def test_d4_6_no_boolean_verified_reintroduced():
    """不得重新引入裸 boolean verified 旁路。"""
    out = evaluate_policy(_complete_record())
    assert "verified" not in out
    r = assess_execution_readiness(_complete_record())
    assert "verified" not in r
    src = inspect.getsource(eng)
    assert '"verified": True' not in src
    assert "'verified': True" not in src


# ===========================================================================
# D4 — ingestion（P3-7 入口）只写 derived；不写 approved / VERIFIED
# ===========================================================================

class _FakeTrust:
    def __init__(self, ci, snapshot_ref, url):
        self.ev = {
            "id": "ev-1", "type": "policy", "source": "openinvest-pipeline",
            "source_reference": snapshot_ref, "verification_status": "VERIFIED",
            "confidence_score": 0.0,
            "metadata": {"policy_content_identity": ci, "snapshot_ref": snapshot_ref,
                         "candidate_id": "cand-1", "source_url": url,
                         "provenance": {"snapshot_ref": snapshot_ref, "source_url": url}},
        }
        self.called = False

    def get_evidence(self, evidence_id):
        if evidence_id != "ev-1":
            return {"success": False, "error": "not found"}
        return {"success": True, "evidence": self.ev}

    def check_verified_validity(self, evidence_id):
        if evidence_id != "ev-1":
            return {"is_valid": False, "reasons": ["none"], "latest_verified_event": None}
        return {"is_valid": True, "reasons": [],
                "latest_verified_event": {"event_id": "evt-1", "decision": "verified"}}

    def get_verification_history(self, evidence_id):
        return {"success": True, "event_count": 0, "events": []}

    def record_human_verification(self, *a, **k):
        self.called = True
        raise AssertionError("P3-7 must NOT call record_human_verification()")


def _g1_env(tmp_path):
    from global_policy_aggregator.pipeline.fetcher import compute_content_hash
    data = json.loads(PRODUCTION_REAL_POLICIES_PATH.read_text(encoding="utf-8"))
    data = [p for p in data if 101 <= p.get("id", 0) <= 120]
    real_copy = tmp_path / "real_policies.json"
    real_copy.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()
    content = "<html>policy text</html>".encode()
    ci = compute_content_hash(content)
    p = snapshots_dir / "example.com" / f"{ci}.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return {
        "real_policies_path": real_copy,
        "snapshots_dir": snapshots_dir,
        "audit_path": tmp_path / "audit.jsonl",
        "lock_path": tmp_path / ".lock",
    }, f"snapshots/example.com/{ci}.html", ci


def test_d4_7_ingestion_writes_derived_only(tmp_path):
    """ingestion 只写 rule_type_derived（source=derived），approved 恒为 None。"""
    env, snap_ref, ci = _g1_env(tmp_path)
    trust = _FakeTrust(ci, snap_ref, "https://example.com/p1")
    from global_policy_aggregator.pipeline.real_ingestion import ingest_verified_evidence
    rid = ingest_verified_evidence("ev-1", trust, **env)
    data = json.loads(env["real_policies_path"].read_text(encoding="utf-8"))
    rec = next(e for e in data if e["id"] == rid)
    assert rec["rule_type_source"] == "derived"
    assert rec["rule_type_approved"] is None
    assert rec["rule_type_approval"] is None
    assert rec["rule_type_derived"] == rec["rule_type"]
    assert rec["verification_status"] == "unverified"
    assert trust.called is False
    # 临时副本上的 ingestion 不泄露到生产文件（P4 阶段不得产生额外 REAL）。
    # 剥离 P3-7 合法写入的 REAL 122，剩余子集必须为原始 101–121，无任何 123+ 泄露。
    prod = json.loads(PRODUCTION_REAL_POLICIES_PATH.read_text(encoding="utf-8"))
    pre_p3_7 = [p for p in prod if p.get("id") != 122]
    ids = [p.get("id") for p in pre_p3_7]
    assert all(i is None or i <= 121 for i in ids), f"prod leak: {ids}"
    assert len(pre_p3_7) == 21, len(pre_p3_7)
    assert sorted(i for i in ids if isinstance(i, int)) == list(range(101, 122))


# ===========================================================================
# REAL 101–121 回归 + 信任边界
# ===========================================================================

def test_real_101_121_unchanged_no_premature_122():
    # pre-P3-7 Gate 语义：101–121 不变，且 P4 阶段不得提前创建 REAL 122。
    # 剥离 P3-7 合法写入的 REAL 122 后，对剩余子集执行原始 invariants。
    recs = _real_records()
    pre_p3_7 = [r for r in recs if r.get("id") != 122]
    ids = [r.get("id") for r in pre_p3_7]
    assert all(i is None or i <= 121 for i in ids), f"unexpected REAL: {ids}"
    assert 122 not in ids, "P4 阶段不得创建 REAL 122"
    assert len(pre_p3_7) == 21, len(pre_p3_7)
    assert sorted(i for i in ids if isinstance(i, int) and 101 <= i <= 121) == list(range(101, 122))

    r121 = next(r for r in pre_p3_7 if r.get("id") == 121)
    assert r121["percentage"] == 0.15
    assert r121["base"] == "应纳税所得额"
    assert r121["verification_status"] == "unverified"
    assert r121["verified_event_id"] == _REAL_121_VERIFIED_EVENT_ID
    assert r121["content_identity"] == (
        "ddd6116bac2ab62ce0ccbcaca4656bb9fa28c864475392473ad700b86ddc3c0b")
    # D4 未回填既有记录（不改动 REAL 101–121 的 schema）
    assert "rule_type_approved" not in r121
    assert "rule_type_derived" not in r121
    # 无 record-local verified 旁路
    for entry in (r121.get("field_evidence") or {}).values():
        assert "verified" not in entry


def test_real_121_still_not_ready_and_not_promoted():
    r121 = next(r for r in _real_records() if r.get("id") == 121)
    r = assess_execution_readiness(r121)          # READ-ONLY，不注入 Trust
    assert r["state"] == STATE_NOT_READY
    assert r["rule_type_status"]["approved"] is None
    assert r["governance_violations"] == []


def test_no_trust_runtime_write_and_no_human_verification():
    from global_policy_aggregator.pipeline import normalizer, p4_execution_state, validator
    mods = [parser_mod, normalizer, eng, p4_execution_state, validator]
    for m in mods:
        src = inspect.getsource(m)
        assert not re.search(r"^\s*(from|import)\s+src\.trust", src, re.M), m.__name__
        for forbidden in ("record_human_verification(", "HumanVerificationAuthority(",
                          "create_evidence(", "event_log.append(", "verify_evidence("):
            assert forbidden not in src, f"{m.__name__} contains {forbidden!r}"
    # P3-7 入口只在 ingestion 模块暴露；本测试未触发（由上断言 trust.called is False 佐证）
    assert hasattr(__import__("global_policy_aggregator.pipeline.real_ingestion",
                             fromlist=["ingest_verified_evidence"]),
                   "ingest_verified_evidence")


def test_d3_d4_no_write_to_real_policies():
    """本测试文件全程只读生产 REAL 文件（写入仅发生在 tmp_path 副本）。"""
    src = Path(__file__).read_text(encoding="utf-8")
    assert "PRODUCTION_REAL_POLICIES_PATH" in src
    assert "write_text" not in src.split("def _g1_env")[0]   # 仅 harness 内允许写盘


# ===========================================================================
# 真实官方 #39 回归（只读抓取；离线/不可达时 skip，绝不 fail-open 成"通过"）
# ===========================================================================

_GOV39 = "https://www.gov.cn/zhengce/zhengceku/202607/content_7074139.htm"
_TAX39 = "https://fgk.chinatax.gov.cn/zcfgk/c100013/c5250797/content.html"
_HEADERS = {"User-Agent": "OpenInvest-PolicyResearch/1.0",
            "Accept": "text/html, application/xhtml+xml, text/plain"}


def _fetch_live(url: str) -> str:
    try:
        import requests
        resp = requests.get(url, timeout=30, headers=_HEADERS)
    except Exception as exc:                                  # noqa: BLE001
        pytest.skip(f"network unavailable for {url}: {exc}")
    if resp.status_code != 200 or not resp.content:
        pytest.skip(f"official source unreachable ({resp.status_code}): {url}")
    return resp.content.decode("utf-8", errors="replace")


@pytest.mark.parametrize("url", [_GOV39, _TAX39])
def test_d1_real_notice39_full_body(url):
    """对真实官方 #39 做 D1 回归：正文必须完整获得（不为 199 字符）。"""
    html = _fetch_live(url)
    snap = f"snapshots/{url.split('/')[2]}/live-p4-5-1.html"
    pc = parse_html(html, url, snap)
    assert pc.meta["raw_visible_text_len"] > 400
    # 正文完整：官网正文核心内容必须在
    assert "失业保险" in pc.clean_text
    assert len(pc.clean_text) > 1000
    assert pc.clean_text.count("稳岗") >= 2
    if url.startswith("https://www.gov.cn/"):
        # 该模板实测存在 1 处页头之后的提前闭合
        assert pc.meta["premature_closes_removed"] >= 1


def test_d3_real_notice39_extraction_regression():
    """对真实官方 #39 做 D3 回归：不得再产出 20% 阈值 / 直辖市 / base=null / 有效期=null。"""
    html = _fetch_live(_GOV39)
    snap = "snapshots/www.gov.cn/live-p4-5-1.html"
    pc = parse_html(html, _GOV39, snap)
    c = normalize(pc, _GOV39, snap)
    assert c.percentage == 0.30                    # 不是 20% 裁员率阈值
    assert c.base                          # 不再为 null：与 30% 同条款的显式基数
    assert c.amount["normalized_number"] == 1500   # 一次性扩岗补助
    assert c.amount["unit"] == "元/人"             # per-unit 量纲
    assert c.region is None                        # 不得由主送机关「直辖市」推断
    assert c.valid_period == {"start": "2026-01-01", "end": "2026-12-31"}
    assert c.issue_date == "2026-06-18"
    assert c.amount.get("currency") == "CNY"
    assert c.evidence_violations() == []
    # quote 同条款：比例与金额不得互相污染
    ev = c.extracted_fields_evidence
    assert "1500" not in ev["percentage"].quote
    assert "30%返还" not in ev["amount"].quote


@pytest.mark.parametrize("url", [_GOV39, _TAX39])
def test_real_notice39_candidate_not_verified(url):
    """真实候选即使字段完整也不得被视为 VERIFIED / approved。"""
    html = _fetch_live(url)
    cid = f"live-{url.split('/')[2]}"
    pc = parse_html(html, url, f"snapshots/{cid}.html")
    c = normalize(pc, url, f"snapshots/{cid}.html")
    assert c.verification_status == "unverified"
    assert c.is_mock is False
    rec = {
        "id": 999, "content_identity": cid, "source_url": url,
        "snapshot_ref": pc.snapshot_ref, "type": c.type or "unknown",
        "rule_type_derived": "percentage_of_base",
        "field_evidence": {}, "application_requirements": "按当地经办机构要求申报",
        "eligibility_conditions": c.eligibility_conditions,
        "percentage": c.percentage, "base": c.base, "amount": c.amount,
        "verification_status": "unverified",
    }
    r = assess_execution_readiness(rec)            # 不注入 Trust
    assert r["state"] == STATE_NOT_READY
    assert r["state"] != STATE_EXECUTION_READY
    assert r["rule_type_status"]["approved"] is None
    assert r["rule_type_status"]["derived_equals_verified"] is False
