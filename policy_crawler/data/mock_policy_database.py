"""
Mock Policy Database
提供示例政策数据，用于演示政策清洗和结构化功能

⚠️ TASK-P0-2 DATA-INTEGRITY 声明：
本文件全部内容为 MOCK 演示数据（verification_status="mock"），禁止标记为 VERIFIED。
其中的电话/邮箱/地址/联系人名均为虚构占位值，不代表任何真实政府机构联系方式。
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class MockPolicyDatabase:
    """模拟政策数据库"""
    
    def __init__(self):
        self.policies = self._generate_mock_policies()
    
    def _generate_mock_policies(self) -> List[Dict[str, Any]]:
        """生成模拟政策数据"""
        policies = []
        
        # 上海张江高科技园区政策
        shanghai_policy = {
            "policy_metadata": {
                "policy_id": "shanghai-zhangjiang-2024",
                "source_url": "https://www.zjpark.gov.cn/policies/2024/tech-incentives",
                "publication_date": "2024-01-15",
                "last_updated": "2024-08-01",
                "jurisdiction": "Shanghai",
                "policy_type": "incentive",
                "authority": "Shanghai Municipal Government",
                "validity_period": {
                    "start_date": "2024-01-15",
                    "end_date": "2025-12-31",
                    "is_permanent": False
                }
            },
            "incentives": {
                "tax_incentives": [
                    {
                        "type": "rd_tax_credit",
                        "description": "研发费用加计扣除",
                        "rate_reduction": 0.75,
                        "max_amount_usd": 500000,
                        "duration_years": 3,
                        "eligibility_criteria": ["高新技术企业认证", "研发费用占比超过15%"],
                        "application_deadline": "2025-12-31"
                    },
                    {
                        "type": "corporate_tax_reduction",
                        "description": "企业所得税减免",
                        "rate_reduction": 0.15,
                        "max_amount_usd": 300000,
                        "duration_years": 5,
                        "eligibility_criteria": ["注册地在上海", "年营收超过1000万美元"],
                        "application_deadline": "2025-12-31"
                    }
                ],
                "financial_subsidies": [
                    {
                        "type": "startup_grant",
                        "amount_usd": 100000,
                        "currency": "USD",
                        "purpose": "初创企业启动资金",
                        "duration_months": 12,
                        "eligibility_criteria": ["注册时间不超过2年", "团队规模10-50人"],
                        "application_deadline": "2024-12-31"
                    },
                    {
                        "type": "rd_funding",
                        "amount_usd": 500000,
                        "currency": "USD",
                        "purpose": "研发项目资助",
                        "duration_months": 24,
                        "eligibility_criteria": ["拥有核心专利", "研发团队博士比例超过30%"],
                        "application_deadline": "2024-11-30"
                    }
                ],
                "land_incentives": [
                    {
                        "type": "rental_discount",
                        "location": "张江科学城",
                        "area_sqm": 1000,
                        "rental_discount_rate": 0.5,
                        "construction_grant_usd": 200000,
                        "infrastructure_support": ["高速网络", "实验室设施", "会议室"],
                        "eligibility_criteria": ["AI或量子计算企业", "研发投入超过500万美元"]
                    }
                ]
            },
            "requirements": {
                "staffing_requirements": {
                    "min_employees": 20,
                    "min_researchers": 10,
                    "researcher_percentage": 0.5,
                    "min_phd_count": 3,
                    "phd_percentage": 0.3,
                    "min_experience_years": 2,
                    "senior_management_requirements": ["CEO需有相关行业经验", "CTO需有技术背景"]
                },
                "intellectual_property": {
                    "min_patents": 2,
                    "patent_types": ["发明专利", "实用新型专利"],
                    "min_trademarks": 1,
                    "min_copyrights": 1,
                    "ip_ownership_requirements": ["IP所有权归企业所有", "无知识产权纠纷"]
                },
                "financial_requirements": {
                    "min_investment_usd": 1000000,
                    "min_revenue_usd": 2000000,
                    "net_worth_requirements": ["净资产不低于500万美元"],
                    "bank_guarantee_amount": 100000
                },
                "technology_requirements": {
                    "tech_stack_requirements": ["Python", "TensorFlow", "PyTorch"],
                    "TRL_requirements": "prototype",
                    "certification_requirements": ["高新技术企业认证", "ISO9001质量管理体系"],
                    "technology_transfer_requirements": ["技术成果转化率超过30%"]
                }
            },
            "compliance": {
                "data_localization": {
                    "required": True,
                    "scope": ["用户数据", "研发数据", "财务数据"],
                    "penalties": ["罚款", "暂停优惠政策", "取消资质"]
                },
                "export_controls": {
                    "applies": True,
                    "restricted_technologies": ["量子加密算法", "AI决策系统"],
                    "licensing_requirements": ["出口许可证", "技术审查"],
                    "penalties": ["罚款", "禁止出口", "刑事责任"]
                },
                "security_clearance": {
                    "required": False,
                    "clearance_levels": [],
                    "background_check_requirements": []
                },
                "environmental_compliance": {
                    "standards": ["ISO14001", "GB/T24001"],
                    "certifications_required": ["环境管理体系认证"],
                    "reporting_requirements": ["季度环境报告", "年度碳排放报告"]
                },
                "labor_compliance": {
                    "labor_laws": ["劳动合同法", "社会保险法"],
                    "benefit_requirements": ["五险一金", "带薪年假"],
                    "workplace_safety": ["安全生产许可证", "消防验收"]
                }
            },
            "application_process": {
                "steps": [
                    {
                        "step_number": 1,
                        "description": "提交申请材料",
                        "required_documents": ["营业执照", "商业计划书", "技术白皮书", "团队简历"],
                        "duration_days": 15,
                        "contact_information": {
                            "email": "application@zjpark.gov.cn",
                            "phone": "+86-21-12345678",
                            "address": "上海市浦东新区张江高科技园区"
                        }
                    },
                    {
                        "step_number": 2,
                        "description": "专家评审",
                        "required_documents": ["技术可行性报告", "市场分析报告", "财务预测"],
                        "duration_days": 30,
                        "contact_information": {
                            "email": "review@zjpark.gov.cn",
                            "phone": "+86-21-87654321",
                            "address": "上海市浦东新区张江高科技园区"
                        }
                    },
                    {
                        "step_number": 3,
                        "description": "签约落地",
                        "required_documents": ["投资协议", "土地租赁合同", "优惠政策协议"],
                        "duration_days": 10,
                        "contact_information": {
                            "email": "contract@zjpark.gov.cn",
                            "phone": "+86-21-24681357",
                            "address": "上海市浦东新区张江高科技园区"
                        }
                    }
                ],
                "estimated_processing_time": "55个工作日",
                "appeal_process": ["提交申诉材料", "专家复审", "最终裁定"],
                "success_criteria": ["技术先进性评分超过80分", "市场前景评估良好", "团队结构合理"]
            },
            "contact_information": {
                "department": "招商局",
                "contact_person": "张经理",
                "email": "zhang@zjpark.gov.cn",
                "phone": "+86-21-13800138000",
                "address": "上海市浦东新区张江高科技园区招商局",
                "website": "https://www.zjpark.gov.cn",
                "office_hours": "周一至周五 9:00-17:00"
            },
            "tags": ["上海", "张江", "高科技园区", "AI", "量子计算", "税收优惠", "研发补贴"],
            "priority_score": 9,
            "target_industries": ["ai_ml", "quantum_computing", "biotech", "semiconductor"]
        }
        
        # 硅谷科技创新中心政策
        silicon_valley_policy = {
            "policy_metadata": {
                "policy_id": "silicon-valley-innovation-hub-2024",
                "source_url": "https://www.svhub.org/policies/2024/tech-incentives",
                "publication_date": "2024-02-01",
                "last_updated": "2024-07-15",
                "jurisdiction": "California",
                "policy_type": "incentive",
                "authority": "Silicon Valley Innovation Hub",
                "validity_period": {
                    "start_date": "2024-02-01",
                    "end_date": "2026-01-31",
                    "is_permanent": False
                }
            },
            "incentives": {
                "tax_incentives": [
                    {
                        "type": "rd_tax_credit",
                        "description": "Research & Development Tax Credit",
                        "rate_reduction": 0.25,
                        "max_amount_usd": 1000000,
                        "duration_years": 5,
                        "eligibility_criteria": ["R&D expenses over $500k", "California-based company"],
                        "application_deadline": "2026-01-31"
                    }
                ],
                "financial_subsidies": [
                    {
                        "type": "startup_grant",
                        "amount_usd": 200000,
                        "currency": "USD",
                        "purpose": "Early-stage startup funding",
                        "duration_months": 18,
                        "eligibility_criteria": ["Seed stage funding", "Diversity team", "Innovative technology"],
                        "application_deadline": "2024-12-31"
                    },
                    {
                        "type": "equipment_subsidy",
                        "amount_usd": 150000,
                        "currency": "USD",
                        "purpose": "Advanced equipment purchase",
                        "duration_months": 12,
                        "eligibility_criteria": ["AI/ML hardware", "Quantum computing equipment"],
                        "application_deadline": "2024-11-30"
                    }
                ],
                "land_incentives": [
                    {
                        "type": "rental_discount",
                        "location": "Palo Alto Innovation District",
                        "area_sqm": 500,
                        "rental_discount_rate": 0.3,
                        "construction_grant_usd": 300000,
                        "infrastructure_support": ["Gigabit fiber", "AI clusters", "Quantum labs"],
                        "eligibility_criteria": ["DeepTech companies", "Series A+ funding"]
                    }
                ]
            },
            "requirements": {
                "staffing_requirements": {
                    "min_employees": 15,
                    "min_researchers": 8,
                    "researcher_percentage": 0.6,
                    "min_phd_count": 2,
                    "phd_percentage": 0.4,
                    "min_experience_years": 3,
                    "senior_management_requirements": ["CEO experience in tech", "CTO PhD in relevant field"]
                },
                "intellectual_property": {
                    "min_patents": 1,
                    "patent_types": ["Patent", "Trade secret"],
                    "min_trademarks": 1,
                    "min_copyrights": 1,
                    "ip_ownership_requirements": ["Clean IP portfolio", "No infringement history"]
                },
                "financial_requirements": {
                    "min_investment_usd": 2000000,
                    "min_revenue_usd": 5000000,
                    "net_worth_requirements": ["Net worth > $2M", "Positive cash flow"],
                    "bank_guarantee_amount": 200000
                },
                "technology_requirements": {
                    "tech_stack_requirements": ["Python", "TensorFlow", "PyTorch", "CUDA"],
                    "TRL_requirements": "pilot",
                    "certification_requirements": ["ISO 27001", "SOC 2"],
                    "technology_transfer_requirements": ["Open source contribution", "Academic partnerships"]
                }
            },
            "compliance": {
                "data_localization": {
                    "required": False,
                    "scope": [],
                    "penalties": []
                },
                "export_controls": {
                    "applies": True,
                    "restricted_technologies": ["Quantum tech", "Advanced AI"],
                    "licensing_requirements": ["EAR compliance", "ITAR certification"],
                    "penalties": ["Export restrictions", "Civil penalties"]
                },
                "security_clearance": {
                    "required": False,
                    "clearance_levels": [],
                    "background_check_requirements": ["Standard background check"]
                },
                "environmental_compliance": {
                    "standards": ["ISO 14001", "California Environmental Quality Act"],
                    "certifications_required": ["Environmental compliance certification"],
                    "reporting_requirements": ["Annual environmental audit"]
                },
                "labor_compliance": {
                    "labor_laws": ["California Labor Code", "Federal labor laws"],
                    "benefit_requirements": ["Health insurance", "Retirement plan"],
                    "workplace_safety": ["OSHA compliance", "Workplace safety training"]
                }
            },
            "application_process": {
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Online Application Submission",
                        "required_documents": ["Business plan", "Team bios", "Technology description", "Financial projections"],
                        "duration_days": 10,
                        "contact_information": {
                            "email": "applications@svhub.org",
                            "phone": "+1-650-123-4567",
                            "address": "Palo Alto, CA"
                        }
                    },
                    {
                        "step_number": 2,
                        "description": "Due Diligence Review",
                        "required_documents": ["Financial statements", "IP documentation", "Market analysis"],
                        "duration_days": 20,
                        "contact_information": {
                            "email": "due diligence@svhub.org",
                            "phone": "+1-650-234-5678",
                            "address": "Palo Alto, CA"
                        }
                    },
                    {
                        "step_number": 3,
                        "description": "Investment Committee Review",
                        "required_documents": ["Final proposal", "Legal documents", "Term sheet"],
                        "duration_days": 15,
                        "contact_information": {
                            "email": "review@svhub.org",
                            "phone": "+1-650-345-6789",
                            "address": "Palo Alto, CA"
                        }
                    }
                ],
                "estimated_processing_time": "45 days",
                "appeal_process": ["Reconsideration request", "Arbitration", "Final review"],
                "success_criteria": ["Innovation score > 80", "Market potential > 75", "Team quality > 85"]
            },
            "contact_information": {
                "department": "Investment Relations",
                "contact_person": "Sarah Johnson",
                "email": "sarah@svhub.org",
                "phone": "+1-650-555-0123",
                "address": "350 Tasman Drive, Palo Alto, CA",
                "website": "https://www.svhub.org",
                "office_hours": "Monday-Friday 9:00-18:00"
            },
            "tags": ["Silicon Valley", "California", "Innovation Hub", "AI", "Quantum", "Startup", "Tax Credit"],
            "priority_score": 10,
            "target_industries": ["ai_ml", "quantum_computing", "robotics", "fintech", "cleantech"]
        }
        
        # 欧盟数字计划政策
        eu_policy = {
            "policy_metadata": {
                "policy_id": "eu-digital-plan-2024",
                "source_url": "https://digital-strategy.ec.europa.eu/policies/2024/digital-incentives",
                "publication_date": "2024-03-01",
                "last_updated": "2024-07-01",
                "jurisdiction": "EU",
                "policy_type": "incentive",
                "authority": "European Commission",
                "validity_period": {
                    "start_date": "2024-03-01",
                    "end_date": "2027-02-28",
                    "is_permanent": False
                }
            },
            "incentives": {
                "tax_incentives": [
                    {
                        "type": "corporate_tax_reduction",
                        "description": "Digital Innovation Tax Credit",
                        "rate_reduction": 0.20,
                        "max_amount_usd": 800000,
                        "duration_years": 4,
                        "eligibility_criteria": ["EU-based company", "Digital transformation project"],
                        "application_deadline": "2027-02-28"
                    }
                ],
                "financial_subsidies": [
                    {
                        "type": "rd_funding",
                        "amount_usd": 750000,
                        "currency": "USD",
                        "purpose": "Digital R&D project funding",
                        "duration_months": 36,
                        "eligibility_criteria": ["Cross-border collaboration", "Open source contribution"],
                        "application_deadline": "2026-12-31"
                    },
                    {
                        "type": "salary_subsidy",
                        "amount_usd": 250000,
                        "currency": "USD",
                        "purpose": "Digital talent recruitment",
                        "duration_months": 24,
                        "eligibility_criteria": ["Hiring EU citizens", "Digital skills training"],
                        "application_deadline": "2025-12-31"
                    }
                ],
                "land_incentives": [
                    {
                        "type": "infrastructure_support",
                        "location": "EU Digital Innovation Hubs",
                        "area_sqm": 800,
                        "rental_discount_rate": 0.4,
                        "construction_grant_usd": 400000,
                        "infrastructure_support": ["5G network", "Cloud infrastructure", "AI testbed"],
                        "eligibility_criteria": ["EU Digital Innovation Hub", "Cross-border partnerships"]
                    }
                ]
            },
            "requirements": {
                "staffing_requirements": {
                    "min_employees": 25,
                    "min_researchers": 15,
                    "researcher_percentage": 0.6,
                    "min_phd_count": 5,
                    "phd_percentage": 0.4,
                    "min_experience_years": 3,
                    "senior_management_requirements": ["EU citizenship required", "Experience in digital transformation"]
                },
                "intellectual_property": {
                    "min_patents": 3,
                    "patent_types": ["European Patent", "International Patent"],
                    "min_trademarks": 2,
                    "min_copyrights": 2,
                    "ip_ownership_requirements": ["IP shared across EU", "No export restrictions"]
                },
                "financial_requirements": {
                    "min_investment_usd": 3000000,
                    "min_revenue_usd": 10000000,
                    "net_worth_requirements": ["Net worth > €5M", "Positive EBITDA"],
                    "bank_guarantee_amount": 300000
                },
                "technology_requirements": {
                    "tech_stack_requirements": ["Python", "R", "TensorFlow", "PyTorch", "Kubernetes"],
                    "TRL_requirements": "pilot",
                    "certification_requirements": ["ISO 27001", "GDPR compliance", "Cyber Essentials"],
                    "technology_transfer_requirements": ["Technology transfer to EU partners", "Open source contribution"]
                }
            },
            "compliance": {
                "data_localization": {
                    "required": True,
                    "scope": ["Personal data", "Research data", "Financial data"],
                    "penalties": ["Heavy fines", "Business suspension", "Legal action"]
                },
                "export_controls": {
                    "applies": True,
                    "restricted_technologies": ["Dual-use technologies", "Critical infrastructure"],
                    "licensing_requirements": ["EU export license", "Technology transfer approval"],
                    "penalties": ["Export bans", "Financial penalties", "Criminal liability"]
                },
                "security_clearance": {
                    "required": True,
                    "clearance_levels": ["Basic", "Standard", "Enhanced"],
                    "background_check_requirements": ["EU security clearance", "Criminal record check"]
                },
                "environmental_compliance": {
                    "standards": ["EU Green Deal", "Circular Economy Action Plan"],
                    "certifications_required": ["Environmental Management System", "Carbon Footprint Assessment"],
                    "reporting_requirements": ["Annual sustainability report", "Carbon footprint reporting"]
                },
                "labor_compliance": {
                    "labor_laws": ["EU Labor Law", "Working Time Directive", "Data Protection Directive"],
                    "benefit_requirements": ["Health insurance", "Pension plan", "Paid leave"],
                    "workplace_safety": ["EU OSHA standards", "Workplace safety training"]
                }
            },
            "application_process": {
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Pre-application consultation",
                        "required_documents": ["Concept note", "Team composition", "Initial budget"],
                        "duration_days": 7,
                        "contact_information": {
                            "email": "info@digital-strategy.ec.europa.eu",
                            "phone": "+32-2-123-4567",
                            "address": "Brussels, Belgium"
                        }
                    },
                    {
                        "step_number": 2,
                        "description": "Full application submission",
                        "required_documents": ["Detailed proposal", "Business plan", "Financial projections", "Risk assessment"],
                        "duration_days": 30,
                        "contact_information": {
                            "email": "applications@digital-strategy.ec.europa.eu",
                            "phone": "+32-2-234-5678",
                            "address": "Brussels, Belgium"
                        }
                    },
                    {
                        "step_number": 3,
                        "description": "Expert evaluation",
                        "required_documents": ["Technical evaluation", "Market analysis", "Impact assessment"],
                        "duration_days": 45,
                        "contact_information": {
                            "email": "evaluation@digital-strategy.ec.europa.eu",
                            "phone": "+32-2-345-6789",
                            "address": "Brussels, Belgium"
                        }
                    }
                ],
                "estimated_processing_time": "82 days",
                "appeal_process": ["Complaint to European Ombudsman", "Administrative review", "Judicial appeal"],
                "success_criteria": ["Technical excellence", "Market impact", "EU value alignment", "Cross-border collaboration"]
            },
            "contact_information": {
                "department": "Digital Innovation Unit",
                "contact_person": "Dr. Maria Schmidt",
                "email": "maria.schmidt@ec.europa.eu",
                "phone": "+32-2-500-1234",
                "address": "B-1049 Brussels, Belgium",
                "website": "https://digital-strategy.ec.europa.eu",
                "office_hours": "Monday-Friday 9:00-17:00"
            },
            "tags": ["EU", "Digital Strategy", "Innovation", "Cross-border", "GDPR", "Green Deal"],
            "priority_score": 8,
            "target_industries": ["ai_ml", "cleantech", "fintech", "cybersecurity", "iot"]
        }
        
        policies.extend([shanghai_policy, silicon_valley_policy, eu_policy])
        return policies
    
    def get_policy_by_id(self, policy_id: str) -> Dict[str, Any]:
        """根据ID获取政策"""
        for policy in self.policies:
            if policy["policy_metadata"]["policy_id"] == policy_id:
                return policy
        return None
    
    def get_policies_by_jurisdiction(self, jurisdiction: str) -> List[Dict[str, Any]]:
        """根据地区获取政策"""
        return [policy for policy in self.policies if policy["policy_metadata"]["jurisdiction"] == jurisdiction]
    
    def get_policies_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """根据行业获取政策"""
        return [policy for policy in self.policies if industry in policy.get("target_industries", [])]
    
    def get_all_policies(self) -> List[Dict[str, Any]]:
        """获取所有政策"""
        return self.policies
    
    def save_to_file(self, filepath: str):
        """保存政策数据到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.policies, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, filepath: str):
        """从文件加载政策数据"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                self.policies = json.load(f)