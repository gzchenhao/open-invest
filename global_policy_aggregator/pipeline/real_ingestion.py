"""P3-7 Production Ingestion — Trust VERIFIED Evidence → REAL 121+ (atomic, concurrency-safe).

JUDGE 边界（P3-7 DESIGN DECISION LOCK）：
- 本模块消费 Trust 已经产生的 ``VERIFIED``；**绝不**调用 ``record_human_verification``，
  绝不授予 VERIFIED，绝不产生 Trust 层状态。Trust ownership 不变。
- 并发安全：仅调用 Trust read-only API；不 import ``src.trust``。
- **0 修改 ``src/trust/**``**：只调用既有 Trust read-only API
  （``get_evidence`` / ``check_verified_validity`` / ``get_verification_history``），
  不 import ``src.trust``。VERIFIED 的授予权完全属于 Trust + 真实 Human Verifier。
- REAL = Production Dataset Membership，与 Trust verification 正交：
  新 REAL 记录 ``verification_status`` 保持 ``"unverified"``（DD-1），VERIFIED 事实经
  独立字段 ``verified_event_id`` 追溯；新增顶层 ``content_identity`` = Pipeline snapshot SHA256（DD-3）。
- 不新增 ``PipelineState.REAL``；Pipeline/Trust/Production 三轴正交（``states.py`` 不改）。
- 既有的 101–120 不修改 / 不覆盖 / 不重编号 / 不 backfill；新 REAL 仅 ``id >= 121``（DD-2/ID rule）。

Verification Gate（全部满足，任一不可确认 → FAIL CLOSED）：
  1. Evidence exists
  2. verification_status == "VERIFIED"
  3. check_verified_validity()["is_valid"] == True  （覆盖 revoked 检测）
  4. verification event not revoked   （由 #3 覆盖，可证明）
  5. current snapshot SHA256 == metadata["policy_content_identity"]  （防 VERIFIED 后替换）
  6. source_reference / provenance 可追溯
  7. Evidence 非 MOCK
  8. duplicate checks 通过（见 _is_duplicate）
  9. new_id = max(existing_ids)+1 且 >= 121
 10. 并发锁覆盖 read→check→ID 分配→write 完整 critical section

Duplicate Rule（严格四态）：
  A. same content_identity                → duplicate → FAIL CLOSED
  B. same source_url + diff content_identity → FAIL CLOSED（需新 evidence + 新 Trust verification）
  C. diff source_url + same content_identity  → duplicate → FAIL CLOSED
  D. diff source_url + diff content_identity  → 继续 Production Gate
  （same URL 本身不等于 duplicate）

Revoke 后处理（DD-2）：已进入 REAL 后若 Trust 后续 revoke，本模块**不自动删除** REAL，
仅通过 ``record_revoked_after_ingest`` 写入独立 production audit（不修改 real_policies.json、
不动 101–120、不实现动态 REAL deletion）。revoke watcher 不在本阶段 scope。
"""

import hashlib  # noqa: F401  (kept for potential future hashing; compute_content_hash is reused)
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# 复用 P3-1 / P3-3 既有安全原语（不重复实现、不修改）：
from global_policy_aggregator.pipeline.fetcher import (
    compute_content_hash,
    DEFAULT_SNAPSHOTS_DIR,
)
from global_policy_aggregator.pipeline.validator import resolve_snapshot_path

# G1（P4-4）：复用 P4-2 既有*确定性* rule_type 判定（禁止 title 猜测）。
# 说明：仅复用纯映射逻辑以填充 execution contract 字段；本模块**不产生**任何
# verification 状态 —— execution-critical field 的 VERIFIED 事实仍只由 Trust-owned
# provenance（verified_event_id + check_verified_validity）决定。
from global_policy_aggregator.pipeline.p4_rule_engine import build_rule_from_real_record

# 固定生产数据集路径（不允许任意 output path）：
_MODULE_DIR = Path(__file__).resolve().parent
_PROD_DATA_DIR = _MODULE_DIR.parent / "data" / "real_policies"
PRODUCTION_REAL_POLICIES_PATH = _PROD_DATA_DIR / "real_policies.json"
PRODUCTION_AUDIT_PATH = _PROD_DATA_DIR / "ingestion_audit.jsonl"

REAL_MIN_ID = 121  # 101–120 为 grandfather，P3-7 仅产生 >= 121
INGESTION_SCHEMA_VERSION = "pipeline-real-ingestion-v1"
LOCK_TIMEOUT_SECONDS = 30.0


