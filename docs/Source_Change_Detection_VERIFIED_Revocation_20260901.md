# P1-4.4 — Source Change Detection & VERIFIED Revocation

**Date:** 2026-09-01
**Quest:** P1-4.4
**Baseline:** P1-4.3 complete (commit `bf033be`, 494 tests passed)
**Status:** COMPLETE

***

## AUDIT

### Current Content Identity Reality

`compute_content_identity()` (in `verification_event_log.py`) computes a
SHA-256 hash over a FIXED set of EvidenceObject fields:

```python
_CONTENT_IDENTITY_FIELDS = (
    "id", "type", "source", "source_reference",
    "confidence_score",
)
```

**P1-4.4 fix:** `verification_status` was REMOVED from this field list.
It represents verification STATE, not content. Including it created a
self-invalidation paradox — an event recorded while the evidence was
`UNVERIFIED` would immediately become stale the moment the gate granted
`VERIFIED`, making every `VERIFIED` invalid by construction. Content
identity must be stable across verification state transitions.

`confidence_score` IS included because it is substantive assessed content:
a changed confidence assessment is a real content change requiring
re-verification.

The hash is deterministic (sort\_keys=True, ensure\_ascii=False) and
key-ordering-independent.

### VERIFIED Event Storage

`VERIFIED` events are stored as `VerificationDecision` records in the
append-only JSONL `VerificationEventLog`. Each event captures:

- `event_id` — unique UUID4 hex

- `evidence_id` — reference to the EvidenceObject

- `decision` — `"verified"` / `"revoked"` / `"candidate"` / `"rejected"`

- `actor` — identifier of the decision-maker

- `actor_role` — `"human_verifier"` / `"authorized_reviewer"` / `"system"` / `"agent"`

- `method` — how the decision was made

- `timestamp` — ISO-8601 UTC

- `content_identity` — SHA-256 of canonical content at decision time

- `evidence_refs` — supporting evidence references

- `notes` — free-text rationale (revocation events store JSON with previous/current identity + reason)

### How Current Content Identity Is Obtained

`compute_content_identity(evidence_data)` accepts the evidence dict
(e.g., from `EvidenceObject.to_dict()`) and returns the SHA-256 hash.

### VERIFIED Granting Path

The ONLY path to `VERIFIED` is `TrustEvidenceService.record_human_verification()`:

1. Computes current content\_identity
2. Appends a `"verified"` VerificationDecision event
3. Calls `HumanVerificationGate.can_grant_verified()` — checks ALL conditions
4. If gate grants → mutates evidence graph node `verification_status = "VERIFIED"`

### Pre-P1-4.4 Gaps (Resolved)

| Gap                                        | Resolution                                              |
| ------------------------------------------ | ------------------------------------------------------- |
| No change detection mechanism              | `detect_content_change()` + `check_verified_validity()` |
| No revocation event type                   | `decision="revoked"` added (additive, no enum break)    |
| No automatic revocation                    | `revoke_verified()` with system actor                   |
| No effective-state query                   | `get_effective_verified_state()` on gate                |
| Gate used first (oldest) verified event    | Fixed: gate now uses LATEST verified event              |
| Gate did not check revocation              | Fixed: gate now checks for later revocation events      |
| `verification_status` in content\_identity | Fixed: removed (self-invalidation paradox)              |

***

## DESIGN

### Change Detection Model

```
Verified Content Identity (from latest "verified" event)
        ↓
Current Content Identity (from current evidence)
        ↓
Compare
        ↓
MATCH ───────────────→ VERIFIED remains valid
MISMATCH ────────────→ append REVOCATION event
                        ↓
                        VERIFIED invalidated → UNVERIFIED
                        ↓
                        Human re-verification required
```

### Revocation Event Contract

Revocation reuses the existing `VerificationDecision` dataclass with
`decision="revoked"`. No new event type or enum was needed — this is
additive and non-breaking.

