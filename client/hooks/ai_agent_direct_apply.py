"""
AI Agent Direct Apply Integration Hook
Demonstrates how projects can apply to government policies through secure gateway
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from api.protocol_client import ProtocolClient, ClientType
from utils.project_evaluator import ProjectEvaluator, MatchScore

logger = logging.getLogger(__name__)

class ApplicationStatus(str, Enum):
    """Application status enumeration"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUESTED_MORE_INFO = "requested_more_info"

class SecurityLevel(str, Enum):
    """Security level for data transmission"""
    BASIC = "basic"
    ENHANCED = "enhanced"
    RESTRICTED = "restricted"

@dataclass
class ApplyResult:
    """Application result data structure"""
    application_id: str
    status: ApplicationStatus
    match_score: float
    confidence_level: str
    next_steps: List[str]
    estimated_processing_time: str
    contact_officer: Optional[str] = None
    required_documents: List[str] = None
    rejection_reason: Optional[str] = None

@dataclass
class PolicyTarget:
    """Target policy information"""
    policy_id: str
    location: str
    title: str
    industry_focus: List[str]
    incentives: List[Dict[str, Any]]
    compliance_requirements: Dict[str, Any]
    contact_info: Dict[str, str]

@dataclass
class ProjectProfile:
    """Project profile for application"""
    project_id: str
    name: str
    industry: str
    scale: str
    tech_readiness_level: str
    core_competencies: List[str]
    investment_requirements: Dict[str, Any]
    team_size: int
    ip_portfolio: Dict[str, int]
    risk_factors: List[str]

