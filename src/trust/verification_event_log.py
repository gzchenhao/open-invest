"""P1-4.1 Phase 1 — Durable Verification Event Log + Read-only Status Adapter

Provides the minimal, auditable infrastructure for future Real Policy
Verification WITHOUT granting VERIFIED.  This module:

1. VerificationDecision  — additive record of a verification decision
   (actor / timestamp / method / evidence reference / content identity).
2. VerificationEventLog   — append-only JSONL event log.  Write failures
   propagate (never silently swallowed).  Malformed lines are isolated
   and reported, never auto-repaired.
3. VerificationStatusAdapter — read-only normaliser for the divergent
   status vocabularies (uppercase trust island vs lowercase policy island).
   It NEVER mutates the original status and NEVER invents new values.

Governance rules enforced by design:
- Recording a decision event does NOT change any EvidenceObject status.
- An Agent decision is always recorded as actor_role="agent" and can never
  carry decision="verified".  The log refuses to persist such an event.
- VERIFIED can only appear in a decision event whose actor_role is
  "human" (the Human Verification Authority).  No human authority exists
  in the system today, so VERIFIED is effectively ungrantable.
- MOCK is orthogonal and never enters the decision stream.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Content Identity — SHA-256 of canonical evidence content
# ---------------------------------------------------------------------------

# Fields included in content identity (stable, ordered, deterministic).
_CONTENT_IDENTITY_FIELDS = (
    "id", "type", "source", "source_reference",
    "verification_status", "confidence_score",
)


def compute_content_identity(evidence_data: Optional[Dict[str, Any]]) -> Optional[str]:
    """Compute SHA-256 content identity for an evidence dict.

    The canonical content is a JSON string built from a FIXED set of fields
    with sort_keys=True, ensuring key ordering does not affect the hash.
    This is a CONTENT identity, NOT a verification proof — SHA-256 alone
    never implies VERIFIED, official, or trustworthy.

    Returns None for None input (no content → no identity).
    """
    if evidence_data is None:
        return None
    canonical = {k: evidence_data.get(k) for k in _CONTENT_IDENTITY_FIELDS}
    canonical_json = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# VerificationDecision — additive dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VerificationDecision:
    """A single verification decision record (additive, non-breaking).

    Existence of a VerificationDecision does NOT automatically change any
    EvidenceObject.verification_status.  Consumers must explicitly read the
    log and apply policy.  In P1-4.1 no consumer grants VERIFIED.

    Attributes:
        event_id        : unique identifier (uuid4 hex).
        evidence_id     : reference to the EvidenceObject / policy record.
        decision        : one of "candidate", "rejected", "verified".
        actor           : identifier of the human/agent making the decision.
        actor_role      : "human" or "agent".
        method          : how verification was performed (free text, e.g.
                          "manual_source_check", "agent_candidate_proposal").
        timestamp       : ISO-8601 UTC string.
        content_identity: sha256 of canonical policy text (or None).
        evidence_refs   : list of supporting evidence references.
        notes           : free-text rationale.
    """

    event_id: str
    evidence_id: str
    decision: str
    actor: str
    actor_role: str
    method: str
    timestamp: str
    content_identity: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationDecision":
        return cls(
            event_id=data["event_id"],
            evidence_id=data["evidence_id"],
            decision=data["decision"],
            actor=data["actor"],
            actor_role=data["actor_role"],
            method=data["method"],
            timestamp=data["timestamp"],
            content_identity=data.get("content_identity"),
            evidence_refs=data.get("evidence_refs", []),
            notes=data.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# VerificationEventLog — append-only JSONL
# ---------------------------------------------------------------------------

class VerificationEventLog:
    """Append-only JSONL verification event log.

    Design constraints:
    - Append-only: no update or delete operations exist.
    - Write failure propagates (raises OSError/IOError); never silent.
    - Malformed lines during replay are collected and reported, never
      auto-repaired or silently skipped.
    - Duplicate event_ids are rejected on append (deterministic).
    - The log NEVER grants VERIFIED by itself — it only records decisions.
    """

    def __init__(self, log_path: str):
        self.log_path = log_path
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create the log file if it does not exist (empty file = empty log)."""
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, "a", encoding="utf-8") as f:
                pass  # touch

    # -- append ----------------------------------------------------------

    def append(self, decision: VerificationDecision) -> str:
        """Append a verification decision to the log.

        Returns the event_id on success.

        Raises:
            ValueError  — if the decision violates safety rules (agent
                           attempting "verified", or duplicate event_id).
            OSError      — if the write fails (never silently swallowed).
        """
        # Safety gate: agent can never record a "verified" decision.
        if decision.actor_role == "agent" and decision.decision == "verified":
            raise ValueError(
                "Agent cannot record a 'verified' decision — "
                "only a human verification authority may do so.")
        # Safety gate: "verified" requires actor_role == "human"
        if decision.decision == "verified" and decision.actor_role != "human":
            raise ValueError(
                "'verified' decision requires actor_role='human'.")

        # Duplicate event_id check (deterministic replay).
        existing_ids = self._read_event_ids()
        if decision.event_id in existing_ids:
            raise ValueError(
                f"Duplicate event_id '{decision.event_id}' — "
                "append-only log rejects duplicates.")

        line = json.dumps(decision.to_dict(), ensure_ascii=False)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
        return decision.event_id

    # -- replay / read ---------------------------------------------------

    def replay(self) -> Tuple[List[VerificationDecision], List[Dict[str, Any]]]:
        """Replay the log.

        Returns:
            (events, malformed_lines)
            events         : list of VerificationDecision successfully parsed.
            malformed_lines: list of {"line_number": int, "raw": str, "error": str}
                             for lines that failed to parse.  Malformed lines
                             are reported, never silently skipped or repaired.
        """
        events: List[VerificationDecision] = []
        malformed: List[Dict[str, Any]] = []
        if not os.path.exists(self.log_path):
            return events, malformed
        with open(self.log_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                    events.append(VerificationDecision.from_dict(data))
                except (json.JSONDecodeError, KeyError, TypeError) as exc:
                    malformed.append({
                        "line_number": i,
                        "raw": stripped[:200],
                        "error": str(exc),
                    })
        return events, malformed

    def get_events_for_evidence(self, evidence_id: str) -> List[VerificationDecision]:
        """Return all events for a given evidence_id (chronological)."""
        events, _ = self.replay()
        return [e for e in events if e.evidence_id == evidence_id]

    def _read_event_ids(self) -> set:
        """Read existing event_ids for duplicate detection."""
        events, _ = self.replay()
        return {e.event_id for e in events}


# ---------------------------------------------------------------------------
# VerificationStatusAdapter — read-only normaliser
# ---------------------------------------------------------------------------

class VerificationStatusAdapter:
    """Read-only adapter for the divergent verification status vocabularies.

    The trust island (src/trust/) uses an uppercase enum:
        UNVERIFIED, MOCK, VERIFIED, REJECTED

    The policy island (global_policy_aggregator/) uses lowercase strings:
        verified, partially_verified, unverified, mock

    This adapter normalises both to a single canonical lowercase string
    WITHOUT modifying any existing enum or schema.  It is strictly
    read-only and introduces no new status values.

    Canonical output set: {"unverified", "mock", "verified", "rejected",
                            "partially_verified", "unknown"}

    "unknown" is returned for any unrecognised value — NEVER "other",
    NEVER "verified".  (宁可 unknown，不要 guess.)
    """

    _CANONICAL_MAP = {
        # uppercase trust island
        "UNVERIFIED": "unverified",
        "MOCK": "mock",
        "VERIFIED": "verified",
        "REJECTED": "rejected",
        # lowercase policy island
        "unverified": "unverified",
        "mock": "mock",
        "verified": "verified",
        "partially_verified": "partially_verified",
    }

    @classmethod
    def normalise(cls, raw_status: Any) -> str:
        """Normalise a raw status value to canonical lowercase.

        Returns "unknown" for None, empty, or unrecognised values.
        NEVER upgrades "unknown" to "verified" or any specific status.
        """
        if raw_status is None:
            return "unknown"
        # Handle enum types (e.g., VerificationStatus enum)
        raw_str = str(raw_status.value) if hasattr(raw_status, "value") else str(raw_status)
        raw_str = raw_str.strip()
        if not raw_str:
            return "unknown"
        return cls._CANONICAL_MAP.get(raw_str, "unknown")

    @classmethod
    def is_verified(cls, raw_status: Any) -> bool:
        """Check if a raw status normalises to 'verified'. Read-only."""
        return cls.normalise(raw_status) == "verified"

    @classmethod
    def is_mock(cls, raw_status: Any) -> bool:
        """Check if a raw status normalises to 'mock'. Read-only."""
        return cls.normalise(raw_status) == "mock"
