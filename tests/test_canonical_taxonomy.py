"""
P1-3.2 — Canonical Taxonomy Registry and Legacy Mapping Tests

Tests cover all 21 requirements from Section 13:
 1. canonical registry exists
 2. all canonical IDs unique
 3. all IDs snake_case
 4. required categories exist
 5. unknown exists
 6. other exists
 7. exact legacy mapping
 8. synonym mapping
 9. unknown handling
10. other handling
11. no silent guessing
12. legacy values remain resolvable
13. canonical → display name
14. invalid canonical ID rejection
15. mapping determinism
16. serialization
17. parser compatibility
18. 21-category legacy source mapping
19. 5-category schema mapping
20. 8-category parser mapping
21. 12-category web portal mapping

Quest: P1-3.2 — Implement Canonical Taxonomy Registry and Legacy Mapping Layer
"""

import re

import pytest

from schema.canonical_taxonomy import (
    CanonicalIndustry,
    CanonicalIndustryRegistry,
    LegacyMapping,
    MappingConfidence,
    get_registry,
)


@pytest.fixture
def registry():
    """Provide a fresh CanonicalIndustryRegistry instance."""
    return CanonicalIndustryRegistry()


# ============================================================
# 1. Canonical registry exists
# ============================================================
class TestRegistryExists:
    """TEST-TAXONOMY-IMPL-001: Canonical registry must exist and be functional."""

    def test_registry_class_exists(self):
        """CanonicalIndustryRegistry class must be importable."""
        assert CanonicalIndustryRegistry is not None

    def test_registry_instantiation(self):
        """Registry must be instantiable."""
        r = CanonicalIndustryRegistry()
        assert r is not None

    def test_singleton_accessor(self):
        """get_registry() must return a valid registry."""
        r = get_registry()
        assert isinstance(r, CanonicalIndustryRegistry)

    def test_registry_has_canonical_industries(self):
        """Registry must contain canonical industry entries."""
        r = CanonicalIndustryRegistry()
        assert r.canonical_count > 0


# ============================================================
# 2. All canonical IDs unique
# ============================================================
class TestCanonicalIDUniqueness:
    """TEST-TAXONOMY-IMPL-002: All canonical IDs must be unique."""

    def test_ids_are_unique(self, registry):
        """No duplicate canonical IDs."""
        ids = registry.list_ids()
        assert len(ids) == len(set(ids))

    def test_aliases_no_cross_contamination(self, registry):
        """No alias of one canonical ID should be the ID of another."""
        ids = set(registry.list_ids())
        for industry in registry.list():
            for alias in industry.aliases:
                assert alias not in ids or alias == industry.id, (
                    f"Alias '{alias}' of '{industry.id}' conflicts with another canonical ID"
                )


# ============================================================
# 3. All IDs snake_case
# ============================================================
class TestCanonicalIDFormat:
    """TEST-TAXONOMY-IMPL-003: All canonical IDs must be snake_case."""

    def test_all_ids_snake_case(self, registry):
        """Every canonical ID must be lowercase snake_case."""
        snake_case_pattern = re.compile(r'^[a-z][a-z0-9_]*$')
        for cid in registry.list_ids():
            assert snake_case_pattern.match(cid), (
                f"Canonical ID '{cid}' is not valid snake_case"
            )

    def test_no_spaces_in_ids(self, registry):
        """No canonical ID should contain spaces."""
        for cid in registry.list_ids():
            assert " " not in cid


# ============================================================
# 4. Required categories exist
# ============================================================
class TestRequiredCategories:
    """TEST-TAXONOMY-IMPL-004: All required canonical categories must exist."""

    REQUIRED_IDS = [
        "ai", "robotics", "embodied_ai", "quantum_computing",
        "semiconductor", "biotech", "autonomous_driving", "aerospace",
        "new_energy", "new_materials", "blockchain", "fintech",
        "high_end_equipment", "cybersecurity", "iot", "vr_ar",
    ]

    def test_all_required_categories_exist(self, registry):
        """All 16 required canonical categories must be present."""
        for cid in self.REQUIRED_IDS:
            assert registry.validate(cid), f"Required canonical ID '{cid}' not found"

    def test_active_count_is_16(self, registry):
        """Active (non-special) categories should be exactly 16."""
        assert registry.active_count == 16

    def test_total_count_includes_special(self, registry):
        """Total count should include other and unknown."""
        assert registry.canonical_count == 18


