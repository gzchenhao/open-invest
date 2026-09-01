"""P1-4.6 — Persistent / Config-Driven Human Authority Registry Tests

Covers:
- Config loading: valid config, from_config, deterministic, process-equivalent reload
- Fail-closed: missing file, malformed JSON, missing authorities key, wrong type,
  invalid role, invalid active, empty verifier_id, duplicate verifier_id, non-object entry
- VERIFIED gate with config-driven registry: registered active → allowed;
  unregistered/inactive/role-mismatch/empty → denied
- No config → VERIFIED denied (fail closed, no role-only fallback)
- Security: Agent/System/MOCK/content_identity_mismatch/missing_evidence_ref → denied
- Service integration: config_path param, explicit registry takes precedence,
  config load failure propagates (no silent fallback)
- Backward compatibility: legacy events readable, revocation/re-verification preserved,
  no authentication claim
"""

import json
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


def _write_config(path: str, authorities: list) -> str:
    """Write a JSON authority config file and return the path."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"authorities": authorities}, f, ensure_ascii=False)
    return path


def _valid_authority(vid="human-reviewer-001", role="human_verifier",
                     active=True, metadata=None):
    d = {"verifier_id": vid, "role": role, "active": active}
    if metadata is not None:
        d["metadata"] = metadata
    return d


class TestConfigLoading(unittest.TestCase):
    """from_config() loads a valid JSON config into a registry."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "authorities.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cl_001_valid_config_loads(self):
        _write_config(self.config_path, [
            _valid_authority("v1", "human_verifier"),
            _valid_authority("v2", "authorized_reviewer"),
        ])
        reg = HumanVerificationAuthorityRegistry.from_config(self.config_path)
        self.assertEqual(len(reg), 2)
        self.assertTrue(reg.is_authorized("v1", "human_verifier"))
        self.assertTrue(reg.is_authorized("v2", "authorized_reviewer"))

    def test_cl_002_deterministic_loading(self):
        _write_config(self.config_path, [
            _valid_authority("v1", "human_verifier"),
            _valid_authority("v2", "human_verifier", active=False),
        ])
        reg1 = HumanVerificationAuthorityRegistry.from_config(self.config_path)
        reg2 = HumanVerificationAuthorityRegistry.from_config(self.config_path)
        self.assertEqual(len(reg1), len(reg2))
        for vid in ("v1", "v2"):
            self.assertEqual(reg1.lookup(vid), reg2.lookup(vid))

    def test_cl_003_process_equivalent_reload(self):
        """Reloading the same config produces an equivalent registry."""
        _write_config(self.config_path, [
            _valid_authority("hr-001", "human_verifier", metadata={"display_name": "HR 1"}),
        ])
        reg1 = HumanVerificationAuthorityRegistry.from_config(self.config_path)
        # Simulate "process restart" by creating a fresh instance
        reg2 = HumanVerificationAuthorityRegistry.from_config(self.config_path)
        self.assertEqual(reg1.is_authorized("hr-001", "human_verifier"),
                         reg2.is_authorized("hr-001", "human_verifier"))
        self.assertEqual(reg1.lookup("hr-001").metadata,
                         reg2.lookup("hr-001").metadata)

    def test_cl_004_metadata_preserved(self):
        _write_config(self.config_path, [
            _valid_authority("v1", "human_verifier", metadata={"display_name": "Alice"}),
        ])
        reg = HumanVerificationAuthorityRegistry.from_config(self.config_path)
        self.assertEqual(reg.lookup("v1").metadata, {"display_name": "Alice"})

    def test_cl_005_empty_authorities_list(self):
        """An empty authorities list is valid — produces an empty registry."""
        _write_config(self.config_path, [])
        reg = HumanVerificationAuthorityRegistry.from_config(self.config_path)
        self.assertEqual(len(reg), 0)

    def test_cl_006_active_false_preserved(self):
        _write_config(self.config_path, [
            _valid_authority("v1", "human_verifier", active=False),
        ])
        reg = HumanVerificationAuthorityRegistry.from_config(self.config_path)
        self.assertTrue(reg.is_registered("v1"))
        self.assertFalse(reg.is_active("v1"))
        self.assertFalse(reg.is_authorized("v1", "human_verifier"))


