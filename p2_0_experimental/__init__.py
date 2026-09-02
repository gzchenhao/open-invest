"""
P2-0 EXPERIMENTAL Record Format — VALIDATION-ONLY / NON-CANONICAL

Minimal experimental record format for P2-0 E1/E2/E3 real-world experiment
observation.  This package exists solely so that Policy / ProjectIntent / Hook /
Participant / Event records produced during P2-0 experiments can be reliably
recorded, audited, and replayed.

SEMANTIC LOCKS — must not be violated by any future edit:
  - Experimental Record  ≠  Canonical Schema
  - Hook                 ≠  Claim          (Hook has no status / claim_status / claim_token)
  - ProjectIntent        ≠  Project        (no Project Entity, no Project CRUD)
  - REAL                 ≠  VERIFIED       (is_mock=false + verification_status="UNVERIFIED"
                                            is the only REAL combination; "VERIFIED" is NEVER
                                            producible at this layer)
  - Hook has NO status machine               (Interest / Response / Connection are Events,
                                             not Hook fields)
  - No automatic event generation            (creating a Hook does NOT auto-create
                                             HOOK_INTERESTED; PARTICIPANT_CONTACTED does NOT
                                             auto-create INTERESTED or Claim)
  - Response Ladder L0-L4 is observation     (NOT a state machine; NOT auto-promoted)

ISOLATION:
  This package is completely isolated from src/trust/ (Trust Layer).
  It does NOT import, call, or share log files with the Trust Layer.
  It CANNOT grant VERIFIED status.
  Trust Layer VERIFIED is granted ONLY by HumanVerificationGate (10-condition fail-closed).

EXPERIMENTAL | VALIDATION-ONLY | NON-CANONICAL
DO NOT TREAT AS PRODUCTION SCHEMA.
"""

__all__ = ["record_validator", "jsonl_store"]
