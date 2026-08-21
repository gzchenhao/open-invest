"""
Open Invest Protocol 高级使用示例
演示如何使用协议进行高级操作和批量处理
"""

import asyncio
import json
from typing import List, Dict, Any
from client.api.protocol_client import ProtocolClient, ClientType
from client.utils.project_evaluator import ProjectEvaluator, MatchScore
from client.main import GovernmentInvestmentPromotion, InvestmentProject


class InvestmentAnalyzer:
    """投资分析器"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.client = ProtocolClient(server_url, ClientType.GOV)
        self.evaluator = ProjectEvaluator(self.client)
        self.promotion = GovernmentInvestmentPromotion(server_url)
    
    async def analyze_cross_region_investment(self, project_id: str, regions: List[str]) -> Dict[str, Any]:
        """
        分析跨地区投资机会
        
        Args:
            project_id: 项目ID
            regions: 目标地区列表
            
        Returns:
            Dict[str, Any]: 跨地区分析结果
        """
        print(f"\n🌍 分析项目 {project_id} 在不同地区的投资机会...")
        
        region_results = {}
        
        for region in regions:
            print(f"  分析地区: {region}")
            
            # 评估项目在该地区的表现
            evaluation = await self.evaluator.evaluate_project(
                project_id, 
                region, 
                "standard"
            )
            
            if evaluation:
                region_results[region] = {
                    "overall_score": evaluation.overall_score,
                    "match_level": evaluation.match_level.value,
                    "tech_readiness_score": evaluation.tech_readiness_score,
                    "landing_requirements_score": evaluation.landing_requirements_score,
                    "economic_compliance_score": evaluation.economic_compliance_score,
                    "strengths": evaluation.strengths,
                    "weaknesses": evaluation.weaknesses,
                    "recommendations": evaluation.recommendations
                }
                
                print(f"    总体评分: {evaluation.overall_score:.1f}")
                print(f"    匹配等级: {evaluation.match_level.value}")
            else:
                region_results[region] = {
                    "error": "评估失败"
                }
                print(f"    ❌ 评估失败")
        
        # 找出最佳投资地区
        valid_regions = {k: v for k, v in region_results.items() if "error" not in v}
        if valid_regions:
            best_region = max(valid_regions.items(), key=lambda x: x[1]["overall_score"])
            print(f"\n🏆 最佳投资地区: {best_region[0]} (评分: {best_region[1]['overall_score']:.1f})")
        
        return region_results
    
    async def analyze_compliance_impact(self, project_id: str, region: str) -> Dict[str, Any]:
        """
        分析不同合规级别对项目的影响
        
        Args:
            project_id: 项目ID
            region: 目标地区
            
        Returns:
            Dict[str, Any]: 合规影响分析结果
        """
        print(f"\n⚖️ 分析项目 {project_id} 在 {region} 的合规影响...")
        
        compliance_levels = ["basic", "standard", "enhanced"]
        compliance_results = {}
        
        for level in compliance_levels:
            print(f"  分析合规级别: {level}")
            
            # 评估不同合规级别下的项目表现
            evaluation = await self.evaluator.evaluate_project(
                project_id, 
                region, 
                level
            )
            
            if evaluation:
                compliance_results[level] = {
                    "overall_score": evaluation.overall_score,
                    "match_level": evaluation.match_level.value,
                    "tech_readiness_score": evaluation.tech_readiness_score,
                    "landing_requirements_score": evaluation.landing_requirements_score,
                    "economic_compliance_score": evaluation.economic_compliance_score,
                    "recommendations": evaluation.recommendations
                }
                
                print(f"    总体评分: {evaluation.overall_score:.1f}")
                print(f"    匹配等级: {evaluation.match_level.value}")
            else:
                compliance_results[level] = {
                    "error": "评估失败"
                }
                print(f"    ❌ 评估失败")
        
        # 分析合规级别对评分的影响
        valid_results = {k: v for k, v in compliance_results.items() if "error" not in v}
        if valid_results:
            basic_score = valid_results.get("basic", {}).get("overall_score", 0)
            standard_score = valid_results.get("standard", {}).get("overall_score", 0)
            enhanced_score = valid_results.get("enhanced", {}).get("overall_score", 0)
            
            print(f"\n📊 合规级别影响分析:")
            print(f"  Basic级别: {basic_score:.1f}")
            print(f"  Standard级别: {standard_score:.1f}")
            print(f"  Enhanced级别: {enhanced_score:.1f}")
            
            if standard_score > basic_score:
                print(f"  ✅ Standard级别比Basic级别高 {standard_score - basic_score:.1f} 分")
            if enhanced_score > standard_score:
                print(f"  ✅ Enhanced级别比Standard级别高 {enhanced_score - standard_score:.1f} 分")
        
        return compliance_results
    
    async def batch_project_analysis(self, project_ids: List[str], region: str) -> Dict[str, Any]:
        """
        批量项目分析
        
        Args:
            project_ids: 项目ID列表
            region: 目标地区
            
        Returns:
            Dict[str, Any]: 批量分析结果
        """
        print(f"\n📊 批量分析项目在 {region} 的投资机会...")
        
        # 批量评估项目
        evaluations = await self.evaluator.batch_evaluate_projects(
            project_ids, 
            region, 
            "standard"
        )
        
        analysis_results = {}
        
        for evaluation in evaluations:
            project_id = evaluation.project_id
            analysis_results[project_id] = {
                "project_name": evaluation.project_name,
                "overall_score": evaluation.overall_score,
                "match_level": evaluation.match_level.value,
                "tech_readiness_score": evaluation.tech_readiness_score,
                "landing_requirements_score": evaluation.landing_requirements_score,
                "economic_compliance_score": evaluation.economic_compliance_score,
                "strengths": evaluation.strengths,
                "weaknesses": evaluation.weaknesses,
                "recommendations": evaluation.recommendations
            }
            
            print(f"  {evaluation.project_name}: {evaluation.overall_score:.1f}分 ({evaluation.match_level.value})")
        
        # 生成投资建议
        high_score_projects = [
            p for p in evaluations if p.overall_score >= 80
        ]
        medium_score_projects = [
            p for p in evaluations if 60 <= p.overall_score < 80
        ]
        low_score_projects = [
            p for p in evaluations if p.overall_score < 60
        ]
        
        print(f"\n🎯 投资建议:")
        print(f"  高分项目 (≥80分): {len(high_score_projects)}个 - 建议优先引进")
        print(f"  中等项目 (60-79分): {len(medium_score_projects)}个 - 建议考虑引进")
        print(f"  低分项目 (<60分): {len(low_score_projects)}个 - 建议谨慎考虑")
        
        return analysis_results
    
    async def generate_investment_report(self, project_ids: List[str], regions: List[str]) -> Dict[str, Any]:
        """
        生成综合投资报告
        
        Args:
            project_ids: 项目ID列表
            regions: 目标地区列表
            
        Returns:
            Dict[str, Any]: 综合投资报告
        """
        print("\n📋 生成综合投资报告...")
        
        report = {
            "title": "高科技项目投资分析报告",
            "generated_at": "2024-01-01T00:00:00Z",
            "analysis_summary": {},
            "cross_region_analysis": {},
            "compliance_analysis": {},
            "batch_analysis": {},
            "investment_recommendations": []
        }
        
        # 1. 批量分析
        print("\n1. 批量项目分析...")
        if regions:
            region = regions[0]  # 使用第一个地区进行批量分析
            report["batch_analysis"] = await self.batch_project_analysis(project_ids, region)
        
        # 2. 跨地区分析
        print("\n2. 跨地区分析...")
        if project_ids and regions:
            project_id = project_ids[0]  # 使用第一个项目进行跨地区分析
            report["cross_region_analysis"] = await self.analyze_cross_region_investment(project_id, regions)
        
        # 3. 合规分析
        print("\n3. 合规影响分析...")
        if project_ids and regions:
            project_id = project_ids[0]  # 使用第一个项目进行合规分析
            region = regions[0]  # 使用第一个地区
            report["compliance_analysis"] = await self.analyze_compliance_impact(project_id, region)
        
        # 4. 生成投资建议
        print("\n4. 生成投资建议...")
        report["investment_recommendations"] = self._generate_investment_recommendations(
            report["batch_analysis"], 
            report["cross_region_analysis"],
            report["compliance_analysis"]
        )
        
        # 5. 生成分析摘要
        report["analysis_summary"] = self._generate_analysis_summary(
            project_ids, 
            regions, 
            report
        )
        
        return report
    
    def _generate_investment_recommendations(self, batch_analysis: Dict, 
                                         cross_region_analysis: Dict, 
                                         compliance_analysis: Dict) -> List[str]:
        """生成投资建议"""
        recommendations = []
        
        # 基于批量分析的建议
        if batch_analysis:
            high_score_count = sum(1 for p in batch_analysis.values() 
                                if p.get("overall_score", 0) >= 80)
            if high_score_count > 0:
                recommendations.append(f"发现 {high_score_count} 个高分项目，建议优先引进")
            
            medium_score_count = sum(1 for p in batch_analysis.values() 
                                   if 60 <= p.get("overall_score", 0) < 80)
            if medium_score_count > 0:
                recommendations.append(f"发现 {medium_score_count} 个中等项目，建议加强支持后引进")
        
        # 基于跨地区分析的建议
        if cross_region_analysis:
            best_regions = [region for region, data in cross_region_analysis.items() 
                          if data.get("overall_score", 0) >= 80]
            if best_regions:
                recommendations.append(f"最佳投资地区: {', '.join(best_regions)}")
        
        # 基于合规分析的建议
        if compliance_analysis:
            best_compliance = max(compliance_analysis.keys(), 
                               key=lambda x: compliance_analysis[x].get("overall_score", 0))
            recommendations.append(f"建议采用 {best_compliance} 合规级别以获得最佳效果")
        
        # 通用建议
        recommendations.append("建议建立长期跟踪机制，持续评估项目进展")
        recommendations.append("建议加强政府与企业之间的沟通协调")
        recommendations.append("建议建立风险预警机制，及时应对潜在风险")
        
        return recommendations
    
    def _generate_analysis_summary(self, project_ids: List[str], regions: List[str], 
                                report: Dict) -> Dict[str, Any]:
        """生成分析摘要"""
        summary = {
            "total_projects": len(project_ids),
            "total_regions": len(regions),
            "high_score_projects": 0,
            "medium_score_projects": 0,
            "low_score_projects": 0,
            "best_region": None,
            "best_compliance_level": None,
            "average_score": 0.0
        }
        
        # 统计项目评分
        if report["batch_analysis"]:
            scores = [p.get("overall_score", 0) for p in report["batch_analysis"].values()]
            summary["average_score"] = sum(scores) / len(scores) if scores else 0.0
            summary["high_score_projects"] = sum(1 for s in scores if s >= 80)
            summary["medium_score_projects"] = sum(1 for s in scores if 60 <= s < 80)
            summary["low_score_projects"] = sum(1 for s in scores if s < 60)
        
        # 找出最佳地区
        if report["cross_region_analysis"]:
            best_region = max(report["cross_region_analysis"].items(), 
                            key=lambda x: x[1].get("overall_score", 0))
            summary["best_region"] = best_region[0]
        
        # 找出最佳合规级别
        if report["compliance_analysis"]:
            best_compliance = max(report["compliance_analysis"].items(), 
                               key=lambda x: x[1].get("overall_score", 0))
            summary["best_compliance_level"] = best_compliance[0]
        
        return summary
    
    async def close(self):
        """关闭分析器"""
        self.client.close()


async def main():
    """主函数演示高级使用"""
    
    # 创建投资分析器
    analyzer = InvestmentAnalyzer("http://localhost:8000")
    
    try:
        # 连接到服务器
        print("🔌 连接到服务器...")
        connected = await analyzer.promotion.connect_to_server()
        if not connected:
            print("❌ 无法连接到服务器")
            return
        
        # 定义分析参数
        project_ids = ["ai-auto-pilot-2024", "robotics-care-2024", "quantum-sensor-2024"]
        regions = ["上海", "深圳", "杭州"]
        
        # 生成综合投资报告
        print("\n📊 开始综合分析...")
        investment_report = await analyzer.generate_investment_report(
            project_ids, 
            regions
        )
        
        # 输出报告
        print("\n" + "="*60)
        print("📋 综合投资分析报告")
        print("="*60)
        
        print(f"\n📊 分析摘要:")
        summary = investment_report["analysis_summary"]
        print(f"  总项目数: {summary['total_projects']}")
        print(f"  总地区数: {summary['total_regions']}")
        print(f"  平均评分: {summary['average_score']:.1f}")
        print(f"  高分项目: {summary['high_score_projects']}")
        print(f"  中等项目: {summary['medium_score_projects']}")
        print(f"  低分项目: {summary['low_score_projects']}")
        print(f"  最佳地区: {summary['best_region']}")
        print(f"  最佳合规级别: {summary['best_compliance_level']}")
        
        print(f"\n🎯 投资建议:")
        for recommendation in investment_report["investment_recommendations"]:
            print(f"  • {recommendation}")
        
        # 保存报告到文件
        report_file = "investment_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(investment_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 报告已保存到: {report_file}")
        
    finally:
        # 关闭分析器
        await analyzer.close()


if __name__ == "__main__":
    asyncio.run(main())