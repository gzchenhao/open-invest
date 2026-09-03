"""P2-0B.6 — E3 manual outreach recording tests.

ENGINEERING TEST ONLY — NOT AUTHENTIC E2/E3 EVIDENCE.

These tests verify ONLY that the experimenter-side CLI can record E3 events
into the existing B.2 store. They do NOT create, assert, or imply any real
outreach, any real hook, or any experimentally validated outcome.
Authentic E3 observed behavior remains 0 (authentic Hook = 0).

Scope guards enforced here:
  - No Portal-side E3 write path is exercised or created.
  - Evidence Guard: factual E3 events require evidence_ref or note.
  - L0 is NEVER recorded as PARTICIPANT_RESPONDED.
  - No automatic event chains: contact does not create HOOK_INTERESTED;
    respond does not create any Claim artifacts.
  - Records isolation: all writes go to a tmp store; the production
    p2_0_experimental/records/ directory stays empty (only .gitignore).
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from p2_0_experimental.jsonl_store import ExperimentalJSONLStore
from p2_0_experimental.record_outreach import main
from p2_0_experimental.record_validator import compute_event_id, validate

PRODUCTION_RECORDS_DIR = (
    Path(__file__).resolve().parents[1] / "p2_0_experimental" / "records"
)


# ─── Helpers ─────────────────────────────────────────────────────────


def _make_store(tmp_path) -> ExperimentalJSONLStore:
    return ExperimentalJSONLStore(str(tmp_path / "records"))


def _seed_hook(store: ExperimentalJSONLStore, hook_id="hook_e3_001") -> None:
    store.append(
        {
            "record_type": "HOOK",
            "hook_id": hook_id,
            "hook_type": "POLICY_HOOK",
            "object_id": "policy_seed_001",
            "created_at": "2026-09-02T00:00:00+00:00",
            "source": "test_seed",
        }
    )


def _seed_participant(store: ExperimentalJSONLStore, participant_id="park_a_001") -> None:
    store.append(
        {
            "record_type": "PARTICIPANT",
            "participant_id": participant_id,
            "participant_type": "PARK",
            "source": "test_seed",
        }
    )


def _raw_lines(store: ExperimentalJSONLStore, filename):
    path = Path(store.records_dir) / filename
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _events(store: ExperimentalJSONLStore):
    return store.read_all("EVENT")


# ─── participant-add ─────────────────────────────────────────────────


class TestParticipantAdd:
    def test_participant_add_success(self, tmp_path):
        store = _make_store(tmp_path)
        rc = main(
            ["participant-add", "--participant-id", "park_a_001",
             "--participant-type", "PARK"],
            store=store,
        )
        assert rc == 0
        records = store.read_all("PARTICIPANT")
        assert len(records) == 1
        rec = records[0]
        # Exact 4-field schema: no PII / CRM fields possible.
        assert set(rec.keys()) == {
            "record_type", "participant_id", "participant_type", "source",
        }
        assert rec["participant_id"] == "park_a_001"
        assert rec["participant_type"] == "PARK"
        assert rec["source"] == "record_outreach_cli"
        assert validate(rec)[0] is True

    def test_participant_alias_is_not_verified_identity(self, tmp_path):
        store = _make_store(tmp_path)
        main(["participant-add", "--participant-id", "x1",
              "--participant-type", "CAPITAL"], store=store)
        rec = store.read_by_id("PARTICIPANT", "x1")
        # No identity fields exist at all — alias only.
        assert "name" not in rec and "email" not in rec and "phone" not in rec
        assert "company" not in rec and "verification_status" not in rec

    def test_participant_add_duplicate_refused(self, tmp_path):
        store = _make_store(tmp_path)
        main(["participant-add", "--participant-id", "park_a_001",
              "--participant-type", "PARK"], store=store)
        rc = main(["participant-add", "--participant-id", "park_a_001",
                   "--participant-type", "PARK"], store=store)
        assert rc == 1
        assert len(store.read_all("PARTICIPANT")) == 1

    def test_participant_add_illegal_type_refused(self, tmp_path):
        store = _make_store(tmp_path)
        with pytest.raises(SystemExit) as exc:
            main(["participant-add", "--participant-id", "x1",
                  "--participant-type", "NOT_A_TYPE"], store=store)
        assert exc.value.code == 2
        assert store.read_all("PARTICIPANT") == []

    def test_participant_add_pii_fields_rejected(self, tmp_path):
        store = _make_store(tmp_path)
        with pytest.raises(SystemExit) as exc:
            main(["participant-add", "--participant-id", "x1",
                  "--participant-type", "PARK",
                  "--email", "someone@example.com"], store=store)
        assert exc.value.code == 2
        assert store.read_all("PARTICIPANT") == []


# ─── contact ─────────────────────────────────────────────────────────


class TestContact:
    def test_contact_success(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        rc = main(
            ["contact", "--participant-id", "park_a_001",
             "--hook-id", "hook_e3_001",
             "--note", "Emailed via public park mailbox"], store=store,
        )
        assert rc == 0
        events = _events(store)
        assert len(events) == 1
        ev = events[0]
        assert ev["event_type"] == "PARTICIPANT_CONTACTED"
        # Event points at the correct object: the PARTICIPANT contacted.
        assert ev["object_type"] == "PARTICIPANT"
        assert ev["object_id"] == "park_a_001"
        assert ev["actor_type"] == "EXPERIMENTER"
        assert ev["source"] == "record_outreach_cli"
        assert "hook_e3_001" in ev["note"]
        assert ev.get("response_level") is None

    def test_contact_missing_participant_refused(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        rc = main(["contact", "--participant-id", "ghost",
                   "--hook-id", "hook_e3_001", "--note", "n"], store=store)
        assert rc == 1
        assert _events(store) == []

    def test_contact_missing_hook_refused(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_participant(store)
        rc = main(["contact", "--participant-id", "park_a_001",
                   "--hook-id", "ghost_hook", "--note", "n"], store=store)
        assert rc == 1
        assert _events(store) == []

    def test_contact_requires_note(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        rc = main(["contact", "--participant-id", "park_a_001",
                   "--hook-id", "hook_e3_001"], store=store)
        assert rc == 1
        assert _events(store) == []

    def test_contact_does_not_auto_generate_interest(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        main(["contact", "--participant-id", "park_a_001",
              "--hook-id", "hook_e3_001", "--note", "cold outreach"], store=store)
        event_types = [e["event_type"] for e in _events(store)]
        assert event_types == ["PARTICIPANT_CONTACTED"]
        assert "HOOK_INTERESTED" not in event_types


# ─── respond ─────────────────────────────────────────────────────────


class TestRespond:
    @pytest.mark.parametrize("level", ["L1", "L2", "L3", "L4"])
    def test_respond_levels_l1_to_l4_success(self, tmp_path, level):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        rc = main(
            ["respond", "--participant-id", "park_a_001",
             "--hook-id", "hook_e3_001", "--level", level,
             "--evidence-ref", "email-reply-001.eml"], store=store,
        )
        assert rc == 0
        ev = _events(store)[0]
        assert ev["event_type"] == "PARTICIPANT_RESPONDED"
        assert ev["response_level"] == level
        assert ev["object_type"] == "PARTICIPANT"
        assert ev["object_id"] == "park_a_001"
        assert ev["actor_type"] == "EXPERIMENTER"
        assert ev["evidence_ref"] == "email-reply-001.eml"

    def test_respond_missing_level_refused(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        with pytest.raises(SystemExit) as exc:
            main(["respond", "--participant-id", "park_a_001",
                  "--hook-id", "hook_e3_001",
                  "--note", "replied"], store=store)
        assert exc.value.code == 2
        assert _events(store) == []

    def test_respond_l0_refused(self, tmp_path, capsys):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        rc = main(["respond", "--participant-id", "park_a_001",
                   "--hook-id", "hook_e3_001", "--level", "L0",
                   "--note", "silence"], store=store)
        assert rc == 1
        assert "L0" in capsys.readouterr().err
        assert _events(store) == []

    def test_respond_l5_refused(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        with pytest.raises(SystemExit) as exc:
            main(["respond", "--participant-id", "park_a_001",
                  "--hook-id", "hook_e3_001", "--level", "L5",
                  "--note", "bogus"], store=store)
        assert exc.value.code == 2
        assert _events(store) == []

    def test_respond_missing_participant_refused(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        rc = main(["respond", "--participant-id", "ghost",
                   "--hook-id", "hook_e3_001", "--level", "L1",
                   "--note", "n"], store=store)
        assert rc == 1
        assert _events(store) == []

    def test_respond_missing_hook_refused(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_participant(store)
        rc = main(["respond", "--participant-id", "park_a_001",
                   "--hook-id", "ghost_hook", "--level", "L2",
                   "--evidence-ref", "x"], store=store)
        assert rc == 1
        assert _events(store) == []

    def test_respond_evidence_guard_both_empty_refused(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        rc = main(["respond", "--participant-id", "park_a_001",
                   "--hook-id", "hook_e3_001", "--level", "L1"], store=store)
        assert rc == 1
        assert _events(store) == []

    def test_respond_evidence_ref_alone_suffices(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        rc = main(["respond", "--participant-id", "park_a_001",
                   "--hook-id", "hook_e3_001", "--level", "L2",
                   "--evidence-ref", "wechat-screenshot.png"], store=store)
        assert rc == 0

    def test_respond_does_not_generate_claim(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        main(["respond", "--participant-id", "park_a_001",
              "--hook-id", "hook_e3_001", "--level", "L1",
              "--note", "interested, asked for deck"], store=store)
        # No second event, no claim artifact anywhere in the raw JSONL.
        assert len(_events(store)) == 1
        raw = "\n".join(
            _raw_lines(store, "events.jsonl")
            + _raw_lines(store, "hooks.jsonl")
        )
        assert "CLAIM" not in raw
        assert "claim_status" not in raw
        assert "claim_token" not in raw
        assert "HOOK_CLAIMED" not in raw

    def test_respond_l3_no_claim_artifacts(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        main(["respond", "--participant-id", "park_a_001",
              "--hook-id", "hook_e3_001", "--level", "L3",
              "--evidence-ref", "signed-loi.pdf"], store=store)
        # L3 stays a pure experimental observation.
        events = _events(store)
        assert len(events) == 1
        assert events[0]["event_type"] == "PARTICIPANT_RESPONDED"
        assert events[0]["response_level"] == "L3"
        for ev in events:
            assert "claim_status" not in ev
            assert "claim_token" not in ev
        assert store.read_all("HOOK")[0].get("claim_status") is None


# ─── hook events ─────────────────────────────────────────────────────


class TestHookEvents:
    @pytest.mark.parametrize(
        "cmd,event_type",
        [
            ("hook-interested", "HOOK_INTERESTED"),
            ("hook-responded", "HOOK_RESPONDED"),
            ("hook-connected", "HOOK_CONNECTED"),
        ],
    )
    def test_hook_event_success(self, tmp_path, cmd, event_type):
        store = _make_store(tmp_path)
        _seed_hook(store)
        rc = main([cmd, "--hook-id", "hook_e3_001",
                   "--note", "phone call follow-up"], store=store)
        assert rc == 0
        ev = _events(store)[0]
        assert ev["event_type"] == event_type
        assert ev["object_type"] == "HOOK"
        assert ev["object_id"] == "hook_e3_001"
        assert ev["actor_type"] == "EXPERIMENTER"
        assert ev.get("response_level") is None

    def test_hook_event_missing_hook_refused(self, tmp_path):
        store = _make_store(tmp_path)
        rc = main(["hook-interested", "--hook-id", "ghost",
                   "--note", "n"], store=store)
        assert rc == 1
        assert _events(store) == []

    @pytest.mark.parametrize(
        "cmd",
        ["hook-interested", "hook-responded", "hook-connected"],
    )
    def test_hook_event_evidence_guard_refused(self, tmp_path, cmd):
        store = _make_store(tmp_path)
        _seed_hook(store)
        rc = main([cmd, "--hook-id", "hook_e3_001"], store=store)
        assert rc == 1
        assert _events(store) == []

    @pytest.mark.parametrize(
        "cmd",
        ["hook-interested", "hook-responded", "hook-connected"],
    )
    def test_hook_event_response_level_flag_refused(self, tmp_path, cmd):
        store = _make_store(tmp_path)
        _seed_hook(store)
        with pytest.raises(SystemExit) as exc:
            main([cmd, "--hook-id", "hook_e3_001",
                  "--note", "n", "--response-level", "L1"], store=store)
        assert exc.value.code == 2
        assert _events(store) == []

    def test_a1_pairing_shares_evidence(self, tmp_path):
        """A1: real L1 = paired PARTICIPANT_RESPONDED(L1) + HOOK_INTERESTED
        sharing the same evidence_ref. Manual, two CLI calls, no automation."""
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        rc1 = main(["respond", "--participant-id", "park_a_001",
                    "--hook-id", "hook_e3_001", "--level", "L1",
                    "--evidence-ref", "reply-mail-007.eml"], store=store)
        rc2 = main(["hook-interested", "--hook-id", "hook_e3_001",
                    "--evidence-ref", "reply-mail-007.eml"], store=store)
        assert rc1 == 0 and rc2 == 0
        events = _events(store)
        by_type = {e["event_type"]: e for e in events}
        assert by_type["PARTICIPANT_RESPONDED"]["response_level"] == "L1"
        assert (
            by_type["PARTICIPANT_RESPONDED"]["evidence_ref"]
            == by_type["HOOK_INTERESTED"]["evidence_ref"]
            == "reply-mail-007.eml"
        )

    def test_a2_responded_and_connected_independent(self, tmp_path):
        """A2: HOOK_RESPONDED and HOOK_CONNECTED are recorded separately;
        CONNECTED is never auto-derived from RESPONDED."""
        store = _make_store(tmp_path)
        _seed_hook(store)
        rc1 = main(["hook-responded", "--hook-id", "hook_e3_001",
                    "--note", "asked for more material"], store=store)
        rc2 = main(["hook-connected", "--hook-id", "hook_e3_001",
                    "--note", "intro call happened"], store=store)
        assert rc1 == 0 and rc2 == 0
        types = [e["event_type"] for e in _events(store)]
        assert types == ["HOOK_RESPONDED", "HOOK_CONNECTED"]


# ─── event identity / actor ──────────────────────────────────────────


class TestEventIdentity:
    def test_event_id_uses_existing_canonicalization(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        main(["hook-interested", "--hook-id", "hook_e3_001",
              "--evidence-ref", "ev-1"], store=store)
        ev = _events(store)[0]
        assert ev["event_id"] == compute_event_id(ev)

    def test_all_events_actor_type_experimenter(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        main(["contact", "--participant-id", "park_a_001",
              "--hook-id", "hook_e3_001", "--note", "n"], store=store)
        main(["respond", "--participant-id", "park_a_001",
              "--hook-id", "hook_e3_001", "--level", "L2",
              "--evidence-ref", "e"], store=store)
        main(["hook-connected", "--hook-id", "hook_e3_001",
              "--note", "n"], store=store)
        for ev in _events(store):
            assert ev["actor_type"] == "EXPERIMENTER"

    def test_all_records_revalidate(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        main(["contact", "--participant-id", "park_a_001",
              "--hook-id", "hook_e3_001", "--note", "n1"], store=store)
        main(["respond", "--participant-id", "park_a_001",
              "--hook-id", "hook_e3_001", "--level", "L4",
              "--evidence-ref", "e2"], store=store)
        main(["hook-interested", "--hook-id", "hook_e3_001",
              "--note", "n3"], store=store)
        for record in (
            store.read_all("HOOK")
            + store.read_all("PARTICIPANT")
            + store.read_all("EVENT")
        ):
            is_valid, errors = validate(record)
            assert is_valid, errors


# ─── CLI behavior / isolation ────────────────────────────────────────


class TestCLIBehaviorAndIsolation:
    def test_unknown_command_exit_2(self, tmp_path):
        store = _make_store(tmp_path)
        with pytest.raises(SystemExit) as exc:
            main(["bogus-command"], store=store)
        assert exc.value.code == 2

    def test_no_command_exit_2(self, tmp_path):
        store = _make_store(tmp_path)
        with pytest.raises(SystemExit) as exc:
            main([], store=store)
        assert exc.value.code == 2

    def test_store_isolated_to_tmp_dir(self, tmp_path):
        store = _make_store(tmp_path)
        _seed_hook(store)
        _seed_participant(store)
        main(["contact", "--participant-id", "park_a_001",
              "--hook-id", "hook_e3_001", "--note", "n"], store=store)
        files = sorted(p.name for p in Path(store.records_dir).iterdir())
        assert files == ["events.jsonl", "hooks.jsonl", "participants.jsonl"]

    def test_production_records_untouched(self):
        # Production records dir must contain ONLY .gitignore.
        entries = sorted(p.name for p in PRODUCTION_RECORDS_DIR.iterdir())
        assert entries == [".gitignore"]
