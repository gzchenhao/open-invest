# Real Policy Verification Workflow — Audit & Design (P1-4.0)

**Date**: 2026-08-31
**Quest**: P1-4.0 — Real Policy Verification Workflow Audit & Design
**Baseline**: commit `db5004e`, master, LOCAL == REMOTE, worktree clean, 406 passed / 0 failed / 1 warning

> **This document is DESIGN ONLY.** It does not implement a production verification workflow and does not upgrade any existing verification status. No production code, schema, seed data, mock data, tests, Trust semantics, Provenance semantics, or MCP/A2A status were modified by this quest.

---

## 1. Executive Summary

**AUDIT RESULT**: OpenInvest today has **no real policy verification workflow** — and, critically, **no code path anywhere in the repository that grants VERIFIED**. All policy data is MOCK. The "Policy → Evidence → Provenance → Verification → Trust" chain exists only as **two disconnected islands**: a Policy Intelligence island (crawler/cleaner/validator/seed data/web portal) and a Trust Prototype island (`src/trust/`), with no runtime bridge between them, and a third island (JSON-RPC `server/`) with zero trust coupling.

**DESIGN RESULT**: This document designs a minimal, safe, auditable Real Policy Verification Workflow for P1-4.1: a five-level Verification Authority Model (agent-assisted recommendation → human/authorized authority → VERIFIED), a conservative state machine (MOCK orthogonal; UNVERIFIED cannot jump to VERIFIED), an additive Verification Evidence Contract (no breaking schema changes), and a threat model with current protections and gaps.

**Most important safety finding**: the current system is trivially safe against false VERIFIED (nothing can produce it), but it also contains a **label-based implicit trust elevation** — a free-text `source` value of `"government"/"official"` raises the trust score and the "source_reliability" confidence factor with zero verification (see §6, Finding F-04). Any future verification workflow must close this, not build on top of it.

---

## 2. Scope

**In scope (AUDIT + DESIGN only)**:
- Audit of existing Policy → Evidence → Provenance → Verification → Trust reality
- Verification Authority Model (conceptual)
- Verification state machine (design)
- Verification evidence contract (field-level design)
- Provenance requirements
- Agent/human verification boundary
- Threat / abuse model
- Public-repo trust-communication review (README)

**Out of scope (Non-Goals, §17)**: production crawler activation, real government data fetch, MCP server, A2A protocol, UI redesign, database migration, taxonomy redesign, Trust Score redesign, schema migration, any enum/schema modification.

---

## 3. Current Repository Reality (AUDIT)

### 3.1 The actual chain — two disconnected islands

```
ISLAND 1: Policy Intelligence (lowercase "mock" vocabulary)
  crawlers/ (scaffolded; real HTTP capability + hardcoded real URLs,
             NOT wired into any runtime pipeline)
    → data/raw_policies/*.txt (sample text)
    → processors/policy_cleaner.py (parse/clean, canonical_industry)
    → processors/provenance_validator.py (label validation only)
    → data/seed_data/*.json (21 records, ALL is_mock=true, status "mock")
    → web portal (interactive_ai_server.py / fixed_server.py)

ISLAND 2: Trust Prototype (uppercase "MOCK" vocabulary)
  src/trust/evidence_object.py, evidence_graph.py, provenance.py,
  trust_score.py, trust_service.py, graph_query_engine.py
  — fed ONLY by mock demos (examples/trust_demo/), NEVER by Island 1

ISLAND 3: Protocol Server (server/main.py, JSON-RPC)
  — ZERO references to verification/trust/provenance/mock (grep: no matches)
```

**There is no runtime path from a PolicyRecord to an EvidenceObject.** The designed chain "Policy → Evidence → Provenance → Verification → Trust" is architecturally aspirational, not implemented.

### 3.2 Verification status vocabularies (three, divergent)

