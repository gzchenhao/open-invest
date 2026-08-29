"""
P1-3.4 — fixed_server.py Runtime Integration Tests (F-10 Closure)

These tests exercise the REAL runtime paths of ``fixed_server.py``:

    Path A (current repo state): module-level ``load_policies()`` with the
        seed file ABSENT -> hardcoded MOCK fallback policies.
    Path B (seed file present): ``load_policies()`` reads
        ``web/data/seed_data/detailed_china_tech_policies.json`` and applies
        the P1-3.3 canonical_industry enrichment (lines with the
        ``get_registry().resolve(...)`` call).
    Path C: FastAPI endpoints (``/api/stats``, ``/api/search``) served via
        TestClient against the module-level policies.

They do NOT call Registry.resolve() directly and assert on it (registry
level is covered by P1-3.2/P1-3.3 tests). F-10 (P1-3.3.1 Independent
Verification) required exactly this coverage.

Known runtime fact (recorded honestly, see P1-3.4 closure doc): the seed
file does NOT exist in the current repo, so production traffic takes the
fallback path, which emits policies WITHOUT the canonical_industry field
(graceful degradation: field absent, never a wrong value). Path B is
exercised by temporarily providing a synthetic MOCK seed file.

No real government data is used anywhere; every policy entry below is
synthetic MOCK data (``is_mock=True`` is enforced by the server itself).

Quest: P1-3.4 — Runtime Integration Test Closure (closes F-10)
"""

import importlib
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
WEB_DIR = PROJECT_ROOT / "global_policy_aggregator" / "web"
SEED_PATH = WEB_DIR / "data" / "seed_data" / "detailed_china_tech_policies.json"

# Production legacy-key -> canonical expectations (from
# schema/canonical_taxonomy.py _T7_FIXED_SERVER and the seed-path resolve
# call in fixed_server.load_policies).
T7_EXPECTED = {
    "embodied_ai": "embodied_ai",
    "auto_driving": "autonomous_driving",  # synonym
    "semiconductor": "semiconductor",
    "ai": "ai",
    "biotechnology": "biotech",  # synonym
    "quantum_computing": "quantum_computing",
    "new_energy": "new_energy",
    "fintech": "fintech",
    "aerospace": "aerospace",
    "advanced_manufacturing": "high_end_equipment",  # merged
}
# Production EN key -> CN label (from fixed_server.load_policies industry_map)
INDUSTRY_MAP_CN = {
    "embodied_ai": "具身智能",
    "auto_driving": "自动驾驶",
    "semiconductor": "半导体",
    "ai": "人工智能",
    "biotechnology": "生物医药",
    "quantum_computing": "量子计算",
    "new_energy": "新能源",
    "fintech": "金融科技",
    "aerospace": "航空航天",
    "advanced_manufacturing": "先进制造",
}


@pytest.fixture
def server_module(monkeypatch):
    """Import fixed_server with CWD at web/ (templates dir requirement)."""
    monkeypatch.chdir(WEB_DIR)
    if str(WEB_DIR) not in sys.path:
        sys.path.insert(0, str(WEB_DIR))
    return importlib.import_module("fixed_server")


@pytest.fixture
def seed_policies_file():
    """Temporarily provide a synthetic MOCK seed file, then restore state."""
    existed = SEED_PATH.exists()
    backup = SEED_PATH.parent / (SEED_PATH.name + ".p134bak") if existed else None
    if existed:
        SEED_PATH.rename(backup)
    SEED_PATH.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    for key in list(T7_EXPECTED) + ["ai_hardware", "mystery_unknown_field"]:
        entries.append(
            {
                "title": f"MOCK seed policy for {key}",
                "region": "MOCK区域",
                "industry": key,
                "policy_type": "专项补贴",
                "description": "Synthetic MOCK entry for runtime testing only.",
            }
        )
    # entry with NO industry key -> exercises the ``else "unknown"`` branch
    entries.append(
        {
            "title": "MOCK seed policy without industry",
            "region": "MOCK区域",
            "policy_type": "专项补贴",
            "description": "Synthetic MOCK entry for runtime testing only.",
        }
    )
    SEED_PATH.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    yield entries

    SEED_PATH.unlink(missing_ok=True)
    if backup is not None:
        backup.rename(SEED_PATH)


# ============================================================
# 1. Fallback path (current actual repo state)
# ============================================================
class TestFixedServerFallbackRuntime:
    def test_fallback_policies_load_without_error(self, server_module):
        policies = server_module.load_policies()
        assert len(policies) == 2

    def test_fallback_has_no_canonical_field_graceful_degradation(
        self, server_module
    ):
        policies = server_module.load_policies()
        for policy in policies:
            # graceful degradation: field ABSENT, never a wrong value
            assert "canonical_industry" not in policy

    def test_fallback_mock_markers_preserved(self, server_module):
        for policy in server_module.load_policies():
            assert policy["is_mock"] is True
            assert policy["verification_status"] == "mock"

    def test_fallback_legacy_fields_intact(self, server_module):
        for policy in server_module.load_policies():
            for legacy_field in (
                "id",
                "title",
                "region",
                "industry",
                "type",
                "amount",
                "issue_date",
                "description",
                "claim_status",
            ):
                assert legacy_field in policy
        industries = {p["industry"] for p in server_module.load_policies()}
        assert industries == {"人工智能", "半导体"}


