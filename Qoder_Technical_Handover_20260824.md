# OpenInvest — AI Handover Constitution

**Document**: `Qoder_Technical_Handover_20260824.md`
**Purpose**: Immutable AI handover constitution. Any future AI coding agent must read and obey this document before touching the repository.
**Created**: 2026-08-24
**Repository**: https://github.com/gzchenhao/open-invest.git (branch `master`)
**Precedence (highest → lowest)**:
1. Existing Code & Data
2. Existing Schema / Protocol
3. Existing Tests
4. Current Repository Reality
5. Handover Constitution
6. New Requirements

> **Reading rule**: If any number, path, or status in this document disagrees with the repository, the repository wins. This document records the *Verified Reality* and the *Expected Baseline* difference rather than rewriting business data.

---

## 1. PROJECT IDENTITY & VISION

### 1.1 Project Positioning
OpenInvest is an open protocol for **global DeepTech investment and cross-border industrial landing**. The ambition is to become the **"USB-C / TCP/IP"** of the DeepTech world — a universal, standardized, plug-and-play layer connecting technology supply with government/capital demand.

```
DeepTech Project / Company
          │
          │   OpenInvest Protocol
          ▼
Government / Industrial Park / Capital Ecosystem
```

### 1.2 Server (High-Tech Project Side)
The Server represents high-tech project owners. Core guarantees:
- **Data de-sensitization / anonymization** — core IP never leaves the owner's domain
- **Trust proof** — structured, verifiable readiness signals
- **Protocol Contract** — JSON-RPC 2.0 methods
- **Data sovereignty** — tiered access control
- **No leakage of core commercial secrets**

### 1.3 Client (Government / Park / Capital Side)
The Client represents governments, industrial parks, and industrial capital. Capabilities:
- Consume structured trust information from the Server
- Agentic conversation
- Project ↔ policy matching
- Industrial investment promotion (招商)

### 1.4 Cold-Start Strategy
The platform bootstraps through **Policy Intelligence** as the bait pool:

```
Policy Intelligence
        ↓
Data-Led Growth
        ↓
Attract DeepTech Users
        ↓
AI Agent Direct Apply / Matching
        ↓
Claim OpenInvest Server
        ↓
A2A / MCP Protocol Network
        ↓
Two-sided Network Effect
```

---

## 2. CURRENT TRUTH / SINGLE SOURCE OF TRUTH

This chapter is the primary reference for any future agent judging project facts. Each item records **Expected Baseline**, **Verified Reality**, and the **Difference**. All figures below were verified against actual code/data on 2026-08-24 (see Appendix A).

### 2.1 Crawler Coverage
- **Definition**: Chinese mainstream hard-tech industrial clusters that the crawler / policy-intelligence system *plans or already covers*.
- **Expected Baseline**: 12 regions
- **Verified Reality**: **No single crawler defines 12 regions.** Actual per-file counts:

| Crawler file | Region/cluster definitions |
|---|---|
| `global_policy_aggregator/crawlers/china_tech_cluster_crawler.py` | **6** clusters (北京中关村, 上海张江, 深圳高新区, 广州高新区, 苏州工业园区, 合肥高新区) |
| `global_policy_aggregator/crawlers/china_tech_hub_crawler.py` | **10** parks / **6** provinces |
| `global_policy_aggregator/crawlers/china_tech_park_crawler.py` | **10** parks / **6** provinces |
| `global_policy_aggregator/crawlers/china_policy_crawler.py` | **5** parks |

- **Difference**: Expected `12` vs Verified `6–10` (depending on which file/granularity). The "12 regions" figure does **not** correspond to any single crawler configuration. It aligns instead with the **Web server's in-memory dataset** (see 2.3). **Do not alter crawler data to force 12.**

### 2.2 Seed Data Coverage
- **Definition**: Regions that actually have policy data present in the Mock / Seed dataset.
- **Expected Baseline**: 10 regions
- **Verified Reality**:
  - `global_policy_aggregator/data/seed_data/china_policy_seed_data.json` → **12 records / 10 regions** ✅ MATCHES
  - `global_policy_aggregator/data/seed_data/detailed_china_tech_policies.json` → **9 records / 9 regions**
- **Difference**: Matches for `china_policy_seed_data.json`. Do **not** state "12 regions of real policy data have been built" — the seed set covers 10 regions.

### 2.3 Actual Policy Records
- **Expected Baseline**: 12 records
- **Verified Reality**: `global_policy_aggregator/web/interactive_ai_server.py` holds an in-memory `policies` list with **12 records** (ids `1`–`12`). ✅ MATCHES
- **Note**: These 12 records are **Mock / seed data**, not crawled real policy documents. They must remain identifiable as mock (see INV-004).

### 2.4 Industry Taxonomy
- **Definition**: The industry classification system. 8 categories is a *taxonomy*, not a claim that every category has rich real policy data.
- **Expected Baseline**: 8 categories
- **Verified Reality**: Multiple taxonomies coexist. They are **not** all "8":

| Source | Count | Values |
|---|---|---|
| `PolicyCleaner.industry_mapping` effective output | **8** | `ai, robotics, quantum_computing, biotech, autonomous_driving, blockchain, vr_ar, other` |
| `schema/types.py` `IndustryType` enum | **5** | `autonomous_driving, embodied_ai, robotics, ai_hardware, quantum_computing` |
| `deeptech_policy_schema.json` industry `enum` | **21** | `ai_ml, robotics, quantum_computing, biotech, fintech, cleantech, aerospace, semiconductor, blockchain, vr_ar, nanotech, space_tech, embodied_ai, autonomous_driving, cybersecurity, iot, 5g, edge_computing, metaverse, web3, digital_twin` |
| Web server in-memory data | **12** | AI, 生物科技, 半导体, 新材料, 新能源, 金融科技, 区块链, 自动驾驶, 航空航天, 量子计算, 纳米技术, 高端装备 |

- **Difference**: The "8 categories" baseline matches the **PolicyCleaner normalization taxonomy** (8 distinct output values). It does **not** match `types.py` (5) or `deeptech_policy_schema.json` (21). **These taxonomies are currently inconsistent — an open gap, not something to silently unify.**

### 2.5 Tech Stack (Verified Status)
Verified against `requirements.txt`, imports, and code presence. Status legend: `Implemented` / `Partially Implemented` / `Scaffolded` / `MCP-ready` / `Planned`.

