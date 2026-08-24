"""
Open Invest Protocol 高级使用示例 - AI Agent Direct Apply 集成演示
演示项目方在平台上浏览到心仪的政府/园区政策后，如何通过点击 [AI Agent Direct Apply] 触发本地的 open-invest Server 端，通过安全网关自动将脱敏后的技术成熟度（TRL）和落地诉求一键安全对接到目标客户端。
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime

from client.api.protocol_client import ProtocolClient, ClientType
from client.hooks.ai_agent_direct_apply import AIAgentDirectApply, ApplyResult
from client.utils.project_evaluator import ProjectEvaluator, ProjectMatchResult, MatchScore

class InvestmentWorkflowManager:
    """投资工作流管理器"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.client = ProtocolClient(server_url, ClientType.GOV)
        self.ai_agent = AIAgentDirectApply(self.client)
        self.project_evaluator = ProjectEvaluator(self.client)
    
    async def complete_investment_workflow(self, project_id: str, target_locations: List[str]) -> Dict[str, Any]:
        """
        完整的投资工作流程
        
        Args:
            project_id: 项目ID
            target_locations: 目标地点列表
            
        Returns:
            Dict[str, Any]: 工作流结果
        """
        print(f"🚀 开始完整投资工作流程: {project_id}")
        print(f"📍 目标地点: {', '.join(target_locations)}")
        print("=" * 60)
        
        workflow_result = {
            "project_id": project_id,
            "target_locations": target_locations,
            "timestamp": datetime.now().isoformat(),
            "steps": {},
            "final_recommendations": []
        }
        
        # 步骤1: 获取项目基本信息
        print("📊 步骤1: 获取项目基本信息...")
        try:
            project_info = await self.client.get_tech_readiness(project_id)
            workflow_result["steps"]["project_info"] = project_info
            print(f"✅ 项目: {project_info['name']}")
            print(f"🏭 行业: {project_info['industry']}")
            print(f"📈 技术成熟度: {project_info['level']}")
            print()
        except Exception as e:
            print(f"❌ 获取项目信息失败: {str(e)}")
            return workflow_result
        
        # 步骤2: 获取目标地点政策
        print("📋 步骤2: 获取目标地点政策...")
        policies = {}
        for location in target_locations:
            try:
                policy_data = await self.client.get_landing_requirements(
                    location=location,
                    industry=project_info['industry']
                )
                policies[location] = policy_data
                print(f"✅ {location}: {len(policy_data.get('incentives', []))} 个激励政策")
            except Exception as e:
                print(f"❌ 获取 {location} 政策失败: {str(e)}")
        
        workflow_result["steps"]["policies"] = policies
        print()
        
        # 步骤3: 评估政策匹配度
        print("🎯 步骤3: 评估政策匹配度...")
        match_results = []
        for location, policy_data in policies.items():
            try:
                match_result = await self.project_evaluator.evaluate_single_policy(
                    project_id=project_id,
                    policy_data=policy_data
                )
                match_results.append(match_result)
                print(f"📍 {location}: 匹配分数 {match_result.overall_score:.2f} ({match_result.match_level.value})")
            except Exception as e:
                print(f"❌ 评估 {location} 匹配度失败: {str(e)}")
        
        workflow_result["steps"]["match_results"] = [result.__dict__ for result in match_results]
        print()
        
        # 步骤4: 排序和筛选
        print("🏆 步骤4: 排序和筛选...")
        sorted_results = sorted(match_results, key=lambda x: x.overall_score, reverse=True)
        
        print("📊 匹配度排名:")
        for i, result in enumerate(sorted_results[:5], 1):
            print(f"{i}. {result.location}: {result.overall_score:.2f} ({result.match_level.value})")
            print(f"   优势: {', '.join(result.strengths[:2])}")
        
        workflow_result["steps"]["sorted_results"] = [result.__dict__ for result in sorted_results]
        print()
        
        # 步骤5: AI Agent Direct Apply
        print("🤖 步骤5: AI Agent Direct Apply...")
        apply_results = []
        for result in sorted_results[:3]:  # 对前3个最佳匹配进行申请
            try:
                print(f"📍 正在申请 {result.location} 的政策...")
                apply_result = await self.ai_agent.direct_apply(
                    project_id=project_id,
                    policy_id=result.location,
                    user_data={
                        "workflow_type": "full_investment_workflow",
                        "priority": "high"
                    }
                )
                apply_results.append(apply_result)
                print(f"✅ 申请成功! ID: {apply_result.application_id}")
                print(f"   匹配分数: {apply_result.match_score}")
                print(f"   预计时间: {apply_result.estimated_timeline}")
            except Exception as e:
                print(f"❌ 申请 {result.location} 失败: {str(e)}")
        
        workflow_result["steps"]["apply_results"] = [result.__dict__ for result in apply_results]
        print()
        
        # 步骤6: 生成最终推荐
        print("🎯 步骤6: 生成最终推荐...")
        final_recommendations = []
        
        for apply_result in apply_results:
            recommendation = {
                "location": apply_result.policy_id,
                "application_id": apply_result.application_id,
                "match_score": apply_result.match_score,
                "status": apply_result.status,
                "next_steps": apply_result.next_steps,
                "estimated_timeline": apply_result.estimated_timeline,
                "contact_info": apply_result.contact_info
            }
            final_recommendations.append(recommendation)
        
        workflow_result["final_recommendations"] = final_recommendations
        
        print("🎉 最终推荐:")
        for i, rec in enumerate(final_recommendations, 1):
            print(f"{i}. {rec['location']}:")
            print(f"   申请ID: {rec['application_id']}")
            print(f"   匹配分数: {rec['match_score']:.2f}")
            print(f"   状态: {rec['status']}")
            print(f"   预计时间: {rec['estimated_timeline']}")
            print()
        
        return workflow_result
    
    async def batch_policy_analysis(self, project_ids: List[str], locations: List[str]) -> Dict[str, Any]:
        """
        批量政策分析
        
        Args:
            project_ids: 项目ID列表
            locations: 地点列表
            
        Returns:
            Dict[str, Any]: 批量分析结果
        """
        print(f"🔍 开始批量政策分析...")
        print(f"📋 项目数量: {len(project_ids)}")
        print(f"📍 地点数量: {len(locations)}")
        print("=" * 60)
        
        batch_result = {
            "timestamp": datetime.now().isoformat(),
            "total_projects": len(project_ids),
            "total_locations": len(locations),
            "analysis_results": []
        }
        
        for project_id in project_ids:
            print(f"\n📊 分析项目: {project_id}")
            
            try:
                # 获取项目信息
                project_info = await self.client.get_tech_readiness(project_id)
                print(f"✅ 项目: {project_info['name']} ({project_info['industry']})")
                
                # 分析每个地点
                location_analysis = []
                for location in locations:
                    try:
                        policy_data = await self.client.get_landing_requirements(
                            location=location,
                            industry=project_info['industry']
                        )
                        
                        match_result = await self.project_evaluator.evaluate_single_policy(
                            project_id=project_id,
                            policy_data=policy_data
                        )
                        
                        location_analysis.append({
                            "location": location,
                            "match_score": match_result.overall_score,
                            "match_level": match_result.match_level.value,
                            "strengths": match_result.strengths,
                            "weaknesses": match_result.weaknesses
                        })
                        
                        print(f"   📍 {location}: {match_result.overall_score:.2f} ({match_result.match_level.value})")
                        
                    except Exception as e:
                        print(f"   ❌ 分析 {location} 失败: {str(e)}")
                        continue
                
                batch_result["analysis_results"].append({
                    "project_id": project_id,
                    "project_name": project_info['name'],
                    "industry": project_info['industry'],
                    "location_analysis": location_analysis
                })
                
            except Exception as e:
                print(f"❌ 分析项目 {project_id} 失败: {str(e)}")
                continue
        
        # 生成汇总报告
        print(f"\n📈 批量分析汇总:")
        print("=" * 40)
        
        total_analyses = sum(len(result["location_analysis"]) for result in batch_result["analysis_results"])
        successful_analyses = total_analyses
        
        print(f"总分析次数: {total_analyses}")
        print(f"成功分析: {successful_analyses}")
        print(f"成功率: {successful_analyses/total_analyses*100:.1f}%")
        
        # 找出最佳匹配
        best_matches = []
        for result in batch_result["analysis_results"]:
            for location in result["location_analysis"]:
                best_matches.append({
                    "project": result["project_name"],
                    "location": location["location"],
                    "match_score": location["match_score"]
                })
        
        best_matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        print(f"\n🏆 最佳匹配 (前5名):")
        for i, match in enumerate(best_matches[:5], 1):
            print(f"{i}. {match['project']} -> {match['location']}: {match['match_score']:.2f}")
        
        return batch_result

