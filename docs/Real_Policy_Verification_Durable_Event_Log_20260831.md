# Real Policy Verification — Durable Event Log & F-04 Containment (P1-4.1)

**Date**: 2026-08-31
**Quest**: P1-4.1 Phase 1 — Durable Verification Event Log + F-04 Trust Safety Containment
**Baseline**: commit `4f71ca8`, master, LOCAL == REMOTE, 406 passed / 0 failed / 1 warning

> **This document covers IMPLEMENTED code with VERIFIED tests.** However, the VERIFIED *verification status* itself remains **NOT IMPLEMENTED** — no system path grants it. The infrastructure built here records verification decisions but cannot manufacture VERIFIED.

---

## 1. Objective

1. **Contain F-04** (P1-4.0 finding): free-text `source="government"/"official"` no longer raises trust score / source_reliability for UNVERIFIED or MOCK evidence.
2. **Build append-only Durable Verification Event Log** (JSONL, minimal, auditable).
3. **Add additive VerificationDecision** dataclass (actor / timestamp / method / evidence reference / content identity).
4. **Build read-only VerificationStatusAdapter** for divergent vocabularies.
5. **VERIFIED must remain ungrantable** by the system in this phase.

## 2. Baseline

| Item | Value |
|---|---|
| Branch | master |
| LOCAL HEAD | `4f71ca8` |
| REMOTE HEAD | `4f71ca8` |
| Worktree | CLEAN (after stashing external markdown reformat) |
| Tests before | 406 passed, 0 failed, 1 warning |

## 3. F-04 Audit & Fix (AUDIT → IMPLEMENTED → VERIFIED)

### AUDIT

Root cause (2 runtime paths):

1. `src/trust/trust_score.py:107-114` — `_calculate_source_score()` checked `source.lower() in self.source_reliability_weights` unconditionally. Any caller passing `source="government"` got 0.8 regardless of verification status.
2. `src/trust/trust_service.py:358-360` — `calculate_trust()` set `confidence_factors["source_reliability"]="high"` with reason "Source is government/official" for any `source.lower()` in `["government", "official"]`, regardless of `verification_status`.

Failing tests (written before fix) confirmed: UNVERIFIED + government → source_score=80 (should be 50); MOCK + government → 80; explanation "high".

### IMPLEMENTED fix (minimal, additive)

**`trust_score.py`** — `_calculate_source_score()` now accepts `verification_status` parameter; preset label weights apply ONLY when `verification_status.upper() == "VERIFIED"`. For UNVERIFIED/MOCK, falls back to manual weight (default 0.5 → score 50).

**`trust_service.py`** — `calculate_trust()` now checks `evidence.verification_status.value == "VERIFIED"` before reporting "high" source_reliability. For non-VERIFIED government/official labels, reports `"unverified_label"` with reason "Source labeled government/official but NOT verified (label is not verification authority)".

**`test_trust_prototype.py`** — `test_additional_trust_prototype_validations` previously called `calculate_trust_score(dict)` without passing `verification_status` parameter, relying on the label boost for the "high > low" assertion. Fixed to pass `verification_status="VERIFIED"` / `"UNVERIFIED"` explicitly. The test's intent (VERIFIED government > UNVERIFIED unknown) is preserved; the unsafe implicit boost is removed.

### VERIFIED

9 tests (TEST-F04-001..009): UNVERIFIED government → 50 (not 80); MOCK government → 50; UNVERIFIED official → 50; VERIFIED government → 80 (legitimate path preserved); case-insensitive labels contained; explanation not "high" for UNVERIFIED/MOCK; verification_status semantics unchanged; determinism.

## 4. Durable Verification Event Log (DESIGN → IMPLEMENTED → VERIFIED)

### DESIGN

- **Append-only JSONL**: one file, one event per line. No update/delete operations exist.
- **Event identity**: `event_id` (uuid4 hex) + `evidence_id` reference.
- **Safety gates** (enforced at `append()`):
  - `actor_role == "agent"` + `decision == "verified"` → **ValueError** (agent can never record verified).
  - `decision == "verified"` + `actor_role != "human"` → **ValueError** (only human authority).
  - Duplicate `event_id` → **ValueError** (deterministic replay).
- **Write failure**: `OSError` propagates (fsync + flush; never silently swallowed).
- **Malformed lines**: collected and reported in `replay()` return, never auto-repaired or silently skipped.
- **No dependencies**: stdlib only (`json`, `os`, `uuid`, `hashlib`, `dataclasses`).

### IMPLEMENTED

`src/trust/verification_event_log.py` (new, ~180 lines):
- `VerificationDecision` (frozen dataclass, additive): `event_id`, `evidence_id`, `decision`, `actor`, `actor_role`, `method`, `timestamp`, `content_identity` (Optional), `evidence_refs` (List), `notes`.
- `VerificationEventLog`: `append()`, `replay() → (events, malformed)`, `get_events_for_evidence()`.
- `VerificationStatusAdapter`: `normalise()`, `is_verified()`, `is_mock()` — read-only, never mutates input, returns "unknown" for unrecognised values (宁可 unknown，不要 guess).

