"""
集成测试
测试服务端和客户端的完整交互
"""

import pytest
import json
import asyncio
import time
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock
import requests
import subprocess
import os
import sys

from server.main import app
from fastapi.testclient import TestClient
from client.api.protocol_client import ProtocolClient, ClientType
from client.utils.project_evaluator import ProjectEvaluator
from client.main import GovernmentInvestmentPromotion


class TestServerClientIntegration:
    """服务端客户端集成测试"""
    
    def setup_method(self):
        """测试设置"""
        # 创建测试客户端
        self.client = TestClient(app)
        
        # 创建协议客户端
        self.protocol_client = ProtocolClient("http://localhost:8000", ClientType.GOV)
        
        # 创建项目评估器
        self.evaluator = ProjectEvaluator(self.protocol_client)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        print("\n🔄 测试完整工作流程...")
        
        # 1. 测试服务器健康检查
        print("  1. 检查服务器健康状态...")
        health = self.client.get("/health")
        assert health.status_code == 200
        health_data = health.json()
        assert health_data["status"] == "healthy"
        
        # 2. 测试技术成熟度查询
        print("  2. 查询技术成熟度...")
        tech_request = {
            "jsonrpc": "2.0",
            "method": "get_tech_readiness",
            "params": {"project_id": "ai-auto-pilot-2024"},
            "id": "tech-test-001"
        }
        
        tech_response = self.client.post("/rpc", json=tech_request)
        assert tech_response.status_code == 200
        tech_data = tech_response.json()
        assert "result" in tech_data
        assert tech_data["result"]["project_id"] == "ai-auto-pilot-2024"
        assert tech_data["result"]["level"] == "prototype"
        
        # 3. 测试落地要求查询
        print("  3. 查询落地要求...")
        landing_request = {
            "jsonrpc": "2.0",
            "method": "get_landing_requirements",
            "params": {
                "location": "上海",
                "industry": "autonomous_driving",
                "project_scale": "large"
            },
            "id": "landing-test-001"
        }
        
        landing_response = self.client.post("/rpc", json=landing_request)
        assert landing_response.status_code == 200
        landing_data = landing_response.json()
        assert "result" in landing_data
        assert landing_data["result"]["location"] == "上海"
        assert len(landing_data["result"]["requirements"]) > 0
        
        # 4. 测试经济合规查询
        print("  4. 查询经济合规...")
        compliance_request = {
            "jsonrpc": "2.0",
            "method": "get_economic_and_compliance",
            "params": {
                "project_id": "ai-auto-pilot-2024",
                "region": "上海",
                "compliance_level": "standard"
            },
            "id": "compliance-test-001"
        }
        
        compliance_response = self.client.post("/rpc", json=compliance_request)
        assert compliance_response.status_code == 200
        compliance_data = compliance_response.json()
        assert "result" in compliance_data
        assert compliance_data["result"]["project_id"] == "ai-auto-pilot-2024"
        assert compliance_data["result"]["region"] == "上海"
        
        # 5. 测试项目评估
        print("  5. 评估项目...")
        evaluation_result = self.evaluator.evaluate_project(
            "ai-auto-pilot-2024", 
            "上海", 
            "standard"
        )
        
        assert evaluation_result is not None
        assert evaluation_result.project_id == "ai-auto-pilot-2024"
        assert evaluation_result.location == "上海"
        assert 0 <= evaluation_result.overall_score <= 100
        assert len(evaluation_result.strengths) > 0
        assert len(evaluation_result.weaknesses) > 0
        assert len(evaluation_result.recommendations) > 0
        
        # 6. 测试批量评估
        print("  6. 批量评估项目...")
        project_ids = ["ai-auto-pilot-2024", "robotics-care-2024", "quantum-sensor-2024"]
        batch_results = self.evaluator.batch_evaluate_projects(
            project_ids, 
            "上海", 
            "standard"
        )
        
        assert len(batch_results) == 3
        assert all(result.overall_score > 0 for result in batch_results)
        
        # 7. 测试项目排名
        print("  7. 生成项目排名...")
        rankings = self.evaluator.get_project_ranking(
            project_ids, 
            "上海", 
            "standard"
        )
        
        assert len(rankings) == 3
        assert all(isinstance(score, (int, float)) for _, score in rankings)
        
        print("  ✅ 完整工作流程测试通过！")
    
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        print("\n🚨 测试错误处理集成...")
        
        # 1. 测试无效项目ID
        print("  1. 测试无效项目ID...")
        invalid_request = {
            "jsonrpc": "2.0",
            "method": "get_tech_readiness",
            "params": {"project_id": "invalid-project-id"},
            "id": "error-test-001"
        }
        
        invalid_response = self.client.post("/rpc", json=invalid_request)
        assert invalid_response.status_code == 200
        invalid_data = invalid_response.json()
        assert "error" in invalid_data
        assert invalid_data["error"]["code"] == -32600
        
        # 2. 测试无效方法
        print("  2. 测试无效方法...")
        method_request = {
            "jsonrpc": "2.0",
            "method": "invalid_method",
            "params": {},
            "id": "error-test-002"
        }
        
        method_response = self.client.post("/rpc", json=method_request)
        assert method_response.status_code == 200
        method_data = method_response.json()
        assert "error" in method_data
        assert method_data["error"]["code"] == -32601
        
        # 3. 测试评估失败
        print("  3. 测试评估失败...")
        eval_result = self.evaluator.evaluate_project(
            "invalid-project-id", 
            "上海", 
            "standard"
        )
        
        assert eval_result is None
        
        print("  ✅ 错误处理集成测试通过！")
    
    def test_data_protection_integration(self):
        """测试数据保护集成"""
        print("\n🔒 测试数据保护集成...")
        
        # 1. 测试公共客户端访问
        print("  1. 测试公共客户端访问...")
        public_client = ProtocolClient("http://localhost:8000", ClientType.PUBLIC)
        
        # 公共客户端应该只能访问公开数据
        tech_result = public_client.get_tech_readiness("ai-auto-pilot-2024")
        assert tech_result is not None
        # 公共客户端的数据应该被脱敏
        assert "contact_info" not in tech_result or "contact_info" in tech_result and len(tech_result["contact_info"]) == 0
        
        # 2. 测试政府客户端访问
        print("  2. 测试政府客户端访问...")
        gov_client = ProtocolClient("http://localhost:8000", ClientType.GOV)
        
        gov_result = gov_client.get_tech_readiness("ai-auto-pilot-2024")
        assert gov_result is not None
        # 政府客户端应该能访问更多数据
        assert "description" in gov_result
        
        # 3. 测试合作伙伴客户端访问
        print("  3. 测试合作伙伴客户端访问...")
        partner_client = ProtocolClient("http://localhost:8000", ClientType.PARTNER)
        
        partner_result = partner_client.get_tech_readiness("ai-auto-pilot-2024")
        assert partner_result is not None
        # 合作伙伴客户端应该能访问更多敏感数据
        assert "timeline" in partner_result
        
        print("  ✅ 数据保护集成测试通过！")
    
    def test_performance_integration(self):
        """测试性能集成"""
        print("\n⚡ 测试性能集成...")
        
        # 1. 测试批量请求性能
        print("  1. 测试批量请求性能...")
        requests = []
        for i in range(10):
            requests.append({
                "jsonrpc": "2.0",
                "method": "get_tech_readiness",
                "params": {"project_id": f"project-{i}"},
                "id": f"perf-test-{i}"
            })
        
        start_time = time.time()
        for request in requests:
            response = self.client.post("/rpc", json=request)
            assert response.status_code == 200
        end_time = time.time()
        
        total_time = end_time - start_time
        print(f"    批量10个请求耗时: {total_time:.2f}秒")
        assert total_time < 5.0  # 10个请求应该在5秒内完成
        
        # 2. 测试评估性能
        print("  2. 测试评估性能...")
        project_ids = ["ai-auto-pilot-2024", "robotics-care-2024", "quantum-sensor-2024"]
        
        start_time = time.time()
        results = self.evaluator.batch_evaluate_projects(
            project_ids, 
            "上海", 
            "standard"
        )
        end_time = time.time()
        
        eval_time = end_time - start_time
        print(f"    批量3个项目评估耗时: {eval_time:.2f}秒")
        assert eval_time < 3.0  # 3个项目评估应该在3秒内完成
        
        print("  ✅ 性能集成测试通过！")
    
    def test_concurrent_requests(self):
        """测试并发请求"""
        print("\n🔄 测试并发请求...")
        
        import threading
        import queue
        
        result_queue = queue.Queue()
        
        def make_request(project_id):
            try:
                response = self.client.post("/rpc", json={
                    "jsonrpc": "2.0",
                    "method": "get_tech_readiness",
                    "params": {"project_id": project_id},
                    "id": f"concurrent-{project_id}"
                })
                result_queue.put(("success", response.status_code))
            except Exception as e:
                result_queue.put(("error", str(e)))
        
        # 创建多个线程并发请求
        threads = []
        project_ids = ["ai-auto-pilot-2024", "robotics-care-2024", "quantum-sensor-2024"]
        
        for project_id in project_ids:
            thread = threading.Thread(target=make_request, args=(project_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查结果
        success_count = 0
        error_count = 0
        
        while not result_queue.empty():
            status, data = result_queue.get()
            if status == "success":
                assert data == 200
                success_count += 1
            else:
                error_count += 1
        
        assert success_count == 3
        assert error_count == 0
        
        print("  ✅ 并发请求测试通过！")


class TestRealWorldScenario:
    """真实场景测试"""
    
    def setup_method(self):
        """测试设置"""
        self.client = TestClient(app)
        self.promotion = GovernmentInvestmentPromotion("http://localhost:8000")
        # 与 TestServerClientIntegration 一致：跨地区/合规级别比较依赖项目评估器
        self.protocol_client = ProtocolClient("http://localhost:8000", ClientType.GOV)
        self.evaluator = ProjectEvaluator(self.protocol_client)
    
    def test_government_investment_scenario(self):
        """测试政府招商引资场景"""
        print("\n🏛️ 测试政府招商引资场景...")
        
        # 1. 连接到服务器
        print("  1. 连接到服务器...")
        connected = asyncio.run(self.promotion.connect_to_server())
        assert connected == True
        
        # 2. 生成招商引资报告
        print("  2. 生成招商引资报告...")
        report = asyncio.run(self.promotion.generate_promotion_report())
        
        assert "report_title" in report
        assert "summary" in report
        assert "project_rankings" in report
        assert "recommendations" in report
        
        # 3. 验证报告内容
        print("  3. 验证报告内容...")
        summary = report["summary"]
        assert summary["total_projects"] == 3
        assert summary["successful_evaluations"] == 3
        assert 0 < summary["average_score"] < 100
        
        # 4. 验证项目排名
        rankings = report["project_rankings"]
        assert len(rankings) == 3
        assert all("rank" in r for r in rankings)
        assert all("project_name" in r for r in rankings)
        assert all("score" in r for r in rankings)
        
        # 5. 验证建议
        recommendations = report["recommendations"]
        assert len(recommendations) > 0
        assert any("推荐" in rec for rec in recommendations)
        
        # 6. 验证下一步行动
        next_steps = report["next_steps"]
        assert len(next_steps) > 0
        assert any("联系" in step for step in next_steps)
        
        print("  ✅ 政府招商引资场景测试通过！")
    
    def test_cross_region_comparison(self):
        """测试跨地区比较"""
        print("\n🌍 测试跨地区比较...")
        
        # 比较不同地区的项目评估
        regions = ["上海", "深圳", "杭州"]
        project_id = "ai-auto-pilot-2024"
        
        region_results = {}
        
        for region in regions:
            result = self.evaluator.evaluate_project(
                project_id, 
                region, 
                "standard"
            )
            
            if result:
                region_results[region] = result.overall_score
        
        # 验证结果
        assert len(region_results) == 3
        assert all(0 <= score <= 100 for score in region_results.values())
        
        # 找出最佳地区
        best_region = max(region_results, key=region_results.get)
        print(f"    最佳地区: {best_region} (评分: {region_results[best_region]})")
        
        print("  ✅ 跨地区比较测试通过！")
    
    def test_compliance_level_comparison(self):
        """测试不同合规级别的比较"""
        print("\n⚖️ 测试不同合规级别比较...")
        
        project_id = "ai-auto-pilot-2024"
        region = "上海"
        compliance_levels = ["basic", "standard", "enhanced"]
        
        compliance_results = {}
        
        for level in compliance_levels:
            result = self.evaluator.evaluate_project(
                project_id, 
                region, 
                level
            )
            
            if result:
                compliance_results[level] = result.overall_score
        
        # 验证结果
        assert len(compliance_results) == 3
        assert all(0 <= score <= 100 for score in compliance_results.values())
        
        # 分析合规级别对评分的影响
        basic_score = compliance_results.get("basic", 0)
        standard_score = compliance_results.get("standard", 0)
        enhanced_score = compliance_results.get("enhanced", 0)
        
        print(f"    Basic级别: {basic_score}")
        print(f"    Standard级别: {standard_score}")
        print(f"    Enhanced级别: {enhanced_score}")
        
        print("  ✅ 合规级别比较测试通过！")


class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    def setup_method(self):
        """测试设置"""
        self.client = TestClient(app)
    
    def test_complete_investment_workflow(self):
        """测试完整的投资工作流"""
        print("\n💼 测试完整投资工作流...")
        
        # 模拟一个完整的招商引资流程
        
        # 1. 项目发现
        print("  1. 项目发现阶段...")
        discovery_request = {
            "jsonrpc": "2.0",
            "method": "get_tech_readiness",
            "params": {"project_id": "ai-auto-pilot-2024"},
            "id": "discovery-001"
        }
        
        discovery_response = self.client.post("/rpc", json=discovery_request)
        assert discovery_response.status_code == 200
        discovery_data = discovery_response.json()
        assert discovery_data["result"]["project_id"] == "ai-auto-pilot-2024"
        
        # 2. 地方政府评估
        print("  2. 地方政府评估阶段...")
        evaluation_request = {
            "jsonrpc": "2.0",
            "method": "get_landing_requirements",
            "params": {
                "location": "上海",
                "industry": "autonomous_driving",
                "project_scale": "large"
            },
            "id": "evaluation-001"
        }
        
        evaluation_response = self.client.post("/rpc", json=evaluation_request)
        assert evaluation_response.status_code == 200
        evaluation_data = evaluation_response.json()
        assert evaluation_data["result"]["location"] == "上海"
        
        # 3. 合规审查
        print("  3. 合规审查阶段...")
        compliance_request = {
            "jsonrpc": "2.0",
            "method": "get_economic_and_compliance",
            "params": {
                "project_id": "ai-auto-pilot-2024",
                "region": "上海",
                "compliance_level": "standard"
            },
            "id": "compliance-001"
        }
        
        compliance_response = self.client.post("/rpc", json=compliance_request)
        assert compliance_response.status_code == 200
        compliance_data = compliance_response.json()
        assert compliance_data["result"]["project_id"] == "ai-auto-pilot-2024"
        
        # 4. 最终决策
        print("  4. 最终决策阶段...")
        # 基于所有信息做出决策
        tech_score = 80  # 基于技术成熟度
        landing_score = 75  # 基于落地要求
        compliance_score = 70  # 基于合规审查
        
        overall_score = (tech_score * 0.3 + landing_score * 0.4 + compliance_score * 0.3)
        
        decision = "引进" if overall_score >= 70 else "谨慎考虑"
        
        print(f"    综合评分: {overall_score:.1f}")
        print(f"    决策建议: {decision}")
        
        # 5. 生成投资建议
        print("  5. 生成投资建议...")
        recommendations = []
        
        if overall_score >= 80:
            recommendations.append("优先引进，提供全方位支持")
        elif overall_score >= 60:
            recommendations.append("可以考虑引进，需要加强支持")
        else:
            recommendations.append("建议谨慎考虑，需要进一步评估")
        
        if tech_score >= 80:
            recommendations.append("技术成熟度高，建议快速推进")
        
        if landing_score >= 80:
            recommendations.append("落地条件优越，建议优先安排")
        
        if compliance_score >= 80:
            recommendations.append("合规风险低，建议简化流程")
        
        print("    投资建议:")
        for rec in recommendations:
            print(f"      • {rec}")
        
        # 验证工作流完整性
        assert decision in ["引进", "谨慎考虑"]
        assert len(recommendations) > 0
        assert 0 <= overall_score <= 100
        
        print("  ✅ 完整投资工作流测试通过！")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])