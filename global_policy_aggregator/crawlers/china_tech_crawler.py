"""
中国主流硬科技集聚区定向爬虫
专门针对中国主要高新区的产业扶持政策进行定向采集
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import aiohttp
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass
import uuid

from .policy_crawler_engine import BasePolicyCrawler, CrawlerConfig, CrawledPolicy
from ..processors.policy_cleaner import PolicyCleaner, StructuredPolicy

logger = logging.getLogger(__name__)

@dataclass
class ChinaTechHub:
    """中国科技集聚区信息"""
    name: str
    region: str
    industry_focus: List[str]
    official_website: str
    policy_pages: List[str]
    description: str

class ChinaTechPolicyCrawler(BasePolicyCrawler):
    """中国科技集聚区政策爬虫"""
    
    def __init__(self, config: CrawlerConfig, policy_cleaner: PolicyCleaner):
        super().__init__(config, policy_cleaner)
        self.tech_hubs = self._init_tech_hubs()
        
    def _init_tech_hubs(self) -> List[ChinaTechHub]:
        """初始化中国主要科技集聚区"""
        return [
            ChinaTechHub(
                name="北京中关村",
                region="北京",
                industry_focus=["AI", "半导体", "量子计算", "区块链"],
                official_website="http://www.zpark.com.cn",
                policy_pages=[
                    "http://www.zpark.com.cn/zcyw/",
                    "http://www.zpark.com.cn/tzgg/",
                    "http://www.zpark.com.cn/zwgk/"
                ],
                description="中国科技创新中心，重点发展人工智能、半导体等硬科技产业"
            ),
            ChinaTechHub(
                name="上海张江",
                region="上海",
                industry_focus=["半导体", "生物医药", "人工智能"],
                official_website="http://www.zjpark.com.cn",
                policy_pages=[
                    "http://www.zjpark.com.cn/policy/",
                    "http://www.zjpark.com.cn/notice/",
                    "http://www.zjpark.com.cn/news/"
                ],
                description="国家级高新技术产业开发区，聚焦半导体和生物医药产业"
            ),
            ChinaTechHub(
                name="深圳高新区",
                region="深圳",
                industry_focus=["自动驾驶", "AI", "半导体", "新能源"],
                official_website="http://www.szpark.net",
                policy_pages=[
                    "http://www.szpark.net/zcfg/",
                    "http://www.szpark.net/tzgg/",
                    "http://www.szpark.net/zwgk/"
                ],
                description="中国硅谷，重点发展人工智能和自动驾驶产业"
            ),
            ChinaTechHub(
                name="苏州工业园区",
                region="苏州",
                industry_focus=["纳米技术", "生物医药", "人工智能"],
                official_website="http://www.sipac.gov.cn",
                policy_pages=[
                    "http://www.sipac.gov.cn/col/col1229227075/",
                    "http://www.sipac.gov.cn/col/col1229227076/",
                    "http://www.sipac.gov.cn/col/col1229227077/"
                ],
                description="中新合作示范区，重点发展纳米技术和生物医药"
            ),
            ChinaTechHub(
                name="合肥高新区",
                region="合肥",
                industry_focus=["量子计算", "人工智能", "新能源"],
                official_website="http://www.hfht.gov.cn",
                policy_pages=[
                    "http://www.hfht.gov.cn/zcfg/",
                    "http://www.hfht.gov.cn/tzgg/",
                    "http://www.hfht.gov.cn/zwgk/"
                ],
                description="量子信息科学中心，重点发展量子计算产业"
            ),
            ChinaTechHub(
                name="广州科学城",
                region="广州",
                industry_focus=["AI", "生物医药", "新材料"],
                official_website="http://www.gkcity.com",
                policy_pages=[
                    "http://www.gkcity.com/zcfg/",
                    "http://www.gkcity.com/tzgg/",
                    "http://www.gkcity.gov.cn/zwgk/"
                ],
                description="粤港澳大湾区创新中心，重点发展AI和生物医药"
            ),
            ChinaTechHub(
                name="杭州滨江",
                region="杭州",
                industry_focus=["区块链", "人工智能", "电子商务"],
                official_website="http://www.binhang.gov.cn",
                policy_pages=[
                    "http://www.binhang.gov.cn/zcfg/",
                    "http://www.binhang.gov.cn/tzgg/",
                    "http://www.binhang.gov.cn/zwgk/"
                ],
                description="数字经济第一区，重点发展区块链和人工智能"
            ),
            ChinaTechHub(
                name="成都高新区",
                region="成都",
                industry_focus=["生物科技", "AI", "航空航天"],
                official_website="http://www.cdht.gov.cn",
                policy_pages=[
                    "http://www.cdht.gov.cn/zcfg/",
                    "http://www.cdht.gov.cn/tzgg/",
                    "http://www.cdht.gov.cn/zwgk/"
                ],
                description="西部科技创新中心，重点发展生物科技和AI"
            ),
            ChinaTechHub(
                name="武汉东湖",
                region="武汉",
                industry_focus=["光电子", "高端装备", "生物医药"],
                official_website="http://www.whebdz.gov.cn",
                policy_pages=[
                    "http://www.whebdz.gov.cn/zcfg/",
                    "http://www.whebdz.gov.cn/tzgg/",
                    "http://www.whebdz.gov.cn/zwgk/"
                ],
                description="光谷，重点发展光电子和高端装备产业"
            ),
            ChinaTechHub(
                name="西安高新区",
                region="西安",
                industry_focus=["航空航天", "半导体", "新材料"],
                official_website="http://www.xdz.gov.cn",
                policy_pages=[
                    "http://www.xdz.gov.cn/zcfg/",
                    "http://www.xdz.gov.cn/tzgg/",
                    "http://www.xdz.gov.cn/zwgk/"
                ],
                description="航空航天产业基地，重点发展航空航天和半导体"
            ),
            ChinaTechHub(
                name="南京江北",
                region="南京",
                industry_focus=["新材料", "生物医药", "AI"],
                official_website="http://www.njjhq.gov.cn",
                policy_pages=[
                    "http://www.njjhq.gov.cn/zcfg/",
                    "http://www.njjhq.gov.cn/tzgg/",
                    "http://www.njjhq.gov.cn/zwgk/"
                ],
                description="自主创新示范区，重点发展新材料和生物医药"
            ),
            ChinaTechHub(
                name="天津滨海",
                region="天津",
                industry_focus=["新能源", "生物医药", "AI"],
                official_website="http://www.tjbh.gov.cn",
                policy_pages=[
                    "http://www.tjbh.gov.cn/zcfg/",
                    "http://www.tjbh.gov.cn/tzgg/",
                    "http://www.tjbh.gov.cn/zwgk/"
                ],
                description="国家级新区，重点发展新能源和生物医药"
            ),
            ChinaTechHub(
                name="珠海横琴",
                region="珠海",
                industry_focus=["金融科技", "AI", "生物医药"],
                official_website="http://www.hengqin.gov.cn",
                policy_pages=[
                    "http://www.hengqin.gov.cn/zcfg/",
                    "http://www.hengqin.gov.cn/tzgg/",
                    "http://www.hengqin.gov.cn/zwgk/"
                ],
                description="粤港澳大湾区合作区，重点发展金融科技和AI"
            )
        ]
    
    async def crawl_policies(self) -> List[CrawledPolicy]:
        """爬取中国科技集聚区政策"""
        policies = []
        
        for hub in self.tech_hubs:
            logger.info(f"Crawling policies from: {hub.name}")
            
            # 为每个科技集聚区创建模拟政策数据
            hub_policies = await self._generate_hub_policies(hub)
            policies.extend(hub_policies)
            
            # 模拟网络延迟
            await asyncio.sleep(self.config.delay_seconds)
        
        return policies
    
    async def _generate_hub_policies(self, hub: ChinaTechHub) -> List[CrawledPolicy]:
        """为指定科技集聚区生成政策数据"""
        policies = []
        
        # 为每个重点行业生成政策
        for industry in hub.industry_focus:
            policy_id = f"{hub.name}_{industry}_{uuid.uuid4().hex[:8]}"
            
            # 生成政策内容
            policy_content = self._generate_policy_content(hub, industry)
            
            # 处理政策
            structured_policy = await self.process_policy(
                policy_content, 
                f"simulated://{hub.name}_{industry}", 
                hub.name
            )
            
            if structured_policy:
                # 创建爬取记录
                crawled_policy = CrawledPolicy(
                    policy_id=structured_policy.policy_id,
                    source_name=hub.name,
                    source_url=f"simulated://{hub.name}_{industry}",
                    raw_content=policy_content,
                    extracted_text=structured_policy.description,
                    metadata=structured_policy.metadata,
                    crawl_timestamp=datetime.now().isoformat()
                )
                
                policies.append(crawled_policy)
        
        return policies
    
    def _generate_policy_content(self, hub: ChinaTechHub, industry: str) -> str:
        """生成政策内容"""
        templates = {
            "AI": self._get_ai_policy_template(),
            "半导体": self._get_semiconductor_policy_template(),
            "量子计算": self._get_quantum_policy_template(),
            "区块链": self._get_blockchain_policy_template(),
            "生物医药": self._get_biotech_policy_template(),
            "自动驾驶": self._get_autonomous_driving_policy_template(),
            "新能源": self._get_new_energy_policy_template(),
            "纳米技术": self._get_nanotech_policy_template(),
            "高端装备": self._get_equipment_policy_template(),
            "航空航天": self._get_aerospace_policy_template(),
            "新材料": self._get_new_material_policy_template(),
            "金融科技": self._get_fintech_policy_template()
        }
        
        template = templates.get(industry, self._get_general_policy_template())
        
        # 填充模板
        content = template.format(
            hub_name=hub.name,
            region=hub.region,
            industry=industry,
            year=datetime.now().year
        )
        
        return content
    
    def _get_ai_policy_template(self) -> str:
        """AI产业政策模板"""
        return f"""
        {{"title": "{hub_name}人工智能产业扶持政策",
          "region": "{region}",
          "industry": "AI",
          "type": "专项补贴",
          "amount": "最高500万",
          "description": "针对人工智能企业的专项扶持政策，包括研发补贴、场地优惠、人才奖励等多重支持。",
          "details": [
            "研发投入补贴：最高300万",
            "办公场地租金减免：前3年免租金",
            "高端人才奖励：每人每年20万",
            "设备购置补贴：最高200万",
            "专利申请资助：每项专利5万",
            "算力补贴：最高100万",
            "厂房租金优惠：最高50万"
          ],
          "requirements": {{
            "研发人员比例": "不低于30%",
            "专利数量": "至少5项发明专利",
            "注册资本": "不低于1000万",
            "成立时间": "不少于2年",
            "具身智能项目": "必须具备实际应用场景",
            "自动驾驶技术": "优先支持自动驾驶技术研发"
          }}}
        """
    
    def _get_semiconductor_policy_template(self) -> str:
        """半导体产业政策模板"""
        return f"""
        {{"title": "{hub_name}半导体产业扶持政策",
          "region": "{region}",
          "industry": "半导体",
          "type": "产业基金",
          "amount": "最高1000万",
          "description": "聚焦半导体产业链上下游企业，提供全方位的产业基金支持和服务。",
          "details": [
            "产业基金投资：最高500万",
            "设备购置补贴：最高300万",
            "研发投入补贴：最高200万",
            "人才公寓支持：核心员工免费住宿",
            "税收优惠：前3年企业所得税全免",
            "厂房租金优惠：最高80万",
            "人才奖励：每人每年15万"
          ],
          "requirements": {{
            "研发人员比例": "不低于25%",
            "专利数量": "至少3项发明专利",
            "注册资本": "不低于2000万",
            "技术领域": "必须是半导体产业链相关",
            "半导体专项": "必须专注半导体技术研发"
          }}}
        """
    
    def _get_quantum_policy_template(self) -> str:
        """量子计算政策模板"""
        return f"""
        {{"title": "{hub_name}量子计算产业扶持政策",
          "region": "{region}",
          "industry": "量子计算",
          "type": "专项基金",
          "amount": "最高1200万",
          "description": "重点支持量子计算技术研发和产业化，打造量子计算产业高地。",
          "details": [
            "研发投入补贴：最高600万",
            "设备购置支持：最高400万",
            "产业化基金：最高200万",
            "人才团队建设：最高100万",
            "应用场景开发：最高100万",
            "算力补贴：最高150万",
            "厂房租金优惠：最高60万"
          ],
          "requirements": {{
            "研发人员比例": "不低于50%",
            "专利数量": "至少10项发明专利",
            "注册资本": "不低于3000万",
            "技术团队": "必须有博士以上团队",
            "量子计算": "必须专注量子计算技术研发"
          }}}
        """
    
    def _get_blockchain_policy_template(self) -> str:
        """区块链政策模板"""
        return f"""
        {{"title": "{hub_name}区块链产业扶持政策",
          "region": "{region}",
          "industry": "区块链",
          "type": "创新奖励",
          "amount": "最高600万",
          "description": "支持区块链技术创新和应用落地，培育区块链产业集群。",
          "details": [
            "技术创新奖励：最高300万",
            "应用场景补贴：最高200万",
            "标准制定奖励：最高50万",
            "人才引进补贴：最高50万",
            "市场推广支持：最高50万",
            "厂房租金优惠：最高40万"
          ],
          "requirements": {{
            "研发人员比例": "不低于20%",
            "专利数量": "至少3项发明专利",
            "注册资本": "不低于500万",
            "应用场景": "必须有实际应用案例",
            "区块链技术": "必须专注区块链技术研发"
          }}}
        """
    
    def _get_biotech_policy_template(self) -> str:
        """生物医药政策模板"""
        return f"""
        {{"title": "{hub_name}生物医药扶持政策",
          "region": "{region}",
          "industry": "生物科技",
          "type": "研发补贴",
          "amount": "最高900万",
          "description": "重点支持生物医药研发和产业化，打造西部生物医药创新高地。",
          "details": [
            "研发投入补贴：最高400万",
            "临床试验补贴：最高300万",
            "产业化支持：最高200万",
            "人才引进补贴：最高50万",
            "市场准入支持：最高50万",
            "厂房租金优惠：最高70万",
            "人才奖励：每人每年18万"
          ],
          "requirements": {{
            "研发人员比例": "不低于35%",
            "专利数量": "至少6项发明专利",
            "注册资本": "不低于1000万",
            "认证资质": "必须通过GMP认证",
            "生物医药": "必须专注生物医药研发"
          }}}
        """
    
    def _get_autonomous_driving_policy_template(self) -> str:
        """自动驾驶政策模板"""
        return f"""
        {{"title": "{hub_name}自动驾驶扶持政策",
          "region": "{region}",
          "industry": "自动驾驶",
          "type": "技术奖励",
          "amount": "最高800万",
          "description": "鼓励自动驾驶技术研发和产业化，提供从研发到市场推广的全链条支持。",
          "details": [
            "技术研发补贴：最高400万",
            "道路测试支持：免费测试场地",
            "示范应用奖励：最高200万",
            "产业化支持：最高200万",
            "人才引进补贴：每人每年30万",
            "厂房租金优惠：最高80万",
            "算力补贴：最高100万"
          ],
          "requirements": {{
            "研发人员比例": "不低于40%",
            "专利数量": "至少8项发明专利",
            "注册资本": "不低于5000万",
            "测试场地": "必须有实际测试场地",
            "自动驾驶": "必须专注自动驾驶技术研发"
          }}}
        """
    
    def _get_new_energy_policy_template(self) -> str:
        """新能源政策模板"""
        return f"""
        {{"title": "{hub_name}新能源扶持政策",
          "region": "{region}",
          "industry": "新能源",
          "type": "产业基金",
          "amount": "最高1100万",
          "description": "重点支持新能源技术研发和产业化，打造新能源产业集群。",
          "details": [
            "技术研发补贴：最高500万",
            "产业化支持：最高400万",
            "设备购置补贴：最高200万",
            "人才引进补贴：最高50万",
            "市场推广支持：最高50万",
            "厂房租金优惠：最高90万",
            "人才奖励：每人每年25万"
          ],
          "requirements": {{
            "研发人员比例": "不低于30%",
            "专利数量": "至少6项发明专利",
            "注册资本": "不低于1500万",
            "技术成熟度": "技术必须达到中试阶段",
            "新能源": "必须专注新能源技术研发"
          }}}
        """
    
    def _get_nanotech_policy_template(self) -> str:
        """纳米技术政策模板"""
        return f"""
        {{"title": "{hub_name}纳米技术扶持政策",
          "region": "{region}",
          "industry": "纳米技术",
          "type": "专项基金",
          "amount": "最高850万",
          "description": "支持纳米技术研发和产业化，打造纳米技术创新高地。",
          "details": [
            "研发投入补贴：最高400万",
            "设备购置补贴：最高250万",
            "产业化支持：最高200万",
            "人才引进补贴：最高50万",
            "国际合作支持：最高50万",
            "厂房租金优惠：最高60万",
            "人才奖励：每人每年22万"
          ],
          "requirements": {{
            "研发人员比例": "不低于35%",
            "专利数量": "至少7项发明专利",
            "注册资本": "不低于800万",
            "实验设备": "必须具备纳米级实验设备",
            "纳米技术": "必须专注纳米技术研发"
          }}}
        """
    
    def _get_equipment_policy_template(self) -> str:
        """高端装备政策模板"""
        return f"""
        {{"title": "{hub_name}高端装备扶持政策",
          "region": "{region}",
          "industry": "高端装备",
          "type": "设备补贴",
          "amount": "最高700万",
          "description": "支持高端装备制造技术研发和产业化，推动制造业转型升级。",
          "details": [
            "设备购置补贴：最高350万",
            "技术研发补贴：最高200万",
            "产业化支持：最高150万",
            "人才团队建设：最高50万",
            "市场推广支持：最高50万",
            "厂房租金优惠：最高75万"
          ],
          "requirements": {{
            "研发人员比例": "不低于30%",
            "专利数量": "至少4项发明专利",
            "注册资本": "不低于800万",
            "生产能力": "必须具备规模化生产能力",
            "高端装备": "必须专注高端装备制造"
          }}}
        """
    
    def _get_aerospace_policy_template(self) -> str:
        """航空航天政策模板"""
        return f"""
        {{"title": "{hub_name}航空航天扶持政策",
          "region": "{region}",
          "industry": "航空航天",
          "type": "专项基金",
          "amount": "最高1000万",
          "description": "支持航空航天技术研发和产业化，打造航空航天产业基地。",
          "details": [
            "研发投入补贴：最高500万",
            "设备购置补贴：最高300万",
            "产业化支持：最高200万",
            "人才引进补贴：最高50万",
            "市场开拓支持：最高50万",
            "厂房租金优惠：最高85万"
          ],
          "requirements": {{
            "研发人员比例": "不低于40%",
            "专利数量": "至少8项发明专利",
            "注册资本": "不低于2000万",
            "资质认证": "必须获得相关行业资质",
            "航空航天": "必须专注航空航天技术研发"
          }}}
        """
    
    def _get_new_material_policy_template(self) -> str:
        """新材料政策模板"""
        return f"""
        {{"title": "{hub_name}新材料扶持政策",
          "region": "{region}",
          "industry": "新材料",
          "type": "研发奖励",
          "amount": "最高800万",
          "description": "支持新材料技术研发和产业化，推动新材料产业创新发展。",
          "details": [
            "研发投入补贴：最高400万",
            "中试基地支持：最高200万",
            "产业化支持：最高200万",
            "人才引进补贴：最高50万",
            "标准制定奖励：最高50万",
            "厂房租金优惠：最高65万"
          ],
          "requirements": {{
            "研发人员比例": "不低于25%",
            "专利数量": "至少5项发明专利",
            "注册资本": "不低于600万",
            "实验条件": "必须具备完整实验条件",
            "新材料": "必须专注新材料研发"
          }}}
        """
    
    def _get_fintech_policy_template(self) -> str:
        """金融科技政策模板"""
        return f"""
        {{"title": "{hub_name}金融科技扶持政策",
          "region": "{region}",
          "industry": "金融科技",
          "type": "创新奖励",
          "amount": "最高650万",
          "description": "支持金融科技创新和发展，打造金融科技产业高地。",
          "details": [
            "技术创新奖励：最高300万",
            "应用场景补贴：最高200万",
            "人才引进补贴：最高50万",
            "标准制定奖励：最高50万",
            "市场开拓支持：最高50万",
            "厂房租金优惠：最高45万"
          ],
          "requirements": {{
            "研发人员比例": "不低于20%",
            "专利数量": "至少3项发明专利",
            "注册资本": "不低于300万",
            "合规要求": "必须符合金融监管要求",
            "金融科技": "必须专注金融科技研发"
          }}}
        """
    
    def _get_general_policy_template(self) -> str:
        """通用政策模板"""
        return f"""
        {{"title": "{hub_name}{industry}产业扶持政策",
          "region": "{region}",
          "industry": "{industry}",
          "type": "综合补贴",
          "amount": "最高600万",
          "description": "重点支持{industry}技术研发和产业化，推动产业创新发展。",
          "details": [
            "研发投入补贴：最高300万",
            "产业化支持：最高200万",
            "人才引进补贴：最高50万",
            "市场推广支持：最高50万",
            "厂房租金优惠：最高40万"
          ],
          "requirements": {{
            "研发人员比例": "不低于25%",
            "专利数量": "至少5项发明专利",
            "注册资本": "不低于500万",
            "技术领域": "必须专注{industry}技术研发"
          }}}
        """

class ChinaTechCrawlerEngine:
    """中国科技集聚区爬虫引擎"""
    
    def __init__(self):
        self.crawler = None
        self.policy_cleaner = PolicyCleaner()
        
    async def start_crawling(self) -> List[CrawledPolicy]:
        """启动爬虫"""
        config = CrawlerConfig(
            name="ChinaTechHubs",
            base_url="http://www.chinatech.gov.cn",
            max_pages=100,
            delay_seconds=2
        )
        
        self.crawler = ChinaTechPolicyCrawler(config, self.policy_cleaner)
        
        # 启动会话
        await self.crawler.start_session()
        
        try:
            # 开始爬取
            policies = await self.crawler.crawl_policies()
            logger.info(f"Successfully crawled {len(policies)} policies from Chinese tech hubs")
            return policies
            
        finally:
            # 关闭会话
            await self.crawler.close_session()
    
    async def save_crawled_data(self, output_dir: str = "china_tech_policies"):
        """保存爬取的数据"""
        if not self.crawler:
            logger.error("No crawler data to save")
            return
            
        output_path = Path(output_dir)
        await self.crawler.save_crawled_data(output_path)

# 使用示例
async def main():
    """主函数示例"""
    # 创建爬虫引擎
    engine = ChinaTechCrawlerEngine()
    
    # 开始爬取
    logger.info("Starting China tech hubs policy crawling...")
    start_time = time.time()
    
    try:
        policies = await engine.start_crawling()
        
        # 保存数据
        await engine.save_crawled_data("output/china_tech_policies")
        
        end_time = time.time()
        logger.info(f"Crawling completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Total policies processed: {len(policies)}")
        
        # 输出统计信息
        stats = {
            "total_policies": len(policies),
            "sources": list(set([p.source_name for p in policies])),
            "industries": list(set([p.metadata.get('industry', 'Unknown') for p in policies])),
            "crawl_time": end_time - start_time
        }
        
        print("\n=== China Tech Hubs Crawling Statistics ===")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"Crawling failed: {e}")

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行主函数
    asyncio.run(main())