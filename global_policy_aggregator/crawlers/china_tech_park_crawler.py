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

from ..processors.policy_cleaner import PolicyCleaner, StructuredPolicy
from .policy_crawler_engine import BasePolicyCrawler, CrawlerConfig, CrawledPolicy

logger = logging.getLogger(__name__)

@dataclass
class ChinaTechParkConfig:
    """中国科技园区配置"""
    name: str
    region: str
    base_url: str
    policy_urls: List[str]
    focus_industries: List[str]
    special_fields: List[str]

class ChinaTechParkCrawler(BasePolicyCrawler):
    """中国主流硬科技集聚区定向爬虫"""
    
    def __init__(self, config: CrawlerConfig, park_config: ChinaTechParkConfig, policy_cleaner: PolicyCleaner):
        super().__init__(config, policy_cleaner)
        self.park_config = park_config
        self.focus_keywords = [
            "具身智能", "自动驾驶", "半导体", "量子计算", "人工智能", "区块链",
            "生物医药", "高端装备", "新材料", "新能源", "金融科技", "纳米技术",
            "算力补贴", "厂房租金", "人才奖励", "研发补贴", "专项基金"
        ]
        
    async def crawl_policies(self) -> List[CrawledPolicy]:
        """爬取中国科技园区政策"""
        policies = []
        
        logger.info(f"开始爬取 {self.park_config.name} 政策数据...")
        
        # 遍历所有政策页面
        for url in self.park_config.policy_urls:
            logger.info(f"爬取政策页面: {url}")
            
            try:
                # 获取页面内容
                content = await self.fetch_page(url)
                if not content:
                    logger.warning(f"无法获取页面内容: {url}")
                    continue
                
                # 解析页面内容
                extracted_policies = await self.parse_policy_page(content, url)
                policies.extend(extracted_policies)
                
                # 模拟延迟
                await asyncio.sleep(self.config.delay_seconds)
                
            except Exception as e:
                logger.error(f"爬取页面 {url} 时发生错误: {e}")
                continue
        
        logger.info(f"从 {self.park_config.name} 爬取到 {len(policies)} 条政策")
        return policies
    
    async def parse_policy_page(self, content: str, source_url: str) -> List[CrawledPolicy]:
        """解析政策页面，提取政策信息"""
        policies = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 查找政策相关元素
            policy_elements = self.find_policy_elements(soup)
            
            for element in policy_elements:
                # 提取政策文本
                policy_text = self.extract_policy_text(element)
                
                # 检查是否包含重点关注字段
                if self.is_relevant_policy(policy_text):
                    # 处理政策
                    structured_policy = await self.process_policy(policy_text, source_url, self.park_config.name)
                    if structured_policy:
                        # 创建爬取记录
                        crawled_policy = CrawledPolicy(
                            policy_id=structured_policy.policy_id,
                            source_name=self.park_config.name,
                            source_url=source_url,
                            raw_content=policy_text,
                            extracted_text=structured_policy.description,
                            metadata=structured_policy.metadata,
                            crawl_timestamp=datetime.now().isoformat()
                        )
                        policies.append(crawled_policy)
                        
        except Exception as e:
            logger.error(f"解析政策页面时发生错误: {e}")
        
        return policies
    
    def find_policy_elements(self, soup: BeautifulSoup) -> List[Any]:
        """查找政策相关元素"""
        policy_elements = []
        
        # 查找可能的政策标题元素
        selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            '.title', '.policy-title', '.news-title',
            '.article-title', '.document-title',
            '[class*="policy"]', '[class*="notice"]', '[class*="announcement"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                # 检查文本内容是否包含政策相关关键词
                text = element.get_text(strip=True)
                if any(keyword in text for keyword in ['政策', '通知', '公告', '办法', '规定', '实施细则']):
                    policy_elements.append(element)
        
        return policy_elements
    
    def extract_policy_text(self, element: Any) -> str:
        """从元素中提取政策文本"""
        try:
            # 如果是元素，获取其文本内容
            if hasattr(element, 'get_text'):
                text = element.get_text(separator=' ', strip=True)
            else:
                text = str(element)
            
            # 清理文本
            text = re.sub(r'\s+', ' ', text)  # 合并多个空格
            text = re.sub(r'\n+', '\n', text)  # 合并多个换行
            
            return text
            
        except Exception as e:
            logger.error(f"提取政策文本时发生错误: {e}")
            return ""
    
    def is_relevant_policy(self, text: str) -> bool:
        """检查政策是否包含重点关注字段"""
        text_lower = text.lower()
        
        # 检查是否包含重点关注行业
        industry_keywords = ['人工智能', 'ai', '半导体', '自动驾驶', '量子计算', '区块链', 
                           '生物医药', '高端装备', '新材料', '新能源', '金融科技', '纳米技术']
        
        # 检查是否包含重点关注政策类型
        policy_keywords = ['补贴', '奖励', '扶持', '基金', '优惠', '支持', '资助']
        
        # 检查是否包含具体政策内容
        content_keywords = ['研发', '人才', '厂房', '租金', '算力', '专利', '设备', '税收']
        
        # 检查是否匹配任一类别
        return (
            any(keyword in text_lower for keyword in industry_keywords) or
            any(keyword in text_lower for keyword in policy_keywords) or
            any(keyword in text_lower for keyword in content_keywords)
        )
    
    async def process_specific_policy_types(self, policy_text: str) -> Dict[str, Any]:
        """处理特定类型的政策，提取关键信息"""
        result = {
            'subsidies': [],
            'rental_benefits': [],
            'talent_rewards': [],
            'rd_support': [],
            'patent_requirements': [],
            'talent_ratio_requirements': []
        }
        
        try:
            # 提取补贴信息
            subsidy_patterns = [
                r'补贴\s*[:：]\s*(\d+万|\d+万元|\d+元)',
                r'扶持\s*[:：]\s*(\d+万|\d+万元|\d+元)',
                r'资助\s*[:：]\s*(\d+万|\d+万元|\d+元)',
                r'最高\s*(\d+万|\d+万元|\d+元)'
            ]
            
            for pattern in subsidy_patterns:
                matches = re.findall(pattern, policy_text)
                for match in matches:
                    result['subsidies'].append(match)
            
            # 提取厂房租金优惠
            rental_patterns = [
                r'厂房\s*租金\s*(优惠|减免|补贴)',
                r'办公\s*场地\s*(优惠|减免|补贴)',
                r'租金\s*(减免|优惠|补贴)',
                r'前\s*(\d+)\s*年\s*(免租金|半价)'
            ]
            
            for pattern in rental_patterns:
                matches = re.findall(pattern, policy_text)
                result['rental_benefits'].extend(matches)
            
            # 提取人才奖励
            talent_patterns = [
                r'人才\s*奖励\s*[:：]\s*(\d+万|\d+万元|\d+元)',
                r'高端\s*人才\s*奖励\s*[:：]\s*(\d+万|\d+万元|\d+元)',
                r'研发\s*人员\s*奖励\s*[:：]\s*(\d+万|\d+万元|\d+元)',
                r'每人\s*每年\s*(\d+万|\d+万元|\d+元)'
            ]
            
            for pattern in talent_patterns:
                matches = re.findall(pattern, policy_text)
                result['talent_rewards'].extend(matches)
            
            # 提取研发支持
            rd_patterns = [
                r'研发\s*投入\s*补贴\s*[:：]\s*(\d+万|\d+万元|\d+元)',
                r'研发\s*费用\s*(补贴|资助)',
                r'技术\s*研发\s*支持\s*[:：]\s*(\d+万|\d+万元|\d+元)',
                r'设备\s*购置\s*补贴\s*[:：]\s*(\d+万|\d+万元|\d+元)'
            ]
            
            for pattern in rd_patterns:
                matches = re.findall(pattern, policy_text)
                result['rd_support'].extend(matches)
            
            # 提取专利数量要求
            patent_patterns = [
                r'专利\s*数量\s*[:：]\s*(至少|不少于)\s*(\d+)\s*(项|个)',
                r'至少\s*(\d+)\s*项\s*专利',
                r'拥有\s*(\d+)\s*项\s*以上\s*专利',
                r'专利\s*(\d+)\s*项'
            ]
            
            for pattern in patent_patterns:
                matches = re.findall(pattern, policy_text)
                result['patent_requirements'].extend(matches)
            
            # 提取研发人员比例要求
            ratio_patterns = [
                r'研发\s*人员\s*比例\s*[:：]\s*(至少|不少于|不低于)\s*(\d+)%',
                r'研发\s*人员\s*占比\s*[:：]\s*(至少|不少于|不低于)\s*(\d+)%',
                r'技术\s*人员\s*比例\s*[:：]\s*(至少|不少于|不低于)\s*(\d+)%',
                r'不低于\s*(\d+)%\s*研发\s*人员'
            ]
            
            for pattern in ratio_patterns:
                matches = re.findall(pattern, policy_text)
                result['talent_ratio_requirements'].extend(matches)
                
        except Exception as e:
            logger.error(f"处理特定政策类型时发生错误: {e}")
        
        return result

