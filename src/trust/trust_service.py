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
import os
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from .evidence_object import EvidenceObject, VerificationStatus
from .provenance import ProvenanceChain
from .trust_score import TrustScoreCalculator
from .evidence_graph import EvidenceGraph, NodeType, RelationType
from .graph_query_engine import GraphQueryEngine
from .verification_event_log import (
    VerificationDecision,
    VerificationEventLog,
    HumanVerificationGate,
    HumanVerificationAuthority,
    HumanVerificationAuthorityRegistry,
    HUMAN_AUTHORITY_ROLES,
    compute_content_identity,
)


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
    
    def __init__(
        self,
        event_log_path: Optional[str] = None,
        authority_registry: Optional[HumanVerificationAuthorityRegistry] = None,
    ):
        """Initialize trust evidence service.

        Args:
            event_log_path: Optional path to the durable verification event
                log (JSONL).  When provided, verify_evidence() records
                VerificationDecision events to this log.  When None (default),
                no event log is active — backward compatible with all
                existing callers that use TrustEvidenceService().
            authority_registry: (P1-4.5) Optional HumanVerificationAuthorityRegistry.
                When provided, VERIFIED can only be granted if the verifier_id
                is registered AND active AND role matches.  When None (default),
                VERIFIED is NEVER granted (fail closed — closes the free-string
                verifier_id loophole).  Non-VERIFIED operations are unaffected.
        """
        self.evidence_graph = EvidenceGraph()
        self.graph_query_engine = GraphQueryEngine(self.evidence_graph)
        self.trust_calculator = TrustScoreCalculator()
        self.event_log: Optional[VerificationEventLog] = (
            VerificationEventLog(event_log_path) if event_log_path else None
        )
        self.authority_registry: Optional[HumanVerificationAuthorityRegistry] = authority_registry
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

                # P1-4.2: Record durable verification event if log is active.
                # This records the decision but does NOT grant VERIFIED —
                # mock verification always results in MOCK status.
                if self.event_log is not None:
                    content_id = compute_content_identity(evidence.to_dict())
                    decision = VerificationDecision(
                        event_id=uuid.uuid4().hex,
                        evidence_id=evidence_id,
                        decision="mock",
                        actor="mock_system",
                        actor_role="system",
                        method="mock_verification",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        content_identity=content_id,
                        evidence_refs=[evidence.source_reference] if evidence.source_reference else [],
                        notes="Mock verification (not authoritative)",
                    )
                    self.event_log.append(decision)  # raises on failure — never silent

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

    def get_verification_history(self, evidence_id: str) -> Dict[str, Any]:
        """Get durable verification event history for an evidence.

        P1-4.2: reads from the VerificationEventLog (if active).  Returns
        the chronological list of VerificationDecision records.  If no
        event log is configured, returns success=False with a clear message.

        This is a READ-ONLY operation — it never changes verification_status.
        """
        if self.event_log is None:
            return {
                "success": False,
                "error": "No event log configured",
                "message": "TrustEvidenceService was initialized without event_log_path"
            }
        try:
            events = self.event_log.get_events_for_evidence(evidence_id)
            return {
                "success": True,
                "evidence_id": evidence_id,
                "event_count": len(events),
                "events": [e.to_dict() for e in events],
                "message": f"{len(events)} verification event(s) found"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve verification history"
            }

    def record_human_verification(
        self,
        evidence_id: str,
        verifier_id: str,
        verifier_role: str,
        verification_evidence: List[str],
        notes: str = "",
    ) -> Dict[str, Any]:
        """P1-4.3: Record a human verification decision and attempt to grant VERIFIED.

        This is the ONLY method that can result in evidence.verification_status
        being set to VERIFIED.  It enforces all security rules:

        - verifier_role must be in HUMAN_AUTHORITY_ROLES (Rule A/B)
        - verifier_id must be present (Rule B)
        - verification_evidence must be non-empty (Rule B)
        - content_identity is computed from the evidence (Rule D)
        - The decision event is persisted to the durable EventLog (Rule C)
        - The evidence must NOT be MOCK (Rule E)
        - The HumanVerificationGate must confirm all conditions (Rule F)

        If ANY condition fails, VERIFIED is NOT granted and the failure
        reason is returned.  The event is still recorded only if the
        EventLog's own safety gates pass (agent+verified→ValueError).

        Agent/System/Mock can NEVER call this method successfully because
        their roles are not in HUMAN_AUTHORITY_ROLES.

        Returns: {"success": bool, "evidence_id": str, "verification_status": str, ...}
        """
        if self.event_log is None:
            return {
                "success": False,
                "error": "No event log configured",
                "message": "Human verification requires a durable event log"
            }

        # P1-4.5: Authority Registry required — fail closed.
        # Without a registry, VERIFIED is NEVER granted (closes the free-string
        # verifier_id loophole).  The event is NOT recorded when the registry
        # is absent, because recording a "verified" event that can never be
        # granted would only pollute the audit log.
        if self.authority_registry is None:
            return {
                "success": False,
                "evidence_id": evidence_id,
                "error": "no_authority_registry",
                "verification_status": "UNVERIFIED",
                "message": "No Authority Registry configured — VERIFIED cannot be "
                           "granted without a registered, active verifier (P1-4.5)"
            }

        # Rule A/B: validate verifier_role
        if verifier_role not in HUMAN_AUTHORITY_ROLES:
            return {
                "success": False,
                "evidence_id": evidence_id,
                "error": "invalid_verifier_role",
                "verification_status": "UNVERIFIED",
                "message": f"verifier_role '{verifier_role}' is not in HUMAN_AUTHORITY_ROLES "
                           f"({sorted(HUMAN_AUTHORITY_ROLES)}). Agent/System/Mock cannot grant VERIFIED."
            }

        # P1-4.5: verifier_id must be registered AND active AND role must match.
        # This is the identity-binding gate — an unregistered verifier_id is
        # denied, never assumed human.
        if not self.authority_registry.is_authorized(verifier_id, verifier_role):
            if not self.authority_registry.is_registered(verifier_id):
                msg = (f"verifier_id '{verifier_id}' is NOT registered in the "
                       "Authority Registry — unknown verifier denied (P1-4.5)")
            elif not self.authority_registry.is_active(verifier_id):
                msg = (f"verifier_id '{verifier_id}' is registered but INACTIVE — "
                       "inactive verifier cannot grant VERIFIED (P1-4.5)")
            else:
                msg = (f"verifier_id '{verifier_id}' registered role does not match "
                       f"verifier_role '{verifier_role}' — role mismatch denied (P1-4.5)")
            return {
                "success": False,
                "evidence_id": evidence_id,
                "error": "verifier_not_authorized",
                "verification_status": "UNVERIFIED",
                "message": msg
            }

        # Rule B: verifier_id must be present
        if not verifier_id or not str(verifier_id).strip():
            return {
                "success": False,
                "evidence_id": evidence_id,
                "error": "missing_verifier_id",
                "verification_status": "UNVERIFIED",
                "message": "verifier_id must be present (Rule B)"
            }

        # Rule B: verification_evidence must be non-empty
        if not verification_evidence:
            return {
                "success": False,
                "evidence_id": evidence_id,
                "error": "missing_verification_evidence",
                "verification_status": "UNVERIFIED",
                "message": "verification_evidence must be non-empty (Rule B)"
            }

        try:
            # Get the evidence via existing API
            result = self.get_evidence(evidence_id)
            if not result["success"]:
                return {
                    "success": False,
                    "evidence_id": evidence_id,
                    "error": "evidence_not_found",
                    "verification_status": "UNVERIFIED",
                    "message": f"Evidence '{evidence_id}' not found"
                }

            evidence_data = result["evidence"]
            current_content_identity = compute_content_identity(evidence_data)

            # Rule E: MOCK is orthogonal — can never be VERIFIED
            is_mock = (
                evidence_data.get("verification_status") == "MOCK"
                or (evidence_data.get("metadata", {}) or {}).get("is_mock", False)
            )

            # Record the human decision event to the durable log
            decision = VerificationDecision(
                event_id=uuid.uuid4().hex,
                evidence_id=evidence_id,
                decision="verified",
                actor=verifier_id,
                actor_role=verifier_role,
                method="human_verification",
                timestamp=datetime.now(timezone.utc).isoformat(),
                content_identity=current_content_identity,
                evidence_refs=verification_evidence,
                notes=notes,
            )
            self.event_log.append(decision)  # raises on failure — never silent

            # Gate check: verify ALL conditions before granting VERIFIED
            gate = HumanVerificationGate(self.event_log, self.authority_registry)
            gate_result = gate.can_grant_verified(
                evidence_id=evidence_id,
                expected_content_identity=current_content_identity,
                evidence_is_mock=is_mock,
            )

            if gate_result["granted"]:
                # ONLY path to set VERIFIED — through the gate
                # Mutate the stored GraphNode data directly
                node = self.evidence_graph.nodes[evidence_id]
                node.data["verification_status"] = "VERIFIED"
                return {
                    "success": True,
                    "evidence_id": evidence_id,
                    "verification_status": "VERIFIED",
                    "verifier_id": verifier_id,
                    "verifier_role": verifier_role,
                    "content_identity": current_content_identity,
                    "event_id": decision.event_id,
                    "message": "Human verification recorded and VERIFIED granted via gate"
                }
            else:
                return {
                    "success": False,
                    "evidence_id": evidence_id,
                    "verification_status": evidence_data.get("verification_status", "UNVERIFIED"),
                    "verifier_id": verifier_id,
                    "event_id": decision.event_id,
                    "gate_reasons": gate_result["reasons"],
                    "message": "Human decision recorded but VERIFIED NOT granted — gate conditions not met"
                }

        except ValueError as e:
            return {
                "success": False,
                "evidence_id": evidence_id,
                "error": "event_log_rejected",
                "verification_status": "UNVERIFIED",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "evidence_id": evidence_id,
                "error": str(e),
                "verification_status": "UNVERIFIED",
                "message": "Failed to record human verification"
            }

    def detect_content_change(self, evidence_id: str) -> Dict[str, Any]:
        """P1-4.4: Detect if a VERIFIED evidence's content has changed.

        Compares the content_identity stored in the latest "verified" event
        against the current evidence's content_identity.  If they differ,
        the source content has changed and VERIFIED must be revoked.

        Returns:
            {"changed": bool, "verified_content_identity": Optional[str],
             "current_content_identity": Optional[str], "reason": str}
        """
        if self.event_log is None:
            return {
                "changed": False,
                "reason": "No event log configured — cannot detect changes"
            }

        try:
            # Get current evidence
            result = self.get_evidence(evidence_id)
            if not result["success"]:
                return {
                    "changed": False,
                    "reason": f"Evidence '{evidence_id}' not found"
                }

            current_ci = compute_content_identity(result["evidence"])

            # Find latest verified event
            events = self.event_log.get_events_for_evidence(evidence_id)
            latest_verified = None
            for evt in events:
                if evt.decision == "verified":
                    if latest_verified is None or evt.timestamp >= latest_verified.timestamp:
                        latest_verified = evt

            if latest_verified is None:
                return {
                    "changed": False,
                    "verified_content_identity": None,
                    "current_content_identity": current_ci,
                    "reason": "No verified event found — nothing to compare"
                }

            if latest_verified.content_identity is None:
                return {
                    "changed": False,
                    "verified_content_identity": None,
                    "current_content_identity": current_ci,
                    "reason": "Verified event has no content_identity"
                }

            if latest_verified.content_identity != current_ci:
                return {
                    "changed": True,
                    "verified_content_identity": latest_verified.content_identity,
                    "current_content_identity": current_ci,
                    "reason": "Content identity mismatch — source content has changed (Rule A)"
                }
            else:
                return {
                    "changed": False,
                    "verified_content_identity": latest_verified.content_identity,
                    "current_content_identity": current_ci,
                    "reason": "Content identity matches — VERIFIED still valid"
                }
        except Exception as e:
            return {
                "changed": False,
                "error": str(e),
                "reason": "Failed to detect content change"
            }

    def revoke_verified(self, evidence_id: str, reason: str = "content_changed") -> Dict[str, Any]:
        """P1-4.4: Revoke VERIFIED status and record a revocation event.

        This is an AUTOMATIC revocation — it does NOT require Human Authority.
        The system can revoke VERIFIED (Rule B) but can NEVER grant it (Rule C).

        The revocation event is recorded as:
          VerificationDecision(decision="revoked", actor="system_content_change_detector",
                               actor_role="system", content_identity=<current>,
                               notes=<JSON with previous + reason>)

        The old VERIFIED event is NOT deleted — it remains in the append-only
        log for audit history (Rule F).

        After revocation, evidence.verification_status is set to "UNVERIFIED".
        Re-verification requires a new Human Authority decision with the NEW
        content_identity (Rule C/D).
        """
        if self.event_log is None:
            return {
                "success": False,
                "error": "No event log configured",
                "message": "Revocation requires a durable event log"
            }

        try:
            # Get current evidence
            result = self.get_evidence(evidence_id)
            if not result["success"]:
                return {
                    "success": False,
                    "evidence_id": evidence_id,
                    "error": "evidence_not_found",
                    "message": f"Evidence '{evidence_id}' not found"
                }

            evidence_data = result["evidence"]
            current_ci = compute_content_identity(evidence_data)

            # Find the latest verified event to capture the old content_identity
            events = self.event_log.get_events_for_evidence(evidence_id)
            latest_verified_ci = None
            for evt in events:
                if evt.decision == "verified":
                    if latest_verified_ci is None or evt.timestamp >= (latest_verified_ci.timestamp if latest_verified_ci else ""):
                        latest_verified_ci = evt

            previous_ci = latest_verified_ci.content_identity if latest_verified_ci else None

            # Record revocation event (system actor — can revoke but NOT grant)
            import json as _json
            revocation_notes = _json.dumps({
                "previous_content_identity": previous_ci,
                "current_content_identity": current_ci,
                "reason": reason,
            })

            decision = VerificationDecision(
                event_id=uuid.uuid4().hex,
                evidence_id=evidence_id,
                decision="revoked",
                actor="system_content_change_detector",
                actor_role="system",
                method="automatic_content_change_detection",
                timestamp=datetime.now(timezone.utc).isoformat(),
                content_identity=current_ci,
                evidence_refs=[],
                notes=revocation_notes,
            )
            self.event_log.append(decision)  # raises on failure — never silent

            # Revoke VERIFIED — set back to UNVERIFIED
            node = self.evidence_graph.nodes[evidence_id]
            node.data["verification_status"] = "UNVERIFIED"

            return {
                "success": True,
                "evidence_id": evidence_id,
                "verification_status": "UNVERIFIED",
                "revoked": True,
                "previous_content_identity": previous_ci,
                "current_content_identity": current_ci,
                "event_id": decision.event_id,
                "reason": reason,
                "message": "VERIFIED revoked — content changed. Re-verification requires Human Authority."
            }
        except Exception as e:
            return {
                "success": False,
                "evidence_id": evidence_id,
                "error": str(e),
                "message": "Failed to revoke VERIFIED"
            }

    def check_verified_validity(self, evidence_id: str) -> Dict[str, Any]:
        """P1-4.4: Check whether an evidence's VERIFIED status is still valid.

        VERIFIED is valid ONLY if:
          1. Current verification_status == "VERIFIED"
          2. A human "verified" event exists in the durable log
          3. No later "revoked" event supersedes it
          4. The verified event's content_identity matches current
          5. The evidence is not MOCK

        If invalid, returns reasons.  This method does NOT automatically
        revoke — it reports.  Use revoke_verified() to act on a finding.
        """
        if self.event_log is None:
            return {
                "is_valid": False,
                "reasons": ["No event log configured"],
                "message": "Cannot verify without durable event log"
            }

        try:
            result = self.get_evidence(evidence_id)
            if not result["success"]:
                return {
                    "is_valid": False,
                    "reasons": [f"Evidence '{evidence_id}' not found"],
                    "message": "Evidence not found"
                }

            evidence_data = result["evidence"]
            current_ci = compute_content_identity(evidence_data)
            is_mock = (
                evidence_data.get("verification_status") == "MOCK"
                or (evidence_data.get("metadata", {}) or {}).get("is_mock", False)
            )

            gate = HumanVerificationGate(self.event_log, self.authority_registry)
            state = gate.get_effective_verified_state(
                evidence_id=evidence_id,
                current_content_identity=current_ci,
                evidence_is_mock=is_mock,
            )

            return {
                "is_valid": state["is_valid"],
                "reasons": state["reasons"],
                "current_verification_status": evidence_data.get("verification_status", "UNVERIFIED"),
                "current_content_identity": current_ci,
                "latest_verified_event": (
                    state["latest_verified_event"].to_dict()
                    if state["latest_verified_event"] else None
                ),
                "latest_revocation_event": (
                    state["latest_revocation_event"].to_dict()
                    if state["latest_revocation_event"] else None
                ),
                "message": "VERIFIED is valid" if state["is_valid"] else "VERIFIED is NOT valid"
            }
        except Exception as e:
            return {
                "is_valid": False,
                "reasons": [str(e)],
                "message": "Failed to check verified validity"
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