"""P4-3 Execution-state + orchestration tests (READ-ONLY, 仅 fixture / 不碰 REAL / 不碰 Trust).

覆盖：
A. p4_execution_state.assess_execution_readiness（REQUIRED / PARTIAL / NOT_READY）
B. evaluate_project_against_policies 编排（Match → Eligibility → Benefit）
D. PARTIAL 严格边界（仅 OPTIONAL 缺失 → PARTIAL；关键字段缺失 → NOT_READY）
E. 3 条 fixture policy（percentage_of_base / fixed_amount / tax_treatment_rate）
F. 16 项 negative / boundary 测试
G. REAL 121 regression（assess → NOT_READY，不产出 cash，real_policies.json 未变）
"""
import copy
import ast
import hashlib
import inspect
import json
import re
from pathlib import Path

import pytest

from global_policy_aggregator.pipeline import p4_execution_state as es
from global_policy_aggregator.pipeline import p4_execution_orchestrator as orch
from global_policy_aggregator.pipeline.p4_execution_state import (
    STATE_NOT_READY, STATE_PARTIAL, STATE_EXECUTION_READY,
    assess_execution_readiness,
)
from global_policy_aggregator.pipeline.p4_rule_operator import evaluate_policy
from global_policy_aggregator.pipeline.p4_rule_engine import _resolve_rule_type

_FIX = json.loads((Path(__file__).parent / "fixtures"
                   / "p4_execution_policies.json").read_text(encoding="utf-8"))
_REAL_PATH = Path(__file__).resolve().parent.parent \
    / "global_policy_aggregator" / "data" / "real_policies" / "real_policies.json"


def _real_records():
    d = json.loads(_REAL_PATH.read_text(encoding="utf-8"))
    recs = d["policies"] if isinstance(d, dict) else d
    return [r for r in recs if isinstance(r.get("id"), int) and 101 <= r["id"] <= 121]


# ===================== A. Execution-state assessor =====================

def test_fixture_pob_is_execution_ready():
    r = assess_execution_readiness(_FIX["FIX_POB_1"])
    assert r["state"] == STATE_EXECUTION_READY


def test_fixture_fa_is_execution_ready():
    r = assess_execution_readiness(_FIX["FIX_FA_1"])
    assert r["state"] == STATE_EXECUTION_READY


def test_fixture_tt_is_partial_valid_period_null():
    # tax_treatment 全部执行关键字段完整且已验证，仅 valid_period=null → PARTIAL
    r = assess_execution_readiness(_FIX["FIX_TT_1"])
    assert r["state"] == STATE_PARTIAL
    assert "valid_period" in r["missing_optional"]


# ===================== F. Negative / boundary tests =====================

def test_neg1_eligibility_conditions_null_not_ready():
    pol = dict(_FIX["FIX_POB_1"], eligibility_conditions=None)
    assert assess_execution_readiness(pol)["state"] == STATE_NOT_READY


def test_neg2_missing_percentage_not_ready():
    pol = dict(_FIX["FIX_POB_1"]); pol.pop("percentage", None)
    assert assess_execution_readiness(pol)["state"] == STATE_NOT_READY


def test_neg3_missing_amount_not_ready():
    pol = dict(_FIX["FIX_FA_1"]); pol.pop("amount", None)
    assert assess_execution_readiness(pol)["state"] == STATE_NOT_READY


def test_neg4_missing_base_not_ready():
    pol = dict(_FIX["FIX_POB_1"]); pol.pop("base", None)
    assert assess_execution_readiness(pol)["state"] == STATE_NOT_READY


def test_neg5_cap_without_mode_not_ready():
    pol = dict(_FIX["FIX_POB_1"]); pol.pop("cap_mode", None)
    assert assess_execution_readiness(pol)["state"] == STATE_NOT_READY


def test_neg6_floor_without_mode_not_ready():
    pol = dict(_FIX["FIX_POB_1"], floor=0.1)
    pol.pop("floor_mode", None)
    assert assess_execution_readiness(pol)["state"] == STATE_NOT_READY


