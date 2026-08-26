"""Trust Query Contract for OpenInvest Trust Evidence System

Define machine-readable query contracts for Agent trust questions.
This establishes the "Trust Query Language" that Agents can use to ask
questions about evidence trustworthiness.

OpenInvest - Trust Evidence API Boundary
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum

from .trust_request_response import (
    TrustQueryRequest, TrustQueryResponse, 
    VerificationStatus, TrustScoreInfo, ProvenanceInfo,
    ConfidenceLevel
)


class TrustQueryType(str, Enum):
    """Machine-readable trust query types"""
    # Provenance questions
    WHO_CREATED = "who_created"
    WHERE_CAME_FROM = "where_came_from" 
    WHEN_CREATED = "when_created"
    HAS_MODIFIED = "has_modified"
    
    # Trustworthiness questions
    WHY_TRUST = "why_trust"
    WHAT_SUPPORTS = "what_supports"
    WHAT_UNVERIFIED = "what_unverified"
    
    # Analysis questions
    EVIDENCE_TRACE = "evidence_trace"
    TRUST_CALCULATION = "trust_calculation"
    INTEGRITY_CHECK = "integrity_check"


@dataclass
class ProvenanceAnswer:
    """Answer to provenance-related queries"""
    
    who_created: Optional[str] = None
    where_came_from: Optional[str] = None
    when_created: Optional[float] = None
    has_modified: bool = False
    modification_count: int = 0
    modification_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class TrustAnswer:
    """Answer to trustworthiness-related queries"""
    
    trust_score: float = 0.0
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    reasons: List[str] = field(default_factory=list)
    supporting_evidence_count: int = 0
    unverified_items: List[str] = field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisAnswer:
    """Answer to analysis-related queries"""
    
    evidence_trace: List[Dict[str, Any]] = field(default_factory=list)
    trust_calculation: Optional[TrustScoreInfo] = None
    integrity_valid: bool = True
    integrity_issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.trust_calculation:
            data["trust_calculation"] = self.trust_calculation.to_dict()
        return data


@dataclass
class TrustQueryContract:
    """
    Machine-readable trust query contract.
    
    This defines the interface that Agents can use to ask questions about
    evidence trustworthiness in a standardized way.
    """
    
    evidence_id: str
    query_type: TrustQueryType
    query_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert query contract to dictionary format."""
        data = asdict(self)
        # Handle both enum and string cases
        if isinstance(self.query_type, TrustQueryType):
            data["query_type"] = self.query_type.value
        else:
            data["query_type"] = str(self.query_type)
        # Add future integration note
        data["future_integration"] = "MCP/A2A compatible (future implementation)"
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustQueryContract":
        """Create query contract from dictionary."""
        if "query_type" in data and isinstance(data["query_type"], str):
            data["query_type"] = TrustQueryType(data["query_type"])
        
        return cls(**data)


