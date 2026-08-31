"""Trust Evidence Service Boundary

Experimental internal service for OpenInvest Trust Evidence System.
NOT MCP Server, NOT A2A Service - internal Python service boundary only.

Current Status:
Runnable internal trust service prototype

Future Integration Points:
- MCP-compatible trust tools (future)
- A2A-compatible trust exchange (future)
- Cross-agent trust negotiation (future)

OpenInvest - Trust Evidence API Boundary
"""

import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict

from .evidence_object import EvidenceObject, VerificationStatus
from .provenance import ProvenanceChain
from .trust_score import TrustScoreCalculator
from .evidence_graph import EvidenceGraph, NodeType, RelationType
from .graph_query_engine import GraphQueryEngine


@dataclass
class ServiceStatus:
    """Service status information"""
    is_ready: bool
    service_name: str
    version: str
    capabilities: List[str]
    limitations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TrustEvidenceService:
    """
    Trust Evidence Service - Experimental internal service boundary.
    
    This is NOT an MCP Server or A2A Service.
    It's an internal Python service that provides a stable interface
    for future Agent integration.
    
    Service Boundaries:
    - MCP integration: NOT IMPLEMENTED
    - A2A integration: NOT IMPLEMENTED  
    - External network access: NOT IMPLEMENTED
    - Production verification: NOT IMPLEMENTED
    """
    
    def __init__(self):
        """Initialize trust evidence service."""
        self.evidence_graph = EvidenceGraph()
        self.graph_query_engine = GraphQueryEngine(self.evidence_graph)
        self.trust_calculator = TrustScoreCalculator()
        self.service_status = ServiceStatus(
            is_ready=True,
            service_name="OpenInvest Trust Evidence Service",
            version="1.0.0-experimental",
            capabilities=[
                "Evidence creation and management",
                "Provenance tracking", 
                "Trust scoring",
                "Evidence graph queries",
                "Trust decision explanations"
            ],
            limitations=[
                "Experimental prototype only",
                "Uses MOCK data only",
                "No real verification",
                "No production-ready claims",
                "No external network access"
            ]
        )
    
    def create_evidence(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new evidence object.
        
        Args:
            evidence_data: Evidence data with required fields
            
        Returns:
            Response with created evidence information
        """
        try:
            # Parse verification status from input
            verification_status = evidence_data.get("verification_status", "MOCK")
            if isinstance(verification_status, str):
                verification_status = VerificationStatus(verification_status)
            elif not isinstance(verification_status, VerificationStatus):
                verification_status = VerificationStatus.MOCK
            
            # Create evidence object
            evidence = EvidenceObject(
                id=evidence_data.get("id"),
                type=evidence_data.get("type", "evidence"),
                source=evidence_data.get("source", "mock"),
                source_reference=evidence_data.get("source_reference", ""),
                verification_status=verification_status,
                confidence_score=evidence_data.get("confidence_score", 0.0),
                metadata=evidence_data.get("metadata", {})
            )
            
            # Add to graph
            self.evidence_graph.add_node(
                node_id=evidence.id,
                node_type=self._map_type_to_node(evidence.type),
                data=evidence.to_dict()
            )
            
            return {
                "success": True,
                "evidence_id": evidence.id,
                "evidence_type": evidence.type,
                "verification_status": evidence.verification_status.value,
                "message": "Evidence created successfully (experimental)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create evidence"
            }
    
    def get_evidence(self, evidence_id: str) -> Dict[str, Any]:
        """
        Get evidence by ID.
        
        Args:
            evidence_id: Evidence identifier
            
        Returns:
            Response with evidence information and provenance
        """
        try:
            # Get from graph
            if evidence_id not in self.evidence_graph.nodes:
                return {
                    "success": False,
                    "error": "Evidence not found",
                    "message": f"Evidence {evidence_id} does not exist"
                }
            
            node = self.evidence_graph.nodes[evidence_id]
            evidence = EvidenceObject.from_dict(node.data)
            
            # Get provenance chain
            provenance = ProvenanceChain(evidence_id)
            
            return {
                "success": True,
                "evidence": evidence.to_dict(),
                "provenance_chain": provenance.get_trust_chain(),
                "verification_status": evidence.verification_status.value,
                "integrity_status": "VALID" if provenance.verify_integrity() else "MODIFIED"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve evidence"
            }
    
    def verify_evidence(self, evidence_id: str, verification_method: str = "mock") -> Dict[str, Any]:
        """
        Verify evidence (mock implementation only).
        
        Args:
            evidence_id: Evidence identifier
            verification_method: Verification method (mock only)
            
        Returns:
            Response with verification result
        """
        try:
            # Get evidence
            result = self.get_evidence(evidence_id)
            if not result["success"]:
                return result
            
            evidence = EvidenceObject.from_dict(result["evidence"])
            provenance = ProvenanceChain(evidence_id)
            
            # Add verification event (mock)
            if verification_method == "mock":
                provenance.add_verification_event(
                    verifier="mock_system",
                    method="mock_verification", 
                    result="mock_result"
                )
                
                # Update verification status
                evidence.verification_status = VerificationStatus.MOCK
                
                return {
                    "success": True,
                    "evidence_id": evidence_id,
                    "verification_method": verification_method,
                    "verification_result": "mock_verification_completed",
                    "verification_status": evidence.verification_status.value,
                    "provenance_updated": True,
                    "message": "Mock verification completed (not authoritative)"
                }
            
            else:
                return {
                    "success": False,
                    "error": "Unsupported verification method",
                    "message": "Only mock verification is available"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to verify evidence"
            }
    
    def get_provenance(self, evidence_id: str) -> Dict[str, Any]:
        """
        Get provenance chain for evidence.
        
        Args:
            evidence_id: Evidence identifier
            
        Returns:
            Response with provenance chain information
        """
        try:
            provenance = ProvenanceChain(evidence_id)
            chain_data = provenance.get_trust_chain()
            is_valid = provenance.verify_integrity()
            
            return {
                "success": True,
                "evidence_id": evidence_id,
                "provenance_chain": chain_data,
                "integrity_valid": is_valid,
                "record_count": len(provenance.records),
                "message": "Provenance retrieved successfully" if is_valid else "Provenance integrity compromised"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve provenance"
            }
    
    def calculate_trust(self, evidence_id: str) -> Dict[str, Any]:
        """
        Calculate trust score for evidence with detailed explanation.
        
        Args:
            evidence_id: Evidence identifier
            
        Returns:
            Response with trust score, confidence, and detailed reasons
        """
        try:
            # Get evidence
            result = self.get_evidence(evidence_id)
            if not result["success"]:
                return result
            
            evidence = EvidenceObject.from_dict(result["evidence"])
            evidence_dict = evidence.to_dict()
            
            # Calculate trust score with detailed breakdown
            trust_result = self.trust_calculator.calculate_trust_score(evidence_dict)
            
            # Get provenance for additional context
            provenance = ProvenanceChain(evidence_id)
            provenance_chain = provenance.get_trust_chain()
            integrity_valid = provenance.verify_integrity()
            
            # Generate detailed explanation based on evidence properties
            detailed_explanation = self._generate_detailed_trust_explanation(
                evidence, 
                trust_result,
                provenance_chain,
                integrity_valid
            )
            
            return {
                "success": True,
                "evidence_id": evidence_id,
                "trust_score": trust_result["score"],
                "confidence": trust_result["confidence"],
                "reason": detailed_explanation["reasons"],
                "confidence_factors": detailed_explanation["confidence_factors"],
                "integrity_valid": integrity_valid,
                "provenance_chain": provenance_chain,
                "verification_status": evidence.verification_status.value,
                "evidence_metadata": {
                    "source": evidence.source,
                    "source_reference": evidence.source_reference,
                    "type": evidence.type,
                    "confidence_score": evidence.confidence_score,
                    "verification_status": evidence.verification_status.value
                },
                "warning": detailed_explanation["warning"],
                "message": "Trust score calculated with detailed explanation (experimental prototype)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to calculate trust"
            }
    
    def _generate_detailed_trust_explanation(self, evidence: EvidenceObject, 
                                            trust_result: Dict[str, Any],
                                            provenance_chain: List[Dict[str, Any]],
                                            integrity_valid: bool) -> Dict[str, Any]:
        """
        Generate detailed trust explanation with confidence factors.
        """
        reasons = []
        confidence_factors = {}
        warning = ""
        
        # Base reasons from calculator
        reasons.extend(trust_result["reason"])
        
        # Add verification status context
        if evidence.verification_status.value == "MOCK":
            reasons.append("Evidence marked as MOCK data - prototype demonstration only")
            warning = "This is experimental prototype data with no authoritative verification"
        elif evidence.verification_status.value == "UNVERIFIED":
            reasons.append("Evidence has not been independently verified")
            confidence_factors["verification"] = "low"
        
        # Add provenance context
        if integrity_valid:
            reasons.append("Provenance chain integrity verified")
            confidence_factors["provenance"] = "high"
        else:
            reasons.append("Provenance chain integrity compromised")
            confidence_factors["provenance"] = "low"
            warning = "Warning: Provenance chain integrity issues detected"
        
        # Add source reliability context
        source_reliability = evidence.source.lower()
        if source_reliability == "mock":
            confidence_factors["source_reliability"] = "low"
            reasons.append("Source marked as mock for demonstration")
        elif source_reliability in ["government", "official"]:
            # P1-4.1 F-04 containment: a free-text source label is NOT a
            # verification authority. Report "high" only for already-VERIFIED
            # evidence; otherwise label it explicitly as an unverified claim.
            if evidence.verification_status.value == "VERIFIED":
                confidence_factors["source_reliability"] = "high"
                reasons.append("Source is government/official (verified)")
            else:
                confidence_factors["source_reliability"] = "unverified_label"
                reasons.append(
                    "Source labeled government/official but NOT verified "
                    "(label is not verification authority)")
        elif source_reliability in ["academic", "industry"]:
            confidence_factors["source_reliability"] = "medium"
            reasons.append("Source is academic/industry")
        
        # Add confidence level breakdown
        if trust_result["confidence"] == "high":
            confidence_factors["overall"] = "high"
        elif trust_result["confidence"] == "medium":
            confidence_factors["overall"] = "medium"
        else:
            confidence_factors["overall"] = "low"
        
        return {
            "reasons": reasons,
            "confidence_factors": confidence_factors,
            "warning": warning
        }
    
    def query_evidence_graph(self, query_type: str, **kwargs) -> Dict[str, Any]:
        """
        Query evidence graph using high-value query engine.
        
        Args:
            query_type: Type of query
            **kwargs: Query parameters
            
        Returns:
            Response with query results
        """
        try:
            if query_type == "find_supporting_evidence":
                evidence_id = kwargs.get("evidence_id")
                max_depth = kwargs.get("max_depth", 3)
                result = self.graph_query_engine.find_supporting_evidence(evidence_id, max_depth)
                return result.to_dict()
            
            elif query_type == "find_policy_sources":
                policy_type = kwargs.get("policy_type")
                result = self.graph_query_engine.find_policy_sources(policy_type)
                return result.to_dict()
            
            elif query_type == "find_company_evidence":
                company_name = kwargs.get("company_name")
                sector = kwargs.get("sector")
                result = self.graph_query_engine.find_company_evidence(company_name, sector)
                return result.to_dict()
            
            elif query_type == "find_related_evidence":
                evidence_id = kwargs.get("evidence_id")
                relation_types = kwargs.get("relation_types")
                max_depth = kwargs.get("max_depth", 2)
                result = self.graph_query_engine.find_related_evidence(evidence_id, relation_types, max_depth)
                return result.to_dict()
            
            elif query_type == "trace_provenance":
                evidence_id = kwargs.get("evidence_id")
                max_depth = kwargs.get("max_depth", 5)
                result = self.graph_query_engine.trace_provenance(evidence_id, max_depth)
                return result.to_dict()
            
            elif query_type == "explain_trust_path":
                evidence_id = kwargs.get("evidence_id")
                target_type = kwargs.get("target_type")
                result = self.graph_query_engine.explain_trust_path(evidence_id, target_type)
                return result.to_dict()
            
            else:
                return {
                    "success": False,
                    "error": "Unsupported query type",
                    "message": f"Query type '{query_type}' is not supported"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute graph query"
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get service status information.
        
        Returns:
            Response with service status
        """
        return {
            "success": True,
            "status": self.service_status.to_dict(),
            "message": "Trust Evidence Service status retrieved"
        }
    
    def _map_type_to_node(self, evidence_type: str) -> NodeType:
        """Map evidence type to graph node type."""
        type_mapping = {
            "policy": NodeType.POLICY,
            "company": NodeType.COMPANY,
            "technology": NodeType.TECHNOLOGY,
            "evidence": NodeType.EVIDENCE
        }
        return type_mapping.get(evidence_type.lower(), NodeType.EVIDENCE)