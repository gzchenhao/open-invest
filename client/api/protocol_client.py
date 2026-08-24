"""
Open Invest Protocol Client
地方政府招商局客户端实现
"""

import logging
import json
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ClientType(str, Enum):
    """客户端类型"""
    PUBLIC = "public_client"
    GOV = "gov_client"
    PARTNER = "partner_client"
    INTERNAL = "internal_client"


@dataclass
class ProtocolRequest:
    """协议请求"""
    method: str
    params: Dict[str, Any]
    request_id: Optional[str] = None


@dataclass
class ProtocolResponse:
    """协议响应"""
    jsonrpc: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class ProtocolClient:
    """协议客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000", client_type: ClientType = ClientType.PUBLIC):
        """
        初始化协议客户端
        
        Args:
            base_url: 服务器基础URL
            client_type: 客户端类型
        """
        self.base_url = base_url.rstrip('/')
        self.client_type = client_type
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "OpenInvest-Protocol-Client/1.0.0"
        })
        
        logger.info(f"Initialized protocol client: {base_url} ({client_type})")
    
    def _make_request(self, method: str, params: Dict[str, Any], request_id: Optional[str] = None) -> ProtocolResponse:
        """
        发送协议请求
        
        Args:
            method: 方法名
            params: 参数
            request_id: 请求ID
            
        Returns:
            ProtocolResponse: 响应对象
        """
        try:
            # 构建请求
            request_data = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": request_id or f"req_{method}_{id(self)}"
            }
            
            logger.debug(f"Sending request: {method} with params: {params}")
            
            # 发送请求
            response = self.session.post(
                f"{self.base_url}/rpc",
                json=request_data,
                timeout=30
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            response_data = response.json()
            
            protocol_response = ProtocolResponse(
                jsonrpc=response_data.get("jsonrpc", "2.0"),
                result=response_data.get("result"),
                error=response_data.get("error"),
                id=response_data.get("id")
            )
            
            logger.debug(f"Received response: {protocol_response}")
            return protocol_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return ProtocolResponse(
                jsonrpc="2.0",
                error={
                    "code": -32603,
                    "message": f"Request failed: {str(e)}"
                },
                id=request_id or f"req_{method}_{id(self)}"
            )
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return ProtocolResponse(
                jsonrpc="2.0",
                error={
                    "code": -32700,
                    "message": f"JSON decode error: {str(e)}"
                },
                id=request_id or f"req_{method}_{id(self)}"
            )
    
    def get_tech_readiness(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        获取项目技术成熟度信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            Optional[Dict[str, Any]]: 技术成熟度信息，如果失败则返回None
        """
        params = {"project_id": project_id}
        response = self._make_request("get_tech_readiness", params)
        
        if response.error:
            logger.error(f"Failed to get tech readiness: {response.error}")
            return None
        
        return response.result
    
    def get_landing_requirements(self, location: str, industry: str, project_scale: str = "medium") -> Optional[Dict[str, Any]]:
        """
        获取项目落地要求信息
        
        Args:
            location: 目标地区
            industry: 行业类型
            project_scale: 项目规模
            
        Returns:
            Optional[Dict[str, Any]]: 落地要求信息，如果失败则返回None
        """
        params = {
            "location": location,
            "industry": industry,
            "project_scale": project_scale
        }
        response = self._make_request("get_landing_requirements", params)
        
        if response.error:
            logger.error(f"Failed to get landing requirements: {response.error}")
            return None
        
        return response.result
    
    def get_economic_and_compliance(self, project_id: str, region: str, compliance_level: str = "standard") -> Optional[Dict[str, Any]]:
        """
        获取项目经济合规信息
        
        Args:
            project_id: 项目ID
            region: 目标地区
            compliance_level: 合规级别
            
        Returns:
            Optional[Dict[str, Any]]: 经济合规信息，如果失败则返回None
        """
        params = {
            "project_id": project_id,
            "region": region,
            "compliance_level": compliance_level
        }
        response = self._make_request("get_economic_and_compliance", params)
        
        if response.error:
            logger.error(f"Failed to get economic compliance: {response.error}")
            return None
        
        return response.result
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        获取服务器信息
        
        Returns:
            Dict[str, Any]: 服务器信息
        """
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get server info: {str(e)}")
            return {"error": str(e)}
    
    def batch_request(self, requests: List[ProtocolRequest]) -> List[ProtocolResponse]:
        """
        批量请求
        
        Args:
            requests: 请求列表
            
        Returns:
            List[ProtocolResponse]: 响应列表
        """
        responses = []
        
        for request in requests:
            response = self._make_request(
                request.method,
                request.params,
                request.request_id
            )
            responses.append(response)
        
        return responses
    
    def change_client_type(self, client_type: ClientType):
        """
        更改客户端类型
        
        Args:
            client_type: 新的客户端类型
        """
        self.client_type = client_type
        logger.info(f"Client type changed to: {client_type}")
    
    def get_client_type(self) -> ClientType:
        """
        获取当前客户端类型
        
        Returns:
            ClientType: 当前客户端类型
        """
        return self.client_type
    
    def close(self):
        """关闭客户端（关闭连接并清空适配器，使 session 不再可用）"""
        self.session.close()
        self.session.adapters.clear()
        logger.info("Protocol client closed")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()