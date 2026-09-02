"""
P2-0 Experimental Record Validator — stdlib-only.

Validates the 5 record types defined in p2_0_experimental_record.schema.json.
Does NOT depend on the jsonschema library; uses pure Python checks so that
no new dependency is introduced.

SEMANTIC LOCKS enforced here:
  - Hook has NO status / claim_status / claim_token fields        (Hook ≠ Claim)
  - Policy verification_status ∈ {"MOCK", "UNVERIFIED"} ONLY      (REAL ≠ VERIFIED)
  - "VERIFIED" / "REJECTED" are NEVER valid at this layer
  - Event has NO metadata field; uses explicit named fields only
  - Participant has NO metadata field; only 3 data fields
  - response_level is non-null ONLY on PARTICIPANT_RESPONDED events
  - event_type must be one of 9 approved types (no HOOK_VIEWED, no HOOK_CLAIMED)
"""

import hashlib
import json
from typing import Any, Dict, List, Tuple

# ─── Constants ───────────────────────────────────────────────────────

RECORD_TYPES = {"POLICY", "PROJECT_INTENT", "HOOK", "PARTICIPANT", "EVENT"}

EVENT_TYPES = {
    "POLICY_SEARCHED",
    "POLICY_VIEWED",
    "PROJECT_INTENT_CREATED",
    "PROJECT_HOOK_CREATED",
    "HOOK_INTERESTED",
    "HOOK_RESPONDED",
    "HOOK_CONNECTED",
    "PARTICIPANT_CONTACTED",
    "PARTICIPANT_RESPONDED",
}

HOOK_TYPES = {"POLICY_HOOK", "PROJECT_HOOK"}

PARTICIPANT_TYPES = {"POLICY_AUTHORITY", "PARK", "PROJECT", "CAPITAL", "OTHER"}

ACTOR_TYPES = {"PROJECT", "PARTICIPANT", "EXPERIMENTER", "SYSTEM"}

OBJECT_TYPES = {"POLICY", "PROJECT_INTENT", "HOOK", "PARTICIPANT"}

RESPONSE_LEVELS = {"L0", "L1", "L2", "L3", "L4"}

# Policy: ONLY "MOCK" or "UNVERIFIED" — NEVER "VERIFIED", NEVER "REJECTED"
ALLOWED_VERIFICATION_STATUSES = {"MOCK", "UNVERIFIED"}

# ─── Forbidden fields (structural enforcement) ──────────────────────

# Hook MUST NOT have these — enforces Hook ≠ Claim and no state machine
FORBIDDEN_HOOK_FIELDS = {
    "status",            # no state machine
    "claim_status",      # Hook ≠ Claim
    "claim_token",       # Hook ≠ Claim
    "claim_owner",       # Hook ≠ Claim
    "claim_verified",    # Hook ≠ Claim
    "metadata",          # no open-ended extension
}

# Participant MUST NOT have these — prevents CRM / Participant System
FORBIDDEN_PARTICIPANT_FIELDS = {
    "metadata",
    "name",
    "phone",
    "email",
    "company",
    "crm_status",
    "score",
    "match",
}

# Policy MUST NOT have metadata
FORBIDDEN_POLICY_FIELDS = {"metadata"}

# ProjectIntent MUST NOT have metadata or auto-generated PII
FORBIDDEN_PROJECT_INTENT_FIELDS = {
    "metadata",
    "company_name",
    "phone",
    "email",
    "investor",
}

# Event MUST NOT have metadata — replaced by explicit named fields
FORBIDDEN_EVENT_FIELDS = {
    "metadata",
    "claim_status",
    "claim_token",
    "match_score",
    "investment_id",
}

# ─── Helpers ────────────────────────────────────────────────────────


# Optional fields on EVENT records where "key absent" and "key present with None"
# are semantically equivalent. compute_event_id() normalizes these so that
# omitted-vs-null does not produce different event_ids for the same event fact.
_EVENT_OPTIONAL_FIELDS_FOR_IDENTITY = {
    "actor_id",
    "actor_type",
    "object_type",
    "object_id",
    "evidence_ref",
    "response_level",
    "note",
}