# ============================================================
# 5. unknown exists
# ============================================================
class TestUnknownCategory:
    """TEST-TAXONOMY-IMPL-005: 'unknown' category must exist."""

    def test_unknown_exists(self, registry):
        """'unknown' must be a valid canonical ID."""
        assert registry.validate("unknown")

    def test_unknown_is_special(self, registry):
        """'unknown' must have status='special'."""
        industry = registry.get("unknown")
        assert industry is not None
        assert industry.status == "special"

    def test_unknown_display_names(self, registry):
        """'unknown' must have proper display names."""
        industry = registry.get("unknown")
        assert industry.display_name_zh == "未知"
        assert industry.display_name_en == "Unknown"


# ============================================================
# 6. other exists
# ============================================================
class TestOtherCategory:
    """TEST-TAXONOMY-IMPL-006: 'other' category must exist."""

    def test_other_exists(self, registry):
        """'other' must be a valid canonical ID."""
        assert registry.validate("other")

    def test_other_is_special(self, registry):
        """'other' must have status='special'."""
        industry = registry.get("other")
        assert industry is not None
        assert industry.status == "special"

    def test_other_display_names(self, registry):
        """'other' must have proper display names."""
        industry = registry.get("other")
        assert industry.display_name_zh == "其他"
        assert industry.display_name_en == "Other"


# ============================================================
# 7. Exact legacy mapping
# ============================================================
class TestExactLegacyMapping:
    """TEST-TAXONOMY-IMPL-007: Known exact legacy mappings must resolve correctly."""

    EXACT_MAPPINGS = {
        # T1: Parser
        "ai": "ai",
        "robotics": "robotics",
        "quantum_computing": "quantum_computing",
        "biotech": "biotech",
        "autonomous_driving": "autonomous_driving",
        "blockchain": "blockchain",
        "vr_ar": "vr_ar",
        # T6: Cleaning Service
        "semiconductor": "semiconductor",
        "embodied_ai": "embodied_ai",
        "new_energy": "new_energy",
        "new_materials": "new_materials",
        "high_end_equipment": "high_end_equipment",
    }

    def test_exact_mappings_resolve(self, registry):
        """All exact legacy mappings must resolve to correct canonical ID."""
        for legacy, expected in self.EXACT_MAPPINGS.items():
            result = registry.resolve(legacy)
            assert result == expected, (
                f"Legacy '{legacy}' should resolve to '{expected}', got '{result}'"
            )

    def test_exact_mappings_have_exact_confidence(self, registry):
        """Exact mappings must have EXACT confidence."""
        for legacy in self.EXACT_MAPPINGS:
            confidence = registry.get_mapping_confidence(legacy)
            assert confidence == MappingConfidence.EXACT, (
                f"Legacy '{legacy}' should have EXACT confidence, got {confidence}"
            )


