"""
Evidence Object Prototype

Prototype for the minimum trust primitive that future DeepTech agents can rely on.
NOT PRODUCTION CODE.

OpenInvest - Trust Evidence Prototype
"""

import json
import time
from enum import Enum
from typing import Dict, Any, Optional


class VerificationStatus(Enum):
    """Evidence verification status"""
    UNVERIFIED = "UNVERIFIED"
    MOCK = "MOCK"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class EvidenceObject:
    """
    Prototype Evidence Object for OpenInvest Trust System.
    
    This is a prototype, not production code.
    Build the minimum trust primitive that future DeepTech agents can rely on.
    """
    
    def __init__(
        self,
        id: str,
        type: str,
        source: str,
        source_reference: str,
        verification_status: VerificationStatus = VerificationStatus.UNVERIFIED,
        confidence_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Evidence Object.
        
        Args:
            id: Unique identifier for this evidence
            type: Type of evidence (policy, company, technology, etc.)
            source: Source of the evidence
            source_reference: Reference to the original source
            verification_status: Current verification status
            confidence_score: Confidence score (0.0-1.0)
            metadata: Additional metadata
        """
        self.id = id
        self.type = type
        self.source = source
        self.source_reference = source_reference
        self.verification_status = verification_status
        self.confidence_score = confidence_score
        self.created_time = time.time()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Evidence Object to dictionary format."""
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "source_reference": self.source_reference,
            "verification_status": self.verification_status.value,
            "confidence_score": self.confidence_score,
            "created_time": self.created_time,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceObject":
        """Create Evidence Object from dictionary."""
        verification_status = VerificationStatus(data.get("verification_status", "UNVERIFIED"))
        obj = cls(
            id=data["id"],
            type=data["type"],
            source=data["source"],
            source_reference=data["source_reference"],
            verification_status=verification_status,
            confidence_score=data.get("confidence_score", 0.0),
            metadata=data.get("metadata", {})
        )
        # Preserve original created_time for consistency
        obj.created_time = data.get("created_time", obj.created_time)
        return obj
    
    def validate(self) -> bool:
        """Validate Evidence Object data."""
        # Required fields
        required_fields = ["id", "type", "source"]
        for field in required_fields:
            if not getattr(self, field):
                return False
        
        # source_reference can be empty for mock data
        if not self.source_reference:
            pass  # Allow empty source_reference for mock data
        
        # Confidence score validation
        if not (0.0 <= self.confidence_score <= 1.0):
            return False
        
        # Verification status validation
        if self.verification_status not in VerificationStatus:
            return False
        
        # Time validation
        if self.created_time > time.time():
            return False
        
        return True
    
    def __str__(self) -> str:
        """String representation of Evidence Object."""
        return f"EvidenceObject(id={self.id}, type={self.type}, status={self.verification_status.value})"
    
    def __repr__(self) -> str:
        """Detailed representation of Evidence Object."""
        return f"EvidenceObject(id='{self.id}', type='{self.type}', source='{self.source}', verification_status={self.verification_status.value})"