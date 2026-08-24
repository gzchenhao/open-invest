#!/usr/bin/env python3
"""
TASK-P0-2 数据治理脚本：对种子数据执行 Mock 显式标记 + 虚构溯源信息置 null。
原则：只标记与置 null，绝不删除任何记录（INV-000 / 第十六条）。

处理：
1. china_policy_seed_data.json（12 条）
   - 顶层追加 is_mock=true, verification_status="mock"
   - metadata.source_url（模板生成的虚构 URL）→ null，保留说明
   - metadata.confidence_score（AI 自评分）→ null
2. detailed_china_tech_policies.json（9 条）
   - 顶层追加 is_mock=true, verification_status="mock"
   - metadata.source_url（虚构 URL）→ null
   - application_process.contact_info 的 phone/email/address → null + contact_status="unverified"
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

def mark(record: dict) -> dict:
    """在记录开头位置插入 mock 标记（重建字典保持字段顺序）"""
    new = {"is_mock": True, "verification_status": "mock"}
    new.update(record)
    return new

# ---- 1. china_policy_seed_data.json ----
seed_path = BASE / "data" / "seed_data" / "china_policy_seed_data.json"
records = json.loads(seed_path.read_text(encoding="utf-8"))
for rec in records:
    meta = rec.get("metadata", {})
    if meta.get("source_url"):
        meta["source_url_note"] = (
            "original source_url was template-generated (never verified); "
            "nullified by TASK-P0-2 per DATA-INTEGRITY-001")
        meta["source_url"] = None
    if "confidence_score" in meta:
        meta["confidence_score"] = None
        meta["confidence_score_note"] = "self-assessed score had no evidence basis; nullified by TASK-P0-2"
marked = [mark(r) for r in records]
seed_path.write_text(json.dumps(marked, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[OK] {seed_path.name}: {len(marked)} records marked as mock")

# ---- 2. detailed_china_tech_policies.json ----
det_path = BASE / "data" / "seed_data" / "detailed_china_tech_policies.json"
records = json.loads(det_path.read_text(encoding="utf-8"))
for rec in records:
    meta = rec.get("metadata", {})
    if meta.get("source_url"):
        meta["source_url_note"] = (
            "original source_url was template-generated (never verified); "
            "nullified by TASK-P0-2 per DATA-INTEGRITY-001")
        meta["source_url"] = None
    ci = (rec.get("application_process") or {}).get("contact_info")
    if isinstance(ci, dict):
        for key in ("phone", "email", "address"):
            ci[key] = None
        ci["contact_status"] = "unverified"
        ci["contact_note"] = (
            "phone/email/address were fabricated demo values; nullified by TASK-P0-2. "
            "Null is safer than wrong contact info.")
marked = [mark(r) for r in records]
det_path.write_text(json.dumps(marked, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[OK] {det_path.name}: {len(marked)} records marked as mock, contacts nullified")
