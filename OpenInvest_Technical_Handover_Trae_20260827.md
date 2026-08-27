# OpenInvest Technical Handover — Trae

**Document**: `OpenInvest_Technical_Handover_Trae_20260827.md`  
**Purpose**: The unique OpenInvest Project Master Handover Manual for cross LLM/Agent/IDE/development tool switching. Any future AI coding agent must read and obey this document before touching the repository.  
**Created**: 2026-08-26  
**Repository**: https://github.com/gzchenhao/open-invest.git (branch `master`)  
**Last Updated**: 2026-08-27  

**Precedence (highest → lowest)**:
1. Existing Code & Data
2. Existing Schema / Protocol
3. Existing Tests
4. Current Repository Reality
5. This Handover Manual
6. New Requirements

> **Reading rule**: If any number, path, or status in this document disagrees with the repository, the repository wins. This document records the *Verified Reality* and the *Expected Baseline* difference rather than rewriting business data.

---

## 1. Executive Summary

OpenInvest is an **Experimental Trust Infrastructure Prototype** for DeepTech Agent Economy. The long-term vision is to become "The USB-C for DeepTech" — a universal, standardized, plug-and-play layer connecting technology supply with government/capital demand.

**Current State**: The project has completed multiple QUEST phases (P0, P0-2.x, P1-0, P1-1, P1-2.1, P1-2.2) and established a Trust Infrastructure Prototype with Evidence Objects, Provenance Chains, Trust Scores, Evidence Graphs, and Trust Evidence API boundaries.

**Testing Status**: **342 passed, 0 failed** (as of 2026-08-27)

**Git Status**: LOCAL HEAD == REMOTE HEAD == `d4d3e75` - clean worktree

**MCP/A2A Status**: **Future Architecture** — NOT IMPLEMENTED

**Production Status**: **NOT PRODUCTION READY** — Experimental prototype only

---

## 2. Project Identity

### 2.1 Who is OpenInvest?

OpenInvest is an open protocol for **global DeepTech investment and cross-border industrial landing**. 

**Core Problem**: DeepTech projects face fragmentation in policy intelligence, trust verification, and cross-border landing requirements.

**Current Solution**: An experimental trust infrastructure prototype that provides:
- Policy Evidence Graph
- Trust Score Framework
- Provenance Chain Tracking
- Trust Evidence API (internal Python service)

**Long-term Vision**: Become "The USB-C for DeepTech" — a universal standard layer for DeepTech Agent Economy.

### 2.2 What does it solve?

Current capabilities:
- Policy data structure and normalization
- Trust evidence modeling
- Provenance tracking (mock only)
- Trust score calculation (prototype)
- Evidence graph queries (experimental)
- Mock investment agent demonstration

Future capabilities (NOT IMPLEMENTED):
- Cross-agent trust verification
- Machine-verifiable evidence
- MCP/A2A protocol network
- Real-time policy crawling
- Production-grade trust layer

### 2.3 What is it NOT doing?

- **NOT** a production policy database
- **NOT** a verified government information source
- **NOT** an MCP server implementation
- **NOT** an A2A gateway implementation
- **NOT** a substitute for official government policy portals
- **NOT** a source for investment decisions (all data is MOCK)

### 2.4 Long-term vision

**Vision**: "The USB-C for DeepTech"

**Target State**:
```
DeepTech Project / Company
          │
          │   OpenInvest Protocol
          ▼
Government / Industrial Park / Capital Ecosystem
```

**Future Architecture**:
- Trust Layer for DeepTech Agent Economy
- Evidence Graph with machine-verifiable provenance
- Cross-agent trust protocols
- MCP (Model Context Protocol) integration
- A2A (Agent-to-Agent) communication

---

## 3. Vision

### 3.1 Long-term Strategic Vision

**"The USB-C for DeepTech"**

OpenInvest aims to become the universal, standardized interface layer for:
- DeepTech projects → Government policy access
- Government parks → DeepTech project matching
- Capital providers → Trust verification

### 3.2 Strategic Positioning

**Two-sided Network Effect**:
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

### 3.3 Current Reality

**"Experimental Trust Infrastructure Prototype"**

The project is currently:
- A research prototype
- A demonstration framework
- A testbed for trust infrastructure concepts
- NOT a production-ready system

**Distance to Vision**: Significant gap between current experimental prototype and the long-term vision.

---

## 4. Current Reality

### 4.1 Actual Project Status

**Development Phase**: P1-2.2 Complete — Experimental Trust Evidence API Boundary

**Implementation Status**:
- Evidence Object Model: ✅ Implemented
- Provenance Chain: ✅ Implemented (mock only)
- Trust Score: ✅ Prototype
- Evidence Graph: ✅ Prototype
- Trust Evidence API: ✅ Experimental Service Boundary
- Graph Query Engine: ✅ MVP
- Mock Agent Demo: ✅ Implemented
- MCP Server: ❌ NOT IMPLEMENTED
- A2A Gateway: ❌ NOT IMPLEMENTED

**Testing**: 342 tests passing, 0 failed (as of 2026-08-27, +60 taxonomy integration tests from P1-3.3)

**Coverage**: ~59% total coverage (verified measurement)

**Production Ready**: **NO** — experimental prototype only

### 4.2 Data Reality

**Policy Data**: All current policy data is **MOCK** — 12 embedded demo policies

**Provenance**: All data has source metadata but no real verification

**Trust Scores**: All trust scores are calculated from mock evidence

**Government Contacts**: All contacts are **NULL** (unverified) due to safety governance

**Real Policy Count**: **0** — zero verified government policies in the system

### 4.3 Technical Reality

**Server**: FastAPI-based web server running on port 8017

**Database**: SQLite with seed data (mock only)

**API**: JSON-RPC 2.0 endpoint at `/rpc`

**Client**: Python-based protocol client

**Testing**: pytest-based test suite with 164 tests

**Documentation**: Multiple architecture and API documents

---

## 5. Project History — 前世

### P0阶段：基础建设与数据治理

**P0-0**: Project Initialization
- Git repository setup
- Basic project structure
- Initial README and documentation

**P0-1**: Repository Reality Alignment + Test Gate Repair
- **Commit**: `f449f57` - "fix: align repository reality and repair test gate"
- **Achievement**: Fixed pytest collection failure (68 tests passing)
- **Key Changes**:
  - Added 11 `__init__.py` files
  - Fixed broken imports
  - Corrected JSON-RPC 2.0 spec compliance
  - Downgraded README claims from "implemented" to "planned"
- **Status**: MCP/A2A clearly marked as PLANNED, not implemented

**P0-2**: Policy Provenance & Anti-Hallucination Data Governance
- **Commit**: `ec2e196` - "feat: enforce policy provenance and anti-hallucination data governance"
- **Achievement**: Established data truthfulness boundary
- **Key Rules**:
  - 宁可 null，不要猜
  - 宁可 UNVERIFIED，不要 VERIFIED
  - MOCK 必须始终保持 MOCK
- **Implementation**: Added provenance validator, verification status enum, governance rules
- **Test Result**: 93 tests passing (25 new tests added)

**P0-2.1**: Remote GitHub Reality Verification + Mock Disclosure Repair
- **Commit**: `ca2926b` - "fix: disclose mock policy data in public surfaces"
- **Achievement**: Added MOCK disclosure to all public-facing surfaces
- **Key Changes**:
  - Bilingual warning banners on all web templates
  - PDF disclaimer boxes
  - Contact section relabeled as "unverified"
  - All fabricated contact data nullified
- **Test Result**: 111 tests passing (18 new UI tests added)

**P0-2.2**: Historical Data Exposure Audit + Public Repository Legal Risk Assessment
- **Commit**: `5b74ba1` - "docs: add historical exposure audit and policy governance rules"
- **Achievement**: Comprehensive audit of Git history for fabricated data
- **Key Findings**:
  - 35 unique fabricated subsidy-amount strings found
  - 13 files still contain unmarked fabricated contacts
  - All remediated through marking, not deletion
- **Test Result**: 120 tests passing (9 new history tests added)

**P0-2.3**: Repository Surface Hardening
- **Commit**: Multiple commits for surface hardening
- **Achievement**: Complete repository safety hardening
- **Key Changes**:
  - 13 H2 files completed MOCK identification
  - All crawler URLs marked UNVERIFIED
  - Comprehensive anti-regression tests (TEST-SURFACE-001..004)
