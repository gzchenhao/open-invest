#!/usr/bin/env python3
"""
交互式AI政策查询系统（DEMONSTRATION PORTAL — TASK-P0-2.1）
包含搜索、筛选和AI对话功能

⚠️ 本门户展示的全部政策为 MOCK 演示数据（is_mock=True，0 条 VERIFIED），
非生产政府政策服务。页面横幅 / 卡片 MOCK 标签 / PDF 免责声明为强制披露层，不得移除。
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import json
import re
import io
import os
import sys
from datetime import datetime
from pathlib import Path

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 演示政策数据（MOCK）：is_mock=True 显式标记；联系方式/来源均未经官方核验。
# 依据 TASK-P0-2 DATA-INTEGRITY 规则：宁可 null，不要猜。
policies = [
    {
        "id": 1,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "北京中关村人工智能产业扶持政策",
        "region": "北京中关村",
        "industry": "AI",
        "type": "专项补贴",
        "amount": "最高500万",
        "issue_date": "2024-03-15",  # 颁布日期
        "valid_period": "2024-03-15至2026-12-31",  # 有效期
        "source_url": "/api/policy/1/pdf",  # 源文件下载
        "official_contact": {  # 联系方式字段（全部未核验，TASK-P0-2 已置 null）
            "department": "中关村科学城管理委员会产业发展处",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",  # 认领状态: unclaimed/claimed
        "claim_token": None,  # 认领令牌（用于政策所有者认领）
        "description": "针对人工智能企业的专项扶持政策，包括研发补贴、场地优惠、人才奖励等多重支持。",
        "details": [
            "研发投入补贴：最高300万",
            "办公场地租金减免：前3年免租金",
            "高端人才奖励：每人每年20万",
            "设备购置补贴：最高200万",
            "专利申请资助：每项专利5万"
        ],
        "requirements": {
            "研发人员比例": "不低于30%",
            "专利数量": "至少5项发明专利",
            "注册资本": "不低于1000万",
            "成立时间": "不少于2年"
        }
    },
    {
        "id": 2,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "上海张江半导体产业扶持政策",
        "region": "上海张江",
        "industry": "半导体",
        "type": "产业基金",
        "amount": "最高1000万",
        "issue_date": "2024-04-10",
        "valid_period": "2024-04-10至2027-04-09",
        "source_url": "/api/policy/2/pdf",
        "official_contact": {
            "department": "上海张江高科技园区管理委员会产业发展处",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",
        "claim_token": None,
        "description": "聚焦半导体产业链上下游企业，提供全方位的产业基金支持和服务。",
        "details": [
            "产业基金投资：最高500万",
            "设备购置补贴：最高300万",
            "研发投入补贴：最高200万",
            "人才公寓支持：核心员工免费住宿",
            "税收优惠：前3年企业所得税全免"
        ],
        "requirements": {
            "研发人员比例": "不低于25%",
            "专利数量": "至少3项发明专利",
            "注册资本": "不低于2000万",
            "技术领域": "必须是半导体产业链相关"
        }
    },
    {
        "id": 3,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "深圳高新区自动驾驶扶持政策",
        "region": "深圳高新区",
        "industry": "自动驾驶",
        "type": "技术奖励",
        "amount": "最高800万",
        "issue_date": "2024-05-20",
        "valid_period": "2024-05-20至2027-05-19",
        "source_url": "/api/policy/3/pdf",
        "official_contact": {
            "department": "深圳高新区管理委员会科技创新处",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",
        "claim_token": None,
        "description": "鼓励自动驾驶技术研发和产业化，提供从研发到市场推广的全链条支持。",
        "details": [
            "技术研发补贴：最高400万",
            "道路测试支持：免费测试场地",
            "示范应用奖励：最高200万",
            "产业化支持：最高200万",
            "人才引进补贴：每人每年30万"
        ],
        "requirements": {
            "研发人员比例": "不低于40%",
            "专利数量": "至少8项发明专利",
            "注册资本": "不低于5000万",
            "测试场地": "必须有实际测试场地"
        }
    },
    {
        "id": 4,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "合肥高新区量子计算产业扶持政策",
        "region": "合肥高新区",
        "industry": "量子计算",
        "type": "专项基金",
        "amount": "最高1200万",
        "issue_date": "2024-03-01",
        "valid_period": "2024-03-01至2026-12-31",
        "source_url": "/api/policy/4/pdf",
        "official_contact": {
            "department": "合肥高新区量子计算产业发展办公室",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",
        "claim_token": None,
        "description": "重点支持量子计算技术研发和产业化，打造量子计算产业高地。",
        "details": [
            "研发投入补贴：最高600万",
            "设备购置支持：最高400万",
            "产业化基金：最高200万",
            "人才团队建设：最高100万",
            "应用场景开发：最高100万"
        ],
        "requirements": {
            "研发人员比例": "不低于50%",
            "专利数量": "至少10项发明专利",
            "注册资本": "不低于3000万",
            "技术团队": "必须有博士以上团队"
        }
    },
    {
        "id": 5,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "杭州滨江区块链产业扶持政策",
        "region": "杭州滨江区",
        "industry": "区块链",
        "type": "创新奖励",
        "amount": "最高600万",
        "issue_date": "2024-06-15",
        "valid_period": "2024-06-15至2027-06-14",
        "source_url": "/api/policy/5/pdf",
        "official_contact": {
            "department": "杭州滨江高新区管理委员会创新发展处",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",
        "claim_token": None,
        "description": "支持区块链技术创新和应用落地，培育区块链产业集群。",
        "details": [
            "技术创新奖励：最高300万",
            "应用场景补贴：最高200万",
            "标准制定奖励：最高50万",
            "人才引进补贴：最高50万",
            "市场推广支持：最高50万"
        ],
        "requirements": {
            "研发人员比例": "不低于20%",
            "专利数量": "至少3项发明专利",
            "注册资本": "不低于500万",
            "应用场景": "必须有实际应用案例"
        }
    },
    {
        "id": 6,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "成都高新区生物医药扶持政策",
        "region": "成都高新区",
        "industry": "生物科技",
        "type": "研发补贴",
        "amount": "最高900万",
        "issue_date": "2024-04-25",
        "valid_period": "2024-04-25至2027-04-24",
        "source_url": "/api/policy/6/pdf",
        "official_contact": {
            "department": "成都高新区生物医药产业发展推进办公室",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",
        "claim_token": None,
        "description": "重点支持生物医药研发和产业化，打造西部生物医药创新高地。",
        "details": [
            "研发投入补贴：最高400万",
            "临床试验补贴：最高300万",
            "产业化支持：最高200万",
            "人才引进补贴：最高50万",
            "市场准入支持：最高50万"
        ],
        "requirements": {
            "研发人员比例": "不低于35%",
            "专利数量": "至少6项发明专利",
            "注册资本": "不低于1000万",
            "认证资质": "必须通过GMP认证"
        }
    },
    {
        "id": 7,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "武汉东湖高端装备扶持政策",
        "region": "武汉东湖高新区",
        "industry": "高端装备",
        "type": "设备补贴",
        "amount": "最高700万",
        "issue_date": "2024-05-10",
        "valid_period": "2024-05-10至2027-05-09",
        "source_url": "/api/policy/7/pdf",
        "official_contact": {
            "department": "武汉东湖高新区装备制造产业推进处",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",
        "claim_token": None,
        "description": "支持高端装备制造技术研发和产业化，推动制造业转型升级。",
        "details": [
            "设备购置补贴：最高350万",
            "技术研发补贴：最高200万",
            "产业化支持：最高150万",
            "人才团队建设：最高50万",
            "市场推广支持：最高50万"
        ],
        "requirements": {
            "研发人员比例": "不低于30%",
            "专利数量": "至少4项发明专利",
            "注册资本": "不低于800万",
            "生产能力": "必须具备规模化生产能力"
        }
    },
    {
        "id": 8,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "西安高新区航空航天扶持政策",
        "region": "西安高新区",
        "industry": "航空航天",
        "type": "专项基金",
        "amount": "最高1000万",
        "issue_date": "2024-03-20",
        "valid_period": "2024-03-20至2027-03-19",
        "source_url": "/api/policy/8/pdf",
        "official_contact": {
            "department": "西安高新区航空航天产业发展办公室",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",
        "claim_token": None,
        "description": "支持航空航天技术研发和产业化，打造航空航天产业基地。",
        "details": [
            "研发投入补贴：最高500万",
            "设备购置补贴：最高300万",
            "产业化支持：最高200万",
            "人才引进补贴：最高50万",
            "市场开拓支持：最高50万"
        ],
        "requirements": {
            "研发人员比例": "不低于40%",
            "专利数量": "至少8项发明专利",
            "注册资本": "不低于2000万",
            "资质认证": "必须获得相关行业资质"
        }
    },
    {
        "id": 9,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "南京江北新区新材料扶持政策",
        "region": "南京江北新区",
        "industry": "新材料",
        "type": "研发奖励",
        "amount": "最高800万",
        "issue_date": "2024-06-01",
        "valid_period": "2024-06-01至2027-05-31",
        "source_url": "/api/policy/9/pdf",
        "official_contact": {
            "department": "南京江北新区新材料产业发展中心",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",
        "claim_token": None,
        "description": "支持新材料技术研发和产业化，推动新材料产业创新发展。",
        "details": [
            "研发投入补贴：最高400万",
            "中试基地支持：最高200万",
            "产业化支持：最高200万",
            "人才引进补贴：最高50万",
            "标准制定奖励：最高50万"
        ],
        "requirements": {
            "研发人员比例": "不低于25%",
            "专利数量": "至少5项发明专利",
            "注册资本": "不低于600万",
            "实验条件": "必须具备完整实验条件"
        }
    },
    {
        "id": 10,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "天津滨海新能源扶持政策",
        "region": "天津滨海高新区",
        "industry": "新能源",
        "type": "产业基金",
        "amount": "最高1100万",
        "issue_date": "2024-04-15",
        "valid_period": "2024-04-15至2027-04-14",
        "source_url": "/api/policy/10/pdf",
        "official_contact": {
            "department": "天津滨海高新区新能源产业推进处",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",
        "claim_token": None,
        "description": "重点支持新能源技术研发和产业化，打造新能源产业集群。",
        "details": [
            "技术研发补贴：最高500万",
            "产业化支持：最高400万",
            "设备购置补贴：最高200万",
            "人才引进补贴：最高50万",
            "市场推广支持：最高50万"
        ],
        "requirements": {
            "研发人员比例": "不低于30%",
            "专利数量": "至少6项发明专利",
            "注册资本": "不低于1500万",
            "技术成熟度": "技术必须达到中试阶段"
        }
    },
    {
        "id": 11,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "珠海横琴金融科技扶持政策",
        "region": "珠海横琴新区",
        "industry": "金融科技",
        "type": "创新奖励",
        "amount": "最高650万",
        "issue_date": "2024-05-25",
        "valid_period": "2024-05-25至2027-05-24",
        "source_url": "/api/policy/11/pdf",
        "official_contact": {
            "department": "珠海横琴新区金融产业发展局",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",
        "claim_token": None,
        "description": "支持金融科技创新和发展，打造金融科技产业高地。",
        "details": [
            "技术创新奖励：最高300万",
            "应用场景补贴：最高200万",
            "人才引进补贴：最高50万",
            "标准制定奖励：最高50万",
            "市场开拓支持：最高50万"
        ],
        "requirements": {
            "研发人员比例": "不低于20%",
            "专利数量": "至少3项发明专利",
            "注册资本": "不低于300万",
            "合规要求": "必须符合金融监管要求"
        }
    },
    {
        "id": 12,
        "is_mock": True,  # TASK-P0-2: 演示数据显式标记（非真实政府政策）
        "verification_status": "mock",
        "title": "苏州工业园区纳米技术扶持政策",
        "region": "苏州工业园区",
        "industry": "纳米技术",
        "type": "专项基金",
        "amount": "最高850万",
        "issue_date": "2024-03-10",
        "valid_period": "2024-03-10至2026-12-31",
        "source_url": "/api/policy/12/pdf",
        "official_contact": {
            "department": "苏州工业园区纳米技术产业发展处",
            "phone": None,  # TASK-P0-2: 未经官方来源核验的电话一律置 null
            "email": None,  # TASK-P0-2: 未经官方来源核验的邮箱一律置 null
            "address": None,  # TASK-P0-2: 未经官方来源核验的地址一律置 null
            "contact_status": "unverified"  # 联系方式未核验（DATA-INTEGRITY-003）
        },
        "claim_status": "unclaimed",
        "claim_token": None,
        "description": "支持纳米技术研发和产业化，打造纳米技术创新高地。",
        "details": [
            "研发投入补贴：最高400万",
            "设备购置补贴：最高250万",
            "产业化支持：最高200万",
            "人才引进补贴：最高50万",
            "国际合作支持：最高50万"
        ],
        "requirements": {
            "研发人员比例": "不低于35%",
            "专利数量": "至少7项发明专利",
            "注册资本": "不低于800万",
            "实验设备": "必须具备纳米级实验设备"
        }
    }
]

# P1-3.3: Enrich policies with canonical_industry (non-destructive, optional field)
try:
    _project_root = str(Path(__file__).parent.parent.parent)
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    from schema.canonical_taxonomy import get_registry
    _registry = get_registry()
    for _p in policies:
        _legacy = _p.get("industry", "")
        _p["canonical_industry"] = _registry.resolve(_legacy) if _legacy else "unknown"
except Exception:
    pass  # Graceful degradation: canonical_industry simply not added

def search_policies(query="", region="", industry="", min_amount=0):
    """搜索政策"""
    results = []
    
    for policy in policies:
        # 匹配查询关键词
        query_match = True
        if query:
            query_lower = query.lower()
            title_match = query_lower in policy["title"].lower()
            desc_match = query_lower in policy["description"].lower()
            industry_match = query_lower in policy["industry"].lower()
            if not (title_match or desc_match or industry_match):
                query_match = False
        
        # 匹配地区
        region_match = not region or region == policy["region"]
        
        # 匹配行业
        industry_match = not industry or industry == policy["industry"]
        
        # 匹配金额
        amount_match = True
        if min_amount > 0:
            try:
                # 提取金额数字
                amount_str = policy["amount"].replace("最高", "").replace("万", "").strip()
                amount = int(amount_str)
                if amount < min_amount:
                    amount_match = False
            except:
                amount_match = False
        
        if query_match and region_match and industry_match and amount_match:
            results.append(policy)
    
    return results

@app.get("/", response_class=HTMLResponse)
async def home():
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenInvest AI政策查询系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: #333; 
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header h1 { color: #667eea; margin-bottom: 10px; font-size: 2.5em; }
        .header p { color: #666; font-size: 1.2em; }
        
        .search-section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .search-title { color: #667eea; margin-bottom: 20px; font-size: 1.5em; }
        .search-form { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr auto; gap: 15px; align-items: end; }
        .form-group { display: flex; flex-direction: column; }
        .form-group label { margin-bottom: 5px; font-weight: bold; color: #555; }
        .form-group input, .form-group select { 
            padding: 12px; 
            border: 2px solid #e0e0e0; 
            border-radius: 8px; 
            font-size: 16px;
            transition: border-color 0.3s;
        }
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        .search-btn { 
            padding: 12px 30px; 
            background: #667eea; 
            color: white; 
            border: none; 
            border-radius: 8px; 
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .search-btn:hover { background: #5a6fd8; }
        
        .results-section { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .results-title { color: #667eea; margin-bottom: 20px; font-size: 1.5em; }
        .policy-card { 
            background: #f8f9fa; 
            padding: 25px; 
            margin: 15px 0; 
            border-radius: 12px; 
            border-left: 5px solid #667eea;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .policy-card:hover { 
            transform: translateY(-5px); 
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }
        .policy-title { color: #667eea; font-size: 1.3em; font-weight: bold; margin-bottom: 15px; }
        .policy-meta { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px; }
        .policy-tag { 
            padding: 6px 15px; 
            border-radius: 20px; 
            font-size: 0.9em; 
            font-weight: bold;
        }
        .region-tag { background: #667eea; color: white; }
        .industry-tag { background: #28a745; color: white; }
        .type-tag { background: #17a2b8; color: white; }
        .amount-tag { background: #ffc107; color: #333; }
        .policy-description { color: #666; margin-bottom: 15px; }
        .policy-details { 
            background: white; 
            padding: 15px; 
            border-radius: 8px; 
            margin-bottom: 15px; 
        }
        .policy-details h4 { color: #667eea; margin-bottom: 10px; }
        .policy-details ul { margin: 0; padding-left: 20px; }
        .policy-details li { margin: 5px 0; color: #555; }
        .policy-requirements { 
            background: #fff3cd; 
            padding: 15px; 
            border-radius: 8px; 
            border: 1px solid #ffeaa7;
        }
        .policy-requirements h4 { color: #856404; margin-bottom: 10px; }
        .policy-requirements ul { margin: 0; padding-left: 20px; }
        .policy-requirements li { margin: 5px 0; color: #856404; }
        
        .no-results { text-align: center; color: #666; font-size: 1.2em; margin: 40px 0; }
        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat { text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px; }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .ai-section { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            border-radius: 15px; 
            margin: 30px 0;
            text-align: center;
        }
        .ai-section h3 { margin-bottom: 15px; font-size: 1.8em; }
        .ai-section p { margin-bottom: 20px; font-size: 1.1em; }
        .ai-btn { 
            padding: 15px 40px; 
            background: white; 
            color: #667eea; 
            border: none; 
            border-radius: 30px; 
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        .ai-btn:hover { transform: scale(1.05); }
        
        @media (max-width: 768px) {
            .search-form { grid-template-columns: 1fr; }
            .policy-meta { flex-direction: column; }
            .stats { flex-direction: column; gap: 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 OpenInvest AI政策查询系统</h1>
            <p>智能发现 · 精准匹配 · 高效申请</p>
            <p style="margin-top: 12px; padding: 10px 16px; background: #fff3cd; color: #856404; border: 1px solid #ffeeba; border-radius: 8px; font-size: 0.9em;">
                ⚠️ 数据声明：当前展示的政策均为 <strong>MOCK 演示数据</strong>（is_mock=true），
                未经官方来源核验，不得作为申报、投资或决策依据。联系方式未经核验前一律留空。
            </p>
        </div>

        <div class="search-section">
            <h2 class="search-title">🔍 智能政策搜索</h2>
            <form class="search-form" onsubmit="searchPolicies(event)">
                <div class="form-group">
                    <label for="query">关键词搜索</label>
                    <input type="text" id="query" placeholder="输入AI、自动驾驶、半导体等关键词...">
                </div>
                <div class="form-group">
                    <label for="region">地区</label>
                    <select id="region">
                        <option value="">全部地区</option>
                        <option value="北京中关村">北京中关村</option>
                        <option value="上海张江">上海张江</option>
                        <option value="深圳高新区">深圳高新区</option>
                        <option value="合肥高新区">合肥高新区</option>
                        <option value="杭州滨江区">杭州滨江区</option>
                        <option value="成都高新区">成都高新区</option>
                        <option value="武汉东湖高新区">武汉东湖高新区</option>
                        <option value="西安高新区">西安高新区</option>
                        <option value="南京江北新区">南京江北新区</option>
                        <option value="天津滨海高新区">天津滨海高新区</option>
                        <option value="珠海横琴新区">珠海横琴新区</option>
                        <option value="苏州工业园区">苏州工业园区</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="industry">行业</label>
                    <select id="industry">
                        <option value="">全部行业</option>
                        <option value="AI">AI</option>
                        <option value="半导体">半导体</option>
                        <option value="自动驾驶">自动驾驶</option>
                        <option value="量子计算">量子计算</option>
                        <option value="区块链">区块链</option>
                        <option value="生物科技">生物科技</option>
                        <option value="高端装备">高端装备</option>
                        <option value="航空航天">航空航天</option>
                        <option value="新材料">新材料</option>
                        <option value="新能源">新能源</option>
                        <option value="金融科技">金融科技</option>
                        <option value="纳米技术">纳米技术</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="minAmount">最低金额(万)</label>
                    <input type="number" id="minAmount" placeholder="0" min="0">
                </div>
                <button type="submit" class="search-btn">🔍 搜索</button>
            </form>
        </div>

        <div class="ai-section">
            <h3>🤖 AI智能助手</h3>
            <p>让AI为您精准匹配最适合的政策</p>
            <button class="ai-btn" onclick="startAIChat()">💬 开始AI对话</button>
        </div>

        <div class="results-section">
            <h2 class="results-title">📋 搜索结果</h2>
            <div id="results">
                <!-- 搜索结果将在这里显示 -->
            </div>
        </div>
    </div>

    <script>
        // 政策数据 - 由Python后端自动生成，确保前后端数据一致
        const policies = {{POLICIES_JSON}};

        // 初始化显示所有政策
        document.addEventListener('DOMContentLoaded', function() {
            displayAllPolicies();
        });

        function displayAllPolicies() {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            
            policies.forEach(policy => {
                const policyCard = createPolicyCard(policy);
                resultsDiv.appendChild(policyCard);
            });
        }

        function createPolicyCard(policy) {
            const card = document.createElement('div');
            card.className = 'policy-card';
            
            const requirements = Object.entries(policy.requirements).map(([key, value]) => 
                `<li><strong>${key}:</strong> ${value}</li>`
            ).join('');
            
            // 构建联系方式HTML
            let contactHtml = '';
            if (policy.official_contact) {
                contactHtml = `
                    <div style="margin-top: 15px; padding: 12px; background: #e3f2fd; border-radius: 8px; border-left: 4px solid #2196f3;">
                        <h4 style="color: #1976d2; margin-bottom: 8px;">📞 联系方式：未核验</h4>
                        <p style="margin: 5px 0; color: #555;"><strong>部门：</strong>${policy.official_contact.department || '未核验'}</p>
                        <p style="margin: 5px 0; color: #555;"><strong>电话：</strong>${policy.official_contact.phone || '未核验（待官方认领后提供）'}</p>
                        <p style="margin: 5px 0; color: #555;"><strong>邮箱：</strong>${policy.official_contact.email || '未核验（待官方认领后提供）'}</p>
                        <p style="margin: 5px 0; color: #555;"><strong>地址：</strong>${policy.official_contact.address || '未核验'}</p>
                    </div>
                `;
            }
            
            // 构建认领勾子HTML
            let claimHookHtml = '';
            if (policy.claim_status === 'unclaimed') {
                claimHookHtml = `
                    <div style="margin-top: 15px; padding: 12px; background: linear-gradient(135deg, #fff9e6 0%, #ffeaa7 100%); border-radius: 8px; border: 2px dashed #ffc107; text-align: center;">
                        <p style="margin: 0 0 10px 0; color: #856404; font-weight: bold;">🎯 您是该政策的发布方吗？</p>
                        <button onclick="claimPolicy(${policy.id})" style="padding: 8px 20px; background: #ffc107; color: #333; border: none; border-radius: 20px; cursor: pointer; font-weight: bold; transition: all 0.3s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                            👉 立即认领此政策
                        </button>
                        <p style="margin: 8px 0 0 0; font-size: 0.85em; color: #856404;">认领后可更新政策信息、维护联系方式</p>
                        <p style="margin: 5px 0 0 0; font-size: 0.8em; color: #856404;">联系平台管理员: <a href="mailto:30861337@qq.com" style="color: #1976d2;">30861337@qq.com</a></p>
                    </div>
                `;
            } else {
                claimHookHtml = `
                    <div style="margin-top: 15px; padding: 10px; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745; text-align: center;">
                        <p style="margin: 0; color: #155724; font-weight: bold;">✅ 该政策已被官方认领</p>
                    </div>
                `;
            }
            
            card.innerHTML = `
                <div class="policy-title">${policy.title}</div>
                <div class="policy-meta">
                    ${policy.is_mock ? '<span class="policy-tag" style="background:#fff3cd;color:#856404;border:1px solid #ffc107;font-weight:bold;">⚠️ MOCK / 演示数据 · 未经官方来源核验</span>' : ''}
                    <span class="policy-tag region-tag">${policy.region}</span>
                    <span class="policy-tag industry-tag">${policy.industry}</span>
                    <span class="policy-tag type-tag">${policy.type}</span>
                    <span class="policy-tag amount-tag">${policy.amount}</span>
                </div>
                
                <!-- 新增：颁布日期和有效期 -->
                <div style="margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #6c757d;">
                    <p style="margin: 5px 0; color: #495057;"><strong>📅 颁布日期：</strong>${policy.issue_date || '未注明'}</p>
                    <p style="margin: 5px 0; color: #495057;"><strong>⏰ 有效期：</strong>${policy.valid_period || '长期有效'}</p>
                </div>
                
                <!-- 新增：源文件下载 -->
                ${policy.source_url ? `
                <div style="margin: 10px 0;">
                    <a href="${policy.source_url}" target="_blank" style="display: inline-block; padding: 10px 20px; background: #dc3545; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; transition: all 0.3s;" onmouseover="this.style.background='#c82333'" onmouseout="this.style.background='#dc3545'">
                        📄 下载演示文档（PDF，非官方红头文件）
                    </a>
                </div>
                ` : ''}
                
                <div class="policy-description">${policy.description}</div>
                <div class="policy-details">
                    <h4>📋 政策详情</h4>
                    <ul>
                        ${policy.details.map(detail => `<li>${detail}</li>`).join('')}
                    </ul>
                </div>
                <div class="policy-requirements">
                    <h4>📊 申请要求</h4>
                    <ul>
                        ${requirements}
                    </ul>
                </div>
                
                <!-- 联系方式：未核验 -->
                ${contactHtml}
                
                <!-- 新增：认领勾子 -->
                ${claimHookHtml}
            `;
            
            return card;
        }

        function searchPolicies(event) {
            event.preventDefault();
            
            const query = document.getElementById('query').value;
            const region = document.getElementById('region').value;
            const industry = document.getElementById('industry').value;
            const minAmount = parseInt(document.getElementById('minAmount').value) || 0;
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            
            // 过滤政策
            const filteredPolicies = policies.filter(policy => {
                // 关键词匹配
                const queryMatch = !query || 
                    policy.title.toLowerCase().includes(query.toLowerCase()) ||
                    policy.description.toLowerCase().includes(query.toLowerCase()) ||
                    policy.industry.toLowerCase().includes(query.toLowerCase());
                
                // 地区匹配
                const regionMatch = !region || policy.region === region;
                
                // 行业匹配
                const industryMatch = !industry || policy.industry === industry;
                
                // 金额匹配
                const amountMatch = !minAmount || checkAmountMatch(policy.amount, minAmount);
                
                return queryMatch && regionMatch && industryMatch && amountMatch;
            });
            
            if (filteredPolicies.length === 0) {
                resultsDiv.innerHTML = '<div class="no-results">😔 没有找到匹配的政策，请尝试调整搜索条件</div>';
            } else {
                filteredPolicies.forEach(policy => {
                    const policyCard = createPolicyCard(policy);
                    resultsDiv.appendChild(policyCard);
                });
            }
        }
        
        // 辅助函数：检查金额匹配
        function checkAmountMatch(amountStr, minAmount) {
            try {
                const amount = parseInt(amountStr.replace(/[^0-9]/g, ''));
                return amount >= minAmount;
            } catch {
                return true;
            }
        }

        function startAIChat() {
            alert('🤖 AI对话功能正在开发中！\\n\\n未来将包含：\\n• 自然语言政策查询\\n• 智能推荐匹配\\n• 申请指导\\n• 政策解读');
        }
        
        // 新增：认领政策功能
        function claimPolicy(policyId) {
            const policy = policies.find(p => p.id === policyId);
            if (!policy) {
                alert('❌ 未找到该政策');
                return;
            }
            
            // 显示认领对话框
            const claimToken = prompt(
                `🎯 认领政策：${policy.title}\n\n` +
                `请输入您的认领令牌（Claim Token）：\n` +
                `（如果您是政策发布方，请联系平台管理员获取令牌）\n\n` +
                `平台管理员邮箱: 30861337@qq.com`
            );
            
            if (!claimToken) {
                return; // 用户取消
            }
            
            // 模拟认领验证（实际应该调用后端API）
            if (claimToken.length >= 8) {
                // 更新政策状态
                policy.claim_status = 'claimed';
                policy.claim_token = claimToken;
                
                alert(
                    '✅ 认领成功！\\n\\n' +
                    '您现在可以：\\n' +
                    '• 更新政策信息\\n' +
                    '• 维护联系方式\\n' +
                    '• 上传最新文件\\n' +
                    '• 查看申请统计'
                );
                
                // 刷新页面显示
                displayAllPolicies();
            } else {
                alert('❌ 认领令牌无效，请联系系统管理员');
            }
        }
    </script>
</body>
</html>'''
    # 将Python政策数据注入到JavaScript中，确保前后端数据完全一致
    policies_json = json.dumps(policies, ensure_ascii=False)
    return html.replace('{{POLICIES_JSON}}', policies_json)

# PDF生成端点
@app.get("/api/policy/{policy_id}/pdf")
async def generate_policy_pdf(policy_id: int):
    """生成政策文件PDF"""
    from fpdf import FPDF
    
    # 查找政策
    policy = None
    for p in policies:
        if p["id"] == policy_id:
            policy = p
            break
    
    if not policy:
        return {"error": "Policy not found"}
    
    # 创建PDF
    pdf = FPDF()
    pdf.add_page()
    
    # 加载中文字体
    font_path = r"C:\Windows\Fonts\simhei.ttf"
    if os.path.exists(font_path):
        pdf.add_font("SimHei", "", font_path, uni=True)
        font_name = "SimHei"
    else:
        font_name = "Helvetica"
    
    # 标题
    pdf.set_font(font_name, size=18)
    pdf.cell(0, 15, policy["title"], ln=True, align="C")
    pdf.ln(2)

    # TASK-P0-2.1 首页醒目免责声明：PDF 不得在无警示情况下呈现 MOCK 政策
    pdf.set_fill_color(255, 243, 205)  # 黄色警示底（与页面横幅一致）
    pdf.set_text_color(133, 100, 4)
    pdf.set_font(font_name, size=10)
    pdf.multi_cell(
        0, 6,
        "⚠️ MOCK / DEMONSTRATION DATA：本文档内容为演示数据，"
        "未经官方来源核验，不代表任何政府部门的正式政策、补贴承诺或招商条件，"
        "不得用于实际申报、投资或商业决策。",
        ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # 基本信息
    pdf.set_font(font_name, size=11)
    pdf.cell(0, 8, f"颁布日期: {policy.get('issue_date', '未注明')}", ln=True)
    pdf.cell(0, 8, f"有效期: {policy.get('valid_period', '长期有效')}", ln=True)
    pdf.cell(0, 8, f"地区: {policy['region']}", ln=True)
    pdf.cell(0, 8, f"行业: {policy['industry']}", ln=True)
    pdf.cell(0, 8, f"类型: {policy['type']}", ln=True)
    pdf.cell(0, 8, f"扶持金额: {policy['amount']}", ln=True)
    pdf.ln(5)
    
    # 政策描述
    pdf.set_font(font_name, size=14)
    pdf.cell(0, 10, "政策概述", ln=True)
    pdf.set_font(font_name, size=11)
    pdf.multi_cell(0, 7, policy["description"])
    pdf.ln(5)
    
    # 政策详情
    pdf.set_font(font_name, size=14)
    pdf.cell(0, 10, "政策详情", ln=True)
    pdf.set_font(font_name, size=11)
    for detail in policy.get("details", []):
        pdf.cell(0, 7, f"  - {detail}", ln=True)
    pdf.ln(5)
    
    # 申请要求
    pdf.set_font(font_name, size=14)
    pdf.cell(0, 10, "申请要求", ln=True)
    pdf.set_font(font_name, size=11)
    for key, value in policy.get("requirements", {}).items():
        pdf.cell(0, 7, f"  {key}: {value}", ln=True)
    pdf.ln(5)
    
    # 联系方式（未核验；字段为 null 时显示“未核验”，绝不生成虚构联系方式）
    contact = policy.get("official_contact", {})
    if contact:
        pdf.set_font(font_name, size=14)
        pdf.cell(0, 10, "联系方式（未核验）", ln=True)
        pdf.set_font(font_name, size=11)
        pdf.cell(0, 7, f"  部门: {contact.get('department') or '未核验'}", ln=True)
        pdf.cell(0, 7, f"  电话: {contact.get('phone') or '未核验（待官方认领后提供）'}", ln=True)
        pdf.cell(0, 7, f"  邮箱: {contact.get('email') or '未核验（待官方认领后提供）'}", ln=True)
        pdf.cell(0, 7, f"  地址: {contact.get('address') or '未核验'}", ln=True)
    
    # 页脚
    pdf.ln(10)
    pdf.set_font(font_name, size=9)
    pdf.cell(0, 7, "声明：本政策为 MOCK 演示数据（is_mock=true），未经官方来源核验，仅供参考", ln=True, align="C")
    pdf.cell(0, 7, f"本文档由OpenInvest平台自动生成 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.cell(0, 7, "平台管理员邮箱: 30861337@qq.com", ln=True, align="C")
    
    # 输出PDF
    pdf_bytes = pdf.output()
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=policy_{policy_id}.pdf"}
    )

# API 端点
@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    regions = list(set(policy.get('region', 'Unknown') for policy in policies))
    industries = list(set(policy.get('industry', 'Unknown') for policy in policies))
    
    return {
        "total_policies": len(policies),
        "regions_count": len(regions),
        "industries_count": len(industries),
        "regions": regions,
        "industries": industries
    }

@app.post("/api/search")
async def search_policies_api(request: Request):
    """搜索政策 - 接受JSON格式"""
    try:
        body = await request.json()
        keywords = str(body.get("keywords", "")).strip()
        limit = int(body.get("limit", 10))
        
        if not keywords:
            return {"count": len(policies), "policies": policies[:limit]}
        
        # 关键词匹配（标题、地区、行业、描述）
        results = []
        kw = keywords.lower()
        for policy in policies:
            title = policy.get("title", "")
            region = policy.get("region", "")
            industry = policy.get("industry", "")
            description = policy.get("description", "")
            
            if (kw in title.lower() or kw in region.lower() or 
                kw in industry.lower() or kw in description.lower()):
                results.append(policy)
        
        return {
            "count": len(results),
            "policies": results[:limit]
        }
    except Exception as e:
        return {"count": 0, "policies": [], "error": str(e)}

# 启动服务

if __name__ == "__main__":
    import uvicorn
    import sys
    # 允许通过命令行参数指定端口，默认为8017
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8017
    print("OpenInvest Policy Query System Starting...")
    print(f"Access URL: http://localhost:{port}")
    print(f"Tip: Change port by: python {sys.argv[0]} [port]")
    uvicorn.run(app, host="0.0.0.0", port=port)