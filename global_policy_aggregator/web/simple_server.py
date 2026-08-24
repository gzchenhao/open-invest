#!/usr/bin/env python3
"""
简单测试服务器（LEGACY / DEMONSTRATION ONLY — TASK-P0-2.1）

⚠️ 本页内联硬编码的政策卡片为 MOCK 演示数据，非真实政府政策；
页面顶部已注入强制 MOCK 披露横幅，不得移除。
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    return '''<!DOCTYPE html>
<html>
<head>
    <title>OpenInvest 中国政策展示系统</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .container { max-width: 1000px; margin: 0 auto; background: white; color: #333; padding: 30px; border-radius: 10px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #667eea; margin: 0; }
        .stats { display: flex; justify-content: space-around; margin: 30px 0; }
        .stat { text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .policies { margin-top: 30px; }
        .policy-card { background: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }
    </style>
</head>
<body>
<!-- P0-2.1-MOCK-DISCLOSURE: 强制 MOCK 数据披露横幅（TASK-P0-2.1） -->
<div style="position:relative;z-index:9999;margin:0;padding:14px 20px;background:#fff3cd;color:#856404;border-bottom:3px solid #ffc107;font-size:14px;line-height:1.7;font-family:sans-serif;">
  <strong>⚠️ 演示数据声明：</strong>
  当前页面展示的政策信息均为 <strong>MOCK / 演示数据</strong>，尚未经过官方来源核验，
  不代表任何政府部门的正式政策、补贴承诺或招商条件。请勿将其用于实际申报、投资或商业决策。<br>
  <strong>⚠️ DEMONSTRATION DATA:</strong>
  All policy information displayed on this portal is MOCK / synthetic demonstration data and has not been
  verified against authoritative government sources. It does not represent official government policy,
  subsidy commitments, investment terms, or eligibility conditions.
</div>

    <div class="container">
        <div class="header">
            <h1>🚀 OpenInvest 中国政策展示系统</h1>
            <p>智能发现 · 精准匹配 · 高效申请</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">12</div>
                <div>中国政策</div>
            </div>
            <div class="stat">
                <div class="stat-number">10</div>
                <div>覆盖地区</div>
            </div>
            <div class="stat">
                <div class="stat-number">8</div>
                <div>热门行业</div>
            </div>
            <div class="stat">
                <div class="stat-number">100%</div>
                <div>结构化数据</div>
            </div>
        </div>
        
        <div class="policies">
            <h2>📋 中国高新区产业扶持政策</h2>
            
            <div class="policy-card">
                <h3>北京中关村人工智能产业扶持政策</h3>
                <p><strong>地区：</strong>北京中关村</p>
                <p><strong>行业：</strong>AI</p>
                <p><strong>类型：</strong>专项补贴</p>
                <p><strong>金额：</strong>最高500万</p>
                <p><strong>描述：</strong>针对人工智能企业的专项扶持政策，包括研发补贴、场地优惠、人才奖励等多重支持。</p>
            </div>
            
            <div class="policy-card">
                <h3>上海张江半导体产业扶持政策</h3>
                <p><strong>地区：</strong>上海张江</p>
                <p><strong>行业：</strong>半导体</p>
                <p><strong>类型：</strong>产业基金</p>
                <p><strong>金额：</strong>最高1000万</p>
                <p><strong>描述：</strong>聚焦半导体产业链上下游企业，提供全方位的产业基金支持和服务。</p>
            </div>
            
            <div class="policy-card">
                <h3>深圳高新区自动驾驶扶持政策</h3>
                <p><strong>地区：</strong>深圳高新区</p>
                <p><strong>行业：</strong>自动驾驶</p>
                <p><strong>类型：</strong>技术奖励</p>
                <p><strong>金额：</strong>最高800万</p>
                <p><strong>描述：</strong>鼓励自动驾驶技术研发和产业化，提供从研发到市场推广的全链条支持。</p>
            </div>
            
            <div class="policy-card">
                <h3>合肥高新区量子计算产业扶持政策</h3>
                <p><strong>地区：</strong>合肥高新区</p>
                <p><strong>行业：</strong>量子计算</p>
                <p><strong>类型：</strong>专项基金</p>
                <p><strong>金额：</strong>最高1200万</p>
                <p><strong>描述：</strong>重点支持量子计算技术研发和产业化，打造量子计算产业高地。</p>
            </div>
            
            <div class="policy-card">
                <h3>杭州滨江区块链产业扶持政策</h3>
                <p><strong>地区：</strong>杭州滨江区</p>
                <p><strong>行业：</strong>区块链</p>
                <p><strong>类型：</strong>创新奖励</p>
                <p><strong>金额：</strong>最高600万</p>
                <p><strong>描述：</strong>支持区块链技术创新和应用落地，培育区块链产业集群。</p>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #667eea;">
            <p>© 2026 OpenInvest Protocol | 全球政策聚合器</p>
            <p>让AI为您找到最适合的政策</p>
        </div>
    </div>
</body>
</html>'''

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)