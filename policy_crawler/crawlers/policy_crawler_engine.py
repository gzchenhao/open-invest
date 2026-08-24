"""
Global Policy Intelligence Crawler Engine
Aggregates and structures government policies from 500+ global tech hubs
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from ..processors.policy_cleaner import PolicyCleaner

logger = logging.getLogger(__name__)

class RegionalCrawler:
    """Base class for regional policy crawlers"""
    
    def __init__(self, region: str, country: str, base_url: str):
        self.region = region
        self.country = country
        self.base_url = base_url
        self.policy_cleaner = PolicyCleaner()
    
    async def crawl_policies(self) -> List[Dict[str, Any]]:
        """Crawl policies from regional government sources"""
        raise NotImplementedError("Subclasses must implement crawl_policies method")
    
    async def crawl_single_policy(self, policy_url: str, policy_id: str) -> Optional[Dict[str, Any]]:
        """Crawl and clean a single policy"""
        try:
            # Simulate web scraping (in real implementation, use requests/selenium)
            raw_policy_text = await self._fetch_policy_text(policy_url)
            
            if raw_policy_text:
                cleaned_policy = self.policy_cleaner.clean_policy_text(
                    raw_policy_text=raw_policy_text,
                    policy_id=policy_id,
                    region=self.region,
                    country=self.country
                )
                
                if cleaned_policy:
                    return {
                        "policy_id": cleaned_policy.policy_id,
                        "region": self.region,
                        "country": self.country,
                        "raw_text": raw_policy_text,
                        "structured_data": self.policy_cleaner._policy_to_dict(cleaned_policy),
                        "crawled_at": datetime.now().isoformat()
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error crawling policy {policy_id}: {e}")
            return None
    
    async def _fetch_policy_text(self, url: str) -> Optional[str]:
        """Fetch policy text from URL (mock implementation)"""
        # In real implementation, this would use requests, selenium, etc.
        # For now, return mock data based on region
        if "shanghai" in url.lower():
            return self._get_shanghai_mock_policy()
        elif "silicon" in url.lower():
            return self._get_silicon_valley_mock_policy()
        else:
            return self._get_generic_mock_policy()
    
    def _get_shanghai_mock_policy(self) -> str:
        """Mock Shanghai policy text"""
        return """
        SHANGHAI QUANTUM TECHNOLOGY HUB INCENTIVE POLICY 2024
        Publication Date: January 15, 2024
        Authority: Shanghai Municipal Government
        
        1. TAX INCENTIVES
           - Corporate tax reduction of 30% for 5 years
           - R&D tax credit of 40% for qualified quantum computing projects
           
        2. FINANCIAL SUBSIDIES
           - Startup grant of $2,000,000 for quantum computing companies
           - R&D funding up to $5,000,000 for breakthrough technologies
           
        3. REQUIREMENTS
           - Minimum 50 research staff members
           - At least 30% PhD holders in technical positions
           - Minimum 10 patents filed in quantum computing
           - Minimum investment of $10,000,000
           
        4. COMPLIANCE
           - Data localization required for quantum data
           - Export controls on quantum technologies
        """
    
    def _get_silicon_valley_mock_policy(self) -> str:
        """Mock Silicon Valley policy text"""
        return """
        SILICON VALLEY AI INNOVATION HUB INCENTIVE PROGRAM 2024
        Publication Date: March 1, 2024
        Authority: California State Government
        
        1. TAX INCENTIVES
           - Corporate tax reduction of 25% for 7 years
           - R&D tax credit of 35% for qualified AI projects
           
        2. FINANCIAL SUBSIDIES
           - Startup grant of $1,500,000 for AI companies
           - R&D funding up to $10,000,000 for breakthrough AI research
           
        3. REQUIREMENTS
           - Minimum 25 research staff members
           - At least 20% PhD holders in technical positions
           - Minimum 5 patents filed in AI/ML
           - Minimum investment of $5,000,000
           
        4. COMPLIANCE
           - Data privacy compliance with CCPA
           - AI ethics standards adherence
        """
    
    def _get_generic_mock_policy(self) -> str:
        """Generic mock policy text"""
        return """
        TECHNOLOGY INCENTIVE POLICY 2024
        Authority: Regional Government
        
        1. TAX INCENTIVES
           - Corporate tax reduction of 20% for 5 years
           - R&D tax credit of 30% for qualified projects
           
        2. FINANCIAL SUBSIDIES
           - Startup grant of $1,000,000
           - R&D funding up to $3,000,000
           
        3. REQUIREMENTS
           - Minimum 20 research staff members
           - Minimum 5 patents filed
           - Minimum investment of $2,000,000
        """

class ChinaCrawler(RegionalCrawler):
    """China regional policy crawler"""
    
    def __init__(self):
        super().__init__(
            region="China",
            country="CN",
            base_url="https://www.gov.cn"
        )
        self.target_regions = [
            "Shanghai", "Beijing", "Shenzhen", "Hangzhou", "Suzhou"
        ]
    
    async def crawl_policies(self) -> List[Dict[str, Any]]:
        """Crawl policies from Chinese tech hubs"""
        policies = []
        
        for region in self.target_regions:
            policy_urls = [
                f"{self.base_url}/policy/{region.lower()}/quantum-tech-2024",
                f"{self.base_url}/policy/{region.lower()}/ai-innovation-2024",
                f"{self.base_url}/policy/{region.lower()}/semiconductor-2024"
            ]
            
            for i, url in enumerate(policy_urls):
                policy_id = f"{region.lower()}-tech-{2024}-{i+1}"
                policy = await self.crawl_single_policy(url, policy_id)
                if policy:
                    policies.append(policy)
        
        logger.info(f"Crawled {len(policies)} policies from China")
        return policies

class SiliconValleyCrawler(RegionalCrawler):
    """Silicon Valley policy crawler"""
    
    def __init__(self):
        super().__init__(
            region="Silicon Valley",
            country="US",
            base_url="https://www.siliconvalley.gov"
        )
    
    async def crawl_policies(self) -> List[Dict[str, Any]]:
        """Crawl policies from Silicon Valley"""
        policies = []
        
        policy_urls = [
            f"{self.base_url}/ai-innovation-hub-2024",
            f"{self.base_url}/autonomous-driving-program-2024",
            f"{self.base_url}/quantum-computing-initiative-2024"
        ]
        
        for i, url in enumerate(policy_urls):
            policy_id = f"silicon-valley-ai-{2024}-{i+1}"
            policy = await self.crawl_single_policy(url, policy_id)
            if policy:
                policies.append(policy)
        
        logger.info(f"Crawled {len(policies)} policies from Silicon Valley")
        return policies

class EUCrawler(RegionalCrawler):
    """European Union policy crawler"""
    
    def __init__(self):
        super().__init__(
            region="European Union",
            country="EU",
            base_url="https://europa.eu"
        )
        self.target_countries = [
            "Germany", "France", "Netherlands", "Finland", "Sweden"
        ]
    
    async def crawl_policies(self) -> List[Dict[str, Any]]:
        """Crawl policies from EU tech hubs"""
        policies = []
        
        for country in self.target_countries:
            policy_urls = [
                f"{self.base_url}/{country.lower()}/digital-hub-2024",
                f"{self.base_url}/{country.lower()}/green-tech-2024",
                f"{self.base_url}/{country.lower()}/ai-regulation-2024"
            ]
            
            for i, url in enumerate(policy_urls):
                policy_id = f"eu-{country.lower()}-tech-{2024}-{i+1}"
                policy = await self.crawl_single_policy(url, policy_id)
                if policy:
                    policies.append(policy)
        
        logger.info(f"Crawled {len(policies)} policies from EU")
        return policies

class SingaporeCrawler(RegionalCrawler):
    """Singapore policy crawler"""
    
    def __init__(self):
        super().__init__(
            region="Singapore",
            country="SG",
            base_url="https://www.singapore.gov.sg"
        )
    
    async def crawl_policies(self) -> List[Dict[str, Any]]:
        """Crawl policies from Singapore"""
        policies = []
        
        policy_urls = [
            f"{self.base_url}/ai-governance-2024",
            f"{self.base_url}/fintech-hub-2024",
            f"{self.base_url}/biomedical-center-2024"
        ]
        
        for i, url in enumerate(policy_urls):
            policy_id = f"singapore-tech-{2024}-{i+1}"
            policy = await self.crawl_single_policy(url, policy_id)
            if policy:
                policies.append(policy)
        
        logger.info(f"Crawled {len(policies)} policies from Singapore")
        return policies

class PolicyCrawlerEngine:
    """Main policy crawler engine"""
    
    def __init__(self):
        self.crawlers = [
            ChinaCrawler(),
            SiliconValleyCrawler(),
            EUCrawler(),
            SingaporeCrawler()
        ]
        self.output_dir = Path(__file__).parent.parent / "data" / "structured_policies"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def crawl_all_policies(self) -> List[Dict[str, Any]]:
        """Crawl policies from all regions"""
        all_policies = []
        
        logger.info("Starting global policy crawl...")
        
        # Run crawlers concurrently
        tasks = [crawler.crawl_policies() for crawler in self.crawlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Crawler error: {result}")
            elif isinstance(result, list):
                all_policies.extend(result)
        
        logger.info(f"Total policies crawled: {len(all_policies)}")
        return all_policies
    
    async def save_policies(self, policies: List[Dict[str, Any]]) -> None:
        """Save crawled policies to structured format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"policies_{timestamp}.json"
        
        # Save structured policies
        structured_data = []
        for policy in policies:
            structured_data.append({
                "policy_id": policy["policy_id"],
                "region": policy["region"],
                "country": policy["country"],
                "structured_data": policy["structured_data"],
                "crawled_at": policy["crawled_at"]
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(structured_data)} policies to {output_file}")
        
        # Save raw policies
        raw_output_file = self.output_dir.parent / "raw_policies" / f"raw_policies_{timestamp}.json"
        raw_data = []
        for policy in policies:
            raw_data.append({
                "policy_id": policy["policy_id"],
                "region": policy["region"],
                "country": policy["country"],
                "raw_text": policy["raw_text"],
                "crawled_at": policy["crawled_at"]
            })
        
        with open(raw_output_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(raw_data)} raw policies to {raw_output_file}")
    
    async def run_crawl(self) -> None:
        """Run complete crawl process"""
        try:
            # Step 1: Crawl all policies
            policies = await self.crawl_all_policies()
            
            if not policies:
                logger.warning("No policies were crawled")
                return
            
            # Step 2: Save policies
            await self.save_policies(policies)
            
            # Step 3: Generate summary report
            await self.generate_summary_report(policies)
            
            logger.info("Policy crawl completed successfully")
            
        except Exception as e:
            logger.error(f"Error during crawl: {e}")
            raise
    
    async def generate_summary_report(self, policies: List[Dict[str, Any]]) -> None:
        """Generate summary report of crawled policies"""
        summary = {
            "crawl_timestamp": datetime.now().isoformat(),
            "total_policies": len(policies),
            "regions": {},
            "industries": {},
            "incentives": {},
            "requirements": {}
        }
        
        for policy in policies:
            region = policy["region"]
            country = policy["country"]
            
            # Count by region
            if region not in summary["regions"]:
                summary["regions"][region] = 0
            summary["regions"][region] += 1
            
            # Count by country
            if country not in summary["regions"]:
                summary["regions"][country] = 0
            summary["regions"][country] += 1
            
            # Extract industries from structured data
            structured_data = policy["structured_data"]
            if "target_industries" in structured_data:
                for industry in structured_data["target_industries"]:
                    if industry not in summary["industries"]:
                        summary["industries"][industry] = 0
                    summary["industries"][industry] += 1
            
            # Count incentive types
            if "incentives" in structured_data:
                for incentive_type, incentives in structured_data["incentives"].items():
                    if incentive_type not in summary["incentives"]:
                        summary["incentives"][incentive_type] = 0
                    summary["incentives"][incentive_type] += len(incentives)
        
        # Save summary report
        summary_file = self.output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Summary report saved to {summary_file}")

async def main():
    """Main function to run the policy crawler engine"""
    engine = PolicyCrawlerEngine()
    await engine.run_crawl()

if __name__ == "__main__":
    asyncio.run(main())