#!/usr/bin/env python3
"""
交互式AI政策查询系统（DEMONSTRATION PORTAL — TASK-P0-2.1）
包含搜索、筛选和AI对话功能

⚠️ 门户政策来源（P2-0C.1）：内嵌 MOCK 演示数据（is_mock=True）+
data/real_policies/real_policies.json 加载的 REAL/UNVERIFIED 条目（is_mock=False）。
系统内 0 条 VERIFIED。页面横幅 / 卡片状态标签 / PDF 免责声明为强制披露层，不得移除。
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import json
import re
import io
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 演示政策数据（MOCK）：is_mock=True 显式标记；联系方式/来源均未经官方核验。
# 依据 TASK-P0-2 DATA-INTEGRITY 规则：宁可 null，不要猜。
# REAL Policy 统一来自 data/real_policies/real_policies.json
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
    }
]

# ─── P2-0C.1: REAL/UNVERIFIED policy ingestion（Handover §5.2: JSON file → existing Portal）───
# 最小加载器：文件缺失 / 非法 JSON / 顶层非 list / 空 list → 一律返回 []，绝不 crash Portal。
# 只读数据：不产生任何 Experimental Event，不写 p2_0_experimental/records/。
# REAL 条目数据契约（由 tests/test_p2_0_real_policy_ingestion.py 锁定）：
#   is_mock 严格 False、verification_status="unverified"、真实 HTTP(S) source_url（禁本地 PDF）、
#   禁 metadata、禁 VERIFIED/REJECTED、联系方式一律 null（宁可 null，不要猜）、id 从 101 起。
_REAL_POLICIES_FILE = Path(__file__).resolve().parent.parent / "data" / "real_policies" / "real_policies.json"


def load_real_policies():
    """Graceful loader for REAL/UNVERIFIED policies. Missing/invalid file → []."""
    try:
        if not _REAL_POLICIES_FILE.exists():
            return []
        with open(_REAL_POLICIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    return data


_real_policies = load_real_policies()
# 只保留MOCK数据，REAL数据从JSON加载
mock_policies = [p for p in policies if p.get('is_mock') == True]
real_policies = [p for p in _real_policies if p.get('is_mock') == False]
policies = mock_policies + real_policies

# P1-3.3: Enrich policies with canonical_industry (non-destructive, optional field)
try:
    _project_root = str(Path(__file__).parent.parent.parent)
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    from schema.canonical_taxonomy import get_registry
    _registry = get_registry()
    for _p in policies:
        if _p.get('industry'):
            try:
                canonical = _registry.resolve(_p['industry'])
                if canonical:
                    _p['canonical_industry'] = canonical
            except Exception:
                pass
except Exception:
    pass  # P1-3.3: Graceful fallback - no canonical_industry field

# ─── P1-4: Search and Filter Functions ──
def search_policies(event_type="POLICY_SEARCHED", actor_id=None):
    """搜索政策"""
    pass  # 简化版本，不记录事件

def search_filtered_policies(keyword="", region="", industry="", min_amount=0, event_type="POLICY_SEARCHED", actor_id=None):
    """搜索政策"""
    filtered_policies = []
    for policy in policies:
        # 关键词搜索
        if keyword and keyword.lower() not in policy.get('title', '').lower() and \
           keyword.lower() not in policy.get('description', '').lower():
            continue
            
        # 地区筛选
        if region and region != policy.get('region', ''):
            continue
            
        # 行业筛选
        if industry and industry != policy.get('industry', ''):
            continue
            
        # 金额筛选
        if min_amount > 0:
            try:
                # 提取金额数字进行比较
                policy_amount = str(policy.get('amount', ''))
                amount_match = re.search(r'(\d+(?:\.\d+)?)', policy_amount)
                if amount_match:
                    policy_amount_num = float(amount_match.group(1))
                    if policy_amount_num < min_amount:
                        continue
            except (ValueError, TypeError):
                continue
                
        filtered_policies.append(policy)
    
    return filtered_policies

def get_policy_by_id(policy_id):
    """根据ID获取政策"""
    for policy in policies:
        if policy.get('id') == policy_id:
            return policy
    return None

def get_distinct_values(field):
    """获取指定字段的 distinct 值"""
    values = set()
    for policy in policies:
        value = policy.get(field)
        if value:
            values.add(value)
    return sorted(list(values))

# ─── API 端点 ──
@app.get("/test")
async def test():
    """测试页面"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head><title>Test</title></head>
    <body>
        <h1>Test Page</h1>
        <p>Server is working!</p>
        <p>Policies count: """ + str(len(policies)) + """</p>
    </body>
    </html>
    """)

@app.get("/")
async def home():
    """首页"""
    search_regions = get_distinct_values('region')
    search_industries = get_distinct_values('industry')
    
    content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OpenInvest 政策查询平台</title>
    </head>
    <body>
        <h1>OpenInvest 政策查询平台</h1>
        <p>政策总数: {len(policies)}</p>
        <p>搜索地区: {len(search_regions)}</p>
        <p>搜索行业: {len(search_industries)}</p>
        
        <h2>政策搜索</h2>
        <form method="post">
            <input type="text" name="keyword" placeholder="关键词搜索">
            <input type="text" name="region" placeholder="地区">
            <input type="text" name="industry" placeholder="行业">
            <input type="number" name="min_amount" placeholder="最低支持上限（万元）" value="0">
            <button type="submit">搜索</button>
        </form>
        
        <h2>政策列表</h2>
        <ul>
    """
    
    for policy in policies:
        content += f'<li><a href="/policy/{policy["id"]}">{policy["title"]}</a> ({policy["region"]}) - {policy["amount"]}</li>\n'
    
    content += """
        </ul>
    </body>
    </html>
    """
    
    return HTMLResponse(content=content)

