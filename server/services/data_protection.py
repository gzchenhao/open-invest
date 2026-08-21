"""
数据保护服务
确保核心机密数据不出域，提供数据脱敏和访问控制功能
"""

import logging
import hashlib
import json
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SensitivityLevel(str, Enum):
    """数据敏感级别"""
    PUBLIC = "public"          # 公开数据
    INTERNAL = "internal"      # 内部数据
    CONFIDENTIAL = "confidential"  # 机密数据
    RESTRICTED = "restricted"  # 限制访问数据


@dataclass
class DataField:
    """数据字段定义"""
    name: str
    sensitivity: SensitivityLevel
    description: str
    mask_char: str = "*"
    required: bool = True


class DataProtectionService:
    """数据保护服务类"""
    
    def __init__(self):
        """初始化数据保护服务"""
        self.sensitive_fields = {
            "project_id": DataField("project_id", SensitivityLevel.INTERNAL, "项目ID"),
            "name": DataField("name", SensitivityLevel.INTERNAL, "项目名称"),
            "description": DataField("description", SensitivityLevel.PUBLIC, "项目描述"),
            "contact_info": DataField("contact_info", SensitivityLevel.CONFIDENTIAL, "联系信息"),
            "financial_data": DataField("financial_data", SensitivityLevel.RESTRICTED, "财务数据"),
            "technical_secrets": DataField("technical_secrets", SensitivityLevel.RESTRICTED, "技术秘密"),
            "strategy_info": DataField("strategy_info", SensitivityLevel.CONFIDENTIAL, "战略信息"),
            "timeline": DataField("timeline", SensitivityLevel.INTERNAL, "时间线"),
            "risks": DataField("risks", SensitivityLevel.INTERNAL, "风险评估"),
            "milestones": DataField("milestones", SensitivityLevel.INTERNAL, "里程碑"),
            "requirements": DataField("requirements", SensitivityLevel.PUBLIC, "要求"),
            "incentives": DataField("incentives", SensitivityLevel.PUBLIC, "优惠政策"),
            "infrastructure": DataField("infrastructure", SensitivityLevel.PUBLIC, "基础设施"),
            "compliance_status": DataField("compliance_status", SensitivityLevel.INTERNAL, "合规状态"),
            "estimated_costs": DataField("estimated_costs", SensitivityLevel.CONFIDENTIAL, "预计成本"),
            "compliance_requirements": DataField("compliance_requirements", SensitivityLevel.INTERNAL, "合规要求")
        }
        
        # 访问控制配置
        self.access_control = {
            "public_client": {
                "allowed_sensitivity": [SensitivityLevel.PUBLIC],
                "allowed_fields": ["description", "requirements", "incentives", "infrastructure"]
            },
            "gov_client": {
                "allowed_sensitivity": [SensitivityLevel.PUBLIC, SensitivityLevel.INTERNAL],
                "allowed_fields": ["description", "timeline", "milestones", "risks", "requirements", 
                                "incentives", "infrastructure", "compliance_status"]
            },
            "partner_client": {
                "allowed_sensitivity": [SensitivityLevel.PUBLIC, SensitivityLevel.INTERNAL, SensitivityLevel.CONFIDENTIAL],
                "allowed_fields": ["name", "description", "timeline", "milestones", "risks", 
                                "requirements", "incentives", "infrastructure", "compliance_status",
                                "estimated_costs", "compliance_requirements"]
            },
            "internal_client": {
                "allowed_sensitivity": [SensitivityLevel.PUBLIC, SensitivityLevel.INTERNAL, 
                                     SensitivityLevel.CONFIDENTIAL, SensitivityLevel.RESTRICTED],
                "allowed_fields": ["all"]
            }
        }
        
        # 数据脱敏规则
        self.masking_rules = {
            "phone": lambda x: f"{x[:3]}****{x[-4:]}" if len(x) >= 7 else "****",
            "email": lambda x: f"{x.split('@')[0]}@***" if '@' in x else "***",
            "id_number": lambda x: f"{x[:6]}********{x[-4:]}" if len(x) >= 18 else "********",
            "bank_account": lambda x: f"{x[:4]}********{x[-4:]}" if len(x) >= 8 else "********",
            "address": lambda x: x[:2] + "****" + x[-2:] if len(x) > 4 else "****"
        }
    
    def mask_sensitive_data(self, data: Dict[str, Any], client_type: str = "public_client") -> Dict[str, Any]:
        """
        对敏感数据进行脱敏处理
        
        Args:
            data: 原始数据
            client_type: 客户端类型
            
        Returns:
            Dict[str, Any]: 脱敏后的数据
        """
        try:
            if not data:
                return {}
            
            # 获取客户端访问权限
            client_config = self.access_control.get(client_type, self.access_control["public_client"])
            
            masked_data = {}
            
            for field_name, field_value in data.items():
                field_info = self.sensitive_fields.get(field_name)
                
                if not field_info:
                    # 未定义的字段，默认脱敏
                    masked_data[field_name] = self._apply_masking(field_value)
                    continue
                
                # 检查访问权限
                if not self._has_access(field_info, client_config):
                    masked_data[field_name] = self._apply_masking(field_value)
                else:
                    # 根据敏感级别决定是否脱敏
                    if field_info.sensitivity in [SensitivityLevel.CONFIDENTIAL, SensitivityLevel.RESTRICTED]:
                        masked_data[field_name] = self._apply_masking(field_value)
                    else:
                        masked_data[field_name] = field_value
            
            logger.info(f"Data masking applied for client type: {client_type}")
            return masked_data
            
        except Exception as e:
            logger.error(f"Error masking data: {str(e)}")
            return data
    
    def _has_access(self, field: DataField, client_config: Dict[str, Any]) -> bool:
        """检查客户端是否有访问权限"""
        if client_config["allowed_fields"] == ["all"]:
            return True
        
        allowed_sensitivity = client_config["allowed_sensitivity"]
        return field.sensitivity in allowed_sensitivity and field.name in client_config["allowed_fields"]
    
    def _apply_masking(self, value: Any) -> Any:
        """应用脱敏规则"""
        if isinstance(value, str):
            # 检查是否匹配脱敏规则
            for pattern, mask_func in self.masking_rules.items():
                if pattern in value.lower():
                    return mask_func(value)
            
            # 默认脱敏
            return f"{value[:2]}****{value[-2:]}" if len(value) > 4 else "****"
        
        elif isinstance(value, dict):
            return {k: self._apply_masking(v) for k, v in value.items()}
        
        elif isinstance(value, list):
            return [self._apply_masking(item) for item in value]
        
        else:
            return value
    
    def validate_data_access(self, data: Dict[str, Any], client_type: str) -> bool:
        """
        验证数据访问权限
        
        Args:
            data: 要验证的数据
            client_type: 客户端类型
            
        Returns:
            bool: 是否有访问权限
        """
        try:
            client_config = self.access_control.get(client_type, self.access_control["public_client"])
            
            for field_name, field_value in data.items():
                field_info = self.sensitive_fields.get(field_name)
                
                if field_info and not self._has_access(field_info, client_config):
                    logger.warning(f"Access denied for field: {field_name}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating data access: {str(e)}")
            return False
    
    def hash_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        对敏感数据进行哈希处理（用于内部审计）
        
        Args:
            data: 原始数据
            
        Returns:
            Dict[str, Any]: 哈希处理后的数据
        """
        try:
            hashed_data = {}
            
            for field_name, field_value in data.items():
                field_info = self.sensitive_fields.get(field_name)
                
                if field_info and field_info.sensitivity in [SensitivityLevel.CONFIDENTIAL, SensitivityLevel.RESTRICTED]:
                    # 对敏感字段进行哈希处理
                    if isinstance(field_value, str):
                        hashed_data[field_name] = hashlib.sha256(field_value.encode()).hexdigest()
                    elif isinstance(field_value, dict):
                        hashed_data[field_name] = {
                            k: hashlib.sha256(str(v).encode()).hexdigest() 
                            for k, v in field_value.items()
                        }
                    elif isinstance(field_value, list):
                        hashed_data[field_name] = [
                            hashlib.sha256(str(item).encode()).hexdigest() 
                            for item in field_value
                        ]
                else:
                    hashed_data[field_name] = field_value
            
            return hashed_data
            
        except Exception as e:
            logger.error(f"Error hashing sensitive data: {str(e)}")
            return data
    
    def get_audit_log(self, operation: str, client_type: str, data_hash: str) -> Dict[str, Any]:
        """
        生成审计日志
        
        Args:
            operation: 操作类型
            client_type: 客户端类型
            data_hash: 数据哈希值
            
        Returns:
            Dict[str, Any]: 审计日志
        """
        return {
            "timestamp": "2024-01-01T00:00:00Z",  # 实际应该使用当前时间
            "operation": operation,
            "client_type": client_type,
            "data_hash": data_hash,
            "status": "success"
        }
    
    def get_client_types(self) -> List[str]:
        """获取支持的客户端类型"""
        return list(self.access_control.keys())
    
    def get_sensitivity_levels(self) -> List[str]:
        """获取数据敏感级别列表"""
        return [level.value for level in SensitivityLevel]