# ============================================================
# 8. Synonym mapping
# ============================================================
class TestSynonymMapping:
    """TEST-TAXONOMY-IMPL-008: Synonyms must normalize consistently."""

    SYNONYM_MAPPINGS = {
        "auto_driving": "autonomous_driving",
        "biotechnology": "biotech",
        "advanced_manufacturing": "high_end_equipment",
    }

    def test_synonyms_resolve(self, registry):
        """All known synonyms must resolve to correct canonical ID."""
        for synonym, expected in self.SYNONYM_MAPPINGS.items():
            result = registry.resolve(synonym)
            assert result == expected, (
                f"Synonym '{synonym}' should resolve to '{expected}', got '{result}'"
            )

    def test_synonyms_have_synonym_confidence(self, registry):
        """Synonym mappings must have SYNONYM confidence."""
        for synonym in self.SYNONYM_MAPPINGS:
            confidence = registry.get_mapping_confidence(synonym)
            assert confidence == MappingConfidence.SYNONYM

    def test_biotech_biotechnology_same_canonical(self, registry):
        """biotech and biotechnology must resolve to same canonical ID."""
        assert registry.resolve("biotech") == registry.resolve("biotechnology")

    def test_autonomous_driving_auto_driving_same_canonical(self, registry):
        """autonomous_driving and auto_driving must resolve to same canonical ID."""
        assert registry.resolve("autonomous_driving") == registry.resolve("auto_driving")


# ============================================================
# 9. Unknown handling
# ============================================================
class TestUnknownHandling:
    """TEST-TAXONOMY-IMPL-009: Unknown values must resolve to 'unknown', not a specific industry."""

    def test_ai_hardware_is_unknown(self, registry):
        """ai_hardware cannot be reliably mapped → unknown."""
        result = registry.resolve("ai_hardware")
        assert result == "unknown", (
            f"ai_hardware should resolve to 'unknown', got '{result}'"
        )

    def test_completely_unknown_value(self, registry):
        """Completely unknown string → unknown."""
        result = registry.resolve("xyzzy_industry_42")
        assert result == "unknown"

    def test_empty_string_is_unknown(self, registry):
        """Empty string → unknown."""
        assert registry.resolve("") == "unknown"

    def test_none_is_unknown(self, registry):
        """None → unknown."""
        assert registry.resolve(None) == "unknown"

    def test_whitespace_is_unknown(self, registry):
        """Whitespace-only string → unknown."""
        assert registry.resolve("   ") == "unknown"

    def test_unknown_has_unknown_confidence(self, registry):
        """Unknown values must have UNKNOWN confidence."""
        metadata = registry.resolve_with_metadata("ai_hardware")
        assert metadata.confidence == MappingConfidence.UNKNOWN


# ============================================================
# 10. Other handling
# ============================================================
class TestOtherHandling:
    """TEST-TAXONOMY-IMPL-010: 'other' is for confirmed industry but not specific category."""

    def test_parser_other_fallback(self, registry):
        """Parser 'other' value should resolve to canonical 'other'."""
        result = registry.resolve("other")
        assert result == "other"

    def test_other_is_not_unknown(self, registry):
        """'other' and 'unknown' must be distinct."""
        other = registry.get("other")
        unknown = registry.get("unknown")
        assert other.id != unknown.id

    def test_other_semantic_distinction(self, registry):
        """'other' means confirmed industry, 'unknown' means cannot determine."""
        other = registry.get("other")
        unknown = registry.get("unknown")
        assert "not in specific" in other.description.lower() or "confirmed" in other.description.lower()
        assert "cannot" in unknown.description.lower() or "no guessing" in unknown.description.lower()


# ============================================================
# 11. No silent guessing
# ============================================================
class TestNoSilentGuessing:
    """TEST-TAXONOMY-IMPL-011: Registry must never silently guess a mapping."""

    def test_unknown_industry_not_silently_mapped(self, registry):
        """An unrecognized industry must not silently become a specific category."""
        result = registry.resolve("underwater_basket_weaving")
        assert result == "unknown", (
            "Unknown industry should not be silently mapped to a specific category"
        )

    def test_resolve_with_metadata_shows_unknown(self, registry):
        """resolve_with_metadata must clearly indicate UNKNOWN for unrecognized values."""
        metadata = registry.resolve_with_metadata("nonexistent_industry")
        assert metadata.canonical_id == "unknown"
        assert metadata.confidence == MappingConfidence.UNKNOWN

    def test_no_ambiguous_semantic_mapping(self, registry):
        """ai_hardware must not be silently mapped to ai or semiconductor."""
        result = registry.resolve("ai_hardware")
        assert result not in ("ai", "semiconductor"), (
            "ai_hardware must not be silently mapped to ai or semiconductor"
        )