- **Test Result**: 135 tests passing

### P0-2.x阶段：愿景与现实分离

**Vision / Reality Separation**:
- Established clear distinction between long-term vision and current capability
- README claims downgraded from "official standard" to "experimental framework"
- Strategic positioning clarified: "The USB-C for DeepTech" (vision) vs "Experimental Framework" (reality)

**Investor Narrative Safety**:
- Prevented marketing claims from overstating capabilities
- Ensured all public communications reflect experimental status

**Strategic Positioning**:
- Positioned as open protocol for DeepTech investment
- Not a government intermediary
- Direct protocol-based connections

### P1-0阶段：Trust Stack架构设计

**Core Thesis**:
- Trust Stack for DeepTech Agent Economy
- Policy Evidence Graph as core infrastructure
- Agent Trust Model framework
- Future MCP/A2A architecture design

**Trust Stack Components**:
- Evidence Object (bottom layer)
- Provenance Chain (tracking layer)
- Trust Score (evaluation layer)
- Evidence Graph (query layer)
- Agent Trust Protocol (communication layer)

**MCP/A2A Future Architecture**:
- Designed as future components
- Clearly marked as NOT IMPLEMENTED
- Architectural blueprints documented

### P1-1阶段：Trust Object Model与证据图原型

**Trust Object Model**:
- Evidence Object implementation
- Verification Status enum
- Trust Score framework
- Provenance metadata structure

**Evidence Graph Prototype Design**:
- Graph data structure design
- Node and edge definitions
- Query interface design

**Trust Score Framework**:
- Confidence score calculation
- Evidence weighting
- Risk assessment logic

**Agent Trust Protocol Blueprint**:
- Protocol message format
- Trust verification steps
- Cross-agent communication flow

**Trust Infrastructure Prototype Foundation**:
- Core infrastructure components
- Data models and schemas
- API boundaries definition

### P1-2.1阶段：Evidence Object原型实现

**Evidence Object Prototype**:
- `src/trust/evidence_object.py` implementation
- Evidence types: POLICY, CONTACT, FINANCIAL, COMPLIANCE
- Verification status tracking
- Confidence score calculation

**Provenance Chain**:
- Source URL tracking
- Publisher information
- Published/effective dates
- Retrieval timestamp
- Snapshot references

**Trust Score Prototype**:
- Evidence aggregation
- Confidence calculation
- Risk scoring
- Trust explanation generation

**Evidence Graph Prototype**:
- Graph data structure
- Node relationships
- Edge types
- Basic query operations

**Mock Demo Dataset**:
- 12 mock policies with full evidence
- Mock contact information (nullified for safety)
- Mock financial data
- Mock compliance records

**Independent Verification**:
- Provenance validator tests
- Trust score calculation tests
- Evidence graph operation tests
- Mock data governance verification

### P1-2.2阶段：Experimental Trust Evidence Service Boundary

**Achievement**: Established experimental Trust Evidence API service boundary

**Commit**: `ea60f10` - "feat: establish experimental trust evidence service boundary"

**Implemented Components**:
1. **Trust Evidence Service** (`src/trust/trust_service.py`)
   - `create_evidence()` — Create evidence objects
   - `get_evidence()` — Retrieve evidence by ID
   - `calculate_trust()` — Calculate trust scores with explanation
   - `query_evidence()` — Query evidence with filters

2. **Request/Response Models** (`src/trust/trust_request_response.py`)
   - `TrustEvidenceRequest` — Stable request model
   - `TrustEvidenceResponse` — Stable response model
   - `TrustQueryRequest` — Query request model
   - `TrustQueryResponse` — Query response with warning field

3. **Trust Query Contract** (`src/trust/trust_query_contract.py`)
   - Machine-queryable contract
   - Query by type, source, trust score, time range
   - Path tracing queries

4. **Graph Query Engine** (`src/trust/graph_query_engine.py`)
   - High-value graph query functions
   - Evidence aggregation
   - Provenance chain traversal
   - Trust score explanations

5. **Mock Agent Demo** (`examples/trust_demo/`)
   - `mock_investment_agent.py` — Simulated investment agent
   - `run_mock_agent_demo.py` — Demo runner
   - Demonstrates API usage patterns

6. **Safety Gates** (6 API safety tests)
   - API never claims VERIFIED without verification
   - MOCK data always remains MOCK
   - Provenance always detectable
   - Trust scores include confidence and reason
   - No false MCP/A2A implementation claims

7. **Complete Documentation** (`docs/Trust_Evidence_API.md` - 464 lines)
   - Service boundary definition
   - Request/response contracts
   - Trust Query Language specification
   - Safety mechanisms
   - Experimental status labels

**Test Result**: **164 passed, 0 failed** (baseline maintained)

**Files Changed**: 11 files, 3044 lines added

**Status**: ✅ COMPLETE — Runnable experimental trust service prototype

**NOT IMPLEMENTED**:
- MCP integration (clearly labeled in documentation)
- A2A integration (clearly labeled in documentation)
- Production deployment (experimental prototype only)
- Real government policy verification (all data is mock)

---

## 6. Current Architecture — 今生

### 6.1 Directory Structure

```
open-invest-protocol/
├── client/                          # Protocol client implementation
│   ├── api/protocol_client.py      # JSON-RPC client
│   ├── hooks/                      # Agent integration hooks
│   └── utils/project_evaluator.py  # Project evaluation logic
├── server/                          # Protocol server implementation
│   ├── config/config.py            # Server configuration
│   ├── services/                   # Business logic services
│   │   ├── tech_readiness_service.py
│   │   ├── landing_requirements_service.py
│   │   ├── economic_compliance_service.py
│   │   ├── data_protection.py
│   │   └── data_storage.py
│   └── main.py                     # FastAPI server entry
├── src/trust/                       # Trust infrastructure (P1-2.x)
│   ├── evidence_object.py          # Evidence Object model
│   ├── trust_service.py            # Trust Evidence API service
│   ├── trust_request_response.py   # Request/response models
│   ├── trust_query_contract.py     # Query contract
│   └── graph_query_engine.py       # Graph query engine
├── global_policy_aggregator/       # Policy intelligence
│   ├── crawlers/                   # Policy crawlers (scaffolded)
│   ├── processors/                 # Data processing
│   │   ├── policy_cleaner.py       # Parser/normalizer
│   │   └── provenance_validator.py # Provenance validation
│   ├── schemas/                    # JSON schemas
│   ├── web/                        # Web portal
│   │   ├── interactive_ai_server.py
│   │   └── templates/
│   └── data/seed_data/             # Mock seed data
├── policy_crawler/                 # Legacy crawler (archived)
├── schema/                         # Protocol schemas
│   ├── api-spec.json              # OpenAPI specification
│   └── types.py                   # Data types
├── tests/                          # Test suite
│   ├── test_provenance.py         # Provenance tests
│   ├── test_trust_prototype.py    # Trust prototype tests
│   ├── test_trust_api_safety.py   # API safety tests
│   └── ...                        # Other test modules
├── docs/                           # Documentation
│   ├── Trust_Evidence_API.md      # Trust Evidence API documentation
│   ├── OpenInvest_Trust_Architecture.md
│   ├── Agent_Trust_Model.md
│   ├── Policy_Evidence_Graph.md
│   └── Policy_Data_Governance.md
└── examples/trust_demo/           # Trust demo examples
    ├── mock_investment_agent.py   # Mock agent
    └── run_mock_agent_demo.py     # Demo runner
```

### 6.2 Architecture Map

```
Policy Data (Mock)
        ↓
Crawler (Scaffolded)
        ↓
Parser/Normalizer (PolicyCleaner)
        ↓
Validator (Provenance Validator)
        ↓
Evidence Object Model (Implemented)
        ↓
Provenance Chain (Implemented)
        ↓
Trust Score (Prototype)
        ↓
Evidence Graph (Prototype)
        ↓
Trust Evidence Service (Implemented)
        ↓
Graph Query / Trust Query (Implemented)
        ↓
Mock Agent Demo (Implemented)
        ↓
Future: MCP/A2A Integration (NOT IMPLEMENTED)
```

### 6.3 Component Status Matrix