| Component | Status | Evidence |
|---|---|---|
| Python | Implemented | repo-wide |
| FastAPI | Implemented | `server/main.py`, `global_policy_aggregator/web/interactive_ai_server.py` |
| JSON-RPC 2.0 endpoint (`/rpc`) | Implemented | `server/main.py` `@app.post("/rpc")` |
| SQLite storage | Implemented | `policy_database.db`, `data/seed_data/policy_database.db` |
| JSON-Schema validation | Partially Implemented | `policy_cleaner.py` uses `jsonschema`, but validation is **non-blocking** (logs warnings only) |
| PDF generation | Implemented | `/api/policy/{id}/pdf` via `fpdf2` |
| Policy crawler engine | Scaffolded | crawler classes exist; target URLs are placeholder gov domains, **no verified live crawl output** |
| MCP server | **Planned / Not present** | **No MCP code found anywhere** |
| A2A gateway | **Planned / Not present** | **No A2A code found anywhere** |
| `policy_intelligence_service.py` | **Missing** | Referenced in README project tree but **does not exist** in `server/services/` |
| `a2a_protocol_handler.py` | **Missing** | Referenced in README project tree but **does not exist** |

> **Discrepancy note**: README.md advertises "A2A Ready / MCP" and lists `policy_intelligence_service.py` + `a2a_protocol_handler.py` under `server/`. None of these exist as code. Treat them as **Planned**, not Implemented.

---

## 3. NON-NEGOTIABLE INVARIANTS

This is the OpenInvest **AI Constitution**. Any agent taking over the project must obey these first.

### INV-000 — Preservation First
Without explicit user authorization, **never** delete, overwrite, or refactor existing core content (industry data, Robotaxi data, Schema, Protocol definitions, APIs, parsers, historical datasets, documentation). Only **CREATE / DOCUMENT / VERIFY / UPDATE Handover** are permitted for a governance quest. Allowed: `extend`, `append`, `deprecate`, `version`, `migrate`. Forbidden: `silent delete`, `silent overwrite`, `silent replacement`.

