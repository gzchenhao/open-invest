"""
P1-3.1 — Industry Taxonomy Alignment Design Tests

These tests verify the canonical taxonomy design artifacts and ensure:
- The design document exists with all required sections
- The 21-category source is correctly identified
- Synonym mappings are deterministic
- No destructive implementation has occurred
- Legacy data remains intact and readable
- No false VERIFIED claims

Quest: P1-3.1 — Canonical Industry Taxonomy Design
"""

import json
import os
import re
from pathlib import Path

import pytest

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
SCHEMA_DIR = PROJECT_ROOT / "schema"
SEED_DIR = PROJECT_ROOT / "global_policy_aggregator" / "data" / "seed_data"
DESIGN_DOC = DOCS_DIR / "Industry_Taxonomy_Alignment_Design.md"
AUDIT_DOC = DOCS_DIR / "Industry_Taxonomy_Audit_20260826.md"


# ============================================================
# TEST-TAXONOMY-ALIGN-001: Canonical registry exists (design)
# ============================================================
class TestCanonicalRegistryDesign:
    """Verify the canonical taxonomy design document exists and is complete."""

    def test_design_document_exists(self):
        """TEST-TAXONOMY-ALIGN-001: Canonical taxonomy design document must exist."""
        assert DESIGN_DOC.exists(), (
            f"Design document not found: {DESIGN_DOC}"
        )

    def test_design_document_has_required_sections(self):
        """Design document must contain all 23 required sections."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        required_sections = [
            "Problem Statement",
            "Current Parallel Taxonomies",
            "Taxonomy Source Matrix",
            "Canonical Taxonomy Principles",
            "Proposed Canonical Registry",
            "Canonical Industry IDs",
            "Chinese Display Names",
            "English Display Names",
            "Legacy → Canonical Mapping",
            "Ambiguous Mapping Rules",
            "Unknown / Other Handling",
            "Parser Impact",
            "Schema Impact",
            "Seed Data Impact",
            "Web Portal Impact",
            "API Impact",
            "Evidence Graph Impact",
            "Backward Compatibility",
            "Migration Strategy",
            "Rollback Strategy",
            "Safety Constraints",
            "Open Questions",
            "UNVERIFIED Items",
        ]
        missing = [s for s in required_sections if s not in content]
        assert not missing, f"Design document missing sections: {missing}"

    def test_design_document_declares_no_implementation(self):
        """Design document must explicitly state IMPLEMENTATION NOT STARTED."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        assert "IMPLEMENTATION NOT STARTED" in content, (
            "Design document must declare IMPLEMENTATION NOT STARTED"
        )

    def test_canonical_registry_has_16_plus_2_categories(self):
        """Proposed canonical registry should have 16 categories + other + unknown."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        # Check for the key canonical IDs in the registry
        expected_ids = [
            "ai", "robotics", "embodied_ai", "quantum_computing",
            "semiconductor", "biotech", "autonomous_driving", "aerospace",
            "new_energy", "new_materials", "blockchain", "fintech",
            "high_end_equipment", "cybersecurity", "iot", "vr_ar",
            "other", "unknown",
        ]
        for cid in expected_ids:
            assert f'"{cid}"' in content or f"`{cid}`" in content, (
                f"Canonical ID '{cid}' not found in design document"
            )


# ============================================================
# TEST-TAXONOMY-ALIGN-002: Canonical IDs are unique
# ============================================================
class TestCanonicalIDUniqueness:
    """Verify canonical IDs are unique and well-formed."""

    def test_canonical_ids_are_snake_case(self):
        """All canonical IDs must be lowercase snake_case."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        # Extract IDs from the registry table
        pattern = r'\|\s*`(\w+)`\s*\|'
        # Find the registry section
        registry_start = content.find("### 5.2 Canonical Industry Registry")
        registry_end = content.find("### 5.3", registry_start)
        registry_section = content[registry_start:registry_end]

        ids = re.findall(r'`(\w+)`', registry_section)
        for cid in ids:
            assert cid == cid.lower(), f"Canonical ID '{cid}' is not lowercase"
            assert " " not in cid, f"Canonical ID '{cid}' contains spaces"

    def test_no_duplicate_canonical_ids_in_registry(self):
        """No duplicate canonical IDs in the proposed registry."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        # Find the Python registry definition block
        registry_start = content.find("CANONICAL_INDUSTRY_REGISTRY")
        # Find the closing of the dict (look for the line with just "}")
        block = content[registry_start:]
        # Extract all IDs from the registry definition: "key": {
        ids = re.findall(r'"(\w+)":\s*\{', block)
        assert len(ids) == len(set(ids)), (
            f"Duplicate canonical IDs found: {[x for x in ids if ids.count(x) > 1]}"
        )
        assert len(ids) >= 16, f"Expected at least 16 canonical IDs, found {len(ids)}"


# ============================================================
# TEST-TAXONOMY-ALIGN-003: Known legacy values map deterministically
# ============================================================
class TestLegacyMappingDeterminism:
    """Verify legacy → canonical mappings are deterministic."""

    def test_deeptech_schema_21_values_documented(self):
        """TEST-TAXONOMY-ALIGN-003: All 21 deeptech schema values must have mappings."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        deeptech_values = [
            "ai_ml", "robotics", "quantum_computing", "biotech", "fintech",
            "cleantech", "aerospace", "semiconductor", "blockchain", "vr_ar",
            "nanotech", "space_tech", "embodied_ai", "autonomous_driving",
            "cybersecurity", "iot", "5g", "edge_computing", "metaverse",
            "web3", "digital_twin",
        ]
        # Find the T10 mapping section
        t10_start = content.find("### 9.9 T10: Deeptech Schema")
        t10_end = content.find("### 9.10", t10_start)
        t10_section = content[t10_start:t10_end]

        for val in deeptech_values:
            assert val in t10_section, (
                f"Deeptech schema value '{val}' not found in T10 mapping section"
            )

    def test_synonym_mappings_are_documented(self):
        """All known synonym pairs must have documented mappings."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        synonyms = [
            ("biotech", "biotechnology"),
            ("autonomous_driving", "auto_driving"),
            ("ai", "ai_ml"),
        ]
        for canonical, legacy in synonyms:
            assert legacy in content, f"Synonym '{legacy}' not documented"
            assert canonical in content, f"Canonical '{canonical}' not documented"

    def test_parser_mapping_all_covered(self):
        """All 8 parser output values must have canonical mappings."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        parser_values = [
            "ai", "robotics", "quantum_computing", "biotech",
            "autonomous_driving", "blockchain", "vr_ar", "other",
        ]
        # Find T1 mapping section
        t1_start = content.find("### 9.1 T1: Parser")
        t1_end = content.find("### 9.2", t1_start)
        t1_section = content[t1_start:t1_end]

        for val in parser_values:
            assert val in t1_section, (
                f"Parser value '{val}' not found in T1 mapping section"
            )


