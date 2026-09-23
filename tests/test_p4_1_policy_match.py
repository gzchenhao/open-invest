"""P4-1 Policy Match — verification tests.

覆盖 P4-0 锁死条件 + JUDGE 16 项审计点。
所有测试不修改 real_policies.json / src.trust / 101–120 / 不产生 VERIFIED。
"""
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from global_policy_aggregator.matching import (
    build_project_profile,
    match_project_to_policy,
    match_project_to_policies,
    PolicyMatcher,
    MatchResult,
    MATCH_STATUS_MATCHED,
    MATCH_STATUS_PARTIAL,
    MATCH_STATUS_INSUFFICIENT,
    MATCH_STATUS_NOT,
    REAL_POLICIES_PATH,
)
import global_policy_aggregator.matching.policy_match as pm
import global_policy_aggregator.matching.project_profile as pp

_REPO = Path(__file__).resolve().parent.parent
_REAL_PATH = REAL_POLICIES_PATH


def _src() -> str:
    return inspect.getsource(pm) + "\n" + inspect.getsource(pp)


@pytest.fixture
def policies():
    return [
        {"id": 101, "industry": "AI", "region": None, "type": None, "amount": None,
         "source_url": "https://x/101", "title": "AI policy", "description": "AI for industry",
         "details": "", "requirements": ""},
        {"id": 102, "industry": "Semiconductor", "region": "Beijing", "type": None, "amount": None,
         "source_url": "https://x/102", "title": "semi", "description": "semi"},
        {"id": 103, "industry": "AI", "region": "Shanghai", "type": None, "amount": None,
         "source_url": "https://x/103", "title": "ai sh", "description": "ai shanghai",
         "content_identity": "abc123", "snapshot_ref": "snap/103.txt"},
        # P3-7 风格记录：带 content_identity / verified_event_id / snapshot_ref
        {"id": 121, "industry": "AI", "region": "Beijing", "type": None, "amount": "最高 5000 万元",
         "source_url": "https://x/121", "title": "AI 资助", "description": "AI 企业资助",
         "content_identity": "deadbeef", "snapshot_ref": "snap/121.txt",
         "verified_event_id": "evt_1"},
    ]


# 1. Project Input -> Profile
def test_project_input_string_to_profile():
    prof = build_project_profile("我们做 AI 芯片")
    assert prof.project_description == "我们做 AI 芯片"
    assert prof.industry is None
    assert prof.region is None


def test_project_input_dict_explicit():
    prof = build_project_profile({"industry": "AI", "region": "Beijing", "funding_need": "3000"})
    assert prof.industry == "AI"
    assert prof.region == "Beijing"
    assert prof.funding_need == 3000.0
    assert prof.extracted_fields_evidence["industry"].method == "explicit_user_input"
    assert prof.extracted_fields_evidence["industry"].source_text == "AI"


def test_profile_keeps_unknown_null():
    prof = build_project_profile({"industry": "AI"})
    assert prof.region is None
    assert prof.technology_stage is None
    assert prof.use_of_funds is None


# 2. explicit industry -> successful match
def test_explicit_industry_successful_match(policies):
    prof = build_project_profile({"industry": "AI"})
    res = match_project_to_policy(prof, policies[0])
    # industry 明确匹配成功；其余维度 unknown -> partial（unknown ≠ not_matched）
    assert res.match_status in (MATCH_STATUS_MATCHED, MATCH_STATUS_PARTIAL)
    assert any(d.dimension == "industry" for d in res.matched_dimensions)


# 3. region match / mismatch
def test_region_match(policies):
    prof = build_project_profile({"industry": "AI", "region": "Shanghai"})
    res = match_project_to_policy(prof, policies[2])  # industry=AI, region=Shanghai
    assert res.match_status in (MATCH_STATUS_MATCHED, MATCH_STATUS_PARTIAL)
    assert any(d.dimension == "region" for d in res.matched_dimensions)
    assert any(d.dimension == "industry" for d in res.matched_dimensions)


def test_region_mismatch_is_partial_not_not_matched(policies):
    prof = build_project_profile({"industry": "AI", "region": "Beijing"})
    res = match_project_to_policy(prof, policies[2])  # region=Shanghai
    assert res.match_status == MATCH_STATUS_PARTIAL
    assert any(d.dimension == "region" and d.policy_value == "Shanghai"
               for d in res.unmatched_dimensions)