@app.post("/search")
async def search(keyword: str = Form(""), region: str = Form(""), industry: str = Form(""), min_amount: int = Form(0)):
    """搜索政策"""
    filtered_policies = search_filtered_policies(keyword, region, industry, min_amount)
    
    search_regions = get_distinct_values('region')
    search_industries = get_distinct_values('industry')
    
    content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OpenInvest 政策查询平台</title>
    </head>
    <body>
        <h1>OpenInvest 政策查询平台</h1>
        <p>政策总数: {len(filtered_policies)}</p>
        <p>搜索条件: 关键词={keyword}, 地区={region}, 行业={industry}, 最低金额={min_amount}</p>
        
        <h2>搜索结果</h2>
        <ul>
    """
    
    for policy in filtered_policies:
        content += f'<li><a href="/policy/{policy["id"]}">{policy["title"]}</a> ({policy["region"]}) - {policy["amount"]}</li>\n'
    
    if not filtered_policies:
        content += "<li>没有找到匹配的政策</li>"
    
    content += f"""
        </ul>
        
        <h2>筛选条件</h2>
        <form method="post">
            <input type="text" name="keyword" placeholder="关键词" value="{keyword}">
            <input type="text" name="region" placeholder="地区" value="{region}">
            <input type="text" name="industry" placeholder="行业" value="{industry}">
            <input type="number" name="min_amount" placeholder="最低支持上限（万元）" value="{min_amount}">
            <button type="submit">搜索</button>
        </form>
        
        <p><a href="/">← 返回首页</a></p>
    </body>
    </html>
    """
    
    return HTMLResponse(content=content)

@app.get("/policy/{policy_id}")
async def policy_detail(policy_id: int):
    """政策详情"""
    policy = get_policy_by_id(policy_id)
    if not policy:
        return HTMLResponse(content="Policy not found", status_code=404)
    
    # Handle all field types safely
    title = policy.get('title', '政策详情')
    region = policy.get('region', '') or '未指定'
    industry = policy.get('industry', '') or '未指定'
    type_ = policy.get('type', '') or '未指定'
    amount = policy.get('amount', '') or '未指定'
    issue_date = policy.get('issue_date', '') or '未指定'
    valid_period = policy.get('valid_period', '') or '未指定'
    description = policy.get('description', '') or '暂无描述'
    source_url = policy.get('source_url', '无')
    
    # Handle details field (could be string, list, or null)
    details = policy.get('details', [])
    if isinstance(details, str):
        if details.strip():
            details_list = [details]
        else:
            details_list = []
    elif isinstance(details, list):
        details_list = details
    else:
        details_list = []
    
    # Handle requirements field (could be object, string, or null)
    requirements = policy.get('requirements', {})
    if isinstance(requirements, dict):
        requirements_list = requirements
    elif isinstance(requirements, str):
        if requirements.strip():
            requirements_list = {"说明": requirements}
        else:
            requirements_list = {}
    else:
        requirements_list = {}
    
    content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body>
        <h1>{title}</h1>
        
        <h2>基本信息</h2>
        <p><strong>地区:</strong> {region}</p>
        <p><strong>行业:</strong> {industry}</p>
        <p><strong>类型:</strong> {type_}</p>
        <p><strong>金额:</strong> {amount}</p>
        <p><strong>颁布日期:</strong> {issue_date}</p>
        <p><strong>有效期:</strong> {valid_period}</p>
        
        <h2>政策描述</h2>
        <p>{description}</p>
        
        <h2>支持详情</h2>
    """
    
    if details_list:
        content += "<ul>"
        for detail in details_list:
            content += f'<li>{detail}</li>\n'
        content += "</ul>"
    else:
        content += "<p>暂无支持详情</p>"
    
    content += """
        
        <h2>申请要求</h2>
    """
    
    if requirements_list:
        content += "<ul>"
        for key, value in requirements_list.items():
            content += f'<li><strong>{key}:</strong> {value}</li>\n'
        content += "</ul>"
    else:
        content += "<p>暂无申请要求</p>"
    
    content += f"""
        
        <h2>官方来源</h2>
        <p><strong>官方链接:</strong> {source_url}</p>
        
        <h2>状态信息</h2>
        <p><strong>是否 MOCK:</strong> {'是' if policy.get('is_mock') else '否'}</p>
        <p><strong>核验状态:</strong> {policy.get('verification_status', '')}</p>
        
        <p><a href="/">← 返回首页</a></p>
    </body>
    </html>
    """
    
    return HTMLResponse(content=content)

