"""
Global Policy Crawler Engine
全球政府政策情报爬虫引擎，用于收集和清洗全球各地的政府招商政策
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

logger = logging.getLogger(__name__)

@dataclass
class CrawlerConfig:
    """爬虫配置"""
    name: str
    base_url: str
    max_pages: int = 100
    delay_seconds: int = 2
    timeout_seconds: int = 30
    retry_attempts: int = 3
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

@dataclass
class CrawledPolicy:
    """爬取的政策数据"""
    policy_id: str
    source_name: str
    source_url: str
    raw_content: str
    extracted_text: str
    metadata: Dict[str, Any]
    crawl_timestamp: str

class BasePolicyCrawler:
    """政策爬虫基类"""
    
    def __init__(self, config: CrawlerConfig, policy_cleaner: PolicyCleaner):
        self.config = config
        self.cleaner = policy_cleaner
        self.session = None
        self.is_running = False
        self.crawled_policies = []
        
    async def start_session(self):
        """启动HTTP会话"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self.config.headers
        )
        
    async def close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """获取页面内容"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    async def crawl_policies(self) -> List[CrawledPolicy]:
        """爬取政策数据 - 子类需要实现"""
        raise NotImplementedError("Subclasses must implement crawl_policies method")
    
    async def process_policy(self, raw_content: str, source_url: str, source_name: str) -> Optional[StructuredPolicy]:
        """处理单个政策"""
        try:
            # 清洗政策文本
            structured_policy = self.cleaner.clean_policy_text(raw_content, source_url)
            
            # 创建爬取记录
            crawled_policy = CrawledPolicy(
                policy_id=structured_policy.policy_id,
                source_name=source_name,
                source_url=source_url,
                raw_content=raw_content,
                extracted_text=structured_policy.description,
                metadata=structured_policy.metadata,
                crawl_timestamp=datetime.now().isoformat()
            )
            
            self.crawled_policies.append(crawled_policy)
            return structured_policy
            
        except Exception as e:
            logger.error(f"Error processing policy from {source_url}: {e}")
            return None
    
    async def save_crawled_data(self, output_dir: Path):
        """保存爬取的数据"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存原始数据
        raw_data_file = output_dir / "crawled_policies.json"
        with open(raw_data_file, 'w', encoding='utf-8') as f:
            json.dump([{
                'policy_id': p.policy_id,
                'source_name': p.source_name,
                'source_url': p.source_url,
                'raw_content': p.raw_content,
                'extracted_text': p.extracted_text,
                'metadata': p.metadata,
                'crawl_timestamp': p.crawl_timestamp
            } for p in self.crawled_policies], f, indent=2, ensure_ascii=False)
        
        # 保存结构化数据
        structured_data_file = output_dir / "structured_policies.json"
        structured_policies = []
        for crawled in self.crawled_policies:
            try:
                structured = self.cleaner.clean_policy_text(crawled.raw_content, crawled.source_url)
                structured_policies.append({
                    'policy_id': structured.policy_id,
                    'location': structured.location,
                    'country': structured.country,
                    'region': structured.region,
                    'industry': structured.industry,
                    'policy_type': structured.policy_type,
                    'title': structured.title,
                    'description': structured.description,
                    'incentives': structured.incentives,
                    'requirements': structured.requirements,
                    'compliance_standards': structured.compliance_standards,
                    'metadata': structured.metadata
                })
            except Exception as e:
                logger.error(f"Error reprocessing policy {crawled.policy_id}: {e}")
        
        with open(structured_data_file, 'w', encoding='utf-8') as f:
            json.dump(structured_policies, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.crawled_policies)} crawled policies to {output_dir}")