### VERIFIED

19 tests (TEST-VD-001..002, TEST-EL-001..011, TEST-SA-001..006):
- Serialization roundtrip + frozen immutability.
- Append + replay; append-only (duplicate event_id rejected); agent cannot record verified; verified requires human role; human can record verified; malformed line reported; duplicate rejected; empty log; get_events_for_evidence; write failure propagates OSError; recording does NOT change EvidenceObject status.
- Adapter: uppercase/lowercase/enum normalisation; None/empty → unknown; unrecognised → unknown (never verified); read-only (input unchanged).

## 5. Backward Compatibility

- `calculate_trust_score()` signature: `verification_status` was already a parameter (default "UNVERIFIED"); the call site now passes it to `_calculate_source_score`. No API change.
- `_calculate_source_score()` gains an optional parameter with default — existing callers unaffected.
- `trust_service.py calculate_trust()`: no API change; only the confidence_factors/reason values for government/official labels change when status is not VERIFIED.
- Existing 406 tests all pass (including `test_trust_prototype.py` after call-signature fix).
- No schema/enum modification. No data change. No crawler/MCP/A2A activation.

## 6. Trust Impact

- **Verification_status semantics**: unchanged (MOCK stays MOCK, UNVERIFIED stays UNVERIFIED, VERIFIED is still ungrantable).
- **Trust Score**: for UNVERIFIED/MOCK evidence with government/official label, source_score drops from 80/70 to 50 (the default). This is the intended containment — the previous boost was an unverified label inflating the score.
- **VERIFIED path preserved**: VERIFIED government source still gets 80.
- **No new implicit trust**: the event log records decisions but does NOT feed back into Trust Score or verification_status.

## 7. Safety / Governance

- MOCK remains MOCK ✅; UNVERIFIED remains UNVERIFIED ✅; VERIFIED ungrantable ✅.
- Agent cannot record "verified" decision ✅ (enforced at append).
- No fake verifier / fake verification evidence ✅.
- No MCP/A2A false claims ✅ (still NOT IMPLEMENTED).
- No hidden fallback / silent guessing ✅ (malformed lines reported, unknown → "unknown" never "verified").
- No crawler activation ✅.
- No canonical taxonomy modification ✅.

## 8. Tests

| Phase | Count | Result |
|---|---|---|
| Before | 406 | 406 passed, 0 failed |
| New (test_verification_infrastructure.py) | 28 | 28 passed |
| After (full regression) | 434 | **434 passed, 0 failed**, 1 warning (pre-existing starlette deprecation) |

Test categories: F-04 label containment (9), VerificationDecision serialization/immutability (2), EventLog append/replay/safety gates (11), StatusAdapter normalisation (6).

## 9. Runtime Coverage

- **VERIFIED (runtime)**: F-04 containment tested via `TrustScoreCalculator.calculate_trust_score()` and `TrustEvidenceService.calculate_trust()` — both are real runtime paths.
- **VERIFIED (runtime)**: EventLog tested via real filesystem operations (tempfile, append, replay, fsync).
- **VERIFIED (runtime)**: StatusAdapter tested with real `VerificationStatus` enum instances.
- **NOT VERIFIED**: EventLog is not yet wired into any production service (no runtime call site appends events during policy processing). This is by design — Phase 1 provides infrastructure only; Phase 2+ will wire it.

## 10. Known Limitations

1. **EventLog not wired into production**: no service currently appends verification events during policy processing. Infrastructure exists but is dormant.
2. **No Human Verification Authority**: the system has no concept of a registered human verifier. `actor_role="human"` is accepted by the log but no UI/workflow produces it.
3. **`calculate_trust_score` reads `verification_status` as an explicit parameter, not from the dict field**: this was already the case before P1-4.1; the F-04 fix relies on this existing design. A future quest may consolidate.
4. **F-04 containment is label-based, not provenance-based**: the fix gates on `verification_status` string, not on verified provenance records. Once Phase 2+ (durable event log wired + content identity) lands, source_reliability should key on verified provenance instead.
5. **External markdown reformat stashed**: the P1-4.0 design doc was auto-reformatted by an external tool; the reformat was stashed (not discarded) to keep worktree clean. It contains no semantic changes.

## 11. Final Decision

P1-4.1 Phase 1 delivers: (a) F-04 contained — unverified labels no longer inflate trust; (b) durable event log infrastructure — append-only, auditable, safe; (c) additive VerificationDecision contract; (d) read-only status adapter. VERIFIED remains ungrantable. The foundation for Phase 2 (content identity + source change detection) and Phase 3 (human verification gate) is established.

## 12. Next Quest

**P1-4.2** (suggested): wire VerificationEventLog into TrustEvidenceService (record verification events durably) + introduce content_identity (sha256) at evidence creation. NOT started — awaiting user instruction.