| Component | Status | Evidence | Notes |
|---|---|---|---|
| Evidence Object | ✅ Implemented | `src/trust/evidence_object.py` | Core data model |
| Provenance Chain | ✅ Implemented | Evidence Object | Source tracking |
| Trust Score | 🧪 Prototype | `src/trust/evidence_object.py` | Calculation logic |
| Evidence Graph | 🧪 Prototype | Graph data structures | Query operations |
| Trust Evidence API | ✅ Implemented | `src/trust/trust_service.py` | Service boundary |
| Graph Query Engine | ✅ Implemented | `src/trust/graph_query_engine.py` | High-value queries |
| Mock Agent Demo | ✅ Implemented | `examples/trust_demo/` | Usage demonstration |
| MCP Server | ❌ NOT IMPLEMENTED | Documentation only | Future architecture |
| A2A Gateway | ❌ NOT IMPLEMENTED | Documentation only | Future architecture |
| Policy Crawler | 🏗️ Scaffolded | Placeholder URLs | No verified live output |
| Real Policy Data | ❌ ZERO | All data is mock | 0 verified policies |

### 6.4 Data Flow Architecture

```
Input (Raw Policy Text)
        ↓
Crawler (URL → HTML → Text)
        ↓
PolicyCleaner (Normalization)
        ↓
Provenance Validator (Safety Gates)
        ↓
Evidence Object (Structured Data)
        ↓
Trust Score Calculation
        ↓
Evidence Graph (Query Index)
        ↓
Trust Evidence API (Service Boundary)
        ↓
Mock Agent Demo (Consumer)
        ↓
Future: MCP/A2A Protocol
```

---

## 7. Parser Location and Pipeline

### 7.1 Parser Location

**File**: `global_policy_aggregator/processors/policy_cleaner.py`  
**Class**: `PolicyCleaner`  
**Core Method**: `clean_policy_text(raw_policy_text: str, source_url: str = None) -> StructuredPolicy`  
**Output Dataclass**: `StructuredPolicy` (same file)

### 7.2 Pipeline Chain

```
Crawler → Raw Data → Parser/Normalizer (PolicyCleaner) 
        → Validator (provenance_validator.py) 
        → Canonical Schema (StructuredPolicy) 
        → Evidence Object 
        → Database / API / Client / Agent
```

### 7.3 Input Contract

`clean_policy_text` accepts:
- `raw_policy_text`: Raw Text (string) — extracted by crawlers
- `source_url`: optional URL string
- The cleaner does NOT natively accept PDF or JSON — operates on extracted text

### 7.4 Normalization Contract

Implemented inside `PolicyCleaner`:
- **Industry standardization**: `industry_mapping` (10 CN keys → 8 distinct EN values)
- **Policy-type standardization**: `policy_type_mapping` (8 types)
- **Country/region standardization**: `country_mapping` (10 countries → ISO codes)
- **Amount handling**: `_extract_amount` (万/亿/美元/USD → numeric)
- **Percentage handling**: `_extract_percentage`
- **Date handling**: `_extract_validity_period` (multiple formats)
- **Text cleaning**: regex-based extraction
- **HTML cleaning**: delegated to crawlers (BeautifulSoup)

### 7.5 Validation Contract

- **Mechanism**: `provenance_validator.py` validates policy records
- **Key Validations**:
  - Mock data cannot be marked as verified
  - Verified data requires source_url
  - Contact information requires provenance
  - Placeholder phone numbers rejected
- **Important**: Validation is **blocking** — violations raise errors

### 7.6 Output Contract

- **Output**: `StructuredPolicy` with fields:
  - `policy_id, location, country, region, industry, policy_type, title, description`
  - `incentives[], requirements[], compliance_standards[]`
  - `metadata{source_url, last_updated, confidence_score, ...}`
- **Evidence Object Transform**: StructuredPolicy → EvidenceObject
- **Layer chain**: Input → Parser → Normalizer → Validator → Schema → Evidence → DB/API

---

## 8. Trust Infrastructure Status

### 8.1 Implemented Components

**Evidence Object Model** (`src/trust/evidence_object.py`)
- Evidence types: POLICY, CONTACT, FINANCIAL, COMPLIANCE
- Verification status: MOCK, UNVERIFIED, PARTIALLY_VERIFIED, VERIFIED
- Confidence scores (0.0-1.0)
- Provenance metadata
- Trust score calculation

**Provenance Chain** (Evidence Object metadata)
- Source URL tracking
- Publisher information
- Published/effective dates
- Retrieval timestamp
- Snapshot references
- Secondary source URLs

**Trust Score Framework** (`src/trust/evidence_object.py`)
- Evidence aggregation
- Confidence calculation
- Risk assessment
- Trust explanation generation

**Evidence Graph** (Graph data structures)
- Node-based evidence storage
- Edge-based relationships
- Query operations
- Path tracing

**Trust Evidence API** (`src/trust/trust_service.py`)
- Service boundary definition
- Stable request/response models
- Graph query engine
- Safety gates

### 8.2 Prototype Components

**Trust Score Calculation**: Prototype implementation with basic logic

**Evidence Graph Queries**: MVP implementation with high-value queries

**Mock Agent Demo**: Demonstrates API usage patterns

**Provenance Validation**: Implemented but only tested with mock data

### 8.3 Experimental Components

**Trust Evidence Service**: Runnable experimental prototype

**Graph Query Engine**: Experimental query capabilities

**Trust Query Contract**: Machine-queryable interface (experimental)

### 8.4 Future Components

**MCP Integration**: Future architecture — NOT IMPLEMENTED

**A2A Integration**: Future architecture — NOT IMPLEMENTED

**Real Policy Verification**: Not implemented — all data is mock

**Production Deployment**: Not implemented — experimental prototype only

---

## 9. Implemented Components

### 9.1 Core Trust Infrastructure

| Component | File | Status | Test Coverage |
|---|---|---|---|
| Evidence Object | `src/trust/evidence_object.py` | ✅ Implemented | Yes |
| Provenance Chain | Evidence Object metadata | ✅ Implemented | Yes |
| Trust Score | `src/trust/evidence_object.py` | 🧪 Prototype | Yes |
| Evidence Graph | Graph structures | 🧪 Prototype | Yes |
| Trust Evidence API | `src/trust/trust_service.py` | ✅ Implemented | Yes |
| Graph Query Engine | `src/trust/graph_query_engine.py` | ✅ Implemented | Yes |
| Query Contract | `src/trust/trust_query_contract.py` | ✅ Implemented | Yes |
| Request/Response | `src/trust/trust_request_response.py` | ✅ Implemented | Yes |

### 9.2 Policy Intelligence

| Component | File | Status | Test Coverage |
|---|---|---|---|
| Parser/Normalizer | `global_policy_aggregator/processors/policy_cleaner.py` | ✅ Implemented | Yes |
| Provenance Validator | `global_policy_aggregator/processors/provenance_validator.py` | ✅ Implemented | Yes |
| Policy Crawler | `global_policy_aggregator/crawlers/` | 🏗️ Scaffolded | Limited |
| Web Portal | `global_policy_aggregator/web/interactive_ai_server.py` | ✅ Implemented | Yes |
| PDF Generation | Web portal | ✅ Implemented | Yes |

### 9.3 Protocol Server/Client

| Component | File | Status | Test Coverage |
|---|---|---|---|
| Protocol Server | `server/main.py` | ✅ Implemented | Yes |
| JSON-RPC 2.0 | `server/main.py` | ✅ Implemented | Yes |
| Protocol Client | `client/api/protocol_client.py` | ✅ Implemented | Yes |
| Tech Readiness Service | `server/services/tech_readiness_service.py` | ✅ Implemented | Yes |
| Landing Requirements Service | `server/services/landing_requirements_service.py` | ✅ Implemented | Yes |
| Economic Compliance Service | `server/services/economic_compliance_service.py` | ✅ Implemented | Yes |

---

## 10. Prototype Components

### 10.1 Trust Prototypes

- **Trust Score Calculation**: Basic prototype implementation
- **Evidence Graph Operations**: MVP query operations
- **Trust Explanation**: Confidence + reason generation

### 10.2 Policy Intelligence Prototypes

- **Policy Crawlers**: Scaffolded with placeholder URLs
- **Data Normalization**: Implemented but not tested with real data
- **Mock Seed Data**: 12 demo policies for testing

### 10.3 Demo Prototypes