class IngestionRejected(RuntimeError):
    """FAIL-CLOSED：Production Gate 任一条件不可确认时抛出（不写生产数据）。"""


# ---------------------------------------------------------------------------
# Concurrency control — Windows-compatible file lock (DD-4)
# ---------------------------------------------------------------------------

@contextmanager
def ingestion_lock(lock_path: Any):
    """跨进程互斥锁，覆盖完整 critical section（read→check→ID→write→audit）。

    Windows 用 ``msvcrt.locking``（非 POSIX-only fcntl）；其他平台回退 ``fcntl.flock``。
    使用非阻塞加锁 + 重试 + 超时，避免死锁；释放时解锁并关闭句柄。
    """
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_path, "w", encoding="utf-8")
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    acquired = False
    try:
        while time.monotonic() < deadline:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError:
                time.sleep(0.005)
        if not acquired:
            raise IngestionRejected(
                f"could not acquire ingestion lock within {LOCK_TIMEOUT_SECONDS}s")
        yield
    finally:
        try:
            if acquired:
                if sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _recompute_snapshot_identity(snapshot_ref: Optional[str], snapshots_dir) -> Optional[str]:
    """实时重算当前 snapshot SHA256（P3-1 compute_content_hash，与 P3-6 同口径）。

    无法可靠确认（缺 ref / 解析失败 / 文件缺失 / 读取异常 / traversal）→ None → FAIL CLOSED。
    """
    if not snapshot_ref:
        return None
    try:
        p = resolve_snapshot_path(snapshot_ref, snapshots_dir)
    except ValueError:
        return None
    if not p.exists():
        return None
    try:
        raw = p.read_bytes()
    except Exception:
        return None
    return compute_content_hash(raw)