def test_neg7_critical_field_unverified_not_ready():
    pol = copy.deepcopy(_FIX["FIX_POB_1"])  # 深拷贝，避免污染共享 fixture
    pol["field_evidence"]["percentage"]["verified"] = False
    r = assess_execution_readiness(pol)
    assert r["state"] == STATE_NOT_READY
    assert "percentage" in r["unverified_critical_fields"]


def test_neg8_incomplete_evidence_not_ready():
    pol = copy.deepcopy(_FIX["FIX_POB_1"])  # 深拷贝，避免污染共享 fixture
    pol["field_evidence"]["base"] = {"field": "base", "quote": "x"}  # 缺 trace
    r = assess_execution_readiness(pol)
    assert r["state"] == STATE_NOT_READY
    assert "base" in r["evidence_gaps"]


def test_neg9_only_optional_missing_is_partial():
    pol = dict(_FIX["FIX_POB_1"]); pol["valid_period"] = None
    r = assess_execution_readiness(pol)
    assert r["state"] == STATE_PARTIAL
    assert "valid_period" in r["missing_optional"]


def test_neg10_explicit_eligibility_conflict_fail():
    prof = {"industry": "AI", "region": "Shenzhen",
            "rd_staff_ratio": 0.05, "years_registered": 3}
    res = evaluate_policy(_FIX["FIX_POB_1"], project_profile=prof)
    assert res["eligibility"]["overall"] == "FAIL"


def test_neg11_missing_project_fact_unknown():
    prof = {"industry": "AI", "region": "Shenzhen", "years_registered": 3}
    res = evaluate_policy(_FIX["FIX_POB_1"], project_profile=prof)
    assert res["eligibility"]["overall"] == "UNKNOWN"  # rd_staff_ratio 缺失


def test_neg12_tax_treatment_never_cash():
    prof = {"industry": "AI"}
    res = evaluate_policy(_FIX["FIX_TT_1"], project_profile=prof,
                          project_inputs={"taxable_income": 1_000_000})
    b = res["benefit"]
    assert b["calculation_status"] == "unable_to_calculate"
    assert b["calculated_amount"] is None
    assert b["policy_outcome"]["applicable_tax_rate"] == 0.15
    assert "150000" not in json.dumps(b, ensure_ascii=False)


def test_neg13_no_title_heuristic():
    # 仅检查 _resolve_rule_type 的“代码”是否引用 title 作为决策输入（忽略 docstring）
    tree = ast.parse(inspect.getsource(_resolve_rule_type))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "title" not in names and "title" not in attrs
    state_src = inspect.getsource(es)
    assert '"税率" in' not in state_src  # 不得出现 title substring 税率 heuristic


def test_neg14_no_llm_decision():
    src = inspect.getsource(es) + inspect.getsource(orch)
    # 仅检测真实 LLM SDK 调用/导入，不误伤 docstring 中“不调用 LLM 决策”字样
    assert not re.search(r'(openai|anthropic|chat\.completions|'
                         r'generate_content|langchain|cohere|gemini)',
                         src, re.I)


def test_neg15_no_production_write():
    src = inspect.getsource(es) + inspect.getsource(orch)
    assert "real_policies.json" not in src
    assert "json.dump" not in src
    assert "'w'" not in src and '"w"' not in src
    assert "'a'" not in src and '"a"' not in src


def test_neg16_no_trust_write():
    # P4-3.1: es/orch 仅可通过**注入**的 trust_service 只读调用
    # check_verified_validity 绑定 Trust VERIFIED provenance；但绝不允许：
    #   - import src.trust（Trust 归属不变，本模块不拥有 Trust）
    #   - 写 Trust / 调用 record_human_verification（即 Human Verification）
    src = inspect.getsource(es) + inspect.getsource(orch)
    assert "from src.trust" not in src and "import src.trust" not in src
    assert "record_human_verification" not in src
    # 只读绑定 check_verified_validity 现被允许；仅禁止 Trust 写入 / HV 调用。


