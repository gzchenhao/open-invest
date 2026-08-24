#!/usr/bin/env python3
"""
中国高新区详细政策数据库填充脚本
将结构极其详尽的中国高新区产业扶持政策Mock数据填充到数据库
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent))

def populate_detailed_china_policies():
    """填充详细的中国高新区政策数据到数据库"""
    print("[INFO] 开始填充详细的中国高新区政策数据到数据库...")
    
    try:
        # 导入数据库服务和政策清洗器
        from global_policy_aggregator.services.policy_database_service import PolicyDatabaseService
        from processors.policy_cleaner import PolicyCleaner
        
        # 创建数据库服务实例
        db_service = PolicyDatabaseService()
        
        # 读取详细政策数据文件
        detailed_policies_file = Path(__file__).parent.parent / "data" / "seed_data" / "detailed_china_tech_policies.json"
        
        if not detailed_policies_file.exists():
            print(f"[ERROR] 详细政策数据文件不存在: {detailed_policies_file}")
            return False
        
        with open(detailed_policies_file, 'r', encoding='utf-8') as f:
            detailed_policies = json.load(f)
        
        print(f"[INFO] 读取到 {len(detailed_policies)} 条详细中国高新区政策数据")
        
        # 统计信息
        success_count = 0
        existing_count = 0
        error_count = 0
        
        for policy_data in detailed_policies:
            try:
                # 检查是否已存在
                existing = db_service.get_policy(policy_data['policy_id'])
                if not existing:
                    # 添加新政策
                    result = db_service.add_policy(policy_data)
                    if result:
                        print(f"[SUCCESS] 已添加政策: {policy_data['title']} ({policy_data['region']})")
                        success_count += 1
                    else:
                        print(f"[ERROR] 添加政策失败: {policy_data['title']}")
                        error_count += 1
                else:
                    print(f"[INFO] 政策已存在: {policy_data['title']}")
                    existing_count += 1
                    
            except Exception as e:
                print(f"[ERROR] 处理政策 {policy_data['title']} 时出错: {e}")
                error_count += 1
        
        print(f"\n[INFO] 数据库填充完成:")
        print(f"   - 成功添加: {success_count} 条")
        print(f"   - 已存在: {existing_count} 条")
        print(f"   - 失败: {error_count} 条")
        
        return True
            
    except Exception as e:
        print(f"[ERROR] 数据库填充失败: {e}")
        return False

def verify_detailed_policies():
    """验证数据库中的详细中国高新区政策数据"""
    print("\n[INFO] 验证数据库中的详细中国高新区政策数据...")
    
    try:
        # 导入数据库服务
        from services.policy_database_service import PolicyDatabaseService
        
        # 创建数据库服务实例
        db_service = PolicyDatabaseService()
        
        # 查询所有中国政策
        china_policies = db_service.search_policies(country="CN")
        
        print(f"[INFO] 数据库中找到 {len(china_policies)} 条中国政策")
        
        if china_policies:
            # 统计信息
            regions = set()
            industries = set()
            total_incentives = 0
            total_requirements = 0
            high_value_policies = 0
            
            for policy in china_policies:
                regions.add(policy.get('region', 'Unknown'))
                industries.add(policy.get('industry', 'Unknown'))
                
                # 计算激励措施和要求数量
                incentives = policy.get('incentives', [])
                requirements = policy.get('requirements', [])
                total_incentives += len(incentives)
                total_requirements += len(requirements)
                
                # 统计高价值政策（激励金额超过1000万元）
                if incentives:
                    for incentive in incentives:
                        if incentive.get('amount_details', {}).get('max_amount_cny', 0) >= 10000000:
                            high_value_policies += 1
                            break
            
            print("\n[INFO] 详细中国高新区政策统计:")
            print(f"   - 覆盖地区: {len(regions)} 个")
            print(f"   - 涵盖行业: {len(industries)} 个")
            print(f"   - 总激励措施: {total_incentives} 项")
            print(f"   - 总要求: {total_requirements} 项")
            print(f"   - 高价值政策(≥1000万): {high_value_policies} 项")
            
            # 显示所有地区
            print(f"\n[INFO] 覆盖地区: {', '.join(sorted(regions))}")
            
            # 显示所有行业
            print(f"[INFO] 涵盖行业: {', '.join(sorted(industries))}")
            
            # 显示前10条政策
            print(f"\n[INFO] 前10条详细政策:")
            for i, policy in enumerate(china_policies[:10]):
                incentives = policy.get('incentives', [])
                max_amount = 0
                for incentive in incentives:
                    amount = incentive.get('amount_details', {}).get('max_amount_cny', 0)
                    max_amount = max(max_amount, amount)
                
                print(f"   {i+1}. {policy['title']} ({policy['region']}) - 最高激励: {max_amount/10000:.0f}万元")
            
            return True
        else:
            print("[WARNING] 数据库中没有找到中国政策数据")
            return False
            
    except Exception as e:
        print(f"[ERROR] 验证失败: {e}")
        return False

def generate_policy_summary():
    """生成政策统计摘要"""
    print("\n[INFO] 生成政策统计摘要...")
    
    try:
        # 导入数据库服务
        from services.policy_database_service import PolicyDatabaseService
        
        # 创建数据库服务实例
        db_service = PolicyDatabaseService()
        
        # 获取统计信息
        stats = db_service.get_policy_statistics()
        
        print(f"[INFO] 政策数据库统计摘要:")
        print(f"   - 总政策数: {stats.get('total_policies', 0)}")
        print(f"   - 中国政策数: {stats.get('by_country', {}).get('CN', 0)}")
        print(f"   - 最近30天新增: {stats.get('recent_30_days', 0)}")
        
        # 按地区统计
        print(f"\n[INFO] 按地区统计:")
        for region, count in stats.get('by_country', {}).items():
            if region != 'CN':
                continue
            print(f"   - {region}: {count} 条")
        
        # 按行业统计
        print(f"\n[INFO] 按行业统计:")
        industry_stats = {}
        for policy in db_service.search_policies(country="CN"):
            industry = policy.get('industry', 'Unknown')
            industry_stats[industry] = industry_stats.get(industry, 0) + 1
        
        for industry, count in sorted(industry_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {industry}: {count} 条")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 生成摘要失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("中国高新区详细政策数据库填充工具")
    print("=" * 60)
    
    # 1. 填充数据库
    if populate_detailed_china_policies():
        print("\n[SUCCESS] 数据库填充成功")
    else:
        print("\n[ERROR] 数据库填充失败")
        return False
    
    # 2. 验证数据
    if verify_detailed_policies():
        print("\n[SUCCESS] 数据验证成功")
    else:
        print("\n[ERROR] 数据验证失败")
        return False
    
    # 3. 生成摘要
    if generate_policy_summary():
        print("\n[SUCCESS] 摘要生成成功")
    else:
        print("\n[ERROR] 摘要生成失败")
        return False
    
    print("\n" + "=" * 60)
    print("所有任务完成！数据库已填充详细的中国高新区政策数据")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)