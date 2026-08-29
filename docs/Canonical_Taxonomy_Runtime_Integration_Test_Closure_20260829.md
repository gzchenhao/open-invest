# Canonical Taxonomy Runtime Integration Test Closure (P1-3.4)

**Date**: 2026-08-29
**Quest**: P1-3.4 — Runtime Integration Test Closure
**Closes**: F-10 from `docs/Canonical_Taxonomy_Integration_Independent_Verification_20260827.md` (P1-3.3.1)
**Final Verdict**: **PASS WITH FINDINGS** — **F-10 = CLOSED**
**Baseline commit**: `f5fc8ec` (LOCAL == REMOTE, worktree clean)

This document closes the F-10 follow-up identified during P1-3.3.1 Independent Verification.

---

## 1. Purpose

F-10 (P1-3.3.1) recorded that `ChinaPolicyCleaningService` and `fixed_server.py`
canonical_industry population had NO runtime test coverage (only registry-level
tests + one-off audit runtime checks). This quest adds REAL runtime integration
tests through the actual service/server processing paths and closes F-10.

Out of scope (unchanged): taxonomy redesign, Trust Infrastructure, MCP/A2A,
real government data, canonical category count, mapping strategy.

## 2. F-10 Background

> F-10 | `tests/test_taxonomy_integration.py` | No runtime test of
> `ChinaPolicyCleaningService` / `fixed_server` canonical_industry population
> (covered only via registry-level tests + audit runtime checks) | LOW-MEDIUM
> | FOLLOW-UP — recommend adding 2-3 runtime tests in a future quest

## 3. Baseline

| Item | Value |
|---|---|
| Branch | `master` |
| LOCAL == REMOTE | ✅ `f5fc8ec` |
| Worktree | CLEAN |
| Tests | 342 passed, 0 failed, 1 warning (pre-existing third-party StarletteDeprecationWarning) |
| Handover | `OpenInvest_Technical_Handover_Trae_20260829.md` (unique) |

## 4. Cleaning Service Runtime Path

Confirmed from code (not assumed):

- Public batch entry: `ChinaPolicyCleaningService.batch_clean_china_policies(files)`
  → per-file `_clean_china_policy_text(text, source_url, region)` →
  `_extract_china_basic_info(...)` (canonical resolution happens here) →
  `StructuredPolicy(...)` → `db_service.add_policy(policy)`.
- The industry keyword mapping is a LOCAL variable inside
  `_extract_china_basic_info` (`china_industry_mapping`, 10 CN→EN keys). Its
  runtime input domain is therefore fixed: 10 EN values + the "other" fallback.

### Finding A (real runtime bug — FIXED, minimal)

`_clean_china_policy_text` resolved the canonical value into
`basic_info["canonical_industry"]` but did NOT pass it into the
`StructuredPolicy(...)` constructor, so every cleaned policy carried
`canonical_industry=None` regardless of input. Probe evidence (pre-fix):

```
policy.industry          : 'ai'
policy.canonical_industry: None
basic_info[canonical_industry]: 'ai'
```

Fix (4 lines, `china_policy_cleaning_service.py`): propagate
`canonical_industry=basic_info.get("canonical_industry")` into the
`StructuredPolicy(...)` construction. No taxonomy/mapping changes.

### Runtime test coverage (tests/test_cleaning_service_runtime_integration.py — 20 tests)

| Requirement (QUEST PART 2) | Result |
|---|---|
| legacy industry → canonical (all 10 production keys, end-to-end) | ✅ parametrized 10/10 |
| synonym → canonical | runtime-unreachable (local mapping fixed); covered at registry level by P1-3.3 tests |
| normalization → canonical | runtime-unreachable (same); registry-level by P1-3.3 |
| semantic mapping → canonical | runtime-unreachable (same); registry-level by P1-3.3 |
| unknown → UNKNOWN (no silent guess) | ✅ no-keyword text → industry="other", canonical="other" |
| ai_hardware → UNKNOWN | runtime-unreachable via service input domain; REAL runtime proof provided via fixed_server seed path (below) |
| legacy industry unchanged | ✅ |
| canonical_industry additive | ✅ (all other fields byte-identical semantics; backward-compatible construction covered) |
| deterministic output | ✅ 20 runs single service + 5 fresh service instances |
| mock/quality markers preserved | ✅ `metadata.data_quality == "estimated"`, region metadata intact |
| invalid/missing industry — no silent guess | ✅ |
| exception handling — fail loudly, no wrong canonical | ✅ broken registry → RuntimeError propagates; batch marks file failed; db receives nothing |
| full batch chain incl. db hand-off | ✅ tmp file → batch → StubDB captured policy has canonical_industry |

Honesty note: synonym/normalization/semantic/ai_hardware CANNOT be reached
through the service's production text extraction (fixed local mapping). We did
NOT fabricate coverage; those confidence levels remain covered by P1-3.3
registry-level tests, and the ai_hardware→UNKNOWN behavior is proven at
runtime through the fixed_server seed path, which CAN accept arbitrary legacy
keys.

## 5. Fixed Server Runtime Path

Confirmed from code (not assumed):

- Module-level `policies = load_policies()` at import time.
- `load_policies()` main path: reads
  `web/data/seed_data/detailed_china_tech_policies.json`; for each entry maps
  EN industry key → CN label, then applies the P1-3.3 enrichment
  (`get_registry().resolve(legacy_key)` inside try/except — graceful).
- Fallback path (seed file absent): returns 2 hardcoded MOCK policies WITHOUT
  canonical_industry.
- FastAPI endpoints `/api/stats` and `/api/search` serve the module-level
  policies.

### Finding B (safe behavior — recorded, NOT changed)

