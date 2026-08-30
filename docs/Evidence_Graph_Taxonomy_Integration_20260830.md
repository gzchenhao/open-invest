# P1-3.5 Evidence Graph Taxonomy Integration

Date: 2026-08-30
Quest: P1-3.5 — Evidence Graph Canonical Taxonomy Integration (OPTION A)
Status markers used in this document: **AUDIT** (observed reality), **DESIGN** (decided approach), **IMPLEMENTED** (code written), **VERIFIED** (proven by tests/runtime).

---

## 1. Objective

Verify the Evidence Graph's `sector` reality, and — where justified — align it with the existing Canonical Industry Taxonomy via a minimal additive change, without breaking Evidence Graph, Trust, Provenance, MOCK, UNVERIFIED, or backward compatibility.

## 2. Baseline (VERIFIED at quest start)

- Branch: `master`, LOCAL HEAD == REMOTE HEAD (`e7394b7`), WORKTREE CLEAN.
- Test baseline: 377 passed, 1 warning (pre-existing fastapi/starlette testclient deprecation).
- Master Handover: exactly one (`OpenInvest_Technical_Handover_Trae_20260829.md`).
- Test interpreter note: `py -3.14 -m pytest` (bare `python` resolves to a 3.12 without pytest on this machine — environment PATH issue, not a project conflict).

## 3. Evidence Graph Current Reality (AUDIT)

- `GraphNode.data` is free-form `Dict[str, Any]` ([src/trust/evidence_graph.py]). `sector` was a free string key with no canonical linkage.
- Runtime-observed sector values (entire repository):
  - `"AI"` — only in `example_graph_operations()` example code.
  - `"人工智能"` — only in `examples/trust_demo/company_example.json`, which is **not loaded by any runtime code**.
- Design-doc enum (`docs/Evidence_Graph_Prototype.md` `TechnologyNode.category`): `AI | BIOTECH | QUANTUM | CLEAN_TECH | ADVANCED_MATERIALS | OTHER` — this exact set is already registered in the canonical taxonomy as legacy source **T11_evidence_graph** (P1-3.2).
- `EvidenceObject` has **no** sector field. `TrustEvidenceService.create_evidence()` stores `evidence.to_dict()` as node data — no top-level sector is possible on service-created evidence nodes.
- `GraphQueryEngine.find_company_evidence(company_name, sector)` filters by case-insensitive substring match on `node.data["sector"]` — a legacy consumer of the raw sector string.
- `GraphNode` is used only inside `evidence_graph.py`; `src/trust/` is a namespace package (no `__init__.py` exports to preserve).
- Existing tests had **no** dependency on sector semantics.

**Conclusion:** sector was a free string that already carried de-facto taxonomy-identifier semantics (used as a query filter) without any canonical definition — a mild, real inconsistency. Integration was justified (registry already reserved T11 for this exact domain; Handover OPTION A mandated it).

## 4. Canonical Mapping (AUDIT + DESIGN; zero new mapping definitions)

All resolution is delegated to `schema/canonical_taxonomy.py` `resolve()` (deterministic lookup; order: direct → case-insensitive → alias → `"unknown"`). No second taxonomy is defined anywhere in this quest.

| Raw sector value | Canonical ID | Classification | Registry basis |
|---|---|---|---|
| `AI` | `ai` | NORMALIZATION | T11 direct |
| `BIOTECH` | `biotech` | NORMALIZATION | T11 direct |
| `QUANTUM` | `quantum_computing` | NORMALIZATION | T11 direct |
| `CLEAN_TECH` | `new_energy` | SEMANTIC_MAPPING | T11 |
| `ADVANCED_MATERIALS` | `new_materials` | SEMANTIC_MAPPING | T11 |
| `OTHER` | `other` | NORMALIZATION | T11 direct |
| `人工智能` | `ai` | SYNONYM | registry alias |
| any other provided value | `unknown` | UNKNOWN | registry fallback |
| `ai_hardware` | `unknown` | UNKNOWN | T2 rule — stays UNKNOWN, never upgraded |
| sector key absent / `None` | `None` | — | prefer null over guess |

No duplicate mappings, no silent fallback, no UNKNOWN→OTHER conversion, no registry changes.

## 5. Architecture Decision (DESIGN → IMPLEMENTED)

**Additive integration**: keep `sector` untouched; add optional derived field `GraphNode.canonical_industry`.