# ============================================================
# 2. Seed path (canonical enrichment actually fires)
# ============================================================
class TestFixedServerSeedPathRuntime:
    def test_seed_path_t7_keys_end_to_end(self, server_module, seed_policies_file):
        policies = server_module.load_policies()
        by_canonical_input = {}
        for policy in policies:
            title = policy["title"]
            for key in T7_EXPECTED:
                if title == f"MOCK seed policy for {key}":
                    by_canonical_input[key] = policy
        assert set(by_canonical_input) == set(T7_EXPECTED)
        for key, policy in by_canonical_input.items():
            assert policy["canonical_industry"] == T7_EXPECTED[key], key
            # legacy CN label preserved untouched
            assert policy["industry"] == INDUSTRY_MAP_CN[key], key

    def test_ai_hardware_resolves_to_unknown_via_runtime(
        self, server_module, seed_policies_file
    ):
        policies = server_module.load_policies()
        target = [
            p
            for p in policies
            if p["title"] == "MOCK seed policy for ai_hardware"
        ]
        assert len(target) == 1
        # UNKNOWN — never guessed as ai or semiconductor
        assert target[0]["canonical_industry"] == "unknown"
        assert target[0]["canonical_industry"] != "ai"
        assert target[0]["canonical_industry"] != "semiconductor"
        # legacy field falls back to 其他 (production industry_map default)
        assert target[0]["industry"] == "其他"

    def test_unknown_seed_key_not_guessed(
        self, server_module, seed_policies_file
    ):
        policies = server_module.load_policies()
        target = [
            p
            for p in policies
            if p["title"] == "MOCK seed policy for mystery_unknown_field"
        ]
        assert len(target) == 1
        assert target[0]["canonical_industry"] == "unknown"

    def test_missing_industry_field_defaults_to_unknown(
        self, server_module, seed_policies_file
    ):
        policies = server_module.load_policies()
        target = [
            p
            for p in policies
            if p["title"] == "MOCK seed policy without industry"
        ]
        assert len(target) == 1
        assert target[0]["canonical_industry"] == "unknown"

    def test_seed_path_mock_markers_preserved(
        self, server_module, seed_policies_file
    ):
        for policy in server_module.load_policies():
            assert policy["is_mock"] is True
            assert policy["verification_status"] == "mock"
            assert policy["claim_status"] == "unclaimed"

    def test_seed_path_canonical_is_additive(
        self, server_module, seed_policies_file
    ):
        policy = server_module.load_policies()[0]
        assert policy["title"].startswith("MOCK seed policy")
        assert policy["region"] == "MOCK区域"
        assert policy["type"] == "专项补贴"
        assert policy["source_url"] == "#"
        assert isinstance(policy["details"], list)
        assert isinstance(policy["requirements"], dict)

    def test_seed_path_deterministic_20_runs(
        self, server_module, seed_policies_file
    ):
        first = [
            (p["title"], p["industry"], p["canonical_industry"])
            for p in server_module.load_policies()
        ]
        for _ in range(20):
            again = [
                (p["title"], p["industry"], p["canonical_industry"])
                for p in server_module.load_policies()
            ]
            assert again == first
        canonical = [c for (_t, _i, c) in first]
        assert canonical.count("unknown") == 3  # ai_hardware + mystery + missing


# ============================================================
# 3. FastAPI endpoints (real HTTP runtime path, fallback state)
# ============================================================
class TestFixedServerAPIEndpoints:
    @pytest.fixture
    def client(self, server_module):
        from fastapi.testclient import TestClient

        return TestClient(server_module.app)

    def test_stats_endpoint_runtime(self, client):
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_policies"] == 2
        assert set(data["industries"]) == {"人工智能", "半导体"}

    def test_search_endpoint_runtime(self, client):
        response = client.post("/api/search", data={"keywords": "半导体"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        hit = data["policies"][0]
        assert hit["industry"] == "半导体"
        # fallback state: canonical field absent, no wrong value injected
        assert "canonical_industry" not in hit

    def test_search_empty_keywords_runtime(self, client):
        response = client.post("/api/search", data={"keywords": ""})
        assert response.status_code == 200
        assert response.json() == {"count": 0, "policies": []}

    def test_endpoints_preserve_trust_semantics(self, client):
        response = client.post("/api/search", data={"keywords": "政策"})
        for policy in response.json()["policies"]:
            assert policy["is_mock"] is True
            assert policy["verification_status"] == "mock"
            assert policy["claim_status"] == "unclaimed"
            assert policy["claim_token"] is None
