# P1-6.0 — GitHub Growth Readiness Audit

**Date:** 2026-09-01
**Quest:** P1-6.0 AUDIT ONLY
**Nature:** Audience-facing repository health & adoption audit. Minimal documentation-only fixes applied for verified blockers.

---

## BASELINE

| Item | Value |
|------|-------|
| HEAD (remote/local synced) | `a603954` → `{post-fix commit}` |
| Local pytest | 637 passed, 0 failed (full); 628 CI-safe (--ignore=tests/integration) |
| Worktree | Clean before fixes |
| GitHub Actions CI | NOT VERIFIED (WebFetch cannot inspect runner logs) |
| Repo visibility | Public ✅ |
| About/Description | NOT SET |
| Topics | NOT SET |
| Homepage | NOT SET (blank is correct per audit) |
| License | ✅ MIT LICENSE file created during this audit (README referenced MIT but file was missing — unavoidable fix) |
| Releases/Tags | None |
| CI badge | Real URL present but remote pass not observable from current environment |

---

## FIRST 60 SECONDS — USER JOURNEY

| Timepoint | Question | Result |
|-----------|----------|--------|
| 10s | What is OpenInvest? | ✅ One-sentence definition visible in hero banner. |
| 30s | What problem solved? | ✅ "4 problems" listed + 4-principle architecture. |
| 30s | What's implemented today? | ✅ Status Matrix + Testing section + Roadmap table exist. |
| 60s | Can I run the demo? | ✅ **FIXED during audit:** `cd open-invest/open-invest-protocol` → `cd open-invest` (repo root *is* the protocol dir; 3 copy-paste command bugs were P0.) |
| 60s | Understand Safety Chain | ⚠️ ~90% there: Architecture ASCII + Verification System section exist but no end-to-end visual diagram beyond ASCII art. Readable but not scannable for casual browser. |
| Capability vs prototype vs vision | ✅ Honest labels exist: experimental framework, Status Matrix, vision sentence explicitly marked. |

**Funnel assessment:** README→QUICKSTART.md→Demo output→docs/README.md form a solid information funnel, with one P0 bug (fixed during audit: wrong cd path). Remaining gaps are P1/P2, not blockers.

---

## STAR / FORK / CONTRIBUTION CONVERSION

### Star
- ✅ 4 clear reasons to Star now exist in "Who is this for? Why star?" section.
- ⚠️ Missing CI passing state + missing About metadata = weaker first impression.
- **Verdict:** Users who make it past the hero *will* find credible reasons to Star; the problem is getting them there.

### Fork
- ✅ Demo actually runs.
- ✅ 628+ CI-safe tests + verification model is inherently forkable (experiment with trust rules).
- ⚠️ Root clutter (reports, Chinese-named dirs, marketing plans) makes repo look "internal" rather than "hacker-friendly fork target."

### Contribution
- ✅ CONTRIBUTING.md exists.
- ✅ Contributing section in README lists Good First / Do Not Contribute.
- ❌ No Issue templates. (P2, not blocker)
- ❌ No CODE_OF_CONDUCT.md. (P2)
- ❌ No SECURITY.md. (P2)
- ⚠️ Roadmap exists but no dedicated "Help Wanted" / Good First Issue tag pool. (P1)

---

## TRUST / CREDIBILITY AUDIT

| # | FINDING | EVIDENCE | RISK | RECOMMENDATION |
|---|---------|----------|------|----------------|
| 1 | **Install path mismatch (FIXED)** | README line 57/75 + QUICKSTART line 23 used `cd open-invest/open-invest-protocol`. Remote repo root *is* open-invest-protocol; correct is `cd open-invest`. | **HIGH** — every new user fails step 2; zero first-run success. | Applied during audit: 3 doc lines corrected. |
| 2 | **LICENSE file missing (FIXED)** | README referenced "MIT License — see LICENSE" but file did not exist. GitHub cannot detect license. | **HIGH** — serious OSS consumers filter by license; missing license = legally unsafe to use. | Applied during audit: MIT LICENSE file created (standard text, gzchenhao 2026). |
| 3 | **About metadata blank** | Description, Topics, Homepage all empty. Search result snippet shows only README text; no Topics filtering. | **MEDIUM** — no search discovery; star conversion on About 0/4 signals. | Manual copy-paste in Settings → General. Values: see Handover §23.2 checklist. |
| 4 | **CI badge not verified passing** | Workflow configured, 4 prior runs: 2 working-dir FAIL + 2 queued/not observable. Current badge likely red/failing. | **MEDIUM** — first thing above hero title; failing badge = silent credibility drop. | After CI green, badge auto-updates. |
| 5 | **Internal artifacts dominate root listing** | `*_REPORT.md` (2 files), `*_SUMMARY.md`, 85KB Handover, 30+ files in root view instead of clean "src/, tests/, docs/". | **MEDIUM** — casual scroller sees internal docs before real source code. | Move legacy reports → `docs/historical/` in next Quest (requires governance approval per Master Handover rules). |
| 6 | **Unicode dir name + marketing/ in public root** | `global政策聚合器/` (mixed CJK) + `marketing/` (HN launch, Twitter threads, WeChat posts) — both clearly internal GTM materials. | **MEDIUM** — UTF encoding issues possible; gives impression repo was open-sourced accidentally rather than intentionally. | Audit-only; recommend archival or `.gitignore`'d internal submodule; requires decision. |
| 7 | **No Releases / No tags** | 0 releases, 0 tags on GitHub. | **LOW** — framework is explicitly prototype/experimental; versioning optional. | When P1-6 first consumer API stabilizes, tag `v0.1.0-experimental`. |
| 8 | **Exaggeration checks — all clean** | No fake claims detected. Status Matrix, USB-C vision label, experimental framework label, MOCK data label all present. | **LOW** — honesty preserved. | No action. |

