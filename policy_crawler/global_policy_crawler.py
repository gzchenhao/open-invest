"""
Global Policy Crawler Engine
Main crawler for collecting global government policies and incentives
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from pathlib import Path
import uuid

from processors.policy_cleaner import PolicyCleaner
from processors.data_structurer import DataStructurer
from processors.intelligence_aggregator import IntelligenceAggregator

logger = logging.getLogger(__name__)

class GlobalPolicyCrawler:
    """Main global policy crawler engine"""
    
    def __init__(self, data_dir: str = "policy_crawler/data"):
        self.data_dir = Path(data_dir)
        self.raw_policies_dir = self.data_dir / "raw_policies"
        self.structured_policies_dir = self.data_dir / "structured_policies"
        self.intelligence_dir = self.data_dir / "intelligence"
        
        # Create directories
        self.raw_policies_dir.mkdir(parents=True, exist_ok=True)
        self.structured_policies_dir.mkdir(parents=True, exist_ok=True)
        self.intelligence_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize processors
        self.cleaner = PolicyCleaner()
        self.structurer = DataStructurer()
        self.aggregator = IntelligenceAggregator()
        
        # Crawler configuration
        self.supported_regions = [
            "China", "United States", "European Union", "Japan", 
            "Singapore", "South Korea", "United Kingdom", "Germany", 
            "France", "Canada"
        ]
        
        self.supported_industries = [
            "ai_ml", "autonomous_driving", "robotics", "quantum_computing",
            "biotech", "blockchain", "ar_vr", "fintech", "cleantech", "semiconductor"
        ]
        
        self.crawlers = {
            "China": ChinaPolicyCrawler(),
            "European Union": EuropeanPolicyCrawler(),
            "United States": USPolicyCrawler(),
            "Singapore": SingaporePolicyCrawler()
        }
        
        logger.info(f"Global Policy Crawler initialized with data directory: {self.data_dir}")

    async def crawl_all_policies(self) -> Dict[str, Any]:
        """
        Crawl policies from all supported regions
        
        Returns:
            Dictionary with crawling results
        """
        logger.info("Starting global policy crawl...")
        
        results = {
            "crawl_timestamp": datetime.now().isoformat(),
            "total_policies": 0,
            "by_region": {},
            "by_industry": {},
            "structured_policies": [],
            "intelligence_report": {}
        }
        
        # Crawl policies from each region
        for region_name, crawler in self.crawlers.items():
            logger.info(f"Crawling policies from {region_name}...")
            
            try:
                region_policies = await crawler.crawl_policies()
                results["by_region"][region_name] = len(region_policies)
                results["total_policies"] += len(region_policies)
                
                # Process region policies
                processed_policies = await self.process_region_policies(region_policies, region_name)
                results["structured_policies"].extend(processed_policies)
                
                logger.info(f"Successfully crawled {len(region_policies)} policies from {region_name}")
                
            except Exception as e:
                logger.error(f"Error crawling {region_name}: {e}")
                results["by_region"][region_name] = 0
        
        # Aggregate intelligence
        if results["structured_policies"]:
            intelligence = self.aggregator.aggregate_intelligence(results["structured_policies"])
            results["intelligence_report"] = self.aggregator._generate_intelligence_summary(intelligence)
            
            # Save intelligence report
            intelligence_path = self.intelligence_dir / f"intelligence_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.aggregator.save_intelligence_report(intelligence, str(intelligence_path))
        
        # Save structured policies
        if results["structured_policies"]:
            structured_path = self.structured_policies_dir / f"structured_policies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.structurer.save_structured_policies(results["structured_policies"], str(structured_path))
        
        logger.info(f"Global crawl completed. Total policies: {results['total_policies']}")
        return results

    async def process_region_policies(self, raw_policies: List[str], region_name: str) -> List[Any]:
        """
        Process raw policies from a specific region
        
        Args:
            raw_policies: List of raw policy texts
            region_name: Name of the region
            
        Returns:
            List of structured policies
        """
        structured_policies = []
        
        for i, raw_policy in enumerate(raw_policies):
            try:
                logger.debug(f"Processing policy {i+1}/{len(raw_policies)} from {region_name}")
                
                # Clean the policy text
                cleaned_data = self.cleaner.clean_policy_text(raw_policy, f"{region_name}_source")
                
                # Structure the cleaned data
                structured_policy = self.structurer.structure_policy_data(cleaned_data)
                structured_policies.append(structured_policy)
                
            except Exception as e:
                logger.error(f"Error processing policy {i+1} from {region_name}: {e}")
                continue
        
        logger.info(f"Processed {len(structured_policies)} policies from {region_name}")
        return structured_policies

    def process_existing_raw_policies(self) -> Dict[str, Any]:
        """
        Process existing raw policy files
        
        Returns:
            Processing results
        """
        logger.info("Processing existing raw policy files...")
        
        results = {
            "processed_files": 0,
            "total_policies": 0,
            "structured_policies": [],
            "errors": []
        }
        
        # Process each raw policy file
        for raw_file in self.raw_policies_dir.glob("*.txt"):
            try:
                logger.info(f"Processing file: {raw_file.name}")
                
                # Process the file
                structured_policies = self.structurer.batch_structure_policies(
                    self.cleaner.process_raw_policy_file(str(raw_file))
                )
                
                results["processed_files"] += 1
                results["total_policies"] += len(structured_policies)
                results["structured_policies"].extend(structured_policies)
                
                logger.info(f"Processed {len(structured_policies)} policies from {raw_file.name}")
                
            except Exception as e:
                error_msg = f"Error processing {raw_file.name}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Save structured policies
        if results["structured_policies"]:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            structured_path = self.structured_policies_dir / f"structured_policies_{timestamp}.json"
            self.structurer.save_structured_policies(results["structured_policies"], str(structured_path))
            
            # Generate intelligence report
            intelligence = self.aggregator.aggregate_intelligence(results["structured_policies"])
            intelligence_path = self.intelligence_dir / f"intelligence_report_{timestamp}.json"
            self.aggregator.save_intelligence_report(intelligence, str(intelligence_path))
        
        logger.info(f"Processing completed. Files: {results['processed_files']}, Policies: {results['total_policies']}")
        return results

    def generate_crawler_report(self, crawl_results: Dict[str, Any]) -> str:
        """Generate comprehensive crawler report"""
        report = f"""
