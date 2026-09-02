"""
P2-0 Experimental Record Format — Validation Tests.

Tests ONLY record-format validation. Does NOT test experimental outcomes.
Does NOT create any "experimentally validated" conclusion.
Does NOT modify the 637 baseline tests.

Covers:
  - Required fields per record type
  - contact_info optional (Hook can exist without contact)
  - POLICY_HOOK vs PROJECT_HOOK distinction
  - Hook has NO status/claim_status/claim_token (Hook ≠ Claim)
  - REAL + UNVERIFIED valid (is_mock=false + verification_status="UNVERIFIED")
  - MOCK + MOCK valid (is_mock=true + verification_status="MOCK")
  - MOCK + UNVERIFIED rejected
  - Any verification_status="VERIFIED" rejected (REAL ≠ VERIFIED)
  - Any verification_status="REJECTED" rejected
  - Participant only 3 fields, no metadata
  - 9 event types accepted; illegal types rejected
  - response_level L0-L4 valid
  - response_level non-null ONLY on PARTICIPANT_RESPONDED
  - event_id deterministic (same input → same hash)
  - null allowed where data unavailable
  - Hook creation does NOT auto-generate events (store behavior)
  - PARTICIPANT_CONTACTED does NOT auto-generate INTERESTED
  - JSONL store: append, read, duplicate event_id rejection
  - Experimental record does NOT grant Trust Layer VERIFIED
"""

import os
import sys
import tempfile
import shutil

import pytest

# Ensure the p2_0_experimental package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from p2_0_experimental.record_validator import (
    validate,
    validate_policy,
    validate_project_intent,
    validate_hook,
    validate_participant,
    validate_event,
    compute_event_id,
    EVENT_TYPES,
    HOOK_TYPES,
    PARTICIPANT_TYPES,
    RESPONSE_LEVELS,
    ALLOWED_VERIFICATION_STATUSES,
    FORBIDDEN_HOOK_FIELDS,
    FORBIDDEN_PARTICIPANT_FIELDS,
    FORBIDDEN_EVENT_FIELDS,
)
from p2_0_experimental.jsonl_store import ExperimentalJSONLStore