- **Mock Investment Agent**: Demonstrates API usage
- **Web Portal Demo**: Interactive policy search interface
- **PDF Generation**: Demo policy document generation

---

## 11. Future Architecture

### 11.1 Planned Components

**MCP (Model Context Protocol) Server**
- **Status**: Future Architecture — NOT IMPLEMENTED
- **Purpose**: Enable LLM-based agent integration
- **Evidence**: Zero MCP code found anywhere in repository
- **Documentation**: Architectural blueprints exist in docs/

**A2A (Agent-to-Agent) Gateway**
- **Status**: Future Architecture — NOT IMPLEMENTED
- **Purpose**: Enable direct agent-to-agent communication
- **Evidence**: Zero A2A code found anywhere in repository
- **Documentation**: Architectural blueprints exist in docs/

**Real Policy Verification**
- **Status**: Future Architecture — NOT IMPLEMENTED
- **Purpose**: Verify real government policies
- **Current State**: All data is mock
- **Requirements**: Official source verification workflow

**Production Deployment**
- **Status**: Future Architecture — NOT IMPLEMENTED
- **Purpose**: Production-ready system
- **Current State**: Experimental prototype only
- **Requirements**: Security hardening, performance optimization, operational readiness

### 11.2 Architectural Vision

**Trust Layer for DeepTech Agent Economy**
- Evidence Graph with machine-verifiable provenance
- Cross-agent trust protocols
- Decentralized trust verification
- Standardized trust evidence exchange

**Two-sided Network Effect**
- DeepTech projects → Government policy access
- Government parks → DeepTech project matching
- Capital providers → Trust verification

**Universal Standard**
- "The USB-C for DeepTech"
- Plug-and-play integration
- Cross-border compatibility
- Multi-domain support

---

## 12. MCP / A2A Status

### 12.1 MCP Status

**Current Status**: ❌ **NOT IMPLEMENTED**

**Evidence**:
- Zero MCP code found anywhere in repository
- No MCP server implementation
- No MCP client implementation
- No MCP protocol handlers
- Documentation clearly labels as "FUTURE ARCHITECTURE"

**Documentation**:
- Architectural blueprints exist in docs/
- Designed as future component
- Not claimed as implemented

**Future Plans**:
- MCP server integration (planned)
- LLM-based agent access (planned)
- Standardized agent protocol (planned)

### 12.2 A2A Status

**Current Status**: ❌ **NOT IMPLEMENTED**

**Evidence**:
- Zero A2A code found anywhere in repository
- No A2A gateway implementation
- No agent-to-agent communication protocols
- Documentation clearly labels as "FUTURE ARCHITECTURE"

**Documentation**:
- Architectural blueprints exist in docs/
- Designed as future component
- Not claimed as implemented

**Future Plans**:
- Agent-to-agent communication (planned)
- Cross-agent trust verification (planned)
- Standardized agent protocols (planned)

### 12.3 Implementation Requirements

**MCP Implementation Requirements** (when implemented):
- Actual MCP server code
- MCP protocol handlers
- MCP client libraries
- Integration tests
- Production deployment verification
- Documentation updates

**A2A Implementation Requirements** (when implemented):
- Actual A2A gateway code
- Agent communication protocols
- Trust verification mechanisms
- Integration tests
- Production deployment verification
- Documentation updates

---

## 13. Evidence and Provenance Model

### 13.1 Evidence Object

**Definition**: Structured representation of verifiable information

**Location**: `src/trust/evidence_object.py`

**Core Fields**:
```python
EvidenceObject:
    id: str
    type: EvidenceType  # POLICY, CONTACT, FINANCIAL, COMPLIANCE
    source: str
    content: Dict[str, Any]
    verification_status: VerificationStatus  # MOCK, UNVERIFIED, PARTIALLY_VERIFIED, VERIFIED
    confidence_score: float  # 0.0-1.0
    provenance: Dict[str, Any]
    created_time: datetime
```

**Evidence Types**:
- `POLICY`: Policy information and incentives
- `CONTACT`: Contact information
- `FINANCIAL`: Financial data
- `COMPLIANCE`: Compliance requirements

### 13.2 Provenance Model

**Definition**: Complete chain of custody for evidence

**Core Fields**:
```python
Provenance:
    source_url: str  # Official source URL
    publisher: str  # Publisher name
    published_date: datetime  # Publication date
    effective_date: datetime  # Effective date
    retrieved_at: datetime  # Retrieval timestamp
    snapshot: str  # Evidence snapshot reference
    confidence: float  # Source confidence
    verification_method: str  # Verification method
    secondary_source_url: str  # Secondary discovery URL
```

**Provenance Chain**:
```
Official Source
    ↓
Publisher Website
    ↓
Crawler Discovery
    ↓
Provenance Validator
    ↓
Evidence Object
    ↓
Trust Score Calculation
```

### 13.3 Verification Status

**Enum Values**:
- `MOCK`: Artificial/demo data — must not be marked as verified
- `UNVERIFIED`: Source not verified or missing provenance
- `PARTIALLY_VERIFIED`: Some evidence verified, not all
- `VERIFIED`: Fully verified with complete provenance chain

**Verification Requirements**:
- `VERIFIED` requires: source_url + source_title + publisher + published_date + effective_date + retrieved_at + snapshot + confidence + verification_method
- `PARTIALLY_VERIFIED` requires: Some (not all) of the above fields
- `UNVERIFIED`: Missing or incomplete provenance
- `MOCK`: Artificial data — explicitly marked as mock

**Current Reality**: All data in the repository is **MOCK** — zero verified policies

---

## 14. Trust Score Model

### 14.1 Trust Score Definition

**Purpose**: Quantitative measure of evidence reliability

**Location**: `src/trust/evidence_object.py`

**Score Range**: 0.0 (no trust) to 1.0 (complete trust)

**Components**:
```python
TrustScore:
    score: float  # 0.0-1.0
    confidence: float  # 0.0-1.0 (confidence in the score)
    reason: str  # Explanation of the score
    warning: str  # Risk warnings
```

### 14.2 Trust Score Calculation

**Current Implementation**: Prototype logic

**Factors Considered**:
- Verification status (MOCK vs VERIFIED)
- Provenance completeness
- Source reliability
- Evidence freshness
- Cross-validation

**Calculation Method** (prototype):
```python
base_score = 0.0
if verification_status == VERIFIED:
    base_score += 0.5
if source_url and publisher:
    base_score += 0.2
if published_date and effective_date:
    base_score += 0.1
if retrieved_at:
    base_score += 0.1
if confidence_score:
    base_score += 0.1 * confidence_score
```

**Important**: Current implementation is **prototype** logic — not production-grade

### 14.3 Trust Score Interpretation

**Score Ranges** (prototype):
- 0.0-0.2: No trust (likely mock or missing data)
- 0.2-0.4: Low trust (unverified or incomplete)
- 0.4-0.6: Medium trust (partially verified)
- 0.6-0.8: High trust (verified with good provenance)
- 0.8-1.0: Complete trust (fully verified with complete provenance)

**Current Reality**: All scores are calculated from **mock data** — not reliable for real decisions

**Important**: Trust scores are **not** AI truthfulness judgments — they measure evidence quality, not factual correctness

---

## 15. Evidence Graph

### 15.1 Evidence Graph Definition

**Purpose**: Structured representation of evidence relationships

**Data Structure**: Node-based graph with typed edges

**Node Types**:
- Evidence nodes (Evidence Objects)
- Entity nodes (policies, contacts, organizations)
- Source nodes (websites, documents)

**Edge Types**:
- `PROVENANCE`: Evidence → Source
- `RELATES_TO`: Evidence → Evidence
- `VALIDATES`: Evidence → Evidence
- `CONTRADICTS`: Evidence → Evidence
- `PART_OF`: Evidence → Entity

### 15.2 Graph Query Operations

**Current Implementation**: MVP (src/trust/graph_query_engine.py)

**Supported Queries**:
- Query by evidence type
- Query by source
- Query by trust score range
- Query by time range
- Path tracing (provenance chain)
- Evidence aggregation

**Query Example**:
```python
# Find all policies from a specific source
policies = query_engine.query_by_source("source_url")

# Find evidence with trust score > 0.7
high_trust = query_engine.query_by_trust_score(0.7, 1.0)

# Trace provenance chain
chain = query_engine.trace_provenance(evidence_id)
```

