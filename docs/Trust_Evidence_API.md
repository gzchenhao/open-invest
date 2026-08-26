# Trust Evidence API - Experimental Service Boundary

**Current Status**: Runnable internal trust service prototype  
**API Version**: 1.0.0-experimental  
**Quest**: P1-2.2 - Trust Evidence API Boundary

---

## Executive Summary

The Trust Evidence API provides an **experimental internal Python service boundary** for OpenInvest's Trust Evidence System. This is **NOT** an MCP Server or A2A Service — it's a stable internal interface designed for future Agent integration.

### Current Capability
- ✅ Runnable experimental trust service
- ✅ Internal Python service boundary  
- ✅ Mock data with proper governance
- ✅ Evidence creation and retrieval
- ✅ Trust score calculation with detailed explanation
- ✅ Evidence graph query capabilities
- ✅ Safety gates (no unauthorized status upgrades)

### Future Integration Points
- 🔄 MCP-compatible trust tools (future implementation)
- 🔄 A2A-compatible trust exchange (future implementation)  
- 🔄 Cross-agent trust negotiation (future implementation)

---

## API Service Boundaries

### Explicit Limitations
```
MCP integration: NOT IMPLEMENTED
A2A integration: NOT IMPLEMENTED
External network access: NOT IMPLEMENTED
Production verification: NOT IMPLEMENTED
```

### What This API Provides
- Internal Python service methods for trust operations
- Stable request/response contracts for future Agent integration
- Machine-readable trust query language prototype
- Safety mechanisms preventing unauthorized verification status changes

### What This API Does NOT Provide
- No external HTTP/REST endpoints (yet)
- No MCP tool definitions (yet)
- No A2A message protocols (yet)
- No production-grade verification (mock data only)

---

## Core Service Interface

### TrustEvidenceService

The main service boundary for trust evidence operations.

#### Service Status
```python
{
    "success": true,
    "status": {
        "is_ready": true,
        "service_name": "OpenInvest Trust Evidence Service",
        "version": "1.0.0-experimental",
        "capabilities": [
            "Evidence creation and management",
            "Provenance tracking",
            "Trust scoring", 
            "Evidence graph queries",
            "Trust decision explanations"
        ],
        "limitations": [
            "Experimental prototype only",
            "Uses MOCK data only",
            "No real verification",
            "No production-ready claims",
            "No external network access"
        ]
    }
}
```

#### Core Methods

**create_evidence(evidence_data)**  
Create new evidence object with proper governance.

```python
trust_service.create_evidence({
    "id": "policy_china_ai_2024",
    "type": "policy",
    "source": "mock",  # Always mock in current version
    "source_reference": "demo_source",
    "verification_status": "MOCK",  # Never automatically upgraded
    "confidence_score": 0.5,
    "metadata": {}
})
```

**get_evidence(evidence_id)**  
Retrieve evidence with provenance and trust information.

```python
trust_service.get_evidence("policy_china_ai_2024")
# Returns: evidence, provenance_chain, verification_status, integrity_status
```

**verify_evidence(evidence_id, verification_method)**  
Verify evidence (mock implementation only).

```python
trust_service.verify_evidence("policy_china_ai_2024", "mock")
# Always returns MOCK status, never upgrades to VERIFIED
```

**calculate_trust(evidence_id)**  
Calculate trust score with detailed explanation.

```python
trust_service.calculate_trust("policy_china_ai_2024")
# Returns: trust_score, confidence, reason[], confidence_factors{}, warning
```

**query_evidence_graph(query_type, **kwargs)**  
Query evidence graph using high-value query engine.

```python
trust_service.query_evidence_graph("trace_provenance", evidence_id="...")
trust_service.query_evidence_graph("find_supporting_evidence", evidence_id="...")
trust_service.query_evidence_graph("find_policy_sources", policy_type="ai_policy")
```

---

## Request/Response Contracts

### Stable Request Models

**TrustEvidenceRequest**
```python
@dataclass
class TrustEvidenceRequest:
    evidence_id: str
    evidence_type: EvidenceType
    source: str
    source_reference: str
    verification_status: VerificationStatus  # Always MOCK/UNVERIFIED
```

**TrustQueryRequest**  
```python
@dataclass
class TrustQueryRequest:
    evidence_id: str
    query_type: QueryType
    query_params: Dict[str, Any] = field(default_factory=dict)
```

