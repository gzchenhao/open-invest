"""Run Mock Investment Agent Demo

Demonstrates the OpenInvest Trust Evidence API Boundary
with a simulated DeepTech investment agent.

OpenInvest - Trust Evidence API Boundary
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from mock_investment_agent import MockInvestmentAgent


def demo_trust_evidence_api():
    """Demonstrate the Trust Evidence API with mock agent."""
    
    print("[OPENINVEST] Trust Evidence API Demo")
    print("Mock Investment Agent Simulation")
    print("=" * 60)
    
    # Create mock agent
    agent = MockInvestmentAgent()
    
    # Demo scenarios
    scenarios = [
        ("company_mock_001", "AI Technology Company"),
        ("policy_mock_001", "Government Policy Support"),
        ("tech_mock_001", "Emerging Technology")
    ]
    
    for company_id, description in scenarios:
        print(f"\n[SCENARIO] {description}")
        print("-" * 40)
        
        try:
            # Run assessment
            decision = agent.assess_company_trustworthiness(company_id)
            
            # Display key results
            print(f"Company: {decision.company_name}")
            print(f"Trust Score: {decision.decision_score:.2f}/100")
            print(f"Confidence: {decision.confidence_level}")
            print(f"Recommendation: {decision.recommendation}")
            
            # Show key risk factors
            if decision.risk_factors:
                print(f"Key Risks: {', '.join(decision.risk_factors[:2])}")
            
            print(f"Status: {'[SUCCESS] Assessment Complete' if decision.decision_score > 0 else '[FAILED] Assessment Failed'}")
            
        except Exception as e:
            print(f"[ERROR] Demo failed: {e}")
    
    print("\n" + "=" * 60)
    print("[DEMO SUMMARY]:")
    print("- Mock Agent successfully demonstrates trust-aware decision making")
    print("- API provides detailed confidence and reasoning")
    print("- All results include proper disclaimers about prototype status")
    print("- Shows future potential for DeepTech investment agents")
    print("=" * 60)


if __name__ == "__main__":
    demo_trust_evidence_api()