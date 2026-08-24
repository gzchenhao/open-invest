#!/usr/bin/env python3
"""
中国主流硬科技集聚区定向爬虫
专门针对广州所有行政区域、北京中关村、上海张江、深圳高新区、苏州工业园区、合肥高新区等
重点采集具身智能/自动驾驶/半导体专项补贴、算力补贴、厂房租金优惠、人才奖励等政策
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

from .policy_crawler_engine import BasePolicyCrawler, CrawlerConfig, CrawledPolicy
from ..processors.policy_cleaner import PolicyCleaner, StructuredPolicy

logger = logging.getLogger(__name__)

@dataclass
class ChinaTechHubConfig:
    """中国科技集聚区配置"""
    name: str
    region: str
    base_urls: List[str]
    industries: List[str]
    priority_fields: List[str] = None
    
    def __post_init__(self):
        if self.priority_fields is None:
            self.priority_fields = [
                "具身智能", "自动驾驶", "半导体", "算力补贴", "厂房租金", 
                "人才奖励", "研发人员比例", "专利数量", "专项补贴"
            ]

class ChinaTechHubCrawler(BasePolicyCrawler):
    """中国科技集聚区定向爬虫"""
    
    def __init__(self, config: CrawlerConfig, tech_hub_config: ChinaTechHubConfig, policy_cleaner: PolicyCleaner):
        super().__init__(config, policy_cleaner)
        self.tech_hub_config = tech_hub_config
        
    async def crawl_policies(self) -> List[CrawledPolicy]:
        """爬取中国科技集聚区政策"""
        policies = []
        
        logger.info(f"开始爬取 {self.tech_hub_config.name} ({self.tech_hub_config.region}) 政策")
        
        for url in self.tech_hub_config.base_urls:
            logger.info(f"爬取URL: {url}")
            
            # 获取页面内容
            content = await self.fetch_page(url)
            if not content:
                logger.warning(f"无法获取页面内容: {url}")
                continue
            
            # 解析页面内容
            extracted_policies = await self.parse_policy_page(content, url)
            
            for policy_content in extracted_policies:
                structured_policy = await self.process_policy(
                    policy_content, url, self.tech_hub_config.name
                )
                if structured_policy:
                    policies.append(structured_policy)
            
            # 模拟延迟
            await asyncio.sleep(self.config.delay_seconds)
        
        logger.info(f"从 {self.tech_hub_config.name} 爬取到 {len(policies)} 条政策")
        return policies
    
    async def parse_policy_page(self, content: str, source_url: str) -> List[str]:
        """解析政策页面，提取政策内容"""
        policies = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 查找政策相关的元素
            policy_elements = []
            
            # 查找标题包含关键词的元素
            for keyword in self.tech_hub_config.priority_fields:
                elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'div', 'p'], 
                                      string=re.compile(keyword, re.IGNORECASE))
                policy_elements.extend(elements)
            
            # 查找可能的政策链接
            policy_links = soup.find_all('a', href=re.compile(
                r'(政策|扶持|补贴|奖励|通知|公告)', re.IGNORECASE))
            policy_elements.extend(policy_links)
            
            # 提取文本内容
            for element in policy_elements:
                if element.name == 'a':
                    # 如果是链接，尝试获取链接页面内容
                    link_url = element.get('href')
                    if link_url and not link_url.startswith('http'):
                        link_url = self.config.base_url + link_url
                    
                    if link_url:
                        link_content = await self.fetch_page(link_url)
                        if link_content:
                            policies.append(link_content)
                else:
                    # 直接提取文本
                    text = element.get_text(strip=True)
                    if len(text) > 100:  # 过滤太短的文本
                        policies.append(text)
            
            # 如果没有找到具体政策，使用整个页面内容
            if not policies:
                logger.warning(f"在 {source_url} 中未找到具体政策内容，使用页面全文")
                policies.append(content)
            
        except Exception as e:
            logger.error(f"解析页面 {source_url} 时出错: {e}")
            policies.append(content)
        
        return policies
    
    async def extract_policy_details(self, content: str) -> Dict[str, Any]:
        """提取政策详细信息"""
        details = {
            "具身智能补贴": self._extract_amount(content, ["具身智能", "智能机器人"]),
            "自动驾驶补贴": self._extract_amount(content, ["自动驾驶", "智能网联"]),
            "半导体专项补贴": self._extract_amount(content, ["半导体", "集成电路", "芯片"]),
            "算力补贴": self._extract_amount(content, ["算力", "计算资源", "云计算"]),
            "厂房租金优惠": self._extract_rent_discount(content),
            "人才奖励": self._extract_talent_reward(content),
            "研发人员比例": self._extract_rdp_ratio(content),
            "专利数量": self._extract_patent_count(content),
            "注册资本要求": self._extract_capital_requirement(content),
            "申请截止日期": self._extract_deadline(content)
        }
        
        return details
    
    def _extract_amount(self, content: str, keywords: List[str]) -> str:
        """提取补贴金额"""
        for keyword in keywords:
            pattern = rf"{keyword}[^\d]*(\d+万|\d+万元|\d+亿|\d+亿元)"
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return "未明确"
    
    def _extract_rent_discount(self, content: str) -> str:
        """提取厂房租金优惠"""
        patterns = [
            r"厂房租金.*?(\d+年.*?免租金|\d+折|免费)",
            r"办公场地.*?(租金.*?\d+折|免.*?\d+年)",
            r"租金.*?(减免|优惠).*?(\d+年|\d+折)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0)
        
        return "未明确"
    
    def _extract_talent_reward(self, content: str) -> str:
        """提取人才奖励"""
        patterns = [
            r"人才.*?(奖励|补贴).*?(\d+万|\d+万元)",
            r"高端人才.*?(\d+万|\d+万元)每年",
            r"引进人才.*?(\d+万|\d+万元)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0)
        
        return "未明确"
    
    def _extract_rdp_ratio(self, content: str) -> str:
        """提取研发人员比例"""
        patterns = [
            r"研发人员.*?(比例|占比).*?(\d+%|不低于\d+%|不少于\d+%)",
            r"研发人员.*?(\d+人.*?总人数)",
            r"科技人员.*?(\d+%)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0)
        
        return "未明确"
    
    def _extract_patent_count(self, content: str) -> str:
        """提取专利数量要求"""
        patterns = [
            r"专利.*?(数量|个数).*?(\d+项|\d+个)",
            r"至少.*?(\d+)项.*?专利",
            r"拥有.*?(\d+)项.*?专利"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0)
        
        return "未明确"
    
    def _extract_capital_requirement(self, content: str) -> str:
        """提取注册资本要求"""
        patterns = [
            r"注册资本.*?(不少于|不低于|至少).*?(\d+万|\d+万元|\d+亿|\d+亿元)",
            r"注册资金.*?(不少于|不低于|至少).*?(\d+万|\d+万元|\d+亿|\d+亿元)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0)
        
        return "未明确"
    
    def _extract_deadline(self, content: str) -> str:
        """提取申请截止日期"""
        patterns = [
            r"截止.*?(\d{4}年\d{1,2}月\d{1,2}日)",
            r"截止.*?(\d{4}-\d{1,2}-\d{1,2})",
            r"申请.*?截止.*?(\d{4}年\d{1,2}月)",
            r"(\d{4}年\d{1,2}月\d{1,2}日).*?(截止|结束)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return "未明确"

class ChinaTechHubCrawlerEngine:
    """中国科技集聚区爬虫引擎"""
    
    def __init__(self):
        self.crawlers = []
        self.policy_cleaner = PolicyCleaner()
        self.is_running = False
        
        # 中国主要科技集聚区配置
        self.tech_hubs = [
            ChinaTechHubConfig(
                name="北京中关村",
                region="北京",
                base_urls=[
                    "http://www.zpark.com.cn",
                    "http://www.zgc.gov.cn",
                    "http://www.zgcgw.gov.cn"
                ],
                industries=["AI", "量子计算", "生物医药", "新材料"]
            ),
            ChinaTechHubConfig(
                name="上海张江",
                region="上海",
                base_urls=[
                    "http://www.zjpark.com.cn",
                    "http://www.zjpark.sh.cn",
                    "http://www.shanghai.gov.cn"
                ],
                industries=["半导体", "AI", "生物医药", "新能源"]
            ),
            ChinaTechHubConfig(
                name="深圳高新区",
                region="深圳",
                base_urls=[
                    "http://www.szhigh-tech.com",
                    "http://www.sz.gov.cn",
                    "http://www.szzgc.gov.cn"
                ],
                industries=["自动驾驶", "半导体", "AI", "金融科技"]
            ),
            ChinaTechHubConfig(
                name="苏州工业园区",
                region="苏州",
                base_urls=[
                    "http://www.sipac.gov.cn",
                    "http://www.sip.gov.cn",
                    "http://www.suzhou.gov.cn"
                ],
                industries=["纳米技术", "生物医药", "AI", "新材料"]
            ),
            ChinaTechHubConfig(
                name="合肥高新区",
                region="合肥",
                base_urls=[
                    "http://www.hfht.gov.cn",
                    "http://www.hf.gov.cn",
                    "http://www.ah.gov.cn"
                ],
                industries=["量子计算", "AI", "生物医药", "新能源"]
            ),
            # 广州所有行政区域
            ChinaTechHubConfig(
                name="广州天河区",
                region="广州",
                base_urls=[
                    "http://www.thnet.gov.cn",
                    "http://www.gz.gov.cn"
                ],
                industries=["AI", "金融科技", "生物医药"]
            ),
            ChinaTechHubConfig(
                name="广州黄埔区",
                region="广州",
                base_urls=[
                    "http://www.hp.gov.cn",
                    "http://www.gz.gov.cn"
                ],
                industries=["智能制造", "新材料", "新能源"]
            ),
            ChinaTechHubConfig(
                name="广州番禺区",
                region="广州",
                base_urls=[
                    "http://www.panyu.gov.cn",
                    "http://www.gz.gov.cn"
                ],
                industries=["AI", "电子信息", "生物医药"]
            ),
            ChinaTechHubConfig(
                name="广州南沙区",
                region="广州",
                base_urls=[
                    "http://www.nansha.gov.cn",
                    "http://www.gz.gov.cn"
                ],
                industries=["AI", "新能源", "生物医药"]
            ),
            ChinaTechHubConfig(
                name="广州白云区",
                region="广州",
                base_urls=[
                    "http://www.baiyun.gov.cn",
                    "http://www.gz.gov.cn"
                ],
                industries=["AI", "智能制造", "新材料"]
            )
        ]
    
    def add_crawler(self, crawler: ChinaTechHubCrawler):
        """添加爬虫"""
        self.crawlers.append(crawler)
        
    async def start_all_crawlers(self):
        """启动所有爬虫"""
        if self.is_running:
            logger.warning("爬虫已经在运行")
            return
            
        self.is_running = True
        logger.info("启动中国科技集聚区爬虫引擎...")
        
        # 启动所有爬虫的会话
        for crawler in self.crawlers:
            await crawler.start_session()
        
        try:
            # 并发运行所有爬虫
            tasks = [crawler.crawl_policies() for crawler in self.crawlers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 收集结果
            all_policies = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"爬虫错误: {result}")
                elif result:
                    all_policies.extend(result)
            
            logger.info(f"总共爬取到 {len(all_policies)} 条政策")
            return all_policies
            
        finally:
            # 关闭所有爬虫的会话
            for crawler in self.crawlers:
                await crawler.close_session()
            
            self.is_running = False
    
    async def crawl_and_save(self, output_dir: str = "china_tech_hubs"):
        """爬取并保存数据"""
        output_path = Path(output_dir)
        
        # 启动所有爬虫
        all_policies = await self.start_all_crawlers()
        
        # 保存数据
        for crawler in self.crawlers:
            await crawler.save_crawled_data(output_path / crawler.tech_hub_config.name.lower())
        
        return all_policies

# 使用示例
async def main():
    """主函数示例"""
    # 创建爬虫引擎
    engine = ChinaTechHubCrawlerEngine()
    
    # 为每个科技集聚区创建爬虫配置
    for tech_hub in engine.tech_hubs:
        config = CrawlerConfig(
            name=tech_hub.name,
            base_url=tech_hub.base_urls[0],
            max_pages=50,
            delay_seconds=3
        )
        
        crawler = ChinaTechHubCrawler(config, tech_hub, engine.policy_cleaner)
        engine.add_crawler(crawler)
    
    # 开始爬取
    logger.info("开始中国科技集聚区政策爬取...")
    start_time = time.time()
    
    try:
        policies = await engine.crawl_and_save("output/china_tech_hubs")
        
        end_time = time.time()
        logger.info(f"爬取完成，耗时 {end_time - start_time:.2f} 秒")
        logger.info(f"总共处理 {len(policies)} 条政策")
        
        # 输出统计信息
        stats = {
            "total_policies": len(policies),
            "regions": list(set([p.location for p in policies])),
            "industries": list(set([p.industry for p in policies])),
            "crawl_time": end_time - start_time
        }
        
        print("\n=== 中国科技集聚区爬取统计 ===")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"爬取失败: {e}")

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行主函数
    asyncio.run(main())