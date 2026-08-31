"""P1-4.3 — Human Verification Authority Gate Tests

Covers:
- Authority: valid human verifier → VERIFIED allowed; missing/invalid roles rejected
- Event integrity: VERIFIED without event / mismatched evidence_id / mismatched content_identity rejected
- Safety: MOCK → never VERIFIED; UNVERIFIED → cannot bypass; Agent → cannot VERIFIED; unknown → never VERIFIED
- Persistence: decision survives replay; matching event found across instances

Governance: VERIFIED is not granted by Agent, System, MOCK, or label alone.
"""

import os
import sys
import shutil
import tempfile
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from trust.evidence_object import EvidenceObject, VerificationStatus
from trust.trust_service import TrustEvidenceService
from trust.verification_event_log import (
    VerificationDecision,
    VerificationEventLog,
    HumanVerificationGate,
    HUMAN_AUTHORITY_ROLES,
    compute_content_identity,
)


class TestHumanAuthorityGate(unittest.TestCase):
    """Authority role validation — who can grant VERIFIED."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.service = TrustEvidenceService(event_log_path=self.log_path)
        # Create non-mock UNVERIFIED evidence
        self.service.create_evidence({
            "id": "ev_hv_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_hv_001_valid_human_verifier_grants_verified(self):
        result = self.service.record_human_verification(
            evidence_id="ev_hv_001",
            verifier_id="test-human-verifier-001",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"],
            notes="manual source check")
        self.assertTrue(result["success"])
        self.assertEqual(result["verification_status"], "VERIFIED")
        self.assertEqual(result["verifier_id"], "test-human-verifier-001")

    def test_hv_002_authorized_reviewer_grants_verified(self):
        result = self.service.record_human_verification(
            evidence_id="ev_hv_001",
            verifier_id="test-reviewer-002",
            verifier_role="authorized_reviewer",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertTrue(result["success"])
        self.assertEqual(result["verification_status"], "VERIFIED")

    def test_hv_003_missing_verifier_id_rejected(self):
        result = self.service.record_human_verification(
            evidence_id="ev_hv_001",
            verifier_id="",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertNotEqual(result["verification_status"], "VERIFIED")

    def test_hv_004_agent_role_rejected(self):
        result = self.service.record_human_verification(
            evidence_id="ev_hv_001",
            verifier_id="agent-bot",
            verifier_role="agent",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertIn("not in HUMAN_AUTHORITY_ROLES", result["message"])
        self.assertNotEqual(result["verification_status"], "VERIFIED")

    def test_hv_005_system_role_rejected(self):
        result = self.service.record_human_verification(
            evidence_id="ev_hv_001",
            verifier_id="system-automator",
            verifier_role="system",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertNotEqual(result["verification_status"], "VERIFIED")

    def test_hv_006_unknown_role_rejected(self):
        result = self.service.record_human_verification(
            evidence_id="ev_hv_001",
            verifier_id="mystery",
            verifier_role="super_admin",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertNotEqual(result["verification_status"], "VERIFIED")

    def test_hv_007_missing_verification_evidence_rejected(self):
        result = self.service.record_human_verification(
            evidence_id="ev_hv_001",
            verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=[])
        self.assertFalse(result["success"])
        self.assertNotEqual(result["verification_status"], "VERIFIED")


class TestEventIntegrity(unittest.TestCase):
    """VERIFIED must have matching event with matching content_identity."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.service = TrustEvidenceService(event_log_path=self.log_path)
        self.service.create_evidence({
            "id": "ev_ei_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        self.service.create_evidence({
            "id": "ev_ei_002", "type": "policy", "source": "academic",
            "source_reference": "https://example.edu/paper/002",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_ei_001_verified_without_event_rejected(self):
        # No event recorded yet — gate must reject
        log = VerificationEventLog(self.log_path)
        gate = HumanVerificationGate(log)
        result = gate.can_grant_verified("ev_ei_001", "some_hash", False)
        self.assertFalse(result["granted"])
        self.assertTrue(any("No verification decision event" in r for r in result["reasons"]))

    def test_ei_002_mismatched_evidence_id_rejected(self):
        # Record a verified event for ev_ei_001, then check gate for ev_ei_002
        self.service.record_human_verification(
            evidence_id="ev_ei_001",
            verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        log = VerificationEventLog(self.log_path)
        gate = HumanVerificationGate(log)
        # Check for ev_ei_002 — should NOT find a matching event
        result = gate.can_grant_verified("ev_ei_002", "any_hash", False)
        self.assertFalse(result["granted"])

    def test_ei_003_mismatched_content_identity_rejected(self):
        # Record a verified event with content_identity, then check with different hash
        self.service.record_human_verification(
            evidence_id="ev_ei_001",
            verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        log = VerificationEventLog(self.log_path)
        gate = HumanVerificationGate(log)
        result = gate.can_grant_verified(
            "ev_ei_001", "0123456789abcdef" * 4, False)  # wrong hash
        self.assertFalse(result["granted"])
        self.assertTrue(any("Content identity mismatch" in r for r in result["reasons"]))

    def test_ei_004_missing_content_identity_rejected(self):
        # Manually append an event without content_identity
        log = VerificationEventLog(self.log_path)
        d = VerificationDecision(
            event_id="evt_no_ci", evidence_id="ev_ei_001",
            decision="verified", actor="test-verifier",
            actor_role="human_verifier", method="human_verification",
            timestamp="2026-08-31T10:00:00Z",
            content_identity=None,  # missing!
            evidence_refs=["ref"])
        log.append(d)
        gate = HumanVerificationGate(log)
        result = gate.can_grant_verified("ev_ei_001", "some_hash", False)
        self.assertFalse(result["granted"])
        self.assertTrue(any("no content_identity" in r for r in result["reasons"]))

    def test_ei_005_missing_evidence_refs_rejected(self):
        log = VerificationEventLog(self.log_path)
        d = VerificationDecision(
            event_id="evt_no_refs", evidence_id="ev_ei_001",
            decision="verified", actor="test-verifier",
            actor_role="human_verifier", method="human_verification",
            timestamp="2026-08-31T10:00:00Z",
            content_identity="some_hash",
            evidence_refs=[])  # empty!
        log.append(d)
        gate = HumanVerificationGate(log)
        result = gate.can_grant_verified("ev_ei_001", "some_hash", False)
        self.assertFalse(result["granted"])
        self.assertTrue(any("no verification evidence references" in r for r in result["reasons"]))

    def test_ei_006_duplicate_event_id_rejected(self):
        log = VerificationEventLog(self.log_path)
        d = VerificationDecision(
            event_id="evt_dup", evidence_id="ev_ei_001",
            decision="verified", actor="test-verifier",
            actor_role="human_verifier", method="test",
            timestamp="2026-08-31T10:00:00Z",
            content_identity="hash", evidence_refs=["ref"])
        log.append(d)
        with self.assertRaises(ValueError):
            log.append(d)  # same event_id


class TestSafetyBoundaries(unittest.TestCase):
    """MOCK / UNVERIFIED / Agent / unknown — all cannot produce VERIFIED."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.service = TrustEvidenceService(event_log_path=self.log_path)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_sf_001_mock_never_verified(self):
        self.service.create_evidence({
            "id": "ev_mock_001", "type": "policy", "source": "mock",
            "source_reference": "", "verification_status": "MOCK",
            "confidence_score": 0.1,
        })
        result = self.service.record_human_verification(
            evidence_id="ev_mock_001",
            verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertNotEqual(result["verification_status"], "VERIFIED")

    def test_sf_002_unverified_cannot_bypass_gate(self):
        self.service.create_evidence({
            "id": "ev_unv_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        # Try with agent role — must be rejected
        result = self.service.record_human_verification(
            evidence_id="ev_unv_001",
            verifier_id="agent-bot",
            verifier_role="agent",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertNotEqual(result["verification_status"], "VERIFIED")

    def test_sf_003_agent_recommendation_cannot_verified(self):
        # An agent records a candidate decision — this must never produce VERIFIED
        self.service.create_evidence({
            "id": "ev_agent_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        # Directly append an agent candidate event
        d = VerificationDecision(
            event_id="evt_agent_cand", evidence_id="ev_agent_001",
            decision="candidate", actor="agent-x", actor_role="agent",
            method="agent_proposal", timestamp="2026-08-31T10:00:00Z",
            content_identity="some_hash", evidence_refs=["ref"])
        self.service.event_log.append(d)
        # Now check gate
        gate = HumanVerificationGate(self.service.event_log)
        result = gate.can_grant_verified("ev_agent_001", "some_hash", False)
        self.assertFalse(result["granted"])

    def test_sf_004_unknown_status_never_verified(self):
        log = VerificationEventLog(self.log_path)
        gate = HumanVerificationGate(log)
        # No events at all
        result = gate.can_grant_verified("nonexistent", "any_hash", False)
        self.assertFalse(result["granted"])

    def test_sf_005_government_label_alone_cannot_verified(self):
        # Having source="government" without a human decision event must NOT grant VERIFIED
        self.service.create_evidence({
            "id": "ev_gov_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        # No human verification recorded — just check gate
        gate = HumanVerificationGate(self.service.event_log)
        result = gate.can_grant_verified("ev_gov_001", "any_hash", False)
        self.assertFalse(result["granted"])

    def test_sf_006_verified_requires_event_log(self):
        # Service without event_log_path cannot grant VERIFIED
        service = TrustEvidenceService()
        service.create_evidence({
            "id": "ev_no_log", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        result = service.record_human_verification(
            evidence_id="ev_no_log",
            verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertIn("durable event log", result["message"])


class TestPersistence(unittest.TestCase):
    """Decision events survive replay and cross-instance lookup."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_ps_001_decision_survives_replay(self):
        service = TrustEvidenceService(event_log_path=self.log_path)
        service.create_evidence({
            "id": "ev_ps_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        service.record_human_verification(
            evidence_id="ev_ps_001",
            verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        events, malformed = service.event_log.replay()
        self.assertEqual(malformed, [])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].decision, "verified")

    def test_ps_002_matching_event_found_across_instances(self):
        service1 = TrustEvidenceService(event_log_path=self.log_path)
        service1.create_evidence({
            "id": "ev_ps_002", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        service1.record_human_verification(
            evidence_id="ev_ps_002",
            verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        # New service instance
        service2 = TrustEvidenceService(event_log_path=self.log_path)
        gate = HumanVerificationGate(service2.event_log)
        result = gate.can_grant_verified("ev_ps_002", None, False)
        # Should find the matching event (content_identity check is skipped
        # when expected is None)
        self.assertTrue(result["granted"])

    def test_ps_003_verified_status_persists_in_graph(self):
        service = TrustEvidenceService(event_log_path=self.log_path)
        service.create_evidence({
            "id": "ev_ps_003", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        result = service.record_human_verification(
            evidence_id="ev_ps_003",
            verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        self.assertTrue(result["success"])
        # Verify the evidence in the graph now has VERIFIED
        node = service.evidence_graph.nodes["ev_ps_003"]
        self.assertEqual(node.data["verification_status"], "VERIFIED")


class TestBackwardCompatibility(unittest.TestCase):
    """Legacy behavior preserved."""

    def test_bc_001_service_without_event_log_works(self):
        service = TrustEvidenceService()
        result = service.create_evidence({
            "id": "bc_001", "type": "policy", "source": "mock",
            "source_reference": "", "verification_status": "MOCK",
            "confidence_score": 0.1,
        })
        self.assertTrue(result["success"])

    def test_bc_002_mock_verify_still_works(self):
        service = TrustEvidenceService()
        service.create_evidence({
            "id": "bc_002", "type": "policy", "source": "mock",
            "source_reference": "", "verification_status": "MOCK",
            "confidence_score": 0.1,
        })
        result = service.verify_evidence("bc_002", "mock")
        self.assertEqual(result["verification_status"], "MOCK")

    def test_bc_003_unverified_stays_unverified(self):
        tmpdir = tempfile.mkdtemp()
        try:
            log_path = os.path.join(tmpdir, "events.jsonl")
            service = TrustEvidenceService(event_log_path=log_path)
            service.create_evidence({
                "id": "bc_003", "type": "policy", "source": "government",
                "source_reference": "https://example.gov.cn/1",
                "verification_status": "UNVERIFIED", "confidence_score": 0.5,
            })
            # No human verification recorded — must stay UNVERIFIED
            result = service.get_evidence("bc_003")
            self.assertEqual(result["verification_status"], "UNVERIFIED")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_bc_004_canonical_industry_unaffected(self):
        from trust.evidence_graph import EvidenceGraph, NodeType
        graph = EvidenceGraph()
        graph.add_node("bc_004", NodeType.POLICY, {"sector": "AI"})
        d = graph.nodes["bc_004"].to_dict()
        self.assertIn("canonical_industry", d)

    def test_bc_005_human_authority_roles_are_allowlisted(self):
        # Only these roles can grant VERIFIED
        self.assertIn("human_verifier", HUMAN_AUTHORITY_ROLES)
        self.assertIn("authorized_reviewer", HUMAN_AUTHORITY_ROLES)
        self.assertNotIn("agent", HUMAN_AUTHORITY_ROLES)
        self.assertNotIn("system", HUMAN_AUTHORITY_ROLES)
        self.assertNotIn("mock", HUMAN_AUTHORITY_ROLES)


class TestDeterminism(unittest.TestCase):
    """Gate checks are deterministic."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.service = TrustEvidenceService(event_log_path=self.log_path)
        self.service.create_evidence({
            "id": "ev_det_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_dt_001_gate_result_deterministic(self):
        self.service.record_human_verification(
            evidence_id="ev_det_001",
            verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        gate = HumanVerificationGate(self.service.event_log)
        evidence_data = self.service.get_evidence("ev_det_001")["evidence"]
        ci = compute_content_identity(evidence_data)
        r1 = gate.can_grant_verified("ev_det_001", ci, False)
        r2 = gate.can_grant_verified("ev_det_001", ci, False)
        self.assertEqual(r1["granted"], r2["granted"])
        self.assertEqual(r1["reasons"], r2["reasons"])

    def test_dt_002_replay_deterministic(self):
        self.service.record_human_verification(
            evidence_id="ev_det_001",
            verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        e1, _ = self.service.event_log.replay()
        e2, _ = self.service.event_log.replay()
        self.assertEqual(
            [e.event_id for e in e1],
            [e.event_id for e in e2])


if __name__ == '__main__':
    unittest.main()
