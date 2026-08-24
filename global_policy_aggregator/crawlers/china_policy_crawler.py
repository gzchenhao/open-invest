"""
China Industrial Policy Crawler
中国本土产业政策定向爬虫，专门采集中国主流硬科技集聚区的招商与产业扶持政策

重点目标：
- 北京中关村
- 上海张江
- 深圳高新区
- 苏州工业园区
- 合肥高新区

采集重点：
- 具身智能/自动驾驶/半导体专项补贴
- 算力补贴
- 厂房租金优惠
- 人才奖励
- 研发人员比例/专利数量要求
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
import pandas as pd

from ..processors.policy_cleaner import PolicyCleaner, StructuredPolicy

logger = logging.getLogger(__name__)

@dataclass
class ChinaTechZone:
    """中国科技园区配置"""
    name: str
    base_url: str
    policy_url: str
    features: List[str]  # 该园区重点产业
    priority: int  # 采集优先级 1-5
    last_updated: str

# 中国主流硬科技集聚区配置
CHINA_TECH_ZONES = [
    ChinaTechZone(
        name="北京中关村",
        base_url="https://www.zpark.com.cn",
        policy_url="https://www.zpark.com.cn/zcqw/",
        features=["具身智能", "自动驾驶", "半导体", "人工智能", "量子计算"],
        priority=5,
        last_updated="2024-01-01"
    ),
    ChinaTechZone(
        name="上海张江",
        base_url="https://www.zjpark.com",
        policy_url="https://www.zjpark.com/zhengce/",
        features=["集成电路", "生物医药", "人工智能", "航空航天"],
        priority=5,
        last_updated="2024-01-01"
    ),
    ChinaTechZone(
        name="深圳高新区",
        base_url="https://www.szhigh-tech.com",
        policy_url="https://www.szhigh-tech.com/zcfg/",
        features=["新一代信息技术", "高端制造", "生物医药", "新能源"],
        priority=5,
        last_updated="2024-01-01"
    ),
    ChinaTechZone(
        name="苏州工业园区",
        base_url="https://www.sipac.com",
        policy_url="https://www.sipac.com/zhengce/",
        features=["纳米技术", "生物医药", "人工智能", "纳米技术"],
        priority=4,
        last_updated="2024-01-01"
    ),
    ChinaTechZone(
        name="合肥高新区",
        base_url="https://www.hfht.gov.cn",
        policy_url="https://www.hfht.gov.cn/zcfg/",
        features=["量子信息", "集成电路", "新能源汽车", "生物医药"],
        priority=4,
        last_updated="2024-01-01"
    )
]

@dataclass
class IndustryIncentive:
    """产业激励政策数据结构"""
    zone_name: str
    policy_title: str
    policy_url: str
    policy_type: str  # 补贴/优惠/奖励/要求
    industry_focus: List[str]
    incentive_amount: Optional[str]
    requirements: Dict[str, Any]
    application_deadline: Optional[str]
    contact_info: Dict[str, str]
    raw_content: str
    crawl_timestamp: str

class ChinaPolicyCrawler:
    """中国产业政策爬虫"""
    
    def __init__(self, policy_cleaner: PolicyCleaner):
        self.cleaner = policy_cleaner
        self.session = None
        self.crawled_data = []
        self.china_specific_keywords = {
            'subsidies': ['补贴', '资助', '资金支持', '专项经费', '扶持资金'],
            'tax_incentives': ['税收优惠', '税收减免', '退税', '税收返还'],
            'rent_discount': ['厂房租金', '办公用房', '场地优惠', '租金减免'],
            'talent_rewards': ['人才奖励', '人才补贴', '安家费', '住房补贴'],
            'rd_requirements': ['研发投入', '研发人员比例', '专利数量', '高新技术企业'],
            'power_subsidy': ['算力补贴', '算力支持', '云计算补贴', '数据中心支持'],
            'auto_industry': ['自动驾驶', '智能网联', '新能源汽车', '具身智能'],
            'semiconductor': ['半导体', '集成电路', '芯片', 'EDA工具'],
            'ai_industry': ['人工智能', '机器学习', '深度学习', '大模型']
        }
        
    async def start_session(self):
        """启动HTTP会话"""
        timeout = aiohttp.ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://www.baidu.com/',
                'Cookie': 'cookie_policy_accepted=true'
            }
        )
        
    async def close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_zone_policies(self, zone: ChinaTechZone) -> List[IndustryIncentive]:
        """获取特定园区的政策数据"""
        logger.info(f"开始采集 {zone.name} 政策数据...")
        
        policies = []
        
        try:
            # 获取政策列表页面
            policy_list_html = await self.fetch_page(zone.policy_url)
            if not policy_list_html:
                logger.warning(f"无法获取 {zone.name} 政策列表页面")
                return policies
            
            # 解析政策列表
            policy_links = self.extract_policy_links(policy_list_html, zone.name)
            
            for link in policy_links:
                try:
                    policy_html = await self.fetch_page(link)
                    if policy_html:
                        policy = await self.parse_policy_content(policy_html, link, zone)
                        if policy:
                            policies.append(policy)
                            logger.info(f"成功采集政策: {policy.policy_title}")
                    
                    # 避免请求过于频繁
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"处理政策链接 {link} 时出错: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"采集 {zone.name} 政策时出错: {e}")
        
        logger.info(f"{zone.name} 采集完成，共获取 {len(policies)} 条政策")
        return policies
    
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
    
    def extract_policy_links(self, html_content: str, zone_name: str) -> List[str]:
        """从政策列表页面提取政策链接"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # 常见的政策链接选择器
        link_selectors = [
            'a[href*="zhengce"]',
            'a[href*="policy"]',
            'a[href*="zc"]',
            'a[href*="通知"]',
            'a[href*="办法"]',
            'a[href*="意见"]',
            'a[href*="规定"]'
        ]
        
        for selector in link_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and not href.startswith('javascript:'):
                    # 转换为完整URL
                    if href.startswith('/'):
                        # 找到对应的base_url
                        zone_config = next((z for z in CHINA_TECH_ZONES if z.name == zone_name), None)
                        if zone_config:
                            href = zone_config.base_url + href
                    
                    if href not in links:
                        links.append(href)
        
        # 如果没有找到足够的链接，尝试其他方法
        if len(links) < 5:
            logger.warning(f"在 {zone_name} 只找到 {len(links)} 个政策链接，尝试其他方法...")
            # 查找包含政策关键词的链接
            text_elements = soup.find_all(['a'], text=re.compile(r'补贴|政策|扶持|资助|通知'))
            for element in text_elements:
                href = element.get('href')
                if href and href not in links:
                    links.append(href)
        
        return links[:20]  # 限制最多20个链接
    
    async def parse_policy_content(self, html_content: str, policy_url: str, zone: ChinaTechZone) -> Optional[IndustryIncentive]:
        """解析政策内容"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取政策标题
            title = self.extract_policy_title(soup)
            if not title:
                return None
            
            # 提取政策正文
            content = self.extract_policy_content_text(soup)
            
            # 分析政策类型和激励内容
            policy_analysis = self.analyze_policy_content(content, zone.name)
            
            # 构建政策数据结构
            policy = IndustryIncentive(
                zone_name=zone.name,
                policy_title=title,
                policy_url=policy_url,
                policy_type=policy_analysis['policy_type'],
                industry_focus=policy_analysis['industry_focus'],
                incentive_amount=policy_analysis['incentive_amount'],
                requirements=policy_analysis['requirements'],
                application_deadline=policy_analysis['application_deadline'],
                contact_info=policy_analysis['contact_info'],
                raw_content=content,
                crawl_timestamp=datetime.now().isoformat()
            )
            
            return policy
            
        except Exception as e:
            logger.error(f"解析政策内容时出错: {e}")
            return None
    
    def extract_policy_title(self, soup: BeautifulSoup) -> Optional[str]:
        """提取政策标题"""
        # 常见的标题选择器
        title_selectors = [
            'h1',
            'h2',
            'h3',
            '.title',
            '.policy-title',
            '.article-title',
            '[class*="title"]'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if len(title) > 5 and len(title) < 200:  # 合理的标题长度
                    return title
        
        # 如果没有找到，尝试从页面标题提取
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        return None
    
    def extract_policy_content_text(self, soup: BeautifulSoup) -> str:
        """提取政策正文内容"""
        # 移除不需要的元素
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'menu']):
            element.decompose()
        
        # 常见的正文选择器
        content_selectors = [
            '.content',
            '.article-content',
            '.policy-content',
            '.main-content',
            '.text-content',
            '[class*="content"]',
            'div[class*="text"]',
            'div[class*="article"]'
        ]
        
        content = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if len(text) > 100:  # 只取有意义的文本内容
                    content += text + "\n"
        
        # 如果没有找到，取body内容
        if not content:
            body = soup.find('body')
            if body:
                content = body.get_text(strip=True)
        
        return content[:10000]  # 限制内容长度
    
    def analyze_policy_content(self, content: str, zone_name: str) -> Dict[str, Any]:
        """分析政策内容，提取关键信息"""
        analysis = {
            'policy_type': 'other',
            'industry_focus': [],
            'incentive_amount': None,
            'requirements': {},
            'application_deadline': None,
            'contact_info': {}
        }
        
        content_lower = content.lower()
        
        # 识别政策类型
        if any(keyword in content for keyword in self.china_specific_keywords['subsidies']):
            analysis['policy_type'] = 'subsidy'
        elif any(keyword in content for keyword in self.china_specific_keywords['tax_incentives']):
            analysis['policy_type'] = 'tax_incentive'
        elif any(keyword in content for keyword in self.china_specific_keywords['rent_discount']):
            analysis['policy_type'] = 'rent_discount'
        elif any(keyword in content for keyword in self.china_specific_keywords['talent_rewards']):
            analysis['policy_type'] = 'talent_reward'
        
        # 识别产业重点
        for industry, keywords in self.china_specific_keywords.items():
            if industry in ['auto_industry', 'semiconductor', 'ai_industry', 'power_subsidy']:
                for keyword in keywords:
                    if keyword in content:
                        analysis['industry_focus'].append(keyword)
        
        # 提取激励金额
        amount_patterns = [
            r'(\d+(?:\.\d+)?)\s*万元',
            r'(\d+(?:\.\d+)?)\s*亿元',
            r'(\d+(?:\.\d+)?)\s*千万',
            r'补贴\s*(\d+(?:\.\d+)?)\s*万元',
            r'资助\s*(\d+(?:\.\d+)?)\s*万元'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, content)
            if match:
                analysis['incentive_amount'] = match.group(1)
                break
        
        # 提取要求
        requirement_patterns = {
            'rd_ratio': r'研发人员比例\s*[：:]\s*(\d+(?:\.\d+)?)%',
            'patent_count': r'专利数量\s*[：:]\s*(\d+)',
            'rd_investment': r'研发投入\s*[：:]\s*(\d+(?:\.\d+)?)%',
            'company_size': r'企业规模\s*[：:]\s*(\d+)人'
        }
        
        for req_type, pattern in requirement_patterns.items():
            match = re.search(pattern, content)
            if match:
                analysis['requirements'][req_type] = match.group(1)
        
        # 提取申请截止日期
        deadline_patterns = [
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            r'截止日期\s*[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)',
            r'申请截止\s*[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, content)
            if match:
                analysis['application_deadline'] = match.group(1)
                break
        
        # 提取联系方式
        contact_patterns = {
            'phone': r'联系电话\s*[：:]\s*(\d{3,4}-\d{7,8}|\d{11})',
            'email': r'邮箱\s*[：:]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'address': r'地址\s*[：:]\s*([^\n]+)'
        }
        
        for contact_type, pattern in contact_patterns.items():
            match = re.search(pattern, content)
            if match:
                analysis['contact_info'][contact_type] = match.group(1)
        
        return analysis
    
    async def crawl_all_zones(self) -> List[IndustryIncentive]:
        """爬取所有中国科技园区的政策"""
        logger.info("开始中国产业政策采集...")
        
        all_policies = []
        
        await self.start_session()
        
        try:
            # 按优先级排序
            sorted_zones = sorted(CHINA_TECH_ZONES, key=lambda x: x.priority, reverse=True)
            
            for zone in sorted_zones:
                logger.info(f"正在采集 {zone.name} (优先级: {zone.priority})...")
                
                zone_policies = await self.fetch_zone_policies(zone)
                all_policies.extend(zone_policies)
                
                # 间隔时间，避免过于频繁
                await asyncio.sleep(3)
        
        finally:
            await self.close_session()
        
        logger.info(f"中国产业政策采集完成，共获取 {len(all_policies)} 条政策")
        self.crawled_data = all_policies
        
        return all_policies
    
    def save_to_json(self, policies: List[IndustryIncentive], filename: str = "china_industrial_policies.json"):
        """保存政策数据到JSON文件"""
        data = []
        for policy in policies:
            data.append({
                'zone_name': policy.zone_name,
                'policy_title': policy.policy_title,
                'policy_url': policy.policy_url,
                'policy_type': policy.policy_type,
                'industry_focus': policy.industry_focus,
                'incentive_amount': policy.incentive_amount,
                'requirements': policy.requirements,
                'application_deadline': policy.application_deadline,
                'contact_info': policy.contact_info,
                'raw_content': policy.raw_content,
                'crawl_timestamp': policy.crawl_timestamp
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"政策数据已保存到 {filename}")
    
    def save_to_csv(self, policies: List[IndustryIncentive], filename: str = "china_industrial_policies.csv"):
        """保存政策数据到CSV文件"""
        data = []
        for policy in policies:
            data.append({
                'zone_name': policy.zone_name,
                'policy_title': policy.policy_title,
                'policy_type': policy.policy_type,
                'industry_focus': ','.join(policy.industry_focus),
                'incentive_amount': policy.incentive_amount,
                'application_deadline': policy.application_deadline,
                'crawl_timestamp': policy.crawl_timestamp
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"政策数据已保存到 {filename}")

# 使用示例
async def main():
    """主函数"""
    from ..processors.policy_cleaner import PolicyCleaner
    
    cleaner = PolicyCleaner()
    crawler = ChinaPolicyCrawler(cleaner)
    
    # 爬取所有政策
    policies = await crawler.crawl_all_zones()
    
    # 保存数据
    crawler.save_to_json(policies)
    crawler.save_to_csv(policies)
    
    print(f"成功采集 {len(policies)} 条中国产业政策")

if __name__ == "__main__":
    asyncio.run(main())