# 4. policy evidence binding
def test_policy_evidence_binding(policies):
    prof = build_project_profile({"industry": "AI"})
    res = match_project_to_policy(prof, policies[2])  # has content_identity + snapshot_ref
    assert res.evidence_refs
    ev = res.evidence_refs[0]
    assert ev.field == "industry"
    assert ev.source_url == "https://x/103"
    assert ev.policy_content_identity == "abc123"
    assert ev.snapshot_ref == "snap/103.txt"


# 5. missing project field -> insufficient_evidence
def test_missing_project_field_insufficient_evidence(policies):
    prof = build_project_profile({"project_description": "某硬科技项目"})
    res = match_project_to_policy(prof, policies[0])
    assert res.match_status == MATCH_STATUS_INSUFFICIENT
    assert not res.matched_dimensions


# 6. unknown != not_matched
def test_unknown_not_not_matched(policies):
    # policy 有 industry，但 profile 未提供 industry -> 该维度 unknown，不是 not_matched
    prof = build_project_profile({"region": "Beijing"})
    res = match_project_to_policy(prof, policies[0])
    assert "industry" in res.unknown_dimensions
    assert res.match_status == MATCH_STATUS_INSUFFICIENT
    assert res.match_status != MATCH_STATUS_NOT


# 7. explicit contradiction -> not_matched
def test_explicit_contradiction_not_matched(policies):
    prof = build_project_profile({"industry": "AI"})
    res = match_project_to_policy(prof, policies[1])  # industry=Semiconductor, 无其他匹配
    assert res.match_status == MATCH_STATUS_NOT
    assert any(d.dimension == "industry" for d in res.unmatched_dimensions)


# 8. score not eligibility
def test_score_not_eligibility(policies):
    prof = build_project_profile({"industry": "AI"})
    res = match_project_to_policy(prof, policies[0])
    assert isinstance(res.score, float)
    assert not hasattr(res, "eligibility")
    assert "不构成政府资格认定" in res.explanation
    # score 仅是排序/建议信号，不代表 eligible
    assert res.match_status in (MATCH_STATUS_MATCHED, MATCH_STATUS_PARTIAL,
                                MATCH_STATUS_INSUFFICIENT, MATCH_STATUS_NOT)


# 9. no-evidence match must fail closed
def test_no_evidence_match_fail_closed(policies):
    # policy industry 为 null，profile 提供 industry -> 维度 unknown，不臆造匹配
    prof = build_project_profile({"industry": "AI"})
    no_industry_policy = {"id": 999, "industry": None, "source_url": "https://x/999",
                          "title": "t", "description": "d"}
    res = match_project_to_policy(prof, no_industry_policy)
    assert res.match_status == MATCH_STATUS_INSUFFICIENT
    assert res.evidence_refs == []


# 10/11/12/13/15/16. static boundaries (no forbidden deps / no VERIFIED / no benefit / no eligibility)
def test_no_forbidden_imports():
    import re
    src = _src()
    # 仅检查 import 行（docstring 中“不使用 X”的说明文字不算依赖）
    import_re = re.compile(r'^\s*(from|import)\s+.*(policy_ai_agent|crawlers|src\.trust)', re.M)
    assert not import_re.search(src), "matching 层不得 import 禁用模块"
    # 不得调用 Trust verification 写方法
    assert "record_human_verification" not in src
    assert "check_verified_validity" not in src


def test_no_benefit_implementation():
    src = _src()
    assert "def benefit" not in src
    assert "estimated_benefits" not in src
    assert "subsidy" not in src


def test_no_eligibility_implementation():
    src = _src()
    assert "def eligibility" not in src
    assert "ELIGIBILITY" not in src


def test_no_verified_produced_in_module():
    src = _src()
    # 匹配引擎不得产生/赋值 VERIFIED
    assert "verification_status" not in src or '"VERIFIED"' not in src


# 14. 101-120 unchanged + read-only
def test_real_policies_101_120_unchanged_and_readonly():
    before = hashlib.sha256(Path(_REAL_PATH).read_bytes()).hexdigest()
    matcher = PolicyMatcher.from_real_policies()
    ids = [p["id"] for p in matcher.policies]
    assert all(i in ids for i in range(101, 121))
    prof = build_project_profile({"industry": "AI"})
    _ = matcher.match(prof)
    after = hashlib.sha256(Path(_REAL_PATH).read_bytes()).hexdigest()
    assert before == after
    # 所有 101-120 verification_status 保持 unverified
    assert all(p.get("verification_status") == "unverified" for p in matcher.policies
               if 101 <= p["id"] <= 120)


