# Human Verification Authority Gate (P1-4.3)

**Date**: 2026-08-31
**Quest**: P1-4.3 — Human Verification Authority Gate
**Baseline**: commit `b24d169`, master, LOCAL == REMOTE, 465 passed / 0 failed / 1 warning

> **VERIFIED status is now grantable — but ONLY through the Human Verification Authority Gate.** Agent, System, MOCK, labels, and direct status mutation CANNOT produce VERIFIED. However, the gate is an application-level authority boundary, NOT an identity authentication platform.

---

## 1. Objective

Build a minimal, unbypassable Human Verification Authority Gate so that VERIFIED requires: Human Authority + Verification Decision + Durable Event + Matching Content Identity + Evidence Reference.

## 2. Baseline

| Item | Value |
|---|---|
| Branch | master |
| LOCAL HEAD | `b24d169` |
| REMOTE HEAD | `b24d169` |
| Worktree | CLEAN |
| Tests before | 465 passed, 0 failed, 1 warning |

## 3. Audit Findings (AUDIT)

1. **Status mutation**: `verify_evidence()` L221 sets MOCK (only); `create_evidence()` takes default from input. **No code path sets VERIFIED.**
2. **VERIFIED string**: only in enum definitions, weight maps, and comment guards — no production grant.
3. **EventLog schema sufficient**: `VerificationDecision` already supports `actor_role` + `decision="verified"`; `append()` already had safety gates. No additive fields needed.
4. **Minimal insertion point**: new `record_human_verification()` on `TrustEvidenceService` — records human decision event + checks gate before granting VERIFIED.
5. **G-09**: duplicate `@dataclass` at `trust_request_response.py:235-236` — NOT on this Quest's modification path. Left unchanged.

## 4. Human Authority Model (DESIGN)

**Allowlisted roles**: `HUMAN_AUTHORITY_ROLES = frozenset({"human_verifier", "authorized_reviewer"})`

These are application-level authority boundary identifiers, NOT:
- user accounts / OAuth / JWT / RBAC backend
- email verification
- government identity verification
- real human login

**Flow**: Agent/System records candidate → Human Authority reviews → `record_human_verification(verifier_id, verifier_role, verification_evidence)` → Gate checks ALL conditions → VERIFIED granted (or refused)

## 5. VERIFIED Gate (DESIGN → IMPLEMENTED)

`HumanVerificationGate.can_grant_verified()` checks ALL conditions:
1. Human decision event exists in durable EventLog (Rule C)
2. `decision == "verified"` (Rule D)
3. `actor_role in HUMAN_AUTHORITY_ROLES` (Rule A/B)
4. `content_identity` matches evidence's current identity (Rule D)
5. Evidence is NOT MOCK (Rule E)
6. `evidence_refs` is non-empty (Rule B)
7. `evidence_id` matches target (Rule D)

If ANY condition fails → VERIFIED refused. Gate is read-only w.r.t. EventLog.

## 6. Event Integration (IMPLEMENTED)