| Field              | Value for revocation                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------ |
| `event_id`         | UUID4 hex                                                                                  |
| `evidence_id`      | target evidence                                                                            |
| `decision`         | `"revoked"`                                                                                |
| `actor`            | `"system_content_change_detector"`                                                         |
| `actor_role`       | `"system"`                                                                                 |
| `method`           | `"automatic_content_change_detection"`                                                     |
| `timestamp`        | ISO-8601 UTC                                                                               |
| `content_identity` | current (new) content identity                                                             |
| `evidence_refs`    | `[]` (empty — revocation needs no evidence)                                                |
| `notes`            | JSON: `{"previous_content_identity": ..., "current_content_identity": ..., "reason": ...}` |

**Security boundary:** The system actor `system_content_change_detector`
can ONLY revoke (append `"revoked"` events). It can NEVER grant
`VERIFIED`. The `VerificationEventLog.append()` safety gate enforces:
`decision="verified"` requires `actor_role in HUMAN_AUTHORITY_ROLES`.

### VERIFIED Validity Model

`VERIFIED` is valid ONLY if ALL of the following are true:

1. Current `verification_status == "VERIFIED"`
2. A human `"verified"` event exists in the durable log
3. No later `"revoked"` event supersedes it
4. The verified event's `content_identity` matches the current content identity
5. The evidence is NOT MOCK

This is checked by `HumanVerificationGate.get_effective_verified_state()`
and exposed via `TrustEvidenceService.check_verified_validity()`.

### Append-Only History

Revocation is an append-only event. The old `"verified"` event is NEVER
deleted. The log maintains the complete audit trail:

- WHO verified WHAT content and WHEN

- WHO revoked it and WHY

- The content identities before and after the change

***

## IMPLEMENTED

### Files Modified

1. **`src/trust/verification_event_log.py`**

   - Removed `verification_status` from `_CONTENT_IDENTITY_FIELDS` (bug fix)

   - `HumanVerificationGate.can_grant_verified()` — now finds LATEST verified event (not first) and checks for later revocation events (defence-in-depth)

   - Added `HumanVerificationGate.get_effective_verified_state()` — determines effective VERIFIED state considering revocations

2. **`src/trust/trust_service.py`**

   - Added `detect_content_change(evidence_id)` — compares latest verified event's content\_identity against current

   - Added `revoke_verified(evidence_id, reason)` — records revocation event with system actor, sets evidence to UNVERIFIED

   - Added `check_verified_validity(evidence_id)` — queries effective VERIFIED state via gate

### Files Created

1. **`tests/test_source_change_revocation.py`** — 29 tests across 7 test classes

***

## VERIFIED

### Test Results

| Metric            | Value                           |
| ----------------- | ------------------------------- |
| Baseline (P1-4.3) | 494 passed, 0 failed, 1 warning |
| After P1-4.4      | 523 passed, 0 failed, 1 warning |
| New tests added   | 29                              |
| Regressions       | 0                               |

### Test Coverage

**Content Identity (4 tests)**

- Identical content → same identity ✓

- Changed content → different identity ✓

- Deterministic hashing ✓

- Key ordering does not change identity ✓

**VERIFIED Validity (3 tests)**

- VERIFIED + same content → remains valid ✓

- VERIFIED + changed content → detected ✓

- Old verification event cannot validate new content ✓

**Revocation (6 tests)**

- Content change creates revocation event ✓

- Revocation is append-only ✓

- Old verification event remains in history ✓

- Latest state reflects revocation ✓

- Revocation records old/new content\_identity ✓

- Revocation records timestamp/reason ✓

**Security Boundaries (6 tests)**

- Agent cannot revoke by pretending to be Human Authority ✓

- System may revoke but cannot grant VERIFIED ✓

- MOCK cannot become VERIFIED ✓

- UNVERIFIED cannot become VERIFIED through change detection ✓

- Revoked VERIFIED cannot automatically return to VERIFIED ✓

- Changed content cannot inherit old Human Verification ✓

**Human Re-verification (2 tests)**