| Location | Values | Case |
|---|---|---|
| `src/trust/evidence_object.py:16` | UNVERIFIED, MOCK, VERIFIED, **REJECTED** | UPPERCASE |
| `global_policy_aggregator/processors/provenance_validator.py:28` | verified, **partially_verified**, unverified, mock | lowercase |
| Design docs (`OpenInvest_Trust_Object_Model.md`, `Trust_Score_Framework.md`, etc.) | PENDING, VERIFIED, REJECTED, OUTDATED | mixed |

No REJECTED in the policy island; no PARTIALLY_VERIFIED in the trust island; PENDING/OUTDATED exist only on paper.

### 3.3 Where VERIFIED could come from — answer: nowhere

- Repo-wide grep for code assigning `verification_status = VERIFIED/verified`: **0 hits** (only docs).
- `apply_provenance_governance.py:23` writes only `{"is_mock": True, "verification_status": "mock"}`.
- `provenance_validator.py` **validates** pre-existing labels (mock must not be verified; verified requires valid non-placeholder URL) — it never **grants** anything.
- `trust_service.py:173 verify_evidence()` supports **only** `method="mock"`, sets status to MOCK, message "not authoritative"; any other method → failure "Only mock verification is available".

**VERIFIED production path: NOT FOUND.**

### 3.4 Provenance reality

**Policy island** (`PolicyProvenance`, provenance_validator.py:58): fields exist for source_url / source_title / publisher / published_date / effective_date / retrieved_at / secondary_source_url / url_status / source_verification_status / contact — **all Optional, all null in current data** (fabricated URLs were nullified by TASK-P0-2 governance). No snapshot, no content hash, no content identity.

**Trust island** (`ProvenanceChain`, provenance.py): event-log with per-record sha256 — but **ephemeral**: `trust_service.py` instantiates a fresh `ProvenanceChain(evidence_id)` on every `get_evidence`/`verify_evidence`/`get_provenance`/`calculate_trust` call, so (a) the "create" record timestamp is always *now*, (b) verification events added in `verify_evidence` are written to a local object and **discarded**, (c) `verify_integrity()` is trivially True for a freshly generated chain. Provenance is **not persisted, not append-only, not immutable**.

**Consequence**: the system cannot currently answer *"why does OpenInvest believe this policy?"* with durable evidence — only with a regenerated placeholder chain.

### 3.5 DOCUMENTED vs IMPLEMENTED drift (Repository wins; handover corrected in P1-4.0)

| Handover §13.1/§8.1 claims | Actual `evidence_object.py` |
|---|---|
| fields `content: Dict`, `provenance: Dict` | do not exist (only free-form `metadata`) |
| `EvidenceType` enum POLICY/CONTACT/FINANCIAL/COMPLIANCE | `type` is a free string; no enum |
| VerificationStatus includes PARTIALLY_VERIFIED | has REJECTED instead; no PARTIALLY_VERIFIED |
| §13.2 snapshot + verification_method fields | not implemented anywhere |

### 3.6 Enforcement tests that DO exist (AUDIT, verified present)

`tests/test_provenance.py`, `test_trust_api_safety.py`, `test_trust_prototype_safety.py`, `test_ui_mock_disclosure.py`, `test_history_policy_rules.py` — mock labeling, no-escalation, disclosure rules are test-enforced.

---

## 4. Current Verification Status (AUDIT, PART 3 answers)

**A. Does a verification workflow exist?**
- status field exists: YES (two vocabularies, §3.2)
- validation function exists: YES (negative label validation only, §3.3)
- verification service exists: MOCK-ONLY (`verify_evidence` mock path, §3.3)
- runtime workflow exists: **NO**
- human confirmation mechanism: **NO**
- agent confirmation mechanism: **NO**

**B. VERIFIED production path**: **NOT FOUND** (§3.3).

**C. UNVERIFIED / MOCK production**: UNVERIFIED is the `EvidenceObject` default (evidence_object.py:38); service default input status is "MOCK" (trust_service.py:94); seed data "mock" written by governance script. Test-covered (§3.6).