# ============================================================
# 12. Legacy values remain resolvable
# ============================================================
class TestLegacyResolvability:
    """TEST-TAXONOMY-IMPL-012: All known legacy values must remain resolvable."""

    def test_all_t1_parser_values_resolvable(self, registry):
        """All T1 parser output values must resolve."""
        t1_values = ["ai", "robotics", "quantum_computing", "biotech",
                     "autonomous_driving", "blockchain", "vr_ar", "other"]
        for v in t1_values:
            result = registry.resolve(v)
            assert result != "unknown", f"T1 value '{v}' should be resolvable"

    def test_all_t2_schema_values_resolvable(self, registry):
        """All T2 schema enum values must resolve."""
        t2_values = ["autonomous_driving", "embodied_ai", "robotics",
                     "ai_hardware", "quantum_computing"]
        for v in t2_values:
            result = registry.resolve(v)
            assert result is not None

    def test_all_t3_web_portal_values_resolvable(self, registry):
        """All T3 web portal CN labels must resolve."""
        t3_values = ["AI", "半导体", "自动驾驶", "量子计算", "区块链",
                     "生物科技", "高端装备", "航空航天", "新材料", "新能源",
                     "金融科技", "纳米技术"]
        for v in t3_values:
            result = registry.resolve(v)
            assert result != "unknown", f"T3 value '{v}' should be resolvable"

    def test_all_t10_deeptech_schema_values_resolvable(self, registry):
        """All 21 T10 deeptech schema values must resolve."""
        t10_values = [
            "ai_ml", "robotics", "quantum_computing", "biotech", "fintech",
            "cleantech", "aerospace", "semiconductor", "blockchain", "vr_ar",
            "nanotech", "space_tech", "embodied_ai", "autonomous_driving",
            "cybersecurity", "iot", "5g", "edge_computing", "metaverse",
            "web3", "digital_twin",
        ]
        for v in t10_values:
            result = registry.resolve(v)
            assert result is not None, f"T10 value '{v}' should be resolvable"


# ============================================================
# 13. Canonical → display name
# ============================================================
class TestDisplayNames:
    """TEST-TAXONOMY-IMPL-013: Canonical → display name mapping must work."""

    def test_english_display_name(self, registry):
        """get_display_name must return English name."""
        name = registry.get_display_name("ai", lang="en")
        assert name == "Artificial Intelligence"

    def test_chinese_display_name(self, registry):
        """get_display_name must return Chinese name."""
        name = registry.get_display_name("ai", lang="zh")
        assert name == "人工智能"

    def test_all_canonical_have_display_names(self, registry):
        """Every canonical industry must have both zh and en display names."""
        for industry in registry.list():
            assert industry.display_name_zh, f"{industry.id} missing zh name"
            assert industry.display_name_en, f"{industry.id} missing en name"

    def test_invalid_id_returns_none(self, registry):
        """Invalid canonical ID must return None for display name."""
        assert registry.get_display_name("nonexistent") is None


# ============================================================
# 14. Invalid canonical ID rejection
# ============================================================
class TestInvalidIDRejection:
    """TEST-TAXONOMY-IMPL-014: Invalid canonical IDs must be rejected."""

    def test_validate_rejects_invalid(self, registry):
        """validate() must return False for invalid IDs."""
        assert not registry.validate("nonexistent_industry")
        assert not registry.validate("")
        assert not registry.validate("AI_ML")  # case-sensitive

    def test_get_returns_none_for_invalid(self, registry):
        """get() must return None for invalid IDs."""
        assert registry.get("nonexistent") is None

    def test_map_legacy_rejects_unknown_source(self, registry):
        """map_legacy() must raise KeyError for unknown source IDs."""
        with pytest.raises(KeyError):
            registry.map_legacy("T99_nonexistent_source")


