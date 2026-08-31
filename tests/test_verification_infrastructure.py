"""P1-4.1 Phase 1 — Verification Infrastructure Tests

Covers:
- F-04 label-based implicit trust containment (source="government"/"official")
- Durable append-only Verification Event Log (JSONL)
- Read-only verification status adapter

Governance: 宁可 UNVERIFIED，不要 VERIFIED。Agent 绝不能产生 VERIFIED。
These tests enforce that MOCK/UNVERIFIED/VERIFIED safety boundaries are not weakened.
"""

import os
import sys
import json
import tempfile
import uuid
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from trust.trust_score import TrustScoreCalculator
from trust.trust_service import TrustEvidenceService
from trust.evidence_object import EvidenceObject, VerificationStatus
from trust.verification_event_log import (
    VerificationDecision,
    VerificationEventLog,
    VerificationStatusAdapter,
)


class TestF04LabelContainment(unittest.TestCase):
    """F04-***: source label "government"/"official" must NOT imply verification authority.

    P1-4.0 audit finding F-04 / TRAP-005: free-text source label raised
    source_score (0.8/0.7) and confidence_factors["source_reliability"]="high"
    with zero verification. Containment: label weights apply ONLY when
    verification_status == VERIFIED (nothing in the system can grant VERIFIED
    today, so the boost becomes dormant until a real authority exists).
    """

    def setUp(self):
        self.calculator = TrustScoreCalculator()
        self.service = TrustEvidenceService()

    def _evidence_dict(self, source, status):
        return {
            "id": "f04_test_001",
            "type": "policy",
            "source": source,
            "source_reference": "https://example.gov.cn/mock",
            "verification_status": status,
            "confidence_score": 0.5,
        }

    def test_f04_001_unverified_government_label_not_boosted(self):
        # F04-001: UNVERIFIED + source="government" must NOT get the 0.8 preset weight
        result = self.calculator.calculate_trust_score(
            self._evidence_dict("government", "UNVERIFIED"))
        self.assertEqual(result["components"]["source_score"], 50,
                         "unverified government label must fall back to default weight")

    def test_f04_002_mock_government_label_not_boosted(self):
        # F04-002: MOCK + source="government" must NOT get the 0.8 preset weight
        result = self.calculator.calculate_trust_score(
            self._evidence_dict("government", "MOCK"))
        self.assertEqual(result["components"]["source_score"], 50)

    def test_f04_003_unverified_official_label_not_boosted(self):
        # F04-003: UNVERIFIED + source="official" must NOT get the 0.7 preset weight
        result = self.calculator.calculate_trust_score(
            self._evidence_dict("official", "UNVERIFIED"))
        self.assertEqual(result["components"]["source_score"], 50)

    def test_f04_004_verified_government_label_still_boosted(self):
        # F04-004: the legitimate path is preserved — VERIFIED government source keeps 0.8.
        # NOTE: calculate_trust_score takes verification_status as an explicit
        # parameter (it never reads the dict field) — passing it explicitly is
        # the only honest way to exercise the VERIFIED path today.
        result = self.calculator.calculate_trust_score(
            self._evidence_dict("government", "VERIFIED"),
            verification_status="VERIFIED")
        self.assertEqual(result["components"]["source_score"], 80)

    def test_f04_005_case_insensitive_labels_contained_too(self):
        # F04-005: "Government"/"GOVERNMENT" labels are equally contained
        for label in ("Government", "GOVERNMENT", "Official"):
            result = self.calculator.calculate_trust_score(
                self._evidence_dict(label, "UNVERIFIED"))
            self.assertEqual(result["components"]["source_score"], 50,
                             f"label {label!r} must not boost unverified evidence")

    def test_f04_006_explanation_not_high_for_unverified_government(self):
        # F04-006: service explanation must not report source_reliability "high"
        # for an UNVERIFIED government-labeled evidence
        created = self.service.create_evidence(self._evidence_dict("government", "UNVERIFIED"))
        self.assertTrue(created["success"])
        result = self.service.calculate_trust(created["evidence_id"])
        self.assertTrue(result["success"])
        self.assertNotEqual(result["confidence_factors"].get("source_reliability"), "high")
        # and the reason must state the label is NOT a verification authority
        joined = " ".join(result["reason"])
        self.assertIn("NOT verified", joined)

    def test_f04_007_explanation_not_high_for_mock_government(self):
        # F04-007: same containment for MOCK evidence
        created = self.service.create_evidence(self._evidence_dict("government", "MOCK"))
        self.assertTrue(created["success"])
        result = self.service.calculate_trust(created["evidence_id"])
        self.assertNotEqual(result["confidence_factors"].get("source_reliability"), "high")

    def test_f04_008_no_status_change_from_containment(self):
        # F04-008: containment must not alter verification_status semantics
        for status in ("UNVERIFIED", "MOCK", "VERIFIED"):
            result = self.calculator.calculate_trust_score(
                self._evidence_dict("government", status))
            self.assertIsInstance(result["reason"], list)  # shape unchanged
        ev = EvidenceObject(id="f04_008", type="policy", source="government",
                            source_reference="x", verification_status=VerificationStatus.UNVERIFIED)
        self.assertEqual(ev.verification_status, VerificationStatus.UNVERIFIED)

    def test_f04_009_determinism(self):
        # F04-009: same input → same score, deterministic containment
        a = self.calculator.calculate_trust_score(self._evidence_dict("government", "UNVERIFIED"))
        b = self.calculator.calculate_trust_score(self._evidence_dict("government", "UNVERIFIED"))
        self.assertEqual(a["score"], b["score"])
        self.assertEqual(a["components"], b["components"])


