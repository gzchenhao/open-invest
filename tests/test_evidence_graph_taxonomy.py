"""
P1-3.5 Evidence Graph Canonical Taxonomy Integration Tests

TEST-EG-TAX-001..045

Verifies:
- sector -> canonical_industry resolution (exact / synonym / normalization /
  semantic mapping / unknown / other / missing / invalid)
- deterministic resolution
- legacy sector preservation
- additive serialization backward compatibility (GraphNode / EvidenceGraph)
- EvidenceObject-level service path unaffected
- MOCK stays MOCK, UNVERIFIED stays UNVERIFIED, no VERIFIED escalation
- legacy sector query path unchanged

OpenInvest - P1-3.5
"""

import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from trust.evidence_graph import (
    EvidenceGraph,
    GraphNode,
    NodeType,
    RelationType,
    resolve_sector_canonical,
)
from trust.evidence_object import EvidenceObject, VerificationStatus
from trust.trust_service import TrustEvidenceService


class TestSectorCanonicalResolution(unittest.TestCase):
    """TEST-EG-TAX-001..012: raw sector -> canonical industry resolution."""

    def test_001_exact_sector_maps_to_canonical(self):
        """TEST-EG-TAX-001: registry T11 value AI -> ai."""
        self.assertEqual(resolve_sector_canonical("AI"), "ai")

    def test_002_registry_value_biotech(self):
        """TEST-EG-TAX-002: registry T11 value BIOTECH -> biotech."""
        self.assertEqual(resolve_sector_canonical("BIOTECH"), "biotech")

    def test_003_registry_value_quantum(self):
        """TEST-EG-TAX-003: registry T11 value QUANTUM -> quantum_computing."""
        self.assertEqual(resolve_sector_canonical("QUANTUM"), "quantum_computing")

    def test_004_synonym_chinese_maps_via_alias(self):
        """TEST-EG-TAX-004: 人工智能 -> ai via registry alias."""
        self.assertEqual(resolve_sector_canonical("人工智能"), "ai")

    def test_005_case_insensitive_normalization(self):
        """TEST-EG-TAX-005: lowercase ai resolves via case-insensitive lookup."""
        self.assertEqual(resolve_sector_canonical("ai"), "ai")

    def test_006_semantic_mapping_clean_tech(self):
        """TEST-EG-TAX-006: CLEAN_TECH -> new_energy (registry semantic mapping)."""
        self.assertEqual(resolve_sector_canonical("CLEAN_TECH"), "new_energy")

    def test_007_semantic_mapping_advanced_materials(self):
        """TEST-EG-TAX-007: ADVANCED_MATERIALS -> new_materials (registry semantic mapping)."""
        self.assertEqual(resolve_sector_canonical("ADVANCED_MATERIALS"), "new_materials")

    def test_008_unknown_sector_stays_unknown(self):
        """TEST-EG-TAX-008: ai_hardware stays unknown (no upgrade to ai/semiconductor)."""
        self.assertEqual(resolve_sector_canonical("ai_hardware"), "unknown")

    def test_009_other_maps_to_other(self):
        """TEST-EG-TAX-009: OTHER -> other (never silently converted to unknown)."""
        self.assertEqual(resolve_sector_canonical("OTHER"), "other")

    def test_010_invalid_sector_maps_to_unknown(self):
        """TEST-EG-TAX-010: arbitrary invalid sector -> unknown (no guessing)."""
        self.assertEqual(resolve_sector_canonical("totally_fake_sector_xyz"), "unknown")

    def test_011_none_sector_returns_none(self):
        """TEST-EG-TAX-011: missing sector -> None (prefer null over guess)."""
        self.assertIsNone(resolve_sector_canonical(None))

    def test_012_empty_sector_maps_via_registry(self):
        """TEST-EG-TAX-012: empty string sector follows registry semantics -> unknown."""
        self.assertEqual(resolve_sector_canonical(""), "unknown")


