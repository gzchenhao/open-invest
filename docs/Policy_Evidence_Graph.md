# 🔍 Policy Evidence Graph Design

## Overview

The Policy Evidence Graph is designed to answer the critical question: **"Why should I trust this information?"**

This graph structure enables DeepTech agents to verify information provenance, track reliability, and establish confidence in policy data through comprehensive **evidence layer** chains. It serves as a core component of the **trust infrastructure**.

---

## Core Graph Structure

### Policy Node (Central Entity - Trust Layer Integration)
```
Policy
├── id: string (Unique identifier)
├── title: string
├── description: text
├── policy_type: enum (REGULATORY|INCENTIVE|GUIDANCE|MANDATE)
├── domain: string (AI|BIOTECH|QUANTUM|CLEAN_TECH|ADVANCED_MATERIALS)
├── jurisdiction: string (Country/Region/City)
├── status: enum (ACTIVE|DRAFT|REPEALED|SUSPENDED)
├── confidence_score: decimal (0.0-1.0)
└── last_updated: datetime
```

### Source Node (Origin Information)
```
Source
├── id: string (Unique identifier)
├── name: string
├── type: enum (GOVERNMENT|INDUSTRY|ACADEMIC|NGO|PRIVATE)
├── url: string
├── domain: string
├── reputation_score: decimal (0.0-1.0)
├── verification_status: enum (VERIFIED|UNVERIFIED|MOCK|SUSPECTED)
├── contact_info: json
├── history: array (Change records)
└── metadata: json (Additional attributes)
```

### Publisher Node (Distribution Channel)
```
Publisher
├── id: string (Unique identifier)
├── name: string
├── role: enum (AUTHOR|DISTRIBUTOR|AGGREGATOR|TRANSLATOR)
├── relationship_to_source: string
├── verification_status: enum (VERIFIED|UNVERIFIED|MOCK)
├── publication_history: array
└── reliability_score: decimal (0.0-1.0)
```

### Publication Node (Specific Instance)
```
Publication
├── id: string (Unique identifier)
├── policy_id: string (Reference to Policy)
├── publisher_id: string (Reference to Publisher)
├── source_id: string (Reference to Source)
├── title: string
├── content_hash: string (Content fingerprint)
├── language: string
├── publication_date: datetime
├── effective_date: datetime
├── expiry_date: datetime
├── format: enum (PDF|HTML|JSON|XML|TEXT)
├── access_level: enum (PUBLIC|RESTRICTED|CONFIDENTIAL)
└── download_url: string
```

### Verification Node (Validation Process)
```
Verification
├── id: string (Unique identifier)
├── publication_id: string (Reference to Publication)
├── verification_type: enum (AUTOMATIC|MANUAL|EXPERT|CROSS_REFERENCE)
├── verified_by: string (Agent/organization ID)
├── verification_date: datetime
├── verification_result: enum (APPROVED|REJECTED|PENDING|NEEDS_REVIEW)
├── confidence_level: decimal (0.0-1.0)
├── evidence_provided: text
├── methodology: string
├── verification_cost: decimal
└── auto_recheck_date: datetime
```

### Supporting Document Node (Corroboration)
```
SupportingDocument
├── id: string (Unique identifier)
├── name: string
├── document_type: enum (STUDY|REPORT|STATISTIC|CASE_LAW|REFERENCE)
├── source: string
├── url: string
├── relevance_score: decimal (0.0-1.0)
├── relationship_to_policy: string
├── verification_status: enum (VERIFIED|UNVERIFIED|MOCK)
├── citation_count: integer
└── influential_score: decimal (0.0-1.0)
```

### Confidence Score Calculation
```
ConfidenceScore = {
  base_reputation: 0.3,      // Source reputation (30%)
  verification_quality: 0.25, // Verification process quality (25%)
  document_freshness: 0.2,    // How recent is information (20%)
  corroboration: 0.15,        // Supporting evidence strength (15%)
  publisher_trust: 0.1        // Publisher reliability (10%)
}

// Dynamic adjustment factors
TimeDecay = exp(-time_since_update / 365)  // Annual decay
CorroborationBonus = min(supporting_count * 0.05, 0.15)
VerificationBonus = verification_quality * multiplier
```

---

## Edge Relationships

### Direct Relationships
```
Policy -- PUBLISHED_AS --> Publication
Policy -- HAS_SOURCE --> Source  
Publication -- PUBLISHED_BY --> Publisher
Publication -- VERIFIED_BY --> Verification
Publication -- REFERENCES --> SupportingDocument
Verification -- USES_SOURCE --> Source
```

### Inferred Relationships
```
Policy -- TRUST_LEVEL --> ConfidenceScore
Source -- IMPACTS_CONFIDENCE --> Policy
Verification -- VALIDATES --> Publication
SupportingDocument -- CORROBORATES --> Policy
Publisher -- TRANSMITS --> Source
```

### Temporal Relationships
```
Publication -- FOLLOWS --> Publication (Version history)
Verification -- UPDATED --> Verification (Re-verification)
Policy -- SUPERSEDES --> Policy (Amendment history)
Source -- REVISED --> Source (Content changes)
```

---

## Trust Query Patterns