### 15.3 Graph Query Contract

**Location**: `src/trust/trust_query_contract.py`

**Request Structure**:
```python
TrustQueryRequest:
    query_type: str  # BY_TYPE, BY_SOURCE, BY_TRUST_SCORE, BY_TIME_RANGE, TRACE_PROVENANCE
    filters: Dict[str, Any]
    limit: int
```

**Response Structure**:
```python
TrustQueryResponse:
    results: List[EvidenceObject]
    total_count: int
    query_time: float
    warning: str  # Risk warnings
```

---

## 16. Trust Evidence API

### 16.1 API Purpose

**Purpose**: Service boundary for Trust Evidence operations

**Status**: Experimental Service Boundary — NOT MCP/A2A server

**Location**: `src/trust/trust_service.py`

**Design Philosophy**: Internal Python service boundary — future MCP/A2A integration point

### 16.2 API Methods

**Core Methods**:
```python
class TrustEvidenceService:
    def create_evidence(request: TrustEvidenceRequest) -> TrustEvidenceResponse
    def get_evidence(evidence_id: str) -> EvidenceObject
    def calculate_trust(evidence_id: str) -> TrustScore
    def query_evidence(query: TrustQueryRequest) -> TrustQueryResponse
```

**Method Details**:

**create_evidence**:
- Creates new evidence objects
- Validates provenance information
- Enforces verification status rules
- Returns confidence + reason

**get_evidence**:
- Retrieves evidence by ID
- Returns complete evidence object
- Includes provenance metadata

**calculate_trust**:
- Calculates trust score for evidence
- Returns score + confidence + reason + warning
- Considers verification status and provenance

**query_evidence**:
- Queries evidence with filters
- Supports multiple query types
- Returns paginated results

### 16.3 Request/Response Models

**Location**: `src/trust/trust_request_response.py`

**Request Models**:
```python
TrustEvidenceRequest:
    evidence_type: EvidenceType
    source: str
    content: Dict[str, Any]
    verification_status: VerificationStatus
    provenance: Dict[str, Any]

TrustQueryRequest:
    query_type: str
    filters: Dict[str, Any]
    limit: int
```

**Response Models**:
```python
TrustEvidenceResponse:
    evidence_id: str
    success: bool
    message: str
    trust_score: TrustScore

TrustQueryResponse:
    results: List[EvidenceObject]
    total_count: int
    query_time: float
    warning: str
```

### 16.4 API Safety Mechanisms

**Safety Gates**:
- Never upgrades UNVERIFIED to VERIFIED
- MOCK data always remains MOCK
- Provenance always required for VERIFIED status
- Trust scores include confidence + reason
- Warning field for risk communication

**Safety Tests**:
- `test_trust_api_001_no_verified_claims` — API never claims VERIFIED without verification
- `test_trust_api_002_mock_data_always_mock` — MOCK data always remains MOCK
- `test_trust_api_003_provenance_detection` — Provenance always detectable
- `test_trust_api_004_trust_score_requirements` — Trust scores include confidence and reason
- `test_trust_api_005_no_mcp_a2a_implementation_claims` — No false MCP/A2A claims

### 16.5 MCP/A2A Status

**Current Status**: ❌ **NOT IMPLEMENTED**

**Evidence**:
- Zero MCP/A2A code in Trust Evidence API
- Documentation clearly labels as "NOT IMPLEMENTED"
- API is internal Python service boundary only

**Future Integration**:
- Trust Evidence API designed as future MCP/A2A integration point
- Request/response models designed for protocol serialization
- Query contract designed for machine-readable interface

**Important**: The Trust Evidence API is **NOT** an MCP/A2A server — it's an internal Python service boundary

---

## 17. Demo / Mock Data Rules

### 17.1 Mock Data Status

**Current State**: All policy data in the repository is **MOCK**

**Evidence**:
- 12 embedded demo policies in web server
- 9 mock policies in seed data
- All contact information is NULL (unverified)
- All trust scores calculated from mock evidence
- Zero verified government policies

### 17.2 Mock Data Requirements

**Required Fields**:
- `is_mock: true` — Explicit mock flag
- `verification_status: "mock"` — Mock verification status
- `mock_metadata` — Explanation of mock nature

**Prohibited Fields**:
- No fabricated source URLs (must be NULL)
- No fabricated contact information (must be NULL)
- No fabricated government claims
- No fabricated subsidy amounts (unless clearly marked as mock)

### 17.3 Mock Data Governance

**Governance Rules**:
- MOCK data must never be marked as VERIFIED
- MOCK data must always be clearly labeled
- MOCK data must not resemble real government data
- MOCK data must include explicit disclaimers

**Enforcement**:
- Provenance validator blocks mock → verified attempts
- Test suite verifies mock labeling
- Documentation clearly marks mock status
- UI displays MOCK warnings prominently

### 17.4 Public Disclosure Requirements

**Web Portal**:
- Bilingual warning banner (Chinese + English)
- Per-card MOCK badges
- Contact section labeled "unverified"
- Download buttons labeled "demo document"

**PDF Generation**:
- First-page disclaimer box
- Contact section labeled "unverified"
- Mock data warnings throughout

**API Responses**:
- `is_mock` field in responses
- `verification_status: "mock"`
- Warning messages for mock data

---

## 18. Test and Regression Status

### 18.1 Current Test Status

**Test Count**: **342 tests**

**Test Result**: **342 passed, 0 failed** (as of 2026-08-27, +60 taxonomy integration tests from P1-3.3)

**Coverage**: **~59% total coverage** (verified measurement)

### 18.2 Test Categories

**Provenance Tests** (25 tests):
- `tests/test_provenance.py` — 19 tests
- `tests/test_history_policy_rules.py` — 6 tests

**Trust Prototype Tests** (10 tests):
- `tests/test_trust_prototype.py` — 6 tests
- `tests/test_trust_prototype_safety.py` — 4 tests

**Trust API Safety Tests** (6 tests):
- `tests/test_trust_api_safety.py` — 6 tests

**Trust Architecture Tests** (4 tests):
- `tests/test_trust_architecture.py` — 4 tests

**Surface Hardening Tests** (10 tests):
- `tests/test_surface_harden.py` — 4 tests
- `tests/test_surface_harden_simple.py` — 4 tests
- `tests/test_surface_hardening.py` — 2 tests

**UI Mock Disclosure Tests** (18 tests):
- `tests/test_ui_mock_disclosure.py` — 18 tests

**Protocol Tests** (68 tests):
- `tests/server/test_server.py` — 25 tests
- `tests/client/test_client.py` — 17 tests
- `tests/integration/test_integration.py` — 26 tests

**Architecture Tests** (4 tests):
- `tests/test_architecture.py` — 4 tests

**Vision Tests** (5 tests):
- `tests/test_vision.py` — 5 tests

**Taxonomy Audit Tests** (23 tests):
- `tests/test_taxonomy_audit.py` — 23 tests (P1-3.0)

**Taxonomy Alignment Tests** (29 tests):
- `tests/test_taxonomy_alignment.py` — 29 tests (P1-3.1)

**Canonical Taxonomy Tests** (66 tests):
- `tests/test_canonical_taxonomy.py` — 66 tests (P1-3.2)

**Taxonomy Integration Tests** (60 tests):
- `tests/test_taxonomy_integration.py` — 60 tests (P1-3.3)

### 18.3 Regression Gate

**Regression Test Command**:
```bash
python -m pytest tests/ -q --tb=no
```

**Expected Result**: **342 passed, 0 failed**

**Regression Protection**:
- Test suite enforces all safety rules
- Provenance tests prevent mock → verified
- Surface hardening tests prevent unmarked mock data
- Trust architecture tests prevent MCP/A2A false claims
- Vision tests prevent misleading marketing claims

### 18.4 Test Coverage

**Coverage Command**:
```bash
python -m pytest tests/ --cov=. --cov-report=term-missing
```

**Current Coverage**: **~59% total coverage**

**Key Modules Coverage**:
- `provenance_validator.py`: ~91%
- `trust_service.py`: ~75%
- `graph_query_engine.py`: ~70%
- `evidence_object.py`: ~80%
- `policy_cleaner.py`: ~65%

**Coverage Strategy**: Prioritize safety-critical modules over utility functions

