"""P1-4.5 — Human Verification Authority Registry & Identity Binding Tests

Covers:
- Registry: register/lookup/active/authorized, duplicate rejection, malformed entry fail-closed
- VERIFIED gate with registry: registered active → allowed; unregistered/inactive/wrong-role → denied
- Security: no registry → VERIFIED denied (fail closed); agent/system/MOCK → denied;
  free-form verifier_id → denied; empty verifier_id → denied
- Identity binding: actor_role / registry role mismatch → denied
- Legacy compatibility: events remain readable; legacy events without registry → not VERIFIED
- Existing behavior: revocation still works; human re-verification still works;
  content_identity mismatch → denied; evidence_ref missing → denied
- Persistence: EventLog survives restart; deterministic registry lookup
- No authentication claim: registry is application-level authorization, not identity proof
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
    HumanVerificationAuthority,
    HumanVerificationAuthorityRegistry,
    HUMAN_AUTHORITY_ROLES,
    compute_content_identity,
)


def _build_registry(*authorities):
    """Helper: build a registry from the given authorities."""
    return HumanVerificationAuthorityRegistry(list(authorities))


def _std_verifier():
    return HumanVerificationAuthority("test-verifier", "human_verifier")


class TestRegistryBasics(unittest.TestCase):
    """Registry register / lookup / active / authorized."""

    def test_rg_001_register_and_lookup(self):
        reg = HumanVerificationAuthorityRegistry([_std_verifier()])
        self.assertIsNotNone(reg.lookup("test-verifier"))
        self.assertTrue(reg.is_registered("test-verifier"))

    def test_rg_002_lookup_unknown_returns_none(self):
        reg = HumanVerificationAuthorityRegistry([_std_verifier()])
        self.assertIsNone(reg.lookup("unknown"))
        self.assertFalse(reg.is_registered("unknown"))

    def test_rg_003_active_by_default(self):
        reg = HumanVerificationAuthorityRegistry([_std_verifier()])
        self.assertTrue(reg.is_active("test-verifier"))

    def test_rg_004_inactive_authority(self):
        a = HumanVerificationAuthority("v1", "human_verifier", active=False)
        reg = HumanVerificationAuthorityRegistry([a])
        self.assertTrue(reg.is_registered("v1"))
        self.assertFalse(reg.is_active("v1"))

    def test_rg_005_authorized_matches_role(self):
        reg = HumanVerificationAuthorityRegistry([_std_verifier()])
        self.assertTrue(reg.is_authorized("test-verifier", "human_verifier"))

    def test_rg_006_authorized_role_mismatch(self):
        reg = HumanVerificationAuthorityRegistry([_std_verifier()])
        self.assertFalse(reg.is_authorized("test-verifier", "authorized_reviewer"))

    def test_rg_007_duplicate_verifier_id_rejected(self):
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry([
                HumanVerificationAuthority("v1", "human_verifier"),
                HumanVerificationAuthority("v1", "human_verifier"),
            ])

    def test_rg_008_empty_registry(self):
        reg = HumanVerificationAuthorityRegistry()
        self.assertEqual(len(reg), 0)
        self.assertFalse(reg.is_authorized("anyone", "human_verifier"))


class TestRegistryMalformedEntry(unittest.TestCase):
    """Malformed entries must fail closed (raise)."""

    def test_me_001_empty_verifier_id_rejected(self):
        with self.assertRaises(ValueError):
            HumanVerificationAuthority("", "human_verifier")

    def test_me_002_invalid_role_rejected(self):
        with self.assertRaises(ValueError):
            HumanVerificationAuthority("v1", "agent")

    def test_me_003_non_bool_active_rejected(self):
        with self.assertRaises(ValueError):
            HumanVerificationAuthority("v1", "human_verifier", active="yes")

    def test_me_004_from_dict_missing_field(self):
        with self.assertRaises(ValueError):
            HumanVerificationAuthority.from_dict({"role": "human_verifier"})

    def test_me_005_from_dict_bad_role(self):
        with self.assertRaises(ValueError):
            HumanVerificationAuthority.from_dict({"verifier_id": "v1", "role": "super_admin"})


class TestVerifiedGateWithRegistry(unittest.TestCase):
    """VERIFIED gate now requires registry — registered active → allowed."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.registry = HumanVerificationAuthorityRegistry([_std_verifier()])
        self.service = TrustEvidenceService(
            event_log_path=self.log_path, authority_registry=self.registry)
        self.service.create_evidence({
            "id": "ev_gr_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_gr_001_registered_active_verifier_grants_verified(self):
        result = self.service.record_human_verification(
            evidence_id="ev_gr_001", verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        self.assertTrue(result["success"])
        self.assertEqual(result["verification_status"], "VERIFIED")

    def test_gr_002_unregistered_verifier_denied(self):
        result = self.service.record_human_verification(
            evidence_id="ev_gr_001", verifier_id="unknown-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertNotEqual(result["verification_status"], "VERIFIED")
        self.assertIn("NOT registered", result["message"])

    def test_gr_003_inactive_verifier_denied(self):
        self.registry.register(
            HumanVerificationAuthority("inactive-v", "human_verifier", active=False))
        result = self.service.record_human_verification(
            evidence_id="ev_gr_001", verifier_id="inactive-v",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertIn("INACTIVE", result["message"])

    def test_gr_004_wrong_role_denied(self):
        result = self.service.record_human_verification(
            evidence_id="ev_gr_001", verifier_id="test-verifier",
            verifier_role="authorized_reviewer",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertIn("role mismatch", result["message"])

    def test_gr_005_actor_role_registry_role_mismatch_denied(self):
        # Register with human_verifier but try with authorized_reviewer
        result = self.service.record_human_verification(
            evidence_id="ev_gr_001", verifier_id="test-verifier",
            verifier_role="authorized_reviewer",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])

    def test_gr_006_empty_verifier_id_denied(self):
        result = self.service.record_human_verification(
            evidence_id="ev_gr_001", verifier_id="",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])

    def test_gr_007_arbitrary_free_form_verifier_id_denied(self):
        result = self.service.record_human_verification(
            evidence_id="ev_gr_001", verifier_id="any-random-string-12345",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertIn("NOT registered", result["message"])


class TestNoRegistryFailClosed(unittest.TestCase):
    """Without registry, VERIFIED is NEVER granted (fail closed)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        # Service with event_log but NO registry
        self.service = TrustEvidenceService(event_log_path=self.log_path)
        self.service.create_evidence({
            "id": "ev_nr_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_nr_001_no_registry_denies_verified(self):
        result = self.service.record_human_verification(
            evidence_id="ev_nr_001", verifier_id="test-verifier",
            verifier_role="human_verifier",
            verification_evidence=["ref"])
        self.assertFalse(result["success"])
        self.assertIn("No Authority Registry", result["message"])

    def test_nr_002_gate_without_registry_denies(self):
        # Even if an event is manually appended, gate without registry → denied
        log = VerificationEventLog(self.log_path)
        d = VerificationDecision(
            event_id="evt_nr_002", evidence_id="ev_nr_001",
            decision="verified", actor="test-verifier",
            actor_role="human_verifier", method="test",
            timestamp="2026-09-01T10:00:00Z",
            content_identity="some_hash", evidence_refs=["ref"])
        log.append(d)
        gate = HumanVerificationGate(log)  # no registry
        result = gate.can_grant_verified("ev_nr_001", "some_hash", False)
        self.assertFalse(result["granted"])


class TestSecurityBoundaries(unittest.TestCase):
    """Agent/System/MOCK still blocked; content_identity/evidence_refs still enforced."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.registry = HumanVerificationAuthorityRegistry([_std_verifier()])
        self.service = TrustEvidenceService(
            event_log_path=self.log_path, authority_registry=self.registry)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_sb_001_agent_denied(self):
        self.service.create_evidence({
            "id": "ev_sb_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        result = self.service.record_human_verification(
            evidence_id="ev_sb_001", verifier_id="agent-bot",
            verifier_role="agent", verification_evidence=["ref"])
        self.assertFalse(result["success"])

    def test_sb_002_system_denied(self):
        self.service.create_evidence({
            "id": "ev_sb_002", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        result = self.service.record_human_verification(
            evidence_id="ev_sb_002", verifier_id="system-automator",
            verifier_role="system", verification_evidence=["ref"])
        self.assertFalse(result["success"])

    def test_sb_003_mock_denied(self):
        self.service.create_evidence({
            "id": "ev_sb_003", "type": "policy", "source": "mock",
            "source_reference": "", "verification_status": "MOCK",
            "confidence_score": 0.1,
        })
        result = self.service.record_human_verification(
            evidence_id="ev_sb_003", verifier_id="test-verifier",
            verifier_role="human_verifier", verification_evidence=["ref"])
        self.assertFalse(result["success"])

    def test_sb_004_content_identity_mismatch_denied(self):
        self.service.create_evidence({
            "id": "ev_sb_004", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        self.service.record_human_verification(
            evidence_id="ev_sb_004", verifier_id="test-verifier",
            verifier_role="human_verifier", verification_evidence=["ref"])
        # Change content
        node = self.service.evidence_graph.nodes["ev_sb_004"]
        node.data["confidence_score"] = 0.9
        result = self.service.check_verified_validity("ev_sb_004")
        self.assertFalse(result["is_valid"])

    def test_sb_005_evidence_ref_missing_denied(self):
        self.service.create_evidence({
            "id": "ev_sb_005", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        result = self.service.record_human_verification(
            evidence_id="ev_sb_005", verifier_id="test-verifier",
            verifier_role="human_verifier", verification_evidence=[])
        self.assertFalse(result["success"])


class TestLegacyEventCompatibility(unittest.TestCase):
    """Legacy events remain readable; legacy events without registry → not VERIFIED."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_lc_001_legacy_event_remains_readable(self):
        # Manually append a verified event (legacy style)
        log = VerificationEventLog(self.log_path)
        d = VerificationDecision(
            event_id="evt_lc_001", evidence_id="ev_legacy",
            decision="verified", actor="old-verifier",
            actor_role="human_verifier", method="legacy",
            timestamp="2026-08-01T10:00:00Z",
            content_identity="old_hash", evidence_refs=["ref"])
        log.append(d)
        # Replay must still read it
        events, malformed = log.replay()
        self.assertEqual(malformed, [])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].actor, "old-verifier")

    def test_lc_002_legacy_event_not_verified_without_registry(self):
        log = VerificationEventLog(self.log_path)
        d = VerificationDecision(
            event_id="evt_lc_002", evidence_id="ev_legacy",
            decision="verified", actor="old-verifier",
            actor_role="human_verifier", method="legacy",
            timestamp="2026-08-01T10:00:00Z",
            content_identity="old_hash", evidence_refs=["ref"])
        log.append(d)
        # Gate without registry → not granted
        gate = HumanVerificationGate(log)
        result = gate.can_grant_verified("ev_legacy", "old_hash", False)
        self.assertFalse(result["granted"])

    def test_lc_003_legacy_event_with_registry_unregistered_verifier(self):
        log = VerificationEventLog(self.log_path)
        d = VerificationDecision(
            event_id="evt_lc_003", evidence_id="ev_legacy",
            decision="verified", actor="old-verifier",
            actor_role="human_verifier", method="legacy",
            timestamp="2026-08-01T10:00:00Z",
            content_identity="old_hash", evidence_refs=["ref"])
        log.append(d)
        # Registry has a different verifier — old-verifier not registered
        reg = HumanVerificationAuthorityRegistry([
            HumanVerificationAuthority("new-verifier", "human_verifier")])
        gate = HumanVerificationGate(log, reg)
        result = gate.can_grant_verified("ev_legacy", "old_hash", False)
        self.assertFalse(result["granted"])
        self.assertTrue(any("NOT registered" in r for r in result["reasons"]))


class TestExistingBehaviorPreserved(unittest.TestCase):
    """Revocation, re-verification, and validity checks still work with registry."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.registry = HumanVerificationAuthorityRegistry([
            HumanVerificationAuthority("test-verifier", "human_verifier"),
            HumanVerificationAuthority("v1", "human_verifier"),
            HumanVerificationAuthority("v2", "human_verifier"),
        ])
        self.service = TrustEvidenceService(
            event_log_path=self.log_path, authority_registry=self.registry)
        self.service.create_evidence({
            "id": "ev_eb_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_eb_001_revocation_still_works(self):
        self.service.record_human_verification(
            evidence_id="ev_eb_001", verifier_id="test-verifier",
            verifier_role="human_verifier", verification_evidence=["ref"])
        node = self.service.evidence_graph.nodes["ev_eb_001"]
        node.data["confidence_score"] = 0.9
        result = self.service.revoke_verified("ev_eb_001")
        self.assertTrue(result["success"])
        self.assertEqual(result["verification_status"], "UNVERIFIED")

    def test_eb_002_human_re_verification_still_works(self):
        self.service.record_human_verification(
            evidence_id="ev_eb_001", verifier_id="test-verifier",
            verifier_role="human_verifier", verification_evidence=["ref"])
        node = self.service.evidence_graph.nodes["ev_eb_001"]
        node.data["confidence_score"] = 0.9
        self.service.revoke_verified("ev_eb_001")
        # Re-verify with the new content_identity
        result = self.service.record_human_verification(
            evidence_id="ev_eb_001", verifier_id="v2",
            verifier_role="human_verifier", verification_evidence=["ref2"])
        self.assertTrue(result["success"])
        self.assertEqual(result["verification_status"], "VERIFIED")

    def test_eb_003_verified_validity_check_works(self):
        self.service.record_human_verification(
            evidence_id="ev_eb_001", verifier_id="test-verifier",
            verifier_role="human_verifier", verification_evidence=["ref"])
        result = self.service.check_verified_validity("ev_eb_001")
        self.assertTrue(result["is_valid"])


class TestPersistenceAndDeterminism(unittest.TestCase):
    """EventLog survives restart; registry lookup is deterministic."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_pd_001_eventlog_survives_restart(self):
        reg = HumanVerificationAuthorityRegistry([_std_verifier()])
        service1 = TrustEvidenceService(
            event_log_path=self.log_path, authority_registry=reg)
        service1.create_evidence({
            "id": "ev_pd_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        service1.record_human_verification(
            evidence_id="ev_pd_001", verifier_id="test-verifier",
            verifier_role="human_verifier", verification_evidence=["ref"])
        # New service instance with same registry
        service2 = TrustEvidenceService(
            event_log_path=self.log_path, authority_registry=reg)
        events, malformed = service2.event_log.replay()
        self.assertEqual(malformed, [])
        self.assertTrue(any(e.decision == "verified" for e in events))

    def test_pd_002_deterministic_registry_lookup(self):
        reg = HumanVerificationAuthorityRegistry([_std_verifier()])
        # Same query → same result
        r1 = reg.is_authorized("test-verifier", "human_verifier")
        r2 = reg.is_authorized("test-verifier", "human_verifier")
        self.assertEqual(r1, r2)
        self.assertTrue(r1)

    def test_pd_003_multiple_events_chronological_history(self):
        reg = HumanVerificationAuthorityRegistry([
            HumanVerificationAuthority("v1", "human_verifier"),
            HumanVerificationAuthority("v2", "human_verifier"),
        ])
        service = TrustEvidenceService(
            event_log_path=self.log_path, authority_registry=reg)
        service.create_evidence({
            "id": "ev_pd_003", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/1",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        service.record_human_verification(
            evidence_id="ev_pd_003", verifier_id="v1",
            verifier_role="human_verifier", verification_evidence=["ref1"])
        node = service.evidence_graph.nodes["ev_pd_003"]
        node.data["confidence_score"] = 0.9
        service.revoke_verified("ev_pd_003")
        service.record_human_verification(
            evidence_id="ev_pd_003", verifier_id="v2",
            verifier_role="human_verifier", verification_evidence=["ref2"])
        events = service.event_log.get_events_for_evidence("ev_pd_003")
        # verified, revoked, verified (3 events)
        self.assertEqual(len(events), 3)


class TestNoAuthenticationClaim(unittest.TestCase):
    """Registry is application-level authorization, NOT identity authentication."""

    def test_na_001_metadata_not_identity_claim(self):
        a = HumanVerificationAuthority(
            "v1", "human_verifier",
            metadata={"display_name": "Test Verifier"})
        self.assertEqual(a.metadata["display_name"], "Test Verifier")
        # metadata is optional and does not affect authorization
        reg = HumanVerificationAuthorityRegistry([a])
        self.assertTrue(reg.is_authorized("v1", "human_verifier"))

    def test_na_002_registry_not_authentication(self):
        # The registry docstring must state it is NOT authentication
        self.assertIn(
            "not real-world identity",
            HumanVerificationAuthorityRegistry.__doc__)

    def test_na_003_no_fake_authority(self):
        # Registering an authority does NOT create a real user account
        reg = HumanVerificationAuthorityRegistry([_std_verifier()])
        # Registry is just an in-memory allowlist
        self.assertEqual(len(reg), 1)
        self.assertEqual(reg.all_authorities()[0].verifier_id, "test-verifier")


class TestBackwardCompatibility(unittest.TestCase):
    """Non-VERIFIED operations still work without registry."""

    def test_bc_001_service_without_registry_works(self):
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

    def test_bc_003_canonical_industry_unaffected(self):
        from trust.evidence_graph import EvidenceGraph, NodeType
        graph = EvidenceGraph()
        graph.add_node("bc_003", NodeType.POLICY, {"sector": "AI"})
        d = graph.nodes["bc_003"].to_dict()
        self.assertIn("canonical_industry", d)


if __name__ == '__main__':
    unittest.main()
