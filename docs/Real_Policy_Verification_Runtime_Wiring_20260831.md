# Real Policy Verification — Runtime Wiring + Content Identity (P1-4.2)

**Date**: 2026-08-31
**Quest**: P1-4.2 — Verification Event Log Runtime Wiring + Content Identity
**Baseline**: commit `45fc682`, master, LOCAL == REMOTE, 434 passed / 0 failed / 1 warning

> **This document covers IMPLEMENTED code with VERIFIED tests.** However, the VERIFIED *verification status* itself remains **NOT IMPLEMENTED** — no system path grants it. The event log runtime wiring is verified; Real Policy Verification is NOT verified.

---

## 1. Objective

1. Wire P1-4.1 `VerificationEventLog` into `TrustEvidenceService` runtime path (dormant → active).
2. Implement `compute_content_identity()` — SHA-256 of canonical evidence content.
3. Verify F-04 second-layer safety (no VERIFIED-like trust without legitimate verification).
4. Maintain backward compatibility (legacy callers unaffected).

## 2. Baseline

| Item | Value |
|---|---|
| Branch | master |
| LOCAL HEAD | `45fc682` |
| REMOTE HEAD | `45fc682` |
| Worktree | CLEAN |
| Tests before | 434 passed, 0 failed, 1 warning |

## 3. Runtime Wiring Audit (AUDIT)

**Q1: Where does TrustEvidenceService create/update Evidence?**
- `create_evidence()` (L82): creates `EvidenceObject`, adds to `EvidenceGraph`. No verification event recorded.
- `verify_evidence()` (L188): mock-only; mutates `evidence.verification_status = VerificationStatus.MOCK` (L221). ProvenanceChain event added but ephemeral (discarded after call).

**Q2: Where is verification_status produced?**
- Default in `create_evidence`: `evidence_data.get("verification_status", "MOCK")` (L94).
- Mutation in `verify_evidence`: sets to `VerificationStatus.MOCK` (L221).
- No code path sets `VERIFIED` (repo-wide grep confirmed in P1-4.0).

**Q3: Minimal insertion point for EventLog?**
- `__init__`: optional `event_log_path` parameter → instantiates `VerificationEventLog`.
- `verify_evidence`: after mock verification, before return — append `VerificationDecision` if log is active.

**Q4: Verification event lifecycle?**
- `verify_evidence(mock)` → `VerificationDecision(decision="mock", actor_role="system")` → `event_log.append()` → persisted to JSONL → readable via `get_verification_history()`.

**Q5: Can EventLog truly save and re-read?**
- Yes — VERIFIED by test_rw_003 (persistence across instances).

**Q6: Can any code bypass EventLog to modify status?**
- `verify_evidence` directly mutates `evidence.verification_status` (L221). This is the EXISTING behavior (pre-P1-4.2) and only sets MOCK (never VERIFIED). The EventLog is additive — it records the decision but does not gate the mutation. No bypass to VERIFIED exists.

## 4. Content Identity (DESIGN → IMPLEMENTED → VERIFIED)

### DESIGN

`content_identity = SHA-256(canonical_json)` where canonical_json is built from a FIXED set of fields (`id`, `type`, `source`, `source_reference`, `verification_status`, `confidence_score`) with `sort_keys=True, ensure_ascii=False`.

Key ordering does not affect the hash. Content change changes the hash. None input returns None (no content → no identity). SHA-256 is a content identity, NOT a verification proof.

### IMPLEMENTED

`compute_content_identity()` in `verification_event_log.py` (new function, ~15 lines).

### VERIFIED

6 tests (TEST-CI-001..006): determinism, key-order independence, content-change detection, empty/missing, non-string values, cross-instance determinism.

## 5. Event Log Runtime Wiring (IMPLEMENTED → VERIFIED)

### IMPLEMENTED

**`trust_service.py`**:
- `__init__` gains optional `event_log_path` parameter (default None → no log, backward compatible).
- `verify_evidence` appends `VerificationDecision` (decision="mock", actor_role="system", content_identity=compute_content_identity) if log is active.
- New `get_verification_history(evidence_id)` method: read-only, returns events from log.

