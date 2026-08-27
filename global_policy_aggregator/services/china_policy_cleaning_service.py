"""
China Policy Enhanced Cleaning Service
专门针对中国政府红头文件、管委会官网公告的智能清洗服务
将杂乱无章的中国政府政策精准"洗"成标准化的JSON格式
"""

import json
import logging
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import jsonschema
from pathlib import Path
import sqlite3

from processors.policy_cleaner import PolicyCleaner, StructuredPolicy

# P1-3.3: Canonical taxonomy integration (lazy import)
_canonical_registry = None

def _get_canonical_registry():
    """Lazy-load the canonical taxonomy registry."""
    global _canonical_registry
    if _canonical_registry is None:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from schema.canonical_taxonomy import get_registry
        _canonical_registry = get_registry()
    return _canonical_registry

logger = logging.getLogger(__name__)

@dataclass
class ChinaCleaningJob:
    """中国政策清洗任务"""
    job_id: str
    source_file: str
    region: str  # 中关村、张江、深圳高新区等
    policy_source: str  # 政府红头文件、管委会官网等
    status: str  # pending, processing, completed, failed
    created_at: str
    completed_at: Optional[str]
    policies_processed: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

@dataclass
class ChinaCleaningReport:
    """中国政策清洗报告"""
    total_files: int
    processed_files: int
    total_policies: int
    successful_policies: int
    failed_policies: int
    cleaning_time_seconds: float
    error_summary: Dict[str, int]
    quality_metrics: Dict[str, Any]
    region_coverage: Dict[str, int]