class TrustQueryExecutor:
    """
    Executes trust queries against the evidence system.
    
    This class provides the actual implementation of the trust query contract,
    translating Agent questions into answers using the underlying evidence system.
    """
    
    def __init__(self, trust_service):
        """Initialize with trust evidence service."""
        self.trust_service = trust_service
    
    def execute_query(self, query: TrustQueryContract) -> TrustQueryResponse:
        """
        Execute a trust query and return standardized response.
        
        Args:
            query: The trust query contract
            
        Returns:
            Standardized response with query results
        """
        try:
            if query.query_type == TrustQueryType.WHO_CREATED:
                return self._query_who_created(query.evidence_id)
            
            elif query.query_type == TrustQueryType.WHERE_CAME_FROM:
                return self._query_where_came_from(query.evidence_id)
                
            elif query.query_type == TrustQueryType.WHEN_CREATED:
                return self._query_when_created(query.evidence_id)
                
            elif query.query_type == TrustQueryType.HAS_MODIFIED:
                return self._query_has_modified(query.evidence_id)
                
            elif query.query_type == TrustQueryType.WHY_TRUST:
                return self._query_why_trust(query.evidence_id)
                
            elif query.query_type == TrustQueryType.WHAT_SUPPORTS:
                return self._query_what_supports(query.evidence_id, query.query_params)
                
            elif query.query_type == TrustQueryType.WHAT_UNVERIFIED:
                return self._query_what_unverified(query.evidence_id)
                
            elif query.query_type == TrustQueryType.EVIDENCE_TRACE:
                return self._query_evidence_trace(query.evidence_id)
                
            elif query.query_type == TrustQueryType.TRUST_CALCULATION:
                return self._query_trust_calculation(query.evidence_id)
                
            elif query.query_type == TrustQueryType.INTEGRITY_CHECK:
                return self._query_integrity_check(query.evidence_id)
                
            else:
                return TrustQueryResponse(
                    success=False,
                    query_type=query.query_type,
                    evidence_id=query.evidence_id,
                    error="Unsupported query type",
                    message=f"Query type '{query.query_type}' is not supported"
                )
                
        except Exception as e:
            return TrustQueryResponse(
                success=False,
                query_type=query.query_type,
                evidence_id=query.evidence_id,
                error=str(e),
                message="Failed to execute trust query"
            )
    
    def _query_who_created(self, evidence_id: str) -> TrustQueryResponse:
        """Answer: WHO created this evidence?"""
        try:
            provenance_result = self.trust_service.get_provenance(evidence_id)
            if not provenance_result["success"]:
                return TrustQueryResponse(
                    success=False,
                    query_type=TrustQueryType.WHO_CREATED,
                    evidence_id=evidence_id,
                    error=provenance_result["error"],
                    message="Failed to retrieve provenance"
                )
            
            chain_data = provenance_result["provenance_chain"]
            creator = None
            
            # Look for creation event
            for record in chain_data:
                if record.get("action") == "created":
                    creator = record.get("actor")
                    break
            
            return TrustQueryResponse(
                success=True,
                query_type=TrustQueryType.WHO_CREATED,
                evidence_id=evidence_id,
                query_result={"creator": creator},
                message=f"Evidence created by: {creator or 'unknown'}"
            )
            
        except Exception as e:
            return TrustQueryResponse(
                success=False,
                query_type=TrustQueryType.WHO_CREATED,
                evidence_id=evidence_id,
                error=str(e),
                message="Failed to determine creator"
            )
    
    def _query_where_came_from(self, evidence_id: str) -> TrustQueryResponse:
        """Answer: WHERE did it come from?"""
        try:
            evidence_result = self.trust_service.get_evidence(evidence_id)
            if not evidence_result["success"]:
                return TrustQueryResponse(
                    success=False,
                    query_type=TrustQueryType.WHERE_CAME_FROM,
                    evidence_id=evidence_id,
                    error=evidence_result["error"],
                    message="Failed to retrieve evidence"
                )
            
            source = evidence_result["evidence"].get("source", "unknown")
            source_reference = evidence_result["evidence"].get("source_reference", "")
            
            return TrustQueryResponse(
                success=True,
                query_type=TrustQueryType.WHERE_CAME_FROM,
                evidence_id=evidence_id,
                query_result={"source": source, "source_reference": source_reference},
                message=f"Evidence originated from: {source}"
            )
            
        except Exception as e:
            return TrustQueryResponse(
                success=False,
                query_type=TrustQueryType.WHERE_CAME_FROM,
                evidence_id=evidence_id,
                error=str(e),
                message="Failed to determine source"
            )
    
    def _query_when_created(self, evidence_id: str) -> TrustQueryResponse:
        """Answer: WHEN was it created?"""
        try:
            provenance_result = self.trust_service.get_provenance(evidence_id)
            if not provenance_result["success"]:
                return TrustQueryResponse(
                    success=False,
                    query_type=TrustQueryType.WHEN_CREATED,
                    evidence_id=evidence_id,
                    error=provenance_result["error"],
                    message="Failed to retrieve provenance"
                )
            
            chain_data = provenance_result["provenance_chain"]
            creation_time = None
            
            # Look for creation event
            for record in chain_data:
                if record.get("action") == "created":
                    creation_time = record.get("timestamp")
                    break
            
            return TrustQueryResponse(
                success=True,
                query_type=TrustQueryType.WHEN_CREATED,
                evidence_id=evidence_id,
                query_result={"creation_timestamp": creation_time},
                message=f"Evidence created at: {creation_time or 'unknown'}"
            )
            
        except Exception as e:
            return TrustQueryResponse(
                success=False,
                query_type=TrustQueryType.WHEN_CREATED,
                evidence_id=evidence_id,
                error=str(e),
                message="Failed to determine creation time"
            )
    
    def _query_has_modified(self, evidence_id: str) -> TrustQueryResponse:
        """Answer: HAS it been modified?"""
        try:
            provenance_result = self.trust_service.get_provenance(evidence_id)
            if not provenance_result["success"]:
                return TrustQueryResponse(
                    success=False,
                    query_type=TrustQueryType.HAS_MODIFIED,
                    evidence_id=evidence_id,
                    error=provenance_result["error"],
                    message="Failed to retrieve provenance"
                )
            
            chain_data = provenance_result["provenance_chain"]
            modification_count = 0
            modification_history = []
            
            # Count modification events
            for record in chain_data:
                if record.get("action") in ["modified", "updated"]:
                    modification_count += 1
                    modification_history.append({
                        "timestamp": record.get("timestamp"),
                        "actor": record.get("actor"),
                        "action": record.get("action")
                    })
            
            has_modified = modification_count > 0
            
            return TrustQueryResponse(
                success=True,
                query_type=TrustQueryType.HAS_MODIFIED,
                evidence_id=evidence_id,
                query_result={
                    "has_modified": has_modified,
                    "modification_count": modification_count,
                    "modification_history": modification_history
                },
                message=f"Evidence {'has' if has_modified else 'has not'} been modified ({modification_count} times)"
            )
            
        except Exception as e:
            return TrustQueryResponse(
                success=False,
                query_type=TrustQueryType.HAS_MODIFIED,
                evidence_id=evidence_id,
                error=str(e),
                message="Failed to check modifications"
            )
    
    def _query_why_trust(self, evidence_id: str) -> TrustQueryResponse:
        """Answer: WHY should I trust it?"""
        try:
            trust_result = self.trust_service.calculate_trust(evidence_id)
            if not trust_result["success"]:
                return TrustQueryResponse(
                    success=False,
                    query_type=TrustQueryType.WHY_TRUST,
                    evidence_id=evidence_id,
                    error=trust_result["error"],
                    message="Failed to calculate trust"
                )
            
            # Build trust assessment
            trust_score = trust_result["trust_score"]
            confidence = trust_result["confidence"]
            reasons = trust_result["reason"] or []
            
            # Add context-specific reasons
            evidence_result = self.trust_service.get_evidence(evidence_id)
            if evidence_result["success"]:
                evidence = evidence_result["evidence"]
                verification_status = evidence.get("verification_status", "UNVERIFIED")
                
                if verification_status == "MOCK":
                    reasons.append("This is marked as MOCK data - prototype demonstration only")
                elif verification_status == "UNVERIFIED":
                    reasons.append("Evidence has not been verified")
                
                if trust_result.get("integrity_valid"):
                    reasons.append("Provenance chain is intact")
                else:
                    reasons.append("Provenance chain integrity issues detected")
            
            return TrustQueryResponse(
                success=True,
                query_type=TrustQueryType.WHY_TRUST,
                evidence_id=evidence_id,
                trust_assessment=TrustScoreInfo(
                    score=trust_score,
                    confidence=ConfidenceLevel(confidence.lower()) if confidence else ConfidenceLevel.LOW,
                    reason=reasons,
                    verification_status=VerificationStatus(evidence_result["evidence"].get("verification_status", "UNVERIFIED"))
                ),
                warning=trust_result.get("warning", ""),
                message=f"Trust assessment: {trust_score:.2f} confidence"
            )
            
        except Exception as e:
            return TrustQueryResponse(
                success=False,
                query_type=TrustQueryType.WHY_TRUST,
                evidence_id=evidence_id,
                error=str(e),
                message="Failed to assess trustworthiness"
            )
    
    def _query_what_supports(self, evidence_id: str, params: Dict[str, Any]) -> TrustQueryResponse:
        """Answer: WHAT evidence supports it?"""
        try:
            # Use existing graph query
            graph_result = self.trust_service.query_evidence_graph(
                "find_supporting_evidence",
                evidence_id=evidence_id
            )
            
            if not graph_result["success"]:
                return TrustQueryResponse(
                    success=False,
                    query_type=TrustQueryType.WHAT_SUPPORTS,
                    evidence_id=evidence_id,
                    error=graph_result["error"],
                    message="Failed to find supporting evidence"
                )
            
            supporting_evidence = graph_result.get("supporting_evidence", [])
            
            return TrustQueryResponse(
                success=True,
                query_type=TrustQueryType.WHAT_SUPPORTS,
                evidence_id=evidence_id,
                supporting_evidence=supporting_evidence,
                query_result={"supporting_count": len(supporting_evidence)},
                message=f"Found {len(supporting_evidence)} supporting evidence items"
            )
            
        except Exception as e:
            return TrustQueryResponse(
                success=False,
                query_type=TrustQueryType.WHAT_SUPPORTS,
                evidence_id=evidence_id,
                error=str(e),
                message="Failed to find supporting evidence"
            )
    
    def _query_what_unverified(self, evidence_id: str) -> TrustQueryResponse:
        """Answer: WHAT is still unverified?"""
        try:
            # This would require more sophisticated analysis in a real implementation
            # For now, we check the evidence status directly
            evidence_result = self.trust_service.get_evidence(evidence_id)
            if not evidence_result["success"]:
                return TrustQueryResponse(
                    success=False,
                    query_type=TrustQueryType.WHAT_UNVERIFIED,
                    evidence_id=evidence_id,
                    error=evidence_result["error"],
                    message="Failed to retrieve evidence"
                )
            
            evidence = evidence_result["evidence"]
            verification_status = evidence.get("verification_status", "UNVERIFIED")
            
            unverified_items = []
            if verification_status == "UNVERIFIED":
                unverified_items.append("Evidence itself")
            
            # Check supporting evidence
            supporting_result = self._query_what_supports(evidence_id, {})
            if supporting_result.success:
                for item in supporting_result.supporting_evidence:
                    item_status = item.get("data", {}).get("verification_status", "UNVERIFIED")
                    if item_status == "UNVERIFIED":
                        unverified_items.append(f"Supporting evidence: {item.get('id', 'unknown')}")
            
            return TrustQueryResponse(
                success=True,
                query_type=TrustQueryType.WHAT_UNVERIFIED,
                evidence_id=evidence_id,
                query_result={"unverified_items": unverified_items},
                message=f"Found {len(unverified_items)} unverified items"
            )
            
        except Exception as e:
            return TrustQueryResponse(
                success=False,
                query_type=TrustQueryType.WHAT_UNVERIFIED,
                evidence_id=evidence_id,
                error=str(e),
                message="Failed to identify unverified items"
            )
    
    def _query_evidence_trace(self, evidence_id: str) -> TrustQueryResponse:
        """Answer: Evidence trace query"""
        try:
            # Use existing provenance trace
            trace_result = self.trust_service.query_evidence_graph(
                "trace_provenance",
                evidence_id=evidence_id
            )
            
            if not trace_result["success"]:
                return TrustQueryResponse(
                    success=False,
                    query_type=TrustQueryType.EVIDENCE_TRACE,
                    evidence_id=evidence_id,
                    error=trace_result["error"],
                    message="Failed to trace evidence"
                )
            
            return TrustQueryResponse(
                success=True,
                query_type=TrustQueryType.EVIDENCE_TRACE,
                evidence_id=evidence_id,
                query_result=trace_result,
                message="Evidence trace completed"
            )
            
        except Exception as e:
            return TrustQueryResponse(
                success=False,
                query_type=TrustQueryType.EVIDENCE_TRACE,
                evidence_id=evidence_id,
                error=str(e),
                message="Failed to trace evidence"
            )
    
    def _query_trust_calculation(self, evidence_id: str) -> TrustQueryResponse:
        """Answer: Trust calculation query"""
        try:
            trust_result = self.trust_service.calculate_trust(evidence_id)
            if not trust_result["success"]:
                return TrustQueryResponse(
                    success=False,
                    query_type=TrustQueryType.TRUST_CALCULATION,
                    evidence_id=evidence_id,
                    error=trust_result["error"],
                    message="Failed to calculate trust"
                )
            
            return TrustQueryResponse(
                success=True,
                query_type=TrustQueryType.TRUST_CALCULATION,
                evidence_id=evidence_id,
                query_result=trust_result,
                message="Trust calculation completed"
            )
            
        except Exception as e:
            return TrustQueryResponse(
                success=False,
                query_type=TrustQueryType.TRUST_CALCULATION,
                evidence_id=evidence_id,
                error=str(e),
                message="Failed to calculate trust"
            )
    
    def _query_integrity_check(self, evidence_id: str) -> TrustQueryResponse:
        """Answer: Integrity check query"""
        try:
            provenance_result = self.trust_service.get_provenance(evidence_id)
            if not provenance_result["success"]:
                return TrustQueryResponse(
                    success=False,
                    query_type=TrustQueryType.INTEGRITY_CHECK,
                    evidence_id=evidence_id,
                    error=provenance_result["error"],
                    message="Failed to check integrity"
                )
            
            integrity_valid = provenance_result.get("integrity_valid", True)
            integrity_issues = []
            
            if not integrity_valid:
                integrity_issues.append("Provenance chain integrity compromised")
            
            return TrustQueryResponse(
                success=True,
                query_type=TrustQueryType.INTEGRITY_CHECK,
                evidence_id=evidence_id,
                query_result={
                    "integrity_valid": integrity_valid,
                    "integrity_issues": integrity_issues
                },
                message=f"Integrity check: {'PASSED' if integrity_valid else 'FAILED'}"
            )
            
        except Exception as e:
            return TrustQueryResponse(
                success=False,
                query_type=TrustQueryType.INTEGRITY_CHECK,
                evidence_id=evidence_id,
                error=str(e),
                message="Failed to check integrity"
            )