# ============================================================
# 15. Mapping determinism
# ============================================================
class TestMappingDeterminism:
    """TEST-TAXONOMY-IMPL-015: Same input must always produce same output."""

    def test_resolve_is_deterministic(self, registry):
        """resolve() must return same result for same input."""
        test_values = ["ai", "biotechnology", "auto_driving", "半导体", "ai_ml", "xyzzy"]
        for v in test_values:
            r1 = registry.resolve(v)
            r2 = registry.resolve(v)
            assert r1 == r2, f"resolve('{v}') is not deterministic"

    def test_resolve_with_metadata_is_deterministic(self, registry):
        """resolve_with_metadata() must return same canonical_id for same input."""
        test_values = ["ai", "biotechnology", "5g", "unknown_value"]
        for v in test_values:
            m1 = registry.resolve_with_metadata(v)
            m2 = registry.resolve_with_metadata(v)
            assert m1.canonical_id == m2.canonical_id
            assert m1.confidence == m2.confidence


# ============================================================
# 16. Serialization
# ============================================================
class TestSerialization:
    """TEST-TAXONOMY-IMPL-016: Registry data must be serializable."""

    def test_canonical_industry_is_frozen_dataclass(self, registry):
        """CanonicalIndustry must be a frozen dataclass (immutable)."""
        industry = registry.get("ai")
        assert industry is not None
        with pytest.raises(AttributeError):
            industry.id = "modified"

    def test_legacy_mapping_is_frozen(self, registry):
        """LegacyMapping must be a frozen dataclass."""
        mapping = registry.resolve_with_metadata("ai")
        with pytest.raises(AttributeError):
            mapping.canonical_id = "modified"

    def test_list_ids_returns_list(self, registry):
        """list_ids() must return a proper list."""
        ids = registry.list_ids()
        assert isinstance(ids, list)
        assert len(ids) == 18

    def test_all_mappings_returns_list(self, registry):
        """get_all_mappings() must return a list of LegacyMapping."""
        mappings = registry.get_all_mappings()
        assert isinstance(mappings, list)
        assert all(isinstance(m, LegacyMapping) for m in mappings)
        assert len(mappings) > 0


# ============================================================
# 17. Parser compatibility
# ============================================================
class TestParserCompatibility:
    """TEST-TAXONOMY-IMPL-017: Registry must be compatible with existing parser."""

    def test_parser_mapping_values_resolvable(self, registry):
        """All parser industry_mapping output values must be resolvable."""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        for cn_key, en_value in cleaner.industry_mapping.items():
            canonical = registry.resolve(en_value)
            assert canonical is not None, (
                f"Parser output '{en_value}' (from '{cn_key}') not resolvable"
            )

    def test_parser_output_not_broken(self, registry):
        """Parser must still work independently of registry."""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        assert len(cleaner.industry_mapping) == 10


# ============================================================
# 18. 21-category legacy source mapping
# ============================================================
class Test21CategoryMapping:
    """TEST-TAXONOMY-IMPL-018: All 21 deeptech schema values must be mapped."""

    T10_VALUES = [
        "ai_ml", "robotics", "quantum_computing", "biotech", "fintech",
        "cleantech", "aerospace", "semiconductor", "blockchain", "vr_ar",
        "nanotech", "space_tech", "embodied_ai", "autonomous_driving",
        "cybersecurity", "iot", "5g", "edge_computing", "metaverse",
        "web3", "digital_twin",
    ]

    def test_all_21_values_mapped(self, registry):
        """Every one of the 21 deeptech schema values must have a canonical mapping."""
        mapping = registry.map_legacy("T10_deeptech_schema")
        for val in self.T10_VALUES:
            assert val in mapping, f"T10 value '{val}' not in mapping"
            assert mapping[val] != "", f"T10 value '{val}' has empty mapping"

    def test_21_values_resolve_correctly(self, registry):
        """All 21 values must resolve via registry.resolve()."""
        for val in self.T10_VALUES:
            result = registry.resolve(val)
            assert result is not None
            assert registry.validate(result), (
                f"T10 value '{val}' resolved to invalid canonical ID '{result}'"
            )

    def test_21_source_has_21_entries(self, registry):
        """T10 source must have exactly 21 entries."""
        mapping = registry.map_legacy("T10_deeptech_schema")
        assert len(mapping) == 21


