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
- **Commit Hash**: `__COMMIT_HASH__`
- **Push Result**: `origin/master`
- **Worktree after push**: CLEAN (only pre-existing untracked `test_*.ps1` remain untracked by design)

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

*End of Constitution. Preserve > Modify · Evidence > Assertion · Reality > Documentation · Compatibility > Convenience · Explicit Migration > Silent Deletion · Verified Data > Fabricated Data.*
