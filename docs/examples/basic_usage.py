"""
Open Invest Protocol 基本使用示例
演示如何使用协议进行基本操作
"""

import asyncio
import json
from client.api.protocol_client import ProtocolClient, ClientType
from client.utils.project_evaluator import ProjectEvaluator


async def main():
    """主函数演示基本使用"""
    
    # 1. 创建协议客户端
    print("🚀 创建协议客户端...")
    client = ProtocolClient("http://localhost:8000", ClientType.GOV)
    
    try:
        # 2. 健康检查
        print("🔍 检查服务器健康状态...")
        health = client.health_check()
        print(f"服务器状态: {health}")
        
        # 3. 获取技术成熟度信息
        print("\n📊 获取技术成熟度信息...")
        tech_info = client.get_tech_readiness("ai-auto-pilot-2024")
        
        if tech_info:
            print(f"项目ID: {tech_info['project_id']}")
            print(f"技术等级: {tech_info['level']}")
            print(f"描述: {tech_info['description']}")
            print("时间线:")
            for period, task in tech_info['timeline'].items():
                print(f"  {period}: {task}")
            print("里程碑:")
            for milestone in tech_info['milestones']:
                print(f"  • {milestone}")
        else:
            print("❌ 获取技术成熟度信息失败")
        
        # 4. 获取落地要求信息
        print("\n🏢 获取落地要求信息...")
        landing_info = client.get_landing_requirements(
            "上海", 
            "autonomous_driving", 
            "large"
        )
        
        if landing_info:
            print(f"目标地区: {landing_info['location']}")
            print(f"行业类型: {landing_info['industry']}")
            print("要求:")
            for req in landing_info['requirements']:
                print(f"  • {req['type']}: {req['description']}")
            print("优惠政策:")
            for incentive in landing_info['incentives']:
                print(f"  • {incentive['type']}: {incentive['description']}")
            print("基础设施:")
            for infra in landing_info['infrastructure']:
                print(f"  • {infra}")
        else:
            print("❌ 获取落地要求信息失败")
        
        # 5. 获取经济合规信息
        print("\n⚖️ 获取经济合规信息...")
        compliance_info = client.get_economic_and_compliance(
            "ai-auto-pilot-2024", 
            "上海", 
            "standard"
        )
        
        if compliance_info:
            print(f"项目ID: {compliance_info['project_id']}")
            print(f"地区: {compliance_info['region']}")
            print(f"合规状态: {compliance_info['compliance_status']}")
            print("预计成本:")
            for cost_type, amount in compliance_info['estimated_costs'].items():
                print(f"  • {cost_type}: ¥{amount:,}")
            print("风险:")
            for risk in compliance_info['risks']:
                print(f"  • {risk}")
        else:
            print("❌ 获取经济合规信息失败")
        
        # 6. 创建项目评估器
        print("\n🎯 创建项目评估器...")
        evaluator = ProjectEvaluator(client)
        
        # 7. 评估项目
        print("\n📈 评估项目匹配度...")
        evaluation = evaluator.evaluate_project(
            "ai-auto-pilot-2024", 
            "上海", 
            "standard"
        )
        
        if evaluation:
            print(f"项目名称: {evaluation.project_name}")
            print(f"总体评分: {evaluation.overall_score:.1f}")
            print(f"匹配等级: {evaluation.match_level.value}")
            print("技术成熟度评分:", evaluation.tech_readiness_score)
            print("落地要求评分:", evaluation.landing_requirements_score)
            print("经济合规评分:", evaluation.economic_compliance_score)
            print("\n优势:")
            for strength in evaluation.strengths:
                print(f"  • {strength}")
            print("\n劣势:")
            for weakness in evaluation.weaknesses:
                print(f"  • {weakness}")
            print("\n建议:")
            for recommendation in evaluation.recommendations:
                print(f"  • {recommendation}")
        else:
            print("❌ 项目评估失败")
        
        # 8. 批量评估项目
        print("\n📊 批量评估项目...")
        project_ids = ["ai-auto-pilot-2024", "robotics-care-2024", "quantum-sensor-2024"]
        batch_results = evaluator.batch_evaluate_projects(
            project_ids, 
            "上海", 
            "standard"
        )
        
        print("批量评估结果:")
        for i, result in enumerate(batch_results, 1):
            print(f"  {i}. {result.project_name}: {result.overall_score:.1f}分")
        
        # 9. 获取项目排名
        print("\n🏆 获取项目排名...")
        rankings = evaluator.get_project_ranking(
            project_ids, 
            "上海", 
            "standard"
        )
        
        print("项目排名:")
        for rank, (project_id, score) in enumerate(rankings, 1):
            print(f"  {rank}. {project_id}: {score:.1f}分")
        
    finally:
        # 10. 关闭客户端
        print("\n🔒 关闭客户端...")
        client.close()


if __name__ == "__main__":
    asyncio.run(main())