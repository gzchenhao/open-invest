"""P4-1 Policy Matching (consumption layer).

P4-0 锁死边界：消费层 / 实验层，不属于 Trust Verification，也不属于 P3 ingestion。
不 import agents.policy_ai_agent / crawlers / src.trust。
"""

from global_policy_aggregator.matching.project_profile import (  # noqa: F401
    ProjectProfile,
    ProfileFieldEvidence,
    build_project_profile,
    SCHEMA_VERSION as PROFILE_SCHEMA_VERSION,
)
from global_policy_aggregator.matching.policy_match import (  # noqa: F401
    MatchResult,
    EvidenceRef,
    DimensionResult,
    PolicyMatcher,
    match_project_to_policy,
    match_project_to_policies,
    MATCH_STATUS_MATCHED,
    MATCH_STATUS_PARTIAL,
    MATCH_STATUS_INSUFFICIENT,
    MATCH_STATUS_NOT,
    REAL_POLICIES_PATH,
    MATCH_RESULTS_PATH,
)
