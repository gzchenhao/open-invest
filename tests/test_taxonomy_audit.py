"""
P1-3.0 — Industry Taxonomy Consistency Audit Tests

These tests verify the EXISTING state of industry taxonomy inconsistency.
They do NOT implement a unified taxonomy.

Purpose:
- Document the current taxonomy landscape
- Ensure taxonomy inconsistency is detectable (not silently resolved)
- Prevent accidental taxonomy changes without awareness
- Verify that no component falsely claims taxonomy unification

Quest: P1-3.0 AUDIT ONLY — No Implementation
"""

import pytest
import json
from pathlib import Path


# ─────────────────────────────────────────────────────────
# T1: Parser industry_mapping audit
# ─────────────────────────────────────────────────────────

class TestParserTaxonomy:
    """Audit: Parser (policy_cleaner.py) industry taxonomy"""

    def test_parser_industry_mapping_exists(self):
        """Parser must have an industry_mapping"""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        assert hasattr(cleaner, 'industry_mapping')
        assert isinstance(cleaner.industry_mapping, dict)
        assert len(cleaner.industry_mapping) > 0

    def test_parser_mapping_has_10_cn_keys(self):
        """Parser industry_mapping has 10 Chinese input keys"""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        assert len(cleaner.industry_mapping) == 10

    def test_parser_mapping_produces_8_unique_en_values(self):
        """Parser industry_mapping produces 8 distinct English output values"""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        unique_values = set(cleaner.industry_mapping.values())
        assert len(unique_values) == 8

    def test_parser_mapping_contains_other_fallback(self):
        """Parser must have 'other' as fallback category"""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        values = set(cleaner.industry_mapping.values())
        assert "other" in values

    def test_parser_mapping_vr_ar_merge(self):
        """Parser merges 虚拟现实 and 增强现实 into vr_ar"""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        assert cleaner.industry_mapping.get("虚拟现实") == "vr_ar"
        assert cleaner.industry_mapping.get("增强现实") == "vr_ar"


# ─────────────────────────────────────────────────────────
# T2: Schema IndustryType enum audit
# ─────────────────────────────────────────────────────────

class TestSchemaTaxonomy:
    """Audit: Schema (types.py) IndustryType enum"""

    def test_schema_industry_type_exists(self):
        """Schema must define IndustryType enum"""
        from schema.types import IndustryType
        assert IndustryType is not None

    def test_schema_industry_type_has_5_values(self):
        """Schema IndustryType has exactly 5 enum values"""
        from schema.types import IndustryType
        assert len(IndustryType) == 5

    def test_schema_industry_type_values(self):
        """Schema IndustryType contains expected values"""
        from schema.types import IndustryType
        expected = {"autonomous_driving", "embodied_ai", "robotics", "ai_hardware", "quantum_computing"}
        actual = {e.value for e in IndustryType}
        assert actual == expected


# ─────────────────────────────────────────────────────────
# T3: Web Portal taxonomy audit
# ─────────────────────────────────────────────────────────

class TestWebPortalTaxonomy:
    """Audit: Web Portal (interactive_ai_server.py) industry labels"""

    def test_web_portal_has_12_policies(self):
        """Web portal has 12 mock policies"""
        from global_policy_aggregator.web.interactive_ai_server import policies
        assert len(policies) == 12

    def test_web_portal_has_12_unique_industries(self):
        """Web portal policies have 12 unique Chinese industry labels"""
        from global_policy_aggregator.web.interactive_ai_server import policies
        industries = set(p["industry"] for p in policies)
        assert len(industries) == 12

    def test_web_portal_all_policies_are_mock(self):
        """All web portal policies must be marked as mock"""
        from global_policy_aggregator.web.interactive_ai_server import policies
        for p in policies:
            assert p.get("is_mock") is True
            assert p.get("verification_status") == "mock"


# ─────────────────────────────────────────────────────────
# T4: Seed Data taxonomy audit
# ─────────────────────────────────────────────────────────

class TestSeedDataTaxonomy:
    """Audit: Seed Data JSON files industry taxonomy"""

    def test_seed_data_china_policy_exists(self):
        """china_policy_seed_data.json must exist"""
        path = Path(__file__).parent.parent / "global_policy_aggregator" / "data" / "seed_data" / "china_policy_seed_data.json"
        assert path.exists()

    def test_seed_data_has_12_policies(self):
        """china_policy_seed_data.json has 12 policies"""
        path = Path(__file__).parent.parent / "global_policy_aggregator" / "data" / "seed_data" / "china_policy_seed_data.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 12

    def test_seed_data_has_8_unique_industries(self):
        """china_policy_seed_data.json has 8 unique industry values"""
        path = Path(__file__).parent.parent / "global_policy_aggregator" / "data" / "seed_data" / "china_policy_seed_data.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        industries = set(p["industry"] for p in data)
        assert len(industries) == 8

    def test_detailed_policies_exist(self):
        """detailed_china_tech_policies.json must exist"""
        path = Path(__file__).parent.parent / "global_policy_aggregator" / "data" / "seed_data" / "detailed_china_tech_policies.json"
        assert path.exists()

    def test_detailed_policies_has_9_policies(self):
        """detailed_china_tech_policies.json has 9 policies"""
        path = Path(__file__).parent.parent / "global_policy_aggregator" / "data" / "seed_data" / "detailed_china_tech_policies.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 9

    def test_detailed_policies_has_8_unique_industries(self):
        """detailed_china_tech_policies.json has 8 unique industry values"""
        path = Path(__file__).parent.parent / "global_policy_aggregator" / "data" / "seed_data" / "detailed_china_tech_policies.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        industries = set(p["industry"] for p in data)
        assert len(industries) == 8