class ChinaTechParkCrawlerEngine:
    """中国科技园区爬虫引擎"""
    
    def __init__(self):
        self.crawlers = []
        self.policy_cleaner = PolicyCleaner()
        self.is_running = False
        
        # 定义中国主流硬科技集聚区配置
        self.park_configs = [
            ChinaTechParkConfig(
                name="北京中关村",
                region="北京",
                base_url="http://www.zpark.com.cn",
                policy_urls=[
                    "http://www.zpark.com.cn/policy/",
                    "http://www.zpark.com.cn/notice/",
                    "http://www.zpark.com.cn/news/"
                ],
                focus_industries=["AI", "半导体", "量子计算", "生物医药"],
                special_fields=["具身智能", "自动驾驶", "算力补贴", "人才奖励"]
            ),
            ChinaTechParkConfig(
                name="上海张江",
                region="上海",
                base_url="http://www.zjpark.com.cn",
                policy_urls=[
                    "http://www.zjpark.com.cn/policy/",
                    "http://www.zjpark.com.cn/notice/",
                    "http://www.zjpark.com.cn/news/"
                ],
                focus_industries=["半导体", "AI", "生物医药", "新材料"],
                special_fields=["算力补贴", "厂房租金", "研发补贴", "设备购置"]
            ),
            ChinaTechParkConfig(
                name="深圳高新区",
                region="深圳",
                base_url="http://www.szpark.com",
                policy_urls=[
                    "http://www.szpark.com/policy/",
                    "http://www.szpark.com/notice/",
                    "http://www.szpark.com/news/"
                ],
                focus_industries=["AI", "自动驾驶", "半导体", "高端装备"],
                special_fields=["自动驾驶补贴", "人才奖励", "研发支持", "产业化支持"]
            ),
            ChinaTechParkConfig(
                name="苏州工业园区",
                region="苏州",
                base_url="http://www.sipac.com.cn",
                policy_urls=[
                    "http://www.sipac.com.cn/policy/",
                    "http://www.sipac.com.cn/notice/",
                    "http://www.sipac.com.cn/news/"
                ],
                focus_industries=["纳米技术", "生物医药", "AI", "新材料"],
                special_fields=["纳米技术专项", "厂房优惠", "人才引进", "国际合作"]
            ),
            ChinaTechParkConfig(
                name="合肥高新区",
                region="合肥",
                base_url="http://www.hfep.gov.cn",
                policy_urls=[
                    "http://www.hfep.gov.cn/policy/",
                    "http://www.hfep.gov.cn/notice/",
                    "http://www.hfep.gov.cn/news/"
                ],
                focus_industries=["量子计算", "AI", "生物医药", "新能源"],
                special_fields=["量子计算专项", "算力支持", "研发补贴", "团队建设"]
            ),
            # 广州所有行政区域
            ChinaTechParkConfig(
                name="广州天河区",
                region="广州",
                base_url="http://www.thnet.gov.cn",
                policy_urls=[
                    "http://www.thnet.gov.cn/policy/",
                    "http://www.thnet.gov.cn/notice/",
                    "http://www.thnet.gov.cn/news/"
                ],
                focus_industries=["AI", "金融科技", "生物医药", "新材料"],
                special_fields=["AI专项", "金融科技", "人才奖励", "场地支持"]
            ),
            ChinaTechParkConfig(
                name="广州黄埔区",
                region="广州",
                base_url="http://www.hp.gov.cn",
                policy_urls=[
                    "http://www.hp.gov.cn/policy/",
                    "http://www.hp.gov.cn/notice/",
                    "http://www.hp.gov.cn/news/"
                ],
                focus_industries=["自动驾驶", "半导体", "高端装备", "新能源"],
                special_fields=["自动驾驶补贴", "半导体专项", "研发支持", "产业化"]
            ),
            ChinaTechParkConfig(
                name="广州番禺区",
                region="广州",
                base_url="http://www.panyu.gov.cn",
                policy_urls=[
                    "http://www.panyu.gov.cn/policy/",
                    "http://www.panyu.gov.cn/notice/",
                    "http://www.panyu.gov.cn/news/"
                ],
                focus_industries=["AI", "区块链", "生物医药", "新材料"],
                special_fields=["AI创新", "区块链专项", "人才引进", "研发补贴"]
            ),
            ChinaTechParkConfig(
                name="广州白云区",
                region="广州",
                base_url="http://www.baiyun.gov.cn",
                policy_urls=[
                    "http://www.baiyun.gov.cn/policy/",
                    "http://www.baiyun.gov.cn/notice/",
                    "http://www.baiyun.gov.cn/news/"
                ],
                focus_industries=["高端装备", "新材料", "新能源", "AI"],
                special_fields=["装备制造", "新材料研发", "新能源支持", "技术改造"]
            ),
            ChinaTechParkConfig(
                name="广州南沙区",
                region="广州",
                base_url="http://www.nansha.gov.cn",
                policy_urls=[
                    "http://www.nansha.gov.cn/policy/",
                    "http://www.nansha.gov.cn/notice/",
                    "http://www.nansha.gov.cn/news/"
                ],
                focus_industries=["AI", "生物医药", "新能源", "金融科技"],
                special_fields=["AI+", "生物医药专项", "绿色能源", "金融创新"]
            )
        ]
    
    def add_crawler(self, crawler: ChinaTechParkCrawler):
        """添加爬虫"""
        self.crawlers.append(crawler)
        
    async def start_all_crawlers(self):
        """启动所有爬虫"""
        if self.is_running:
            logger.warning("Crawlers are already running")
            return
            
        self.is_running = True
        logger.info("启动中国科技园区政策爬虫引擎...")
        
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
            
            logger.info(f"总共爬取到 {len(all_policies)} 条中国科技园区政策")
            return all_policies
            
        finally:
            # 关闭所有爬虫的会话
            for crawler in self.crawlers:
                await crawler.close_session()
            
            self.is_running = False
    
    async def crawl_and_save(self, output_dir: str = "china_tech_park_policies"):
        """爬取并保存数据"""
        output_path = Path(output_dir)
        
        # 启动所有爬虫
        all_policies = await self.start_all_crawlers()
        
        # 保存数据
        for crawler in self.crawlers:
            await crawler.save_crawled_data(output_path / crawler.park_config.name)
        
        return all_policies
    
    def create_all_crawlers(self):
        """创建所有科技园区的爬虫"""
        for park_config in self.park_configs:
            crawler_config = CrawlerConfig(
                name=park_config.name,
                base_url=park_config.base_url,
                max_pages=100,
                delay_seconds=2
            )
            
            crawler = ChinaTechParkCrawler(crawler_config, park_config, self.policy_cleaner)
            self.add_crawler(crawler)

# 使用示例
async def main():
    """主函数示例"""
    # 创建爬虫引擎
    engine = ChinaTechParkCrawlerEngine()
    
    # 创建所有爬虫
    engine.create_all_crawlers()
    
    # 开始爬取
    logger.info("开始中国科技园区政策爬取...")
    start_time = time.time()
    
    try:
        policies = await engine.crawl_and_save("output/china_tech_park_policies")
        
        end_time = time.time()
        logger.info(f"爬取完成，耗时 {end_time - start_time:.2f} 秒")
        logger.info(f"总共处理 {len(policies)} 条政策")
        
        # 输出统计信息
        stats = {
            "total_policies": len(policies),
            "regions": list(set([p.metadata.get('region', 'Unknown') for p in policies])),
            "industries": list(set([p.metadata.get('industry', 'Unknown') for p in policies])),
            "crawl_time": end_time - start_time,
            "parks": [config.name for config in engine.park_configs]
        }
        
        print("\n=== 中国科技园区政策爬取统计 ===")
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