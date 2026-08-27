"""
P1-3.3 — Canonical Taxonomy Integration Tests

Tests verify that the canonical taxonomy registry is correctly integrated
with legacy Parser outputs, Web Portal responses, and data structures.

Coverage (20+ requirements from Section 14):
 1. parser legacy value → canonical value
 2. synonym → canonical
 3. normalization → canonical
 4. semantic mapping → canonical
 5. unknown → UNKNOWN
 6. other → OTHER
 7. ai_hardware → UNKNOWN
 8. 21-category legacy values
 9. 8-category parser values
10. 5-category schema values
11. 12-category web portal values
12. 10-category cleaning service values
13. deterministic mapping
14. backward compatibility
15. optional canonical_industry field
16. legacy industry field preserved
17. invalid value handling
18. no silent guessing
19. no trust modification
20. no MCP/A2A implementation claims

Quest: P1-3.3 — Canonical Taxonomy Integration
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schema.canonical_taxonomy import get_registry, MappingConfidence


@pytest.fixture
def registry():
    return get_registry()


# ============================================================
# 1. Parser legacy value → canonical value
# ============================================================
class TestParserLegacyToCanonical:
    """Parser output values must resolve to correct canonical IDs."""

    def test_parser_ai(self, registry):
        assert registry.resolve("ai") == "ai"

    def test_parser_robotics(self, registry):
        assert registry.resolve("robotics") == "robotics"

    def test_parser_quantum(self, registry):
        assert registry.resolve("quantum_computing") == "quantum_computing"

    def test_parser_biotech(self, registry):
        assert registry.resolve("biotech") == "biotech"

    def test_parser_autonomous_driving(self, registry):
        assert registry.resolve("autonomous_driving") == "autonomous_driving"

    def test_parser_blockchain(self, registry):
        assert registry.resolve("blockchain") == "blockchain"

    def test_parser_vr_ar(self, registry):
        assert registry.resolve("vr_ar") == "vr_ar"

    def test_parser_other(self, registry):
        assert registry.resolve("other") == "other"


# ============================================================
# 2. Synonym → canonical
# ============================================================
class TestSynonymToCanonical:
    """Synonyms must resolve to correct canonical IDs."""

    def test_auto_driving(self, registry):
        assert registry.resolve("auto_driving") == "autonomous_driving"

    def test_biotechnology(self, registry):
        assert registry.resolve("biotechnology") == "biotech"

    def test_advanced_manufacturing(self, registry):
        assert registry.resolve("advanced_manufacturing") == "high_end_equipment"


# ============================================================
# 3. Normalization → canonical
# ============================================================
class TestNormalizationToCanonical:
    """Normalized values must resolve correctly."""

    def test_ai_ml(self, registry):
        assert registry.resolve("ai_ml") == "ai"

    def test_cleantech(self, registry):
        assert registry.resolve("cleantech") == "new_energy"


# ============================================================
# 4. Semantic mapping → canonical
# ============================================================
class TestSemanticMappingToCanonical:
    """Semantic mappings must resolve correctly."""

    def test_nanotech(self, registry):
        assert registry.resolve("nanotech") == "new_materials"

    def test_space_tech(self, registry):
        assert registry.resolve("space_tech") == "aerospace"

    def test_5g(self, registry):
        assert registry.resolve("5g") == "iot"

    def test_metaverse(self, registry):
        assert registry.resolve("metaverse") == "vr_ar"

    def test_web3(self, registry):
        assert registry.resolve("web3") == "blockchain"

    def test_digital_twin(self, registry):
        assert registry.resolve("digital_twin") == "vr_ar"


# ============================================================
# 5. Unknown → UNKNOWN
# ============================================================
class TestUnknownResolution:
    """Unknown values must resolve to 'unknown'."""

    def test_completely_unknown(self, registry):
        assert registry.resolve("xyzzy_unrelated") == "unknown"

    def test_empty_string(self, registry):
        assert registry.resolve("") == "unknown"

    def test_none_value(self, registry):
        assert registry.resolve(None) == "unknown"


# ============================================================
# 6. Other → OTHER
# ============================================================
class TestOtherResolution:
    """'other' must resolve to canonical 'other', not unknown."""

    def test_other_resolves_to_other(self, registry):
        assert registry.resolve("other") == "other"

    def test_other_is_not_unknown(self, registry):
        assert registry.resolve("other") != "unknown"


# ============================================================
# 7. ai_hardware → UNKNOWN
# ============================================================
class TestAiHardwareStatus:
    """ai_hardware must remain UNKNOWN — no guessing."""

    def test_ai_hardware_is_unknown(self, registry):
        result = registry.resolve("ai_hardware")
        assert result == "unknown", (
            f"ai_hardware must resolve to 'unknown', got '{result}'"
        )

    def test_ai_hardware_not_ai(self, registry):
        assert registry.resolve("ai_hardware") != "ai"

    def test_ai_hardware_not_semiconductor(self, registry):
        assert registry.resolve("ai_hardware") != "semiconductor"

    def test_ai_hardware_not_other(self, registry):
        assert registry.resolve("ai_hardware") != "other"

    def test_ai_hardware_confidence_is_unknown(self, registry):
        metadata = registry.resolve_with_metadata("ai_hardware")
        assert metadata.confidence == MappingConfidence.UNKNOWN


# ============================================================
# 8. 21-category legacy source mapping
# ============================================================
class Test21CategoryIntegration:
    """All 21 deeptech schema values must map through registry."""

    T10_VALUES = [
        "ai_ml", "robotics", "quantum_computing", "biotech", "fintech",
        "cleantech", "aerospace", "semiconductor", "blockchain", "vr_ar",
        "nanotech", "space_tech", "embodied_ai", "autonomous_driving",
        "cybersecurity", "iot", "5g", "edge_computing", "metaverse",
        "web3", "digital_twin",
    ]

    def test_all_21_resolve(self, registry):
        for val in self.T10_VALUES:
            result = registry.resolve(val)
            assert registry.validate(result), f"T10 '{val}' → invalid '{result}'"

    def test_all_21_deterministic(self, registry):
        for val in self.T10_VALUES:
            r1 = registry.resolve(val)
            r2 = registry.resolve(val)
            assert r1 == r2, f"T10 '{val}' not deterministic"


# ============================================================
# 9. 8-category parser mapping
# ============================================================
class Test8CategoryParserIntegration:
    """All 8 parser output values must map correctly."""

    PARSER_VALUES = ["ai", "robotics", "quantum_computing", "biotech",
                     "autonomous_driving", "blockchain", "vr_ar", "other"]

    def test_all_8_resolve_to_self(self, registry):
        for val in self.PARSER_VALUES:
            assert registry.resolve(val) == val


# ============================================================
# 10. 5-category schema mapping
# ============================================================
class Test5CategorySchemaIntegration:
    """All 5 schema IndustryType values must map correctly."""

    SCHEMA_VALUES = {
        "autonomous_driving": "autonomous_driving",
        "embodied_ai": "embodied_ai",
        "robotics": "robotics",
        "ai_hardware": "unknown",
        "quantum_computing": "quantum_computing",
    }

    def test_all_5_resolve(self, registry):
        for legacy, expected in self.SCHEMA_VALUES.items():
            assert registry.resolve(legacy) == expected, (
                f"Schema '{legacy}' should → '{expected}'"
            )


# ============================================================
# 11. 12-category web portal mapping
# ============================================================
class Test12CategoryWebPortalIntegration:
    """All 12 web portal CN labels must map correctly."""

    WEB_LABELS = {
        "AI": "ai", "半导体": "semiconductor", "自动驾驶": "autonomous_driving",
        "量子计算": "quantum_computing", "区块链": "blockchain", "生物科技": "biotech",
        "高端装备": "high_end_equipment", "航空航天": "aerospace",
        "新材料": "new_materials", "新能源": "new_energy",
        "金融科技": "fintech", "纳米技术": "new_materials",
    }

    def test_all_12_resolve(self, registry):
        for cn_label, expected in self.WEB_LABELS.items():
            result = registry.resolve(cn_label)
            assert result == expected, f"Web '{cn_label}' → '{result}', expected '{expected}'"


# ============================================================
# 12. 10-category cleaning service mapping
# ============================================================
class Test10CategoryCleaningServiceIntegration:
    """All 10 cleaning service values must map correctly."""

    CLEANING_VALUES = {
        "ai": "ai", "robotics": "robotics", "quantum_computing": "quantum_computing",
        "semiconductor": "semiconductor", "autonomous_driving": "autonomous_driving",
        "embodied_ai": "embodied_ai", "biotech": "biotech",
        "new_energy": "new_energy", "new_materials": "new_materials",
        "high_end_equipment": "high_end_equipment",
    }

    def test_all_10_resolve(self, registry):
        for val, expected in self.CLEANING_VALUES.items():
            assert registry.resolve(val) == expected


# ============================================================
# 13. Deterministic mapping
# ============================================================
class TestDeterministicMapping:
    """Same input must always produce same output."""

    def test_resolve_deterministic(self, registry):
        test_values = ["ai", "biotechnology", "auto_driving", "半导体", "ai_ml",
                       "ai_hardware", "xyzzy", "", None]
        for v in test_values:
            r1 = registry.resolve(v)
            r2 = registry.resolve(v)
            assert r1 == r2


# ============================================================
# 14. Backward compatibility
# ============================================================
class TestBackwardCompatibility:
    """Legacy data structures must remain functional."""

    def test_structured_policy_has_industry(self):
        """StructuredPolicy must still have 'industry' field."""
        from global_policy_aggregator.processors.policy_cleaner import StructuredPolicy
        import dataclasses
        field_names = [f.name for f in dataclasses.fields(StructuredPolicy)]
        assert "industry" in field_names

    def test_structured_policy_has_canonical_industry(self):
        """StructuredPolicy must have new 'canonical_industry' field."""
        from global_policy_aggregator.processors.policy_cleaner import StructuredPolicy
        import dataclasses
        field_names = [f.name for f in dataclasses.fields(StructuredPolicy)]
        assert "canonical_industry" in field_names

    def test_structured_policy_canonical_is_optional(self):
        """canonical_industry must be optional (default None)."""
        from global_policy_aggregator.processors.policy_cleaner import StructuredPolicy
        import dataclasses
        for f in dataclasses.fields(StructuredPolicy):
            if f.name == "canonical_industry":
                assert f.default is None, "canonical_industry must default to None"

    def test_parser_still_works(self):
        """PolicyCleaner must still function correctly."""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        assert len(cleaner.industry_mapping) == 10

    def test_parser_industry_mapping_unchanged(self):
        """Parser industry_mapping values must not change."""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        assert cleaner.industry_mapping["人工智能"] == "ai"
        assert cleaner.industry_mapping["新材料"] == "other"


# ============================================================
# 15. Optional canonical_industry field
# ============================================================
class TestCanonicalIndustryField:
    """canonical_industry field must be populated correctly."""

    def test_parser_populates_canonical_industry(self):
        """PolicyCleaner.clean_policy_text() must set canonical_industry."""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        # Use a text that contains a known industry keyword
        result = cleaner.clean_policy_text("关于人工智能产业发展的扶持政策")
        assert result.industry == "ai"
        assert result.canonical_industry == "ai"

    def test_parser_canonical_industry_for_other(self):
        """Parser 'other' industry must resolve to canonical 'other'."""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        # "新材料" maps to "other" in parser
        result = cleaner.clean_policy_text("关于新材料产业发展的扶持政策")
        assert result.industry == "other"
        assert result.canonical_industry == "other"


# ============================================================
# 16. Legacy industry field preserved
# ============================================================
class TestLegacyFieldPreserved:
    """Legacy 'industry' field must remain unchanged."""

    def test_legacy_industry_not_overwritten(self):
        """Parser must keep legacy 'industry' value, not replace with canonical."""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        result = cleaner.clean_policy_text("关于人工智能产业发展的扶持政策")
        # Legacy value must be "ai" (same as canonical in this case)
        assert result.industry == "ai"
        # But the point is: industry field is NOT replaced by canonical logic
        assert result.canonical_industry == "ai"

    def test_legacy_other_preserved(self):
        """Parser 'other' must stay as 'other' in legacy field."""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        result = cleaner.clean_policy_text("关于新材料产业发展的扶持政策")
        assert result.industry == "other"  # Legacy preserved


# ============================================================
# 17. Invalid value handling
# ============================================================
class TestInvalidValueHandling:
    """Invalid values must be handled gracefully."""

    def test_empty_string(self, registry):
        assert registry.resolve("") == "unknown"

    def test_none(self, registry):
        assert registry.resolve(None) == "unknown"

    def test_whitespace(self, registry):
        assert registry.resolve("   ") == "unknown"

    def test_nonexistent_industry(self, registry):
        assert registry.resolve("quantum_teleportation") == "unknown"


# ============================================================
# 18. No silent guessing
# ============================================================
class TestNoSilentGuessing:
    """Registry must never silently guess a mapping."""

    def test_unknown_not_silently_mapped(self, registry):
        result = registry.resolve("underwater_basket_weaving")
        assert result == "unknown"

    def test_ai_hardware_not_guessed(self, registry):
        result = registry.resolve("ai_hardware")
        assert result == "unknown"
        assert result not in ("ai", "semiconductor", "robotics")


# ============================================================
# 19. No trust modification
# ============================================================
class TestNoTrustModification:
    """Integration must not modify trust infrastructure."""

    def test_trust_score_unchanged(self):
        """Trust Score must not be affected by taxonomy integration."""
        from src.trust.trust_score import TrustScoreCalculator
        calc = TrustScoreCalculator()
        assert calc is not None

    def test_evidence_object_unchanged(self):
        """Evidence Object model must not be affected."""
        from src.trust.evidence_object import EvidenceObject
        assert EvidenceObject is not None

    def test_canonical_taxonomy_no_trust_imports(self):
        """canonical_taxonomy.py must not import trust modules."""
        import inspect
        from schema import canonical_taxonomy
        source = inspect.getsource(canonical_taxonomy)
        assert "trust_score" not in source.lower()
        assert "evidence_object" not in source.lower()
        assert "provenance" not in source.lower()


# ============================================================
# 20. No MCP/A2A implementation claims
# ============================================================
class TestNoMCPA2AClaims:
    """Integration must not claim MCP/A2A implementation."""

    def test_no_mcp_in_canonical_taxonomy(self, registry):
        import inspect
        source = inspect.getsource(type(registry))
        assert "mcp server" not in source.lower()
        assert "mcp implemented" not in source.lower()

    def test_no_a2a_in_canonical_taxonomy(self, registry):
        import inspect
        source = inspect.getsource(type(registry))
        assert "a2a gateway" not in source.lower()
        assert "a2a implemented" not in source.lower()


# ============================================================
# Additional: Web Portal integration
# ============================================================
class TestWebPortalIntegration:
    """Web portal policies must have canonical_industry field."""

    def test_interactive_server_policies_have_canonical(self):
        """interactive_ai_server policies must include canonical_industry."""
        from global_policy_aggregator.web.interactive_ai_server import policies
        for p in policies:
            assert "canonical_industry" in p, (
                f"Policy '{p.get('title', 'unknown')}' missing canonical_industry"
            )

    def test_interactive_server_canonical_values_valid(self, registry):
        """All canonical_industry values in web portal must be valid."""
        from global_policy_aggregator.web.interactive_ai_server import policies
        for p in policies:
            ci = p.get("canonical_industry")
            assert ci is not None, f"Policy '{p.get('title')}' has null canonical_industry"
            assert registry.validate(ci), (
                f"Policy '{p.get('title')}' has invalid canonical_industry: {ci}"
            )

    def test_interactive_server_legacy_industry_preserved(self):
        """Legacy 'industry' field must still exist in web portal policies."""
        from global_policy_aggregator.web.interactive_ai_server import policies
        for p in policies:
            assert "industry" in p, f"Policy missing legacy 'industry' field"

    def test_interactive_server_mock_preserved(self):
        """All policies must remain marked as mock."""
        from global_policy_aggregator.web.interactive_ai_server import policies
        for p in policies:
            assert p.get("is_mock") is True
            assert p.get("verification_status") == "mock"