**D. Dangerous implicit verification audit**:

| Candidate rule | Exists? | Evidence |
|---|---|---|
| source_url exists → VERIFIED | NO | validator explicitly separates `url_status` ≠ `source_verification_status` (provenance_validator.py:16-18) — GOOD |
| HTTP 200 → VERIFIED | NO | crawlers fetch pages but never set status |
| parser success → VERIFIED | NO | cleaner does not set status |
| government domain → VERIFIED | NO | no domain check anywhere |
| Agent response → VERIFIED | NO | no agent path; A2A/MCP not implemented |
| Evidence exists → VERIFIED | NO | |
| TrustScore high → VERIFIED | NO | no reverse path |
| **source LABEL "government"/"official" → high trust score + "high" source_reliability confidence factor** | **YES — FINDING F-04** | trust_score.py:39-45 (`government: 0.8`), trust_service.py:358-360 (`confidence_factors["source_reliability"]="high"`, reason "Source is government/official") |

**F-04 is not a VERIFIED escalation** (verification_status is untouched) but it **is trust elevation from an unverified free-text label** — any caller can pass `source="government"` to raise the score and the explanation. Recorded, not fixed (Trust module is protected; fix belongs to a dedicated safety quest).

---

## 5. Policy → Evidence → Provenance: Current Gaps (AUDIT)

1. **G-01 No bridge**: PolicyRecord never becomes an EvidenceObject at runtime (§3.1).
2. **G-02 Ephemeral provenance**: verification events are not persisted (§3.4).
3. **G-03 No content identity**: no snapshot/hash → cannot detect modified or stale sources.
4. **G-04 Vocabulary split**: two status enums + doc-only vocabulary (§3.2).
5. **G-05 Label-based source trust**: F-04 above.
6. **G-06 No verifier identity/timestamp/method**: nothing records WHO verified, WHEN, HOW.
7. **G-07 No re-verification trigger**: no mechanism to detect source change and demote stale VERIFIED.
8. **G-08 Doc drift**: handover §13 described a richer model than implemented (§3.5) — corrected in P1-4.0.
9. **G-09 Minor code defect**: `trust_request_response.py:235-236` stacked duplicate `@dataclass` decorator (harmless today) — recorded, not fixed (protected module, out of scope).
10. **G-10 README trust communication**: honest status legend exists, but README never explains the trust model / verification semantics / how to interpret a trust score (see §14).

---

## 6. Verification Authority Model (DESIGN)

Five levels; **each is necessary-but-insufficient for the next**; only L4 grants VERIFIED.

```
L1 SOURCE EXISTENCE     URL well-formed, reachable (url_status)          → never equals verified
L2 SOURCE AUTHENTICITY  domain genuinely belongs to the claimed
                        official publisher (allowlist + ownership check) → still not content proof
L3 CONTENT VERIFICATION fetched canonical text hash matches record;
                        title/date/publisher cross-check                 → strongest AUTOMATED level
L4 HUMAN / AUTHORIZED   named verifier with recorded identity,
   VERIFICATION         method, timestamp, in append-only log            → ONLY path to VERIFIED
L5 AGENT-ASSISTED       evidence extraction, candidate matching,
                        discrepancy detection, confidence + rationale   → ADVISORY ONLY
```

**Mandatory flow**:

```
Agent Recommendation (L5)
        ↓  (produces CANDIDATE + rationale, never VERIFIED)
Human / Authorized Verification Authority (L4)
        ↓  (records decision + identity + timestamp + evidence refs)
     VERIFIED
```

Repository has **no Human Verification Authority today** — recorded as a P1-4.1 design requirement, NOT implemented here.

---

## 7. Verification State Machine (DESIGN)