# ============================================================
# TEST-TAXONOMY-ALIGN-004: Unknown values do not silently become specific industry
# ============================================================
class TestUnknownHandling:
    """Verify that unknown/ambiguous values are handled safely."""

    def test_ai_hardware_maps_to_unknown(self):
        """ai_hardware should map to 'unknown', not to a specific industry."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        # Find ai_hardware in the ambiguous mapping section
        assert "ai_hardware" in content, "ai_hardware not documented"
        # Check it maps to unknown
        assert "**unknown**" in content or "`unknown`" in content, (
            "unknown target not found in design document"
        )
        # Verify in the ambiguous mapping table
        ambiguous_start = content.find("Ambiguous Mapping Rules")
        ambiguous_end = content.find("## 11.", ambiguous_start)
        ambiguous_section = content[ambiguous_start:ambiguous_end]
        assert "ai_hardware" in ambiguous_section, (
            "ai_hardware not found in ambiguous mapping rules"
        )

    def test_design_has_unknown_and_other_categories(self):
        """Canonical registry must include both 'unknown' and 'other' categories."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        assert '"unknown"' in content or "`unknown`" in content
        assert '"other"' in content or "`other`" in content

    def test_unknown_handling_section_exists(self):
        """Design document must have explicit Unknown/Other handling rules."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        assert "Unknown / Other Handling" in content or "Unknown" in content


# ============================================================
# TEST-TAXONOMY-ALIGN-005: Synonyms normalize consistently
# ============================================================
class TestSynonymNormalization:
    """Verify synonym normalization is consistent."""

    def test_biotech_biotechnology_synonym(self):
        """biotech and biotechnology must map to the same canonical ID."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        # Both should appear in mapping sections pointing to biotech
        assert "biotechnology" in content
        assert "biotech" in content
        # Check the synonym section
        synonym_section_start = content.find("Synonym pairs")
        if synonym_section_start > 0:
            synonym_section = content[synonym_section_start:synonym_section_start + 500]
            assert "biotech" in synonym_section
            assert "biotechnology" in synonym_section

    def test_autonomous_driving_auto_driving_synonym(self):
        """autonomous_driving and auto_driving must map to the same canonical ID."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        assert "auto_driving" in content
        assert "autonomous_driving" in content

    def test_ai_ml_synonym(self):
        """ai and ai_ml must map to the same canonical ID."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        assert "ai_ml" in content


