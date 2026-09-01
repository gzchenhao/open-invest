# P1-5.6 — GitHub Repository Metadata & Discoverability Audit

**Date:** 2026-09-01
**Quest:** P1-5.6
**Status:** COMPLETE

---

## CI REMOTE FIX (P1-5.5 regression)

**Finding #1:** First CI remote run FAILED.

**Root cause:** Workflow used `working-directory: open-invest-protocol`. The remote repo `gzchenhao/open-invest`'s root IS the `open-invest-protocol/` directory content. There is no `open-invest-protocol/` subdirectory at repo root.

**Error:**
```
working directory '/home/runner/work/open-invest/open-invest/open-invest-protocol'. No such file or directory
```

**Fix applied:** Removed `working-directory: open-invest-protocol` from both install and test steps. Steps now run at repo root (correct path).

**CI file:** [`.github/workflows/tests.yml`](.github/workflows/tests.yml)

**Current CI status:** RE-CONFIGURED. Will be remote-verified when this commit is pushed to master. Run #1 FAIL, Run #2 pending.

---

## REPOSITORY METADATA AUDIT

TRAE environment cannot write GitHub repository settings via API. Values below are for manual setup in repo **Settings → General**.

### Repository Description (About → Description)

**Current (observed via WebFetch):** Not set / empty.

**Suggested value:**
```
Experimental framework for evidence, verification, provenance, and trust-oriented workflows for DeepTech investment intelligence.
```

Why this text:
- Matches README one-line definition closely (consistency)
- Includes all 4 core capability keywords: evidence, verification, provenance, trust
- Clearly labels as "experimental framework" (no production claim)
- Ends with DeepTech investment intelligence positioning
- Length reasonable for GitHub search results

### GitHub Topics (About → Topics)

**Current (observed via WebFetch):** None set.

**Suggested topics (max 20 characters each; GitHub-enforced):**

```
deeptech
investment-intelligence
evidence-graph
provenance
verification
trust
ai
autonomous-driving
policy-analysis
new-energy
semiconductor
```

**Selection rationale:**
- ✅ `deeptech` — core target domain
- ✅ `investment-intelligence` — product purpose
- ✅ `evidence-graph` — real implemented feature
- ✅ `provenance` — real implemented feature
- ✅ `verification` — real implemented feature
- ✅ `trust` — real implemented feature
- ✅ `ai` — AI agent workflows in scope
- ✅ `autonomous-driving` — real industry in canonical taxonomy
- ✅ `policy-analysis` — policy evidence use case
- ✅ `new-energy` — real industry in canonical taxonomy
- ✅ `semiconductor` — real industry in canonical taxonomy

**Topics EXPLICITLY NOT suggested:**
- ❌ `government` — no real government data
- ❌ `production` — not production-ready
- ❌ `enterprise` — no enterprise claims
- ❌ `mcp` / `a2a` — not implemented (future architecture, out of scope)
- ❌ `agi` — overclaiming
- ❌ `oauth` / `authentication` — not implemented
- ❌ `database` — not implemented

### Homepage URL (About → Website)

**Current:** Not set.

**Suggestion:** Do NOT set. No verified, stable, long-term product homepage exists.

- GitHub repo itself is the canonical entry point.
- Setting a fake or personal website would reduce credibility.
- Setting `QUICKSTART.md` as a direct link is not a standard homepage practice.
- **Recommendation:** Leave blank until a real product site exists.

### Social Preview / Open Graph Image (About → Social preview)

**Current:** Not set. GitHub will auto-generate from README.

**Audit result:**
- TRAE cannot upload images to GitHub settings via API.
- No existing brand visual asset was found in the repo.
- Auto-generated preview (README content) is acceptable — no fake workaround.
- **Recommendation:** Can be set later with a simple graphic (logo + tagline). Not a blocker.

### Repository Visibility

**Current:** Public. ✅ Correct. Confirmed via WebFetch.

**No change needed.**

---

## README CONSISTENCY AUDIT

Chain: Repository description → README → QUICKSTART → Demo → docs/README.md

| Layer | One-line positioning | Consistent? |
|-------|---------------------|-------------|
| **Repository description** | (not yet set) — suggestion matches README | N/A |
| **README (line 6)** | "An open protocol and evidence infrastructure for trustworthy hard-tech investment intelligence." | — |
| **QUICKSTART.md (line 5)** | "experimental framework for evidence, verification, provenance, and trust-oriented workflows for DeepTech investment intelligence." | ✅ Consistent. Slightly different angle (actual capabilities vs definition), but aligned. |
| **trust_pipeline_demo.py** | Output says DEMO DATA — NOT REAL GOVERNMENT DATA; authority is application-level | ✅ Consistent with governance rules |
| **docs/README.md (line 5)** | "637 tests passing, 0 failed. This signals engineering discipline on a prototype — not production certification." | ✅ Consistent. Honest boundary. |

**No contradictions found.** No README modification needed.

---

## CI BADGE VALIDITY

Badge URL in README: `https://github.com/gzchenhao/open-invest/actions/workflows/tests.yml/badge.svg`

- ✅ Workflow `tests.yml` matches actual workflow file
- ✅ Owner/repo `gzchenhao/open-invest` matches actual remote
- ✅ Badge points to real workflow page
- ⚠️ Badge will show "failing" or "no status" until the fixed workflow completes successfully on remote

---

## CI REMOTE EXECUTION SUMMARY

| Run | Commit | Status | Python 3.11 | Python 3.12 | Cause |
|-----|--------|--------|-------------|-------------|-------|
| Run #1 | `e395bc7` | ❌ FAIL | working-directory wrong | working-directory wrong | P1-5.5 first push |
| Run #2 | (pending) | PENDING — will trigger on this commit push | — | — | Fixed workflow |

CI will be marked PASS only when Run #2 completes successfully on GitHub.

---

## HOW TO APPLY METADATA (Manual Steps)

In your browser, go to:
**https://github.com/gzchenhao/open-invest → Settings → General**

1. **Description** field: paste
   `Experimental framework for evidence, verification, provenance, and trust-oriented workflows for DeepTech investment intelligence.`

2. **Topics** field: paste (space-separated)
   `deeptech investment-intelligence evidence-graph provenance verification trust ai autonomous-driving policy-analysis new-energy semiconductor`

3. **Website** field: Leave blank.

4. **Social preview:** Upload an image if/when available. Otherwise auto-generated is acceptable.

No API/token exposure required. TRAE cannot perform these steps.

---

## KNOWN LIMITATIONS

1. CI run #1 failed due to working-directory mismatch — workflow re-configured, fixed version pending push → remote run #2.
2. TRAE cannot write GitHub settings (description / topics / homepage / social preview) without GitHub API token or credential — per directive, no token requested. Values provided as manual suggestions.
3. Social preview not set — no visual asset created, auto-generated acceptable.
4. Homepage not set — no real product site exists, blank is more credible than placeholder.
5. Python badge (3.11 | 3.12) does not include 3.13/3.14 — conservative matrix for dependency compatibility.

---

*This audit is accurate to observable remote state. Configuration honesty > marketing.*
