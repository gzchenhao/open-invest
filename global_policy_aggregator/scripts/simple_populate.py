#!/usr/bin/env python3
"""
简单政策数据库填充脚本
"""

import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

def main():
    print("[INFO] 开始填充政策数据...")
    
    try:
        # 读取详细政策数据文件
        detailed_policies_file = Path(__file__).parent.parent / "data" / "seed_data" / "detailed_china_tech_policies.json"
        
        if not detailed_policies_file.exists():
            print(f"[ERROR] 详细政策数据文件不存在: {detailed_policies_file}")
            return False
        
        with open(detailed_policies_file, 'r', encoding='utf-8') as f:
            detailed_policies = json.load(f)
        
        print(f"[INFO] 读取到 {len(detailed_policies)} 条详细中国高新区政策数据")
        
        # 显示政策摘要
        regions = set()
        industries = set()
        
        for policy in detailed_policies:
            regions.add(policy.get('region', 'Unknown'))
            industries.add(policy.get('industry', 'Unknown'))
        
        print(f"[INFO] 覆盖地区: {len(regions)} 个")
        print(f"[INFO] 涵盖行业: {len(industries)} 个")
        print(f"[INFO] 覆盖地区: {', '.join(sorted(regions))}")
        print(f"[INFO] 涵盖行业: {', '.join(sorted(industries))}")
        
        # 显示前5条政策
        print(f"\n[INFO] 前5条详细政策:")
        for i, policy in enumerate(detailed_policies[:5]):
            incentives = policy.get('incentives', [])
            max_amount = 0
            for incentive in incentives:
                amount = incentive.get('amount_details', {}).get('max_amount_cny', 0)
                max_amount = max(max_amount, amount)
            
            print(f"   {i+1}. {policy['title']} ({policy['region']}) - 最高激励: {max_amount/10000:.0f}万元")
        
        print(f"\n[SUCCESS] 政策数据准备完成，共 {len(detailed_policies)} 条详细政策")
        return True
        
    except Exception as e:
        print(f"[ERROR] 处理失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)