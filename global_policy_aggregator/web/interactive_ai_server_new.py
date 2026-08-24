#!/usr/bin/env python3
"""
交互式AI政策查询系统（LEGACY / DEMONSTRATION ONLY — TASK-P0-2.1）
包含搜索、筛选和AI对话功能

⚠️ 本服务器为演示/遗留入口，非生产政府政策服务。其内置回退数据全部为
MOCK 演示数据（is_mock=True），不得对外宣称为真实政府政策。
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
import re
from pathlib import Path

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 动态加载政策数据
def load_policies():
    """从详细政策数据文件加载政策数据"""
    policies = []
    
    # 尝试从详细政策数据文件加载
    try:
        detailed_policies_file = Path(__file__).parent / "data" / "seed_data" / "detailed_china_tech_policies.json"
        if detailed_policies_file.exists():
            with open(detailed_policies_file, 'r', encoding='utf-8') as f:
                detailed_policies = json.load(f)
            
            for i, detailed_policy in enumerate(detailed_policies):
                # 映射英文行业标签到中文
                industry_map = {
                    "embodied_ai": "具身智能",
                    "auto_driving": "自动驾驶", 
                    "semiconductor": "半导体",
                    "ai": "人工智能",
                    "biotechnology": "生物医药",
                    "quantum_computing": "量子计算",
                    "new_energy": "新能源",
                    "fintech": "金融科技",
                    "aerospace": "航空航天",
                    "advanced_manufacturing": "先进制造"
                }
                
                # 计算最高金额
                max_amount = 0
                if detailed_policy.get("incentives"):
                    for incentive in detailed_policy.get("incentives", []):
                        amount = incentive.get("amount_details", {}).get("max_amount_cny", 0)
                        max_amount = max(max_amount, amount)
                
                simplified_policy = {
                    "id": i + 1,
                    "title": detailed_policy.get("title", "未知政策"),
                    "region": detailed_policy.get("region", "未知地区"),
                    "industry": industry_map.get(detailed_policy.get("industry", ""), "其他"),
                    "type": detailed_policy.get("policy_type", "专项补贴"),
                    "amount": f"最高{max_amount//10000}万" if max_amount > 0 else "面议",
                    "issue_date": detailed_policy.get("issue_date", "2024-01-01"),
                    "valid_period": detailed_policy.get("valid_period", "长期有效"),
                    "source_url": detailed_policy.get("policy_document_url", "#"),
                    "is_mock": True,  # TASK-P0-2: 演示数据显式标记（未逐条完成官方来源验证）
                    "verification_status": "mock",
                    "official_contact": detailed_policy.get("contact_information", {
                        "department": "相关部门",
                        "phone": None,
                        "email": None,
                        "address": None,
                        "contact_status": "unverified"
                    }),
                    "claim_status": "unclaimed",
                    "claim_token": None,
                    "description": detailed_policy.get("description", "政策描述"),
                    "details": [incentive.get("title", "") for incentive in detailed_policy.get("incentives", [])],
                    "requirements": {req.get("requirement_type", ""): req.get("description", "") for req in detailed_policy.get("requirements", [])}
                }
                
                policies.append(simplified_policy)
                
            print(f"DEBUG: 成功加载 {len(policies)} 条政策数据")
            return policies
    
    except Exception as e:
        print(f"ERROR: 加载详细政策数据失败: {e}")
    
    # 如果加载失败，使用简化的测试数据
    # TASK-P0-2: 以下为 MOCK 演示数据。原 source_url 与联系方式均为虚构，已按 DATA-INTEGRITY 规则置 null。
    return [
        {
            "id": 1,
            "is_mock": True,
            "verification_status": "mock",
            "title": "北京中关村人工智能产业扶持政策",
            "region": "北京中关村",
            "industry": "人工智能",
            "type": "专项补贴",
            "amount": "最高500万",
            "issue_date": "2024-03-15",
            "valid_period": "2024-03-15至2026-12-31",
            "source_url": None,  # TASK-P0-2: 原 URL 为虚构，未经官方核验不保留（DATA-INTEGRITY-002）
            "official_contact": {
                "department": "中关村科学城管理委员会产业发展处",
                "phone": None,  # TASK-P0-2: 虚构电话置 null（宁可没有，不要错误）
                "email": None,
                "address": None,
                "contact_status": "unverified"
            },
            "claim_status": "unclaimed",
            "claim_token": None,
            "description": "支持人工智能技术研发和产业化应用，打造全球人工智能创新高地。",
            "details": [
                "研发投入补贴：最高500万",
                "设备购置补贴：最高300万",
                "人才团队建设：最高100万",
                "市场推广支持：最高50万",
                "产业化支持：最高200万"
            ],
            "requirements": {
                "研发人员比例": "不低于40%",
                "专利数量": "至少3项发明专利",
                "注册资本": "不低于1000万",
                "企业规模": "员工不少于50人"
            }
        },
        {
            "id": 2,
            "is_mock": True,
            "verification_status": "mock",
            "title": "上海张江半导体产业扶持政策", 
            "region": "上海张江",
            "industry": "半导体",
            "type": "专项资金",
            "amount": "最高2000万",
            "issue_date": "2024-02-20",
            "valid_period": "2024-02-20至2026-12-31",
            "source_url": None,  # TASK-P0-2: 原 URL 为虚构，未经官方核验不保留
            "official_contact": {
                "department": "张江科学城管理委员会产业发展处",
                "phone": None,  # TASK-P0-2: 虚构电话置 null
                "email": None,
                "address": None,
                "contact_status": "unverified"
            },
            "claim_status": "unclaimed",
            "claim_token": None,
            "description": "支持集成电路设计、制造、封测全产业链发展，打造世界级集成电路产业集群。",
            "details": [
                "研发投入补贴：最高1000万",
                "设备购置补贴：最高800万",
                "人才引进补贴：最高200万",
                "市场开拓支持：最高100万",
                "产业化支持：最高500万"
            ],
            "requirements": {
                "研发人员比例": "不低于50%",
                "专利数量": "至少5项发明专利",
                "注册资本": "不低于2000万",
                "生产能力": "必须具备量产能力"
            }
        }
    ]

# 加载政策数据
policies = load_policies()