async def demonstrate_integration_workflow():
    """演示集成工作流程"""
    # 创建工作流管理器
    workflow_manager = InvestmentWorkflowManager()
    
    # 示例项目ID
    project_id = "ai-auto-pilot-2024"
    target_locations = ["Shanghai", "Shenzhen", "Silicon Valley"]
    
    print("🚀 Open Invest Protocol - AI Agent Direct Apply 集成演示")
    print("=" * 60)
    
    try:
        # 执行完整工作流程
        result = await workflow_manager.complete_investment_workflow(
            project_id=project_id,
            target_locations=target_locations
        )
        
        # 保存结果到文件
        with open("investment_workflow_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("✅ 工作流程完成！结果已保存到 investment_workflow_result.json")
        
    except Exception as e:
        print(f"❌ 工作流程执行失败: {str(e)}")

async def demonstrate_batch_analysis():
    """演示批量分析"""
    # 创建工作流管理器
    workflow_manager = InvestmentWorkflowManager()
    
    # 示例项目列表
    project_ids = ["ai-auto-pilot-2024", "quantum-encryption-startup-2024", "biotech-medical-device-2024"]
    locations = ["Shanghai", "Shenzhen", "Singapore", "Silicon Valley"]
    
    print("🔍 Open Invest Protocol - 批量政策分析演示")
    print("=" * 60)
    
    try:
        # 执行批量分析
        result = await workflow_manager.batch_policy_analysis(
            project_ids=project_ids,
            locations=locations
        )
        
        # 保存结果到文件
        with open("batch_analysis_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("✅ 批量分析完成！结果已保存到 batch_analysis_result.json")
        
    except Exception as e:
        print(f"❌ 批量分析执行失败: {str(e)}")

async def main():
    """主函数"""
    print("🎯 Open Invest Protocol 高级使用示例")
    print("=" * 50)
    
    # 选择演示模式
    print("请选择演示模式:")
    print("1. 完整投资工作流程演示")
    print("2. 批量政策分析演示")
    print("3. 运行所有演示")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    if choice == "1":
        await demonstrate_integration_workflow()
    elif choice == "2":
        await demonstrate_batch_analysis()
    elif choice == "3":
        await demonstrate_integration_workflow()
        print("\n" + "=" * 60)
        await demonstrate_batch_analysis()
    else:
        print("无效选择，运行默认演示...")
        await demonstrate_integration_workflow()

if __name__ == "__main__":
    asyncio.run(main())