# ===================== B/E. Orchestrator end-to-end =====================

def test_orchestrator_pob_normal_benefit():
    policies = [_FIX["FIX_POB_1"]]
    profile = {"industry": "AI", "region": "Shenzhen",
               "rd_staff_ratio": 0.2, "years_registered": 3}
    res = orch.evaluate_project_against_policies(profile, policies,
                                                  project_inputs={"rd_expense": 1_000_000})
    e = res[0]
    assert e["readiness_state"] == STATE_EXECUTION_READY
    assert e["match"]["match_status"] in ("matched", "partial_match")
    assert e["eligibility"]["overall"] == "PASS"
    assert e["benefit"]["calculation_status"] == "calculated"
    assert e["benefit"]["calculated_amount"] == 300000.0
    assert e["benefit"]["assumptions"] == []


def test_orchestrator_pob_relative_cap():
    policies = [_FIX["FIX_POB_1"]]
    profile = {"industry": "AI", "region": "Shenzhen",
               "rd_staff_ratio": 0.2, "years_registered": 3}
    res = orch.evaluate_project_against_policies(profile, policies,
                                                  project_inputs={"rd_expense": 10_000_000})
    b = res[0]["benefit"]
    assert b["calculated_amount"] == 3_000_000.0  # min(3M, 50%*10M)


def test_orchestrator_fa_fixed_amount():
    policies = [_FIX["FIX_FA_1"]]
    profile = {"industry": "HighTech", "region": "Beijing",
               "annual_revenue": 2_000_000}
    res = orch.evaluate_project_against_policies(profile, policies)
    b = res[0]["benefit"]
    assert b["calculation_status"] == "calculated"
    assert b["calculated_amount"] == 50000.0


def test_orchestrator_not_ready_skips_benefit():
    pol = dict(_FIX["FIX_POB_1"], eligibility_conditions=None)
    res = orch.evaluate_project_against_policies({"industry": "AI"}, [pol])
    e = res[0]
    assert e["readiness_state"] == STATE_NOT_READY
    assert e["benefit"] is None
    assert e["eligibility"] is None


def test_orchestrator_evidence_bound_fields():
    res = orch.evaluate_project_against_policies(
        {"industry": "AI", "region": "Shenzhen",
         "rd_staff_ratio": 0.2, "years_registered": 3},
        [_FIX["FIX_POB_1"]], project_inputs={"rd_expense": 1_000_000})
    e = res[0]
    assert e["policy_id"] == "FIX-POB-1"
    assert e["content_identity"].startswith("fixpob1cid")
    assert e["snapshot_ref"].startswith("snapshots/example.gov.cn")
    assert e["source_url"].startswith("https://www.example.gov.cn")
    assert e["evidence_refs"]


# ===================== G. REAL 121 regression =====================

def test_real_121_unchanged_and_not_ready():
    before = hashlib.sha256(_REAL_PATH.read_bytes()).hexdigest()
    recs = _real_records()
    r121 = next(r for r in recs if r["id"] == 121)
    assert r121["verification_status"] == "unverified"
    assert r121["percentage"] == 0.15
    assert r121["base"] == "应纳税所得额"
    assert "source_organization" not in r121
    # REAL 121 缺 verified provenance / eligibility_conditions → NOT_READY，不执行 Benefit
    r = assess_execution_readiness(r121)
    assert r["state"] == STATE_NOT_READY
    after = hashlib.sha256(_REAL_PATH.read_bytes()).hexdigest()
    assert before == after  # 只读


def test_real_121_no_cash_via_operator():
    r121 = next(r for r in _real_records() if r["id"] == 121)
    res = evaluate_policy(r121, project_inputs={"taxable_income": 1_000_000})
    assert res["benefit"]["calculated_amount"] is None
    assert res["benefit"]["policy_outcome"]["applicable_tax_rate"] == 0.15
