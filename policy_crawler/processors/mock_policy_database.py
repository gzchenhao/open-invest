"""
Mock Policy Database Service
Provides sample policy data and demonstrates policy cleaning functionality
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from .policy_structurer import StructuredPolicy, PolicyDataStructurer


@dataclass
class MockPolicyData:
    """Mock policy data for demonstration"""
    
    jurisdiction: str
    tech_hub: str
    policy_type: str
    title: str
    description: str
    incentives: Dict[str, Any]
    requirements: Dict[str, Any]
    compliance: Dict[str, Any]


class MockPolicyDatabase:
    """Mock policy database for demonstration purposes"""
    
    def __init__(self):
        self.policies = []
        self.structurer = PolicyDataStructurer()
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize mock policy data"""
        
        # Shanghai Silicon Valley Policy
        shanghai_policy = {
            "jurisdiction": "China",
            "tech_hub": "Shanghai",
            "policy_type": "tax_incentive",
            "title": "Shanghai Silicon Valley Policy 2024",
            "description": "Comprehensive policy for AI and robotics companies establishing in Shanghai's tech parks",
            "incentives": {
                "tax_incentives": [
                    {
                        "type": "rd_tax_credit",
                        "description": "R&D tax credit of 30% on qualified R&D expenses",
                        "rate_reduction": 30.0,
                        "duration_years": 5,
                        "eligibility_criteria": ["AI/ML company", "Minimum 10 employees", "R&D expenditure > $1M"]
                    },
                    {
                        "type": "corporate_tax_reduction",
                        "description": "Corporate tax reduction from 25% to 15% for tech companies",
                        "rate_reduction": 10.0,
                        "duration_years": 3,
                        "eligibility_criteria": ["Tech company", "Annual revenue > $5M", "Local employment > 50"]
                    }
                ],
                "financial_subsidies": [
                    {
                        "type": "rd_grant",
                        "description": "R&D grant up to $2M for AI and robotics projects",
                        "amount_usd": 2000000,
                        "purpose": "AI and robotics R&D",
                        "eligibility_criteria": ["AI/ML project", "Technical innovation", "Market potential"]
                    },
                    {
                        "type": "equipment_subsidy",
                        "description": "50% subsidy on equipment purchases",
                        "amount_usd": 500000,
                        "purpose": "Equipment purchase",
                        "eligibility_criteria": ["New equipment", "Tech-related", "Local employment"]
                    }
                ],
                "land_and_infrastructure": [
                    {
                        "type": "land_grant",
                        "description": "Free land usage for 5 years in tech parks",
                        "area_sqm": 1000,
                        "duration_years": 5,
                        "location": "Shanghai Zhangjiang Hi-Tech Park"
                    },
                    {
                        "type": "factory_rent_reduction",
                        "description": "70% reduction in factory rent for first 3 years",
                        "rent_reduction_percentage": 70.0,
                        "duration_years": 3,
                        "location": "Shanghai Free Trade Zone"
                    }
                ]
            },
            "requirements": {
                "staffing_requirements": {
                    "min_employees": 50,
                    "min_researchers": 20,
                    "researcher_percentage": 40,
                    "min_phd_percentage": 10,
                    "min_experience_years": 3
                },
                "financial_requirements": {
                    "min_investment_usd": 5000000,
                    "min_revenue_usd": 10000000
                },
                "intellectual_property": {
                    "min_patents": 5,
                    "min_patents_pending": 3,
                    "patent_field_requirements": ["AI", "Robotics", "Machine Learning"]
                },
                "technology_requirements": {
                    "required_technologies": ["AI", "Machine Learning", "Robotics"],
                    "trl_requirements": ["prototype", "pilot"]
                }
            },
            "compliance": {
                "data_localization": {
                    "required": True,
                    "jurisdiction": "China",
                    "specific_requirements": ["Data storage within China", "Regular data reporting"]
                },
                "export_controls": {
                    "applies": True,
                    "restricted_technologies": ["Quantum computing", "Advanced AI"],
                    "licensing_requirements": ["Export license", "Technology approval"]
                },
                "security_clearance": {
                    "required": True,
                    "clearance_level": "enhanced",
                    "background_check_requirements": ["Criminal background check", "Security clearance"]
                },
                "environmental_compliance": {
                    "required": True,
                    "standards": ["ISO 14001", "Environmental protection law"],
                    "certification_requirements": ["Environmental impact assessment"]
                },
                "labor_compliance": {
                    "required": True,
                    "labor_laws": ["Chinese labor law", "Social security requirements"],
                    "benefit_requirements": ["Health insurance", "Pension", "Housing fund"]
                }
            }
        }
        
        # Silicon Valley AI Policy
        silicon_valley_policy = {
            "jurisdiction": "USA",
            "tech_hub": "Silicon Valley",
            "policy_type": "subsidy",
            "title": "Silicon Valley AI Innovation Grant 2024",
            "description": "Grant program for AI startups focusing on ethical AI and social impact",
            "incentives": {
                "tax_incentives": [
                    {
                        "type": "corporate_tax_reduction",
                        "description": "Corporate tax reduction for AI companies with social impact",
                        "rate_reduction": 15.0,
                        "duration_years": 7,
                        "eligibility_criteria": ["AI company", "Social impact focus", "US-based"]
                    }
                ],
                "financial_subsidies": [
                    {
                        "type": "startup_capital",
                        "description": "Startup capital grant up to $1M for AI startups",
                        "amount_usd": 1000000,
                        "purpose": "Startup capital",
                        "eligibility_criteria": ["AI startup", "Innovative technology", "US-based team"]
                    },
                    {
                        "type": "rd_grant",
                        "description": "R&D grant for ethical AI research",
                        "amount_usd": 500000,
                        "purpose": "Ethical AI research",
                        "eligibility_criteria": ["Ethical AI focus", "Research collaboration", "Public benefit"]
                    }
                ],
                "land_and_infrastructure": [
                    {
                        "type": "facility_subsidy",
                        "description": "Free co-working space for 12 months",
                        "duration_years": 1,
                        "location": "Silicon Valley Innovation Center"
                    }
                ]
            },
            "requirements": {
                "staffing_requirements": {
                    "min_employees": 10,
                    "min_researchers": 5,
                    "researcher_percentage": 50,
                    "min_experience_years": 2
                },
                "financial_requirements": {
                    "min_investment_usd": 100000
                },
                "intellectual_property": {
                    "min_patents": 2,
                    "patent_field_requirements": ["AI Ethics", "Machine Learning"]
                },
                "technology_requirements": {
                    "required_technologies": ["AI", "Machine Learning", "Ethics"],
                    "trl_requirements": ["proof_of_concept", "prototype"]
                }
            },
            "compliance": {
                "data_localization": {
                    "required": False
                },
                "export_controls": {
                    "applies": True,
                    "restricted_technologies": ["Advanced AI", "Dual-use technologies"],
                    "licensing_requirements": ["Export compliance", "Technology transfer review"]
                },
                "security_clearance": {
                    "required": False
                },
                "environmental_compliance": {
                    "required": False
                },
                "labor_compliance": {
                    "required": True,
                    "labor_laws": ["US labor law", "Fair employment practices"],
                    "benefit_requirements": ["Health insurance", "Retirement plan"]
                }
            }
        }
        
        # EU Quantum Computing Policy
        eu_policy = {
            "jurisdiction": "EU",
            "tech_hub": "Berlin",
            "policy_type": "investment_promotion",
            "title": "EU Quantum Computing Initiative 2024",
            "description": "Comprehensive support for quantum computing startups and research",
            "incentives": {
                "tax_incentives": [
                    {
                        "type": "rd_tax_credit",
                        "description": "R&D tax credit of 40% for quantum computing research",
                        "rate_reduction": 40.0,
                        "duration_years": 10,
                        "eligibility_criteria": ["Quantum computing research", "EU-based", "Collaborative research"]
                    }
                ],
                "financial_subsidies": [
                    {
                        "type": "rd_grant",
                        "description": "Quantum computing research grant up to €5M",
                        "amount_usd": 5500000,
                        "purpose": "Quantum computing research",
                        "eligibility_criteria": ["Quantum computing", "Research excellence", "EU collaboration"]
                    },
                    {
                        "type": "equipment_subsidy",
                        "description": "80% subsidy on quantum computing equipment",
                        "amount_usd": 2000000,
                        "purpose": "Quantum computing equipment",
                        "eligibility_criteria": ["Quantum equipment", "Research institution", "EU-based"]
                    }
                ],
                "land_and_infrastructure": [
                    {
                        "type": "facility_subsidy",
                        "description": "Free access to quantum computing facilities",
                        "duration_years": 5,
                        "location": "Berlin Quantum Hub"
                    }
                ]
            },
            "requirements": {
                "staffing_requirements": {
                    "min_employees": 20,
                    "min_researchers": 15,
                    "researcher_percentage": 75,
                    "min_phd_percentage": 30,
                    "min_experience_years": 5
                },
                "financial_requirements": {
                    "min_investment_usd": 2000000
                },
                "intellectual_property": {
                    "min_patents": 10,
                    "min_patents_pending": 5,
                    "patent_field_requirements": ["Quantum computing", "Quantum algorithms", "Quantum hardware"]
                },
                "technology_requirements": {
                    "required_technologies": ["Quantum computing", "Quantum algorithms", "Quantum hardware"],
                    "trl_requirements": ["proof_of_concept", "prototype", "pilot"]
                }
            },
            "compliance": {
                "data_localization": {
                    "required": True,
                    "jurisdiction": "EU",
                    "specific_requirements": ["GDPR compliance", "Data storage within EU"]
                },
                "export_controls": {
                    "applies": True,
                    "restricted_technologies": ["Quantum technologies", "Cryptography"],
                    "licensing_requirements": ["EU export license", "Dual-use technology license"]
                },
                "security_clearance": {
                    "required": False
                },
                "environmental_compliance": {
                    "required": True,
                    "standards": ["EU environmental standards", "Green computing"],
                    "certification_requirements": ["Environmental management system"]
                },
                "labor_compliance": {
                    "required": True,
                    "labor_laws": ["EU labor law", "Working time directive"],
                    "benefit_requirements": ["Health insurance", "Pension", "Paid leave"]
                }
            }
        }
        
        # Singapore Biotech Policy
        singapore_policy = {
            "jurisdiction": "Singapore",
            "tech_hub": "One North",
            "policy_type": "land_grant",
            "title": "Singapore Biotech Innovation Policy 2024",
            "description": "Comprehensive support for biotech companies in Singapore's biomedical hub",
            "incentives": {
                "tax_incentives": [
                    {
                        "type": "rd_tax_credit",
                        "description": "R&D tax credit of 250% for biotech research",
                        "rate_reduction": 150.0,
                        "duration_years": 10,
                        "eligibility_criteria": ["Biotech research", "Clinical trials", "Commercialization"]
                    }
                ],
                "financial_subsidies": [
                    {
                        "type": "rd_grant",
                        "description": "Biotech research grant up to SGD 10M",
                        "amount_usd": 7500000,
                        "purpose": "Biotech research",
                        "eligibility_criteria": ["Biotech company", "Research innovation", "Clinical trials"]
                    },
                    {
                        "type": "training_subsidy",
                        "description": "90% subsidy for employee training",
                        "amount_usd": 100000,
                        "purpose": "Employee training",
                        "eligibility_criteria": ["Biotech training", "Skills development", "Local employment"]
                    }
                ],
                "land_and_infrastructure": [
                    {
                        "type": "land_grant",
                        "description": "Free land usage for 10 years in biomedical hub",
                        "area_sqm": 2000,
                        "duration_years": 10,
                        "location": "One North Biomedical Park"
                    },
                    {
                        "type": "facility_subsidy",
                        "description": "Free access to biomedical facilities",
                        "duration_years": 5,
                        "location": "Singapore Biomedical Hub"
                    }
                ]
            },
            "requirements": {
                "staffing_requirements": {
                    "min_employees": 30,
                    "min_researchers": 20,
                    "researcher_percentage": 67,
                    "min_phd_percentage": 20,
                    "min_experience_years": 3
                },
                "financial_requirements": {
                    "min_investment_usd": 3000000,
                    "min_revenue_usd": 5000000
                },
                "intellectual_property": {
                    "min_patents": 8,
                    "min_patents_pending": 5,
                    "patent_field_requirements": ["Biotech", "Pharmaceuticals", "Medical devices"]
                },
                "technology_requirements": {
                    "required_technologies": ["Biotech", "Pharmaceuticals", "Medical devices"],
                    "trl_requirements": ["pilot", "production"]
                }
            },
            "compliance": {
                "data_localization": {
                    "required": False
                },
                "export_controls": {
                    "applies": True,
                    "restricted_technologies": ["Biotechnology", "Medical devices"],
                    "licensing_requirements": ["Health authority approval", "Export license"]
                },
                "security_clearance": {
                    "required": False
                },
                "environmental_compliance": {
                    "required": True,
                    "standards": ["Singapore environmental standards", "Waste management"],
                    "certification_requirements": ["Environmental compliance certificate"]
                },
                "labor_compliance": {
                    "required": True,
                    "labor_laws": ["Singapore labor law", "Work permit requirements"],
                    "benefit_requirements": ["Health insurance", "CPF contributions", "Training benefits"]
                }
            }
        }
        
        self.policies = [shanghai_policy, silicon_valley_policy, eu_policy, singapore_policy]
    
    def get_all_policies(self) -> List[MockPolicyData]:
        """Get all mock policies"""
        return [MockPolicyData(**policy) for policy in self.policies]
    
    def get_policies_by_jurisdiction(self, jurisdiction: str) -> List[MockPolicyData]:
        """Get policies by jurisdiction"""
        return [
            MockPolicyData(**policy) 
            for policy in self.policies 
            if policy["jurisdiction"].lower() == jurisdiction.lower()
        ]
    
    def get_policies_by_tech_hub(self, tech_hub: str) -> List[MockPolicyData]:
        """Get policies by tech hub"""
        return [
            MockPolicyData(**policy) 
            for policy in self.policies 
            if policy["tech_hub"].lower() == tech_hub.lower()
        ]
    
    def get_policies_by_industry(self, industry: str) -> List[MockPolicyData]:
        """Get policies by industry"""
        industry_mapping = {
            "ai": ["ai_ml"],
            "artificial intelligence": ["ai_ml"],
            "robotics": ["robotics"],
            "quantum": ["quantum_computing"],
            "biotech": ["biotech"],
            "biotechnology": ["biotech"],
            "fintech": ["fintech"],
            "financial": ["fintech"],
            "clean": ["cleantech"],
            "clean tech": ["cleantech"]
        }
        
        target_industries = industry_mapping.get(industry.lower(), [])
        
        matching_policies = []
        for policy in self.policies:
            for industry_data in policy.get("requirements", {}).get("technology_requirements", {}).get("required_technologies", []):
                if industry_data.lower() in target_industries:
                    matching_policies.append(policy)
                    break
        
        return [MockPolicyData(**policy) for policy in matching_policies]
    
    def get_policy_by_id(self, policy_id: str) -> Optional[MockPolicyData]:
        """Get policy by ID"""
        for policy in self.policies:
            if policy.get("title", "").lower().replace(" ", "-") == policy_id.lower():
                return MockPolicyData(**policy)
        return None
    
    def generate_raw_policy_text(self, policy: MockPolicyData) -> str:
        """Generate raw policy text from structured data"""
        
        raw_text = f"""
{policy.title}
{policy.description}

INCENTIVES:
"""
        
        # Add tax incentives
        for incentive in policy.incentives.get("tax_incentives", []):
            raw_text += f"\n- {incentive['description']}: "
            if incentive.get("rate_reduction"):
                raw_text += f"{incentive['rate_reduction']}% reduction "
            if incentive.get("duration_years"):
                raw_text += f"for {incentive['duration_years']} years "
            raw_text += f"Eligibility: {', '.join(incentive['eligibility_criteria'])}"
        
        # Add financial subsidies
        for subsidy in policy.incentives.get("financial_subsidies", []):
            raw_text += f"\n- {subsidy['description']}: "
            if subsidy.get("amount_usd"):
                raw_text += f"${subsidy['amount_usd']:,.0f} "
            if subsidy.get("purpose"):
                raw_text += f"for {subsidy['purpose']} "
            raw_text += f"Eligibility: {', '.join(subsidy['eligibility_criteria'])}"
        
        # Add land and infrastructure
        for incentive in policy.incentives.get("land_and_infrastructure", []):
            raw_text += f"\n- {incentive['description']}: "
            if incentive.get("area_sqm"):
                raw_text += f"{incentive['area_sqm']} sqm "
            if incentive.get("duration_years"):
                raw_text += f"for {incentive['duration_years']} years "
            if incentive.get("location"):
                raw_text += f"at {incentive['location']}"
        
        raw_text += """

REQUIREMENTS:
"""
        
        # Add staffing requirements
        staffing = policy.requirements.get("staffing_requirements", {})
        if staffing:
            raw_text += "\nStaffing Requirements:\n"
            if staffing.get("min_employees"):
                raw_text += f"- Minimum {staffing['min_employees']} employees\n"
            if staffing.get("min_researchers"):
                raw_text += f"- Minimum {staffing['min_researchers']} researchers\n"
            if staffing.get("researcher_percentage"):
                raw_text += f"- {staffing['researcher_percentage']}% researchers\n"
            if staffing.get("min_phd_percentage"):
                raw_text += f"- {staffing['min_phd_percentage']}% PhD holders\n"
        
        # Add financial requirements
        financial = policy.requirements.get("financial_requirements", {})
        if financial:
            raw_text += "\nFinancial Requirements:\n"
            if financial.get("min_investment_usd"):
                raw_text += f"- Minimum investment ${financial['min_investment_usd']:,.0f}\n"
            if financial.get("min_revenue_usd"):
                raw_text += f"- Minimum annual revenue ${financial['min_revenue_usd']:,.0f}\n"
        
        # Add IP requirements
        ip = policy.requirements.get("intellectual_property", {})
        if ip:
            raw_text += "\nIntellectual Property Requirements:\n"
            if ip.get("min_patents"):
                raw_text += f"- Minimum {ip['min_patents']} patents\n"
            if ip.get("min_patents_pending"):
                raw_text += f"- Minimum {ip['min_patents_pending']} pending patents\n"
        
        # Add compliance requirements
        raw_text += "\nCOMPLIANCE:\n"
        for compliance_type, compliance_data in policy.compliance.items():
            if compliance_data.get("required") or compliance_data.get("applies"):
                raw_text += f"- {compliance_type.replace('_', ' ').title()}: "
                if compliance_data.get("required"):
                    raw_text += "Required\n"
                elif compliance_data.get("applies"):
                    raw_text += "Applies\n"
        
        return raw_text.strip()
    
    def demonstrate_policy_cleaning(self, jurisdiction: str = "China", tech_hub: str = "Shanghai") -> StructuredPolicy:
        """Demonstrate policy cleaning functionality"""
        
        # Get mock policy
        policies = self.get_policies_by_jurisdiction(jurisdiction)
        if not policies:
            policies = self.get_policies_by_tech_hub(tech_hub)
        
        if not policies:
            raise ValueError(f"No policies found for {jurisdiction} or {tech_hub}")
        
        policy = policies[0]
        
        # Generate raw text
        raw_text = self.generate_raw_policy_text(policy)
        
        # Create source URL
        source_url = f"https://{jurisdiction.lower()}-gov-policies/{tech_hub.lower()}-tech-policy-2024"
        
        # Structure the policy
        structured_policy = self.structurer.structure_policy(raw_text, source_url, jurisdiction)
        
        return structured_policy
    
    def save_mock_policies(self, output_dir: str):
        """Save mock policies to JSON files"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, policy in enumerate(self.policies):
            filename = f"mock_policy_{i+1}_{policy['jurisdiction'].lower()}_{policy['tech_hub'].lower()}.json"
            filepath = output_path / filename
            
            # Generate raw text
            mock_policy_data = MockPolicyData(**policy)
            raw_text = self.generate_raw_policy_text(mock_policy_data)
            
            # Create structured policy
            source_url = f"https://{policy['jurisdiction'].lower()}-gov-policies/{policy['tech_hub'].lower()}-tech-policy-2024"
            structured_policy = self.structurer.structure_policy(raw_text, source_url, policy['jurisdiction'])
            
            # Save structured policy
            self.structurer.save_structured_policy(structured_policy, str(filepath))
            
            print(f"Saved mock policy to: {filepath}")
    
    def get_policy_statistics(self) -> Dict[str, Any]:
        """Get statistics about mock policies"""
        
        stats = {
            "total_policies": len(self.policies),
            "jurisdictions": {},
            "tech_hubs": {},
            "policy_types": {},
            "industries": {}
        }
        
        for policy in self.policies:
            # Count jurisdictions
            jurisdiction = policy["jurisdiction"]
            stats["jurisdictions"][jurisdiction] = stats["jurisdictions"].get(jurisdiction, 0) + 1
            
            # Count tech hubs
            tech_hub = policy["tech_hub"]
            stats["tech_hubs"][tech_hub] = stats["tech_hubs"].get(tech_hub, 0) + 1
            
            # Count policy types
            policy_type = policy["policy_type"]
            stats["policy_types"][policy_type] = stats["policy_types"].get(policy_type, 0) + 1
            
            # Count industries
            industries = policy["requirements"].get("technology_requirements", {}).get("required_technologies", [])
            for industry in industries:
                stats["industries"][industry] = stats["industries"].get(industry, 0) + 1
        
        return stats


# Example usage
if __name__ == "__main__":
    # Initialize mock database
    db = MockPolicyDatabase()
    
    # Get all policies
    all_policies = db.get_all_policies()
    print(f"Total policies: {len(all_policies)}")
    
    # Get policies by jurisdiction
    china_policies = db.get_policies_by_jurisdiction("China")
    print(f"China policies: {len(china_policies)}")
    
    # Get policies by tech hub
    shanghai_policies = db.get_policies_by_tech_hub("Shanghai")
    print(f"Shanghai policies: {len(shanghai_policies)}")
    
    # Get policies by industry
    ai_policies = db.get_policies_by_industry("AI")
    print(f"AI policies: {len(ai_policies)}")
    
    # Demonstrate policy cleaning
    try:
        structured_policy = db.demonstrate_policy_cleaning()
        print(f"Structured policy confidence score: {structured_policy.confidence_score}")
    except Exception as e:
        print(f"Error demonstrating policy cleaning: {e}")
    
    # Save mock policies
    try:
        db.save_mock_policies("c:\\OpenInvest\\open-invest-protocol\\policy_crawler\\data\\structured_policies")
        print("Mock policies saved successfully")
    except Exception as e:
        print(f"Error saving mock policies: {e}")
    
    # Get statistics
    stats = db.get_policy_statistics()
    print(f"Policy statistics: {stats}")