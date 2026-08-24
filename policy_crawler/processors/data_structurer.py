"""
Data Structurer Module
Convert structured policy data into standardized OpenInvest format
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class PolicyFormat(str, Enum):
    """Supported policy output formats"""
    OPEN_INVEST = "open_invest"
    JSON = "json"
    CSV = "csv"
    XML = "xml"

@dataclass
class OpenInvestPolicy:
    """Policy data in OpenInvest standard format"""
    policy_id: str
    policy_type: str  # "incentive", "requirement", "compliance"
    location: str
    jurisdiction: str
    industry: str
    title: str
    description: str
    source_url: str
    last_updated: str
    confidence_score: float
    
    # Incentive specific fields
    incentive_type: Optional[str] = None
    value_usd: Optional[float] = None
    currency: Optional[str] = None
    validity_period: Optional[Dict[str, Any]] = None
    
    # Requirement specific fields
    requirement_type: Optional[str] = None
    mandatory: Optional[bool] = None
    priority_level: Optional[str] = None
    
    # Compliance specific fields
    compliance_type: Optional[str] = None
    compliance_level: Optional[str] = None
    legal_basis: Optional[Dict[str, Any]] = None
    
    # Common fields
    eligibility_criteria: Optional[List[Dict[str, Any]]] = None
    application_process: Optional[Dict[str, Any]] = None
    benefits: Optional[List[Dict[str, Any]]] = None
    compliance_requirements: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class DataStructurer:
    """Convert policy data to OpenInvest standard format"""
    
    def __init__(self):
        self.format_mapping = {
            "incentive": PolicyFormat.OPEN_INVEST,
            "requirement": PolicyFormat.OPEN_INVEST,
            "compliance": PolicyFormat.OPEN_INVEST
        }
    
    def structure_policy(self, structured_policy: Dict[str, Any], target_format: PolicyFormat = PolicyFormat.OPEN_INVEST) -> Union[OpenInvestPolicy, Dict[str, Any]]:
        """
        Convert structured policy data to target format
        
        Args:
            structured_policy: Structured policy data from PolicyCleaner
            target_format: Target output format
            
        Returns:
            Formatted policy data
        """
        logger.info(f"Structuring policy {structured_policy.get('policy_id', 'unknown')} to {target_format.value} format")
        
        if target_format == PolicyFormat.OPEN_INVEST:
            return self._to_open_invest_format(structured_policy)
        elif target_format == PolicyFormat.JSON:
            return self._to_json_format(structured_policy)
        elif target_format == PolicyFormat.CSV:
            return self._to_csv_format(structured_policy)
        elif target_format == PolicyFormat.XML:
            return self._to_xml_format(structured_policy)
        else:
            raise ValueError(f"Unsupported format: {target_format}")
    
    def _to_open_invest_format(self, structured_policy: Dict[str, Any]) -> OpenInvestPolicy:
        """Convert to OpenInvest standard format"""
        policy_type = structured_policy.get("policy_type", "incentive")
        
        # Create base OpenInvest policy
        open_invest_policy = OpenInvestPolicy(
            policy_id=structured_policy.get("policy_id", ""),
            policy_type=policy_type,
            location=structured_policy.get("location", ""),
            jurisdiction=self._extract_jurisdiction(structured_policy.get("location", "")),
            industry=structured_policy.get("industry", "other"),
            title=structured_policy.get("title", ""),
            description=structured_policy.get("description", ""),
            source_url=structured_policy.get("metadata", {}).get("source_url", ""),
            last_updated=structured_policy.get("metadata", {}).get("last_updated", datetime.now().isoformat()),
            confidence_score=structured_policy.get("confidence_score", 0.0)
        )
        
        # Add policy-specific fields
        if policy_type == "incentive":
            self._add_incentive_fields(open_invest_policy, structured_policy)
        elif policy_type == "requirement":
            self._add_requirement_fields(open_invest_policy, structured_policy)
        elif policy_type == "compliance":
            self._add_compliance_fields(open_invest_policy, structured_policy)
        
        # Add common fields
        self._add_common_fields(open_invest_policy, structured_policy)
        
        return open_invest_policy
    
    def _add_incentive_fields(self, policy: OpenInvestPolicy, structured_policy: Dict[str, Any]) -> None:
        """Add incentive-specific fields"""
        incentive_data = structured_policy.get("structured_data", {})
        
        policy.incentive_type = incentive_data.get("incentive_type", "subsidy")
        policy.value_usd = incentive_data.get("value_usd", 0)
        policy.currency = incentive_data.get("currency", "CNY")
        policy.validity_period = incentive_data.get("validity_period", {})
        policy.eligibility_criteria = incentive_data.get("eligibility_criteria", [])
        policy.application_process = incentive_data.get("application_process", {})
        policy.benefits = incentive_data.get("benefits", [])
        policy.compliance_requirements = incentive_data.get("compliance_requirements", [])
    
    def _add_requirement_fields(self, policy: OpenInvestPolicy, structured_policy: Dict[str, Any]) -> None:
        """Add requirement-specific fields"""
        requirement_data = structured_policy.get("structured_data", {})
        
        policy.requirement_type = requirement_data.get("requirement_type", "regulatory")
        policy.mandatory = requirement_data.get("mandatory", True)
        policy.priority_level = requirement_data.get("priority_level", "medium")
        policy.eligibility_criteria = requirement_data.get("eligibility_criteria", [])
        policy.compliance_requirements = requirement_data.get("compliance_requirements", [])
    
    def _add_compliance_fields(self, policy: OpenInvestPolicy, structured_policy: Dict[str, Any]) -> None:
        """Add compliance-specific fields"""
        compliance_data = structured_policy.get("structured_data", {})
        
        policy.compliance_type = compliance_data.get("compliance_type", "regulatory")
        policy.compliance_level = compliance_data.get("compliance_level", "standard")
        policy.legal_basis = compliance_data.get("legal_basis", {})
        policy.compliance_requirements = compliance_data.get("requirements", [])
        policy.eligibility_criteria = compliance_data.get("eligibility_criteria", [])
    
    def _add_common_fields(self, policy: OpenInvestPolicy, structured_policy: Dict[str, Any]) -> None:
        """Add common fields to all policy types"""
        metadata = structured_policy.get("metadata", {})
        policy.metadata = {
            "extraction_date": metadata.get("extraction_date", datetime.now().isoformat()),
            "source_confidence": metadata.get("confidence_score", 0.0),
            "verification_status": metadata.get("verification_status", "pending"),
            "raw_text_length": metadata.get("raw_text_length", 0),
            "processing_timestamp": datetime.now().isoformat()
        }
    
    def _extract_jurisdiction(self, location: str) -> str:
        """Extract jurisdiction from location"""
        # Simple mapping - in production, use a comprehensive location database
        jurisdiction_map = {
            "Shanghai, China": "Shanghai Municipal Government",
            "Beijing, China": "Beijing Municipal Government",
            "Shenzhen, China": "Shenzhen Municipal Government",
            "Hangzhou, China": "Hangzhou Municipal Government",
            "Silicon Valley, USA": "State of California",
            "New York, USA": "State of New York",
            "London, UK": "UK Government",
            "Berlin, Germany": "German Government",
            "Singapore": "Singapore Government",
            "Tokyo, Japan": "Japanese Government"
        }
        
        return jurisdiction_map.get(location, "Unknown Jurisdiction")
    
    def _to_json_format(self, structured_policy: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to JSON format"""
        # Convert to OpenInvest format first, then to dict
        open_invest_policy = self._to_open_invest_format(structured_policy)
        return open_invest_policy.to_dict()
    
    def _to_csv_format(self, structured_policy: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to CSV format"""
        # Extract key fields for CSV
        csv_data = {
            "policy_id": structured_policy.get("policy_id", ""),
            "policy_type": structured_policy.get("policy_type", ""),
            "location": structured_policy.get("location", ""),
            "jurisdiction": self._extract_jurisdiction(structured_policy.get("location", "")),
            "industry": structured_policy.get("industry", ""),
            "title": structured_policy.get("title", ""),
            "description": structured_policy.get("description", ""),
            "confidence_score": structured_policy.get("confidence_score", 0.0),
            "source_url": structured_policy.get("metadata", {}).get("source_url", ""),
            "last_updated": structured_policy.get("metadata", {}).get("last_updated", "")
        }
        
        # Add policy-specific fields
        policy_type = structured_policy.get("policy_type", "")
        if policy_type == "incentive":
            csv_data["incentive_type"] = structured_policy.get("structured_data", {}).get("incentive_type", "")
            csv_data["value_usd"] = structured_policy.get("structured_data", {}).get("value_usd", 0)
            csv_data["currency"] = structured_policy.get("structured_data", {}).get("currency", "")
        elif policy_type == "requirement":
            csv_data["requirement_type"] = structured_policy.get("structured_data", {}).get("requirement_type", "")
            csv_data["mandatory"] = structured_policy.get("structured_data", {}).get("mandatory", False)
            csv_data["priority_level"] = structured_policy.get("structured_data", {}).get("priority_level", "")
        elif policy_type == "compliance":
            csv_data["compliance_type"] = structured_policy.get("structured_data", {}).get("compliance_type", "")
            csv_data["compliance_level"] = structured_policy.get("structured_data", {}).get("compliance_level", "")
        
        return csv_data
    
    def _to_xml_format(self, structured_policy: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to XML format"""
        # For XML, we'll return a dictionary that can be converted to XML
        xml_data = {
            "policy": {
                "@id": structured_policy.get("policy_id", ""),
                "@type": structured_policy.get("policy_type", ""),
                "location": structured_policy.get("location", ""),
                "jurisdiction": self._extract_jurisdiction(structured_policy.get("location", "")),
                "industry": structured_policy.get("industry", ""),
                "title": structured_policy.get("title", ""),
                "description": structured_policy.get("description", ""),
                "confidence_score": structured_policy.get("confidence_score", 0.0),
                "metadata": {
                    "source_url": structured_policy.get("metadata", {}).get("source_url", ""),
                    "last_updated": structured_policy.get("metadata", {}).get("last_updated", "")
                }
            }
        }
        
        return xml_data
    
    def batch_structure_policies(self, structured_policies: List[Dict[str, Any]], target_format: PolicyFormat = PolicyFormat.OPEN_INVEST) -> List[Union[OpenInvestPolicy, Dict[str, Any]]]:
        """Structure multiple policies in batch"""
        structured_results = []
        
        for policy in structured_policies:
            try:
                result = self.structure_policy(policy, target_format)
                structured_results.append(result)
            except Exception as e:
                logger.error(f"Error structuring policy {policy.get('policy_id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Batch structuring completed. Successfully structured {len(structured_results)} out of {len(structured_policies)} policies.")
        return structured_results
    
    def export_policies(self, policies: List[Union[OpenInvestPolicy, Dict[str, Any]]], output_path: str, format_type: PolicyFormat = PolicyFormat.JSON) -> None:
        """Export policies to file"""
        if format_type == PolicyFormat.JSON:
            export_data = []
            for policy in policies:
                if isinstance(policy, OpenInvestPolicy):
                    export_data.append(policy.to_dict())
                else:
                    export_data.append(policy)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        elif format_type == PolicyFormat.CSV:
            import csv
            
            if policies:
                # Get all possible keys from first policy
                first_policy = policies[0]
                if isinstance(first_policy, OpenInvestPolicy):
                    first_policy = first_policy.to_dict()
                
                fieldnames = list(first_policy.keys())
                
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for policy in policies:
                        if isinstance(policy, OpenInvestPolicy):
                            writer.writerow(policy.to_dict())
                        else:
                            writer.writerow(policy)
        
        elif format_type == PolicyFormat.XML:
            import xml.etree.ElementTree as ET
            
            root = ET.Element("policies")
            
            for policy in policies:
                policy_element = ET.SubElement(root, "policy")
                
                if isinstance(policy, OpenInvestPolicy):
                    policy_dict = policy.to_dict()
                else:
                    policy_dict = policy
                
                for key, value in policy_dict.items():
                    if isinstance(value, dict):
                        sub_element = ET.SubElement(policy_element, key)
                        for sub_key, sub_value in value.items():
                            sub_sub_element = ET.SubElement(sub_element, sub_key)
                            sub_sub_element.text = str(sub_value)
                    else:
                        element = ET.SubElement(policy_element, key)
                        element.text = str(value)
            
            tree = ET.ElementTree(root)
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        logger.info(f"Exported {len(policies)} policies to {output_path} in {format_type.value} format")
    
    def create_policy_index(self, policies: List[Union[OpenInvestPolicy, Dict[str, Any]]]) -> Dict[str, Any]:
        """Create searchable index of policies"""
        index = {
            "by_location": {},
            "by_industry": {},
            "by_type": {},
            "by_confidence": {},
            "searchable_text": []
        }
        
        for policy in policies:
            if isinstance(policy, OpenInvestPolicy):
                policy_dict = policy.to_dict()
            else:
                policy_dict = policy
            
            # Index by location
            location = policy_dict.get("location", "")
            if location:
                if location not in index["by_location"]:
                    index["by_location"][location] = []
                index["by_location"][location].append(policy_dict["policy_id"])
            
            # Index by industry
            industry = policy_dict.get("industry", "")
            if industry:
                if industry not in index["by_industry"]:
                    index["by_industry"][industry] = []
                index["by_industry"][industry].append(policy_dict["policy_id"])
            
            # Index by type
            policy_type = policy_dict.get("policy_type", "")
            if policy_type:
                if policy_type not in index["by_type"]:
                    index["by_type"][policy_type] = []
                index["by_type"][policy_type].append(policy_dict["policy_id"])
            
            # Index by confidence
            confidence = policy_dict.get("confidence_score", 0.0)
            confidence_range = self._get_confidence_range(confidence)
            if confidence_range not in index["by_confidence"]:
                index["by_confidence"][confidence_range] = []
            index["by_confidence"][confidence_range].append(policy_dict["policy_id"])
            
            # Create searchable text
            searchable_text = f"{policy_dict.get('title', '')} {policy_dict.get('description', '')} {policy_dict.get('location', '')} {policy_dict.get('industry', '')}"
            index["searchable_text"].append({
                "policy_id": policy_dict["policy_id"],
                "text": searchable_text.lower()
            })
        
        return index
    
    def _get_confidence_range(self, confidence: float) -> str:
        """Get confidence range for indexing"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    def search_policies(self, policies: List[Union[OpenInvestPolicy, Dict[str, Any]], query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search policies with optional filters"""
        results = []
        query_lower = query.lower()
        
        for policy in policies:
            if isinstance(policy, OpenInvestPolicy):
                policy_dict = policy.to_dict()
            else:
                policy_dict = policy
            
            # Apply text search
            searchable_text = f"{policy_dict.get('title', '')} {policy_dict.get('description', '')} {policy_dict.get('location', '')} {policy_dict.get('industry', '')}"
            searchable_text_lower = searchable_text.lower()
            
            if query_lower not in searchable_text_lower:
                continue
            
            # Apply filters
            if filters:
                if "location" in filters and policy_dict.get("location") != filters["location"]:
                    continue
                if "industry" in filters and policy_dict.get("industry") != filters["industry"]:
                    continue
                if "policy_type" in filters and policy_dict.get("policy_type") != filters["policy_type"]:
                    continue
                if "min_confidence" in filters and policy_dict.get("confidence_score", 0) < filters["min_confidence"]:
                    continue
            
            results.append(policy_dict)
        
        return results