# ============================================================
# 19. 5-category schema mapping
# ============================================================
class Test5CategorySchemaMapping:
    """TEST-TAXONOMY-IMPL-019: All 5 schema IndustryType values must be mapped."""

    def test_schema_source_has_5_entries(self, registry):
        """T2 source must have exactly 5 entries."""
        mapping = registry.map_legacy("T2_schema")
        assert len(mapping) == 5

    def test_schema_values_resolve(self, registry):
        """All 5 schema values must resolve to valid canonical IDs."""
        schema_values = ["autonomous_driving", "embodied_ai", "robotics",
                         "ai_hardware", "quantum_computing"]
        for val in schema_values:
            result = registry.resolve(val)
            assert registry.validate(result), (
                f"Schema value '{val}' resolved to invalid ID '{result}'"
            )


# ============================================================
# 20. 8-category parser mapping
# ============================================================
class Test8CategoryParserMapping:
    """TEST-TAXONOMY-IMPL-020: All 8 parser output values must be mapped."""

    def test_parser_source_has_8_entries(self, registry):
        """T1 source must have exactly 8 unique output values."""
        mapping = registry.map_legacy("T1_parser")
        unique_canonical = set(mapping.values())
        assert len(unique_canonical) == 8

    def test_parser_values_resolve(self, registry):
        """All parser output values must resolve."""
        parser_values = ["ai", "robotics", "quantum_computing", "biotech",
                         "autonomous_driving", "blockchain", "vr_ar", "other"]
        for val in parser_values:
            result = registry.resolve(val)
            assert result == val, (
                f"Parser value '{val}' should resolve to itself, got '{result}'"
            )


# ============================================================
# 21. 12-category web portal mapping
# ============================================================
class Test12CategoryWebPortalMapping:
    """TEST-TAXONOMY-IMPL-021: All 12 web portal CN labels must be mapped."""

    def test_web_portal_source_has_12_entries(self, registry):
        """T3 source must have exactly 12 entries."""
        mapping = registry.map_legacy("T3_web_portal")
        assert len(mapping) == 12

    def test_web_portal_values_resolve(self, registry):
        """All 12 web portal CN labels must resolve to valid canonical IDs."""
        cn_labels = ["AI", "半导体", "自动驾驶", "量子计算", "区块链",
                     "生物科技", "高端装备", "航空航天", "新材料", "新能源",
                     "金融科技", "纳米技术"]
        for label in cn_labels:
            result = registry.resolve(label)
            assert registry.validate(result), (
                f"Web portal label '{label}' resolved to invalid ID '{result}'"
            )
            assert result != "unknown", (
                f"Web portal label '{label}' should not resolve to unknown"
            )


# ============================================================
# Safety gates
# ============================================================
class TestSafetyGates:
    """Safety gates: no false claims, no trust modification."""

    def test_registry_does_not_modify_trust(self, registry):
        """Registry must not import or depend on trust infrastructure."""
        import inspect
        source = inspect.getsource(CanonicalIndustryRegistry)
        assert "trust_score" not in source.lower()
        assert "provenance" not in source.lower()
        assert "evidence_object" not in source.lower()

    def test_registry_does_not_claim_production(self, registry):
        """Registry must not claim production readiness."""
        import inspect
        source = inspect.getsource(CanonicalIndustryRegistry)
        assert "production" not in source.lower()

    def test_legacy_source_count(self, registry):
        """Registry must track all 10 legacy sources."""
        assert registry.legacy_source_count == 10