def compute_event_id(event: Dict[str, Any]) -> str:
    """Deterministic event_id = sha256 of canonical JSON (sorted keys).

    The event_id field itself is excluded from the hash to avoid
    self-referential computation.

    FIX 3 — Canonical Optional-Field Normalization:
    For the 7 defined EVENT optional fields, "key absent" and "key present
    with None" are canonicalized identically (None values are dropped before
    hashing). This ensures the same event fact produces the same event_id
    regardless of whether a caller omits an optional field or explicitly
    passes null. Non-null values are preserved and still affect the hash.

    This is NOT a global None-filter — only the named optional fields above
    are normalized. Required fields (record_type, timestamp, event_type,
    source) are never None in a valid event, so they are unaffected.
    """
    fields = {}
    for k, v in event.items():
        if k == "event_id":
            continue
        # Normalize: for the defined optional fields, drop None values so
        # that omitted and explicit-null produce the same canonical payload.
        if k in _EVENT_OPTIONAL_FIELDS_FOR_IDENTITY and v is None:
            continue
        fields[k] = v
    canonical = json.dumps(fields, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and len(value) > 0


def _is_bool(value: Any) -> bool:
    """Strict bool check — rejects int 0/1, string 'true'/'false'."""
    return isinstance(value, bool)


# ─── Per-type validators ────────────────────────────────────────────


def validate_policy(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if record.get("record_type") != "POLICY":
        errors.append("record_type must be 'POLICY'")
        return False, errors

    # Required fields
    for field in ["policy_id", "title", "source_url", "is_mock", "verification_status", "created_at", "source"]:
        if field not in record:
            errors.append(f"missing required field: {field}")

    if errors:
        return False, errors

    # Type checks
    if not _is_non_empty_str(record.get("policy_id")):
        errors.append("policy_id must be a non-empty string")
    if not _is_non_empty_str(record.get("title")):
        errors.append("title must be a non-empty string")
    if not _is_non_empty_str(record.get("source_url")):
        errors.append("source_url must be a non-empty string")
    if not _is_non_empty_str(record.get("created_at")):
        errors.append("created_at must be a non-empty string")
    if not _is_non_empty_str(record.get("source")):
        errors.append("source must be a non-empty string")

    # is_mock must be strict bool
    if not _is_bool(record.get("is_mock")):
        errors.append("is_mock must be a boolean (not int/string)")
        return False, errors

    # verification_status: ONLY "MOCK" or "UNVERIFIED"
    vs = record.get("verification_status")
    if vs not in ALLOWED_VERIFICATION_STATUSES:
        errors.append(
            f"verification_status must be 'MOCK' or 'UNVERIFIED' — got '{vs}'. "
            f"'VERIFIED' and 'REJECTED' are NEVER allowed at the experimental layer."
        )

    # Cross-field consistency: is_mock ↔ verification_status
    if record["is_mock"] is True and vs != "MOCK":
        errors.append("is_mock=true requires verification_status='MOCK'")
    if record["is_mock"] is False and vs != "UNVERIFIED":
        errors.append("is_mock=false requires verification_status='UNVERIFIED'")

    # Forbidden fields
    for field in FORBIDDEN_POLICY_FIELDS:
        if field in record:
            errors.append(f"forbidden field in POLICY record: {field}")

    return (len(errors) == 0), errors


def validate_project_intent(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if record.get("record_type") != "PROJECT_INTENT":
        errors.append("record_type must be 'PROJECT_INTENT'")
        return False, errors

    # Required fields
    for field in ["project_intent_id", "policy_id", "need_description", "actor_id", "created_at", "source"]:
        if field not in record:
            errors.append(f"missing required field: {field}")

    if errors:
        return False, errors

    # Type checks (required)
    for field in ["project_intent_id", "policy_id", "need_description", "actor_id", "created_at", "source"]:
        if not _is_non_empty_str(record.get(field)):
            errors.append(f"{field} must be a non-empty string")

    # Optional fields (must be str or null)
    for field in ["project_type", "industry", "region", "contact_info"]:
        val = record.get(field)
        if val is not None and not isinstance(val, str):
            errors.append(f"{field} must be a string or null")

    # contact_info is explicitly optional — no error if missing or null
    # (Hook can exist without contact info)

    # Forbidden fields
    for field in FORBIDDEN_PROJECT_INTENT_FIELDS:
        if field in record:
            errors.append(f"forbidden field in PROJECT_INTENT record: {field}")

    return (len(errors) == 0), errors


def validate_hook(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if record.get("record_type") != "HOOK":
        errors.append("record_type must be 'HOOK'")
        return False, errors

    # Required fields
    for field in ["hook_id", "hook_type", "object_id", "created_at", "source"]:
        if field not in record:
            errors.append(f"missing required field: {field}")

    if errors:
        return False, errors

    # Type checks
    for field in ["hook_id", "object_id", "created_at", "source"]:
        if not _is_non_empty_str(record.get(field)):
            errors.append(f"{field} must be a non-empty string")

    # hook_type enum
    ht = record.get("hook_type")
    if ht not in HOOK_TYPES:
        errors.append(f"hook_type must be one of {HOOK_TYPES} — got '{ht}'")

    # FORBIDDEN fields — structural enforcement of Hook ≠ Claim and no state machine
    for field in FORBIDDEN_HOOK_FIELDS:
        if field in record:
            errors.append(
                f"forbidden field in HOOK record: {field}. "
                f"Hook has NO state machine and NO claim fields (Hook ≠ Claim)."
            )

    return (len(errors) == 0), errors


def validate_participant(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if record.get("record_type") != "PARTICIPANT":
        errors.append("record_type must be 'PARTICIPANT'")
        return False, errors

    # Required fields
    for field in ["participant_id", "participant_type", "source"]:
        if field not in record:
            errors.append(f"missing required field: {field}")

    if errors:
        return False, errors

    # Type checks
    for field in ["participant_id", "source"]:
        if not _is_non_empty_str(record.get(field)):
            errors.append(f"{field} must be a non-empty string")

    # participant_type enum
    pt = record.get("participant_type")
    if pt not in PARTICIPANT_TYPES:
        errors.append(f"participant_type must be one of {PARTICIPANT_TYPES} — got '{pt}'")

    # Forbidden fields — prevents CRM / Participant System
    for field in FORBIDDEN_PARTICIPANT_FIELDS:
        if field in record:
            errors.append(
                f"forbidden field in PARTICIPANT record: {field}. "
                f"Participant is minimal; no CRM / Participant System."
            )

    # Only allowed fields: record_type, participant_id, participant_type, source
    allowed = {"record_type", "participant_id", "participant_type", "source"}
    extra = set(record.keys()) - allowed
    if extra:
        errors.append(f"unexpected fields in PARTICIPANT record: {extra}")

    return (len(errors) == 0), errors


def validate_event(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if record.get("record_type") != "EVENT":
        errors.append("record_type must be 'EVENT'")
        return False, errors

    # Required fields
    for field in ["event_id", "timestamp", "event_type", "source"]:
        if field not in record:
            errors.append(f"missing required field: {field}")

    if errors:
        return False, errors

    # Type checks (required)
    for field in ["event_id", "timestamp", "source"]:
        if not _is_non_empty_str(record.get(field)):
            errors.append(f"{field} must be a non-empty string")

    # event_type enum (9 types only)
    et = record.get("event_type")
    if et not in EVENT_TYPES:
        errors.append(
            f"event_type must be one of the 9 approved types {sorted(EVENT_TYPES)} — got '{et}'. "
            f"HOOK_VIEWED, HOOK_CLAIMED, HOOK_VERIFIED, MATCH_CREATED, INVESTMENT_CREATED are NOT allowed."
        )

    # Optional fields type checks
    if record.get("actor_id") is not None and not _is_non_empty_str(record.get("actor_id")):
        errors.append("actor_id must be a non-empty string or null")
    if record.get("object_id") is not None and not _is_non_empty_str(record.get("object_id")):
        errors.append("object_id must be a non-empty string or null")

    # actor_type enum
    at = record.get("actor_type")
    if at is not None and at not in ACTOR_TYPES:
        errors.append(f"actor_type must be one of {ACTOR_TYPES} or null — got '{at}'")

    # object_type enum
    ot = record.get("object_type")
    if ot is not None and ot not in OBJECT_TYPES:
        errors.append(f"object_type must be one of {OBJECT_TYPES} or null — got '{ot}'")

    # response_level: L0-L4 or null
    rl = record.get("response_level")
    if rl is not None:
        if rl not in RESPONSE_LEVELS:
            errors.append(f"response_level must be one of {sorted(RESPONSE_LEVELS)} or null — got '{rl}'")
        # response_level is non-null ONLY on PARTICIPANT_RESPONDED
        if et != "PARTICIPANT_RESPONDED":
            errors.append(
                f"response_level must be null when event_type is '{et}' "
                f"(non-null only allowed on PARTICIPANT_RESPONDED)"
            )
    else:
        # response_level is null — fine for all events
        pass

    # evidence_ref: string or null
    er = record.get("evidence_ref")
    if er is not None and not isinstance(er, str):
        errors.append("evidence_ref must be a string or null")

    # note: string or null
    note = record.get("note")
    if note is not None and not isinstance(note, str):
        errors.append("note must be a string or null")

    # Forbidden fields
    for field in FORBIDDEN_EVENT_FIELDS:
        if field in record:
            errors.append(
                f"forbidden field in EVENT record: {field}. "
                f"Use explicit named fields (evidence_ref, response_level, note) instead of metadata."
            )

    # Canonical identity consistency: event_id MUST equal compute_event_id(record).
    # This prevents callers from supplying an arbitrary event_id that does not
    # match the deterministic SHA-256 of the canonical payload.
    # Skipped only when earlier errors already invalidate the record (e.g.
    # forbidden fields present would alter the canonical payload).
    if not errors:
        expected_id = compute_event_id(record)
        if record.get("event_id") != expected_id:
            errors.append(
                f"event_id does not match canonical identity. "
                f"provided='{record.get('event_id')}' expected='{expected_id}'. "
                f"event_id must be the deterministic SHA-256 of the canonical event payload."
            )

    return (len(errors) == 0), errors


# ─── Dispatch ───────────────────────────────────────────────────────


_VALIDATORS = {
    "POLICY": validate_policy,
    "PROJECT_INTENT": validate_project_intent,
    "HOOK": validate_hook,
    "PARTICIPANT": validate_participant,
    "EVENT": validate_event,
}


def validate(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate any record. Returns (is_valid, error_list).

    If record_type is missing or unknown, returns False with an error.
    """
    if not isinstance(record, dict):
        return False, ["record must be a dict"]

    rt = record.get("record_type")
    if rt not in RECORD_TYPES:
        return False, [f"unknown record_type: '{rt}'. Must be one of {sorted(RECORD_TYPES)}"]

    return _VALIDATORS[rt](record)