# ─────────────────────────────────────────────────────────
# T5: Cross-component taxonomy inconsistency detection
# ─────────────────────────────────────────────────────────

class TestTaxonomyInconsistency:
    """Verify that taxonomy inconsistency is preserved (not silently resolved)"""

    def test_parser_and_schema_taxonomies_differ(self):
        """Parser output values and Schema enum values are NOT the same set"""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        from schema.types import IndustryType

        cleaner = PolicyCleaner()
        parser_values = set(cleaner.industry_mapping.values())
        schema_values = {e.value for e in IndustryType}

        # These two sets should NOT be equal (known inconsistency)
        assert parser_values != schema_values

    def test_web_portal_and_parser_use_different_languages(self):
        """Web portal uses Chinese labels, Parser uses English labels"""
        from global_policy_aggregator.web.interactive_ai_server import policies
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner

        cleaner = PolicyCleaner()
        parser_values = set(cleaner.industry_mapping.values())
        web_industries = set(p["industry"] for p in policies)

        # Web portal uses Chinese, Parser uses English — no overlap expected
        overlap = parser_values & web_industries
        # At most "AI" might overlap with something, but generally no overlap
        # This test documents the language mismatch
        assert len(overlap) <= 1, "Web portal and Parser should use different label systems"

    def test_seed_data_files_use_different_labels(self):
        """Two seed data files use some different industry labels"""
        path1 = Path(__file__).parent.parent / "global_policy_aggregator" / "data" / "seed_data" / "china_policy_seed_data.json"
        path2 = Path(__file__).parent.parent / "global_policy_aggregator" / "data" / "seed_data" / "detailed_china_tech_policies.json"

        with open(path1, "r", encoding="utf-8") as f:
            data1 = json.load(f)
        with open(path2, "r", encoding="utf-8") as f:
            data2 = json.load(f)

        industries1 = set(p["industry"] for p in data1)
        industries2 = set(p["industry"] for p in data2)

        # They share some labels but also have unique ones
        # This documents the naming inconsistency
        only_in_1 = industries1 - industries2
        only_in_2 = industries2 - industries1

        assert len(only_in_1) > 0, "Seed data 1 should have unique labels"
        assert len(only_in_2) > 0, "Seed data 2 should have unique labels"

    def test_cleaning_service_has_separate_mapping(self):
        """Cleaning service has its own independent industry mapping"""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner

        cleaner = PolicyCleaner()
        parser_mapping = cleaner.industry_mapping

        # Cleaning service mapping (from china_policy_cleaning_service.py)
        # has 10 entries with different keys than parser
        cleaning_service_mapping = {
            "人工智能": "ai",
            "机器人": "robotics",
            "量子计算": "quantum_computing",
            "半导体": "semiconductor",
            "自动驾驶": "autonomous_driving",
            "具身智能": "embodied_ai",
            "生物技术": "biotech",
            "新能源": "new_energy",
            "新材料": "new_materials",
            "高端装备": "high_end_equipment",
        }

        # The two mappings have different CN keys
        parser_keys = set(parser_mapping.keys())
        cleaning_keys = set(cleaning_service_mapping.keys())

        # Cleaning service has keys not in parser
        assert "半导体" in cleaning_keys
        assert "半导体" not in parser_keys

        # Parser has keys not in cleaning service
        assert "虚拟现实" in parser_keys
        assert "虚拟现实" not in cleaning_keys


# ─────────────────────────────────────────────────────────
# T6: Taxonomy safety — no false unification claims
# ─────────────────────────────────────────────────────────

class TestTaxonomySafety:
    """Ensure no component falsely claims taxonomy unification"""

    def test_no_taxonomy_unification_claim_in_code(self):
        """No production code file should claim taxonomy is unified (audit guard)"""
        project_root = Path(__file__).parent.parent
        claim_patterns = [
            "taxonomy unified",
            "taxonomy统一",
            "行业分类已统一",
            "unified industry taxonomy",
        ]

        suspicious_files = []
        for py_file in project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            # Exclude this audit test file itself
            if py_file.name == "test_taxonomy_audit.py":
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                for pattern in claim_patterns:
                    if pattern.lower() in content.lower():
                        suspicious_files.append(str(py_file))
                        break
            except Exception:
                pass

        assert len(suspicious_files) == 0, (
            f"Found false taxonomy unification claims in: {suspicious_files}"
        )

    def test_landing_service_only_supports_3_industries(self):
        """Landing requirements service only has data for 3 industries"""
        from server.services.landing_requirements_service import LandingRequirementsService
        service = LandingRequirementsService()
        supported = service.get_supported_locations()  # This returns locations
        # Check industry_requirements directly
        assert len(service.industry_requirements) == 3
        assert set(service.industry_requirements.keys()) == {
            "autonomous_driving", "embodied_ai", "quantum_computing"
        }
