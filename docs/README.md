# OpenInvest Documentation Index

This is the navigation hub for all OpenInvest documentation. If you're new here, follow the **Recommended Reading Path** below.

> **Test suite:** 637 tests passing, 0 failed. This signals engineering discipline on a prototype — not production certification.

---

## Recommended Reading Path

```
Root README  →  Demo  →  Verification Architecture  →  Human Verification  →  Revocation  →  Governance
```

1. **Start here:** [Root README](../README.md) — what OpenInvest is, how to run it
2. **See it work:** [Trust Verification Showcase Demo](Trust_Verification_Showcase_Demo_20260901.md) — 10-step verification lifecycle
3. **Understand the architecture:** [Trust Architecture](OpenInvest_Trust_Architecture.md) — how the trust layer works
4. **Learn the verification boundary:** [Human Verification Authority Gate](Human_Verification_Authority_Gate_20260831.md) — who can grant VERIFIED
5. **See how trust can be revoked:** [Source Change Detection & Revocation](Source_Change_Detection_VERIFIED_Revocation_20260901.md) — content change → auto-revoke
6. **Understand the safety model:** [Public Repository Safety Status](Public_Repository_Final_Safety_Status.md) — fail-closed, no fake claims

---

## 1. Start Here

For first-time visitors. Read these before anything else.

| Document | Why read this? |
|----------|---------------|
| [Root README](../README.md) | What OpenInvest is, how to install, how to run the demo, status matrix |
| [Core Thesis](OpenInvest_Core_Thesis.md) | Why this project exists — the problem it solves |
| [Trust Verification Showcase Demo](Trust_Verification_Showcase_Demo_20260901.md) | The 10-step demo that shows the verification lifecycle end-to-end |
| [Trust Architecture](OpenInvest_Trust_Architecture.md) | High-level architecture of the trust/verification system |

---

## 2. Architecture

Core design documents for the trust/evidence/verification system.

| Document | Status | Why read this? |
|----------|--------|---------------|
| [Trust Object Model](OpenInvest_Trust_Object_Model.md) | IMPLEMENTED | Evidence, Provenance, Verification data models |
| [Trust Score Framework](Trust_Score_Framework.md) | IMPLEMENTED | How trust scores are calculated |
| [Evidence Graph Prototype](Evidence_Graph_Prototype.md) | IMPLEMENTED | Graph structure for evidence relationships |
| [Evidence Graph + Taxonomy Integration](Evidence_Graph_Taxonomy_Integration_20260830.md) | IMPLEMENTED | How the graph integrates with canonical taxonomy |
| [Policy Evidence Graph](Policy_Evidence_Graph.md) | DESIGN | Graph design for policy evidence |
| [Trust Evidence API](Trust_Evidence_API.md) | IMPLEMENTED | API reference for the trust service |
| [API Specification](API.md) | IMPLEMENTED | JSON-RPC protocol endpoint reference |

---

## 3. Verification & Trust

The P1-4.x verification safety chain — OpenInvest's core technical asset.

| Document | Status | Why read this? |
|----------|--------|---------------|
| [Durable Verification Event Log](Real_Policy_Verification_Durable_Event_Log_20260831.md) | IMPLEMENTED | Append-only JSONL log — the foundation of the verification chain (P1-4.1) |
| [Runtime Wiring](Real_Policy_Verification_Runtime_Wiring_20260831.md) | IMPLEMENTED | How EventLog connects to TrustEvidenceService (P1-4.2) |
| [Verification Workflow Design](Real_Policy_Verification_Workflow_Design_20260831.md) | IMPLEMENTED | End-to-end verification workflow design |
| [Human Verification Authority Gate](Human_Verification_Authority_Gate_20260831.md) | IMPLEMENTED | The 10-condition gate that controls VERIFIED (P1-4.3) |
| [Source Change Detection & Revocation](Source_Change_Detection_VERIFIED_Revocation_20260901.md) | IMPLEMENTED | Content change → automatic VERIFIED revocation (P1-4.4) |
| [Human Verification Authority Registry](Human_Verification_Authority_Registry_20260901.md) | IMPLEMENTED | Application-level verifier allowlist (P1-4.5) |
| [Authority Registry Config](Human_Verification_Authority_Registry_Config_20260901.md) | IMPLEMENTED | Config-driven registry loading, fail-closed (P1-4.6) |

