"""
Global Policy Intelligence Engine - Mock Policy Database
提供示例政策数据和清洗服务，展示如何将碎片化的政策网页文字"洗"成符合OpenInvest标准的结构化情报

⚠️ TASK-P0-2 DATA-INTEGRITY 声明：
本文件全部内容为 MOCK 演示数据（verification_status="mock"），禁止标记为 VERIFIED。
其中的 source_url、联系方式、金额、日期均为虚构占位值，不代表任何真实政府来源。
"""

import json
import re
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PolicyType(str, Enum):
    """政策类型枚举"""
    TAX_INCENTIVE = "tax_incentive"
    SUBSIDY = "subsidy"
    LAND_GRANT = "land_grant"
    REGULATORY = "regulatory"
    COMPLIANCE = "compliance"
    INCENTIVE_PACKAGE = "incentive_package"

class Jurisdiction(str, Enum):
    """司法管辖区枚举"""
    SHANGHAI = "Shanghai, China"
    SHENZHEN = "Shenzhen, China"
    BEIJING = "Beijing, China"
    SILICON_VALLEY = "California, USA"
    SHENZHEN_BAY = "Shenzhen Bay Area, China"
    SINGAPORE = "Singapore"
    EU = "European Union"
    DUBAI = "Dubai, UAE"

@dataclass
class TaxBreak:
    """税收减免政策"""
    type: str
    rate_reduction: float
    duration_years: int
    max_amount_usd: Optional[float] = None
    eligibility_criteria: List[str] = None
    application_deadline: Optional[str] = None
    
    def __post_init__(self):
        if self.eligibility_criteria is None:
            self.eligibility_criteria = []

@dataclass
class Subsidy:
    """补贴政策"""
    type: str
    amount_usd: float
    purpose: str
    duration_months: int = 12
    currency: str = "USD"
    eligibility_criteria: List[str] = None
    application_deadline: Optional[str] = None
    
    def __post_init__(self):
        if self.eligibility_criteria is None:
            self.eligibility_criteria = []

@dataclass
class LandGrant:
    """土地政策"""
    type: str
    area_sqm: float
    duration_years: int
    rental_rate_per_sqm: Optional[float] = None
    location: Optional[str] = None
    infrastructure_included: List[str] = None
    
    def __post_init__(self):
        if self.infrastructure_included is None:
            self.infrastructure_included = []

@dataclass
class StaffingRequirement:
    """人员配置要求"""
    min_employees: Optional[int] = None
    min_researchers: Optional[int] = None
    phd_percentage: Optional[float] = None
    experience_years: Optional[int] = None
    salary_threshold_usd: Optional[float] = None

@dataclass
class IPRequirement:
    """知识产权要求"""
    min_patents: Optional[int] = None
    patent_types: List[str] = None
    min_trademarks: Optional[int] = None
    copyrights_required: bool = False
    
    def __post_init__(self):
        if self.patent_types is None:
            self.patent_types = []

@dataclass
class FinancialRequirement:
    """财务要求"""
    min_investment_usd: Optional[float] = None
    min_revenue_usd: Optional[float] = None
    credit_rating: Optional[str] = None
    net_worth_threshold: Optional[float] = None

@dataclass
class ComplianceRequirement:
    """合规要求"""
    data_localization: bool = False
    export_controls: bool = False
    security_clearance: Optional[str] = None
    environmental_standards: List[str] = None
    reporting_requirements: List[Dict] = None
    audit_requirements: List[str] = None
    
    def __post_init__(self):
        if self.environmental_standards is None:
            self.environmental_standards = []
        if self.reporting_requirements is None:
            self.reporting_requirements = []
        if self.audit_requirements is None:
            self.audit_requirements = []

@dataclass
class PolicyMetadata:
    """政策元数据"""
    policy_id: str
    source_url: str
    jurisdiction: str
    policy_type: PolicyType
    effective_date: str
    expiration_date: Optional[str] = None
    last_updated: Optional[str] = None
    crawl_timestamp: str = None
    confidence_score: float = 1.0
    
    def __post_init__(self):
        if self.crawl_timestamp is None:
            self.crawl_timestamp = datetime.datetime.now().isoformat()

