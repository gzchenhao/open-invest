#!/usr/bin/env python3
"""P2-0 E3 inbound signal recorder — MANUAL CLI, no web endpoint.

人工记录 E3 CANDIDATE / INBOUND SIGNAL（JUDGE 批准 2026-09-06）。

治理规则：
- org_name / contact / evidence_refs：没有真实证据一律 null（宁可 null，不要猜）
- observation_status 固定为 CANDIDATE（人工记录本身即人类判断）
- 不得把"政府提出需求"解释成 VERIFIED / traction / PMF
- 每次后续真实交互由人工追加新记录并在 evidence_refs 中引用证据
- 不恢复旧 B.6 outreach server endpoint；本 CLI 是唯一的 E3 记录通道

用法：
    python p2_0_experimental/record_e3_inbound.py \
        --description "某区政府提出一键查询 / 一键申请 / 自动审查 / 自动到账的政策服务需求" \
        --recorded-by <experimenter标识> \
        [--evidence-refs path1,path2]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from p2_0_experimental.evidence_store import (  # noqa: E402
    EvidenceV1Store,
    STATUS_CANDIDATE,
    default_records_dir,
    make_record,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Record an E3 inbound signal (manual, CANDIDATE).")
    parser.add_argument(
        "--description",
        default="某区政府提出一键查询 / 一键申请 / 自动审查 / 自动到账的政策服务需求",
        help="Inbound need description (verbatim; never fabricate org/contact details).",
    )
    parser.add_argument("--recorded-by", required=True, help="Experimenter identifier performing this manual record.")
    parser.add_argument(
        "--evidence-refs",
        default="",
        help="Comma-separated references to real interaction evidence; omit when none exists (stays null).",
    )
    parser.add_argument(
        "--records-dir",
        default=None,
        help="Override evidence records directory (default: evidence_store.default_records_dir()).",
    )
    args = parser.parse_args()

    evidence_refs = None
    if args.evidence_refs.strip():
        evidence_refs = [ref.strip() for ref in args.evidence_refs.split(",") if ref.strip()]

    record = make_record(
        event_type="E3_INBOUND_RECORDED",
        payload={
            "description": args.description,
            "participant_class": "government",
            "org_name": None,      # 没有真实证据一律 null（宁可 null，不要猜）
            "contact": None,       # 不得虚构联系人 / 邮箱 / 电话
            "recorded_by": args.recorded_by,
        },
        record_type="E3_INBOUND",
        anchor_policy_id=None,
        observation_status=STATUS_CANDIDATE,
        source="manual_cli",
        evidence_refs=evidence_refs,
    )

    store = EvidenceV1Store(args.records_dir or default_records_dir())
    record_id = store.append(record)

    print(json.dumps({
        "status": "recorded",
        "record_id": record_id,
        "observation_status": record["observation_status"],
        "note": "E3 CANDIDATE / INBOUND SIGNAL — 不是 VERIFIED / Hook / traction / PMF。升级需真实交互证据。",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
