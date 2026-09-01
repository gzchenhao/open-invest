# P1-5 — Public Product / DX Audit (DESIGN ONLY)

**Date:** 2026-09-01
**Phase:** P1-5 Phase 0 (AUDIT + DESIGN ONLY)
**Status:** AUDIT COMPLETE — No production code changed
**Baseline:** P1-4.6 complete, 611 tests, commit `a0ad5dd`

---

## Current GitHub-Facing Reality

A stranger opening the repository today encounters:

1. **README (557 lines)** — long, internally-focused, reads like an engineering handover with marketing veneer. The first screen is badges + "USB-C for DeepTech" slogan + a long feature list mixing IMPLEMENTED/PROTOTYPE/PLANNED/UNVERIFIED statuses.
2. **Quick Start** — 4 steps (clone → install → server → client). Runnable, but produces a JSON-RPC server with mock data. No visible "wow" moment.
3. **A second demo** (`examples/trust_pipeline_demo.py`) that actually showcases the trust pipeline (Evidence → Provenance → Trust Score → Evidence Graph) — but this demo is **not mentioned anywhere in the README**.
4. **611 passing tests** — but README claims "68 passed" (stale by 543 tests; P1-4.x work invisible).
5. **38 docs/** files — a mix of positioning docs, audit docs, and P1-4.x acceptance reports. No index, no "start here."

### The Core Mismatch

The README markets the **old layer** (JSON-RPC protocol + policy crawler + web portal). The **real intellectual asset** — the P1-4.1→4.6 Verification Safety Chain (durable event log, human verification gate, content identity, automatic revocation, authority registry, fail-closed security) — is **invisible** to any GitHub visitor. A stranger cannot tell this project has a sophisticated, tested trust-verification system.

---

## First-5-Minute User Journey (Simulated)

| Time | What user does | What user sees | Problem |
|------|---------------|----------------|---------|
| 0:00 | Opens README | Badges, slogan, "experimental framework" | No one-sentence answer to "what is this?" |
| 0:30 | Scrolls to Core Value Proposition | 6 bullet points mixing real + planned | Cannot distinguish asset from aspiration |
| 1:00 | Tries Quick Start | `pip install`, `python main.py` | Starts a JSON-RPC server with mock data — no visible trust/verification output |
| 2:00 | Looks for demo | README mentions web portal at port 8017 | Different server, separate directory, separate start command — confusing |
| 3:00 | Opens `examples/` | Finds `trust_pipeline_demo.py` | **Not mentioned in README** — user may never find it |
| 4:00 | Runs trust demo | Sees Evidence → Provenance → Trust Score → Graph | **This is the real value** — but discovered by accident |
| 5:00 | Checks tests | README says "68 tests" | Actually 611 — README is stale, P1-4.x invisible |

**Verdict:** A motivated user *can* find value, but the path is accidental, not guided.

---

## Top 5 Blockers (P0 → P3)

### P0 — Stranger cannot understand "What is OpenInvest?" in 30 seconds
README leads with "USB-C for DeepTech" + "borderless investment protocol." This is **aspiration**, not the current reality. The current reality is: **a trust-evidence verification system with a deterministic taxonomy and fail-closed VERIFIED gate.** The README never says this.

### P1 — Runnable but no visible core value
Quick Start starts a JSON-RPC server (`server/main.py`) that returns mock policy data. This does **not** demonstrate the trust/verification chain. The one demo that does (`trust_pipeline_demo.py`) is unmentioned.

### P2 — The real asset is invisible
611 tests, P1-4.1→4.6 Verification Safety Chain, content identity, automatic revocation, authority registry, fail-closed authorization — **none of this appears in the README, Quick Start, or architecture overview.** A visitor sees the old protocol layer and assumes the project is a mock-data CRUD server.

### P3 — README reads like internal handover, not a product
Mixes marketing language ("Join the Revolution"), engineering caveats ("Reality Status Legend"), stale test counts, and contributor tables. No clean narrative arc: problem → solution → how it works → try it → roadmap.

---

## README Audit

| Section | Finding |
|---------|---------|
| Title/Hero | "Open Invest Protocol" + slogan. No one-sentence product definition. |
| Strategic Vision | "USB-C for DeepTech" repeated twice (lines 30 + 35). Redundant. |
| Current Status | "experimental framework" — stated but buried. |
| Core Value Proposition | 6 bullets mixing real/planned. Status legend helps but is overwhelming on first read. |
| Quick Start | Works but shows mock JSON-RPC, not trust pipeline. |
| Architecture Overview | ASCII diagram shows old 3-party model. No trust/verification layer shown. |
| Project Structure | Lists `policy_crawler/`, `global_policy_aggregator/` prominently. `src/trust/` not mentioned. |
| Testing | Claims "68 passed" — stale by 543 tests. P1-4.x invisible. |
| Web Interface | Marketed heavily (PDF portal, 12 policies). This is the *old* demo, not the trust system. |
| Roadmap | Missing entirely. |

---

## Quickstart Audit

**Current Quick Start:**
```
clone → pip install → cd server → python main.py → cd client → python main.py
```

**Problems:**
1. Starts JSON-RPC server — returns mock policy data, no trust/verification visible.
2. No `python examples/trust_pipeline_demo.py` in Quick Start.
3. No "expected output" shown.
4. No mention of `pytest tests/ -q` as a verification step (it's in Testing section but not Quick Start).
5. No single-command "see the core value" entrypoint.

---

## Demo Audit

| Demo | Location | Shows Core Value? | In README? |
|------|----------|-------------------|------------|
| `trust_pipeline_demo.py` | `examples/` | ✅ Yes — Evidence → Provenance → Trust Score → Graph | ❌ Not mentioned |
| `run_mock_agent_demo.py` | `examples/trust_demo/` | Partial — mock agent | ❌ Not mentioned |
| Web portal (port 8017) | `global_policy_aggregator/web/` | ❌ No — mock policy search + PDF | ✅ Marketed heavily |
| JSON-RPC server | `server/main.py` | ❌ No — mock policy CRUD | ✅ In Quick Start |

**The best demo (`trust_pipeline_demo.py`) is the least visible.** The most visible demo (web portal) shows the least core value.

---

## Architecture Communication Audit

**Current architecture diagram (README):** 3-party model (Innovators ↔ Protocol ↔ Capital/Gov) + crawler engine. This is the **product vision**, not the **technical architecture**.

**Missing:** No diagram of the actual trust/verification system:
```
Evidence Object → Provenance Chain → Trust Score → Evidence Graph
                                           ↓
                              Verification Event Log (JSONL, append-only)
                                           ↓
                              Human Verification Gate (10 conditions)
                                           ↓
                                  VERIFIED (or UNVERIFIED)
                                           ↓
                              Content Identity (SHA-256) → Change Detection → Revocation
                                           ↓
                              Authority Registry (config-driven, fail-closed)
```

This system exists, is tested (611 tests), and is the differentiator — but no visitor can see it.

---

## Trust / Verification Communication Audit

| Asset | Exists? | Tested? | In README? | In Architecture Doc? |
|-------|---------|---------|------------|---------------------|
| Durable Event Log (JSONL, append-only) | ✅ | ✅ | ❌ | ❌ |
| Human Verification Gate (10 conditions) | ✅ | ✅ | ❌ | ❌ |
| Content Identity (SHA-256) | ✅ | ✅ | ❌ | ❌ |
| Automatic VERIFIED Revocation | ✅ | ✅ | ❌ | ❌ |
| Human Authority Registry | ✅ | ✅ | ❌ | ❌ |
| Config-driven Registry (fail-closed) | ✅ | ✅ | ❌ | ❌ |
| Deterministic Canonical Taxonomy | ✅ | ✅ | ❌ | ❌ |
| Evidence Graph | ✅ | ✅ | ❌ (mentioned in project structure only) | ❌ |
| Provenance Chain | ✅ | ✅ | ❌ | ❌ |

**Every row above is invisible to a GitHub visitor.** This is the single biggest DX gap.

---

## Implemented vs Prototype vs Mock Matrix

| Component | Status | Notes |
|-----------|--------|-------|
| **JSON-RPC Server** | IMPLEMENTED | 25 endpoint tests, mock data |
| **Client CLI** | IMPLEMENTED | 17 tests, mock matching |
| **Canonical Taxonomy** | IMPLEMENTED | Deterministic, tested, integrated |
| **Evidence Object + Graph** | IMPLEMENTED | Tested, used in demo |
| **Provenance Chain** | IMPLEMENTED | Tested |
| **Trust Score Calculator** | IMPLEMENTED | Tested (formula not changed since P1-2) |
| **Verification Event Log** | IMPLEMENTED | Append-only JSONL, 28+ tests |
| **Human Verification Gate** | IMPLEMENTED | 10-condition gate, 29 tests |
| **Content Identity** | IMPLEMENTED | SHA-256, deterministic |
| **VERIFIED Revocation** | IMPLEMENTED | Auto-revoke on content change, 29 tests |
| **Authority Registry** | IMPLEMENTED | In-memory, 42 tests |
| **Config-driven Registry** | IMPLEMENTED | JSON config, fail-closed, 46 tests |
| **Policy Crawlers** | PROTOTYPE | Structure exists, data is mock/sample |
| **Web Portal (port 8017)** | PROTOTYPE | Mock policy search + PDF |
| **MCP / A2A** | PLANNED | No implementation |
| **Real Government Data** | NOT IMPLEMENTED | All data is mock/sample |
| **Authentication / OAuth / SSO** | NOT IMPLEMENTED | Explicitly out of scope |
| **Database** | NOT IMPLEMENTED | File-based (JSONL) only |

---

## Recommended P1-5 Roadmap (Design Only — Not Implemented)

### Phase P1-5.1: README Rewrite (P0 fix)
- Replace hero with one-sentence product definition: what it is, what it does, what it doesn't do.
- Add "Trust & Verification System" section surfacing P1-4.x assets.
- Add architecture diagram of the verification chain.
- Update test count (611, not 68).
- Remove redundant "USB-C" repetition.
- Add clear status matrix (implemented / prototype / mock / planned).

### Phase P1-5.2: Quick Start Rewrite (P1 fix)
- Make `trust_pipeline_demo.py` the primary Quick Start.
- Show expected output (Evidence → Provenance → Trust Score → Graph).
- Add `pytest tests/ -q` as step 2 (proof of tested system).
- Demote JSON-RPC server to "Advanced: Protocol Server."

### Phase P1-5.3: Verification Demo Enhancement (P2 fix)
- Extend `trust_pipeline_demo.py` to show: create evidence → human verification attempt → gate decision → content change → revocation → re-verification.
- Show fail-closed behavior (unknown verifier → denied).
- Output should make the security model tangible.

### Phase P1-5.4: Documentation Index (P3 fix)
- Create `docs/README.md` index: "Start here" → core thesis → architecture → verification chain → API.
- Categorize existing 38 docs into: product / architecture / audit reports / acceptance reports.

### Phase P1-5.5: Roadmap + Contribution Entry (P4)
- Add public roadmap (P1-4.x done → P1-5 DX → future).
- Clarify contribution entry points (tests, docs, demos — not verification semantics).

---

## GitHub Star / Fork Conversion Opportunities

1. **Lead with the differentiator:** "Fail-closed trust verification for policy evidence" is rare and valuable. Most open-source policy tools are CRUD. This project has a real security model.
2. **Show the security model working:** A 30-second demo of "VERIFIED denied because verifier not in registry" is compelling and honest.
3. **Test count as trust signal:** 611 tests on a prototype signals engineering seriousness. Currently invisible.
4. **Honest status labeling:** The existing IMPLEMENTED/PROTOTYPE/MOCK/PLANNED legend is good — surface it more prominently, not bury it.
5. **Architecture diagram:** A clean visual of the verification chain is shareable and differentiating.

---

## Non-Goals

- Fake demos, fake government data, fake verification, fake benchmarks
- MCP / A2A implementation
- Database / authentication / OAuth / SSO
- Complex frontend
- Crawler activation / real data pipeline
- Verification semantics changes
- Trust Score formula changes
- Taxonomy changes
- Production deployment claims

---

## Known Limitations

1. All policy data is mock/sample — no real government data in repository.
2. No real authentication — Authority Registry is application-level allowlist, not identity verification.
3. No database — EventLog is file-based (JSONL), Registry is in-memory (config-loaded).
4. No MCP/A2A — protocol layer is JSON-RPC only.
5. Web portal is a separate prototype, not integrated with trust/verification system.
6. README and docs are internally-oriented (handover reports, audit docs) — not yet public-product-grade.

---

## Summary Verdict

**P0 (critical):** Stranger cannot understand what OpenInvest is in 30 seconds. The real asset (verification safety chain) is invisible.

**P1 (high):** Quick Start runs but doesn't show core value. The demo that does show it is unmentioned.

**P2 (medium):** Even if found, the demo doesn't show the security model (gate, revocation, fail-closed).

**P3 (low):** README/docs are not yet shareable as public product artifacts.

**Recommended first action:** README rewrite + Quick Start pivot to `trust_pipeline_demo.py` + surface P1-4.x verification chain. This is the highest-leverage DX change with zero production code risk.

---

*No production code changed. DESIGN ONLY.*
