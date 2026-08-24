"""
服务器测试
测试服务端功能和API端点
"""

import pytest
import json
import asyncio
from typing import Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.main import app
from schema.types import TechReadinessRequest, LandingRequirementsRequest, EconomicComplianceRequest


class TestServer:
    """服务器测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """测试根端点"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "Open Invest Protocol Server"
        assert "version" in data
        assert "endpoints" in data
    
    def test_health_endpoint(self):
        """测试健康检查端点"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
    
    def test_json_rpc_endpoint_valid_request(self):
        """测试有效的JSON-RPC请求"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "get_tech_readiness",
            "params": {"project_id": "ai-auto-pilot-2024"},
            "id": "test-001"
        }
        
        response = self.client.post("/rpc", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "jsonrpc" in data
        assert data["jsonrpc"] == "2.0"
        assert "result" in data
        assert "id" in data
        assert data["id"] == "test-001"
        
        # 验证响应内容
        result = data["result"]
        assert "project_id" in result
        assert "level" in result
        assert "description" in result
        assert "timeline" in result
        assert "milestones" in result
        assert "risks" in result
    
    def test_json_rpc_endpoint_invalid_method(self):
        """测试无效的方法"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "invalid_method",
            "params": {},
            "id": "test-002"
        }
        
        response = self.client.post("/rpc", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "jsonrpc" in data
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found
        assert data["id"] == "test-002"
    
    def test_json_rpc_endpoint_missing_params(self):
        """测试缺少参数"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "get_tech_readiness",
            "params": {},  # 缺少project_id
            "id": "test-003"
        }
        
        response = self.client.post("/rpc", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "jsonrpc" in data
        assert "error" in data
        assert data["error"]["code"] == -32600  # Invalid request
        assert "Missing required parameter" in data["error"]["message"]
    
    def test_json_rpc_endpoint_invalid_json(self):
        """测试无效的JSON（JSON-RPC 2.0 规范：解析错误返回 -32700 信封，而非 REST 式 422）"""
        response = self.client.post("/rpc", data="invalid json")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32700  # Parse error
    
    def test_tech_readiness_endpoint(self):
        """测试技术成熟度端点"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "get_tech_readiness",
            "params": {"project_id": "ai-auto-pilot-2024"},
            "id": "test-004"
        }
        
        response = self.client.post("/rpc", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应内容
        result = data["result"]
        assert result["project_id"] == "ai-auto-pilot-2024"
        assert result["level"] == "prototype"
        # "AI自动驾驶系统"是项目名称（name 字段），描述为另一段业务文案，不得混用
        assert result["name"] == "AI自动驾驶系统"
        assert result["description"]
        assert "2024-Q1" in result["timeline"]
        assert "算法模型训练完成" in result["milestones"]
        assert "算法安全性验证" in result["risks"]
    
    def test_landing_requirements_endpoint(self):
        """测试落地要求端点"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "get_landing_requirements",
            "params": {
                "location": "上海",
                "industry": "autonomous_driving",
                "project_scale": "large"
            },
            "id": "test-005"
        }
        
        response = self.client.post("/rpc", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应内容
        result = data["result"]
        assert result["location"] == "上海"
        assert result["industry"] == "autonomous_driving"
        assert "requirements" in result
        assert "incentives" in result
        assert "infrastructure" in result
        assert "timeline" in result
        
        # 验证要求内容
        requirements = result["requirements"]
        assert len(requirements) > 0
        assert any(req["type"] == "资质要求" for req in requirements)
    
    def test_economic_compliance_endpoint(self):
        """测试经济合规端点"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "get_economic_and_compliance",
            "params": {
                "project_id": "ai-auto-pilot-2024",
                "region": "上海",
                "compliance_level": "standard"
            },
            "id": "test-006"
        }
        
        response = self.client.post("/rpc", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应内容
        result = data["result"]
        assert result["project_id"] == "ai-auto-pilot-2024"
        assert result["region"] == "上海"
        assert result["compliance_status"] == "严格监管"
        assert "requirements" in result
        assert "timeline" in result
        assert "estimated_costs" in result
        assert "risks" in result
        
        # 验证成本估算
        costs = result["estimated_costs"]
        assert "setup" in costs
        assert "monthly" in costs
        assert costs["setup"] > 0
    
    def test_batch_requests(self):
        """测试批量请求"""
        requests = [
            {
                "jsonrpc": "2.0",
                "method": "get_tech_readiness",
                "params": {"project_id": "ai-auto-pilot-2024"},
                "id": "batch-001"
            },
            {
                "jsonrpc": "2.0",
                "method": "get_landing_requirements",
                "params": {
                    "location": "深圳",
                    "industry": "embodied_ai",
                    "project_scale": "medium"
                },
                "id": "batch-002"
            }
        ]
        
        # 发送多个请求
        for request in requests:
            response = self.client.post("/rpc", json=request)
            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert data["id"] == request["id"]
    
    def test_cors_headers(self):
        """测试CORS头部（需携带 Origin 的预检请求，CORS 中间件才会返回相应头部）"""
        response = self.client.options("/rpc", headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "POST"
        })
        
        # 验证CORS头部（allow_origins=["*"] + allow_credentials=True 时，
        # Starlette 会回显请求 Origin，并放行凭据与全部方法）
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://example.com"
        assert response.headers["access-control-allow-credentials"] == "true"
        assert "POST" in response.headers["access-control-allow-methods"]
    
    def test_error_handling(self):
        """测试错误处理（JSON-RPC 2.0 规范：非法请求返回 -32600 信封，而非 REST 式 422）"""
        # 测试空的请求体（缺少 jsonrpc 与 method）
        response = self.client.post("/rpc", json={})
        assert response.status_code == 200
        assert response.json()["error"]["code"] == -32600  # Invalid Request
        
        # 测试缺少jsonrpc字段
        response = self.client.post("/rpc", json={
            "method": "get_tech_readiness",
            "params": {"project_id": "test"},
            "id": "test-error"
        })
        assert response.status_code == 200
        assert response.json()["error"]["code"] == -32600
        
        # 测试无效的jsonrpc版本
        response = self.client.post("/rpc", json={
            "jsonrpc": "1.0",
            "method": "get_tech_readiness",
            "params": {"project_id": "test"},
            "id": "test-error"
        })
        assert response.status_code == 200
        assert response.json()["error"]["code"] == -32600


class TestTechReadinessService:
    """技术成熟度服务测试"""
    
    def setup_method(self):
        """测试设置"""
        from server.services.tech_readiness_service import TechReadinessService
        self.service = TechReadinessService()
    
    def test_get_tech_readiness_success(self):
        """测试成功获取技术成熟度"""
        result = asyncio.run(self.service.get_tech_readiness({
            "project_id": "ai-auto-pilot-2024"
        }))
        
        assert result.project_id == "ai-auto-pilot-2024"
        assert result.level.value == "prototype"
        # "AI自动驾驶系统"是项目名称（name 字段），描述为另一段业务文案，不得混用
        assert result.name == "AI自动驾驶系统"
        assert result.description
        assert len(result.timeline) > 0
        assert len(result.milestones) > 0
        assert len(result.risks) > 0
    
    def test_get_tech_readiness_invalid_project(self):
        """测试无效的项目ID"""
        from server.services.tech_readiness_service import ValidationError
        
        with pytest.raises(ValidationError):
            asyncio.run(self.service.get_tech_readiness({
                "project_id": "invalid_project"
            }))
    
    def test_get_tech_readiness_missing_params(self):
        """测试缺少参数"""
        from server.services.tech_readiness_service import ValidationError
        
        with pytest.raises(ValidationError):
            asyncio.run(self.service.get_tech_readiness({}))
    
    def test_get_available_projects(self):
        """测试获取可用项目"""
        result = self.service.get_available_projects()
        
        assert "projects" in result
        assert "total" in result
        assert result["total"] > 0
        assert "ai-auto-pilot-2024" in result["projects"]
    
    def test_add_project(self):
        """测试添加项目"""
        project_data = {
            "name": "测试项目",
            "industry": "autonomous_driving",
            "level": "concept",
            "description": "测试描述",
            "timeline": {},
            "milestones": [],
            "risks": []
        }
        
        result = self.service.add_project("test-project-2024", project_data)
        assert result == True
        
        # 验证项目是否添加成功
        projects = self.service.get_available_projects()
        assert "test-project-2024" in projects["projects"]


class TestLandingRequirementsService:
    """落地要求服务测试"""
    
    def setup_method(self):
        """测试设置"""
        from server.services.landing_requirements_service import LandingRequirementsService
        self.service = LandingRequirementsService()
    
    def test_get_landing_requirements_success(self):
        """测试成功获取落地要求"""
        result = asyncio.run(self.service.get_landing_requirements({
            "location": "上海",
            "industry": "autonomous_driving",
            "project_scale": "large"
        }))
        
        assert result.location == "上海"
        assert result.industry == "autonomous_driving"
        assert len(result.requirements) > 0
        assert len(result.incentives) > 0
        assert len(result.infrastructure) > 0
        assert result.timeline is not None  # pydantic 模型不支持 dict 式 'in'，改用字段存在性断言
    
    def test_get_landing_requirements_invalid_location(self):
        """测试无效的地区"""
        from server.services.landing_requirements_service import ValidationError
        
        with pytest.raises(ValidationError):
            asyncio.run(self.service.get_landing_requirements({
                "location": "无效地区",
                "industry": "autonomous_driving"
            }))
    
    def test_get_supported_locations(self):
        """测试获取支持的地区"""
        result = self.service.get_supported_locations()
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "上海" in result
        assert "深圳" in result
        assert "杭州" in result
    
    def test_get_supported_industries(self):
        """测试获取支持的行业"""
        result = self.service.get_supported_industries()
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "autonomous_driving" in result
        assert "embodied_ai" in result
        assert "quantum_computing" in result


class TestEconomicComplianceService:
    """经济合规服务测试"""
    
    def setup_method(self):
        """测试设置"""
        from server.services.economic_compliance_service import EconomicComplianceService
        self.service = EconomicComplianceService()
    
    def test_get_economic_compliance_success(self):
        """测试成功获取经济合规信息"""
        result = asyncio.run(self.service.get_economic_and_compliance({
            "project_id": "ai-auto-pilot-2024",
            "region": "上海",
            "compliance_level": "standard"
        }))
        
        assert result.project_id == "ai-auto-pilot-2024"
        assert result.region == "上海"
        assert result.compliance_status == "严格监管"
        assert len(result.requirements) > 0
        assert result.timeline is not None  # pydantic 模型不支持 dict 式 'in'，改用字段存在性断言
        assert result.estimated_costs is not None
        assert len(result.risks) > 0
    
    def test_get_compliance_levels(self):
        """测试获取合规级别"""
        result = self.service.get_compliance_levels()
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "basic" in result
        assert "standard" in result
        assert "enhanced" in result
    
    def test_get_supported_regions(self):
        """测试获取支持的地区"""
        result = self.service.get_supported_regions()
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "上海" in result
        assert "深圳" in result
        assert "杭州" in result
    
    def test_get_compliance_cost_estimate(self):
        """测试获取合规成本估算"""
        result = self.service.get_compliance_cost_estimate("standard", "上海")
        
        assert isinstance(result, dict)
        assert "setup" in result
        assert "monthly" in result
        assert "quarterly" in result
        assert "yearly" in result
        assert all(isinstance(cost, (int, float)) for cost in result.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])