"""P1-5.2 — Trust Verification Showcase Demo Tests

Tests that the demo:
- Runs successfully (no NameError, no crash)
- Demonstrates the full verification lifecycle via real production APIs
- Agent/System cannot grant VERIFIED
- Registered human authority can grant VERIFIED
- Content identity changes are detected
- Revocation occurs and is recorded
- Revoked evidence is no longer VERIFIED
- New identity + human authority can re-verify
- MOCK remains MOCK
- No fake authentication claim

These tests import the demo module and exercise its functions directly
with a real TrustEvidenceService instance (same as the demo uses).
"""

import os
import sys
import shutil
import tempfile
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'examples'))

from trust.trust_service import TrustEvidenceService
from trust.verification_event_log import (
    HumanVerificationAuthority,
    HumanVerificationAuthorityRegistry,
    compute_content_identity,
)

# Import demo module
import trust_pipeline_demo as demo


class TestDemoRunsSuccessfully(unittest.TestCase):
    """Demo runs without NameError or crash."""

    def test_d001_demo_main_returns_true(self):
        """main() returns True — demo completes successfully."""
        result = demo.main()
        self.assertTrue(result)

    def test_d002_no_name_error(self):
        """The old NameError (step1_create_evidence_objects) is fixed."""
        # If the demo runs without NameError, this passes.
        # The old bug was: step1_create_evidence_objects vs step1_create_evidence_object
        import importlib
        # Force re-import to check for errors
        importlib.reload(demo)
        self.assertTrue(hasattr(demo, 'step_create_evidence'))
        self.assertTrue(hasattr(demo, 'main'))


class TestDemoEvidenceCreation(unittest.TestCase):
    """Demo creates evidence correctly."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.service = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry=demo.DEMO_AUTHORITY_REGISTRY,
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_d003_evidence_created_unverified(self):
        ci = demo.step_create_evidence(self.service)
        self.assertIsNotNone(ci)
        status = demo._get_status(self.service, demo.DEMO_EVIDENCE_ID)
        self.assertEqual(status, "UNVERIFIED")


class TestDemoAgentSystemDenied(unittest.TestCase):
    """Agent and System cannot grant VERIFIED."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.service = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry=demo.DEMO_AUTHORITY_REGISTRY,
        )
        demo.step_create_evidence(self.service)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_d004_agent_denied(self):
        """Agent role → record_human_verification returns success=False."""
        result = self.service.record_human_verification(
            evidence_id=demo.DEMO_EVIDENCE_ID,
            verifier_id="demo-agent-001",
            verifier_role="agent",
            verification_evidence=[demo.DEMO_EVIDENCE_SOURCE_REF],
        )
        self.assertFalse(result["success"])

    def test_d005_system_denied(self):
        """System role → record_human_verification returns success=False."""
        result = self.service.record_human_verification(
            evidence_id=demo.DEMO_EVIDENCE_ID,
            verifier_id="demo-system-001",
            verifier_role="system",
            verification_evidence=[demo.DEMO_EVIDENCE_SOURCE_REF],
        )
        self.assertFalse(result["success"])

    def test_d006_status_remains_unverified_after_agent(self):
        demo.step_agent_attempt(self.service)
        status = demo._get_status(self.service, demo.DEMO_EVIDENCE_ID)
        self.assertEqual(status, "UNVERIFIED")

    def test_d007_status_remains_unverified_after_system(self):
        demo.step_agent_attempt(self.service)
        demo.step_system_attempt(self.service)
        status = demo._get_status(self.service, demo.DEMO_EVIDENCE_ID)
        self.assertEqual(status, "UNVERIFIED")


class TestDemoHumanVerification(unittest.TestCase):
    """Registered human authority can grant VERIFIED."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.service = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry=demo.DEMO_AUTHORITY_REGISTRY,
        )
        demo.step_create_evidence(self.service)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_d008_human_verifier_grants_verified(self):
        result = self.service.record_human_verification(
            evidence_id=demo.DEMO_EVIDENCE_ID,
            verifier_id="demo-human-verifier",
            verifier_role="human_verifier",
            verification_evidence=[demo.DEMO_EVIDENCE_SOURCE_REF],
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["verification_status"], "VERIFIED")

    def test_d009_status_becomes_verified(self):
        demo.step_human_verification(self.service)
        status = demo._get_status(self.service, demo.DEMO_EVIDENCE_ID)
        self.assertEqual(status, "VERIFIED")

    def test_d010_unregistered_verifier_denied(self):
        """Unregistered verifier_id → denied."""
        result = self.service.record_human_verification(
            evidence_id=demo.DEMO_EVIDENCE_ID,
            verifier_id="random-stranger",
            verifier_role="human_verifier",
            verification_evidence=[demo.DEMO_EVIDENCE_SOURCE_REF],
        )
        self.assertFalse(result["success"])


class TestDemoMockEvidence(unittest.TestCase):
    """MOCK evidence can never become VERIFIED."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.service = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry=demo.DEMO_AUTHORITY_REGISTRY,
        )
        demo.step_create_evidence(self.service)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_d011_mock_remains_mock(self):
        demo.step_mock_evidence(self.service)
        status = demo._get_status(self.service, "demo-mock-evidence-001")
        self.assertEqual(status, "MOCK")

    def test_d012_mock_verification_denied(self):
        result = self.service.record_human_verification(
            evidence_id="demo-mock-evidence-001",
            verifier_id="demo-human-verifier",
            verifier_role="human_verifier",
            verification_evidence=["mock://test"],
        )
        self.assertFalse(result["success"])


