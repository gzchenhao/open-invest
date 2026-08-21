"""
项目评估工具
为地方政府招商局提供项目评估和匹配功能
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..api.protocol_client import ProtocolClient, ClientType

logger = logging.getLogger(__name__)


class MatchScore(str, Enum):
    """匹配评分"""
    EXCELLENT = "excellent"    # 优秀 (90-100)
    GOOD = "good"            # 良好 (70-89)
    FAIR = "fair"            # 一般 (50-69)
    POOR = "poor"            # 较差 (30-49)
    VERY_POOR = "very_poor"  # 很差 (0-29)


@dataclass
class ProjectMatchResult:
    """项目匹配结果"""
    project_id: str
    project_name: str
    location: str
    industry: str
    tech_readiness_score: float
    landing_requirements_score: float
    economic_compliance_score: float
    overall_score: float
    match_level: MatchScore
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    timeline: Dict[str, str]


class ProjectEvaluator:
    """项目评估器"""
    
    def __init__(self, protocol_client: ProtocolClient):
        """
        初始化项目评估器
        
        Args:
            protocol_client: 协议客户端
        """
        self.client = protocol_client
        self.client.change_client_type(ClientType.GOV)
        
        # 评估权重
        self.weights = {
            "tech_readiness": 0.3,      # 技术成熟度权重
            "landing_requirements": 0.4,  # 落地要求权重
            "economic_compliance": 0.3   # 经济合规权重
        }
        
        logger.info("ProjectEvaluator initialized")
    
    def evaluate_project(self, project_id: str, target_location: str, 
                        compliance_level: str = "standard") -> Optional[ProjectMatchResult]:
        """
        评估项目匹配度
        
        Args:
            project_id: 项目ID
            target_location: 目标地区
            compliance_level: 合规级别
            
        Returns:
            Optional[ProjectMatchResult]: 评估结果，如果失败则返回None
        """
        try:
            logger.info(f"Evaluating project {project_id} for location {target_location}")
            
            # 获取技术成熟度信息
            tech_info = self.client.get_tech_readiness(project_id)
            if not tech_info:
                logger.error(f"Failed to get tech readiness for project {project_id}")
                return None
            
            # 获取落地要求信息
            landing_info = self.client.get_landing_requirements(
                target_location, 
                tech_info.get("industry", ""),
                tech_info.get("scale", "medium")
            )
            if not landing_info:
                logger.error(f"Failed to get landing requirements for {target_location}")
                return None
            
            # 获取经济合规信息
            compliance_info = self.client.get_economic_and_compliance(
                project_id, 
                target_location, 
                compliance_level
            )
            if not compliance_info:
                logger.error(f"Failed to get economic compliance for {target_location}")
                return None
            
            # 计算各项评分
            tech_score = self._calculate_tech_readiness_score(tech_info)
            landing_score = self._calculate_landing_requirements_score(landing_info)
            compliance_score = self._calculate_economic_compliance_score(compliance_info)
            
            # 计算总分
            overall_score = (
                tech_score * self.weights["tech_readiness"] +
                landing_score * self.weights["landing_requirements"] +
                compliance_score * self.weights["economic_compliance"]
            )
            
            # 确定匹配等级
            match_level = self._get_match_level(overall_score)
            
            # 分析优势和劣势
            strengths, weaknesses = self._analyze_strengths_weaknesses(
                tech_score, landing_score, compliance_score
            )
            
            # 生成建议
            recommendations = self._generate_recommendations(
                tech_info, landing_info, compliance_info, 
                strengths, weaknesses, match_level
            )
            
            # 构建评估结果
            result = ProjectMatchResult(
                project_id=project_id,
                project_name=tech_info.get("name", ""),
                location=target_location,
                industry=tech_info.get("industry", ""),
                tech_readiness_score=tech_score,
                landing_requirements_score=landing_score,
                economic_compliance_score=compliance_score,
                overall_score=overall_score,
                match_level=match_level,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                timeline={
                    "evaluation_complete": "已完成",
                    "next_steps": "根据建议制定具体计划"
                }
            )
            
            logger.info(f"Evaluation completed for project {project_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating project {project_id}: {str(e)}")
            return None
    
    def _calculate_tech_readiness_score(self, tech_info: Dict[str, Any]) -> float:
        """
        计算技术成熟度评分
        
        Args:
            tech_info: 技术成熟度信息
            
        Returns:
            float: 评分 (0-100)
        """
        level_scores = {
            "concept": 20,
            "proof_of_concept": 40,
            "prototype": 60,
            "pilot": 80,
            "production": 100
        }
        
        base_score = level_scores.get(tech_info.get("level", "concept"), 20)
        
        # 根据里程碑完成情况调整
        milestones = tech_info.get("milestones", [])
        completed_milestones = len([m for m in milestones if m.endswith("完成")])
        milestone_bonus = (completed_milestones / len(milestones)) * 20 if milestones else 0
        
        # 根据风险数量调整
        risks = tech_info.get("risks", [])
        risk_penalty = min(len(risks) * 5, 20)
        
        final_score = max(0, min(100, base_score + milestone_bonus - risk_penalty))
        return round(final_score, 2)
    
    def _calculate_landing_requirements_score(self, landing_info: Dict[str, Any]) -> float:
        """
        计算落地要求评分
        
        Args:
            landing_info: 落地要求信息
            
        Returns:
            float: 评分 (0-100)
        """
        base_score = 70  # 基础分
        
        # 根据优惠政策数量调整
        incentives = landing_info.get("incentives", [])
        incentive_bonus = min(len(incentives) * 5, 20)
        
        # 根据基础设施条件调整
        infrastructure = landing_info.get("infrastructure", [])
        infrastructure_bonus = min(len(infrastructure) * 3, 15)
        
        # 根据时间线调整
        timeline = landing_info.get("timeline", {})
        if "审批" in timeline:
            approval_time = timeline.get("审批", "")
            if "1-2周" in approval_time:
                time_bonus = 10
            elif "1个月" in approval_time:
                time_bonus = 5
            else:
                time_bonus = 0
        else:
            time_bonus = 0
        
        final_score = base_score + incentive_bonus + infrastructure_bonus + time_bonus
        return round(min(100, final_score), 2)
    
    def _calculate_economic_compliance_score(self, compliance_info: Dict[str, Any]) -> float:
        """
        计算经济合规评分
        
        Args:
            compliance_info: 经济合规信息
            
        Returns:
            float: 评分 (0-100)
        """
        base_score = 80  # 基础分
        
        # 根据合规状态调整
        compliance_status = compliance_info.get("compliance_status", "")
        if "严格监管" in compliance_status:
            status_penalty = 10
        elif "创新监管" in compliance_status:
            status_bonus = 5
        else:
            status_penalty = 0
        
        # 根据成本调整
        costs = compliance_info.get("estimated_costs", {})
        total_setup_cost = costs.get("setup", 0)
        if total_setup_cost > 200000:
            cost_penalty = min((total_setup_cost - 200000) / 10000, 20)
        else:
            cost_penalty = 0
        
        # 根据风险数量调整
        risks = compliance_info.get("risks", [])
        risk_penalty = min(len(risks) * 3, 15)
        
        final_score = base_score + status_bonus - status_penalty - cost_penalty - risk_penalty
        return round(max(0, final_score), 2)
    
    def _get_match_level(self, score: float) -> MatchScore:
        """
        根据评分确定匹配等级
        
        Args:
            score: 评分
            
        Returns:
            MatchScore: 匹配等级
        """
        if score >= 90:
            return MatchScore.EXCELLENT
        elif score >= 70:
            return MatchScore.GOOD
        elif score >= 50:
            return MatchScore.FAIR
        elif score >= 30:
            return MatchScore.POOR
        else:
            return MatchScore.VERY_POOR
    
    def _analyze_strengths_weaknesses(self, tech_score: float, landing_score: float, 
                                   compliance_score: float) -> Tuple[List[str], List[str]]:
        """
        分析优势和劣势
        
        Args:
            tech_score: 技术评分
            landing_score: 落地评分
            compliance_score: 合规评分
            
        Returns:
            Tuple[List[str], List[str]]: 优势和劣势列表
        """
        strengths = []
        weaknesses = []
        
        # 分析技术方面
        if tech_score >= 80:
            strengths.append("技术成熟度高，具备商业化条件")
        elif tech_score >= 60:
            strengths.append("技术有一定基础，需要进一步验证")
        else:
            weaknesses.append("技术成熟度较低，存在较大风险")
        
        # 分析落地方面
        if landing_score >= 80:
            strengths.append("落地条件优越，政策支持力度大")
        elif landing_score >= 60:
            strengths.append("落地条件较好，需要进一步对接")
        else:
            weaknesses.append("落地条件一般，需要更多支持")
        
        # 分析合规方面
        if compliance_score >= 80:
            strengths.append("合规风险较低，便于快速推进")
        elif compliance_score >= 60:
            strengths.append("合规风险可控，需要加强管理")
        else:
            weaknesses.append("合规风险较高，需要重点关注")
        
        return strengths, weaknesses
    
    def _generate_recommendations(self, tech_info: Dict[str, Any], landing_info: Dict[str, Any], 
                                compliance_info: Dict[str, Any], strengths: List[str], 
                                weaknesses: List[str], match_level: MatchScore) -> List[str]:
        """
        生成建议
        
        Args:
            tech_info: 技术信息
            landing_info: 落地信息
            compliance_info: 合规信息
            strengths: 优势列表
            weaknesses: 劣势列表
            match_level: 匹配等级
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        # 根据匹配等级给出总体建议
        if match_level == MatchScore.EXCELLENT:
            recommendations.append("建议优先引进，重点关注")
            recommendations.append("提供全方位政策支持")
        elif match_level == MatchScore.GOOD:
            recommendations.append("建议引进，给予政策支持")
            recommendations.append("重点关注技术落地")
        elif match_level == MatchScore.FAIR:
            recommendations.append("可以考虑引进，但需要加强风险评估")
            recommendations.append("制定详细的推进计划")
        else:
            recommendations.append("建议谨慎考虑，需要进一步评估")
            recommendations.append("制定风险管控措施")
        
        # 根据优势给出建议
        for strength in strengths:
            if "技术" in strength:
                recommendations.append("加强技术对接和合作")
            elif "落地" in strength:
                recommendations.append("快速推进落地工作")
            elif "合规" in strength:
                recommendations.append("简化审批流程，加快项目推进")
        
        # 根据劣势给出建议
        for weakness in weaknesses:
            if "技术" in weakness:
                recommendations.append("加强技术验证和支持")
            elif "落地" in weakness:
                recommendations.append("改善落地条件，提供更多支持")
            elif "合规" in weakness:
                recommendations.append("加强合规管理，降低风险")
        
        return recommendations
    
    def batch_evaluate_projects(self, project_ids: List[str], target_location: str, 
                              compliance_level: str = "standard") -> List[ProjectMatchResult]:
        """
        批量评估项目
        
        Args:
            project_ids: 项目ID列表
            target_location: 目标地区
            compliance_level: 合规级别
            
        Returns:
            List[ProjectMatchResult]: 评估结果列表
        """
        results = []
        
        for project_id in project_ids:
            result = self.evaluate_project(project_id, target_location, compliance_level)
            if result:
                results.append(result)
        
        # 按总分排序
        results.sort(key=lambda x: x.overall_score, reverse=True)
        
        return results
    
    def get_project_ranking(self, project_ids: List[str], target_location: str, 
                           compliance_level: str = "standard") -> List[Tuple[str, float]]:
        """
        获取项目排名
        
        Args:
            project_ids: 项目ID列表
            target_location: 目标地区
            compliance_level: 合规级别
            
        Returns:
            List[Tuple[str, float]]: 项目ID和总分列表，按分数排序
        """
        results = self.batch_evaluate_projects(project_ids, target_location, compliance_level)
        return [(result.project_id, result.overall_score) for result in results]