- After revocation: new HumanVerificationDecision with new content\_identity required ✓

- Old content\_identity fails after change ✓

**Persistence (3 tests)**

- Revocation survives process restart (replay) ✓

- Replay produces deterministic state ✓

- Multiple events maintain correct chronological/auditable history ✓

**Backward Compatibility (5 tests)**

- Service without event log still works ✓

- Mock verify still works ✓

- Detect change without log is safe ✓

- Revoke without log is safe ✓

- Canonical industry unaffected ✓

***

## Security Boundary

> **Content change may automatically revoke VERIFIED, but no automated process may restore VERIFIED.**

- **Automatic revocation is allowed** — `revoke_verified()` uses `actor="system_content_change_detector"`, `actor_role="system"`. The `VerificationEventLog.append()` gate allows system actors to record `"revoked"` events.

- **Automatic re-verification is forbidden** — `VerificationEventLog.append()` rejects `decision="verified"` when `actor_role` is not in `HUMAN_AUTHORITY_ROLES`. No system, agent, or mock actor can ever produce a `"verified"` event.

- **Old verification cannot validate new content** — `get_effective_verified_state()` checks that the latest verified event's `content_identity` matches the current content identity. If they differ, VERIFIED is invalid regardless of any historical verification.

- **MOCK remains MOCK** — the gate checks `evidence_is_mock` first and returns `is_valid=False` unconditionally (Rule E).

***

## Re-verification Requirement

After revocation, re-verification requires ALL of:

1. **Human Authority** — `actor_role` in `{"human_verifier", "authorized_reviewer"}`
2. **VerificationDecision** — a new `"verified"` event appended to the log
3. **Matching content\_identity** — the new event's `content_identity` must match the current content identity
4. **Verification evidence** — non-empty `evidence_refs`

The old verification event (with the old content\_identity) CANNOT be reused — the gate selects the LATEST verified event, and the new event will have the new content\_identity.

***

## Backward Compatibility

- **EventLog remains optional** — `TrustEvidenceService()` without `event_log_path` still works for all legacy operations.

- **Safe failure without EventLog** — `detect_content_change()` returns `{"changed": False, ...}`; `revoke_verified()` returns `{"success": False, ...}`; `check_verified_validity()` returns `{"is_valid": False, ...}`.

- **No schema migration** — `VerificationDecision` dataclass is unchanged; `"revoked"` is a new string value for the existing `decision` field.

- **No enum break** — `VerificationStatus` enum (`UNVERIFIED`, `MOCK`, `VERIFIED`, `REJECTED`) is unchanged. Revocation sets status to `UNVERIFIED` (existing value).

- **No canonical taxonomy modification** — taxonomy is untouched.

- **No Trust Score refactoring** — trust score is untouched.

***

## Known Limitations

1. **EventLog still optional** — legacy callers without EventLog cannot detect changes or revoke. This is intentional (P1-4.3 deferred forcing EventLog).
2. **Human verifier identity is application-level** — `actor` is a free string, not authenticated identity. A real verifier registry/authentication is deferred.
3. **Content identity covers EvidenceObject fields only** — `id`, `type`, `source`, `source_reference`, `confidence_score`. Deep content fields (e.g., policy text body) are not yet included.
4. **No automatic change polling** — `detect_content_change()` and `revoke_verified()` are explicit calls. No scheduler or crawler triggers them.
5. **Revocation reason is free text** — structured reason taxonomy is deferred.
6. **No re-verification notification** — the system records revocation but does not notify human verifiers.

***

## Explicit NON-GOALS

- Crawler activation / real government data scraping

- Automatic re-verification (VERIFIED restoration)

- Human authentication / identity platform

- Complete verifier registry

- Database / external storage

- Third-party dependencies

- Trust Score formula refactoring

- Canonical taxonomy modification

- MCP / A2A integration (future architecture, out of scope)

- UI changes

- Large-scale schema migration

- Deep content field hashing (beyond EvidenceObject fields)

- Automatic change polling / scheduler

