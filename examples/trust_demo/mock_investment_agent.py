"""Mock Investment Agent for OpenInvest Trust Evidence System

Demonstration of how a DeepTech investment agent would use
the OpenInvest Trust Evidence Service to make informed decisions.

OpenInvest - Trust Evidence API Boundary
"""

import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.trust.trust_service import TrustEvidenceService
from src.trust.trust_query_contract import TrustQueryContract, TrustQueryExecutor, TrustQueryType
from src.trust.trust_request_response import TrustEvidenceRequest, TrustEvidenceResponse, EvidenceType


@dataclass
class InvestmentDecision:
    """Investment decision result"""
    company_name: str
    decision_score: float
    confidence_level: str
    reasoning: List[str]
    risk_factors: List[str]
    trust_assessment: Dict[str, Any]
    recommendation: str
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MockInvestmentAgent:
    """
    Mock investment agent that demonstrates how a DeepTech agent
    would use the OpenInvest Trust Evidence Service.
    """
    
    def __init__(self):
        """Initialize the mock investment agent."""
        self.trust_service = TrustEvidenceService()
        self.query_executor = TrustQueryExecutor(self.trust_service)
        self.agent_name = "OpenInvest Mock Investment Agent"
        self.version = "1.0.0-experimental"
        self.description = "Demonstrates trust-aware investment decision making"
    
    def assess_company_trustworthiness(self, company_evidence_id: str) -> InvestmentDecision:
        """
        Assess the trustworthiness of a company based on evidence.
        
        Args:
            company_evidence_id: ID of company evidence to assess
            
        Returns:
            Investment decision with detailed reasoning
        """
        print(f"[AGENT] {self.agent_name}: Assessing trustworthiness of company {company_evidence_id}")
        
        try:
            # Step 1: Get basic company information
            print("[STEP1] Retrieving company evidence...")
            company_result = self.trust_service.get_evidence(company_evidence_id)
            
            if not company_result["success"]:
                return InvestmentDecision(
                    company_name=company_evidence_id,
                    decision_score=0.0,
                    confidence_level="none",
                    reasoning=[f"Failed to retrieve company evidence: {company_result.get('error', 'unknown')}"],
                    risk_factors=["Evidence unavailable"],
                    trust_assessment={},
                    recommendation="UNABLE TO ASSESS - NO EVIDENCE",
                    explanation="Cannot make investment decision without valid evidence"
                )
            
            company_data = company_result["evidence"]
            company_name = company_data.get("name", company_evidence_id)
            print(f"[COMPANY] {company_name}")
            
            # Step 2: Calculate trust score
            print("[STEP2] Calculating trust score...")
            trust_result = self.trust_service.calculate_trust(company_evidence_id)
            
            if not trust_result["success"]:
                print(f"[WARNING] Trust calculation failed: {trust_result.get('error')}")
                return self._create_default_decision(company_name, company_evidence_id)
            
            trust_score = trust_result["trust_score"]
            confidence = trust_result["confidence"]
            reasons = trust_result.get("reason", [])
            integrity_valid = trust_result.get("integrity_valid", False)
            verification_status = trust_result.get("verification_status", "UNVERIFIED")
            
            print(f"[SCORE] Trust Score: {trust_score:.2f} (confidence: {confidence})")
            print(f"[INTEGRITY] Integrity Valid: {integrity_valid}")
            print(f"[VERIFICATION] Verification Status: {verification_status}")
            
            # Step 3: Ask trust-related questions
            print("[STEP3] Investigating trust factors...")
            trust_questions = [
                (TrustQueryType.WHY_TRUST, "Why should I trust this company?"),
                (TrustQueryType.WHERE_CAME_FROM, "Where did this evidence come from?"),
                (TrustQueryType.HAS_MODIFIED, "Has this evidence been modified?"),
                (TrustQueryType.WHAT_SUPPORTS, "What evidence supports this company?"),
                (TrustQueryType.WHAT_UNVERIFIED, "What is still unverified?")
            ]
            
            query_results = []
            for query_type, question in trust_questions:
                try:
                    query_contract = TrustQueryContract(
                        evidence_id=company_evidence_id,
                        query_type=query_type
                    )
                    query_result = self.query_executor.execute_query(query_contract)
                    query_results.append((question, query_result))
                    
                    if query_result.success:
                        print(f"[OK] {question}")
                        if hasattr(query_result, 'query_result') and query_result.query_result:
                            print(f"  Answer: {str(query_result.query_result)[:100]}...")
                    else:
                        print(f"[ERROR] {question}: {query_result.error}")
                        
                except Exception as e:
                    print(f"[WARNING] Query failed: {e}")
            
            # Step 4: Find supporting evidence
            print("[STEP4] Finding supporting evidence...")
            supporting_result = self.trust_service.query_evidence_graph(
                "find_supporting_evidence",
                evidence_id=company_evidence_id
            )
            
            supporting_count = 0
            if supporting_result["success"]:
                supporting_count = supporting_result.get("count", 0)
                print(f"[FOUND] {supporting_count} supporting evidence items")
            
            # Step 5: Generate risk factors
            risk_factors = self._identify_risk_factors(
                trust_result, 
                verification_status,
                integrity_valid,
                supporting_count
            )
            
            # Step 6: Make recommendation
            recommendation = self._generate_recommendation(
                trust_score,
                confidence,
                verification_status,
                supporting_count,
                risk_factors
            )
            
            # Step 7: Build final decision
            final_reasoning = reasons.copy()
            final_reasoning.extend([
                f"Trust score: {trust_score:.2f}",
                f"Confidence level: {confidence}",
                f"Supporting evidence: {supporting_count} items",
                f"Integrity status: {'valid' if integrity_valid else 'compromised'}"
            ])
            
            final_reasoning.extend([f"Risk: {risk}" for risk in risk_factors])
            
            return InvestmentDecision(
                company_name=company_name,
                decision_score=trust_score,
                confidence_level=confidence,
                reasoning=final_reasoning,
                risk_factors=risk_factors,
                trust_assessment=trust_result,
                recommendation=recommendation,
                explanation=self._generate_explanation(
                    company_name, trust_result, query_results, recommendation
                )
            )
            
        except Exception as e:
            print(f"[ERROR] Error during assessment: {e}")
            return InvestmentDecision(
                company_name=company_name if 'company_name' in locals() else company_evidence_id,
                decision_score=0.0,
                confidence_level="error",
                reasoning=[f"Assessment failed: {str(e)}"],
                risk_factors=["System error"],
                trust_assessment={},
                recommendation="UNABLE TO ASSESS - SYSTEM ERROR",
                explanation="Investment decision system encountered an error"
            )
    
    def _identify_risk_factors(self, trust_result: Dict[str, Any], 
                              verification_status: str,
                              integrity_valid: bool,
                              supporting_count: int) -> List[str]:
        """Identify potential risk factors."""
        risk_factors = []
        
        # Check verification status
        if verification_status == "UNVERIFIED":
            risk_factors.append("Evidence not independently verified")
        elif verification_status == "MOCK":
            risk_factors.append("Based on prototype demonstration data")
        
        # Check integrity
        if not integrity_valid:
            risk_factors.append("Provenance chain integrity compromised")
        
        # Check supporting evidence
        if supporting_count == 0:
            risk_factors.append("No supporting evidence available")
        elif supporting_count < 2:
            risk_factors.append("Limited supporting evidence")
        
        # Check trust score
        trust_score = trust_result.get("trust_score", 0)
        if trust_score < 30:
            risk_factors.append("Low trust score")
        elif trust_score < 50:
            risk_factors.append("Moderate trust score")
        
        # Check confidence
        confidence = trust_result.get("confidence", "low")
        if confidence == "low":
            risk_factors.append("Low confidence in assessment")
        
        return risk_factors
    
    def _generate_recommendation(self, trust_score: float, confidence: str,
                               verification_status: str, supporting_count: int,
                               risk_factors: List[str]) -> str:
        """Generate investment recommendation."""
        
        # Base recommendation on trust score
        if trust_score >= 80:
            base_recommendation = "STRONG BUY"
        elif trust_score >= 60:
            base_recommendation = "BUY"
        elif trust_score >= 40:
            base_recommendation = "HOLD"
        elif trust_score >= 20:
            base_recommendation = "SELL"
        else:
            base_recommendation = "STRONG SELL"
        
        # Adjust based on verification status
        if verification_status == "MOCK":
            return f"DEMONSTRATION ONLY - {base_recommendation} (Prototype Data)"
        elif verification_status == "UNVERIFIED":
            return f"{base_recommendation} (UNVERIFIED - REQUIRES DUE DILIGENCE)"
        else:
            return base_recommendation
    
    def _generate_explanation(self, company_name: str, trust_result: Dict[str, Any],
                            query_results: List[tuple], recommendation: str) -> str:
        """Generate detailed explanation for the recommendation."""
        
        explanation = f"Investment recommendation for {company_name}: {recommendation}\n\n"
        explanation += "This recommendation is based on the following factors:\n\n"
        
        # Add trust assessment explanation
        trust_score = trust_result.get("trust_score", 0)
        confidence = trust_result.get("confidence", "unknown")
        explanation += f"• Trust Score: {trust_score:.2f} ({confidence} confidence)\n"
        
        # Add verification status
        verification_status = trust_result.get("verification_status", "unknown")
        explanation += f"• Verification Status: {verification_status}\n"
        
        # Add integrity status
        integrity_valid = trust_result.get("integrity_valid", False)
        explanation += f"• Data Integrity: {'Verified' if integrity_valid else 'Issues detected'}\n"
        
        # Add query results
        explanation += "\nKey findings from trust investigation:\n"
        for question, result in query_results:
            if result.success and hasattr(result, 'query_result'):
                result_summary = str(result.query_result)[:100]
                explanation += f"• {question}: {result_summary}...\n"
        
        # Add important disclaimer
        explanation += f"\n⚠️  IMPORTANT: This is a demonstration using prototype experimental data. "
        explanation += f"The recommendation '{recommendation}' is based on mock evidence and should not be used for actual investment decisions. "
        explanation += f"Always conduct proper due diligence before making investment choices.\n"
        
        return explanation
    
    def _create_default_decision(self, company_name: str, company_id: str) -> InvestmentDecision:
        """Create a default decision when assessment fails."""
        return InvestmentDecision(
            company_name=company_name,
            decision_score=0.0,
            confidence_level="none",
            reasoning=["Unable to complete trust assessment"],
            risk_factors=["Assessment system error"],
            trust_assessment={},
            recommendation="UNABLE TO ASSESS",
            explanation="Trust assessment system encountered an error and could not complete evaluation"
        )
    
    def demonstrate_investment_workflow(self):
        """Demonstrate the complete investment workflow."""
        print("[START] Starting Mock Investment Agent Demo")
        print("=" * 50)
        
        # Demo 1: Assess a company
        company_id = "company_mock_001"
        print(f"\n[DEMO1] Assessing Company {company_id}")
        print("-" * 30)
        
        decision = self.assess_company_trustworthiness(company_id)
        
        # Display results
        print("\n[DECISION] INVESTMENT DECISION")
        print("=" * 30)
        print(f"Company: {decision.company_name}")
        print(f"Decision Score: {decision.decision_score:.2f}")
        print(f"Confidence: {decision.confidence_level}")
        print(f"Recommendation: {decision.recommendation}")
        
        print(f"\n📝 Reasoning:")
        for reason in decision.reasoning:
            print(f"  • {reason}")
        
        print(f"\n⚠️  Risk Factors:")
        for risk in decision.risk_factors:
            print(f"  • {risk}")
        
        print(f"\n[ASSESSMENT] Full Assessment:")
        print(decision.explanation)
        
        # Demo 2: Show system status
        print(f"\n[DEMO2] Trust Evidence Service Status")
        print("-" * 30)
        status = self.trust_service.get_service_status()
        if status["success"]:
            service_info = status["status"]
            print(f"Service: {service_info['service_name']}")
            print(f"Version: {service_info['version']}")
            print(f"Ready: {service_info['is_ready']}")
            print(f"Capabilities: {', '.join(service_info['capabilities'])}")
            print(f"Limitations: {', '.join(service_info['limitations'])}")
        
        print(f"\n[COMPLETE] Demo Complete!")
        print("=" * 50)
        print("This demonstrates how a DeepTech investment agent would use")
        print("the OpenInvest Trust Evidence Service to make informed decisions.")
        print("\nKey takeaway: The service provides trust-aware decision making")
        print("with clear explanations of why certain recommendations are made.")


def main():
    """Main function to run the mock investment agent demo."""
    agent = MockInvestmentAgent()
    agent.demonstrate_investment_workflow()


if __name__ == "__main__":
    main()