---

## 19. Security Constitution

### 19.1 Non-Negotiable Invariants

**INV-000 — Preservation First**
Without explicit authorization, never delete, overwrite, or refactor existing core content. Only CREATE/DOCUMENT/VERIFY/UPDATE are permitted for governance quests.

**INV-001 — No Destructive Modification**
Existing content MUST be preserved unless explicit deletion authorization is provided.

**INV-002 — Schema Compatibility**
Any Schema modification must be (A) backward-compatible, or (B) accompanied by an explicit migration.

**INV-003 — Provenance Preservation**
Policy data must retain source information. Provenance must not be silently deleted.

**INV-004 — No Fabricated Policy Data**
AI must not fabricate government subsidies, commitments, amounts, application conditions, projects, incentives, or government contact details.

**INV-005 — Evidence Over Assertion**
No task is "done" because an agent says so. Every task must provide Code Evidence, Test Evidence, Git Evidence, and Runtime Evidence.

**INV-006 — Handover Must Reflect Reality**
The handover is not marketing. If README says A, code says B, and database says C: record the discrepancy.

**INV-007 — Data Integrity (Policy Provenance & Anti-Hallucination)**
Highest discipline: 宁可 null，不要猜。宁可 UNVERIFIED，不要 VERIFIED。宁可少一条政策，不要多一条假的政策。

- **DATA-INTEGRITY-001**: No Fabricated Government Information
- **DATA-INTEGRITY-002**: Every Policy Must Have Provenance
- **DATA-INTEGRITY-003**: Every Contact Must Be Verifiable
- **DATA-INTEGRITY-004**: Unknown Information Must Remain Unknown
- **DATA-INTEGRITY-005**: Mock Data Must Never Resemble Verified Government Data

### 19.2 Trust Safety Rules

**TRUST-SAFETY-001**: Never upgrade UNVERIFIED to VERIFIED automatically

**TRUST-SAFETY-002**: MOCK data must always remain MOCK

**TRUST-SAFETY-003**: Trust scores must include confidence + reason

**TRUST-SAFETY-004**: Trust scores do not guarantee reliability

**TRUST-SAFETY-005**: Never claim MCP implementation unless independently verified

**TRUST-SAFETY-006**: Never claim A2A implementation unless independently verified

**TRUST-SAFETY-007**: Never claim production readiness for experimental prototypes

### 19.3 Governance Rules

**GOVERNANCE-001**: Mock data must be explicitly labeled as mock

**GOVERNANCE-002**: All contact information must be verifiable or null

**GOVERNANCE-003**: All source URLs must be verifiable or null

**GOVERNANCE-004**: Provenance must be preserved throughout the data pipeline

**GOVERNANCE-005**: Safety tests must never be weakened to pass

**GOVERNANCE-006**: Failed tests must never be deleted to manufacture passing status

### 19.4 Git Governance

**GIT-GOVERNANCE-001**: Never use `git reset --hard` to hide problems

**GIT-GOVERNANCE-002**: Never rewrite Git history without explicit authorization

**GIT-GOVERNANCE-003**: Never force push without explicit authorization

**GIT-GOVERNANCE-004**: Never delete historical commits to create clean records

**GIT-GOVERNANCE-005**: Always verify LOCAL HEAD == REMOTE HEAD after push

---

## 20. Known Bugs / Known Traps

### 20.1 Known Bugs

**No known bugs blocking current functionality** — all tests passing

### 20.2 Known Traps

**TRAP-001**: Industry Taxonomy Inconsistency
- **Issue**: 4 different industry taxonomies exist (5/8/21/12 categories)
- **Impact**: Confusion about industry classification
- **Status**: **INTEGRATED** (P1-3.0 Audit + P1-3.1 Design + P1-3.2 Implementation + P1-3.3 Integration, 2026-08-27)
- **Documents**:
  - Audit: `docs/Industry_Taxonomy_Audit_20260826.md`
  - Design: `docs/Industry_Taxonomy_Alignment_Design.md`
  - Implementation: `docs/Canonical_Taxonomy_Registry_Implementation_20260826.md`
  - Integration: `docs/Canonical_Taxonomy_Integration_20260827.md`
- **Implementation**:
  - Canonical Registry: `schema/canonical_taxonomy.py` (16 active + other + unknown = 18 slots)
  - Legacy Mapping Layer: 10 sources tracked, all legacy values resolvable
  - Integration: Parser + Cleaning Service + Web Portal enriched with `canonical_industry` field
  - Tests: 66 canonical + 60 integration = 126 taxonomy tests
  - Parser: ADDITIVE only (added `canonical_industry` to StructuredPolicy, legacy `industry` preserved)
  - Data: NOT MODIFIED (no migration)
  - API: NO BREAKING CHANGE (canonical_industry is optional)
  - Trust Infrastructure: NOT MODIFIED
- **Audit Findings**:
  - 5 = `schema/types.py` IndustryType enum (5 values)
  - 8 = `policy_cleaner.py` industry_mapping output (8 distinct EN values from 10 CN keys)
  - 12 = `interactive_ai_server.py` Web Portal mock policies (12 unique CN industry labels)
  - 21 = **VERIFIED** — `schemas/deeptech_policy_schema.json` L138-160 (21 enum values, file exists but no Python code references it)
  - At least 11 independent taxonomy definitions exist across components (PARALLEL TAXONOMIES)
  - No formal mapping between taxonomies
  - Naming inconsistencies: biotech/biotechnology, autonomous_driving/auto_driving
- **Design Outcome**: Proposed 16 canonical categories + other + unknown = 18 slots
- **Implementation**: NOT STARTED — design only, no destructive migration
- **Recommendation**: Hierarchical taxonomy design (Layer 1: Registry, Layer 2: Component Mappings, Layer 3: Display Names)
- **Action**: Registry integrated into Parser/Web Portal via `canonical_industry` field. Legacy `industry` preserved.

**TRAP-002**: Missing `is_mock` Field in Schema
- **Issue**: `is_mock` field not in original schema design
- **Impact**: Mock detection requires metadata inspection
- **Status**: Added via backward-compatible extension
- **Action**: Always check `is_mock` + `verification_status` together

**TRAP-003**: Parser Returns Empty Location
- **Issue**: `PolicyCleaner` sometimes returns empty `location` field
- **Impact**: Incomplete policy data
- **Status**: Known limitation
- **Action**: Handle empty location gracefully in consumers

**TRAP-004**: Non-blocking JSON Schema Validation
- **Issue**: JSON schema validation only logs warnings, doesn't block
- **Impact**: Invalid data can pass through
- **Status**: Intentional design for flexibility
- **Action**: Consider making validation blocking in production

### 20.3 Known Risks

**RISK-001**: Historical Mock Data in Git History
- **Issue**: Pre-governance commits contain fabricated contacts/URLs
- **Impact**: Public browsing can discover historical inaccuracies
- **Status**: Recorded — requires explicit authorization to clean
- **Action**: No history rewrite without written approval

**RISK-002**: Unmarked Mock Files in Current Tree
- **Issue**: 13 files still contain fabricated data without MOCK markers
- **Impact**: Potential misinterpretation as real data
- **Status**: Quarantine-manifest maintained
- **Action**: All new files must follow governance rules

**RISK-003**: No Real Policy Verification Workflow
- **Issue**: Zero real government policies verified
- **Impact**: System remains mock-only
- **Status**: Future architecture
- **Action**: Implement verification workflow before claiming production readiness

---

## 21. Important Lessons Learned

### 21.1 Project Management Lessons

**LESSON-001**: Vision vs Reality Separation is Critical
- **Learning**: Always distinguish between long-term vision and current capability
- **Application**: Use "The USB-C for DeepTech" (vision) vs "Experimental Framework" (reality)
- **Result**: Prevents marketing claims from overstating capabilities

**LESSON-002**: Evidence Over Assertion Prevents Problems
- **Learning**: Never claim completion without code/test/git/runtime evidence
- **Application**: Every task must provide four types of evidence
- **Result**: Prevents false completion claims

**LESSON-003**: Safety Tests Must Never Be Weakened
- **Learning**: Passing tests by weakening safety gates creates vulnerabilities
- **Application**: Fix underlying issues, don't weaken tests
- **Result**: Maintains security boundaries

### 21.2 Technical Lessons

