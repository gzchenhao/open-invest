"""
Open Invest Protocol - 数据类型定义
定义协议中使用的所有数据结构和类型
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field


class ProjectScale(str, Enum):
    """项目规模枚举"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class ComplianceLevel(str, Enum):
    """合规级别枚举"""
    BASIC = "basic"
    STANDARD = "standard"
    ENHANCED = "enhanced"


class IndustryType(str, Enum):
    """行业类型枚举"""
    AUTONOMOUS_DRIVING = "autonomous_driving"
    EMBODIED_AI = "embodied_ai"
    ROBOTICS = "robotics"
    AI_HARDWARE = "ai_hardware"
    QUANTUM_COMPUTING = "quantum_computing"


class TechReadinessLevel(str, Enum):
    """技术成熟度等级"""
    CONCEPT = "concept"
    PROOF_OF_CONCEPT = "proof_of_concept"
    PROTOTYPE = "prototype"
    PILOT = "pilot"
    PRODUCTION = "production"


class JsonRpcRequest(BaseModel):
    """JSON-RPC 请求模型"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC 版本")
    method: str = Field(description="API 方法名")
    params: Dict[str, Any] = Field(description="方法参数")
    id: Optional[str] = Field(description="请求ID")


class JsonRpcResponse(BaseModel):
    """JSON-RPC 响应模型（按 JSON-RPC 2.0 规范，result 与 error 二选一）"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC 版本")
    result: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")
    error: Optional[Dict[str, Any]] = Field(default=None, description="错误信息")
    id: Optional[str] = Field(default=None, description="请求ID")


class TechReadinessRequest(BaseModel):
    """技术成熟度查询请求"""
    project_id: str = Field(description="项目唯一标识符")


class TechReadinessResponse(BaseModel):
    """技术成熟度查询响应"""
    project_id: str = Field(description="项目唯一标识符")
    level: TechReadinessLevel = Field(description="技术成熟度等级")
    description: str = Field(description="技术成熟度描述")
    timeline: Dict[str, str] = Field(description="预计时间线")
    milestones: List[str] = Field(description="关键里程碑")
    risks: List[str] = Field(description="技术风险")
    # 可选扩展字段（向后兼容）：客户端项目评估器依赖行业信息发起落地要求查询；
    # 项目名称用于评估报告展示（服务侧 projects_data 中本就包含这两个字段）
    name: Optional[str] = Field(default=None, description="项目名称")
    industry: Optional[IndustryType] = Field(default=None, description="行业类型")


class LandingRequirementsRequest(BaseModel):
    """落地要求查询请求"""
    location: str = Field(description="目标地区")
    industry: IndustryType = Field(description="行业类型")
    project_scale: ProjectScale = Field(description="项目规模")


class LandingRequirementsResponse(BaseModel):
    """落地要求查询响应"""
    location: str = Field(description="目标地区")
    industry: IndustryType = Field(description="行业类型")
    requirements: List[Dict[str, Any]] = Field(description="落地要求清单")
    incentives: List[Dict[str, Any]] = Field(description="优惠政策")
    infrastructure: List[str] = Field(description="基础设施条件")
    timeline: Dict[str, str] = Field(description="落地时间线")


class EconomicComplianceRequest(BaseModel):
    """经济合规查询请求"""
    project_id: str = Field(description="项目唯一标识符")
    region: str = Field(description="目标地区")
    compliance_level: ComplianceLevel = Field(description="合规级别要求")


class EconomicComplianceResponse(BaseModel):
    """经济合规查询响应"""
    project_id: str = Field(description="项目唯一标识符")
    region: str = Field(description="目标地区")
    compliance_status: str = Field(description="合规状态")
    requirements: List[Dict[str, Any]] = Field(description="合规要求")
    timeline: Dict[str, str] = Field(description="合规时间线")
    estimated_costs: Dict[str, float] = Field(description="预计成本")
    risks: List[str] = Field(description="合规风险")


class ProjectInfo(BaseModel):
    """项目基本信息"""
    project_id: str = Field(description="项目唯一标识符")
    name: str = Field(description="项目名称")
    industry: IndustryType = Field(description="行业类型")
    scale: ProjectScale = Field(description="项目规模")
    description: str = Field(description="项目描述")
    contact_info: Dict[str, str] = Field(description="联系信息")


class ServerConfig(BaseModel):
    """服务端配置"""
    host: str = Field(default="localhost", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    debug: bool = Field(default=True, description="调试模式")
    data_dir: str = Field(default="./data", description="数据目录")
    max_request_size: int = Field(default=10 * 1024 * 1024, description="最大请求大小")


class ProtocolError(Exception):
    """协议错误基类"""
    def __init__(self, code: int, message: str, data: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(self.message)


class ValidationError(ProtocolError):
    """验证错误"""
    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(-32600, message, data)


class MethodNotFoundError(ProtocolError):
    """方法未找到错误"""
    def __init__(self, method: str):
        super().__init__(-32601, f"Method '{method}' not found")


class InternalError(ProtocolError):
    """内部错误"""
    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(-32603, message, data)