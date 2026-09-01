# P1-4.6 — Persistent / Config-Driven Human Authority Registry

**Date:** 2026-09-01
**Quest:** P1-4.6
**Baseline:** P1-4.5 complete (commit `0209381`, 565 tests passed)
**Status:** COMPLETE

---

## AUDIT

### P1-4.5 Limitation: In-Memory Registry

The `HumanVerificationAuthorityRegistry` (P1-4.5) is fully in-memory —
`__init__` takes an optional list of `HumanVerificationAuthority` objects
stored in a `Dict[str, HumanVerificationAuthority]`. No persistence, no
config loading. Each `TrustEvidenceService` instance must be explicitly
seeded with a registry; process restart loses the authorization boundary.

### Existing Config Mechanisms

- `server/config/config.py` — Pydantic `BaseModel` + `from_env()` for uvicorn
  server runtime config. Server-specific, not trust-module config.
- `examples/trust_pipeline_demo.py` — `json.load()` from JSON files for demo
  data. Demonstrates JSON loading pattern.
- No trust-module config convention exists.

### Conclusion

JSON is the minimal config format — stdlib (`json`), already used throughout
(EventLog is JSONL, EvidenceObject serialises to JSON), no new dependencies.
Config loading belongs co-located with the registry in
`verification_event_log.py`, following the existing `from_dict()` pattern.

---

## DESIGN

### Config Format (JSON)

```json
{
    "authorities": [
        {
            "verifier_id": "human-reviewer-001",
            "role": "human_verifier",
            "active": true,
            "metadata": {"display_name": "Reviewer 001"}
        }
    ]
}
```

- `verifier_id`: non-empty string (stable identifier)
- `role`: must be in `HUMAN_AUTHORITY_ROLES` (`human_verifier`, `authorized_reviewer`)
- `active`: must be a real `bool` (no silent coercion from strings/integers)
- `metadata`: optional dict (display info only, NOT identity claims)

### from_config() Classmethod

`HumanVerificationAuthorityRegistry.from_config(config_path: str)` loads a
registry from a JSON file. The existing `__init__(authorities=...)` API is
unchanged — `from_config` is purely additive.

### Service Integration

`TrustEvidenceService.__init__` gains optional `authority_registry_config_path`.
Priority: explicit `authority_registry` > `authority_registry_config_path` > None.

### Fail-Closed Rules

| Condition | Result |
|-----------|--------|
| Config file not found | `FileNotFoundError` — no registry |
| Malformed JSON | `ValueError` — no registry |
| Missing `authorities` key | `ValueError` — no registry |
| `authorities` not a list | `ValueError` — no registry |
| Entry not a JSON object | `ValueError` — no registry |
| Invalid role | `ValueError` — no registry |
| Empty verifier_id | `ValueError` — no registry |
| Non-bool `active` | `ValueError` — no registry |
| Duplicate verifier_id | `ValueError` — no registry |
| Empty config path | Treated as None → no registry → VERIFIED denied |

**Never**: load failure → assume human → VERIFIED.

---

## IMPLEMENTED

### Files Modified

1. **`src/trust/verification_event_log.py`**
   - Added `HumanVerificationAuthorityRegistry.from_config()` classmethod — loads from JSON, fail-closed on all error paths.
   - Hardened `HumanVerificationAuthority.from_dict()` — `active` field now type-checked (no silent `bool()` coercion of strings/integers).

2. **`src/trust/trust_service.py`**
   - `__init__` gains optional `authority_registry_config_path` parameter.
   - Registry resolution: explicit registry > config path > None (fail closed).

### Files Created

3. **`tests/test_authority_registry_config.py`** — 46 new tests across 7 test classes.

---

## VERIFIED

### Test Results

| Metric | Value |
|--------|-------|
| Baseline (P1-4.5) | 565 passed, 0 failed, 1 warning |
| After P1-4.6 | 611 passed, 0 failed, 1 warning |
| New tests added | 46 |
| Regressions | 0 |

### Test Coverage