def test_match_result_has_no_verification_field():
    prof = build_project_profile({"industry": "AI"})
    res = match_project_to_policy(prof, {"id": 1, "industry": "AI", "source_url": "u"})
    assert not hasattr(res, "verification_status")


# persistence (separate from real_policies / trust)
def test_save_and_load_match_separate_layer(tmp_path):
    prof = build_project_profile({"industry": "AI"})
    res = match_project_to_policy(prof, {"id": 1, "industry": "AI", "source_url": "u"})
    out = tmp_path / "match_results.jsonl"
    pm.save_match(res, out)
    loaded = pm.load_matches(out)
    assert len(loaded) == 1
    assert loaded[0]["match_id"] == res.match_id
    assert loaded[0]["match_status"] == res.match_status


def test_match_status_enum_values():
    assert MATCH_STATUS_MATCHED == "matched"
    assert MATCH_STATUS_PARTIAL == "partial_match"
    assert MATCH_STATUS_INSUFFICIENT == "insufficient_evidence"
    assert MATCH_STATUS_NOT == "not_matched"


# real dataset end-to-end (integration, read-only)
def test_real_dataset_ai_profile_end_to_end():
    matcher = PolicyMatcher.from_real_policies()
    prof = build_project_profile({"industry": "AI", "region": "Beijing"})
    results = matcher.match(prof)
    # 结果全部为建议态，且解释含 disclaim
    assert results
    assert all("不构成政府资格认定" in r.explanation for r in results)
    # 不得出现 eligibility/VERIFIED 语义
    assert all(r.match_status in (MATCH_STATUS_MATCHED, MATCH_STATUS_PARTIAL,
                                  MATCH_STATUS_INSUFFICIENT, MATCH_STATUS_NOT)
               for r in results)


# ===================== P4-1.1 ADVERSARIAL REGRESSION TESTS =====================
# 目标：确认 topic/keyword 重叠不产生“看起来匹配但无明确政策依据”的 false positive。
# Semantic/topic similarity ≠ Policy applicability ≠ Eligibility。

# case 1: industry 相同但 description/topic 无真实对应 -> 结构化 industry 匹配合法，但不产生 topic 假匹配
def test_adv1_industry_same_no_fake_topic():
    prof = build_project_profile({"industry": "AI"})
    pol = {"id": 1, "industry": "AI", "source_url": "u",
           "title": "某产业政策", "description": "支持相关企业发展"}  # 文本不含 "AI"
    res = match_project_to_policy(prof, pol)
    assert any(d.dimension == "industry" for d in res.matched_dimensions)
    assert res.suggested_dimensions == []  # 无关键词重叠则不建议信号


# case 2/3: industry 不同 + 大量通用关键词重叠 -> 不得形成强匹配
def test_adv2_generic_keyword_overlap_not_strong():
    prof = build_project_profile({"industry": "Biotech"})
    pol = {"id": 2, "industry": None, "source_url": "u",
           "title": "创新平台", "description": "推动 innovation technology platform industry investment development"}
    res = match_project_to_policy(prof, pol)
    assert res.matched_dimensions == []          # 通用词重叠不进入强匹配
    assert res.suggested_dimensions == []        # Biotech 不在文本 -> 无弱信号
    assert res.match_status == MATCH_STATUS_INSUFFICIENT


# case 8(part): 仅 topic 关键词重叠（industry 字段为 null） -> 弱信号 partial，非 matched
def test_adv3_topic_overlap_alone_is_weak_partial():
    prof = build_project_profile({"industry": "AI"})
    pol = {"id": 3, "industry": None, "source_url": "u",
           "title": "AI 政策", "description": "支持 AI 创新发展"}
    res = match_project_to_policy(prof, pol)
    assert res.matched_dimensions == []
    assert res.suggested_dimensions  # topic 作为弱信号存在
    assert res.match_status == MATCH_STATUS_PARTIAL
    assert all(d.dimension != "topic" for d in res.matched_dimensions)


# case 4: 项目缺失政策所需关键维度 -> unknown（非 not_matched）
def test_adv4_missing_dimension_is_unknown():
    prof = build_project_profile({"industry": "AI"})
    pol = {"id": 4, "industry": "AI", "region": "Beijing", "source_url": "u"}
    res = match_project_to_policy(prof, pol)
    assert "region" in res.unknown_dimensions
    assert res.match_status in (MATCH_STATUS_MATCHED, MATCH_STATUS_PARTIAL)