class TestGraphNodeCanonicalIndustry(unittest.TestCase):
    """TEST-EG-TAX-020..028: GraphNode additive canonical_industry behavior."""

    def test_020_node_with_sector_gets_canonical_industry(self):
        """TEST-EG-TAX-020: add_node with sector AI computes canonical ai."""
        graph = EvidenceGraph()
        graph.add_node(
            "c1", NodeType.COMPANY, {"name": "C", "sector": "AI", "is_mock": True}
        )
        self.assertEqual(graph.nodes["c1"].canonical_industry, "ai")

    def test_021_node_without_sector_gets_none(self):
        """TEST-EG-TAX-021: missing sector -> canonical_industry None."""
        graph = EvidenceGraph()
        graph.add_node("p1", NodeType.POLICY, {"title": "P", "is_mock": True})
        self.assertIsNone(graph.nodes["p1"].canonical_industry)

    def test_022_legacy_sector_value_preserved(self):
        """TEST-EG-TAX-022: data["sector"] is never mutated by resolution."""
        graph = EvidenceGraph()
        original = {"name": "C", "sector": "AI", "is_mock": True}
        graph.add_node("c1", NodeType.COMPANY, original)
        self.assertEqual(graph.nodes["c1"].data["sector"], "AI")
        self.assertEqual(original["sector"], "AI")

    def test_023_deterministic_resolution(self):
        """TEST-EG-TAX-023: same sector resolves identically across graph instances."""
        graph_one = EvidenceGraph()
        graph_two = EvidenceGraph()
        graph_one.add_node("c1", NodeType.COMPANY, {"sector": "人工智能"})
        graph_two.add_node("c2", NodeType.COMPANY, {"sector": "人工智能"})
        self.assertEqual(graph_one.nodes["c1"].canonical_industry, "ai")
        self.assertEqual(
            graph_one.nodes["c1"].canonical_industry,
            graph_two.nodes["c2"].canonical_industry,
        )

    def test_024_node_to_dict_includes_canonical_when_present(self):
        """TEST-EG-TAX-024: to_dict carries canonical_industry for sector nodes."""
        node = GraphNode("c1", NodeType.COMPANY, {"sector": "AI"})
        node_dict = node.to_dict()
        self.assertEqual(node_dict["canonical_industry"], "ai")

    def test_025_node_to_dict_omits_canonical_when_absent(self):
        """TEST-EG-TAX-025: sector-less node output keeps pre-P1-3.5 shape."""
        node = GraphNode("p1", NodeType.POLICY, {"title": "P"})
        node_dict = node.to_dict()
        self.assertNotIn("canonical_industry", node_dict)
        self.assertEqual(set(node_dict.keys()), {"id", "type", "data", "created_time"})

    def test_026_node_roundtrip_preserves_both_fields(self):
        """TEST-EG-TAX-026: to_dict/from_dict round-trip keeps sector + canonical."""
        node = GraphNode("c1", NodeType.COMPANY, {"sector": "CLEAN_TECH"})
        restored = GraphNode.from_dict(node.to_dict())
        self.assertEqual(restored.data["sector"], "CLEAN_TECH")
        self.assertEqual(restored.canonical_industry, "new_energy")

    def test_027_legacy_serialized_node_recomputes(self):
        """TEST-EG-TAX-027: old serialization (no canonical field) recomputes on load."""
        legacy = {
            "id": "c1",
            "type": "company",
            "data": {"sector": "BIOTECH"},
            "created_time": 123.0,
        }
        node = GraphNode.from_dict(legacy)
        self.assertEqual(node.canonical_industry, "biotech")

    def test_028_stored_canonical_wins_over_recompute(self):
        """TEST-EG-TAX-028: stored canonical_industry is not overwritten."""
        payload = {
            "id": "c1",
            "type": "company",
            "data": {"sector": "AI"},
            "created_time": 123.0,
            "canonical_industry": "ai",
        }
        node = GraphNode.from_dict(payload)
        self.assertEqual(node.canonical_industry, "ai")


