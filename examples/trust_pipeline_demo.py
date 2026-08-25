"""
Trust Pipeline Demo

Demonstrates the complete trust pipeline:
Mock Policy Evidence → Create Evidence Object → Create Provenance → Calculate Trust Score → Graph Query

OpenInvest - Trust Evidence Prototype
"""

import json
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from trust.evidence_object import EvidenceObject, VerificationStatus
from trust.provenance import ProvenanceChain
from trust.trust_score import TrustScoreCalculator
from trust.evidence_graph import EvidenceGraph, NodeType, RelationType


def load_demo_data():
    """Load demo data from JSON files."""
    demo_dir = os.path.join(os.path.dirname(__file__), 'trust_demo')
    
    # Load policy data
    with open(os.path.join(demo_dir, 'policy_example.json'), 'r', encoding='utf-8') as f:
        policy_data = json.load(f)
    
    # Load company data  
    with open(os.path.join(demo_dir, 'company_example.json'), 'r', encoding='utf-8') as f:
        company_data = json.load(f)
    
    # Load evidence data
    with open(os.path.join(demo_dir, 'evidence_example.json'), 'r', encoding='utf-8') as f:
        evidence_data = json.load(f)
    
    return policy_data, company_data, evidence_data


def step1_create_evidence_object(policy_data, company_data, evidence_data):
    """Step 1: Create Evidence Objects from demo data."""
    print("=== Step 1: Create Evidence Objects ===")
    
    # Create policy evidence object
    policy_evidence = EvidenceObject(
        id=policy_data["id"],
        type=policy_data["type"],
        source=policy_data["source"],
        source_reference=policy_data["source_reference"],
        verification_status=VerificationStatus.MOCK,
        confidence_score=0.8,
        metadata=policy_data
    )
    
    # Create company evidence object
    company_evidence = EvidenceObject(
        id=company_data["id"],
        type=company_data["type"],
        source=company_data["source"],
        source_reference=company_data.get("registration_number", ""),
        verification_status=VerificationStatus.MOCK,
        confidence_score=0.7,
        metadata=company_data
    )
    
    # Create evidence evidence object
    evidence_evidence = EvidenceObject(
        id=evidence_data["id"],
        type=evidence_data["type"],
        source=evidence_data["source"],
        source_reference=evidence_data["source_reference"],
        verification_status=VerificationStatus.MOCK,
        confidence_score=evidence_data["confidence_score"],
        metadata=evidence_data
    )
    
    print(f"Policy Evidence Created: {policy_evidence}")
    print(f"Company Evidence Created: {company_evidence}")
    print(f"Evidence Evidence Created: {evidence_evidence}")
    
    return policy_evidence, company_evidence, evidence_evidence


def step2_create_provenance_chains(evidence_objects):
    """Step 2: Create provenance chains for each evidence."""
    print("\n=== Step 2: Create Provenance Chains ===")
    
    provenance_chains = {}
    
    for evidence in evidence_objects:
        chain = ProvenanceChain(evidence.id)
        
        # Add mock verification events
        if "policy" in evidence.id.lower():
            chain.add_verification_event(
                verifier="mock_policy_analyst",
                method="policy_document_review",
                result="approved"
            )
        elif "company" in evidence.id.lower():
            chain.add_verification_event(
                verifier="mock_business_analyst", 
                method="company_document_review",
                result="verified"
            )
        else:
            chain.add_verification_event(
                verifier="mock_trust_analyst",
                method="evidence_cross_reference",
                result="confirmed"
            )
        
        # Add mock trust assessments
        chain.add_trust_assessment(
            assessor="mock_trust_system",
            score=evidence.confidence_score,
            reason="mock_assessment"
        )
        
        provenance_chains[evidence.id] = chain
        print(f"Provenance Chain Created for {evidence.id}")
    
    return provenance_chains


def step3_calculate_trust_scores(evidence_objects):
    """Step 3: Calculate trust scores for evidence objects."""
    print("\n=== Step 3: Calculate Trust Scores ===")
    
    calculator = TrustScoreCalculator()
    trust_scores = {}
    
    for evidence in evidence_objects:
        # Convert evidence to dict for score calculation
        evidence_dict = evidence.to_dict()
        
        # Calculate trust score
        score_result = calculator.calculate_for_evidence_object(evidence_dict)
        trust_scores[evidence.id] = score_result
        
        print(f"Trust Score for {evidence.id}: {score_result['score']} ({score_result['confidence']})")
        print(f"  Reasons: {', '.join(score_result['reason'])}")
    
    return trust_scores


