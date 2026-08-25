"""
Trust Score Prototype

Simple scoring model for OpenInvest Trust System.
NOT PRODUCTION CODE.

Requirements:
- 不要复杂算法
- 不要机器学习
- 不要声称准确

OpenInvest - Trust Evidence Prototype
"""

import json
import time
from typing import Dict, Any, List, Optional
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence level for trust score"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TrustScoreCalculator:
    """
    Simple trust score prototype.
    
    Trust Score = Source Reliability + Evidence Completeness + Verification Status + Freshness
    
    No complex algorithms, no machine learning, no accuracy claims.
    """
    
    def __init__(self):
        """Initialize trust score calculator."""
        self.source_reliability_weights = {
            "government": 0.8,
            "official": 0.7,
            "academic": 0.6,
            "industry": 0.5,
            "mock": 0.1  # For prototype/demo only
        }
    
    def calculate_trust_score(
        self,
        evidence_dict: Dict[str, Any],
        source_reliability: float = 0.5,
        evidence_completeness: float = 0.5,
        verification_status: str = "UNVERIFIED",
        freshness_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate simple trust score.
        
        Args:
            evidence_dict: Evidence object dictionary
            source_reliability: Source reliability (0.0-1.0)
            evidence_completeness: Evidence completeness (0.0-1.0)  
            verification_status: Verification status string
            freshness_days: How many old the evidence is (days)
            
        Returns:
            Trust score result with confidence and reasons
        """
        
        # Calculate score components
        source_score = self._calculate_source_score(evidence_dict.get("source", ""), source_reliability)
        completeness_score = self._calculate_completeness_score(evidence_dict, evidence_completeness)
        verification_score = self._calculate_verification_score(verification_status)
        freshness_score = self._calculate_freshness_score(freshness_days)
        
        # Simple weighted sum (no machine learning, no complex algorithms)
        total_score = (
            source_score * 0.3 +
            completeness_score * 0.3 +
            verification_score * 0.2 +
            freshness_score * 0.2
        )
        
        # Convert to 0-100 scale
        score_100 = min(100, max(0, int(total_score * 100)))
        
        # Generate confidence level
        confidence = self._get_confidence_level(score_100)
        
        # Generate reasons
        reasons = self._generate_reasons(
            source_score,
            completeness_score,
            verification_score,
            freshness_score
        )
        
        return {
            "score": score_100,
            "confidence": confidence.value,
            "reason": reasons,
            "components": {
                "source_score": int(source_score * 100),
                "completeness_score": int(completeness_score * 100),
                "verification_score": int(verification_score * 100),
                "freshness_score": int(freshness_score * 100)
            }
        }
    
    def _calculate_source_score(self, source: str, manual_weight: float) -> float:
        """Calculate source reliability score."""
        # Use predefined weights if available
        if source.lower() in self.source_reliability_weights:
            return self.source_reliability_weights[source.lower()]
        # Fall back to manual weight
        return manual_weight
    
    def _calculate_completeness_score(self, evidence_dict: Dict[str, Any], base_score: float) -> float:
        """Calculate evidence completeness score."""
        # Check for required fields
        required_fields = ["id", "type", "source", "source_reference"]
        present_fields = sum(1 for field in required_fields if field in evidence_dict)
        
        completeness_ratio = present_fields / len(required_fields)
        return base_score * completeness_ratio
    
    def _calculate_verification_score(self, verification_status: str) -> float:
        """Calculate verification status score."""
        status_scores = {
            "VERIFIED": 1.0,
            "MOCK": 0.2,  # For prototype/demo
            "UNVERIFIED": 0.1,
            "REJECTED": 0.0
        }
        return status_scores.get(verification_status.upper(), 0.1)
    
    def _calculate_freshness_score(self, freshness_days: int) -> float:
        """Calculate freshness score."""
        # Simple decay: newer is better
        if freshness_days <= 7:
            return 1.0
        elif freshness_days <= 30:
            return 0.8
        elif freshness_days <= 90:
            return 0.6
        elif freshness_days <= 180:
            return 0.4
        else:
            return 0.2
    
    def _get_confidence_level(self, score: int) -> ConfidenceLevel:
        """Get confidence level based on score."""
        if score >= 80:
            return ConfidenceLevel.HIGH
        elif score >= 50:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _generate_reasons(self, source_score: float, completeness_score: float, verification_score: float, freshness_score: float) -> List[str]:
        """Generate human-readable reasons for trust score."""
        reasons = []
        
        if source_score >= 0.7:
            reasons.append("source available")
        elif source_score >= 0.3:
            reasons.append("source available but limited reliability")
        else:
            reasons.append("source reliability concerns")
        
        if completeness_score >= 0.8:
            reasons.append("evidence complete")
        elif completeness_score >= 0.5:
            reasons.append("evidence partially complete")
        else:
            reasons.append("evidence incomplete")
        
        if verification_score >= 0.8:
            reasons.append("independently verified")
        elif verification_score >= 0.3:
            reasons.append("not independently verified")
        else:
            reasons.append("verification concerns")
        
        if freshness_score >= 0.8:
            reasons.append("recent data")
        elif freshness_score >= 0.5:
            reasons.append("moderately recent")
        else:
            reasons.append("data potentially outdated")
        
        return reasons
    
    def calculate_for_evidence_object(self, evidence_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate trust score for evidence object."""
        return self.calculate_trust_score(evidence_dict)


# Example usage
def example_trust_score_calculation():
    """Example of trust score calculation."""
    calculator = TrustScoreCalculator()
    
    # Example 1: Mock policy evidence (for prototype)
    mock_evidence = {
        "id": "policy_001",
        "type": "policy",
        "source": "mock",  # Marked as mock for prototype
        "source_reference": "https://example-policy.gov",
        "verification_status": "MOCK",
        "confidence_score": 0.5
    }
    
    result = calculator.calculate_for_evidence_object(mock_evidence)
    print("Mock Trust Score Result:")
    print(json.dumps(result, indent=2))
    
    return result