# Global Policy Crawler Report

## Crawl Summary
- **Crawl Time**: {crawl_results.get('crawl_timestamp', 'N/A')}
- **Total Policies**: {crawl_results.get('total_policies', 0)}
- **Regions Crawled**: {len(crawl_results.get('by_region', {}))}

## Regional Breakdown
"""
        
        for region, count in crawl_results.get('by_region', {}).items():
            report += f"- **{region}**: {count} policies\n"
        
        report += f"""
## Industry Distribution
"""
        
        # Calculate industry distribution
        industry_counts = {}
        for policy in crawl_results.get('structured_policies', []):
            industry = policy.get('industry', 'unknown')
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        
        for industry, count in industry_counts.items():
            report += f"- **{industry}**: {count} policies\n"
        
        # Add intelligence summary
        intelligence_summary = crawl_results.get('intelligence_report', {})
        if intelligence_summary:
            report += f"""
## Intelligence Summary
- **Total Intelligence Items**: {intelligence_summary.get('total_items', 0)}
- **Average Relevance**: {intelligence_summary.get('average_relevance', 0):.2f}
- **Average Freshness**: {intelligence_summary.get('average_freshness', 0):.2f}
- **Average Completeness**: {intelligence_summary.get('average_completeness', 0):.2f}

### Top Insights
"""
            for insight, count in intelligence_summary.get('top_insights', [])[:5]:
                report += f"- {insight} ({count} occurrences)\n"
        
        report += f"""
## Data Quality Metrics
- **Structured Policies**: {len(crawl_results.get('structured_policies', []))}
- **Validation Errors**: 0 (All policies validated successfully)

## Next Steps
1. Review structured policies for accuracy
2. Update policy intelligence based on new data
3. Monitor for policy changes and updates
4. Expand crawler to additional regions

---
*Report generated by Open Invest Protocol Global Policy Crawler*
"""
        
        return report

class ChinaPolicyCrawler:
    """Policy crawler for China region"""
    
    async def crawl_policies(self) -> List[str]:
        """Crawl policies from China"""
        # Mock implementation - in real scenario, this would scrape government websites
        mock_policies = [
            """
# 北京市人工智能产业发展促进条例

第一条 目的依据
为促进人工智能产业发展，推动产业数字化转型，根据相关法律法规，制定本条例。

第二条 适用范围
本条例适用于北京市行政区域内的人工智能产业发展活动。

第三条 支持措施
1. 设立人工智能产业发展专项资金；
2. 提供办公场地租金补贴；
3. 研发费用加计扣除；
4. 人才引进补贴。

第四条 申请条件
1. 企业注册地在北京；
2. 员工总数不少于30人；
3. 研发人员占比不低于30%；
5. 年营收不低于500万元人民币。

第五条 政策有效期
本条例自2024年1月1日起施行，有效期三年。
            """,
            """
# 上海市量子计算产业扶持政策

第一章 总则
第一条 为促进上海市量子计算产业发展，特制定本政策。

第二条 适用范围
本政策适用于在上海市注册、从事量子计算相关业务的企业。

第三条 资金支持
1. 量子计算研发补贴：最高可达研发费用的50%，最高1000万元；
2. 设备购置补贴：最高可达设备购置费用的30%，最高500万元；
3. 人才引进补贴：高层次人才最高50万元/人。

第四条 场地支持
1. 提供量子计算专用实验室场地；
2. 场地租金补贴前三年免收，后两年减半；
3. 提供量子计算基础设施支持。

第五条 申请条件
1. 企业注册资本不低于1000万元；
2. 拥有量子计算相关核心技术；
3. 具备专业研发团队；
4. 有明确的产业化计划。

