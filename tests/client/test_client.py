"""
客户端测试
测试客户端功能和API调用
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.api.protocol_client import ProtocolClient, ClientType, ProtocolRequest, ProtocolResponse
from client.utils.project_evaluator import ProjectEvaluator, ProjectMatchResult, MatchScore
from client.main import GovernmentInvestmentPromotion, InvestmentProject


class TestProtocolClient:
    """协议客户端测试"""
    
    def setup_method(self):
        """测试设置"""
        self.client = ProtocolClient("http://localhost:8000", ClientType.PUBLIC)
    
    def test_init_client(self):
        """测试客户端初始化"""
        assert self.client.base_url == "http://localhost:8000"
        assert self.client.client_type == ClientType.PUBLIC
        assert self.client.session is not None
    
    def test_client_types(self):
        """测试客户端类型"""
        assert ClientType.PUBLIC == "public_client"
        assert ClientType.GOV == "gov_client"
        assert ClientType.PARTNER == "partner_client"
        assert ClientType.INTERNAL == "internal_client"
    
    def test_make_request_success(self):
        """测试成功请求"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"status": "success"},
            "id": "test-001"
        }
        
        with patch('requests.Session.post', return_value=mock_response):
            response = self.client._make_request("test_method", {"param": "value"})
            
            assert response.jsonrpc == "2.0"
            assert response.result == {"status": "success"}
            assert response.id == "test-001"
    
    def test_make_request_failure(self):
        """测试请求失败"""
        import requests
        
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Connection error")
        
        with patch('requests.Session.post', return_value=mock_response):
            response = self.client._make_request("test_method", {"param": "value"})
            
            assert response.jsonrpc == "2.0"
            assert response.error is not None
            assert response.error["code"] == -32603
            assert "Connection error" in response.error["message"]
    
    def test_make_request_json_error(self):
        """测试JSON解析错误"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        with patch('requests.Session.post', return_value=mock_response):
            response = self.client._make_request("test_method", {"param": "value"})
            
            assert response.jsonrpc == "2.0"
            assert response.error is not None
            assert response.error["code"] == -32700
            assert "JSON decode error" in response.error["message"]
    
    def test_get_tech_readiness(self):
        """测试获取技术成熟度"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {
                "project_id": "test-project",
                "level": "prototype",
                "description": "Test project"
            },
            "id": "test-001"
        }
        
        with patch('requests.Session.post', return_value=mock_response):
            result = self.client.get_tech_readiness("test-project")
            
            assert result is not None
            assert result["project_id"] == "test-project"
            assert result["level"] == "prototype"
    
    def test_get_tech_readiness_failure(self):
        """测试技术成熟度获取失败"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid request"},
            "id": "test-001"
        }
        
        with patch('requests.Session.post', return_value=mock_response):
            result = self.client.get_tech_readiness("invalid-project")
            
            assert result is None
    
    def test_get_landing_requirements(self):
        """测试获取落地要求"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {
                "location": "上海",
                "industry": "autonomous_driving",
                "requirements": []
            },
            "id": "test-001"
        }
        
        with patch('requests.Session.post', return_value=mock_response):
            result = self.client.get_landing_requirements("上海", "autonomous_driving")
            
            assert result is not None
            assert result["location"] == "上海"
            assert result["industry"] == "autonomous_driving"
    
    def test_get_economic_and_compliance(self):
        """测试获取经济合规信息"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {
                "project_id": "test-project",
                "region": "上海",
                "compliance_status": "严格监管"
            },
            "id": "test-001"
        }
        
        with patch('requests.Session.post', return_value=mock_response):
            result = self.client.get_economic_and_compliance("test-project", "上海")
            
            assert result is not None
            assert result["project_id"] == "test-project"
            assert result["region"] == "上海"
    
    def test_health_check(self):
        """测试健康检查"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        
        with patch('requests.Session.get', return_value=mock_response):
            result = self.client.health_check()
            
            assert result["status"] == "healthy"
    
    def test_health_check_failure(self):
        """测试健康检查失败"""
        import requests
        
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Connection error")
        
        with patch('requests.Session.get', return_value=mock_response):
            result = self.client.health_check()
            
            assert result["status"] == "error"
            assert "Connection error" in result["message"]
    
    def test_get_server_info(self):
        """测试获取服务器信息"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "service": "Open Invest Protocol Server",
            "version": "1.0.0"
        }
        
        with patch('requests.Session.get', return_value=mock_response):
            result = self.client.get_server_info()
            
            assert result["service"] == "Open Invest Protocol Server"
            assert result["version"] == "1.0.0"
    
    def test_batch_request(self):
        """测试批量请求"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"status": "success"},
            "id": "test-001"
        }
        
        requests = [
            ProtocolRequest("method1", {"param1": "value1"}),
            ProtocolRequest("method2", {"param2": "value2"})
        ]
        
        with patch('requests.Session.post', return_value=mock_response):
            responses = self.client.batch_request(requests)
            
            assert len(responses) == 2
            assert all(response.result == {"status": "success"} for response in responses)
    
    def test_change_client_type(self):
        """测试更改客户端类型"""
        self.client.change_client_type(ClientType.GOV)
        assert self.client.client_type == ClientType.GOV
    
    def test_context_manager(self):
        """测试上下文管理器"""
        with ProtocolClient("http://localhost:8000") as client:
            assert client.base_url == "http://localhost:8000"
        
        # 验证session已关闭
        assert client.session.adapters == {}


