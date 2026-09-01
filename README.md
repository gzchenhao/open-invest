# OpenInvest

**An open protocol and evidence infrastructure for trustworthy hard-tech investment intelligence.**

OpenInvest provides a deterministic evidence layer, provenance tracking, and a fail-closed verification boundary for policy and investment intelligence. OpenInvest is currently an experimental framework — not a production system, not a government data source, and not an identity authentication platform.

**Strategic vision:** "The USB-C for DeepTech" — a future trust layer for DeepTech agent interoperability. This is a vision, not a current capability.

[Quick Start](#quick-start) · [Architecture](#architecture) · [Status Matrix](#status-matrix) · [Tests](#testing) · [Docs](#documentation)

---

## Why OpenInvest?

Hard-tech investment intelligence suffers from four problems:

1. **Scattered sources** — policies, incentives, and compliance requirements live in isolated, heterogeneous systems.
2. **Untraceable evidence** — investment claims rarely carry verifiable provenance.
3. **Label-vs-status confusion** — a "government" source label is often mistaken for "verified," inflating trust.
4. **No machine-readable trust boundary** — AI agents cannot distinguish evidence that a human has verified from evidence that merely exists.

OpenInvest addresses this with an **evidence + provenance + verification** architecture where:

- An **agent** may propose evidence.
- A **human authority** may verify evidence.
- The **system** may revoke verification when content changes.
- **No automated path** may restore VERIFIED status.

---

## What Can I Run Today?

```bash
git clone https://github.com/gzchenhao/open-invest.git
cd open-invest/open-invest-protocol
pip install -r requirements.txt
python -m pytest tests/ -q          # 637 tests, 0 failed
python examples/trust_pipeline_demo.py   # see the verification lifecycle (10 steps)
```

The demo shows the complete verification lifecycle: Create Evidence → Agent/System Denied → Human Verification → VERIFIED → Content Change → Revocation → Re-verification. All demo data is **MOCK** — no real government data is included.

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/gzchenhao/open-invest.git
cd open-invest/open-invest-protocol
pip install -r requirements.txt
```

### 2. Run the Test Suite

```bash
python -m pytest tests/ -q
```

**Expected:** `637 passed, 0 failed` — the test suite covers the JSON-RPC server, client, integration, canonical taxonomy, evidence graph, provenance, trust score, verification event log, human verification gate, content identity, revocation, authority registry, config-driven registry, and the verification showcase demo.

### 3. Run the Trust Verification Showcase Demo

```bash
python examples/trust_pipeline_demo.py
```

**What it shows (10 steps, all via real production APIs):**
1. Create Evidence → UNVERIFIED
2. Agent attempt → DENIED (not human authority)
3. System attempt → DENIED (not human authority)
4. Human Authority verification → VERIFIED
5. MOCK evidence → remains MOCK (can never be VERIFIED)
6. Content change → content_identity changes
7. Change detection → VERIFIED invalid
8. Revocation → UNVERIFIED (revocation event recorded)
9. Human Re-verification → VERIFIED (new content_identity)
10. Event history → append-only log (verified + revoked + verified)

**Sample output:**
```
[4] HUMAN AUTHORITY VERIFICATION
    Verifier: demo-human-verifier (registered, active, human_verifier)
    Result: VERIFIED

[8] REVOCATION
    Revoked: True
    Status After Revocation: UNVERIFIED

[9] HUMAN RE-VERIFICATION
    Result: VERIFIED
    VERIFIED Valid: True
```

**What is MOCK:** All demo data is mock. The demo authority (`demo-human-verifier`) is an application-level demo identifier, NOT real-world identity authentication. See [Verification System](#verification-system) below.

### 4. Start the JSON-RPC Protocol Server (Advanced)

```bash
cd server
python main.py
```

Server starts at `http://localhost:8000` with a JSON-RPC 2.0 `/rpc` endpoint. Returns mock policy data — this is the original protocol layer, not the trust/verification system.

---

## Architecture

```
  Policy / Evidence Sources (mock/sample data)
              │
              ▼
     ┌────────────────────┐
     │   Evidence Layer    │   EvidenceObject · ProvenanceChain · TrustScore
     └────────┬───────────┘
              │
              ▼
     ┌────────────────────┐
     │   Evidence Graph    │   Typed nodes + relations (Policy, Company, Evidence)
     └────────┬───────────┘
              │
              ▼
     ┌────────────────────┐
     │ Verification Layer  │   Durable Event Log (append-only JSONL)
     │                      │   Content Identity (SHA-256 of canonical content)
     └────────┬───────────┘
              │
              ▼
     ┌────────────────────┐
     │ Human Authority Gate│   10 conditions — fail-closed
     │                      │   Authority Registry (config-driven, allowlist)
     └────────┬───────────┘
              │
         VERIFIED (or UNVERIFIED)
              │
              ▼
     ┌────────────────────┐
     │  Change Detection   │   Content change → automatic revocation
     │                      │   Re-verification requires new human decision
     └────────────────────┘
```

### Key Design Principle: Fail-Closed

```
Unknown verifier    → denied (never assumed human)
No registry         → VERIFIED never granted
Inactive verifier   → denied
Role mismatch       → denied
MOCK evidence       → can never become VERIFIED
Content changed     → VERIFIED revoked, no auto-restore
```

The Authority Registry is **application-level authorization**, not real-world identity authentication. No login, OAuth, SSO, or cryptographic identity proof exists in this repository.

---

## Verification System

The verification system (P1-4.1 → P1-4.6) is the core technical asset of OpenInvest. It is **implemented and tested** (611 tests), but operates on mock/sample data only.

| Component | What It Does |
|-----------|-------------|
| **Durable Event Log** | Append-only JSONL log of all verification decisions. Never mutated, never deleted. |
| **Content Identity** | SHA-256 of canonical evidence fields. Detects when verified content has changed. |
| **Human Verification Gate** | 10-condition gate. VERIFIED requires a registered, active human authority + matching content identity + non-MOCK evidence + non-empty evidence refs. |
| **Authority Registry** | Config-driven allowlist of authorized verifiers. Loaded from JSON, fail-closed on all errors. |
| **Automatic Revocation** | When content identity changes, VERIFIED is automatically revoked. A new human decision is required to re-verify. |
| **MOCK / UNVERIFIED / VERIFIED** | Three explicit statuses. MOCK can never become VERIFIED. VERIFIED requires human authority. UNVERIFIED is the default. |

### VERIFIED Gate Conditions (10)

VERIFIED is granted only when ALL of the following are true:

1. A human decision event exists in the durable log
2. The event's decision is `"verified"`
3. The event's `actor_role` is in `{human_verifier, authorized_reviewer}`
4. The event's `content_identity` matches the evidence's current identity
5. The evidence is **not** MOCK
6. The event has non-empty `evidence_refs`
7. The event's `evidence_id` matches the target
8. An Authority Registry is configured
9. The verifier_id is registered **and** active
10. The registered role matches the event's `actor_role`

If any condition fails, VERIFIED is refused.

---

## Status Matrix

| Capability | Status |
|------------|--------|
| JSON-RPC 2.0 Protocol Server | Implemented |
| Client CLI | Implemented |
| Canonical Taxonomy | Implemented |
| Evidence Object + Evidence Graph | Implemented |
| Provenance Chain | Implemented |
| Trust Score Calculator | Implemented |
| Durable Verification Event Log | Implemented |
| Content Identity (SHA-256) | Implemented |
| Human Verification Authority Gate | Implemented |
| Human Authority Registry | Implemented |
| Config-driven Registry Loading | Implemented |
| Content-change Revocation | Implemented |
| Trust Pipeline Demo | Implemented (verification lifecycle showcase) |
| Policy Crawlers | Prototype (mock/sample data) |
| Web Portal (port 8017) | Prototype (mock policy search) |
| Real-world Identity Authentication | Not Implemented |
| Real Government Data | Not Implemented |
| MCP (Model Context Protocol) | Not Implemented |
| A2A (Agent-to-Agent) | Not Implemented |
| Database Persistence | Not Implemented |
| OAuth / SSO / MFA | Not Implemented |
| Production Deployment | Not Implemented |

**Honest boundaries are part of OpenInvest's credibility.** This matrix reflects the repository's actual state, not aspirations.

---

## Testing

```bash
# Full regression suite
python -m pytest tests/ -q

# Specific subsystems
python -m pytest tests/test_verification_infrastructure.py -q   # event log
python -m pytest tests/test_human_verification_gate.py -q       # human gate
python -m pytest tests/test_authority_registry.py -q            # authority registry
python -m pytest tests/test_authority_registry_config.py -q     # config loading
python -m pytest tests/test_source_change_revocation.py -q      # revocation
python -m pytest tests/server/test_server.py -q                 # JSON-RPC server
python -m pytest tests/client/test_client.py -q                 # client
python -m pytest tests/integration/test_integration.py -q       # integration
```

**Current result:** 637 passed, 0 failed.

Test coverage spans: JSON-RPC server endpoints, client logic, end-to-end integration, canonical taxonomy, evidence graph, provenance, trust score, verification event log, human verification gate, authority registry, config-driven registry loading, content-change revocation, verification showcase demo, architecture invariants, and UI mock disclosure.

---

## Documentation

> **Full index:** [`docs/README.md`](docs/README.md) — categorized navigation for all documentation.

### Start Here
- [OpenInvest Core Thesis](docs/OpenInvest_Core_Thesis.md) — why this project exists
- [OpenInvest Trust Architecture](docs/OpenInvest_Trust_Architecture.md) — how the trust layer works
- [OpenInvest Trust Object Model](docs/OpenInvest_Trust_Object_Model.md) — evidence/provenance/verification model

### Architecture
- [Evidence Graph Prototype](docs/Evidence_Graph_Prototype.md) — graph design
- [Evidence Graph + Taxonomy Integration](docs/Evidence_Graph_Taxonomy_Integration_20260830.md) — graph + taxonomy
- [Trust Score Framework](docs/Trust_Score_Framework.md) — scoring model
- [Trust Evidence API](docs/Trust_Evidence_API.md) — API reference

### Verification & Trust
- [Human Verification Authority Gate](docs/Human_Verification_Authority_Gate_20260831.md) — P1-4.3 gate design
- [Human Verification Authority Registry](docs/Human_Verification_Authority_Registry_20260901.md) — P1-4.5 registry
- [Config-driven Registry](docs/Human_Verification_Authority_Registry_Config_20260901.md) — P1-4.6 config loading
- [Source Change Detection & Revocation](docs/Source_Change_Detection_VERIFIED_Revocation_20260901.md) — P1-4.4 revocation
- [Durable Event Log](docs/Real_Policy_Verification_Durable_Event_Log_20260831.md) — P1-4.1 event log
- [Runtime Wiring](docs/Real_Policy_Verification_Runtime_Wiring_20260831.md) — P1-4.2 wiring

### Governance / Security
- [Policy Data Governance](docs/Policy_Data_Governance.md) — data governance rules
- [Public Repository Safety Status](docs/Public_Repository_Final_Safety_Status.md) — safety audit
- [MCP / A2A Future Architecture](docs/MCP_A2A_Future_Architecture.md) — future (not implemented)

### Development
- [API Specification](docs/API.md) — endpoint reference
- [Contributing Guide](CONTRIBUTING.md) — how to contribute

### Audit & Historical
- [Public Product DX Audit](docs/Public_Product_DX_Audit_20260901.md) — P1-5 audit
- [Canonical Taxonomy Registry](docs/Canonical_Taxonomy_Registry_Implementation_20260826.md) — taxonomy implementation
- [Canonical Taxonomy Integration](docs/Canonical_Taxonomy_Integration_20260827.md) — taxonomy integration

---

## Project Structure

```
open-invest-protocol/
├── src/trust/                    # Trust & Verification System (Implemented)
│   ├── verification_event_log.py #   Event log + Human gate + Authority registry
│   ├── trust_service.py          #   Service boundary
│   ├── evidence_object.py        #   Evidence model
│   ├── evidence_graph.py         #   Evidence graph
│   ├── provenance.py             #   Provenance chain
│   ├── trust_score.py            #   Trust score calculator
│   └── graph_query_engine.py     #   Graph queries
├── server/                       # JSON-RPC Protocol Server (Implemented)
│   ├── main.py                   #   FastAPI + JSON-RPC 2.0 /rpc endpoint
│   └── services/                 #   Business logic
├── client/                       # Client CLI (Implemented)
├── schema/                       # Protocol types + canonical taxonomy
├── examples/                     # Demos
│   ├── trust_pipeline_demo.py    #   Verification lifecycle showcase demo
│   └── trust_demo/               #   Mock demo data
├── tests/                        # 637 tests, 0 failed
├── docs/                         # Documentation
├── policy_crawler/               # Policy crawlers (prototype, mock data)
├── global_policy_aggregator/     # China policy intelligence (prototype)
└── requirements.txt
```

---

## Contributing

We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

**Good first contributions:**
- Documentation improvements
- Test coverage expansion
- Demo fixes (e.g., extending the verification showcase demo)
- Example scripts

**Do not contribute:**
- Changes to verification semantics without discussion
- Fake government data or fake verification claims
- Production deployment claims without evidence

---

## License

MIT License — see [LICENSE](LICENSE).

---

<div align="center">

**OpenInvest** — Evidence infrastructure for trustworthy hard-tech investment intelligence.

Experimental framework · 637 tests · No real government data · No identity authentication

⭐ If this project's technical direction is interesting, consider giving it a star.

</div>
