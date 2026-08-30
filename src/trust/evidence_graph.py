"""
Evidence Graph Minimal Prototype

Minimal graph implementation for OpenInvest Trust System.
Supports: add_node(), add_relation(), query_evidence()

Node Types: Policy, Company, Technology, Evidence
Relation Types: SUPPORTED_BY, BENEFITS_FROM, DERIVED_FROM

NOT PRODUCTION CODE.

OpenInvest - Trust Evidence Prototype
"""

import json
import time
from typing import Dict, Any, List, Optional, Set
from enum import Enum

_canonical_registry = None


def _get_canonical_registry():
    """Lazily load the canonical industry taxonomy registry.

    Reuses schema/canonical_taxonomy.py (P1-3.2/P1-3.3). No second taxonomy
    mapping is defined here. Import failures propagate so a broken registry
    is never silently replaced by guessed values.
    """
    global _canonical_registry
    if _canonical_registry is None:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
        from schema.canonical_taxonomy import get_registry
        _canonical_registry = get_registry()
    return _canonical_registry


def resolve_sector_canonical(sector: Any) -> Optional[str]:
    """Resolve a raw sector value to a canonical industry ID.

    Deterministic: delegates entirely to the canonical taxonomy registry
    (legacy source T11_evidence_graph). Provided but unresolvable values
    resolve to "unknown" per registry semantics. None input yields None
    (a missing sector carries no canonical claim).
    """
    if sector is None:
        return None
    return _get_canonical_registry().resolve(sector)


class NodeType(Enum):
    """Node types for evidence graph"""
    POLICY = "policy"
    COMPANY = "company"
    TECHNOLOGY = "technology"
    EVIDENCE = "evidence"


class RelationType(Enum):
    """Relation types for evidence graph"""
    SUPPORTED_BY = "supported_by"
    BENEFITS_FROM = "benefits_from"
    DERIVED_FROM = "derived_from"