**Key boundary:** Authority Registry = application-level authorization, NOT real-world identity authentication.

---

## 4. Governance & Safety

How OpenInvest stays honest about its boundaries.

| Document | Why read this? |
|----------|---------------|
| [Policy Data Governance](Policy_Data_Governance.md) | Rules for data governance, source labels, and verification status |
| [Public Repository Safety Status](Public_Repository_Final_Safety_Status.md) | Safety audit — what is safe to publish, what is not |
| [Agent Trust Model](Agent_Trust_Model.md) | How agents interact with the trust system (design) |
| [Agent Trust Protocol Blueprint](Agent_Trust_Protocol_Blueprint.md) | Future agent-to-trust protocol (design only) |
| [MCP / A2A Future Architecture](MCP_A2A_Future_Architecture.md) | Future integration architecture (NOT IMPLEMENTED) |

---

## 5. Development

For contributors and developers.

| Document | Why read this? |
|----------|---------------|
| [Contributing Guide](../CONTRIBUTING.md) | How to contribute — what's welcome, what's not |
| [Technical Handover](../OpenInvest_Technical_Handover_Trae_20260831.md) | Current engineering state, quest history, known findings |
| [Canonical Taxonomy Integration](Canonical_Taxonomy_Integration_20260827.md) | How canonical taxonomy is integrated into the codebase |

---

## 6. Historical

Earlier audit reports, acceptance reports, and positioning documents. Useful for context, but later quests may have superseded specific details.

| Document | Why read this? |
|----------|---------------|
| [P1-2 Trust Evidence Prototype Acceptance](P1-2_Trust_Evidence_Prototype_Acceptance.md) | P1-2 acceptance report — prototype milestone |
| [Trust Evidence Prototype Status](Trust_Evidence_Prototype_Status.md) | Early prototype status snapshot |
| [Canonical Taxonomy Registry Implementation](Canonical_Taxonomy_Registry_Implementation_20260826.md) | Taxonomy registry implementation (P1-1 era) |
| [Canonical Taxonomy Integration — Independent Verification](Canonical_Taxonomy_Integration_Independent_Verification_20260827.md) | Independent verification of taxonomy integration |
| [Canonical Taxonomy Runtime Integration Test Closure](Canonical_Taxonomy_Runtime_Integration_Test_Closure_20260829.md) | Test closure for taxonomy runtime integration |
| [Industry Taxonomy Audit](Industry_Taxonomy_Audit_20260826.md) | Audit of industry taxonomy alignment |
| [Industry Taxonomy Alignment Design](Industry_Taxonomy_Alignment_Design.md) | Design for taxonomy alignment |
| [Historical Data Exposure Audit](Historical_Data_Exposure_Audit_20260824.md) | Early audit of data exposure risks |
| [Public Product DX Audit](Public_Product_DX_Audit_20260901.md) | P1-5 audit of GitHub-facing developer experience |
| [OpenInvest Positioning Framework](OpenInvest_Positioning_Framework.md) | Product positioning framework |
| [DeepTech Agent Economy Positioning](DeepTech_Agent_Economy_Positioning.md) | Positioning in the DeepTech agent economy |
| [Investor Narrative Guide](Investor_Narrative_Guide.md) | Narrative guide for investors |
| [Examples](examples/) | Code examples (basic usage, advanced usage, agent demos) |

---

## Status Legend

| Label | Meaning |
|-------|---------|
| **IMPLEMENTED** | Code exists, tested, integrated |
| **DESIGN** | Design document, may or may not be implemented |
| **NOT IMPLEMENTED** | Explicitly not yet built |
| **PROTOTYPE** | Code exists but uses mock/sample data |

---

## Quick Facts

- **Tests:** 637 passing, 0 failed
- **Verification chain:** P1-4.1 → P1-4.6 complete (event log → gate → registry → revocation)
- **Real government data:** None — all data is mock/sample
- **Authentication:** None — Authority Registry is application-level only
- **MCP / A2A:** Not implemented
- **Database:** Not implemented — file-based (JSONL) only

---

*Honest boundaries are part of OpenInvest's credibility. This index reflects the repository's actual state.*