### Query 1: Why trust this policy?
```
MATCH (p:Policy)-[:HAS_SOURCE]->(s:Source),
      (p)-[:PUBLISHED_AS]->(pub:Publication)-[:VERIFIED_BY]->(v:Verification)
WHERE p.id = "policy_123"
RETURN p.title, s.reputation_score, v.confidence_level, 
       s.verification_status, v.verification_result
```

### Query 2: Is this information current?
```
MATCH (p:Policy)-[:PUBLISHED_AS]->(pub:Publication)
WHERE p.id = "policy_123" 
RETURN pub.publication_date, pub.effective_date, 
       datetime.duration(pub.publication_date, datetime()).years as years_old
```

### Query 3: What corroborates this policy?
```
MATCH (p:Policy)-[:REFERENCES]->(sd:SupportingDocument)
WHERE p.id = "policy_123"
RETURN sd.name, sd.relevance_score, sd.verification_status
ORDER BY sd.relevance_score DESC
```

### Query 4: Who verified this information?
```
MATCH (p:Policy)-[:PUBLISHED_AS]->(pub:Publication)-[:VERIFIED_BY]->(v:Verification)
WHERE p.id = "policy_123"
RETURN v.verified_by, v.verification_type, v.verification_date,
       v.confidence_level, v.evidence_provided
```

---

## Data Validation Rules

### Source Validation
1. **Government Sources**: Must have gov.cn domain and official contact information
2. **Academic Sources**: Must be from recognized institutions with DOI or ISBN
3. **Industry Sources**: Must be from recognized organizations with verifiable contact
4. **Private Sources**: Must have explicit verification status and disclaimer

### Publication Validation
1. **Content Integrity**: Content hash must match source document
2. **Format Consistency**: Must match declared format specification
3. **Language Accuracy**: Must match declared language
4. **Date Validity**: Publication date must be reasonable for content

### Verification Validation
1. **Process Documentation**: Must record verification methodology
2. **Evidence Trail**: Must maintain evidence of verification process
3. **Recheck Schedule**: Must schedule automatic re-verification
4. **Cost Tracking**: Must record verification resource usage

---

## Current Implementation Status

### ✅ Implemented Features
- **Basic Node Types**: Policy, Source, Publisher nodes with core attributes
- **Simple Relationships**: Direct publication and source relationships
- **Mock Verification**: Basic verification status tracking (VERIFIED/UNVERIFIED/MOCK)
- **Confidence Scoring**: rudimentary confidence calculation
- **Hash Tracking**: Content fingerprint for integrity verification

### 🔄 In Progress
- **Supporting Documents**: Document node structure defined, integration pending
- **Advanced Queries**: Complex query patterns in development
- **Temporal Relationships**: Version tracking under development
- **Automated Verification**: Algorithm verification system in planning

### ❌ Not Implemented
- **Full Verification Workflow**: Complete automation planned for future
- **Cross-source Validation**: Multiple source verification planned
- **Dynamic Scoring**: Real-time confidence adjustment planned
- **Reputation System**: Comprehensive agent reputation tracking planned

---

## Future Enhancement Roadmap

### Phase 1: Current Foundation
- Complete basic graph structure implementation
- Implement core validation rules
- Develop essential trust queries

### Phase 2: Advanced Validation
- Implement automated verification algorithms
- Add cross-source validation capabilities
- Develop dynamic confidence scoring

### Phase 3: Intelligence Integration
- Implement machine learning for trust assessment
- Add natural language processing for document analysis
- Develop predictive trust metrics

### Phase 4: Ecosystem Integration
- Connect to external verification services
- Implement blockchain for immutable audit trails
- Develop API for agent trust queries

---

## Example Trust Assessment

### Policy: "Shanghai AI Development Policy 2024"

**Trust Query Results:**
- **Source**: Shanghai Municipal Government (gov.cn) - Reputation: 0.95
- **Publisher**: Official government portal - Verification: VERIFIED
- **Publication Date**: 2024-01-15 - Freshness: 0.9
- **Verification**: Manual expert review - Confidence: 0.88
- **Supporting Documents**: 3 academic papers, 2 statistics reports
- **Overall Confidence Score**: 0.87

**Trust Assessment:** "This information has high trustworthiness due to authoritative source, recent publication, expert verification, and strong corroboration."

## Trust Infrastructure Components

The OpenInvest ecosystem relies on several key trust infrastructure components:

- **Trust Layer**: The foundational security layer that enables agent-to-agent verification
- **Trust Infrastructure**: Comprehensive systems for establishing and maintaining agent credibility
- **Trust Framework**: Architectural guidelines for secure DeepTech agent interactions
- **Trust Model**: Mathematical models for evaluating agent reliability and trustworthiness
- **Evidence Layer**: Systems for collecting and verifying information provenance
- **Provenance Layer**: Tracking information origin and chain of custody
- **Verification Layer**: Mechanisms for validating agent claims and data authenticity

---

*Evidence Graph Design: August 25, 2026*  
*Status: Experimental Trust Evidence API Boundary (P1-2.2 Complete)*  
*Vision: "The USB-C for DeepTech"*  
*Current: Runnable experimental graph query engine with API boundaries*