class TestGraphSerialization(unittest.TestCase):
    """TEST-EG-TAX-030..031: EvidenceGraph-level serialization compatibility."""

    def test_030_graph_roundtrip_preserves_sector_and_canonical(self):
        """TEST-EG-TAX-030: graph to_dict/from_dict keeps both fields."""
        graph = EvidenceGraph()
        graph.add_node("c1", NodeType.COMPANY, {"sector": "QUANTUM"})
        graph.add_node("p1", NodeType.POLICY, {"title": "P"})
        graph.add_relation("c1", "p1", RelationType.BENEFITS_FROM)
        restored = EvidenceGraph.from_dict(graph.to_dict())
        self.assertEqual(restored.nodes["c1"].canonical_industry, "quantum_computing")
        self.assertIsNone(restored.nodes["p1"].canonical_industry)
        self.assertEqual(restored.nodes["c1"].data["sector"], "QUANTUM")

    def test_031_legacy_graph_dict_loads_without_canonical(self):
        """TEST-EG-TAX-031: pre-P1-3.5 serialized graph loads cleanly."""
        legacy = {
            "nodes": [
                {
                    "id": "c1",
                    "type": "company",
                    "data": {"sector": "AI"},
                    "created_time": 1.0,
                }
            ],
            "edges": [],
        }
        graph = EvidenceGraph.from_dict(legacy)
        self.assertIn("c1", graph.nodes)
        self.assertEqual(graph.nodes["c1"].canonical_industry, "ai")


class TestTrustPathUnaffected(unittest.TestCase):
    """TEST-EG-TAX-040..045: Trust/Provenance/MOCK semantics untouched."""

    def setUp(self):
        self.service = TrustEvidenceService()

    def _create(self, status):
        return self.service.create_evidence(
            {
                "id": "ev_%s" % status.value.lower(),
                "type": "company",
                "source": "mock",
                "source_reference": "mock://x",
                "verification_status": status,
                "confidence_score": 0.0,
                "metadata": {"sector": "AI", "is_mock": True},
            }
        )

    def test_040_service_evidence_node_has_no_canonical(self):
        """TEST-EG-TAX-040: service evidence data has no top-level sector -> canonical None."""
        response = self._create(VerificationStatus.MOCK)
        self.assertTrue(response["success"])
        node = self.service.evidence_graph.nodes[response["evidence_id"]]
        self.assertIsNone(node.canonical_industry)
        self.assertNotIn("canonical_industry", node.data)

    def test_041_mock_stays_mock(self):
        """TEST-EG-TAX-041: MOCK evidence is not upgraded."""
        response = self._create(VerificationStatus.MOCK)
        node = self.service.evidence_graph.nodes[response["evidence_id"]]
        self.assertEqual(node.data["verification_status"], "MOCK")
        self.assertEqual(response["verification_status"], "MOCK")

    def test_042_unverified_stays_unverified(self):
        """TEST-EG-TAX-042: UNVERIFIED evidence is not escalated."""
        response = self._create(VerificationStatus.UNVERIFIED)
        node = self.service.evidence_graph.nodes[response["evidence_id"]]
        self.assertEqual(node.data["verification_status"], "UNVERIFIED")

    def test_043_no_automatic_verified_escalation(self):
        """TEST-EG-TAX-043: creating evidence never yields VERIFIED status."""
        for status in (VerificationStatus.MOCK, VerificationStatus.UNVERIFIED):
            response = self._create(status)
            self.assertNotEqual(response["verification_status"], "VERIFIED")

    def test_044_evidence_object_serialization_unchanged(self):
        """TEST-EG-TAX-044: EvidenceObject dict shape has no canonical/sector fields."""
        obj = EvidenceObject(
            id="ev1",
            type="company",
            source="mock",
            source_reference="",
            verification_status=VerificationStatus.MOCK,
        )
        obj_dict = obj.to_dict()
        self.assertNotIn("canonical_industry", obj_dict)
        self.assertNotIn("sector", obj_dict)
        restored = EvidenceObject.from_dict(obj_dict)
        self.assertEqual(restored.verification_status, VerificationStatus.MOCK)

    def test_045_sector_substring_query_still_works(self):
        """TEST-EG-TAX-045: legacy sector query path unchanged (find_company_evidence)."""
        self.service.evidence_graph.add_node(
            "c1",
            NodeType.COMPANY,
            {"name": "Alpha AI", "sector": "AI", "is_mock": True},
        )
        result = self.service.graph_query_engine.find_company_evidence(
            "Alpha", sector="AI"
        )
        self.assertTrue(result.success)
        self.assertEqual(result.count, 1)
        self.assertEqual(result.results[0]["evidence_id"], "c1")


if __name__ == "__main__":
    unittest.main()