```
                ┌────────────────────────────────────────────┐
                │  is_mock = true  (orthogonal dimension)    │
                │  MOCK data NEVER enters this machine       │
                └────────────────────────────────────────────┘

 UNKNOWN ──(claim recorded)──► UNVERIFIED
 UNVERIFIED ──(L1-L3 automated pass OR agent proposal)──► CANDIDATE_REVIEW_REQUIRED
 CANDIDATE_REVIEW_REQUIRED ──(L4 human approval)──► VERIFIED
 CANDIDATE_REVIEW_REQUIRED ──(L4 human rejection)──► REJECTED
 VERIFIED ──(source content hash changed / recheck failed)──► CANDIDATE_REVIEW_REQUIRED (demotion)
 any ──(human rejection)──► REJECTED
```

Design decisions (all DESIGN, no enum changes in P1-4.0):

| Question | Decision | Rationale |
|---|---|---|
| Is MOCK a verification state? | **No — orthogonal `is_mock` flag** | current code mixes them; MOCK is data provenance, not verification progress |
| UNVERIFIED → VERIFIED directly? | **Forbidden** | must pass CANDIDATE + human authority; blocks all implicit escalation paths |
| REVIEW_REQUIRED needed? | **Yes, as CANDIDATE_REVIEW_REQUIRED** | gives agents/humans a safe intermediate; named to avoid ambiguity with generic "review" |
| Revocable? | **Yes — mandatory demotion on source change** | stale VERIFIED is a top threat (§13) |
| Verifier identity? | **Mandatory for VERIFIED** | G-06 |
| Timestamp? | **Mandatory** | enables staleness/decay decisions |
| Evidence reference? | **Mandatory (content hash + event id)** | G-03 |
| Existing enums? | **Unchanged in P1-4.0**; CANDIDATE_REVIEW_REQUIRED is a future ADDITIVE value; uppercase/lowercase reconciliation via read-only adapter, never enum rewrite | backward compatibility |

---

## 8. Verification Evidence Contract (DESIGN)

| Field | Status today | Future role | Schema change needed |
|---|---|---|---|
| policy_id | Existing (record id) | Required | none |
| source / publisher | Existing (`PolicyProvenance`) | Required | none |
| source_url | Existing field, **values null** (mock) | Required for L2+ | none |
| retrieved_at | Existing field, values null | Required | none |
| published_at (`published_date`) | Existing field, values null | Required | none |
| url_status | Existing (VALID_FORMAT etc.) | Required (L1 signal only) | none |
| content_identity (sha256 of canonical text) | **MISSING** | Required for L3/demotion | **additive optional field** |
| verification_status | Existing (two vocabularies) | Required | adapter only (no enum change) |
| verification_method | Documented only (§13.2 handover) — not implemented | Required | **additive** |
| verification_actor (verifier identity) | **MISSING** | Required for VERIFIED | **additive** |
| verification_timestamp | **MISSING** (provenance timestamps ephemeral) | Required for VERIFIED | **additive** |
| verification_evidence (event id + hash refs) | **MISSING** | Required | **additive** |
| verification_notes | MISSING | Optional | additive |

All future fields are **optional/additive** following the established `PolicyProvenance` all-optional pattern (backward-compatible with every existing payload, precedent TEST-PROVENANCE-006). No breaking API/schema change.

---

## 9. Provenance Requirements (DESIGN)

1. **Durable append-only event log** (e.g., JSONL) — replaces per-call ephemeral chains; one event per create/verify/demote/reject.
2. **Content identity**: sha256 of canonicalized policy text recorded at retrieval; re-fetch compares hashes → change triggers demotion (§7).
3. **Immutability**: events are append-only; corrections are new events, never edits. Integrity hash per event (existing ProvenanceRecord hash concept, made persistent).
4. **Answerability**: for any policy, the system must be able to answer: source URL + retrieval time + content hash + who verified + when + method + evidence refs.
5. **Separation preserved**: `url_status` (technical) never conflated with `source_verification_status` (truthfulness) — existing rule, kept.

---

## 10. Agent-Assisted vs Human Verification Boundary (DESIGN)