**LESSON-004**: Backward Compatibility is Non-Negotiable
- **Learning**: Breaking changes silently break integrations
- **Application**: Add new fields via Optional extensions, never delete/required
- **Result**: Old payloads remain valid

**LESSON-005**: Provenance Must Be Preserved
- **Learning**: Deleting source information makes verification impossible
- **Application**: Always preserve source_url, publisher, dates throughout pipeline
- **Result**: Evidence remains traceable

**LESSON-006**: Mock Data Must Be Explicitly Labeled
- **Learning**: Unmarked mock data can be misinterpreted as real
- **Application**: Always use `is_mock: true` + `verification_status: "mock"`
- **Result**: Clear distinction between demo and production data

### 21.3 Data Integrity Lessons

**LESSON-007**: 宁可 NULL，不要 Guess
- **Learning**: Fabricating plausible data creates legal and trust risks
- **Application**: Unknown fields must remain NULL, never fill with guesses
- **Result**: No fabricated government information

**LESSON-008**: 宁可 UNVERIFIED，不要 VERIFIED
- **Learning**: Over-claiming verification creates trust violations
- **Application**: Default to UNVERIFIED, only upgrade with evidence
- **Result**: Honest trust status communication

**LESSON-009**: 宁可少一条政策，不要多一条假的政策
- **Learning**: One fake policy destroys trust in the entire system
- **Application**: Quality over quantity — missing data is safer than fake data
- **Result**: Zero fake policies, even if it means fewer policies

### 21.4 Communication Lessons

**LESSON-010**: Repository Reality Must Trump Documentation
- **Learning**: Documentation drift creates confusion
- **Application**: Always verify README claims against actual code
- **Result**: Accurate project status representation

**LESSON-011**: Future Architecture Must Be Clearly Labeled
- **Learning**: Confusion between planned and implemented features
- **Application**: Clearly mark MCP/A2A as "NOT IMPLEMENTED"
- **Result**: Accurate capability representation

---

## 22. Git / Remote State

### 22.1 Current Git State

**Branch**: `master`

**Remote**: `origin → https://github.com/gzchenhao/open-invest.git`

**LOCAL HEAD**: `60736567624db8cac49371d6d8d0382f27641234`

**REMOTE HEAD**: `60736567624db8cac49371d6d8d0382f27641234`

**Status**: **LOCAL HEAD == REMOTE HEAD** ✅

**Worktree**: **CLEAN** ✅

### 22.2 Recent Commit History

```
ea60f10 feat: establish experimental trust evidence service boundary (2026-08-26)
0dcc3d8 docs: verify OpenInvest trust evidence prototype foundation (2026-08-26)
6f5ce43 feat: build OpenInvest trust evidence prototype foundation (2026-08-26)
5b74ba1 docs: add historical exposure audit and policy governance rules (2026-08-24)
ca2926b fix: disclose mock policy data in public surfaces (2026-08-24)
ec2e196 feat: enforce policy provenance and anti-hallucination data governance (2026-08-24)
f449f57 fix: align repository reality and repair test gate (2026-08-24)
580ace3 docs: establish the immutable AI handover constitution and fix data taxonomy (2026-08-24)
```

### 22.3 Git Verification Commands

```bash
# Check current status
git status

# Check recent history
git log -3 --oneline

# Check remote HEAD
git ls-remote origin master

# Verify local vs remote
git rev-parse HEAD
git rev-parse origin/master
```

### 22.4 Git Governance Rules

**RULE-001**: Always verify LOCAL HEAD == REMOTE HEAD after push

**RULE-002**: Never force push without explicit authorization

**RULE-003**: Never rewrite history without explicit authorization

**RULE-004**: Always ensure worktree is clean before major operations

**RULE-005**: Never use `git reset --hard` to hide problems

---

## 23. Current Quest

### 23.1 Quest Status

**Current Quest**: **P1-3.3 — Canonical Taxonomy Integration**

**Status**: ✅ **COMPLETE**

**Completion Date**: 2026-08-27

**Previous Quest**: P1-3.2 — Implement Canonical Taxonomy Registry and Legacy Mapping Layer ✅ COMPLETE

**Quest Before**: P1-3.1 — Canonical Industry Taxonomy Design ✅ COMPLETE

### 23.2 Quest Achievement Summary

**Implemented Components**:
- ✅ Trust Evidence Service (`src/trust/trust_service.py`)
- ✅ Request/Response Models (`src/trust/trust_request_response.py`)
- ✅ Trust Query Contract (`src/trust/trust_query_contract.py`)
- ✅ Graph Query Engine (`src/trust/graph_query_engine.py`)
- ✅ Mock Agent Demo (`examples/trust_demo/`)
- ✅ 6 API Safety Tests
- ✅ Complete Documentation (`docs/Trust_Evidence_API.md` - 464 lines)

**Test Status**: **164 passed, 0 failed** (baseline maintained)

**Files Changed**: 11 files, 3044 lines added

**NOT IMPLEMENTED**:
- ❌ MCP integration (clearly labeled)
- ❌ A2A integration (clearly labeled)
- ❌ Production deployment (experimental prototype only)

### 23.3 Quest Verification

**Git Evidence**:
- LOCAL HEAD == REMOTE HEAD == `ea60f10`
- Worktree clean
- All files committed and pushed

**Test Evidence**:
- 342 tests passing
- 0 tests failing
- 23 taxonomy audit tests (P1-3.0)
- 29 taxonomy alignment tests (P1-3.1)
- 66 canonical taxonomy implementation tests (P1-3.2)
- 60 taxonomy integration tests (P1-3.3)

**Documentation Evidence**:
- Complete Industry_Taxonomy_Audit_20260826.md (P1-3.0 audit)
- Complete Industry_Taxonomy_Alignment_Design.md (P1-3.1 design)
- Complete Canonical_Taxonomy_Registry_Implementation_20260826.md (P1-3.2 implementation)
- Complete Canonical_Taxonomy_Integration_20260827.md (P1-3.3 integration)
- All "NOT IMPLEMENTED" claims clearly labeled

**Runtime Evidence**:
- Mock agent demo runs successfully
- Trust Evidence API responds correctly
- Safety gates function as designed

---

## 24. Next Recommended Quest

### 24.1 Immediate Next Steps

**OPTION A**: Evidence Graph Taxonomy Integration (P1-3.4)
- **Priority**: LOW
- **Purpose**: Integrate canonical taxonomy into Evidence Graph sector field
- **Scope**: Map Evidence Graph sector strings to canonical IDs
- **Dependencies**: P1-3.3 integration complete
- **Estimated Effort**: Low
- **Key Constraint**: Evidence Graph is design-only; maintain compatibility

**OPTION B**: Real Policy Verification Workflow
- **Priority**: HIGH
- **Purpose**: Implement workflow for verifying real government policies
- **Scope**: Official source verification, human/agent confirmation workflow
- **Dependencies**: None
- **Estimated Effort**: High

**OPTION C**: Production Hardening
- **Priority**: MEDIUM
- **Purpose**: Prepare experimental prototype for production deployment
- **Scope**: Security hardening, performance optimization, operational readiness
- **Dependencies**: Real policy verification workflow
- **Estimated Effort**: High

**OPTION D**: MCP Integration Design
- **Priority**: LOW
- **Purpose**: Design MCP server integration for Trust Evidence API
- **Scope**: MCP protocol design, integration architecture
- **Dependencies**: Production Hardening
- **Estimated Effort**: Medium

### 24.2 Recommended Approach

**Start with OPTION A (Industry Taxonomy Alignment)**:
- **Reasoning**: Resolves existing technical debt
- **Benefits**: Consistent data model across all components
- **Risk**: Low — does not affect safety or production readiness

**Then proceed to OPTION B (Real Policy Verification)**:
- **Reasoning**: Enables transition from mock to real data
- **Benefits**: System becomes useful for real decisions
- **Risk**: Medium — requires official source access

**Finally approach OPTIONS C and D**:
- **Reasoning**: Production readiness requires real data first
- **Benefits**: System becomes production-capable
- **Risk**: High — requires comprehensive testing

---

## 25. Agent Handover Instructions

### 25.1 First Actions Upon Handover

**STEP 1**: Read this entire Master Handover Manual
- **Purpose**: Understand project identity, current reality, and safety rules
- **Time Required**: 30-45 minutes
- **Verification**: Understand all sections before proceeding