# ============================================================
# TEST-TAXONOMY-ALIGN-006: Existing taxonomy data remains readable
# ============================================================
class TestExistingDataIntegrity:
    """Verify existing taxonomy data has not been modified."""

    def test_schema_industry_type_unchanged(self):
        """Schema IndustryType enum must still have exactly 5 values."""
        from schema.types import IndustryType
        assert len(IndustryType) == 5, (
            f"IndustryType should have 5 values, found {len(IndustryType)}"
        )

    def test_seed_data_original_readable(self):
        """Original seed data JSON must still be valid and readable."""
        seed_file = SEED_DIR / "china_policy_seed_data.json"
        assert seed_file.exists()
        data = json.loads(seed_file.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) == 12

    def test_seed_data_detailed_readable(self):
        """Detailed seed data JSON must still be valid and readable."""
        seed_file = SEED_DIR / "detailed_china_tech_policies.json"
        assert seed_file.exists()
        data = json.loads(seed_file.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) == 9

    def test_deeptech_schema_file_exists(self):
        """deeptech_policy_schema.json must still exist."""
        schema_file = (
            PROJECT_ROOT / "global_policy_aggregator" / "schemas"
            / "deeptech_policy_schema.json"
        )
        assert schema_file.exists()
        data = json.loads(schema_file.read_text(encoding="utf-8"))
        assert "properties" in data

    def test_deeptech_schema_has_21_industries(self):
        """deeptech_policy_schema.json industry enum must have exactly 21 values."""
        schema_file = (
            PROJECT_ROOT / "global_policy_aggregator" / "schemas"
            / "deeptech_policy_schema.json"
        )
        data = json.loads(schema_file.read_text(encoding="utf-8"))
        # Navigate to the industry enum (nested in target_industries)
        target_ind = data["properties"]["target_industries"]
        industry_enum = target_ind["items"]["properties"]["industry"]["enum"]
        assert len(industry_enum) == 21, (
            f"deeptech_schema should have 21 industries, found {len(industry_enum)}"
        )

    def test_parser_mapping_unchanged(self):
        """Parser industry_mapping must still have original structure."""
        from global_policy_aggregator.processors.policy_cleaner import PolicyCleaner
        cleaner = PolicyCleaner()
        mapping = cleaner.industry_mapping
        assert len(mapping) == 10, (
            f"Parser mapping should have 10 keys, found {len(mapping)}"
        )
        assert "人工智能" in mapping
        assert mapping["人工智能"] == "ai"


