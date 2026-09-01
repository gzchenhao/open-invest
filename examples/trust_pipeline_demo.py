"""
OpenInvest Trust Verification Showcase Demo

Demonstrates the complete verification lifecycle using REAL production APIs:
  TrustEvidenceService · VerificationEventLog · HumanVerificationAuthorityRegistry
  HumanVerificationGate · compute_content_identity · record_human_verification
  detect_content_change · revoke_verified · check_verified_validity

Lifecycle:
  Create Evidence → UNVERIFIED
    → Agent/System attempt → DENIED
    → Human Authority verification → VERIFIED
    → Content change → change detected
    → Revocation → UNVERIFIED
    → Human Re-verification → VERIFIED

DEMO DATA — NOT REAL GOVERNMENT DATA.
The demo authority is an application-level demo identifier, NOT real-world identity authentication.

OpenInvest — Trust Evidence System
"""

import os
import sys
import tempfile
import traceback

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from trust.trust_service import TrustEvidenceService
from trust.verification_event_log import (
    VerificationEventLog,
    HumanVerificationAuthority,
    HumanVerificationAuthorityRegistry,
    compute_content_identity,
)


# ---------------------------------------------------------------------------
# Demo configuration — deterministic, isolated, no real identity claims.
# ---------------------------------------------------------------------------

DEMO_AUTHORITY_REGISTRY = HumanVerificationAuthorityRegistry([
    HumanVerificationAuthority(
        verifier_id="demo-human-verifier",
        role="human_verifier",
        active=True,
        metadata={"display_name": "Demo Human Verifier (application-level)"},
    ),
    HumanVerificationAuthority(
        verifier_id="demo-reviewer",
        role="authorized_reviewer",
        active=True,
        metadata={"display_name": "Demo Authorized Reviewer (application-level)"},
    ),
])

DEMO_EVIDENCE_ID = "demo-policy-evidence-001"
DEMO_EVIDENCE_SOURCE_REF = "demo://mock-policy-reference"

# Evidence fields that determine content_identity
EVIDENCE_INITIAL = {
    "id": DEMO_EVIDENCE_ID,
    "type": "policy",
    "source": "demo-source",
    "source_reference": DEMO_EVIDENCE_SOURCE_REF,
    "verification_status": "UNVERIFIED",
    "confidence_score": 0.5,
}

EVIDENCE_CHANGED = {
    "id": DEMO_EVIDENCE_ID,
    "type": "policy",
    "source": "demo-source",
    "source_reference": DEMO_EVIDENCE_SOURCE_REF,
    "verification_status": "UNVERIFIED",
    "confidence_score": 0.9,  # changed → different content_identity
}


def _short_hash(h):
    """Truncate a hash for display."""
    if not h:
        return "N/A"
    return h[:16] + "..."


def _get_content_identity(service, evidence_id):
    """Get current content_identity of an evidence via production API."""
    result = service.get_evidence(evidence_id)
    if result["success"]:
        return compute_content_identity(result["evidence"])
    return None


def _get_status(service, evidence_id):
    """Get current verification_status of an evidence."""
    result = service.get_evidence(evidence_id)
    if result["success"]:
        return result["evidence"].get("verification_status", "UNKNOWN")
    return "NOT_FOUND"


