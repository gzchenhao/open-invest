"""P4-2 First Pilot — full vertical slice (P3-2 → P3-7 → REAL 121+).

使用真实 TrustEvidenceService + 明确标识的 DEV/TEST verifier（仅测试用）。
所有写操作落在临时 dataset / 临时 snapshot；不触碰生产 real_policies.json。

覆盖 JUDGE G:
- P3-7 不再丢失 extracted_fields
- field_evidence 正确保存
- content_identity 一致
- snapshot_ref 一致
- quote 与 snapshot 一致
- 15% tax-treatment 不得错误计算成 15% monetary subsidy
- 101–120 不变化
- REAL 新记录 id >= 121
- 测试 verifier ≠ production verifier（dev 标识）
"""

import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

from global_policy_aggregator.pipeline.fetcher import compute_content_hash
from global_policy_aggregator.pipeline.real_ingestion import (
    PRODUCTION_REAL_POLICIES_PATH,
)
from global_policy_aggregator.scripts import run_p4_pilot
from global_policy_aggregator.pipeline.p4_rule_engine import (
    build_rule_from_real_record,
    calculate_benefit,
)

FIX = os.path.join(os.path.dirname(__file__), "fixtures",
                   "policy_hightech_15pct.html")
SOURCE_URL = "https://www.gov.cn/zhengce/qiye_income_tax.html"


@pytest.fixture
def pilot_env(tmp_path):
    real_copy = tmp_path / "real_policies.json"
    data = json.loads(PRODUCTION_REAL_POLICIES_PATH.read_text(encoding="utf-8"))
    # 隔离为 pre-ingestion 基线（仅 grandfather 101–120），
    # 使 P3-7 测试不再依赖已被真实 P3-7 写入的 REAL 121+。
    data = [p for p in data if 101 <= p.get("id", 0) <= 120]
    real_copy.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()
    audit = tmp_path / "audit.jsonl"
    lock = tmp_path / ".lock"
    # DEV/TEST authority config（明确标识，仅测试）
    auth = tmp_path / "dev_authorities.json"
    auth.write_text(json.dumps({
        "authorities": [
            {"verifier_id": "hr-dev-001", "role": "human_verifier",
             "active": True, "note": "DEV/TEST verifier only — NOT production"}
        ]
    }), encoding="utf-8")
    event_log = str(tmp_path / "trust_events.jsonl")
    return {
        "real_policies_path": real_copy, "snapshots_dir": snapshots_dir,
        "audit_path": audit, "lock_path": lock,
        "authority_config": str(auth), "event_log": event_log,
    }


def test_first_pilot_vertical_slice(pilot_env):
    html = open(FIX, encoding="utf-8").read()
    summary = run_p4_pilot.run(
        html, SOURCE_URL,
        snapshots_dir=pilot_env["snapshots_dir"],
        real_policies_path=pilot_env["real_policies_path"],
        authority_config=pilot_env["authority_config"],
        event_log=pilot_env["event_log"],
        pipeline_approver="pilot-reviewer-dev",
        trust_verifier_id="hr-dev-001",
        trust_verifier_role="human_verifier",
        verification_evidence=SOURCE_URL,
        audit_path=pilot_env["audit_path"],
        lock_path=pilot_env["lock_path"],
    )

    # 1) REAL 新记录 id >= 121
    assert summary["new_real_id"] == 121
    # 2) VERIFIED 已授予（dev verifier）
    assert summary["verification_status"] == "VERIFIED"
    # 3) content_identity 与 snapshot 文件哈希一致
    snap_path = pilot_env["snapshots_dir"] / summary["snapshot_ref"].split("/", 1)[1]
    snap_bytes = snap_path.read_bytes()
    assert compute_content_hash(snap_bytes) == summary["content_identity"]

    data = json.loads(pilot_env["real_policies_path"].read_text(encoding="utf-8"))
    rec = next(e for e in data if e["id"] == 121)

    # 4) P3-7 不再丢失业务字段 + field_evidence
    assert "企业所得税法" in rec["title"]
    assert rec["percentage"] == 0.15
    assert rec["base"] == "应纳税所得额"
    assert rec["type"] == "tax_break"
    fe = rec["field_evidence"]
    assert "15" in fe["percentage"]["quote"]
    assert fe["percentage"]["content_identity"] == summary["content_identity"]
    assert fe["percentage"]["source_url"] == SOURCE_URL
    # 5) quote 确实存在于 snapshot clean text
    from global_policy_aggregator.pipeline.parser import parse_html
    parsed = parse_html(snap_bytes.decode("utf-8"), SOURCE_URL,
                        summary["snapshot_ref"])
    assert fe["percentage"]["quote"] in parsed.clean_text

    # 6) 101–120 完全不变
    before = json.loads(PRODUCTION_REAL_POLICIES_PATH.read_text(encoding="utf-8"))
    before_by_id = {e["id"]: e for e in before}
    for rid_ in range(101, 121):
        assert rec.get("_not_used") or True
        assert any(e["id"] == rid_ for e in data)
        produced = next(e for e in data if e["id"] == rid_)
        assert produced == before_by_id[rid_]

    # 7) 15% tax-treatment 不得建模为现金补贴
    rule = build_rule_from_real_record(rec)
    assert rule.rule_type == "tax_treatment_rate"
    res = calculate_benefit(rule, project_inputs={"taxable_income": 1_000_000})
    assert res.calculation_status == "unable_to_calculate"
    assert res.calculated_amount is None
    assert res.policy_outcome == {"applicable_tax_rate": 0.15,
                                  "basis": "应纳税所得额"}
    # 严禁把 15% 当作现金补贴计算金额：explanation 必须明确是税率优惠
    assert "税率" in res.explanation
    assert "15%" in res.explanation

    # 8) dev verifier 明确记录（≠ production）
    with open(pilot_env["event_log"], encoding="utf-8") as f:
        log_lines = [l for l in f.read().splitlines() if l.strip()]
    assert any("hr-dev-001" in l for l in log_lines)


def test_no_authority_registry_fail_closed(pilot_env):
    """无合法 Authority Registry → 不能 VERIFIED（fail-closed）。"""
    html = open(FIX, encoding="utf-8").read()
    with pytest.raises(RuntimeError):
        run_p4_pilot.run(
            html, SOURCE_URL,
            snapshots_dir=pilot_env["snapshots_dir"],
            real_policies_path=pilot_env["real_policies_path"],
            authority_config="",  # 不提供 → 无 registry
            event_log=pilot_env["event_log"],
            pipeline_approver="x",
            trust_verifier_id="hr-dev-001",
            trust_verifier_role="human_verifier",
            verification_evidence=SOURCE_URL,
            audit_path=pilot_env["audit_path"],
            lock_path=pilot_env["lock_path"],
        )
