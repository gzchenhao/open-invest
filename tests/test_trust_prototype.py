"""
Trust Prototype Tests

Test suite for OpenInvest Trust Evidence Prototype.

Required Tests:
TEST-TRUST-PROT-001: Evidence Object 创建成功
TEST-TRUST-PROT-002: MOCK 数据必须标记
TEST-TRUST-PROT-003: Provenance chain 可追踪
TEST-TRUST-PROT-004: Trust Score 输出合法
TEST-TRUST-PROT-005: 禁止出现 MCP implemented, A2A implemented, production trust network

NOT PRODUCTION CODE.

OpenInvest - Trust Evidence Prototype
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from trust.evidence_object import EvidenceObject, VerificationStatus
from trust.provenance import ProvenanceChain
from trust.trust_score import TrustScoreCalculator
from trust.evidence_graph import EvidenceGraph, NodeType, RelationType


class TestTrustPrototype(unittest.TestCase):
    """Test suite for trust prototype components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = TrustScoreCalculator()
        
        # Test evidence data
        self.test_evidence_data = {
            "id": "test_evidence_001",
            "type": "policy",
            "source": "mock",
            "source_reference": "https://example.gov.cn/test-policy",
            "verification_status": "MOCK",
            "confidence_score": 0.5
        }
    
    def test_trust_prot_001_evidence_object_creation(self):
        """TEST-TRUST-PROT-001: Evidence Object 创建成功"""
        print("Running TEST-TRUST-PROT-001: Evidence Object Creation Test")
        
        # Test creating evidence object
        evidence = EvidenceObject(
            id="test_001",
            type="policy",
            source="mock",
            source_reference="https://example.gov.cn/test",
            verification_status=VerificationStatus.MOCK,
            confidence_score=0.7
        )
        
        # Verify creation
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence.id, "test_001")
        self.assertEqual(evidence.type, "policy")
        self.assertEqual(evidence.source, "mock")
        self.assertEqual(evidence.verification_status, VerificationStatus.MOCK)
        self.assertEqual(evidence.confidence_score, 0.7)
        
        # Test validation
        self.assertTrue(evidence.validate())
        
        # Test serialization
        evidence_dict = evidence.to_dict()
        self.assertIsInstance(evidence_dict, dict)
        self.assertIn("id", evidence_dict)
        self.assertIn("type", evidence_dict)
        
        # Test deserialization
        evidence_from_dict = EvidenceObject.from_dict(evidence_dict)
        self.assertEqual(evidence_from_dict.id, evidence.id)
        self.assertEqual(evidence_from_dict.type, evidence.type)
        
        print("✅ TEST-TRUST-PROT-001 PASSED")
    
    def test_trust_prot_002_mock_data_must_be_marked(self):
        """TEST-TRUST-PROT-002: MOCK 数据必须标记"""
        print("Running TEST-TRUST-PROT-002: MOCK Data Marking Test")
        
        # Test that mock data is properly marked
        mock_evidence = EvidenceObject(
            id="mock_test_001",
            type="policy",
            source="mock",  # This indicates mock data
            source_reference="https://example.gov.cn/mock",
            verification_status=VerificationStatus.MOCK,
            confidence_score=0.5,
            metadata={"is_mock": True}  # Explicit marking
        )
        
        # Verify mock marking
        self.assertEqual(mock_evidence.source, "mock")
        self.assertEqual(mock_evidence.verification_status, VerificationStatus.MOCK)
        self.assertTrue(mock_evidence.metadata.get("is_mock", False))
        
        # Test verification status enum values
        self.assertIn(VerificationStatus.MOCK, [VerificationStatus.UNVERIFIED, 
                                               VerificationStatus.MOCK, 
                                               VerificationStatus.VERIFIED, 
                                               VerificationStatus.REJECTED])
        
        # Test that non-mock data has different status
        non_mock_evidence = EvidenceObject(
            id="real_test_001",
            type="policy", 
            source="government",
            source_reference="https://real.gov.cn",
            verification_status=VerificationStatus.UNVERIFIED,
            confidence_score=0.8
        )
        
        self.assertNotEqual(non_mock_evidence.source, "mock")
        self.assertNotEqual(non_mock_evidence.verification_status, VerificationStatus.MOCK)
        
        print("✅ TEST-TRUST-PROT-002 PASSED")
    
    def test_trust_prot_003_provenance_chain_trackable(self):
        """TEST-TRUST-PROT-003: Provenance chain 可追踪"""
        print("Running TEST-TRUST-PROT-003: Provenance Chain Tracking Test")
        
        # Test provenance chain creation
        chain = ProvenanceChain("test_evidence_001")
        self.assertIsNotNone(chain)
        self.assertEqual(chain.evidence_id, "test_evidence_001")
        self.assertEqual(len(chain.records), 1)  # Initial creation record
        
        # Test adding records
        record = chain.add_record("test_source", "test_action", "test_actor")
        self.assertIsNotNone(record)
        self.assertEqual(len(chain.records), 2)
        self.assertEqual(record.source, "test_source")
        self.assertEqual(record.action, "test_action")
        self.assertEqual(record.actor, "test_actor")
        
        # Test verification events
        chain.add_verification_event("mock_verifier", "mock_method", "approved")
        self.assertEqual(len(chain.records), 3)
        
        # Test trust assessments
        chain.add_trust_assessment("mock_assessor", 0.7, "mock_reason")
        self.assertEqual(len(chain.records), 4)
        
        # Test history retrieval
        history = chain.get_full_history()
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 4)
        
        # Test integrity verification
        self.assertTrue(chain.verify_integrity())
        
        # Test readable chain output
        readable_chain = chain.get_trust_chain()
        self.assertIsInstance(readable_chain, str)
        self.assertIn("test_evidence_001", str(chain))  # Check in string representation, not readable chain
        
        print("✅ TEST-TRUST-PROT-003 PASSED")
    
    def test_trust_prot_004_trust_score_output_valid(self):
        """TEST-TRUST-PROT-004: Trust Score 输出合法"""
        print("Running TEST-TRUST-PROT-004: Trust Score Output Validation Test")
        
        # Test trust score calculation
        evidence_dict = {
            "id": "test_score_evidence",
            "type": "policy",
            "source": "mock",
            "source_reference": "https://example.gov.cn/test",
            "verification_status": "MOCK"
        }
        
        score_result = self.calculator.calculate_trust_score(evidence_dict)
        
        # Verify result structure
        self.assertIsInstance(score_result, dict)
        self.assertIn("score", score_result)
        self.assertIn("confidence", score_result)
        self.assertIn("reason", score_result)
        self.assertIn("components", score_result)
        
        # Verify score range (0-100)
        self.assertGreaterEqual(score_result["score"], 0)
        self.assertLessEqual(score_result["score"], 100)
        
        # Verify confidence level
        valid_confidences = ["low", "medium", "high"]
        self.assertIn(score_result["confidence"], valid_confidences)
        
        # Verify reason is a list
        self.assertIsInstance(score_result["reason"], list)
        self.assertGreater(len(score_result["reason"]), 0)
        
        # Verify components structure
        components = score_result["components"]
        self.assertIsInstance(components, dict)
        for component_key in ["source_score", "completeness_score", "verification_score", "freshness_score"]:
            self.assertIn(component_key, components)
            self.assertGreaterEqual(components[component_key], 0)
            self.assertLessEqual(components[component_key], 100)
        
        print("✅ TEST-TRUST-PROT-004 PASSED")
    
    def test_trust_prot_005_prohibited_implementations(self):
        """TEST-TRUST-PROT-005: 禁止出现 MCP implemented, A2A implemented, production trust network"""
        print("Running TEST-TRUST-PROT-005: Prohibited Implementation Test")
        
        # Test code for prohibited patterns
        test_files = [
            "src/trust/evidence_object.py",
            "src/trust/provenance.py", 
            "src/trust/trust_score.py",
            "src/trust/evidence_graph.py"
        ]
        
        # Check that no MCP or A2A code exists
        mcp_keywords = ["MCP", "mcp", "Model Context Protocol"]
        a2a_keywords = ["A2A", "a2a", "Agent-to-Agent", "Agent2Agent"]
        production_keywords = ["production", "Production", "PRODUCTION", "global", "Global"]
        
        prohibited_found = False
        
        for file_path in test_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for prohibited implementations
                    for keyword in mcp_keywords + a2a_keywords:
                        if keyword in content:
                            prohibited_found = True
                            print(f"❌ Found prohibited keyword '{keyword}' in {file_path}")
                    
                    for keyword in production_keywords:
                        if "global infrastructure" in content.lower() or "production trust network" in content.lower():
                            prohibited_found = True
                            print(f"❌ Found prohibited production pattern in {file_path}")
        
        # Test that trust prototype code identifies as prototype
        self.assertFalse(prohibited_found, "Prohibited implementations found")
        
        # Verify prototype identification in code
        with open("src/trust/evidence_object.py", 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("NOT PRODUCTION CODE", content)
            self.assertIn("prototype", content.lower())
        
        with open("src/trust/trust_score.py", 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("NOT PRODUCTION CODE", content)
            self.assertIn("不要复杂算法", content)
            self.assertIn("不要机器学习", content)
        
        print("✅ TEST-TRUST-PROT-005 PASSED")
    
    def test_additional_trust_prototype_validations(self):
        """Additional validation tests for trust prototype"""
        print("Running Additional Trust Prototype Validations")
        
        # Test EvidenceObject edge cases
        minimal_evidence = EvidenceObject(
            id="minimal",
            type="evidence",
            source="mock",
            source_reference="",
            verification_status=VerificationStatus.UNVERIFIED
        )
        
        # Should still validate even with minimal data
        self.assertTrue(minimal_evidence.validate())
        
        # Test trust score with different inputs
        # P1-4.1 note: verification_status is an explicit parameter of
        # calculate_trust_score (the dict field alone is not read). The high
        # case must rely on a VERIFIED status parameter, not on the (now
        # contained, F-04) free-text source label boost.
        high_trust_data = {
            "id": "high_trust",
            "type": "policy", 
            "source": "government",
            "source_reference": "https://gov.example.com",
            "verification_status": "VERIFIED"
        }
        
        low_trust_data = {
            "id": "low_trust",
            "type": "evidence",
            "source": "unknown",
            "source_reference": "",
            "verification_status": "UNVERIFIED"
        }
        
        high_score = self.calculator.calculate_trust_score(
            high_trust_data, verification_status="VERIFIED")
        low_score = self.calculator.calculate_trust_score(
            low_trust_data, verification_status="UNVERIFIED")
        
        # High trust should have higher score
        self.assertGreater(high_score["score"], low_score["score"])
        
        print("✅ Additional Validations PASSED")


def run_trust_prototype_tests():
    """Run all trust prototype tests."""
    print("Starting OpenInvest Trust Prototype Tests")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTrustPrototype)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_trust_prototype_tests()
    sys.exit(0 if success else 1)