**`verification_event_log.py`**:
- New `compute_content_identity()` function.

### VERIFIED

10 runtime wiring tests (TEST-RW-001..010):
- verify_evidence records event ✅; event contains content_identity ✅; persistence across instances ✅; duplicate event_id rejected ✅; malformed event reported ✅; write failure propagates ✅; deterministic replay ✅; get_verification_history ✅; create_evidence does NOT record event ✅; verify never upgrades to VERIFIED ✅.

## 6. F-04 Second-Layer Safety (VERIFIED)

7 tests (TEST-F04S-001..007):
- VERIFIED + government → 80 (legitimate) ✅
- UNVERIFIED/MOCK/REJECTED + government → 50 (contained) ✅
- Agent candidate decision does not produce VERIFIED ✅
- Missing verification event does not produce VERIFIED ✅
- Missing/malformed verifier cannot record "verified" (ValueError) ✅

## 7. Backward Compatibility (VERIFIED)

5 tests (TEST-BC-001..005):
- Legacy EvidenceObject without content_identity loads ✅
- `TrustEvidenceService()` without event_log_path works ✅
- Legacy serialized record loads ✅
- MOCK not upgraded ✅
- canonical_industry (P1-3.5) unaffected ✅

## 8. Trust / Provenance Impact

- Trust Score formula: unchanged (F-04 containment from P1-4.1 preserved).
- ProvenanceChain: unchanged (still ephemeral; EventLog is a separate durable layer).
- verification_status semantics: unchanged (MOCK stays MOCK, UNVERIFIED stays UNVERIFIED).
- EventLog is NOT a Trust Score input — it does not add "points".

## 9. Security Boundary

- Agent cannot record "verified" ✅ (enforced at append)
- MOCK cannot become VERIFIED ✅ (verify_evidence only sets MOCK)
- UNVERIFIED cannot become VERIFIED ✅ (no code path)
- No Human Verification Authority exists ✅ (NOT IMPLEMENTED)
- No fake verifier in events ✅ (system/mock actor only)
- No hidden fallback / silent guessing ✅
- MCP/A2A: still NOT IMPLEMENTED ✅
- Crawler: not activated ✅

## 10. Tests

| Phase | Count | Result |
|---|---|---|
| Before | 434 | 434 passed, 0 failed |
| New | 31 | 31 passed |
| After | 465 | **465 passed, 0 failed**, 1 warning (pre-existing) |

## 11. Known Limitations

1. **EventLog is optional**: `TrustEvidenceService()` without `event_log_path` has no event log — existing callers are unaffected but also uninstrumented.
2. **verify_evidence still directly mutates status**: the EventLog records the decision but does not gate the MOCK mutation. This is the existing behavior; gating would require changing verification semantics (out of scope).
3. **Content identity covers EvidenceObject fields only**: it does not cover policy text or source page content (no policy text exists in EvidenceObject today).
4. **No Human Verification Authority**: `actor_role="human"` is accepted by the log but no workflow produces it. VERIFIED remains ungrantable.
5. **get_verification_history is new API**: additive, no breaking change, but existing consumers are unaware of it.

## 12. Final Decision

P1-4.2 delivers: (a) EventLog wired into `verify_evidence` runtime path (dormant → active when configured); (b) `compute_content_identity()` for deterministic SHA-256 content hashing; (c) `get_verification_history()` read-only API; (d) F-04 second-layer safety verified across all status × label combinations. VERIFIED remains ungrantable. The foundation for Phase 3 (Human Authority → VERIFIED) is established but not implemented.

## 13. Next Quest

**P1-4.3** (suggested): Human Verification Authority gate — design and implement the minimal interface for a registered human verifier to record a "verified" decision, with the provenance validator enforcing that a "verified" label without a matching human decision event is a governance violation. NOT started — awaiting user instruction.