class SecurityGateway:
    """Security gateway for data anonymization and secure transmission"""
    
    def __init__(self):
        self.sensitive_fields = [
            "exact_revenue", "precise_employee_count", "internal_financials",
            "proprietary_algorithms", "unpatented_ip", "strategic_plans"
        ]
    
    def anonymize_project_data(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize sensitive project data for secure transmission
        
        Args:
            project_data: Raw project data
            
        Returns:
            Anonymized project data
        """
        anonymized = project_data.copy()
        
        # Apply anonymization rules
        anonymized["revenue_range"] = self._get_revenue_range(anonymized.get("revenue", 0))
        anonymized["employee_range"] = self._get_employee_range(anonymized.get("team_size", 0))
        anonymized["tech_maturity"] = self._get_tech_maturity(anonymized.get("tech_readiness_level", "unknown"))
        
        # Remove sensitive fields
        for field in self.sensitive_fields:
            anonymized.pop(field, None)
        
        # Add anonymization metadata
        anonymized["anonymization_level"] = "enhanced"
        anonymized["data_hash"] = self._generate_data_hash(anonymized)
        
        return anonymized
    
    def encrypt_transmission(self, data: Dict[str, Any], security_level: SecurityLevel = SecurityLevel.ENHANCED) -> Dict[str, Any]:
        """
        Encrypt data for secure transmission
        
        Args:
            data: Data to encrypt
            security_level: Security level for encryption
            
        Returns:
            Encrypted data wrapper
        """
        # In real implementation, use actual encryption
        encrypted_data = {
            "payload": data,
            "encryption_level": security_level.value,
            "timestamp": asyncio.get_event_loop().time(),
            "checksum": self._generate_checksum(data)
        }
        
        return encrypted_data
    
    def decrypt_transmission(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt received data
        
        Args:
            encrypted_data: Encrypted data
            
        Returns:
            Decrypted data
        """
        # In real implementation, use actual decryption
        return encrypted_data.get("payload", {})
    
    def _get_revenue_range(self, revenue: float) -> str:
        """Get revenue range for anonymization"""
        if revenue < 1000000:
            return "< $1M"
        elif revenue < 10000000:
            return "$1M - $10M"
        elif revenue < 100000000:
            return "$10M - $100M"
        else:
            return "> $100M"
    
    def _get_employee_range(self, employees: int) -> str:
        """Get employee range for anonymization"""
        if employees < 10:
            return "< 10"
        elif employees < 50:
            return "10 - 50"
        elif employees < 200:
            return "50 - 200"
        else:
            return "> 200"
    
    def _get_tech_maturity(self, trl_level: str) -> str:
        """Get technology maturity level"""
        maturity_mapping = {
            "concept": "early_stage",
            "proof_of_concept": "early_stage",
            "prototype": "development_stage",
            "pilot": "validation_stage",
            "production": "mature_stage"
        }
        return maturity_mapping.get(trl_level, "unknown")
    
    def _generate_data_hash(self, data: Dict[str, Any]) -> str:
        """Generate data hash for integrity checking"""
        # In real implementation, use proper hash function
        return f"hash_{len(str(data))}"
    
    def _generate_checksum(self, data: Dict[str, Any]) -> str:
        """Generate checksum for data integrity"""
        # In real implementation, use proper checksum
        return f"checksum_{len(str(data))}"

class AIAgentDirectApply:
    """AI Agent Direct Apply integration hook"""
    
    def __init__(self, protocol_client: ProtocolClient, security_gateway: SecurityGateway = None):
        self.client = protocol_client
        self.security_gateway = security_gateway or SecurityGateway()
        self.evaluator = ProjectEvaluator(protocol_client)
    
    async def browse_and_apply(self, project_id: str, policy_id: str) -> ApplyResult:
        """
        Browse policies and trigger direct application
        
        Args:
            project_id: ID of the project applying
            policy_id: ID of the target policy
            
        Returns:
            ApplyResult: Application result
        """
        logger.info(f"Starting direct application for project {project_id} to policy {policy_id}")
        
        try:
            # Step 1: Retrieve project data
            project_data = await self.client.get_tech_readiness(project_id)
            project_profile = self._create_project_profile(project_data)
            
            # Step 2: Retrieve target policy
            policy_data = await self.client.get_landing_requirements(
                location=policy_id.split('-')[0],  # Extract location from policy_id
                industry=project_data["industry"]
            )
            policy_target = self._create_policy_target(policy_data)
            
            # Step 3: Evaluate match
            match_result = await self.evaluator.evaluate_project_policy_match(
                project_profile, policy_target
            )
            
            # Step 4: Anonymize data
            anonymized_project = self.security_gateway.anonymize_project_data(project_data)
            
            # Step 5: Prepare application
            application_result = await self._prepare_application(
                project_profile, policy_target, match_result, anonymized_project
            )
            
            logger.info(f"Application prepared successfully: {application_result.application_id}")
            return application_result
            
        except Exception as e:
            logger.error(f"Error in direct application: {str(e)}")
            raise
    
    async def trigger_direct_apply(self, project_id: str, policy_id: str) -> ApplyResult:
        """
        Trigger direct application through secure gateway
        
        Args:
            project_id: ID of the project applying
            policy_id: ID of the target policy
            
        Returns:
            ApplyResult: Application result
        """
        logger.info(f"Triggering direct apply for {project_id} -> {policy_id}")
        
        # Get project and policy data
        project_data = await self.client.get_tech_readiness(project_id)
        policy_data = await self.client.get_landing_requirements(
            location=policy_id.split('-')[0],
            industry=project_data["industry"]
        )
        
        # Apply data anonymization
        anonymized_data = self.security_gateway.anonymize_project_data(project_data)
        
        # Secure transmission to target client
        encrypted_data = self.security_gateway.encrypt_transmission(anonymized_data)
        
        # Simulate application submission
        application_id = f"app_{project_id}_{policy_id}_{asyncio.get_event_loop().time()}"
        
        return ApplyResult(
            application_id=application_id,
            status=ApplicationStatus.PENDING,
            match_score=self._calculate_match_score(project_data, policy_data),
            confidence_level="high",
            next_steps=[
                "Application submitted to review board",
                "Initial screening within 5 business days",
                "Detailed technical evaluation",
                "Final approval decision"
            ],
            estimated_processing_time="15-30 business days",
            contact_officer="Investment Promotion Officer",
            required_documents=[
                "Business Plan",
                "Financial Projections",
                "Technical Documentation",
                "Team CVs",
                "IP Portfolio Documentation"
            ]
        )
    
    def _create_project_profile(self, project_data: Dict[str, Any]) -> ProjectProfile:
        """Create project profile from project data"""
        return ProjectProfile(
            project_id=project_data["project_id"],
            name=project_data.get("name", "Unknown Project"),
            industry=project_data.get("industry", "unknown"),
            scale=project_data.get("scale", "unknown"),
            tech_readiness_level=project_data.get("level", "unknown"),
            core_competencies=project_data.get("core_competencies", []),
            investment_requirements=project_data.get("investment_requirements", {}),
            team_size=project_data.get("team_size", 0),
            ip_portfolio=project_data.get("ip_portfolio", {}),
            risk_factors=project_data.get("risk_factors", [])
        )
    
    def _create_policy_target(self, policy_data: Dict[str, Any]) -> PolicyTarget:
        """Create policy target from policy data"""
        return PolicyTarget(
            policy_id=policy_data.get("policy_id", "unknown"),
            location=policy_data.get("location", "unknown"),
            title=policy_data.get("title", "Unknown Policy"),
            industry_focus=policy_data.get("industry_focus", []),
            incentives=policy_data.get("incentives", []),
            compliance_requirements=policy_data.get("compliance_requirements", {}),
            contact_info=policy_data.get("contact_info", {})
        )
    
    async def _prepare_application(self, project_profile: ProjectProfile, policy_target: PolicyTarget, 
                                 match_result: Dict[str, Any], anonymized_project: Dict[str, Any]) -> ApplyResult:
        """Prepare application package"""
        
        # Generate application ID
        application_id = f"app_{project_profile.project_id}_{policy_target.policy_id}_{asyncio.get_event_loop().time()}"
        
        # Determine application status based on match score
        match_score = match_result.get("overall_score", 0.5)
        if match_score >= 0.8:
            status = ApplicationStatus.APPROVED
        elif match_score >= 0.6:
            status = ApplicationStatus.UNDER_REVIEW
        else:
            status = ApplicationStatus.REQUESTED_MORE_INFO
        
        return ApplyResult(
            application_id=application_id,
            status=status,
            match_score=match_score,
            confidence_level=match_result.get("confidence_level", "medium"),
            next_steps=self._generate_next_steps(status, match_score),
            estimated_processing_time=self._estimate_processing_time(policy_target, match_score),
            contact_officer=policy_target.contact_info.get("primary_officer"),
            required_documents=self._get_required_documents(policy_target, project_profile),
            rejection_reason=None if status != ApplicationStatus.REJECTED else "Insufficient match criteria"
        )
    
    def _calculate_match_score(self, project_data: Dict[str, Any], policy_data: Dict[str, Any]) -> float:
        """Calculate match score between project and policy"""
        score = 0.5  # Base score
        
        # Industry match
        if project_data.get("industry") in policy_data.get("industry_focus", []):
            score += 0.3
        
        # Scale match
        project_scale = project_data.get("scale", "unknown")
        if project_scale in policy_data.get("target_scales", []):
            score += 0.2
        
        # Tech readiness match
        trl_level = project_data.get("level", "unknown")
        if trl_level in policy_data.get("min_trl_levels", []):
            score += 0.2
        
        # Team size match
        team_size = project_data.get("team_size", 0)
        if team_size >= policy_data.get("min_team_size", 0):
            score += 0.1
        
        # Investment match
        investment = project_data.get("investment_requirements", {}).get("min_investment_usd", 0)
        if investment >= policy_data.get("min_investment_usd", 0):
            score += 0.2
        
        return min(1.0, score)
    
    def _generate_next_steps(self, status: ApplicationStatus, match_score: float) -> List[str]:
        """Generate next steps based on application status"""
        if status == ApplicationStatus.APPROVED:
            return [
                "Contract preparation",
                "Legal review",
                "Onboarding process",
                "First incentive disbursement"
            ]
        elif status == ApplicationStatus.UNDER_REVIEW:
            return [
                "Technical documentation review",
                "Financial verification",
                "Site visit scheduling",
                "Final approval process"
            ]
        elif status == ApplicationStatus.REQUESTED_MORE_INFO:
            return [
                "Additional documentation required",
                "Technical clarification meeting",
                "Financial audit preparation",
                "Resubmission deadline"
            ]
        else:
            return [
                "Application rejected",
                "Feedback provided",
                "Appeal process available",
                "Alternative options suggested"
            ]
    
    def _estimate_processing_time(self, policy_target: PolicyTarget, match_score: float) -> str:
        """Estimate processing time based on policy and match score"""
        base_time = 30  # days
        
        if match_score >= 0.8:
            base_time *= 0.7  # Fast track
        elif match_score < 0.6:
            base_time *= 1.5  # Requires more review
        
        # Policy-specific adjustments
        if "fast_track" in policy_target.title.lower():
            base_time *= 0.5
        
        return f"{int(base_time)}-{int(base_time * 1.2)} business days"
    
    def _get_required_documents(self, policy_target: PolicyTarget, project_profile: ProjectProfile) -> List[str]:
        """Get required documents based on policy and project"""
        base_documents = [
            "Business Registration",
            "Financial Statements",
            "Technical Documentation",
            "Team CVs",
            "IP Portfolio"
        ]
        
        # Policy-specific requirements
        if "quantum" in policy_target.title.lower():
            base_documents.extend(["Quantum Technology Whitepaper", "Security Clearance Application"])
        
        if "ai" in project_profile.industry.lower():
            base_documents.append("AI Ethics Assessment")
        
        return base_documents

# Example usage
async def example_usage():
    """Example usage of AI Agent Direct Apply"""
    
    # Initialize client
    client = ProtocolClient("http://localhost:8000", ClientType.GOV)
    direct_apply = AIAgentDirectApply(client)
    
    # Example project and policy IDs
    project_id = "quantum-encryption-startup-2024"
    policy_id = "shanghai-quantum-hub-2024"
    
    # Trigger direct apply
    result = await direct_apply.trigger_direct_apply(project_id, policy_id)
    
    print(f"Application ID: {result.application_id}")
    print(f"Status: {result.status}")
    print(f"Match Score: {result.match_score}")
    print(f"Next Steps: {result.next_steps}")
    print(f"Estimated Processing Time: {result.estimated_processing_time}")

if __name__ == "__main__":
    asyncio.run(example_usage())