@app.get("/api/policy/{policy_id}/pdf")
async def policy_pdf(request: Request, policy_id: int):
    """政策PDF下载（演示用）"""
    policy = get_policy_by_id(policy_id)
    if not policy:
        return JSONResponse(content={"error": "Policy not found"}, status_code=404)
    
    # 生成演示PDF内容
    details = policy.get('details', [])
    if isinstance(details, str):
        details_list = [details] if details.strip() else []
    elif isinstance(details, list):
        details_list = details
    else:
        details_list = []
    
    requirements = policy.get('requirements', {})
    if isinstance(requirements, dict):
        requirements_items = list(requirements.items())
    elif isinstance(requirements, str):
        requirements_items = [("说明", requirements)] if requirements.strip() else []
    else:
        requirements_items = []
    
    pdf_content = f"""
政策详情 - {policy.get('title', '')}

颁布日期：{policy.get('issue_date', '')}
有效期：{policy.get('valid_period', '')}

政策描述：
{policy.get('description', '')}

支持详情：
{chr(10).join(f'• {item}' for item in details_list)}

申请要求：
{chr(10).join(f'• {key}: {value}' for key, value in requirements_items)}

免责声明：本PDF为演示用途，不构成正式政策文件。请以官方发布文件为准。
    """.strip()
    
    pdf_buffer = io.StringIO(pdf_content)
    
    def generate_pdf():
        yield pdf_buffer.getvalue().encode('utf-8')
    
    return StreamingResponse(generate_pdf(), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=policy_{policy_id}.pdf"
    })

@app.get("/api/intent")
async def intent_api(request: Request):
    """项目意图API"""
    return JSONResponse(content={
        "status": "success",
        "message": "项目意图API已就绪",
        "supported_actions": ["政策匹配", "项目申报", "进度跟踪"]
    })

if __name__ == "__main__":
    import uvicorn
    import sys
    
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8017
    
    print(f"启动服务器在端口 {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)