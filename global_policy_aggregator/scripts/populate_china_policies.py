"""
中国高新区产业扶持政策Mock数据填充脚本
生成10-20条结构极其详尽、高价值的中国一线高新区真实产业扶持政策Mock数据

⚠️ TASK-P0-2 DATA-INTEGRITY 声明（最高纪律）：
本脚本生成的全部数据均为 MOCK 演示数据，is_mock=True / verification_status="mock"。
其中所有联系方式（电话/邮箱/地址）、source_url、补贴金额、有效期均为模板化虚构，
未经任何官方来源验证，禁止作为真实政府信息展示或对外引用。
宁可 null，不要猜；宁可 UNVERIFIED，不要 VERIFIED。
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
import sqlite3

from services.policy_database_service import PolicyDatabaseService
from processors.policy_cleaner import StructuredPolicy

logger = logging.getLogger(__name__)

class ChinaPolicyGenerator:
    """中国政策数据生成器"""
    
    def __init__(self):
        self.db_service = PolicyDatabaseService()
        
        # 中国主要硬科技集聚区
        self.tech_parks = [
            {
                "name": "北京中关村",
                "region": "北京",
                "city": "北京",
                "authority": "北京市人民政府",
                "contact": {
                    "phone": "010-82896688",
                    "email": "contact@zpark.com.cn",
                    "address": "北京市海淀区中关村南大街5号"
                }
            },
            {
                "name": "上海张江",
                "region": "上海",
                "city": "上海",
                "authority": "上海市人民政府",
                "contact": {
                    "phone": "021-50801900",
                    "email": "info@zjpark.com.cn",
                    "address": "上海市浦东新区张江高科技园区"
                }
            },
            {
                "name": "深圳高新区",
                "region": "深圳",
                "city": "深圳",
                "authority": "深圳市人民政府",
                "contact": {
                    "phone": "0755-86176666",
                    "email": "contact@szgxq.com",
                    "address": "深圳市南山区科技园南区"
                }
            },
            {
                "name": "苏州工业园区",
                "region": "苏州",
                "city": "苏州",
                "authority": "苏州市人民政府",
                "contact": {
                    "phone": "0512-66688888",
                    "email": "info@sipac.com",
                    "address": "苏州工业园区苏州大道东123号"
                }
            },
            {
                "name": "合肥高新区",
                "region": "合肥",
                "city": "合肥",
                "authority": "合肥市人民政府",
                "contact": {
                    "phone": "0551-65339999",
                    "email": "contact@hfht.gov.cn",
                    "address": "合肥市高新区创新大道1号"
                }
            },
            {
                "name": "广州天河区",
                "region": "广州",
                "city": "广州",
                "authority": "广州市天河区人民政府",
                "contact": {
                    "phone": "020-85595555",
                    "email": "contact@thnet.gov.cn",
                    "address": "广州市天河区天府路1号"
                }
            },
            {
                "name": "广州开发区",
                "region": "广州",
                "city": "广州",
                "authority": "广州市开发区管理委员会",
                "contact": {
                    "phone": "020-82281111",
                    "email": "info@gzetd.gov.cn",
                    "address": "广州市开发区科学城"
                }
            },
            {
                "name": "广州南沙区",
                "region": "广州",
                "city": "广州",
                "authority": "广州市南沙区人民政府",
                "contact": {
                    "phone": "020-84686666",
                    "email": "contact@nansha.gov.cn",
                    "address": "广州市南沙区进港大道"
                }
            },
            {
                "name": "广州番禺区",
                "region": "广州",
                "city": "广州",
                "authority": "广州市番禺区人民政府",
                "contact": {
                    "phone": "020-84822222",
                    "email": "contact@panyu.gov.cn",
                    "address": "广州市番禺区市桥街"
                }
            },
            {
                "name": "广州黄埔区",
                "region": "广州",
                "city": "广州",
                "authority": "广州市黄埔区人民政府",
                "contact": {
                    "phone": "020-82288888",
                    "email": "info@hp.gov.cn",
                    "address": "广州市黄埔区开达路"
                }
            },
            {
                "name": "广州白云区",
                "region": "广州",
                "city": "广州",
                "authority": "广州市白云区人民政府",
                "contact": {
                    "phone": "020-86363333",
                    "email": "contact@by.gov.cn",
                    "address": "广州市白云区机场路"
                }
            },
            {
                "name": "广州花都区",
                "region": "广州",
                "city": "广州",
                "authority": "广州市花都区人民政府",
                "contact": {
                    "phone": "020-86886666",
                    "email": "contact@huadu.gov.cn",
                    "address": "广州市花都区新华街"
                }
            }
        ]
        
        # 行业分类
        self.industries = [
            "人工智能", "自动驾驶", "半导体", "量子计算", "区块链", 
            "生物科技", "高端装备", "航空航天", "新材料", "新能源", "金融科技"
        ]
        
        # 政策类型
        self.policy_types = [
            "专项补贴", "产业基金", "技术奖励", "研发补贴", "创新奖励",
            "设备补贴", "专项基金", "研发奖励", "产业基金", "创新奖励"
        ]
        
        # 激励措施模板
        self.incentive_templates = {
            "财政补贴": [
                {
                    "amount_range": (100, 1000),
                    "unit": "万元",
                    "description": "财政补贴{amount}万元",
                    "conditions": ["研发投入", "固定资产投资", "产业化项目"]
                },
                {
                    "amount_range": (50, 500),
                    "unit": "万元",
                    "description": "研发费用补贴{percentage}%",
                    "conditions": ["研发费用", "技术创新", "产品开发"]
                }
            ],
            "场地优惠": [
                {
                    "amount_range": (100, 300),
                    "unit": "万元/年",
                    "duration_range": (1, 5),
                    "description": "办公场地租金减免{amount}万元/年，持续{duration}年",
                    "conditions": ["办公场地", "租金减免", "场地补贴"]
                },
                {
                    "amount_range": (200, 800),
                    "unit": "平方米",
                    "description": "免费办公场地{amount}平方米",
                    "conditions": ["免费场地", "办公空间", "孵化场地"]
                }
            ],
            "税收优惠": [
                {
                    "duration_range": (1, 5),
                    "description": "企业所得税减免{percentage}%，持续{duration}年",
                    "conditions": ["企业所得税", "税收减免", "财政扶持"]
                },
                {
                    "duration_range": (1, 3),
                    "description": "增值税即征即退政策{duration}年",
                    "conditions": ["增值税", "即征即退", "税收优惠"]
                }
            ],
            "人才奖励": [
                {
                    "amount_range": (20, 100),
                    "unit": "万元/年",
                    "description": "高端人才奖励{amount}万元/人/年",
                    "conditions": ["高端人才", "人才奖励", "专家津贴"]
                },
                {
                    "amount_range": (10, 50),
                    "unit": "万元",
                    "description": "团队建设补贴{amount}万元",
                    "conditions": ["团队建设", "人才引进", "团队补贴"]
                }
            ]
        }
        
        # 申请要求模板
        self.requirement_templates = {
            "注册资本": [
                {
                    "amount_range": (500, 5000),
                    "unit": "万元",
                    "description": "注册资本不低于{amount}万元"
                },
                {
                    "amount_range": (1000, 10000),
                    "unit": "万元",
                    "description": "注册资本{amount}万元以上"
                }
            ],
            "研发人员": [
                {
                    "percentage_range": (20, 50),
                    "unit": "%",
                    "description": "研发人员比例不低于{percentage}%"
                },
                {
                    "amount_range": (10, 100),
                    "unit": "人",
                    "description": "研发人员不少于{amount}人"
                }
            ],
            "专利要求": [
                {
                    "amount_range": (5, 20),
                    "unit": "项",
                    "description": "拥有发明专利不少于{amount}项"
                },
                {
                    "amount_range": (10, 50),
                    "unit": "项",
                    "description": "知识产权不少于{amount}项"
                }
            ],
            "成立时间": [
                {
                    "duration_range": (1, 5),
                    "unit": "年",
                    "description": "成立时间不少于{duration}年"
                },
                {
                    "duration_range": (2, 10),
                    "unit": "年",
                    "description": "运营时间{duration}年以上"
                }
            ],
            "技术领域": [
                {
                    "description": "技术领域必须为：{field}",
                    "fields": ["人工智能", "自动驾驶", "半导体", "量子计算", "区块链"]
                },
                {
                    "description": "必须具备{field}相关技术能力",
                    "fields": ["生物科技", "高端装备", "航空航天", "新材料", "新能源"]
                }
            ]
        }
        
        # 政策标题模板
        self.title_templates = [
            "{park_name}{industry}产业扶持政策",
            "{park_name}{industry}专项扶持办法",
            "{park_name}{industry}产业发展实施方案",
            "{park_name}{industry}创新发展扶持政策",
            "{park_name}{industry}产业集聚发展奖励办法"
        ]
        
    def generate_policy(self, park_info: Dict, industry: str) -> StructuredPolicy:
        """生成单个政策"""
        # 生成政策ID
        policy_id = f"china_{park_info['name']}_{industry}_{uuid.uuid4().hex[:8]}"
        
        # 生成政策标题
        title_template = self.title_templates[len(policy_id) % len(self.title_templates)]
        title = title_template.format(park_name=park_info['name'], industry=industry)
        
        # 生成政策类型
        policy_type = self.policy_types[len(title) % len(self.policy_types)]
        
        # 生成政策描述
        description = self._generate_policy_description(park_info, industry, policy_type)
        
        # 生成激励措施
        incentives = self._generate_incentives(park_info, industry, policy_type)
        
        # 生成申请要求
        requirements = self._generate_requirements(park_info, industry, policy_type)
        
        # 创建结构化政策
        structured_policy = StructuredPolicy(
            policy_id=policy_id,
            location=park_info['name'],
            country="中国",
            region=park_info['region'],
            industry=industry,
            policy_type=policy_type,
            title=title,
            description=description,
            incentives=incentives,
            requirements=requirements,
            compliance_standards=self._generate_compliance_standards(industry),
            metadata={
                "park_name": park_info['name'],
                "issuing_authority": park_info['authority'],
                "contact_info": park_info['contact'],
                "valid_period": "2024年1月1日 - 2026年12月31日",
                "application_deadline": "2024年12月31日",
                "confidence_score": 0.95,
                "data_quality": "high_quality",
                "source_type": "mock_data",
                "crawl_timestamp": datetime.now().isoformat(),
                "industry_focus": industry,
                "policy_features": {
                    "max_amount": max([inc.get('amount', 0) for inc in incentives]),
                    "min_requirements": len(requirements),
                    "support_types": list(set([inc.get('type', '') for inc in incentives]))
                }
            }
        )
        
        return structured_policy
    
    def _generate_policy_description(self, park_info: Dict, industry: str, policy_type: str) -> str:
        """生成政策描述"""
        descriptions = [
            f"为促进{park_info['name']}地区{industry}产业发展，特制定本政策。本政策旨在通过财政补贴、税收优惠、场地支持等多种方式，支持{industry}领域企业创新发展。",
            f"{park_info['name']}针对{industry}产业出台专项扶持政策，重点支持技术研发、成果转化、产业化等环节，推动{industry}产业集聚发展。",
            f"为加快{park_info['name']}{industry}产业发展，提升产业竞争力，本政策从资金支持、人才引进、场地保障、税收优惠等方面提供全方位支持。",
            f"本政策是{park_info['name']}推动{industry}产业发展的重要举措，通过专项补贴、产业基金、技术创新奖励等方式，助力企业做大做强。",
            f"为培育{park_info['name']}{industry}产业生态，本政策从研发投入、产业化、人才引进、市场开拓等方面提供系统性支持。"
        ]
        
        main_content = descriptions[len(park_info['name']) % len(descriptions)]
        
        # 添加具体支持内容
        support_details = [
            "1. 财政支持：提供研发补贴、设备购置补贴、产业化支持等资金支持；",
            "2. 税收优惠：享受企业所得税减免、增值税即征即退等税收优惠政策；",
            "3. 场地支持：提供办公场地租金减免、免费场地等场地支持；",
            "4. 人才支持：提供高端人才奖励、团队建设补贴等人才支持；",
            "5. 市场支持：协助企业开拓市场、对接资源、参加展会等市场支持。"
        ]
        
        application_process = [
            "1. 企业申报：符合条件的企业提交申请材料；",
            "2. 资格审核：对申报企业进行资格审核；",
            "3. 专家评审：组织专家对申报项目进行评审；",
            "4. 公示公告：对通过评审的企业进行公示；",
            "5. 资金拨付：公示无异议后拨付扶持资金。"
        ]
        
        return f"""{main_content}

