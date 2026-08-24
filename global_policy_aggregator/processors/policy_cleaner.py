"""
Global Policy Data Cleaner
清洗和结构化全球政府政策数据，将碎片化的政策网页文字转换为符合OpenInvest标准结构化情报
"""

import re
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import jsonschema
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class StructuredPolicy:
    """结构化政策数据"""
    policy_id: str
    location: str
    country: str
    region: str
    industry: str
    policy_type: str
    title: str
    description: str
    incentives: List[Dict[str, Any]]
    requirements: List[Dict[str, Any]]
    compliance_standards: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class PolicyCleaner:
    """政策数据清洗器"""
    
    def __init__(self):
        self.incentive_schema = self._load_schema("incentive_schema.json")
        self.requirement_schema = self._load_schema("requirement_schema.json")
        self.compliance_schema = self._load_schema("compliance_schema.json")
        
        # 行业映射
        self.industry_mapping = {
            "人工智能": "ai",
            "机器人": "robotics",
            "量子计算": "quantum_computing",
            "生物技术": "biotech",
            "自动驾驶": "autonomous_driving",
            "区块链": "blockchain",
            "虚拟现实": "vr_ar",
            "增强现实": "vr_ar",
            "新材料": "other",
            "新能源": "other"
        }
        
        # 政策类型映射
        self.policy_type_mapping = {
            "税收优惠": "tax_break",
            "财政补贴": "subsidy",
            "土地优惠": "land_grant",
            "专项资金": "grant",
            "贷款支持": "loan",
            "担保服务": "guarantee",
            "培训补贴": "training_grant",
            "研发税收抵免": "rtp_credit"
        }
        
        # 国家/地区映射
        self.country_mapping = {
            "中国": "CN",
            "美国": "US",
            "欧盟": "EU",
            "新加坡": "SG",
            "日本": "JP",
            "韩国": "KR",
            "德国": "DE",
            "英国": "GB",
            "法国": "FR",
            "加拿大": "CA"
        }
    
    def _load_schema(self, schema_file: str) -> Dict[str, Any]:
        """加载JSON Schema"""
        try:
            schema_path = Path(__file__).parent.parent / "schemas" / schema_file
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load schema {schema_file}: {e}")
            return {}
    
    def clean_policy_text(self, raw_policy_text: str, source_url: str = None) -> StructuredPolicy:
        """
        将原始政策文本清洗为结构化数据
        
        Args:
            raw_policy_text: 原始政策文本
            source_url: 政策来源URL
            
        Returns:
            StructuredPolicy: 结构化政策数据
        """
        logger.info(f"Cleaning policy text from source: {source_url}")
        
        # 1. 提取基本信息
        basic_info = self._extract_basic_info(raw_policy_text)
        
        # 2. 提取激励措施
        incentives = self._extract_incentives(raw_policy_text)
        
        # 3. 提取落地要求
        requirements = self._extract_requirements(raw_policy_text)
        
        # 4. 提取合规标准
        compliance = self._extract_compliance_standards(raw_policy_text)
        
        # 5. 构建结构化政策
        policy = StructuredPolicy(
            policy_id=self._generate_policy_id(basic_info),
            location=basic_info.get("location", ""),
            country=basic_info.get("country", ""),
            region=basic_info.get("region", ""),
            industry=basic_info.get("industry", "other"),
            policy_type=basic_info.get("policy_type", "other"),
            title=basic_info.get("title", ""),
            description=basic_info.get("description", ""),
            incentives=incentives,
            requirements=requirements,
            compliance_standards=compliance,
            metadata=self._build_metadata(raw_policy_text, source_url)
        )
        
        # 6. 验证数据完整性
        self._validate_policy(policy)
        
        logger.info(f"Successfully cleaned policy: {policy.policy_id}")
        return policy
    
    def _extract_basic_info(self, text: str) -> Dict[str, Any]:
        """提取基本信息"""
        info = {}
        
        # 提取标题
        title_patterns = [
            r'《([^》]+)》',
            r'《([^<]+)》',
            r'([^。\n]{10,50})[政策|办法|规定|通知]',
            r'([^。\n]{10,50})[实施|管理|促进|支持]'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                info["title"] = match.group(1).strip()
                break
        
        # 提取地点
        location_patterns = [
            r'([省市县区]{2,10}[新区|开发区|高新区|保税区|经济区])',
            r'([北上广深杭州成都南京武汉西安]{2,10})',
            r'([^\n]{3,20}市[^\n]{3,20}区)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                location = match.group(1)
                info["location"] = location
                info["country"] = self.country_mapping.get("中国", "CN")
                info["region"] = "中国"
                break
        
        # 提取行业
        for industry_cn, industry_en in self.industry_mapping.items():
            if industry_cn in text:
                info["industry"] = industry_en
                break
        
        # 提取政策类型
        for policy_cn, policy_type in self.policy_type_mapping.items():
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
    
    def _extract_incentives(self, text: str) -> List[Dict[str, Any]]:
        """提取激励措施"""
        incentives = []
        
        # 税收优惠提取
        tax_patterns = [
            r'税收[减免|优惠|返还|补贴]\s*([^\n。]{20,100})',
            r'企业所得税[减免|优惠|返还]\s*([^\n。]{20,100})',
            r'增值税[减免|优惠|返还]\s*([^\n。]{20,100})',
            r'研发费用加计扣除\s*([^\n。]{20,100})'
        ]
        
        for i, pattern in enumerate(tax_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                incentive = {
                    "incentive_id": f"tax_incentive_{i+1}",
                    "incentive_type": "tax_break",
                    "title": "税收优惠",
                    "description": match.strip(),
                    "amount_details": {
                        "rate_percentage": self._extract_percentage(match),
                        "conditions": self._extract_conditions(match)
                    },
                    "eligibility_criteria": self._extract_eligibility(match),
                    "validity_period": self._extract_validity_period(text)
                }
                incentives.append(incentive)
        
        # 财政补贴提取
        subsidy_patterns = [
            r'财政补贴\s*([^\n。]{20,100})',
            r'专项资金\s*([^\n。]{20,100})',
            r'研发资助\s*([^\n。]{20,100})',
            r'创业扶持\s*([^\n。]{20,100})'
        ]
        
        for i, pattern in enumerate(subsidy_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                incentive = {
                    "incentive_id": f"subsidy_{i+1}",
                    "incentive_type": "subsidy",
                    "title": "财政补贴",
                    "description": match.strip(),
                    "amount_details": {
                        "max_amount_usd": self._extract_amount(match),
                        "conditions": self._extract_conditions(match)
                    },
                    "eligibility_criteria": self._extract_eligibility(match),
                    "validity_period": self._extract_validity_period(text)
                }
                incentives.append(incentive)
        
        return incentives
    
    def _extract_requirements(self, text: str) -> List[Dict[str, Any]]:
        """提取落地要求"""
        requirements = []
        
        # 人员要求
        staffing_patterns = [
            r'研发人员\s*([^\n。]{20,100})',
            r'技术人员\s*([^\n。]{20,100})',
            r'员工总数\s*([^\n。]{20,100})',
            r'博士占比\s*([^\n。]{20,100})',
            r'硕士占比\s*([^\n。]{20,100})'
        ]
        
        for i, pattern in enumerate(staffing_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                requirement = {
                    "requirement_id": f"staffing_req_{i+1}",
                    "requirement_type": "staffing",
                    "title": "人员要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "min_employees": self._extract_number(match),
                        "min_researchers": self._extract_number(match) // 2,
                        "phd_percentage": self._extract_percentage(match)
                    }
                }
                requirements.append(requirement)
        
        # 知识产权要求
        ip_patterns = [
            r'专利\s*([^\n。]{20,100})',
            r'商标\s*([^\n。]{20,100})',
            r'著作权\s*([^\n。]{20,100})',
            r'知识产权\s*([^\n。]{20,100})'
        ]
        
        for i, pattern in enumerate(ip_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                requirement = {
                    "requirement_id": f"ip_req_{i+1}",
                    "requirement_type": "intellectual_property",
                    "title": "知识产权要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "min_patents": self._extract_number(match),
                        "min_trademarks": self._extract_number(match) // 2
                    }
                }
                requirements.append(requirement)
        
        # 投资要求
        investment_patterns = [
            r'投资额\s*([^\n。]{20,100})',
            r'注册资本\s*([^\n。]{20,100})',
            r'固定资产投资\s*([^\n。]{20,100})'
        ]
        
        for i, pattern in enumerate(investment_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                requirement = {
                    "requirement_id": f"investment_req_{i+1}",
                    "requirement_type": "financial",
                    "title": "投资要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "min_investment_usd": self._extract_amount(match)
                    }
                }
                requirements.append(requirement)
        
        return requirements
    
    def _extract_compliance_standards(self, text: str) -> List[Dict[str, Any]]:
        """提取合规标准"""
        compliance = []
        
        # 数据本地化要求
        data_localization_patterns = [
            r'数据本地化\s*([^\n。]{20,100})',
            r'数据存储\s*([^\n。]{20,100})',
            r'数据中心\s*([^\n。]{20,100})'
        ]
        
        for i, pattern in enumerate(data_localization_patterns):
            matches = re.findall(pattern, text)
            for match in matches:
                standard = {
                    "compliance_id": f"data_localization_{i+1}",
                    "compliance_type": "data_localization",
                    "title": "数据本地化要求",
                    "description": match.strip(),
                    "mandatory": True,
                    "specific_requirements": {
                        "data_types": ["personal_data", "commercial_data"],
                        "storage_location": "domestic"
                    }
                }
                compliance.append(standard)
        
        # 出口管制要求
        export_patterns = [
            r'出口管制\s*([^\n。]{20,100})',
            r'技术出口\s*([^\n。]{20,100})',
            r'技术审查\s*([^\n。]{20,100})'
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
                        "controlled_technologies": ["AI", "quantum", "robotics"],
                        "export_licensing": True
                    }
                }
                compliance.append(standard)
        
        return compliance
    
    def _extract_percentage(self, text: str) -> Optional[float]:
        """提取百分比"""
        patterns = [r'(\d+(?:\.\d+)?)%', r'百分之(\d+(?:\.\d+)?)']
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """提取金额"""
        patterns = [
            r'(\d+(?:,\d+)?)万',
            r'(\d+(?:,\d+)?)亿元',
            r'(\d+(?:,\d+)?)美元',
            r'(\d+(?:,\d+)?)USD',
            r'\$?(\d+(?:,\d+)?(?:\.\d+)?)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount = float(match.group(1).replace(',', ''))
                # 简单的货币转换
                if '万' in text:
                    amount *= 10000
                elif '亿' in text:
                    amount *= 100000000
                return amount
        return None
    
    def _extract_number(self, text: str) -> Optional[int]:
        """提取数字"""
        patterns = [r'(\d+)人', r'(\d+)个', r'(\d+)项', r'(\d+)年']
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None
    
    def _extract_conditions(self, text: str) -> List[str]:
        """提取条件"""
        conditions = []
        condition_keywords = ['条件', '要求', '标准', '需', '应', '必须']
        
        for keyword in condition_keywords:
            if keyword in text:
                # 提取条件描述
                condition_match = re.search(f'{keyword}([^。.]{10,50})', text)
                if condition_match:
                    conditions.append(condition_match.group(1).strip())
        
        return conditions
    
    def _extract_eligibility(self, text: str) -> List[Dict[str, Any]]:
        """提取资格条件"""
        eligibility = []
        
        # 简单的资格提取
        if '高新技术企业' in text:
            eligibility.append({
                "criteria_type": "industry_focus",
                "description": "高新技术企业"
            })
        
        if '初创企业' in text:
            eligibility.append({
                "criteria_type": "company_size",
                "description": "初创企业"
            })
        
        return eligibility
    
    def _extract_validity_period(self, text: str) -> Dict[str, Any]:
        """提取有效期"""
        period = {}
        
        # 提取日期
        date_patterns = [
            r'(\d{4})年(\d{1,2})月',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{4}/\d{1,2}/\d{1,2})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if len(matches) >= 2:
                    # 提取开始和结束日期
                    start_date = matches[0]
                    end_date = matches[1]
                    period["start_date"] = f"{start_date[0]}-{start_date[1]:0>2}-{start_date[2]:0>2}" if len(start_date) == 3 else f"{start_date[0]}-{start_date[1]:0>2}-01"
                    period["end_date"] = f"{end_date[0]}-{end_date[1]:0>2}-{end_date[2]:0>2}" if len(end_date) == 3 else f"{end_date[0]}-{end_date[1]:0>2}-31"
                else:
                    # 单个日期，设为开始日期
                    date_match = matches[0]
                    period["start_date"] = f"{date_match[0]}-{date_match[1]:0>2}-{date_match[2]:0>2}" if len(date_match) == 3 else f"{date_match[0]}-{date_match[1]:0>2}-01"
                    period["end_date"] = f"{date_match[0]}-{date_match[1]:0>2}-31"
                break
        
        return period
    
    def _generate_policy_id(self, basic_info: Dict[str, Any]) -> str:
        """生成政策ID"""
        location = basic_info.get("location", "unknown")
        industry = basic_info.get("industry", "other")
        policy_type = basic_info.get("policy_type", "other")
        
        # 清理特殊字符
        location_clean = re.sub(r'[^\w\u4e00-\u9fff]', '_', location)
        industry_clean = re.sub(r'[^\w]', '_', industry)
        policy_type_clean = re.sub(r'[^\w]', '_', policy_type)
        
        return f"{location_clean}_{industry_clean}_{policy_type_clean}_{datetime.now().strftime('%Y%m%d')}"
    
    def _build_metadata(self, raw_text: str, source_url: str = None) -> Dict[str, Any]:
        """构建元数据"""
        return {
            "source_url": source_url,
            "last_updated": datetime.now().isoformat(),
            "confidence_score": self._calculate_confidence_score(raw_text),
            "data_quality": "estimated",
            "raw_text_length": len(raw_text),
            "processing_timestamp": datetime.now().timestamp()
        }
    
    def _calculate_confidence_score(self, text: str) -> float:
        """计算置信度分数"""
        score = 0.0
        
        # 基于文本长度
        if len(text) > 1000:
            score += 0.2
        elif len(text) > 500:
            score += 0.1
        
        # 基于关键词
        keywords = ['税收', '补贴', '优惠', '政策', '要求', '标准', '申请', '条件']
        for keyword in keywords:
            if keyword in text:
                score += 0.1
        
        # 基于数字
        numbers = re.findall(r'\d+', text)
        if len(numbers) > 5:
            score += 0.1
        
        return min(score, 1.0)
    
    def _validate_policy(self, policy: StructuredPolicy):
        """验证政策数据"""
        try:
            # 验证激励措施
            for incentive in policy.incentives:
                jsonschema.validate(incentive, self.incentive_schema)
            
            # 验证要求
            for requirement in policy.requirements:
                jsonschema.validate(requirement, self.requirement_schema)
            
            # 验证合规标准
            for standard in policy.compliance_standards:
                jsonschema.validate(standard, self.compliance_schema)
                
        except jsonschema.ValidationError as e:
            logger.warning(f"Policy validation warning: {e}")
        except Exception as e:
            logger.error(f"Policy validation error: {e}")

# 使用示例
if __name__ == "__main__":
    # 示例原始政策文本
    sample_policy_text = """
    《上海市张江科学城人工智能产业扶持政策（2024年）》
    
    为促进人工智能产业发展，特制定本政策。对在张江科学城注册的人工智能企业，给予以下支持：
    
    1. 税收优惠：企业所得税减免50%，最高不超过500万元；增值税即征即退政策。
    2. 财政补贴：研发费用补贴30%，最高1000万元；办公场地租金补贴50%，最高200万元/年。
    3. 人员要求：研发人员不少于20人，博士占比不低于30%。
    4. 知识产权：拥有发明专利不少于5项，软件著作权不少于10项。
    5. 投资要求：固定资产投资不低于2000万元人民币。
    6. 数据本地化：用户数据必须存储在境内服务器。
    7. 出口管制：涉及核心技术的出口需要审批。
    
    本政策自2024年1月1日起实施，有效期至2026年12月31日。
    """
    
    # 创建清洗器实例
    cleaner = PolicyCleaner()
    
    # 清洗政策文本
    structured_policy = cleaner.clean_policy_text(sample_policy_text, "http://example.com/policy")
    
    # 输出结果
    print("=== 结构化政策数据 ===")
    print(json.dumps({
        "policy_id": structured_policy.policy_id,
        "title": structured_policy.title,
        "location": structured_policy.location,
        "incentives_count": len(structured_policy.incentives),
        "requirements_count": len(structured_policy.requirements),
        "compliance_count": len(structured_policy.compliance_standards)
    }, indent=2, ensure_ascii=False))
    
    print("\n=== 激励措施 ===")
    for incentive in structured_policy.incentives:
        print(f"- {incentive['title']}: {incentive['description']}")
    
    print("\n=== 落地要求 ===")
    for requirement in structured_policy.requirements:
        print(f"- {requirement['title']}: {requirement['description']}")
    
    print("\n=== 合规标准 ===")
    for standard in structured_policy.compliance_standards:
        print(f"- {standard['title']}: {standard['description']}")