@dataclass
class StructuredPolicy:
    """结构化政策数据"""
    policy_metadata: PolicyMetadata
    incentives: Dict[str, List]
    requirements: Dict[str, Any]
    compliance: ComplianceRequirement
    application_process: Dict[str, Any]
    target_industries: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "policy_metadata": asdict(self.policy_metadata),
            "incentives": self.incentives,
            "requirements": self.requirements,
            "compliance": asdict(self.compliance),
            "application_process": self.application_process,
            "target_industries": self.target_industries
        }
        return result
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

class MockPolicyDatabase:
    """Mock政策数据库"""
    
    def __init__(self):
        self.policies: Dict[str, StructuredPolicy] = {}
        self._load_mock_data()
    
    def _load_mock_data(self):
        """加载Mock数据"""
        # 上海张江高科技园区税收优惠政策
        shanghai_policy = self._create_shanghai_policy()
        self.policies[shanghai_policy.policy_id] = shanghai_policy
        
        # 深圳前海深港现代服务业合作区补贴政策
        shenzhen_policy = self._create_shenzhen_policy()
        self.policies[shenzhen_policy.policy_id] = shenzhen_policy
        
        # 硅谷科技创新政策
        silicon_valley_policy = self._create_silicon_valley_policy()
        self.policies[silicon_valley_policy.policy_id] = silicon_valley_policy
        
        # 新加坡科技创新政策
        singapore_policy = self._create_singapore_policy()
        self.policies[singapore_policy.policy_id] = singapore_policy
        
        logger.info(f"Loaded {len(self.policies)} mock policies")
    
    def _create_shanghai_policy(self) -> StructuredPolicy:
        """创建上海张江政策"""
        metadata = PolicyMetadata(
            policy_id="shanghai-zhangjiang-2024-tax",
            source_url="http://www.zhangjiang.gov.cn/policy/2024-tax-incentive",  # [UNVERIFIED] 虚构政府URL，未经官方核验
            jurisdiction="Shanghai, China",
            policy_type=PolicyType.TAX_INCENTIVE,
            effective_date="2024-01-01",
            expiration_date="2026-12-31",
            last_updated="2024-01-15"
        )
        
        incentives = {
            "tax_breaks": [
                TaxBreak(
                    type="corporate_tax_reduction",
                    rate_reduction=40,
                    duration_years=3,
                    max_amount_usd=500000,
                    eligibility_criteria=["高新技术企业认证", "年营收超1000万", "研发投入占比超15%"],
                    application_deadline="2024-12-31"
                ).__dict__
            ]
        }
        
        requirements = {
            "staffing": StaffingRequirement(
                min_employees=50,
                min_researchers=20,
                phd_percentage=30,
                experience_years=2
            ).__dict__,
            "intellectual_property": IPRequirement(
                min_patents=5,
                patent_types=["发明专利", "实用新型"],
                min_trademarks=2
            ).__dict__,
            "financial": FinancialRequirement(
                min_investment_usd=1000000,
                min_revenue_usd=10000000
            ).__dict__
        }
        
        compliance = ComplianceRequirement(
            data_localization=True,
            export_controls=False,
            environmental_standards=["ISO14001", "绿色制造标准"]
        )
        
        application_process = {
            "steps": [
                {
                    "step_number": 1,
                    "description": "提交高新技术企业申请",
                    "required_documents": ["营业执照", "财务报表", "专利证书"],
                    "duration_days": 30
                },
                {
                    "step_number": 2,
                    "description": "税务备案",
                    "required_documents": ["税务登记证", "财务报表"],
                    "duration_days": 15
                }
            ],
            "contact_info": {
                "department": "张江高新区税务局",
                "email": "tax@zhangjiang.gov.cn",
                "phone": "+86-21-12345678",
                "address": "上海市浦东新区张江高科技园区"
            }
        }
        
        target_industries = [
            {
                "industry": "ai_ml",
                "priority_level": "high",
                "specific_focus": ["机器学习", "自然语言处理", "计算机视觉"]
            },
            {
                "industry": "biotech",
                "priority_level": "high",
                "specific_focus": ["生物医药", "基因编辑", "精准医疗"]
            }
        ]
        
        return StructuredPolicy(
            policy_metadata=metadata,
            incentives=incentives,
            requirements=requirements,
            compliance=compliance,
            application_process=application_process,
            target_industries=target_industries
        )
    
    def _create_shenzhen_policy(self) -> StructuredPolicy:
        """创建深圳前海政策"""
        metadata = PolicyMetadata(
            policy_id="shenzhen-qianhai-2024-subsidy",
            source_url="http://qianhai.sz.gov.cn/policy/2024-subsidy",  # [UNVERIFIED] 虚构政府URL，未经官方核验
            jurisdiction="Shenzhen, China",
            policy_type=PolicyType.SUBSIDY,
            effective_date="2024-01-01",
            expiration_date="2027-12-31",
            last_updated="2024-02-01"
        )
        
        incentives = {
            "subsidies": [
                Subsidy(
                    type="rd_subsidy",
                    amount_usd=200000,
                    purpose="研发费用补贴",
                    duration_months=12,
                    eligibility_criteria=["注册在前海", "科技型企业", "研发投入超500万"],
                    application_deadline="2024-12-31"
                ).__dict__
            ]
        }
        
        requirements = {
            "staffing": StaffingRequirement(
                min_employees=30,
                min_researchers=15,
                phd_percentage=20
            ).__dict__,
            "intellectual_property": IPRequirement(
                min_patents=3,
                min_trademarks=1
            ).__dict__,
            "financial": FinancialRequirement(
                min_investment_usd=500000,
                min_revenue_usd=5000000
            ).__dict__
        }
        
        compliance = ComplianceRequirement(
            data_localization=False,
            export_controls=True,
            environmental_standards=["ISO14001"]
        )
        
        application_process = {
            "steps": [
                {
                    "step_number": 1,
                    "description": "提交补贴申请",
                    "required_documents": ["营业执照", "财务报表", "研发费用明细"],
                    "duration_days": 45
                }
            ],
            "contact_info": {
                "department": "前海管理局科技创新处",
                "email": "tech@qianhai.gov.cn",
                "phone": "+86-755-12345678"
            }
        }
        
        target_industries = [
            {
                "industry": "fintech",
                "priority_level": "high",
                "specific_focus": ["区块链", "数字货币", "智能投顾"]
            },
            {
                "industry": "cleantech",
                "priority_level": "medium",
                "specific_focus": ["新能源", "节能环保", "碳交易"]
            }
        ]
        
        return StructuredPolicy(
            policy_metadata=metadata,
            incentives=incentives,
            requirements=requirements,
            compliance=compliance,
            application_process=application_process,
            target_industries=target_industries
        )
    
    def _create_silicon_valley_policy(self) -> StructuredPolicy:
        """创建硅谷政策"""
        metadata = PolicyMetadata(
            policy_id="silicon-valley-2024-incentive-package",
            source_url="https://www.siliconvalley.org/policies/2024-incentive-package",  # [UNVERIFIED] 虚构政府URL，未经官方核验
            jurisdiction="California, USA",
            policy_type=PolicyType.INCENTIVE_PACKAGE,
            effective_date="2024-01-01",
            expiration_date=None,
            last_updated="2024-03-01"
        )
        
        incentives = {
            "tax_breaks": [
                TaxBreak(
                    type="corporate_tax_reduction",
                    rate_reduction=15,
                    duration_years=5,
                    eligibility_criteria=["加州注册", "科技企业", "创造就业岗位"]
                ).__dict__
            ],
            "subsidies": [
                Subsidy(
                    type="rd_subsidy",
                    amount_usd=100000,
                    purpose="研发补贴",
                    duration_months=12,
                    eligibility_criteria ["早期科技企业", "创新项目"]
                ).__dict__
            ]
        }
        
        requirements = {
            "staffing": StaffingRequirement(
                min_employees=10,
                min_researchers=5,
                experience_years=1
            ).__dict__,
            "financial": FinancialRequirement(
                min_investment_usd=200000,
                min_revenue_usd=1000000
            ).__dict__
        }
        
        compliance = ComplianceRequirement(
            data_localization=False,
            export_controls=True,
            security_clearance="basic"
        )
        
        application_process = {
            "steps": [
                {
                    "step_number": 1,
                    "description": "在线申请",
                    "required_documents": ["商业计划书", "财务报表", "团队简历"],
                    "duration_days": 60
                }
            ],
            "contact_info": {
                "department": "Silicon Valley Innovation Office",
                "email": "innovation@siliconvalley.org",
                "phone": "+1-408-123-4567"
            }
        }
        
        target_industries = [
            {
                "industry": "ai_ml",
                "priority_level": "high",
                "specific_focus": ["深度学习", "自动驾驶", "AI芯片"]
            },
            {
                "industry": "blockchain",
                "priority_level": "medium",
                "specific_focus": ["DeFi", "NFT", "Web3"]
            }
        ]
        
        return StructuredPolicy(
            policy_metadata=metadata,
            incentives=incentives,
            requirements=requirements,
            compliance=compliance,
            application_process=application_process,
            target_industries=target_industries
        )
    
    def _create_singapore_policy(self) -> StructuredPolicy:
        """创建新加坡政策"""
        metadata = PolicyMetadata(
            policy_id="singapore-2024-land-grant",
            source_url="https://www.enterprise.gov.sg/policies/2024-land-grant",  # [UNVERIFIED] 虚构政府URL，未经官方核验
            jurisdiction="Singapore",
            policy_type=PolicyType.LAND_GRANT,
            effective_date="2024-01-01",
            expiration_date="2028-12-31",
            last_updated="2024-01-01"
        )
        
        incentives = {
            "land_grants": [
                LandGrant(
                    type="land_lease",
                    area_sqm=1000,
                    duration_years=10,
                    rental_rate_per_sqm=50,
                    location="One North",
                    infrastructure_included=["lab_equipment", "high_speed_internet", "security_system"]
                ).__dict__
            ]
        }
        
        requirements = {
            "staffing": StaffingRequirement(
                min_employees=20,
                min_researchers=10,
                phd_percentage=25
            ).__dict__,
            "intellectual_property": IPRequirement(
                min_patents=2,
                min_trademarks=1
            ).__dict__,
            "financial": FinancialRequirement(
                min_investment_usd=800000,
                min_revenue_usd=2000000
            ).__dict__
        }
        
        compliance = ComplianceRequirement(
            data_localization=False,
            export_controls=False,
            environmental_standards=["ISO14001", "Green Mark"]
        )
        
        application_process = {
            "steps": [
                {
                    "step_number": 1,
                    "description": "提交土地申请",
                    "required_documents": ["商业计划书", "财务报表", "技术方案"],
                    "duration_days": 90
                }
            ],
            "contact_info": {
                "department": "Enterprise Singapore",
                "email": "land@enterprisesg.gov.sg",
                "phone": "+65-6337-5800"
            }
        }
        
        target_industries = [
            {
                "industry": "biotech",
                "priority_level": "high",
                "specific_focus": ["生物医药", "医疗器械", "精准医疗"]
            },
            {
                "industry": "cleantech",
                "priority_level": "high",
                "specific_focus": ["清洁能源", "可持续发展", "环保技术"]
            }
        ]
        
        return StructuredPolicy(
            policy_metadata=metadata,
            incentives=incentives,
            requirements=requirements,
            compliance=compliance,
            application_process=application_process,
            target_industries=target_industries
        )
    
    def get_policy(self, policy_id: str) -> Optional[StructuredPolicy]:
        """获取政策"""
        return self.policies.get(policy_id)
    
    def get_policies_by_jurisdiction(self, jurisdiction: str) -> List[StructuredPolicy]:
        """按司法管辖区获取政策"""
        return [policy for policy in self.policies.values() 
                if policy.policy_metadata.jurisdiction == jurisdiction]
    
    def get_policies_by_industry(self, industry: str) -> List[StructuredPolicy]:
        """按行业获取政策"""
        result = []
        for policy in self.policies.values():
            for target in policy.target_industries:
                if target["industry"] == industry:
                    result.append(policy)
                    break
        return result
    
    def search_policies(self, keywords: List[str]) -> List[StructuredPolicy]:
        """搜索政策"""
        result = []
        for policy in self.policies.values():
            # 搜索政策描述和元数据
            search_text = f"{policy.policy_metadata.policy_id} {policy.policy_metadata.jurisdiction}"
            for target in policy.target_industries:
                search_text += f" {target['industry']} {target['specific_focus']}"
            
            if any(keyword.lower() in search_text.lower() for keyword in keywords):
                result.append(policy)
        
        return result