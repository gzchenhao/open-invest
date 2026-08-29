# Canonical Taxonomy Integration

**Document**: `Canonical_Taxonomy_Integration_20260827.md`  
**Quest**: P1-3.3 — Canonical Taxonomy Integration  
**Type**: INTEGRATION — Non-destructive, backward compatible  
**Date**: 2026-08-27  
**Depends on**: P1-3.2 Implementation (`schema/canonical_taxonomy.py`)  
**Status**: ✅ INTEGRATION COMPLETE  

---

## 1. Integration Architecture

```
Legacy Parser Output
      ↓
Legacy Industry Value (e.g. "ai", "other", "auto_driving")
      ↓
Canonical Registry.resolve()
      ↓
Canonical Industry ID (e.g. "ai", "other", "autonomous_driving")
      ↓
Optional Output Field: canonical_industry
```

**Key principle**: Legacy `industry` field is NEVER modified. `canonical_industry` is an ADDITIONAL optional field.

---

## 2. Parser Integration Point

### PolicyCleaner (`policy_cleaner.py`)

- `StructuredPolicy` dataclass: added `canonical_industry: Optional[str] = None`
- `clean_policy_text()`: after determining legacy `industry`, calls `registry.resolve(legacy_industry)` to populate `canonical_industry`
- Lazy import pattern avoids circular dependencies

### ChinaPolicyCleaningService (`china_policy_cleaning_service.py`)

- After setting `info["industry"]`, also sets `info["canonical_industry"]` via `registry.resolve()`
- Same lazy import pattern

---

## 3. Legacy Field Behavior

| Field | Status | Example |
|---|---|---|
| `industry` | **PRESERVED** — never modified | `"ai"`, `"other"`, `"auto_driving"` |
| `canonical_industry` | **NEW** — optional, populated by registry | `"ai"`, `"other"`, `"autonomous_driving"` |

Legacy clients that only read `industry` continue to work unchanged.

---

## 4. canonical_industry Behavior

- Always populated when registry is available
- Web servers (`interactive_ai_server.py`, `fixed_server.py`): graceful degradation if registry import fails (field simply not added)
- Parser/Cleaning Service (`policy_cleaner.py`, `china_policy_cleaning_service.py`): fail loudly if registry import fails (no silent wrong classification)
- Value is always a valid canonical ID (16 active + other + unknown)
- Deterministic: same legacy value → same canonical value

---

## 5. UNKNOWN Semantics

`unknown` means: **cannot reliably determine which canonical category this belongs to.**

Current UNKNOWN mappings:
- `ai_hardware` → `unknown` (could be ai or semiconductor, no reliable basis to decide)
- Any unrecognized string → `unknown`
- Empty/None → `unknown`

---

## 6. OTHER Semantics

`other` means: **confirmed as a DeepTech industry, but not in any specific canonical category.**

Current OTHER mappings:
- Parser output `"other"` (e.g. "新材料" in parser maps to "other") → canonical `"other"`

---

## 7. Mapping Transparency

After integration, every policy can answer:

```
Legacy value:    auto_driving
Canonical value: autonomous_driving
Mapping type:    SYNONYM
```

```
Legacy value:    ai_hardware
Canonical value: unknown
Mapping type:    UNKNOWN
```

---

## 8. Backward Compatibility

| Component | Modified? | Change |
|---|---|---|
| `StructuredPolicy` | ADDITIVE | New optional field `canonical_industry` |
| `PolicyCleaner` | ADDITIVE | Populates `canonical_industry` in output |
| `ChinaPolicyCleaningService` | ADDITIVE | Populates `canonical_industry` in info dict |
| `interactive_ai_server.py` | ADDITIVE | Enriches policy dicts with `canonical_industry` |
| `fixed_server.py` | ADDITIVE | Adds `canonical_industry` to simplified policies |

**No existing field renamed, removed, or changed.**

---

## 9. 21-Category Legacy Mapping

All 21 values from `deeptech_policy_schema.json` resolve through the registry:

| Legacy | Canonical | Confidence |
|---|---|---|
| ai_ml | ai | NORMALIZATION |
| robotics | robotics | EXACT |
| quantum_computing | quantum_computing | EXACT |
| biotech | biotech | EXACT |
| fintech | fintech | EXACT |
| cleantech | new_energy | NORMALIZATION |
| aerospace | aerospace | EXACT |
| semiconductor | semiconductor | EXACT |
| blockchain | blockchain | EXACT |
| vr_ar | vr_ar | EXACT |
| nanotech | new_materials | SEMANTIC |
| space_tech | aerospace | SEMANTIC |
| embodied_ai | embodied_ai | EXACT |
| autonomous_driving | autonomous_driving | EXACT |
| cybersecurity | cybersecurity | EXACT |
| iot | iot | EXACT |
| 5g | iot | SEMANTIC |
| edge_computing | iot | SEMANTIC |
| metaverse | vr_ar | SEMANTIC |
| web3 | blockchain | SEMANTIC |
| digital_twin | vr_ar | SEMANTIC |

---

## 10. API Impact

**No breaking change.** API responses now optionally include `canonical_industry`. Legacy clients ignoring this field continue to work.

---

## 11. Data Impact

**No data modified.** No seed data JSON, no database records, no mock data rewritten. The `canonical_industry` field is computed at runtime from the legacy `industry` value.

---

## 12. Trust Impact

**NOT MODIFIED.** No changes to Trust Score, Provenance, Evidence Object, Evidence Graph, or Trust Evidence API. Taxonomy integration does not affect trust semantics.

---

## 13. Future Migration Policy

- Phase 1 (CURRENT): Add `canonical_industry` as optional field alongside legacy `industry`
- Phase 2 (FUTURE): New code can prefer `canonical_industry` over `industry`
- Phase 3 (FUTURE): Legacy `industry` field can be deprecated if all consumers migrate
- All phases are backward compatible

---

## Implementation Files

| File | Change | Lines |
|---|---|---|
| `global_policy_aggregator/processors/policy_cleaner.py` | ADDITIVE | +17 (lazy import + canonical_industry field) |
| `global_policy_aggregator/services/china_policy_cleaning_service.py` | ADDITIVE | +17 (lazy import + canonical_industry) |
| `global_policy_aggregator/web/interactive_ai_server.py` | ADDITIVE | +15 (enrich policies) |
| `global_policy_aggregator/web/fixed_server.py` | ADDITIVE | +13 (add canonical_industry) |
| `tests/test_taxonomy_integration.py` | NEW | 60 tests |

---

*Integration Complete: 2026-08-27*  
*Tests: 342 passed, 0 failed (+60 new)*  
*Quest: P1-3.3 STATUS: PASS*
