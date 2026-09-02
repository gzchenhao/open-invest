"""
P2-0 Experimental JSONL Store — append-only, isolated from Trust Layer.

Mirrors the append-only / fail-loud philosophy of src/trust/verification_event_log.py
but shares NO code, NO log files, and NO imports with the Trust Layer.

This store CANNOT grant VERIFIED status. It only records experimental observations.

Design constraints:
  - Append-only: no update or delete operations.
  - Write failure raises OSError (never silently swallowed).
  - Duplicate event_id on EVENT records is rejected.
  - One JSON object per line, UTF-8.
  - Records are validated BEFORE write (validator runs first).
"""

import json
import os
from typing import Any, Dict, List

from p2_0_experimental.record_validator import validate, compute_event_id

# File name per record type
_FILE_MAP = {
    "POLICY": "policies.jsonl",
    "PROJECT_INTENT": "project_intents.jsonl",
    "HOOK": "hooks.jsonl",
    "PARTICIPANT": "participants.jsonl",
    "EVENT": "events.jsonl",
}

# ID field per record type (for return value and duplicate check)
_ID_FIELD = {
    "POLICY": "policy_id",
    "PROJECT_INTENT": "project_intent_id",
    "HOOK": "hook_id",
    "PARTICIPANT": "participant_id",
    "EVENT": "event_id",
}


class ExperimentalJSONLStore:
    """Append-only JSONL store for P2-0 experimental records.

    ISOLATED from Trust Layer VerificationEventLog:
      - Does NOT import src.trust.*
      - Does NOT read/write Trust Layer log paths
      - Does NOT grant VERIFIED
      - Does NOT call HumanVerificationGate
    """

    def __init__(self, records_dir: str):
        """Initialize with a records directory.

        The directory is created lazily on first append if it does not exist.
        """
        self.records_dir = records_dir

    # ─── append ──────────────────────────────────────────────────

    def append(self, record: Dict[str, Any]) -> str:
        """Validate and append a record. Returns the record's ID on success.

        Raises:
            ValueError — if the record fails validation, or if an EVENT
                         record has a duplicate event_id.
            OSError    — if the write fails (never silently swallowed).
        """
        # 1. Validate before write
        is_valid, errors = validate(record)
        if not is_valid:
            raise ValueError(f"Invalid record: {errors}")

        rt = record["record_type"]
        filename = _FILE_MAP[rt]
        filepath = os.path.join(self.records_dir, filename)

        # 2. Ensure directory exists
        os.makedirs(self.records_dir, exist_ok=True)

        # 3. Duplicate event_id check for EVENT records
        if rt == "EVENT":
            event_id = record["event_id"]
            if self._id_exists(filepath, "event_id", event_id):
                raise ValueError(f"Duplicate event_id rejected: {event_id}")

        # 4. Append (one JSON per line, UTF-8, fsync for durability)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())

        # 5. Return the record's ID
        id_field = _ID_FIELD[rt]
        return record[id_field]

    # ─── read ────────────────────────────────────────────────────

    def read_all(self, record_type: str) -> List[Dict[str, Any]]:
        """Read all records of a given type. Returns [] if file does not exist.

        Malformed lines are collected and reported via a returned error list,
        never silently skipped (mirrors Trust Layer replay philosophy).
        """
        if record_type not in _FILE_MAP:
            raise ValueError(f"Unknown record_type: {record_type}")

        filepath = os.path.join(self.records_dir, _FILE_MAP[record_type])
        if not os.path.exists(filepath):
            return []

        records: List[Dict[str, Any]] = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Malformed JSON at {filepath}:{line_num}: {e}"
                    ) from e
        return records

    def read_by_id(self, record_type: str, record_id: str) -> Dict[str, Any] | None:
        """Read a single record by ID. Returns None if not found."""
        id_field = _ID_FIELD.get(record_type)
        if id_field is None:
            raise ValueError(f"Unknown record_type: {record_type}")

        for record in self.read_all(record_type):
            if record.get(id_field) == record_id:
                return record
        return None

    # ─── helpers ─────────────────────────────────────────────────

    def _id_exists(self, filepath: str, id_field: str, id_value: str) -> bool:
        """Check if an ID already exists in the log file.

        Fail-closed: malformed JSON lines raise ValueError (consistent with
        read_all()). No silent skip. This prevents a malformed line from
        hiding a pre-existing duplicate event_id.
        """
        if not os.path.exists(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if record.get(id_field) == id_value:
                        return True
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Malformed JSON at {filepath}:{line_num}: {e}"
                    ) from e
        return False

    # ─── convenience ─────────────────────────────────────────────

    def append_event(self, event: Dict[str, Any]) -> str:
        """Convenience: compute event_id if missing, then append.

        If event_id is absent, it is computed deterministically via
        compute_event_id(). This is the ONLY place event_id is auto-set —
        and it is a deterministic hash, not an invented value.
        """
        if "event_id" not in event or not event.get("event_id"):
            event = dict(event)  # shallow copy — don't mutate caller's dict
            event["event_id"] = compute_event_id(event)
        return self.append(event)
