"""
China Policy Database Populator
将中国政策种子数据填充到数据库
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

def populate_china_policies_from_json():
    """从JSON文件填充中国政策数据"""
    print("[INFO] 开始填充中国政策数据到数据库...")
    
    try:
        # 导入数据库服务
        from services.policy_database_service import PolicyDatabaseService
        
        # 创建数据库服务实例
        db_service = PolicyDatabaseService()
        
        # 读取种子数据文件
        seed_data_file = Path(__file__).parent / "china_policy_seed_data.json"
        
        if not seed_data_file.exists():
            print(f"[ERROR] 种子数据文件不存在: {seed_data_file}")
            return False
        
        with open(seed_data_file, 'r', encoding='utf-8') as f:
            policies = json.load(f)
        
        print(f"[INFO] 读取到 {len(policies)} 条中国政策数据")
        
        # 统计信息
        success_count = 0
        existing_count = 0
        error_count = 0
        
        for policy in policies:
            try:
                # 检查是否已存在
                existing = db_service.get_policy(policy['policy_id'])
                
                if existing:
                    existing_count += 1
                    print(f"[INFO] 政策已存在: {policy['title']}")
                else:
                    # 添加新政策
                    policy_id = db_service.add_policy(policy)
                    success_count += 1
                    print(f"[SUCCESS] 已添加政策: {policy['title']} (ID: {policy_id})")
                    
            except Exception as e:
                error_count += 1
                print(f"[ERROR] 添加政策失败: {policy['title']} - {e}")
        
        # 输出统计信息
        print("\n[INFO] 填充统计:")
        print(f"   - 成功添加: {success_count}")
        print(f"   - 已存在: {existing_count}")
        print(f"   - 失败: {error_count}")
        print(f"   - 总计: {len(policies)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 数据库填充失败: {e}")
        return False

def populate_china_policies_from_sql():
    """从SQL文件填充中国政策数据"""
    print("[INFO] 开始从SQL文件填充中国政策数据...")
    
    try:
        # 导入数据库服务
        from services.policy_database_service import PolicyDatabaseService
        
        # 创建数据库服务实例
        db_service = PolicyDatabaseService()
        
        # 读取SQL文件
        sql_file = Path(__file__).parent / "china_policy_seed_data.sql"
        
        if not sql_file.exists():
            print(f"[ERROR] SQL文件不存在: {sql_file}")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 提取INSERT语句
        import re
        insert_pattern = r'INSERT INTO policies VALUES \((.*?)\);'
        insert_statements = re.findall(insert_pattern, sql_content, re.DOTALL)
        
        print(f"[INFO] 找到 {len(insert_statements)} 条INSERT语句")
        
        # 执行INSERT语句
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(insert_statements):
            try:
                # 清理语句
                clean_statement = statement.strip()
                
                # 执行SQL
                db_service.execute_sql(clean_statement)
                success_count += 1
                print(f"[SUCCESS] 执行第 {i+1} 条INSERT语句")
                
            except Exception as e:
                error_count += 1
                print(f"[ERROR] 执行第 {i+1} 条INSERT语句失败: {e}")
        
        # 输出统计信息
        print("\n[INFO] SQL填充统计:")
        print(f"   - 成功执行: {success_count}")
        print(f"   - 失败: {error_count}")
        print(f"   - 总计: {len(insert_statements)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] SQL填充失败: {e}")
        return False

def verify_china_policies_in_database():
    """验证数据库中的中国政策数据"""
    print("[INFO] 验证数据库中的中国政策数据...")
    
    try:
        # 导入数据库服务
        from services.policy_database_service import PolicyDatabaseService
        
        # 创建数据库服务实例
        db_service = PolicyDatabaseService()
        
        # 查询中国政策
        china_policies = db_service.search_policies(country="CN")
        
        print(f"[INFO] 数据库中找到 {len(china_policies)} 条中国政策")
        
        if china_policies:
            # 统计信息
            regions = set()
            industries = set()
            total_incentives = 0
            total_requirements = 0
            
            for policy in china_policies:
                regions.add(policy.get('region', 'Unknown'))
                industries.add(policy.get('industry', 'Unknown'))
                
                # 计算激励措施和要求数量
                incentives = policy.get('incentives', [])
                requirements = policy.get('requirements', [])
                total_incentives += len(incentives)
                total_requirements += len(requirements)
            
            print("\n[INFO] 中国政策统计:")
            print(f"   - 覆盖地区: {len(regions)}")
            print(f"   - 涵盖行业: {len(industries)}")
            print(f"   - 总激励措施: {total_incentives}")
            print(f"   - 总要求: {total_requirements}")
            
            # 显示前5条政策
            print("\n[INFO] 前5条中国政策:")
            for i, policy in enumerate(china_policies[:5]):
                print(f"   {i+1}. {policy['title']} ({policy['region']})")
            
            return True
        else:
            print("[WARNING] 数据库中没有找到中国政策数据")
            return False
            
    except Exception as e:
        print(f"[ERROR] 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("[INFO] 中国政策数据库填充工具启动...")
    
    # 方法1: 从JSON文件填充
    print("\n[INFO] 方法1: 从JSON文件填充...")
    json_success = populate_china_policies_from_json()
    
    # 方法2: 从SQL文件填充
    print("\n[INFO] 方法2: 从SQL文件填充...")
    sql_success = populate_china_policies_from_sql()
    
    # 验证结果
    print("\n[INFO] 验证数据库...")
    verify_success = verify_china_policies_in_database()
    
    # 总结
    print("\n[INFO] 执行总结:")
    print(f"   - JSON填充: {'成功' if json_success else '失败'}")
    print(f"   - SQL填充: {'成功' if sql_success else '失败'}")
    print(f"   - 验证结果: {'成功' if verify_success else '失败'}")
    
    if json_success or sql_success:
        print("\n[SUCCESS] 中国政策数据填充完成!")
        return True
    else:
        print("\n[ERROR] 中国政策数据填充失败!")
        return False

if __name__ == "__main__":
    main()