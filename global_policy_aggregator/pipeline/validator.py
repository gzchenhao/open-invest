"""P3-3 Validation v1 — Candidate 结构 / 证据链 / provenance / snapshot / 状态机合法性校验。

职责边界（JUDGE P3-3 最终决策）：
- validate() 只验证，不证明政策真实性；不修改 Candidate 业务字段。
- 输出 ValidationResult{status, errors, warnings, checked_rules,
  observed_content_hash, validated_at, snapshot_resolved}。
  status ∈ PASS | NEED_HUMAN_REVIEW | REJECTED。
- Validation 与 State Transition 严格分离：validate() 不推进 pipeline_state；
  仅提供 ``promote_to_validated()`` / ``try_transition()`` 供明确且合法的推进使用。
- 绝不产生 VERIFIED；绝不写 real_policies.json；不调用 LLM。

content_hash 闭环（DECISION 1）：
- 当提供 FetchResult 时，FetchResult.content_hash 必须与按 snapshot 内容重算的 SHA256 一致，
  否则 HARD FAIL。
- 无 FetchResult / recorded hash 时，仅记录 observed hash，不能声称 provenance 完整验证
  → NEED_HUMAN_REVIEW。
- 禁止修改 P3-2 candidate.py / Provenance。
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Optional
from urllib.parse import urlparse

# 复用 P3-1 / P3-2 已有原语（不重复实现、不修改）：
from global_policy_aggregator.pipeline.fetcher import (
    FetchResult,
    compute_content_hash,
    DEFAULT_SNAPSHOTS_DIR,
)
from global_policy_aggregator.pipeline.parser import parse_html, ParseError
from global_policy_aggregator.pipeline.source_registry import SourceRegistry
from global_policy_aggregator.pipeline.candidate import Candidate, CLASSIFICATION_FIELDS
from global_policy_aggregator.pipeline.states import (
    PipelineState,
    can_transition,
    try_transition,
    InvalidTransitionError,
)

# 明确允许的证据抽取方法集合（来自 normalizer 实际使用的 method 字符串）。
ALLOWED_METHODS = frozenset({
    "bs4_title_or_booktitle",
    "passthrough_from_fetch",
    "verbatim_slice",
    "regex_publisher_label",
    "regex_region_label",
    "regex_admin_division",
    "regex_type_label",
    "regex_issue_date",
    "regex_valid_period",
    "canonical_taxonomy.resolve",
    "regex_amount",
    "regex_requirements_label",
    "regex_eligibility_label",
})

# source_url 的证据是 passthrough（来自 P3-1 fetch，非 snapshot 正文），
# 不参与“quote 必须位于 snapshot clean text”的检查。
_PASSTHROUGH_FIELDS = frozenset({"source_url"})

STATUS_PASS = "PASS"
STATUS_REVIEW = "NEED_HUMAN_REVIEW"
STATUS_REJECTED = "REJECTED"


@dataclass
class ValidationResult:
    status: str
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    checked_rules: list = field(default_factory=list)
    observed_content_hash: Optional[str] = None
    validated_at: str = ""
    snapshot_resolved: Optional[bool] = None

    def is_pass(self) -> bool:
        return self.status == STATUS_PASS

    def to_dict(self) -> dict:
        return asdict(self)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_utc(value: Optional[str]):
    if not value:
        return None
    text = value
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def resolve_snapshot_path(snapshot_ref: str, snapshots_dir) -> Path:
    """snapshot_ref 形如 ``snapshots/<host>/<hash>.html``（相对 data/raw_policies/）。

    解析为绝对路径：snapshots_dir / <host>/<hash>.html。

    Fail-closed path-traversal 防护（BLOCKER 1）：
    - 拒绝绝对路径；
    - 拒绝任何包含 ".." 父目录段；
    - 解析后路径必须位于 snapshots root 内（root == p 或 root in p.parents），
      否则 raise ValueError（不得通过字符串拼接绕过）。
    """
    rel = snapshot_ref
    if rel.startswith("snapshots/"):
        rel = rel[len("snapshots/"):]
    if rel.startswith("/") or ".." in PurePosixPath(rel).parts:
        raise ValueError("snapshot_ref escapes snapshots root")
    p = (Path(snapshots_dir) / rel).resolve()
    root = Path(snapshots_dir).resolve()
    if root != p and root not in p.parents:
        raise ValueError("snapshot_ref escapes snapshots root")
    return p


def validate(candidate: Candidate,
             fetch_result: Optional[FetchResult] = None,
             snapshot_bytes: Optional[bytes] = None,
             snapshots_dir=None) -> ValidationResult:
    """验证 Candidate 的结构 / 证据链 / provenance / snapshot / 状态机合法性。

    纯验证：不修改 candidate 的任何业务字段（含 pipeline_state）。
    """
    errors: list = []
    warnings: list = []
    checked: list = []
    observed_hash: Optional[str] = None
    needs_review = False

    snapshots_dir = Path(snapshots_dir) if snapshots_dir is not None else DEFAULT_SNAPSHOTS_DIR

    # ── 1. required 字段 ─────────────────────────────────────────────
    checked.append("title_required")
    if not candidate.title or not candidate.title.strip():
        errors.append("HARD: title missing/empty")  # DECISION 2

    checked.append("source_url_required")
    if not candidate.source_url:
        errors.append("HARD: source_url missing/empty")
    else:
        checked.append("source_url_scheme")
        scheme = urlparse(candidate.source_url).scheme.lower()
        if scheme not in ("http", "https"):
            errors.append("HARD: source_url scheme not http(s)")
        else:
            checked.append("source_url_allowlist")
            reg = SourceRegistry.from_file()
            allowed, _reason = reg.is_url_allowed(candidate.source_url)
            if not allowed:
                errors.append("HARD: source_url not in allowlist")

    # ── 2. pipeline state 合法性 ─────────────────────────────────────
    checked.append("pipeline_state")
    cur_state = candidate.pipeline_state
    if not PipelineState.is_valid(cur_state):
        errors.append(f"HARD: illegal pipeline state '{cur_state}'")
    elif cur_state not in (PipelineState.NORMALIZED.value, PipelineState.VALIDATED.value):
        # P3-3 只验证 NORMALIZED（或已 VALIDATED 的冪等复核）；其余均为非法跳跃
        errors.append(
            f"HARD: illegal state transition from '{cur_state}' "
            f"(P3-3 validates only NORMALIZED/VALIDATED)"
        )

    # ── 3. provenance + snapshot ─────────────────────────────────────
    checked.append("provenance_present")
    prov = candidate.provenance
    raw: Optional[bytes] = None
    snapshot_ref = prov.snapshot_ref if prov is not None else None
    if prov is None:
        errors.append("HARD: provenance missing")
    else:
        if snapshot_bytes is not None:
            raw = snapshot_bytes
            # 双来源冲突检测（FINDING 3，fail-closed）：若同时提供了对应
            # snapshot_ref 的磁盘文件，则必须与 snapshot_bytes 内容一致。
            if snapshot_ref:
                file_path = None
                try:
                    file_path = resolve_snapshot_path(snapshot_ref, snapshots_dir)
                except ValueError:
                    errors.append("HARD: snapshot_ref escapes snapshots root")
                if file_path is not None and file_path.exists():
                    try:
                        file_bytes = file_path.read_bytes()
                    except Exception:
                        file_bytes = None
                    if file_bytes is not None and file_bytes != snapshot_bytes:
                        errors.append("HARD: snapshot source conflict")
        elif not snapshot_ref:
            errors.append("HARD: snapshot_ref missing")
        else:
            path = None
            try:
                path = resolve_snapshot_path(snapshot_ref, snapshots_dir)
            except ValueError:
                errors.append("HARD: snapshot_ref escapes snapshots root")
            if path is not None:
                if path.exists():
                    try:
                        raw = path.read_bytes()
                    except Exception:
                        errors.append("HARD: snapshot unreadable")
                else:
                    errors.append("HARD: snapshot file missing")

    clean: Optional[str] = None
    if raw is not None:
        try:
            parsed = parse_html(
                raw.decode("utf-8", "replace"), candidate.source_url, snapshot_ref
            )
            clean = parsed.clean_text
            if parsed.structure_changed:
                warnings.append("structure_changed=true; manual review recommended")
                needs_review = True
            observed_hash = compute_content_hash(raw)
            if fetch_result is not None:
                checked.append("content_hash_match")
                if fetch_result.content_hash != observed_hash:
                    errors.append(
                        "HARD: content_hash mismatch "
                        f"(fetch={fetch_result.content_hash} observed={observed_hash})"
                    )
            else:
                checked.append("content_hash_no_record")
                warnings.append("no recorded content_hash; provenance not fully closed")
                needs_review = True
        except ParseError:
            errors.append("HARD: snapshot unreadable/empty (parse failed)")

    # ── 4. evidence 字段级校验 ───────────────────────────────────────
    checked.append("evidence_fields")
    for fname, ev in candidate.extracted_fields_evidence.items():
        if ev is None or ev.value is None:
            continue
        is_classification = fname in CLASSIFICATION_FIELDS
        if is_classification and ev.value == "unknown":
            # industry/type = unknown 是合法判定，豁免 quote 要求（DECISION 3）
            pass
        else:
            if not ev.quote:
                errors.append(f"HARD: field '{fname}' has value but no quote")
        if ev.snapshot_ref is not None and prov is not None \
                and ev.snapshot_ref != prov.snapshot_ref:
            errors.append(f"HARD: field '{fname}' snapshot_ref mismatch")
        if ev.method is not None and ev.method not in ALLOWED_METHODS:
            errors.append(f"HARD: field '{fname}' method '{ev.method}' not allowed")
        if ev.extracted_at is not None and _parse_utc(ev.extracted_at) is None:
            errors.append(f"HARD: field '{fname}' extracted_at invalid")
        if fname not in _PASSTHROUGH_FIELDS and clean is not None and ev.quote:
            if ev.quote not in clean:
                errors.append(
                    f"HARD: field '{fname}' quote not found in snapshot clean text"
                )
            if ev.char_span is not None:
                s, e = ev.char_span
                if not (0 <= s <= e <= len(clean)) or clean[s:e] != ev.quote:
                    errors.append(f"HARD: field '{fname}' char_span mismatch")

    # ── 5. 治理字段 ───────────────────────────────────────────────────
    checked.append("contact_null")
    if candidate.contact is not None:
        errors.append("HARD: contact must be null (P3-2 extraction deferred)")

    checked.append("verification_status")
    if candidate.verification_status != "unverified":
        errors.append("HARD: verification_status must be 'unverified' (never VERIFIED)")

    checked.append("is_mock")
    if candidate.is_mock is not False:
        errors.append("HARD: is_mock must be False")

    # ── 6. 结论 ───────────────────────────────────────────────────────
    if errors:
        status = STATUS_REJECTED
    elif needs_review:
        status = STATUS_REVIEW
    else:
        status = STATUS_PASS

    return ValidationResult(
        status=status,
        errors=errors,
        warnings=warnings,
        checked_rules=checked,
        observed_content_hash=observed_hash,
        validated_at=_utcnow(),
        snapshot_resolved=(raw is not None),
    )


def promote_to_validated(candidate: Candidate, result: ValidationResult) -> Candidate:
    """P3-3 唯一允许的推进：NORMALIZED → VALIDATED（fail-closed）。

    必须先通过 validate() 且 result.status == PASS，否则拒绝
    （REJECTED / NEED_HUMAN_REVIEW / None 一律 raise，禁止绕过 validation）。
    仅修改 pipeline_state 并 append-only history；不修改业务字段、不产生 VERIFIED。
    """
    if result is None or result.status != STATUS_PASS:
        raise InvalidTransitionError("cannot promote without PASS validation")
    return try_transition(candidate, PipelineState.VALIDATED.value)
