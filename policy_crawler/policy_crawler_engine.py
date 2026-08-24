"""
Global Policy Intelligence Crawler Engine
Main engine for crawling and structuring global government policies
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from crawlers.china_crawler import ChinaPolicyCrawler
from crawlers.silicon_valley_crawler import SiliconValleyPolicyCrawler
from crawlers.eu_crawler import EUPolicyCrawler
from crawlers.singapore_crawler import SingaporePolicyCrawler
from processors.policy_cleaner import PolicyCleaner
from data_structurer import DataStructurer
from intelligence_aggregator import IntelligenceAggregator

logger = logging.getLogger(__name__)

class PolicyCrawlerEngine:
    """Main policy crawler engine"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.cleaner = PolicyCleaner()
        self.structurer = DataStructurer()
        self.aggregator = IntelligenceAggregator()
        
        # Initialize crawlers
        self.crawlers = {
            "china": ChinaPolicyCrawler(),
            "silicon_valley": SiliconValleyPolicyCrawler(),
            "eu": EUPolicyCrawler(),
            "singapore": SingaporePolicyCrawler()
        }
        
        # Statistics
        self.stats = {
            "total_policies_crawled": 0,
            "total_policies_processed": 0,
            "total_policies_structured": 0,
            "errors": []
        }
    
    async def crawl_all_regions(self) -> Dict[str, Any]:
        """
        Crawl policies from all configured regions
        
        Returns:
            Dict containing crawling results and statistics
        """
        logger.info("Starting global policy crawl")
        results = {}
        
        # Crawl each region
        for region_name, crawler in self.crawlers.items():
            try:
                logger.info(f"Crawling policies from {region_name}")
                region_results = await self.crawl_region(region_name, crawler)
                results[region_name] = region_results
                self.stats["total_policies_crawled"] += region_results["policies_found"]
                
            except Exception as e:
                error_msg = f"Error crawling {region_name}: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)
                results[region_name] = {"error": error_msg}
        
        logger.info(f"Completed crawling. Total policies found: {self.stats['total_policies_crawled']}")
        return results
    
    async def crawl_region(self, region_name: str, crawler) -> Dict[str, Any]:
        """
        Crawl policies from a specific region
        
        Args:
            region_name: Name of the region
            crawler: Region-specific crawler instance
            
        Returns:
            Dict containing region crawling results
        """
        try:
            # Step 1: Crawl raw policies
            raw_policies = await crawler.crawl_policies()
            logger.info(f"Found {len(raw_policies)} raw policies in {region_name}")
            
            # Step 2: Process each policy
            processed_policies = []
            for raw_policy in raw_policies:
                try:
                    # Clean and structure the policy
                    cleaned_policy = self.cleaner.clean_policy_text(
                        raw_policy["content"],
                        raw_policy.get("source_url")
                    )
                    
                    # Structure the data
                    structured_policy = self.structurer.structure_policy(cleaned_policy)
                    
                    processed_policies.append(structured_policy)
                    self.stats["total_policies_processed"] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing policy {raw_policy.get('id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    self.stats["errors"].append(error_msg)
            
            # Step 3: Aggregate intelligence
            aggregated_data = self.aggregator.aggregate_intelligence(processed_policies)
            
            # Step 4: Store results
            await self.store_region_results(region_name, processed_policies, aggregated_data)
            
            return {
                "region": region_name,
                "policies_found": len(raw_policies),
                "policies_processed": len(processed_policies),
                "policies_structured": len(processed_policies),
                "aggregated_data": aggregated_data,
                "processing_errors": len(self.stats["errors"])
            }
            
        except Exception as e:
            raise Exception(f"Region crawling failed: {str(e)}")
    
    async def crawl_single_policy(self, region_name: str, policy_url: str) -> Dict[str, Any]:
        """
        Crawl a single policy from a specific region
        
        Args:
            region_name: Name of the region
            policy_url: URL of the policy to crawl
            
        Returns:
            Dict containing the processed policy
        """
        try:
            crawler = self.crawlers[region_name]
            raw_policy = await crawler.crawl_single_policy(policy_url)
            
            cleaned_policy = self.cleaner.clean_policy_text(
                raw_policy["content"],
                raw_policy["source_url"]
            )
            
            structured_policy = self.structurer.structure_policy(cleaned_policy)
            
            # Store single policy
            await self.store_single_policy(region_name, structured_policy)
            
            return {
                "policy_id": structured_policy.policy_id,
                "region": region_name,
                "title": structured_policy.title,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "policy_url": policy_url,
                "region": region_name,
                "status": "error",
                "error": str(e)
            }
    
    async def store_region_results(self, region_name: str, policies: List[Any], aggregated_data: Dict[str, Any]):
        """
        Store crawling results for a region
        
        Args:
            region_name: Name of the region
            policies: List of processed policies
            aggregated_data: Aggregated intelligence data
        """
        try:
            # Create region directory
            region_dir = Path(f"../../data/structured_policies/{region_name}")
            region_dir.mkdir(parents=True, exist_ok=True)
            
            # Store individual policies
            for policy in policies:
                policy_file = region_dir / f"{policy.policy_id}.json"
                with open(policy_file, 'w', encoding='utf-8') as f:
                    json.dump(policy.__dict__, f, ensure_ascii=False, indent=2)
            
            # Store aggregated data
            aggregated_file = region_dir / "aggregated_data.json"
            with open(aggregated_file, 'w', encoding='utf-8') as f:
                json.dump(aggregated_data, f, ensure_ascii=False, indent=2)
            
            # Store metadata
            metadata = {
                "region": region_name,
                "crawl_date": datetime.now().isoformat(),
                "policies_count": len(policies),
                "last_updated": datetime.now().isoformat()
            }
            
            metadata_file = region_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Stored {len(policies)} policies for {region_name}")
            
        except Exception as e:
            logger.error(f"Error storing results for {region_name}: {str(e)}")
    
    async def store_single_policy(self, region_name: str, policy):
        """
        Store a single policy
        
        Args:
            region_name: Name of the region
            policy: Processed policy object
        """
        try:
            policy_dir = Path(f"../../data/structured_policies/{region_name}")
            policy_dir.mkdir(parents=True, exist_ok=True)
            
            policy_file = policy_dir / f"{policy.policy_id}.json"
            with open(policy_file, 'w', encoding='utf-8') as f:
                json.dump(policy.__dict__, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Stored single policy: {policy.policy_id}")
            
        except Exception as e:
            logger.error(f"Error storing single policy: {str(e)}")
    
    async def get_crawl_statistics(self) -> Dict[str, Any]:
        """
        Get crawling statistics
        
        Returns:
            Dict containing crawling statistics
        """
        return {
            **self.stats,
            "crawl_date": datetime.now().isoformat(),
            "regions_configured": list(self.crawlers.keys()),
            "success_rate": (
                self.stats["total_policies_processed"] / 
                max(self.stats["total_policies_crawled"], 1)
            ) * 100
        }
    
    async def generate_policy_report(self, region_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive policy report
        
        Args:
            region_name: Optional region name to generate report for specific region
            
        Returns:
            Dict containing policy report
        """
        try:
            if region_name:
                # Generate report for specific region
                region_dir = Path(f"../../data/structured_policies/{region_name}")
                if not region_dir.exists():
                    return {"error": f"Region {region_name} not found"}
                
                # Load aggregated data
                aggregated_file = region_dir / "aggregated_data.json"
                if aggregated_file.exists():
                    with open(aggregated_file, 'r', encoding='utf-8') as f:
                        aggregated_data = json.load(f)
                else:
                    aggregated_data = {}
                
                # Load metadata
                metadata_file = region_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                else:
                    metadata = {}
                
                return {
                    "region": region_name,
                    "aggregated_data": aggregated_data,
                    "metadata": metadata,
                    "generated_at": datetime.now().isoformat()
                }
            
            else:
                # Generate global report
                global_report = {
                    "global_summary": {},
                    "regional_breakdown": {},
                    "trends": {},
                    "recommendations": [],
                    "generated_at": datetime.now().isoformat()
                }
                
                # Aggregate data from all regions
                for region_name in self.crawlers.keys():
                    region_dir = Path(f"../../data/structured_policies/{region_name}")
                    if region_dir.exists():
                        aggregated_file = region_dir / "aggregated_data.json"
                        if aggregated_file.exists():
                            with open(aggregated_file, 'r', encoding='utf-8') as f:
                                regional_data = json.load(f)
                                global_report["regional_breakdown"][region_name] = regional_data
                
                return global_report
                
        except Exception as e:
            logger.error(f"Error generating policy report: {str(e)}")
            return {"error": str(e)}

# Example usage
async def main():
    """Example usage of the policy crawler engine"""
    engine = PolicyCrawlerEngine()
    
    # Crawl all regions
    results = await engine.crawl_all_regions()
    
    # Get statistics
    stats = await engine.get_crawl_statistics()
    
    # Generate report
    report = await engine.generate_policy_report()
    
    print(f"Crawling completed: {results}")
    print(f"Statistics: {stats}")
    print(f"Report: {report}")

if __name__ == "__main__":
    asyncio.run(main())