class TestProjectEvaluator:
    """项目评估器测试"""
    
    def setup_method(self):
        """测试设置"""
        self.mock_client = Mock()
        self.evaluator = ProjectEvaluator(self.mock_client)
    
    def test_init_evaluator(self):
        """测试评估器初始化"""
        assert self.evaluator.client == self.mock_client
        assert self.evaluator.weights["tech_readiness"] == 0.3
        assert self.evaluator.weights["landing_requirements"] == 0.4
        assert self.evaluator.weights["economic_compliance"] == 0.3
    
    def test_get_match_level(self):
        """测试匹配等级确定"""
        from client.utils.project_evaluator import MatchScore
        
        assert self.evaluator._get_match_level(95) == MatchScore.EXCELLENT
        assert self.evaluator._get_match_level(75) == MatchScore.GOOD
        assert self.evaluator._get_match_level(55) == MatchScore.FAIR
        assert self.evaluator._get_match_level(35) == MatchScore.POOR
        assert self.evaluator._get_match_level(15) == MatchScore.VERY_POOR
    
    def test_calculate_tech_readiness_score(self):
        """测试技术成熟度评分"""
        tech_info = {
            "level": "prototype",
            "milestones": ["算法模型训练完成", "封闭场地测试完成"],
            "risks": ["算法安全性验证", "法规合规性"]
        }
        
        score = self.evaluator._calculate_tech_readiness_score(tech_info)
        assert 0 <= score <= 100
        assert score >= 60  # prototype级别的基础分
    
    def test_calculate_landing_requirements_score(self):
        """测试落地要求评分"""
        landing_info = {
            "incentives": [
                {"type": "税收优惠", "description": "企业所得税减免15%"},
                {"type": "资金支持", "description": "最高500万研发补贴"}
            ],
            "infrastructure": ["5G网络覆盖", "云计算平台"],
            "timeline": {"审批": "1-2周"}
        }
        
        score = self.evaluator._calculate_landing_requirements_score(landing_info)
        assert 0 <= score <= 100
        assert score >= 70  # 基础分
    
    def test_calculate_economic_compliance_score(self):
        """测试经济合规评分"""
        compliance_info = {
            "compliance_status": "严格监管",
            "estimated_costs": {"setup": 100000, "monthly": 20000},
            "risks": ["税务风险", "法律风险"]
        }
        
        score = self.evaluator._calculate_economic_compliance_score(compliance_info)
        assert 0 <= score <= 100
        assert score <= 80  # 严格监管会扣分
    
    def test_analyze_strengths_weaknesses(self):
        """测试优势和劣势分析"""
        strengths, weaknesses = self.evaluator._analyze_strengths_weaknesses(
            85, 75, 65
        )
        
        assert isinstance(strengths, list)
        assert isinstance(weaknesses, list)
        assert len(strengths) > 0
        assert len(weaknesses) > 0
    
    def test_generate_recommendations(self):
        """测试建议生成"""
        tech_info = {"level": "prototype"}
        landing_info = {"incentives": []}
        compliance_info = {"compliance_status": "严格监管"}
        
        strengths = ["技术成熟度高"]
        weaknesses = ["合规风险较高"]
        match_level = MatchScore.GOOD
        
        recommendations = self.evaluator._generate_recommendations(
            tech_info, landing_info, compliance_info, strengths, weaknesses, match_level
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    @patch.object(ProjectEvaluator, 'evaluate_project')
    def test_batch_evaluate_projects(self, mock_evaluate):
        """测试批量项目评估"""
        mock_evaluate.side_effect = [
            ProjectMatchResult(
                project_id="project1",
                project_name="项目1",
                location="上海",
                industry="autonomous_driving",
                tech_readiness_score=80,
                landing_requirements_score=75,
                economic_compliance_score=70,
                overall_score=75,
                match_level=MatchScore.GOOD,
                strengths=["技术成熟度高"],
                weaknesses=["合规风险较高"],
                recommendations=["加强合规管理"],
                timeline={}
            ),
            ProjectMatchResult(
                project_id="project2",
                project_name="项目2",
                location="上海",
                industry="embodied_ai",
                tech_readiness_score=90,
                landing_requirements_score=85,
                economic_compliance_score=80,
                overall_score=85,
                match_level=MatchScore.GOOD,
                strengths=["技术成熟度高", "落地条件好"],
                weaknesses=[],
                recommendations=["优先引进"],
                timeline={}
            )
        ]
        
        results = self.evaluator.batch_evaluate_projects(
            ["project1", "project2"], "上海"
        )
        
        assert len(results) == 2
        assert results[0].overall_score == 85  # 应该按总分排序
        assert results[1].overall_score == 75
    
    @patch.object(ProjectEvaluator, 'batch_evaluate_projects')
    def test_get_project_ranking(self, mock_batch_evaluate):
        """测试项目排名"""
        mock_batch_evaluate.return_value = [
            ProjectMatchResult(
                project_id="project2",
                project_name="项目2",
                location="上海",
                industry="embodied_ai",
                tech_readiness_score=90,
                landing_requirements_score=85,
                economic_compliance_score=80,
                overall_score=85,
                match_level=MatchScore.GOOD,
                strengths=["技术成熟度高", "落地条件好"],
                weaknesses=[],
                recommendations=["优先引进"],
                timeline={}
            ),
            ProjectMatchResult(
                project_id="project1",
                project_name="项目1",
                location="上海",
                industry="autonomous_driving",
                tech_readiness_score=80,
                landing_requirements_score=75,
                economic_compliance_score=70,
                overall_score=75,
                match_level=MatchScore.GOOD,
                strengths=["技术成熟度高"],
                weaknesses=["合规风险较高"],
                recommendations=["加强合规管理"],
                timeline={}
            )
        ]
        
        rankings = self.evaluator.get_project_ranking(
            ["project1", "project2"], "上海"
        )
        
        assert len(rankings) == 2
        assert rankings[0][0] == "project2"  # 排名第一
        assert rankings[0][1] == 85
        assert rankings[1][0] == "project1"
        assert rankings[1][1] == 75


class TestGovernmentInvestmentPromotion:
    """政府招商引资服务测试"""
    
    def setup_method(self):
        """测试设置"""
        self.promotion = GovernmentInvestmentPromotion("http://localhost:8000")
    
    def test_init_promotion(self):
        """测试服务初始化"""
        assert self.promotion.server_url == "http://localhost:8000"
        assert self.promotion.client is not None
        assert self.promotion.evaluator is not None
        assert len(self.promotion.sample_projects) == 3
    
    def test_sample_projects(self):
        """测试示例项目"""
        project = self.promotion.sample_projects[0]
        assert project.id == "ai-auto-pilot-2024"
        assert project.name == "AI自动驾驶系统"
        assert project.industry == "autonomous_driving"
        assert project.scale == "large"
        assert project.target_location == "上海"
    
    @patch.object(ProtocolClient, 'health_check')
    def test_connect_to_server_success(self, mock_health_check):
        """测试成功连接到服务器"""
        mock_health_check.return_value = {"status": "healthy"}
        
        result = asyncio.run(self.promotion.connect_to_server())
        assert result == True
    
    @patch.object(ProtocolClient, 'health_check')
    def test_connect_to_server_failure(self, mock_health_check):
        """测试连接服务器失败"""
        mock_health_check.return_value = {"status": "error"}
        
        result = asyncio.run(self.promotion.connect_to_server())
        assert result == False
    
    @patch.object(ProjectEvaluator, 'evaluate_project')
    def test_evaluate_single_project_success(self, mock_evaluate):
        """测试成功评估单个项目"""
        mock_evaluate.return_value = ProjectMatchResult(
            project_id="test-project",
            project_name="测试项目",
            location="上海",
            industry="autonomous_driving",
            tech_readiness_score=80,
            landing_requirements_score=75,
            economic_compliance_score=70,
            overall_score=75,
            match_level=MatchScore.GOOD,
            strengths=["技术成熟度高"],
            weaknesses=["合规风险较高"],
            recommendations=["加强合规管理"],
            timeline={}
        )
        
        project = self.promotion.sample_projects[0]
        result = asyncio.run(self.promotion.evaluate_single_project(project))
        
        assert result["project_id"] == "test-project"
        assert result["project_name"] == "测试项目"
        assert result["overall_score"] == 75
        assert result["match_level"] == "good"
        assert result["status"] == "success"
    
    @patch.object(ProjectEvaluator, 'evaluate_project')
    def test_evaluate_single_project_failure(self, mock_evaluate):
        """测试评估单个项目失败"""
        mock_evaluate.return_value = None
        
        project = self.promotion.sample_projects[0]
        result = asyncio.run(self.promotion.evaluate_single_project(project))
        
        assert result["status"] == "failed"
        assert "error" in result
    
    @patch.object(GovernmentInvestmentPromotion, 'evaluate_single_project')
    def test_evaluate_all_projects(self, mock_evaluate_single):
        """测试评估所有项目"""
        mock_evaluate_single.side_effect = [
            {
                "project_id": "project1",
                "project_name": "项目1",
                "overall_score": 80,
                "status": "success"
            },
            {
                "project_id": "project2",
                "project_name": "项目2",
                "overall_score": 90,
                "status": "success"
            }
        ]
        
        results = asyncio.run(self.promotion.evaluate_all_projects())
        
        assert len(results) == 2
        assert results[0]["overall_score"] == 90  # 按分数排序
        assert results[1]["overall_score"] == 80
    
    @patch.object(ProjectEvaluator, 'get_project_ranking')
    def test_get_project_ranking(self, mock_get_ranking):
        """测试获取项目排名"""
        mock_get_ranking.return_value = [
            ("project2", 90),
            ("project1", 80)
        ]
        
        rankings = asyncio.run(self.promotion.get_project_ranking())
        
        assert len(rankings) == 2
        assert rankings[0]["rank"] == 1
        assert rankings[0]["project_id"] == "project2"
        assert rankings[0]["score"] == 90
        assert rankings[1]["rank"] == 2
        assert rankings[1]["project_id"] == "project1"
        assert rankings[1]["score"] == 80
    
    @patch.object(ProtocolClient, 'get_server_info')
    def test_get_server_info(self, mock_get_info):
        """测试获取服务器信息"""
        mock_get_info.return_value = {
            "service": "Open Invest Protocol Server",
            "version": "1.0.0"
        }
        
        result = asyncio.run(self.promotion.get_server_info())
        
        assert result["service"] == "Open Invest Protocol Server"
        assert result["version"] == "1.0.0"
    
    @patch.object(GovernmentInvestmentPromotion, 'get_project_ranking')
    @patch.object(GovernmentInvestmentPromotion, 'evaluate_all_projects')
    @patch.object(GovernmentInvestmentPromotion, 'get_server_info')
    def test_generate_promotion_report(self, mock_get_info, mock_evaluate_all, mock_get_ranking):
        """测试生成招商引资报告"""
        mock_get_info.return_value = {"service": "Test Server"}
        mock_evaluate_all.return_value = [
            {"project_id": "project1", "overall_score": 80, "status": "success"},
            {"project_id": "project2", "overall_score": 90, "status": "success"}
        ]
        mock_get_ranking.return_value = [
            ("project2", 90),
            ("project1", 80)
        ]
        
        report = asyncio.run(self.promotion.generate_promotion_report())
        
        assert "report_title" in report
        assert "summary" in report
        assert "priority_distribution" in report
        assert "match_level_distribution" in report
        assert "project_rankings" in report
        assert "detailed_evaluations" in report
        assert "recommendations" in report
        assert "next_steps" in report
        
        assert report["summary"]["total_projects"] == 2
        assert report["summary"]["successful_evaluations"] == 2
        assert report["summary"]["average_score"] == 85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])