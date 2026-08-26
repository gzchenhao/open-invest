"""
Canonical Industry Taxonomy Registry and Legacy Mapping Layer

Quest: P1-3.2 — Implement Canonical Taxonomy Registry and Legacy Mapping Layer

This module provides:
1. Canonical Industry Registry — single source of truth for industry IDs
2. Legacy Mapping Layer — deterministic mapping from all legacy taxonomy sources
3. Resolution logic — resolve any legacy industry value to a canonical ID

Design principles:
- Stable snake_case IDs
- One concept = one canonical ID
- Unknown → "unknown" (never guess)
- Other → "other" (confirmed industry but not in canonical registry)
- Backward compatible — legacy values remain resolvable
- Decoupled from Trust Infrastructure

Status: IMPLEMENTED (P1-3.2, 2026-08-26)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class MappingConfidence(str, Enum):
    """Confidence level for legacy → canonical mapping."""
    EXACT = "exact"
    SYNONYM = "synonym"
    NORMALIZATION = "normalization"
    SEMANTIC_MAPPING = "semantic_mapping"
    UNKNOWN = "unknown"
    OTHER = "other"


@dataclass(frozen=True)
class CanonicalIndustry:
    """
    A single canonical industry entry.

    Attributes:
        id: Stable snake_case canonical ID (e.g. "autonomous_driving")
        display_name_zh: Chinese display name
        display_name_en: English display name
        aliases: Known synonyms/variants that map to this canonical ID
        description: Brief description of the industry
        status: "active" for canonical categories, "special" for other/unknown
    """
    id: str
    display_name_zh: str
    display_name_en: str
    aliases: tuple = ()
    description: str = ""
    status: str = "active"


@dataclass(frozen=True)
class LegacyMapping:
    """
    A single legacy → canonical mapping entry.

    Attributes:
        legacy_value: The original legacy value
        canonical_id: The resolved canonical ID
        confidence: Mapping confidence level
        source: Which taxonomy source this legacy value comes from
        reason: Explanation for non-exact mappings
    """
    legacy_value: str
    canonical_id: str
    confidence: MappingConfidence
    source: str
    reason: str = ""


class CanonicalIndustryRegistry:
    """
    Single source of truth for OpenInvest canonical industry taxonomy.

    Usage:
        registry = CanonicalIndustryRegistry()
        industry = registry.get("ai")
        canonical_id = registry.resolve("ai_ml")  # → "ai"
        is_valid = registry.validate("semiconductor")  # → True
    """

    # Canonical Industry Registry (Layer 1)
    # 16 canonical categories + other + unknown = 18 slots
    _CANONICAL_INDUSTRIES: Dict[str, CanonicalIndustry] = {
        "ai": CanonicalIndustry(
            id="ai",
            display_name_zh="人工智能",
            display_name_en="Artificial Intelligence",
            aliases=("ai_ml", "AI", "人工智能"),
            description="Core AI industry including machine learning, deep learning, NLP, computer vision",
        ),
        "robotics": CanonicalIndustry(
            id="robotics",
            display_name_zh="机器人",
            display_name_en="Robotics",
            aliases=("机器人",),
            description="Industrial and service robotics, robotic systems and components",
        ),
        "embodied_ai": CanonicalIndustry(
            id="embodied_ai",
            display_name_zh="具身智能",
            display_name_en="Embodied AI",
            aliases=("具身智能",),
            description="AI systems with physical embodiment; intersection of AI and robotics",
        ),
        "quantum_computing": CanonicalIndustry(
            id="quantum_computing",
            display_name_zh="量子计算",
            display_name_en="Quantum Computing",
            aliases=("quantum", "量子计算",),
            description="Quantum computing hardware, software, and algorithms",
        ),
        "semiconductor": CanonicalIndustry(
            id="semiconductor",
            display_name_zh="半导体",
            display_name_en="Semiconductor",
            aliases=("半导体",),
            description="Semiconductor design, manufacturing, and packaging",
        ),
        "biotech": CanonicalIndustry(
            id="biotech",
            display_name_zh="生物医药",
            display_name_en="Biotechnology",
            aliases=("biotechnology", "生物科技",),
            description="Biotechnology, pharmaceuticals, genomics, and biomedical engineering",
        ),
        "autonomous_driving": CanonicalIndustry(
            id="autonomous_driving",
            display_name_zh="自动驾驶",
            display_name_en="Autonomous Driving",
            aliases=("auto_driving", "自动驾驶",),
            description="Autonomous vehicle technology, ADAS, and intelligent transportation",
        ),
        "aerospace": CanonicalIndustry(
            id="aerospace",
            display_name_zh="航空航天",
            display_name_en="Aerospace & Defense",
            aliases=("space_tech", "航空航天",),
            description="Aerospace, aviation, space technology, and defense",
        ),
        "new_energy": CanonicalIndustry(
            id="new_energy",
            display_name_zh="新能源",
            display_name_en="New Energy & CleanTech",
            aliases=("cleantech", "新能源",),
            description="Solar, wind, hydrogen, energy storage, and clean technology",
        ),
        "new_materials": CanonicalIndustry(
            id="new_materials",
            display_name_zh="新材料",
            display_name_en="Advanced Materials",
            aliases=("nanotech", "新材料",),
            description="Advanced materials, nanotechnology, composites, and specialty materials",
        ),
        "blockchain": CanonicalIndustry(
            id="blockchain",
            display_name_zh="区块链",
            display_name_en="Blockchain & Web3",
            aliases=("web3", "区块链",),
            description="Blockchain, distributed ledger, and Web3 technologies",
        ),
        "fintech": CanonicalIndustry(
            id="fintech",
            display_name_zh="金融科技",
            display_name_en="FinTech",
            aliases=("金融科技",),
            description="Financial technology, digital payments, and regtech",
        ),
        "high_end_equipment": CanonicalIndustry(
            id="high_end_equipment",
            display_name_zh="高端装备",
            display_name_en="Advanced Manufacturing",
            aliases=("advanced_manufacturing", "高端装备",),
            description="High-end equipment, advanced manufacturing, and industrial automation",
        ),
        "cybersecurity": CanonicalIndustry(
            id="cybersecurity",
            display_name_zh="网络安全",
            display_name_en="Cybersecurity",
            aliases=("网络安全",),
            description="Cybersecurity, information security, and privacy technology",
        ),
        "iot": CanonicalIndustry(
            id="iot",
            display_name_zh="物联网",
            display_name_en="Internet of Things",
            aliases=("5g", "edge_computing", "物联网",),
            description="IoT, 5G, edge computing, and connected devices",
        ),
        "vr_ar": CanonicalIndustry(
            id="vr_ar",
            display_name_zh="虚拟现实/增强现实",
            display_name_en="VR/AR & Metaverse",
            aliases=("metaverse", "digital_twin", "虚拟现实/增强现实"),
            description="Virtual reality, augmented reality, metaverse, and digital twins",
        ),
        "other": CanonicalIndustry(
            id="other",
            display_name_zh="其他",
            display_name_en="Other",
            aliases=(),
            description="Confirmed DeepTech/industry but not in specific canonical category",
            status="special",
        ),
        "unknown": CanonicalIndustry(
            id="unknown",
            display_name_zh="未知",
            display_name_en="Unknown",
            aliases=(),
            description="Cannot reliably determine canonical category; no guessing",
            status="special",
        ),
    }

    # ================================================================
    # Legacy → Canonical Mapping (Layer 2)
    # ================================================================

    # T1: Parser (policy_cleaner.py) — CN→EN mapping output values
    _T1_PARSER: Dict[str, str] = {
        "ai": "ai",
        "robotics": "robotics",
        "quantum_computing": "quantum_computing",
        "biotech": "biotech",
        "autonomous_driving": "autonomous_driving",
        "blockchain": "blockchain",
        "vr_ar": "vr_ar",
        "other": "other",
    }

    # T2: Schema (schema/types.py) — IndustryType enum values
    _T2_SCHEMA: Dict[str, str] = {
        "autonomous_driving": "autonomous_driving",
        "embodied_ai": "embodied_ai",
        "robotics": "robotics",
        "ai_hardware": "unknown",  # Cannot determine: ai or semiconductor
        "quantum_computing": "quantum_computing",
    }

    # T3: Web Portal (interactive_ai_server.py) — CN labels
    _T3_WEB_PORTAL: Dict[str, str] = {
        "AI": "ai",
        "半导体": "semiconductor",
        "自动驾驶": "autonomous_driving",
        "量子计算": "quantum_computing",
        "区块链": "blockchain",
        "生物科技": "biotech",
        "高端装备": "high_end_equipment",
        "航空航天": "aerospace",
        "新材料": "new_materials",
        "新能源": "new_energy",
        "金融科技": "fintech",
        "纳米技术": "new_materials",  # nanotech → new_materials
    }

    # T4/T5: Seed Data — EN values (both seed files use same values)
    _T4_SEED_DATA: Dict[str, str] = {
        "ai": "ai",
        "quantum_computing": "quantum_computing",
        "semiconductor": "semiconductor",
        "biotech": "biotech",
        "autonomous_driving": "autonomous_driving",
        "new_materials": "new_materials",
        "blockchain": "blockchain",
        "high_end_equipment": "high_end_equipment",
        "embodied_ai": "embodied_ai",
        "auto_driving": "autonomous_driving",  # synonym
        "biotechnology": "biotech",  # synonym
        "new_energy": "new_energy",
        "fintech": "fintech",
    }

    # T6: Cleaning Service (china_policy_cleaning_service.py) — CN→EN
    _T6_CLEANING_SERVICE: Dict[str, str] = {
        "ai": "ai",
        "robotics": "robotics",
        "quantum_computing": "quantum_computing",
        "semiconductor": "semiconductor",
        "autonomous_driving": "autonomous_driving",
        "embodied_ai": "embodied_ai",
        "biotech": "biotech",
        "new_energy": "new_energy",
        "new_materials": "new_materials",
        "high_end_equipment": "high_end_equipment",
    }

    # T7: Fixed Server (fixed_server.py) — EN→CN mapping keys
    _T7_FIXED_SERVER: Dict[str, str] = {
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

    # T8: Landing Service (landing_requirements_service.py) — EN values
    _T8_LANDING_SERVICE: Dict[str, str] = {
        "autonomous_driving": "autonomous_driving",
        "embodied_ai": "embodied_ai",
        "quantum_computing": "quantum_computing",
    }

    # T9: Legacy Mock DB (policy_crawler/processors/mock_policy_database.py)
    _T9_LEGACY_MOCK_DB: Dict[str, str] = {
        "ai_ml": "ai",  # merged
        "biotech": "biotech",
        "fintech": "fintech",
        "cleantech": "new_energy",  # merged
        "blockchain": "blockchain",
    }

    # T10: Deeptech Schema (deeptech_policy_schema.json) — 21 enum values
    _T10_DEEPTECH_SCHEMA: Dict[str, str] = {
        "ai_ml": "ai",  # merged
        "robotics": "robotics",
        "quantum_computing": "quantum_computing",
        "biotech": "biotech",
        "fintech": "fintech",
        "cleantech": "new_energy",  # merged
        "aerospace": "aerospace",
        "semiconductor": "semiconductor",
        "blockchain": "blockchain",
        "vr_ar": "vr_ar",
        "nanotech": "new_materials",  # merged
        "space_tech": "aerospace",  # merged
        "embodied_ai": "embodied_ai",
        "autonomous_driving": "autonomous_driving",
        "cybersecurity": "cybersecurity",
        "iot": "iot",
        "5g": "iot",  # merged: 5G → IoT infrastructure
        "edge_computing": "iot",  # merged: edge computing → IoT infrastructure
        "metaverse": "vr_ar",  # merged: metaverse → VR/AR
        "web3": "blockchain",  # merged: Web3 → blockchain
        "digital_twin": "vr_ar",  # merged: digital twin → VR/AR
    }

    # T11: Evidence Graph (docs/Evidence_Graph_Prototype.md) — design doc
    _T11_EVIDENCE_GRAPH: Dict[str, str] = {
        "AI": "ai",
        "BIOTECH": "biotech",
        "QUANTUM": "quantum_computing",
        "CLEAN_TECH": "new_energy",  # merged
        "ADVANCED_MATERIALS": "new_materials",
        "OTHER": "other",
    }

    # All legacy sources keyed by source ID
    _LEGACY_SOURCES: Dict[str, Dict[str, str]] = {
        "T1_parser": _T1_PARSER,
        "T2_schema": _T2_SCHEMA,
        "T3_web_portal": _T3_WEB_PORTAL,
        "T4_seed_data": _T4_SEED_DATA,
        "T6_cleaning_service": _T6_CLEANING_SERVICE,
        "T7_fixed_server": _T7_FIXED_SERVER,
        "T8_landing_service": _T8_LANDING_SERVICE,
        "T9_legacy_mock_db": _T9_LEGACY_MOCK_DB,
        "T10_deeptech_schema": _T10_DEEPTECH_SCHEMA,
        "T11_evidence_graph": _T11_EVIDENCE_GRAPH,
    }

    # Mapping confidence classification
    _CONFIDENCE_RULES: Dict[str, MappingConfidence] = {
        # Exact matches (same string in legacy and canonical)
        "ai": MappingConfidence.EXACT,
        "robotics": MappingConfidence.EXACT,
        "quantum_computing": MappingConfidence.EXACT,
        "biotech": MappingConfidence.EXACT,
        "autonomous_driving": MappingConfidence.EXACT,
        "blockchain": MappingConfidence.EXACT,
        "vr_ar": MappingConfidence.EXACT,
        "semiconductor": MappingConfidence.EXACT,
        "new_materials": MappingConfidence.EXACT,
        "high_end_equipment": MappingConfidence.EXACT,
        "embodied_ai": MappingConfidence.EXACT,
        "new_energy": MappingConfidence.EXACT,
        "fintech": MappingConfidence.EXACT,
        "aerospace": MappingConfidence.EXACT,
        "cybersecurity": MappingConfidence.EXACT,
        "iot": MappingConfidence.EXACT,
        "other": MappingConfidence.EXACT,
        "unknown": MappingConfidence.EXACT,
        # Synonyms
        "auto_driving": MappingConfidence.SYNONYM,
        "biotechnology": MappingConfidence.SYNONYM,
        "advanced_manufacturing": MappingConfidence.SYNONYM,
        # Normalizations
        "ai_ml": MappingConfidence.NORMALIZATION,
        "cleantech": MappingConfidence.NORMALIZATION,
        "AI": MappingConfidence.NORMALIZATION,
        "BIOTECH": MappingConfidence.NORMALIZATION,
        "QUANTUM": MappingConfidence.NORMALIZATION,
        "OTHER": MappingConfidence.NORMALIZATION,
        # Semantic mappings
        "nanotech": MappingConfidence.SEMANTIC_MAPPING,
        "space_tech": MappingConfidence.SEMANTIC_MAPPING,
        "5g": MappingConfidence.SEMANTIC_MAPPING,
        "edge_computing": MappingConfidence.SEMANTIC_MAPPING,
        "metaverse": MappingConfidence.SEMANTIC_MAPPING,
        "web3": MappingConfidence.SEMANTIC_MAPPING,
        "digital_twin": MappingConfidence.SEMANTIC_MAPPING,
        "CLEAN_TECH": MappingConfidence.SEMANTIC_MAPPING,
        "ADVANCED_MATERIALS": MappingConfidence.SEMANTIC_MAPPING,
        "ai_hardware": MappingConfidence.UNKNOWN,
        # Chinese label mappings
        "半导体": MappingConfidence.EXACT,
        "自动驾驶": MappingConfidence.EXACT,
        "量子计算": MappingConfidence.EXACT,
        "区块链": MappingConfidence.EXACT,
        "生物科技": MappingConfidence.EXACT,
        "高端装备": MappingConfidence.EXACT,
        "航空航天": MappingConfidence.EXACT,
        "新材料": MappingConfidence.EXACT,
        "新能源": MappingConfidence.EXACT,
        "金融科技": MappingConfidence.EXACT,
        "纳米技术": MappingConfidence.SEMANTIC_MAPPING,
    }

    def get(self, canonical_id: str) -> Optional[CanonicalIndustry]:
        """Get a canonical industry by ID. Returns None if not found."""
        return self._CANONICAL_INDUSTRIES.get(canonical_id)

    def list(self) -> List[CanonicalIndustry]:
        """List all canonical industries."""
        return list(self._CANONICAL_INDUSTRIES.values())

    def list_ids(self) -> List[str]:
        """List all canonical industry IDs."""
        return list(self._CANONICAL_INDUSTRIES.keys())

    def validate(self, canonical_id: str) -> bool:
        """Check if a canonical ID is valid."""
        return canonical_id in self._CANONICAL_INDUSTRIES

    def resolve(self, legacy_value: str) -> str:
        """
        Resolve a legacy industry value to a canonical ID.

        Resolution order:
        1. Exact match in any legacy source → canonical ID
        2. Case-insensitive match in any legacy source → canonical ID
        3. Match via canonical aliases → canonical ID
        4. Return "unknown" (never guess)

        Args:
            legacy_value: Any industry value from any legacy source

        Returns:
            Canonical industry ID (never raises; falls back to "unknown")
        """
        if not legacy_value or not isinstance(legacy_value, str):
            return "unknown"

        value = legacy_value.strip()
        if not value:
            return "unknown"

        # 1. Direct lookup across all legacy sources
        for source_name, source_map in self._LEGACY_SOURCES.items():
            if value in source_map:
                return source_map[value]

        # 2. Case-insensitive lookup
        value_lower = value.lower()
        for source_name, source_map in self._LEGACY_SOURCES.items():
            for legacy_key, canonical_id in source_map.items():
                if legacy_key.lower() == value_lower:
                    return canonical_id

        # 3. Check canonical aliases
        for cid, industry in self._CANONICAL_INDUSTRIES.items():
            if value in industry.aliases or value_lower in [a.lower() for a in industry.aliases]:
                return cid

        # 4. Unknown — never guess
        return "unknown"

    def resolve_with_metadata(self, legacy_value: str) -> LegacyMapping:
        """
        Resolve a legacy value and return full mapping metadata.

        Returns a LegacyMapping with confidence level and source info.
        """
        if not legacy_value or not isinstance(legacy_value, str):
            return LegacyMapping(
                legacy_value=str(legacy_value),
                canonical_id="unknown",
                confidence=MappingConfidence.UNKNOWN,
                source="runtime",
                reason="Empty or invalid input",
            )

        value = legacy_value.strip()
        if not value:
            return LegacyMapping(
                legacy_value=legacy_value,
                canonical_id="unknown",
                confidence=MappingConfidence.UNKNOWN,
                source="runtime",
                reason="Empty string",
            )

        # Search all sources
        for source_name, source_map in self._LEGACY_SOURCES.items():
            if value in source_map:
                canonical_id = source_map[value]
                confidence = self._CONFIDENCE_RULES.get(value, MappingConfidence.EXACT)
                return LegacyMapping(
                    legacy_value=value,
                    canonical_id=canonical_id,
                    confidence=confidence,
                    source=source_name,
                )

        # Case-insensitive
        value_lower = value.lower()
        for source_name, source_map in self._LEGACY_SOURCES.items():
            for legacy_key, canonical_id in source_map.items():
                if legacy_key.lower() == value_lower:
                    confidence = self._CONFIDENCE_RULES.get(legacy_key, MappingConfidence.EXACT)
                    return LegacyMapping(
                        legacy_value=value,
                        canonical_id=canonical_id,
                        confidence=confidence,
                        source=source_name,
                    )

        # Check aliases
        for cid, industry in self._CANONICAL_INDUSTRIES.items():
            if value in industry.aliases or value_lower in [a.lower() for a in industry.aliases]:
                return LegacyMapping(
                    legacy_value=value,
                    canonical_id=cid,
                    confidence=MappingConfidence.SYNONYM,
                    source="alias",
                    reason=f"Matched alias of {cid}",
                )

        # Unknown
        return LegacyMapping(
            legacy_value=value,
            canonical_id="unknown",
            confidence=MappingConfidence.UNKNOWN,
            source="runtime",
            reason="No matching legacy mapping found",
        )

    def map_legacy(self, source_id: str) -> Dict[str, str]:
        """
        Get the full legacy → canonical mapping for a specific source.

        Args:
            source_id: Source identifier (e.g. "T1_parser", "T10_deeptech_schema")

        Returns:
            Dict mapping legacy values to canonical IDs

        Raises:
            KeyError: If source_id is not recognized
        """
        if source_id not in self._LEGACY_SOURCES:
            raise KeyError(
                f"Unknown legacy source: {source_id}. "
                f"Available: {list(self._LEGACY_SOURCES.keys())}"
            )
        return dict(self._LEGACY_SOURCES[source_id])

    def get_display_name(self, canonical_id: str, lang: str = "en") -> Optional[str]:
        """
        Get display name for a canonical industry.

        Args:
            canonical_id: Canonical industry ID
            lang: "en" for English, "zh" for Chinese

        Returns:
            Display name string, or None if canonical_id not found
        """
        industry = self.get(canonical_id)
        if industry is None:
            return None
        if lang == "zh":
            return industry.display_name_zh
        return industry.display_name_en

    def get_all_legacy_values(self, source_id: Optional[str] = None) -> Set[str]:
        """
        Get all known legacy values, optionally filtered by source.

        Args:
            source_id: If provided, only return values from this source.
                       If None, return values from all sources.

        Returns:
            Set of all known legacy values
        """
        if source_id:
            return set(self.map_legacy(source_id).keys())
        all_values = set()
        for source_map in self._LEGACY_SOURCES.values():
            all_values.update(source_map.keys())
        return all_values

    def get_mapping_confidence(self, legacy_value: str) -> MappingConfidence:
        """Get the confidence level for a specific legacy value mapping."""
        return self._CONFIDENCE_RULES.get(legacy_value, MappingConfidence.UNKNOWN)

    def get_all_mappings(self) -> List[LegacyMapping]:
        """
        Get all legacy → canonical mappings across all sources.

        Returns a flat list of LegacyMapping entries.
        """
        mappings = []
        for source_name, source_map in self._LEGACY_SOURCES.items():
            for legacy_value, canonical_id in source_map.items():
                confidence = self._CONFIDENCE_RULES.get(legacy_value, MappingConfidence.EXACT)
                mappings.append(LegacyMapping(
                    legacy_value=legacy_value,
                    canonical_id=canonical_id,
                    confidence=confidence,
                    source=source_name,
                ))
        return mappings

    @property
    def canonical_count(self) -> int:
        """Number of canonical industry categories (including other and unknown)."""
        return len(self._CANONICAL_INDUSTRIES)

    @property
    def active_count(self) -> int:
        """Number of active (non-special) canonical categories."""
        return sum(1 for i in self._CANONICAL_INDUSTRIES.values() if i.status == "active")

    @property
    def legacy_source_count(self) -> int:
        """Number of legacy taxonomy sources tracked."""
        return len(self._LEGACY_SOURCES)


# Module-level singleton for convenience
_default_registry: Optional[CanonicalIndustryRegistry] = None


def get_registry() -> CanonicalIndustryRegistry:
    """Get the default CanonicalIndustryRegistry singleton."""
    global _default_registry
    if _default_registry is None:
        _default_registry = CanonicalIndustryRegistry()
    return _default_registry