The seed file does NOT exist in the current repo, so production traffic always
takes the fallback path, which emits policies with NO canonical_industry field
(graceful degradation: field absent, never a wrong value). The P1-3.3
enrichment code is currently dead in practice. Left unchanged: adding
enrichment to the hardcoded fallback would expand scope and alter legacy
demo output; field-absence is safe by design (P1-3.3 integration doc §4).

### Runtime test coverage (tests/test_fixed_server_runtime_integration.py — 15 tests)

| Requirement (QUEST PART 3) | Result |
|---|---|
| policy input → canonical_industry (seed path) | ✅ all 10 T7 keys end-to-end |
| legacy industry preserved (CN label) | ✅ per-key CN label assertions |
| canonical_industry correct | ✅ (incl. synonym `auto_driving→autonomous_driving`, merged `advanced_manufacturing→high_end_equipment`) |
| unknown input not guessed | ✅ `mystery_unknown_field → unknown` |
| ai_hardware → UNKNOWN at REAL runtime | ✅ via seed path; never ai/semiconductor |
| missing industry field | ✅ → unknown (`else` branch) |
| Mock data stays Mock | ✅ both paths: `is_mock=True`, `verification_status="mock"`, `claim_status="unclaimed"` |
| canonical_industry additive | ✅ |
| old fields still present | ✅ |
| graceful degradation correct | ✅ fallback path: field absent, no error |
| server runtime does not modify Trust semantics | ✅ markers verified through HTTP responses |
| determinism | ✅ 20 runs of `load_policies()` identical |
| FastAPI endpoints (real HTTP) | ✅ `/api/stats`, `/api/search` (+empty keywords) |

## 6. Test Cases

New files (35 tests total):

- `tests/test_cleaning_service_runtime_integration.py` — 20 tests
- `tests/test_fixed_server_runtime_integration.py` — 15 tests

`.gitignore` note: `test_*.py` (line 40) ignores new test files; both are
force-added (`git add -f`) as REQUIRED by the quest (existing tracked test
files follow the same pattern). `.gitignore` itself was NOT modified.

## 7. Backward Compatibility

- Legacy `industry` values unchanged everywhere (service + server + API).
- `canonical_industry` remains optional; `StructuredPolicy` still constructs
  without it (None default) — old callers unaffected.
- Old inputs never fail due to missing canonical_industry.
- Old clients can keep reading `industry`; no rename/removal/override.

## 8. UNKNOWN / OTHER Safety

- `ai_hardware → unknown` at runtime (fixed_server seed path) — never `ai`,
  never `semiconductor`.
- Unknown/missing inputs → `unknown` / `other` — never guessed.
- `UNKNOWN ≠ OTHER` (distinct canonical ids, distinct runtime outcomes).
- `UNKNOWN ≠ VERIFIED`; `MOCK ≠ VERIFIED` (markers asserted in both files).
- No taxonomy decision was changed in this quest.

## 9. Determinism

- Cleaning Service: same text ×20 (one instance) + ×5 fresh instances →
  identical `(industry, canonical_industry)`.
- Fixed Server: `load_policies()` ×20 → identical
  `(title, industry, canonical_industry)` tuples.

## 10. Mock Safety

- No real government data, contacts, or verification used anywhere.
- No production-ready / fully-verified / MCP / A2A claims introduced
  (grep-verified: 0 matches).
- All mock data keeps `is_mock=True`; taxonomy integration never touches
  `verification_status`.

## 11. Test Results

| Metric | Value |
|---|---|
| Before | 342 passed, 0 failed |
| After | **377 passed, 0 failed** |
| New tests | 35 (20 + 15) |
| Warnings | 1 — pre-existing third-party `StarletteDeprecationWarning` (fastapi testclient); none added by this quest |

## 12. Findings

| ID | Finding | Severity | Disposition |
|---|---|---|---|
| P134-A | Cleaning Service resolved canonical value never reached `StructuredPolicy` output (always None) | MEDIUM (correctness of P1-3.3 integration) | **FIXED** (minimal 4-line propagation; no mapping change) |
| P134-B | fixed_server enrichment is dead code in current repo state (seed file absent); fallback emits no canonical field | LOW (safe by design) | RECORDED (graceful degradation; not changed to avoid scope expansion) |
| P134-C | `services` top-level name ambiguous (`server/services` regular package beats `global_policy_aggregator/services` namespace package under pytest.ini `pythonpath = . server`) | LOW (test-infra only) | HANDLED (test loads aggregator module via importlib from file path; no production change) |
| P134-D | synonym/normalization/semantic/ai_hardware unreachable via cleaning service runtime (fixed local mapping) | LOW (coverage honesty) | RECORDED (registry-level coverage from P1-3.3 remains; ai_hardware runtime proof moved to fixed_server seed path) |

## 13. F-10 Closure Status

**F-10 = CLOSED**

Criteria met:

1. `ChinaPolicyCleaningService` has REAL runtime integration coverage
   (text → service → StructuredPolicy → db hand-off): 20 tests.
2. `fixed_server.py` has REAL runtime integration coverage
   (seed path + fallback path + FastAPI HTTP endpoints): 15 tests.
3. All key behaviors pass (mapping correctness, unknown safety, backward
   compatibility, determinism, mock markers, fail-loudly exception path).
4. One real runtime bug found by the new coverage was FIXED (P134-A) — the
   coverage is demonstrably meaningful, not decorative.

## 14. Final Verdict

**PASS WITH FINDINGS** (findings P134-B/C/D recorded; P134-A fixed)

- F-10 is closed through genuine runtime paths, not test-count inflation.
- Trust Infrastructure untouched; no data changes; no taxonomy changes.
- Scope: 2 new test files + 1 minimal production correctness fix (4 lines).