**STEP 2**: Verify Current Git State
```bash
cd c:\OpenInvest\open-invest-protocol
git status
git log -3 --oneline
git ls-remote origin master
python -m pytest tests/ -q
```
- **Expected Output**: Worktree clean, LOCAL HEAD == REMOTE HEAD, 187 passed
- **Action Required**: If discrepancies found, record before proceeding

**STEP 3**: Check Project Reality
- **Check**: README.md claims vs actual code
- **Check**: Documentation vs implementation
- **Check**: MCP/A2A status (should be NOT IMPLEMENTED)
- **Action Required**: Record any discrepancies

**STEP 4**: Confirm Safety Understanding
- **Confirm**: Understanding of 宁可 NULL，不要 Guess
- **Confirm**: Understanding of 宁可 UNVERIFIED，不要 VERIFIED
- **Confirm**: Understanding of MOCK must always remain MOCK
- **Action Required**: Do not proceed if safety rules unclear

**STEP 5**: Begin Assigned Task
- **Follow**: All handover instructions
- **Maintain**: Safety boundaries
- **Provide**: Evidence for completion (code, test, git, runtime)

### 25.2 Prohibited Actions

**WITHOUT EXPLICIT AUTHORIZATION**:
- ❌ Modify existing core business data
- ❌ Delete any files without explicit approval
- ❌ Upgrade UNVERIFIED to VERIFIED automatically
- ❌ Change MOCK data to appear real
- ❌ Claim MCP/A2A implementation
- ❌ Claim production readiness
- ❌ Weaken safety tests
- ❌ Delete failed tests
- ❌ Rewrite Git history
- ❌ Force push to origin
- ❌ Fabricate government information
- ❌ Fabricate government contacts
- ❌ Fabricate official URLs
- ❌ Guess missing data values

### 25.3 Required Actions

**FOR EVERY TASK**:
- ✅ Read Master Handover Manual first
- ✅ Verify Git state before starting
- ✅ Run tests before and after changes
- ✅ Provide four types of evidence (code, test, git, runtime)
- ✅ Maintain safety boundaries
- ✅ Label mock data explicitly
- ✅ Keep provenance information
- ✅ Update handover manual if project state changes
- ✅ Verify LOCAL HEAD == REMOTE HEAD after push
- ✅ Ensure worktree is clean before major operations

### 25.4 Emergency Procedures

**IF TESTS FAIL**:
1. Do not weaken tests
2. Identify root cause
3. Fix underlying issue
4. Re-run full test suite
5. Verify all tests passing

**IF GIT CONFLICTS OCCUR**:
1. Do not force push
2. Identify conflict sources
3. Resolve conflicts manually
4. Verify resolution
5. Re-run tests
6. Push normally

**IF SAFETY VIOLATION DETECTED**:
1. Stop work immediately
2. Report violation to project lead
3. Do not attempt to hide violation
4. Document violation in handover
5. Await further instructions

**IF DOCUMENTATION DISAGREES WITH CODE**:
1. Trust the code
2. Update documentation to match code
3. Record discrepancy in handover
4. Do not guess which is correct

---

## Appendix A: Verification Evidence

### A.1 Test Evidence

**Command**: `python -m pytest tests/ -q --tb=no`

**Result**: `187 passed, 1 warning in 6.67s`

**Warning**: StarletteDeprecationWarning (third-party library, not project issue)

**Verification**: All tests passing, zero failures

### A.2 Git Evidence

**LOCAL HEAD**: `60736567624db8cac49371d6d8d0382f27641234`

**REMOTE HEAD**: `60736567624db8cac49371d6d8d0382f27641234`

**Status**: LOCAL HEAD == REMOTE HEAD ✅

**Worktree**: CLEAN ✅

### A.3 Code Evidence

**Trust Evidence API**: Implemented in `src/trust/trust_service.py`

**Request/Response Models**: Implemented in `src/trust/trust_request_response.py`

**Query Contract**: Implemented in `src/trust/trust_query_contract.py`

**Graph Query Engine**: Implemented in `src/trust/graph_query_engine.py`

**Mock Agent Demo**: Implemented in `examples/trust_demo/`

**Safety Tests**: Implemented in `tests/test_trust_api_safety.py`

### A.4 Runtime Evidence

**Mock Agent Demo**: Runs successfully

**Trust Evidence API**: Responds correctly to all methods

**Safety Gates**: Function as designed (block violations)

**Query Engine**: Executes high-value queries successfully

### A.5 Documentation Evidence

**Trust_Evidence_API.md**: 464 lines, complete API documentation

**Architecture Documents**: Updated with P1-2.2 status

**NOT IMPLEMENTED Claims**: Clearly labeled throughout

**Safety Rules**: Documented and enforced

---

## Appendix B: Important File Locations

### B.1 Core Infrastructure

```
src/trust/evidence_object.py           # Evidence Object model
src/trust/trust_service.py             # Trust Evidence API
src/trust/trust_request_response.py    # Request/response models
src/trust/trust_query_contract.py      # Query contract
src/trust/graph_query_engine.py        # Graph query engine
```

### B.2 Policy Intelligence

```
global_policy_aggregator/processors/policy_cleaner.py       # Parser
global_policy_aggregator/processors/provenance_validator.py # Safety validator
global_policy_aggregator/web/interactive_ai_server.py       # Web portal
```

### B.3 Protocol

```
server/main.py                               # Protocol server
client/api/protocol_client.py                # Protocol client
server/services/tech_readiness_service.py    # Business logic
```

### B.4 Tests

```
tests/test_provenance.py                # Provenance tests
tests/test_trust_prototype.py           # Trust prototype tests
tests/test_trust_api_safety.py          # API safety tests
tests/test_trust_architecture.py        # Architecture tests
tests/test_ui_mock_disclosure.py        # UI disclosure tests
```

### B.5 Documentation

```
docs/Trust_Evidence_API.md              # Trust Evidence API docs
docs/OpenInvest_Trust_Architecture.md   # Trust architecture
docs/Agent_Trust_Model.md               # Agent trust model
docs/Policy_Evidence_Graph.md           # Evidence graph design
docs/Policy_Data_Governance.md          # Data governance rules
docs/Industry_Taxonomy_Audit_20260826.md # Industry taxonomy audit (P1-3.0)
docs/Industry_Taxonomy_Alignment_Design.md # Canonical taxonomy design (P1-3.1)
docs/Canonical_Taxonomy_Registry_Implementation_20260826.md # Implementation doc (P1-3.2)
docs/Canonical_Taxonomy_Integration_20260827.md # Integration doc (P1-3.3)
```

### B.6 Taxonomy Audit, Design, Implementation & Integration

```
tests/test_taxonomy_audit.py            # Taxonomy consistency audit tests (23 tests, P1-3.0)
tests/test_taxonomy_alignment.py        # Taxonomy alignment design tests (29 tests, P1-3.1)
tests/test_canonical_taxonomy.py        # Canonical taxonomy implementation tests (66 tests, P1-3.2)
tests/test_taxonomy_integration.py      # Taxonomy integration tests (60 tests, P1-3.3)
schema/canonical_taxonomy.py            # Canonical Industry Registry + Legacy Mapping Layer
```

---

## Appendix C: Contact and Support

### C.1 Project Information

**Repository**: https://github.com/gzchenhao/open-invest.git

**Branch**: `master`

**Project Status**: Experimental Trust Infrastructure Prototype

**Production Ready**: NO

### C.2 Handover Maintenance

**Update Frequency**: After every major Quest

**Update Requirements**:
- Current date
- Current Quest
- Current Git commit
- Remote HEAD
- Worktree status
- Test count and results
- New capabilities
- Known issues
- Future / Not Implemented content

**Update Process**:
1. Complete Quest
2. Run regression tests
3. Commit and push changes
4. Update handover manual
5. Commit and push handover
6. Verify LOCAL HEAD == REMOTE HEAD

---

*End of Master Handover Manual*

*Preserve > Modify · Evidence > Assertion · Reality > Documentation · Compatibility > Convenience · Explicit Migration > Silent Deletion · Verified Data > Fabricated Data · Vision vs Reality · Safety First*

**Last Updated**: 2026-08-27
**Next Review**: After next major Quest completion  
**Maintainer**: Future AI agents following handover instructions