class TestConfigFailClosed(unittest.TestCase):
    """Malformed / missing config → fail closed (raise, no registry returned)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "authorities.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_fc_001_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            HumanVerificationAuthorityRegistry.from_config(
                os.path.join(self.tmpdir, "nonexistent.json"))

    def test_fc_002_malformed_json_raises(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("{not valid json")
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config(self.config_path)

    def test_fc_003_missing_authorities_key_raises(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({"wrong_key": []}, f)
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config(self.config_path)

    def test_fc_004_authorities_not_list_raises(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({"authorities": "not a list"}, f)
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config(self.config_path)

    def test_fc_005_invalid_role_raises(self):
        _write_config(self.config_path, [
            _valid_authority("v1", "super_admin"),
        ])
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config(self.config_path)

    def test_fc_006_empty_verifier_id_raises(self):
        _write_config(self.config_path, [
            _valid_authority("", "human_verifier"),
        ])
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config(self.config_path)

    def test_fc_007_duplicate_verifier_id_raises(self):
        _write_config(self.config_path, [
            _valid_authority("v1", "human_verifier"),
            _valid_authority("v1", "human_verifier"),
        ])
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config(self.config_path)

    def test_fc_008_non_object_entry_raises(self):
        _write_config(self.config_path, ["not_an_object"])
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config(self.config_path)

    def test_fc_009_non_bool_active_raises(self):
        _write_config(self.config_path, [
            {"verifier_id": "v1", "role": "human_verifier", "active": "yes"},
        ])
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config(self.config_path)

    def test_fc_010_empty_config_path_raises(self):
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config("")

    def test_fc_011_config_not_dict_raises(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(["not", "a", "dict"], f)
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config(self.config_path)

    def test_fc_012_missing_verifier_id_field_raises(self):
        _write_config(self.config_path, [
            {"role": "human_verifier", "active": True},
        ])
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config(self.config_path)

    def test_fc_013_missing_role_field_raises(self):
        _write_config(self.config_path, [
            {"verifier_id": "v1", "active": True},
        ])
        with self.assertRaises(ValueError):
            HumanVerificationAuthorityRegistry.from_config(self.config_path)


class TestVerifiedGateWithConfigRegistry(unittest.TestCase):
    """VERIFIED gate with a config-driven registry."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.config_path = os.path.join(self.tmpdir, "authorities.json")
        _write_config(self.config_path, [
            _valid_authority("hr-001", "human_verifier"),
            _valid_authority("ar-002", "authorized_reviewer"),
        ])
        self.service = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry_config_path=self.config_path,
        )
        self.service.create_evidence({
            "id": "ev_cfg_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cg_001_registered_active_verifier_grants_verified(self):
        result = self.service.record_human_verification(
            evidence_id="ev_cfg_001",
            verifier_id="hr-001",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertTrue(result["success"])
        self.assertEqual(result["verification_status"], "VERIFIED")

    def test_cg_002_authorized_reviewer_grants_verified(self):
        result = self.service.record_human_verification(
            evidence_id="ev_cfg_001",
            verifier_id="ar-002",
            verifier_role="authorized_reviewer",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertTrue(result["success"])
        self.assertEqual(result["verification_status"], "VERIFIED")

    def test_cg_003_unregistered_verifier_denied(self):
        result = self.service.record_human_verification(
            evidence_id="ev_cfg_001",
            verifier_id="unknown-person",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertFalse(result["success"])
        self.assertEqual(result["verification_status"], "UNVERIFIED")

    def test_cg_004_inactive_verifier_denied(self):
        # Add an inactive verifier to config
        _write_config(self.config_path, [
            _valid_authority("hr-001", "human_verifier"),
            _valid_authority("ar-002", "authorized_reviewer"),
            _valid_authority("inactive-003", "human_verifier", active=False),
        ])
        svc = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry_config_path=self.config_path,
        )
        result = svc.record_human_verification(
            evidence_id="ev_cfg_001",
            verifier_id="inactive-003",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertFalse(result["success"])
        self.assertEqual(result["verification_status"], "UNVERIFIED")

    def test_cg_005_role_mismatch_denied(self):
        result = self.service.record_human_verification(
            evidence_id="ev_cfg_001",
            verifier_id="hr-001",
            verifier_role="authorized_reviewer",  # hr-001 is registered as human_verifier
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertFalse(result["success"])
        self.assertEqual(result["verification_status"], "UNVERIFIED")

    def test_cg_006_empty_verifier_id_denied(self):
        result = self.service.record_human_verification(
            evidence_id="ev_cfg_001",
            verifier_id="",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertFalse(result["success"])

    def test_cg_007_arbitrary_free_form_verifier_id_denied(self):
        result = self.service.record_human_verification(
            evidence_id="ev_cfg_001",
            verifier_id="i-am-root",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertFalse(result["success"])


class TestNoConfigFailClosed(unittest.TestCase):
    """No config + no registry → VERIFIED must NOT be granted (fail closed)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        # Service with event_log but NO authority registry and NO config path
        self.service = TrustEvidenceService(event_log_path=self.log_path)
        self.service.create_evidence({
            "id": "ev_nc_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_nc_001_no_registry_no_config_verified_denied(self):
        result = self.service.record_human_verification(
            evidence_id="ev_nc_001",
            verifier_id="anyone",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertFalse(result["success"])
        self.assertEqual(result["verification_status"], "UNVERIFIED")

    def test_nc_002_no_role_only_fallback(self):
        """Even with a valid role, without registry VERIFIED is denied."""
        result = self.service.record_human_verification(
            evidence_id="ev_nc_001",
            verifier_id="someone",
            verifier_role="authorized_reviewer",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertFalse(result["success"])
        # Must NOT be VERIFIED
        self.assertNotEqual(result.get("verification_status"), "VERIFIED")


class TestConfigSecurityBoundaries(unittest.TestCase):
    """Security boundaries preserved with config-driven registry."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.config_path = os.path.join(self.tmpdir, "authorities.json")
        _write_config(self.config_path, [
            _valid_authority("hr-001", "human_verifier"),
        ])
        self.service = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry_config_path=self.config_path,
        )
        self.service.create_evidence({
            "id": "ev_sec_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_sb_001_agent_denied(self):
        """Agent actor_role cannot grant VERIFIED."""
        # Agent records a candidate decision directly
        log = VerificationEventLog(self.log_path)
        content_id = compute_content_identity({
            "id": "ev_sec_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "confidence_score": 0.5,
        })
        agent_event = VerificationDecision(
            event_id="evt-agent-001",
            evidence_id="ev_sec_001",
            decision="verified",
            actor="agent-001",
            actor_role="agent",
            method="agent_proposal",
            timestamp="2026-09-01T10:00:00Z",
            content_identity=content_id,
            evidence_refs=["https://example.gov.cn/policy/001"],
        )
        with self.assertRaises(ValueError):
            log.append(agent_event)

    def test_sb_002_system_denied(self):
        """System actor_role cannot grant VERIFIED."""
        log = VerificationEventLog(self.log_path)
        content_id = compute_content_identity({
            "id": "ev_sec_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "confidence_score": 0.5,
        })
        system_event = VerificationDecision(
            event_id="evt-sys-001",
            evidence_id="ev_sec_001",
            decision="verified",
            actor="system-001",
            actor_role="system",
            method="system_proposal",
            timestamp="2026-09-01T10:00:00Z",
            content_identity=content_id,
            evidence_refs=["https://example.gov.cn/policy/001"],
        )
        with self.assertRaises(ValueError):
            log.append(system_event)

    def test_sb_003_mock_denied(self):
        """MOCK evidence can never become VERIFIED."""
        self.service.create_evidence({
            "id": "ev_mock_001", "type": "policy", "source": "mock",
            "source_reference": "mock://test",
            "verification_status": "MOCK", "confidence_score": 0.0,
        })
        result = self.service.record_human_verification(
            evidence_id="ev_mock_001",
            verifier_id="hr-001",
            verifier_role="human_verifier",
            verification_evidence=["mock://test"])
        self.assertFalse(result["success"])

    def test_sb_004_content_identity_mismatch_denied(self):
        """Content change after verification → mismatch → denied."""
        # First verify
        result = self.service.record_human_verification(
            evidence_id="ev_sec_001",
            verifier_id="hr-001",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertTrue(result["success"])
        # Change content
        self.service.create_evidence({
            "id": "ev_sec_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "verification_status": "UNVERIFIED", "confidence_score": 0.9,
        })
        # Check effective state — should be invalid due to content change
        gate = HumanVerificationGate(
            VerificationEventLog(self.log_path),
            self.service.authority_registry,
        )
        new_content_id = compute_content_identity({
            "id": "ev_sec_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "confidence_score": 0.9,
        })
        state = gate.get_effective_verified_state(
            "ev_sec_001", new_content_id, evidence_is_mock=False)
        self.assertFalse(state["is_valid"])

    def test_sb_005_missing_evidence_ref_denied(self):
        """Verification event with empty evidence_refs → denied by gate."""
        log = VerificationEventLog(self.log_path)
        content_id = compute_content_identity({
            "id": "ev_sec_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "confidence_score": 0.5,
        })
        event = VerificationDecision(
            event_id="evt-no-refs-001",
            evidence_id="ev_sec_001",
            decision="verified",
            actor="hr-001",
            actor_role="human_verifier",
            method="manual_check",
            timestamp="2026-09-01T10:00:00Z",
            content_identity=content_id,
            evidence_refs=[],
        )
        log.append(event)
        gate = HumanVerificationGate(log, self.service.authority_registry)
        result = gate.can_grant_verified(
            "ev_sec_001", content_id, evidence_is_mock=False)
        self.assertFalse(result["granted"])


class TestServiceIntegrationWithConfig(unittest.TestCase):
    """TrustEvidenceService integration with config_path parameter."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.config_path = os.path.join(self.tmpdir, "authorities.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_si_001_config_path_loads_registry(self):
        _write_config(self.config_path, [
            _valid_authority("hr-001", "human_verifier"),
        ])
        svc = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry_config_path=self.config_path,
        )
        self.assertIsNotNone(svc.authority_registry)
        self.assertTrue(svc.authority_registry.is_authorized("hr-001", "human_verifier"))

    def test_si_002_explicit_registry_takes_precedence(self):
        _write_config(self.config_path, [
            _valid_authority("from-config", "human_verifier"),
        ])
        explicit_reg = HumanVerificationAuthorityRegistry([
            HumanVerificationAuthority("from-explicit", "human_verifier"),
        ])
        svc = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry=explicit_reg,
            authority_registry_config_path=self.config_path,
        )
        # Explicit registry should be used, not config
        self.assertTrue(svc.authority_registry.is_registered("from-explicit"))
        self.assertFalse(svc.authority_registry.is_registered("from-config"))

    def test_si_003_config_load_failure_propagates(self):
        """Malformed config → construction fails, no silent fallback."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("{invalid json")
        with self.assertRaises(ValueError):
            TrustEvidenceService(
                event_log_path=self.log_path,
                authority_registry_config_path=self.config_path,
            )

    def test_si_004_missing_config_file_propagates(self):
        with self.assertRaises(FileNotFoundError):
            TrustEvidenceService(
                event_log_path=self.log_path,
                authority_registry_config_path=os.path.join(self.tmpdir, "no.json"),
            )

    def test_si_005_no_config_no_registry_legacy_compat(self):
        """Service without registry or config still works for non-VERIFIED ops."""
        svc = TrustEvidenceService(event_log_path=self.log_path)
        result = svc.create_evidence({
            "id": "ev_legacy_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        self.assertTrue(result["success"])
        self.assertIsNone(svc.authority_registry)

    def test_si_006_empty_config_path_ignored(self):
        """Empty string config_path is treated as None (no config)."""
        svc = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry_config_path="",
        )
        self.assertIsNone(svc.authority_registry)


class TestConfigBackwardCompat(unittest.TestCase):
    """Backward compatibility: legacy events, revocation, re-verification."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmpdir, "events.jsonl")
        self.config_path = os.path.join(self.tmpdir, "authorities.json")
        _write_config(self.config_path, [
            _valid_authority("hr-001", "human_verifier"),
        ])

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_bc_001_legacy_events_remain_readable(self):
        """Events written before P1-4.6 are still readable."""
        log = VerificationEventLog(self.log_path)
        event = VerificationDecision(
            event_id="evt-legacy-001",
            evidence_id="ev_legacy",
            decision="candidate",
            actor="agent-001",
            actor_role="agent",
            method="agent_proposal",
            timestamp="2026-08-31T10:00:00Z",
            content_identity=None,
            evidence_refs=["ref"],
        )
        log.append(event)
        # Re-open the log
        log2 = VerificationEventLog(self.log_path)
        events, malformed = log2.replay()
        self.assertEqual(len(events), 1)
        self.assertEqual(len(malformed), 0)
        self.assertEqual(events[0].event_id, "evt-legacy-001")

    def test_bc_002_revocation_still_works(self):
        svc = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry_config_path=self.config_path,
        )
        svc.create_evidence({
            "id": "ev_rev_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        # Verify
        result = svc.record_human_verification(
            evidence_id="ev_rev_001",
            verifier_id="hr-001",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertTrue(result["success"])
        # Revoke
        revoke_result = svc.revoke_verified("ev_rev_001", reason="source changed")
        self.assertTrue(revoke_result["success"])

    def test_bc_003_re_verification_still_works(self):
        svc = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry_config_path=self.config_path,
        )
        svc.create_evidence({
            "id": "ev_rever_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        # Verify
        r1 = svc.record_human_verification(
            evidence_id="ev_rever_001",
            verifier_id="hr-001",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertTrue(r1["success"])
        # Revoke
        svc.revoke_verified("ev_rever_001", reason="content change")
        # Re-verify
        r2 = svc.record_human_verification(
            evidence_id="ev_rever_001",
            verifier_id="hr-001",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"])
        self.assertTrue(r2["success"])
        self.assertEqual(r2["verification_status"], "VERIFIED")

    def test_bc_004_eventlog_persistence_across_instances(self):
        """EventLog survives service restart (different instance, same path)."""
        svc1 = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry_config_path=self.config_path,
        )
        svc1.create_evidence({
            "id": "ev_persist_001", "type": "policy", "source": "government",
            "source_reference": "https://example.gov.cn/policy/001",
            "verification_status": "UNVERIFIED", "confidence_score": 0.5,
        })
        svc1.record_human_verification(
            evidence_id="ev_persist_001",
            verifier_id="hr-001",
            verifier_role="human_verifier",
            verification_evidence=["https://example.gov.cn/policy/001"])
        # New instance from same paths
        svc2 = TrustEvidenceService(
            event_log_path=self.log_path,
            authority_registry_config_path=self.config_path,
        )
        state = svc2.check_verified_validity("ev_persist_001")
        self.assertIsNotNone(state)


class TestNoAuthenticationClaim(unittest.TestCase):
    """Verify no authentication claims are made — registry = authorization, not identity."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "authorities.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_na_001_registry_docstring_not_authentication(self):
        _write_config(self.config_path, [_valid_authority("v1", "human_verifier")])
        reg = HumanVerificationAuthorityRegistry.from_config(self.config_path)
        doc = (HumanVerificationAuthorityRegistry.__doc__ or "") + \
              (HumanVerificationAuthorityRegistry.from_config.__doc__ or "")
        doc_lower = doc.lower()
        # Must NOT claim to implement authentication
        self.assertNotIn("implements oauth", doc_lower)
        self.assertNotIn("provides authentication", doc_lower)
        self.assertNotIn("password verification", doc_lower)
        # Must explicitly state NOT real-world identity authentication
        self.assertIn("not real-world identity", doc_lower)

    def test_na_002_metadata_not_identity_claim(self):
        """metadata is optional display info, NOT an identity claim."""
        _write_config(self.config_path, [
            _valid_authority("v1", "human_verifier",
                            metadata={"display_name": "Alice"}),
        ])
        reg = HumanVerificationAuthorityRegistry.from_config(self.config_path)
        auth = reg.lookup("v1")
        self.assertEqual(auth.metadata, {"display_name": "Alice"})
        # metadata does NOT affect authorization
        self.assertTrue(reg.is_authorized("v1", "human_verifier"))

    def test_na_003_no_password_or_token_field(self):
        """Config entries must not carry password/token/secret fields."""
        _write_config(self.config_path, [
            {"verifier_id": "v1", "role": "human_verifier", "active": True,
             "password": "should-not-be-here"},
        ])
        # from_dict only reads verifier_id/role/active/metadata — password is ignored
        reg = HumanVerificationAuthorityRegistry.from_config(self.config_path)
        auth = reg.lookup("v1")
        # password must NOT be stored on the authority object
        self.assertFalse(hasattr(auth, "password"))
        self.assertNotIn("password", auth.metadata)


if __name__ == "__main__":
    unittest.main()
