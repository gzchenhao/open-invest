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
# P1-4.4 fix: verification_status is intentionally EXCLUDED.  It represents
# verification STATE, not content.  Including it created a self-invalidating
# paradox — an event recorded while UNVERIFIED would immediately become stale
# the moment the gate granted VERIFIED, making every VERIFIED invalid by
# construction.  Content identity must be stable across verification state
# transitions so that "the content that was verified" remains identifiable.
# confidence_score IS included because it is substantive assessed content:
# a changed confidence assessment is a real content change requiring re-verification.
_CONTENT_IDENTITY_FIELDS = (
    "id", "type", "source", "source_reference",
    "confidence_score",
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
        # Safety gate: "verified" requires a human authority role
        if decision.decision == "verified" and decision.actor_role not in HUMAN_AUTHORITY_ROLES:
            raise ValueError(
                f"'verified' decision requires a human authority role "
                f"(one of {sorted(HUMAN_AUTHORITY_ROLES)}), got '{decision.actor_role}'.")

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


# ---------------------------------------------------------------------------
# Human Verification Authority Registry (P1-4.5)
# ---------------------------------------------------------------------------

# Allowlisted human authority roles. Only these roles can record a "verified"
# decision.  This is an application-level authority boundary, NOT an identity
# authentication platform.  See P1-4.3/P1-4.5 design docs for rationale.
HUMAN_AUTHORITY_ROLES = frozenset({"human_verifier", "authorized_reviewer"})


@dataclass(frozen=True)
class HumanVerificationAuthority:
    """A registered human verification authority (P1-4.5, additive).

    This is an APPLICATION-LEVEL authorization record, NOT real-world identity
    authentication.  Existence in the registry means the operator has decided
    this verifier_id is allowed to perform human verification — it does NOT
    prove the caller is who they claim to be.  Real authentication (OAuth/SSO/
    login/crypto identity) is explicitly out of scope (NON-GOAL).

    Attributes:
        verifier_id: stable identifier of the verifier (must be non-empty).
        role:        must be in HUMAN_AUTHORITY_ROLES.
        active:      inactive authorities cannot grant VERIFIED.
        metadata:    optional display info (e.g. {"display_name": "..."}).
                     MUST NOT be treated as identity claims.
    """

    verifier_id: str
    role: str
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.verifier_id or not str(self.verifier_id).strip():
            raise ValueError("HumanVerificationAuthority.verifier_id must be non-empty")
        if self.role not in HUMAN_AUTHORITY_ROLES:
            raise ValueError(
                f"HumanVerificationAuthority.role '{self.role}' is not in "
                f"HUMAN_AUTHORITY_ROLES {sorted(HUMAN_AUTHORITY_ROLES)}")
        if not isinstance(self.active, bool):
            raise ValueError("HumanVerificationAuthority.active must be bool")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumanVerificationAuthority":
        # Malformed entry → fail closed (raise).  Never silently coerce.
        try:
            active_raw = data.get("active", True)
            if not isinstance(active_raw, bool):
                raise ValueError(
                    f"'active' must be a bool, got {type(active_raw).__name__}")
            return cls(
                verifier_id=data["verifier_id"],
                role=data["role"],
                active=active_raw,
                metadata=data.get("metadata", {}) or {},
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Malformed authority entry: {exc}") from exc


class HumanVerificationAuthorityRegistry:
    """Application-level registry of human verification authorities (P1-4.5).

    Establishes APPLICATION-LEVEL AUTHORIZATION, not real-world identity
    authentication.  The registry is an allowlist: only registered + active
    authorities can participate in granting VERIFIED.

    Security semantics (fail closed):
      - Empty registry → NO VERIFIED possible.
      - Unknown verifier_id → denied (never assumed human).
      - Inactive verifier_id → denied.
      - Role mismatch (registered role != event actor_role) → denied.
      - Malformed entry on load → raise (never silently skipped).

    The registry is intentionally NOT backed by a database, OAuth provider,
    or external IAM.  It is an in-memory allowlist that may be seeded at
    construction or loaded from a JSON config file (P1-4.6).  Config
    persistence solves authorization configuration durability — it does NOT
    provide identity authentication.
    """

    def __init__(self, authorities: Optional[List[HumanVerificationAuthority]] = None):
        self._by_id: Dict[str, HumanVerificationAuthority] = {}
        if authorities is not None:
            for a in authorities:
                self.register(a)

    # -- P1-4.6: config-driven loading (fail closed) -------------------

    @classmethod
    def from_config(cls, config_path: str) -> "HumanVerificationAuthorityRegistry":
        """Load a registry from a JSON config file (P1-4.6, fail closed).

        Config format (JSON):
            {
                "authorities": [
                    {
                        "verifier_id": "human-reviewer-001",
                        "role": "human_verifier",
                        "active": true,
                        "metadata": {"display_name": "Reviewer 001"}
                    },
                    ...
                ]
            }

        Fail-closed semantics — the following raise and NO registry is
        returned:
          - File not found / not readable
          - Malformed JSON
          - Missing "authorities" key or wrong type
          - Any malformed authority entry (invalid role, empty verifier_id,
            non-bool active, etc.)
          - Duplicate verifier_id within the config

        This method establishes APPLICATION-LEVEL AUTHORIZATION
        configuration durability.  It does NOT provide real-world identity
        authentication.
        """
        if not config_path or not str(config_path).strip():
            raise ValueError("config_path must be a non-empty string")
        if not os.path.isfile(config_path):
            raise FileNotFoundError(
                f"Authority registry config file not found: {config_path}")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Authority registry config is not valid JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError(
                f"Authority registry config must be a JSON object, got {type(raw).__name__}")
        authorities_data = raw.get("authorities")
        if authorities_data is None:
            raise ValueError(
                "Authority registry config missing 'authorities' key")
        if not isinstance(authorities_data, list):
            raise ValueError(
                f"'authorities' must be a list, got {type(authorities_data).__name__}")

        # Construct authorities — from_dict raises on malformed entries.
        authorities: List[HumanVerificationAuthority] = []
        for i, entry in enumerate(authorities_data):
            if not isinstance(entry, dict):
                raise ValueError(
                    f"Authority entry at index {i} is not a JSON object "
                    f"(got {type(entry).__name__}) — fail closed")
            authorities.append(HumanVerificationAuthority.from_dict(entry))

        # Construct registry — register() rejects duplicate verifier_ids.
        return cls(authorities=authorities)

    def register(self, authority: HumanVerificationAuthority) -> None:
        """Register a new authority.  Rejects duplicate verifier_id."""
        if not isinstance(authority, HumanVerificationAuthority):
            raise ValueError("authority must be a HumanVerificationAuthority")
        if authority.verifier_id in self._by_id:
            raise ValueError(
                f"verifier_id '{authority.verifier_id}' already registered — "
                "duplicate registration rejected")
        self._by_id[authority.verifier_id] = authority

    def lookup(self, verifier_id: str) -> Optional[HumanVerificationAuthority]:
        """Return the authority for verifier_id, or None if not registered."""
        return self._by_id.get(verifier_id)

    def is_registered(self, verifier_id: str) -> bool:
        """True if verifier_id exists in the registry (regardless of active)."""
        return verifier_id in self._by_id

    def is_active(self, verifier_id: str) -> bool:
        """True if verifier_id exists AND is active."""
        a = self._by_id.get(verifier_id)
        return a is not None and a.active

    def is_authorized(self, verifier_id: str, role: str) -> bool:
        """True if verifier_id is registered AND active AND role matches."""
        a = self._by_id.get(verifier_id)
        if a is None or not a.active:
            return False
        return a.role == role

    def __len__(self) -> int:
        return len(self._by_id)

    def all_authorities(self) -> List[HumanVerificationAuthority]:
        """Return all registered authorities (for audit/inspection)."""
        return list(self._by_id.values())


class HumanVerificationGate:
    """Minimal, unbypassable gate for granting VERIFIED status.

    VERIFIED can only be granted when ALL of the following are true:
      1. A human decision event exists in the durable EventLog
      2. The event's decision == "verified"
      3. The event's actor_role is in HUMAN_AUTHORITY_ROLES
      4. The event's content_identity matches the evidence's current identity
      5. The evidence is NOT MOCK (is_mock orthogonal — Rule E)
      6. The event has non-empty evidence_refs (verification evidence — Rule B)
      7. The event's evidence_id matches the target evidence
      8. (P1-4.5) An Authority Registry is configured
      9. (P1-4.5) The event's actor (verifier_id) is registered AND active
     10. (P1-4.5) The registered role matches the event's actor_role

    If ANY condition fails, VERIFIED is refused.  The gate is read-only
    with respect to the EventLog and the Registry — it never mutates either.

    P1-4.5 fail-closed: if no authority_registry is configured, VERIFIED is
    NEVER granted.  This closes the free-string verifier_id loophole.

    This gate does NOT implement:
      - user accounts / OAuth / JWT / RBAC backend
      - email verification
      - government identity verification
      - real human login
    """

    def __init__(
        self,
        event_log: VerificationEventLog,
        authority_registry: Optional[HumanVerificationAuthorityRegistry] = None,
    ):
        self.event_log = event_log
        self.authority_registry = authority_registry

    def can_grant_verified(
        self,
        evidence_id: str,
        expected_content_identity: Optional[str],
        evidence_is_mock: bool = False,
    ) -> Dict[str, Any]:
        """Check whether VERIFIED can be granted for the given evidence.

        Returns {"granted": bool, "reasons": [str], "matching_event": Optional[VerificationDecision]}.
        Never mutates the evidence, the log, or any event.
        """
        reasons: List[str] = []
        matching_event: Optional[VerificationDecision] = None

        # Rule E: MOCK is orthogonal — can never be VERIFIED
        if evidence_is_mock:
            reasons.append("Evidence is MOCK — MOCK can never become VERIFIED (Rule E)")

        # Read events from durable log
        events = self.event_log.get_events_for_evidence(evidence_id)

        if not events:
            reasons.append("No verification decision event exists in the durable log (Rule C)")
        else:
            # Find the LATEST "verified" decision by a human authority.
            # P1-4.4: must use the latest, not the first — after revocation +
            # re-verification, the oldest event has a stale content_identity
            # and would cause a spurious mismatch (Rule D).
            for evt in events:
                if evt.decision == "verified" and evt.actor_role in HUMAN_AUTHORITY_ROLES:
                    if matching_event is None or evt.timestamp >= matching_event.timestamp:
                        matching_event = evt

            if matching_event is None:
                reasons.append(
                    "No 'verified' decision from a human authority role found "
                    f"(events exist but none match: roles={[e.actor_role for e in events]}, "
                    f"decisions={[e.decision for e in events]})")

        # Rule D: content_identity must match
        if matching_event is not None:
            if matching_event.content_identity is None:
                reasons.append("Matching event has no content_identity (Rule B)")
            elif expected_content_identity is not None:
                if matching_event.content_identity != expected_content_identity:
                    reasons.append(
                        f"Content identity mismatch: event={matching_event.content_identity[:16]}... "
                        f"vs evidence={expected_content_identity[:16]}... (Rule D)")
            # Rule B: evidence_refs must be non-empty
            if not matching_event.evidence_refs:
                reasons.append("Matching event has no verification evidence references (Rule B)")
            # P1-4.4 Rule C: if a revocation event exists AFTER the latest
            # verified event, the verification has been invalidated and the
            # gate must NOT grant (defence-in-depth — prevents a stale
            # verified event from re-granting VERIFIED without a new human
            # decision).
            latest_revoked = None
            for evt in events:
                if evt.decision == "revoked":
                    if latest_revoked is None or evt.timestamp >= latest_revoked.timestamp:
                        latest_revoked = evt
            if (latest_revoked is not None and matching_event is not None
                    and latest_revoked.timestamp >= matching_event.timestamp):
                reasons.append(
                    f"VERIFIED was revoked at {latest_revoked.timestamp} — "
                    "re-verification requires a new Human Authority decision (Rule C)")

        # P1-4.5: Authority Registry binding — fail closed.
        # Without a registry, VERIFIED is NEVER granted (closes the free-string
        # verifier_id loophole).  With a registry, the event's actor (verifier_id)
        # must be registered, active, and have a matching role.
        if matching_event is not None and not evidence_is_mock:
            if self.authority_registry is None:
                reasons.append(
                    "No Authority Registry configured — VERIFIED cannot be "
                    "granted without a registered, active verifier (P1-4.5)")
            else:
                vid = matching_event.actor
                if not self.authority_registry.is_registered(vid):
                    reasons.append(
                        f"verifier_id '{vid}' is NOT registered in the Authority "
                        "Registry — unknown verifier denied (P1-4.5)")
                elif not self.authority_registry.is_active(vid):
                    reasons.append(
                        f"verifier_id '{vid}' is registered but INACTIVE — "
                        "inactive verifier cannot grant VERIFIED (P1-4.5)")
                elif not self.authority_registry.is_authorized(vid, matching_event.actor_role):
                    reasons.append(
                        f"verifier_id '{vid}' registered role does not match "
                        f"event actor_role '{matching_event.actor_role}' — "
                        "role mismatch denied (P1-4.5)")

        granted = len(reasons) == 0 and matching_event is not None and not evidence_is_mock
        return {
            "granted": granted,
            "reasons": reasons,
            "matching_event": matching_event,
        }

    def get_effective_verified_state(
        self,
        evidence_id: str,
        current_content_identity: Optional[str],
        evidence_is_mock: bool = False,
    ) -> Dict[str, Any]:
        """Determine the effective VERIFIED state after considering revocations.

        P1-4.4: VERIFIED is only valid if:
          1. A human "verified" event exists
          2. No later "revoked" event supersedes it
          3. The verified event's content_identity matches the current one
          4. The evidence is not MOCK

        Returns:
            {"is_valid": bool, "reasons": [str], "latest_verified_event": Optional[VerificationDecision],
             "latest_revocation_event": Optional[VerificationDecision]}
        """
        events = self.event_log.get_events_for_evidence(evidence_id)

        # Rule E: MOCK can never be VERIFIED
        if evidence_is_mock:
            return {
                "is_valid": False,
                "reasons": ["Evidence is MOCK — MOCK can never be VERIFIED (Rule E)"],
                "latest_verified_event": None,
                "latest_revocation_event": None,
            }

        # Find latest verified and latest revoked events
        latest_verified: Optional[VerificationDecision] = None
        latest_revoked: Optional[VerificationDecision] = None
        for evt in events:
            if evt.decision == "verified":
                if latest_verified is None or evt.timestamp >= latest_verified.timestamp:
                    latest_verified = evt
            elif evt.decision == "revoked":
                if latest_revoked is None or evt.timestamp >= latest_revoked.timestamp:
                    latest_revoked = evt

        reasons: List[str] = []

        if latest_verified is None:
            reasons.append("No 'verified' decision event found")
        else:
            # Check if revoked AFTER verified
            if latest_revoked is not None and latest_revoked.timestamp >= latest_verified.timestamp:
                reasons.append(
                    f"VERIFIED was revoked at {latest_revoked.timestamp} — "
                    "re-verification required (Rule C: never auto-reverify)")

            # Check content_identity match (Rule D)
            if latest_verified.content_identity is None:
                reasons.append("Verified event has no content_identity")
            elif current_content_identity is not None:
                if latest_verified.content_identity != current_content_identity:
                    reasons.append(
                        f"Content identity changed: verified="
                        f"{latest_verified.content_identity[:16]}... vs current="
                        f"{current_content_identity[:16]}... (Rule D)")

            # P1-4.5: Authority Registry binding for effective state.
            # A VERIFIED event from an unregistered/inactive/mismatched verifier
            # is NOT effectively valid.
            if self.authority_registry is None:
                reasons.append(
                    "No Authority Registry configured — VERIFIED cannot be "
                    "valid without a registered, active verifier (P1-4.5)")
            else:
                vid = latest_verified.actor
                if not self.authority_registry.is_registered(vid):
                    reasons.append(
                        f"verifier_id '{vid}' is NOT registered — unknown "
                        "verifier (P1-4.5)")
                elif not self.authority_registry.is_active(vid):
                    reasons.append(
                        f"verifier_id '{vid}' is INACTIVE — inactive verifier "
                        "(P1-4.5)")
                elif not self.authority_registry.is_authorized(vid, latest_verified.actor_role):
                    reasons.append(
                        f"verifier_id '{vid}' role mismatch with "
                        f"'{latest_verified.actor_role}' (P1-4.5)")

        is_valid = len(reasons) == 0 and latest_verified is not None
        return {
            "is_valid": is_valid,
            "reasons": reasons,
            "latest_verified_event": latest_verified,
            "latest_revocation_event": latest_revoked,
        }
