"""
Policy Data Cleaning Service
Converts raw policy text into structured OpenInvest format
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import jsonschema
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StructuredPolicy:
    """Structured policy data"""
    policy_id: str
    location: Dict[str, Any]
    policy_type: str
    title: str
    description: str
    eligibility_criteria: List[Dict[str, Any]]
    incentives: List[Dict[str, Any]]
    requirements: Dict[str, Any]
    compliance: Dict[str, Any]
    application_process: Dict[str, Any]
    metadata: Dict[str, Any]

class PolicyCleaner:
    """Clean and structure global policy data"""
    
    def __init__(self):
        self.schema_path = "../../schemas/policy_schema.json"
        self.industry_keywords = {
            "AI/ML": ["artificial intelligence", "machine learning", "deep learning", "neural networks"],
            "Robotics": ["robot", "automation", "autonomous", "cobot"],
            "Quantum Computing": ["quantum", "qubit", "quantum computing", "quantum algorithm"],
            "Biotech": ["biotechnology", "biotech", "genetic", "pharmaceutical", "biomedical"],
            "Fintech": ["financial technology", "fintech", "blockchain", "cryptocurrency"],
            "Cleantech": ["clean tech", "renewable", "sustainable", "green technology"],
            "Autonomous Driving": ["self-driving", "autonomous vehicle", "driverless", "AV"],
            "Embodied AI": ["embodied ai", "embodied intelligence", "physical ai", "robotics ai"],
            "Blockchain": ["blockchain", "distributed ledger", "smart contract", "web3"],
            "AR/VR": ["augmented reality", "virtual reality", "mixed reality", "metaverse"],
            "Nanotech": ["nanotechnology", "nano", "nanomaterial", "nanoscale"],
            "Space Tech": ["space technology", "aerospace", "satellite", "space exploration"]
        }
        
        self.incentive_patterns = {
            "tax_break": r"tax\s+(break|incentive|credit|reduction|exemption)",
            "subsidy": r"subsid(y|ies)|grant|financial support|funding",
            "land_grant": r"land\s+(grant|allocation|free|discount)",
            "rdd_support": r"r\s*.*\s*d\s*.*\s*d|research\s+development|innovation\s+support",
            "infrastructure_support": r"infrastructure|facility|equipment|construction",
            "training_grant": r"training|education|development|skill|talent",
            "export_support": r"export|international|global|foreign trade",
            "ip_protection": r"intellectual\s+property|patent|trademark|copyright|ip",
            "immigration_benefits": r"visa|immigration|work permit|residence"
        }
        
        self.requirement_patterns = {
            "employee_count": r"employee|staff|workforce|team",
            "revenue": r"revenue|turnover|income|sales",
            "investment": r"investment|capital|funding|budget",
            "patent": r"patent|ip|intellectual\s+property",
            "experience": r"experience|years|track\s+record|history",
            "qualification": r"qualification|degree|certificate|license",
            "location": r"location|site|premises|facility"
        }
    
    def clean_policy_text(self, raw_policy_text: str, source_url: str = None) -> StructuredPolicy:
        """
        Convert raw policy text to structured format
        
        Args:
            raw_policy_text: Raw policy text from government website
            source_url: URL of the original policy document
            
        Returns:
            StructuredPolicy: Cleaned and structured policy data
        """
        logger.info(f"Cleaning policy text from {source_url}")
        
        # 1. Extract basic information
        basic_info = self._extract_basic_info(raw_policy_text)
        
        # 2. Extract eligibility criteria
        eligibility = self._extract_eligibility_criteria(raw_policy_text)
        
        # 3. Extract incentives
        incentives = self._extract_incentives(raw_policy_text)
        
        # 4. Extract requirements
        requirements = self._extract_requirements(raw_policy_text)
        
        # 5. Extract compliance information
        compliance = self._extract_compliance(raw_policy_text)
        
        # 6. Extract application process
        application_process = self._extract_application_process(raw_policy_text)
        
        # 7. Build structured policy
        structured_policy = StructuredPolicy(
            policy_id=basic_info["policy_id"],
            location=basic_info["location"],
            policy_type=basic_info["policy_type"],
            title=basic_info["title"],
            description=basic_info["description"],
            eligibility_criteria=eligibility,
            incentives=incentives,
            requirements=requirements,
            compliance=compliance,
            application_process=application_process,
            metadata={
                "source_url": source_url,
                "last_updated": datetime.now().isoformat(),
                "validity_period": self._extract_validity_period(raw_policy_text),
                "confidence_score": self._calculate_confidence_score({
                    "basic_info": basic_info,
                    "eligibility": eligibility,
                    "incentives": incentives,
                    "requirements": requirements,
                    "compliance": compliance
                }),
                "data_quality": "cleaned"
            }
        )
        
        # 8. Validate against schema
        self._validate_policy_schema(structured_policy)
        
        logger.info(f"Successfully cleaned policy: {structured_policy.policy_id}")
        return structured_policy
    
    def _extract_basic_info(self, text: str) -> Dict[str, Any]:
        """Extract basic policy information"""
        # Extract title (usually in first few lines)
        lines = text.split('\n')
        title = lines[0].strip() if lines else "Unknown Policy"
        
        # Extract location (simplified - in real implementation, use NER)
        location = {
            "country": "China",  # Default, should be extracted with NER
            "region": "Shanghai",  # Default
            "city": "Shanghai",  # Default
            "tech_hub": "Pudong New Area"
        }
        
        # Extract policy type
        policy_type = self._classify_policy_type(text)
        
        # Extract description
        description = self._extract_description(text)
        
        # Generate policy ID
        policy_id = f"policy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "policy_id": policy_id,
            "location": location,
            "policy_type": policy_type,
            "title": title,
            "description": description
        }
    
    def _classify_policy_type(self, text: str) -> str:
        """Classify policy type based on content"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ["tax", "fiscal", "revenue"]):
            return "tax_incentive"
        elif any(keyword in text_lower for keyword in ["subsid", "grant", "funding"]):
            return "subsidy"
        elif any(keyword in text_lower for keyword in ["land", "space", "property"]):
            return "land_grant"
        elif any(keyword in text_lower for keyword in ["research", "development", "innovation"]):
            return "rdd_support"
        elif any(keyword in text_lower for keyword in ["compliance", "regulation", "law"]):
            return "compliance"
        elif any(keyword in text_lower for keyword in ["visa", "immigration", "work permit"]):
            return "immigration"
        else:
            return "infrastructure"
    
    def _extract_description(self, text: str) -> str:
        """Extract policy description"""
        # Remove title and focus on main content
        lines = text.split('\n')[1:]  # Skip first line (title)
        description_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('http') and not line.startswith('www'):
                description_lines.append(line)
        
        return ' '.join(description_lines[:10])  # Limit to first 10 meaningful lines
    
    def _extract_eligibility_criteria(self, text: str) -> List[Dict[str, Any]]:
        """Extract eligibility criteria"""
        criteria = []
        
        # Extract company size requirements
        size_match = re.search(r'(company|enterprise)\s+size\s*[:：]?\s*(\d+)\s*(employees?|people)', text, re.IGNORECASE)
        if size_match:
            criteria.append({
                "criteria_type": "company_size",
                "condition": "Minimum company size",
                "threshold": int(size_match.group(2))
            })
        
        # Extract employee count requirements
        employee_match = re.search(r'employee\s+count\s*[:：]?\s*(\d+)\s*(minimum|at least)', text, re.IGNORECASE)
        if employee_match:
            criteria.append({
                "criteria_type": "employee_count",
                "condition": "Minimum employee count",
                "threshold": int(employee_match.group(1))
            })
        
        # Extract investment requirements
        investment_match = re.search r'investment\s*[:：]?\s*(\$?[\d,]+)\s*(usd|million|billion)', text, re.IGNORECASE)
        if investment_match:
            criteria.append({
                "criteria_type": "investment_amount",
                "condition": "Minimum investment amount",
                "threshold": investment_match.group(1)
            })
        
        return criteria
    
    def _extract_incentives(self, text: str) -> List[Dict[str, Any]]:
        """Extract financial and non-financial incentives"""
        incentives = []
        
        # Extract tax incentives
        tax_matches = re.finditer(self.incentive_patterns["tax_break"], text, re.IGNORECASE)
        for match in tax_matches:
            incentives.append({
                "incentive_type": "tax_break",
                "financial_details": {
                    "percentage": self._extract_percentage(text, match.start()),
                    "duration_years": self._extract_duration(text, match.start())
                },
                "non_financial_benefits": []
            })
        
        # Extract subsidies
        subsidy_matches = re.finditer(self.incentive_patterns["subsidy"], text, re.IGNORECASE)
        for match in subsidy_matches:
            amount = self._extract_amount(text, match.start())
            if amount:
                incentives.append({
                    "incentive_type": "subsidy",
                    "financial_details": {
                        "amount_usd": amount,
                        "currency": "USD"
                    },
                    "non_financial_benefits": []
                })
        
        return incentives
    
    def _extract_requirements(self, text: str) -> Dict[str, Any]:
        """Extract various requirements"""
        requirements = {
            "staffing": {},
            "intellectual_property": {},
            "investment": {},
            "location_requirements": {}
        }
        
        # Extract staffing requirements
        staff_matches = re.finditer(self.requirement_patterns["employee_count"], text, re.IGNORECASE)
        for match in staff_matches:
            min_employees = self._extract_number(text, match.start())
            if min_employees:
                requirements["staffing"]["min_employees"] = min_employees
        
        # Extract IP requirements
        ip_matches = re.finditer(self.requirement_patterns["patent"], text, re.IGNORECASE)
        for match in ip_matches:
            patent_count = self._extract_number(text, match.start())
            if patent_count:
                requirements["intellectual_property"]["patent_count"] = patent_count
        
        # Extract investment requirements
        investment_matches = re.finditer(self.requirement_patterns["investment"], text, re.IGNORECASE)
        for match in investment_matches:
            min_investment = self._extract_amount(text, match.start())
            if min_investment:
                requirements["investment"]["min_investment_usd"] = min_investment
        
        return requirements
    
    def _extract_compliance(self, text: str) -> Dict[str, Any]:
        """Extract compliance requirements"""
        compliance = {
            "data_localization": False,
            "export_controls": False,
            "security_clearance": "none",
            "certifications": [],
            "reporting_requirements": []
        }
        
        # Check for data localization requirements
        if any(keyword in text.lower() for keyword in ["data localization", "data must be stored locally", "local data storage"]):
            compliance["data_localization"] = True
        
        # Check for export controls
        if any(keyword in text.lower() for keyword in ["export control", "export restriction", "dual use"]):
            compliance["export_controls"] = True
        
        return compliance
    
    def _extract_application_process(self, text: str) -> Dict[str, Any]:
        """Extract application process information"""
        process = {
            "application_deadline": None,
            "processing_time_days": None,
            "required_documents": [],
            "contact_information": {}
        }
        
        # Extract deadline
        deadline_match = re.search(r'(deadline|截止日期)[:：]\s*(\d{4}-\d{2}-\d{2})', text)
        if deadline_match:
            process["application_deadline"] = deadline_match.group(2)
        
        # Extract processing time
        time_match = re.search(r'processing\s+time|处理时间[:：]\s*(\d+)\s*(days|工作日)', text)
        if time_match:
            process["processing_time_days"] = int(time_match.group(1))
        
        return process
    
    def _extract_validity_period(self, text: str) -> Dict[str, Any]:
        """Extract policy validity period"""
        validity = {}
        
        # Extract start and end dates
        date_matches = re.finditer(r'(\d{4}-\d{2}-\d{2})', text)
        dates = [match.group(1) for match in date_matches]
        
        if len(dates) >= 2:
            validity["start_date"] = dates[0]
            validity["end_date"] = dates[1]
        elif len(dates) == 1:
            validity["start_date"] = dates[0]
            validity["end_date"] = "2025-12-31"  # Default end date
        
        return validity
    
    def _calculate_confidence_score(self, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted data"""
        score = 1.0
        
        # Reduce score for missing data
        if not extracted_data["basic_info"]["title"]:
            score -= 0.2
        if not extracted_data["incentives"]:
            score -= 0.3
        if not extracted_data["requirements"]:
            score -= 0.2
        if not extracted_data["eligibility"]:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _extract_percentage(self, text: str, position: int) -> Optional[float]:
        """Extract percentage from text around given position"""
        context = text[max(0, position-100):position+100]
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', context)
        return float(match.group(1)) if match else None
    
    def _extract_amount(self, text: str, position: int) -> Optional[float]:
        """Extract monetary amount from text around given position"""
        context = text[max(0, position-100):position+100]
        match = re.search(r'\$?(\d+(?:,\d+)*)\s*(?:million|billion|usd|USD)?', context)
        if match:
            amount = float(match.group(1).replace(',', ''))
            return amount * 1000000 if 'million' in context.lower() else amount
        return None
    
    def _extract_duration(self, text: str, position: int) -> Optional[int]:
        """Extract duration in years from text around given position"""
        context = text[max(0, position-100):position+100]
        match = re.search(r'(\d+)\s*(?:years?|年)', context)
        return int(match.group(1)) if match else None
    
    def _extract_number(self, text: str, position: int) -> Optional[int]:
        """Extract number from text around given position"""
        context = text[max(0, position-100):position+100]
        match = re.search(r'(\d+)', context)
        return int(match.group(1)) if match else None
    
    def _validate_policy_schema(self, policy: StructuredPolicy):
        """Validate policy against schema"""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # Convert StructuredPolicy to dict for validation
            policy_dict = {
                "policy_id": policy.policy_id,
                "location": policy.location,
                "policy_type": policy.policy_type,
                "title": policy.title,
                "description": policy.description,
                "eligibility_criteria": policy.eligibility_criteria,
                "incentives": policy.incentives,
                "requirements": policy.requirements,
                "compliance": policy.compliance,
                "application_process": policy.application_process,
                "metadata": policy.metadata
            }
            
            jsonschema.validate(policy_dict, schema)
            logger.info("Policy validation passed")
            
        except jsonschema.ValidationError as e:
            logger.error(f"Policy validation failed: {e}")
            raise
        except FileNotFoundError:
            logger.warning("Schema file not found, skipping validation")
    
    def clean_and_store_policy(self, raw_policy_text: str, source_url: str = None) -> StructuredPolicy:
        """
        Clean policy text and store it in structured format
        
        Args:
            raw_policy_text: Raw policy text
            source_url: Source URL of the policy
            
        Returns:
            StructuredPolicy: Cleaned and stored policy
        """
        # Clean the policy text
        cleaned_policy = self.clean_policy_text(raw_policy_text, source_url)
        
        # Store in structured format (in real implementation, save to database)
        storage_path = "../../data/structured_policies"
        import os
        os.makedirs(storage_path, exist_ok=True)
        
        filename = f"{cleaned_policy.policy_id}.json"
        filepath = os.path.join(storage_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cleaned_policy.__dict__, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Policy stored at: {filepath}")
        return cleaned_policy