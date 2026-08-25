# 🕸️ Evidence Graph Prototype Design

## Overview

This document advances the Policy Evidence Graph from P1-0 into a comprehensive evidence graph prototype. The graph enables future DeepTech agents to navigate complex relationships between policies, companies, technologies, and investment decisions with full trust transparency.

**Important**: This represents a prototype design. No implementation exists yet. This conceptual framework enables future agent interoperability.

---

## Current Status

**PROTOTYPE DESIGN PHASE**

All graph components defined in this document are architectural designs for future implementation.

---

## Node Types

### 1. Policy Node
Represents government policies, regulations, and incentive programs with complete provenance tracking.

```typescript
interface PolicyNode {
  id: string;                              // Unique UUID identifier
  title: string;                           // Human-readable policy title
  jurisdiction: string;                    // Geographic/country jurisdiction
  policy_type: "REGULATORY" | "INCENTIVE" | "GUIDANCE" | "MANDATE";
  
  // Source Information
  source_url: string;                     // Original source URL
  source_type: "GOVERNMENT" | "THIRD_PARTY" | "AGGREGATOR";
  publisher: string;                       // Publishing entity
  publication_date: Date;                  // Official publication date
  
  // Content & Metadata
  summary: string;                         // Policy summary description
  full_text: string;                       // Complete policy text
  tags: string[];                         // Technology domain tags
  keywords: string[];                     // Search keywords
  
  // Trust Metrics
  verification_status: "PENDING" | "VERIFIED" | "REJECTED" | "OUTDATED";
  confidence_score: number;                // 0.0 to 1.0 confidence rating
  evidence_hash: string;                  // Cryptographic hash of evidence
  
  // Temporal Data
  effective_date: Date;                   // Policy effective date
  expiration_date: Date;                  // Policy expiration date (if applicable)
  last_updated: Date;                     // Last update timestamp
}
```

### 2. Company Node
Represents technology companies with investment-relevant information and market positioning.

```typescript
interface CompanyNode {
  id: string;                              // Unique UUID identifier
  legal_name: string;                     // Official legal company name
  dba_name: string;                       // "Doing Business As" name
  
  // Technology Profile
  technology_tags: string[];               // Core technology domains
  technology_stage: "RESEARCH" | "DEVELOPMENT" | "PROTOTYPE" | "PRODUCT" | "SCALE";
  technical_maturity: number;             // 1-10 scale of technical readiness
  
  // Business Information
  industry_sector: string;                 // Primary industry classification
  business_model: "B2B" | "B2C" | "B2G" | "HYBRID";
  revenue_stage: "PRE_REVENUE" | "EARLY_REVENUE" | "GROWTH" | "MATURE";
  
  // Investment Context
  funding_stage: "SEED" | "SERIES_A" | "SERIES_B" | "LATER" | "PUBLIC";
  total_funding: number;                  // Total funding in USD
  last_funding_date: Date;                // Most recent funding date
  
  // Market Position
  market_position: string;                // Market positioning description
  target_markets: string[];               // Target market segments
  competitive_landscape: string[];         // Related competitor IDs
  
  // Trust & Verification
  verification_status: "PENDING" | "VERIFIED" | "OUTDATED";
  source_reliability: number;             // 0.0 to 1.0 source reliability
  data_freshness: Date;                   // Last data update timestamp
}
```

### 3. Technology Node
Represents specific technologies, innovations, and technical capabilities with maturity assessments.

```typescript
interface TechnologyNode {
  id: string;                              // Unique UUID identifier
  name: string;                           // Technology name
  category: "AI" | "BIOTECH" | "QUANTUM" | "CLEAN_TECH" | "ADVANCED_MATERIALS" | "OTHER";
  
  // Technical Specifications
  technical_description: string;           // Detailed technical description
  maturity_level: number;                 // 1-10 technology maturity scale
  innovation_stage: "CONCEPT" | "RESEARCH" | "DEVELOPMENT" | "VALIDATION" | "DEPLOYMENT";
  
  // Application Context
  application_domains: string[];          // Industry/application areas
  target_markets: string[];               // Target market segments
  competitive_advantages: string[];        // Key differentiators
  
  // Technical Metrics
  performance_metrics: PerformanceMetric[]; // Key performance indicators
  scalability_score: number;              // 1-10 scalability assessment
  adoption_rate: number;                  // Market adoption rate (0.0-1.0)
  
  // Source & Verification
  research_sources: string[];             // Academic/patent sources
  verification_status: "PENDING" | "VERIFIED" | "OUTDATED";
  expert_consensus: number;               // 0.0 to 1.0 expert consensus rating
}
```