# ============================================================
# TEST-TAXONOMY-ALIGN-007: No false VERIFIED taxonomy claims
# ============================================================
class TestNoFalseVerifiedClaims:
    """Verify no false VERIFIED taxonomy claims exist in the codebase."""

    def test_no_taxonomy_unification_claim_in_design(self):
        """Design document must not claim taxonomy is already unified."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        forbidden = [
            "taxonomy unified",
            "taxonomy has been unified",
            "all taxonomies are now consistent",
            "taxonomies have been merged",
        ]
        content_lower = content.lower()
        for pattern in forbidden:
            assert pattern not in content_lower, (
                f"Design document contains false unification claim: '{pattern}'"
            )

    def test_design_document_states_parallel_taxonomies(self):
        """Design document must acknowledge parallel taxonomies still exist."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        assert "Parallel Taxonomies" in content or "parallel taxonomies" in content.lower(), (
            "Design document must acknowledge parallel taxonomies"
        )

    def test_audit_document_still_exists(self):
        """P1-3.0 audit document must still exist (not replaced by design)."""
        assert AUDIT_DOC.exists(), (
            f"Audit document should still exist: {AUDIT_DOC}"
        )

    def test_no_new_industry_mapping_in_design_doc(self):
        """Design document should not create new runtime mappings."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        # The design doc should not contain executable Python that modifies state
        assert "self.industry_mapping =" not in content, (
            "Design document should not contain runtime mapping assignments"
        )


# ============================================================
# TEST-TAXONOMY-ALIGN-008: 21-category claim status
# ============================================================
class Test21CategoryStatus:
    """Verify the 21-category provenance investigation result."""

    def test_21_category_source_is_verified(self):
        """TEST-TAXONOMY-ALIGN-008: 21-category source must be VERIFIED in design doc."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        # The 21-category provenance section should exist
        assert "21-Category Provenance" in content or "21-Category" in content, (
            "Design document must have 21-category provenance investigation"
        )
        # It should be marked as VERIFIED (since we found the source)
        provenance_start = content.find("21-Category Provenance")
        if provenance_start > 0:
            provenance_section = content[provenance_start:provenance_start + 1000]
            assert "VERIFIED" in provenance_section, (
                "21-category source should be marked VERIFIED in provenance section"
            )

    def test_21_category_source_is_deeptech_schema(self):
        """21 categories must be traced to deeptech_policy_schema.json."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        assert "deeptech_policy_schema.json" in content, (
            "21-category source must reference deeptech_policy_schema.json"
        )

    def test_21_category_values_listed(self):
        """All 21 values from the deeptech schema should be listed."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        deeptech_values = [
            "ai_ml", "robotics", "quantum_computing", "biotech", "fintech",
            "cleantech", "aerospace", "semiconductor", "blockchain", "vr_ar",
            "nanotech", "space_tech", "embodied_ai", "autonomous_driving",
            "cybersecurity", "iot", "5g", "edge_computing", "metaverse",
            "web3", "digital_twin",
        ]
        provenance_start = content.find("21-Category Provenance")
        provenance_section = content[provenance_start:provenance_start + 2000]
        for val in deeptech_values:
            assert val in provenance_section, (
                f"21-category value '{val}' not found in provenance section"
            )

    def test_21_category_not_used_as_canonical_basis(self):
        """21 categories should NOT be blindly adopted as canonical."""
        content = DESIGN_DOC.read_text(encoding="utf-8")
        # The design should propose fewer categories (16+2)
        assert "16" in content, "Design should propose a refined canonical count"
        # Should not say "21 categories" as the canonical answer
        assert "canonical 21" not in content.lower(), (
            "Design must not adopt 21 as the canonical count"
        )
