"""P1-4.2 — Verification Event Log Runtime Wiring + Content Identity Tests

Covers:
- Content identity (SHA-256 of canonical evidence content)
- EventLog runtime wiring into TrustEvidenceService
- F-04 second-layer safety (no VERIFIED-like trust without legitimate verification)
- Backward compatibility (legacy EvidenceObject without content_identity)

Governance: Agent 永远不能授予 VERIFIED。没有合法 verification evidence 不得产生 VERIFIED。
"""

import os
import sys
import json
import hashlib
import tempfile
import shutil
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from trust.evidence_object import EvidenceObject, VerificationStatus
from trust.trust_service import TrustEvidenceService
from trust.trust_score import TrustScoreCalculator
from trust.verification_event_log import (
    VerificationDecision,
    VerificationEventLog,
    VerificationStatusAdapter,
)


class TestContentIdentity(unittest.TestCase):
    """Content identity = SHA-256 of canonical evidence content."""

    def test_ci_001_deterministic_same_content(self):
        from trust.verification_event_log import compute_content_identity
        data = {"id": "ev1", "type": "policy", "source": "gov",
                "source_reference": "http://x", "verification_status": "UNVERIFIED",
                "confidence_score": 0.5}
        h1 = compute_content_identity(data)
        h2 = compute_content_identity(data)
        self.assertEqual(h1, h2)
        self.assertIsInstance(h1, str)
        self.assertEqual(len(h1), 64)  # sha256 hex

    def test_ci_002_key_order_independent(self):
        from trust.verification_event_log import compute_content_identity
        d1 = {"id": "ev1", "type": "policy", "source": "gov",
              "source_reference": "http://x", "verification_status": "UNVERIFIED",
              "confidence_score": 0.5}
        d2 = {"confidence_score": 0.5, "verification_status": "UNVERIFIED",
              "source_reference": "http://x", "source": "gov",
              "type": "policy", "id": "ev1"}
        self.assertEqual(compute_content_identity(d1), compute_content_identity(d2))

    def test_ci_003_content_change_changes_hash(self):
        from trust.verification_event_log import compute_content_identity
        d1 = {"id": "ev1", "type": "policy", "source": "gov",
              "source_reference": "http://x", "verification_status": "UNVERIFIED",
              "confidence_score": 0.5}
        d2 = dict(d1, confidence_score=0.9)
        self.assertNotEqual(compute_content_identity(d1), compute_content_identity(d2))

    def test_ci_004_empty_missing_content(self):
        from trust.verification_event_log import compute_content_identity
        # Empty dict still produces a deterministic hash
        h = compute_content_identity({})
        self.assertEqual(len(h), 64)
        # None input returns None (no content → no identity)
        self.assertIsNone(compute_content_identity(None))

    def test_ci_005_non_string_values(self):
        from trust.verification_event_log import compute_content_identity
        data = {"id": "ev1", "type": "policy", "source": "gov",
                "source_reference": "http://x", "verification_status": "UNVERIFIED",
                "confidence_score": 0.5, "nested": {"b": 1, "a": 2}}
        h1 = compute_content_identity(data)
        h2 = compute_content_identity(data)
        self.assertEqual(h1, h2)

    def test_ci_006_cross_instance_determinism(self):
        from trust.verification_event_log import compute_content_identity
        data = {"id": "ev1", "type": "policy", "source": "gov",
                "source_reference": "http://x", "verification_status": "UNVERIFIED",
                "confidence_score": 0.5}
        h1 = compute_content_identity(data)
        # Simulate cross-instance by computing in a fresh call
        h2 = compute_content_identity(json.loads(json.dumps(data)))
        self.assertEqual(h1, h2)