- `record_human_verification()` on `TrustEvidenceService` — the **ONLY** method that can result in VERIFIED.
- Records `VerificationDecision(decision="verified", actor_role=<human_role>, content_identity=...)` to durable JSONL log.
- `append()` safety gate updated: `verified` requires `actor_role in HUMAN_AUTHORITY_ROLES` (was `== "human"` — too narrow for P1-4.3's allowlisted roles).
- After successful append, `HumanVerificationGate.can_grant_verified()` re-checks ALL conditions before mutating `node.data["verification_status"] = "VERIFIED"`.

## 7. Runtime Verification (VERIFIED)

29 tests across 6 classes:
- **Authority** (7): valid human_verifier/authorized_reviewer → VERIFIED ✅; missing verifier_id → rejected ✅; agent/system/unknown role → rejected ✅; missing evidence → rejected ✅
- **Event integrity** (6): VERIFIED without event → rejected ✅; mismatched evidence_id → rejected ✅; mismatched content_identity → rejected ✅; missing content_identity → rejected ✅; missing evidence_refs → rejected ✅; duplicate event_id → ValueError ✅
- **Safety** (6): MOCK → never VERIFIED ✅; UNVERIFIED → cannot bypass gate ✅; Agent candidate → cannot VERIFIED ✅; unknown status → never VERIFIED ✅; government label alone → never VERIFIED ✅; no event log → no VERIFIED ✅
- **Persistence** (3): decision survives replay ✅; matching event found across instances ✅; VERIFIED status persists in graph ✅
- **Backward compatibility** (5): service without event_log works ✅; mock verify works ✅; unverified stays unverified ✅; canonical_industry unaffected ✅; HUMAN_AUTHORITY_ROLES is allowlisted ✅
- **Determinism** (2): gate result deterministic ✅; replay deterministic ✅

## 8. Security Boundary

| Rule | Status |
|---|---|
| A — Agent cannot VERIFIED | ✅ enforced at append() + record_human_verification() |
| B — Human Authority mandatory | ✅ verifier_id + role + evidence_refs required |
| C — EventLog mandatory for VERIFIED | ✅ no event → no VERIFIED |
| D — Event matching | ✅ evidence_id + content_identity + decision verified |
| E — MOCK orthogonal | ✅ is_mock → always rejected |
| F — UNVERIFIED cannot jump to VERIFIED | ✅ must go through Human Gate |
| G — No fake authority | ✅ tests use "test-human-verifier-001" synthetic identity |

## 9. Backward Compatibility

- `TrustEvidenceService()` without `event_log_path` — works unchanged ✅
- `verify_evidence("mock")` — works unchanged (MOCK only) ✅
- Legacy EvidenceObject / serialized records — load correctly ✅
- canonical_industry (P1-3.5) — unaffected ✅
- Trust Score formula — unchanged ✅
- P1-4.1 tests updated: `actor_role="human"` → `"human_verifier"` (role vocabulary alignment, NOT test weakening) ✅

## 10. Trust Impact

- Trust Score formula: unchanged ✅
- F-04 containment: preserved (VERIFIED path still gets 80; non-VERIFIED gets 50) ✅
- ProvenanceChain: unchanged (ephemeral; EventLog is separate durable layer) ✅
- New: VERIFIED is now reachable through `record_human_verification()` — but ONLY through the gate.

## 11. Tests

| Phase | Count | Result |
|---|---|---|
| Before | 465 | 465 passed, 0 failed |
| New | 29 | 29 passed |
| After | 494 | **494 passed, 0 failed**, 1 warning (pre-existing) |

2 P1-4.1 tests updated for role vocabulary alignment (no weakening).

## 12. Known Limitations

1. **Application-level authority**: no real authentication — `verifier_id` is a free string. Future Quest may add identity verification.
2. **No human verifier registration**: any caller passing `verifier_role="human_verifier"` can attempt verification. The gate validates the role but not the identity. This is a known boundary — real authentication is a future Quest.
3. **EventLog still optional**: `TrustEvidenceService()` without `event_log_path` has no gate — but also cannot grant VERIFIED (returns "No event log configured").
4. **content_identity covers EvidenceObject fields only**: not policy text or source page content.
5. **G-09**: `trust_request_response.py:235-236` duplicate `@dataclass` — not on this Quest's path.

## 13. Non-Goals

This Quest does NOT implement:
- User accounts / OAuth / JWT / RBAC
- Database / email verification / government identity
- Real human login / crawler activation / MCP/A2A
- Trust Score formula changes / ProvenanceChain redesign

## 14. Final Decision

**VERIFIED is not granted by Agent, System, MOCK, or label alone.** It requires: Human Authority Role + Verifier Identity + Verification Evidence + Durable Decision Event + Matching Content Identity. The gate is implemented, tested, and backward compatible.

## 15. Next Quest

**P1-4.4** (suggested): Source Change Detection — when a verified source's content_identity changes, automatically downgrade VERIFIED back to CANDIDATE_REVIEW_REQUIRED and flag for re-verification. NOT started — awaiting user instruction.