class ShanghaiPolicyCrawler(BasePolicyCrawler):
    """上海政策爬虫"""
    
    async def crawl_policies(self) -> List[CrawledPolicy]:
        """爬取上海政策"""
        policies = []
        
        # 示例：张江科学城政策页面
        urls = [
            "http://www.zjpark.com.cn/policy/",
            "http://www.zjpark.com.cn/notice/",
            "http://www.zjpark.com.cn/news/"
        ]
        
        for url in urls:
            logger.info(f"Crawling Shanghai policies from: {url}")
            
            # 这里应该是实际的网页爬取逻辑
            # 为了演示，我们使用本地数据
            if "zjpark.com.cn" in url:
                local_file = Path(__file__).parent.parent / "data" / "raw_policies" / "shanghai_ai_policy_2024.txt"
                if local_file.exists():
                    with open(local_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    structured_policy = await self.process_policy(content, str(local_file), "Shanghai Zhangjiang")
                    if structured_policy:
                        policies.append(structured_policy)
                
                # 模拟延迟
                await asyncio.sleep(self.config.delay_seconds)
        
        return policies

class SiliconValleyPolicyCrawler(BasePolicyCrawler):
    """硅谷政策爬虫"""
    
    async def crawl_policies(self) -> List[CrawledPolicy]:
        """爬取硅谷政策"""
        policies = []
        
        # 示例：硅谷量子计算政策
        local_file = Path(__file__).parent.parent / "data" / "raw_policies" / "silicon_valley_quantum_policy_2024.txt"
        if local_file.exists():
            with open(local_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            structured_policy = await self.process_policy(content, str(local_file), "Silicon Valley")
            if structured_policy:
                policies.append(structured_policy)
        
        return policies

class EUPolicyCrawler(BasePolicyCrawler):
    """欧盟政策爬虫"""
    
    async def crawl_policies(self) -> List[CrawledPolicy]:
        """爬取欧盟政策"""
        policies = []
        
        # 示例：欧盟AI法案
        local_file = Path(__file__).parent.parent / "data" / "raw_policies" / "eu_ai_act_compliance_2024.txt"
        if local_file.exists():
            with open(local_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            structured_policy = await self.process_policy(content, str(local_file), "European Union")
            if structured_policy:
                policies.append(structured_policy)
        
        return policies

class GlobalPolicyCrawlerEngine:
    """全球政策爬虫引擎"""
    
    def __init__(self):
        self.crawlers = []
        self.policy_cleaner = PolicyCleaner()
        self.is_running = False
        
    def add_crawler(self, crawler: BasePolicyCrawler):
        """添加爬虫"""
        self.crawlers.append(crawler)
        
    async def start_all_crawlers(self):
        """启动所有爬虫"""
        if self.is_running:
            logger.warning("Crawlers are already running")
            return
            
        self.is_running = True
        logger.info("Starting global policy crawler engine...")
        
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
    
    async def crawl_and_save(self, output_dir: str = "crawled_data"):
        """爬取并保存数据"""
        output_path = Path(output_dir)
        
        # 启动所有爬虫
        all_policies = await self.start_all_crawlers()
        
        # 保存数据
        for crawler in self.crawlers:
            await crawler.save_crawled_data(output_path / crawler.config.name.lower())
        
        return all_policies

# 使用示例
async def main():
    """主函数示例"""
    # 创建爬虫引擎
    engine = GlobalPolicyCrawlerEngine()
    
    # 添加各个地区的爬虫
    shanghai_config = CrawlerConfig(
        name="Shanghai",
        base_url="http://www.zjpark.com.cn",
        max_pages=50,
        delay_seconds=3
    )
    
    sv_config = CrawlerConfig(
        name="SiliconValley",
        base_url="https://www.siliconvalley.org",
        max_pages=30,
        delay_seconds=2
    )
    
    eu_config = CrawlerConfig(
        name="EuropeanUnion",
        base_url="https://eur-lex.europa.eu",
        max_pages=100,
        delay_seconds=2
    )
    
    # 创建爬虫实例
    shanghai_crawler = ShanghaiPolicyCrawler(shanghai_config, engine.policy_cleaner)
    sv_crawler = SiliconValleyPolicyCrawler(sv_config, engine.policy_cleaner)
    eu_crawler = EUPolicyCrawler(eu_config, engine.policy_cleaner)
    
    # 添加到引擎
    engine.add_crawler(shanghai_crawler)
    engine.add_crawler(sv_crawler)
    engine.add_crawler(eu_crawler)
    
    # 开始爬取
    logger.info("Starting global policy crawling...")
    start_time = time.time()
    
    try:
        policies = await engine.crawl_and_save("output/crawled_policies")
        
        end_time = time.time()
        logger.info(f"Crawling completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Total policies processed: {len(policies)}")
        
        # 输出统计信息
        stats = {
            "total_policies": len(policies),
            "sources": list(set([p.location for p in policies])),
            "industries": list(set([p.industry for p in policies])),
            "crawl_time": end_time - start_time
        }
        
        print("\n=== Crawling Statistics ===")
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