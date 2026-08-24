"""
Singapore Policy Crawler
Crawls Singapore policies for tech investment and incentives
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup


@dataclass
class SingaporePolicySource:
    """Singapore policy source information"""
    
    name: str
    url: str
    jurisdiction: str
    tech_hub: str
    policy_type: str
    description: str


class SingaporePolicyCrawler:
    """Singapore policy crawler for tech investment policies"""
    
    def __init__(self):
        self.sources = self._initialize_sources()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _initialize_sources(self) -> List[SingaporePolicySource]:
        """Initialize Singapore policy sources"""
        
        sources = [
            SingaporePolicySource(
                name="Singapore Economic Development Board",
                url="https://www.edb.gov.sg/",
                jurisdiction="Singapore",
                tech_hub="One North",
                policy_type="investment_promotion",
                description="Singapore tech investment policies and incentives"
            ),
            SingaporePolicySource(
                name="Enterprise Singapore",
                url="https://www.enterprisesg.gov.sg/",
                jurisdiction="Singapore",
                tech_hub="Singapore",
                policy_type="investment_promotion",
                description="Singapore enterprise support and incentive policies"
            ),
            SingaporePolicySource(
                name="Singapore National Research Foundation",
                url="https://www.nrf.gov.sg/",
                jurisdiction="Singapore",
                tech_hub="Singapore",
                policy_type="investment_promotion",
                description="Singapore research funding and innovation policies"
            ),
            SingaporePolicySource(
                name="Singapore Agency for Science, Technology and Research (A*STAR)",
                url="https://www.a-star.edu.sg/",
                jurisdiction="Singapore",
                tech_hub="Singapore",
                policy_type="investment_promotion",
                description="Singapore R&D funding and support policies"
            ),
            SingaporePolicySource(
                name="Singapore Ministry of Trade and Industry",
                url="https://www.mti.gov.sg/",
                jurisdiction="Singapore",
                tech_hub="Singapore",
                policy_type="investment_promotion",
                description="Singapore trade and industry policies"
            )
        ]
        
        return sources
    
    def crawl_policies(self, source: SingaporePolicySource, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Crawl policies from a specific source
        
        Args:
            source: Policy source to crawl
            max_pages: Maximum number of pages to crawl
            
        Returns:
            List of crawled policies
        """
        
        policies = []
        
        try:
            # Get main page
            response = self.session.get(source.url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract policy links
            policy_links = self._extract_policy_links(soup, source)
            
            # Crawl individual policy pages
            for i, link in enumerate(policy_links[:max_pages]):
                try:
                    policy_data = self._crawl_policy_page(link, source)
                    if policy_data:
                        policies.append(policy_data)
                        print(f"Crawled policy {i+1}/{len(policy_links[:max_pages])}: {policy_data.get('title', 'Unknown')}")
                except Exception as e:
                    print(f"Error crawling policy page {link}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error crawling source {source.name}: {e}")
        
        return policies
    
    def _extract_policy_links(self, soup: BeautifulSoup, source: SingaporePolicySource) -> List[str]:
        """Extract policy links from page"""
        
        links = []
        
        # Look for policy-related keywords
        policy_keywords = ['policy', 'incentive', 'grant', 'subsidy', 'program', 'funding', 'economic', 'development', 'business', 'startup', 'innovation', 'research', 'technology', 'biomedical', 'digital', 'enterprise']
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip().lower()
            
            # Check if link contains policy keywords
            if any(keyword in text for keyword in policy_keywords):
                # Convert relative URL to absolute
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = source.url.rstrip('/') + href
                else:
                    full_url = source.url.rstrip('/') + '/' + href
                
                links.append(full_url)
        
        return links
    
    def _crawl_policy_page(self, url: str, source: SingaporePolicySource) -> Optional[Dict[str, Any]]:
        """
        Crawl individual policy page
        
        Args:
            url: Policy page URL
            source: Policy source information
            
        Returns:
            Policy data dictionary
        """
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract policy information
            title = self._extract_policy_title(soup)
            content = self._extract_policy_content(soup)
            publish_date = self._extract_publish_date(soup)
            
            if not title or not content:
                return None
            
            # Create policy data
            policy_data = {
                "title": title,
                "content": content,
                "source_url": url,
                "source_name": source.name,
                "jurisdiction": source.jurisdiction,
                "tech_hub": source.tech_hub,
                "policy_type": source.policy_type,
                "publish_date": publish_date,
                "crawl_timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                "raw_text": content
            }
            
            return policy_data
            
        except Exception as e:
            print(f"Error crawling policy page {url}: {e}")
            return None
    
    def _extract_policy_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract policy title from page"""
        
        # Try different title selectors
        title_selectors = [
            'h1',
            'h2',
            '.title',
            '.policy-title',
            '.article-title',
            '[class*="title"]',
            'title'
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                title = title_element.get_text().strip()
                if len(title) > 5:  # Reasonable title length
                    return title
        
        return None
    
    def _extract_policy_content(self, soup: BeautifulSoup) -> str:
        """Extract policy content from page"""
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try different content selectors
        content_selectors = [
            '.content',
            '.article-content',
            '.policy-content',
            '.main-content',
            '[class*="content"]',
            'div',
            'article'
        ]
        
        content = ""
        for selector in content_selectors:
            content_elements = soup.select(selector)
            for element in content_elements:
                text = element.get_text().strip()
                if len(text) > 100:  # Reasonable content length
                    content += text + "\n"
        
        # Clean up content
        content = re.sub(r'\s+', ' ', content)  # Multiple spaces to single space
        content = re.sub(r'\.{2,}', '.', content)  # Multiple dots to single dot
        
        return content.strip()
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> str:
        """Extract publish date from page"""
        
        # Try different date selectors
        date_selectors = [
            '.publish-date',
            '.date',
            '.time',
            '[class*="date"]',
            '[class*="time"]',
            'time'
        ]
        
        for selector in date_selectors:
            date_element = soup.select_one(selector)
            if date_element:
                date_text = date_element.get_text().strip()
                # Try to parse date
                try:
                    # Simple date parsing (in real implementation, use proper date parsing)
                    if re.search(r'\d{4}-\d{1,2}-\d{1,2}', date_text):
                        return re.search(r'\d{4}-\d{1,2}-\d{1,2}', date_text).group()
                except:
                    pass
        
        # Default to current date
        return datetime.now().strftime('%Y-%m-%d')
    
    def crawl_all_sources(self, max_pages_per_source: int = 3) -> List[Dict[str, Any]]:
        """
        Crawl all policy sources
        
        Args:
            max_pages_per_source: Maximum pages to crawl per source
            
        Returns:
            List of all crawled policies
        """
        
        all_policies = []
        
        for source in self.sources:
            print(f"Crawling {source.name}...")
            policies = self.crawl_policies(source, max_pages_per_source)
            all_policies.extend(policies)
            print(f"Found {len(policies)} policies from {source.name}")
        
        return all_policies
    
    def save_crawled_policies(self, policies: List[Dict[str, Any]], output_path: str):
        """Save crawled policies to JSON file"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(policies, f, indent=2, ensure_ascii=False)
    
    def load_crawled_policies(self, file_path: str) -> List[Dict[str, Any]]:
        """Load crawled policies from JSON file"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_statistics(self, policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about crawled policies"""
        
        stats = {
            "total_policies": len(policies),
            "sources": {},
            "jurisdictions": {},
            "tech_hubs": {},
            "policy_types": {},
            "date_range": {}
        }
        
        dates = []
        
        for policy in policies:
            # Count sources
            source = policy.get("source_name", "Unknown")
            stats["sources"][source] = stats["sources"].get(source, 0) + 1
            
            # Count jurisdictions
            jurisdiction = policy.get("jurisdiction", "Unknown")
            stats["jurisdictions"][jurisdiction] = stats["jurisdictions"].get(jurisdiction, 0) + 1
            
            # Count tech hubs
            tech_hub = policy.get("tech_hub", "Unknown")
            stats["tech_hubs"][tech_hub] = stats["tech_hubs"].get(tech_hub, 0) + 1
            
            # Count policy types
            policy_type = policy.get("policy_type", "Unknown")
            stats["policy_types"][policy_type] = stats["policy_types"].get(policy_type, 0) + 1
            
            # Collect dates
            publish_date = policy.get("publish_date")
            if publish_date:
                dates.append(publish_date)
        
        # Calculate date range
        if dates:
            stats["date_range"]["earliest"] = min(dates)
            stats["date_range"]["latest"] = max(dates)
        
        return stats


# Example usage
if __name__ == "__main__":
    # Initialize crawler
    crawler = SingaporePolicyCrawler()
    
    # Crawl all sources
    try:
        policies = crawler.crawl_all_sources(max_pages_per_source=2)
        print(f"Total crawled policies: {len(policies)}")
        
        # Save policies
        crawler.save_crawled_policies(policies, "singapore_policies.json")
        
        # Get statistics
        stats = crawler.get_statistics(policies)
        print(f"Statistics: {stats}")
        
    except Exception as e:
        print(f"Error in crawling: {e}")