# case 5: 政策对应字段为 null -> unknown
def test_adv5_policy_field_null_is_unknown():
    prof = build_project_profile({"industry": "AI"})
    pol = {"id": 5, "industry": None, "source_url": "u"}
    res = match_project_to_policy(prof, pol)
    assert "industry" in res.unknown_dimensions
    assert res.match_status == MATCH_STATUS_INSUFFICIENT


# case 6: 明确冲突 -> not_matched
def test_adv6_explicit_contradiction_not_matched():
    prof = build_project_profile({"industry": "AI"})
    pol = {"id": 6, "industry": "Semiconductor", "source_url": "u"}
    res = match_project_to_policy(prof, pol)
    assert res.match_status == MATCH_STATUS_NOT
    assert any(d.dimension == "industry" for d in res.unmatched_dimensions)


# case 7: 完全没有可引用 Policy Evidence -> insufficient_evidence
def test_adv7_no_citeable_evidence_insufficient():
    prof = build_project_profile({"project_description": "某硬科技项目"})
    pol = {"id": 7, "industry": None, "source_url": "u"}
    res = match_project_to_policy(prof, pol)
    assert res.match_status == MATCH_STATUS_INSUFFICIENT
    assert res.evidence_refs == []


# case 8: 多条 Policy 仅因通用关键词重叠获得高 score -> 结构化匹配须排名更高
def test_adv8_ranking_structured_beats_topic_only():
    prof = build_project_profile({"industry": "AI"})
    p_topic = {"id": 8, "industry": None, "source_url": "u",
               "title": "AI 支持", "description": "AI 创新"}
    p_strong = {"id": 9, "industry": "AI", "source_url": "u",
                "title": "AI 产业", "description": "AI 企业扶持"}
    res_topic = match_project_to_policy(prof, p_topic)
    res_strong = match_project_to_policy(prof, p_strong)
    assert res_topic.match_status == MATCH_STATUS_PARTIAL  # 仅弱信号
    assert res_strong.score > res_topic.score             # 结构化匹配排名更高


# case 9: industry 匹配但其他证据不足 -> partial + unknown 维度
def test_adv9_industry_match_other_evidence_insufficient():
    prof = build_project_profile({"industry": "AI"})
    pol = {"id": 10, "industry": "AI", "region": None, "type": None,
           "amount": "5000万元", "source_url": "u"}  # 政策有金额，项目未提供 -> funding unknown
    res = match_project_to_policy(prof, pol)
    assert res.match_status == MATCH_STATUS_PARTIAL
    assert "region" in res.unknown_dimensions
    assert "type" in res.unknown_dimensions
    assert "funding" in res.unknown_dimensions


# case 10 (KEY): topic 匹配但 industry 明确冲突 -> not_matched（topic 不覆盖冲突）
def test_adv10_topic_match_but_industry_conflict_not_matched():
    prof = build_project_profile({"industry": "AI"})
    pol = {"id": 11, "industry": "Semiconductor", "source_url": "u",
           "title": "半导体政策", "description": "AI 芯片相关扶持"}  # 文本含 "AI"
    res = match_project_to_policy(prof, pol)
    assert res.match_status == MATCH_STATUS_NOT
    assert any(d.dimension == "industry" for d in res.unmatched_dimensions)
    # topic 关键词命中仅作为弱信号，绝不作为强匹配
    assert all(d.dimension != "topic" for d in res.matched_dimensions)
    assert any(d.dimension == "topic" for d in res.suggested_dimensions)


# score 仅排序信号，不作为 matched 阈值
def test_adv11_score_never_used_as_matched_threshold():
    prof = build_project_profile({"industry": "AI"})
    pol = {"id": 12, "industry": None, "source_url": "u",
           "title": "AI", "description": "AI"}  # 仅 topic 弱信号，score=0
    res = match_project_to_policy(prof, pol)
    assert res.score == 0.0
    assert res.match_status != MATCH_STATUS_MATCHED


# suggested 维度必须可追溯（有 Evidence）
def test_adv12_suggested_dimension_traceable():
    prof = build_project_profile({"industry": "AI"})
    pol = {"id": 13, "industry": None, "source_url": "https://x/13",
           "title": "AI 政策", "description": "AI 扶持",
           "content_identity": "cid13", "snapshot_ref": "snap/13"}
    res = match_project_to_policy(prof, pol)
    assert res.suggested_dimensions
    ev = res.suggested_dimensions[0].evidence
    assert ev.source_url == "https://x/13"
    assert ev.policy_content_identity == "cid13"
    assert "AI" in ev.quote
