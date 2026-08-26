"""Trust Prototype Safety Tests

Additional safety tests for OpenInvest Trust Evidence Prototype.
Ensures prototype maintains experimental boundaries and prohibits dangerous claims.

Required Tests:
TEST-TRUST-SAFETY-001: 禁止生产声明
TEST-TRUST-SAFETY-002: 所有demo数据必须is_mock=true
TEST-TRUST-SAFETY-003: Trust Score必须包含confidence和reason
TEST-TRUST-SAFETY-004: Provenance hash修改后integrity check必须失败

NOT PRODUCTION CODE.

OpenInvest - Trust Evidence Prototype Independent Verification
"""

import unittest
import json
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from trust.evidence_object import EvidenceObject, VerificationStatus
from trust.provenance import ProvenanceChain
from trust.trust_score import TrustScoreCalculator
from trust.evidence_graph import EvidenceGraph, NodeType, RelationType


class TestTrustPrototypeSafety(unittest.TestCase):
    """Safety tests for trust prototype components."""
    
    def setUp(self):
        """Set up test data."""
        self.test_policy = {
            "id": "test_policy_001",
            "type": "policy",
            "source": "mock",
            "source_reference": "https://example.com/test-policy",
            "verification_status": "MOCK",
            "confidence_score": 0.7,
            "is_mock": True,
            "metadata": {}
        }
    
    def test_trust_safety_001_production_declarations_prohibited(self):
        """TEST-TRUST-SAFETY-001: 禁止生产声明"""
        # Test all source files don't contain production claims
        forbidden_phrases = [
            "production ready",
            "fully verified",
            "trusted network",
            "production deployment",
            "production environment"
        ]
        
        # Check all source files
        source_files = [
            "src/trust/evidence_object.py",
            "src/trust/provenance.py", 
            "src/trust/trust_score.py",
            "src/trust/evidence_graph.py"
        ]
        
        for file_path in source_files:
            file_path = os.path.join(os.path.dirname(__file__), "..", file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                
            for phrase in forbidden_phrases:
                self.assertNotIn(phrase, content, 
                    f"Found forbidden phrase '{phrase}' in {file_path}")
    
    def test_trust_safety_002_demo_data_mandatory_mock(self):
        """TEST-TRUST-SAFETY-002: 所有demo数据必须is_mock=true"""
        demo_dir = os.path.join(os.path.dirname(__file__), '..', 'examples', 'trust_demo')
        
        json_files = ['policy_example.json', 'company_example.json', 'evidence_example.json']
        
        for json_file in json_files:
            file_path = os.path.join(demo_dir, json_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.assertIn('is_mock', data, f"{json_file} missing 'is_mock' field")
            self.assertTrue(data['is_mock'], f"{json_file} has 'is_mock': {data['is_mock']}")
            
            # Ensure no real government data
            if 'source_reference' in data:
                self.assertNotIn('.gov.cn', data['source_reference'], 
                    f"{json_file} contains government domain in source_reference")
    
    def test_trust_safety_003_trust_score_confidence_reason(self):
        """TEST-TRUST-SAFETY-003: Trust Score必须包含confidence和reason"""
        calculator = TrustScoreCalculator()
        
        test_evidence = EvidenceObject(
            id="test_evidence_001",
            type="policy",
            source="mock",
            source_reference="https://example.com/test",
            verification_status=VerificationStatus.MOCK,
            confidence_score=0.5,
            metadata={}
        )
        
        # Convert evidence object to dict for trust score calculation
        evidence_dict = test_evidence.to_dict()
        result = calculator.calculate_trust_score(evidence_dict)
        
        # Must contain required fields
        self.assertIn('score', result)
        self.assertIn('confidence', result)
        self.assertIn('reason', result)
        
        # confidence must be valid
        valid_confidences = ['low', 'medium', 'high']
        self.assertIn(result['confidence'], valid_confidences)
        
        # reason must be a list
        self.assertIsInstance(result['reason'], list)
        self.assertTrue(len(result['reason']) > 0)
    
    def test_trust_safety_004_provenance_integrity_check_fails_on_hash_modification(self):
        """TEST-TRUST-SAFETY-004: Provenance hash修改后integrity check必须失败"""
        chain = ProvenanceChain("test_evidence")
        
        # Add a record
        record = chain.add_record("test_source", "test_action", "test_actor")
        original_hash = record.hash
        
        # Verify integrity passes with original hash
        self.assertTrue(chain.verify_integrity(), 
            "Integrity check should pass with original hash")
        
        # Modify the hash
        record.hash = "modified_hash_" + original_hash
        
        # Integrity check should now fail
        self.assertFalse(chain.verify_integrity(),
            "Integrity check should fail after hash modification")


if __name__ == '__main__':
    unittest.main()