**Agent MAY**: fetch candidates, extract evidence, propose field mappings, compute content hashes, detect discrepancies between sources, attach confidence + rationale, mark CANDIDATE_REVIEW_REQUIRED.

**Agent MUST NOT**: write VERIFIED, modify verification events, alter trust scores on its own assertion, or convert its own output into verification evidence without a recorded human decision.

**Human/Authorized Authority (does not exist yet — design requirement)**: an identified operator (recorded identity string + method) whose decision event is the ONLY transition into VERIFIED. In a public-repo context this authority must be **explicitly configured and logged**, never inferred.

---

## 11. Threat / Abuse Model (AUDIT + DESIGN)

| # | Threat | Current Protection | Gap | Future Mitigation |
|---|---|---|---|---|
| T-01 | Fake source URL | placeholder-pattern checks; verified requires non-placeholder URL | nothing grants verified yet → trivially safe today, unsafe once workflow exists | L2 domain allowlist before CANDIDATE |
| T-02 | Spoofed official domain | none | full | registrar/suffix allowlist + manual domain registry |
| T-03 | Stale policy (source updated) | freshness decay in trust score only | no re-check | content hash re-verification + demotion (§7) |
| T-04 | Modified policy content | none | no content identity | sha256 content_identity (§9.2) |
| T-05 | Duplicate evidence | graph node ids dedupe by id only | no semantic dedupe | content hash + policy_id dedupe at ingest |
| T-06 | Contradictory sources | none | full | discrepancy detection as agent task; contradiction blocks CANDIDATE |
| T-07 | Agent hallucination | mock-only verify path refuses other methods | no agent path at all | agent output = recommendation only (§10) |
| T-08 | Automatic trust escalation | NO VERIFIED grant path exists (§3.3) | will appear with any workflow | state machine forbids UNVERIFIED→VERIFIED (§7) |
| T-09 | Human verification spoofing | n/a (no human path) | full | recorded verifier identity + append-only log; credentials out of scope for repo |
| T-10 | Provenance tampering | per-record sha256 exists but ephemeral | not persisted | durable append-only log + integrity hashes (§9) |
| T-11 | MOCK leaking into VERIFIED | validator blocks mock→verified labels; tests enforce | — (keep) | state machine excludes is_mock entirely (§7) |
| T-12 | Label-based trust ("government" string) | none — **F-04 live today** | trust score + explanation elevated by unverified label | source_reliability must key on verified provenance, not free text (dedicated quest) |

---

## 12. Trust Safety Rules (DESIGN, binding for P1-4.1)

1. VERIFIED is granted ONLY by a recorded L4 decision event. No code path may set it from HTTP status, parse success, domain match, agent output, or trust score.
2. MOCK is orthogonal and永久 excluded from the state machine; `is_mock=true` records can never hold VERIFIED.
3. Every VERIFIED must carry verifier identity, timestamp, method, and evidence references; missing any → CANDIDATE_REVIEW_REQUIRED at most.
4. Source content change demotes VERIFIED automatically.
5. Trust Score keeps consuming verification_status explicitly (current documented behavior) but must never feed back into status (no reverse path — already true today).
6. No silent fallback: unresolvable status → UNVERIFIED, never OTHER/VERIFIED.

---

## 13. Backward Compatibility (DESIGN)

- Existing enums, fields, seed data, mock markers: **unchanged**.
- All new fields optional/additive → every existing payload parses unchanged (PolicyProvenance precedent).
- Legacy consumers reading `verification_status` continue to work; adapter layer reads both vocabularies read-only.
- Existing tests (406) remain the regression baseline; P1-4.0 adds none.

---

## 14. Public Trust / Open-Source Quality Review (AUDIT, PART 10)

