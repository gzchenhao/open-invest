# Policy Ingestion Pipeline — Contract v1 (P3-0, JUDGE approved 2026-09)

Canonical record: `OpenInvest_Technical_Handover_Trae_20260831.md` (P3-0 section).
This file is the code-side summary for future agents.

## Purpose & boundary

The pipeline performs **DISCOVER → FETCH → PARSE → NORMALIZE → VALIDATE → INGEST**.
**The crawler is NOT a verification engine.** Every candidate is
`is_mock=false, verification_status="unverified"`. VERIFIED has no code path here.
Governance: 宁可 null，不要猜；宁可 UNVERIFIED，不要 VERIFIED.

Implemented / planned stages:
- **P3-1 (done)**: `source_registry.py` + `source_registry.json` (official allowlist),
  `fetcher.py` (fetch + raw snapshot + failure log).
- **P3-2 (done)**: `candidate.py` (Candidate + FieldEvidence) + `parser.py`
  (bs4/lxml → clean text + fail-safe ParseFailure) + `normalizer.py`
  (逐字段 null-safe 抽取 + canonical_taxonomy 映射 + 字段级 quote evidence)。
  复用的纯逻辑：canonical_taxonomy.get_registry().resolve()（industry）；
  金额/日期正则抽取为独立纯函数，仅在有明确证据时填充。contact 在 P3-2 暂不抽取。
- **P3-3 (planned)**: validate + staging + human approval; only then entries may enter
  `global_policy_aggregator/data/real_policies/real_policies.json` (human-approved, id 121+).
  P3-1 绝不写入该文件（见 Key rules #5）。

## Key rules (do not violate)

1. **Registry allowlist**: only HTTP(S) URLs on `allowed_domains` of *enabled* sources
   may be fetched. Registry-external URLs are rejected. No automatic domain discovery;
   new sources are added by humans to the tracked `source_registry.json`.
2. **Snapshot** (`data/raw_policies/snapshots/`): runtime artifact, gitignored, never
   published; dedup by normalized-content SHA-256; source_url in policy records is
   permanent regardless of snapshot fate. Missing snapshot ⇒ no guessed fields.
3. **null-first**: `amount / requirements / eligibility / contact` have NO extraction
   code path in v1 (not "failed extraction" — deliberately absent). Every non-null
   extracted field must carry a verbatim quote from the snapshot
   (`extracted_fields_evidence`, enforced from P3-3 validate stage).
4. **Failure honesty**: failures are typed (timeout / connection_error / http_4xx /
   http_5xx / unexpected_content / url_not_allowed), logged to
   `fetch_failures.jsonl`, and never produce policies or fake successes.
5. **Existing 20 REAL policies**: never rewritten, never re-ingested, ids unchanged;
   they are the regression/contract fixture (grandfathered from the new provenance
   hard gate).
6. **Trust isolation**: no `src/trust/**` imports, no `verification_status` writes,
   no VERIFIED value, ever. Provenance for ingested policies lives in SIDECAR files
   (JUDGE decision), not in the portal policy schema.
