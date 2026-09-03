"""P2-0B.6 — Experimenter-side E3 outreach recording CLI (stdlib-only).

Canonical E3 (per Handover): after E2 accumulates >=3 real Project Hooks,
the EXPERIMENTER manually outreaches to real policy publishers / parks /
capital participants and records their REAL responses on the L0-L4 ladder.

This CLI is the ONLY sanctioned write path for E3 events:
  - NO Portal-side E3 buttons, NO public API, NO anonymous injection.
    (Anonymous clicks must never be misread as canonical Interest/Response;
    an unauthenticated public write endpoint would let anyone forge E3
    evidence and pollute the experiment.)
  - actor_type is always EXPERIMENTER (a human-recorded fact).
  - Evidence Guard (tool-layer, NOT a schema change): factual E3 events
    (HOOK_INTERESTED / HOOK_RESPONDED / HOOK_CONNECTED / PARTICIPANT_RESPONDED)
    require a non-empty evidence_ref or note; PARTICIPANT_CONTACTED requires
    a non-empty note describing the outreach fact (channel / object linkage).
    Contact details (phone/email/etc.) must NOT be written into the JSONL.
  - Relation integrity: participant_id / hook_id must already exist.
    No orphan E3 events.
  - L0 is NEVER recorded as PARTICIPANT_RESPONDED: canonical L0 = No
    Response, while PARTICIPANT_RESPONDED asserts a response happened.
    Every outreach is recorded as PARTICIPANT_CONTACTED; if no reply arrives
    within the experiment window, L0 is DERIVED by experiment analysis,
    never written as an event.
  - NO automatic event chains: contact does NOT auto-create HOOK_INTERESTED;
    respond --level L1 does NOT auto-create any Claim; L3 stays a pure
    experimental observation (no CLAIM / HOOK_CLAIMED / claim_status /
    claim_token). Claim implementation remains PROTOTYPE / DESIGN SIGNAL.
  - A1 pairing protocol (manual, never automated): a real L1 is recorded as
    a PARTICIPANT_RESPONDED(response_level="L1") on the PARTICIPANT plus a
    HOOK_INTERESTED on the HOOK, sharing the same evidence_ref or note
    semantics. They are two projections of ONE fact, not two replies.
  - A2: HOOK_RESPONDED (asked for more material / asked to connect) and
    HOOK_CONNECTED (actual contact established) are recorded separately;
    HOOK_CONNECTED is never derived from HOOK_RESPONDED.
  - Event IDs fully reuse the existing B.2 canonicalization
    (ExperimentalJSONLStore.append_event -> compute_event_id). No second
    ID scheme, no new database, no changes to record_validator.py,
    jsonl_store.py, or any *.schema.json.

Exit codes: 0 = recorded; 1 = refused by this tool (semantic guard);
2 = argparse usage error (SystemExit).
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from p2_0_experimental.jsonl_store import ExperimentalJSONLStore
from p2_0_experimental.record_validator import PARTICIPANT_TYPES

RECORDS_DIR = Path(__file__).resolve().parent / "records"
SOURCE = "record_outreach_cli"

# Canonical ladder: L0 = No Response is DERIVED by analysis, never recorded.
# PARTICIPANT_RESPONDED only accepts L1-L4.
RESPONSE_LEVELS_ALLOWED = ("L1", "L2", "L3", "L4")

_HOOK_TAG_SUFFIX = " [hook={hook_id}]"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fail(message: str) -> int:
    print(f"[P2-0B.6] REFUSED: {message}", file=sys.stderr)
    return 1


def _has_evidence(args: argparse.Namespace) -> bool:
    """Evidence Guard on RAW user input (before any marker is appended)."""
    return bool((args.evidence_ref or "").strip()) or bool((args.note or "").strip())


def _compose_event(
    event_type: str,
    object_type: str,
    object_id: str,
    *,
    evidence_ref=None,
    note=None,
    response_level=None,
):
    event = {
        "record_type": "EVENT",
        "timestamp": _utc_now_iso(),
        "event_type": event_type,
        "source": SOURCE,
        "actor_type": "EXPERIMENTER",
        "object_type": object_type,
        "object_id": object_id,
    }
    if evidence_ref:
        event["evidence_ref"] = evidence_ref
    if note:
        event["note"] = note
    if response_level:
        event["response_level"] = response_level
    return event


def _append(store: ExperimentalJSONLStore, event: dict) -> int:
    try:
        event_id = store.append_event(event)
    except (ValueError, OSError) as exc:
        return _fail(f"store refused event: {exc}")
    print(
        f"OK {event['event_type']} object={event['object_type']}:{event['object_id']} "
        f"event_id={event_id}"
    )
    return 0


def _require_participant(store: ExperimentalJSONLStore, participant_id: str):
    return store.read_by_id("PARTICIPANT", participant_id)


def _require_hook(store: ExperimentalJSONLStore, hook_id: str):
    return store.read_by_id("HOOK", hook_id)


# ─── Handlers ────────────────────────────────────────────────────────


def _cmd_participant_add(args: argparse.Namespace, store: ExperimentalJSONLStore) -> int:
    if _require_participant(store, args.participant_id) is not None:
        return _fail(
            f"participant alias already exists: '{args.participant_id}'. "
            f"participant_id is an experimenter-local alias, not a verified identity."
        )
    record = {
        "record_type": "PARTICIPANT",
        "participant_id": args.participant_id,
        "participant_type": args.participant_type,
        "source": args.source,
    }
    try:
        store.append(record)
    except (ValueError, OSError) as exc:
        return _fail(f"store refused participant: {exc}")
    print(f"OK PARTICIPANT participant_id={args.participant_id}")
    return 0


def _cmd_contact(args: argparse.Namespace, store: ExperimentalJSONLStore) -> int:
    if _require_participant(store, args.participant_id) is None:
        return _fail(f"participant does not exist: '{args.participant_id}'")
    if _require_hook(store, args.hook_id) is None:
        return _fail(f"hook does not exist: '{args.hook_id}'")
    note = (args.note or "").strip()
    if not note:
        return _fail(
            "PARTICIPANT_CONTACTED requires a non-empty --note describing the "
            "outreach fact (channel / object linkage). Contact details "
            "(phone/email/etc.) must NOT be recorded."
        )
    note = note + _HOOK_TAG_SUFFIX.format(hook_id=args.hook_id)
    event = _compose_event(
        "PARTICIPANT_CONTACTED",
        "PARTICIPANT",
        args.participant_id,
        evidence_ref=(args.evidence_ref or "").strip() or None,
        note=note,
    )
    return _append(store, event)


def _cmd_respond(args: argparse.Namespace, store: ExperimentalJSONLStore) -> int:
    if args.level == "L0":
        return _fail(
            "L0 (No Response) is NEVER recorded as PARTICIPANT_RESPONDED: "
            "'RESPONDED' asserts a response happened, L0 asserts none did. "
            "Record every outreach via 'contact'; if no reply arrives within "
            "the experiment window, L0 is derived by experiment analysis."
        )
    if args.level not in RESPONSE_LEVELS_ALLOWED:
        return _fail(
            f"--level must be one of {RESPONSE_LEVELS_ALLOWED} — got '{args.level}'"
        )
    if _require_participant(store, args.participant_id) is None:
        return _fail(f"participant does not exist: '{args.participant_id}'")
    if _require_hook(store, args.hook_id) is None:
        return _fail(f"hook does not exist: '{args.hook_id}'")
    if not _has_evidence(args):
        return _fail(
            "PARTICIPANT_RESPONDED requires a non-empty --evidence-ref or "
            "--note (Evidence Guard). Refusing to write an unevidenced fact."
        )
    note = (args.note or "").strip()
    if note:
        note = note + _HOOK_TAG_SUFFIX.format(hook_id=args.hook_id)
    event = _compose_event(
        "PARTICIPANT_RESPONDED",
        "PARTICIPANT",
        args.participant_id,
        evidence_ref=(args.evidence_ref or "").strip() or None,
        note=note or None,
        response_level=args.level,
    )
    return _append(store, event)


def _make_hook_handler(event_type: str):
    def handler(args: argparse.Namespace, store: ExperimentalJSONLStore) -> int:
        if _require_hook(store, args.hook_id) is None:
            return _fail(f"hook does not exist: '{args.hook_id}'")
        if not _has_evidence(args):
            return _fail(
                f"{event_type} requires a non-empty --evidence-ref or --note "
                f"(Evidence Guard). Refusing to write an unevidenced fact."
            )
        event = _compose_event(
            event_type,
            "HOOK",
            args.hook_id,
            evidence_ref=(args.evidence_ref or "").strip() or None,
            note=(args.note or "").strip() or None,
        )
        return _append(store, event)

    handler.__name__ = f"_cmd_{event_type.lower()}"
    return handler


# ─── Parser ──────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="record_outreach",
        description=(
            "Record canonical E3 manual-outreach facts as EXPERIMENTER "
            "(P2-0B.6). Tool-layer Evidence Guard; no Portal write path."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser(
        "participant-add",
        help=(
            "Create a minimal experimenter-local participant alias "
            "(NOT a verified identity; no name/company/phone/email/CRM)."
        ),
    )
    p_add.add_argument("--participant-id", required=True)
    p_add.add_argument(
        "--participant-type",
        required=True,
        choices=sorted(PARTICIPANT_TYPES),
    )
    p_add.add_argument("--source", default=SOURCE)
    p_add.set_defaults(func=_cmd_participant_add)

    p_contact = sub.add_parser(
        "contact",
        help="Record one real outreach as PARTICIPANT_CONTACTED (note required).",
    )
    p_contact.add_argument("--participant-id", required=True)
    p_contact.add_argument("--hook-id", required=True)
    p_contact.add_argument("--evidence-ref", default=None)
    p_contact.add_argument("--note", default=None)
    p_contact.set_defaults(func=_cmd_contact)

    p_respond = sub.add_parser(
        "respond",
        help=(
            "Record a REAL participant response as PARTICIPANT_RESPONDED "
            "with --level L1-L4. L0 is never recordable."
        ),
    )
    p_respond.add_argument("--participant-id", required=True)
    p_respond.add_argument("--hook-id", required=True)
    p_respond.add_argument(
        "--level",
        required=True,
        choices=["L0", "L1", "L2", "L3", "L4"],
        help="Canonical ladder level of the response (L1-L4; L0 refused).",
    )
    p_respond.add_argument("--evidence-ref", default=None)
    p_respond.add_argument("--note", default=None)
    p_respond.set_defaults(func=_cmd_respond)

    for event_type in ("HOOK_INTERESTED", "HOOK_RESPONDED", "HOOK_CONNECTED"):
        cmd_name = event_type.lower().replace("_", "-")
        p_hook = sub.add_parser(
            cmd_name,
            help=f"Record {event_type} on an existing hook (evidence required).",
        )
        p_hook.add_argument("--hook-id", required=True)
        p_hook.add_argument("--evidence-ref", default=None)
        p_hook.add_argument("--note", default=None)
        p_hook.set_defaults(func=_make_hook_handler(event_type))

    return parser


def _load_store() -> ExperimentalJSONLStore:
    records_dir = os.environ.get("P2_0_RECORDS_DIR") or str(RECORDS_DIR)
    return ExperimentalJSONLStore(records_dir)


def main(argv=None, store: ExperimentalJSONLStore | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if store is None:
        store = _load_store()
    return args.func(args, store)


if __name__ == "__main__":
    raise SystemExit(main())