**Can a stranger understand "why is this policy trustworthy" from the repo today?** Partially:
- ✅ README carries an explicit Reality Status Legend (IMPLEMENTED/PROTOTYPE/PLANNED/UNVERIFIED), states "experimental framework", marks seed data as mock (12 records, 10 regions), explicitly says no MCP/A2A exists.
- ✅ Handover §17 mock rules are strict and test-enforced.
- ❌ README never explains the trust model, verification semantics, or how to interpret a trust score — a newcomer cannot learn "MOCK vs UNVERIFIED vs VERIFIED" from README alone.
- ❌ Trust scores are presented with reasons like "Source is government/official" (F-04) that read as verification but are label-based.
- ⚠️ `build-passing` badge has no CI evidence in-repo (minor).

**Recommendation (P1-4.1 documentation phase, not this quest)**: add a short "Trust & Verification Semantics" section to README; fix F-04 wording/weights in a dedicated safety quest.

---

## 15. Future Implementation Boundary (P1-4.1 plan)

- **Phase 1 — Durable verification event log** (append-only JSONL + VerificationDecision additive dataclass; no enum change; status vocabulary read-only adapter).
- **Phase 2 — Content identity** (sha256 canonical hash at ingest; change detector → demotion hook design).
- **Phase 3 — Human verification gate** (explicit verifier identity required; refuses is_mock; only CANDIDATE→VERIFIED; validator extended: verified label without matching decision event = governance violation).
- **Phase 4 — Agent-assisted candidate generator** (output = recommendation + rationale only).
- Each phase: tests first, audit trail, no Trust Score changes, no crawler activation, no real data.

## 16. Non-Goals

Production crawler activation; real government data fetch; MCP/A2A; UI redesign; DB migration; taxonomy redesign; Trust Score redesign; enum/schema modification; fixing F-04/G-09 (separate quests).

## 17. Known Limitations of THIS document

- DESIGN sections are unimplemented and untested by definition; nothing here may be cited as IMPLEMENTED.
- Threat model is qualitative; no quantitative risk scoring performed.
- Domain allowlist contents (which registrars/suffixes count as official) deliberately deferred — requires human policy decision, not agent guess.
- F-04 and G-09 remain live in code until their dedicated quests.

## 18. Final Decision

P1-4.0 concludes: the gap is **architectural (no bridge, no durable provenance, no authority model)**, not a missing checkmark. P1-4.1 must start from the **durable event log + additive contract** (Phase 1-2), because every other control (state machine enforcement, demotion, human gate) depends on persistence that does not exist today. VERIFIED must remain ungrantable until Phase 3 lands with the human authority requirement enforced by the provenance validator.

---

## Appendix: Evidence Index (file:line, AUDIT)

- `src/trust/evidence_object.py:16-21` — uppercase enum (no PARTIALLY_VERIFIED, has REJECTED); `:38` default UNVERIFIED
- `src/trust/trust_service.py:94` default "MOCK"; `:173-226` verify_evidence mock-only, sets MOCK, "not authoritative"; `:156,191,239,282` ephemeral ProvenanceChain; `:358-360` label-based "government/official" → high confidence factor
- `src/trust/trust_score.py:39-45` source_reliability_weights government 0.8 / official 0.7; `:126-134` VERIFIED 1.0 / MOCK 0.2 / UNVERIFIED 0.1
- `src/trust/provenance.py:96-104` chain created fresh with now-timestamp; `:117-126` add_verification_event (no persistence)
- `global_policy_aggregator/processors/provenance_validator.py:16-18` url_status ≠ source_verification_status; `:28-33` lowercase enum; `:117-192` label validation (no granting)
- `global_policy_aggregator/scripts/apply_provenance_governance.py:23` writes only mock
- `global_policy_aggregator/data/seed_data/*.json` — all records `is_mock: true`, `verification_status: "mock"`, source_url null
- `server/` — zero verification/trust/provenance references (grep verified)
- `src/trust/trust_request_response.py:235-236` — duplicate @dataclass decorator (G-09)
- Tests present: `tests/test_provenance.py`, `test_trust_api_safety.py`, `test_trust_prototype_safety.py`, `test_ui_mock_disclosure.py`, `test_history_policy_rules.py`
