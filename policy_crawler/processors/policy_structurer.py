"""
Policy Data Structurer Module
Converts raw policy text into structured format according to global policy schema
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import jsonschema
from schema.global_policy_schema import GlobalPolicySchema


class PolicyType(str, Enum):
    """Policy type enumeration"""
    TAX_INCENTIVE = "tax_incentive"
    SUBSIDY = "subsidy"
    LAND_GRANT = "land_grant"
    REGULATORY = "regulatory"
    COMPLIANCE = "compliance"
    INVESTMENT_PROMOTION = "investment_promotion"


class IndustryType(str, Enum):
    """Industry type enumeration"""
    AI_ML = "ai_ml"
    ROBOTICS = "robotics"
    QUANTUM_COMPUTING = "quantum_computing"
    BIOTECH = "biotech"
    FINTECH = "fintech"
    CLEANTECH = "cleantech"
    SEMICONDUCTOR = "semiconductor"
    AUTONOMOUS_DRIVING = "autonomous_driving"
    VR_AR = "vr_ar"
    BLOCKCHAIN = "blockchain"
    IOT = "iot"
    CYBERSECURITY = "cybersecurity"
    AEROSPACE = "aerospace"
    NANOTECHNOLOGY = "nanotechnology"
    BIOMEDICAL = "biomedical"
    NEURAL_INTERFACE = "neural_interface"
    EDGE_COMPUTING = "edge_computing"
    FIVE_G_SIX_G = "5g_6g"
    METAVERSE = "metaverse"
    DIGITAL_TWIN = "digital_twin"


@dataclass
class StructuredPolicy:
    """Structured policy data"""
    policy_metadata: Dict[str, Any]
    incentives: Dict[str, Any]
    requirements: Dict[str, Any]
    compliance: Dict[str, Any]
    application_process: Dict[str, Any]
    target_industries: List[Dict[str, Any]]
    eligibility_criteria: List[Dict[str, Any]]
    raw_text: str
    confidence_score: float


class PolicyDataStructurer:
    """Policy data structuring service"""
    
    def __init__(self):
        self.schema = GlobalPolicySchema()
        self.confidence_threshold = 0.7
        
        # Initialize NLP patterns for extraction
        self._initialize_extraction_patterns()
    
    def _initialize_extraction_patterns(self):
        """Initialize regex patterns for policy text extraction"""
        
        # Tax incentive patterns
        self.tax_patterns = {
            'rd_tax_credit': r'R&D\s+tax\s+credit|research\s+and\s+development\s+tax\s+(credit|deduction)',
            'corporate_tax_reduction': r'corporate\s+tax\s+(reduction|rebate|exemption)',
            'income_tax_holiday': r'income\s+tax\s+holiday|tax\s+holiday',
            'property_tax_exemption': r'property\s+tax\s+(exemption|exclusion)',
            'customs_duty_exemption': r'customs\s+duty\s+(exemption|exclusion|waiver)'
        }
        
        # Financial subsidy patterns
        self.subsidy_patterns = {
            'rd_grant': r'R&D\s+grant|research\s+(grant|funding)',
            'startup_capital': r'startup\s+(capital|funding|grant)',
            'equipment_subsidy': r'equipment\s+(subsidy|grant|funding)',
            'training_subsidy': r'training\s+(subsidy|grant|funding)',
            'export_promotion': r'export\s+(promotion|subsidy|grant)',
            'market_access': r'market\s+(access|entry|penetration)'
        }
        
        # Land and infrastructure patterns
        self.land_patterns = {
            'land_grant': r'land\s+(grant|allocation|provision)',
            'factory_rent_reduction': r'factory\s+rent\s+(reduction|discount|subsidy)',
            'facility_subsidy': r'facility\s+(subsidy|grant|funding)',
            'infrastructure_access': r'infrastructure\s+(access|usage)',
            'utility_discount': r'utility\s+(discount|subsidy|reduction)'
        }
        
        # Requirement patterns
        self.requirement_patterns = {
            'min_employees': r'minimum\s+(\d+)\s+employees?|at\s+least\s+(\d+)\s+employees?',
            'min_researchers': r'minimum\s+(\d+)\s+researchers?|at\s+least\s+(\d+)\s+researchers?',
            'researcher_percentage': r'researchers?\s+(constitute|make\s+up)\s+(\d+)%',
            'min_phd_percentage': r'PhD\s+(holders?|employees?)\s+(constitute|make\s+up)\s+(\d+)%',
            'min_investment': r'minimum\s+investment\s+of\s+\$?(\d+(?:,\d+)*)',
            'min_patents': r'minimum\s+(\d+)\s+patents?|at\s+least\s+(\d+)\s+patents?'
        }
        
        # Compliance patterns
        self.compliance_patterns = {
            'data_localization': r'data\s+(localization|localization\s+requirement)',
            'export_controls': r'export\s+(control|restriction|regulation)',
            'security_clearance': r'security\s+(clearance|clearance\s+requirement)',
            'environmental_compliance': r'environmental\s+(compliance|regulation|standard)',
            'labor_compliance': r'labor\s+(compliance|regulation|law)'
        }
    
    def structure_policy(self, raw_policy_text: str, source_url: str, jurisdiction: str) -> StructuredPolicy:
        """
        Convert raw policy text to structured format
        
        Args:
            raw_policy_text: Raw policy text from government websites
            source_url: Original URL of the policy
            jurisdiction: Jurisdiction where the policy applies
            
        Returns:
            StructuredPolicy: Structured policy data
        """
        
        # Extract policy metadata
        policy_metadata = self._extract_policy_metadata(raw_policy_text, source_url, jurisdiction)
        
        # Extract incentives
        incentives = self._extract_incentives(raw_policy_text)
        
        # Extract requirements
        requirements = self._extract_requirements(raw_policy_text)
        
        # Extract compliance
        compliance = self._extract_compliance(raw_policy_text)
        
        # Extract application process
        application_process = self._extract_application_process(raw_policy_text)
        
        # Extract target industries
        target_industries = self._extract_target_industries(raw_policy_text)
        
        # Extract eligibility criteria
        eligibility_criteria = self._extract_eligibility_criteria(raw_policy_text)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            raw_policy_text, incentives, requirements, compliance
        )
        
        # Create structured policy
        structured_policy = StructuredPolicy(
            policy_metadata=policy_metadata,
            incentives=incentives,
            requirements=requirements,
            compliance=compliance,
            application_process=application_process,
            target_industries=target_industries,
            eligibility_criteria=eligibility_criteria,
            raw_text=raw_policy_text,
            confidence_score=confidence_score
        )
        
        # Validate against schema
        self._validate_policy_schema(structured_policy)
        
        return structured_policy
    
    def _extract_policy_metadata(self, raw_text: str, source_url: str, jurisdiction: str) -> Dict[str, Any]:
        """Extract policy metadata from raw text"""
        
        # Extract policy type
        policy_type = self._detect_policy_type(raw_text)
        
        # Extract dates
        effective_date = self._extract_date(raw_text, ['effective', 'commencement', 'implementation'])
        expiry_date = self._extract_date(raw_text, ['expiry', 'expiration', 'termination'])
        
        # Generate policy ID
        policy_id = f"{jurisdiction.lower().replace(' ', '-')}_{policy_type}_{datetime.now().strftime('%Y%m%d')}"
        
        return {
            "policy_id": policy_id,
            "source_url": source_url,
            "jurisdiction": jurisdiction,
            "tech_hub": self._extract_tech_hub(raw_text, jurisdiction),
            "policy_type": policy_type,
            "effective_date": effective_date or datetime.now().strftime('%Y-%m-%d'),
            "expiry_date": expiry_date,
            "last_updated": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "crawl_timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "confidence_score": 0.0  # Will be updated later
        }
    
    def _detect_policy_type(self, raw_text: str) -> str:
        """Detect policy type from text"""
        
        text_lower = raw_text.lower()
        
        # Check for specific policy types
        if any(keyword in text_lower for keyword in ['tax', 'incentive', 'credit', 'deduction']):
            return PolicyType.TAX_INCENTIVE
        elif any(keyword in text_lower for keyword in ['subsidy', 'grant', 'funding', 'financial']):
            return PolicyType.SUBSIDY
        elif any(keyword in text_lower for keyword in ['land', 'property', 'real estate', 'facility']):
            return PolicyType.LAND_GRANT
        elif any(keyword in text_lower for keyword in ['compliance', 'regulation', 'requirement']):
            return PolicyType.COMPLIANCE
        elif any(keyword in text_lower for keyword in ['investment', 'promotion', 'attraction']):
            return PolicyType.INVESTMENT_PROMOTION
        else:
            return PolicyType.REGULATORY
    
    def _extract_date(self, raw_text: str, date_keywords: List[str]) -> Optional[str]:
        """Extract date from text using keywords"""
        
        for keyword in date_keywords:
            pattern = rf'{keyword}\s*[^\d]*(\d{{4}}[-/]\d{{1,2}}[-/]\d{{1,2}}|\d{{1,2}}[-/]\d{{1,2}}[-/]\d{{4}})'
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                return match.group(1).replace('/', '-')
        
        return None
    
    def _extract_tech_hub(self, raw_text: str, jurisdiction: str) -> str:
        """Extract specific tech hub from text"""
        
        # Common tech hubs
        tech_hubs = {
            'china': ['shanghai', 'beijing', 'shenzhen', 'hangzhou', 'guangzhou'],
            'usa': ['silicon valley', 'austin', 'seattle', 'boston', 'research triangle'],
            'eu': ['berlin', 'paris', 'london', 'amsterdam', 'copenhagen'],
            'singapore': ['one north', 'tuas', 'jurong island']
        }
        
        text_lower = raw_text.lower()
        jurisdiction_lower = jurisdiction.lower()
        
        # Check for specific tech hubs in the text
        for country, hubs in tech_hubs.items():
            if country in jurisdiction_lower:
                for hub in hubs:
                    if hub in text_lower:
                        return hub.title()
        
        # Return jurisdiction as fallback
        return jurisdiction.title()
    
    def _extract_incentives(self, raw_text: str) -> Dict[str, Any]:
        """Extract incentives from raw text"""
        
        incentives = {
            "tax_incentives": [],
            "financial_subsidies": [],
            "land_and_infrastructure": []
        }
        
        # Extract tax incentives
        for incentive_type, pattern in self.tax_patterns.items():
            matches = re.finditer(pattern, raw_text, re.IGNORECASE)
            for match in matches:
                incentive = {
                    "type": incentive_type,
                    "description": self._extract_description(raw_text, match.start()),
                    "rate_reduction": self._extract_percentage(raw_text, match.start()),
                    "duration_years": self._extract_years(raw_text, match.start()),
                    "eligibility_criteria": self._extract_eligibility(raw_text, match.start())
                }
                incentives["tax_incentives"].append(incentive)
        
        # Extract financial subsidies
        for subsidy_type, pattern in self.subsidy_patterns.items():
            matches = re.finditer(pattern, raw_text, re.IGNORECASE)
            for match in matches:
                subsidy = {
                    "type": subsidy_type,
                    "description": self._extract_description(raw_text, match.start()),
                    "amount_usd": self._extract_amount(raw_text, match.start()),
                    "eligibility_criteria": self._extract_eligibility(raw_text, match.start())
                }
                incentives["financial_subsidies"].append(subsidy)
        
        # Extract land and infrastructure incentives
        for land_type, pattern in self.land_patterns.items():
            matches = re.finditer(pattern, raw_text, re.IGNORECASE)
            for match in matches:
                incentive = {
                    "type": land_type,
                    "description": self._extract_description(raw_text, match.start()),
                    "area_sqm": self._extract_area(raw_text, match.start()),
                    "duration_years": self._extract_years(raw_text, match.start())
                }
                incentives["land_and_infrastructure"].append(incentive)
        
        return incentives
    
    def _extract_requirements(self, raw_text: str) -> Dict[str, Any]:
        """Extract requirements from raw text"""
        
        requirements = {
            "staffing_requirements": {},
            "financial_requirements": {},
            "intellectual_property": {},
            "technology_requirements": {}
        }
        
        # Extract staffing requirements
        for requirement_type, pattern in self.requirement_patterns.items():
            matches = re.finditer(pattern, raw_text)
            for match in matches:
                if 'employees' in requirement_type:
                    value = int(re.search(r'\d+', match.group()).group())
                    requirements["staffing_requirements"]["min_employees"] = value
                elif 'researchers' in requirement_type:
                    value = int(re.search(r'\d+', match.group()).group())
                    requirements["staffing_requirements"]["min_researchers"] = value
                elif 'percentage' in requirement_type:
                    value = float(re.search(r'\d+', match.group()).group())
                    if 'researcher' in requirement_type:
                        requirements["staffing_requirements"]["researcher_percentage"] = value
                    elif 'phd' in requirement_type:
                        requirements["staffing_requirements"]["min_phd_percentage"] = value
        
        # Extract financial requirements
        investment_match = re.search(r'minimum\s+investment\s+of\s+\$?(\d+(?:,\d+)*)', raw_text)
        if investment_match:
            amount = float(investment_match.group(1).replace(',', ''))
            requirements["financial_requirements"]["min_investment_usd"] = amount
        
        # Extract IP requirements
        patent_match = re.search(r'minimum\s+(\d+)\s+patents?', raw_text)
        if patent_match:
            requirements["intellectual_property"]["min_patents"] = int(patent_match.group(1))
        
        return requirements
    
    def _extract_compliance(self, raw_text: str) -> Dict[str, Any]:
        """Extract compliance requirements from raw text"""
        
        compliance = {
            "data_localization": {"required": False},
            "export_controls": {"applies": False},
            "security_clearance": {"required": False},
            "environmental_compliance": {"required": False},
            "labor_compliance": {"required": False}
        }
        
        # Check for compliance requirements
        for compliance_type, pattern in self.compliance_patterns.items():
            if re.search(pattern, raw_text, re.IGNORECASE):
                if compliance_type == 'data_localization':
                    compliance["data_localization"]["required"] = True
                elif compliance_type == 'export_controls':
                    compliance["export_controls"]["applies"] = True
                elif compliance_type == 'security_clearance':
                    compliance["security_clearance"]["required"] = True
                elif compliance_type == 'environmental_compliance':
                    compliance["environmental_compliance"]["required"] = True
                elif compliance_type == 'labor_compliance':
                    compliance["labor_compliance"]["required"] = True
        
        return compliance
    
    def _extract_application_process(self, raw_text: str) -> Dict[str, Any]:
        """Extract application process information"""
        
        application_process = {
            "application_deadline": None,
            "processing_time_days": None,
            "required_documents": [],
            "application_fee_usd": None,
            "contact_information": {}
        }
        
        # Extract application deadline
        deadline_match = re.search(r'application\s+deadline\s*[:\-]?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})', raw_text)
        if deadline_match:
            application_process["application_deadline"] = deadline_match.group(1).replace('/', '-')
        
        # Extract processing time
        time_match = re.search(r'processing\s+time\s*[:\-]?\s*(\d+)\s*(days?|business days?)', raw_text)
        if time_match:
            application_process["processing_time_days"] = int(time_match.group(1))
        
        # Extract application fee
        fee_match = re.search(r'application\s+fee\s*[:\-]?\s*\$?(\d+(?:,\d+)*)', raw_text)
        if fee_match:
            application_process["application_fee_usd"] = float(fee_match.group(1).replace(',', ''))
        
        return application_process
    
    def _extract_target_industries(self, raw_text: str) -> List[Dict[str, Any]]:
        """Extract target industries from text"""
        
        industries = []
        industry_keywords = {
            "ai_ml": ["artificial intelligence", "machine learning", "AI", "ML"],
            "robotics": ["robotics", "automation", "robot"],
            "quantum_computing": ["quantum computing", "quantum"],
            "biotech": ["biotechnology", "biotech", "biological"],
            "fintech": ["fintech", "financial technology", "blockchain"],
            "cleantech": ["cleantech", "clean technology", "renewable"],
            "semiconductor": ["semiconductor", "chip", "integrated circuit"],
            "autonomous_driving": ["autonomous driving", "self-driving", "self-driving car"],
            "vr_ar": ["VR", "AR", "virtual reality", "augmented reality"],
            "iot": ["IoT", "internet of things", "connected devices"],
            "cybersecurity": ["cybersecurity", "information security", "network security"],
            "aerospace": ["aerospace", "aviation", "space technology"]
        }
        
        text_lower = raw_text.lower()
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                industries.append({
                    "industry": industry,
                    "priority_level": "medium",  # Default priority
                    "specific_requirements": []
                })
        
        return industries
    
    def _extract_eligibility_criteria(self, raw_text: str) -> List[Dict[str, Any]]:
        """Extract eligibility criteria from text"""
        
        criteria = []
        
        # Extract company size requirements
        size_match = re.search(r'company\s+size\s*[:\-]?\s*(\d+)\s*employees?', raw_text)
        if size_match:
            criteria.append({
                "criteria_type": "company_size",
                "condition": f"Minimum {size_match.group(1)} employees",
                "required": True
            })
        
        # Extract revenue requirements
        revenue_match = re.search(r'annual\s+revenue\s*[:\-]?\s*\$?(\d+(?:,\d+)*)', raw_text)
        if revenue_match:
            criteria.append({
                "criteria_type": "revenue",
                "condition": f"Minimum annual revenue ${revenue_match.group(1)}",
                "required": True
            })
        
        return criteria
    
    def _extract_description(self, raw_text: str, position: int) -> str:
        """Extract description text around the match position"""
        
        # Extract sentences around the match
        start = max(0, position - 200)
        end = min(len(raw_text), position + 200)
        
        description = raw_text[start:end].strip()
        
        # Clean up the description
        description = re.sub(r'\s+', ' ', description)
        description = re.sub(r'\.{2,}', '.', description)
        
        return description
    
    def _extract_percentage(self, raw_text: str, position: int) -> Optional[float]:
        """Extract percentage value around match position"""
        
        # Look for percentage near the match
        pattern = r'(\d+)%'
        match = re.search(pattern, raw_text[max(0, position-50):position+50])
        
        if match:
            return float(match.group(1))
        
        return None
    
    def _extract_years(self, raw_text: str, position: int) -> Optional[int]:
        """Extract number of years around match position"""
        
        # Look for years near the match
        pattern = r'(\d+)\s*(years?|year)'
        match = re.search(pattern, raw_text[max(0, position-50):position+50])
        
        if match:
            return int(match.group(1))
        
        return None
    
    def _extract_amount(self, raw_text: str, position: int) -> Optional[float]:
        """Extract amount value around match position"""
        
        # Look for amounts near the match
        pattern = r'\$?(\d+(?:,\d+)*)'
        match = re.search(pattern, raw_text[max(0, position-50):position+50])
        
        if match:
            return float(match.group(1).replace(',', ''))
        
        return None
    
    def _extract_area(self, raw_text: str, position: int) -> Optional[float]:
        """Extract area value around match position"""
        
        # Look for area near the match
        pattern = r'(\d+(?:,\d+)*)\s*(sq\.?m|square meters|m²|㎡)'
        match = re.search(pattern, raw_text[max(0, position-50):position+50])
        
        if match:
            return float(match.group(1).replace(',', ''))
        
        return None
    
    def _extract_eligibility(self, raw_text: str, position: int) -> List[str]:
        """Extract eligibility criteria around match position"""
        
        # Look for eligibility keywords near the match
        keywords = ['eligible', 'requirement', 'must', 'should', 'criteria']
        criteria = []
        
        for keyword in keywords:
            pattern = rf'{keyword}[^.]*\.'
            matches = re.finditer(pattern, raw_text[max(0, position-100):position+100])
            for match in matches:
                criteria.append(match.group().strip())
        
        return criteria[:3]  # Return top 3 criteria
    
    def _calculate_confidence_score(self, raw_text: str, incentives: Dict, requirements: Dict, compliance: Dict) -> float:
        """Calculate confidence score for the structured policy"""
        
        score = 0.0
        
        # Check if we found substantial content
        text_length = len(raw_text)
        if text_length > 1000:
            score += 0.2
        elif text_length > 500:
            score += 0.1
        
        # Check incentive extraction
        total_incentives = len(incentives.get("tax_incentives", [])) + \
                          len(incentives.get("financial_subsidies", [])) + \
                          len(incentives.get("land_and_infrastructure", []))
        
        if total_incentives > 0:
            score += min(0.3, total_incentives * 0.1)
        
        # Check requirement extraction
        has_requirements = any(requirements.get("staffing_requirements", {})) or \
                         any(requirements.get("financial_requirements", {})) or \
                         any(requirements.get("intellectual_property", {}))
        
        if has_requirements:
            score += 0.2
        
        # Check compliance extraction
        has_compliance = any(compliance.get("data_localization", {}).get("required", False)) or \
                        any(compliance.get("export_controls", {}).get("applies", False)) or \
                        any(compliance.get("security_clearance", {}).get("required", False))
        
        if has_compliance:
            score += 0.2
        
        # Check target industries
        if len(self._extract_target_industries(raw_text)) > 0:
            score += 0.1
        
        return min(1.0, score)
    
    def _validate_policy_schema(self, policy: StructuredPolicy) -> bool:
        """Validate policy against JSON schema"""
        
        try:
            policy_dict = {
                "policy_metadata": policy.policy_metadata,
                "incentives": policy.incentives,
                "requirements": policy.requirements,
                "compliance": policy.compliance,
                "application_process": policy.application_process,
                "target_industries": policy.target_industries,
                "eligibility_criteria": policy.eligibility_criteria
            }
            
            jsonschema.validate(policy_dict, self.schema.schema)
            return True
            
        except jsonschema.ValidationError as e:
            print(f"Schema validation error: {e}")
            return False
    
    def save_structured_policy(self, policy: StructuredPolicy, output_path: str):
        """Save structured policy to JSON file"""
        
        policy_dict = {
            "policy_metadata": policy.policy_metadata,
            "incentives": policy.incentives,
            "requirements": policy.requirements,
            "compliance": policy.compliance,
            "application_process": policy.application_process,
            "target_industries": policy.target_industries,
            "eligibility_criteria": policy.eligibility_criteria,
            "raw_text": policy.raw_text,
            "confidence_score": policy.confidence_score
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(policy_dict, f, indent=2, ensure_ascii=False)
    
    def load_structured_policy(self, file_path: str) -> StructuredPolicy:
        """Load structured policy from JSON file"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            policy_dict = json.load(f)
        
        return StructuredPolicy(
            policy_metadata=policy_dict["policy_metadata"],
            incentives=policy_dict["incentives"],
            requirements=policy_dict["requirements"],
            compliance=policy_dict["compliance"],
            application_process=policy_dict["application_process"],
            target_industries=policy_dict["target_industries"],
            eligibility_criteria=policy_dict["eligibility_criteria"],
            raw_text=policy_dict["raw_text"],
            confidence_score=policy_dict["confidence_score"]
        )