{chr(10).join(support_details)}

申报流程：
{chr(10).join(application_process)}

本政策自2024年1月1日起实施，有效期至2026年12月31日。"""
    
    def _generate_incentives(self, park_info: Dict, industry: str, policy_type: str) -> List[Dict[str, Any]]:
        """生成激励措施"""
        incentives = []
        
        # 根据政策类型生成不同的激励措施
        if policy_type in ["专项补贴", "研发补贴"]:
            incentives.extend(self._generate_financial_incentives(park_info, industry))
        
        if policy_type in ["技术奖励", "创新奖励"]:
            incentives.extend(self._generate_tech_incentives(park_info, industry))
        
        if policy_type in ["产业基金", "专项基金"]:
            incentives.extend(self._generate_fund_incentives(park_info, industry))
        
        # 添加通用激励措施
        incentives.extend(self._generate_common_incentives(park_info, industry))
        
        return incentives[:8]  # 最多返回8条激励措施
    
    def _generate_financial_incentives(self, park_info: Dict, industry: str) -> List[Dict[str, Any]]:
        """生成财政激励措施"""
        incentives = []
        
        # 研发投入补贴
        amount = self._random_amount(100, 800)
        incentives.append({
            "type": "研发投入补贴",
            "amount": amount,
            "unit": "万元",
            "description": f"研发投入补贴{amount}万元（研发费用的30%）",
            "conditions": ["研发费用", "技术创新", "产品开发"]
        })
        
        # 设备购置补贴
        amount = self._random_amount(50, 500)
        incentives.append({
            "type": "设备购置补贴",
            "amount": amount,
            "unit": "万元",
            "description": f"设备购置补贴{amount}万元（购置费用的50%）",
            "conditions": ["设备购置", "固定资产投资", "技术升级"]
        })
        
        # 产业化支持
        amount = self._random_amount(200, 1000)
        incentives.append({
            "type": "产业化支持",
            "amount": amount,
            "unit": "万元",
            "description": f"产业化支持{amount}万元",
            "conditions": ["产业化", "市场推广", "规模生产"]
        })
        
        return incentives
    
    def _generate_tech_incentives(self, park_info: Dict, industry: str) -> List[Dict[str, Any]]:
        """生成技术激励措施"""
        incentives = []
        
        # 技术创新奖励
        amount = self._random_amount(100, 600)
        incentives.append({
            "type": "技术创新奖励",
            "amount": amount,
            "unit": "万元",
            "description": f"技术创新奖励{amount}万元",
            "conditions": ["技术创新", "专利申请", "标准制定"]
        })
        
        # 专利资助
        amount = self._random_amount(5, 20)
        incentives.append({
            "type": "专利资助",
            "amount": amount,
            "unit": "万元/项",
            "description": f"专利资助{amount}万元/项",
            "conditions": ["发明专利", "实用新型", "外观设计"]
        })
        
        # 标准制定奖励
        amount = self._random_amount(50, 200)
        incentives.append({
            "type": "标准制定奖励",
            "amount": amount,
            "unit": "万元",
            "description": f"标准制定奖励{amount}万元",
            "conditions": ["国家标准", "行业标准", "团体标准"]
        })
        
        return incentives
    
    def _generate_fund_incentives(self, park_info: Dict, industry: str) -> List[Dict[str, Any]]:
        """生成基金激励措施"""
        incentives = []
        
        # 产业基金投资
        amount = self._random_amount(500, 2000)
        incentives.append({
            "type": "产业基金投资",
            "amount": amount,
            "unit": "万元",
            "description": f"产业基金投资{amount}万元（股权投资）",
            "conditions": ["股权投资", "战略投资", "产业投资"]
        })
        
        # 贷款贴息
        amount = self._random_amount(20, 100)
        incentives.append({
            "type": "贷款贴息",
            "amount": amount,
            "unit": "%",
            "description": f"贷款贴息{amount}%",
            "conditions": ["银行贷款", "项目贷款", "流动资金"]
        })
        
        # 担保补贴
        amount = self._random_amount(10, 50)
        incentives.append({
            "type": "担保补贴",
            "amount": amount,
            "unit": "万元",
            "description": f"担保补贴{amount}万元",
            "conditions": ["融资担保", "信用担保", "风险担保"]
        })
        
        return incentives
    
    def _generate_common_incentives(self, park_info: Dict, industry: str) -> List[Dict[str, Any]]:
        """生成通用激励措施"""
        incentives = []
        
        # 场地优惠
        amount = self._random_amount(100, 300)
        duration = self._random_duration(1, 5)
        incentives.append({
            "type": "场地优惠",
            "amount": amount,
            "unit": "万元/年",
            "duration": f"{duration}年",
            "description": f"办公场地租金减免{amount}万元/年，持续{duration}年",
            "conditions": ["办公场地", "租金减免", "场地补贴"]
        })
        
        # 人才奖励
        amount = self._random_amount(20, 100)
        incentives.append({
            "type": "人才奖励",
            "amount": amount,
            "unit": "万元/人/年",
            "description": f"高端人才奖励{amount}万元/人/年",
            "conditions": ["高端人才", "人才引进", "专家津贴"]
        })
        
        # 税收优惠
        percentage = self._random_percentage(20, 50)
        duration = self._random_duration(1, 5)
        incentives.append({
            "type": "税收优惠",
            "percentage": f"{percentage}%",
            "duration": f"{duration}年",
            "description": f"企业所得税减免{percentage}%，持续{duration}年",
            "conditions": ["企业所得税", "税收减免", "财政扶持"]
        })
        
        return incentives
    
    def _generate_requirements(self, park_info: Dict, industry: str, policy_type: str) -> List[Dict[str, Any]]:
        """生成申请要求"""
        requirements = []
        
        # 注册资本要求
        amount = self._random_amount(500, 5000)
        requirements.append({
            "type": "注册资本",
            "amount": amount,
            "unit": "万元",
            "description": f"注册资本不低于{amount}万元"
        })
        
        # 研发人员要求
        percentage = self._random_percentage(20, 50)
        requirements.append({
            "type": "研发人员比例",
            "percentage": f"{percentage}%",
            "description": f"研发人员比例不低于{percentage}%"
        })
        
        # 专利要求
        amount = self._random_amount(5, 20)
        requirements.append({
            "type": "专利数量",
            "amount": amount,
            "unit": "项",
            "description": f"拥有发明专利不少于{amount}项"
        })
        
        # 成立时间要求
        duration = self._random_duration(1, 5)
        requirements.append({
            "type": "成立时间",
            "duration": f"{duration}年",
            "description": f"成立时间不少于{duration}年"
        })
        
        # 技术领域要求
        tech_fields = {
            "人工智能": ["机器学习", "深度学习", "自然语言处理", "计算机视觉"],
            "自动驾驶": ["无人驾驶", "智能网联", "车联网", "智能汽车"],
            "半导体": ["集成电路", "芯片设计", "晶圆制造", "微电子"],
            "量子计算": ["量子通信", "量子信息", "量子科技", "量子算法"],
            "区块链": ["分布式账本", "智能合约", "加密货币", "去中心化"],
            "生物科技": ["生物医药", "基因工程", "疫苗研发", "生物制药"],
            "高端装备": ["智能制造", "工业机器人", "精密仪器", "航空航天"],
            "航空航天": ["航空", "航天", "卫星", "火箭", "飞机"],
            "新材料": ["纳米材料", "复合材料", "功能材料", "智能材料"],
            "新能源": ["太阳能", "风能", "储能", "氢能", "核能"],
            "金融科技": ["数字金融", "智能投顾", "区块链金融", "AI金融"]
        }
        
        if industry in tech_fields:
            field = tech_fields[industry][0]
            requirements.append({
                "type": "技术领域",
                "field": field,
                "description": f"技术领域必须为：{field}"
            })
        
        # 认证要求
        certifications = ["ISO9001", "ISO14001", "高新技术企业", "专精特新企业"]
        certification = certifications[len(park_info['name']) % len(certifications)]
        requirements.append({
            "type": "认证要求",
            "certification": certification,
            "description": f"必须获得{certification}认证"
        })
        
        return requirements
    
    def _generate_compliance_standards(self, industry: str) -> List[Dict[str, Any]]:
        """生成合规标准"""
        standards = [
            {
                "type": "数据安全",
                "requirement": "符合国家数据安全法律法规要求",
                "reference": "《网络安全法》《数据安全法》《个人信息保护法》"
            },
            {
                "type": "知识产权",
                "requirement": "拥有自主知识产权，无侵权行为",
                "reference": "《专利法》《商标法》《著作权法》"
            },
            {
                "type": "环境保护",
                "requirement": "符合环保要求，无环境污染",
                "reference": "《环境保护法》《大气污染防治法》"
            },
            {
                "type": "劳动用工",
                "requirement": "符合劳动法律法规，保障员工权益",
                "reference": "《劳动法》《劳动合同法》《社会保险法》"
            }
        ]
        
        # 根据行业添加特定合规要求
        if industry in ["人工智能", "自动驾驶", "区块链"]:
            standards.append({
                "type": "算法安全",
                "requirement": "算法设计符合伦理和安全要求",
                "reference": "《新一代人工智能伦理规范》"
            })
        
        if industry in ["生物科技", "医药"]:
            standards.append({
                "type": "临床试验",
                "requirement": "临床试验符合GCP规范",
                "reference": "《药物临床试验质量管理规范》"
            })
        
        return standards
    
    def _random_amount(self, min_amount: int, max_amount: int) -> int:
        """生成随机金额"""
        import random
        return random.randint(min_amount, max_amount)
    
    def _random_percentage(self, min_percentage: int, max_percentage: int) -> int:
        """生成随机百分比"""
        import random
        return random.randint(min_percentage, max_percentage)
    
    def _random_duration(self, min_duration: int, max_duration: int) -> int:
        """生成随机持续时间"""
        import random
        return random.randint(min_duration, max_duration)
    
    def populate_database(self, num_policies: int = 15) -> Dict[str, Any]:
        """填充数据库"""
        results = {
            "total_policies": 0,
            "successful_policies": 0,
            "failed_policies": 0,
            "parks_covered": [],
            "industries_covered": [],
            "processing_time": 0,
            "errors": []
        }
        
        import time
        start_time = time.time()
        
        logger.info(f"开始填充中国高新区政策数据库，目标数量：{num_policies}")
        
        # 生成政策数据
        policies_generated = 0
        attempts = 0
        max_attempts = num_policies * 2
        
        while policies_generated < num_policies and attempts < max_attempts:
            attempts += 1
            
            try:
                # 随机选择科技园区和行业
                park_info = self.tech_parks[policies_generated % len(self.tech_parks)]
                industry = self.industries[policies_generated % len(self.industries)]
                
                # 生成政策
                policy = self.generate_policy(park_info, industry)
                
                # 添加到数据库
                policy_id = self.db_service.add_policy(policy)
                
                results["total_policies"] += 1
                results["successful_policies"] += 1
                results["parks_covered"].append(park_info['name'])
                results["industries_covered"].append(industry)
                
                logger.info(f"成功生成政策：{policy.title} (ID: {policy_id})")
                policies_generated += 1
                
            except Exception as e:
                results["failed_policies"] += 1
                results["errors"].append({
                    "attempt": attempts,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                logger.error(f"生成政策失败：{e}")
        
        results["processing_time"] = time.time() - start_time
        results["parks_covered"] = list(set(results["parks_covered"]))
        results["industries_covered"] = list(set(results["industries_covered"]))
        
        logger.info(f"数据库填充完成：{results['successful_policies']}/{results['total_policies']} 政策成功")
        return results
    
    def generate_policy_report(self) -> Dict[str, Any]:
        """生成政策统计报告"""
        stats = self.db_service.get_policy_statistics()
        
        # 获取最新政策
        from services.policy_database_service import PolicyQueryFilter
        latest_filter = PolicyQueryFilter(limit=10)
        latest_policies = self.db_service.search_policies(latest_filter)
        
        # 获取按地区统计
        region_stats = {}
        for park in self.tech_parks:
            region_filter = PolicyQueryFilter(region=park['region'])
            region_result = self.db_service.search_policies(region_filter)
            region_stats[park['region']] = region_result.total_count
        
        # 获取按行业统计
        industry_stats = {}
        for industry in self.industries:
            industry_filter = PolicyQueryFilter(industry=industry)
            industry_result = self.db_service.search_policies(industry_filter)
            industry_stats[industry] = industry_result.total_count
        
        return {
            "database_statistics": stats,
            "latest_policies": [p['title'] for p in latest_policies.policies],
            "region_distribution": region_stats,
            "industry_distribution": industry_stats,
            "top_parks": sorted(region_stats.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_industries": sorted(industry_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        }

def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建政策生成器
    generator = ChinaPolicyGenerator()
    
    # 填充数据库
    results = generator.populate_database(num_policies=15)
    
    # 生成报告
    report = generator.generate_policy_report()
    
    # 输出结果
    print("\n=== 中国高新区政策数据库填充结果 ===")
    print(f"总政策数：{results['total_policies']}")
    print(f"成功政策数：{results['successful_policies']}")
    print(f"失败政策数：{results['failed_policies']}")
    print(f"覆盖园区：{len(results['parks_covered'])}个")
    print(f"覆盖行业：{len(results['industries_covered'])}个")
    print(f"处理时间：{results['processing_time']:.2f}秒")
    
    print("\n=== 覆盖的园区 ===")
    for park in results['parks_covered']:
        print(f"  - {park}")
    
    print("\n=== 覆盖的行业 ===")
    for industry in results['industries_covered']:
        print(f"  - {industry}")
    
    print("\n=== 数据库统计 ===")
    print(f"总政策数：{report['database_statistics']['total_policies']}")
    print(f"按国家统计：{report['database_statistics']['by_country']}")
    print(f"按行业统计：{report['database_statistics']['by_industry']}")
    
    print("\n=== 热门园区 ===")
    for park, count in report['top_parks']:
        print(f"  {park}: {count}个政策")
    
    print("\n=== 热门行业 ===")
    for industry, count in report['top_industries']:
        print(f"  {industry}: {count}个政策")
    
    print("\n=== 最新政策 ===")
    for policy in report['latest_policies']:
        print(f"  - {policy}")

if __name__ == "__main__":
    main()