### Stable Response Models

**TrustEvidenceResponse**
```python
@dataclass
class TrustEvidenceResponse:
    success: bool
    evidence_id: str
    evidence: Dict[str, Any]
    evidence_type: EvidenceType
    verification_status: VerificationStatus  # Never VERIFIED automatically
    provenance_chain: List[ProvenanceInfo]
    trust_score: Optional[TrustScoreInfo]
```

**TrustQueryResponse**
```python
@dataclass  
class TrustQueryResponse:
    success: bool
    query_type: QueryType
    evidence_id: str
    trust_assessment: TrustScoreInfo
    warning: str  # Always includes prototype warning
    message: str
```

---

## Trust Query Language (Experimental)

The API defines a machine-readable "Trust Query Language" for Agents.

### Supported Query Types

**Provenance Questions**
- `who_created`: WHO created this evidence?
- `where_came_from`: WHERE did it come from?  
- `when_created`: WHEN was it created?
- `has_modified`: HAS it been modified?

**Trustworthiness Questions**  
- `why_trust`: WHY should I trust it?
- `what_supports`: WHAT evidence supports it?
- `what_unverified`: WHAT is still unverified?

**Analysis Questions**
- `evidence_trace`: Trace evidence chain
- `trust_calculation`: Explain trust score calculation
- `integrity_check`: Check data integrity

### Query Example

```python
from trust.trust_query_contract import TrustQueryContract, TrustQueryType, TrustQueryExecutor

query = TrustQueryContract("evidence_id", TrustQueryType.WHY_TRUST)
executor = TrustQueryExecutor(trust_service)
result = executor.execute_query(query)

# Result includes: trust_score, confidence, reason[], warning
```

---

## Evidence Graph Query MVP

The API provides high-value graph queries focused on explainability rather than complexity.

### Available Queries

**find_supporting_evidence(evidence_id, max_depth)**  
Find evidence that supports the given evidence.

**find_policy_sources(policy_type)**  
Find all policy sources for a specific policy type.

**find_company_evidence(company_name, sector)**  
Find evidence related to a specific company or sector.

**find_related_evidence(evidence_id, relation_types, max_depth)**  
Find evidence with specific relationship types.

**trace_provenance(evidence_id, max_depth)**  
Trace the provenance chain for evidence.

**explain_trust_path(evidence_id, target_type)**  
Explain the trust path from evidence to target type.

### Graph Query Focus

The graph query engine focuses on **explainable, traceable queries** rather than complex graph algorithms. This is designed to answer Agent questions like:

- "Why should I trust this company?"
- "What policy supports this technology?"  
- "Trace the evidence chain for this claim"

---

## Trust Decision Explanation

The API provides detailed trust score explanations, not just scores.

### Score Output Format

```python
{
    "trust_score": 0.72,
    "confidence": "medium",  # low/medium/high
    "reason": [
        "Evidence source exists",
        "Provenance chain intact", 
        "Verification status = MOCK",
        "Supporting evidence = 3",
        "Independent verification = unavailable"
    ],
    "confidence_factors": {
        "overall": "medium",
        "source_reliability": "medium",
        "provenance": "high",
        "verification": "low"
    },
    "warning": "This is experimental prototype data with no authoritative verification"
}
```

### Explanation Philosophy

OpenInvest tells Agents **"how much to trust"** AND **"why"**:

- **Not just**: `score = 0.72`
- **But also**: `reason + confidence + warning`

This is crucial for commercial differentiation in Agent-to-Agent trust.

---

## Safety Gates

The API includes multiple safety mechanisms to prevent trust misrepresentation.

### Core Safety Principle

**No API can automatically upgrade UNVERIFIED to VERIFIED based on caller requirements.**

### Implemented Safety Tests

**TEST-TRUST-API-001: No Verified Claims**  
API never claims to provide VERIFIED data, always maintains proper status disclosure.

**TEST-TRUST-API-002: Mock Data Remains Mock**  
MOCK data is never accidentally upgraded or misrepresented as verified data.

**TEST-TRUST-API-003: Provenance Modification Detection**  
Any modifications to evidence provenance can be detected through integrity checks.

**TEST-TRUST-API-004: Trust Score Requirements**  
Trust score calculations always include confidence level and detailed reasoning.

