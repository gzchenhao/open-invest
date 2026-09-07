"""P2-0 Minimal Evidence Layer v1 — append-only observation store.

观察层（Evidence Layer），不是信任层（Trust Layer）：
- 只记录事实：POLICY_SEARCHED / POLICY_VIEWED / NEED_SUBMITTED / E3_INBOUND_RECORDED
- 每条记录 observation_status 初始为 UNVERIFIED_OBSERVATION（人工 CLI 可记 CANDIDATE）
- 永不生成 VERIFIED；任何记录禁止携带 verification_status 字段
- append-only：原始记录只增不改；状态迁移通过独立 TRANSITION 记录表达
- 不 import src/trust/**，不读写任何 policy 的 verification_status

写入失败策略（JUDGE 裁决 2026-09-06）：Evidence 是观察层而非信任层，portal 调用方
采用 fail-open —— 写入失败时门户继续服务，仅向 stderr 记 warning，不伪造 evidence，
不返回假 record_id。
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "evidence-v1"

STATUS_UNVERIFIED_OBSERVATION = "UNVERIFIED_OBSERVATION"
STATUS_CANDIDATE = "CANDIDATE"
STATUS_ARCHIVED_INVALID_ANCHOR = "ARCHIVED_INVALID_ANCHOR"
ALLOWED_STATUSES = {
    STATUS_UNVERIFIED_OBSERVATION,
    STATUS_CANDIDATE,
    STATUS_ARCHIVED_INVALID_ANCHOR,
}

# VERIFIED 仅作为未来 Trust Layer 人工验证门的保留标签，本层无任何代码路径可达。
STATUS_RESERVED_VERIFIED = "VERIFIED"

ALLOWED_RECORD_TYPES = {"EVIDENCE_EVENT", "NEED_OBSERVATION", "E3_INBOUND", "TRANSITION"}
ALLOWED_EVENT_TYPES = {
    "POLICY_SEARCHED",
    "POLICY_VIEWED",
    "NEED_SUBMITTED",
    "E3_INBOUND_RECORDED",
}

_RECORD_TYPE_FILE_MAP = {
    "EVIDENCE_EVENT": "events.jsonl",
    "NEED_OBSERVATION": "needs.jsonl",
    "E3_INBOUND": "e3_inbound.jsonl",
    "TRANSITION": "transitions.jsonl",
}

_FORBIDDEN_KEYS = {"verification_status"}


def _assert_no_forbidden_keys(value, path="record"):
    """任何嵌套层级出现 verification_status 字段即拒绝（Trust 语义隔离，测试锁定）。"""
    if isinstance(value, dict):
        for key, sub in value.items():
            if key in _FORBIDDEN_KEYS:
                raise ValueError(f"evidence record must not contain '{key}' (Trust isolation): {path}.{key}")
            _assert_no_forbidden_keys(sub, f"{path}.{key}")
    elif isinstance(value, list):
        for i, sub in enumerate(value):
            _assert_no_forbidden_keys(sub, f"{path}[{i}]")


def make_record(
    event_type: str,
    payload: dict,
    record_type: str = "EVIDENCE_EVENT",
    anchor_policy_id=None,
    observation_status: str = STATUS_UNVERIFIED_OBSERVATION,
    source: str = "portal_minimal_evidence_v1",
    actor_hash=None,
    evidence_refs=None,
) -> dict:
    """构造一条 evidence-v1 信封记录。actor_hash v1 统一为 null（JUDGE 裁决：不做 IP/salt）。"""
    if record_type not in ALLOWED_RECORD_TYPES:
        raise ValueError(f"invalid record_type: {record_type}")
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(f"invalid event_type: {event_type}")
    if observation_status not in ALLOWED_STATUSES:
        raise ValueError(
            f"invalid observation_status: {observation_status} "
            f"(VERIFIED is reserved for the Trust Layer human gate; no code path may set it here)"
        )
    return {
        "record_id": str(uuid.uuid4()),
        "schema_version": SCHEMA_VERSION,
        "record_type": record_type,
        "event_type": event_type,
        "observation_status": observation_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "actor_hash": actor_hash,  # v1: 统一 null（JUDGE 裁决：不记 IP / 不做 daily salt）
        "payload": payload,
        "anchor_policy_id": anchor_policy_id,
        "evidence_refs": evidence_refs,
    }


class EvidenceV1Store:
    """append-only JSONL store，文件按 record_type 分文件，位于 records_dir 下。"""

    def __init__(self, records_dir):
        self.records_dir = Path(records_dir)
        self.records_dir.mkdir(parents=True, exist_ok=True)

    def _filepath(self, record_type: str) -> Path:
        if record_type not in _RECORD_TYPE_FILE_MAP:
            raise ValueError(f"Unknown record_type: {record_type}")
        return self.records_dir / _RECORD_TYPE_FILE_MAP[record_type]

    def append(self, record: dict) -> str:
        """校验信封后追加一行 JSON。失败抛异常（portal 侧负责 fail-open）。"""
        record_type = record.get("record_type")
        if record_type not in ALLOWED_RECORD_TYPES:
            raise ValueError(f"invalid record_type: {record_type}")
        if record.get("event_type") not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"invalid event_type: {record.get('event_type')}")
        if record.get("observation_status") not in ALLOWED_STATUSES:
            raise ValueError(f"invalid observation_status: {record.get('observation_status')}")
        if record.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"invalid schema_version: {record.get('schema_version')}")
        _assert_no_forbidden_keys(record)

        filepath = self._filepath(record_type)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True)
        with open(filepath, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return record["record_id"]

    def read_all(self, record_type: str):
        """只读工具（测试 / 人工核查用）。文件不存在 → 空列表。"""
        filepath = self._filepath(record_type)
        if not filepath.exists():
            return []
        records = []
        with open(filepath, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records


def default_records_dir() -> Path:
    """默认 evidence 目录：仓库内 p2_0_experimental/records/evidence_v1/。

    - 环境变量 OPENINVEST_EVIDENCE_DIR 优先（测试注入用）。
    - pytest 运行下自动重定向到系统临时目录，避免测试污染真实 observation 数据。
    """
    env_dir = os.environ.get("OPENINVEST_EVIDENCE_DIR")
    if env_dir:
        return Path(env_dir)
    if "pytest" in sys.modules:
        return Path(os.path.join(os.path.realpath(os.path.normpath(os.environ.get("TEMP", "/tmp"))), "openinvest_evidence_pytest"))
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "p2_0_experimental" / "records" / "evidence_v1"