# High-level query interface for Agents
def create_trust_query(evidence_id: str, question: str, **params) -> TrustQueryContract:
    """
    Create a trust query from natural language question.
    
    This provides a convenience mapping for Agent developers to convert
    questions into machine-readable queries.
    
    Args:
        evidence_id: ID of evidence to query
        question: Natural language question
        **params: Additional query parameters
        
    Returns:
        Standardized trust query contract
    """
    question = question.lower().strip()
    
    # Map questions to query types
    if any(word in question for word in ["who", "created", "creator"]):
        return TrustQueryContract(evidence_id, TrustQueryType.WHO_CREATED, params)
    
    elif any(word in question for word in ["where", "came from", "source", "origin"]):
        return TrustQueryContract(evidence_id, TrustQueryType.WHERE_CAME_FROM, params)
    
    elif any(word in question for word in ["when", "created", "time", "date"]):
        return TrustQueryContract(evidence_id, TrustQueryType.WHEN_CREATED, params)
    
    elif any(word in question for word in ["modified", "changed", "altered"]):
        return TrustQueryContract(evidence_id, TrustQueryType.HAS_MODIFIED, params)
    
    elif any(word in question for word in ["why trust", "trustworthy", "reliable"]):
        return TrustQueryContract(evidence_id, TrustQueryType.WHY_TRUST, params)
    
    elif any(word in question for word in ["what supports", "supporting", "backed"]):
        return TrustQueryContract(evidence_id, TrustQueryType.WHAT_SUPPORTS, params)
    
    elif any(word in question for word in ["what unverified", "unverified", "not verified"]):
        return TrustQueryContract(evidence_id, TrustQueryType.WHAT_UNVERIFIED, params)
    
    elif any(word in question for word in ["trace", "provenance", "history"]):
        return TrustQueryContract(evidence_id, TrustQueryType.EVIDENCE_TRACE, params)
    
    elif any(word in question for word in ["trust calculation", "score", "rating"]):
        return TrustQueryContract(evidence_id, TrustQueryType.TRUST_CALCULATION, params)
    
    elif any(word in question for word in ["integrity", "valid", "tampered"]):
        return TrustQueryContract(evidence_id, TrustQueryType.INTEGRITY_CHECK, params)
    
    else:
        # Default to trust calculation for unknown questions
        return TrustQueryContract(evidence_id, TrustQueryType.TRUST_CALCULATION, params)