- New `resolve_sector_canonical(sector)` helper in `evidence_graph.py`: `None` in → `None` out; everything else delegated to the registry. Import failures propagate (no hidden fallback).
- Lazy `_get_canonical_registry()` mirrors the P1-3.3 `policy_cleaner.py` pattern.
- `to_dict()`: `canonical_industry` serialized **only when not None** (sector-less nodes keep the byte-identical pre-P1-3.5 shape).
- `from_dict()`: stored value wins; legacy serializations recompute from `data["sector"]` when present.
- Not modified: `graph_query_engine.py`, `trust_service.py`, `evidence_object.py`, `trust_score.py`, `provenance.py`, `schema/canonical_taxonomy.py`, all data files, MCP/A2A surface.

## 6. Tests (VERIFIED)

New file: `tests/test_evidence_graph_taxonomy.py` (29 tests, TEST-EG-TAX-001..045; requires `git add -f` per existing `.gitignore` `test_*.py` governance).

Coverage:
1. Exact → canonical (AI/BIOTECH/QUANTUM) — VERIFIED
2. Synonym → canonical (人工智能 → ai) — VERIFIED
3. Normalization (lowercase `ai`; OTHER → other) — VERIFIED
4. Semantic mapping (CLEAN_TECH → new_energy; ADVANCED_MATERIALS → new_materials) — VERIFIED
5. Unknown → unknown (ai_hardware stays unknown) — VERIFIED
6. Invalid → unknown — VERIFIED
7. Missing sector → None (node and helper level) — VERIFIED
8. Deterministic resolution across instances — VERIFIED
9. Legacy `sector` never mutated — VERIFIED
10. Node serialization additive compat (omit when None; round-trip; legacy recompute; stored-wins) — VERIFIED
11. Graph serialization round-trip + legacy graph dict load — VERIFIED
12. EvidenceObject serialization unchanged (no sector/canonical keys) — VERIFIED
13. Service path: evidence node canonical_industry is None — VERIFIED
14. MOCK stays MOCK; UNVERIFIED stays UNVERIFIED; no auto-VERIFIED — VERIFIED
15. Legacy sector substring query (`find_company_evidence`) unchanged — VERIFIED

## 7. Runtime Coverage (honest accounting)

- **Runtime-level VERIFIED** (through real call paths): `add_node` with sector (AI, 人工智能, missing), `TrustEvidenceService.create_evidence` (canonical stays None because evidence data carries sector only in nested `metadata`), `find_company_evidence` legacy filter, graph serialization round-trips.
- **Unit-level only** (no runtime call site exists today): `BIOTECH`, `QUANTUM`, `CLEAN_TECH`, `ADVANCED_MATERIALS`, `OTHER`, `ai_hardware`, empty-string sector. These values are design-doc/registry-domain inputs; resolving them through `GraphNode` is covered, but no production code path currently feeds them into the graph. This is recorded, not claimed as runtime coverage.

## 8. Safety (VERIFIED)

- No fake government data; no fake verification; no VERIFIED escalation.
- MOCK remains MOCK; UNKNOWN remains UNKNOWN (incl. `ai_hardware`).
- No MCP/A2A implementation or claims introduced.
- No Trust scoring or Provenance semantics touched (their modules are byte-identical).
- No hidden fallback: the only fallback is the registry's explicit `"unknown"`; registry import failure raises.
- No silent guessing: missing sector → `None`.

## 9. Regression (VERIFIED)

- Before: 377 passed, 1 warning.
- New: +29 (TEST-EG-TAX).
- After: **406 passed, 0 failed, 1 warning** (same pre-existing warning).

## 10. Known Limitations

1. `canonical_industry` on service-created evidence nodes is always `None` today, because `EvidenceObject` has no sector field. Wiring evidence-level sectors is out of P1-3.5 scope (would touch Trust object model).
2. Five design-doc sector values remain unit-level-only (see §7).
3. `examples/trust_demo/company_example.json` is still not loaded by runtime; its `人工智能` value is exercised only via tests.
4. `canonical_industry` is a derived convenience field, not a new source of truth; `data["sector"]` remains the input of record.

## 11. Final Decision

P1-3.5 implemented as a minimal, additive, deterministic integration: **Evidence Graph sector is now deterministically aligned with the Canonical Taxonomy while legacy behavior is fully preserved**. Registry unchanged; Trust/Provenance/MOCK/UNVERIFIED semantics unchanged.

## 12. Next Quest

Per Master Handover (2026-08-30 edition): see "Next Quest" section — remaining OPTION B (canonical taxonomy integration into other policy processors) or P1-4 per handover planning. Not started in this quest.
