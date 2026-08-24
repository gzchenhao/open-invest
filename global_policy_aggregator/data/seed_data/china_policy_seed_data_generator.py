"""
China Policy Seed Data Generator
生成中国高新区产业扶持政策Mock数据，确保当全球硬科技项目方打开Web端或调用API时，能够立刻检索到干货满满的中国高新区政策
"""

import json
import random
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid

class ChinaPolicySeedDataGenerator:
    """中国政策种子数据生成器"""
    
    def __init__(self):
        self.seed_data_dir = Path(__file__).parent
        self.generated_policies = []
        
    def generate_comprehensive_seed_data(self) -> List[Dict[str, Any]]:
        """生成全面的中国政策种子数据"""
        print("[INFO] 开始生成中国政策种子数据...")
        
        # 生成各地区的政策数据
        policies = []
        
        # 1. 北京中关村政策
        policies.extend(self._generate_beijing_zhongguancun_policies())
        
        # 2. 上海张江政策
        policies.extend(self._generate_shanghai_zhangjiang_policies())
        
        # 3. 深圳高新区政策
        policies.extend(self._generate_shenzhen_hitech_policies())
        
        # 4. 苏州工业园区政策
        policies.extend(self._generate_suzhou_industrial_policies())
        
        # 5. 合肥高新区政策
        policies.extend(self._generate_hefei_hitech_policies())
        
        # 6. 杭州高新区政策
        policies.extend(self._generate_hangzhou_hitech_policies())
        
        # 7. 武汉东湖高新区政策
        policies.extend(self._generate_wuhan_donghu_policies())
        
        # 8. 西安高新区政策
        policies.extend(self._generate_xian_hitech_policies())
        
        # 9. 成都高新区政策
        policies.extend(self._generate_chengdu_hitech_policies())
        
        # 10. 广州开发区政策
        policies.extend(self._generate_guangzhou_dev_policies())
        
        self.generated_policies = policies
        print(f"[SUCCESS] 成功生成 {len(policies)} 条中国政策种子数据")
        return policies
    
    def _generate_beijing_zhongguancun_policies(self) -> List[Dict[str, Any]]:
        """生成北京中关村政策数据"""
        policies = []
        
        # 政策1：人工智能专项扶持
        policy1 = {
            "policy_id": f"beijing_zhongguancun_ai_{uuid.uuid4().hex[:8]}",
            "location": "beijing_zhongguancun",
            "country": "CN",
            "region": "北京中关村",
            "industry": "ai",
            "policy_type": "grant",
            "title": "中关村科学城人工智能产业专项扶持政策（2024年）",
            "description": "为促进人工智能产业发展，特制定本政策。对在中关村科学城注册的人工智能企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "ai_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "人工智能研发资助",
                    "description": "对人工智能核心技术研发项目给予最高2000万元资助",
                    "amount_details": {
                        "max_amount_cny": 20000000,
                        "conditions": ["核心技术自主可控", "具有产业化前景"],
                        "support_duration": "3年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "industry_focus", "description": "人工智能领域"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于15%"}
                    ]
                },
                {
                    "incentive_id": "ai_talent_reward_1",
                    "incentive_type": "talent_reward",
                    "title": "高端人才奖励",
                    "description": "对引进的AI领域顶尖人才给予最高500万元奖励",
                    "amount_details": {
                        "max_amount_cny": 5000000,
                        "conditions": ["院士、长江学者等", "在中关村工作满3年"],
                        "target_talent_types": ["phd", "senior_title", "overseas"]
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "talent_level", "description": "高端人才"}
                    ]
                },
                {
                    "incentive_id": "ai_office_subsidy_1",
                    "incentive_type": "factory_rent_discount",
                    "title": "办公场地租金补贴",
                    "description": "在中关村租用办公场地给予50%租金补贴，最高300万元/年",
                    "amount_details": {
                        "discount_percentage": 50,
                        "max_amount_cny": 3000000,
                        "conditions": ["租用面积不少于1000平米", "入驻中关村核心区"]
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "company_size", "description": "规模以上企业"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "ai_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于30%，博士占比不低于10%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.3,
                        "min_phd_ratio": 0.1,
                        "min_master_ratio": 0.2,
                        "min_total_employees": 50
                    }
                },
                {
                    "requirement_id": "ai_patent_1",
                    "requirement_type": "patent_count",
                    "title": "知识产权要求",
                    "description": "拥有发明专利不少于10项，软件著作权不少于20项",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_invention_patents": 10,
                        "min_utility_patents": 20,
                        "min_software_copyrights": 20,
                        "min_trademarks": 5
                    }
                },
                {
                    "requirement_id": "ai_investment_1",
                    "requirement_type": "investment_intensity",
                    "title": "投资强度要求",
                    "description": "固定资产投资不低于5000万元人民币",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_investment_cny": 50000000,
                        "min_registered_capital_cny": 10000000,
                        "investment_per_employee_threshold": 1000000
                    }
                },
                {
                    "requirement_id": "ai_output_1",
                    "requirement_type": "output_value_requirement",
                    "title": "产值要求",
                    "description": "年营业收入不低于1亿元人民币",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_annual_output_cny": 100000000,
                        "growth_rate_threshold": 0.2,
                        "per_employee_output_threshold": 2000000
                    }
                }
            ],
            "compliance_standards": [
                {
                    "compliance_id": "ai_data_security_1",
                    "compliance_type": "data_security",
                    "title": "数据安全要求",
                    "description": "人工智能训练数据必须符合国家数据安全标准",
                    "mandatory": True,
                    "specific_requirements": {
                        "data_classification": "classified",
                        "encryption_required": True,
                        "access_control": "strict",
                        "audit_logging": True,
                        "compliance_standards": ["GB/T 22239", "GB/T 35273"]
                    }
                },
                {
                    "compliance_id": "ai_export_control_1",
                    "compliance_type": "export_control",
                    "title": "技术出口管制",
                    "description": "涉及核心AI技术的出口需要经过技术审查",
                    "mandatory": True,
                    "specific_requirements": {
                        "controlled_technologies": ["deep_learning", "computer_vision", "nlp"],
                        "export_licensing": "required",
                        "technology_classification": "dual_use",
                        "compliance_standards": ["《技术进出口管理条例》"]
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.zgc.gov.cn/policy/ai_2024.html",
                "last_updated": "2024-01-15T10:00:00",
                "confidence_score": 0.95,
                "data_quality": "high",
                "raw_text_length": 5000,
                "processing_timestamp": 1642248000,
                "china_specific": {
                    "region": "beijing_zhongguancun",
                    "policy_source": "government_red_document",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        # 政策2：量子计算专项扶持
        policy2 = {
            "policy_id": f"beijing_zhongguancun_quantum_{uuid.uuid4().hex[:8]}",
            "location": "beijing_zhongguancun",
            "country": "CN",
            "region": "北京中关村",
            "industry": "quantum_computing",
            "policy_type": "grant",
            "title": "中关村科学城量子计算产业专项扶持政策（2024年）",
            "description": "为抢占量子计算技术制高点，特制定本政策。对在中关村科学城注册的量子计算企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "quantum_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "量子计算研发资助",
                    "description": "对量子计算核心技术研发项目给予最高3000万元资助",
                    "amount_details": {
                        "max_amount_cny": 30000000,
                        "conditions": ["具有国际领先水平", "产业化前景明确"],
                        "support_duration": "5年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "technology_level", "description": "国际先进水平"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于20%"}
                    ]
                },
                {
                    "incentive_id": "quantum_equipment_1",
                    "incentive_type": "equipment_purchase_subsidy",
                    "title": "设备采购补贴",
                    "description": "量子计算设备采购给予30%补贴，最高1000万元",
                    "amount_details": {
                        "subsidy_rate": 0.3,
                        "max_amount_cny": 10000000,
                        "conditions": ["采购国产设备", "用于研发和生产"]
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "equipment_type", "description": "量子计算设备"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "quantum_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于40%，博士占比不低于20%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.4,
                        "min_phd_ratio": 0.2,
                        "min_master_ratio": 0.3,
                        "min_total_employees": 30
                    }
                },
                {
                    "requirement_id": "quantum_patent_1",
                    "requirement_type": "patent_count",
                    "title": "知识产权要求",
                    "description": "拥有量子计算相关发明专利不少于15项",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_invention_patents": 15,
                        "min_utility_patents": 25,
                        "min_software_copyrights": 30,
                        "min_trademarks": 8
                    }
                }
            ],
            "compliance_standards": [
                {
                    "compliance_id": "quantum_security_1",
                    "compliance_type": "cybersecurity",
                    "title": "量子安全要求",
                    "description": "量子计算系统必须符合国家量子安全标准",
                    "mandatory": True,
                    "specific_requirements": {
                        "security_level": "量子安全等级",
                        "penetration_testing": "annual",
                        "vulnerability_assessment": "quarterly",
                        "compliance_standards": ["GB/T 35273", "GB/T 22239"]
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.zgc.gov.cn/policy/quantum_2024.html",
                "last_updated": "2024-02-01T10:00:00",
                "confidence_score": 0.92,
                "data_quality": "high",
                "raw_text_length": 4500,
                "processing_timestamp": 1643673600,
                "china_specific": {
                    "region": "beijing_zhongguancun",
                    "policy_source": "government_red_document",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        policies.extend([policy1, policy2])
        return policies
    
    def _generate_shanghai_zhangjiang_policies(self) -> List[Dict[str, Any]]:
        """生成上海张江政策数据"""
        policies = []
        
        # 政策1：半导体专项扶持
        policy1 = {
            "policy_id": f"shanghai_zhangjiang_semiconductor_{uuid.uuid4().hex[:8]}",
            "location": "shanghai_zhangjiang",
            "country": "CN",
            "region": "上海张江",
            "industry": "semiconductor",
            "policy_type": "grant",
            "title": "张江科学城集成电路产业专项扶持政策（2024年）",
            "description": "为促进集成电路产业发展，特制定本政策。对在张江科学城注册的集成电路企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "semiconductor_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "集成电路研发资助",
                    "description": "对集成电路设计、制造、封测等环节给予最高5000万元资助",
                    "amount_details": {
                        "max_amount_cny": 50000000,
                        "conditions": ["技术先进性", "产业化前景"],
                        "support_duration": "3年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "industry_focus", "description": "集成电路领域"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于12%"}
                    ]
                },
                {
                    "incentive_id": "semiconductor_equipment_1",
                    "incentive_type": "equipment_purchase_subsidy",
                    "title": "设备采购补贴",
                    "description": "集成电路设备采购给予25%补贴，最高2000万元",
                    "amount_details": {
                        "subsidy_rate": 0.25,
                        "max_amount_cny": 20000000,
                        "conditions": ["采购国产设备", "用于生产"]
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "equipment_type", "description": "集成电路设备"}
                    ]
                },
                {
                    "incentive_id": "semiconductor_factory_1",
                    "incentive_type": "factory_rent_discount",
                    "title": "厂房租金优惠",
                    "description": "在张江租用厂房给予40%租金补贴，最高500万元/年",
                    "amount_details": {
                        "discount_percentage": 40,
                        "max_amount_cny": 5000000,
                        "conditions": ["租用面积不少于5000平米", "用于集成电路生产"]
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "company_size", "description": "规模以上企业"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "semiconductor_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于25%，硕士以上学历占比不低于30%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.25,
                        "min_phd_ratio": 0.1,
                        "min_master_ratio": 0.3,
                        "min_total_employees": 100
                    }
                },
                {
                    "requirement_id": "semiconductor_patent_1",
                    "requirement_type": "patent_count",
                    "title": "知识产权要求",
                    "description": "拥有集成电路相关发明专利不少于20项",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_invention_patents": 20,
                        "min_utility_patents": 30,
                        "min_software_copyrights": 40,
                        "min_trademarks": 10
                    }
                },
                {
                    "requirement_id": "semiconductor_investment_1",
                    "requirement_type": "investment_intensity",
                    "title": "投资强度要求",
                    "description": "固定资产投资不低于1亿元人民币",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_investment_cny": 100000000,
                        "min_registered_capital_cny": 20000000,
                        "investment_per_employee_threshold": 1000000
                    }
                }
            ],
            "compliance_standards": [
                {
                    "compliance_id": "semiconductor_export_1",
                    "compliance_type": "export_control",
                    "title": "技术出口管制",
                    "description": "涉及集成电路技术的出口需要经过技术审查",
                    "mandatory": True,
                    "specific_requirements": {
                        "controlled_technologies": ["chip_design", "semiconductor_manufacturing", "packaging"],
                        "export_licensing": "required",
                        "technology_classification": "dual_use",
                        "compliance_standards": ["《技术进出口管理条例》"]
                    }
                },
                {
                    "compliance_id": "semiconductor_environmental_1",
                    "compliance_type": "environmental_protection",
                    "title": "环保要求",
                    "description": "集成电路生产必须符合国家环保标准",
                    "mandatory": True,
                    "specific_requirements": {
                        "emission_standards": "national_level",
                        "energy_efficiency": "high",
                        "waste_management": "comprehensive",
                        "compliance_standards": ["GB 13271", "GB 16297"]
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.zhangjiang.gov.cn/policy/semiconductor_2024.html",
                "last_updated": "2024-01-20T10:00:00",
                "confidence_score": 0.93,
                "data_quality": "high",
                "raw_text_length": 4800,
                "processing_timestamp": 1642694400,
                "china_specific": {
                    "region": "shanghai_zhangjiang",
                    "policy_source": "park_authority",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        # 政策2：生物医药专项扶持
        policy2 = {
            "policy_id": f"shanghai_zhangjiang_biotech_{uuid.uuid4().hex[:8]}",
            "location": "shanghai_zhangjiang",
            "country": "CN",
            "region": "上海张江",
            "industry": "biotech",
            "policy_type": "grant",
            "title": "张江科学城生物医药产业专项扶持政策（2024年）",
            "description": "为促进生物医药产业发展，特制定本政策。对在张江科学城注册的生物医药企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "biotech_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "生物医药研发资助",
                    "description": "对创新药物研发项目给予最高3000万元资助",
                    "amount_details": {
                        "max_amount_cny": 30000000,
                        "conditions": ["具有临床价值", "产业化前景明确"],
                        "support_duration": "5年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "industry_focus", "description": "生物医药领域"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于15%"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "biotech_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于35%，博士占比不低于15%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.35,
                        "min_phd_ratio": 0.15,
                        "min_master_ratio": 0.25,
                        "min_total_employees": 80
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.zhangjiang.gov.cn/policy/biotech_2024.html",
                "last_updated": "2024-02-10T10:00:00",
                "confidence_score": 0.91,
                "data_quality": "high",
                "raw_text_length": 4200,
                "processing_timestamp": 1644489600,
                "china_specific": {
                    "region": "shanghai_zhangjiang",
                    "policy_source": "park_authority",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        policies.extend([policy1, policy2])
        return policies
    
    def _generate_shenzhen_hitech_policies(self) -> List[Dict[str, Any]]:
        """生成深圳高新区政策数据"""
        policies = []
        
        # 政策1：自动驾驶专项扶持
        policy1 = {
            "policy_id": f"shenzhen_hitech_autonomous_{uuid.uuid4().hex[:8]}",
            "location": "shenzhen_hitech",
            "country": "CN",
            "region": "深圳高新区",
            "industry": "autonomous_driving",
            "policy_type": "grant",
            "title": "深圳高新区智能网联汽车产业专项扶持政策（2024年）",
            "description": "为促进智能网联汽车产业发展，特制定本政策。对在深圳高新区注册的智能网联汽车企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "auto_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "自动驾驶研发资助",
                    "description": "对自动驾驶技术研发项目给予最高2000万元资助",
                    "amount_details": {
                        "max_amount_cny": 20000000,
                        "conditions": ["技术先进性", "产业化前景"],
                        "support_duration": "3年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "industry_focus", "description": "自动驾驶领域"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于15%"}
                    ]
                },
                {
                    "incentive_id": "auto_testing_1",
                    "incentive_type": "equipment_purchase_subsidy",
                    "title": "测试设备补贴",
                    "description": "自动驾驶测试设备采购给予30%补贴，最高800万元",
                    "amount_details": {
                        "subsidy_rate": 0.3,
                        "max_amount_cny": 8000000,
                        "conditions": ["用于测试验证", "符合国家标准"]
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "equipment_type", "description": "自动驾驶测试设备"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "auto_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于30%，硕士以上学历占比不低于25%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.3,
                        "min_phd_ratio": 0.1,
                        "min_master_ratio": 0.25,
                        "min_total_employees": 60
                    }
                },
                {
                    "requirement_id": "auto_patent_1",
                    "requirement_type": "patent_count",
                    "title": "知识产权要求",
                    "description": "拥有自动驾驶相关发明专利不少于15项",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_invention_patents": 15,
                        "min_utility_patents": 25,
                        "min_software_copyrights": 30,
                        "min_trademarks": 8
                    }
                }
            ],
            "compliance_standards": [
                {
                    "compliance_id": "auto_safety_1",
                    "compliance_type": "safety_production",
                    "title": "安全生产要求",
                    "description": "自动驾驶系统必须符合国家安全生产标准",
                    "mandatory": True,
                    "specific_requirements": {
                        "safety_level": "ASIL-D",
                        "testing_required": "mandatory",
                        "compliance_standards": ["GB/T 34590", "ISO 26262"]
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.szpark.net/policy/autonomous_2024.html",
                "last_updated": "2024-01-25T10:00:00",
                "confidence_score": 0.94,
                "data_quality": "high",
                "raw_text_length": 4600,
                "processing_timestamp": 1643164800,
                "china_specific": {
                    "region": "shenzhen_hitech",
                    "policy_source": "park_authority",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        policies.append(policy1)
        return policies
    
    def _generate_suzhou_industrial_policies(self) -> List[Dict[str, Any]]:
        """生成苏州工业园区政策数据"""
        policies = []
        
        # 政策1：纳米技术专项扶持
        policy1 = {
            "policy_id": f"suzhou_industrial_nanotech_{uuid.uuid4().hex[:8]}",
            "location": "suzhou_industrial",
            "country": "CN",
            "region": "苏州工业园区",
            "industry": "new_materials",
            "policy_type": "grant",
            "title": "苏州工业园区纳米技术产业专项扶持政策（2024年）",
            "description": "为促进纳米技术产业发展，特制定本政策。对在苏州工业园区注册的纳米技术企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "nano_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "纳米技术研发资助",
                    "description": "对纳米技术研发项目给予最高1500万元资助",
                    "amount_details": {
                        "max_amount_cny": 15000000,
                        "conditions": ["技术先进性", "产业化前景"],
                        "support_duration": "3年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "industry_focus", "description": "纳米技术领域"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于10%"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "nano_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于20%，硕士以上学历占比不低于15%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.2,
                        "min_phd_ratio": 0.08,
                        "min_master_ratio": 0.15,
                        "min_total_employees": 40
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.sipac.gov.cn/policy/nano_2024.html",
                "last_updated": "2024-02-05T10:00:00",
                "confidence_score": 0.90,
                "data_quality": "high",
                "raw_text_length": 4000,
                "processing_timestamp": 1644028800,
                "china_specific": {
                    "region": "suzhou_industrial",
                    "policy_source": "park_authority",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        policies.append(policy1)
        return policies
    
    def _generate_hefei_hitech_policies(self) -> List[Dict[str, Any]]:
        """生成合肥高新区政策数据"""
        policies = []
        
        # 政策1：量子信息专项扶持
        policy1 = {
            "policy_id": f"hefei_hitech_quantum_info_{uuid.uuid4().hex[:8]}",
            "location": "hefei_hitech",
            "country": "CN",
            "region": "合肥高新区",
            "industry": "quantum_computing",
            "policy_type": "grant",
            "title": "合肥高新区量子信息产业专项扶持政策（2024年）",
            "description": "为促进量子信息产业发展，特制定本政策。对在合肥高新区注册的量子信息企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "quantum_info_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "量子信息研发资助",
                    "description": "对量子信息研发项目给予最高2500万元资助",
                    "amount_details": {
                        "max_amount_cny": 25000000,
                        "conditions": ["技术先进性", "产业化前景"],
                        "support_duration": "4年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "industry_focus", "description": "量子信息领域"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于18%"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "quantum_info_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于35%，博士占比不低于15%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.35,
                        "min_phd_ratio": 0.15,
                        "min_master_ratio": 0.25,
                        "min_total_employees": 50
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.hfht.gov.cn/policy/quantum_info_2024.html",
                "last_updated": "2024-02-15T10:00:00",
                "confidence_score": 0.91,
                "data_quality": "high",
                "raw_text_length": 4300,
                "processing_timestamp": 1644998400,
                "china_specific": {
                    "region": "hefei_hitech",
                    "policy_source": "park_authority",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        policies.append(policy1)
        return policies
    
    def _generate_hangzhou_hitech_policies(self) -> List[Dict[str, Any]]:
        """生成杭州高新区政策数据"""
        policies = []
        
        # 政策1：数字经济专项扶持
        policy1 = {
            "policy_id": f"hangzhou_hitech_digital_{uuid.uuid4().hex[:8]}",
            "location": "hangzhou_hitech",
            "country": "CN",
            "region": "杭州高新区",
            "industry": "blockchain",
            "policy_type": "grant",
            "title": "杭州高新区数字经济产业专项扶持政策（2024年）",
            "description": "为促进数字经济发展，特制定本政策。对在杭州高新区注册的数字经济企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "digital_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "数字经济研发资助",
                    "description": "对数字经济研发项目给予最高1800万元资助",
                    "amount_details": {
                        "max_amount_cny": 18000000,
                        "conditions": ["技术先进性", "产业化前景"],
                        "support_duration": "3年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "industry_focus", "description": "数字经济领域"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于12%"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "digital_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于25%，硕士以上学历占比不低于20%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.25,
                        "min_phd_ratio": 0.1,
                        "min_master_ratio": 0.2,
                        "min_total_employees": 45
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.hhtz.gov.cn/policy/digital_2024.html",
                "last_updated": "2024-02-20T10:00:00",
                "confidence_score": 0.89,
                "data_quality": "high",
                "raw_text_length": 4100,
                "processing_timestamp": 1645401600,
                "china_specific": {
                    "region": "hangzhou_hitech",
                    "policy_source": "park_authority",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        policies.append(policy1)
        return policies
    
    def _generate_wuhan_donghu_policies(self) -> List[Dict[str, Any]]:
        """生成武汉东湖高新区政策数据"""
        policies = []
        
        # 政策1：光电子专项扶持
        policy1 = {
            "policy_id": f"wuhan_donghu_optoelectronics_{uuid.uuid4().hex[:8]}",
            "location": "wuhan_donghu",
            "country": "CN",
            "region": "武汉东湖高新区",
            "industry": "high_end_equipment",
            "policy_type": "grant",
            "title": "武汉东湖高新区光电子产业专项扶持政策（2024年）",
            "description": "为促进光电子产业发展，特制定本政策。对在武汉东湖高新区注册的光电子企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "optoelectronics_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "光电子研发资助",
                    "description": "对光电子研发项目给予最高1600万元资助",
                    "amount_details": {
                        "max_amount_cny": 16000000,
                        "conditions": ["技术先进性", "产业化前景"],
                        "support_duration": "3年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "industry_focus", "description": "光电子领域"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于10%"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "optoelectronics_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于22%，硕士以上学历占比不低于18%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.22,
                        "min_phd_ratio": 0.08,
                        "min_master_ratio": 0.18,
                        "min_total_employees": 38
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.wdht.gov.cn/policy/optoelectronics_2024.html",
                "last_updated": "2024-02-25T10:00:00",
                "confidence_score": 0.88,
                "data_quality": "high",
                "raw_text_length": 3900,
                "processing_timestamp": 1645849600,
                "china_specific": {
                    "region": "wuhan_donghu",
                    "policy_source": "park_authority",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        policies.append(policy1)
        return policies
    
    def _generate_xian_hitech_policies(self) -> List[Dict[str, Any]]:
        """生成西安高新区政策数据"""
        policies = []
        
        # 政策1：航空航天专项扶持
        policy1 = {
            "policy_id": f"xian_hitech_aerospace_{uuid.uuid4().hex[:8]}",
            "location": "xian_hitech",
            "country": "CN",
            "region": "西安高新区",
            "industry": "high_end_equipment",
            "policy_type": "grant",
            "title": "西安高新区航空航天产业专项扶持政策（2024年）",
            "description": "为促进航空航天产业发展，特制定本政策。对在西安高新区注册的航空航天企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "aerospace_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "航空航天研发资助",
                    "description": "对航空航天研发项目给予最高2200万元资助",
                    "amount_details": {
                        "max_amount_cny": 22000000,
                        "conditions": ["技术先进性", "产业化前景"],
                        "support_duration": "4年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "industry_focus", "description": "航空航天领域"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于15%"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "aerospace_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于28%，硕士以上学历占比不低于20%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.28,
                        "min_phd_ratio": 0.12,
                        "min_master_ratio": 0.2,
                        "min_total_employees": 55
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.xahd.gov.cn/policy/aerospace_2024.html",
                "last_updated": "2024-03-01T10:00:00",
                "confidence_score": 0.87,
                "data_quality": "high",
                "raw_text_length": 4200,
                "processing_timestamp": 1646304000,
                "china_specific": {
                    "region": "xian_hitech",
                    "policy_source": "park_authority",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        policies.append(policy1)
        return policies
    
    def _generate_chengdu_hitech_policies(self) -> List[Dict[str, Any]]:
        """生成成都高新区政策数据"""
        policies = []
        
        # 政策1：人工智能专项扶持
        policy1 = {
            "policy_id": f"chengdu_hitech_ai_{uuid.uuid4().hex[:8]}",
            "location": "chengdu_hitech",
            "country": "CN",
            "region": "成都高新区",
            "industry": "ai",
            "policy_type": "grant",
            "title": "成都高新区人工智能产业专项扶持政策（2024年）",
            "description": "为促进人工智能产业发展，特制定本政策。对在成都高新区注册的人工智能企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "chengdu_ai_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "人工智能研发资助",
                    "description": "对人工智能研发项目给予最高1700万元资助",
                    "amount_details": {
                        "max_amount_cny": 17000000,
                        "conditions": ["技术先进性", "产业化前景"],
                        "support_duration": "3年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "industry_focus", "description": "人工智能领域"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于12%"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "chengdu_ai_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于25%，硕士以上学历占比不低于18%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.25,
                        "min_phd_ratio": 0.1,
                        "min_master_ratio": 0.18,
                        "min_total_employees": 42
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.cdht.gov.cn/policy/ai_2024.html",
                "last_updated": "2024-03-05T10:00:00",
                "confidence_score": 0.86,
                "data_quality": "high",
                "raw_text_length": 4000,
                "processing_timestamp": 1646592000,
                "china_specific": {
                    "region": "chengdu_hitech",
                    "policy_source": "park_authority",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        policies.append(policy1)
        return policies
    
    def _generate_guangzhou_dev_policies(self) -> List[Dict[str, Any]]:
        """生成广州开发区政策数据"""
        policies = []
        
        # 政策1：生物医药专项扶持
        policy1 = {
            "policy_id": f"guangzhou_dev_biotech_{uuid.uuid4().hex[:8]}",
            "location": "guangzhou_dev",
            "country": "CN",
            "region": "广州开发区",
            "industry": "biotech",
            "policy_type": "grant",
            "title": "广州开发区生物医药产业专项扶持政策（2024年）",
            "description": "为促进生物医药产业发展，特制定本政策。对在广州开发区注册的生物医药企业，给予全方位支持。",
            "incentives": [
                {
                    "incentive_id": "guangzhou_biotech_rd_grant_1",
                    "incentive_type": "grant",
                    "title": "生物医药研发资助",
                    "description": "对生物医药研发项目给予最高1900万元资助",
                    "amount_details": {
                        "max_amount_cny": 19000000,
                        "conditions": ["技术先进性", "产业化前景"],
                        "support_duration": "3年"
                    },
                    "eligibility_criteria": [
                        {"criteria_type": "industry_focus", "description": "生物医药领域"},
                        {"criteria_type": "rd_intensity", "description": "研发投入占比不低于14%"}
                    ]
                }
            ],
            "requirements": [
                {
                    "requirement_id": "guangzhou_biotech_rd_ratio_1",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": "研发人员占比不低于30%，硕士以上学历占比不低于22%",
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": 0.3,
                        "min_phd_ratio": 0.12,
                        "min_master_ratio": 0.22,
                        "min_total_employees": 48
                    }
                }
            ],
            "metadata": {
                "source_url": "http://www.gz.gov.cn/policy/biotech_2024.html",
                "last_updated": "2024-03-10T10:00:00",
                "confidence_score": 0.85,
                "data_quality": "high",
                "raw_text_length": 4100,
                "processing_timestamp": 1646880000,
                "china_specific": {
                    "region": "guangzhou_dev",
                    "policy_source": "park_authority",
                    "currency": "CNY",
                    "language": "zh-CN",
                    "document_type": "china_policy"
                }
            }
        }
        
        policies.append(policy1)
        return policies
    
    def save_seed_data_to_files(self, policies: List[Dict[str, Any]]):
        """保存种子数据到文件"""
        print("[INFO] 开始保存种子数据到文件...")
        
        # 保存为JSON文件
        seed_data_file = self.seed_data_dir / "china_policy_seed_data.json"
        with open(seed_data_file, 'w', encoding='utf-8') as f:
            json.dump(policies, f, indent=2, ensure_ascii=False)
        
        # 保存为SQL插入语句
        sql_file = self.seed_data_dir / "china_policy_seed_data.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write("-- 中国政策种子数据SQL插入语句\n")
            f.write("-- 生成时间: " + datetime.now().isoformat() + "\n\n")
            
            for policy in policies:
                f.write(f"-- 政策: {policy['title']}\n")
                f.write(f"INSERT INTO policies VALUES (\n")
                f.write(f"    '{policy['policy_id']}',\n")
                f.write(f"    '{policy['location']}',\n")
                f.write(f"    '{policy['country']}',\n")
                f.write(f"    '{policy['region']}',\n")
                f.write(f"    '{policy['industry']}',\n")
                f.write(f"    '{policy['policy_type']}',\n")
                f.write(f"    '{policy['title']}',\n")
                f.write(f"    '{policy['description']}',\n")
                f.write(f"    '{json.dumps(policy.get('incentives', []), ensure_ascii=False)}',\n")
                f.write(f"    '{json.dumps(policy.get('requirements', []), ensure_ascii=False)}',\n")
                f.write(f"    '{json.dumps(policy.get('compliance_standards', []), ensure_ascii=False)}',\n")
                f.write(f"    '{json.dumps(policy.get('metadata', {}), ensure_ascii=False)}',\n")
                f.write(f"    {policy['metadata'].get('confidence_score', 0.5)},\n")
                f.write(f"    CURRENT_TIMESTAMP,\n")
                f.write(f"    CURRENT_TIMESTAMP\n")
                f.write(");\n\n")
        
        print(f"[SUCCESS] 种子数据已保存到:")
        print(f"   - JSON文件: {seed_data_file}")
        print(f"   - SQL文件: {sql_file}")
        
        return seed_data_file, sql_file
    
    def populate_database(self, policies: List[Dict[str, Any]], db_service):
        """将种子数据填充到数据库"""
        print("[INFO] 开始填充数据库...")
        
        try:
            for policy in policies:
                # 检查是否已存在
                existing = db_service.get_policy(policy['policy_id'])
                if not existing:
                    # 添加新政策
                    db_service.add_policy(policy)
                    print(f"[SUCCESS] 已添加政策: {policy['title']}")
                else:
                    print(f"[INFO] 政策已存在: {policy['title']}")
            
            print(f"[SUCCESS] 成功填充 {len(policies)} 条中国政策数据到数据库")
            return True
            
        except Exception as e:
            print(f"❌ 数据库填充失败: {e}")
            return False

def main():
    """主函数"""
    print("[INFO] 中国政策种子数据生成器启动...")
    
    # 创建生成器
    generator = ChinaPolicySeedDataGenerator()
    
    # 生成种子数据
    policies = generator.generate_comprehensive_seed_data()
    
    # 保存到文件
    seed_data_file, sql_file = generator.save_seed_data_to_files(policies)
    
    # 填充数据库
    try:
        from services.policy_database_service import PolicyDatabaseService
        db_service = PolicyDatabaseService()
        generator.populate_database(policies, db_service)
    except Exception as e:
        print(f"[WARNING] 数据库服务不可用，但数据已保存到文件: {e}")
    
    print("[SUCCESS] 中国政策种子数据生成完成!")
    
    # 输出统计信息
    print("\n[INFO] 统计信息:")
    print(f"   - 总政策数: {len(policies)}")
    print(f"   - 覆盖地区: {len(set(p['region'] for p in policies))}")
    print(f"   - 涵盖行业: {len(set(p['industry'] for p in policies))}")
    print(f"   - 平均置信度: {sum(p['metadata']['confidence_score'] for p in policies) / len(policies):.2f}")
    
    return policies

if __name__ == "__main__":
    main()