class GraphNode:
    """Node in the evidence graph.

    canonical_industry (P1-3.5) is an additive derived field resolved from
    data["sector"] via the canonical taxonomy registry. It is None when
    sector is absent, and data["sector"] is never mutated.
    """

    def __init__(
        self,
        node_id: str,
        node_type: NodeType,
        data: Dict[str, Any],
        created_time: float = None
    ):
        self.id = node_id
        self.type = node_type
        self.data = data
        self.created_time = created_time or time.time()
        self.canonical_industry = (
            resolve_sector_canonical(data["sector"]) if "sector" in data else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary.

        canonical_industry is serialized only when present, so output for
        sector-less nodes keeps the pre-P1-3.5 shape (backward compatible).
        """
        node_dict = {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "created_time": self.created_time
        }
        if self.canonical_industry is not None:
            node_dict["canonical_industry"] = self.canonical_industry
        return node_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphNode":
        """Create node from dictionary.

        A stored canonical_industry wins over recomputation; legacy
        serializations without the field recompute from data["sector"]
        when present.
        """
        node = cls(
            node_id=data["id"],
            node_type=NodeType(data["type"]),
            data=data["data"],
            created_time=data.get("created_time")
        )
        if "canonical_industry" in data:
            node.canonical_industry = data["canonical_industry"]
        return node


class GraphEdge:
    """Edge in the evidence graph."""
    
    def __init__(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type
        self.metadata = metadata or {}
        self.created_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "metadata": self.metadata,
            "created_time": self.created_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphEdge":
        """Create edge from dictionary."""
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation_type=RelationType(data["relation_type"]),
            metadata=data.get("metadata", {})
        )


class EvidenceGraph:
    """
    Minimal evidence graph prototype.
    
    Supports:
    - add_node()
    - add_relation()
    - query_evidence()
    
    Node Types: Policy, Company, Technology, Evidence
    Relation Types: SUPPORTED_BY, BENEFITS_FROM, DERIVED_FROM
    """
    
    def __init__(self):
        """Initialize evidence graph."""
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.adjacency: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        data: Dict[str, Any]
    ) -> bool:
        """Add a node to the graph."""
        if node_id in self.nodes:
            return False  # Node already exists
        
        node = GraphNode(node_id, node_type, data)
        self.nodes[node_id] = node
        
        # Initialize adjacency list
        if node_id not in self.adjacency:
            self.adjacency[node_id] = []
        
        return True
    
    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a relation between two nodes."""
        # Check if both nodes exist
        if source_id not in self.nodes or target_id not in self.nodes:
            return False
        
        # Check if relation already exists
        for edge in self.edges:
            if (edge.source_id == source_id and edge.target_id == target_id and 
                edge.relation_type == relation_type):
                return False
        
        # Create and add edge
        edge = GraphEdge(source_id, target_id, relation_type, metadata)
        self.edges.append(edge)
        
        # Update adjacency list
        self.adjacency[source_id].append({
            "target_id": target_id,
            "relation_type": relation_type.value,
            "metadata": metadata or {}
        })
        
        return True
    
    def query_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Query evidence node and its relations."""
        if evidence_id not in self.nodes:
            return None
        
        node = self.nodes[evidence_id]
        
        # Find all relations involving this node
        incoming_relations = []
        outgoing_relations = []
        
        for edge in self.edges:
            if edge.target_id == evidence_id:
                incoming_relations.append(edge.to_dict())
            if edge.source_id == evidence_id:
                outgoing_relations.append(edge.to_dict())
        
        return {
            "node": node.to_dict(),
            "incoming_relations": incoming_relations,
            "outgoing_relations": outgoing_relations,
            "related_nodes": self._get_related_nodes(evidence_id)
        }
    
    def query_by_type(self, node_type: NodeType) -> List[Dict[str, Any]]:
        """Query all nodes of a specific type."""
        result = []
        for node in self.nodes.values():
            if node.type == node_type:
                result.append(node.to_dict())
        return result
    
    def query_relations(self, source_id: str, relation_type: RelationType) -> List[Dict[str, Any]]:
        """Query all outgoing relations of a specific type from a node."""
        result = []
        for edge in self.edges:
            if edge.source_id == source_id and edge.relation_type == relation_type:
                result.append(edge.to_dict())
        return result
    
    def _get_related_nodes(self, node_id: str) -> List[str]:
        """Get all nodes directly related to the given node."""
        related = set()
        
        # Find nodes connected by outgoing edges
        for edge in self.edges:
            if edge.source_id == node_id:
                related.add(edge.target_id)
        
        # Find nodes connected by incoming edges
        for edge in self.edges:
            if edge.target_id == node_id:
                related.add(edge.source_id)
        
        return list(related)
    
    def get_graph_summary(self) -> Dict[str, Any]:
        """Get summary of the graph structure."""
        node_counts = {}
        for node in self.nodes.values():
            node_type = node.type.value
            node_counts[node_type] = node_counts.get(node_type, 0) + 1
        
        relation_counts = {}
        for edge in self.edges:
            relation_type = edge.relation_type.value
            relation_counts[relation_type] = relation_counts.get(relation_type, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_counts": node_counts,
            "relation_counts": relation_counts,
            "created_time": time.time()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary for serialization."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
            "summary": self.get_graph_summary()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceGraph":
        """Create graph from dictionary."""
        graph = cls()
        
        # Load nodes
        for node_data in data["nodes"]:
            node = GraphNode.from_dict(node_data)
            graph.nodes[node.id] = node
            graph.adjacency[node.id] = []
        
        # Load edges
        for edge_data in data["edges"]:
            edge = GraphEdge.from_dict(edge_data)
            graph.edges.append(edge)
            
            # Update adjacency list
            graph.adjacency[edge.source_id].append({
                "target_id": edge.target_id,
                "relation_type": edge.relation_type.value,
                "metadata": edge.metadata
            })
        
        return graph


# Example usage
def example_graph_operations():
    """Example of graph operations."""
    graph = EvidenceGraph()
    
    # Add nodes
    graph.add_node(
        node_id="company_a",
        node_type=NodeType.COMPANY,
        data={"name": "Company A", "sector": "AI", "is_mock": True}
    )
    
    graph.add_node(
        node_id="policy_x",
        node_type=NodeType.POLICY,
        data={"title": "AI Policy Framework", "jurisdiction": "national", "is_mock": True}
    )
    
    graph.add_node(
        node_id="tech_ai",
        node_type=NodeType.TECHNOLOGY,
        data={"name": "AI Technology", "category": "machine_learning", "is_mock": True}
    )
    
    graph.add_node(
        node_id="evidence_001",
        node_type=NodeType.EVIDENCE,
        data={"type": "policy_support", "description": "Policy supports AI development", "is_mock": True}
    )
    
    # Add relations
    graph.add_relation(
        source_id="company_a",
        target_id="policy_x",
        relation_type=RelationType.BENEFITS_FROM,
        metadata={"strength": "strong", "is_mock": True}
    )
    
    graph.add_relation(
        source_id="company_a",
        target_id="tech_ai",
        relation_type=RelationType.SUPPORTED_BY,
        metadata={"strength": "direct", "is_mock": True}
    )
    
    graph.add_relation(
        source_id="evidence_001",
        target_id="policy_x",
        relation_type=RelationType.DERIVED_FROM,
        metadata={"confidence": "high", "is_mock": True}
    )
    
    # Query operations
    print("Graph Summary:")
    print(json.dumps(graph.get_graph_summary(), indent=2))
    
    print("\nCompany A Query:")
    company_query = graph.query_evidence("company_a")
    print(json.dumps(company_query, indent=2))
    
    return graph