def _load_real_policies(path: Path) -> List[Dict[str, Any]]:
    """读取 REAL dataset（JSON 数组）。缺失/损坏 → 抛错（FAIL CLOSED，不写）。"""
    if not path.exists():
        raise IngestionRejected(f"real_policies file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        raise IngestionRejected(f"real_policies file unreadable: {exc}")
    if not isinstance(data, list):
        raise IngestionRejected("real_policies must be a JSON array")
    return data


def _atomic_write_json(path: Path, data: Any) -> None:
    """temp → flush → fsync → os.replace（原子替换）。

    任何异常：清理 tmp，原文件保持不变；绝不产生半写文件。
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def _append_audit(audit_path: Path, record: Dict[str, Any]) -> None:
    """独立 append-only production audit（不混入 Trust VerificationEventLog）。"""
    audit_path = Path(audit_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True)
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def _is_duplicate(existing: List[Dict[str, Any]],
                  content_identity: str,
                  source_url: str) -> Optional[str]:
    """Duplicate Rule（严格四态）。返回不匹配原因（str）或 None。

    A. same content_identity                → "duplicate:same_content_identity"
    B. same source_url + diff content_identity → "duplicate:same_source_url_changed"
    C. diff source_url + same content_identity  → "duplicate:same_content_identity"
    D. diff both                            → None（继续 Gate）
    """
    for entry in existing:
        entry_ci = entry.get("content_identity")
        entry_url = entry.get("source_url")
        if entry_ci == content_identity:
            # Case A / C：内容身份一致即视为同一政策（不论 URL）。
            return "duplicate:same_content_identity"
        if entry_url and source_url and entry_url == source_url:
            # Case B：同 URL 但内容变化（需新 evidence + 新 Trust verification）。
            return "duplicate:same_source_url_changed"
    return None  # Case D


# ---------------------------------------------------------------------------
# Core ingestion
# ---------------------------------------------------------------------------

def ingest_verified_evidence(
    evidence_id: str,
    trust_service: Any,
    real_policies_path: Optional[Any] = None,
    snapshots_dir: Optional[Any] = None,
    audit_path: Optional[Any] = None,
    lock_path: Optional[Any] = None,
    context_fields_exclude: Optional[Any] = None,
    granularity: Optional[str] = None,
) -> int:
    """Trust VERIFIED Evidence → Production Gate → REAL 121+（FAIL CLOSED）。

    Args:
        evidence_id: P3-6 注册的 EvidenceObject id（"ev_<hash[:20]>"）。
        trust_service: 注入的 Trust 服务（仅调用 read-only 方法；不调用 record_human_verification）。
        real_policies_path: 固定生产数据集路径（默认 PRODUCTION_REAL_POLICIES_PATH）。
        snapshots_dir: snapshot 根目录（默认 DEFAULT_SNAPSHOTS_DIR），用于重算快照哈希。
        audit_path: 独立 production audit 路径（默认 PRODUCTION_AUDIT_PATH）。
        lock_path: 并发锁路径（默认 real_policies_path 同目录 .ingestion.lock）。
        context_fields_exclude: 可选 field-name 集合，从 Context A 专属投影中排除
            （如 Context B「稳岗返还」的 percentage/base/cap/floor）。仅缩小写入字段，
            不绕过任何 Gate。
        granularity: 可选显式 granularity（如 Context A「per_hired_person」）。证据未抽取
            该字段时由调用方作为 Context A 投影显式写入；不臆造、不绕过 Gate。

    注意：trust_content_identity / verifier_id / verifier_role 一律从**正式 verification
    event**（check_verified_validity 返回的 latest_verified_event）自动捕获，禁止由调用方注入。

    Returns:
        int: 新分配的 REAL id（>= 121）。

    Raises:
        IngestionRejected: 任一 Gate 不可确认（不写生产数据）。
    """
    real_policies_path = Path(real_policies_path or PRODUCTION_REAL_POLICIES_PATH)
    audit_path = Path(audit_path or PRODUCTION_AUDIT_PATH)
    lock_path = Path(lock_path or (real_policies_path.parent / ".ingestion.lock"))
    snapshots_dir = snapshots_dir or DEFAULT_SNAPSHOTS_DIR

    # Gate 10：锁覆盖完整 critical section。
    with ingestion_lock(lock_path):
        # ---- Gate 1: Evidence exists ----
        ev_result = trust_service.get_evidence(evidence_id)
        if not ev_result.get("success"):
            raise IngestionRejected(
                f"evidence not found: {evidence_id} ({ev_result.get('error')})")
        edict = ev_result.get("evidence") or {}
        metadata = edict.get("metadata") or {}

        # ---- Gate 2: verification_status == VERIFIED ----
        if edict.get("verification_status") != "VERIFIED":
            raise IngestionRejected(
                f"evidence not VERIFIED (status={edict.get('verification_status')})")

        # ---- Gate 3 & 4: check_verified_validity (覆盖 revoked) ----
        validity = trust_service.check_verified_validity(evidence_id)
        if not validity.get("is_valid"):
            raise IngestionRejected(
                f"verified validity invalid: {validity.get('reasons')}")
        latest_verified = validity.get("latest_verified_event") or {}
        verified_event_id = latest_verified.get("event_id")
        if not verified_event_id:
            raise IngestionRejected("no verified event_id available")
        # Trust 层 provenance：一律从正式 verification event 捕获（禁止调用方注入）。
        trust_content_identity = latest_verified.get("content_identity")
        verifier_id = latest_verified.get("actor")
        verifier_role = latest_verified.get("actor_role")

        # ---- Gate 5: current snapshot identity recheck ----
        policy_content_identity = metadata.get("policy_content_identity")
        snapshot_ref = metadata.get("snapshot_ref")
        if not policy_content_identity or not snapshot_ref:
            raise IngestionRejected("missing policy_content_identity / snapshot_ref")
        current_hash = _recompute_snapshot_identity(snapshot_ref, snapshots_dir)
        if not current_hash:
            raise IngestionRejected(
                "cannot confirm current snapshot identity (missing/unreadable)")
        if current_hash != policy_content_identity:
            raise IngestionRejected(
                "snapshot identity mismatch: VERIFIED evidence content changed after verification")

        # ---- Gate 6: source_reference / provenance traceable ----
        if not metadata.get("provenance"):
            raise IngestionRejected("provenance missing — not traceable")
        source_url = metadata.get("source_url") or ""

        # ---- Gate 7: Evidence not MOCK ----
        is_mock = (
            edict.get("verification_status") == "MOCK"
            or bool((metadata or {}).get("is_mock", False))
        )
        if is_mock:
            raise IngestionRejected("evidence is MOCK — cannot ingest")

        # ---- Read dataset (under lock) ----
        existing = _load_real_policies(real_policies_path)

        # ---- Gate 8: duplicate checks (四态) ----
        dup_reason = _is_duplicate(existing, policy_content_identity, source_url)
        if dup_reason is not None:
            raise IngestionRejected(f"duplicate rejected: {dup_reason}")

        # ---- Gate 9: ID allocation >= 121 ----
        existing_ids = [e.get("id") for e in existing if isinstance(e.get("id"), int)]
        new_id = (max(existing_ids) + 1) if existing_ids else REAL_MIN_ID
        if new_id < REAL_MIN_ID:
            raise IngestionRejected(
                f"new REAL id {new_id} < {REAL_MIN_ID} — grandfather range protected")

        # ---- Build REAL record (DD-1/DD-3) ----
        # P3-7 P0 FIX（P4-2B）：显式映射 Candidate/EvidenceObject 中已通过 P3-3
        # validation 的业务字段 + 每字段 FieldEvidence，不再整批清空为 null/""。
        # 仅映射白名单字段；无 Evidence 的字段保持 null（不推断、不 LLM）。
        extracted_fields = (metadata.get("extracted_fields") or {}) or {}
        _BUSINESS_FIELDS = (
            "title", "region", "industry", "type", "amount", "issue_date",
            "valid_period", "description", "requirements", "eligibility",
            "percentage", "base", "cap", "floor", "unit", "currency",
            "granularity", "eligibility_conditions",
        )
        record = {
            "id": new_id,
            "is_mock": False,
            "verification_status": "unverified",  # DD-1: 保持 unverified；不等于 Trust 未 VERIFIED
            "content_identity": policy_content_identity,  # DD-3: Pipeline snapshot SHA256
            "verified_event_id": verified_event_id,       # DD-1: 独立追溯 VERIFIED 事实
            # ---- Trust 层 provenance（从正式 verification event 捕获）----
            "trust_content_identity": trust_content_identity,  # Trust Evidence content_identity (b4012feb...)
            "verifier_id": verifier_id,                   # human-reviewer-howard
            "verifier_role": verifier_role,               # human_verifier
            "source_url": source_url,
            "evidence_id": evidence_id,
            "candidate_id": metadata.get("candidate_id"),
            "title": "",          # 无 Evidence 时保持空（不臆造）
            "region": None,
            "industry": None,
            "type": None,
            "amount": None,
            "issue_date": None,
            "valid_period": None,
            "official_contact": {
                "department": None,
                "phone": None,
                "email": None,
                "address": None,
                "contact_status": "unverified",
            },
            "description": "",
            "details": "",
            "requirements": "",
            "percentage": None,
            "base": None,
            "cap": None,
            "floor": None,
            "unit": None,
            "currency": None,
            "granularity": None,          # Context A 投影显式写入（per_hired_person）；默认 null
            "eligibility_conditions": None,
            # ---- G1: execution contract 字段（最小兼容，无 Evidence 时 fail-closed）----
            "snapshot_ref": snapshot_ref,          # 顶层证据快照引用（P4-3 REQUIRED）
            "application_requirements": "",        # 申报/申请要求；无证据 → ""（不猜测）
            # ---- G1 + D4: rule_type 分离（derived ≠ approved ≠ VERIFIED）----
            # ``rule_type`` 仅为**确定性 derived** 的有效值（其来源由 rule_type_source
            # 显式标注）；ingestion **绝不**写入 approved，也绝不产生 Trust VERIFIED。
            "rule_type": None,                     # 确定性判定填充（见下）；来源见 rule_type_source
            "rule_type_derived": None,             # D4: 确定性推导结果（READ-ONLY 分析用）
            "rule_type_approved": None,            # D4: 仅人工批准 provenance 可填；ingestion 恒为 None
            "rule_type_approval": None,            # D4: 批准 provenance（须绑定 Trust verified_event_id）
            "rule_type_source": "derived",         # D4: "approved" | "derived"
        }
        # 显式字段映射（Candidate/EvidenceObject → REAL）；每字段保留 FieldEvidence。
        field_evidence: Dict[str, Any] = {}
        for fname in _BUSINESS_FIELDS:
            # Context A 专属投影：排除 Context B 字段（仅缩小写入范围，不绕过 Gate）。
            if context_fields_exclude and fname in context_fields_exclude:
                continue
            ev = extracted_fields.get(fname)
            if not isinstance(ev, dict):
                continue
            val = ev.get("value", None)
            # 仅当 Evidence 存在且值非 null 才落地；否则保留默认 null/""。
            if val is None:
                continue
            record[fname] = val
            field_evidence[fname] = {
                "value": val,
                "quote": ev.get("quote"),
                "char_span": ev.get("char_span"),
                "snapshot_ref": ev.get("snapshot_ref") or snapshot_ref,
                "method": ev.get("method"),
                "content_identity": policy_content_identity,
                "source_url": source_url,
            }
        # ---- G1: application_requirements（复用同证据的 requirements 抽取）----
        # 无明确原文 → 保持 ""（fail-closed，绝不猜测、绝不注入其他法规要求）。
        app_req = extracted_fields.get("application_requirements")
        if not isinstance(app_req, dict):
            app_req = extracted_fields.get("requirements")
        if isinstance(app_req, dict) and app_req.get("value") is not None:
            record["application_requirements"] = app_req["value"]
            field_evidence["application_requirements"] = {
                "value": app_req["value"],
                "quote": app_req.get("quote"),
                "char_span": app_req.get("char_span"),
                "snapshot_ref": app_req.get("snapshot_ref") or snapshot_ref,
                "method": app_req.get("method"),
                "content_identity": policy_content_identity,
                "source_url": source_url,
            }
        record["field_evidence"] = field_evidence  # 每非-null业务字段可溯源

        # ---- Context A 投影：显式 granularity（如 per_hired_person）----
        # 证据未抽取 granularity 时由调用方作为 Context A 投影显式写入（不臆造、不绕过 Gate）。
        if granularity is not None:
            record["granularity"] = granularity
            field_evidence["granularity"] = {
                "value": granularity,
                "quote": None,
                "char_span": None,
                "snapshot_ref": snapshot_ref,
                "method": "context_a_projection",
                "content_identity": policy_content_identity,
                "source_url": source_url,
            }
            record["field_evidence"] = field_evidence

        # ---- G1 + D4: rule_type —— ingestion 只写 **derived**，绝不写 approved ----
        # derived 是确定性推导，**不等于** human-approved，更**不等于** Trust VERIFIED。
        # ``rule_type``（有效值）与 ``rule_type_derived`` 同为 derived；``rule_type_approved``
        # 保持 None，直到由携带合法 Trust 绑定 provenance 的人工批准写入。
        _rule = build_rule_from_real_record(record)
        record["rule_type_derived"] = _rule.rule_type_derived
        record["rule_type"] = _rule.rule_type
        record["rule_type_source"] = _rule.rule_type_source
        record["rule_type_approved"] = None
        record["rule_type_approval"] = None
        # 硬约束：ingestion 不得生成 approved / VERIFIED 事实。
        if record["rule_type_source"] != "derived" or record["rule_type_approved"] is not None:
            raise IngestionRejected(
                "rule_type must stay derived at ingestion (approved is Human-Approval only)")

        # ---- Atomic write (temp → fsync → replace) ----
        updated = existing + [record]
        _atomic_write_json(real_policies_path, updated)

        # ---- Production audit (独立 append-only) ----
        _append_audit(audit_path, {
            "event_id": uuid.uuid4().hex,
            "schema_version": INGESTION_SCHEMA_VERSION,
            "real_id": new_id,
            "evidence_id": evidence_id,
            "target_evidence_id": evidence_id,
            "policy_content_identity": policy_content_identity,
            "source_url": source_url,
            "verified_event_id": verified_event_id,
            "trust_content_identity": trust_content_identity,
            "verifier_id": verifier_id,
            "verifier_role": verifier_role,
            "ingested_at": _utcnow(),
            "status": "ingested",
        })

        return new_id


# ---------------------------------------------------------------------------
# Revoke 后处理（DD-2）：不删除 REAL，仅记录独立 production audit
# ---------------------------------------------------------------------------

def record_revoked_after_ingest(
    real_id: int,
    evidence_id: str,
    trust_service: Any,
    real_policies_path: Optional[Any] = None,
    audit_path: Optional[Any] = None,
) -> bool:
    """若已进入 REAL 的 Evidence 后续被 Trust revoke：记录 ``revoked_after_ingest`` audit。

    不修改 real_policies.json、不动 101–120、不实现动态 REAL deletion。
    返回值：是否检测到 revoke 并写入 audit（False 表示仍有效，无需记录）。
    """
    real_policies_path = Path(real_policies_path or PRODUCTION_REAL_POLICIES_PATH)
    audit_path = Path(audit_path or PRODUCTION_AUDIT_PATH)

    validity = trust_service.check_verified_validity(evidence_id)
    if validity.get("is_valid"):
        return False
    reasons = validity.get("reasons") or []
    _append_audit(audit_path, {
        "event_id": uuid.uuid4().hex,
        "schema_version": INGESTION_SCHEMA_VERSION,
        "real_id": real_id,
        "evidence_id": evidence_id,
        "target_evidence_id": evidence_id,
        "ingested_at": _utcnow(),
        "status": "revoked_after_ingest",
        "reasons": reasons,
    })
    return True
