"""
Evidence Provenance Chain Prototype

Implementation of the evidence provenance chain for OpenInvest Trust System.
This answers: "Why should I trust this evidence?"

Model:
Original Source
↓
Evidence Object
↓
Verification Event
↓
Trust Assessment

NOT PRODUCTION CODE.

OpenInvest - Trust Evidence Prototype
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ProvenanceRecord:
    """
    Provenance Record for tracking evidence history.
    
    Fields:
        source: Source of the action
        timestamp: When the action occurred
        action: What action was performed
        actor: Who performed the action
        hash: Hash of the record for integrity
    """
    source: str
    timestamp: float
    action: str
    actor: str
    hash: str = ""
    
    def __post_init__(self):
        """Generate hash after initialization."""
        if not self.hash:
            self.hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate hash for integrity verification."""
        content = f"{self.source}{self.timestamp}{self.action}{self.actor}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Provenance Record to dictionary."""
        return {
            "source": self.source,
            "timestamp": self.timestamp,
            "action": self.action,
            "actor": self.actor,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvenanceRecord":
        """Create Provenance Record from dictionary."""
        record = cls(
            source=data["source"],
            timestamp=data["timestamp"],
            action=data["action"],
            actor=data["actor"],
            hash=data.get("hash", "")
        )
        # Regenerate hash to ensure consistency
        if not record.hash:
            record.hash = record._generate_hash()
        return record


class ProvenanceChain:
    """
    Evidence Provenance Chain for tracking complete history.
    
    This builds the chain:
    Original Source → Evidence Object → Verification Event → Trust Assessment
    """
    
    def __init__(self, evidence_id: str):
        """Initialize provenance chain for specific evidence."""
        self.evidence_id = evidence_id
        self.records: List[ProvenanceRecord] = []
        self._initialize_chain()
    
    def _initialize_chain(self):
        """Initialize the provenance chain with creation record."""
        creation_record = ProvenanceRecord(
            source="system",
            timestamp=time.time(),
            action="create",
            actor="trust_prototype"
        )
        self.records.append(creation_record)
    
    def add_record(self, source: str, action: str, actor: str) -> ProvenanceRecord:
        """Add a new record to the provenance chain."""
        record = ProvenanceRecord(
            source=source,
            timestamp=time.time(),
            action=action,
            actor=actor
        )
        self.records.append(record)
        return record
    
    def add_verification_event(self, verifier: str, method: str, result: str):
        """Add a verification event to the chain."""
        # Use the complete action including result from the beginning
        complete_action = f"verify_{method}_{result}"
        record = self.add_record(
            source="verification_system",
            action=complete_action,
            actor=verifier
        )
        return record
    
    def add_trust_assessment(self, assessor: str, score: float, reason: str):
        """Add a trust assessment to the chain."""
        # Use the complete action including reason from the beginning
        complete_action = f"assess_score_{score}_reason_{reason}"
        record = self.add_record(
            source="trust_system",
            action=complete_action,
            actor=assessor
        )
        return record
    
    def get_full_history(self) -> List[Dict[str, Any]]:
        """Get complete provenance history."""
        return [record.to_dict() for record in self.records]
    
    def get_trust_chain(self) -> str:
        """Get readable trust chain for Agent queries."""
        chain = []
        for record in self.records:
            chain.append(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record.timestamp))}] "
                f"{record.action} by {record.actor} "
                f"(source: {record.source})"
            )
        return "\n".join(chain)
    
    def verify_integrity(self) -> bool:
        """Verify integrity of the provenance chain."""
        expected_records = []
        for record in self.records:
            expected_hash = record._generate_hash()
            if record.hash != expected_hash:
                return False
            expected_records.append(record)
        return True
    
    def __str__(self) -> str:
        """String representation of provenance chain."""
        return f"ProvenanceChain(evidence_id={self.evidence_id}, records_count={len(self.records)})"