### INV-001 — No Destructive Modification
Existing content MUST be preserved unless explicit deletion authorization is provided. This rule exists because a prior model once **deleted Robotaxi content** while "adding new industries" (see Incident #001).

### INV-002 — Schema Compatibility
Any Schema modification must be (A) backward-compatible, or (B) accompanied by an explicit migration. Breaking changes must record: Old Schema, New Schema, Migration Strategy, Affected Components, Compatibility Impact. Do **not** silently drop existing fields.

### INV-003 — Provenance Preservation
Policy data must retain source information. Checked fields vs current reality:

| Field | Present in web server data? | Present in cleaner metadata? |
|---|---|---|
| `source_url` | ✅ (12/12) | ✅ |
| `issue_date` | ✅ (12/12) | — |
| `valid_period` | ✅ (12/12) | — |
| `source_title` | ❌ Missing | ❌ |
| `published_date` | ❌ Missing | ❌ |
| `effective_date` | ❌ Missing | ❌ |
| `retrieved_at` | ❌ Missing | ⚠️ `processing_timestamp` / `last_updated` only |
| `confidence` | ❌ Missing (record level) | ✅ `confidence_score` in metadata |
| `is_mock` | ❌ Missing | ❌ |

- **Current Implementation**: `source_url`, `issue_date`, `valid_period` (record level); `source_url` + `confidence_score` (cleaner metadata).
- **Missing Fields**: `source_title`, `published_date`, `effective_date`, `retrieved_at` (record level), `confidence` (record level), `is_mock`.
- **Recommended Future Improvement**: Add `is_mock`, `retrieved_at`, `confidence` at record level. **Do not fabricate these fields to satisfy this document.**

### INV-004 — No Fabricated Policy Data
AI must not fabricate government subsidies, commitments, amounts, application conditions, projects, incentives, or government contact details. Mock/seed data must be clearly identifiable.
- **Current mechanism**: The 12 web-server records and `seed_data/*.json` are mock, but there is **no explicit `is_mock` flag**.
- **Recommended Invariant**: Add `is_mock = true` to mock records.
- **Implementation Gap**: `is_mock` does not exist in the current schema.
- **Future Task**: Introduce `is_mock` without breaking the schema (per INV-002). **Do not silently modify the business schema to satisfy this quest.**

### INV-005 — Evidence Over Assertion
No task is "done" because an agent says so. Every task must provide Code Evidence, Test Evidence, Git Evidence, and Runtime Evidence where applicable.

### INV-006 — Handover Must Reflect Reality
The handover is not marketing. If README says A, code says B, and database says C: record the discrepancy, identify the source of truth, and recommend a resolution — never pick the "best-looking" answer.

### INV-007 — Data Integrity (Policy Provenance & Anti-Hallucination)
Added by TASK-P0-2 (2026-08-24). Highest discipline: **宁可 null，不要猜。宁可 UNVERIFIED，不要 VERIFIED。宁可少一条政策，不要多一条假的政策。**

- **[DATA-INTEGRITY-001] No Fabricated Government Information** — AI must never guess, complete, infer, generate, or fabricate government phones, emails, contact names, mobile numbers, subsidy amounts, validity periods, application conditions, official URLs, PDF URLs, publish/effective dates, park addresses, or “最高补贴 XX 万元” figures.
- **[DATA-INTEGRITY-002] Every Policy Must Have Provenance** — a real policy must trace to `source_url` / `source_title` / `publisher` / `published_date` / `effective_date` / `retrieved_at`. Official sources only (government portal → department → agency → park → official platform). Third-party sites may only be recorded as `secondary_source_url`.
- **[DATA-INTEGRITY-003] Every Contact Must Be Verifiable** — contact details must come from an official published page and carry `contact_source_url` (or per-field `phone_source_url` / `email_source_url`); otherwise `contact_status = "unverified"` and unknown fields stay `null`.
- **[DATA-INTEGRITY-004] Unknown Information Must Remain Unknown** — unconfirmable values stay `null` (`contact_name`/`phone`/`email`/`effective_date`/`confidence`). Never invent plausible-looking placeholders.
- **[DATA-INTEGRITY-005] Mock Data Must Never Resemble Verified Government Data Without Explicit Labeling** — mock records must carry `is_mock: true` + `verification_status: "mock"`, and must never be marked `verified` / `official` / `government_confirmed`. Fabricated `source_url` for mock data must be `null`, not invented.

**Verification Status Enum**: `verified` / `partially_verified` / `unverified` / `mock`.
**Key separation**: `url_status` (technical reachability) ≠ `source_verification_status` (authenticity). HTTP 200 never implies a source is official. Enforcement: `global_policy_aggregator/processors/provenance_validator.py`; regression tests: `tests/test_provenance.py` (TEST-PROVENANCE-001..006).

---

## 4. HISTORICAL INSTITUTIONAL MEMORY

### Incident #001 — Robotaxi Deletion
- **Incident**: A historical model, while adding new industry content, mistakenly **deleted existing Robotaxi content**.
- **Root Cause**: The model interpreted "add new industries" as "refactor the existing industry dataset".
- **Permanent Rule**: Existing industry datasets are protected assets. Future models may only **add, extend, version, or explicitly deprecate** — never silently delete.

### Incident #002 — Government Intermediary Trap
- **Risk**: OpenInvest must **not** degenerate into a digitized version of a traditional government-investment intermediary.
- **Forbidden pattern**:
  ```
  Project → Intermediary → Government
  ```
- **Required pattern**:
  ```
  Project ↔ OpenInvest Protocol ↔ Government / Park / Capital
  ```
- **Principle**: Connect directly via protocol, data, and agents — do not depend on a traditional intermediary to relay information.

---

## 5. PARSER & DATA CONTRACT

Full chain (verified against actual code):

```
Crawler → Raw Data → Parser/Normalizer (PolicyCleaner) → Validator (jsonschema)
        → Canonical Schema (StructuredPolicy) → Database / API / Client / Agent
```

### 5.1 Parser Location
- **File**: `global_policy_aggregator/processors/policy_cleaner.py`
- **Class**: `PolicyCleaner`
- **Core method**: `clean_policy_text(raw_policy_text: str, source_url: str = None) -> StructuredPolicy`
- **Output dataclass**: `StructuredPolicy` (same file)
- **Sibling processors**: `data_structurer.py`, `intelligence_aggregator.py`, `policy_structurer.py` (in `policy_crawler/processors/`)
- There is **not** a single module named literally `policy_crawler/` — the concrete files above are the real parser layer.

### 5.2 Input Contract
`clean_policy_text` accepts:
- `raw_policy_text`: **Raw Text** (string). In practice this is the text/HTML extracted by crawlers.
- `source_url`: optional URL string.
- The cleaner does **not** natively accept PDF or JSON as input; it operates on extracted text. Crawlers fetch **URL → HTML → text** then pass text to the cleaner.

### 5.3 Normalization Contract
Implemented inside `PolicyCleaner`:
- **Industry standardization**: `industry_mapping` (10 CN keys → 8 distinct EN values; unmapped → `other`)
- **Policy-type standardization**: `policy_type_mapping` (8 types: `tax_break, subsidy, land_grant, grant, loan, guarantee, training_grant, rtp_credit`)
- **Country/region standardization**: `country_mapping` (10 countries → ISO codes)
- **Amount handling**: `_extract_amount` (万/亿/美元/USD → numeric, with unit scaling)
- **Percentage handling**: `_extract_percentage`
- **Date handling**: `_extract_validity_period` (`YYYY年M月`, `YYYY-MM-DD`, `YYYY/M/D`)
- **Text cleaning**: regex-based extraction; title via `《…》`; location via region patterns
- **HTML cleaning**: delegated to crawlers (BeautifulSoup), not in the cleaner itself

### 5.4 Validation Contract
- **Mechanism**: `_validate_policy` uses `jsonschema.validate` against `incentive_schema.json`, `requirement_schema.json`, `compliance_schema.json`.
- **Important behavior**: Validation is **non-blocking** — on `ValidationError` it only `logger.warning`; the policy is still returned.
- **Required fields**: `StructuredPolicy` dataclass fields are all required by construction, but values may be empty strings (e.g., `location` can be `""`).
- **Duplicate handling**: **None implemented** (no dedup logic found).
- **Missing-data handling**: Falls back to empty string / `"other"` defaults.

### 5.5 Output Contract
- **Output**: `StructuredPolicy` →
  `policy_id, location, country, region, industry, policy_type, title, description, incentives[], requirements[], compliance_standards[], metadata{}`
- **metadata**: `source_url, last_updated, confidence_score, data_quality="estimated", raw_text_length, processing_timestamp`
- **Layer chain**: `Input(raw text) → Parser(PolicyCleaner) → Normalizer(mappings) → Validator(jsonschema, non-blocking) → Schema(StructuredPolicy) → DB/API`

---

## 6. CURRENT ARCHITECTURE & FILE MAP

Verified against the actual repository tree (2026-08-24).

| Path | Purpose | Status | Evidence |
|---|---|---|---|
| `server/main.py` | Protocol Server entry; single `/rpc` JSON-RPC 2.0 endpoint | Implemented | `@app.post("/rpc")`, FastAPI app |
| `server/config/config.py` | Server configuration | Implemented | present |
| `server/services/tech_readiness_service.py` | `get_tech_readiness` | Implemented | imported by main.py |
| `server/services/landing_requirements_service.py` | `get_landing_requirements` | Implemented | imported by main.py |
| `server/services/economic_compliance_service.py` | `get_economic_and_compliance` | Implemented | imported by main.py |
| `server/services/data_protection.py` | Tiered data protection | Implemented | present |
| `server/services/data_storage.py` | Storage layer | Implemented | present |
| `client/main.py` | Client entry | Implemented | present |
| `client/api/protocol_client.py` | Protocol API client | Implemented | present |
| `client/hooks/ai_agent_direct_apply.py` | AI Agent Direct Apply hook | Implemented | present |
| `client/utils/project_evaluator.py` | Project evaluation | Implemented | present |
| `schema/api-spec.json` | OpenAPI spec | Implemented | present |
| `schema/types.py` | Protocol data types (JSON-RPC, `IndustryType`) | Implemented | present |
| `schema/policy-schema.json` | Global policy schema | **Missing** | Referenced in README but **not present** (only `api-spec.json`, `types.py`) |
| `policy_crawler/` | Original global crawler + schemas + sample data | Implemented/Scaffolded | present (china, eu, silicon_valley, singapore) |
| `global_policy_aggregator/crawlers/*` | China-focused cluster/hub/park crawlers | Scaffolded | present; placeholder URLs |
| `global_policy_aggregator/processors/policy_cleaner.py` | Parser/Normalizer/Validator | Implemented | see §5 |
| `global_policy_aggregator/schemas/*.json` | incentive / requirement / compliance / deeptech schemas | Implemented | present |
| `global_policy_aggregator/web/interactive_ai_server.py` | Web portal + PDF + 12 mock policies | Implemented | runs on `:8017` |
| `global_policy_aggregator/services/data_cleaning_service.py` | Cleaning service | Implemented | present |
| `tests/server`, `tests/client`, `tests/integration` | Test suite | **Broken at collection** | `ModuleNotFoundError: services` |

> **Naming/structure note**: The README project tree lists several files (`policy_intelligence_service.py`, `a2a_protocol_handler.py`, `schema/policy-schema.json`) that do **not** exist. Do not assume functionality from directory names.

---

## 7. VERIFICATION EVIDENCE

### 7.1 Current Verification Record
- **Task**: Establish AI Handover Constitution
- **Date**: 2026-08-24
- **Files Changed**: `Qoder_Technical_Handover_20260824.md` (created); no business code modified
- **Tests**:
  - `python -m pytest tests/ -q` → **FAILS at collection**: `ModuleNotFoundError: No module named 'services'` (import-path issue when run from repo root). This is a pre-existing Testing Gap, not introduced here.
  - `python global_policy_aggregator/processors/policy_cleaner.py` → **RUNS OK** (self-test). Runtime evidence: `policy_id="unknown_ai_tax_break_20260824"`, `incentives_count=3`, `requirements_count=1`, `compliance_count=0`, `location=""` (empty — a known normalization gap).
- **Commands**:
  - `git status` / `git branch --show-current` / `git remote -v` / `git log -5 --oneline` / `git ls-files`
  - Data audit via read-only Python scripts (crawler region counts, seed-data region counts, policy-record count, provenance-field scan, industry-enum scan)
- **Result**: See §2 for all verified numbers and discrepancies.
- **Commit**: (filled in §7.3 after commit)
- **Push**: (filled in §7.3 after push)

### 7.2 Future Task Evidence Contract
Every future Quest must append a block:
```
### TASK-XXXX
Task Description: ...
Files Changed: ...
Implementation: ...
Test Command: ...
Test Result: ...
Coverage: ...
Commit Hash: ...
Push Result: ...
Verified At: ...
```
If there is no evidence, the task **must not** be marked DONE.

### 7.3 This Quest Git Evidence
- **Commit Hash**: `580ace39086301cb399dd5625d53e7ec9652055a` (the commit that introduced this document)
- **Commit Message**: `docs: establish the immutable AI handover constitution and fix data taxonomy`
- **Push Result**: SUCCESS — `01ba935..580ace3  master -> master` to `origin` (https://github.com/gzchenhao/open-invest.git)
- **Worktree after push**: CLEAN (only pre-existing untracked `test_*.ps1` remain untracked by design)
- **Verification**: `git rev-parse HEAD` == pushed commit; `git branch --show-current` == `master`; `git status` up to date with `origin/master`

---

## 8. NEXT TASKS & ROADMAP

Built from actual code state. Legend: Priority (P0 highest), Status, Dependencies, Recommended Next Action.

### P0 — Governance
| Item | Status | Recommended Next Action |
|---|---|---|
| Handover Constitution | **Done (this doc)** | Keep it current after every Quest |
| Schema/Data Contract | Partially Implemented | Reconcile the 4 industry taxonomies (8/5/21/12) |
| Evidence System | Scaffolded (§7.2) | Enforce evidence block on every PR |
| Data Provenance | Partially Implemented | Add `source_title`, `retrieved_at`, `confidence` at record level |
| Regression Protection | **Gap** | Fix test-suite import path so `pytest tests/` collects |

### P1 — Protocol
| Item | Status | Recommended Next Action |
|---|---|---|
| OpenInvest Protocol (`/rpc`) | Implemented | Harden error handling |
| A2A Gateway | **Planned / absent** | Design before implementing |
| MCP Server | **Planned / absent** | Design before implementing |
| Agent-to-Agent communication | **Planned / absent** | — |
| Authentication / Trust Layer | Partially Implemented (data_protection) | Formalize trust proofs |

### P2 — Data
| Item | Status | Recommended Next Action |
|---|---|---|
| Expand policy crawler | Scaffolded | Replace placeholder URLs; verify live crawl |
| Improve Parser/Normalizer | Implemented | Fix empty `location` extraction |
| Validator | Non-blocking | Decide blocking vs. warning policy |
| Deduplication | **Gap** | Add dedup stage |
| Provenance | Partially Implemented | See P0 |
| Policy freshness | **Gap** | Add `retrieved_at`/TTL |

### P3 — Product
| Item | Status | Recommended Next Action |
|---|---|---|
| Government/Park Client | Scaffolded | — |
| DeepTech Server | Implemented (`/rpc`) | — |
| Agentic Conversation | Scaffolded (`ai_agent_interface.py`) | — |
| Policy/Project Matching | Partially Implemented | — |
| AI Agent Direct Apply | Implemented (`client/hooks/`) | — |

### P4 — Growth
| Item | Status | Recommended Next Action |
|---|---|---|
| Data-Led Growth | Conceptual | — |
| Policy Intelligence Portal | Implemented (web) | — |
| Government/Park Claim | Implemented (claim hook) | — |
| Project Claim | **Gap** | — |
| Two-sided Network Effect | Conceptual | — |

### P5 — UX
| Item | Status | Recommended Next Action |
|---|---|---|
| Frontend Dashboard | Implemented (web portal) | — |
| Government/Project Dashboards | **Gap** | — |
| Visualization / Matching interface | **Gap** | — |

> Do **not** invent features to make this roadmap look richer. Statuses above reflect verified code.

---

## APPENDIX A — Repository Audit

Executed 2026-08-24, read-only.

- **Branch**: `master`
- **Remote**: `origin → https://github.com/gzchenhao/open-invest.git`
- **Latest commit (before this quest)**: `01ba935d8af1781bf6bf181d8b08c76f950bac32` — "feat: v3.1.0 - Web Portal, PDF Generation, Contact Info & Claim System"
- **Working tree status (before this quest)**: clean except 7 untracked files: `global_policy_aggregator/test_api_simple.ps1`, `test_chinese.ps1`, `test_debug.ps1`, `test_debug_fixed.ps1`, `test_english_keywords.ps1`, `test_final_search.ps1`, `test_simple_debug.ps1` (left untracked on purpose).
- **Tracked files**: 128 (`git ls-files`)
- **Relevant directories**: `client/`, `server/`, `schema/`, `tests/`, `docs/`, `policy_crawler/`, `global_policy_aggregator/`, `marketing/`
- **Existing documentation**:
  - Repo root: `README.md`, `PROJECT_SUMMARY.md`, `PROJECT_COMPLETION_REPORT.md`, `CHINA_QUEST_COMPLETION_REPORT.md`, `CONTRIBUTING.md` — all present in repo
  - Workspace root (`C:\OpenInvest`, outside git): `Qoder_Technical_Handover_20260822.md` (previous handover)
- **Tests**: `tests/server/test_server.py`, `tests/client/test_client.py`, `tests/integration/test_integration.py` (all fail at collection — see §7.1)
- **Audit method**: read-only Python scripts scanning crawler configs, seed JSON, web-server policy list, provenance fields, and industry enums. No business file was modified.

## APPENDIX B — Known Gaps

**Implementation Gap**
- MCP and A2A: advertised in README, **zero code present**.
- `server/services/policy_intelligence_service.py`, `a2a_protocol_handler.py`: referenced in README, **missing**.
- Crawler region counts (6/10/5) do not match the "12 regions" baseline.
- No `is_mock` flag on mock/seed data.
- No deduplication stage in the data pipeline.
- Validator is non-blocking (warnings only).

**Documentation Gap**
- README claims files and features that do not exist (policy_intelligence_service, a2a_protocol_handler, schema/policy-schema.json, A2A/MCP readiness).
- Multiple inconsistent industry taxonomies are undocumented.

**Data Gap**
- Provenance fields missing at record level: `source_title`, `published_date`, `effective_date`, `retrieved_at`, `confidence`.
- `location` extraction returns empty in the cleaner self-test.
- Seed data (10 regions) vs server data (12 regions) vs crawlers (6–10) are not aligned.

**Testing Gap**
- `pytest tests/` fails at **collection** due to `ModuleNotFoundError: services` (import path). No coverage currently measurable.
- Only `policy_cleaner.py` self-test provides runtime evidence.

**Protocol Gap**
- `schema/policy-schema.json` missing (README references it).
- Industry taxonomy mismatch across `types.py` (5), cleaner (8), `deeptech_policy_schema.json` (21).

**Security Gap**
- CORS is `allow_origins=["*"]` in `server/main.py` (acceptable for local/dev, must be locked down for production).
- No authentication layer on the `/rpc` endpoint.

---

## TASK-P0-1

### Repository Reality Alignment + Test Gate Repair

**Task Description**: Re-establish a trustworthy relationship between README claims, actual code state, and the test system; repair the pytest collection failure and establish `python -m pytest tests/ -q` as the permanent regression gate. No new business features; no MCP/A2A development; no crawler expansion; no business data or Schema deletion.

**Verified At**: 2026-08-24

### Repository Reality Findings

1. **pytest collection failure root cause**: the repository had **zero `__init__.py` files**; tests imported `services.*` / `client.*` while the working directory was repo root, so neither top-level package nor relative imports (`..api` in `client/utils/project_evaluator.py`) could resolve.
2. **README listed 10+ non-existent files** as implemented (`a2a_protocol_handler.py`, `policy_intelligence_service.py`, `policy_matcher.py`, `schema/policy-schema.json`, `tests/policy/`, `tests/performance/`, `docker-compose.yml`, ...). Many files the README attributed to `global_policy_aggregator/` actually live under `policy_crawler/` (china/eu/silicon_valley/singapore crawlers, data_structurer, intelligence_aggregator).
3. **MCP/A2A code = zero occurrences repository-wide** → must stay PLANNED.
4. **Test-code drift**: 7 sync methods wrapped in `asyncio.run`, 2 dict-style `in` assertions on pydantic models, mock fixtures contradicting real 3-sample project data, JSON-RPC error codes not spec-compliant (no -32700/-32600), protocol layer returning pydantic objects unserialized (`result=None` at runtime), missing `industry`/`name` passthrough needed by client evaluator.

### README Changes (Reality Alignment)

**README Claims Corrected / Downgraded**:
- "A2A Ready / Native support for MCP/A2A" → **PLANNED** (no implementation exists).
- "500+ global tech hubs" → **PROTOTYPE**: current seed coverage 12 policy records / 10 regions.
- "10,000+ concurrent, sub-100ms" → **UNVERIFIED benchmark goals** (no load-test evidence).
- "secure multi-tier gateway / 3.1 implementation" → tiered-CORS gateway **PROTOTYPE**; full auth **not implemented**.
- "Security penetration tests / Performance benchmarks / A2A protocol interfaces" removed from Test Coverage ✅ list → marked PLANNED.
- Test commands corrected to the real regression gate: `python -m pytest tests/ -q`.
- Added **Reality Status Legend** (IMPLEMENTED / PARTIALLY IMPLEMENTED / SCAFFOLDED / PROTOTYPE / PLANNED / UNVERIFIED).

**Non-existent Files Removed From Documentation**: `a2a_protocol_handler.py` (x2), `policy_intelligence_service.py`, `policy_matcher.py`, `schema/policy-schema.json`, `tests/policy/`, `tests/performance/`, `docker-compose.yml`, `docs/README.md` link, fake `global_policy_aggregator/crawlers/{china_crawler,silicon_valley_crawler,eu_crawler,singapore_crawler}.py` entries (real files live in `policy_crawler/`), fake `processors/data_structurer.py` + `intelligence_aggregator.py` under `global_policy_aggregator/`. All moved to an explicit **Planned** note.

**Status Summary**:
- MCP: **PLANNED** • A2A: **PLANNED**
- Crawler: **PROTOTYPE** — verified 6 files in `global_policy_aggregator/crawlers/` (5 China-focused + engine), 4 regional crawlers in `policy_crawler/crawlers/`; no live government-site scraping verified.
- Industry Taxonomy: **UNRESOLVED / OPEN** — `types.py`=5, PolicyCleaner effective output=8, `deeptech_policy_schema.json`=21, web server=12. **This Quest only records, does not unify.** Recommend a dedicated *Industry Taxonomy Design Quest*.
- Test Gate: **PASS** (68 passed / 0 failed / collection OK).

### Test Gate Repair (before / after)

**Test Collection Before**: FAIL — `ModuleNotFoundError: No module named 'services'` at collection.
**Test Collection After**: PASS — `python -m pytest tests/ --collect-only -q` collects 68 tests.
**Full Test Before**: never reached execution stage.
**Full Test After**: `python -m pytest tests/ -q` → **68 passed, 0 failed** (server 25 + client 17 + integration 26).

**Fixes applied (root-cause, no test deleted/skipped/weakened)**:
- `pytest.ini`: added `pythonpath = .` (pytest ≥7 native option, no PYTHONPATH hack).
- Added 11 `__init__.py` package markers (server, server/config, server/services, client, client/api, client/hooks, client/utils, schema, tests/*).
- Fixed broken imports: `client/main.py`, `client/hooks/ai_agent_direct_apply.py` relative-import chains; `server/main.py` service imports.
- `server/main.py`: JSON-RPC 2.0 spec compliance — parse error `-32700`, invalid request `-32600` (previously lumped into `-32603`); pydantic result serialization; `industry`/`name` passthrough from projects data.
- `schema/types.py`: **additive-only** change per INV-002 — defaults for `JsonRpcResponse.result/error/id`; two Optional backward-compatible fields (`name`, `industry`) on `TechReadinessResponse`. **No field deleted or renamed.** Old schema payloads remain valid.
- Test-side defects proven wrong and fixed (documented, not weakened): 7× `asyncio.run` on sync methods in `test_integration.py`; 2× `in`-on-pydantic-model assertions in `test_server.py`; promotion mock fixtures aligned to the real 3-sample project dataset; `test_analyze_strengths_weaknesses` input expanded to cover the weaknesses branch; added `tests/integration/conftest.py` real-server session fixture (port 8123).

### Coverage

`python -m pytest tests/ --cov=. --cov-report=term -q` (pytest-cov installed) → **TOTAL 67%** (2114 statements, 702 uncovered). Real measured value, not estimated.

### Files Changed

Modified: `README.md`, `pytest.ini`, `server/main.py`, `server/services/tech_readiness_service.py`, `server/services/landing_requirements_service.py`, `schema/types.py` (additive only), `client/main.py`, `client/api/protocol_client.py`, `client/utils/project_evaluator.py`, `client/hooks/ai_agent_direct_apply.py`, `tests/server/test_server.py`, `tests/client/test_client.py`, `tests/integration/test_integration.py`, `Qoder_Technical_Handover_20260824.md`.
Added: 11× `__init__.py`, `tests/integration/conftest.py`.
**Business data / policy seed data / Robotaxi data / crawler datasets: NOT TOUCHED.**

### Known Remaining Gaps

- Industry Taxonomy Alignment: **Status OPEN** (5/8/21/12 across components) — requires a dedicated design quest.
- No authentication on `/rpc`; CORS `allow_origins=["*"]` (dev-only).
- MCP / A2A: PLANNED, zero implementation.
- Performance/security test suites: none (PLANNED).
- Policy data provenance fields still missing (see APPENDIX B).

### Git Evidence

- **Commit Hash**: `f449f578f6665cf7420847fadc0a9cb4599ad09a` (this commit; recorded via follow-up evidence commit)
- **Commit Message**: `fix: align repository reality and repair test gate`
- **Push**: `origin/master` — result recorded in follow-up evidence commit

---

## TASK-P0-2

### Policy Provenance & Anti-Hallucination Data Governance

**Task Description**: Establish the absolute data-truthfulness boundary for all policy / government / contact information: only real, verifiable, traceable information may exist as "real"; everything else must be explicitly MOCK, UNVERIFIED, or null. Govern existing data by **marking + nullifying only — never deleting**. No record was deleted in this task (INV-000).

**Verified At**: 2026-08-24

### Data Integrity Rules (new constitution entries)

DATA-INTEGRITY-001..005 added as **INV-007** in §3 (No Fabricated Government Information / Every Policy Must Have Provenance / Every Contact Must Be Verifiable / Unknown Information Must Remain Unknown / Mock Data Must Be Explicitly Labeled). Highest discipline: 宁可 null，不要猜；宁可 UNVERIFIED，不要 VERIFIED；宁可少一条政策，不要多一条假的政策。

### Policy Provenance Model

Real policy requires: `source_url` (official, reachable-at-verification-time), `source_title`, `publisher`, `published_date`, `effective_date`, `retrieved_at`. Source priority: government portal → department site → agency site → official park site → official platform. Third-party discovery URLs → `secondary_source_url` only. Unknown date fields (e.g. effective date not stated in the document) must remain `null` — never inferred.

Key separation: `url_status` (format/reachability) ≠ `source_verification_status` (authenticity). **HTTP 200 never proves official authorship.**

### Contact Provenance Model

Any contact (`name`/`department`/`phone`/`email`/`address`) must carry `contact_source_url` (or per-field `phone_source_url`/`email_source_url`), otherwise `contact_status = "unverified"` and unconfirmable fields stay `null`. Placeholder detection rejects classic fabricated patterns (`xxx-12345678`, `13800138000`). Private personal data (private mobiles, WeChat, IDs) must never be collected. **没有联系方式，比错误联系方式安全一万倍。**

### Mock Data Audit (结果：只标记，不删除)

| Dataset | Records | Before | After |
|---|---|---|---|
| `global_policy_aggregator/data/seed_data/china_policy_seed_data.json` | 12 | no mock flag; fabricated template `source_url`; AI self-scored `confidence_score` | `is_mock=true` + `verification_status="mock"`; fabricated URLs/confidence → `null` (with `*_note` explanations) |
| `global_policy_aggregator/data/seed_data/detailed_china_tech_policies.json` | 9 | no mock flag; fabricated `source_url`; fabricated contact phones/emails/addresses | mock-flagged; `source_url` → `null`; contacts → `null` + `contact_status="unverified"` |
| `global_policy_aggregator/web/interactive_ai_server.py` (embedded) | 12 | realistic-looking **fabricated** phones/emails/addresses presented as “官方联系方式” | mock-flagged; all contact values → `None` + `contact_status="unverified"`; UI/PDF show “未核验（待官方认领后提供）”; MOCK warning banner added |
| `web/fixed_server.py`, `web/interactive_ai_server_new.py` (fallback data) | 2×2 | fabricated source_url + contacts | mock-flagged; fabricated URLs/contacts → `None` |
| `scripts/populate_china_policies.py`, `policy_crawler/{mock_policy_database.py, data/mock_policy_database.py, processors/mock_policy_database.py, data/raw_policies/sample_raw_policies.py}` | generators/samples | no explicit boundary declaration | explicit DATA-INTEGRITY MOCK banners added (data itself untouched) |

**Governance scripts (kept for audit trail)**: `global_policy_aggregator/scripts/apply_provenance_governance.py`, `scripts/govern_web_portal_data.py`.

### Policy / Contact Audit Summary

- **POLICY RECORDS AUDITED**: 33 (12 seed + 9 detailed + 12 embedded web)
- **MOCK RECORDS**: 33 • **VERIFIED RECORDS**: 0 • **UNVERIFIED RECORDS**: 0
- **MISSING SOURCE URL**: 33/33 — acceptable and intentional: all are mock; fabricated URLs were nullified rather than preserved.
- **CONTACT RECORDS AUDITED**: 30+ across seed/web/crawler sample data
- **FABRICATED CONTACT DATA FOUND**: YES — realistic-looking AI-invented numbers (e.g. `010-82896688`, `policy@zjpark.gov.cn`) and classic placeholders (`010-12345678`, `13800138000`). All served/embedded ones nullified + marked `unverified`; none deleted.
- **FABRICATED POLICY DATA FOUND**: YES (all 33 records are AI-generated demo policies using real-region names) — now explicitly MOCK-flagged everywhere they are served or stored; never labeled verified.

### Validator Changes

New module `global_policy_aggregator/processors/provenance_validator.py`:
- `VerificationStatus` / `UrlStatus` enums; `PolicyContact` / `PolicyProvenance` pydantic models (all-new fields Optional → backward compatible, TEST-PROVENANCE-006).
- `validate_source_url()`: format + placeholder detection only (never asserts authenticity).
- `validate_policy_record()`: enforces mock-never-verified, verified-needs-source_url, contact-needs-provenance-or-unverified, placeholder-phone rejection.
- `audit_policy_dataset()`: TOTAL / MOCK / VERIFIED / UNVERIFIED / MISSING SOURCE URL / MISSING CONTACT PROVENANCE statistics (audit-only, never mutates).

**Schema (additive-only, INV-002)**: `global_policy_aggregator/schemas/deeptech_policy_schema.json` + `policy_crawler/schemas/policy_schema.json` gained a new optional `data_integrity` block (`is_mock`, `verification_status`, `source_title`, `publisher`, `retrieved_at`, `secondary_source_url`, `contact_source_url`, `url_status`) plus `contact_source_url`/`phone_source_url`/`email_source_url`/`contact_status` on `contact_info`. **No field deleted/renamed; no `required` changed → old payloads remain valid.**

**Provenance chain verified (not modified)**: crawler → `PolicyCleaner.clean_policy_text(text, source_url)` → `_build_metadata` keeps `source_url`; `policy_crawler/processors/data_structurer.py` propagates `metadata.source_url`. No provenance loss in parser/cleaner.

### Test Evidence

New: `tests/test_provenance.py` — **TEST-PROVENANCE-001** (mock ≠ verified), **002** (mock may lack source_url), **003** (verified requires source_url), **004** (contact provenance or explicit unverified), **005** (placeholder/invalid URL cannot be VERIFIED source; format-valid ≠ source-verified), **006** (legacy payloads still parse), plus seed-data governance regression (all seed records mock-flagged, zero governance violations, zero contacts with values lacking provenance). Test fixtures use IANA-reserved `.invalid` TLD — no real or fake government URLs invented in tests.

**Full regression gate**: `python -m pytest tests/ -q` → **93 passed, 0 failed** (68 pre-existing all kept + 25 new). No test deleted/skipped/weakened.

### Coverage

`python -m pytest tests/ --cov=. --cov-report=term-missing -q` → **TOTAL 56%** (2875 statements). `provenance_validator.py` itself: **91%**. The percentage drop vs P0-1 (67%) is because the governance work brought previously-untracked modules (web servers, scripts, data modules) into the measured scope — both numbers are real measurements, not estimates.

### Known Remaining Gaps

- No record in the repository is currently VERIFIED — verification of any real policy requires an official-source evidence workflow (crawl + snapshot + human/agent confirmation), which does not exist yet.
- `policy_ai_agent.py` demo `__main__` and `test_ai_agent.py` fixtures contain a synthetic user phone (`13800138000`) — this is user-side demo context, **not** a government contact; left untouched per rule that unverifiable data is marked, not deleted.
- Legacy SQLite/DB stores (if populated by historical generator runs) were not re-audited field-by-field; generators now carry MOCK declarations, but already-populated DB rows would need a one-off re-mark pass if any such DB ships to production.
- Crawler still has no live official-source verification step; until one exists, everything it produces must default to `unverified`.

### Git Evidence

- **Commit Hash**: `ec2e1961811795f89722ce0bd5df3d5fe3caf2bd` (this commit; recorded via follow-up evidence commit)
- **Commit Message**: `feat: enforce policy provenance and anti-hallucination data governance`
- **Push**: `origin/master` — result recorded in follow-up evidence commit
- **Business data check**: Robotaxi / autonomous-driving / historical industry data untouched; no unauthorized deletions (git diff reviewed).

---

## TASK-P0-2.1

### Remote GitHub Reality Verification + Mock Disclosure Repair

**Task Description**: Independent acceptance found that while P0-2 data governance reached the data layer, the **public display layer** (HTML templates, PDF) lacked mandatory MOCK disclosure. This task synced the disclosure to every user-facing surface, with GitHub remote content as the final source of truth. No new features; no data deletion; no history rewrite.

**Verified At**: 2026-08-24

### Remote Verification (first principle: trust the remote, not local)

- `git fetch origin` → LOCAL_HEAD == REMOTE_HEAD == GITHUB_MASTER_HEAD == `07a31cf66dcb201d675e36f25bc1d0570c939a74` → previous push claims were factually correct.
- **README reality check against `origin/master:README.md`** (not the working copy): all previously-flagged claims already downgraded — remaining hits are `*(PLANNED)*` / `*(UNVERIFIED)*` / `Planned (not yet in repository)` / `prototype` statements. `A2A Ready`: 0 hits; `500+`: 0 hits; `verified government contact`: 0 hits. The independently-reported stale README claims did not match `origin/master` content — likely a stale cache / wrong ref view; recorded here with evidence rather than assumed.
- **Real gap confirmed**: `origin/master:global_policy_aggregator/web/templates/index.html` had **zero** MOCK disclosure (user finding B was factual). Disclosure existed only in the inline HTML of `interactive_ai_server.py`.

### Web Disclosure (all entry points, no exceptions)

- New governance script `global_policy_aggregator/scripts/inject_mock_disclosure.py` (idempotent, marker `P0-2.1-MOCK-DISCLOSURE`) injected a **bilingual top-of-page banner** (中文 + English, prominent, no click required, not footer/tooltip) into **all 8 templates** (`index/chat/demo/english/simple/simple_demo/test/test_simple.html`) and the inline HTML of `simple_server.py`.
- Entry-point audit: `ai_agent_interface.py` and `debug_routes.py` render templates (covered); `fixed_server.py` / `interactive_ai_server_new.py` expose API-only routes and always fall back to in-code MOCK data (`web/data/` does not exist — verified), now docstring-marked **LEGACY / DEMONSTRATION ONLY**; `interactive_ai_server.py` marked **DEMONSTRATION PORTAL**.
- **Per-card MOCK label**: every policy card now renders `⚠️ MOCK / 演示数据 · 未经官方来源核验` badge when `policy.is_mock` (Article 6 — banner alone insufficient).
- Contact section relabeled `📞 官方联系方式（未核验）` → `📞 联系方式：未核验`; misleading “下载政策红头文件” button → “下载演示文档（PDF，非官方红头文件）”; all residual `官方联系方式` strings removed (incl. code comments).

### PDF Disclosure

`/api/policy/{id}/pdf` now renders a **first-page prominent yellow disclaimer box** immediately under the title: “⚠️ MOCK / DEMONSTRATION DATA：本文档内容为演示数据，未经官方来源核验，不代表任何政府部门的正式政策、补贴承诺或招商条件…” plus the pre-existing footer declaration. PDF contact section title → `联系方式（未核验）`.

### UI Regression Tests

New `tests/test_ui_mock_disclosure.py` (force-added past `.gitignore` `test_*.py` rule, consistent with `test_provenance.py`):
**TEST-UI-MOCK-001** page contains disclosure banner (before policy content) • **002** card renderer emits MOCK badge + all 12 embedded policies flagged • **003** no “官方联系方式 / Verified Government Contact” anywhere; contact labeled unverified • **004** all contacts null + unverified; null renders as “未核验”; no historical fabricated numbers in served HTML • **005** PDF endpoint returns valid %PDF + generator source carries first-page disclaimer • **006** all 8 templates + 4 server entry points carry disclosure / LEGACY markers. **18 passed.**

### Test Result / Coverage

- `python -m pytest tests/ -q` → **111 passed, 0 failed** (93 pre-existing kept + 18 new). No test deleted/skipped/weakened.
- Coverage: `--cov=. --cov-report=term-missing` → **TOTAL 58%** (3108 statements). Real measurement.

### Git Evidence

- **Commit Hash**: `ca2926bce57170d4644a7ae126b7b325e9cdf8c6` (this commit; recorded via follow-up evidence commit)
- **Commit Message**: `fix: disclose mock policy data in public surfaces`
- **Remote HEAD after push**: `ca2926bce57170d4644a7ae126b7b325e9cdf8c6` (verified via `git ls-remote origin refs/heads/master` + content-level acceptance against `origin/master` blobs)
- **Historical mock data**: old fabricated values still exist in pre-P0-2 commits — recorded as **HISTORICAL MOCK DATA**; no `filter-repo` / BFG / force push executed (requires separate explicit authorization).

### Remaining Risks

- Git history still contains pre-governance fabricated contacts/URLs in old commits (public browsing possible). Cleanup is a separate authorized task.
- `policy_database.db` (web directory) not field-audited this round; served portal uses in-code data only.
- Real (VERIFIED) policy workflow still absent — portal must remain labeled demonstration until it exists.

---

## TASK-P0-2.2

### Historical Data Exposure Audit + Public Repository Legal Risk Assessment

**Task Description**: Read-only audit of the entire Git history of `origin/master` for fabricated government contacts, fabricated source URLs, and fabricated policy content; formal risk report + future VERIFIED-admission governance rules + anti-regression tests. **No data deletion, no content modification of audited files, no history rewrite.**

**Verified At**: 2026-08-24

### Remote First Baseline

- `git fetch origin` → LOCAL_HEAD == REMOTE_HEAD == GITHUB_HEAD == `8c38be15844d2e20b5893db6c7af3900922d2a02`.
- Audit scope: all 11 commits `a970ba5..8c38be1` scanned via `git grep` per commit tree (read-only).

### Historical Audit Result

- **HIST_CONTACT_FINDINGS**: fabricated landlines (`021-12345678`, `010-82896688`, `021-50800880`, `0755-86543210`, `010-12345678`) and fabricated gov-domain emails (`quantum@shanghai.gov.cn`, `policy@zjpark.gov.cn`) introduced in `01ba935` (v3.1.0). Portal/seed exposure remediated in `ec2e196` (P0-2, mark + null); **15 files in the current tree still contain these tokens**, 13 of them without any MOCK marker.
- **HIST_SOURCE_URL_FINDINGS**: fabricated gov.cn URLs in two classes — likely non-existent domains (`zjpark/shqp/zhangjiang/hfht/gzzh/hfep.gov.cn`) and real-style domains with fabricated paths (`shanghai.gov.cn/node12345/...`, `sz.gov.cn/ztzl/ai_policy`). Seed copies remediated; crawler `base_url`s and `structured_policies` copies remain in HEAD. No DNS verification performed; all domains treated as UNVERIFIED.
- **POLICY CLAIM RISKS**: 35 unique fabricated subsidy-amount strings; pre-P0-2 portal displayed fabricated numbers under an `官方联系方式` heading and README carried unverified marketing claims — both eliminated in current version (category 3 resolved), but permanently recoverable from history.
- Full tables: `docs/Historical_Data_Exposure_Audit_20260824.md`.

### Risk Level

- **HIGH (H1)**: commits `01ba935`, `580ace3`, `6c0e0e2`, `1eaa39e` carry unmarked fabricated data + `官方联系方式` UI — checkout-able by anyone; only removable via history rewrite (not executed).
- **HIGH (H2)**: 13 unmarked files with fabricated contacts still in the current tree (list in audit doc §5; frozen as a test-supervised quarantine manifest).
- **MEDIUM**: governed seed datasets (mock-marked, contacts null), 2 mock-headered scripts still carrying fabricated numbers, crawler base_urls.
- **LOW**: `.invalid`/example test fixtures, evidence citations in docs, all `is_mock: true` datasets.

### No History Rewrite Decision

No `filter-repo` / `filter-branch` / BFG / force push executed. Record-only, per quest directive. Any remediation (file annotation/quarantine, history rewrite, repo visibility change) **requires explicit written approval — 需要人工批准：YES**.

### Future Governance Rules

New `docs/Policy_Data_Governance.md`: VERIFIED admission requires all 9 fields (`source_url`, `source_title`, `publisher`, `published_date`, `effective_date`, `retrieved_at`, `snapshot`, `confidence`, `verification_method`); statuses MOCK / UNVERIFIED / PARTIALLY_VERIFIED / VERIFIED; no official source ⇒ no VERIFIED; no actual human/agent verification trail ⇒ no “Official” display; history rewrite forbidden without written authorization.

### Regression Tests

New `tests/test_history_policy_rules.py` (force-added past `.gitignore` `test_*.py` rule): **TEST-HISTORY-001** web serving layer zero-tolerance for fabricated contacts + quarantine-manifest containment (new leaking files fail; stale manifest entries fail) • **TEST-HISTORY-002** validator rejects VERIFIED without `source_url`; current datasets + portal contain 0 VERIFIED records • **TEST-HISTORY-003** every MOCK policy surface carries disclaimer (page banner, card badge, PDF first-page box, mock-marked seed datasets).

### Test Result / Coverage

- `python -m pytest tests/ -q --cov=. --cov-report=term` → **120 passed, 0 failed** (111 pre-existing kept + 9 new TEST-HISTORY). No test deleted/skipped/weakened.
- Coverage: **TOTAL 59%** (3230 statements). Real measurement.

### Git Evidence

- **Commit Hash**: filled by follow-up evidence commit
- **Commit Message**: `docs: add historical exposure audit and policy governance rules`
- **Remote HEAD after push**: filled by follow-up evidence commit

---

*End of Constitution. Preserve > Modify · Evidence > Assertion · Reality > Documentation · Compatibility > Convenience · Explicit Migration > Silent Deletion · Verified Data > Fabricated Data.*
