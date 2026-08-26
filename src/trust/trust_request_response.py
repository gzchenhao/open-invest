"""Stable Request / Response Model for Trust Evidence API

Define standardized request/response contracts for future Agent integration.
This creates a stable interface that can be mapped to MCP tools and A2A protocols.

OpenInvest - Trust Evidence API Boundary
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict, field
from enum import Enum


class EvidenceType(str, Enum):
    """Evidence types for request/response"""
    POLICY = "policy"
    COMPANY = "company"
    TECHNOLOGY = "technology"
    EVIDENCE = "evidence"


class VerificationStatus(str, Enum):
    """Verification status for request/response"""
    UNVERIFIED = "UNVERIFIED"
    MOCK = "MOCK"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ConfidenceLevel(str, Enum):
    """Confidence levels for trust scores"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class QueryType(str, Enum):
    """Query types for evidence graph"""
    FIND_SUPPORTING_EVIDENCE = "find_supporting_evidence"
    FIND_POLICY_SOURCES = "find_policy_sources"
    FIND_COMPANY_EVIDENCE = "find_company_evidence"
    FIND_RELATED_EVIDENCE = "find_related_evidence"
    TRACE_PROVENANCE = "trace_provenance"


@dataclass
class TrustEvidenceRequest:
    """
    Standard request format for trust evidence operations.
    
    This interface is designed to be future-compatible with:
    - MCP Tool calls
    - A2A Message formats
    - Cross-agent communication protocols
    """
    
    # Core identification
    evidence_id: str
    evidence_type: EvidenceType = EvidenceType.EVIDENCE
    
    # Source information
    source: str = "mock"
    source_reference: str = ""
    
    # Trust metadata
    verification_status: VerificationStatus = VerificationStatus.MOCK
    confidence_score: float = 0.0
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Query parameters (for graph queries)
    query_type: Optional[QueryType] = None
    query_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustEvidenceRequest":
        """Create request from dictionary."""
        # Convert string enums to enum types
        if "evidence_type" in data and isinstance(data["evidence_type"], str):
            data["evidence_type"] = EvidenceType(data["evidence_type"])
        
        if "verification_status" in data and isinstance(data["verification_status"], str):
            data["verification_status"] = VerificationStatus(data["verification_status"])
        
        if "query_type" in data and isinstance(data["query_type"], str):
            data["query_type"] = QueryType(data["query_type"])
        
        return cls(**data)


@dataclass
class ProvenanceInfo:
    """Information about evidence provenance"""
    
    source: str
    timestamp: float
    action: str
    actor: str
    hash: str = ""
    integrity_valid: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrustScoreInfo:
    """Trust score and explanation information"""
    
    score: float
    confidence: ConfidenceLevel
    reason: List[str]
    supporting_evidence_count: int = 0
    verification_status: VerificationStatus = VerificationStatus.MOCK
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GraphNodeInfo:
    """Information about graph nodes"""
    
    node_id: str
    node_type: str
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GraphRelationInfo:
    """Information about graph relations"""
    
    source_node_id: str
    target_node_id: str
    relation_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrustEvidenceResponse:
    """
    Standard response format for trust evidence operations.
    
    This interface is designed to be future-compatible with:
    - MCP Tool responses
    - A2A Message formats
    - Cross-agent communication protocols
    """
    
    # Operation result
    success: bool
    evidence_id: str
    
    # Core evidence information
    evidence: Optional[Dict[str, Any]] = None
    evidence_type: EvidenceType = EvidenceType.EVIDENCE
    
    # Trust information
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    trust_score: Optional[TrustScoreInfo] = None
    
    # Provenance information
    provenance_chain: List[ProvenanceInfo] = field(default_factory=list)
    integrity_valid: bool = True
    
    # Graph information
    graph_nodes: List[GraphNodeInfo] = field(default_factory=list)
    graph_relations: List[GraphRelationInfo] = field(default_factory=list)
    
    # Error handling
    error: Optional[str] = None
    message: str = ""
    
    # Additional context
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    related_evidence: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        # Convert complex objects to dictionaries
        data = {}
        for key, value in asdict(self).items():
            if key == "trust_score" and value is not None:
                data[key] = value.to_dict()
            elif key == "provenance_chain":
                data[key] = [item.to_dict() for item in value]
            elif key == "graph_nodes":
                data[key] = [item.to_dict() for item in value]
            elif key == "graph_relations":
                data[key] = [item.to_dict() for item in value]
            else:
                data[key] = value
        
        return data