class ChinaPolicyCleaningService:
    """中国政策智能清洗服务"""
    
    def __init__(self, db_service, output_dir: str = "cleaned_china_policies"):
        self.db_service = db_service
        self.cleaner = PolicyCleaner()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jobs = {}
        
        # 中国特色政策映射
        self.china_region_mapping = {
            "北京中关村": "beijing_zhongguancun",
            "上海张江": "shanghai_zhangjiang", 
            "深圳高新区": "shenzhen_hitech",
            "苏州工业园区": "suzhou_industrial",
            "合肥高新区": "hefei_hitech",
            "杭州高新区": "hangzhou_hitech",
            "武汉东湖高新区": "wuhan_donghu",
            "西安高新区": "xian_hitech",
            "成都高新区": "chengdu_hitech",
            "广州开发区": "guangzhou_dev",
            "天津滨海": "tianjin_binhai",
            "重庆两江": "chongqing_liangjiang"
        }
        
        # 中国特色激励类型
        self.china_incentive_types = {
            "具身智能补贴": "embodied_ai_subsidy",
            "自动驾驶补贴": "autonomous_driving_subsidy", 
            "半导体专项补贴": "semiconductor_subsidy",
            "算力补贴": "computing_power_subsidy",
            "厂房租金优惠": "factory_rent_discount",
            "人才奖励": "talent_reward",
            "研发税收抵免": "rd_tax_credit",
            "设备采购补贴": "equipment_purchase_subsidy",
            "市场开拓补贴": "market_development_subsidy",
            "知识产权奖励": "ip_reward"
        }
        
        # 中国特色要求类型
        self.china_requirement_types = {
            "研发人员比例": "rd_staff_ratio",
            "专利数量": "patent_count",
            "高新技术企业": "high_tech_enterprise",
            "专精特新企业": "specialized_enterprise",
            "投资强度": "investment_intensity",
            "产值要求": "output_value_requirement",
            "税收贡献": "tax_contribution",
            "就业岗位": "employment_positions"
        }
        
        # 中国特色合规要求
        self.china_compliance_types = {
            "数据安全": "data_security",
            "网络安全": "cybersecurity",
            "出口管制": "export_control",
            "技术审查": "technology_review",
            "环保要求": "environmental_protection",
            "安全生产": "safety_production",
            "质量标准": "quality_standards",
            "用地要求": "land_use_requirements"
        }
    
    def batch_clean_china_policies(self, source_files: List[str], region_filter: str = None) -> ChinaCleaningReport:
        """批量清洗中国政策文件"""
        import time
        
        start_time = time.time()
        total_files = len(source_files)
        processed_files = 0
        total_policies = 0
        successful_policies = 0
        failed_policies = 0
        error_summary = {}
        region_coverage = {}
        
        logger.info(f"Starting batch cleaning of {total_files} China policy files")
        
        for file_path in source_files:
            try:
                # 确定地区
                region = self._detect_region_from_file(file_path, region_filter)
                
                job_id = f"china_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{Path(file_path).stem}"
                job = ChinaCleaningJob(
                    job_id=job_id,
                    source_file=file_path,
                    region=region,
                    policy_source=self._detect_policy_source(file_path),
                    status="processing",
                    created_at=datetime.now().isoformat(),
                    completed_at=None
                )
                self.jobs[job_id] = job
                
                # 读取文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 中国特色政策清洗
                structured_policy = self._clean_china_policy_text(content, file_path, region)
                
                # 添加到数据库
                policy_id = self.db_service.add_policy(structured_policy)
                
                # 更新统计
                if region not in region_coverage:
                    region_coverage[region] = 0
                region_coverage[region] += 1
                
                # 更新任务状态
                job.status = "completed"
                job.completed_at = datetime.now().isoformat()
                job.policies_processed = 1
                processed_files += 1
                total_policies += 1
                successful_policies += 1
                
                logger.info(f"Successfully cleaned China policy from {file_path}: {policy_id}")
                
            except Exception as e:
                error_type = type(e).__name__
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
                
                # 更新任务状态
                if job_id in self.jobs:
                    self.jobs[job_id].status = "failed"
                    self.jobs[job_id].completed_at = datetime.now().isoformat()
                    self.jobs[job_id].errors.append(str(e))
                
                failed_policies += 1
                logger.error(f"Failed to clean China policy from {file_path}: {e}")
        
        cleaning_time = time.time() - start_time
        
        # 生成清洗报告
        report = ChinaCleaningReport(
            total_files=total_files,
            processed_files=processed_files,
            total_policies=total_policies,
            successful_policies=successful_policies,
            failed_policies=failed_policies,
            cleaning_time_seconds=cleaning_time,
            error_summary=error_summary,
            quality_metrics=self._calculate_china_quality_metrics(),
            region_coverage=region_coverage
        )
        
        # 保存报告
        self._save_china_cleaning_report(report)
        
        logger.info(f"China policy cleaning completed: {successful_policies}/{total_policies} policies successful")
        return report
    
    def _clean_china_policy_text(self, raw_policy_text: str, source_url: str, region: str) -> StructuredPolicy:
        """
        中国特色政策文本清洗
        
        Args:
            raw_policy_text: 原始政策文本
            source_url: 政策来源URL
            region: 地区标识
            
        Returns:
            StructuredPolicy: 结构化政策数据
        """
        logger.info(f"Cleaning China policy text for region: {region}")
        
        # 1. 中国特色基本信息提取
        basic_info = self._extract_china_basic_info(raw_policy_text, region)
        
        # 2. 中国特色激励措施提取
        incentives = self._extract_china_incentives(raw_policy_text, region)
        
        # 3. 中国特色要求提取
        requirements = self._extract_china_requirements(raw_policy_text, region)
        
        # 4. 中国特色合规标准提取
        compliance = self._extract_china_compliance_standards(raw_policy_text, region)
        
        # 5. 构建结构化政策
        policy = StructuredPolicy(
            policy_id=self._generate_china_policy_id(basic_info),
            location=basic_info.get("location", ""),
            country=basic_info.get("country", "CN"),
            region=basic_info.get("region", ""),
            industry=basic_info.get("industry", "other"),
            policy_type=basic_info.get("policy_type", "other"),
            title=basic_info.get("title", ""),
            description=basic_info.get("description", ""),
            incentives=incentives,
            requirements=requirements,
            compliance_standards=compliance,
            metadata=self._build_china_metadata(raw_policy_text, source_url, region)
        )
        
        # 6. 验证数据完整性
        self._validate_china_policy(policy)
        
        logger.info(f"Successfully cleaned China policy: {policy.policy_id}")
        return policy
    
    def _extract_china_basic_info(self, text: str, region: str) -> Dict[str, Any]:
        """提取中国政策基本信息"""
        info = {}
        
        # 提取标题
        title_patterns = [
            r'《([^》]+)》',
            r'([^。\n]{10,80})[实施|办法|规定|通知|意见|方案]',
            r'([^。\n]{10,80})[扶持|促进|支持|发展|建设]'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                info["title"] = match.group(1).strip()
                break
        
        # 地区信息
        info["location"] = self.china_region_mapping.get(region, region)
        info["country"] = "CN"
        info["region"] = region
        
        # 中国特色行业提取
        china_industry_mapping = {
            "人工智能": "ai",
            "机器人": "robotics", 
            "量子计算": "quantum_computing",
            "半导体": "semiconductor",
            "自动驾驶": "autonomous_driving",
            "具身智能": "embodied_ai",
            "生物技术": "biotech",
            "新能源": "new_energy",
            "新材料": "new_materials",
            "高端装备": "high_end_equipment"
        }
        
        for industry_cn, industry_en in china_industry_mapping.items():
            if industry_cn in text:
                info["industry"] = industry_en
                break
        
        # P1-3.3: Resolve canonical industry from legacy value
        legacy_industry = info.get("industry", "other")
        info["canonical_industry"] = _get_canonical_registry().resolve(legacy_industry)
        
        # 政策类型
        china_policy_type_mapping = {
            "专项资金": "grant",
            "财政补贴": "subsidy",
            "税收优惠": "tax_break",
            "土地优惠": "land_grant",
            "人才政策": "talent_policy",
            "产业扶持": "industry_support",
            "科技创新": "innovation_support"
        }
        
        for policy_cn, policy_type in china_policy_type_mapping.items():
            if policy_cn in text:
                info["policy_type"] = policy_type
                break
        
        # 提取描述
        if not info.get("description"):
            # 提取第一段作为描述
            first_paragraph = re.split(r'[。\n]', text)[0]
            if len(first_paragraph) > 20:
                info["description"] = first_paragraph
        
        return info
    
    def _extract_china_incentives(self, text: str, region: str) -> List[Dict[str, Any]]:
        """提取中国特色激励措施"""
        incentives = []
        
        # 具身智能专项补贴
        embodied_ai_patterns = [
            r'具身智能\s*([^\n。]{30,150})',
            r'人形机器人\s*([^\n。]{30,150})',
            r'智能机器人\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(embodied_ai_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                incentive = {
                    "incentive_id": f"embodied_ai_{i+1}",
                    "incentive_type": "embodied_ai_subsidy",
                    "title": "具身智能专项补贴",
                    "description": match.strip(),
                    "amount_details": {
                        "max_amount_cny": self._extract_china_amount(match),
                        "conditions": self._extract_china_conditions(match),
                        "support_duration": self._extract_china_validity_period(text)
                    },
                    "eligibility_criteria": self._extract_china_eligibility(match),
                    "region_specific": True,
                    "target_regions": [region]
                }
                incentives.append(incentive)
        
        # 自动驾驶补贴
        auto_patterns = [
            r'自动驾驶\s*([^\n。]{30,150})',
            r'智能网联\s*([^\n。]{30,150})',
            r'车联网\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(auto_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                incentive = {
                    "incentive_id": f"auto_driving_{i+1}",
                    "incentive_type": "autonomous_driving_subsidy",
                    "title": "自动驾驶专项补贴",
                    "description": match.strip(),
                    "amount_details": {
                        "max_amount_cny": self._extract_china_amount(match),
                        "conditions": self._extract_china_conditions(match),
                        "support_duration": self._extract_china_validity_period(text)
                    },
                    "eligibility_criteria": self._extract_china_eligibility(match),
                    "region_specific": True,
                    "target_regions": [region]
                }
                incentives.append(incentive)
        
        # 半导体专项补贴
        semiconductor_patterns = [
            r'半导体\s*([^\n。]{30,150})',
            r'集成电路\s*([^\n。]{30,150})',
            r'芯片\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(semiconductor_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                incentive = {
                    "incentive_id": f"semiconductor_{i+1}",
                    "incentive_type": "semiconductor_subsidy",
                    "title": "半导体专项补贴",
                    "description": match.strip(),
                    "amount_details": {
                        "max_amount_cny": self._extract_china_amount(match),
                        "conditions": self._extract_china_conditions(match),
                        "support_duration": self._extract_china_validity_period(text)
                    },
                    "eligibility_criteria": self._extract_china_eligibility(match),
                    "region_specific": True,
                    "target_regions": [region]
                }
                incentives.append(incentive)
        
        # 算力补贴
        computing_patterns = [
            r'算力补贴\s*([^\n。]{30,150})',
            r'数据中心\s*([^\n。]{30,150})',
            r'云计算\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(computing_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                incentive = {
                    "incentive_id": f"computing_{i+1}",
                    "incentive_type": "computing_power_subsidy",
                    "title": "算力补贴",
                    "description": match.strip(),
                    "amount_details": {
                        "max_amount_cny": self._extract_china_amount(match),
                        "conditions": self._extract_china_conditions(match),
                        "support_duration": self._extract_china_validity_period(text)
                    },
                    "eligibility_criteria": self._extract_china_eligibility(match),
                    "region_specific": True,
                    "target_regions": [region]
                }
                incentives.append(incentive)
        
        # 厂房租金优惠
        rent_patterns = [
            r'厂房租金\s*([^\n。]{30,150})',
            r'办公场地\s*([^\n。]{30,150})',
            r'场地补贴\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(rent_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                incentive = {
                    "incentive_id": f"rent_{i+1}",
                    "incentive_type": "factory_rent_discount",
                    "title": "厂房租金优惠",
                    "description": match.strip(),
                    "amount_details": {
                        "discount_percentage": self._extract_china_percentage(match),
                        "max_amount_cny": self._extract_china_amount(match),
                        "conditions": self._extract_china_conditions(match)
                    },
                    "eligibility_criteria": self._extract_china_eligibility(match),
                    "region_specific": True,
                    "target_regions": [region]
                }
                incentives.append(incentive)
        
        # 人才奖励
        talent_patterns = [
            r'人才奖励\s*([^\n。]{30,150})',
            r'人才补贴\s*([^\n。]{30,150})',
            r'人才引进\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(talent_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                incentive = {
                    "incentive_id": f"talent_{i+1}",
                    "incentive_type": "talent_reward",
                    "title": "人才奖励",
                    "description": match.strip(),
                    "amount_details": {
                        "max_amount_cny": self._extract_china_amount(match),
                        "conditions": self._extract_china_conditions(match),
                        "target_talent_types": self._extract_talent_types(match)
                    },
                    "eligibility_criteria": self._extract_china_eligibility(match),
                    "region_specific": True,
                    "target_regions": [region]
                }
                incentives.append(incentive)
        
        return incentives
    
    def _extract_china_requirements(self, text: str, region: str) -> List[Dict[str, Any]]:
        """提取中国特色要求"""
        requirements = []
        
        # 研发人员比例要求
        rd_ratio_patterns = [
            r'研发人员\s*([^\n。]{30,150})',
            r'技术人员\s*([^\n。]{30,150})',
            r'博士占比\s*([^\n。]{30,150})',
            r'硕士占比\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(rd_ratio_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                requirement = {
                    "requirement_id": f"rd_ratio_{i+1}",
                    "requirement_type": "rd_staff_ratio",
                    "title": "研发人员比例要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "min_rd_staff_ratio": self._extract_china_percentage(match),
                        "min_phd_ratio": self._extract_china_percentage(match) * 0.3,
                        "min_master_ratio": self._extract_china_percentage(match) * 0.5,
                        "min_total_employees": self._extract_china_number(match)
                    },
                    "region_specific": True,
                    "target_regions": [region]
                }
                requirements.append(requirement)
        
        # 专利数量要求
        patent_patterns = [
            r'专利\s*([^\n。]{30,150})',
            r'发明专利\s*([^\n。]{30,150})',
            r'软件著作权\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(patent_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                requirement = {
                    "requirement_id": f"patent_{i+1}",
                    "requirement_type": "patent_count",
                    "title": "专利数量要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "min_invention_patents": self._extract_china_number(match),
                        "min_utility_patents": self._extract_china_number(match) * 2,
                        "min_software_copyrights": self._extract_china_number(match) * 3,
                        "min_trademarks": self._extract_china_number(match)
                    },
                    "region_specific": True,
                    "target_regions": [region]
                }
                requirements.append(requirement)
        
        # 高新技术企业要求
        high_tech_patterns = [
            r'高新技术企业\s*([^\n。]{30,150})',
            r'专精特新\s*([^\n。]{30,150})',
            r'科技型中小企业\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(high_tech_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                requirement = {
                    "requirement_id": f"high_tech_{i+1}",
                    "requirement_type": "high_tech_enterprise",
                    "title": "高新技术企业要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "must_be_high_tech": True,
                        "rd_ratio_threshold": 0.06,
                        "patent_threshold": 1,
                        "revenue_growth_threshold": 0.1
                    },
                    "region_specific": True,
                    "target_regions": [region]
                }
                requirements.append(requirement)
        
        # 投资强度要求
        investment_patterns = [
            r'投资额\s*([^\n。]{30,150})',
            r'注册资本\s*([^\n。]{30,150})',
            r'固定资产投资\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(investment_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                requirement = {
                    "requirement_id": f"investment_{i+1}",
                    "requirement_type": "investment_intensity",
                    "title": "投资强度要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "min_investment_cny": self._extract_china_amount(match),
                        "min_registered_capital_cny": self._extract_china_amount(match) * 0.3,
                        "investment_per_employee_threshold": self._extract_china_amount(match) / 50
                    },
                    "region_specific": True,
                    "target_regions": [region]
                }
                requirements.append(requirement)
        
        # 产值要求
        output_patterns = [
            r'产值\s*([^\n。]{30,150})',
            r'营业收入\s*([^\n。]{30,150})',
            r'年产值\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(output_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                requirement = {
                    "requirement_id": f"output_{i+1}",
                    "requirement_type": "output_value_requirement",
                    "title": "产值要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "min_annual_output_cny": self._extract_china_amount(match),
                        "growth_rate_threshold": 0.15,
                        "per_employee_output_threshold": self._extract_china_amount(match) / 50
                    },
                    "region_specific": True,
                    "target_regions": [region]
                }
                requirements.append(requirement)
        
        return requirements
    
    def _extract_china_compliance_standards(self, text: str, region: str) -> List[Dict[str, Any]]:
        """提取中国特色合规标准"""
        compliance = []
        
        # 数据安全要求
        data_security_patterns = [
            r'数据安全\s*([^\n。]{30,150})',
            r'数据保护\s*([^\n。]{30,150})',
            r'数据存储\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(data_security_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                standard = {
                    "compliance_id": f"data_security_{i+1}",
                    "compliance_type": "data_security",
                    "title": "数据安全要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "data_classification": "classified",
                        "encryption_required": True,
                        "access_control": "strict",
                        "audit_logging": True,
                        "compliance_standards": ["GB/T 22239", "GB/T 35273"]
                    },
                    "region_specific": True,
                    "target_regions": [region]
                }
                compliance.append(standard)
        
        # 网络安全要求
        cybersecurity_patterns = [
            r'网络安全\s*([^\n。]{30,150})',
            r'信息安全\s*([^\n。]{30,150})',
            r'等级保护\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(cybersecurity_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                standard = {
                    "compliance_id": f"cybersecurity_{i+1}",
                    "compliance_type": "cybersecurity",
                    "title": "网络安全要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "security_level": "二级以上",
                        "penetration_testing": "annual",
                        "vulnerability_assessment": "quarterly",
                        "incident_response_plan": "required",
                        "compliance_standards": ["GB/T 22239", "GB/T 28448"]
                    },
                    "region_specific": True,
                    "target_regions": [region]
                }
                compliance.append(standard)
        
        # 出口管制要求
        export_patterns = [
            r'出口管制\s*([^\n。]{30,150})',
            r'技术出口\s*([^\n。]{30,150})',
            r'技术审查\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(export_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                standard = {
                    "compliance_id": f"export_control_{i+1}",
                    "compliance_type": "export_control",
                    "title": "出口管制要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "controlled_technologies": ["AI", "quantum", "robotics", "semiconductor"],
                        "export_licensing": "required",
                        "technology_classification": "dual_use",
                        "compliance_standards": ["《技术进出口管理条例》"]
                    },
                    "region_specific": True,
                    "target_regions": [region]
                }
                compliance.append(standard)
        
        # 环保要求
        environmental_patterns = [
            r'环保要求\s*([^\n。]{30,150})',
            r'节能减排\s*([^\n。]{30,150})',
            r'绿色生产\s*([^\n。]{30,150})'
        ]
        
        for i, pattern in enumerate(environmental_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                standard = {
                    "compliance_id": f"environmental_{i+1}",
                    "compliance_type": "environmental_protection",
                    "title": "环保要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "emission_standards": "national_level",
                        "energy_efficiency": "high",
                        "waste_management": "comprehensive",
                        "carbon_neutral_target": "2030",
                        "compliance_standards": ["GB 13271", "GB 16297"]
                    },
                    "region_specific": True,
                    "target_regions": [region]
                }
                compliance.append(standard)
        
        return compliance
    
    def _detect_region_from_file(self, file_path: str, region_filter: str = None) -> str:
        """从文件路径检测地区"""
        file_name = Path(file_path).name.lower()
        
        region_mapping = {
            "中关村": "beijing_zhongguancun",
            "张江": "shanghai_zhangjiang",
            "深圳": "shenzhen_hitech",
            "苏州": "suzhou_industrial",
            "合肥": "hefei_hitech",
            "杭州": "hangzhou_hitech",
            "武汉": "wuhan_donghu",
            "西安": "xian_hitech",
            "成都": "chengdu_hitech",
            "广州": "guangzhou_dev",
            "天津": "tianjin_binhai",
            "重庆": "chongqing_liangjiang"
        }
        
        for region_key, region_value in region_mapping.items():
            if region_key in file_name:
                return region_value
        
        # 如果没有匹配，使用默认或过滤器
        if region_filter:
            return region_filter
        
        return "unknown_region"
    
    def _detect_policy_source(self, file_path: str) -> str:
        """检测政策来源类型"""
        file_name = Path(file_path).name.lower()
        
        if "红头文件" in file_name or "政府文件" in file_name:
            return "government_red_document"
        elif "管委会" in file_name or "园区" in file_name:
            return "park_authority"
        elif "通知" in file_name or "公告" in file_name:
            return "official_notice"
        elif "政策" in file_name:
            return "policy_document"
        else:
            return "unknown_source"
    
    def _extract_china_amount(self, text: str) -> Optional[float]:
        """提取中国金额（人民币）"""
        patterns = [
            r'(\d+(?:,\d+)?)万',
            r'(\d+(?:,\d+)?)亿元',
            r'(\d+(?:,\d+)?)元',
            r'(\d+(?:,\d+)?)人民币',
            r'(\d+(?:,\d+)?)CNY'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount = float(match.group(1).replace(',', ''))
                if '万' in text:
                    amount *= 10000
                elif '亿' in text:
                    amount *= 100000000
                return amount
        return None
    
    def _extract_china_percentage(self, text: str) -> Optional[float]:
        """提取中国百分比"""
        patterns = [r'(\d+(?:\.\d+)?)%', r'百分之(\d+(?:\.\d+)?)']
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return None
    
    def _extract_china_number(self, text: str) -> Optional[int]:
        """提取中国数字"""
        patterns = [r'(\d+)人', r'(\d+)个', r'(\d+)项', r'(\d+)年', r'(\d+)家']
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None
    
    def _extract_china_conditions(self, text: str) -> List[str]:
        """提取中国政策条件"""
        conditions = []
        condition_keywords = ['条件', '要求', '标准', '需', '应', '必须', '符合', '满足']
        
        for keyword in condition_keywords:
            if keyword in text:
                condition_match = re.search(f'{keyword}([^。.]{10,50})', text)
                if condition_match:
                    conditions.append(condition_match.group(1).strip())
        
        return conditions
    
    def _extract_china_eligibility(self, text: str) -> List[Dict[str, Any]]:
        """提取中国政策资格条件"""
        eligibility = []
        
        if '高新技术企业' in text:
            eligibility.append({
                "criteria_type": "high_tech_enterprise",
                "description": "高新技术企业"
            })
        
        if '专精特新' in text:
            eligibility.append({
                "criteria_type": "specialized_enterprise",
                "description": "专精特新企业"
            })
        
        if '初创企业' in text:
            eligibility.append({
                "criteria_type": "startup_company",
                "description": "初创企业"
            })
        
        if '外资企业' in text:
            eligibility.append({
                "criteria_type": "foreign_invested",
                "description": "外资企业"
            })
        
        return eligibility
    
    def _extract_china_validity_period(self, text: str) -> Dict[str, Any]:
        """提取中国政策有效期"""
        period = {}
        
        # 中国日期格式
        date_patterns = [
            r'(\d{4})年(\d{1,2})月',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'有效期至(\d{4})年(\d{1,2})月',
            r'实施期限(\d{4})年至(\d{4})年'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if len(matches) >= 2:
                    # 开始和结束日期
                    start_date = matches[0]
                    end_date = matches[1]
                    period["start_date"] = f"{start_date[0]}-{start_date[1]:0>2}-01" if len(start_date) == 2 else f"{start_date[0]}-{start_date[1]:0>2}-{start_date[2]:0>2}"
                    period["end_date"] = f"{end_date[0]}-{end_date[1]:0>2}-31" if len(end_date) == 2 else f"{end_date[0]}-{end_date[1]:0>2}-{end_date[2]:0>2}"
                else:
                    # 单个日期
                    date_match = matches[0]
                    period["start_date"] = f"{date_match[0]}-{date_match[1]:0>2}-01" if len(date_match) == 2 else f"{date_match[0]}-{date_match[1]:0>2}-{date_match[2]:0>2}"
                    period["end_date"] = f"{date_match[0]}-{date_match[1]:0>2}-31"
                break
        
        return period
    
    def _extract_talent_types(self, text: str) -> List[str]:
        """提取人才类型"""
        talent_types = []
        
        if '博士' in text:
            talent_types.append('phd')
        if '硕士' in text:
            talent_types.append('master')
        if '本科' in text:
            talent_types.append('bachelor')
        if '高级职称' in text:
            talent_types.append('senior_title')
        if '中级职称' in text:
            talent_types.append('middle_title')
        if '海外人才' in text:
            talent_types.append('overseas')
        
        return talent_types
    
    def _generate_china_policy_id(self, basic_info: Dict[str, Any]) -> str:
        """生成中国政策ID"""
        location = basic_info.get("location", "unknown")
        industry = basic_info.get("industry", "other")
        policy_type = basic_info.get("policy_type", "other")
        
        # 清理特殊字符
        location_clean = re.sub(r'[^\w\u4e00-\u9fff]', '_', location)
        industry_clean = re.sub(r'[^\w]', '_', industry)
        policy_type_clean = re.sub(r'[^\w]', '_', policy_type)
        
        return f"china_{location_clean}_{industry_clean}_{policy_type_clean}_{datetime.now().strftime('%Y%m%d')}"
    
    def _build_china_metadata(self, raw_text: str, source_url: str, region: str) -> Dict[str, Any]:
        """构建中国政策元数据"""
        return {
            "source_url": source_url,
            "last_updated": datetime.now().isoformat(),
            "confidence_score": self._calculate_china_confidence_score(raw_text),
            "data_quality": "estimated",
            "raw_text_length": len(raw_text),
            "processing_timestamp": datetime.now().timestamp(),
            "china_specific": {
                "region": region,
                "policy_source": self._detect_policy_source(source_url),
                "currency": "CNY",
                "language": "zh-CN",
                "document_type": "china_policy"
            }
        }
    
    def _calculate_china_confidence_score(self, text: str) -> float:
        """计算中国政策置信度分数"""
        score = 0.0
        
        # 基于文本长度
        if len(text) > 2000:
            score += 0.2
        elif len(text) > 1000:
            score += 0.1
        
        # 基于中国特色关键词
        china_keywords = ['税收', '补贴', '优惠', '政策', '要求', '标准', '申请', '条件', '扶持', '促进', '发展', '建设', '实施', '办法']
        for keyword in china_keywords:
            if keyword in text:
                score += 0.05
        
        # 基于地区关键词
        region_keywords = ['中关村', '张江', '高新区', '开发区', '工业园区', '保税区', '经济区']
        for keyword in region_keywords:
            if keyword in text:
                score += 0.1
        
        # 基于数字
        numbers = re.findall(r'\d+', text)
        if len(numbers) > 10:
            score += 0.1
        
        return min(score, 1.0)
    
    def _validate_china_policy(self, policy: StructuredPolicy):
        """验证中国政策数据"""
        try:
            # 验证激励措施
            for incentive in policy.incentives:
                jsonschema.validate(incentive, self.cleaner.incentive_schema)
            
            # 验证要求
            for requirement in policy.requirements:
                jsonschema.validate(requirement, self.cleaner.requirement_schema)
            
            # 验证合规标准
            for standard in policy.compliance_standards:
                jsonschema.validate(standard, self.cleaner.compliance_schema)
                
        except jsonschema.ValidationError as e:
            logger.warning(f"China policy validation warning: {e}")
        except Exception as e:
            logger.error(f"China policy validation error: {e}")
    
    def _calculate_china_quality_metrics(self) -> Dict[str, Any]:
        """计算中国政策质量指标"""
        try:
            with sqlite3.connect(self.db_service.db_path) as conn:
                cursor = conn.cursor()
                
                # 总政策数
                cursor.execute("SELECT COUNT(*) FROM policies WHERE country = 'CN'")
                total_policies = cursor.fetchone()[0]
                
                if total_policies == 0:
                    return {}
                
                # 平均置信度
                cursor.execute("SELECT AVG(confidence_score) FROM policies WHERE country = 'CN'")
                avg_confidence = cursor.fetchone()[0] or 0.0
                
                # 高质量政策比例（置信度>0.8）
                cursor.execute("SELECT COUNT(*) FROM policies WHERE country = 'CN' AND confidence_score > 0.8")
                high_quality_count = cursor.fetchone()[0]
                high_quality_ratio = high_quality_count / total_policies
                
                # 完整政策比例（有激励措施和要求）
                cursor.execute('''
                    SELECT COUNT(*) FROM policies 
                    WHERE country = 'CN' 
                    AND incentives_json IS NOT NULL AND requirements_json IS NOT NULL
                ''')
                complete_count = cursor.fetchone()[0]
                complete_ratio = complete_count / total_policies
                
                # 地区覆盖度
                cursor.execute("SELECT COUNT(DISTINCT location) FROM policies WHERE country = 'CN'")
                region_coverage = cursor.fetchone()[0]
                
                return {
                    "total_china_policies": total_policies,
                    "average_confidence_score": avg_confidence,
                    "high_quality_policy_ratio": high_quality_ratio,
                    "complete_policy_ratio": complete_ratio,
                    "region_coverage_count": region_coverage,
                    "data_quality_grade": self._get_china_quality_grade(avg_confidence, high_quality_ratio, complete_ratio)
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate China quality metrics: {e}")
            return {}
    
    def _get_china_quality_grade(self, confidence: float, high_quality_ratio: float, complete_ratio: float) -> str:
        """获取中国政策质量等级"""
        score = (confidence * 0.4 + high_quality_ratio * 0.3 + complete_ratio * 0.3)
        
        if score >= 0.8:
            return "A"
        elif score >= 0.6:
            return "B"
        elif score >= 0.4:
            return "C"
        else:
            return "D"
    
    def _save_china_cleaning_report(self, report: ChinaCleaningReport):
        """保存中国政策清洗报告"""
        report_file = self.output_dir / f"china_cleaning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report.__dict__, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"China cleaning report saved to {report_file}")

# 使用示例
if __name__ == "__main__":
    # 创建数据库服务
    from .policy_database_service import PolicyDatabaseService
    
    db_service = PolicyDatabaseService()
    china_cleaning_service = ChinaPolicyCleaningService(db_service)
    
    # 示例中国政策文件列表
    sample_files = [
        "data/raw_policies/beijing_zhongguancun_ai_policy_2024.txt",
        "data/raw_policies/shanghai_zhangjiang_semiconductor_policy_2024.txt",
        "data/raw_policies/shenzhen_hitech_autonomous_driving_policy_2024.txt"
    ]
    
    # 批量清洗中国政策
    report = china_cleaning_service.batch_clean_china_policies(sample_files)
    print(f"China cleaning report: {report}")
    
    # 验证数据质量
    validation = china_cleaning_service.validate_policy_data("sample_china_policy_id")
    print(f"Validation result: {validation}")
    
    # 标准化数据
    standardization = china_cleaning_service.standardize_policy_data("sample_china_policy_id")
    print(f"Standardization result: {standardization}")