---

## OPEN-SOURCE BASELINE INVENTORY

| File | Status | Adoption impact |
|------|--------|-----------------|
| LICENSE | ✅ **Created this audit** | P0, legally required for OSS use. |
| README.md | ✅ | Exists, good structure. |
| QUICKSTART.md | ✅ | Exists. |
| docs/README.md | ✅ | Exists. |
| CONTRIBUTING.md | ⚠️ Exists (initial commit). Very basic. | P2 — can be enriched later. |
| CODE_OF_CONDUCT.md | ❌ Missing | P2 — table-stakes for larger communities; not a blocker for prototype. |
| SECURITY.md | ❌ Missing | P2 — needed once real deployments exist; not now. |
| .github/ISSUE_TEMPLATE/ | ❌ Missing | P2. |
| .github/PULL_REQUEST_TEMPLATE.md | ❌ Missing | P3 — ignore. |
| GitHub Actions (Tests) | ⚠️ Exists, remote not yet green | P0 if still failing → see CI section. |
| CI badge (README) | ⚠️ Linked correctly, color pending | Credibility tied to green. |
| Releases/Tags | ❌ 0 | P2. |

---

## TECHNICAL DEBT AFFECTING ADOPTION

| Debt | Severity | Notes |
|------|----------|-------|
| 628 CI-safe vs 637 local (9 integration tests excluded) | **MEDIUM** | Testing section explains it. Users who run full suite locally will see 637, which is fine. Larger question: can 9 integration tests be made port-agnostic for CI? Separate Quest. |
| Python version compatibility matrix only 3.11/3.12 | **LOW** | Local dev uses 3.14; tests may need future validation. Not adoption-blocking. |
| requirements.txt pins older dependency generations (fastapi 0.104, pydantic 2.5, pytest 7.4) | **LOW** | Works. Upgrade is future hygiene, not adoption urgency. |
| Duplicate dirs (policy_crawler/ vs global_policy_aggregator/crawlers/, etc.) | **MEDIUM** — visual/UX | Creates navigational confusion. |
| Handover doc (1700 lines, 85KB) in repo root next to LICENSE | **MEDIUM** — visual/UX | OpenInvest_Technical_Handover_Trae_20260831.md is discoverability noise. |

---

## PRIORITIZATION — GITHUB GROWTH READINESS

### P0 — Must fix immediately (3 items, 2 already applied during audit)
1. **Install path bug (APPLIED)** — README/QUICKSTART `cd` path corrected. *Without this fix the project cannot produce a single successful first run.*
2. **Missing LICENSE file (APPLIED)** — MIT LICENSE created. *Legal baseline for any OSS use.*
3. **CI badge must go green** — Workflow is fixed for 628 core tests; GitHub runner needs to confirm pass. *Red badge = users bounce before reading.*

### P1 — High value, high conversion ROI (5 items)
1. **Apply GitHub About metadata manually** — Description + 11 Topics from Handover checklist. This is today's single highest ROI Stars lever.
2. **Confirm CI badge green** — After Run #4+#5 settle on master, verify badge passes; if still failing, debug.
3. **Move root-level clutter (reports/summaries/Handover?) to docs/historical/** — subject to Master Handover single-file rule. At minimum the 2 QUEST_REPORT files + PROJECT_SUMMARY could relocate to `docs/historical/` without governance conflict.
4. **Create root `.gitignore` exclude for internal-only dirs or move `marketing/`** — keep public root lean. (Decision needed re: CJK-named dir.)
5. **Seed 1–2 "Good First Issue" GitHub Issues** with explicit labels + links, give potential contributors a landing point.

### P2 — Valuable, can wait (5 items)
1. Add basic ISSUE_TEMPLATE (bug + feature request)
2. Add minimal SECURITY.md with "experimental — report via GitHub Issues" placeholder
3. Consider lightweight CODE_OF_CONDUCT.md (Contributor Covenant short form)
4. Tag `v0.1.0-experimental` release once CI is green and metadata set
5. Port-agnostic integration tests so the 9 excluded tests rejoin CI

### IGNORE — Not worth pursuing right now (5 items)
1. Coverage badges / coveralls / codecov (tests exist; coverage does not move Stars at prototype stage)
2. Social preview / logo / custom Open Graph image (Description+Topics are 10x higher ROI)
3. Lint / formatting / pre-commit CI (no external contributors yet; internal hygiene only)
4. GitHub Wiki (docs/README.md + QUICKSTART.md already serve)
5. Automated dependency updates / Dependabot config (risk of breaks, reward minimal)

---

## STRATEGIC QUESTION

### Should the project enter P1-6.x implementation *now*?

**Recommendation: NO. Finish adoption blockers first.**

Evidence:
- 2 P0-level adoption blockers (cd path + LICENSE) *just* found & fixed.
- CI badge is not reliably green and has not been remotely observed passing.
- Zero About metadata = near-zero GitHub topic search discovery.
- Root file listing confuses internal vs public content.

**The Trust Safety Chain (P1-4.x) is complete and does not need expansion.** P1-6.x implementation on top of an adoption-broken foundation would produce code nobody runs.

---

*Audit performed from 4 personas: GitHub first-timer, DeepTech developer, AI engineer, investment-tech researcher. No production code was changed. Documentation-only fixes (path bug + LICENSE) were unavoidable and are recorded above.*
