"""
技术成熟度服务
提供高科技项目技术成熟度查询功能
"""

import logging
from typing import Dict, Any
from schema.types import (
    TechReadinessRequest, TechReadinessResponse, 
    TechReadinessLevel, ValidationError, InternalError
)

logger = logging.getLogger(__name__)


class TechReadinessService:
    """技术成熟度服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.projects_data = {
            "ai-auto-pilot-2024": {
                "name": "AI自动驾驶系统",
                "industry": "autonomous_driving",
                "level": "prototype",
                "description": "基于深度学习的自动驾驶系统，已实现L3级别自动驾驶功能",
                "timeline": {
                    "2024-Q1": "完成算法优化",
                    "2024-Q2": "实车测试",
                    "2024-Q3": "小批量生产",
                    "2024-Q4": "商业化部署"
                },
                "milestones": [
                    "算法模型训练完成",
                    "封闭场地测试通过",
                    "开放道路测试启动",
                    "获得相关认证"
                ],
                "risks": [
                    "算法安全性验证",
                    "法规合规性",
                    "硬件可靠性",
                    "用户体验优化"
                ]
            },
            "robotics-care-2024": {
                "name": "护理机器人系统",
                "industry": "embodied_ai",
                "level": "pilot",
                "description": "智能护理机器人，提供老人和病人的日常护理服务",
                "timeline": {
                    "2024-Q1": "用户需求调研",
                    "2024-Q2": "原型机开发",
                    "2024-Q3": "试点医院测试",
                    "2024-Q4": "产品优化迭代"
                },
                "milestones": [
                    "需求分析完成",
                    "原型机研发成功",
                    "试点测试启动",
                    "用户反馈收集"
                ],
                "risks": [
                    "安全性验证",
                    "用户接受度",
                    "成本控制",
                    "法规审批"
                ]
            },
            "quantum-sensor-2024": {
                "name": "量子传感器",
                "industry": "quantum_computing",
                "level": "proof_of_concept",
                "description": "基于量子技术的超高精度传感器",
                "timeline": {
                    "2024-Q1": "理论研究",
                    "2024-Q2": "实验验证",
                    "2024-Q3": "工程样机",
                    "2024-Q4": "性能测试"
                },
                "milestones": [
                    "理论模型建立",
                    "实验室验证",
                    "工程样机完成",
                    "性能指标测试"
                ],
                "risks": [
                    "技术可行性",
                    "工艺实现",
                    "成本控制",
                    "市场需求"
                ]
            }
        }
    
    async def get_tech_readiness(self, params: Dict[str, Any]) -> TechReadinessResponse:
        """
        获取项目技术成熟度信息
        
        Args:
            params: 包含 project_id 的参数
            
        Returns:
            TechReadinessResponse: 技术成熟度响应
            
        Raises:
            ValidationError: 参数验证失败
            InternalError: 内部处理错误
        """
        try:
            # 验证参数
            if not params or "project_id" not in params:
                raise ValidationError("Missing required parameter: project_id")
            
            project_id = params["project_id"]
            
            # 检查项目是否存在
            if project_id not in self.projects_data:
                raise ValidationError(f"Project '{project_id}' not found")
            
            project_data = self.projects_data[project_id]
            
            # 构建响应
            response = TechReadinessResponse(
                project_id=project_id,
                level=TechReadinessLevel(project_data["level"]),
                description=project_data["description"],
                timeline=project_data["timeline"],
                milestones=project_data["milestones"],
                risks=project_data["risks"]
            )
            
            logger.info(f"Successfully retrieved tech readiness for project: {project_id}")
            return response
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting tech readiness: {str(e)}")
            raise InternalError(f"Failed to get tech readiness: {str(e)}")
    
    def get_available_projects(self) -> Dict[str, Any]:
        """
        获取可用项目列表
        
        Returns:
            Dict[str, Any]: 项目列表信息
        """
        return {
            "projects": list(self.projects_data.keys()),
            "total": len(self.projects_data)
        }
    
    def add_project(self, project_id: str, project_data: Dict[str, Any]) -> bool:
        """
        添加新项目（用于测试）
        
        Args:
            project_id: 项目ID
            project_data: 项目数据
            
        Returns:
            bool: 添加是否成功
        """
        try:
            if project_id in self.projects_data:
                logger.warning(f"Project '{project_id}' already exists")
                return False
            
            self.projects_data[project_id] = project_data
            logger.info(f"Added new project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding project: {str(e)}")
            return False