# ─── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def tmp_records_dir():
    """Temporary records directory for store tests."""
    d = tempfile.mkdtemp(prefix="p2_0_exp_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _valid_policy_real():
    """A valid REAL policy (is_mock=false, verification_status='UNVERIFIED')."""
    return {
        "record_type": "POLICY",
        "policy_id": "pol_001",
        "title": "Shanghai AI Industry Support Policy 2024",
        "source_url": "https://gov.shanghai.gov.cn/example-policy",
        "is_mock": False,
        "verification_status": "UNVERIFIED",
        "created_at": "2026-09-02T10:00:00Z",
        "source": "manual_ingest_howard",
    }


def _valid_policy_mock():
    """A valid MOCK policy (is_mock=true, verification_status='MOCK')."""
    return {
        "record_type": "POLICY",
        "policy_id": "pol_mock_001",
        "title": "MOCK Demo Policy",
        "source_url": "mock://test-policy-1",
        "is_mock": True,
        "verification_status": "MOCK",
        "created_at": "2026-09-02T10:00:00Z",
        "source": "mock_fixture",
    }


def _valid_project_intent():
    """A valid ProjectIntent (contact_info=None — Hook can exist without contact)."""
    return {
        "record_type": "PROJECT_INTENT",
        "project_intent_id": "pi_001",
        "policy_id": "pol_001",
        "need_description": "We need subsidies for AI chip R&D in Shanghai.",
        "project_type": "AI_CHIP",
        "industry": "semiconductor",
        "region": "shanghai",
        "actor_id": "anonymous_project_001",
        "created_at": "2026-09-02T11:00:00Z",
        "source": "portal_form",
        "contact_info": None,
    }


def _valid_hook(hook_type="PROJECT_HOOK", object_id="pi_001"):
    """A valid Hook. NO status, NO claim_status, NO claim_token."""
    return {
        "record_type": "HOOK",
        "hook_id": "hook_001",
        "hook_type": hook_type,
        "object_id": object_id,
        "created_at": "2026-09-02T11:01:00Z",
        "source": "auto_from_intent",
    }


def _valid_participant():
    """A valid Participant. Only 3 data fields, no metadata."""
    return {
        "record_type": "PARTICIPANT",
        "participant_id": "part_001",
        "participant_type": "POLICY_AUTHORITY",
        "source": "manual_outreach_list",
    }


def _valid_event(event_type="POLICY_VIEWED", **overrides):
    """A valid Event."""
    event = {
        "record_type": "EVENT",
        "event_id": "",  # will be set
        "timestamp": "2026-09-02T12:00:00Z",
        "event_type": event_type,
        "actor_id": "anonymous_project_001",
        "actor_type": "PROJECT",
        "object_type": "POLICY",
        "object_id": "pol_001",
        "source": "portal",
        "evidence_ref": None,
        "response_level": None,
        "note": None,
    }
    event.update(overrides)
    event["event_id"] = compute_event_id(event)
    return event


# ─── T1: Required fields per record type ────────────────────────────


class TestRequiredFields:
    def test_policy_missing_field_rejected(self):
        record = _valid_policy_real()
        del record["source_url"]
        ok, errors = validate_policy(record)
        assert not ok
        assert any("source_url" in e for e in errors)

    def test_project_intent_missing_field_rejected(self):
        record = _valid_project_intent()
        del record["need_description"]
        ok, errors = validate_project_intent(record)
        assert not ok
        assert any("need_description" in e for e in errors)

    def test_hook_missing_field_rejected(self):
        record = _valid_hook()
        del record["hook_type"]
        ok, errors = validate_hook(record)
        assert not ok
        assert any("hook_type" in e for e in errors)

    def test_participant_missing_field_rejected(self):
        record = _valid_participant()
        del record["participant_type"]
        ok, errors = validate_participant(record)
        assert not ok
        assert any("participant_type" in e for e in errors)

    def test_event_missing_field_rejected(self):
        record = _valid_event()
        del record["timestamp"]
        ok, errors = validate_event(record)
        assert not ok
        assert any("timestamp" in e for e in errors)

    def test_unknown_record_type_rejected(self):
        ok, errors = validate({"record_type": "UNKNOWN_TYPE"})
        assert not ok
        assert any("unknown record_type" in e for e in errors)


# ─── T2: contact_info optional ──────────────────────────────────────


class TestContactInfoOptional:
    def test_project_intent_without_contact_info_valid(self):
        record = _valid_project_intent()
        record["contact_info"] = None
        ok, errors = validate_project_intent(record)
        assert ok, f"Should be valid without contact_info: {errors}"

    def test_project_intent_with_contact_info_valid(self):
        record = _valid_project_intent()
        record["contact_info"] = "founder@example.com"
        ok, errors = validate_project_intent(record)
        assert ok, f"Should be valid with contact_info: {errors}"

    def test_project_intent_contact_info_omitted_valid(self):
        """contact_info can be entirely absent — Hook can exist without it."""
        record = _valid_project_intent()
        del record["contact_info"]
        ok, errors = validate_project_intent(record)
        assert ok, f"Should be valid with contact_info omitted: {errors}"


# ─── T3: POLICY_HOOK vs PROJECT_HOOK ────────────────────────────────


class TestHookTypes:
    def test_policy_hook_valid(self):
        ok, errors = validate_hook(_valid_hook("POLICY_HOOK", "pol_001"))
        assert ok, errors

    def test_project_hook_valid(self):
        ok, errors = validate_hook(_valid_hook("PROJECT_HOOK", "pi_001"))
        assert ok, errors

    def test_invalid_hook_type_rejected(self):
        record = _valid_hook("INVALID_HOOK", "pol_001")
        ok, errors = validate_hook(record)
        assert not ok
        assert any("hook_type" in e for e in errors)


# ─── T4: Hook has NO status/claim fields (Hook ≠ Claim) ─────────────


class TestHookNotClaim:
    @pytest.mark.parametrize("forbidden_field", sorted(FORBIDDEN_HOOK_FIELDS))
    def test_hook_rejects_forbidden_field(self, forbidden_field):
        record = _valid_hook()
        record[forbidden_field] = "should_be_rejected"
        ok, errors = validate_hook(record)
        assert not ok
        assert any(forbidden_field in e for e in errors), \
            f"Should reject forbidden field '{forbidden_field}' on HOOK"

    def test_hook_has_no_status_machine(self):
        """Hook must NOT have a 'status' field — no state machine."""
        record = _valid_hook()
        record["status"] = "OPEN"
        ok, errors = validate_hook(record)
        assert not ok

    def test_hook_has_no_claim_status(self):
        """Hook ≠ Claim: no claim_status field."""
        record = _valid_hook()
        record["claim_status"] = "unclaimed"
        ok, errors = validate_hook(record)
        assert not ok

    def test_hook_has_no_claim_token(self):
        """Hook ≠ Claim: no claim_token field."""
        record = _valid_hook()
        record["claim_token"] = "abc123"
        ok, errors = validate_hook(record)
        assert not ok


# ─── T5/T6: REAL + UNVERIFIED valid; MOCK + MOCK valid ──────────────


class TestPolicyVerificationStatus:
    def test_real_unverified_valid(self):
        """is_mock=false + verification_status='UNVERIFIED' = REAL policy."""
        ok, errors = validate_policy(_valid_policy_real())
        assert ok, errors

    def test_mock_mock_valid(self):
        """is_mock=true + verification_status='MOCK' = MOCK policy."""
        ok, errors = validate_policy(_valid_policy_mock())
        assert ok, errors


# ─── T7: MOCK + UNVERIFIED rejected ─────────────────────────────────


class TestMockCannotMasqueradeAsReal:
    def test_mock_with_unverified_rejected(self):
        record = _valid_policy_mock()
        record["verification_status"] = "UNVERIFIED"
        ok, errors = validate_policy(record)
        assert not ok
        assert any("MOCK" in e for e in errors)

    def test_real_with_mock_rejected(self):
        record = _valid_policy_real()
        record["verification_status"] = "MOCK"
        ok, errors = validate_policy(record)
        assert not ok
        assert any("UNVERIFIED" in e for e in errors)


# ─── T8: Any verification_status="VERIFIED" rejected (REAL ≠ VERIFIED)


class TestVerifiedNeverAllowed:
    def test_verified_with_is_mock_false_rejected(self):
        """VERIFIED is NEVER allowed at the experimental layer."""
        record = _valid_policy_real()
        record["verification_status"] = "VERIFIED"
        ok, errors = validate_policy(record)
        assert not ok
        assert any("VERIFIED" in e for e in errors)

    def test_verified_with_is_mock_true_rejected(self):
        record = _valid_policy_mock()
        record["verification_status"] = "VERIFIED"
        ok, errors = validate_policy(record)
        assert not ok

    def test_rejected_status_never_allowed(self):
        """REJECTED is also never allowed at the experimental layer."""
        record = _valid_policy_real()
        record["verification_status"] = "REJECTED"
        ok, errors = validate_policy(record)
        assert not ok

    def test_is_mock_must_be_strict_bool(self):
        """is_mock must be a real bool — no string 'true' or int 1."""
        record = _valid_policy_real()
        record["is_mock"] = "false"  # string, not bool
        ok, errors = validate_policy(record)
        assert not ok
        assert any("is_mock" in e for e in errors)

    def test_is_mock_must_not_be_int(self):
        record = _valid_policy_real()
        record["is_mock"] = 0  # int, not bool
        ok, errors = validate_policy(record)
        assert not ok


# ─── T9: Participant only 3 fields, no metadata ─────────────────────


class TestParticipantMinimal:
    @pytest.mark.parametrize("forbidden_field", sorted(FORBIDDEN_PARTICIPANT_FIELDS))
    def test_participant_rejects_forbidden_field(self, forbidden_field):
        record = _valid_participant()
        record[forbidden_field] = "should_be_rejected"
        ok, errors = validate_participant(record)
        assert not ok
        assert any(forbidden_field in e for e in errors), \
            f"Should reject forbidden field '{forbidden_field}' on PARTICIPANT"

    def test_participant_no_extra_fields(self):
        """Only record_type, participant_id, participant_type, source allowed."""
        record = _valid_participant()
        record["extra_field"] = "no"
        ok, errors = validate_participant(record)
        assert not ok
        assert any("unexpected fields" in e for e in errors)


# ─── T10: 9 event types accepted; illegal types rejected ───────────


class TestEventTypes:
    @pytest.mark.parametrize("et", sorted(EVENT_TYPES))
    def test_all_9_event_types_accepted(self, et):
        event = _valid_event(event_type=et)
        ok, errors = validate_event(event)
        assert ok, f"Event type '{et}' should be valid: {errors}"

    def test_hook_viewed_rejected(self):
        """HOOK_VIEWED is NOT in the approved taxonomy."""
        event = _valid_event(event_type="HOOK_VIEWED")
        ok, errors = validate_event(event)
        assert not ok
        assert any("event_type" in e for e in errors)

    def test_hook_claimed_rejected(self):
        """HOOK_CLAIMED is NOT in the approved taxonomy."""
        event = _valid_event(event_type="HOOK_CLAIMED")
        ok, errors = validate_event(event)
        assert not ok

    def test_hook_verified_rejected(self):
        """HOOK_VERIFIED is NOT in the approved taxonomy."""
        event = _valid_event(event_type="HOOK_VERIFIED")
        ok, errors = validate_event(event)
        assert not ok

    def test_match_created_rejected(self):
        """MATCH_CREATED is NOT in the approved taxonomy (no matching engine)."""
        event = _valid_event(event_type="MATCH_CREATED")
        ok, errors = validate_event(event)
        assert not ok

    def test_investment_created_rejected(self):
        """INVESTMENT_CREATED is NOT in the approved taxonomy."""
        event = _valid_event(event_type="INVESTMENT_CREATED")
        ok, errors = validate_event(event)
        assert not ok


# ─── T11/T12: response_level L0-L4; non-null only on PARTICIPANT_RESPONDED ──


class TestResponseLevel:
    @pytest.mark.parametrize("rl", sorted(RESPONSE_LEVELS))
    def test_response_level_valid_on_participant_responded(self, rl):
        event = _valid_event(event_type="PARTICIPANT_RESPONDED", response_level=rl)
        ok, errors = validate_event(event)
        assert ok, f"response_level='{rl}' should be valid on PARTICIPANT_RESPONDED: {errors}"

    def test_response_level_null_on_participant_responded_valid(self):
        event = _valid_event(event_type="PARTICIPANT_RESPONDED", response_level=None)
        ok, errors = validate_event(event)
        assert ok

    def test_response_level_non_null_on_other_event_rejected(self):
        """response_level must be null when event_type != PARTICIPANT_RESPONDED."""
        event = _valid_event(event_type="HOOK_INTERESTED", response_level="L1")
        ok, errors = validate_event(event)
        assert not ok
        assert any("response_level" in e for e in errors)

    def test_invalid_response_level_rejected(self):
        event = _valid_event(event_type="PARTICIPANT_RESPONDED", response_level="L5")
        ok, errors = validate_event(event)
        assert not ok
        assert any("response_level" in e for e in errors)


# ─── T13: event_id deterministic ────────────────────────────────────


class TestEventIdDeterminism:
    def test_same_input_same_hash(self):
        event1 = _valid_event(event_type="POLICY_VIEWED")
        event2 = _valid_event(event_type="POLICY_VIEWED")
        assert event1["event_id"] == event2["event_id"]

    def test_different_input_different_hash(self):
        event1 = _valid_event(event_type="POLICY_VIEWED")
        event2 = _valid_event(event_type="POLICY_SEARCHED")
        assert event1["event_id"] != event2["event_id"]

    def test_event_id_excluded_from_hash(self):
        """event_id itself should not affect its own computation."""
        event = {
            "record_type": "EVENT",
            "timestamp": "2026-09-02T12:00:00Z",
            "event_type": "POLICY_VIEWED",
            "source": "portal",
        }
        id1 = compute_event_id(event)
        # Adding an event_id field should not change the computed id
        event["event_id"] = id1
        id2 = compute_event_id(event)
        assert id1 == id2


# ─── T14: null allowed where data unavailable ───────────────────────


class TestNullAllowed:
    def test_event_with_null_actor_valid(self):
        event = _valid_event()
        event["actor_id"] = None
        event["actor_type"] = None
        event["object_type"] = None
        event["object_id"] = None
        event["event_id"] = compute_event_id(event)
        ok, errors = validate_event(event)
        assert ok, f"Null fields should be allowed: {errors}"

    def test_event_with_null_evidence_ref_valid(self):
        event = _valid_event()
        event["evidence_ref"] = None
        event["event_id"] = compute_event_id(event)
        ok, errors = validate_event(event)
        assert ok

    def test_project_intent_with_null_optional_fields_valid(self):
        record = _valid_project_intent()
        record["project_type"] = None
        record["industry"] = None
        record["region"] = None
        record["contact_info"] = None
        ok, errors = validate_project_intent(record)
        assert ok


# ─── T15/T16: No automatic event generation (store behavior) ────────


class TestNoAutoEventGeneration:
    def test_hook_creation_does_not_auto_create_event(self, tmp_records_dir):
        """Creating a Hook does NOT auto-generate HOOK_INTERESTED."""
        store = ExperimentalJSONLStore(tmp_records_dir)

        # Append a Hook
        store.append(_valid_hook())

        # Check events log — should be empty
        events = store.read_all("EVENT")
        assert len(events) == 0, "Hook creation must NOT auto-generate any event"

    def test_participant_contacted_does_not_auto_create_interested(self, tmp_records_dir):
        """PARTICIPANT_CONTACTED does NOT auto-generate HOOK_INTERESTED."""
        store = ExperimentalJSONLStore(tmp_records_dir)

        # Append a PARTICIPANT_CONTACTED event
        event = _valid_event(
            event_type="PARTICIPANT_CONTACTED",
            actor_type="EXPERIMENTER",
            object_type="HOOK",
            object_id="hook_001",
        )
        store.append(event)

        # Check all events — should be exactly 1 (the one we appended)
        events = store.read_all("EVENT")
        assert len(events) == 1
        assert events[0]["event_type"] == "PARTICIPANT_CONTACTED"
        # No HOOK_INTERESTED was auto-created
        assert not any(e["event_type"] == "HOOK_INTERESTED" for e in events)


# ─── T17: JSONL store behavior ──────────────────────────────────────


class TestJSONLStore:
    def test_append_and_read_policy(self, tmp_records_dir):
        store = ExperimentalJSONLStore(tmp_records_dir)
        policy = _valid_policy_real()
        rid = store.append(policy)
        assert rid == "pol_001"

        records = store.read_all("POLICY")
        assert len(records) == 1
        assert records[0]["policy_id"] == "pol_001"

    def test_append_and_read_hook(self, tmp_records_dir):
        store = ExperimentalJSONLStore(tmp_records_dir)
        store.append(_valid_hook())

        records = store.read_all("HOOK")
        assert len(records) == 1
        assert records[0]["hook_type"] == "PROJECT_HOOK"

    def test_append_invalid_record_raises(self, tmp_records_dir):
        store = ExperimentalJSONLStore(tmp_records_dir)
        bad_policy = _valid_policy_real()
        bad_policy["verification_status"] = "VERIFIED"
        with pytest.raises(ValueError, match="Invalid record"):
            store.append(bad_policy)

    def test_duplicate_event_id_rejected(self, tmp_records_dir):
        store = ExperimentalJSONLStore(tmp_records_dir)
        event = _valid_event(event_type="POLICY_VIEWED")
        store.append(event)

        # Same event_id → rejected
        with pytest.raises(ValueError, match="Duplicate event_id"):
            store.append(event)

    def test_different_events_accepted(self, tmp_records_dir):
        store = ExperimentalJSONLStore(tmp_records_dir)
        store.append(_valid_event(event_type="POLICY_VIEWED"))
        store.append(_valid_event(event_type="POLICY_SEARCHED"))

        events = store.read_all("EVENT")
        assert len(events) == 2

    def test_read_empty_returns_empty_list(self, tmp_records_dir):
        store = ExperimentalJSONLStore(tmp_records_dir)
        assert store.read_all("POLICY") == []

    def test_append_event_convenience_computes_id(self, tmp_records_dir):
        """append_event auto-computes event_id if missing (deterministic hash)."""
        store = ExperimentalJSONLStore(tmp_records_dir)
        event = {
            "record_type": "EVENT",
            "timestamp": "2026-09-02T12:00:00Z",
            "event_type": "POLICY_VIEWED",
            "source": "portal",
        }
        rid = store.append_event(event)
        assert len(rid) == 64  # sha256 hex

        events = store.read_all("EVENT")
        assert len(events) == 1
        assert events[0]["event_id"] == rid

    def test_records_isolated_from_trust_layer(self, tmp_records_dir):
        """Experimental store files must NOT exist in src/trust/ paths."""
        store = ExperimentalJSONLStore(tmp_records_dir)
        store.append(_valid_policy_real())

        # The records dir should be in tmp, not in src/trust/
        assert "src" not in tmp_records_dir or "trust" not in tmp_records_dir
        # The file should be in the tmp dir
        policy_file = os.path.join(tmp_records_dir, "policies.jsonl")
        assert os.path.exists(policy_file)


# ─── T-extra: Event forbidden fields (metadata, claim, match, investment) ──


class TestEventForbiddenFields:
    @pytest.mark.parametrize("forbidden_field", sorted(FORBIDDEN_EVENT_FIELDS))
    def test_event_rejects_forbidden_field(self, forbidden_field):
        event = _valid_event()
        event[forbidden_field] = "should_be_rejected"
        # Need to recompute event_id since we added a field
        event["event_id"] = compute_event_id(event)
        ok, errors = validate_event(event)
        assert not ok
        assert any(forbidden_field in e for e in errors), \
            f"Should reject forbidden field '{forbidden_field}' on EVENT"

    def test_event_no_metadata_field(self):
        """Event must NOT have 'metadata' — use explicit named fields."""
        event = _valid_event()
        event["metadata"] = {"some": "stuff"}
        event["event_id"] = compute_event_id(event)
        ok, errors = validate_event(event)
        assert not ok


# ─── T-extra: Policy forbidden metadata field ───────────────────────


class TestPolicyNoMetadata:
    def test_policy_rejects_metadata(self):
        record = _valid_policy_real()
        record["metadata"] = {"extra": "data"}
        ok, errors = validate_policy(record)
        assert not ok
        assert any("metadata" in e for e in errors)


# ─── T-extra: Dispatch validate() works for all types ───────────────


class TestValidateDispatch:
    def test_validate_policy(self):
        ok, _ = validate(_valid_policy_real())
        assert ok

    def test_validate_project_intent(self):
        ok, _ = validate(_valid_project_intent())
        assert ok

    def test_validate_hook(self):
        ok, _ = validate(_valid_hook())
        assert ok

    def test_validate_participant(self):
        ok, _ = validate(_valid_participant())
        assert ok

    def test_validate_event(self):
        ok, _ = validate(_valid_event())
        assert ok

    def test_validate_non_dict_rejected(self):
        ok, errors = validate("not a dict")  # type: ignore
        assert not ok

    def test_validate_missing_record_type_rejected(self):
        ok, errors = validate({"policy_id": "x"})
        assert not ok


# ─── FIX 1: event_id canonical identity consistency ────────────────


class TestEventIdCanonicalConsistency:
    """FIX 1: event_id must equal compute_event_id(record)."""

    def test_correct_computed_event_id_accepted(self):
        """An event whose event_id == compute_event_id() is accepted."""
        event = _valid_event(event_type="POLICY_VIEWED")
        ok, errors = validate_event(event)
        assert ok, f"Correctly-computed event_id should be accepted: {errors}"

    def test_arbitrary_wrong_event_id_rejected(self):
        """An event with an arbitrary (non-canonical) event_id is rejected."""
        event = _valid_event(event_type="POLICY_VIEWED")
        event["event_id"] = "arbitrary_wrong_id_that_is_not_the_canonical_hash"
        ok, errors = validate_event(event)
        assert not ok
        assert any("event_id does not match canonical identity" in e for e in errors)

    def test_modifying_a_hashed_field_invalidates_event_id(self):
        """Changing any field that enters the hash invalidates the old event_id."""
        event = _valid_event(event_type="POLICY_VIEWED")
        original_id = event["event_id"]

        # Modify a field that enters the canonical payload
        event["timestamp"] = "2026-09-03T10:00:00Z"
        # event_id is still the old one — should now be invalid
        ok, errors = validate_event(event)
        assert not ok
        assert any("event_id does not match canonical identity" in e for e in errors)

        # Recompute → should be valid again
        event["event_id"] = compute_event_id(event)
        ok, errors = validate_event(event)
        assert ok, f"Recomputed event_id should be accepted: {errors}"
        assert event["event_id"] != original_id

    def test_append_event_auto_generated_id_passes_validator(self, tmp_records_dir):
        """append_event() auto-computes event_id; the result passes validator."""
        store = ExperimentalJSONLStore(tmp_records_dir)
        event = {
            "record_type": "EVENT",
            "timestamp": "2026-09-02T12:00:00Z",
            "event_type": "POLICY_VIEWED",
            "source": "portal",
        }
        rid = store.append_event(event)
        # The stored event should be valid if re-validated
        stored = store.read_by_id("EVENT", rid)
        assert stored is not None
        ok, errors = validate_event(stored)
        assert ok, f"Auto-generated event_id should pass validator: {errors}"

    def test_provided_event_id_routed_through_validator(self, tmp_records_dir):
        """A caller-provided event_id that doesn't match canonical is rejected
        by append() → validate(), not silently trusted."""
        store = ExperimentalJSONLStore(tmp_records_dir)
        event = _valid_event(event_type="POLICY_VIEWED")
        event["event_id"] = "wrong_id_on_purpose"
        with pytest.raises(ValueError, match="Invalid record"):
            store.append(event)


# ─── FIX 2: malformed JSON fail-closed in _id_exists ───────────────


class TestMalformedJsonFailClosed:
    """FIX 2: _id_exists() must raise on malformed JSON, not silently skip."""

    def test_malformed_json_in_events_causes_append_to_fail(self, tmp_records_dir):
        """If events.jsonl contains a malformed line, appending a new event
        must fail (via _id_exists raising), not silently skip the malformed line."""
        store = ExperimentalJSONLStore(tmp_records_dir)

        # Manually write a malformed line into events.jsonl
        os.makedirs(tmp_records_dir, exist_ok=True)
        events_file = os.path.join(tmp_records_dir, "events.jsonl")
        with open(events_file, "w", encoding="utf-8") as f:
            f.write("{this is not valid json}\n")

        # Attempt to append a valid event — should fail because _id_exists
        # encounters the malformed line and raises
        event = _valid_event(event_type="POLICY_VIEWED")
        with pytest.raises(ValueError, match="Malformed JSON"):
            store.append(event)

    def test_malformed_json_not_silently_skipped(self, tmp_records_dir):
        """The malformed line must NOT be silently skipped — the error must
        propagate so the experimenter knows the log is corrupt."""
        store = ExperimentalJSONLStore(tmp_records_dir)
        os.makedirs(tmp_records_dir, exist_ok=True)
        events_file = os.path.join(tmp_records_dir, "events.jsonl")
        with open(events_file, "w", encoding="utf-8") as f:
            f.write('{"event_id": "legit_id", "record_type": "EVENT"}\n')
            f.write("{corrupt line}\n")

        # Append should fail at the corrupt line, not skip it
        event = _valid_event(event_type="POLICY_VIEWED")
        with pytest.raises(ValueError, match="Malformed JSON"):
            store.append(event)


# ─── FIX 3: Canonical optional-field normalization ─────────────────


class TestCanonicalOptionalFieldNormalization:
    """FIX 3: omitted optional field == explicit null in event_id computation.

    Constructs events directly (not via _valid_event helper) to test both the
    omitted path and the explicit-null path, confirming they produce the same
    event_id for the same event fact.
    """

    def _base_required_fields(self, **overrides):
        """Build an event with ONLY required fields (no optional fields)."""
        event = {
            "record_type": "EVENT",
            "timestamp": "2026-09-02T12:00:00Z",
            "event_type": "POLICY_VIEWED",
            "source": "portal",
        }
        event.update(overrides)
        return event

    def test_omitted_optional_equals_explicit_null(self):
        """A single omitted optional field == that field set to None."""
        omitted = self._base_required_fields()
        explicit_null = self._base_required_fields()
        explicit_null["actor_id"] = None

        id_omitted = compute_event_id(omitted)
        id_explicit_null = compute_event_id(explicit_null)

        assert id_omitted == id_explicit_null, (
            "Omitted actor_id and explicit-null actor_id must produce the same event_id"
        )

    def test_all_optional_omitted_equals_all_optional_null(self):
        """All 7 optional fields omitted == all 7 optional fields explicit null."""
        omitted = self._base_required_fields()

        explicit_null = self._base_required_fields()
        for field in ["actor_id", "actor_type", "object_type", "object_id",
                       "evidence_ref", "response_level", "note"]:
            explicit_null[field] = None

        assert compute_event_id(omitted) == compute_event_id(explicit_null)

    def test_mixed_omitted_and_null_combinations_equivalent(self):
        """Any combination of omitted/null across optional fields is equivalent."""
        base = self._base_required_fields()

        # Combination 1: some omitted, some null
        combo1 = self._base_required_fields()
        combo1["actor_id"] = None
        combo1["object_id"] = None
        # actor_type, object_type, evidence_ref, response_level, note omitted

        # Combination 2: the reverse — different fields null vs omitted
        combo2 = self._base_required_fields()
        combo2["actor_type"] = None
        combo2["evidence_ref"] = None
        combo2["note"] = None
        # actor_id, object_id, object_type, response_level omitted

        # Both should equal the all-omitted base (since all nulls are dropped)
        assert compute_event_id(combo1) == compute_event_id(base)
        assert compute_event_id(combo2) == compute_event_id(base)
        assert compute_event_id(combo1) == compute_event_id(combo2)

    def test_non_null_optional_value_changes_event_id(self):
        """A non-null optional value must change the event_id (not be dropped)."""
        without_actor = self._base_required_fields()
        with_actor = self._base_required_fields()
        with_actor["actor_id"] = "anonymous_project_001"

        assert compute_event_id(without_actor) != compute_event_id(with_actor)

    def test_different_non_null_values_produce_different_ids(self):
        """Two different non-null values for the same optional field → different IDs."""
        event_a = self._base_required_fields()
        event_a["actor_id"] = "anonymous_project_001"

        event_b = self._base_required_fields()
        event_b["actor_id"] = "anonymous_project_002"

        assert compute_event_id(event_a) != compute_event_id(event_b)

    def test_timestamp_change_changes_event_id(self):
        """timestamp enters the hash — changing it changes event_id."""
        event_a = self._base_required_fields(timestamp="2026-09-02T12:00:00Z")
        event_b = self._base_required_fields(timestamp="2026-09-02T13:00:00Z")
        assert compute_event_id(event_a) != compute_event_id(event_b)

    def test_event_type_change_changes_event_id(self):
        event_a = self._base_required_fields(event_type="POLICY_VIEWED")
        event_b = self._base_required_fields(event_type="POLICY_SEARCHED")
        assert compute_event_id(event_a) != compute_event_id(event_b)

    def test_object_id_change_changes_event_id(self):
        """object_id (non-null) enters the hash — changing it changes event_id."""
        event_a = self._base_required_fields()
        event_a["object_id"] = "pol_001"

        event_b = self._base_required_fields()
        event_b["object_id"] = "pol_002"

        assert compute_event_id(event_a) != compute_event_id(event_b)

    def test_actor_id_change_changes_event_id(self):
        """actor_id (non-null) enters the hash — changing it changes event_id."""
        event_a = self._base_required_fields()
        event_a["actor_id"] = "actor_001"

        event_b = self._base_required_fields()
        event_b["actor_id"] = "actor_002"

        assert compute_event_id(event_a) != compute_event_id(event_b)

    def test_fix1_consistency_check_still_enforced(self):
        """FIX 1 still active: provided event_id must match compute_event_id()."""
        event = self._base_required_fields()
        correct_id = compute_event_id(event)
        event["event_id"] = correct_id

        ok, errors = validate_event(event)
        assert ok, f"Correct event_id should pass FIX 1 check: {errors}"

    def test_fix1_wrong_event_id_still_rejected(self):
        """FIX 1 still active: wrong event_id is rejected even after FIX 3."""
        event = self._base_required_fields()
        event["event_id"] = "definitely_wrong_id"

        ok, errors = validate_event(event)
        assert not ok
        assert any("event_id does not match canonical identity" in e for e in errors)

    def test_append_event_auto_id_passes_validator(self, tmp_records_dir):
        """append_event() auto-generates ID; result passes validator (FIX 1 + FIX 3)."""
        store = ExperimentalJSONLStore(tmp_records_dir)
        # Event with only required fields — no optional fields at all
        event = self._base_required_fields()
        rid = store.append_event(event)

        stored = store.read_by_id("EVENT", rid)
        assert stored is not None
        ok, errors = validate_event(stored)
        assert ok, f"Auto-generated event_id should pass validator: {errors}"

    def test_provided_wrong_event_id_rejected_via_append(self, tmp_records_dir):
        """append() with a wrong provided event_id is rejected (FIX 1 enforced)."""
        store = ExperimentalJSONLStore(tmp_records_dir)
        event = self._base_required_fields()
        event["event_id"] = "intentionally_wrong"
        with pytest.raises(ValueError, match="Invalid record"):
            store.append(event)

    def test_omitted_event_then_null_event_triggers_duplicate_rejection(
        self, tmp_records_dir
    ):
        """Append an omitted-path event, then a null-path event with same fact.

        After FIX 3, both normalize to the same event_id, so the second append
        must be rejected as a duplicate.
        """
        store = ExperimentalJSONLStore(tmp_records_dir)

        # Path A: omitted optional fields
        event_omitted = self._base_required_fields()
        store.append_event(event_omitted)

        # Path B: explicit null for all optional fields — same event fact
        event_null = self._base_required_fields()
        for field in ["actor_id", "actor_type", "object_type", "object_id",
                       "evidence_ref", "response_level", "note"]:
            event_null[field] = None

        # This must be rejected as duplicate (same canonical event_id after FIX 3)
        with pytest.raises(ValueError, match="Duplicate event_id"):
            store.append_event(event_null)