**TEST-TRUST-API-005: No MCP/A2A Implementation Claims**  
API does not falsely claim MCP or A2A implementation when these are future features.

---

## Mock Agent Simulation

The API includes mock investment Agent demonstrations to validate Agent integration patterns.

### Mock Agent Workflow

```python
# Agent Query
"Assess the trustworthiness of this policy evidence."

# OpenInvest Response
{
    "verification_status": "MOCK",
    "integrity": "VALID", 
    "confidence": "0.62",
    "supporting_evidence": 3,
    "trust_score": "0.71",
    "explanation": "This result is based on prototype scoring rules and mock evidence. No authoritative verification has been performed."
}
```

### Simulation Files

- `examples/trust_demo/mock_investment_agent.py`: Mock investment Agent demonstration
- `examples/trust_demo/run_demo.py`: Simple demonstration runner

---

## Current vs Future Architecture

### Current (Experimental Prototype)
```
Investment Agent
       ↓
[Internal Python Service Boundary]
       ↓
Trust Evidence Service
       ↓
Evidence Graph + Provenance
```

### Future (MCP/A2A Integration)
```
Investment Agent
       ↓
MCP Tool / A2A Message
       ↓
OpenInvest Trust Service
       ↓
Evidence Graph + Provenance
```

The current API creates a **stable internal contract** that can be naturally mapped to future MCP tools and A2A protocols.

---

## Technical Specifications

### Module Structure
```
src/trust/
├── trust_service.py              # Main service boundary
├── trust_request_response.py     # Request/response models  
├── trust_query_contract.py       # Query contract definitions
├── graph_query_engine.py         # Graph query capabilities
├── evidence_object.py            # Evidence data model
├── provenance.py                 # Provenance tracking
├── trust_score.py                # Trust calculation
└── evidence_graph.py             # Graph structure
```

### Test Coverage
- **Total Tests**: 164 passed / 1 warning
- **Safety Tests**: 6 dedicated API safety tests
- **Regression**: All existing tests pass (0 failures)
- **Coverage**: Trust Evidence API comprehensive coverage

---

## Usage Guidelines

### For Developers

1. **Never assume verification**: Always check `verification_status` field
2. **Always check warnings**: `warning` field contains important prototype status  
3. **Respect confidence levels**: Low confidence means low trust
4. **Use query contract**: Prefer `TrustQueryContract` over direct method calls
5. **Trust reasons over scores**: Detailed reasons explain the score

### For Future Agent Integration

1. **Map to MCP tools**: Convert request/response models to MCP tool schemas
2. **Map to A2A messages**: Use stable contracts for Agent-to-Agent communication
3. **Respect boundaries**: Do not assume external access or production verification
4. **Preserve safety**: Maintain UNVERIFIED → VERIFIED upgrade restrictions

---

## Governance Principles

### Trust Evidence API Governance

1. **Transparency**: Always disclose experimental/mock status
2. **No Misrepresentation**: Never claim capabilities that don't exist
3. **Upgrade Safety**: Never auto-upgrade verification status
4. **Explainability**: Always provide reasons, not just scores
5. **Future Clarity**: Clearly distinguish current vs future capabilities

---

## Status and Next Steps

### Current Status (P1-2.2 Complete)
- ✅ Experimental trust service boundary established
- ✅ Stable request/response contracts defined  
- ✅ Machine-readable query language implemented
- ✅ Evidence graph query MVP functional
- ✅ Trust decision explanation enhanced
- ✅ Mock agent simulation created
- ✅ Safety gates implemented (6 tests)
- ✅ Regression test passed (164/0)
- ✅ Documentation completed

### Next Steps (Future Quests)
- 🔄 MCP tool layer implementation
- 🔄 A2A protocol mapping
- 🔄 External HTTP/REST endpoints  
- 🔄 Production verification capabilities
- 🔄 Real data integration
- 🔄 Agent trust negotiation protocols

---

## Contact and Contribution

This is an experimental prototype designed to validate the Trust Layer for the DeepTech Agent Economy. Contributions should respect the experimental nature and safety boundaries defined in this API.

**Quest**: P1-2.2 - Trust Evidence API Boundary  
**Status**: Complete (August 26, 2026)  
**Next**: P1-2.3 (Future - MCP/A2A Integration)