@dataclass
class TrustQueryRequest:
    """
    Request for trust-related queries.
    
    Designed for Agent queries like:
    - "Who created this evidence?"
    - "Why should I trust this?"
    - "What evidence supports this claim?"
    """
    
    query_type: QueryType
    evidence_id: str
    query_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustQueryRequest":
        """Create query request from dictionary."""
        if "query_type" in data and isinstance(data["query_type"], str):
            data["query_type"] = QueryType(data["query_type"])
        
        return cls(**data)


@dataclass
@dataclass
class TrustQueryResponse:
    """
    Response for trust-related queries.
    
    Provides machine-readable answers to Agent questions.
    """
    
    # Query result (no defaults)
    success: bool
    query_type: QueryType
    evidence_id: str
    
    # Query-specific results (with defaults)
    query_result: Dict[str, Any] = field(default_factory=dict)
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    related_evidence: List[Dict[str, Any]] = field(default_factory=list)
    provenance_chain: List[ProvenanceInfo] = field(default_factory=list)
    
    # Trust analysis (with defaults)
    trust_assessment: Optional[TrustScoreInfo] = None
    integrity_valid: bool = True
    
    # Error handling (with defaults)
    error: Optional[str] = None
    message: str = ""
    
    # Warning for prototype status
    warning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        data = asdict(self)
        if self.trust_assessment:
            data["trust_assessment"] = self.trust_assessment.to_dict()
        if self.provenance_chain:
            data["provenance_chain"] = [item.to_dict() for item in self.provenance_chain]
        if self.query_type:
            data["query_type"] = self.query_type.value if hasattr(self.query_type, 'value') else str(self.query_type)
        return data


@dataclass
class ServiceStatusResponse:
    """Response for service status requests"""
    
    success: bool
    service_name: str
    version: str
    is_ready: bool
    capabilities: List[str]
    limitations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Request/Response transformation utilities
class TrustEvidenceTransformer:
    """Transform between internal objects and request/response formats"""
    
    @staticmethod
    def evidence_to_response(evidence_dict: Dict[str, Any], 
                           provenance_chain: List[Dict[str, Any]] = None,
                           trust_score: Dict[str, Any] = None) -> TrustEvidenceResponse:
        """Transform evidence data to response format."""
        
        response = TrustEvidenceResponse(
            success=True,
            evidence_id=evidence_dict.get("id", ""),
            evidence=evidence_dict,
            evidence_type=EvidenceType(evidence_dict.get("type", "evidence")),
            verification_status=VerificationStatus(evidence_dict.get("verification_status", "UNVERIFIED"))
        )
        
        # Add provenance
        if provenance_chain:
            response.provenance_chain = [
                ProvenanceInfo(**item) for item in provenance_chain
            ]
        
        # Add trust score
        if trust_score:
            response.trust_score = TrustScoreInfo(
                score=trust_score.get("score", 0),
                confidence=ConfidenceLevel(trust_score.get("confidence", "low")),
                reason=trust_score.get("reason", [])
            )
        
        return response
    
    @staticmethod
    def error_response(evidence_id: str, error: str, message: str) -> TrustEvidenceResponse:
        """Create error response."""
        return TrustEvidenceResponse(
            success=False,
            evidence_id=evidence_id,
            error=error,
            message=message
        )
    
    @staticmethod
    def success_response(evidence_id: str, message: str, **kwargs) -> TrustEvidenceResponse:
        """Create success response."""
        response = TrustEvidenceResponse(
            success=True,
            evidence_id=evidence_id,
            message=message
        )
        
        # Add any additional fields
        for key, value in kwargs.items():
            if hasattr(response, key):
                setattr(response, key, value)
        
        return response


# Example usage mapping for future MCP/A2A integration
"""
Future MCP Tool Mapping:
mcp.tools = [
    {
        "name": "openinvest_create_evidence",
        "description": "Create trust evidence in OpenInvest system",
        "inputSchema": TrustEvidenceRequest.to_dict().__class__
    },
    {
        "name": "openinvest_get_evidence", 
        "description": "Get evidence with provenance and trust information",
        "inputSchema": {"evidence_id": "string"}
    },
    {
        "name": "openinvest_query_trust",
        "description": "Query trust information for evidence",
        "inputSchema": TrustQueryRequest.to_dict().__class__
    }
]

Future A2A Message Mapping:
a2a.messages = [
    {
        "type": "trust_evidence_request",
        "format": TrustEvidenceRequest.to_dict()
    },
    {
        "type": "trust_evidence_response", 
        "format": TrustEvidenceResponse.to_dict()
    }
]
"""