- Config loading (6): valid config, deterministic, process-equivalent reload, metadata preserved, empty authorities, active=false preserved
- Fail-closed (13): missing file, malformed JSON, missing key, wrong type, invalid role, empty verifier_id, duplicate, non-object entry, non-bool active, empty path, non-dict config, missing verifier_id field, missing role field
- VERIFIED gate with config (7): registered active → allowed; unregistered/inactive/role-mismatch/empty/arbitrary → denied
- No config fail closed (2): no registry + no config → denied; no role-only fallback
- Security boundaries (5): agent/system/MOCK/content_identity_mismatch/missing_evidence_ref → denied
- Service integration (6): config_path loads, explicit takes precedence, load failure propagates, missing file propagates, legacy compat, empty path ignored
- Backward compat (4): legacy events readable, revocation works, re-verification works, EventLog persistence
- No authentication claim (3): docstring disclaims auth, metadata not identity, no password/token field

---

## SECURITY BOUNDARY

The VERIFIED gate conditions (10) from P1-4.5 are unchanged. P1-4.6 adds
config-driven durability to the Authority Registry (condition 8-10) without
weakening any existing condition. The gate still requires:

1. Human decision event exists in durable EventLog
2. Event decision == "verified"
3. Event actor_role in HUMAN_AUTHORITY_ROLES
4. Content_identity matches
5. Evidence is NOT MOCK
6. Non-empty evidence_refs
7. Evidence_id matches
8. Authority Registry configured (now loadable from config)
9. Verifier_id registered AND active
10. Registered role matches event actor_role

**Agent/System/MOCK/free-form verifier_id all blocked.** No registry →
VERIFIED never granted. Config load failure → construction fails (no silent
fallback to role-only authorization).

---

## CONFIGURATION MODEL

- Config persistence solves **authorization configuration durability** — the
  operator's allowlist survives process restarts.
- Config does NOT provide **identity authentication** — the registry is still
  an application-level allowlist, not a login system.
- Config is read once at construction. The registry is in-memory after load.
- Mutation API (`register()`) still exists for programmatic use but is not
  exposed through the config loading path.

> **Config persistence = authorization durability, NOT identity authentication.**

---

## FAIL-CLOSED BEHAVIOR

```
Missing config       → no authority registry   → VERIFIED denied
Malformed config     → load failure (raises)   → VERIFIED denied
Unknown verifier     → not registered          → VERIFIED denied
Inactive verifier    → active=false            → VERIFIED denied
Role mismatch        → registry.role != event  → VERIFIED denied
Empty verifier_id    → construction fails      → VERIFIED denied
Non-bool active      → from_dict raises        → VERIFIED denied
Duplicate verifier   → register() raises       → VERIFIED denied
```

**Never**: load failure → assume human_verifier → VERIFIED.

---

## BACKWARD COMPATIBILITY

- `TrustEvidenceService()` without registry or config → non-VERIFIED ops work (legacy)
- `VerificationDecision` schema → unchanged
- `VerificationStatus` enum → unchanged
- Existing `HumanVerificationAuthorityRegistry(authorities=...)` API → unchanged
- `HumanVerificationGate` → unchanged (receives registry via constructor as before)
- Legacy events in EventLog → remain readable
- Revocation / re-verification → unchanged
- Trust Score / taxonomy / MOCK semantics → unchanged
- No new dependencies (stdlib `json` only)

---

## KNOWN LIMITATIONS

1. **Config is read once** — no hot-reload. Registry changes require service restart.
2. **No config validation UI** — operators must ensure config correctness before deployment.
3. **No config file watching** — no automatic reload on file change.
4. **verifier_id is still a string** — no cryptographic binding to a real person.
5. **No multi-file merge** — single config file only (no include/overlay mechanism).

---

## NON-GOALS

- Login / password authentication
- OAuth / SSO / MFA
- Web UI / admin panel
- Database persistence
- External IAM integration
- Crawler activation
- Real policy verification
- Automatic scheduler
- MCP / A2A (future architecture, out of scope)
- Trust Score redesign
- Taxonomy redesign
- EvidenceObject schema redesign
- Cryptographic identity proof
- Hot-reload / file watching
- Multi-file config merge
