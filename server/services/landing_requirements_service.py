"""
落地要求服务
提供高科技项目落地要求查询功能
"""

import logging
from typing import Dict, Any, List
from schema.types import (
    LandingRequirementsRequest, LandingRequirementsResponse,
    ProjectScale, IndustryType, ValidationError, InternalError
)

logger = logging.getLogger(__name__)


class LandingRequirementsService:
    """落地要求服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.location_data = {
            "上海": {
                "requirements": [
                    {
                        "type": "资质要求",
                        "description": "需要高新技术企业认证",
                        "mandatory": True
                    },
                    {
                        "type": "场地要求",
                        "description": "研发场地面积不少于1000平方米",
                        "mandatory": True
                    },
                    {
                        "type": "人才要求",
                        "description": "核心团队具有相关领域博士学位",
                        "mandatory": False
                    }
                ],
                "incentives": [
                    {
                        "type": "税收优惠",
                        "description": "企业所得税减免15%",
                        "value": "15%"
                    },
                    {
                        "type": "资金支持",
                        "description": "最高500万研发补贴",
                        "value": "最高500万"
                    },
                    {
                        "type": "人才补贴",
                        "description": "高层次人才安家费50万",
                        "value": "50万"
                    }
                ],
                "infrastructure": [
                    "5G网络覆盖",
                    "云计算平台",
                    "测试验证中心",
                    "产业园区配套"
                ]
            },
            "深圳": {
                "requirements": [
                    {
                        "type": "资质要求",
                        "description": "需要科技型中小企业认证",
                        "mandatory": True
                    },
                    {
                        "type": "技术要求",
                        "description": "拥有自主知识产权",
                        "mandatory": True
                    },
                    {
                        "type": "团队要求",
                        "description": "研发人员占比不低于30%",
                        "mandatory": True
                    }
                ],
                "incentives": [
                    {
                        "type": "租金补贴",
                        "description": "办公场地租金补贴50%",
                        "value": "50%"
                    },
                    {
                        "type": "研发补贴",
                        "description": "研发费用加计扣除75%",
                        "value": "75%"
                    },
                    {
                        "type": "人才奖励",
                        "description": "领军人才奖励200万",
                        "value": "200万"
                    }
                ],
                "infrastructure": [
                    "创新基础设施",
                    "产学研合作平台",
                    "国际交流中心",
                    "金融服务体系"
                ]
            },
            "杭州": {
                "requirements": [
                    {
                        "type": "产业要求",
                        "description": "符合杭州重点发展产业方向",
                        "mandatory": True
                    },
                    {
                        "type": "环保要求",
                        "description": "通过环境影响评估",
                        "mandatory": True
                    },
                    {
                        "type": "投资要求",
                        "description": "固定资产投资不低于1000万",
                        "mandatory": True
                    }
                ],
                "incentives": [
                    {
                        "type": "用地支持",
                        "description": "工业用地优先保障",
                        "value": "优先保障"
                    },
                    {
                        "type": "金融支持",
                        "description": "创业担保贷款最高500万",
                        "value": "最高500万"
                    },
                    {
                        "type": "市场支持",
                        "description": "政府采购优先",
                        "value": "优先"
                    }
                ],
                "infrastructure": [
                    "数字经济基础设施",
                    "智能制造基地",
                    "跨境电商平台",
                    "科技创新走廊"
                ]
            }
        }
        
        self.industry_requirements = {
            "autonomous_driving": {
                "special_requirements": [
                    "需要自动驾驶测试牌照",
                    "需要封闭测试场地",
                    "需要数据安全合规"
                ],
                "timeline": {
                    "审批": "1-2个月",
                    "场地准备": "2-3个月",
                    "测试验证": "3-6个月"
                }
            },
            "embodied_ai": {
                "special_requirements": [
                    "需要机器人安全认证",
                    "需要伦理审查",
                    "需要用户隐私保护"
                ],
                "timeline": {
                    "审批": "2-3个月",
                    "产品认证": "3-4个月",
                    "市场准入": "4-6个月"
                }
            },
            "quantum_computing": {
                "special_requirements": [
                    "需要量子安全认证",
                    "需要出口管制合规",
                    "需要技术保密"
                ],
                "timeline": {
                    "审批": "3-4个月",
                    "技术验证": "6-12个月",
                    "商业化": "12-18个月"
                }
            }
        }
    
    async def get_landing_requirements(self, params: Dict[str, Any]) -> LandingRequirementsResponse:
        """
        获取项目落地要求信息
        
        Args:
            params: 包含 location, industry, project_scale 的参数
            
        Returns:
            LandingRequirementsResponse: 落地要求响应
            
        Raises:
            ValidationError: 参数验证失败
            InternalError: 内部处理错误
        """
        try:
            # 验证参数
            if not params:
                raise ValidationError("Missing required parameters")
            
            required_fields = ["location", "industry"]
            for field in required_fields:
                if field not in params:
                    raise ValidationError(f"Missing required parameter: {field}")
            
            location = params["location"]
            industry = params["industry"]
            project_scale = params.get("project_scale", "medium")
            
            # 检查地区是否存在
            if location not in self.location_data:
                raise ValidationError(f"Location '{location}' not supported")
            
            # 获取基础信息
            location_info = self.location_data[location]
            
            # 获取行业特定要求
            industry_info = self.industry_requirements.get(industry, {})
            
            # 根据项目规模调整要求
            scale_adjustments = self._get_scale_adjustments(project_scale)
            
            # 构建响应
            response = LandingRequirementsResponse(
                location=location,
                industry=industry,
                requirements=location_info["requirements"],
                incentives=location_info["incentives"],
                infrastructure=location_info["infrastructure"]
            )
            
            # 添加行业特定要求
            if "special_requirements" in industry_info:
                response.requirements.extend([
                    {
                        "type": "行业特殊要求",
                        "description": req,
                        "mandatory": True
                    }
                    for req in industry_info["special_requirements"]
                ])
            
            # 添加时间线信息
            if "timeline" in industry_info:
                response.timeline = industry_info["timeline"]
            
            logger.info(f"Successfully retrieved landing requirements for {industry} in {location}")
            return response
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting landing requirements: {str(e)}")
            raise InternalError(f"Failed to get landing requirements: {str(e)}")
    
    def _get_scale_adjustments(self, project_scale: str) -> Dict[str, Any]:
        """
        根据项目规模获取调整要求
        
        Args:
            project_scale: 项目规模
            
        Returns:
            Dict[str, Any]: 调整要求
        """
        adjustments = {
            "small": {
                "investment_min": "100万",
                "employment_min": "10人",
                "space_min": "200平方米"
            },
            "medium": {
                "investment_min": "1000万",
                "employment_min": "50人",
                "space_min": "1000平方米"
            },
            "large": {
                "investment_min": "1亿",
                "employment_min": "200人",
                "space_min": "5000平方米"
            }
        }
        return adjustments.get(project_scale, adjustments["medium"])
    
    def get_supported_locations(self) -> List[str]:
        """
        获取支持的地区列表
        
        Returns:
            List[str]: 支持的地区列表
        """
        return list(self.location_data.keys())
    
    def get_supported_industries(self) -> List[str]:
        """
        获取支持的行业列表
        
        Returns:
            List[str]: 支持的行业列表
        """
        return list(self.industry_requirements.keys())