### 4. Investment Node
Represents investment decisions, opportunities, and funding rounds with full transparency.

```typescript
interface InvestmentNode {
  id: string;                              // Unique UUID identifier
  opportunity_name: string;               // Investment opportunity name
  opportunity_type: "SEED" | "SERIES_A" | "SERIES_B" | "LATER" | "ACQUISITION";
  
  // Investment Details
  target_company: string;                 // Target company ID
  investment_amount: number;               // Investment amount in USD
  valuation_assessment: number;           // Valuation assessment
  expected_return: number;               // Expected return percentage
  
  // Risk Assessment
  risk_factors: RiskFactor[];            // Identified risk elements
  mitigation_strategies: string[];       // Risk mitigation approaches
  risk_adjusted_return: number;          // Risk-adjusted return metric
  
  // Decision Context
  decision_maker: string;                 // Agent/analyst making decision
  decision_timestamp: Date;               // Decision timestamp
  decision_framework: string;           // Decision methodology used
  
  // Status Tracking
  current_status: "ACTIVE" | "COMPLETED" | "WITHDRAWN" | "PAUSED";
  stage_progress: number;                // 0.0 to 1.0 stage completion
  next_milestone: Date;                   // Next milestone date
  
  // Verification
  verification_status: "PENDING" | "REVIEWED" | "APPROVED";
  audit_trail: AuditEntry[];             // Complete decision audit trail
}
```

### 5. Agent Node
Represents AI agents, analysts, and decision-makers with identity verification and capability tracking.

```typescript
interface AgentNode {
  id: string;                              // Unique UUID identifier
  agent_name: string;                     // Human-readable agent name
  agent_type: "INVESTMENT" | "POLICY" | "COMPANY" | "ANALYST" | "INFRASTRUCTURE";
  
  // Identity & Verification
  identity_verified: boolean;             // Identity verification status
  verification_provider: string;          // Third-party verification service
  verification_certificate: string;       // Digital certificate ID
  
  // Capabilities & Specializations
  capabilities: string[];                 // What the agent can do
  specializations: string[];               // Areas of expertise
  api_endpoints: string[];                // Available service endpoints
  
  // Performance Metrics
  response_accuracy: number;               // Historical accuracy (0.0-1.0)
  consistency_score: number;              // Response consistency (0.0-1.0)
  timeliness_score: number;               // Response timeliness (0.0-1.0)
  error_rate: number;                     // Historical error rate
  
  // Trust & Reputation
  trust_score: number;                    // 0.0 to 1.0 overall trust score
  reputation_history: ReputationEntry[];  // Historical performance record
  trusted_agents: string[];               // IDs of trusted peer agents
  
  // Activity Tracking
  last_active: Date;                      // Last activity timestamp
  total_decisions: number;                // Total decisions made
  success_rate: number;                   // Decision success rate (0.0-1.0)
}
```

### 6. Evidence Node
Represents individual pieces of evidence with full provenance and verification status.

```typescript
interface EvidenceNode {
  id: string;                              // Unique UUID identifier
  evidence_type: "DOCUMENT" | "DATA" | "ANALYSIS" | "DECISION" | "VERIFICATION";
  
  // Evidence Content
  title: string;                           // Evidence title
  content: string;                        // Evidence content/summary
  source: string;                          // Original source
  source_url: string;                     // Source URL (if applicable)
  
  // Provenance Tracking
  evidence_hash: string;                  // Cryptographic hash of evidence
  verification_status: "PENDING" | "VERIFIED" | "REJECTED" | "OUTDATED";
  confidence_score: number;               // 0.0 to 1.0 confidence rating
  
  // Temporal Data
  created_at: Date;                       // Evidence creation timestamp
  last_verified: Date;                    // Last verification timestamp
  expiration_date: Date;                  // Evidence expiration date (if applicable)
  
  // Metadata
  tags: string[];                         // Evidence categorization tags
  related_evidence: string[];             // IDs of related evidence
  expert_review: string;                  // Expert review comments
}
```

---

## Relationship Types

### Company → Policy Relationships