class TestDemoContentChangeAndRevocation(unittest.TestCase):
    """Content change → revocation → re-verification lifecycle."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.service = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry=demo.DEMO_AUTHORITY_REGISTRY,
        )
        self.original_ci = demo.step_create_evidence(self.service)
        demo.step_human_verification(self.service)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_d013_content_identity_changes(self):
        new_ci = demo.step_content_change(self.service, self.original_ci)
        self.assertNotEqual(self.original_ci, new_ci)

    def test_d014_change_detected(self):
        demo.step_content_change(self.service, self.original_ci)
        result = self.service.detect_content_change(demo.DEMO_EVIDENCE_ID)
        self.assertTrue(result["changed"])

    def test_d015_verified_invalid_after_change(self):
        demo.step_content_change(self.service, self.original_ci)
        validity = self.service.check_verified_validity(demo.DEMO_EVIDENCE_ID)
        self.assertFalse(validity["is_valid"])

    def test_d016_revocation_occurs(self):
        demo.step_content_change(self.service, self.original_ci)
        result = self.service.revoke_verified(demo.DEMO_EVIDENCE_ID, "content_changed")
        self.assertTrue(result["revoked"])

    def test_d017_status_unverified_after_revocation(self):
        demo.step_content_change(self.service, self.original_ci)
        demo.step_revocation(self.service)
        status = demo._get_status(self.service, demo.DEMO_EVIDENCE_ID)
        self.assertEqual(status, "UNVERIFIED")

    def test_d018_revocation_event_in_log(self):
        demo.step_content_change(self.service, self.original_ci)
        demo.step_revocation(self.service)
        history = self.service.get_verification_history(demo.DEMO_EVIDENCE_ID)
        revoked = [e for e in history["events"] if e["decision"] == "revoked"]
        self.assertEqual(len(revoked), 1)

    def test_d019_verified_event_remains_in_log(self):
        """Old verified event is NOT deleted — append-only."""
        demo.step_content_change(self.service, self.original_ci)
        demo.step_revocation(self.service)
        history = self.service.get_verification_history(demo.DEMO_EVIDENCE_ID)
        verified = [e for e in history["events"] if e["decision"] == "verified"]
        self.assertGreaterEqual(len(verified), 1)


class TestDemoReverification(unittest.TestCase):
    """Re-verification with new content_identity → VERIFIED again."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.service = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry=demo.DEMO_AUTHORITY_REGISTRY,
        )
        self.original_ci = demo.step_create_evidence(self.service)
        demo.step_human_verification(self.service)
        demo.step_content_change(self.service, self.original_ci)
        demo.step_revocation(self.service)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_d020_reverification_succeeds(self):
        result = self.service.record_human_verification(
            evidence_id=demo.DEMO_EVIDENCE_ID,
            verifier_id="demo-human-verifier",
            verifier_role="human_verifier",
            verification_evidence=[demo.DEMO_EVIDENCE_SOURCE_REF],
            notes="Re-verification after content change",
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["verification_status"], "VERIFIED")

    def test_d021_status_verified_after_reverification(self):
        demo.step_reverification(self.service)
        status = demo._get_status(self.service, demo.DEMO_EVIDENCE_ID)
        self.assertEqual(status, "VERIFIED")

    def test_d022_validity_true_after_reverification(self):
        demo.step_reverification(self.service)
        validity = self.service.check_verified_validity(demo.DEMO_EVIDENCE_ID)
        self.assertTrue(validity["is_valid"])

    def test_d023_multiple_verified_events_in_history(self):
        """After re-verification, there should be 2 verified events + 1 revoked."""
        demo.step_reverification(self.service)
        history = self.service.get_verification_history(demo.DEMO_EVIDENCE_ID)
        verified = [e for e in history["events"] if e["decision"] == "verified"]
        revoked = [e for e in history["events"] if e["decision"] == "revoked"]
        self.assertEqual(len(verified), 2)
        self.assertEqual(len(revoked), 1)


class TestDemoNoFakeAuthentication(unittest.TestCase):
    """Demo must not claim real authentication."""

    def test_d024_demo_docstring_disclaims_authentication(self):
        doc = (demo.__doc__ or "").lower()
        self.assertIn("not real government data", doc)
        self.assertIn("not real-world identity authentication", doc)

    def test_d025_registry_metadata_disclaims_authentication(self):
        for auth in demo.DEMO_AUTHORITY_REGISTRY._by_id.values():
            meta_str = str(auth.metadata).lower()
            self.assertIn("application-level", meta_str)

    def test_d026_no_oauth_sso_password_claims(self):
        """Demo module must not mention OAuth/SSO/password as implemented."""
        import inspect
        source = inspect.getsource(demo).lower()
        # These terms may appear in "NOT" context, but not as claims
        self.assertNotIn("implements oauth", source)
        self.assertNotIn("provides authentication", source)
        self.assertNotIn("password verification", source)


if __name__ == "__main__":
    unittest.main()