class TestEventLogRuntimeWiring(unittest.TestCase):
    """EventLog wired into TrustEvidenceService runtime path."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "verification_events.jsonl")
        self.service = TrustEvidenceService(event_log_path=self.log_path)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _create_evidence(self, evidence_id="ev_rt_001", source="government",
                         status="UNVERIFIED"):
        result = self.service.create_evidence({
            "id": evidence_id,
            "type": "policy",
            "source": source,
            "source_reference": "https://example.gov.cn/mock",
            "verification_status": status,
            "confidence_score": 0.5,
        })
        self.assertTrue(result["success"])
        return result

    def test_rw_001_verify_evidence_records_event(self):
        # verify_evidence (mock) must append a VerificationDecision to the log
        self._create_evidence()
        result = self.service.verify_evidence("ev_rt_001", "mock")
        self.assertTrue(result["success"])
        events = self.service.event_log.get_events_for_evidence("ev_rt_001")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].decision, "mock")
        self.assertEqual(events[0].actor_role, "system")

    def test_rw_002_event_contains_content_identity(self):
        self._create_evidence()
        self.service.verify_evidence("ev_rt_001", "mock")
        events = self.service.event_log.get_events_for_evidence("ev_rt_001")
        self.assertIsNotNone(events[0].content_identity)
        self.assertEqual(len(events[0].content_identity), 64)

    def test_rw_003_persistence_across_instances(self):
        self._create_evidence()
        self.service.verify_evidence("ev_rt_001", "mock")
        # New service instance pointing at same log file
        service2 = TrustEvidenceService(event_log_path=self.log_path)
        events = service2.event_log.get_events_for_evidence("ev_rt_001")
        self.assertEqual(len(events), 1)

    def test_rw_004_duplicate_event_id_rejected(self):
        self._create_evidence()
        self.service.verify_evidence("ev_rt_001", "mock")
        # Second verify call generates a new event_id (uuid4), so it should
        # succeed — but two calls with the SAME event_id must be rejected.
        from trust.verification_event_log import VerificationDecision
        d = VerificationDecision(
            event_id="forced_dup_id", evidence_id="ev_dup",
            decision="candidate", actor="agent-a", actor_role="agent",
            method="test", timestamp="2026-08-31T10:00:00Z")
        self.service.event_log.append(d)
        with self.assertRaises(ValueError):
            self.service.event_log.append(d)

    def test_rw_005_malformed_event_reported(self):
        # Write a valid event then corrupt a line
        self._create_evidence()
        self.service.verify_evidence("ev_rt_001", "mock")
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write("{corrupt json}\n")
        events, malformed = self.service.event_log.replay()
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(len(malformed), 1)

    def test_rw_006_write_failure_propagates(self):
        # verify_evidence wraps in try/except, so test the log directly:
        # pointing log_path to a directory forces OSError on append
        dir_path = os.path.join(self.tmpdir, "i_am_a_directory")
        os.makedirs(dir_path)
        self.service.event_log.log_path = dir_path
        from trust.verification_event_log import VerificationDecision
        d = VerificationDecision(
            event_id="wf_001", evidence_id="ev_wf",
            decision="candidate", actor="agent", actor_role="agent",
            method="test", timestamp="2026-08-31T10:00:00Z")
        with self.assertRaises(OSError):
            self.service.event_log.append(d)

    def test_rw_007_deterministic_replay(self):
        self._create_evidence()
        self.service.verify_evidence("ev_rt_001", "mock")
        events1, _ = self.service.event_log.replay()
        events2, _ = self.service.event_log.replay()
        self.assertEqual(
            [e.event_id for e in events1],
            [e.event_id for e in events2])

    def test_rw_008_get_verification_history(self):
        # New API: get_verification_history returns events for an evidence_id
        self._create_evidence()
        self.service.verify_evidence("ev_rt_001", "mock")
        result = self.service.get_verification_history("ev_rt_001")
        self.assertTrue(result["success"])
        self.assertEqual(result["event_count"], 1)
        self.assertEqual(len(result["events"]), 1)

    def test_rw_009_create_evidence_does_not_record_event(self):
        # create_evidence must NOT record a verification event — only
        # verify_evidence does.  This prevents false audit trail entries.
        self._create_evidence()
        events = self.service.event_log.get_events_for_evidence("ev_rt_001")
        self.assertEqual(len(events), 0)

    def test_rw_010_verify_does_not_upgrade_to_verified(self):
        # verify_evidence mock path must never produce VERIFIED
        self._create_evidence(status="UNVERIFIED")
        result = self.service.verify_evidence("ev_rt_001", "mock")
        self.assertEqual(result["verification_status"], "MOCK")
        self.assertNotEqual(result["verification_status"], "VERIFIED")


class TestF04SecondLayerSafety(unittest.TestCase):
    """F-04 second layer: no VERIFIED-like trust without legitimate verification."""

    def setUp(self):
        self.calculator = TrustScoreCalculator()

    def _ev(self, source, status):
        return {
            "id": "f04s_001", "type": "policy", "source": source,
            "source_reference": "http://x", "verification_status": status,
            "confidence_score": 0.5,
        }

    def test_f04s_001_verified_government_legitimate_path(self):
        # A: VERIFIED + government → high score (legitimate, if authority existed)
        result = self.calculator.calculate_trust_score(
            self._ev("government", "VERIFIED"),
            verification_status="VERIFIED")
        self.assertEqual(result["components"]["source_score"], 80)

    def test_f04s_002_unverified_government_contained(self):
        # B: UNVERIFIED + government → default, not boosted
        result = self.calculator.calculate_trust_score(
            self._ev("government", "UNVERIFIED"))
        self.assertEqual(result["components"]["source_score"], 50)

    def test_f04s_003_mock_government_contained(self):
        # C: MOCK + government → default, not boosted
        result = self.calculator.calculate_trust_score(
            self._ev("government", "MOCK"))
        self.assertEqual(result["components"]["source_score"], 50)

    def test_f04s_004_rejected_government_contained(self):
        # REJECTED + government → default, not boosted
        result = self.calculator.calculate_trust_score(
            self._ev("government", "REJECTED"))
        self.assertEqual(result["components"]["source_score"], 50)

    def test_f04s_005_agent_recommendation_no_verified_boost(self):
        # D: Agent can only produce "candidate" decisions, never VERIFIED.
        # An agent recommendation must not boost source_score.
        tmpdir = tempfile.mkdtemp()
        try:
            log_path = os.path.join(tmpdir, "events.jsonl")
            service = TrustEvidenceService(event_log_path=log_path)
            service.create_evidence(self._ev("government", "UNVERIFIED"))
            # Agent records a candidate decision (allowed)
            from trust.verification_event_log import VerificationDecision
            d = VerificationDecision(
                event_id="ag_001", evidence_id="f04s_001",
                decision="candidate", actor="agent-x", actor_role="agent",
                method="agent_proposal", timestamp="2026-08-31T10:00:00Z")
            service.event_log.append(d)
            # Even with a candidate event, evidence status remains UNVERIFIED
            result = service.calculate_trust("f04s_001")
            self.assertTrue(result["success"])
            self.assertNotEqual(result["verification_status"], "VERIFIED")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_f04s_006_missing_verification_event_no_verified(self):
        # E: No verification event at all → cannot be VERIFIED
        tmpdir = tempfile.mkdtemp()
        try:
            log_path = os.path.join(tmpdir, "events.jsonl")
            service = TrustEvidenceService(event_log_path=log_path)
            service.create_evidence(self._ev("government", "UNVERIFIED"))
            result = service.calculate_trust("f04s_001")
            self.assertEqual(result["verification_status"], "UNVERIFIED")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_f04s_007_missing_verifier_cannot_verified(self):
        # F: A verification event with missing actor/verifier info cannot
        # grant VERIFIED.  The event log safety gate enforces this.
        tmpdir = tempfile.mkdtemp()
        try:
            log_path = os.path.join(tmpdir, "events.jsonl")
            log = VerificationEventLog(log_path)
            # Attempt to record a "verified" decision with actor_role="agent"
            d = VerificationDecision(
                event_id="bad_001", evidence_id="ev_bad",
                decision="verified", actor="agent-x", actor_role="agent",
                method="fake", timestamp="2026-08-31T10:00:00Z")
            with self.assertRaises(ValueError):
                log.append(d)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestBackwardCompatibility(unittest.TestCase):
    """Legacy data without content_identity or events must not break."""

    def test_bc_001_legacy_evidence_object_without_content_identity(self):
        # EvidenceObject created the old way (no content_identity field)
        ev = EvidenceObject(id="legacy_001", type="policy", source="gov",
                            source_reference="http://x",
                            verification_status=VerificationStatus.UNVERIFIED)
        d = ev.to_dict()
        self.assertNotIn("content_identity", d)  # additive, not present
        # from_dict must still work
        ev2 = EvidenceObject.from_dict(d)
        self.assertEqual(ev2.id, "legacy_001")

    def test_bc_002_legacy_service_without_event_log(self):
        # TrustEvidenceService() without event_log_path must still work
        # (backward compatible — event_log is optional)
        service = TrustEvidenceService()
        result = service.create_evidence({
            "id": "bc_002", "type": "policy", "source": "mock",
            "source_reference": "", "verification_status": "MOCK",
            "confidence_score": 0.1,
        })
        self.assertTrue(result["success"])

    def test_bc_003_legacy_serialized_record_loads(self):
        # A serialized evidence dict from before P1-4.2 has no content_identity
        legacy_dict = {
            "id": "old_001", "type": "policy", "source": "government",
            "source_reference": "http://old.gov",
            "verification_status": "UNVERIFIED",
            "confidence_score": 0.5,
            "created_time": 1234567890,
            "metadata": {"is_mock": True},
        }
        ev = EvidenceObject.from_dict(legacy_dict)
        self.assertEqual(ev.id, "old_001")
        self.assertEqual(ev.verification_status, VerificationStatus.UNVERIFIED)

    def test_bc_004_mock_not_upgraded(self):
        service = TrustEvidenceService()
        service.create_evidence({
            "id": "bc_004", "type": "policy", "source": "mock",
            "source_reference": "", "verification_status": "MOCK",
            "confidence_score": 0.1,
        })
        result = service.verify_evidence("bc_004", "mock")
        self.assertEqual(result["verification_status"], "MOCK")

    def test_bc_005_canonical_industry_unaffected(self):
        # EvidenceGraph canonical_industry (P1-3.5) must still work
        from trust.evidence_graph import EvidenceGraph, GraphNode, NodeType
        graph = EvidenceGraph()
        graph.add_node("bc_005", NodeType.POLICY, {"sector": "AI"})
        d = graph.nodes["bc_005"].to_dict()
        self.assertEqual(d["data"]["sector"], "AI")
        self.assertIn("canonical_industry", d)


class TestTrustProvenancePreserved(unittest.TestCase):
    """Trust Score and Provenance semantics must not change."""

    def test_tp_001_trust_score_formula_unchanged(self):
        calc = TrustScoreCalculator()
        result = calc.calculate_trust_score({
            "id": "tp1", "type": "policy", "source": "academic",
            "source_reference": "http://x", "verification_status": "UNVERIFIED",
            "confidence_score": 0.5,
        })
        # Academic source weight = 0.6, but UNVERIFIED → fallback to default 0.5
        self.assertEqual(result["components"]["source_score"], 50)

    def test_tp_002_provenance_chain_still_works(self):
        from trust.provenance import ProvenanceChain
        chain = ProvenanceChain("tp_002")
        chain.add_verification_event("mock_verifier", "mock_method", "ok")
        self.assertTrue(chain.verify_integrity())

    def test_tp_003_no_fake_verifier_in_events(self):
        # Events recorded by verify_evidence must identify as system/mock,
        # never as a fake human verifier
        tmpdir = tempfile.mkdtemp()
        try:
            log_path = os.path.join(tmpdir, "events.jsonl")
            service = TrustEvidenceService(event_log_path=log_path)
            service.create_evidence({
                "id": "tp_003", "type": "policy", "source": "mock",
                "source_reference": "", "verification_status": "MOCK",
                "confidence_score": 0.1,
            })
            service.verify_evidence("tp_003", "mock")
            events = service.event_log.get_events_for_evidence("tp_003")
            self.assertEqual(len(events), 1)
            self.assertNotEqual(events[0].actor_role, "human")
            self.assertNotEqual(events[0].decision, "verified")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
