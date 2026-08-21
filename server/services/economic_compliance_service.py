"""
经济合规服务
提供高科技项目经济合规查询功能
"""

import logging
from typing import Dict, Any, List
from schema.types import (
    EconomicComplianceRequest, EconomicComplianceResponse,
    ComplianceLevel, ValidationError, InternalError
)

logger = logging.getLogger(__name__)


class EconomicComplianceService:
    """经济合规服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.compliance_data = {
            "basic": {
                "requirements": [
                    {
                        "category": "税务合规",
                        "items": [
                            "增值税一般纳税人资格",
                            "企业所得税申报",
                            "税务登记备案"
                        ]
                    },
                    {
                        "category": "工商合规",
                        "items": [
                            "营业执照年检",
                            "企业年报公示",
                            "经营范围变更"
                        ]
                    },
                    {
                        "category": "劳动合规",
                        "items": [
                            "劳动合同签订",
                            "社保公积金缴纳",
                            "劳动用工备案"
                        ]
                    }
                ],
                "timeline": {
                    "setup": "1-2周",
                    "monthly": "每月",
                    "quarterly": "每季度",
                    "yearly": "每年"
                },
                "estimated_costs": {
                    "setup": 50000,
                    "monthly": 10000,
                    "quarterly": 30000,
                    "yearly": 100000
                },
                "risks": [
                    "税务申报延误",
                    "工商信息变更不及时",
                    "劳动用工纠纷"
                ]
            },
            "standard": {
                "requirements": [
                    {
                        "category": "税务合规",
                        "items": [
                            "增值税一般纳税人资格",
                            "企业所得税申报",
                            "税务登记备案",
                            "税收优惠申请",
                            "转让定价文档"
                        ]
                    },
                    {
                        "category": "工商合规",
                        "items": [
                            "营业执照年检",
                            "企业年报公示",
                            "经营范围变更",
                            "知识产权保护",
                            "反垄断合规"
                        ]
                    },
                    {
                        "category": "劳动合规",
                        "items": [
                            "劳动合同签订",
                            "社保公积金缴纳",
                            "劳动用工备案",
                            "股权激励计划",
                            "员工福利计划"
                        ]
                    },
                    {
                        "category": "财务合规",
                        "items": [
                            "财务审计",
                            "内部控制制度",
                            "信息披露"
                        ]
                    }
                ],
                "timeline": {
                    "setup": "2-4周",
                    "monthly": "每月",
                    "quarterly": "每季度",
                    "yearly": "每年",
                    "audit": "每年"
                },
                "estimated_costs": {
                    "setup": 100000,
                    "monthly": 20000,
                    "quarterly": 60000,
                    "yearly": 200000,
                    "audit": 150000
                },
                "risks": [
                    "税务风险",
                    "法律风险",
                    "财务风险",
                    "声誉风险"
                ]
            },
            "enhanced": {
                "requirements": [
                    {
                        "category": "税务合规",
                        "items": [
                            "增值税一般纳税人资格",
                            "企业所得税申报",
                            "税务登记备案",
                            "税收优惠申请",
                            "转让定价文档",
                            "税务筹划",
                            "跨境税务合规"
                        ]
                    },
                    {
                        "category": "工商合规",
                        "items": [
                            "营业执照年检",
                            "企业年报公示",
                            "经营范围变更",
                            "知识产权保护",
                            "反垄断合规",
                            "数据合规",
                            "出口管制合规"
                        ]
                    },
                    {
                        "category": "劳动合规",
                        "items": [
                            "劳动合同签订",
                            "社保公积金缴纳",
                            "劳动用工备案",
                            "股权激励计划",
                            "员工福利计划",
                            "国际化人才管理",
                            "跨境劳务合规"
                        ]
                    },
                    {
                        "category": "财务合规",
                        "items": [
                            "财务审计",
                            "内部控制制度",
                            "信息披露",
                            "ESG报告",
                            "可持续发展报告"
                        ]
                    },
                    {
                        "category": "合规管理",
                        "items": [
                            "合规体系建设",
                            "风险评估",
                            "合规培训",
                            "内部举报机制"
                        ]
                    }
                ],
                "timeline": {
                    "setup": "4-8周",
                    "monthly": "每月",
                    "quarterly": "每季度",
                    "yearly": "每年",
                    "audit": "每年",
                    "esg_report": "每年"
                },
                "estimated_costs": {
                    "setup": 200000,
                    "monthly": 50000,
                    "quarterly": 150000,
                    "yearly": 400000,
                    "audit": 300000,
                    "esg_report": 200000
                },
                "risks": [
                    "全面合规风险",
                    "国际合规风险",
                    "ESG风险",
                    "供应链风险"
                ]
            }
        }
        
        self.region_specific = {
            "上海": {
                "special_requirements": [
                    "张江科学城特殊政策",
                    "临港新片区政策",
                    "科创板上市辅导"
                ],
                "compliance_status": "严格监管"
            },
            "深圳": {
                "special_requirements": [
                    "前海深港合作区政策",
                    "创业板上市辅导",
                    "跨境金融合规"
                ],
                "compliance_status": "创新监管"
            },
            "杭州": {
                "special_requirements": [
                    "数字经济示范区政策",
                    "科创板上市辅导",
                    "跨境电商合规"
                ],
                "compliance_status": "适度监管"
            }
        }
    
    async def get_economic_and_compliance(self, params: Dict[str, Any]) -> EconomicComplianceResponse:
        """
        获取项目经济合规信息
        
        Args:
            params: 包含 project_id, region, compliance_level 的参数
            
        Returns:
            EconomicComplianceResponse: 经济合规响应
            
        Raises:
            ValidationError: 参数验证失败
            InternalError: 内部处理错误
        """
        try:
            # 验证参数
            if not params:
                raise ValidationError("Missing required parameters")
            
            required_fields = ["project_id", "region"]
            for field in required_fields:
                if field not in params:
                    raise ValidationError(f"Missing required parameter: {field}")
            
            project_id = params["project_id"]
            region = params["region"]
            compliance_level = params.get("compliance_level", "standard")
            
            # 验证合规级别
            if compliance_level not in self.compliance_data:
                raise ValidationError(f"Compliance level '{compliance_level}' not supported")
            
            # 获取合规信息
            compliance_info = self.compliance_data[compliance_level]
            
            # 获取地区特定信息
            region_info = self.region_specific.get(region, {})
            
            # 构建响应
            response = EconomicComplianceResponse(
                project_id=project_id,
                region=region,
                compliance_status=region_info.get("compliance_status", "标准监管"),
                requirements=compliance_info["requirements"],
                timeline=compliance_info["timeline"],
                estimated_costs=compliance_info["estimated_costs"],
                risks=compliance_info["risks"]
            )
            
            # 添加地区特殊要求
            if "special_requirements" in region_info:
                response.requirements.append({
                    "category": "地区特殊要求",
                    "items": region_info["special_requirements"]
                })
            
            logger.info(f"Successfully retrieved economic compliance for project {project_id} in {region}")
            return response
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting economic compliance: {str(e)}")
            raise InternalError(f"Failed to get economic compliance: {str(e)}")
    
    def get_compliance_levels(self) -> List[str]:
        """
        获取支持的合规级别列表
        
        Returns:
            List[str]: 合规级别列表
        """
        return list(self.compliance_data.keys())
    
    def get_supported_regions(self) -> List[str]:
        """
        获取支持的地区列表
        
        Returns:
            List[str]: 支持的地区列表
        """
        return list(self.region_specific.keys())
    
    def get_compliance_cost_estimate(self, compliance_level: str, region: str) -> Dict[str, float]:
        """
        获取合规成本估算
        
        Args:
            compliance_level: 合规级别
            region: 地区
            
        Returns:
            Dict[str, float]: 成本估算
        """
        if compliance_level not in self.compliance_data:
            raise ValidationError(f"Compliance level '{compliance_level}' not supported")
        
        base_costs = self.compliance_data[compliance_level]["estimated_costs"]
        
        # 根据地区调整成本
        region_multiplier = {
            "上海": 1.2,
            "深圳": 1.1,
            "杭州": 1.0
        }
        
        multiplier = region_multiplier.get(region, 1.0)
        
        return {
            item: cost * multiplier 
            for item, cost in base_costs.items()
        }