def _print_header(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def _print_step(num, title):
    print(f"\n[{num}] {title}")


def _print_result(label, value, indent=4):
    print(f"{' ' * indent}{label}: {value}")


# ---------------------------------------------------------------------------
# Demo steps — each calls REAL production APIs.
# ---------------------------------------------------------------------------

def step_create_evidence(service):
    """Step 1: Create evidence → UNVERIFIED."""
    _print_step(1, "CREATE EVIDENCE")
    result = service.create_evidence(dict(EVIDENCE_INITIAL))
    if not result["success"]:
        print(f"    FAILED: {result.get('message', result)}")
        return None
    status = _get_status(service, DEMO_EVIDENCE_ID)
    ci = _get_content_identity(service, DEMO_EVIDENCE_ID)
    _print_result("Evidence ID", DEMO_EVIDENCE_ID)
    _print_result("Status", status)
    _print_result("Content Identity", _short_hash(ci))
    return ci


def step_agent_attempt(service):
    """Step 2: Agent attempts to grant VERIFIED → DENIED."""
    _print_step(2, "AGENT ATTEMPT (automated path)")
    result = service.record_human_verification(
        evidence_id=DEMO_EVIDENCE_ID,
        verifier_id="demo-agent-001",
        verifier_role="agent",
        verification_evidence=[DEMO_EVIDENCE_SOURCE_REF],
    )
    _print_result("Verifier", "demo-agent-001 (role=agent)")
    _print_result("Result", "DENIED" if not result["success"] else "UNEXPECTED SUCCESS")
    _print_result("Reason", result.get("message", "")[:80])


def step_system_attempt(service):
    """Step 3: System attempts to grant VERIFIED → DENIED."""
    _print_step(3, "SYSTEM ATTEMPT (automated path)")
    result = service.record_human_verification(
        evidence_id=DEMO_EVIDENCE_ID,
        verifier_id="demo-system-001",
        verifier_role="system",
        verification_evidence=[DEMO_EVIDENCE_SOURCE_REF],
    )
    _print_result("Verifier", "demo-system-001 (role=system)")
    _print_result("Result", "DENIED" if not result["success"] else "UNEXPECTED SUCCESS")
    _print_result("Reason", result.get("message", "")[:80])


def step_human_verification(service):
    """Step 4: Registered human authority verifies → VERIFIED."""
    _print_step(4, "HUMAN AUTHORITY VERIFICATION")
    result = service.record_human_verification(
        evidence_id=DEMO_EVIDENCE_ID,
        verifier_id="demo-human-verifier",
        verifier_role="human_verifier",
        verification_evidence=[DEMO_EVIDENCE_SOURCE_REF],
        notes="Demo verification — application-level authority, not real identity",
    )
    status = _get_status(service, DEMO_EVIDENCE_ID)
    _print_result("Verifier", "demo-human-verifier (registered, active, human_verifier)")
    _print_result("Result", "VERIFIED" if result["success"] else "DENIED")
    _print_result("Status", status)
    if result["success"]:
        _print_result("Verification Status", result.get("verification_status", ""))
    else:
        _print_result("Reason", result.get("message", "")[:80])
    return result["success"]


def step_mock_evidence(service):
    """Step 5: Show MOCK evidence can never become VERIFIED."""
    _print_step(5, "MOCK EVIDENCE (can never become VERIFIED)")
    mock_id = "demo-mock-evidence-001"
    service.create_evidence({
        "id": mock_id, "type": "policy", "source": "mock",
        "source_reference": "mock://test", "verification_status": "MOCK",
        "confidence_score": 0.0,
    })
    result = service.record_human_verification(
        evidence_id=mock_id,
        verifier_id="demo-human-verifier",
        verifier_role="human_verifier",
        verification_evidence=["mock://test"],
    )
    status = _get_status(service, mock_id)
    _print_result("Evidence ID", mock_id)
    _print_result("Initial Status", "MOCK")
    _print_result("Verification Result", "DENIED" if not result["success"] else "UNEXPECTED SUCCESS")
    _print_result("Status After Attempt", status)
    _print_result("Reason", result.get("message", "")[:80])


def step_content_change(service, original_ci):
    """Step 6: Change content → content_identity changes."""
    _print_step(6, "CONTENT CHANGE")
    # Mutate the evidence content in the graph (same pattern as production tests)
    node = service.evidence_graph.nodes[DEMO_EVIDENCE_ID]
    node.data["confidence_score"] = EVIDENCE_CHANGED["confidence_score"]
    new_ci = _get_content_identity(service, DEMO_EVIDENCE_ID)
    _print_result("Old Identity", _short_hash(original_ci))
    _print_result("New Identity", _short_hash(new_ci))
    _print_result("Changed", original_ci != new_ci)
    return new_ci


def step_change_detection(service):
    """Step 7: Detect content change → VERIFIED invalid."""
    _print_step(7, "CHANGE DETECTION")
    result = service.detect_content_change(DEMO_EVIDENCE_ID)
    _print_result("Changed", result.get("changed", False))
    _print_result("Verified Identity", _short_hash(result.get("verified_content_identity")))
    _print_result("Current Identity", _short_hash(result.get("current_content_identity")))
    _print_result("Reason", result.get("reason", "")[:80])

    # Check validity — should be invalid
    validity = service.check_verified_validity(DEMO_EVIDENCE_ID)
    _print_result("VERIFIED Valid", validity.get("is_valid", True))


def step_revocation(service):
    """Step 8: Revoke VERIFIED → UNVERIFIED."""
    _print_step(8, "REVOCATION")
    result = service.revoke_verified(DEMO_EVIDENCE_ID, reason="content_changed")
    status = _get_status(service, DEMO_EVIDENCE_ID)
    _print_result("Revoked", result.get("revoked", False))
    _print_result("Status After Revocation", status)

    # Verify revocation event exists in history
    history = service.get_verification_history(DEMO_EVIDENCE_ID)
    revoked_events = [e for e in history.get("events", []) if e.get("decision") == "revoked"]
    verified_events = [e for e in history.get("events", []) if e.get("decision") == "verified"]
    _print_result("Verified Events in Log", len(verified_events))
    _print_result("Revoked Events in Log", len(revoked_events))
    _print_result("Total Events in Log", history.get("event_count", 0))


def step_reverification(service):
    """Step 9: Human re-verification with new content_identity → VERIFIED."""
    _print_step(9, "HUMAN RE-VERIFICATION")
    result = service.record_human_verification(
        evidence_id=DEMO_EVIDENCE_ID,
        verifier_id="demo-human-verifier",
        verifier_role="human_verifier",
        verification_evidence=[DEMO_EVIDENCE_SOURCE_REF],
        notes="Re-verification after content change — new content_identity",
    )
    status = _get_status(service, DEMO_EVIDENCE_ID)
    _print_result("Verifier", "demo-human-verifier (registered, active, human_verifier)")
    _print_result("Result", "VERIFIED" if result["success"] else "DENIED")
    _print_result("Status", status)
    if not result["success"]:
        _print_result("Reason", result.get("message", "")[:80])

    # Final validity check
    validity = service.check_verified_validity(DEMO_EVIDENCE_ID)
    _print_result("VERIFIED Valid", validity.get("is_valid", False))
    return result["success"]


def step_verification_history(service):
    """Step 10: Show full verification event history (append-only)."""
    _print_step(10, "VERIFICATION EVENT HISTORY (append-only)")
    history = service.get_verification_history(DEMO_EVIDENCE_ID)
    events = history.get("events", [])
    _print_result("Total Events", len(events))
    for i, evt in enumerate(events):
        print(f"        [{i+1}] decision={evt.get('decision')}, "
              f"actor={evt.get('actor')}, role={evt.get('actor_role')}, "
              f"timestamp={evt.get('timestamp', 'N/A')[:19]}")


def step_safety_principle():
    """Final: Print the safety principle."""
    print(f"\n{'=' * 60}")
    print("  SAFETY PRINCIPLE")
    print(f"{'=' * 60}")
    print("  Agent may recommend.")
    print("  Human authority may verify.")
    print("  System may revoke.")
    print("  No automated path may restore VERIFIED.")
    print(f"\n  MOCK can never become VERIFIED.")
    print("  Content change revokes VERIFIED automatically.")
    print("  Re-verification requires a new human decision.")
    print(f"\n  Authority Registry = application-level authorization,")
    print("  NOT real-world identity authentication.")
    print(f"{'=' * 60}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Run the complete verification lifecycle demo."""
    print("=" * 60)
    print("  OpenInvest Trust Verification Showcase Demo")
    print("=" * 60)
    print("  DEMO DATA — NOT REAL GOVERNMENT DATA")
    print("  Demo authority = application-level, NOT real identity authentication")

    tmpdir = None
    try:
        # Use a temporary directory for the event log — isolated, no pollution.
        tmpdir = tempfile.mkdtemp(prefix="openinvest_demo_")
        log_path = os.path.join(tmpdir, "demo_events.jsonl")

        service = TrustEvidenceService(
            event_log_path=log_path,
            authority_registry=DEMO_AUTHORITY_REGISTRY,
        )

        # Run the full lifecycle
        original_ci = step_create_evidence(service)
        if original_ci is None:
            print("\nFATAL: Evidence creation failed — cannot continue demo.")
            return False

        step_agent_attempt(service)
        step_system_attempt(service)
        verified = step_human_verification(service)
        step_mock_evidence(service)

        if not verified:
            print("\nWARNING: Human verification did not succeed — "
                  "subsequent steps may not demonstrate revocation correctly.")

        step_content_change(service, original_ci)
        step_change_detection(service)
        step_revocation(service)
        step_reverification(service)
        step_verification_history(service)
        step_safety_principle()

        print(f"\n{'=' * 60}")
        print("  DEMO COMPLETE — All steps executed via real production APIs.")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"\nFATAL: Demo failed with exception: {e}")
        traceback.print_exc()
        return False

    finally:
        # Cleanup temporary directory
        if tmpdir and os.path.exists(tmpdir):
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