```typescript
interface CompanyPolicyRelationship {
  from_node: string;                      // Company node ID
  to_node: string;                        // Policy node ID
  relationship_type: "BENEFITS_FROM" | "COMPLIANT_WITH" | "OPPOSES" | "AFFECTED_BY";
  
  // Relationship Details
  impact_strength: number;                // 0.0 to 1.0 impact strength
  impact_type: "FINANCIAL" | "REGULATORY" | "OPERATIONAL" | "STRATEGIC";
  timeframe: "SHORT_TERM" | "MEDIUM_TERM" | "LONG_TERM";
  
  // Quantitative Metrics
  financial_impact: number;               // Financial impact estimate
  compliance_cost: number;               // Compliance cost estimate
  strategic_advantage: number;           // Strategic advantage rating
  
  // Source & Verification
  relationship_evidence: string[];       // Evidence supporting this relationship
  last_updated: Date;                     // Last relationship update
  verification_status: "PENDING" | "VERIFIED";
}
```

### Technology → Evidence Relationships

```typescript
interface TechnologyEvidenceRelationship {
  from_node: string;                      // Technology node ID
  to_node: string;                        // Evidence node ID
  relationship_type: "SUPPORTED_BY" | "VALIDATED_BY" | "CHALLENGED_BY" | "DEMONSTRATED_BY";
  
  // Relationship Details
  evidence_strength: number;              // 0.0 to 1.0 evidence strength
  evidence_type: "ACADEMIC" | "PATENT" | "MARKET" | "EXPERIMENTAL";
  confidence_level: number;               // 0.0 to 1.0 confidence level
  
  // Technical Context
  technical_validation: string;           // Technical validation summary
  peer_review_status: string;             // Peer review status
  expert_consensus: number;               // 0.0 to 1.0 expert consensus
  
  // Temporal Context
  evidence_age: number;                   // Age of evidence in days
  recency_score: number;                  // 0.0 to 1.0 recency rating
  update_frequency: string;               // Update frequency description
}
```

### Agent → Evidence Relationships

```typescript
interface AgentEvidenceRelationship {
  from_node: string;                      // Agent node ID
  to_node: string;                        // Evidence node ID
  relationship_type: "TRUSTS" | "VERIFIED" | "GENERATED" | "REJECTED";
  
  // Trust Context
  trust_level: number;                    // 0.0 to 1.0 trust level
  verification_method: string;            // Method used for verification
  verification_timestamp: Date;          // When verification was performed
  
  // Performance Context
  historical_accuracy: number;            // Historical accuracy of this agent
  consistency_score: number;              // Consistency score
  error_rate: number;                     // Historical error rate
  
  // Authority Context
  agent_authority: string;                // Agent's authority level
  specialization_match: number;          // 0.0 to 1.0 specialization match
  expertise_level: number;               // 1-10 expertise rating
}
```

### Investment → Company Relationships

```typescript
interface InvestmentCompanyRelationship {
  from_node: string;                      // Investment node ID
  to_node: string;                        // Company node ID
  relationship_type: "TARGET_OF" | "COMPLETED" | "WITHDRAWN" | "MONITORING";
  
  // Investment Context
  investment_stage: "DUE_DILIGENCE" | "VALUATION" | "NEGOTIATION" | "CLOSING";
  investment_amount: number;              // Investment amount consideration
  valuation_multiple: number;            // Valuation multiple used
  
  // Risk Context
  risk_assessment: number;                // 1-10 risk assessment
  mitigation_plan: string;                // Risk mitigation plan
  exit_strategy: string;                  // Exit strategy description
  
  // Performance Context
  expected_return: number;                // Expected return percentage
  time_horizon: string;                   // Investment time horizon
  success_probability: number;            // 0.0 to 1.0 success probability
  
  // Verification Context
  due_diligence_status: string;           // Due diligence completion status
  verification_documents: string[];      // Due diligence document IDs
  expert_reviews: string[];               // Expert review IDs
}
```

---

## Trust Query Examples

### Policy Trust Queries

```typescript
// Query 1: Why should I trust this policy?
interface PolicyTrustQuery {
  policy_id: string;                      // Target policy ID
  query_context: string;                  // Context for the query
  required_confidence: number;            // Required confidence level (0.0-1.0)
  
  // Expected Response
  response: {
    policy_summary: string;               // Policy summary
    source_reliability: number;           // Source reliability (0.0-1.0)
    verification_status: string;          // Current verification status
    supporting_evidence: string[];       // Evidence supporting policy
    risk_factors: string[];              // Potential trust issues
    confidence_calculation: string;       // How confidence was calculated
  };
}

// Query 2: What policies affect this company?
interface CompanyPolicyQuery {
  company_id: string;                     // Target company ID
  policy_scope: "ALL" | "ACTIVE" | "EXPIRED" | "REGULATORY_ONLY";
  
  // Expected Response
  response: {
    affected_policies: PolicyReference[]; // Policies affecting the company
    impact_assessment: string;           // Overall impact assessment
    compliance_requirements: string[];    // Key compliance requirements
    strategic_implications: string[];     // Strategic business implications
  };
}
```