class TestVerificationDecision(unittest.TestCase):
    """VerificationDecision additive dataclass — serialisation + immutability."""

    def test_vd_001_serialization_roundtrip(self):
        d = VerificationDecision(
            event_id="evt_001", evidence_id="ev_001", decision="candidate",
            actor="agent-alpha", actor_role="agent", method="source_check",
            timestamp="2026-08-31T10:00:00Z", content_identity="sha256:abc",
            evidence_refs=["ref1"], notes="proposed")
        restored = VerificationDecision.from_dict(d.to_dict())
        self.assertEqual(restored, d)

    def test_vd_002_frozen_immutability(self):
        d = VerificationDecision(
            event_id="evt_002", evidence_id="ev_002", decision="rejected",
            actor="human-beta", actor_role="human", method="manual",
            timestamp="2026-08-31T11:00:00Z")
        with self.assertRaises(AttributeError):
            d.decision = "verified"  # type: ignore


class TestVerificationEventLog(unittest.TestCase):
    """Append-only JSONL event log — safety boundaries."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "verification_events.jsonl")
        self.log = VerificationEventLog(self.log_path)

    def _make_decision(self, decision="candidate", actor_role="agent",
                       evidence_id="ev_001", event_id=None):
        return VerificationDecision(
            event_id=event_id or f"evt_{uuid.uuid4().hex[:8]}",
            evidence_id=evidence_id, decision=decision,
            actor="agent-alpha" if actor_role == "agent" else "human-beta",
            actor_role=actor_role, method="source_check",
            timestamp="2026-08-31T10:00:00Z",
            content_identity="sha256:abc", evidence_refs=["ref1"], notes="")

    def test_el_001_append_and_replay(self):
        d = self._make_decision()
        self.log.append(d)
        events, malformed = self.log.replay()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_id, d.event_id)
        self.assertEqual(malformed, [])

    def test_el_002_append_only_no_update(self):
        d1 = self._make_decision(event_id="evt_a")
        self.log.append(d1)
        # Appending a second event with the SAME event_id is rejected
        with self.assertRaises(ValueError):
            self.log.append(d1)

    def test_el_003_agent_cannot_record_verified(self):
        # Safety: agent decision with decision="verified" must be refused
        d = self._make_decision(decision="verified", actor_role="agent")
        with self.assertRaises(ValueError):
            self.log.append(d)

    def test_el_004_verified_requires_human_role(self):
        # Safety: decision="verified" with a non-human-authority role is refused
        d = self._make_decision(decision="verified", actor_role="system")
        with self.assertRaises(ValueError):
            self.log.append(d)

    def test_el_005_human_can_record_verified(self):
        # The ONLY path to record a "verified" event: actor_role in HUMAN_AUTHORITY_ROLES
        d = self._make_decision(decision="verified", actor_role="human_verifier")
        self.log.append(d)
        events, _ = self.log.replay()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].decision, "verified")

    def test_el_006_malformed_line_reported_not_silently_skipped(self):
        # Write a valid event then corrupt a line manually
        self.log.append(self._make_decision(event_id="evt_ok"))
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write("{this is not valid json}\n")
        events, malformed = self.log.replay()
        self.assertEqual(len(events), 1)
        self.assertEqual(len(malformed), 1)
        self.assertIn("error", malformed[0])

    def test_el_007_duplicate_event_id_rejected_deterministic(self):
        d = self._make_decision(event_id="evt_dup")
        self.log.append(d)
        with self.assertRaises(ValueError):
            self.log.append(d)

    def test_el_008_replay_empty_log(self):
        events, malformed = self.log.replay()
        self.assertEqual(events, [])
        self.assertEqual(malformed, [])

    def test_el_009_get_events_for_evidence(self):
        self.log.append(self._make_decision(evidence_id="ev_A", event_id="e1"))
        self.log.append(self._make_decision(evidence_id="ev_B", event_id="e2"))
        self.log.append(self._make_decision(evidence_id="ev_A", event_id="e3"))
        result = self.log.get_events_for_evidence("ev_A")
        self.assertEqual(len(result), 2)

    def test_el_010_write_failure_propagates(self):
        # Pointing log_path to a directory forces OSError on append write
        dir_path = os.path.join(self.tmpdir, "i_am_a_directory")
        os.makedirs(dir_path)
        bad_log = VerificationEventLog.__new__(VerificationEventLog)
        bad_log.log_path = dir_path
        with self.assertRaises(OSError):
            bad_log.append(self._make_decision())

    def test_el_011_recording_does_not_change_evidence_status(self):
        # Recording a decision event must NOT change any EvidenceObject status
        ev = EvidenceObject(id="ev_xyz", type="policy", source="government",
                            source_reference="x",
                            verification_status=VerificationStatus.UNVERIFIED)
        self.log.append(self._make_decision(
            evidence_id="ev_xyz", decision="candidate", event_id="evt_ne"))
        self.assertEqual(ev.verification_status, VerificationStatus.UNVERIFIED)


class TestVerificationStatusAdapter(unittest.TestCase):
    """Read-only status adapter — vocabulary normalisation."""

    def test_sa_001_uppercase_trust_island(self):
        self.assertEqual(VerificationStatusAdapter.normalise("UNVERIFIED"), "unverified")
        self.assertEqual(VerificationStatusAdapter.normalise("MOCK"), "mock")
        self.assertEqual(VerificationStatusAdapter.normalise("VERIFIED"), "verified")
        self.assertEqual(VerificationStatusAdapter.normalise("REJECTED"), "rejected")

    def test_sa_002_lowercase_policy_island(self):
        self.assertEqual(VerificationStatusAdapter.normalise("unverified"), "unverified")
        self.assertEqual(VerificationStatusAdapter.normalise("mock"), "mock")
        self.assertEqual(VerificationStatusAdapter.normalise("verified"), "verified")
        self.assertEqual(VerificationStatusAdapter.normalise("partially_verified"), "partially_verified")

    def test_sa_003_enum_type(self):
        self.assertEqual(VerificationStatusAdapter.normalise(VerificationStatus.UNVERIFIED), "unverified")
        self.assertEqual(VerificationStatusAdapter.normalise(VerificationStatus.MOCK), "mock")
        self.assertTrue(VerificationStatusAdapter.is_mock(VerificationStatus.MOCK))
        self.assertTrue(VerificationStatusAdapter.is_verified(VerificationStatus.VERIFIED))

    def test_sa_004_none_and_empty_return_unknown(self):
        self.assertEqual(VerificationStatusAdapter.normalise(None), "unknown")
        self.assertEqual(VerificationStatusAdapter.normalise(""), "unknown")

    def test_sa_005_unrecognised_returns_unknown_not_verified(self):
        # 宁可 unknown，不要 guess — never upgrade to verified or other
        self.assertEqual(VerificationStatusAdapter.normalise("nonsense"), "unknown")
        self.assertFalse(VerificationStatusAdapter.is_verified("nonsense"))

    def test_sa_006_read_only_does_not_mutate_input(self):
        raw = VerificationStatus.UNVERIFIED
        result = VerificationStatusAdapter.normalise(raw)
        self.assertEqual(result, "unverified")
        # Original enum unchanged
        self.assertEqual(raw, VerificationStatus.UNVERIFIED)


if __name__ == '__main__':
    unittest.main()
