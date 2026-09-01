# P1-4.5 — Human Verification Authority Registry & Identity Binding

**Date:** 2026-09-01
**Quest:** P1-4.5
**Baseline:** P1-4.4 complete (commit `7d62567`, 523 tests passed)
**Status:** COMPLETE

---

## AUDIT

### The Free-String verifier_id Loophole

Prior to P1-4.5, the VERIFIED gate checked `actor_role in HUMAN_AUTHORITY_ROLES`
but did NOT verify the `verifier_id` (actor) against any registry. Any caller
could pass `verifier_id="any-string"` + `verifier_role="human_verifier"` and
the gate would grant VERIFIED.

**Authority was decided in 3 places — all role-only:**
1. `TrustEvidenceService.record_human_verification()` — checks `verifier_role not in HUMAN_AUTHORITY_ROLES`
2. `VerificationEventLog.append()` — checks `decision="verified"` requires `actor_role in HUMAN_AUTHORITY_ROLES`
3. `HumanVerificationGate.can_grant_verified()` — checks `evt.actor_role in HUMAN_AUTHORITY_ROLES`

**verifier_id was a free string** — only non-empty check (no registry, no
active/inactive, no identity binding).

**No existing registry** — only `HUMAN_AUTHORITY_ROLES` frozenset of role strings.

**No real authentication** — no auth/login/password/jwt/oauth in server/ or src/.

### Conclusion

A minimal additive `HumanVerificationAuthorityRegistry` is needed to close the
free-string loophole. The registry establishes APPLICATION-LEVEL AUTHORIZATION,
not real-world identity authentication.

---

## DESIGN

### HumanVerificationAuthority (frozen dataclass, additive)

```python
@dataclass(frozen=True)
class HumanVerificationAuthority:
    verifier_id: str    # non-empty, stable identifier
    role: str           # must be in HUMAN_AUTHORITY_ROLES
    active: bool = True # inactive authorities cannot grant VERIFIED
    metadata: Dict = {} # optional display info — NOT identity claims
```

- `__post_init__` validates: non-empty verifier_id, role in HUMAN_AUTHORITY_ROLES, active is bool
- `from_dict` raises on malformed entry (fail closed)

### HumanVerificationAuthorityRegistry

- `register(authority)` — rejects duplicates
- `lookup(verifier_id) → Optional[HumanVerificationAuthority]`
- `is_registered(verifier_id) → bool`
- `is_active(verifier_id) → bool`
- `is_authorized(verifier_id, role) → bool` — registered AND active AND role matches

**Fail-closed semantics:**
- Empty registry → NO VERIFIED possible
- Unknown verifier_id → denied (never assumed human)
- Inactive verifier_id → denied
- Role mismatch → denied
- Malformed entry → raise (never silently skipped)

### VERIFIED Gate Change

The gate now requires (in addition to all existing conditions):
8. An Authority Registry is configured
9. The event's actor (verifier_id) is registered AND active
10. The registered role matches the event's actor_role

If ANY condition fails → VERIFIED refused.

### Identity Boundary

**This Quest implements:** Application-level authority registry / allowlist.

**This Quest does NOT implement:** Login, password authentication, OAuth, SSO,
MFA, enterprise identity, government/institutional identity, cryptographic
proof of human identity.

> **Registry establishes application-level authorization, not real-world
> identity authentication.**

---

## IMPLEMENTED

### Files Modified

1. **`src/trust/verification_event_log.py`**
   - Added `HumanVerificationAuthority` dataclass (frozen, validated)
   - Added `HumanVerificationAuthorityRegistry` class (register/lookup/active/authorized)
   - `HumanVerificationGate.__init__` now accepts optional `authority_registry`
   - `can_grant_verified()` now checks registry (fail closed if absent)
   - `get_effective_verified_state()` now checks registry for effective validity

2. **`src/trust/trust_service.py`**
   - `__init__` gains optional `authority_registry` parameter
   - `record_human_verification()` checks registry BEFORE recording event (fail closed)
   - Gate instantiations now pass `self.authority_registry`

3. **`tests/test_human_verification_gate.py`** — existing tests updated to register verifiers
4. **`tests/test_source_change_revocation.py`** — existing tests updated to register verifiers

### Files Created

5. **`tests/test_authority_registry.py`** — 42 new tests across 9 test classes

---

## VERIFIED

### Test Results

| Metric | Value |
|--------|-------|
| Baseline (P1-4.4) | 523 passed, 0 failed, 1 warning |
| After P1-4.5 | 565 passed, 0 failed, 1 warning |
| New tests added | 42 |
| Regressions | 0 |

### Test Coverage

- Registry basics (8): register, lookup, active, authorized, duplicate rejection, empty registry
- Malformed entry (5): empty verifier_id, invalid role, non-bool active, from_dict missing field, from_dict bad role
- VERIFIED gate with registry (7): registered active → allowed; unregistered/inactive/wrong-role/empty/arbitrary → denied
- No registry fail closed (2): no registry → VERIFIED denied; gate without registry → denied
- Security boundaries (5): agent/system/MOCK/content_identity_mismatch/evidence_ref_missing → denied
- Legacy compatibility (3): legacy events readable; legacy events without registry → not VERIFIED; unregistered legacy verifier → denied
- Existing behavior preserved (3): revocation/re-verification/validity check still work
- Persistence & determinism (3): EventLog survives restart; deterministic lookup; chronological history
- No authentication claim (3): metadata not identity; registry docstring states NOT authentication; no fake authority
- Backward compatibility (3): service without registry works; mock verify works; canonical industry unaffected

---

## SECURITY BOUNDARY

The VERIFIED gate now requires ALL of the following (10 conditions):
1. A human decision event exists in the durable EventLog
2. The event's decision == "verified"
3. The event's actor_role is in HUMAN_AUTHORITY_ROLES
4. The event's content_identity matches the evidence's current identity
5. The evidence is NOT MOCK
6. The event has non-empty evidence_refs
7. The event's evidence_id matches the target evidence
8. **(P1-4.5) An Authority Registry is configured**
9. **(P1-4.5) The event's actor (verifier_id) is registered AND active**
10. **(P1-4.5) The registered role matches the event's actor_role**

**Agent/System/MOCK/free-form verifier_id are all blocked.** Without a registry,
VERIFIED is NEVER granted (fail closed). The free-string verifier_id loophole
is closed.

---

## BACKWARD COMPATIBILITY

- `TrustEvidenceService()` without event_log or registry → still works for non-VERIFIED operations
- `verify_evidence(mock)` → unchanged
- Legacy events in EventLog → remain readable (append-only log unchanged)
- Legacy events without registry info → NOT magically VERIFIED (gate checks registry)
- `VerificationDecision` schema → unchanged (actor already stores verifier_id)
- No schema/enum/taxonomy/trust-score changes

---

## KNOWN LIMITATIONS

1. **Registry is in-memory** — no persistence. Caller must re-seed on restart.
2. **No real authentication** — registry is application-level authorization, not identity proof.
3. **verifier_id is still a string** — no cryptographic binding to a real person.
4. **No registry admin UI** — registration is programmatic only.
5. **No role hierarchy** — flat allowlist, no RBAC tree.

---

## NON-GOALS

- Login / password authentication
- OAuth / SSO / MFA
- Web UI
- Database migration
- External IAM integration
- Crawler activation
- Real policy verification
- Automatic scheduler
- MCP / A2A (future architecture, out of scope)
- Trust Score redesign
- Taxonomy redesign
- EvidenceObject schema redesign
- Cryptographic identity proof
