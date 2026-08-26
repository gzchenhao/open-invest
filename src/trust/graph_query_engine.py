"""Evidence Graph Query Engine for OpenInvest Trust System

High-value graph queries for Agent investigation.
Focus on explainable traces rather than large-scale graph operations.

OpenInvest - Trust Evidence API Boundary
"""

import json
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict

from .evidence_graph import EvidenceGraph, NodeType, RelationType


@dataclass
class QueryResult:
    """Standardized query result format"""
    success: bool
    query_type: str
    evidence_id: str
    results: List[Dict[str, Any]]
    count: int
    message: str
    error: str = ""
    integrity_valid: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TraceStep:
    """Single step in evidence trace"""
    step_id: str
    node_id: str
    node_type: str
    relation_type: str
    metadata: Dict[str, Any]
    depth: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GraphQueryEngine:
    """
    High-value graph query engine for Agent investigation.
    
    Focuses on explainable, traceable queries rather than complex graph algorithms.
    Designed to answer Agent questions like:
    - "Why should I trust this company?"
    - "What policy supports this technology?"
    - "Trace the evidence chain for this claim"
    """
    
    def __init__(self, graph: EvidenceGraph):
        """Initialize with evidence graph."""
        self.graph = graph
    
    def find_supporting_evidence(self, evidence_id: str, max_depth: int = 3) -> QueryResult:
        """
        Find evidence that supports the given evidence.
        
        Args:
            evidence_id: ID of evidence to find support for
            max_depth: Maximum depth to search
            
        Returns:
            Query result with supporting evidence
        """
        try:
            if evidence_id not in self.graph.nodes:
                return QueryResult(
                    success=False,
                    query_type="find_supporting_evidence",
                    evidence_id=evidence_id,
                    results=[],
                    count=0,
                    message=f"Evidence {evidence_id} not found"
                )
            
            supporting_evidence = []
            visited = set()
            queue = [(evidence_id, 0)]
            
            while queue:
                current_id, depth = queue.pop(0)
                
                if depth >= max_depth or current_id in visited:
                    continue
                
                visited.add(current_id)
                
                # Find nodes that support current node (reverse relations)
                for edge in self.graph.edges:
                    if (edge.target_id == current_id and 
                        edge.relation_type == RelationType.SUPPORTED_BY and
                        edge.source_id not in visited):
                        
                        source_node = self.graph.nodes.get(edge.source_id)
                        if source_node:
                            supporting_evidence.append({
                                "evidence_id": edge.source_id,
                                "evidence_type": source_node.type.value,
                                "evidence_data": source_node.data,
                                "relation_strength": edge.metadata.get("strength", "unknown"),
                                "relation_confidence": edge.metadata.get("confidence", "unknown"),
                                "support_depth": depth + 1,
                                "relation_metadata": edge.metadata
                            })
                            
                            if depth + 1 < max_depth:
                                queue.append((edge.source_id, depth + 1))
            
            return QueryResult(
                success=True,
                query_type="find_supporting_evidence",
                evidence_id=evidence_id,
                results=supporting_evidence,
                count=len(supporting_evidence),
                message=f"Found {len(supporting_evidence)} supporting evidence items (max depth: {max_depth})"
            )
            
        except Exception as e:
            return QueryResult(
                success=False,
                query_type="find_supporting_evidence",
                evidence_id=evidence_id,
                results=[],
                count=0,
                error=str(e),
                message="Failed to find supporting evidence"
            )
    
    def find_policy_sources(self, policy_type: Optional[str] = None) -> QueryResult:
        """
        Find policy sources in the graph.
        
        Args:
            policy_type: Optional filter for policy type
            
        Returns:
            Query result with policy sources
        """
        try:
            policy_sources = []
            
            for node_id, node in self.graph.nodes.items():
                if node.type == NodeType.POLICY:
                    # Apply filter if specified
                    if policy_type:
                        policy_data = node.data.get("policy_type", "").lower()
                        if policy_type.lower() not in policy_data:
                            continue
                    
                    policy_sources.append({
                        "evidence_id": node_id,
                        "policy_data": node.data,
                        "relation_count": len([
                            edge for edge in self.graph.edges 
                            if edge.source_id == node_id or edge.target_id == node_id
                        ])
                    })
            
            return QueryResult(
                success=True,
                query_type="find_policy_sources",
                evidence_id="",
                results=policy_sources,
                count=len(policy_sources),
                message=f"Found {len(policy_sources)} policy sources"
            )
            
        except Exception as e:
            return QueryResult(
                success=False,
                query_type="find_policy_sources",
                evidence_id="",
                results=[],
                count=0,
                error=str(e),
                message="Failed to find policy sources"
            )
    
    def find_company_evidence(self, company_name: Optional[str] = None, 
                            sector: Optional[str] = None) -> QueryResult:
        """
        Find company-related evidence in the graph.
        
        Args:
            company_name: Optional filter for company name
            sector: Optional filter for sector
            
        Returns:
            Query result with company evidence
        """
        try:
            company_evidence = []
            
            for node_id, node in self.graph.nodes.items():
                if node.type == NodeType.COMPANY:
                    # Apply filters
                    match = True
                    if company_name:
                        company_data = node.data.get("name", "").lower()
                        if company_name.lower() not in company_data:
                            match = False
                    
                    if sector:
                        sector_data = node.data.get("sector", "").lower()
                        if sector.lower() not in sector_data:
                            match = False
                    
                    if match:
                        # Find related evidence
                        related_evidence = []
                        for edge in self.graph.edges:
                            if edge.source_id == node_id or edge.target_id == node_id:
                                related_node_id = edge.target_id if edge.source_id == node_id else edge.source_id
                                related_node = self.graph.nodes.get(related_node_id)
                                if related_node:
                                    related_evidence.append({
                                        "related_id": related_node_id,
                                        "related_type": related_node.type.value,
                                        "relation_type": edge.relation_type.value,
                                        "relation_metadata": edge.metadata
                                    })
                        
                        company_evidence.append({
                            "evidence_id": node_id,
                            "company_data": node.data,
                            "related_evidence": related_evidence,
                            "relation_count": len(related_evidence)
                        })
            
            return QueryResult(
                success=True,
                query_type="find_company_evidence",
                evidence_id="",
                results=company_evidence,
                count=len(company_evidence),
                message=f"Found {len(company_evidence)} company evidence items"
            )
            
        except Exception as e:
            return QueryResult(
                success=False,
                query_type="find_company_evidence",
                evidence_id="",
                results=[],
                count=0,
                error=str(e),
                message="Failed to find company evidence"
            )
    
    def find_related_evidence(self, evidence_id: str, relation_types: Optional[List[str]] = None,
                            max_depth: int = 2) -> QueryResult:
        """
        Find evidence related to the given evidence.
        
        Args:
            evidence_id: ID of evidence to find relations for
            relation_types: Optional list of relation types to include
            max_depth: Maximum depth to search
            
        Returns:
            Query result with related evidence
        """
        try:
            if evidence_id not in self.graph.nodes:
                return QueryResult(
                    success=False,
                    query_type="find_related_evidence",
                    evidence_id=evidence_id,
                    results=[],
                    count=0,
                    message=f"Evidence {evidence_id} not found"
                )
            
            related_evidence = []
            visited = set([evidence_id])
            queue = [(evidence_id, 0)]
            
            while queue:
                current_id, depth = queue.pop(0)
                
                if depth >= max_depth:
                    continue
                
                # Find all relations from current node
                for edge in self.graph.edges:
                    if edge.source_id == current_id and edge.target_id not in visited:
                        # Apply relation type filter
                        if relation_types and edge.relation_type.value not in relation_types:
                            continue
                        
                        target_node = self.graph.nodes.get(edge.target_id)
                        if target_node:
                            related_evidence.append({
                                "evidence_id": edge.target_id,
                                "evidence_type": target_node.type.value,
                                "evidence_data": target_node.data,
                                "relation_type": edge.relation_type.value,
                                "relation_direction": "outgoing",
                                "relation_strength": edge.metadata.get("strength", "unknown"),
                                "relation_confidence": edge.metadata.get("confidence", "unknown"),
                                "relation_metadata": edge.metadata,
                                "path_depth": depth + 1
                            })
                            
                            visited.add(edge.target_id)
                            if depth + 1 < max_depth:
                                queue.append((edge.target_id, depth + 1))
                    
                    # Also check incoming relations
                    elif edge.target_id == current_id and edge.source_id not in visited:
                        if relation_types and edge.relation_type.value not in relation_types:
                            continue
                        
                        source_node = self.graph.nodes.get(edge.source_id)
                        if source_node:
                            related_evidence.append({
                                "evidence_id": edge.source_id,
                                "evidence_type": source_node.type.value,
                                "evidence_data": source_node.data,
                                "relation_type": edge.relation_type.value,
                                "relation_direction": "incoming",
                                "relation_strength": edge.metadata.get("strength", "unknown"),
                                "relation_confidence": edge.metadata.get("confidence", "unknown"),
                                "relation_metadata": edge.metadata,
                                "path_depth": depth + 1
                            })
                            
                            visited.add(edge.source_id)
                            if depth + 1 < max_depth:
                                queue.append((edge.source_id, depth + 1))
            
            return QueryResult(
                success=True,
                query_type="find_related_evidence",
                evidence_id=evidence_id,
                results=related_evidence,
                count=len(related_evidence),
                message=f"Found {len(related_evidence)} related evidence items (max depth: {max_depth})"
            )
            
        except Exception as e:
            return QueryResult(
                success=False,
                query_type="find_related_evidence",
                evidence_id=evidence_id,
                results=[],
                count=0,
                error=str(e),
                message="Failed to find related evidence"
            )
    
    def trace_provenance(self, evidence_id: str, max_depth: int = 5) -> QueryResult:
        """
        Trace the provenance chain for evidence.
        
        Args:
            evidence_id: ID of evidence to trace
            max_depth: Maximum depth to trace
            
        Returns:
            Query result with provenance trace
        """
        try:
            if evidence_id not in self.graph.nodes:
                return QueryResult(
                    success=False,
                    query_type="trace_provenance",
                    evidence_id=evidence_id,
                    results=[],
                    count=0,
                    message=f"Evidence {evidence_id} not found"
                )
            
            trace_steps = []
            visited = set()
            current_node_id = evidence_id
            depth = 0
            
            # Start with the evidence itself
            start_node = self.graph.nodes[evidence_id]
            trace_steps.append({
                "step_id": f"step_0",
                "node_id": evidence_id,
                "node_type": start_node.type.value,
                "relation_type": "root",
                "metadata": {
                    "is_root": True,
                    "node_data": start_node.data
                },
                "depth": 0
            })
            
            # Trace backwards to find sources
            while depth < max_depth:
                found_source = False
                
                # Look for edges pointing to current node (potential sources)
                for edge in self.graph.edges:
                    if (edge.target_id == current_node_id and 
                        edge.source_id not in visited):
                        
                        source_node = self.graph.nodes.get(edge.source_id)
                        if source_node:
                            step = TraceStep(
                                step_id=f"step_{depth + 1}",
                                node_id=edge.source_id,
                                node_type=source_node.type.value,
                                relation_type=edge.relation_type.value,
                                metadata={
                                    "relation_metadata": edge.metadata,
                                    "node_data": source_node.data
                                },
                                depth=depth + 1
                            )
                            trace_steps.append(step.to_dict())
                            
                            visited.add(edge.source_id)
                            current_node_id = edge.source_id
                            depth += 1
                            found_source = True
                            break
                
                if not found_source:
                    break
            
            # For graph-based provenance, we don't have detailed provenance chain
            # So we'll indicate this limitation
            integrity_valid = True  # Graph nodes are assumed valid unless modified
            
            return QueryResult(
                success=True,
                query_type="trace_provenance",
                evidence_id=evidence_id,
                results=trace_steps,
                count=len(trace_steps),
                integrity_valid=integrity_valid,
                message=f"Provenance trace completed with {len(trace_steps)} steps (max depth: {max_depth})"
            )
            
        except Exception as e:
            return QueryResult(
                success=False,
                query_type="trace_provenance",
                evidence_id=evidence_id,
                results=[],
                count=0,
                error=str(e),
                message="Failed to trace provenance"
            )
    
    def explain_trust_path(self, evidence_id: str, target_type: str) -> QueryResult:
        """
        Explain trust path from evidence to target type.
        
        Args:
            evidence_id: Starting evidence ID
            target_type: Target node type to find path to
            
        Returns:
            Query result with trust path explanation
        """
        try:
            if evidence_id not in self.graph.nodes:
                return QueryResult(
                    success=False,
                    query_type="explain_trust_path",
                    evidence_id=evidence_id,
                    results=[],
                    count=0,
                    message=f"Evidence {evidence_id} not found"
                )
            
            # Convert target type to enum
            try:
                target_node_type = NodeType(target_type.lower())
            except ValueError:
                return QueryResult(
                    success=False,
                    query_type="explain_trust_path",
                    evidence_id=evidence_id,
                    results=[],
                    count=0,
                    message=f"Invalid target type: {target_type}"
                )
            
            # Find path from evidence to target type
            path = self._find_path_to_type(evidence_id, target_node_type)
            
            if path:
                path_explanation = {
                    "source_evidence": evidence_id,
                    "target_type": target_type,
                    "path_found": True,
                    "path_length": len(path),
                    "path_steps": []
                }
                
                for i, step in enumerate(path):
                    path_explanation["path_steps"].append({
                        "step": i,
                        "from": step["from_id"],
                        "from_type": step["from_type"],
                        "to": step["to_id"],
                        "to_type": step["to_type"],
                        "relation": step["relation_type"],
                        "metadata": step["metadata"]
                    })
                
                return QueryResult(
                    success=True,
                    query_type="explain_trust_path",
                    evidence_id=evidence_id,
                    results=[path_explanation],
                    count=1,
                    message=f"Found trust path from {evidence_id} to {target_type} ({len(path)} steps)"
                )
            else:
                return QueryResult(
                    success=True,
                    query_type="explain_trust_path",
                    evidence_id=evidence_id,
                    results=[{
                        "source_evidence": evidence_id,
                        "target_type": target_type,
                        "path_found": False,
                        "path_length": 0,
                        "message": "No direct trust path found"
                    }],
                    count=1,
                    message=f"No trust path found from {evidence_id} to {target_type}"
                )
                
        except Exception as e:
            return QueryResult(
                success=False,
                query_type="explain_trust_path",
                evidence_id=evidence_id,
                results=[],
                count=0,
                error=str(e),
                message="Failed to explain trust path"
            )
    
    def _find_path_to_type(self, start_id: str, target_type: NodeType, 
                          visited: Optional[Set[str]] = None, path: Optional[List] = None) -> Optional[List]:
        """
        Helper method to find path to target type.
        """
        if visited is None:
            visited = set()
        if path is None:
            path = []
        
        if start_id in visited:
            return None
        
        visited.add(start_id)
        
        # Check if current node is target type
        current_node = self.graph.nodes.get(start_id)
        if current_node and current_node.type == target_type:
            return path
        
        # Find all outgoing relations
        for edge in self.graph.edges:
            if edge.source_id == start_id and edge.target_id not in visited:
                target_node = self.graph.nodes.get(edge.target_id)
                if target_node:
                    new_path = path + [{
                        "from_id": start_id,
                        "from_type": current_node.type.value if current_node else "unknown",
                        "to_id": edge.target_id,
                        "to_type": target_node.type.value,
                        "relation_type": edge.relation_type.value,
                        "metadata": edge.metadata
                    }]
                    
                    result = self._find_path_to_type(edge.target_id, target_type, visited, new_path)
                    if result:
                        return result
        
        return None
    
    def get_graph_summary(self) -> Dict[str, Any]:
        """
        Get summary of the graph structure.
        
        Returns:
            Graph summary statistics
        """
        try:
            node_counts = {
                node_type.value: 0 for node_type in NodeType
            }
            
            for node in self.graph.nodes.values():
                node_counts[node.type.value] += 1
            
            relation_counts = {
                relation_type.value: 0 for relation_type in RelationType
            }
            
            for edge in self.graph.edges:
                relation_counts[edge.relation_type.value] += 1
            
            return {
                "total_nodes": len(self.graph.nodes),
                "total_edges": len(self.graph.edges),
                "node_counts": node_counts,
                "relation_counts": relation_counts,
                "graph_density": len(self.graph.edges) / (len(self.graph.nodes) * (len(self.graph.nodes) - 1)) if len(self.graph.nodes) > 1 else 0
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "total_nodes": 0,
                "total_edges": 0,
                "node_counts": {},
                "relation_counts": {},
                "graph_density": 0
            }