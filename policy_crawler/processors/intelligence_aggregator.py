"""
Policy Intelligence Aggregator
Aggregate and analyze structured policy data to provide insights and recommendations
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)

@dataclass
class PolicyInsight:
    """Policy insight data structure"""
    insight_id: str
    insight_type: str  # "trend", "comparison", "recommendation", "anomaly"
    title: str
    description: str
    confidence: float
    supporting_data: List[Dict[str, Any]]
    action_items: List[str]
    metadata: Dict[str, Any]

@dataclass
class LocationAnalysis:
    """Analysis of policies by location"""
    location: str
    policy_count: int
    incentive_policies: int
    requirement_policies: int
    compliance_policies: int
    total_value_usd: float
    avg_confidence: float
    top_industries: List[Tuple[str, int]]
    best_incentives: List[Dict[str, Any]]
    compliance_challenges: List[str]

@dataclass
class IndustryAnalysis:
    """Analysis of policies by industry"""
    industry: str
    policy_count: int
    incentive_value_avg: float
    requirement_complexity: float
    compliance_burden: float
    growth_trend: float
    top_locations: List[Tuple[str, int]]
    opportunities: List[str]
    risks: List[str]

class PolicyIntelligenceAggregator:
    """Aggregate and analyze policy data"""
    
    def __init__(self):
        self.policy_database = []
        self.insights_cache = {}
        self.last_analysis = None
    
    def load_policies(self, policies: List[Dict[str, Any]]) -> None:
        """Load policies into the aggregator"""
        self.policy_database = policies
        logger.info(f"Loaded {len(policies)} policies into aggregator")
    
    def generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive policy analysis"""
        logger.info("Generating comprehensive policy analysis")
        
        analysis = {
            "summary": self._generate_summary(),
            "location_analysis": self._analyze_by_location(),
            "industry_analysis": self._analyze_by_industry(),
            "temporal_analysis": self._analyze_temporal_patterns(),
            "competitive_analysis": self._analyze_competitive_landscape(),
            "recommendations": self._generate_recommendations(),
            "insights": self._generate_insights()
        }
        
        self.last_analysis = analysis
        self.insights_cache = analysis
        
        logger.info("Comprehensive analysis generated successfully")
        return analysis
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_policies = len(self.policy_database)
        
        if total_policies == 0:
            return {"error": "No policies loaded"}
        
        # Count by type
        type_counts = Counter(policy.get("policy_type", "unknown") for policy in self.policy_database)
        
        # Count by location
        location_counts = Counter(policy.get("location", "unknown") for policy in self.policy_database)
        
        # Count by industry
        industry_counts = Counter(policy.get("industry", "unknown") for policy in self.policy_database)
        
        # Calculate average confidence
        confidences = [policy.get("confidence_score", 0) for policy in self.policy_database]
        avg_confidence = statistics.mean(confidences) if confidences else 0
        
        # Calculate total incentive value
        incentive_values = [
            policy.get("structured_data", {}).get("value_usd", 0)
            for policy in self.policy_database
            if policy.get("policy_type") == "incentive"
        ]
        total_incentive_value = sum(incentive_values)
        
        return {
            "total_policies": total_policies,
            "policy_types": dict(type_counts),
            "top_locations": dict(location_counts.most_common(5)),
            "top_industries": dict(industry_counts.most_common(5)),
            "average_confidence": avg_confidence,
            "total_incentive_value_usd": total_incentive_value,
            "analysis_timestamp": datetime.now().isoformat(),
            "data_quality": self._assess_data_quality()
        }
    
    def _analyze_by_location(self) -> Dict[str, LocationAnalysis]:
        """Analyze policies by geographic location"""
        location_data = defaultdict(list)
        
        # Group policies by location
        for policy in self.policy_database:
            location = policy.get("location", "unknown")
            location_data[location].append(policy)
        
        # Analyze each location
        location_analyses = {}
        
        for location, policies in location_data.items():
            analysis = self._analyze_single_location(location, policies)
            location_analyses[location] = analysis
        
        return location_analyses
    
    def _analyze_single_location(self, location: str, policies: List[Dict[str, Any]]) -> LocationAnalysis:
        """Analyze policies for a single location"""
        # Count policy types
        type_counts = Counter(policy.get("policy_type", "unknown") for policy in policies)
        
        # Calculate total incentive value
        incentive_values = [
            policy.get("structured_data", {}).get("value_usd", 0)
            for policy in policies
            if policy.get("policy_type") == "incentive"
        ]
        total_value = sum(incentive_values)
        
        # Calculate average confidence
        confidences = [policy.get("confidence_score", 0) for policy in policies]
        avg_confidence = statistics.mean(confidences) if confidences else 0
        
        # Analyze industries
        industry_counts = Counter(policy.get("industry", "unknown") for policy in policies)
        top_industries = industry_counts.most_common(3)
        
        # Find best incentives
        best_incentives = []
        for policy in policies:
            if policy.get("policy_type") == "incentive":
                incentive_data = policy.get("structured_data", {})
                if incentive_data.get("value_usd", 0) > 0:
                    best_incentives.append({
                        "title": policy.get("title", ""),
                        "value_usd": incentive_data.get("value_usd", 0),
                        "incentive_type": incentive_data.get("incentive_type", ""),
                        "confidence": policy.get("confidence_score", 0)
                    })
        
        # Sort by value and take top 3
        best_incentives.sort(key=lambda x: x["value_usd"], reverse=True)
        best_incentives = best_incentives[:3]
        
        # Identify compliance challenges
        compliance_challenges = []
        for policy in policies:
            if policy.get("policy_type") == "compliance":
                compliance_data = policy.get("structured_data", {})
                if compliance_data.get("compliance_level") == "strict":
                    compliance_challenges.append(policy.get("title", ""))
        
        return LocationAnalysis(
            location=location,
            policy_count=len(policies),
            incentive_policies=type_counts.get("incentive", 0),
            requirement_policies=type_counts.get("requirement", 0),
            compliance_policies=type_counts.get("compliance", 0),
            total_value_usd=total_value,
            avg_confidence=avg_confidence,
            top_industries=top_industries,
            best_incentives=best_incentives,
            compliance_challenges=compliance_challenges
        )
    
    def _analyze_by_industry(self) -> Dict[str, IndustryAnalysis]:
        """Analyze policies by industry"""
        industry_data = defaultdict(list)
        
        # Group policies by industry
        for policy in self.policy_database:
            industry = policy.get("industry", "unknown")
            industry_data[industry].append(policy)
        
        # Analyze each industry
        industry_analyses = {}
        
        for industry, policies in industry_data.items():
            analysis = self._analyze_single_industry(industry, policies)
            industry_analyses[industry] = analysis
        
        return industry_analyses
    
    def _analyze_single_industry(self, industry: str, policies: List[Dict[str, Any]]) -> IndustryAnalysis:
        """Analyze policies for a single industry"""
        # Calculate average incentive value
        incentive_values = [
            policy.get("structured_data", {}).get("value_usd", 0)
            for policy in policies
            if policy.get("policy_type") == "incentive"
        ]
        avg_incentive_value = statistics.mean(incentive_values) if incentive_values else 0
        
        # Analyze requirement complexity
        requirement_complexity = self._calculate_requirement_complexity(policies)
        
        # Analyze compliance burden
        compliance_burden = self._calculate_compliance_burden(policies)
        
        # Analyze growth trend (based on recent policies)
        growth_trend = self._calculate_growth_trend(policies)
        
        # Find top locations
        location_counts = Counter(policy.get("location", "unknown") for policy in policies)
        top_locations = location_counts.most_common(3)
        
        # Identify opportunities
        opportunities = self._identify_industry_opportunities(industry, policies)
        
        # Identify risks
        risks = self._identify_industry_risks(industry, policies)
        
        return IndustryAnalysis(
            industry=industry,
            policy_count=len(policies),
            incentive_value_avg=avg_incentive_value,
            requirement_complexity=requirement_complexity,
            compliance_burden=compliance_burden,
            growth_trend=growth_trend,
            top_locations=top_locations,
            opportunities=opportunities,
            risks=risks
        )
    
    def _calculate_requirement_complexity(self, policies: List[Dict[str, Any]]) -> float:
        """Calculate complexity score for requirements"""
        complexity_factors = []
        
        for policy in policies:
            if policy.get("policy_type") == "requirement":
                requirement_data = policy.get("structured_data", {})
                
                # Count mandatory requirements
                mandatory_count = sum(
                    1 for req in requirement_data.get("eligibility_criteria", [])
                    if req.get("mandatory", False)
                )
                
                # Check for strict priority levels
                if requirement_data.get("priority_level") == "critical":
                    complexity_factors.append(3)
                elif requirement_data.get("priority_level") == "high":
                    complexity_factors.append(2)
                else:
                    complexity_factors.append(1)
        
        return statistics.mean(complexity_factors) if complexity_factors else 0
    
    def _calculate_compliance_burden(self, policies: List[Dict[str, Any]]) -> float:
        """Calculate compliance burden score"""
        burden_scores = []
        
        for policy in policies:
            if policy.get("policy_type") == "compliance":
                compliance_data = policy.get("structured_data", {})
                
                # Check compliance level
                level = compliance_data.get("compliance_level", "standard")
                if level == "strict":
                    burden_scores.append(3)
                elif level == "enhanced":
                    burden_scores.append(2)
                else:
                    burden_scores.append(1)
        
        return statistics.mean(burden_scores) if burden_scores else 0
    
    def _calculate_growth_trend(self, policies: List[Dict[str, Any]]) -> float:
        """Calculate growth trend based on policy dates"""
        # This is a simplified calculation - in production, use actual dates
        recent_policies = [
            policy for policy in policies
            if policy.get("metadata", {}).get("last_updated", "")
        ]
        
        if len(policies) == 0:
            return 0
        
        growth_rate = len(recent_policies) / len(policies)
        return growth_rate
    
    def _identify_industry_opportunities(self, industry: str, policies: List[Dict[str, Any]]) -> List[str]:
        """Identify opportunities for an industry"""
        opportunities = []
        
        # Look for high-value incentives
        high_value_incentives = [
            policy for policy in policies
            if (policy.get("policy_type") == "incentive" and
                policy.get("structured_data", {}).get("value_usd", 0) > 100000)
        ]
        
        if high_value_incentives:
            opportunities.append(f"High-value incentives available: ${high_value_incentives[0].get('structured_data', {}).get('value_usd', 0):,.0f}")
        
        # Look for favorable compliance requirements
        favorable_compliance = [
            policy for policy in policies
            if (policy.get("policy_type") == "compliance" and
                policy.get("structured_data", {}).get("compliance_level") == "basic")
        ]
        
        if favorable_compliance:
            opportunities.append("Favorable compliance environment with basic requirements")
        
        # Look for multiple location options
        locations = set(policy.get("location", "") for policy in policies)
        if len(locations) > 1:
            opportunities.append(f"Multiple location options available: {len(locations)} regions")
        
        return opportunities
    
    def _identify_industry_risks(self, industry: str, policies: List[Dict[str, Any]]) -> List[str]:
        """Identify risks for an industry"""
        risks = []
        
        # Look for strict compliance requirements
        strict_compliance = [
            policy for policy in policies
            if (policy.get("policy_type") == "compliance" and
                policy.get("structured_data", {}).get("compliance_level") == "strict")
        ]
        
        if strict_compliance:
            risks.append("Strict compliance requirements may increase operational costs")
        
        # Look for high minimum investment requirements
        high_investment = [
            policy for policy in policies
            if (policy.get("policy_type") == "requirement" and
                policy.get("structured_data", {}).get("financial_requirements", {}).get("minimum_investment", {}).get("amount_usd", 0) > 1000000)
        ]
        
        if high_investment:
            risks.append("High minimum investment requirements may limit entry")
        
        # Check for limited incentive options
        incentive_count = sum(1 for policy in policies if policy.get("policy_type") == "incentive")
        if incentive_count < 3:
            risks.append("Limited incentive options available")
        
        return risks
    
    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal patterns in policy data"""
        # This is a simplified analysis - in production, use actual dates
        current_year = datetime.now().year
        
        # Group policies by year (simplified)
        yearly_data = defaultdict(list)
        
        for policy in self.policy_database:
            metadata = policy.get("metadata", {})
            last_updated = metadata.get("last_updated", "")
            
            if last_updated:
                try:
                    # Extract year from timestamp
                    year = datetime.fromisoformat(last_updated).year
                    yearly_data[year].append(policy)
                except:
                    # Fallback to current year
                    yearly_data[current_year].append(policy)
            else:
                yearly_data[current_year].append(policy)
        
        # Analyze trends
        trends = []
        for year in sorted(yearly_data.keys()):
            policies = yearly_data[year]
            trends.append({
                "year": year,
                "policy_count": len(policies),
                "incentive_count": sum(1 for p in policies if p.get("policy_type") == "incentive"),
                "avg_confidence": statistics.mean([p.get("confidence_score", 0) for p in policies]) if policies else 0
            })
        
        return {
            "yearly_trends": trends,
            "growth_rate": self._calculate_yearly_growth_rate(trends),
            "seasonal_patterns": self._analyze_seasonal_patterns(trends)
        }
    
    def _calculate_yearly_growth_rate(self, trends: List[Dict[str, Any]]) -> float:
        """Calculate yearly growth rate"""
        if len(trends) < 2:
            return 0
        
        latest_year = trends[-1]["policy_count"]
        previous_year = trends[-2]["policy_count"]
        
        if previous_year == 0:
            return 0
        
        return ((latest_year - previous_year) / previous_year) * 100
    
    def _analyze_seasonal_patterns(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze seasonal patterns (simplified)"""
        # This is a placeholder - in production, analyze actual seasonal patterns
        return {
            "peak_season": "Q1 (January-March)",
            "low_season": "Q3 (July-September)",
            "recommendation": "Focus policy searches during peak seasons"
        }
    
    def _analyze_competitive_landscape(self) -> Dict[str, Any]:
        """Analyze competitive landscape"""
        # Analyze locations by policy availability
        location_counts = Counter(policy.get("location", "unknown") for policy in self.policy_database)
        
        # Identify most competitive locations
        competitive_locations = location_counts.most_common(5)
        
        # Identify underserved locations
        all_locations = set(policy.get("location", "unknown") for policy in self.policy_database)
        high_potential_locations = []
        
        for location in all_locations:
            location_policies = [p for p in self.policy_database if p.get("location") == location]
            if len(location_policies) < 3:  # Less than 3 policies
                high_potential_locations.append({
                    "location": location,
                    "policy_count": len(location_policies),
                    "opportunity_score": 10 / (len(location_policies) + 1)  # Higher score for fewer policies
                })
        
        # Sort by opportunity score
        high_potential_locations.sort(key=lambda x: x["opportunity_score"], reverse=True)
        
        return {
            "most_competitive_locations": competitive_locations,
            "high_potential_locations": high_potential_locations[:5],
            "market_concentration": self._calculate_market_concentration(location_counts),
            "barriers_to_entry": self._identify_barriers_to_entry()
        }
    
    def _calculate_market_concentration(self, location_counts: Counter) -> float:
        """Calculate market concentration using Herfindahl index"""
        total = sum(location_counts.values())
        if total == 0:
            return 0
        
        herfindahl = sum((count / total) ** 2 for count in location_counts.values())
        return herfindahl
    
    def _identify_barriers_to_entry(self) -> List[str]:
        """Identify barriers to entry"""
        barriers = []
        
        # Check for high minimum investment requirements
        high_investment_policies = [
            policy for policy in self.policy_database
            if (policy.get("policy_type") == "requirement" and
                policy.get("structured_data", {}).get("financial_requirements", {}).get("minimum_investment", {}).get("amount_usd", 0) > 500000)
        ]
        
        if high_investment_policies:
            barriers.append("High minimum investment requirements")
        
        # Check for strict compliance requirements
        strict_compliance = [
            policy for policy in self.policy_database
            if (policy.get("policy_type") == "compliance" and
                policy.get("structured_data", {}).get("compliance_level") == "strict")
        ]
        
        if strict_compliance:
            barriers.append("Strict compliance requirements")
        
        # Check for limited incentive availability
        incentive_locations = set(policy.get("location", "") for policy in self.policy_database if policy.get("policy_type") == "incentive")
        total_locations = set(policy.get("location", "") for policy in self.policy_database)
        
        if len(incentive_locations) / len(total_locations) < 0.5:
            barriers.append("Limited incentive availability across locations")
        
        return barriers
    
    def _generate_recommendations(self) -> List[PolicyInsight]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # Analyze data to generate insights
        summary = self._generate_summary()
        location_analyses = self._analyze_by_location()
        industry_analyses = self._analyze_by_industry()
        
        # Generate location-based recommendations
        for location, analysis in location_analyses.items():
            if analysis.avg_confidence < 0.6:
                recommendations.append(PolicyInsight(
                    insight_id=f"location_quality_{location}",
                    insight_type="recommendation",
                    title=f"Improve Data Quality for {location}",
                    description=f"Policy data for {location} has low confidence score ({analysis.avg_confidence:.2f}). Consider improving data collection methods.",
                    confidence=0.8,
                    supporting_data=[{"location": location, "avg_confidence": analysis.avg_confidence}],
                    action_items=[
                        "Review data collection sources for {location}",
                        "Implement better validation procedures",
                        "Increase frequency of policy updates"
                    ],
                    metadata={"location": location, "issue_type": "data_quality"}
                ))
        
        # Generate industry-based recommendations
        for industry, analysis in industry_analyses.items():
            if analysis.compliance_burden > 2.0:
                recommendations.append(PolicyInsight(
                    insight_id=f"compliance_burden_{industry}",
                    insight_type="recommendation",
                    title=f"High Compliance Burden in {industry}",
                    description=f"The {industry} sector faces high compliance burden ({analysis.compliance_burden:.2f}). Consider seeking locations with more favorable compliance environments.",
                    confidence=0.7,
                    supporting_data=[{"industry": industry, "compliance_burden": analysis.compliance_burden}],
                    action_items=[
                        "Research alternative locations with lower compliance requirements",
                        "Invest in compliance automation tools",
                        "Consider phased compliance implementation"
                    ],
                    metadata={"industry": industry, "issue_type": "compliance"}
                ))
        
        # Generate competitive recommendations
        competitive_analysis = self._analyze_competitive_landscape()
        high_potential = competitive_analysis["high_potential_locations"]
        
        if high_potential:
            recommendations.append(PolicyInsight(
                insight_id="market_opportunity",
                insight_type="recommendation",
                title="Market Opportunity in Underserved Locations",
                description=f"High potential locations identified: {[loc['location'] for loc in high_potential[:3]]}. These locations offer less competition and growth opportunities.",
                confidence=0.9,
                supporting_data=high_potential[:3],
                action_items=[
                    "Establish presence in high-potential locations",
                    "Develop location-specific strategies",
                    "Monitor policy developments in emerging markets"
                ],
                metadata={"opportunity_type": "market_expansion"}
            ))
        
        return recommendations
    
    def _generate_insights(self) -> List[PolicyInsight]:
        """Generate insights from policy data"""
        insights = []
        
        # Generate trend insights
        temporal_analysis = self._analyze_temporal_patterns()
        if temporal_analysis["growth_rate"] > 20:
            insights.append(PolicyInsight(
                insight_id="growth_trend",
                insight_type="trend",
                title="Rapid Policy Development Growth",
                description=f"Policy development is growing at {temporal_analysis['growth_rate']:.1f}% annually, indicating increasing government focus on attracting investment.",
                confidence=0.8,
                supporting_data=[{"growth_rate": temporal_analysis["growth_rate"]}],
                action_items=[
                    "Monitor policy developments closely",
                    "Adjust strategies based on emerging trends",
                    "Invest in policy research capabilities"
                ],
                metadata={"trend_type": "growth"}
            ))
        
        # Generate comparative insights
        location_analyses = self._analyze_by_location()
        if location_analyses:
            best_location = max(location_analyses.values(), key=lambda x: x.avg_confidence)
            insights.append(PolicyInsight(
                insight_id="best_location",
                insight_type="comparison",
                title=f"Best Location for Data Quality: {best_location.location}",
                description=f"{best_location.location} offers the highest data quality with {best_location.avg_confidence:.2f} confidence score and {best_location.policy_count} policies.",
                confidence=0.9,
                supporting_data=[{"location": best_location.location, "confidence": best_location.avg_confidence}],
                action_items=[
                    "Prioritize {best_location.location} for expansion",
                    "Use {best_location.location} as benchmark for other locations",
                    "Replicate data collection best practices from {best_location.location}"
                ],
                metadata={"comparison_type": "data_quality"}
            ))
        
        return insights
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Assess overall data quality"""
        if not self.policy_database:
            return {"error": "No data available"}
        
        # Calculate data quality metrics
        total_policies = len(self.policy_database)
        high_confidence_policies = sum(1 for p in self.policy_database if p.get("confidence_score", 0) >= 0.8)
        medium_confidence_policies = sum(1 for p in self.policy_database if 0.6 <= p.get("confidence_score", 0) < 0.8)
        low_confidence_policies = sum(1 for p in self.policy_database if p.get("confidence_score", 0) < 0.6)
        
        # Calculate completeness
        complete_policies = sum(1 for p in self.policy_database if all([
            p.get("title", ""),
            p.get("description", ""),
            p.get("location", ""),
            p.get("industry", "")
        ]))
        
        quality_score = (high_confidence_policies / total_policies * 0.4 + 
                        medium_confidence_policies / total_policies * 0.3 + 
                        complete_policies / total_policies * 0.3)
        
        return {
            "total_policies": total_policies,
            "high_confidence_count": high_confidence_policies,
            "medium_confidence_count": medium_confidence_policies,
            "low_confidence_count": low_confidence_policies,
            "complete_policies": complete_policies,
            "quality_score": quality_score,
            "quality_rating": self._get_quality_rating(quality_score)
        }
    
    def _get_quality_rating(self, score: float) -> str:
        """Get quality rating based on score"""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        else:
            return "Poor"
    
    def export_analysis(self, analysis: Dict[str, Any], output_path: str) -> None:
        """Export analysis to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Analysis exported to {output_path}")
    
    def get_insights_by_type(self, insight_type: str) -> List[PolicyInsight]:
        """Get insights by type"""
        if not self.insights_cache:
            self.generate_comprehensive_analysis()
        
        return [
            insight for insight in self.insights_cache.get("recommendations", [])
            if insight.insight_type == insight_type
        ]
    
    def get_location_analysis(self, location: str) -> Optional[LocationAnalysis]:
        """Get analysis for a specific location"""
        if not self.insights_cache:
            self.generate_comprehensive_analysis()
        
        return self.insights_cache.get("location_analysis", {}).get(location)
    
    def get_industry_analysis(self, industry: str) -> Optional[IndustryAnalysis]:
        """Get analysis for a specific industry"""
        if not self.insights_cache:
            self.generate_comprehensive_analysis()
        
        return self.insights_cache.get("industry_analysis", {}).get(industry)