### Investment Trust Queries

```typescript
// Query 3: Why does this company qualify for investment?
interface CompanyQualificationQuery {
  company_id: string;                     // Target company ID
  investment_criteria: string[];          // Investment criteria to evaluate
  
  // Expected Response
  response: {
    qualification_summary: string;        // Overall qualification assessment
    strength_factors: string[];           // Qualification strengths
    weakness_factors: string[];           // Qualification weaknesses
    evidence_support: string[];           // Supporting evidence
    risk_mitigation: string[];           // Risk mitigation strategies
  };
}

// Query 4: What evidence supports this investment recommendation?
interface InvestmentEvidenceQuery {
  investment_id: string;                  // Target investment ID
  evidence_requirements: string[];         // Specific evidence requirements
  
  // Expected Response
  response: {
    recommendation_summary: string;      // Investment recommendation summary
    supporting_evidence: EvidenceReference[]; // Complete evidence trail
    reasoning_trace: ReasoningStep[];     // Step-by-step reasoning
    alternative_analysis: string;         // Alternative investment options
    confidence_breakdown: string;         // Confidence score breakdown
  };
}
```

### Technology Trust Queries

```typescript
// Query 5: What evidence validates this technology?
interface TechnologyValidationQuery {
  technology_id: string;                  // Target technology ID
  validation_focus: "TECHNICAL" | "COMMERCIAL" | "REGULATORY";
  
  // Expected Response
  response: {
    technology_summary: string;          // Technology overview
    validation_evidence: EvidenceReference[]; // Validation evidence
    expert_consensus: number;            // Expert consensus rating
    market_validation: string;           // Market validation status
    regulatory_status: string;            // Regulatory compliance status
  };
}
```

---

## Graph Architecture Implementation

### Node Storage
```typescript
interface GraphStore {
  // Node Management
  nodes: Map<string, BaseNode>;           // All graph nodes
  node_types: string[];                  // Available node types
  
  // Relationship Management
  relationships: Map<string, BaseRelationship>; // All graph relationships
  relationship_types: string[];          // Available relationship types
  
  // Indexing & Search
  node_index: Map<string, string[]>;     // Type-based node indexing
  relationship_index: Map<string, string[]>; // Type-based relationship indexing
  
  // Query Processing
  query_engine: QueryEngine;              // Graph query processor
  trust_calculator: TrustCalculator;      // Trust score calculator
}
```

### Query Engine
```typescript
interface QueryEngine {
  // Graph Traversal
  findNodes(nodeType: string, filters: Filter[]): NodeResult[];
  findPaths(startNode: string, endNode: string, maxDepth: number): PathResult[];
  findRelationships(nodeId: string, relationType: string): RelationshipResult[];
  
  // Trust Queries
  evaluateTrust(targetId: string, context: string): TrustEvaluation;
  findEvidenceSupport(targetId: string, claim: string): EvidenceResult[];
  calculateConfidence(nodeId: string, factors: string[]): ConfidenceScore;
  
  // Path Analysis
  findShortestPath(start: string, end: string): PathResult;
  findStrongestPath(start: string, end: string, metric: string): PathResult;
  findAllPaths(start: string, end: string, maxDepth: number): PathResult[];
}
```

---

## Implementation Roadmap

### Phase 1: Schema Definition (Current)
- Complete node and relationship type definitions
- Establish trust calculation frameworks
- Define query interfaces and protocols

### Phase 1.5: Planned Features (Future)
- Planned trust verification workflows
- Planned relationship optimization
- Planned performance analytics

### Phase 2: Prototype Implementation (Future)
- Build graph storage and indexing systems
- Implement query engine and trust calculator
- Create visualization and analysis tools

### Phase 3: Agent Integration (Future)
- Connect with MCP/A2A communication protocols
- Enable cross-agent trust exchange
- Establish distributed verification networks

### Phase 4: Production Deployment (Future)
- Scale to handle millions of nodes and relationships
- Implement real-time trust updates
- Establish global trust infrastructure

---

*Evidence Graph Prototype Design: August 25, 2026*  
*Status: Architecture Design Phase - No Implementation Yet*  
*Vision: "The USB-C for DeepTech"*  
*Current Status: Experimental Trust Infrastructure Prototype*