def step4_build_evidence_graph(evidence_objects):
    """Step 4: Build evidence graph with relations."""
    print("\n=== Step 4: Build Evidence Graph ===")
    
    graph = EvidenceGraph()
    
    # Add nodes for each evidence
    for evidence in evidence_objects:
        data = evidence.metadata.copy()
        data["evidence_object"] = evidence.to_dict()
        
        node_type = None
        if evidence.type == "policy":
            node_type = NodeType.POLICY
        elif evidence.type == "company":
            node_type = NodeType.COMPANY
        elif evidence.type == "evidence":
            node_type = NodeType.EVIDENCE
        
        if node_type:
            graph.add_node(evidence.id, node_type, data)
            print(f"Added Node: {evidence.id} ({node_type.value})")
    
    # Add relations (demonstrating the example: Company A SUPPORTED_BY Policy Evidence X)
    if "company_ai_tech_corp" in graph.nodes and "policy_ai_national_framework_2024" in graph.nodes:
        graph.add_relation(
            source_id="company_ai_tech_corp",
            target_id="policy_ai_national_framework_2024", 
            relation_type=RelationType.BENEFITS_FROM,
            metadata={"strength": "strategic", "is_mock": True}
        )
        print("Added Relation: company_ai_tech_corp BENEFITS_FROM policy_ai_national_framework_2024")
    
    if "evidence_policy_support_ai" in graph.nodes:
        # Connect evidence to policy
        graph.add_relation(
            source_id="evidence_policy_support_ai",
            target_id="policy_ai_national_framework_2024",
            relation_type=RelationType.DERIVED_FROM,
            metadata={"confidence": "high", "is_mock": True}
        )
        print("Added Relation: evidence_policy_support_ai DERIVED_FROM policy_ai_national_framework_2024")
        
        # Connect evidence to company
        graph.add_relation(
            source_id="company_ai_tech_corp", 
            target_id="evidence_policy_support_ai",
            relation_type=RelationType.SUPPORTED_BY,
            metadata={"type": "policy_support", "is_mock": True}
        )
        print("Added Relation: company_ai_tech_corp SUPPORTED_BY evidence_policy_support_ai")
    
    return graph


def step5_query_trust_pipeline(graph, trust_scores, provenance_chains):
    """Step 5: Query the trust pipeline results."""
    print("\n=== Step 5: Query Trust Pipeline Results ===")
    
    # Query company evidence and its relations
    company_query = graph.query_evidence("company_ai_tech_corp")
    if company_query:
        print(f"Company Query Results:")
        print(f"  Node: {company_query['node']['id']} ({company_query['node']['type']})")
        print(f"  Incoming Relations: {len(company_query['incoming_relations'])}")
        print(f"  Outgoing Relations: {len(company_query['outgoing_relations'])}")
        print(f"  Related Nodes: {company_query['related_nodes']}")
    
    # Show trust score
    company_score = trust_scores.get("company_ai_tech_corp", {})
    print(f"\nCompany Trust Score: {company_score.get('score', 'N/A')}")
    print(f"  Confidence: {company_score.get('confidence', 'N/A')}")
    print(f"  Reasons: {', '.join(company_score.get('reason', []))}")
    
    # Show provenance chain
    company_chain = provenance_chains.get("company_ai_tech_corp")
    if company_chain:
        print(f"\nCompany Provenance Chain:")
        print(company_chain.get_trust_chain())
    
    return company_query


def main():
    """Main trust pipeline demo."""
    print("OpenInvest Trust Pipeline Demo")
    print("=" * 50)
    
    try:
        # Step 1: Load demo data
        print("\nLoading demo data...")
        policy_data, company_data, evidence_data = load_demo_data()
        print("Demo data loaded successfully")
        
        # Step 2: Create evidence objects
        policy_evidence, company_evidence, evidence_evidence = step1_create_evidence_objects(
            policy_data, company_data, evidence_data
        )
        
        # Step 3: Create provenance chains
        evidence_objects = [policy_evidence, company_evidence, evidence_evidence]
        provenance_chains = step2_create_provenance_chains(evidence_objects)
        
        # Step 4: Calculate trust scores
        trust_scores = step3_calculate_trust_scores(evidence_objects)
        
        # Step 5: Build evidence graph
        graph = step4_build_evidence_graph(evidence_objects)
        
        # Step 6: Query pipeline results
        query_results = step5_query_trust_pipeline(graph, trust_scores, provenance_chains)
        
        # Final summary
        print("\n" + "=" * 50)
        print("TRUST PIPELINE DEMO SUMMARY")
        print("=" * 50)
        
        print(f"✅ Evidence Objects Created: {len(evidence_objects)}")
        print(f"✅ Provenance Chains Built: {len(provenance_chains)}")
        print(f"✅ Trust Scores Calculated: {len(trust_scores)}")
        print(f"✅ Graph Nodes Added: {len(graph.nodes)}")
        print(f"✅ Graph Relations Added: {len(graph.edges)}")
        
        print(f"\n🎯 Key Results:")
        print(f"   Company Trust Score: {trust_scores.get('company_ai_tech_corp', {}).get('score', 'N/A')}")
        print(f"   Graph Relations: {len(graph.edges)} connections")
        print(f"   All Data Marked as MOCK: {all(data.get('is_mock', False) for data in [policy_data, company_data, evidence_data])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)