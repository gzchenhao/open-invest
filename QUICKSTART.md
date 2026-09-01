# Quickstart — OpenInvest Verification Lifecycle

**Goal:** From zero to seeing the verification lifecycle in under 2 minutes.

> OpenInvest is currently an experimental framework for evidence, verification, provenance, and trust-oriented workflows for DeepTech investment intelligence. It is **not** production-ready, **not** a government verification platform, and **not** an authenticated identity system.

---

## Prerequisites

- Python 3.10+ (tested on 3.14)
- pip
- git

No database. No external services. No authentication. No real government data.

---

## Step 1 — Clone & Install (30 seconds)

```bash
git clone https://github.com/gzchenhao/open-invest.git
cd open-invest/open-invest-protocol
pip install -r requirements.txt
```

## Step 2 — Run the Verification Lifecycle Demo (10 seconds)

```bash
python examples/trust_pipeline_demo.py
```

You will see the complete verification lifecycle in 10 steps, all executed via real production APIs.

### What you'll see:

```
[1] CREATE EVIDENCE
    Status: UNVERIFIED
    Content Identity: b4c2018cb369724b...

[2] AGENT ATTEMPT
    Result: DENIED  ← agents cannot grant VERIFIED

[3] SYSTEM ATTEMPT
    Result: DENIED  ← systems cannot grant VERIFIED

[4] HUMAN AUTHORITY VERIFICATION
    Result: VERIFIED  ← registered human verifier grants VERIFIED

[5] MOCK EVIDENCE
    Status After Attempt: MOCK  ← MOCK can never become VERIFIED

[6] CONTENT CHANGE
    Changed: True  ← content identity is now different

[7] CHANGE DETECTION
    VERIFIED Valid: False  ← old verification no longer valid

[8] REVOCATION
    Status After Revocation: UNVERIFIED  ← automatic revocation

[9] HUMAN RE-VERIFICATION
    Result: VERIFIED  ← new human decision, new content identity

[10] EVENT HISTORY (append-only)
    [1] verified  — demo-human-verifier
    [2] revoked   — system (content change)
    [3] verified  — demo-human-verifier (re-verification)
```

### 7 Key State Transitions to Understand

| Step | Transition | Why it matters |
|------|-----------|---------------|
| 1 → 4 | UNVERIFIED → VERIFIED | Only a registered human authority can grant VERIFIED |
| 2, 3 | Agent/System → DENIED | Automated paths are structurally blocked |
| 5 | MOCK → stays MOCK | MOCK evidence can never become VERIFIED |
| 4 → 6 | VERIFIED → content changed | Content identity (SHA-256) detects any change |
| 6 → 8 | Changed → REVOKED | VERIFIED is automatically revoked on content change |
| 8 → 9 | UNVERIFIED → VERIFIED | Re-verification requires a **new** human decision |
| 10 | Append-only log | History is never deleted or mutated |

### Safety Principle (printed at end of demo)

```
Agent may recommend.
Human authority may verify.
System may revoke.
No automated path may restore VERIFIED.
```

---

## Step 3 — Run the Test Suite (15 seconds)

```bash
python -m pytest tests/ -q
```

**Expected:** `637 passed, 0 failed`

This covers: JSON-RPC server, client, integration, canonical taxonomy, evidence graph, provenance, trust score, verification event log, human verification gate, authority registry, config-driven registry, content-change revocation, and the verification showcase demo.

---

## Current Boundaries — Read This

| Claim | Reality |
|-------|---------|
| "Verified government data" | ❌ All data is mock/sample. No real government data exists. |
| "Identity authentication" | ❌ Authority Registry is application-level allowlist, not real identity. |
| "Production-ready" | ❌ Experimental framework. |
| "MCP / A2A" | ❌ Not implemented. |
| "Database-backed" | ❌ File-based (JSONL) only. |
| "637 tests passing" | ✅ True — signals engineering discipline, not production certification. |

---

## What to Read Next

1. [Trust Verification Showcase Demo](docs/Trust_Verification_Showcase_Demo_20260901.md) — detailed demo documentation
2. [Trust Architecture](docs/OpenInvest_Trust_Architecture.md) — how the trust layer works
3. [Human Verification Authority Gate](docs/Human_Verification_Authority_Gate_20260831.md) — the 10-condition VERIFIED gate
4. [Full Documentation Index](docs/README.md) — all docs categorized

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'trust'` | Run from `open-invest-protocol/` directory, not from repo root |
| `NameError: step1_create_evidence_objects` | Fixed in P1-5.2. Pull latest: `git pull origin master` |
| Port 8000 already in use (JSON-RPC server) | Only needed for advanced usage, not for the demo |

---

*Experimental framework · 637 tests · No real government data · No identity authentication*
