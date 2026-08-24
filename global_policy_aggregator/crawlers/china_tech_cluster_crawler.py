"""
中国主流硬科技集聚区定向爬虫
专门针对中国主要高新区的产业扶持政策进行爬取
重点采集：具身智能/自动驾驶/半导体专项补贴、算力补贴、厂房租金优惠、人才奖励等
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

from ..processors.policy_cleaner import PolicyCleaner, StructuredPolicy
from .policy_crawler_engine import BasePolicyCrawler, CrawlerConfig, CrawledPolicy

logger = logging.getLogger(__name__)

@dataclass
class TechClusterConfig:
    """科技集聚区配置"""
    name: str
    region: str
    base_url: str
    policy_urls: List[str]
    focus_industries: List[str]
    special_fields: List[str]

class ChinaTechClusterCrawler(BasePolicyCrawler):
    """中国科技集聚区定向爬虫"""
    
    def __init__(self, config: CrawlerConfig, cluster_config: TechClusterConfig, policy_cleaner: PolicyCleaner):
        super().__init__(config, policy_cleaner)
        self.cluster_config = cluster_config
        self.focus_keywords = [
            "具身智能", "自动驾驶", "半导体", "算力", "厂房租金", "人才奖励",
            "研发补贴", "设备补贴", "产业化支持", "税收优惠", "场地优惠",
            "人才公寓", "专利资助", "标准制定", "市场推广", "测试场地",
            "中试基地", "应用场景", "技术团队", "资质认证", "合规要求"
        ]
        
    async def crawl_policies(self) -> List[CrawledPolicy]:
        """爬取中国科技集聚区政策"""
        policies = []
        
        for url in self.cluster_config.policy_urls:
            logger.info(f"Crawling {self.cluster_config.name} policies from: {url}")
            
            try:
                # 获取页面内容
                content = await self.fetch_page(url)
                if not content:
                    logger.warning(f"Failed to fetch {url}")
                    continue
                
                # 解析页面内容
                extracted_policies = await self.parse_policy_page(content, url)
                
                # 处理每个政策
                for policy_content in extracted_policies:
                    structured_policy = await self.process_policy(
                        policy_content, url, self.cluster_config.name
                    )
                    if structured_policy:
                        policies.append(structured_policy)
                
                # 模拟延迟
                await asyncio.sleep(self.config.delay_seconds)
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                continue
        
        return policies
    
    async def parse_policy_page(self, content: str, source_url: str) -> List[str]:
        """解析政策页面，提取政策内容"""
        policies = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 查找政策相关的元素
            policy_elements = []
            
            # 方法1：查找包含政策关键词的div
            for keyword in self.focus_keywords:
                elements = soup.find_all('div', string=re.compile(keyword, re.IGNORECASE))
                policy_elements.extend(elements)
            
            # 方法2：查找包含"政策"、"通知"、"办法"等关键词的标题
            title_elements = soup.find_all(['h1', 'h2', 'h3', 'h4'], 
                                        string=re.compile(r'政策|通知|办法|规定|实施意见', re.IGNORECASE))
            policy_elements.extend(title_elements)
            
            # 方法3：查找可能包含政策内容的文本块
            text_blocks = soup.find_all('div', class_=re.compile(r'content|detail|policy|text', re.IGNORECASE))
            policy_elements.extend(text_blocks)
            
            # 提取文本内容
            for element in policy_elements:
                if hasattr(element, 'text'):
                    text = element.get_text(strip=True)
                    if len(text) > 200:  # 过滤太短的内容
                        policies.append(text)
                        
        except Exception as e:
            logger.error(f"Error parsing policy page {source_url}: {e}")
            # 如果解析失败，返回整个页面内容
            policies.append(content)
        
        return policies
    
    async def process_policy(self, raw_content: str, source_url: str, source_name: str) -> Optional[StructuredPolicy]:
        """处理单个政策，增强中国政策特定字段的处理"""
        try:
            # 先使用基础清洗
            structured_policy = self.cleaner.clean_policy_text(raw_content, source_url)
            
            # 增强中国特定字段的处理
            enhanced_policy = self.enhance_china_policy(structured_policy, raw_content)
            
            # 创建爬取记录
            crawled_policy = CrawledPolicy(
                policy_id=enhanced_policy.policy_id,
                source_name=source_name,
                source_url=source_url,
                raw_content=raw_content,
                extracted_text=enhanced_policy.description,
                metadata=enhanced_policy.metadata,
                crawl_timestamp=datetime.now().isoformat()
            )
            
            self.crawled_policies.append(crawled_policy)
            return enhanced_policy
            
        except Exception as e:
            logger.error(f"Error processing policy from {source_url}: {e}")
            return None
    
    def enhance_china_policy(self, policy: StructuredPolicy, raw_content: str) -> StructuredPolicy:
        """增强中国政策特定字段的处理"""
        # 提取中国特有的政策字段
        enhanced_metadata = policy.metadata.copy()
        
        # 提取具身智能相关补贴
        embodied_ai_subsidy = self.extract_embodied_ai_subsidy(raw_content)
        if embodied_ai_subsidy:
            enhanced_metadata['embodied_ai_subsidy'] = embodied_ai_subsidy
        
        # 提取自动驾驶相关补贴
        auto_driving_subsidy = self.extract_auto_driving_subsidy(raw_content)
        if auto_driving_subsidy:
            enhanced_metadata['auto_driving_subsidy'] = auto_driving_subsidy
        
        # 提取半导体专项补贴
        semiconductor_subsidy = self.extract_semiconductor_subsidy(raw_content)
        if semiconductor_subsidy:
            enhanced_metadata['semiconductor_subsidy'] = semiconductor_subsidy
        
        # 提取算力补贴
        computing_power_subsidy = self.extract_computing_power_subsidy(raw_content)
        if computing_power_subsidy:
            enhanced_metadata['computing_power_subsidy'] = computing_power_subsidy
        
        # 提取厂房租金优惠
        factory_rent_discount = self.extract_factory_rent_discount(raw_content)
        if factory_rent_discount:
            enhanced_metadata['factory_rent_discount'] = factory_rent_discount
        
        # 提取人才奖励
        talent_reward = self.extract_talent_reward(raw_content)
        if talent_reward:
            enhanced_metadata['talent_reward'] = talent_reward
        
        # 更新政策元数据
        policy.metadata = enhanced_metadata
        
        return policy
    
    def extract_embodied_ai_subsidy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取具身智能相关补贴"""
        patterns = [
            r'具身智能.*?补贴.*?(\d+万|\d+万元)',
            r'人形机器人.*?补贴.*?(\d+万|\d+万元)',
            r'智能机器人.*?补贴.*?(\d+万|\d+万元)',
            r'补贴.*?具身智能.*?(\d+万|\d+万元)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                amount = match.group(1)
                return {
                    'type': '专项补贴',
                    'amount': amount,
                    'industry': '具身智能',
                    'description': '具身智能产业专项补贴'
                }
        
        return None
    
    def extract_auto_driving_subsidy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取自动驾驶相关补贴"""
        patterns = [
            r'自动驾驶.*?补贴.*?(\d+万|\d+万元)',
            r'智能网联.*?补贴.*?(\d+万|\d+万元)',
            r'车联网.*?补贴.*?(\d+万|\d+万元)',
            r'补贴.*?自动驾驶.*?(\d+万|\d+万元)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                amount = match.group(1)
                return {
                    'type': '技术奖励',
                    'amount': amount,
                    'industry': '自动驾驶',
                    'description': '自动驾驶技术研发补贴'
                }
        
        return None
    
    def extract_semiconductor_subsidy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取半导体专项补贴"""
        patterns = [
            r'半导体.*?补贴.*?(\d+万|\d+万元)',
            r'集成电路.*?补贴.*?(\d+万|\d+万元)',
            r'芯片.*?补贴.*?(\d+万|\d+万元)',
            r'补贴.*?半导体.*?(\d+万|\d+万元)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                amount = match.group(1)
                return {
                    'type': '产业基金',
                    'amount': amount,
                    'industry': '半导体',
                    'description': '半导体产业专项补贴'
                }
        
        return None
    
    def extract_computing_power_subsidy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取算力补贴"""
        patterns = [
            r'算力.*?补贴.*?(\d+万|\d+万元)',
            r'计算.*?补贴.*?(\d+万|\d+万元)',
            r'GPU.*?补贴.*?(\d+万|\d+万元)',
            r'算力中心.*?补贴.*?(\d+万|\d+万元)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                amount = match.group(1)
                return {
                    'type': '基础设施补贴',
                    'amount': amount,
                    'industry': '算力',
                    'description': '算力基础设施补贴'
                }
        
        return None
    
    def extract_factory_rent_discount(self, content: str) -> Optional[Dict[str, Any]]:
        """提取厂房租金优惠"""
        patterns = [
            r'厂房.*?租金.*?减免.*?(\d+年|免费)',
            r'办公.*?场地.*?租金.*?减免.*?(\d+年|免费)',
            r'租金.*?补贴.*?(\d+万|\d+万元)',
            r'场地.*?优惠.*?(\d+年|免费)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                benefit = match.group(1)
                return {
                    'type': '租金优惠',
                    'amount': benefit,
                    'industry': '场地',
                    'description': '厂房租金减免优惠'
                }
        
        return None
    
    def extract_talent_reward(self, content: str) -> Optional[Dict[str, Any]]:
        """提取人才奖励"""
        patterns = [
            r'人才.*?奖励.*?(\d+万|\d+万元)',
            r'高端.*?人才.*?补贴.*?(\d+万|\d+万元)',
            r'专家.*?补贴.*?(\d+万|\d+万元)',
            r'人才.*?引进.*?补贴.*?(\d+万|\d+万元)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                amount = match.group(1)
                return {
                    'type': '人才奖励',
                    'amount': amount,
                    'industry': '人才',
                    'description': '高端人才引进奖励'
                }
        
        return None

# 中国主要科技集聚区配置
CHINA_TECH_CLUSTERS = {
    "北京中关村": TechClusterConfig(
        name="北京中关村",
        region="北京",
        base_url="http://www.zpark.com.cn",
        policy_urls=[
            "http://www.zpark.com.cn/policy/",
            "http://www.zpark.com.cn/notice/",
            "http://www.zpark.com.cn/news/"
        ],
        focus_industries=["AI", "半导体", "量子计算"],
        special_fields=["具身智能", "自动驾驶", "算力补贴"]
    ),
    "上海张江": TechClusterConfig(
        name="上海张江",
        region="上海",
        base_url="http://www.zjpark.com.cn",
        policy_urls=[
            "http://www.zjpark.com.cn/policy/",
            "http://www.zjpark.com.cn/notice/",
            "http://www.zjpark.com.cn/news/"
        ],
        focus_industries=["半导体", "生物医药", "人工智能"],
        special_fields=["半导体专项补贴", "人才奖励", "厂房租金优惠"]
    ),
    "深圳高新区": TechClusterConfig(
        name="深圳高新区",
        region="深圳",
        base_url="http://www.szpark.net",
        policy_urls=[
            "http://www.szpark.net/policy/",
            "http://www.szpark.net/notice/",
            "http://www.szpark.net/news/"
        ],
        focus_industries=["自动驾驶", "半导体", "新材料"],
        special_fields=["自动驾驶补贴", "算力补贴", "人才奖励"]
    ),
    "广州高新区": TechClusterConfig(
        name="广州高新区",
        region="广州",
        base_url="http://www.gzzh.gov.cn",
        policy_urls=[
            "http://www.gzzh.gov.cn/zcfg/",
            "http://www.gzzh.gov.cn/tzgg/",
            "http://www.gzzh.gov.cn/xwzx/"
        ],
        focus_industries=["AI", "生物医药", "新能源"],
        special_fields=["具身智能", "人才奖励", "厂房租金优惠"]
    ),
    "苏州工业园区": TechClusterConfig(
        name="苏州工业园区",
        region="苏州",
        base_url="http://www.sipac.gov.cn",
        policy_urls=[
            "http://www.sipac.gov.cn/zcfg/",
            "http://www.sipac.gov.cn/tzgg/",
            "http://www.sipac.gov.cn/xwzx/"
        ],
        focus_industries=["纳米技术", "生物医药", "人工智能"],
        special_fields=["纳米技术补贴", "人才奖励", "厂房租金优惠"]
    ),
    "合肥高新区": TechClusterConfig(
        name="合肥高新区",
        region="合肥",
        base_url="http://www.hfht.gov.cn",
        policy_urls=[
            "http://www.hfht.gov.cn/zcfg/",
            "http://www.hfht.gov.cn/tzgg/",
            "http://www.hfht.gov.cn/xwzx/"
        ],
        focus_industries=["量子计算", "生物医药", "新能源"],
        special_fields=["量子计算补贴", "算力补贴", "人才奖励"]
    )
}

class ChinaTechClusterCrawlerEngine:
    """中国科技集聚区爬虫引擎"""
    
    def __init__(self):
        self.crawlers = []
        self.policy_cleaner = PolicyCleaner()
        self.is_running = False
        
    def add_cluster_crawler(self, cluster_name: str):
        """添加科技集聚区爬虫"""
        if cluster_name not in CHINA_TECH_CLUSTERS:
            raise ValueError(f"Unknown cluster: {cluster_name}")
        
        cluster_config = CHINA_TECH_CLUSTERS[cluster_name]
        crawler_config = CrawlerConfig(
            name=cluster_name,
            base_url=cluster_config.base_url,
            max_pages=50,
            delay_seconds=3
        )
        
        crawler = ChinaTechClusterCrawler(crawler_config, cluster_config, self.policy_cleaner)
        self.crawlers.append(crawler)
        logger.info(f"Added crawler for {cluster_name}")
    
    async def start_all_crawlers(self):
        """启动所有爬虫"""
        if self.is_running:
            logger.warning("Crawlers are already running")
            return
            
        self.is_running = True
        logger.info("Starting China tech cluster crawler engine...")
        
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
                    logger.error(f"Crawler error: {result}")
                elif result:
                    all_policies.extend(result)
            
            logger.info(f"Total policies crawled: {len(all_policies)}")
            return all_policies
            
        finally:
            # 关闭所有爬虫的会话
            for crawler in self.crawlers:
                await crawler.close_session()
            
            self.is_running = False
    
    async def crawl_and_save(self, output_dir: str = "china_tech_clusters"):
        """爬取并保存数据"""
        output_path = Path(output_dir)
        
        # 启动所有爬虫
        all_policies = await self.start_all_crawlers()
        
        # 保存数据
        for crawler in self.crawlers:
            await crawler.save_crawled_data(output_path / crawler.config.name)
        
        return all_policies

# 使用示例
async def main():
    """主函数示例"""
    # 创建爬虫引擎
    engine = ChinaTechClusterCrawlerEngine()
    
    # 添加主要科技集聚区爬虫
    for cluster_name in ["北京中关村", "上海张江", "深圳高新区", "广州高新区", "苏州工业园区", "合肥高新区"]:
        engine.add_cluster_crawler(cluster_name)
    
    # 开始爬取
    logger.info("Starting China tech cluster crawling...")
    start_time = time.time()
    
    try:
        policies = await engine.crawl_and_save("output/china_tech_clusters")
        
        end_time = time.time()
        logger.info(f"Crawling completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Total policies processed: {len(policies)}")
        
        # 输出统计信息
        stats = {
            "total_policies": len(policies),
            "clusters": list(set([p.location for p in policies])),
            "industries": list(set([p.industry for p in policies])),
            "crawl_time": end_time - start_time
        }
        
        print("\n=== China Tech Cluster Crawling Statistics ===")
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