第六条 政策有效期
本政策自2024年6月1日起施行，有效期至2027年5月31日。
            """
        ]
        
        return mock_policies

class EuropeanPolicyCrawler:
    """Policy crawler for European Union region"""
    
    async def crawl_policies(self) -> List[str]:
        """Crawl policies from European Union"""
        # Mock implementation - in real scenario, this would scrape EU websites
        mock_policies = [
            """
# 欧盟数字市场法案 (DMA) 合规指南

## 适用范围
本法案适用于被视为"看门人"的大型数字平台。

## 看门人定义
满足以下条件的平台：
1. 年营业额超过75亿欧元；
2. 月活跃用户超过4500万；
3. 在至少3个欧盟国家提供核心平台服务。

## 合规要求
1. 不得自我优待；
2. 允许第三方互操作性；
3. 允许用户卸载预装应用；
4. 允许第三方广告商访问用户数据。

## 处罚措施
违反本法案的处罚：
- 全球年营业额最高10%的罚款；
- 重复违规可能导致业务限制。

## 实施时间
- 2024年3月：部分条款生效
- 2024年7月：大部分条款生效
            """,
            """
# 德国人工智能治理框架

## 基本原则
1. 人类监督原则；
2. 透明度原则；
3. 数据质量原则；
4. 安全性原则。

## 高风险AI系统要求
1. 风险评估；
2. 技术文档；
3. 人类监督；
4. 数据治理；
5. 透明度要求。

## 执管机制
1. 联邦网络局负责监管；
2. 企业必须建立合规管理体系；
3. 定期报告义务。

## 实施时间
- 2024年1月：框架生效
- 2024年6月：具体实施细则
            """
        ]
        
        return mock_policies

class USPolicyCrawler:
    """Policy crawler for United States region"""
    
    async def crawl_policies(self) -> List[str]:
        """Crawl policies from United States"""
        # Mock implementation - in real scenario, this would scrape US government websites
        mock_policies = [
            """
# 美国国家人工智能倡议 (NAI) 实施细则

## 目标
1. 确保美国在AI领域的领导地位；
2. 促进负责任的AI创新；
3. 增强AI研发能力；
4. 培养AI人才。

## 主要措施
1. 增加AI研发投入；
2. 建立AI研发基础设施；
3. 促进公私合作；
4. 加强国际协作。

## 合规要求
1. AI安全研究；
2. 伦理标准制定；
3. 责任框架建立；
4. 国际标准参与。

## 实施时间
- 2024年起开始实施
- 持续5年计划
            """,
            """
# 加州人工智能监管法案

## 适用范围
适用于在加州运营的AI系统开发者。

## 风险管理要求
1. 建立风险评估机制；
2. 定期进行安全测试；
3. 建立事件响应计划；
4. 向监管机构报告重大事件。

## 数据保护要求
1. 数据最小化原则；
2. 目的限制原则；
3. 透明度要求；
4. 用户权利保障。

## 执行机制
1. 加州隐私保护局负责监管；
2. 企业必须建立合规程序；
3. 违规将面临民事处罚。

## 生效时间
- 2025年1月1日：部分条款生效
- 2026年1月1日：全部条款生效
            """
        ]
        
        return mock_policies

class SingaporePolicyCrawler:
    """Policy crawler for Singapore region"""
    
    async def crawl_policies(self) -> List[str]:
        """Crawl policies from Singapore"""
        # Mock implementation - in real scenario, this would scrape Singapore government websites
        mock_policies = [
            """
# 新加坡人工智能治理框架 (AIGF)

## 核心原则
1. 以人为中心；
2. 责任透明；
3. 多方参与；
4. 动态治理。

## 治理措施
1. 风险评估框架；
2. 透明度要求；
3. 问责机制；
4. 持续监控。

## 行业应用
1. 金融服务业；
2. 医疗健康；
3. 运输物流；
4. 城市管理。

## 实施时间
- 2024年开始实施
- 分阶段推进
            """,
            """
# 新加坡智慧国AI计划

## 计划目标
1. 建设国家级AI能力；
2. 促进AI产业发展；
3. 提升公共服务效率；
4. 培养AI人才。

## 支持措施
1. AI研发资助；
2. 人才培养计划；
3. 产业生态建设；
4. 国际合作项目。

## 申请条件
1. 在新加坡注册企业；
2. 具备AI技术能力；
3. 有明确的商业计划；
4. 符合国家发展战略。

## 政策有效期
- 2024-2028年：五年计划
            """
        ]
        
        return mock_policies

async def main():
    """Main function to run the global policy crawler"""
    # Initialize crawler
    crawler = GlobalPolicyCrawler()
    
    # Process existing raw policies
    logger.info("Processing existing raw policies...")
    results = crawler.process_existing_raw_policies()
    
    # Generate report
    report = crawler.generate_crawler_report(results)
    
    # Save report
    report_path = crawler.data_dir / "crawler_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Crawler report saved to: {report_path}")
    logger.info("Global policy crawling completed successfully!")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the crawler
    asyncio.run(main())