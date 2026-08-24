"""
Open Invest Protocol Client
地方政府招商局客户端主程序
"""

import logging
import asyncio
import sys
import os
from typing import List, Dict, Any
from dataclasses import dataclass

# 添加项目根目录到 Python 路径（保证直接运行与测试导入行为一致）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.api.protocol_client import ProtocolClient, ClientType
from client.utils.project_evaluator import ProjectEvaluator, ProjectMatchResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class InvestmentProject:
    """投资项目信息"""
    id: str
    name: str
    industry: str
    scale: str
    description: str
    target_location: str
    priority: str = "medium"


class GovernmentInvestmentPromotion:
    """政府招商引资服务"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        初始化招商引资服务
        
        Args:
            server_url: 服务器URL
        """
        self.server_url = server_url
        self.client = ProtocolClient(server_url, ClientType.GOV)
        self.evaluator = ProjectEvaluator(self.client)
        
        # 示例项目数据
        self.sample_projects = [
            InvestmentProject(
                id="ai-auto-pilot-2024",
                name="AI自动驾驶系统",
                industry="autonomous_driving",
                scale="large",
                description="基于深度学习的自动驾驶系统，已实现L3级别自动驾驶功能",
                target_location="上海",
                priority="high"
            ),
            InvestmentProject(
                id="robotics-care-2024",
                name="护理机器人系统",
                industry="embodied_ai",
                scale="medium",
                description="智能护理机器人，提供老人和病人的日常护理服务",
                target_location="深圳",
                priority="medium"
            ),
            InvestmentProject(
                id="quantum-sensor-2024",
                name="量子传感器",
                industry="quantum_computing",
                scale="small",
                description="基于量子技术的超高精度传感器",
                target_location="杭州",
                priority="low"
            )
        ]
        
        logger.info(f"Government Investment Promotion service initialized for {server_url}")
    
    async def connect_to_server(self) -> bool:
        """
        连接到服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 健康检查
            health = self.client.health_check()
            if health.get("status") == "healthy":
                logger.info("Successfully connected to server")
                return True
            else:
                logger.error(f"Server health check failed: {health}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to server: {str(e)}")
            return False
    
    async def evaluate_single_project(self, project: InvestmentProject) -> Dict[str, Any]:
        """
        评估单个项目
        
        Args:
            project: 投资项目
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        try:
            logger.info(f"Evaluating project: {project.name}")
            
            # 评估项目
            result = self.evaluator.evaluate_project(
                project.id, 
                project.target_location, 
                "standard"
            )
            
            if not result:
                return {
                    "project_id": project.id,
                    "project_name": project.name,
                    "status": "failed",
                    "error": "Evaluation failed"
                }
            
            # 格式化结果
            formatted_result = {
                "project_id": result.project_id,
                "project_name": result.project_name,
                "location": result.location,
                "industry": result.industry,
                "overall_score": result.overall_score,
                "match_level": result.match_level.value,
                "tech_readiness_score": result.tech_readiness_score,
                "landing_requirements_score": result.landing_requirements_score,
                "economic_compliance_score": result.economic_compliance_score,
                "strengths": result.strengths,
                "weaknesses": result.weaknesses,
                "recommendations": result.recommendations,
                "priority": project.priority,
                "status": "success"
            }
            
            logger.info(f"Project {project.name} evaluated successfully")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error evaluating project {project.name}: {str(e)}")
            return {
                "project_id": project.id,
                "project_name": project.name,
                "status": "failed",
                "error": str(e)
            }
    
    async def evaluate_all_projects(self) -> List[Dict[str, Any]]:
        """
        评估所有项目
        
        Returns:
            List[Dict[str, Any]]: 评估结果列表
        """
        logger.info("Starting evaluation of all projects")
        
        results = []
        for project in self.sample_projects:
            result = await self.evaluate_single_project(project)
            results.append(result)
        
        # 按总分排序
        results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        
        logger.info("All projects evaluated successfully")
        return results
    
    async def get_project_ranking(self) -> List[Dict[str, Any]]:
        """
        获取项目排名
        
        Returns:
            List[Dict[str, Any]]: 项目排名列表
        """
        logger.info("Getting project ranking")
        
        project_ids = [project.id for project in self.sample_projects]
        rankings = self.evaluator.get_project_ranking(
            project_ids, 
            "上海",  # 默认使用上海作为目标地区
            "standard"
        )
        
        # 格式化排名结果
        formatted_rankings = []
        for project_id, score in rankings:
            project = next((p for p in self.sample_projects if p.id == project_id), None)
            if project:
                formatted_rankings.append({
                    "rank": len(formatted_rankings) + 1,
                    "project_id": project_id,
                    "project_name": project.name,
                    "score": score,
                    "industry": project.industry,
                    "target_location": project.target_location,
                    "priority": project.priority
                })
        
        logger.info("Project ranking generated successfully")
        return formatted_rankings
    
    async def get_server_info(self) -> Dict[str, Any]:
        """
        获取服务器信息
        
        Returns:
            Dict[str, Any]: 服务器信息
        """
        try:
            return self.client.get_server_info()
        except Exception as e:
            logger.error(f"Error getting server info: {str(e)}")
            return {"error": str(e)}
    
    async def generate_promotion_report(self) -> Dict[str, Any]:
        """
        生成招商引资报告
        
        Returns:
            Dict[str, Any]: 招商引资报告
        """
        logger.info("Generating promotion report")
        
        # 获取项目排名
        rankings = await self.get_project_ranking()
        
        # 获取评估结果
        evaluations = await self.evaluate_all_projects()
        
        # 统计信息
        total_projects = len(self.sample_projects)
        successful_evaluations = len([e for e in evaluations if e.get("status") == "success"])
        average_score = sum(e.get("overall_score", 0) for e in evaluations) / total_projects
        
        # 按优先级统计
        high_priority = [r for r in rankings if r.get("priority") == "high"]
        medium_priority = [r for r in rankings if r.get("priority") == "medium"]
        low_priority = [r for r in rankings if r.get("priority") == "low"]
        
        # 按匹配等级统计
        excellent_count = len([r for r in rankings if r.get("score", 0) >= 90])
        good_count = len([r for r in rankings if 70 <= r.get("score", 0) < 90])
        fair_count = len([r for r in rankings if 50 <= r.get("score", 0) < 70])
        poor_count = len([r for r in rankings if r.get("score", 0) < 50])
        
        report = {
            "report_title": "招商引资项目评估报告",
            "generated_at": "2024-01-01T00:00:00Z",
            "server_info": await self.get_server_info(),
            "summary": {
                "total_projects": total_projects,
                "successful_evaluations": successful_evaluations,
                "average_score": round(average_score, 2),
                "evaluation_success_rate": round(successful_evaluations / total_projects * 100, 2)
            },
            "priority_distribution": {
                "high_priority": len(high_priority),
                "medium_priority": len(medium_priority),
                "low_priority": len(low_priority)
            },
            "match_level_distribution": {
                "excellent": excellent_count,
                "good": good_count,
                "fair": fair_count,
                "poor": poor_count
            },
            "project_rankings": rankings,
            "detailed_evaluations": evaluations,
            "recommendations": self._generate_recommendations(rankings),
            "next_steps": self._generate_next_steps(rankings)
        }
        
        logger.info("Promotion report generated successfully")
        return report
    
    def _generate_recommendations(self, rankings: List[Dict[str, Any]]) -> List[str]:
        """
        生成建议
        
        Args:
            rankings: 项目排名列表
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        # 前三个项目作为重点推荐
        top_projects = rankings[:3]
        if top_projects:
            recommendations.append(f"重点推荐项目: {', '.join([p['project_name'] for p in top_projects])}")
        
        # 高分项目建议
        high_score_projects = [p for p in rankings if p.get('score', 0) >= 80]
        if high_score_projects:
            recommendations.append(f"高分项目建议优先引进: {len(high_score_projects)}个")
        
        # 中等分数项目建议
        medium_score_projects = [p for p in rankings if 60 <= p.get('score', 0) < 80]
        if medium_score_projects:
            recommendations.append(f"中等分数项目需要加强支持: {len(medium_score_projects)}个")
        
        # 低分项目建议
        low_score_projects = [p for p in rankings if p.get('score', 0) < 60]
        if low_score_projects:
            recommendations.append(f"低分项目建议谨慎考虑: {len(low_score_projects)}个")
        
        return recommendations
    
    def _generate_next_steps(self, rankings: List[Dict[str, Any]]) -> List[str]:
        """
        生成下一步行动计划
        
        Args:
            rankings: 项目排名列表
            
        Returns:
            List[str]: 行动计划列表
        """
        next_steps = []
        
        # 立即行动
        next_steps.append("立即联系前3名项目方，进行深入洽谈")
        
        # 短期行动
        next_steps.append("1个月内完成高分项目的实地考察")
        
        # 中期行动
        next_steps.append("3个月内完成政策对接和落地准备")
        
        # 长期行动
        next_steps.append("6个月内完成项目引进和落地")
        
        return next_steps
    
    async def close(self):
        """关闭服务"""
        self.client.close()
        logger.info("Government Investment Promotion service closed")


async def main():
    """主函数"""
    # 创建招商引资服务
    promotion_service = GovernmentInvestmentPromotion()
    
    try:
        # 连接到服务器
        if not await promotion_service.connect_to_server():
            logger.error("Failed to connect to server")
            return
        
        # 生成招商引资报告
        report = await promotion_service.generate_promotion_report()
        
        # 输出报告
        print("\n" + "="*60)
        print("招商引资项目评估报告")
        print("="*60)
        
        print(f"\n📊 报告摘要:")
        print(f"   总项目数: {report['summary']['total_projects']}")
        print(f"   成功评估: {report['summary']['successful_evaluations']}")
        print(f"   平均评分: {report['summary']['average_score']}")
        print(f"   成功率: {report['summary']['evaluation_success_rate']}%")
        
        print(f"\n🎯 优先级分布:")
        print(f"   高优先级: {report['priority_distribution']['high_priority']}个")
        print(f"   中优先级: {report['priority_distribution']['medium_priority']}个")
        print(f"   低优先级: {report['priority_distribution']['low_priority']}个")
        
        print(f"\n📈 匹配等级分布:")
        print(f"   优秀: {report['match_level_distribution']['excellent']}个")
        print(f"   良好: {report['match_level_distribution']['good']}个")
        print(f"   一般: {report['match_level_distribution']['fair']}个")
        print(f"   较差: {report['match_level_distribution']['poor']}个")
        
        print(f"\n🏆 项目排名:")
        for i, project in enumerate(report['project_rankings'][:5], 1):
            print(f"   {i}. {project['project_name']} - {project['score']}分")
        
        print(f"\n💡 建议:")
        for recommendation in report['recommendations']:
            print(f"   • {recommendation}")
        
        print(f"\n📋 下一步行动计划:")
        for step in report['next_steps']:
            print(f"   • {step}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        await promotion_service.close()


if __name__ == "__main__":
    asyncio.run(main())